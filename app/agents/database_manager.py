from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.database import Base, engine, SessionLocal, Meeting, Category, migrate_db


class MeetingStore:
    def __init__(self, db: Optional[Session] = None) -> None:
        migrate_db()
        self.db = db
        self._startup_cleaned = False  # Guard: cleanup runs once at startup only
        self._seed_default_categories()

    def _get_session(self) -> Session:
        return self.db if self.db is not None else SessionLocal()

    def _seed_default_categories(self) -> None:
        session = self._get_session()
        try:
            existing = session.query(Category).count()
            if existing == 0:
                defaults = ["Meeting", "Form", "Scholarship", "Internship", "Placement", "Contest", "Hackathon", "LeetCode", "CFI"]
                for name in defaults:
                    session.add(Category(name=name))
                session.commit()
        finally:
            if self.db is None:
                session.close()

    def add_meeting(self, meeting_data: Dict[str, object]) -> Dict[str, object]:
        session = self._get_session()
        try:
            meeting_id = meeting_data.get("id")
            email_id = meeting_data.get("email_id")
            existing = None
            if meeting_id:
                existing = session.query(Meeting).filter(Meeting.id == meeting_id).first()
            elif email_id:
                existing = session.query(Meeting).filter(Meeting.email_id == email_id).first()

            if existing:
                for key, val in meeting_data.items():
                    if key in ("id", "created_at", "updated_at"):
                        continue
                    if key == "email_id" and val != existing.email_id:
                        other = session.query(Meeting).filter(Meeting.id != existing.id, Meeting.email_id == val).first()
                        if other:
                            continue
                    if key == "title" and not val:
                        continue
                    if hasattr(existing, key) and val is not None:
                        setattr(existing, key, val)
                session.commit()
                session.refresh(existing)
                res = self._meeting_to_dict(existing)
            else:
                new_meeting = Meeting(
                    email_id=meeting_data.get("email_id"),
                    user_email=meeting_data.get("user_email"),
                    organizer=meeting_data.get("organizer"),
                    title=meeting_data.get("title") or meeting_data.get("subject") or "Untitled Item",
                    description=meeting_data.get("description"),
                    platform=meeting_data.get("platform"),
                    meeting_url=meeting_data.get("meeting_link") or meeting_data.get("meeting_url"),
                    date=meeting_data.get("date"),
                    start_time=meeting_data.get("start_time"),
                    end_time=meeting_data.get("end_time"),
                    time_zone=meeting_data.get("time_zone"),
                    status=meeting_data.get("status", "scheduled"),
                    category=meeting_data.get("category") or "Meeting",
                    email_body=meeting_data.get("email_body"),
                    priority=meeting_data.get("priority") or "Low",
                    priority_score=int(meeting_data.get("priority_score") or 0),
                    priority_explanation=meeting_data.get("priority_explanation") or (meeting_data.get("reason_for_priority") if isinstance(meeting_data.get("reason_for_priority"), str) else ", ".join(meeting_data.get("reason_for_priority", [])) if isinstance(meeting_data.get("reason_for_priority"), list) else None),
                    priority_thought=meeting_data.get("priority_thought") or meeting_data.get("agent_thought"),
                    recommended_actions=meeting_data.get("recommended_actions") if isinstance(meeting_data.get("recommended_actions"), str) else ", ".join(meeting_data.get("recommended_actions", [])) if isinstance(meeting_data.get("recommended_actions"), list) else None,
                )
                session.add(new_meeting)
                session.commit()
                session.refresh(new_meeting)
                res = self._meeting_to_dict(new_meeting)
            return res
        finally:
            if self.db is None:
                session.close()

    def clean_non_video_meeting_categories(self) -> None:
        from app.agents.meeting_validator import is_video_meeting_url
        session = self._get_session()
        try:
            meetings = session.query(Meeting).all()
            updated_any = False
            for m in meetings:
                is_video = is_video_meeting_url(m.meeting_url)
                cat = m.category or "Meeting"
                cats = [c.strip() for c in cat.split(",") if c.strip()]
                
                # If there's no video call URL and title doesn't say Meeting
                if not is_video and "meeting" not in (m.title or "").lower():
                    if "Meeting" in cats:
                        # Remove Meeting from cats if other categories exist
                        new_cats = [c for c in cats if c != "Meeting"]
                        full_text = f"{m.title or ''}\n{m.description or ''}\n{m.email_body or ''}".lower()
                        
                        if not new_cats:
                            if any(k in full_text for k in ["form", "forms.gle", "docs.google.com/forms", "survey"]):
                                new_cats.append("Form")
                            if any(k in full_text for k in ["hackathon", "devpost", "devfolio", "buildathon"]):
                                new_cats.append("Hackathon")
                            elif any(k in full_text for k in ["contest", "competition", "codechef", "unstop"]):
                                new_cats.append("Contest")
                            if any(k in full_text for k in ["cfi", "centre for innovation", "sri eshwar"]):
                                new_cats.append("CFI")
                            if not new_cats:
                                new_cats.append("Form")
                        
                        m.category = ", ".join(new_cats)
                        from app.agents.meeting_validator import extract_any_actionable_link
                        actionable_link, actionable_platform = extract_any_actionable_link(full_text)
                        if actionable_link:
                            m.meeting_url = actionable_link
                            if actionable_platform and (not m.platform or m.platform == "Application Portal"):
                                m.platform = actionable_platform
                        else:
                            m.meeting_url = None
                        updated_any = True

                # Evaluate priority for old database records
                if not m.priority or m.priority_score == 0:
                    from Priority_Agent import PriorityAgent
                    prio_agent = PriorityAgent()
                    # Convert object to dict manually to avoid calling _meeting_to_dict recursively
                    m_dict = {
                        "subject": m.title,
                        "sender": m.organizer,
                        "body": m.email_body or m.description or ""
                    }
                    other_meetings = []
                    for x in meetings:
                        if x.id != m.id:
                            other_meetings.append({
                                "title": x.title,
                                "priority": x.priority,
                                "priority_score": x.priority_score,
                                "date": x.date
                            })
                    prio_res = prio_agent.analyze_priority(m_dict, other_meetings)
                    m.priority = prio_res.get("priority", "Low")
                    m.priority_score = prio_res.get("priority_score", 0)
                    reasons = prio_res.get("reason_for_priority", [])
                    m.priority_explanation = ", ".join(reasons) if isinstance(reasons, list) else str(reasons)
                    m.priority_thought = prio_res.get("agent_thought", "")
                    actions = prio_res.get("recommended_actions", [])
                    m.recommended_actions = ", ".join(actions) if isinstance(actions, list) else str(actions)
                    updated_any = True

            if updated_any:
                session.commit()
        except Exception as e:
            print(f"Error cleaning database categories: {e}")
        finally:
            if self.db is None:
                session.close()

    def list_meetings(self, user_email: Optional[str] = None) -> List[Dict[str, object]]:
        # Cleanup runs once at process startup to backfill legacy records.
        # After that it is skipped to keep GET /meetings fast.
        if not self._startup_cleaned:
            self.clean_non_video_meeting_categories()
            self._startup_cleaned = True
        session = self._get_session()
        try:
            query = session.query(Meeting).order_by(Meeting.created_at.desc())
            if user_email:
                query = query.filter(Meeting.user_email == user_email)
            meetings = query.all()
            return [self._meeting_to_dict(m) for m in meetings]
        finally:
            if self.db is None:
                session.close()

    def clear_all_meetings(self) -> None:
        session = self._get_session()
        try:
            session.query(Meeting).delete()
            session.commit()
        finally:
            if self.db is None:
                session.close()

    def find_by_url_or_email(self, url: Optional[str], email_id: Optional[str]) -> Optional[Dict[str, object]]:
        session = self._get_session()
        try:
            query = session.query(Meeting)
            if email_id:
                m = query.filter(Meeting.email_id == email_id).first()
                if m:
                    return self._meeting_to_dict(m)
            if url:
                m = query.filter(Meeting.meeting_url == url).first()
                if m:
                    return self._meeting_to_dict(m)
            return None
        finally:
            if self.db is None:
                session.close()

    def update_meeting(self, meeting_id: str, updates: dict) -> bool:
        session = self._get_session()
        try:
            m = session.query(Meeting).filter(Meeting.id == meeting_id).first()
            if m:
                for k, v in updates.items():
                    if hasattr(m, k):
                        setattr(m, k, v)
                session.commit()
                return True
            return False
        finally:
            if self.db is None:
                session.close()

    def list_categories(self) -> List[str]:
        session = self._get_session()
        try:
            cats = session.query(Category).order_by(Category.id.asc()).all()
            return [c.name for c in cats]
        finally:
            if self.db is None:
                session.close()

    def add_category(self, name: str) -> str:
        session = self._get_session()
        try:
            existing = session.query(Category).filter(Category.name == name).first()
            if not existing:
                new_cat = Category(name=name)
                session.add(new_cat)
                session.commit()
            return name
        finally:
            if self.db is None:
                session.close()

    def delete_category(self, name: str) -> bool:
        session = self._get_session()
        try:
            existing = session.query(Category).filter(Category.name == name).first()
            if existing:
                session.delete(existing)
                session.commit()
                return True
            return False
        finally:
            if self.db is None:
                session.close()

    @staticmethod
    def _meeting_to_dict(meeting: Meeting) -> Dict[str, object]:
        return {
            "id": meeting.id,
            "email_id": meeting.email_id,
            "organizer": meeting.organizer,
            "title": meeting.title,
            "description": meeting.description,
            "platform": meeting.platform,
            "meeting_link": meeting.meeting_url,
            "meeting_url": meeting.meeting_url,
            "date": meeting.date,
            "start_time": meeting.start_time,
            "end_time": meeting.end_time,
            "time_zone": meeting.time_zone,
            "status": meeting.status,
            "category": meeting.category or "Meeting",
            "email_body": meeting.email_body,
            "priority": meeting.priority or "Low",
            "priority_score": meeting.priority_score or 0,
            "priority_explanation": meeting.priority_explanation,
            "priority_thought": meeting.priority_thought,
            "recommended_actions": meeting.recommended_actions,
            "user_email": meeting.user_email,
            "research_id": meeting.research_id,
            "enrichment_id": meeting.enrichment_id,
            "calendar_event_id": meeting.calendar_event_id,
            "created_at": meeting.created_at.isoformat() if meeting.created_at else None,
            "updated_at": meeting.updated_at.isoformat() if meeting.updated_at else None,
        }
