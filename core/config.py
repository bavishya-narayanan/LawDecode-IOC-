"""LAWDECODE Configuration.

Loads environment variables from .env file portably without any hardcoded secrets
or machine-specific paths.
"""

from pathlib import Path
from typing import Optional
import os
from dotenv import load_dotenv

# Base directory of the repository (portable across any OS)
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env if it exists in the project root
ENV_FILE = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_FILE, override=True)


class Settings:
    """Application settings and environment validation."""

    PROJECT_NAME: str = "LAWDECODE"
    PROJECT_VERSION: str = "0.1.0 (Phase 1)"
    DESCRIPTION: str = "Legal document analysis and assistive intelligence platform"

    # Server settings
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))

    # LLM configuration
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", "").strip() or None
    AI_PROVIDER: str = "gemini"
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1").strip()
    DEFAULT_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()

    @property
    def provider(self) -> str:
        """Return the configured provider used by the active pipeline."""
        return "gemini"

    @property
    def api_key(self) -> Optional[str]:
        """Return the active provider's API key."""
        return self.GEMINI_API_KEY

    @property
    def is_api_key_configured(self) -> bool:
        """Check if the active provider key is present and not a placeholder."""
        if not self.api_key:
            return False
        placeholders = {
            "your_gemini_api_key_here",
            "your_key",
            "your_key_here",
            "insert_key_here",
            "xxx",
        }
        return self.api_key.lower() not in placeholders

    @property
    def api_key_status(self) -> str:
        """Safe human-readable status string without exposing the key."""
        if self.is_api_key_configured:
            return "Configured"
        return f"Missing (Please create .env with {self.provider.upper()}_API_KEY)"

    def refresh(self):
        """Reload configuration from disk."""
        load_dotenv(dotenv_path=ENV_FILE, override=True)
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip() or None
        self.AI_PROVIDER = "gemini"
        model_variable = "GEMINI_MODEL"
        default_model = "gemini-3.5-flash-lite"
        self.OLLAMA_BASE_URL = os.getenv(
            "OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1"
        ).strip()
        self.DEFAULT_MODEL = os.getenv(model_variable, default_model).strip()


settings = Settings()
