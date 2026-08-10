import json
import os
import re
from typing import Any, Dict, List, Optional


class PriorityAgent:
    """
    PriorityAgent of AgentOS.
    Analyzes, compares, ranks, and prioritizes incoming emails based on real-world context,
    deadline urgency, sender importance, user preferences, and opportunities.
    """

    def __init__(self, default_threshold: float = 0.60) -> None:
        self.default_threshold = default_threshold

    def analyze_priority(
        self,
        email: Dict[str, Any],
        existing_emails: List[Dict[str, Any]],
        user_preferences: Optional[Dict[str, Any]] = None,
        calendar_events: Optional[List[Dict[str, Any]]] = None,
        current_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Runs the 10-step Priority Agent Workflow:
        Understand -> Determine Category -> Evaluate Importance -> Score Calculation
        -> Priority Assignment -> Global Ranking -> Explanation -> Thought -> Recommendations -> JSON Output.
        """
        subject = email.get("subject") or email.get("title") or ""
        sender = email.get("sender") or email.get("organizer") or ""
        body = email.get("body") or email.get("email_body") or email.get("description") or ""
        full_text = f"Subject: {subject}\nSender: {sender}\nBody: {body}"

        # Default fallback values for preferences/calendar
        prefs = user_preferences or {
            "preferred_companies": ["google", "microsoft", "amazon", "unstop", "devfolio", "devpost", "techgig"],
            "preferred_categories": ["internship", "placement", "contest", "hackathon"],
            "preferred_technologies": ["ai", "python", "javascript", "machine learning"]
        }
        events = calendar_events or []
        time_now = current_time or "2026-07-30T11:00:00"

        # Attempt to call LLM for rich structured analysis
        llm_result = self._call_llm_priority(full_text, existing_emails, prefs, events, time_now)
        if llm_result:
            # Dynamically compute overall rank based on existing emails
            llm_result["overall_rank"] = self._calculate_global_rank(llm_result.get("priority_score", 0), existing_emails)
            return llm_result

        # Heuristic Backup
        return self._heuristic_priority(email, existing_emails, prefs, events, time_now)

    def _call_llm_priority(
        self,
        text: str,
        existing_emails: List[Dict[str, Any]],
        preferences: Dict[str, Any],
        events: List[Dict[str, Any]],
        current_time: str
    ) -> Optional[Dict[str, Any]]:
        """Invokes Gemini/Groq LLM for strict Priority Agent OS Schema output."""
        groq_key = os.getenv("GROQ_API_KEY")
        api_key = os.getenv("GEMINI_API_KEY")

        # Summarize existing emails to allow ranking comparison context
        existing_summary = []
        for idx, item in enumerate(existing_emails[:10]):
            existing_summary.append({
                "title": item.get("title"),
                "priority": item.get("priority", "Low"),
                "score": item.get("priority_score", 0),
                "date": item.get("date")
            })

        prompt = (
            "You are the Priority Agent of AgentOS, an autonomous AI email assistant.\n"
            "Your responsibility is to intelligently analyze, compare, explain, and prioritize every incoming email exactly like an experienced executive assistant.\n\n"
            f"Current Local Time: {current_time}\n"
            f"User Preferences: {json.dumps(preferences)}\n"
            f"Calendar Events: {json.dumps(events)}\n"
            f"Previously Processed Emails: {json.dumps(existing_summary)}\n\n"
            "Respond ONLY with a valid JSON object matching the following schema. Never output markdown code blocks or text outside this JSON:\n"
            "{\n"
            '  "category": ["Hackathons", "Internships", etc.],\n'
            '  "summary": "Brief 1-sentence summary.",\n'
            '  "priority": "Emergency or High or Medium or Low",\n'
            '  "priority_score": 85,\n'
            '  "urgency_score": 75,\n'
            '  "importance_score": 80,\n'
            '  "opportunity_score": 90,\n'
            '  "deadline_risk_score": 40,\n'
            '  "sender_trust_score": 95,\n'
            '  "user_preference_score": 85,\n'
            '  "attachment_score": 0,\n'
            '  "calendar_conflict_score": 0,\n'
            '  "duplicate_penalty": 0,\n'
            '  "confidence": 98,\n'
            '  "deadline": "YYYY-MM-DD or null",\n'
            '  "meeting_time": "YYYY-MM-DDTHH:MM or null",\n'
            '  "sender_importance": "Official Organization or Company HR or Professor or Unknown",\n'
            '  "attachments": [],\n'
            '  "keywords_detected": ["hackathon", "prize"],\n'
            '  "reason_for_priority": ["Registration closes in 24 hours.", "Prize pool is ₹2 Lakhs."],\n'
            '  "agent_thought": "Missing this deadline would permanently lose the opportunity. Thus scored as High priority.",\n'
            '  "priority_breakdown": {\n'
            '    "urgency": 75,\n'
            '    "importance": 80,\n'
            '    "opportunity": 90,\n'
            '    "deadline": 40,\n'
            '    "sender": 95,\n'
            '    "preferences": 85,\n'
            '    "attachments": 0,\n'
            '    "calendar": 0,\n'
            '    "duplicate_penalty": 0,\n'
            '    "final_score": 85\n'
            '  },\n'
            '  "recommended_actions": ["Dashboard Update", "High Priority Notification"],\n'
            '  "required_agents": ["Trigger Meeting Agent", "Trigger Calendar Agent"]\n'
            "}\n\n"
            f"Email Content to Prioritize:\n{text}"
        )

        if groq_key:
            try:
                import requests
                headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
                payload = {
                    "model": "llama-3.1-8b-instant",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"}
                }
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=10)
                if res.status_code == 200:
                    return json.loads(res.json()["choices"][0]["message"]["content"].strip())
            except Exception:
                pass

        if api_key:
            try:
                from google import genai
                client = genai.Client(api_key=api_key)
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
                        # If it's a 429 quota or other error, let's also try next model as separate metrics may apply
                        continue
                
                if content:
                    if content.startswith("```json"):
                        content = content[7:-3].strip()
                    return json.loads(content)
            except Exception:
                pass

        return None

    def _heuristic_priority(
        self,
        email: Dict[str, Any],
        existing_emails: List[Dict[str, Any]],
        preferences: Dict[str, Any],
        events: List[Dict[str, Any]],
        current_time: str
    ) -> Dict[str, Any]:
        """Provides robust fallback heuristic scoring calculations."""
        subject = (email.get("subject") or email.get("title") or "").lower()
        body = (email.get("body") or email.get("email_body") or email.get("description") or "").lower()
        sender = (email.get("sender") or email.get("organizer") or "").lower()
        text = f"{subject} {sender} {body}"

        # Check pre-classified categories in incoming email dict
        input_category = email.get("category")
        pre_categories = []
        if input_category:
            if isinstance(input_category, list):
                pre_categories = [c.strip() for c in input_category if c.strip()]
            elif isinstance(input_category, str):
                pre_categories = [c.strip() for c in input_category.split(",") if c.strip()]

        # Initialize base scores
        urgency = 20
        importance = 30
        opportunity = 10
        trust = 50
        pref_score = 0
        duplicate_penalty = 0

        reasons = []
        keywords = []

        # 1. Category extraction
        categories = []
        if "meet" in text or "zoom" in text or "teams" in text or "webex" in text or "Meetings" in pre_categories or "Meeting" in pre_categories:
            categories.append("Meetings")
            importance = max(importance, 60)
            urgency = max(urgency, 50)
            reasons.append("Email categorized as or mentions a live meeting/call.")
        if "hackathon" in text or "contest" in text or "competition" in text or "Hackathons" in pre_categories or "Contest" in pre_categories:
            categories.append("Hackathons")
            opportunity = max(opportunity, 80)
            urgency = max(urgency, 40)
            reasons.append("Email categorized as or mentions a hackathon/contest.")
        if "intern" in text or "internship" in text or "Internships" in pre_categories or "Internship" in pre_categories:
            categories.append("Internships")
            opportunity = max(opportunity, 85)
            importance = max(importance, 50)
            reasons.append("Email categorized as or mentions an internship opportunity.")
        if "placement" in text or "job offer" in text or "recruit" in text or "Placements" in pre_categories or "Placement" in pre_categories:
            categories.append("Placements")
            opportunity = max(opportunity, 90)
            importance = max(importance, 70)
            reasons.append("Email categorized as or mentions campus placements or recruitment.")
        if "scholarship" in text or "fellowship" in text or "Scholarships" in pre_categories or "Scholarship" in pre_categories:
            categories.append("Scholarships")
            opportunity = max(opportunity, 75)
            reasons.append("Email categorized as or mentions a scholarship/fellowship.")
        if "cfi" in text or "centre for innovation" in text or "CFI" in pre_categories:
            categories.append("Research")
            trust = max(trust, 85)
            importance = max(importance, 60)
            reasons.append("Email associated with Centre for Innovation (CFI).")
        if "leetcode" in text or "LeetCode" in pre_categories:
            categories.append("LeetCode")
            opportunity = max(opportunity, 70)
            reasons.append("Email associated with LeetCode challenges.")
        if "form" in text or "survey" in text or "feedback" in text or "Form" in pre_categories:
            if "Forms" not in categories:
                categories.append("Forms")
            importance = max(importance, 45)
            reasons.append("Email contains a form or survey response action.")

        if not categories:
            categories.append("Company Emails")

        # 2. Sender checks
        sender_importance = "Unknown"
        if "sece.ac.in" in sender or "sri eshwar" in text:
            trust = 90
            sender_importance = "Official Organization"
            reasons.append("Official college sender domain detected.")
        elif any(domain in sender for domain in ["google", "microsoft", "unstop", "devfolio", "devpost"]):
            trust = 85
            sender_importance = "Official Organization"
            reasons.append(f"Trusted industry domain in sender address: {sender}.")

        if trust >= 85:
            importance = max(importance, 65)

        # 3. User Preferences match
        pref_matches = []
        for word in preferences.get("preferred_companies", []):
            if word in text:
                pref_matches.append(word)
        for word in preferences.get("preferred_technologies", []):
            if word in text:
                pref_matches.append(word)
        for cat in preferences.get("preferred_categories", []):
            if any(cat.lower() in tc.lower() for tc in categories):
                pref_matches.append(cat)
        if pref_matches:
            pref_score = min(90, 40 + len(pref_matches) * 15)
            keywords.extend(pref_matches)
            reasons.append(f"Matches user preferences for: {', '.join(pref_matches)}.")

        # 4. Duplicate checks
        for item in existing_emails:
            existing_title = item.get("title") or item.get("subject")
            incoming_title = email.get("title") or email.get("subject")
            if existing_title and incoming_title and existing_title.lower() == incoming_title.lower():
                duplicate_penalty = 50
                reasons.append("Duplicate check: Email with identical title exists.")
                break

        # 5. Urgent Deadline keyword detection
        deadline_detected = None
        date_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
        if date_match:
            deadline_detected = date_match.group(1)

        if "deadline" in text or "closing" in text or "expire" in text or "due" in text or "last date" in text:
            urgency += 35
            reasons.append("Email mentions a closing registration or deadline.")
            if "tomorrow" in text or "today" in text or "24 hours" in text or "urgent" in text:
                urgency += 35
                reasons.append("Deadline is imminent (today/tomorrow/urgent).")

        # Calculate final overall score
        final_score = int((urgency * 0.35) + (importance * 0.20) + (opportunity * 0.25) + (pref_score * 0.20) - duplicate_penalty)
        final_score = max(0, min(100, final_score))

        # Priority label assignment
        if final_score >= 80:
            priority = "Emergency"
        elif final_score >= 60:
            priority = "High"
        elif final_score >= 35:
            priority = "Medium"
        else:
            priority = "Low"

        # Determine rank
        overall_rank = self._calculate_global_rank(final_score, existing_emails)

        summary = f"Opportunity email about {categories[0]} from {email.get('sender') or email.get('organizer') or 'Unknown'}."

        return {
            "category": categories,
            "summary": summary,
            "overall_rank": overall_rank,
            "priority": priority,
            "priority_score": final_score,
            "urgency_score": urgency,
            "importance_score": importance,
            "opportunity_score": opportunity,
            "deadline_risk_score": 0,
            "sender_trust_score": trust,
            "user_preference_score": pref_score,
            "attachment_score": 0,
            "calendar_conflict_score": 0,
            "duplicate_penalty": duplicate_penalty,
            "confidence": 85,
            "deadline": deadline_detected,
            "meeting_time": None,
            "sender_importance": sender_importance,
            "attachments": [],
            "keywords_detected": keywords,
            "reason_for_priority": reasons or ["Standard inbox item priority assigned."],
            "agent_thought": f"Assigned priority {priority} based on opportunity value and keyword match density.",
            "priority_breakdown": {
                "urgency": urgency,
                "importance": importance,
                "opportunity": opportunity,
                "deadline": 0,
                "sender": trust,
                "preferences": pref_score,
                "attachments": 0,
                "calendar": 0,
                "duplicate_penalty": duplicate_penalty,
                "final_score": final_score
            },
            "recommended_actions": ["Dashboard Update"],
            "required_agents": ["Trigger Meeting Agent"]
        }

    def _calculate_global_rank(self, score: int, existing_emails: List[Dict[str, Any]]) -> int:
        """Determines the 1-indexed overall rank position of the email relative to others."""
        rank = 1
        for item in existing_emails:
            if int(item.get("priority_score") or 0) > score:
                rank += 1
        return rank
