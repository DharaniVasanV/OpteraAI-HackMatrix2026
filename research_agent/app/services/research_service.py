"""
app/services/research_service.py

Core Research Agent Service.
Uses Groq API (GROQ_API_KEY2 / llama-3.3-70b-versatile) to perform 19-step structured extraction.
"""

import json
import re
from groq import Groq

from app.config.settings import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

SYSTEM_PROMPT = """
# IDENTITY
You are the Research Agent of AgentOS.
AgentOS is a multi-agent AI productivity operating system.
You are an autonomous AI agent responsible for understanding, analyzing, organizing and extracting structured knowledge from any content provided by the user.
You work independently. You do NOT depend on any other agent.
Your responsibility is NOT to chat. Your responsibility is to produce accurate structured information.
Never fabricate facts. Never assume information. Never hallucinate. Always return structured data.

# PRIMARY RESPONSIBILITIES
Perform all 19 extraction steps:
STEP 1: Identify Content Type (Email, Meeting Transcript, Document, Certificate, Rulebook, Brochure, Notes, Unknown)
STEP 2: Generate a concise title.
STEP 3: Generate a short summary (3-6 sentences explaining what it is, what happened, important outcome).
STEP 4: Extract Key Points (max 15).
STEP 5: Extract People (Name, Role).
STEP 6: Extract Organizations.
STEP 7: Extract Technologies.
STEP 8: Extract URLs (Meeting, Registration, Website, Download, GitHub, Documentation links).
STEP 9: Extract Important Dates (Event, Date, Time, Description).
STEP 10: Extract Tasks (Task, Assigned To, Deadline, Priority, Status, Description; if missing return null).
STEP 11: Extract Decisions (Decision, Reason, Impact).
STEP 12: Extract Risks.
STEP 13: Extract Opportunities (Internship, Hackathon, Scholarship, Competition, Conference, Workshop, Certification, Meeting, Project).
STEP 14: Extract Keywords (max 30).
STEP 15: Extract Categories.
STEP 16: Detect Missing Information.
STEP 17: Generate Recommended Next Agent (choose from: Classification Agent, Priority Agent, Meeting Agent, Search Agent, Document Intelligence Agent, Resume Agent, Application Agent, Notification Agent, Calendar Agent, Learning Agent, Career Agent, Knowledge Agent, Analytics Agent, Supervisor Agent).
STEP 18: Estimate Confidence (0.0 to 1.0).
STEP 19: Estimate Sentiment (Positive, Neutral, Negative, Mixed).

# OUTPUT FORMAT
Return ONLY valid JSON matching this exact structure with NO markdown syntax, NO code blocks, and NO commentary:
{
  "content_type": "",
  "title": "",
  "summary": "",
  "key_points": [],
  "people": [
    {
      "name": "",
      "role": ""
    }
  ],
  "organizations": [],
  "technologies": [],
  "urls": [],
  "important_dates": [
    {
      "event": "",
      "date": "",
      "time": "",
      "description": ""
    }
  ],
  "tasks": [
    {
      "task": "",
      "assigned_to": null,
      "deadline": null,
      "priority": null,
      "status": null,
      "description": ""
    }
  ],
  "decisions": [
    {
      "decision": "",
      "reason": "",
      "impact": ""
    }
  ],
  "risks": [],
  "opportunities": [],
  "keywords": [],
  "categories": [],
  "missing_information": [],
  "recommended_next_agent": [],
  "sentiment": "",
  "confidence": 1.0
}

# BEHAVIOR RULES
Never invent facts, names, deadlines, people, organizations, meeting links, or URLs.
If information is unavailable, return null or empty array.
Return ONLY raw JSON object.
"""


def clean_json_response(text: str) -> dict:
    """Cleans markdown code fences and parses JSON safely."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"\n?```$", "", cleaned, flags=re.MULTILINE)
    cleaned = cleaned.strip()
    return json.loads(cleaned)


async def analyze_content(user_content: str) -> dict:
    """Analyzes raw text using Groq API (llama-3.3-70b-versatile) and returns structured JSON."""
    if not user_content or not user_content.strip():
        raise ValueError("Content to analyze cannot be empty.")

    try:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        
        from groq_rotation import groq_chat_with_rotation
        
        content = await groq_chat_with_rotation(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content[:2000]}
            ],
            model=settings.GROQ_CHAT_MODEL,
            response_format={"type": "json_object"}
        )
        
        data = clean_json_response(content)
        data["provider_used"] = "Groq API (Rotated)"
        return data

    except Exception as e:
        logger.error("[ERROR] All Groq API keys failed: %s", e)
        raise RuntimeError(f"Analysis failed: {e}")
    
    # GEMINI FALLBACK
    import os
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            from google import genai
            if genai:
                client = genai.Client(api_key=gemini_key)
                gemini_models = ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-3.5-flash", "gemini-1.5-flash"]
                for model_name in gemini_models:
                    try:
                        logger.info(f"[GEMINI API] Attempting via {model_name}...")
                        response = client.models.generate_content(
                            model=model_name,
                            contents=f"System:\n{SYSTEM_PROMPT}\n\nUser Content:\n{user_content}"
                        )
                        content = response.text.strip()
                        data = clean_json_response(content)
                        data["provider_used"] = f"Gemini API ({model_name})"
                        logger.info(f"SUCCESS: Analyzed via Gemini API ({model_name})!")
                        return data
                    except Exception as model_exc:
                        exc_str = str(model_exc).lower()
                        if "not found" in exc_str or "not_found" in exc_str or "404" in exc_str or "403" in exc_str:
                            continue
                        logger.warning(f"Model {model_name} failed: {model_exc}")
                        continue
        except Exception as e:
            logger.error("❌ Gemini Fallback failed entirely: %s", e)

    raise RuntimeError(f"All {len(api_keys)} Groq API keys rate limited/failed, and Gemini fallback failed. Last Groq error: {last_err}")
