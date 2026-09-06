"""Legal Analysis Agent (Agent 3) powered by the Gemini API."""

import json
import re
from typing import Any, Dict, Optional

from agents.legal_analysis_agent.models import LegalAnalysisResult
from agents.legal_analysis_agent.prompts import SYSTEM_PROMPT, build_user_message
from core.config import settings


class LegalAnalysisAgent:
    """Synthesizes the original query and upstream agent outputs."""

    NAME: str = "Legal Analysis Agent"
    ROLE: str = "Evaluates legal risks, detects potential liabilities, and formulates recommendations."
    PHASE: str = "Phase 4 - Active"

    def __init__(self):
        self.status = "Active"
        self._gemini_client = None
        self._gemini_key = None

    def get_info(self) -> Dict[str, Any]:
        """Returns agent metadata and operational status."""
        return {
            "name": self.NAME,
            "role": self.ROLE,
            "status": self.status,
            "phase": self.PHASE,
            "capabilities": [
                "Key legal issue synthesis",
                "Legal interpretation",
                "Risk and concern assessment",
                "Practical implications",
                "Final conclusion and disclaimer",
            ],
            "is_active": True,
        }

    def process(
        self,
        user_input: str,
        agent1_output: dict,
        agent2_output: dict,
        model_name: Optional[str] = None,
    ) -> LegalAnalysisResult:
        """Run Agent 3 using the original input and both upstream outputs."""
        settings.refresh()
        clean_input = (user_input or "").strip()

        if agent1_output.get("status") != "Success" or agent2_output.get("status") != "Success":
            result = LegalAnalysisResult(
                status="Skipped",
                error="Agent 3 skipped: Agents 1 and 2 must both succeed before final analysis.",
            )
            self._print_terminal(result)
            return result

        if not settings.is_api_key_configured:
            result = LegalAnalysisResult(
                status="Error",
                error="GEMINI_API_KEY is not configured. Add it to the project .env file.",
            )
            self._print_terminal(result)
            return result

        try:
            raw_response = self._call_model(
                clean_input,
                agent1_output,
                agent2_output,
                model_name or settings.DEFAULT_MODEL,
            )
            parsed = self._parse_response(raw_response)
            result = LegalAnalysisResult(
                status="Success",
                key_legal_issue=str(parsed.get("key_legal_issue", "")),
                legal_interpretation=str(parsed.get("legal_interpretation", "")),
                risks_concerns=str(parsed.get("risks_concerns", "")),
                practical_implications=str(parsed.get("practical_implications", "")),
                final_conclusion=str(parsed.get("final_conclusion", "")),
                disclaimer=str(parsed.get("disclaimer", LegalAnalysisResult.model_fields["disclaimer"].default)),
            )
        except Exception as exc:
            result = LegalAnalysisResult(status="Error", error=self._format_error(exc))

        self._print_terminal(result)
        return result

    def _call_model(self, user_input: str, agent1_output: dict, agent2_output: dict, model_name: str) -> str:
        user_message = build_user_message(user_input, agent1_output, agent2_output)
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
                    contents=f"{SYSTEM_PROMPT}\n\n{user_message}",
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
    def _parse_response(raw_text: str) -> dict:
        text = raw_text.strip()
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if fence_match:
            text = fence_match.group(1).strip()
        brace_match = re.search(r"\{[\s\S]*\}", text)
        if brace_match:
            text = brace_match.group(0)
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            raise ValueError("Gemini response must be a JSON object.")
        return parsed

    @staticmethod
    def _format_error(exc: Exception) -> str:
        raw = str(exc)
        status = getattr(exc, "status_code", "unknown")
        code = getattr(exc, "code", "unknown")
        if "API_KEY_INVALID" in raw or "API key not valid" in raw:
            return "Gemini API rejected the configured GEMINI_API_KEY."
        if "429" in raw or "RESOURCE_EXHAUSTED" in raw:
            return f"Gemini API quota or rate limit reached: {raw[:300]}"
        return f"Gemini API error: {raw[:300]}"

    @staticmethod
    def _print_terminal(result: LegalAnalysisResult) -> None:
        print("\n==================================================")
        print("LAWDECODE - AGENT 3")
        print("===================")
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=True))
        print("==================================================", flush=True)
