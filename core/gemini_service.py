"""Gemini API Service for LAWDECODE.

Handles calling the Google Gemini API cleanly, validating environment credentials,
formatting required terminal output, and providing clear error guidance when the
API key is not configured.
"""

from typing import Dict, Any, Optional
import sys
from core.config import settings


class GeminiService:
    """Service to interface with Google Gemini API."""

    def __init__(self):
        self.settings = settings

    def print_terminal_output(
        self,
        api_status: str,
        test_input: str,
        gemini_response: str
    ) -> None:
        """Prints the required formatted LAWDECODE terminal block."""
        terminal_block = f"""
==================================================
LAWDECODE
=========

Gemini API Status:
{api_status}

Test Input:
{test_input}

Gemini Response:
{gemini_response}
==================================================
"""
        print(terminal_block, flush=True)

    def generate_response(self, prompt: str, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Generates a text response from Gemini API for a given test prompt.

        Args:
            prompt: The user legal query or test input.
            model_name: Optional Gemini model name override.

        Returns:
            Dictionary containing success status, response text, model used,
            and any error message.
        """
        # Always refresh settings to pick up newly created .env without server restart
        self.settings.refresh()
        
        target_model = model_name or self.settings.DEFAULT_MODEL
        clean_input = prompt.strip() if prompt else "(Empty input)"

        # Check if API key is present and configured
        if not self.settings.is_api_key_configured:
            status_msg = "Error: GEMINI_API_KEY is missing or unconfigured."
            error_details = (
                "Gemini API key is not configured. "
                "Please create a '.env' file in the project root and add your API key:\n"
                "GEMINI_API_KEY=your_gemini_api_key_here\n"
                "(Refer to .env.example for template)"
            )
            self.print_terminal_output(
                api_status=status_msg,
                test_input=clean_input,
                gemini_response=f"Unable to query Gemini. {error_details}"
            )
            return {
                "success": False,
                "error": error_details,
                "api_key_configured": False,
                "response": None,
                "model": target_model,
                "status": "API Key Missing"
            }

        api_key = self.settings.GEMINI_API_KEY
        response_text = ""
        used_model = target_model
        error_msg = None

        # Attempt call via modern google-genai SDK first
        try:
            import warnings
            warnings.filterwarnings("ignore")
            from google import genai
            try:
                from google.genai.models import Models
                Models._logged_afc_warning = True
            except Exception:
                pass
            
            client = genai.Client(api_key=api_key)
            
            system_instruction = (
                "You are LAWDECODE AI, an intelligent legal assistant. "
                "Provide a clear, well-structured, professional, and accessible legal analysis."
            )
            
            candidate_models = [target_model]
            if target_model != "gemini-1.5-flash":
                candidate_models.append("gemini-1.5-flash")

            last_exception = None
            for model_candidate in candidate_models:
                try:
                    res = client.models.generate_content(
                        model=model_candidate,
                        contents=f"{system_instruction}\n\nUser Query: {clean_input}"
                    )
                    if res and res.text:
                        response_text = res.text.strip()
                        used_model = model_candidate
                        break
                except Exception as exc:
                    last_exception = exc
                    # If it's an API key error, no need to retry models
                    err_str = str(exc)
                    if "API key not valid" in err_str or "API_KEY_INVALID" in err_str or "PERMISSION_DENIED" in err_str:
                        raise exc
                    continue

            if not response_text and last_exception:
                raise last_exception

        except Exception as primary_exc:
            raw_err = str(primary_exc)
            
            # Format friendly message for common key errors
            if "API key not valid" in raw_err or "API_KEY_INVALID" in raw_err:
                error_msg = (
                    "Google Gemini rejected the provided GEMINI_API_KEY (API key is invalid). "
                    "Please verify your API key in .env and ensure it is active in Google AI Studio."
                )
            elif "PERMISSION_DENIED" in raw_err:
                error_msg = (
                    "Permission denied by Google Gemini API. "
                    "Please check if your API key has access to the requested model."
                )
            elif "RESOURCE_EXHAUSTED" in raw_err or "429" in raw_err:
                error_msg = (
                    "Google Gemini API quota exceeded or rate limited. "
                    "Please wait a moment before trying again."
                )
            else:
                # Truncate overly long technical payloads for clean output
                error_msg = f"Gemini API Error: {raw_err[:200]}"

            self.print_terminal_output(
                api_status=f"Error: {error_msg}",
                test_input=clean_input,
                gemini_response=f"Failed to generate response: {error_msg}"
            )
            return {
                "success": False,
                "error": error_msg,
                "api_key_configured": True,
                "response": None,
                "model": target_model,
                "status": "API Call Failed"
            }

        # Successful generation
        status_msg = f"Active / Success (Model: {used_model})"
        self.print_terminal_output(
            api_status=status_msg,
            test_input=clean_input,
            gemini_response=response_text
        )

        return {
            "success": True,
            "error": None,
            "api_key_configured": True,
            "response": response_text,
            "model": used_model,
            "status": "Success"
        }


# Shared singleton service instance
gemini_service = GeminiService()
