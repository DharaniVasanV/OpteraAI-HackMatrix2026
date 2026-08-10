from datetime import datetime, timezone
from typing import Dict, List
from app.agents.database_manager import MeetingStore


class NotificationAgent:
    def __init__(self, store: MeetingStore) -> None:
        self.store = store

    def get_upcoming_notifications(self, user_email: str = None) -> List[Dict[str, object]]:
        meetings = self.store.list_meetings(user_email=user_email)
        notifications = []
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        from datetime import timedelta
        for m in meetings:
            if m.get("status") == "cancelled":
                notifications.append({
                    "id": f"notif-cancel-{m['id']}",
                    "meeting_id": m["id"],
                    "title": f"Meeting Cancelled: {m['title']}",
                    "message": f"The meeting '{m['title']}' hosted by {m.get('organizer', 'Organizer')} has been cancelled.",
                    "type": "warning",
                    "time": m.get("start_time", ""),
                })
            elif m.get("status") == "updated":
                notifications.append({
                    "id": f"notif-update-{m['id']}",
                    "meeting_id": m["id"],
                    "title": f"Meeting Rescheduled: {m['title']}",
                    "message": f"New schedule: {m.get('date')} at {m.get('start_time')}",
                    "type": "info",
                    "time": m.get("start_time", ""),
                })
            elif m.get("date") == today_str:
                notifications.append({
                    "id": f"notif-today-{m['id']}",
                    "meeting_id": m["id"],
                    "title": f"Upcoming Today: {m['title']}",
                    "message": f"Starts at {m.get('start_time')} on {m.get('platform', 'Online Platform')}",
                    "type": "success",
                    "time": m.get("start_time", ""),
                })
            elif m.get("date"):
                try:
                    m_date = datetime.strptime(m.get("date"), "%Y-%m-%d").date()
                    today_date = datetime.now(timezone.utc).date()
                    if today_date < m_date <= today_date + timedelta(days=7):
                        notifications.append({
                            "id": f"notif-upcoming-{m['id']}",
                            "meeting_id": m["id"],
                            "title": f"Upcoming Event: {m['title']}",
                            "message": f"Scheduled for {m.get('date')} at {m.get('start_time')}",
                            "type": "info",
                            "time": m.get("start_time", ""),
                        })
                except Exception:
                    pass

        return notifications
