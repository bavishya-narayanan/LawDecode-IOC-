"""Legal Understanding Agent - Pydantic Output Models (Phase 2)."""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class LegalUnderstandingResult(BaseModel):
    """Structured output schema for the Legal Understanding Agent."""

    agent_name: str = "Legal Understanding Agent"
    status: str = "Success"
    input: str = ""
    main_issue: str = ""
    key_facts: List[str] = Field(default_factory=list)
    parties: List[str] = Field(default_factory=list)
    legal_concepts: List[str] = Field(default_factory=list)
    points_for_further_analysis: List[str] = Field(default_factory=list)
    summary: str = ""
    tool_results: List[Dict[str, Any]] = Field(default_factory=list)
    memory_context: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None

    class Config:
        populate_by_name = True

    def to_dict(self) -> dict:
        """Serialize to plain dictionary for API response."""
        return self.model_dump()
