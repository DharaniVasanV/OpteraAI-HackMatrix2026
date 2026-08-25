import uuid
import os
import json
import logging
import re
from sqlalchemy.orm import Session
from models.db_models import FormSession, FormQuestion, UserProfile, SubmissionHistory
from services.form_parser import parse_google_form
from services.ai_engine import match_question_to_profile
from services.form_filler import execute_form_filling

logger = logging.getLogger(__name__)

class FillerAgent:
    """
    Autonomous Filler Agent Orchestrator.
    Manages end-to-end lifecycle: form analysis, resume sync, semantic matching,
    user input collection, review, and Playwright form submission.
    """

    @staticmethod
    def _sync_resume_to_profile(db: Session, user_email: str = "default"):
        """
        Pull structured resume data from the Resume Agent's PostgreSQL DB into
        UserProfile so form questions are matched against real resume data.
        """
        try:
            import psycopg2

            db_url = os.getenv("DATABASE_URL", "")
            m = re.search(r"postgresql.*://([^:]+):([^@]+)@([^:/]+):?(\d+)?/(\w+)", db_url)
            if not m:
                return
            user_pg, pw_pg, host_pg, port_pg, dbname_pg = m.groups()

            conn = psycopg2.connect(
                dbname=dbname_pg, user=user_pg, password=pw_pg,
                host=host_pg, port=int(port_pg or 5432), connect_timeout=3
            )
            cur = conn.cursor()

            try:
                # 1. Fetch the user's actual profile name
                cur.execute("SELECT full_name FROM users WHERE email = %s", (user_email,))
                user_row = cur.fetchone()
                user_full_name = str(user_row[0]).lower() if user_row and user_row[0] else ""

                # 2. Fetch all resumes belonging to this user
                cur.execute("""
                    SELECT id, first_name, last_name, email, phone, location, summary, file_path
                    FROM resumes 
                    WHERE user_email = %s
                    ORDER BY id DESC
                """, (user_email,))
                rows = cur.fetchall()

                best_row = None
                if rows:
                    if user_full_name:
                        for r in rows:
                            r_fname = (r[1] or "").lower()
                            r_lname = (r[2] or "").lower()
                            # Match if first name or last name is present in user's profile name
                            if (len(r_fname) > 1 and r_fname in user_full_name) or (len(r_lname) > 1 and r_lname in user_full_name):
                                best_row = r
                                break
                    if not best_row:
                        best_row = rows[0] # Fallback to latest
                else:
                    # Fallback across all if none found explicitly attached
                    cur.execute("""
                        SELECT id, first_name, last_name, email, phone, location, summary, file_path
                        FROM resumes 
                        ORDER BY id DESC LIMIT 1
                    """)
                    best_row = cur.fetchone()

                if best_row:
                    res_id, first_name, last_name, email, phone, location, summary, file_path = best_row
                    fields = {
                        "Full Name": f"{first_name or ''} {last_name or ''}".strip(),
                        "Email Address": email,
                        "Phone Number": phone,
                        "City / Current Location": location,
                        "Briefly describe your career goals and background": summary,
                        "Resume / Curriculum Vitae Document": file_path
                    }
                    
                    cur.execute("SELECT name FROM skills WHERE resume_id = %s", (res_id,))
                    skills_rows = cur.fetchall()
                    if skills_rows:
                        fields["Technical Skills (Select all that apply)"] = ", ".join([r[0] for r in skills_rows])
                        
                    cur.execute("SELECT company, job_title FROM experiences WHERE resume_id = %s", (res_id,))
                    exp_rows = cur.fetchall()
                    if exp_rows:
                        fields["Preferred Job Role / Title"] = exp_rows[0][1]
                        fields["Years of Professional Experience"] = f"{len(exp_rows)} Years"

                    for profile_key, value in fields.items():
                        if value and str(value).strip():
                            val_str = str(value).strip()
                            existing = db.query(UserProfile).filter(UserProfile.field_key == profile_key).first()
                            if existing:
                                existing.field_value = val_str
                            else:
                                db.add(UserProfile(field_key=profile_key, field_value=val_str, category="Resume"))
                    db.commit()
                    logger.info("Synced resume data into UserProfile.")
            except Exception as e:
                logger.debug(f"Resume sync error: {e}")
            finally:
                conn.close()

        except Exception as e:
            logger.debug(f"Resume sync skipped (non-critical): {e}")

    @staticmethod
    async def create_and_analyze_session(db: Session, form_url: str, user_email: str = "default") -> FormSession:
        session_id = str(uuid.uuid4())[:12]

        # Sync latest resume data into UserProfile before matching
        FillerAgent._sync_resume_to_profile(db, user_email)

        # Parse Google Form via Playwright
        form_data = await parse_google_form(form_url, user_email)

        if form_data.get("error") or not form_data.get("questions"):
            err_msg = form_data.get("error", "Failed to fetch form questions. Please check the Google Form URL.")
            raise ValueError(err_msg)

        form_session = FormSession(
            id=session_id,
            form_url=form_url,
            title=form_data.get("title", "Google Form"),
            description=form_data.get("description", ""),
            status="analyzing",
            fill_mode="auto"
        )
        db.add(form_session)
        db.commit()

        # Load enriched user profile
        profiles = db.query(UserProfile).all()
        profile_list = [{"field_key": p.field_key, "field_value": p.field_value} for p in profiles]

        has_missing = False

        for q in form_data.get("questions", []):
            prop_ans, conf, src, is_missing = match_question_to_profile(
                question_text=q["question_text"],
                field_type=q["field_type"],
                options=q.get("options", []),
                profiles=profile_list
            )

            if is_missing and q.get("is_required", False):
                has_missing = True

            fq = FormQuestion(
                session_id=session_id,
                field_id=q["field_id"],
                question_text=q["question_text"],
                field_type=q["field_type"],
                is_required=q["is_required"],
                options=q.get("options", []),
                proposed_answer=prop_ans,
                confidence_score=conf,
                source=src,
                is_missing=is_missing,
                user_answer=prop_ans if not is_missing else ""
            )
            db.add(fq)

        form_session.status = "missing_info" if has_missing else "review"
        db.commit()
        db.refresh(form_session)
        return form_session

    @staticmethod
    def save_missing_information(db: Session, session_id: str, answers: dict, remember_keys: dict):
        session = db.query(FormSession).filter(FormSession.id == session_id).first()
        if not session:
            return None

        for q_id, answer_val in answers.items():
            q = db.query(FormQuestion).filter(FormQuestion.id == int(q_id)).first()
            if q:
                q.user_answer = answer_val
                q.proposed_answer = answer_val
                q.is_missing = False
                q.source = "User"
                q.confidence_score = 1.0

                should_remember = remember_keys.get(str(q_id), False) or remember_keys.get(int(q_id), False)
                if should_remember and answer_val.strip():
                    existing = db.query(UserProfile).filter(UserProfile.field_key == q.question_text).first()
                    if existing:
                        existing.field_value = answer_val
                    else:
                        new_profile = UserProfile(
                            field_key=q.question_text,
                            field_value=answer_val,
                            category="Saved Answers"
                        )
                        db.add(new_profile)

        session.status = "review"
        db.commit()
        return session

    @staticmethod
    async def run_execution(db: Session, session_id: str, fill_mode: str, user_email: str = "default", step_callback=None):
        session = db.query(FormSession).filter(FormSession.id == session_id).first()
        if not session:
            return None

        session.fill_mode = fill_mode
        session.status = "executing"
        db.commit()

        questions_data = []
        for q in session.questions:
            questions_data.append({
                "field_id": q.field_id,
                "question_text": q.question_text,
                "proposed_answer": q.user_answer or q.proposed_answer or "",
                "user_answer": q.user_answer or "",
                "field_type": q.field_type,
                "options": q.options or [],
            })

        # Run Playwright execution flow
        logs = await execute_form_filling(session.form_url, questions_data, fill_mode, user_email, step_callback)

        # Record Submission History
        summary_map = {q.question_text: (q.user_answer or q.proposed_answer or "N/A") for q in session.questions}

        submission = SubmissionHistory(
            session_id=session_id,
            user_email=user_email,
            form_url=session.form_url,
            title=session.title,
            status="completed",
            summary_json=json.dumps(summary_map),
            log_json=json.dumps(logs)
        )
        db.add(submission)

        session.status = "completed"
        db.commit()
        return submission
