"""
app/services/whisper_service.py

Transcribes recorded audio using Groq Whisper API (whisper-large-v3-turbo)
with automatic key rotation across all 6 GROQ_API_KEY* keys when rate limits hit.
Persists the transcript into the DB via crud.py.
"""

import os
import uuid
import time
from groq import Groq
from groq import RateLimitError, AuthenticationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.db import crud
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Key rotation helpers
# ---------------------------------------------------------------------------

def _get_all_groq_clients() -> list[tuple[str, Groq]]:
    """Return a list of (key_label, Groq client) for every non-empty key."""
    return [
        (f"GROQ_API_KEY{'' if i == 0 else i + 1}", Groq(api_key=k))
        for i, k in enumerate(settings.all_groq_keys())
    ]


def _groq_whisper_with_rotation(audio_path: str) -> str:
    """
    Attempt Groq Whisper transcription, rotating through all available API keys
    on RateLimitError (429) or AuthenticationError (401).
    Returns the raw transcript text, or raises if all keys are exhausted.
    """
    clients = _get_all_groq_clients()
    if not clients:
        raise RuntimeError("No GROQ API keys are configured in E:\\AgentOS\\.env")

    filename = os.path.basename(audio_path)
    last_error = None

    for label, client in clients:
        try:
            logger.info("Trying Whisper transcription with %s ...", label)
            with open(audio_path, "rb") as audio_file:
                res = client.audio.transcriptions.create(
                    file=(filename, audio_file.read()),
                    model="whisper-large-v3-turbo",
                    response_format="text",
                    language="en",
                )
            raw_text = str(res).strip()
            logger.info("Whisper success with %s (%d chars).", label, len(raw_text))
            return raw_text

        except RateLimitError as e:
            logger.warning("%s hit rate limit — rotating to next key. (%s)", label, e)
            last_error = e
            time.sleep(0.5)   # brief pause before trying next key
            continue

        except AuthenticationError as e:
            logger.warning("%s has invalid/expired key — rotating. (%s)", label, e)
            last_error = e
            continue

        except Exception as e:
            logger.warning("Whisper error with %s: %s", label, e)
            last_error = e
            # For non-rate-limit errors, raise immediately — rotation won't help
            raise

    raise RuntimeError(
        f"All {len(clients)} Groq API keys exhausted or invalid. Last error: {last_error}"
    )


def _groq_chat_with_rotation(prompt: str, max_tokens: int = 3000) -> str:
    """
    Call Groq chat completion with key rotation on rate limit / auth errors.
    """
    clients = _get_all_groq_clients()
    if not clients:
        raise RuntimeError("No GROQ API keys configured.")

    last_error = None
    for label, client in clients:
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=max_tokens,
            )
            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content.strip()
        except RateLimitError as e:
            logger.warning("%s rate limit on chat — rotating. (%s)", label, e)
            last_error = e
            time.sleep(0.5)
            continue
        except AuthenticationError as e:
            logger.warning("%s invalid key on chat — rotating. (%s)", label, e)
            last_error = e
            continue
        except Exception as e:
            last_error = e
            raise

    raise RuntimeError(f"All Groq keys exhausted for chat. Last error: {last_error}")


# ---------------------------------------------------------------------------
# Transcript formatting
# ---------------------------------------------------------------------------

def _format_as_dialogue(raw_transcript: str, organizer: str = "", meeting_title: str = "") -> str:
    """Uses LLM to convert raw Whisper output into a named speaker dialogue script."""
    if not raw_transcript or len(raw_transcript.strip()) < 10:
        return raw_transcript

    meta_info = ""
    if organizer:
        meta_info += f"Meeting Organizer / Host Name: {organizer}\n"
    if meeting_title:
        meta_info += f"Meeting Title: {meeting_title}\n"

    prompt = (
        "You are an expert meeting transcript editor and name resolution assistant.\n"
        "Convert the following raw audio transcription into a clean, accurate dialogue script with actual person names.\n\n"
        f"{meta_info}"
        "CRITICAL INSTRUCTIONS FOR SPEAKER IDENTIFICATION:\n"
        "1. DO NOT use generic placeholders like 'Speaker 1', 'Speaker 2', 'Speaker A', or 'Speaker B'. "
        "You MUST assign actual person names or specific descriptive roles (e.g. 'Dharani Vasan', 'Mahesh', 'Interviewer', 'Recruiter', 'HR').\n"
        "2. Carefully analyze the context, greetings, introductions, salutations, and addressed names in the conversation.\n"
        "3. Format each spoken line strictly as 'Person Name: Dialogue text'\n"
        "   Example Output:\n"
        "   Recruiter: Hello Mr. Dhanivasan, we would like to inform you that you have been selected...\n"
        "   Mahesh: The technical round will start on 13th July...\n"
        "4. Do NOT add any preamble, markdown formatting, or commentary. Output ONLY the clean speaker dialogue lines.\n\n"
        f"Raw Transcript:\n{raw_transcript}"
    )

    try:
        return _groq_chat_with_rotation(prompt, max_tokens=3000)
    except Exception as e:
        logger.warning("Failed to format transcript into dialogue: %s", e)
        return raw_transcript


def reformat_transcript_text(raw_or_existing_transcript: str, organizer: str = "", meeting_title: str = "") -> str:
    """Public utility to re-format any existing transcript using Groq LLM name resolution."""
    return _format_as_dialogue(raw_or_existing_transcript, organizer=organizer, meeting_title=meeting_title)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def transcribe_and_store(
    session: AsyncSession,
    meeting_id: uuid.UUID,
    audio_path: str = "",
) -> str:
    transcript_text = ""
    language = "en"

    meeting = await crud.get_meeting(session, meeting_id)
    organizer = meeting.organizer if meeting and meeting.organizer else ""
    meeting_title = meeting.title if meeting and meeting.title else ""

    if audio_path and os.path.exists(audio_path):
        try:
            logger.info("Transcribing audio: %s", audio_path)
            raw_text = _groq_whisper_with_rotation(audio_path)

            # Format into named speaker dialogue
            transcript_text = _format_as_dialogue(raw_text, organizer=organizer, meeting_title=meeting_title)
            logger.info("Transcription complete (%d chars).", len(transcript_text))

        except Exception as e:
            logger.warning("Groq Whisper transcription failed: %s", e)
    else:
        logger.warning("No audio file found at path: %s", audio_path)

    if not transcript_text:
        logger.warning("Empty transcript for meeting %s", meeting_id)

    await crud.save_transcript(session, meeting_id, transcript_text, language)
    return transcript_text