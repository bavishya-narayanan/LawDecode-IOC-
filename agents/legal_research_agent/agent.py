"""Legal Research Agent (Agent 2) — Phase 3 Implementation.

Responsibility:
    Receives Agent 1's structured legal understanding and uses Gemini
    to identify relevant legal areas, applicable provisions, principles,
    ambiguities, and points for Agent 3 (Legal Analysis) to focus on.

    Does NOT use any external datasets, RAG, or vector DB.
    Pure Gemini-powered research based on Agent 1's structured output.

Folder: agents/legal_research_agent/
"""

import json
import re
import warnings
from typing import Optional

from core.config import settings
from agents.legal_research_agent.models import LegalResearchResult
from agents.legal_research_agent.prompts import SYSTEM_PROMPT, build_user_message


class LegalResearchAgent:
    """Agent 2: Identifies applicable legal areas, provisions, and principles
    from Agent 1's structured understanding, then flags key points for Agent 3."""

    NAME: str = "Legal Research Agent"
    ROLE: str = "Identifies relevant legal areas, applicable provisions, principles, and open issues."
    PHASE: str = "Phase 3 — Active"

    def __init__(self):
        self.status = "Active"
        self._gemini_client = None
        self._gemini_key = None

    # -------------------------------------------------------------------------
    # Public interface
    # -------------------------------------------------------------------------

    def get_info(self) -> dict:
        """Returns agent metadata and operational status."""
        return {
            "name": self.NAME,
            "role": self.ROLE,
            "status": self.status,
            "phase": self.PHASE,
            "capabilities": [
                "Relevant legal area identification",
                "Applicable provision & statute mapping",
                "Legal principle extraction",
                "Important consideration flagging",
                "Ambiguity & conflict detection",
                "Points-for-analysis forwarding to Agent 3",
                "Research summary generation",
            ],
            "is_active": True,
        }

    def process(
        self,
        agent1_output: dict,
        model_name: Optional[str] = None,
    ) -> LegalResearchResult:
        """Execute Agent 2: research the legal matter based on Agent 1's output.

        Args:
            agent1_output: The dict produced by Agent 1's LegalUnderstandingResult.to_dict().
            model_name:    Optional Gemini model override.

        Returns:
            LegalResearchResult with populated fields or an error state.
        """
        settings.refresh()

        main_issue = agent1_output.get("main_issue", "").strip()
        agent1_status = agent1_output.get("status", "")

        # ------------------------------------------------------------------
        # Guard: only run if Agent 1 succeeded
        # ------------------------------------------------------------------
        if agent1_status != "Success" or not main_issue:
            result = LegalResearchResult(
                status="Skipped",
                main_issue_received=main_issue or "(none)",
                error=(
                    "Agent 2 skipped: Agent 1 did not produce a valid result. "
                    "Please fix the upstream error first."
                ),
            )
            self._print_terminal(result)
            return result

        target_model = model_name or settings.DEFAULT_MODEL

        # ------------------------------------------------------------------
        # API key check
        # ------------------------------------------------------------------
        if not settings.is_api_key_configured:
            result = LegalResearchResult(
                status="Error",
                main_issue_received=main_issue,
                error=(
                    f"{settings.provider.upper()}_API_KEY is not configured. "
                    f"Please create a .env file with your {settings.provider.upper()}_API_KEY."
                ),
            )
            self._print_terminal(result)
            return result

        # ------------------------------------------------------------------
        # Call Gemini
        # ------------------------------------------------------------------
        try:
            raw_json = self._call_model(agent1_output, target_model)
        except Exception as exc:
            err_msg = self._format_error(exc)
            result = LegalResearchResult(
                status="Error",
                main_issue_received=main_issue,
                error=err_msg,
            )
            self._print_terminal(result)
            return result

        # ------------------------------------------------------------------
        # Parse JSON response
        # ------------------------------------------------------------------
        try:
            parsed = self._parse_response(raw_json)
        except Exception as parse_exc:
            result = LegalResearchResult(
                status="Error",
                main_issue_received=main_issue,
                error=f"Failed to parse Gemini response as structured JSON: {str(parse_exc)[:200]}",
            )
            self._print_terminal(result)
            return result

        # ------------------------------------------------------------------
        # Build successful result
        # ------------------------------------------------------------------
        result = LegalResearchResult(
            status="Success",
            main_issue_received=main_issue,
            legal_areas=self._to_list(parsed.get("legal_areas", [])),
            applicable_provisions=self._to_list(parsed.get("applicable_provisions", [])),
            legal_principles=self._to_list(parsed.get("legal_principles", [])),
            important_considerations=self._to_list(parsed.get("important_considerations", [])),
            ambiguities_and_conflicts=self._to_list(parsed.get("ambiguities_and_conflicts", [])),
            points_for_agent3=self._to_list(parsed.get("points_for_agent3", [])),
            research_summary=parsed.get("research_summary", ""),
            error=None,
        )
        self._print_terminal(result)
        return result

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _call_model(self, agent1_output: dict, model_name: str) -> str:
        """Make a structured Gemini request."""
        warnings.filterwarnings("ignore")

        user_message = build_user_message(agent1_output)
        full_prompt = f"{SYSTEM_PROMPT}\n\n{user_message}"

        from google import genai

        if self._gemini_client is None or self._gemini_key != settings.GEMINI_API_KEY:
            self._gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
            self._gemini_key = settings.GEMINI_API_KEY
        candidates = [model_name]
        for fallback in ("gemini-3.5-flash-lite", "gemini-2.5-flash"):
            if fallback not in candidates:
                candidates.append(fallback)
        last_error = None
        for candidate in candidates:
            try:
                response = self._gemini_client.models.generate_content(
                    model=candidate,
                    contents=full_prompt,
                )
                if response and response.text:
                    return response.text.strip()
                last_error = RuntimeError("Gemini returned an empty response.")
            except Exception as exc:
                last_error = exc
                if any(marker in str(exc) for marker in ("API_KEY_INVALID", "API key not valid", "PERMISSION_DENIED")):
                    raise
        raise last_error or RuntimeError("Gemini returned an empty response.")

    def _parse_response(self, raw_text: str) -> dict:
        """Extract and parse JSON from Gemini's response."""
        text = raw_text.strip()
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if fence_match:
            text = fence_match.group(1).strip()
        brace_match = re.search(r"\{[\s\S]*\}", text)
        if brace_match:
            text = brace_match.group(0)
        return json.loads(text)

    @staticmethod
    def _to_list(value) -> list:
        """Safely coerce a value to list."""
        if isinstance(value, list):
            return [str(item).strip() for item in value if item]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []

    @staticmethod
    def _format_error(exc: Exception) -> str:
        """Return a clean, user-friendly Gemini error message."""
        raw = str(exc)
        if "API_KEY_INVALID" in raw or "API key not valid" in raw:
            return "Gemini API rejected the configured GEMINI_API_KEY."
        if "429" in raw or "RESOURCE_EXHAUSTED" in raw:
            return f"Gemini API quota or rate limit reached: {raw[:300]}"
        return f"Gemini API error: {raw[:300]}"

    def _print_terminal(self, result: LegalResearchResult) -> None:
        """Print the structured Agent 2 result in the terminal."""

        def _fmt_list(items: list, fallback: str = "None identified") -> str:
            if not items:
                return f"  - {fallback}"
            return "\n".join(f"  - {item}" for item in items)

        if result.status in ("Error", "Skipped"):
            block = f"""
==================================================
AGENT 2 — LEGAL RESEARCH
=========================

STATUS: {result.status}
ERROR:  {result.error}

MAIN ISSUE RECEIVED:
  {result.main_issue_received}
==================================================
"""
        else:
            block = f"""
==================================================
AGENT 2 — LEGAL RESEARCH
=========================

STATUS: {result.status}

LEGAL AREAS:
{_fmt_list(result.legal_areas)}

APPLICABLE PROVISIONS:
{_fmt_list(result.applicable_provisions)}

LEGAL PRINCIPLES:
{_fmt_list(result.legal_principles)}

IMPORTANT CONSIDERATIONS:
{_fmt_list(result.important_considerations)}

AMBIGUITIES & CONFLICTS:
{_fmt_list(result.ambiguities_and_conflicts, "None identified")}

POINTS FOR AGENT 3:
{_fmt_list(result.points_for_agent3)}

RESEARCH SUMMARY:
  {result.research_summary}
==================================================
"""
        print(block, flush=True)
