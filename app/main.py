import os

def load_env_file():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip()

load_env_file()

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from app.agents.database_manager import MeetingStore
from app.agents.duplicate_detector import find_duplicate, merge_meeting
from app.agents.email_watcher import watch_inbox
from app.agents.information_extractor import extract_meeting
from app.agents.meeting_validator import validate_meeting, is_video_meeting_url
from app.agents.notification_agent import NotificationAgent
from app.gmail_oauth import run_oauth_flow
from Classification_Agent.classification_agent import ClassificationAgent
from Priority_Agent import PriorityAgent

app = FastAPI(title="AI Meeting Intelligence Agent")
store = MeetingStore()
notification_agent = NotificationAgent(store)
classification_agent = ClassificationAgent()
priority_agent = PriorityAgent()


@app.get("/", response_class=HTMLResponse)
def read_dashboard() -> str:
    template_path = os.path.join(os.path.dirname(__file__), "templates", "dashboard.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/meetings")
def list_meetings(user_email: str = None) -> list[dict]:
    return store.list_meetings(user_email=user_email)


@app.post("/meetings/manual")
def add_manual_meeting(data: dict) -> dict:
    # Run priority agent so manually-added items also get scored
    existing_meetings = store.list_meetings()
    prio_res = priority_agent.analyze_priority(
        {"subject": data.get("title", ""), "sender": data.get("organizer", ""), "body": ""},
        existing_meetings
    )
    data["priority"] = prio_res.get("priority", "Low")
    data["priority_score"] = prio_res.get("priority_score", 0)
    reasons = prio_res.get("reason_for_priority", [])
    data["priority_explanation"] = ", ".join(reasons) if isinstance(reasons, list) else str(reasons)
    data["priority_thought"] = prio_res.get("agent_thought", "")
    actions = prio_res.get("recommended_actions", [])
    data["recommended_actions"] = ", ".join(actions) if isinstance(actions, list) else str(actions)
    saved = store.add_meeting(data)
    return saved


@app.patch("/meetings/{meeting_id}")
def update_meeting(meeting_id: str, payload: dict) -> dict:
    success = store.update_meeting(meeting_id, payload)
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"status": "success"}


@app.delete("/meetings")
def clear_meetings() -> dict:
    store.clear_all_meetings()
    return {"message": "All meetings cleared successfully"}


@app.get("/notifications")
def get_notifications(user_email: str = None) -> list[dict]:
    return notification_agent.get_upcoming_notifications(user_email=user_email)


@app.get("/categories")
def get_categories() -> list[str]:
    return store.list_categories()


@app.post("/categories")
def add_category(data: dict) -> dict:
    name = data.get("name")
    if not name:
        return {"error": "Category name is required"}
    saved = store.add_category(name)
    return {"name": saved}


@app.delete("/categories/{name}")
def delete_category(name: str) -> dict:
    deleted = store.delete_category(name)
    return {"success": deleted}


@app.get("/gemini/status")
def get_gemini_status() -> dict:
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            import requests
            headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
            payload = {
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": "Hello"}]
            }
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=5)
            if res.status_code == 200:
                return {"online": True, "message": "Groq connected successfully"}
            else:
                return {"online": False, "message": f"Groq HTTP error: {res.status_code} - {res.text}"}
        except Exception as e:
            return {"online": False, "message": f"Groq check failed: {str(e)}"}

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"online": False, "message": "API Key is missing in .env"}
    try:
        from google import genai
        if not genai:
            return {"online": False, "message": "google-genai library is not installed"}
        
        client = genai.Client(api_key=api_key)
        # Verify connection with a small text call
        gemini_models = ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-3.5-flash", "gemini-1.5-flash"]
        last_error = None
        for model_name in gemini_models:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents="Hello",
                )
                if response.text:
                    return {"online": True, "message": f"Connected successfully via {model_name}"}
            except Exception as model_exc:
                last_error = model_exc
                exc_str = str(model_exc).lower()
                if "not found" in exc_str or "not_found" in exc_str or "404" in exc_str or "403" in exc_str:
                    continue
                continue
        if last_error:
            return {"online": False, "message": f"Failed checking models: {str(last_error)}"}
    except Exception as e:
        return {"online": False, "message": str(e)}
    return {"online": False, "message": "Unknown error occurred"}


# ── Integration helpers ──────────────────────────────────────────────────────

def _persist_email_inbox(email: dict):
    """Save raw email to email_inbox table for traceability."""
    try:
        from app.database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO email_inbox (id, subject, sender, body, timestamp, attachments, processed)
                VALUES (:id, :subject, :sender, :body, :ts, :att::jsonb, FALSE)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": str(email.get("id", "")),
                "subject": email.get("subject", ""),
                "sender": email.get("sender", ""),
                "body": (email.get("body", "") or "")[:50000],
                "ts": str(email.get("timestamp", "")),
                "att": str(email.get("attachments", [])).replace("'", '"'),
            })
            conn.execute(text("commit"))
    except Exception as e:
        print(f"[Watcher] email_inbox persist warning: {e}")


def _save_pipeline_event(source: str, target: str, event_type: str, payload: dict, record_id: str):
    """Log an inter-agent pipeline event."""
    try:
        import json
        from app.database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO agent_pipeline_events
                  (source_agent, target_agent, event_type, payload, status, source_record_id)
                VALUES (:src, :tgt, :etype, :payload::jsonb, 'Pending', :rid)
            """), {
                "src": source, "tgt": target, "etype": event_type,
                "payload": json.dumps(payload)[:10000],
                "rid": str(record_id),
            })
            conn.execute(text("commit"))
    except Exception as e:
        print(f"[Watcher] pipeline_event log warning: {e}")


def _call_research_agent(email_body: str, item_id: int) -> dict:
    """POST to Research Agent for structured extraction."""
    try:
        import requests
        res = requests.post(
            "http://127.0.0.1:8002/analyze",
            json={"content": email_body},
            timeout=30,
        )
        if res.status_code == 200:
            data = res.json()
            _save_pipeline_event("Watcher", "Research", "EMAIL_ANALYZED",
                                 {"watcher_item_id": item_id}, item_id)
            return data
    except Exception as e:
        print(f"[Watcher→Research] call failed: {e}")
    return {}


def _call_enrichment_agent(email: dict, category: str, item_id: int) -> dict:
    """POST to Search/Enrichment Agent for web enrichment."""
    try:
        import requests
        res = requests.post(
            "http://127.0.0.1:8003/api/enrich",
            json={
                "external_record_id": str(email.get("id", item_id)),
                "category": category.split(",")[0].strip().lower() or "general",
                "title": email.get("subject", ""),
                "description": (email.get("body", "") or "")[:8000],
                "sender": email.get("sender", ""),
                "priority": "MEDIUM",
                "missing_fields": [],
            },
            timeout=60,
        )
        if res.status_code == 200:
            data = res.json()
            _save_pipeline_event("Watcher", "Enrichment", "EMAIL_ENRICHED",
                                 {"watcher_item_id": item_id, "enrichment_id": data.get("id")}, item_id)
            return data
    except Exception as e:
        print(f"[Watcher→Enrichment] call failed: {e}")
    return {}


def _call_calendar_sync() -> dict:
    """Trigger Calendar Agent sync so it picks up new watcher_items."""
    try:
        import requests
        res = requests.post("http://127.0.0.1:8011/api/calendar/sync", timeout=30)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"[Watcher→Calendar] sync call failed: {e}")
    return {}


def _call_analytics(event_type: str, category: str, meta: dict):
    """POST a single analytics event to Analytics Agent."""
    try:
        import requests
        requests.post(
            "http://127.0.0.1:8013/api/events/single",
            json={
                "user_id": "dharanivasan",
                "event_type": event_type,
                "category": category,
                "value": 1.0,
                "metadata": meta,
                "agent_name": "Watcher",
            },
            timeout=5,
        )
    except Exception:
        pass


# ── Main Sync Endpoint ───────────────────────────────────────────────────────

@app.post("/sync")
def sync_meetings(user_email: str = None) -> list[dict]:
    emails = watch_inbox()
    processed_results = []
    processed_email_ids = set()
    calendar_needs_sync = False

    for email in emails:
        email_id = email.get("id")
        if email_id:
            if store.find_by_url_or_email(None, email_id):
                continue
            processed_email_ids.add(email_id)

        if len(processed_results) >= 50:
            break


        # ── Persist raw email to email_inbox ──────────────────────────
        _persist_email_inbox(email)

        categories = store.list_categories()
        detected_category = classification_agent.classify(email, categories)
        validation = validate_meeting(email)
        
        if detected_category != "Other" or validation["valid"]:
            extracted = extract_meeting(email)
            extracted["email_body"] = email.get("body")
            extracted["email_id"] = email_id
            extracted["user_email"] = user_email

            meeting_link = validation.get("meeting_link") or extracted.get("meeting_link")
            
            if meeting_link and is_video_meeting_url(meeting_link):
                extracted["meeting_link"] = meeting_link
                extracted["meeting_url"] = meeting_link
            else:
                if meeting_link:
                    extracted["meeting_link"] = meeting_link
                    extracted["meeting_url"] = meeting_link
                else:
                    from app.agents.meeting_validator import extract_any_actionable_link
                    actionable_link, actionable_platform = extract_any_actionable_link(email.get("body") or "")
                    if actionable_link:
                        extracted["meeting_link"] = actionable_link
                        extracted["meeting_url"] = actionable_link
                        if actionable_platform and (not extracted.get("platform") or extracted["platform"] == "Application Portal"):
                            extracted["platform"] = actionable_platform
                    else:
                        extracted["meeting_link"] = None
                        extracted["meeting_url"] = None

            is_video = validation.get("is_video_meeting", False)
            if is_video and validation.get("platform"):
                extracted["platform"] = validation["platform"]
            elif validation.get("platform") and not extracted.get("platform"):
                extracted["platform"] = validation["platform"]

            # Category handling
            cats_list = [c.strip() for c in detected_category.split(",") if c.strip()] if detected_category != "Other" else []
            
            # If "Form" is in the category list, verify if a form link exists
            if "Form" in cats_list:
                from app.agents.meeting_validator import extract_form_link
                form_link, _ = extract_form_link(email.get("body") or "")
                if not form_link:
                    cats_list = [c for c in cats_list if c != "Form"]
                    if not cats_list and not is_video:
                        continue

            if is_video and "Meeting" not in cats_list:
                cats_list.append("Meeting")

            final_category = ", ".join(cats_list) if cats_list else ("Meeting" if is_video else "Other")
            extracted["category"] = final_category
                
            if not extracted.get("platform") or extracted["platform"] == "Application Portal":
                if final_category != "Other":
                    extracted["platform"] = final_category.split(",")[0]
                else:
                    extracted["platform"] = "Online Opportunity"

            # Execute Priority Agent evaluation workflow
            existing_meetings = store.list_meetings()
            prio_res = priority_agent.analyze_priority(extracted, existing_meetings)
            extracted["priority"] = prio_res.get("priority", "Low")
            extracted["priority_score"] = prio_res.get("priority_score", 0)
            
            reasons = prio_res.get("reason_for_priority", [])
            extracted["priority_explanation"] = ", ".join(reasons) if isinstance(reasons, list) else str(reasons)
            extracted["priority_thought"] = prio_res.get("agent_thought", "")
            
            actions = prio_res.get("recommended_actions", [])
            extracted["recommended_actions"] = ", ".join(actions) if isinstance(actions, list) else str(actions)

            duplicate = find_duplicate(store, extracted)
            if duplicate:
                merged = merge_meeting(duplicate, extracted)
                saved = store.add_meeting(merged)
            else:
                saved = store.add_meeting(extracted)

            item_id = saved.get("id")

            # ── Integration: Call downstream agents ──────────────────

            # 1. Research Agent — extract structured info
            email_body = email.get("body", "") or ""
            if email_body.strip():
                research_result = _call_research_agent(email_body, item_id)
                if research_result.get("id"):
                    saved["research_id"] = str(research_result["id"])

            # 2. Search/Enrichment Agent — web enrichment
            enrichment_result = _call_enrichment_agent(email, final_category, item_id)
            if enrichment_result.get("id"):
                saved["enrichment_id"] = enrichment_result["id"]

            from app.database import SessionLocal, Meeting
            with SessionLocal() as db:
                m = db.query(Meeting).filter(Meeting.id == item_id).first()
                if m:
                    if "research_id" in saved: m.research_id = saved["research_id"]
                    if "enrichment_id" in saved: m.enrichment_id = saved["enrichment_id"]
                    db.commit()

            # 3. Mark calendar sync as needed
            calendar_needs_sync = True

            # 4. Analytics tracking
            _call_analytics("email", final_category, {
                "email_id": email_id,
                "subject": email.get("subject", ""),
                "priority": extracted["priority"],
                "category": final_category,
            })

            processed_results.append(saved)

    # 5. Trigger Calendar sync once after all emails processed
    if calendar_needs_sync:
        _call_calendar_sync()

    return processed_results


@app.post("/gmail/oauth")
def gmail_oauth() -> dict:
    return run_oauth_flow()
