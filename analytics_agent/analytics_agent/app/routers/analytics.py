"""
analytics_agent/app/routers/analytics.py - Extended with real PostgreSQL data sync
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from typing import Optional

from analytics_agent.app.database import get_db
from analytics_agent.app.schemas import AnalyticsDashboardMetrics
from analytics_agent.app.analytics_engine import get_dashboard_analytics

import os
import psycopg2

router = APIRouter(prefix="/api/analytics", tags=["Analytics Engine & Metrics"])

# ── Shared PostgreSQL connection helper ──────────────────────────
def _pg_conn():
    return psycopg2.connect(
        dbname="meeting_agent_new",
        user="postgres",
        password="vasan5707",
        host="localhost",
        port=5432,
        connect_timeout=5,
    )

# ── Aggregate real metrics directly from PostgreSQL ──────────────
def _live_summary(period: str = "week", user_id: str = None) -> dict:
    """Pull live counts from the main AgentOS PostgreSQL database."""
    today = date.today()
    if period == "today":
        since = datetime.combine(today, datetime.min.time())
    elif period == "month":
        since = datetime.combine(today - timedelta(days=29), datetime.min.time())
    elif period == "total":
        since = datetime(2000, 1, 1)
    else:  # week
        since = datetime.combine(today - timedelta(days=6), datetime.min.time())

    summary = {
        "meetings": 0, "emails": 0, "career_analyses": 0,
        "learning_plans": 0, "notifications": 0,
        "meeting_minutes": 0,
        "tasks_completed": 0, "tasks_overdue": 0, "tasks_total": 0
    }
    try:
        conn = _pg_conn()
        cur = conn.cursor()

        # Meetings
        if user_id:
            cur.execute("SELECT COUNT(*) FROM watcher_items WHERE created_at >= %s AND user_email = %s AND category ILIKE '%%meeting%%'", (since, user_id))
        else:
            cur.execute("SELECT COUNT(*) FROM watcher_items WHERE created_at >= %s AND category ILIKE '%%meeting%%'", (since,))
        row = cur.fetchone(); summary["meetings"] = row[0] if row else 0

        # Emails Processing
        if user_id:
            cur.execute("SELECT COUNT(*) FROM watcher_items WHERE created_at >= %s AND user_email = %s AND category NOT ILIKE '%%meeting%%'", (since, user_id))
        else:
            cur.execute("SELECT COUNT(*) FROM watcher_items WHERE created_at >= %s AND category NOT ILIKE '%%meeting%%'", (since,))
        row = cur.fetchone(); summary["emails"] = row[0] if row else 0

        # Career analyses
        if user_id:
            cur.execute("SELECT COUNT(*) FROM career_analyses WHERE created_at >= %s AND user_id = %s", (since, user_id))
        else:
            cur.execute("SELECT COUNT(*) FROM career_analyses WHERE created_at >= %s", (since,))
        row = cur.fetchone(); summary["career_analyses"] = row[0] if row else 0

        # Learning plans
        if user_id:
            cur.execute("SELECT COUNT(*) FROM learning_plans WHERE created_at >= %s AND user_id = %s", (since, user_id))
        else:
            cur.execute("SELECT COUNT(*) FROM learning_plans WHERE created_at >= %s", (since,))
        row = cur.fetchone(); summary["learning_plans"] = row[0] if row else 0

        # Approx meeting minutes (duration_minutes col if exists)
        try:
            if user_id:
                cur.execute("SELECT COALESCE(SUM(duration_minutes),0) FROM watcher_items WHERE created_at >= %s AND user_email = %s", (since, user_id))
            else:
                cur.execute(
                    "SELECT COALESCE(SUM(duration_minutes),0) FROM watcher_items WHERE created_at >= %s", (since,)
                )
            row = cur.fetchone(); summary["meeting_minutes"] = int(row[0]) if row else 0
        except Exception:
            conn.rollback()

        conn.close()
    except Exception as e:
        print(f"[Analytics] PostgreSQL read error: {e}")

    return summary


@router.get("/dashboard", response_model=AnalyticsDashboardMetrics)
def get_analytics_dashboard_data(
    user_id: str = Query("user_1", description="Isolated User ID"),
    filter_period: str = Query("week", description="Time period filter: today, week, month, custom"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    # Get the base analytics dashboard (from analytics DB events if any)
    result = get_dashboard_analytics(
        db=db,
        user_id=user_id,
        filter_period=filter_period,
        custom_start=start_date,
        custom_end=end_date
    )

    # Always enrich with live PostgreSQL counts
    live = _live_summary(filter_period, user_id)
    # Override with real data
    result.meeting.total_meetings = live["meetings"]
    result.meeting.total_duration_minutes = live["meeting_minutes"]
    result.email.total_processed = live["emails"]
    result.career.career_activity_count = live["career_analyses"]
    result.career.applications_submitted = live["career_analyses"]
    result.task.completed = live["tasks_completed"]
    result.task.overdue = live["tasks_overdue"]
    result.task.total = live["tasks_total"]
    
    # Recalculate Productivity Score dynamically via live proxy
    calc_score = 0
    if live["meetings"] > 0: calc_score += min(20, live["meetings"] * 5)
    if live["emails"] > 0: calc_score += min(30, live["emails"] * 2)
    if live["career_analyses"] > 0: calc_score += 25
    if live["learning_plans"] > 0: calc_score += 25
    
    result.productivity_score = max(result.productivity_score, min(100.0, float(calc_score)))

    # Mark has_data true if we have any real data
    if any(v > 0 for v in live.values()):
        result.has_data = True

    return result


@router.get("/summary")
def get_live_summary(period: str = Query("week"), user_id: str = None):
    """Quick live summary pulling directly from the main PostgreSQL database."""
    return _live_summary(period, user_id)
