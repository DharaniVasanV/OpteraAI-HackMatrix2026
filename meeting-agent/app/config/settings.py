"""
app/config/settings.py

Single source of truth for runtime configuration.
Always loads from E:\\AgentOS\\.env (the master .env with all 6 Groq keys).
"""

import os
from functools import lru_cache
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Always prefer E:\AgentOS\.env — that is where all 6 GROQ keys live
_AGENTOS_ENV = r"E:\AgentOS\.env"
_HERE = os.path.dirname(os.path.abspath(__file__))
_MEETING_ENV = os.path.normpath(os.path.join(_HERE, "..", "..", ".env"))

# Load both — AgentOS master first so its values take priority
load_dotenv(_AGENTOS_ENV, override=True)
if os.path.exists(_MEETING_ENV) and _MEETING_ENV != _AGENTOS_ENV:
    load_dotenv(_MEETING_ENV, override=False)  # don't override keys already loaded

ENV_PATH = _AGENTOS_ENV if os.path.exists(_AGENTOS_ENV) else _MEETING_ENV


class Settings(BaseSettings):
    # --- Database -----------------------------------------------------
    DATABASE_URL: str = "postgresql+asyncpg://postgres:vasan5707@localhost:5432/meeting_agent_new"

    # --- Groq API Keys (all 6 for rotation) ---------------------------
    GROQ_API_KEY: str = ""
    GROQ_API_KEY2: str = ""
    GROQ_API_KEY3: str = ""
    GROQ_API_KEY4: str = ""
    GROQ_API_KEY5: str = ""
    GROQ_API_KEY6: str = ""
    GROQ_API_BASE: str = "https://api.groq.com/openai/v1"
    GROQ_CHAT_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_WHISPER_MODEL: str = "whisper-large-v3"

    # --- Scheduler / join behavior --------------------------------------
    CHECK_INTERVAL: int = 30
    JOIN_BEFORE_MINUTES: int = 2
    MEETING_MAX_DURATION_MINUTES: int = 180

    # --- Bot identity ----------------------------------------------------
    BOT_DISPLAY_NAME: str = "Meeting Notes Bot"

    # --- Storage ----------------------------------------------------------
    RECORDINGS_DIR: str = "/tmp/meeting-agent/recordings"

    # --- Logging ------------------------------------------------------
    LOG_LEVEL: str = "INFO"

    # --- Retry behavior -------------------------------------------------
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_SECONDS: int = 5

    model_config = SettingsConfigDict(env_file=ENV_PATH, env_file_encoding="utf-8", extra="ignore")

    def __init__(self, **data):
        super().__init__(**data)
        # Hard fallback: pull directly from os.environ if pydantic-settings missed any
        if not self.GROQ_API_KEY:
            self.GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
        if not self.GROQ_API_KEY2:
            self.GROQ_API_KEY2 = os.environ.get("GROQ_API_KEY2", "")
        if not self.GROQ_API_KEY3:
            self.GROQ_API_KEY3 = os.environ.get("GROQ_API_KEY3", "")
        if not self.GROQ_API_KEY4:
            self.GROQ_API_KEY4 = os.environ.get("GROQ_API_KEY4", "")
        if not self.GROQ_API_KEY5:
            self.GROQ_API_KEY5 = os.environ.get("GROQ_API_KEY5", "")
        if not self.GROQ_API_KEY6:
            self.GROQ_API_KEY6 = os.environ.get("GROQ_API_KEY6", "")

    def all_groq_keys(self) -> list[str]:
        """Returns all non-empty Groq API keys for rotation."""
        return [
            k for k in [
                self.GROQ_API_KEY,
                self.GROQ_API_KEY2,
                self.GROQ_API_KEY3,
                self.GROQ_API_KEY4,
                self.GROQ_API_KEY5,
                self.GROQ_API_KEY6,
            ] if k
        ]


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — import and call this, don't instantiate Settings() directly."""
    return Settings()
