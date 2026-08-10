import json
import os
from typing import Dict

try:
    from google import genai
except ImportError:
    genai = None


def classify_email(email: dict) -> Dict[str, object]:
    subject = email.get("subject", "")
    body = email.get("body", "")
    text = f"Subject: {subject}\nBody: {body}"

    api_key = os.getenv("GEMINI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")

    if groq_key:
        try:
            import requests
            prompt = (
                "Analyze if the following email is a meeting invitation/event discussion, "
                "circulated form/survey/registration, or scholarship/internship/hackathon/opportunity announcement. "
                "Respond ONLY with a valid JSON object containing keys: 'is_meeting' (boolean: true ONLY if email involves a live meeting, call, webinar, or meeting link) and 'category' "
                "(string: meeting, form, scholarship, internship, job, hackathon, placement, contest, newsletter, promotional, personal, spam).\n\n"
                f"Email:\n{text}"
            )
            headers = {
                "Authorization": f"Bearer {groq_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            }
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=10)
            if res.status_code == 200:
                data = res.json()
                content = data["choices"][0]["message"]["content"].strip()
                parsed = json.loads(content)
                category = str(parsed.get("category", "Meeting" if parsed.get("is_meeting") else "Other")).title()
                
                # Normalize overlaps
                if 'Intern' in category: category = 'Internship'
                if 'Hack' in category: category = 'Hackathon'
                
                return {
                    "is_meeting": bool(parsed.get("is_meeting")),
                    "category": category,
                }
        except Exception:
            pass

    if api_key and genai:
        try:
            client = genai.Client(api_key=api_key)
            prompt = (
                "Analyze if the following email is a meeting invitation/event discussion, "
                "circulated form/survey/registration, or scholarship/internship/hackathon/opportunity announcement. "
                "Respond ONLY with a valid JSON object containing keys: 'is_meeting' (boolean: true ONLY if email involves a live meeting, call, webinar, or meeting link) and 'category' "
                "(string: Meeting, Form, Scholarship, Internship, Job, Hackathon, Placement, Contest, Newsletter, Promotional, Personal, Spam).\n\n"
                f"Email:\n{text}"
            ) 
            gemini_models = ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-3.5-flash", "gemini-1.5-flash"]
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
                parsed = json.loads(content)
                category = str(parsed.get("category", "Meeting" if parsed.get("is_meeting") else "Other")).title()
                
                # Normalize overlaps
                if 'Intern' in category: category = 'Internship'
                if 'Hack' in category: category = 'Hackathon'
                
                return {
                    "is_meeting": bool(parsed.get("is_meeting")),
                    "category": category,
                }
        except Exception:
            pass

    # Heuristic Fallback
    text_lower = text.lower()
    meeting_keywords = [
        "meeting", "zoom", "google meet", "teams meeting", "webex", "skype call",
        "webinar", "huddle", "sync", "standup", "conference call", "video call",
        "join meeting", "calendar invite", "sprint kickoff", "interview"
    ]
    scholarship_keywords = ["scholarship", "fellowship", "grant", "bursary", "financial aid"]
    internship_keywords = ["internship", "intern", "co-op", "summer analyst", "on-campus placement", "hiring"]
    job_keywords = ["job", "full-time", "offer", "hiring", "open role", "vacancy"]
    hackathon_keywords = ["hackathon", "hack", "codeathon", "icpc", "coding competition", "buildathon"]
    form_keywords = ["google form", "ms form", "survey", "rsvp", "registration form", "feedback form", "fill out"]
    
    has_video_meeting_url = any(domain in text_lower for domain in [
        "meet.google.com", "zoom.us", "teams.microsoft.com", "teams.live.com", "webex.com", "join.skype.com", "gotomeet.me", "whereby.com", "meet.jit.si"
    ])
    
    is_meeting = has_video_meeting_url or any(kw in text_lower for kw in meeting_keywords)
    is_scholarship = any(kw in text_lower for kw in scholarship_keywords)
    is_internship = any(kw in text_lower for kw in internship_keywords)
    is_job = any(kw in text_lower for kw in job_keywords)
    is_hackathon = any(kw in text_lower for kw in hackathon_keywords)
    is_form = any(kw in text_lower for kw in form_keywords) or any(domain in text_lower for domain in ["forms.gle", "forms.office.com", "typeform.com", "jotform.com"])
    
    if is_meeting:
        category = "Meeting"
    elif is_hackathon:
        category = "Hackathon"
    elif is_internship:
        category = "Internship"
    elif is_scholarship:
        category = "Scholarship"
    elif is_job:
        category = "Job"
    elif is_form:
        category = "Form"
    else:
        category = "Other"

    return {
        "is_meeting": is_meeting,
        "category": category
    }
