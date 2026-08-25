import json
import os
import re
from typing import Dict
from app.agents.meeting_validator import extract_meeting_link

try:
    from google import genai
except ImportError:
    genai = None


def extract_meeting(email: dict) -> Dict[str, object]:
    subject = email.get("subject")
    body = email.get("body", "")
    sender = email.get("sender")
    email_id = email.get("id")
    full_text = f"Subject: {subject or ''}\nSender: {sender or ''}\nBody: {body or ''}"

    link_fallback, platform_fallback = extract_meeting_link(full_text)

    api_key = os.getenv("GEMINI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")

    if groq_key:
        try:
            import requests
            prompt = (
                "Extract structured meeting or opportunity details from this email. "
                "Set 'meeting_link' ONLY IF a video meeting link (Google Meet, Zoom, Teams, Webex, Skype) is present; otherwise set 'meeting_link' to null. "
                "If a detail is not present in the email, set its value to null. "
                "Return ONLY a JSON object with keys: "
                "'title' (string or null), 'description' (string or null), 'organizer' (string or null), "
                "'platform' (string or null), 'meeting_link' (string or null), 'date' (YYYY-MM-DD or null), "
                "'start_time' (HH:MM or null), 'end_time' (HH:MM or null), "
                "'time_zone' (string or null), 'status' ('scheduled', 'updated', or 'cancelled').\n\n"
                f"Email Content:\n{full_text}"
            )
            headers = {
                "Authorization": f"Bearer {groq_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "openai/gpt-oss-120b",
                "messages": [
                    {"role": "system", "content": "You are a precise data extractor."},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"}
            }
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=10)
            if res.status_code == 200:
                data = res.json()
                content = data["choices"][0]["message"]["content"].strip()
                extracted_data = json.loads(content)
                extracted_data["email_id"] = email_id
                
                # Filter out non-video meeting URLs from meeting_link
                from app.agents.meeting_validator import is_video_meeting_url
                if extracted_data.get("meeting_link") and not is_video_meeting_url(extracted_data["meeting_link"]):
                    extracted_data["meeting_link"] = None

                if not extracted_data.get("meeting_link") and link_fallback:
                    extracted_data["meeting_link"] = link_fallback
                return extracted_data
        except Exception:
            pass

    if api_key and genai:
        try:
            client = genai.Client(api_key=api_key)
            prompt = (
                "Extract structured meeting or opportunity details from this email. "
                "Set 'meeting_link' ONLY IF a video meeting link (Google Meet, Zoom, Teams, Webex, Skype) is present; otherwise set 'meeting_link' to null. "
                "If a detail is not present in the email, set its value to null. "
                "Return ONLY a JSON object with keys: "
                "'title' (string or null), 'description' (string or null), 'organizer' (string or null), "
                "'platform' (string or null), 'meeting_link' (string or null), 'date' (YYYY-MM-DD or null), "
                "'start_time' (HH:MM or null), 'end_time' (HH:MM or null), "
                "'time_zone' (string or null), 'status' ('scheduled', 'updated', or 'cancelled').\n\n"
                f"Email Content:\n{full_text}"
            )
            gemini_models = ["gemini-1.5-flash", "gemini-2.5-flash", "gemini-2.0-flash"]
            content = None
            for model_name in gemini_models:
                try:
                    response = client.models.generate_content(model=model_name, contents=prompt)
                    content = response.text.strip()
                    break
                except Exception as model_exc:
                    exc_str = str(model_exc).lower()
                    if "not found" in exc_str or "not_found" in exc_str or "404" in exc_str or "403" in exc_str:
                        continue
                    continue

            if content:
                if content.startswith("```json"):
                    content = content[7:-3].strip()
                data = json.loads(content)
                data["email_id"] = email_id
                
                from app.agents.meeting_validator import is_video_meeting_url
                if data.get("meeting_link") and not is_video_meeting_url(data["meeting_link"]):
                    data["meeting_link"] = None

                if not data.get("meeting_link") and link_fallback:
                    data["meeting_link"] = link_fallback
                return data
        except Exception:
            pass

    # Heuristic Regex Extraction (Strict, No Hardcoded Mock Data)
    is_scholarship = any(kw in full_text.lower() for kw in ["scholarship", "fellowship", "grant", "bursary", "financial aid"])
    platform = platform_fallback
    if is_scholarship and (not platform or platform == "Google Forms"):
        platform = "Scholarship"

    # Date regex
    date_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", full_text)
    meeting_date = date_match.group(1) if date_match else None

    # Time regex
    time_matches = re.findall(r"\b(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)\b", full_text)
    start_time = time_matches[0] if time_matches else None
    end_time = time_matches[1] if len(time_matches) > 1 else None

    # Time zone regex
    tz_match = re.search(r"\b(UTC|GMT|EST|PST|CST|IST|EDT|PDT)\b", full_text)
    time_zone = tz_match.group(1) if tz_match else None

    # Status regex
    status = "cancelled" if subject and any(w in subject.lower() for w in ["cancel", "cancelled", "canceled"]) else "scheduled"

    return {
        "email_id": email_id,
        "title": subject or "Untitled Meeting",
        "description": body[:300] if body else None,
        "organizer": sender,
        "platform": platform,
        "meeting_link": link_fallback,
        "date": meeting_date,
        "start_time": start_time,
        "end_time": end_time,
        "time_zone": time_zone,
        "status": status,
    }
