import os # trigger reload
import asyncio
import httpx
from typing import Dict, Any, List
from fastapi import FastAPI, Request, Query, UploadFile, File, Depends, HTTPException, status, Body
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import logging

def load_env_file():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(project_root, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip()

load_env_file()

from ui.models import Base, User
from ui.db import get_db, engine
from ui.auth import (
    verify_password, get_password_hash, create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM
)
from jose import JWTError, jwt

# Ensure DB Tables exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AgentOS Unified API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

# ── Authentication Routes ──────────────────────────────────────────────
@app.post("/auth/signup")
def signup(payload: dict = Body(...), db: Session = Depends(get_db)):
    email = payload.get("email")
    password = payload.get("password")
    name = payload.get("name")
    
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")
        
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hashed_password = get_password_hash(password)
    new_user = User(email=email, hashed_password=hashed_password, full_name=name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "user": {"email": email, "name": name}}

@app.post("/auth/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "user": {"email": user.email, "name": user.full_name}}

@app.get("/auth/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "email": current_user.email,
        "name": current_user.full_name,
        "profile_picture": current_user.profile_picture,
        "college_name": current_user.college_name,
        "department": current_user.department,
        "course": current_user.course
    }

@app.put("/auth/me")
def update_user_me(payload: Dict[str, Any], current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if "name" in payload:
        current_user.full_name = payload["name"]
    if "college_name" in payload:
        current_user.college_name = payload["college_name"]
    if "department" in payload:
        current_user.department = payload["department"]
    if "course" in payload:
        current_user.course = payload["course"]
    db.commit()
    db.refresh(current_user)
    return {
        "message": "Profile updated",
        "user": {
            "name": current_user.full_name,
            "college_name": current_user.college_name,
            "department": current_user.department,
            "course": current_user.course
        }
    }

@app.post("/auth/google")
def google_auth(payload: Dict[str, str], db: Session = Depends(get_db)):
    email = payload.get("email")
    name = payload.get("name")
    google_id = payload.get("google_id")
    picture = payload.get("picture")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, full_name=name, google_id=google_id, profile_picture=picture)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    access_token = create_access_token(data={"sub": user.email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer", "user": {"email": user.email, "name": user.full_name, "picture": picture}}


@app.post("/auth/logout")
async def handle_logout(db: Session = Depends(get_db)):
    # 3. Strip GMAIL tokens from .env file
    env_path = r"E:\AgentOS\.env"
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        newlines = [ln for ln in lines if not (ln.startswith("GMAIL_ACCESS_TOKEN=") or ln.startswith("GMAIL_REFRESH_TOKEN="))]
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(newlines)

    return {"message": "Logged out successfully. User data is persisted."}
# ── Microservices Unified Proxies (No Mock Data) ──────────────────────
# Note: all these route to the actual local agents over loopback ports.

@app.get("/api/agents/status")
async def get_all_status():
    ports = {
        "Watcher": 8001, "Research": 8002, "Enrichment": 8003, "RAG-Ingest": 8004,
        "Knowledge": 8005, "Meeting": 8006, "Filler": 8007, "Career": 8008,
        "Learning": 8009, "Resume": 8010, "Calendar": 8011, "Notification": 8012, "Analytics": 8013
    }
    results = []
    async with httpx.AsyncClient(timeout=2.0) as client:
        for name, p in ports.items():
            try:
                # Basic reachability check
                resp = await client.get(f"http://127.0.0.1:{p}/docs")
                results.append({"name": name, "port": p, "status": "Running" if resp.status_code < 500 else "Error"})
            except Exception:
                results.append({"name": name, "port": p, "status": "Offline"})
    return results


@app.post("/api/research/analyze")
async def analyze_email(payload: Dict[str, Any], current_user: User = Depends(get_current_user)):
    """Send email body to Research Agent for 19-step structured extraction."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post("http://127.0.0.1:8002/analyze", json={"content": payload.get("content", "")})
            resp.raise_for_status()
            data = resp.json()
            
            # Save the returned research_id to the Watcher Agent
            email_id = payload.get("email_id")
            if email_id and "id" in data:
                try:
                    await client.patch(f"http://127.0.0.1:8001/meetings/{email_id}", json={"research_id": data["id"]})
                except Exception as patch_e:
                    logger.warning(f"Failed to update email with research_id: {patch_e}")
                    
            return data
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Research agent unavailable: {e}")

@app.post("/api/calendar/add")
async def add_calendar_event(payload: Dict[str, Any], current_user: User = Depends(get_current_user)):
    """Create a calendar event via the Calendar Agent."""
    import datetime as dt
    
    # Map the frontend payload → CalendarEventCreate schema
    def safe_datetime(val):
        if not val:
            return None
        try:
            import dateutil.parser
            # Attempt to split range like "July 24-26, 2026" to "July 24 2026"
            cleaned_val = str(val).split('-')[0].strip()
            # If the year got stripped in range like July 24, append year (best effort)
            if ',' in str(val) and ',' not in cleaned_val:
                cleaned_val += str(val).split(',')[-1]
                
            parsed = dateutil.parser.parse(cleaned_val, fuzzy=True)
            return parsed.isoformat()
        except Exception:
            return None

    now = dt.datetime.utcnow().isoformat()
    one_hour_later = (dt.datetime.utcnow() + dt.timedelta(hours=1)).isoformat()

    calendar_payload = {
        "user_id": current_user.email,
        "source_type": "email",
        "event_type": payload.get("event_type", "GENERAL_EVENT"),
        "title": payload.get("title", "AgentOS Event"),
        "description": payload.get("description", ""),
        "start_datetime": safe_datetime(payload.get("start_datetime")) or now,
        "end_datetime": safe_datetime(payload.get("end_datetime")) or one_hour_later,
        "all_day": False,
        "timezone": "Asia/Kolkata",
        "location": payload.get("location"),
        "external_url": payload.get("meeting_link"),
        "priority": payload.get("priority", "MEDIUM"),
        "reminders": [10],
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.post("http://127.0.0.1:8011/api/calendar/events", json=calendar_payload)
            if resp.status_code in (200, 201):
                return resp.json()
            raise HTTPException(status_code=resp.status_code, detail=f"Calendar agent error: {resp.text[:300]}")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Calendar agent unavailable: {e}")

@app.get("/api/inbox")
async def get_inbox(current_user: User = Depends(get_current_user)):
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(f"http://127.0.0.1:8001/meetings?user_email={current_user.email}")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Watcher agent unavailable: {e}")

@app.post("/api/sync")
async def trigger_sync(current_user: User = Depends(get_current_user)):
    logger.info(f"Triggering email sync for user {current_user.email}")
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            resp = await client.post(f"http://127.0.0.1:8001/sync?user_email={current_user.email}")
            resp.raise_for_status()
            logger.info(f"Email sync successful for {current_user.email}")
            return {"status": "success", "data": resp.json()}
        except Exception as e:
            logger.error(f"Watcher agent unavailable during sync: {e}")
            raise HTTPException(status_code=502, detail=f"Watcher agent unavailable: {e}")


@app.get("/api/categories")
async def get_categories(current_user: User = Depends(get_current_user)):
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get("http://127.0.0.1:8001/categories")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Watcher agent unavailable: {e}")

@app.post("/api/categories")
async def add_category(payload: dict, current_user: User = Depends(get_current_user)):
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.post("http://127.0.0.1:8001/categories", json=payload)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Watcher agent unavailable: {e}")

@app.delete("/api/categories/{category_name}")
async def delete_category_proxy(category_name: str, current_user: User = Depends(get_current_user)):
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.delete(f"http://127.0.0.1:8001/categories/{category_name}")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Watcher agent unavailable: {e}")

@app.get("/api/calendar/events")
async def get_calendar_events(current_user: User = Depends(get_current_user)):
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(f"http://127.0.0.1:8011/api/calendar/events?user_email={current_user.email}")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Calendar agent unavailable: {e}")

@app.delete("/api/calendar/events/{event_id}")
async def delete_calendar_event(event_id: str, current_user: User = Depends(get_current_user)):
    """Delete a calendar event."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.delete(f"http://127.0.0.1:8011/api/calendar/events/{event_id}?user_email={current_user.email}")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Calendar agent unavailable: {e}")

@app.get("/api/notifications")
async def get_notifications(current_user: User = Depends(get_current_user)):
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(f"http://127.0.0.1:8001/notifications?user_email={current_user.email}")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Notification agent unavailable: {e}")

@app.get("/api/analytics/dashboard")
async def get_analytics_dashboard(filter_period: str = Query("week"), current_user: User = Depends(get_current_user)):
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"http://127.0.0.1:8013/api/analytics/dashboard?user_id={current_user.email}&filter_period={filter_period}")
        if resp.status_code == 200:
            return resp.json()
        raise HTTPException(status_code=502, detail=f"Analytics returned {resp.status_code}")
    except HTTPException: raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Analytics agent unavailable: {e}")

@app.get("/api/analytics/insights")
async def get_analytics_insights(filter_period: str = Query("week"), current_user: User = Depends(get_current_user)):
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"http://127.0.0.1:8013/api/insights?user_id={current_user.email}&filter_period={filter_period}")
        if resp.status_code == 200:
            return resp.json()
        raise HTTPException(status_code=502, detail=f"Analytics returned {resp.status_code}")
    except HTTPException: raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Analytics agent unavailable: {e}")

@app.get("/api/analytics/summary")
async def get_analytics_summary(period: str = Query("week"), current_user: User = Depends(get_current_user)):
    """Live quick-stats panel — feeds the Home dashboard cards."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"http://127.0.0.1:8013/api/analytics/summary?user_id={current_user.email}&period={period}")
        if resp.status_code == 200:
            return resp.json()
        raise HTTPException(status_code=502, detail=f"Analytics returned {resp.status_code}")
    except HTTPException: raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Analytics agent unavailable: {e}")

@app.get("/api/home/stats")
async def get_home_stats(current_user: User = Depends(get_current_user)):
    """Real-time home dashboard stats from PostgreSQL."""
    import psycopg2
    from datetime import date, datetime, timedelta
    stats = {
        "meetings_today": 0,
        "career_analyses": 0,
        "learning_plans": 0,
        "agents_online": 0,
        "notifications": 0,
        "emails_processed": 0,
    }
    try:
        today_start = datetime.combine(date.today(), datetime.min.time())
        conn = psycopg2.connect(dbname="meeting_agent_new", user="postgres",
                                password="vasan5707", host="localhost", port=5432, connect_timeout=3)
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM watcher_items WHERE created_at >= %s AND user_email = %s AND category ILIKE '%%Meeting%%'", (today_start, current_user.email))
        stats["meetings_today"] = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM watcher_items WHERE user_email = %s", (current_user.email,))
        stats["emails_processed"] = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM career_analyses WHERE user_id = %s", (current_user.email,))
        stats["career_analyses"] = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM learning_plans WHERE user_id = %s", (current_user.email,))
        stats["learning_plans"] = cur.fetchone()[0]

        conn.close()
    except Exception as db_err:
        logger.warning(f"Home stats DB error: {db_err}")

    # Count running agents
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get("http://127.0.0.1:9000/api/agents/status")
            agents = resp.json()
            stats["agents_online"] = sum(1 for a in agents if a.get("status") == "Running")
    except Exception:
        pass

    return stats



@app.post("/api/filler/start-form")
async def trigger_filler(payload: Dict[str, Any], current_user: User = Depends(get_current_user)):
    """Start the filler agent process for a specific form_url.
    Timeout is 120s because Playwright form parsing can take 30-60 seconds.
    """
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post("http://127.0.0.1:8007/api/start-form", json=payload)
            if resp.status_code >= 400:
                try:
                    detail = resp.json().get("detail", resp.text[:300])
                except Exception:
                    detail = resp.text[:300]
                raise HTTPException(status_code=resp.status_code, detail=f"Filler agent error: {detail}")
            return resp.json()
        except HTTPException:
            raise
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Filler agent timed out. The form may be complex — please try again.")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Filler agent unavailable: {e}")

@app.get("/api/filler/session/{session_id}")
async def get_filler_session(session_id: str, current_user: User = Depends(get_current_user)):
    """Fetch session info from Filler Agent."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"http://127.0.0.1:8007/api/session/{session_id}")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Filler agent unavailable: {e}")

@app.post("/api/filler/review/{session_id}")
async def trigger_filler_review(session_id: str, payload: Dict[str, Any], current_user: User = Depends(get_current_user)):
    """Update review data and transition to executing state."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(f"http://127.0.0.1:8007/api/review/{session_id}", json=payload)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Filler agent unavailable: {e}")

@app.get("/api/filler/execution/{session_id}/stream")
async def stream_filler_execution(session_id: str, request: Request):
    """Proxy the SSE execution stream from the Filler Agent."""
    import httpx
    from fastapi.responses import StreamingResponse
    async def proxy_stream():
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("GET", f"http://127.0.0.1:8007/api/execution/{session_id}/stream") as response:
                async for chunk in response.aiter_raw():
                    yield chunk
    return StreamingResponse(proxy_stream(), media_type="text/event-stream")

@app.get("/api/filler/history")
async def get_filler_history(current_user: User = Depends(get_current_user)):
    """Fetch history from Filler Agent."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"http://127.0.0.1:8007/api/history?user_email={current_user.email}")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Filler agent unavailable: {e}")

@app.get("/api/meetings")
async def get_meetings(current_user: User = Depends(get_current_user)):
    """Fetch meetings directly from Meeting Agent DB."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"http://127.0.0.1:8006/meetings?user_email={current_user.email}")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Meeting agent unavailable: {e}")

@app.post("/api/meetings")
async def create_meeting(payload: Dict[str, Any], current_user: User = Depends(get_current_user)):
    """Send an email turned meeting to Meeting Agent DB."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            payload["user_email"] = current_user.email
            resp = await client.post("http://127.0.0.1:8006/meetings", json=payload)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Meeting agent unavailable: {e}")

@app.post("/api/meetings/{meeting_id}/trigger")
async def trigger_meeting(meeting_id: str, current_user: User = Depends(get_current_user)):
    """Trigger Meeting Bot join process."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(f"http://127.0.0.1:8006/meetings/{meeting_id}/trigger")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Meeting agent unavailable: {e}")

@app.get("/api/meetings/{meeting_id}")
async def get_meeting(meeting_id: str, current_user: User = Depends(get_current_user)):
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"http://127.0.0.1:8006/meetings/{meeting_id}")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Meeting agent unavailable: {e}")

@app.put("/api/meetings/{meeting_id}")
async def update_meeting(meeting_id: str, payload: Dict[str, Any], current_user: User = Depends(get_current_user)):
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.put(f"http://127.0.0.1:8006/meetings/{meeting_id}", json=payload)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Meeting agent unavailable: {e}")

@app.delete("/api/meetings/{meeting_id}")
async def delete_meeting(meeting_id: str, current_user: User = Depends(get_current_user)):
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.delete(f"http://127.0.0.1:8006/meetings/{meeting_id}")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Meeting agent unavailable: {e}")

@app.post("/api/meetings/{meeting_id}/reformat")
async def reformat_meeting(meeting_id: str, payload: Dict[str, Any] = Body(default={}), current_user: User = Depends(get_current_user)):
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(f"http://127.0.0.1:8006/meetings/{meeting_id}/reformat", json=payload)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Meeting agent unavailable: {e}")

@app.post("/api/bot/connect")
async def connect_bot(current_user: User = Depends(get_current_user)):
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post("http://127.0.0.1:8006/bot/connect")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Meeting agent unavailable: {e}")

@app.post("/api/resume/upload")
async def upload_resume(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    content = await file.read()
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(
                f"http://127.0.0.1:8010/api/v1/upload?user_email={current_user.email}",
                files={"file": (file.filename, content, file.content_type or "application/octet-stream")}
            )
            if resp.status_code not in (200, 201):
                raise HTTPException(status_code=resp.status_code, detail=f"Resume extractor error: {resp.text[:500]}")
            data = resp.json()

            # Groq formatting — production-grade Groq key rotation across all 6 keys
            raw_text = data.get("raw_text", "")
            if raw_text and len(raw_text.strip()) > 20:
                try:
                    import sys as _sys
                    _sys.path.insert(0, r"E:\AgentOS")
                    from groq_rotation import groq_chat_sync
                    prompt = (
                        "You are a professional resume analyst. Given the following raw extracted resume text, "
                        "produce a clean, well-structured and formatted summary of the candidate's profile. "
                        "Include sections: Contact Info, Professional Summary, Skills, Work Experience, Education, Projects, Certifications. "
                        "Be concise and professional. If a section has no data, skip it.\n\n"
                        f"Raw Resume Text:\n{raw_text[:3000]}"
                    )
                    formatted = groq_chat_sync(
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.2,
                        max_tokens=1500,
                    )
                    data["formatted_text"] = formatted
                except Exception as groq_err:
                    logger.warning(f"Groq formatting failed (non-critical): {groq_err}")
                    data["formatted_text"] = raw_text
            else:
                data["formatted_text"] = raw_text

            return data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Resume extractor unavailable: {e}")



@app.post("/api/research/analyze")
async def analyze_research(payload: Dict[str, Any], current_user: User = Depends(get_current_user)):
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post("http://127.0.0.1:8002/analyze", json=payload)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Research agent unavailable: {e}")

@app.get("/api/research/analyses/{analysis_id}")
async def get_analysis_research(analysis_id: str, current_user: User = Depends(get_current_user)):
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.get(f"http://127.0.0.1:8002/analyses/{analysis_id}")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Research agent unavailable: {e}")

@app.post("/api/career/analyze")
async def analyze_career(payload: Dict[str, Any], current_user: User = Depends(get_current_user)):
    try:
        payload["user_id"] = current_user.email
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                resp = await client.post("http://127.0.0.1:8008/analyze", json=payload)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                raise HTTPException(status_code=502, detail=f"Career agent unavailable: {e}")
    except HTTPException:
        raise

@app.get("/api/career/analyses")
async def get_career_analyses(current_user: User = Depends(get_current_user)):
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"http://127.0.0.1:8008/analyses?user_id={current_user.email}")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Career agent unavailable: {e}")

@app.get("/api/resume/list")
async def list_resumes(current_user: User = Depends(get_current_user)):
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"http://127.0.0.1:8010/api/v1/resume?user_email={current_user.email}")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Resume extractor unavailable: {e}")

@app.post("/api/learning/create")
async def create_learning(payload: Dict[str, Any], current_user: User = Depends(get_current_user)):
    try:
        payload["user_id"] = current_user.email
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post("http://127.0.0.1:8009/learning/generate", json=payload)
        if resp.status_code == 200:
            return resp.json()
        else:
            detail = resp.json().get("reason", resp.text[:200]) if resp.content else resp.text[:200]
            raise HTTPException(status_code=resp.status_code, detail=f"Learning agent: {detail}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Learning agent unreachable: {e}")

@app.get("/api/learning/plans")
async def get_learning_plans(current_user: User = Depends(get_current_user)):
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"http://127.0.0.1:8009/learning?user_id={current_user.email}")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
             raise HTTPException(status_code=502, detail=f"Learning agent unavailable: {e}")

@app.get("/api/knowledge/ask")
async def knowledge_ask(query: str, current_user: User = Depends(get_current_user)):
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post("http://127.0.0.1:8005/query", json={"query": query})
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Knowledge service returned HTTP {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        docs    = data.get("retrieved_documents") or []
        max_sim = docs[0].get("similarity_score", 0.0) if docs else 0.0
        return {
            "answer": data.get("answer", "No relevant information found in the knowledge base."),
            "sources": [
                {"title": d.get("document_name", f"Source {i+1}"), "relevance": round(d.get("similarity_score", 0.0), 3)}
                for i, d in enumerate(docs)
            ],
            "similarity_score": round(max_sim, 3),
            "confidence": data.get("confidence", "Unknown"),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Knowledge ask error: {e}")
        raise HTTPException(status_code=502, detail=f"Knowledge Retrieval unavailable: {e}")


@app.post("/api/knowledge/sync")
async def knowledge_sync(current_user: User = Depends(get_current_user)):
    try:
        import psycopg2
        import httpx
        
        conn = psycopg2.connect(dbname="meeting_agent_new", user="postgres", password="vasan5707", host="localhost", port=5432)
        cur = conn.cursor()
        cur.execute("SELECT id, subject, body FROM email_inbox WHERE processed = FALSE LIMIT 50")
        email_rows = cur.fetchall()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for row in email_rows:
                if row[2]:
                    content_str = f"Email Subject: {row[1]}\nEmail Body: {row[2]}"
                    try:
                        await client.post("http://127.0.0.1:8004/ingest", json={
                            "content": content_str[:20000],
                            "source_agent": "Watcher",
                            "user_id": current_user.email
                        })
                    except Exception as pass_err:
                        pass
                        
            # Sync user's latest resumes
            try:
                cur.execute("SELECT first_name, last_name, email, phone, location, summary, raw_text FROM resumes WHERE user_email = %s ORDER BY id DESC LIMIT 5", (current_user.email,))
                for res_row in cur.fetchall():
                    if res_row:
                        res_content = f"Resume & Profile Details:\nName: {res_row[0]} {res_row[1]}\nEmail: {res_row[2]}\nPhone: {res_row[3]}\nLocation: {res_row[4]}\nSummary: {res_row[5]}\nFull Text: {res_row[6]}"
                        await client.post("http://127.0.0.1:8004/ingest", json={"content": res_content[:20000], "source_agent": "Resume Extractor", "user_id": current_user.email})
            except Exception as e:
                logger.error(f"Failed to sync resumes for {current_user.email}: {e}")
                pass
                
            # Sync user's latest meetings/transcripts
            try:
                cur.execute("SELECT id, title, transcript FROM meetings WHERE user_email = %s ORDER BY created_at DESC LIMIT 5", (current_user.email,))
                t_rows = cur.fetchall()
                for tr in t_rows:
                    if tr[2]:
                        await client.post("http://127.0.0.1:8004/ingest", json={"content": f"Meeting ID: {tr[0]}\nTopic: {tr[1]}\nTranscript: {tr[2]}"[:20000], "source_agent": "Meeting Agent", "user_id": current_user.email})
            except Exception as e:
                logger.error(f"Failed to sync meetings for {current_user.email}: {e}")
                pass
                
            # Sync user's latest career analyses
            try:
                cur.execute("SELECT user_name, career_summary, ats_score, employability_score, structured_data FROM career_analyses WHERE user_id = %s ORDER BY created_at DESC LIMIT 5", (current_user.email,))
                for car_row in cur.fetchall():
                    if car_row:
                        import json
                        details_str = str(car_row[4])
                        missing_skills_str = "None identified"
                        try:
                            s_data = car_row[4] if isinstance(car_row[4], dict) else json.loads(car_row[4])
                            missing = s_data.get("skills", {}).get("missing", []) or s_data.get("skill_gap", [])
                            if missing:
                                missing_skills_str = ", ".join(missing)
                        except Exception:
                            pass
                            
                        car_content = f"Career Analysis for {car_row[0]}:\nCareer Summary: {car_row[1]}\nATS Score: {car_row[2]} out of 100\nEmployability Score: {car_row[3]} out of 100\nMissing Skills: {missing_skills_str}\nAdditional Details: {details_str}"
                        await client.post("http://127.0.0.1:8004/ingest", json={"content": car_content[:20000], "source_agent": "Career Agent", "user_id": current_user.email})
            except Exception as e:
                logger.error(f"Failed to sync career analysis for {current_user.email}: {e}")
                pass
                
            # Sync user's latest learning plans
            try:
                cur.execute("SELECT career_goal, missing_skills, learning_roadmap, recommended_topics FROM learning_plans WHERE user_id = %s ORDER BY created_at DESC LIMIT 5", (current_user.email,))
                for learn_row in cur.fetchall():
                    if learn_row:
                        learn_content = f"Learning Plan for {current_user.full_name}:\nGoal: {learn_row[0]}\nMissing Skills Focus: {learn_row[1]}\nRoadmap: {learn_row[2]}\nTopics: {learn_row[3]}"
                        await client.post("http://127.0.0.1:8004/ingest", json={"content": learn_content[:20000], "source_agent": "Learning Agent", "user_id": current_user.email})
            except Exception as e:
                logger.error(f"Failed to sync learning plan for {current_user.email}: {e}")
                pass
        
        cur.execute("UPDATE email_inbox SET processed = TRUE WHERE processed = FALSE")
        conn.commit()
        conn.close()
        return {"status": "success", "message": "Knowledge synchronization complete."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {e}")

@app.get("/gmail/oauth")
async def trigger_google_oauth(user_email: str = None):
    """Trigger real Google OAuth Identity flow directly from the Unified API Gateway."""
    load_env_file()
    CLIENT_ID = os.getenv("GMAIL_CLIENT_ID")
    REDIRECT_URI = os.getenv("GMAIL_REDIRECT_URI", "http://localhost:9000/api/auth/callback")
    
    if not CLIENT_ID:
        return {"status": "error", "message": "Missing GMAIL_CLIENT_ID in E:\\AgentOS\\.env"}
        
    import urllib.parse
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile https://www.googleapis.com/auth/gmail.readonly",
        "access_type": "offline",
        "prompt": "consent",
    }
    if user_email:
        params["state"] = user_email

    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return RedirectResponse(url=auth_url)

@app.get("/api/auth/callback")
async def google_oauth_callback(code: str, state: str = None, db: Session = Depends(get_db)):
    import json, urllib.parse, urllib.request, traceback
    from urllib.request import Request as URLRequest, urlopen
    
    load_env_file()
    CLIENT_ID = os.getenv("GMAIL_CLIENT_ID")
    CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET")
    REDIRECT_URI = os.getenv("GMAIL_REDIRECT_URI", "http://localhost:9000/api/auth/callback")
    
    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    
    try:
        req = URLRequest(token_url, data=urllib.parse.urlencode(payload).encode("utf-8"), method="POST", headers={"Content-Type": "application/x-www-form-urlencoded"})
        with urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
        
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        
        # Save to .env for Watcher agent background tasks
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        skip_keys = {"GMAIL_ACCESS_TOKEN", "GMAIL_REFRESH_TOKEN", "GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET"}
        existing_lines = []
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as handle:
                existing_lines = handle.readlines()
        filtered = [ln for ln in existing_lines if not any(ln.startswith(k + "=") for k in skip_keys)]
        with open(env_path, "w", encoding="utf-8") as handle:
            handle.writelines(filtered)
            if filtered and not filtered[-1].endswith("\n"):
                handle.write("\n")
            handle.write(f"GMAIL_ACCESS_TOKEN={access_token}\n")
            if refresh_token:
                handle.write(f"GMAIL_REFRESH_TOKEN={refresh_token}\n")
            handle.write(f"GMAIL_CLIENT_ID={CLIENT_ID}\n")
            handle.write(f"GMAIL_CLIENT_SECRET={CLIENT_SECRET}\n")
            
        # Get Google Profile
        req_info = URLRequest("https://www.googleapis.com/oauth2/v2/userinfo", headers={"Authorization": f"Bearer {access_token}"})
        with urlopen(req_info, timeout=10) as info_res:
            user_info = json.loads(info_res.read().decode("utf-8"))
            
        email = user_info.get("email")
        name = user_info.get("name")
        google_id = user_info.get("id")
        picture = user_info.get("picture")
        
        # If state provided, we just link the exact existing manual user's google properties
        if state:
            user = db.query(User).filter(User.email == state).first()
            if user:
                user.google_id = google_id
                if not user.full_name:
                    user.full_name = name
                user.profile_picture = picture
                db.commit()
                db.refresh(user)
                
                # We skip log in param redirect to just redirect to settings since they are already logged in
                return RedirectResponse(url="http://localhost:9000/settings?linked=true")
            
        # Normal check if user exists, else create
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(email=email, full_name=name, google_id=google_id, profile_picture=picture)
            db.add(user)
            db.commit()
            db.refresh(user)
            
        # Log User locally by auto-submitting the login endpoint!
        # Redirecting back to React router login which will instantly generate AuthContext if valid
        q = urllib.parse.urlencode({"email": email, "name": name, "google_login": "true"})
        
        # Trigger background Watcher sync process securely
        async with httpx.AsyncClient() as client:
            try:
                await client.post("http://127.0.0.1:8001/sync")
            except:
                pass
                
        return RedirectResponse(url=f"http://localhost:9000/login?{q}")
        
    except Exception as e:
        err_msg = str(e)
        if hasattr(e, "read"):
            try:
                err_msg += " - " + e.read().decode("utf-8")
            except:
                pass
        logger.error(f"Google OAuth Failed: {err_msg}\n{traceback.format_exc()}")
        encoded_err = urllib.parse.quote(err_msg)
        return RedirectResponse(url=f"http://localhost:9000/login?error=Google_OAuth_Failed&detail={encoded_err}")

# ── SPA Hosting ───────────────────────────────────────────────────────
# Mount React frontend static assets (must build frontend to `frontend/dist`)
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../frontend/dist")

@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    # Try serving as an asset if the file exists
    requested_path = os.path.join(FRONTEND_DIR, full_path)
    if os.path.isfile(requested_path):
        return FileResponse(requested_path)
    
    # Fallback to index.html for React Router
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>Frontend not built yet!</h1><p>Run <code>npm run build</code> in <code>/frontend</code></p>")

