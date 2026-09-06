"""Legal Research Agent — Pydantic Output Models (Phase 3).

Defines the structured result returned by Agent 2 after researching
the legal matter identified by Agent 1.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class LegalResearchResult(BaseModel):
    """Structured output schema for the Legal Research Agent."""

    agent_name: str = "Legal Research Agent"
    status: str = "Success"

    # Input context received from Agent 1
    main_issue_received: str = ""

    # Agent 2 research outputs
    legal_areas: List[str] = Field(
        default_factory=list,
        description="Broad areas of law relevant to this matter.",
    )
    applicable_provisions: List[str] = Field(
        default_factory=list,
        description="Potentially applicable statutes, clauses, or regulatory provisions.",
    )
    legal_principles: List[str] = Field(
        default_factory=list,
        description="General legal doctrines and principles that apply.",
    )
    important_considerations: List[str] = Field(
        default_factory=list,
        description="Practical, procedural, or jurisdictional considerations.",
    )
    ambiguities_and_conflicts: List[str] = Field(
        default_factory=list,
        description="Legal ambiguities, conflicts, or unsettled points identified.",
    )
    points_for_agent3: List[str] = Field(
        default_factory=list,
        description="Specific issues Agent 3 (Analysis) should focus on.",
    )
    research_summary: str = Field(
        default="",
        description="Concise 2-4 sentence summary of the legal research findings.",
    )

    error: Optional[str] = None

    class Config:
        populate_by_name = True

    def to_dict(self) -> dict:
        """Serialize to plain dictionary for API response."""
        return self.model_dump()
