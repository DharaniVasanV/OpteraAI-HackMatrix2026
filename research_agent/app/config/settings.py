"""
app/config/settings.py

Settings for Research Agent loading API keys from E:\meeting-agent\.env.
"""

import os
from functools import lru_cache
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Search for .env in AgentOS hierarchy
def _find_env() -> str:
    candidates = [
        r"E:\AgentOS\.env",
        r"e:\AgentOS\.env",
        os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"),
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".env"),
        r"e:\meeting-agent\.env",  # legacy fallback
    ]
    for p in candidates:
        p = os.path.normpath(p)
        if os.path.exists(p):
            return p
    return r"E:\AgentOS\.env"

ENV_PATH = _find_env()
load_dotenv(ENV_PATH, override=True)


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:vasan5707@localhost:5432/meeting_agent_new"
    GROQ_API_KEY: str = ""
    GROQ_API_KEY2: str = ""
    GROQ_API_KEY3: str = ""
    GROQ_API_KEY4: str = ""
    GROQ_API_KEY5: str = ""
    GROQ_API_KEY6: str = ""
    GROQ_API_BASE: str = "https://api.groq.com/openai/v1"
    GROQ_CHAT_MODEL: str = "llama-3.3-70b-versatile"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=ENV_PATH, env_file_encoding="utf-8", extra="ignore")

    @property
    def all_groq_keys(self) -> list[str]:
        """Return all available Groq keys to allow fallback on rate limit."""
        raw_keys = [
            self.GROQ_API_KEY2, self.GROQ_API_KEY3, self.GROQ_API_KEY4,
            self.GROQ_API_KEY5, self.GROQ_API_KEY6, self.GROQ_API_KEY,
        ]
        # read from env too
        for name in ["GROQ_API_KEY2","GROQ_API_KEY3","GROQ_API_KEY4","GROQ_API_KEY5","GROQ_API_KEY6","GROQ_API_KEY"]:
            raw_keys.append(os.getenv(name, ""))
        
        valid_keys = []
        for k in raw_keys:
            if k and k.strip().startswith("gsk_") and k.strip() not in valid_keys:
                valid_keys.append(k.strip())
        return valid_keys


@lru_cache
def get_settings() -> Settings:
    return Settings()
