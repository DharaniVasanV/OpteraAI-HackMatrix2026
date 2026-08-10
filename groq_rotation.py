"""
E:/AgentOS/groq_rotation.py

Shared Groq API Key Rotation utility for all AgentOS agents.
Reads all 6 GROQ_API_KEY* values from the central .env and rotates
automatically when any key hits rate limits or is decommissioned.
"""

import os
import asyncio
from typing import List, Optional
from dotenv import load_dotenv

# Load central .env
load_dotenv(r"E:\AgentOS\.env", override=False)


def get_all_groq_keys() -> List[str]:
    """Returns a deduplicated list of all valid GROQ_API_KEY values from env."""
    env_names = [
        "GROQ_API_KEY",
        "GROQ_API_KEY2",
        "GROQ_API_KEY3",
        "GROQ_API_KEY4",
        "GROQ_API_KEY5",
        "GROQ_API_KEY6",
    ]
    keys = []
    seen = set()
    for name in env_names:
        val = os.getenv(name, "").strip()
        if val and "your_" not in val and val not in seen:
            keys.append(val)
            seen.add(val)
    return keys


GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.3-70b-specdec",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "gemma2-9b-it",
]


async def groq_chat_with_rotation(
    messages: list,
    model: Optional[str] = None,
    response_format: Optional[dict] = None,
    temperature: float = 0.1,
    max_tokens: int = 2000,
) -> str:
    """
    Calls Groq chat completions with automatic key and model rotation.
    Returns the string content on success, raises RuntimeError on total failure.
    """
    from groq import AsyncGroq

    keys = get_all_groq_keys()
    models = [model] + GROQ_MODELS if model else GROQ_MODELS
    models = list(dict.fromkeys(models))  # deduplicate

    if not keys:
        raise RuntimeError("No valid GROQ_API_KEY values found in E:/AgentOS/.env")

    last_exc = None
    for key in keys:
        client = AsyncGroq(api_key=key)
        for m in models:
            try:
                kwargs = dict(
                    model=m,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                if response_format:
                    kwargs["response_format"] = response_format
                resp = await client.chat.completions.create(**kwargs)
                content = resp.choices[0].message.content
                if content:
                    return content.strip()
            except Exception as exc:
                err = str(exc)
                last_exc = exc
                # If rate limited on this key, break to next key immediately
                if "rate_limit" in err.lower() or "429" in err:
                    break
                # If model decommissioned, try next model on same key
                if "model_decommissioned" in err.lower() or "model not found" in err.lower():
                    continue
                # Other errors — try next model
                continue

    raise RuntimeError(
        f"All Groq API keys and models exhausted. Last error: {last_exc}"
    )


def groq_chat_sync(
    messages: list,
    model: Optional[str] = None,
    response_format: Optional[dict] = None,
    temperature: float = 0.1,
    max_tokens: int = 2000,
) -> str:
    """Sync wrapper for groq_chat_with_rotation."""
    from groq import Groq

    keys = get_all_groq_keys()
    models = [model] + GROQ_MODELS if model else GROQ_MODELS
    models = list(dict.fromkeys(models))

    if not keys:
        raise RuntimeError("No valid GROQ_API_KEY values found in E:/AgentOS/.env")

    last_exc = None
    for key in keys:
        client = Groq(api_key=key)
        for m in models:
            try:
                kwargs = dict(
                    model=m,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                if response_format:
                    kwargs["response_format"] = response_format
                resp = client.chat.completions.create(**kwargs)
                content = resp.choices[0].message.content
                if content:
                    return content.strip()
            except Exception as exc:
                err = str(exc)
                last_exc = exc
                if "rate_limit" in err.lower() or "429" in err:
                    break
                if "model_decommissioned" in err.lower() or "model not found" in err.lower():
                    continue
                continue

    raise RuntimeError(
        f"All Groq API keys and models exhausted. Last error: {last_exc}"
    )
