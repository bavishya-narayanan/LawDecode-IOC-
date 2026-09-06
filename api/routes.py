"""API Routes for LAWDECODE - Phase 7 ReAct workflow."""

import traceback
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from core.config import settings
from agents.legal_understanding_agent import LegalUnderstandingAgent
from agents.legal_research_agent import LegalResearchAgent
from agents.legal_analysis_agent import LegalAnalysisAgent
from memory import LocalMemoryStore

router = APIRouter(prefix="/api", tags=["LAWDECODE"])

# Instantiate agents
understanding_agent = LegalUnderstandingAgent()
research_agent = LegalResearchAgent()
analysis_agent = LegalAnalysisAgent()
memory_store = LocalMemoryStore()


class AnalyzeRequest(BaseModel):
    """Payload for legal analysis request."""
    query: str = Field(..., min_length=1, description="Legal text, clause, or inquiry to analyze.")
    model: Optional[str] = Field(None, description="Optional Gemini model override.")


class AnalyzeResponse(BaseModel):
    """Response payload containing all three agent outputs and the final analysis."""
    success: bool
    status: str
    query: str
    model: str
    api_key_configured: bool
    gemini_response: Optional[str] = None
    error: Optional[str] = None
    agent1: Optional[Dict[str, Any]] = None
    agent2: Optional[Dict[str, Any]] = None
    agent3: Optional[Dict[str, Any]] = None
    final_analysis: Optional[Dict[str, Any]] = None
    tools: List[Dict[str, Any]] = Field(default_factory=list)
    memory: Dict[str, Any] = Field(default_factory=dict)
    workflow_events: List[str] = Field(default_factory=list)
    # Backwards-compatible flat list kept for /api/agents consumers
    agents_status: List[Dict[str, Any]] = Field(default_factory=list)


@router.get("/health")
def health_check():
    """Health check endpoint."""
    settings.refresh()
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "status": "healthy",
        "provider": settings.provider,
        "api_key_configured": settings.is_api_key_configured,
        "api_key_status": settings.api_key_status,
        "default_model": settings.DEFAULT_MODEL,
    }


@router.get("/agents")
def list_agents():
    """Returns capability status of all agents."""
    return {
        "total_agents": 3,
        "phase": "Phase 7 — ReAct Workflow Active",
        "agents": [
            understanding_agent.get_info(),
            research_agent.get_info(),
            analysis_agent.get_info(),
        ],
    }


@router.post("/analyze")
def analyze_query(payload: AnalyzeRequest):
    """Runs Agent 1 → Agent 2 pipeline and returns structured JSON.

    Always returns a valid JSON response — never a raw 500 error.
    """
    try:
        settings.refresh()
        target_model = payload.model or settings.DEFAULT_MODEL
        workflow_events: list[str] = []

        def emit(message: str) -> None:
            workflow_events.append(message)
            print(message, flush=True)

        try:
            retrieved_memory = memory_store.retrieve(payload.query)
        except Exception:
            retrieved_memory = []
        emit(f"MEMORY: Retrieved {len(retrieved_memory)} previous interactions")

        # ── Agent 1: Legal Understanding ──────────────────────────────────
        emit("Agent 1 started")
        agent1_result = understanding_agent.process(
            payload.query,
            model_name=target_model,
            memory_context=retrieved_memory,
            event_callback=emit,
        )
        agent1_dict = agent1_result.to_dict()
        agent1_success = agent1_result.status == "Success"
        emit("Agent 1 completed")

        # ── Agent 2: Legal Research (chained from Agent 1) ─────────────────
        emit("Agent 2 started")
        agent2_result = research_agent.process(
            agent1_dict, model_name=target_model
        )
        agent2_dict = agent2_result.to_dict()
        agent2_success = agent2_result.status == "Success"
        emit("Agent 2 completed")

        # ── Agent 3: Final Legal Analysis (chained from Agents 1 and 2) ────
        emit("Agent 3 started")
        agent3_result = analysis_agent.process(
            payload.query,
            agent1_dict,
            agent2_dict,
            model_name=target_model,
        )
        agent3_dict = agent3_result.to_dict()
        agent3_success = agent3_result.status == "Success"
        emit("Agent 3 completed")
        if agent3_success:
            emit("Final analysis generated")

        overall_success = agent1_success and agent2_success and agent3_success

        memory_saved = False
        if overall_success:
            memory_saved = memory_store.save(
                payload.query,
                agent1_dict,
                agent2_dict,
                agent3_dict,
                agent3_dict,
            )

        response = AnalyzeResponse(
            success=overall_success,
            status="Success" if overall_success else (
                agent1_result.status if not agent1_success else (
                    agent2_result.status if not agent2_success else agent3_result.status
                )
            ),
            query=payload.query,
            model=target_model,
            api_key_configured=settings.is_api_key_configured,
            gemini_response=agent1_result.summary if agent1_success else None,
            error=agent1_result.error if not agent1_success else (
                agent2_result.error if not agent2_success else (
                    agent3_result.error if not agent3_success else None
                )
            ),
            agent1=agent1_dict,
            agent2=agent2_dict,
            agent3=agent3_dict,
            final_analysis=agent3_dict if agent3_success else None,
            tools=agent1_dict.get("tool_results", []),
            memory={
                "retrieved_count": len(retrieved_memory),
                "retrieved": retrieved_memory,
                "saved": memory_saved,
            },
            workflow_events=workflow_events,
            agents_status=[agent1_dict, agent2_dict, agent3_dict],
        )
        return response

    except Exception as exc:
        # Safety net — always return JSON, never a raw 500 HTML page
        err_msg = f"Unexpected server error: {str(exc)[:300]}"
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "status": "Error",
                "query": getattr(payload, "query", ""),
                "model": getattr(payload, "model", "") or "",
                "api_key_configured": settings.is_api_key_configured,
                "gemini_response": None,
                "error": err_msg,
                "agent1": None,
                "agent2": None,
                "agent3": None,
                "final_analysis": None,
                "tools": [],
                "memory": {"retrieved_count": 0, "retrieved": [], "saved": False},
                "workflow_events": [],
                "agents_status": [],
            },
        )
