"""Legal Understanding Agent (Agent 1) — Phase 2 Implementation.

    Responsibility:
    Deconstruct and comprehend a legal query or clause using Gemini and local tools.
    Produces a structured, neutral legal understanding without providing a
    final legal conclusion or definitive advice.

Folder: agents/legal_understanding_agent/
"""

import json
import re
import warnings
from typing import Callable, Optional

from core.config import settings
from agents.legal_understanding_agent.models import LegalUnderstandingResult
from agents.legal_understanding_agent.prompts import SYSTEM_PROMPT, build_user_message
from tools import ToolRegistry


class LegalUnderstandingAgent:
    """Agent 1: Deconstructs and structures legal queries for further multi-agent processing."""

    NAME: str = "Legal Understanding Agent"
    ROLE: str = "Deconstructs and clarifies complex legal text, clauses, and agreements."
    PHASE: str = "Phase 2 — Active"

    def __init__(self):
        self.status = "Active"
        self._gemini_client = None
        self._gemini_key = None
        self.tool_registry = ToolRegistry()

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
                "Main legal issue extraction",
                "Key facts identification",
                "Parties involved detection",
                "Legal concepts & clause recognition",
                "Points for further analysis highlighting",
                "Concise summary generation",
            ],
            "is_active": True,
        }

    def process(
        self,
        query: str,
        model_name: Optional[str] = None,
        memory_context: Optional[list[dict]] = None,
        event_callback: Optional[Callable[[str], None]] = None,
    ) -> LegalUnderstandingResult:
        """Execute Agent 1: understand the legal query and return a structured result.

        Args:
            query: Raw legal text, clause, or question from the user.
            model_name: Optional Gemini model override.

        Returns:
            LegalUnderstandingResult with populated fields or an error state.
        """
        # Always refresh settings (supports hot .env reload without restart)
        settings.refresh()

        # --- Input validation ---
        if not query or not query.strip():
            result = LegalUnderstandingResult(
                status="Error",
                input="(empty)",
                error="Input cannot be empty. Please provide a legal text or question.",
            )
            self._print_terminal(result)
            return result

        clean_input = query.strip()
        memory_context = memory_context or []
        target_model = model_name or settings.DEFAULT_MODEL

        # --- API key validation ---
        if not settings.is_api_key_configured:
            result = LegalUnderstandingResult(
                status="Error",
                input=clean_input,
                tool_results=tool_results,
                memory_context=memory_context,
                error=(
                    f"{settings.provider.upper()}_API_KEY is not configured. "
                    f"Please create a .env file with your {settings.provider.upper()}_API_KEY."
                ),
            )
            self._print_terminal(result)
            return result

        # --- ReAct loop: observe, decide, act, observe result, continue ---
        try:
            selected_tools = self._decide_tools(clean_input, target_model, memory_context)
        except Exception:
            selected_tools = []
            self._emit(event_callback, "Tool decision unavailable; continuing without tools")

        if selected_tools:
            for tool_name in selected_tools:
                self._emit(event_callback, f"Tool selected: {tool_name}")
            tool_results = self.tool_registry.run_selected(clean_input, selected_tools)
            for tool_result in tool_results:
                self._emit(event_callback, f"Tool completed: {tool_result['tool']}")
        else:
            tool_results = []
            self._emit(event_callback, "No tool selected")

        # --- Continue with Gemini using the observed tool results ---
        try:
            raw_json = self._call_model(
                clean_input, target_model, tool_results, memory_context
            )
        except Exception as exc:
            err_msg = self._format_error(exc)
            result = LegalUnderstandingResult(
                status="Error",
                input=clean_input,
                tool_results=tool_results,
                memory_context=memory_context,
                error=err_msg,
            )
            self._print_terminal(result)
            return result

        # --- Parse JSON response ---
        try:
            parsed = self._parse_response(raw_json)
        except Exception as parse_exc:
            result = LegalUnderstandingResult(
                status="Error",
                input=clean_input,
                tool_results=tool_results,
                memory_context=memory_context,
                error=f"Failed to parse Gemini response as structured JSON: {str(parse_exc)[:200]}",
            )
            self._print_terminal(result)
            return result

        # --- Build successful result ---
        result = LegalUnderstandingResult(
            status="Success",
            input=clean_input,
            main_issue=parsed.get("main_issue", ""),
            key_facts=self._to_list(parsed.get("key_facts", [])),
            parties=self._to_list(parsed.get("parties", [])),
            legal_concepts=self._to_list(parsed.get("legal_concepts", [])),
            points_for_further_analysis=self._to_list(
                parsed.get("points_for_further_analysis", [])
            ),
            summary=parsed.get("summary", ""),
            tool_results=tool_results,
            memory_context=memory_context,
            error=None,
        )
        self._print_terminal(result)
        return result

    def _decide_tools(
        self,
        legal_input: str,
        model_name: str,
        memory_context: list[dict],
    ) -> list[str]:
        """Ask Gemini for a narrow tool decision, without exposing reasoning."""
        decision_prompt = f"""You are the tool-decision step in a legal analysis workflow.
Observe the user query and choose only tools that are necessary to answer it accurately.
Do not choose a tool merely because a legal word appears.

Available tools:
- Calculator Tool: arithmetic, percentages, totals, or numeric calculations.
- Date/Deadline Tool: date differences, durations, due dates, or deadlines.
- Legal Text Tool: extract and organize clauses when the user supplies a clause or contract text.

Return ONLY JSON in this exact shape: {{"tools": ["Calculator Tool", "Date/Deadline Tool", "Legal Text Tool"]}}
Use an empty list when no tool is necessary. Never invent tool names.

USER QUERY:
{legal_input}

RELEVANT MEMORY CONTEXT:
{json.dumps(memory_context, ensure_ascii=True)}"""
        raw = self._generate_gemini(decision_prompt, model_name)
        parsed = self._parse_response(raw)
        allowed = {
            self.tool_registry.calculator.name,
            self.tool_registry.date_deadline.name,
            self.tool_registry.legal_text.name,
        }
        selected = parsed.get("tools", [])
        if not isinstance(selected, list):
            return []
        return [name for name in selected if name in allowed]

    def _generate_gemini(self, prompt: str, model_name: str) -> str:
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
                    contents=prompt,
                )
                if response and response.text:
                    return response.text.strip()
                last_error = RuntimeError("Gemini returned an empty response.")
            except Exception as exc:
                last_error = exc
                if any(marker in str(exc) for marker in ("API_KEY_INVALID", "API key not valid", "PERMISSION_DENIED")):
                    raise
        raise last_error or RuntimeError("Gemini returned an empty response.")

    @staticmethod
    def _emit(callback: Optional[Callable[[str], None]], message: str) -> None:
        if callback:
            callback(message)

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _call_model(
        self,
        legal_input: str,
        model_name: str,
        tool_results: list[dict],
        memory_context: list[dict],
    ) -> str:
        """Make a structured Gemini request with local-tool context."""
        warnings.filterwarnings("ignore")

        user_message = build_user_message(legal_input, tool_results, memory_context)
        full_prompt = f"{SYSTEM_PROMPT}\n\n{user_message}"

        return self._generate_gemini(f"{SYSTEM_PROMPT}\n\n{user_message}", model_name)

    def _parse_response(self, raw_text: str) -> dict:
        """Extract and parse JSON from Gemini's response.

        Handles cases where the response is wrapped in markdown code fences.
        """
        text = raw_text.strip()

        # Strip markdown code fences if present (```json ... ``` or ``` ... ```)
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if fence_match:
            text = fence_match.group(1).strip()

        # Find the first {...} JSON block in case there's surrounding text
        brace_match = re.search(r"\{[\s\S]*\}", text)
        if brace_match:
            text = brace_match.group(0)

        return json.loads(text)

    @staticmethod
    def _to_list(value) -> list:
        """Safely coerce a value to list (handles string, list, None)."""
        if isinstance(value, list):
            return [str(item).strip() for item in value if item]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []

    @staticmethod
    def _format_error(exc: Exception) -> str:
        """Return a clean, user-friendly error message for common Gemini errors."""
        raw = str(exc)
        if "API_KEY_INVALID" in raw or "API key not valid" in raw:
            return "Gemini API rejected the configured GEMINI_API_KEY."
        if "429" in raw or "RESOURCE_EXHAUSTED" in raw:
            return f"Gemini API quota or rate limit reached: {raw[:300]}"
        return f"Gemini API error: {raw[:300]}"

    def _print_terminal(self, result: LegalUnderstandingResult) -> None:
        """Print the structured Agent 1 result in the required terminal format."""

        if result.tool_results:
            print("\n[AGENT 1 TOOL CONTEXT]")
            for tool_result in result.tool_results:
                print(f"[TOOL USED] {tool_result['tool']}")
                print(f"[TOOL RESULT] {json.dumps(tool_result.get('result') or tool_result.get('error'), ensure_ascii=True)}")

        def _fmt_list(items: list, fallback: str = "None identified") -> str:
            if not items:
                return f"  - {fallback}"
            return "\n".join(f"  - {item}" for item in items)

        if result.status == "Error":
            block = f"""
==================================================
AGENT 1 — LEGAL UNDERSTANDING
=============================

STATUS: {result.status}
ERROR:  {result.error}

INPUT:
  {result.input}
==================================================
"""
        else:
            block = f"""
==================================================
AGENT 1 — LEGAL UNDERSTANDING
=============================

STATUS: {result.status}

MAIN ISSUE:
  {result.main_issue}

KEY FACTS:
{_fmt_list(result.key_facts)}

PARTIES:
{_fmt_list(result.parties, "No specific parties identified")}

LEGAL CONCEPTS:
{_fmt_list(result.legal_concepts, "No specific legal concepts identified")}

POINTS FOR FURTHER ANALYSIS:
{_fmt_list(result.points_for_further_analysis)}

SUMMARY:
  {result.summary}
==================================================
"""
        print(block, flush=True)
