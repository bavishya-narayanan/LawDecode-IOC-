"""Structured output model for the Legal Analysis Agent (Agent 3)."""

from typing import Optional

from pydantic import BaseModel


class LegalAnalysisResult(BaseModel):
    """Final legal analysis synthesized from the user query and Agents 1 and 2."""

    agent_name: str = "Legal Analysis Agent"
    status: str = "Success"
    key_legal_issue: str = ""
    legal_interpretation: str = ""
    risks_concerns: str = ""
    practical_implications: str = ""
    final_conclusion: str = ""
    disclaimer: str = (
        "This is general legal information, not legal advice. Consult a qualified "
        "lawyer for advice about your specific facts and jurisdiction."
    )
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialize the result for API and terminal output."""
        return self.model_dump()
