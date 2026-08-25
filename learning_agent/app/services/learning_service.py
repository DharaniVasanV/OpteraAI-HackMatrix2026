"""
app/services/learning_service.py

Learning Agent Version 1.0 - 12-Step Autonomous AI Learning Mentor Engine.
"""

import json
import os
import sys
import uuid
import httpx
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
sys.path.insert(0, r"E:\AgentOS")
from groq_rotation import groq_chat_with_rotation

from app.config.settings import settings
from app.db import models
from app.db.session import AsyncSessionLocal
from app.utils.logger import get_logger

logger = get_logger(__name__)




async def generate_learning_plan(
    raw_payload: Dict[str, Any],
    session: Optional[AsyncSession] = None
) -> Dict[str, Any]:
    """
    Executes the 12-Step Learning Agent Mentor Workflow.
    """
    try:
        # ── Step 1: Extract Input Parameters ─────────────────────────────────
        career_goal    = raw_payload.get("career_goal") or raw_payload.get("learning_goal")
        skills         = raw_payload.get("skills")
        resume         = raw_payload.get("resume")
        job_description = raw_payload.get("job_description")
        technologies   = raw_payload.get("technologies") or raw_payload.get("technologies_to_learn")
        knowledge_level = raw_payload.get("knowledge_level") or raw_payload.get("current_knowledge_level", "Beginner/Intermediate")
        study_time     = raw_payload.get("study_time") or raw_payload.get("available_study_time", "10-15 hours/week")
        learning_style = raw_payload.get("learning_style") or raw_payload.get("preferred_learning_style", "Hands-on Project Based")
        existing_certs = raw_payload.get("existing_certifications") or []
        prompt         = raw_payload.get("prompt")
        experience_level = raw_payload.get("experience_level", "")
        user_id        = raw_payload.get("user_id", "dharanivasan")

        # ── Step 2: Validation ────────────────────────────────────────────────
        if not career_goal and not technologies and not skills and not prompt:
            logger.warning("Step 2 Validation Failed: No learning information provided.")
            return {"status": "failed", "reason": "Please provide a goal, skills, or a custom prompt."}

        # Use experience_level to enrich knowledge_level if provided
        if experience_level and knowledge_level == "Beginner/Intermediate":
            knowledge_level = experience_level.capitalize()

        # ── Step 3: Build Prompts ─────────────────────────────────────────────
        system_prompt = """You are the Learning Agent Version 1.0 of AgentOS, an autonomous AI Learning Mentor.
Your mission is to analyze the user's learning parameters and construct a comprehensive, factual 12-step learning plan and roadmap.

CRITICAL RULES:
1. Never invent user skills or experience.
2. Never exaggerate abilities.
3. Only recommend technologies strictly relevant to the user's career goal.
4. Always provide a realistic roadmap and encourage project-based learning.
5. You MUST return ONLY a valid JSON object matching the exact specification below.

JSON OUTPUT STRUCTURE:
{
  "status": "success",
  "career_goal": "<User Career or Learning Goal>",
  "current_level": "<Assessed Knowledge Level>",
  "missing_skills": ["<Skill 1>", "<Skill 2>"],
  "learning_roadmap": {
    "immediate": ["<Goal 1>", "<Goal 2>"],
    "weekly":    ["<Goal 1>", "<Goal 2>"],
    "monthly":   ["<Goal 1>", "<Goal 2>"],
    "long_term": ["<Goal 1>", "<Goal 2>"]
  },
  "recommended_topics": ["<Topic 1>", "<Topic 2>", "<Topic 3>"],
  "recommended_resources": [
    {
      "title": "<Resource Title>",
      "type": "<Official Docs / Book / Video / Practice Platform / Course>",
      "difficulty": "<Beginner / Intermediate / Advanced>",
      "reason": "<Why this resource is essential>"
    }
  ],
  "practice_recommendations": ["<Project 1>", "<Project 2>"],
  "recommended_certifications": ["<Cert 1>", "<Cert 2>"],
  "daily_plan": [
    "Day 1: <Topic & Practice>",
    "Day 2: <Topic & Practice>",
    "Day 3: <Topic & Practice>",
    "Day 4: <Topic & Practice>",
    "Day 5: <Topic & Practice>",
    "Day 6: <Mini Project>",
    "Day 7: <Weekly Revision & Assessment>"
  ],
  "weekly_schedule": [
    "Week 1: Foundations & Core Concepts",
    "Week 2: Frameworks & Advanced Tools",
    "Week 3: Real-world Hands-on Project",
    "Week 4: Portfolio Integration & Certification Prep"
  ],
  "progress": {"completed": 0, "remaining": 10, "percentage": 0.0},
  "next_milestone": "<Next Immediate Milestone Goal>",
  "motivation": "<Encouraging, constructive, realistic mentor advice>"
}"""

        user_prompt = f"""Target Goal: {career_goal}
Current Skills: {skills}
Resume Details: {resume}
Job Description Context: {job_description}
Technologies to Learn: {technologies}
Current Knowledge Level: {knowledge_level}
Available Study Time: {study_time}
Preferred Learning Style: {learning_style}
Existing Certifications: {existing_certs}
Custom Prompt (PRIORITIZE THIS IF PROVIDED): {prompt}

Generate the complete 12-Step Learning Plan in strict JSON format."""

        # ── Step 4 & 5: Call Groq with shared key+model rotation ─────────────
        raw_content = await groq_chat_with_rotation(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=3000,
        )
        plan_json = json.loads(raw_content)

        # ── Step 7: Attach metadata ───────────────────────────────────────────
        plan_id = str(uuid.uuid4())
        plan_json["plan_id"]    = plan_id
        plan_json["user_id"]    = user_id
        plan_json["created_at"] = datetime.now().isoformat()
        plan_json["status"]     = "success"

        # ── Step 8: Initialise progress ───────────────────────────────────────
        if "progress" not in plan_json or not isinstance(plan_json["progress"], dict):
            total = len(plan_json.get("recommended_topics", [])) or 10
            plan_json["progress"] = {"completed": 0, "remaining": total, "percentage": 0.0}

        # ── Step 9: Save to JSON store (Removed in favor of Postgres) ───

        # ── Step 10: Persist to PostgreSQL ────────────────────────────────────
        if session:
            try:
                db_plan = models.LearningPlan(
                    id=uuid.UUID(plan_id),
                    user_id=user_id,
                    career_goal=plan_json.get("career_goal", str(career_goal)),
                    current_level=plan_json.get("current_level", str(knowledge_level)),
                    missing_skills=plan_json.get("missing_skills", []),
                    learning_roadmap=plan_json.get("learning_roadmap", {}),
                    recommended_topics=plan_json.get("recommended_topics", []),
                    practice_recommendations=plan_json.get("practice_recommendations", []),
                    recommended_certifications=plan_json.get("recommended_certifications", []),
                    daily_plan=plan_json.get("daily_plan", []),
                    weekly_schedule=plan_json.get("weekly_schedule", []),
                    next_milestone=plan_json.get("next_milestone", ""),
                    motivation=plan_json.get("motivation", ""),
                    created_at=datetime.now(),
                )
                session.add(db_plan)

                for r in plan_json.get("recommended_resources", []):
                    db_res = models.LearningResource(
                        id=uuid.uuid4(),
                        plan_id=uuid.UUID(plan_id),
                        title=r.get("title", "Resource"),
                        type=r.get("type", "Tutorial"),
                        difficulty=r.get("difficulty", "Intermediate"),
                        reason=r.get("reason", ""),
                        created_at=datetime.now(),
                    )
                    session.add(db_res)

                db_hist = models.LearningHistory(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    career_goal=plan_json.get("career_goal", str(career_goal)),
                    status="Active",
                    progress_percentage=0.0,
                    created_at=datetime.now(),
                )
                session.add(db_hist)
                await session.commit()
            except Exception as db_err:
                logger.warning(f"PostgreSQL save skipped: {db_err}")

        logger.info(f"✅ Learning plan generated for goal: '{career_goal}'")
        return plan_json

    except Exception as err:
        logger.error(f"Learning plan generation crashed: {err}")
        return {"status": "failed", "reason": str(err)}


async def get_all_plans(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    async with AsyncSessionLocal() as session:
        stmt = select(models.LearningPlan).order_by(models.LearningPlan.created_at.desc())
        if user_id:
            stmt = stmt.where(models.LearningPlan.user_id == user_id)
        res = await session.execute(stmt)
        plans = res.scalars().all()
        # Create a dict representation consistent with original JSON structure
        result = []
        for plan in plans:
            # Check LearningProgress table just in case, or default if missing
            prg_stmt = select(models.LearningProgress).where(models.LearningProgress.plan_id == plan.id)
            prg_res = await session.execute(prg_stmt)
            prog = prg_res.scalars().first()
            prog_dict = {
                "completed": prog.completed_count if prog else 0,
                "remaining": prog.remaining_count if prog else 10,
                "percentage": prog.percentage if prog else 0.0
            }

            result.append({
                "plan_id": str(plan.id),
                "user_id": plan.user_id,
                "career_goal": plan.career_goal,
                "current_level": plan.current_level,
                "missing_skills": plan.missing_skills or [],
                "learning_roadmap": plan.learning_roadmap or {},
                "recommended_topics": plan.recommended_topics or [],
                "practice_recommendations": plan.practice_recommendations or [],
                "recommended_certifications": plan.recommended_certifications or [],
                "daily_plan": plan.daily_plan or [],
                "weekly_schedule": plan.weekly_schedule or [],
                "next_milestone": plan.next_milestone,
                "motivation": plan.motivation,
                "progress": prog_dict,
                "status": "success",
                "created_at": plan.created_at.isoformat() if plan.created_at else ""
            })
        return result


async def update_plan_progress(plan_id: str, completed_increment: int = 1) -> Dict[str, Any]:
    try:
        async with AsyncSessionLocal() as session:
            try:
                pid = uuid.UUID(plan_id)
            except ValueError:
                return {"status": "failed", "reason": "Invalid plan ID."}

            prg_stmt = select(models.LearningProgress).where(models.LearningProgress.plan_id == pid)
            prg_res = await session.execute(prg_stmt)
            prog = prg_res.scalars().first()

            if not prog:
                prog = models.LearningProgress(
                    plan_id=pid,
                    user_id="default",
                    completed_count=completed_increment,
                    remaining_count=max(0, 10 - completed_increment)
                )
                session.add(prog)
            else:
                prog.completed_count += completed_increment
                prog.remaining_count = max(0, prog.remaining_count - completed_increment)
                
            total = prog.completed_count + prog.remaining_count
            prog.percentage = round((prog.completed_count / total) * 100, 1) if total > 0 else 100.0
            prog.updated_at = datetime.utcnow()

            await session.commit()
            
            return {
                "status": "success", 
                "plan_id": plan_id, 
                "progress": {
                    "completed": prog.completed_count,
                    "remaining": prog.remaining_count,
                    "percentage": prog.percentage
                }
            }
    except Exception as e:
        logger.error(f"Error updating progress: {e}")
        return {"status": "failed", "reason": str(e)}


async def delete_plan_record(plan_id: str) -> bool:
    try:
        async with AsyncSessionLocal() as session:
            try:
                pid = uuid.UUID(plan_id)
            except ValueError:
                return False
            
            stmt = delete(models.LearningPlan).where(models.LearningPlan.id == pid)
            await session.execute(stmt)
            
            # Additional cascading deletions could go here if relationship not set up
            await session.commit()
            return True
    except Exception:
        return False
