import hashlib
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

try:
    from google import genai
except ImportError:
    genai = None


class ClassificationResult(dict):
    """
    Structured classification result object returned by ClassificationAgent.
    Acts as a rich dictionary containing categories, confidence scores, reasoning,
    extracted entities, and agent thoughts, while preserving backward compatibility
    for string operations (.split(), str(), comparison).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def category_string(self) -> str:
        return self.get("category_string", "Other")

    def __str__(self) -> str:
        return self.category_string

    def __repr__(self) -> str:
        primary = self.get("primary_category", "Other")
        return f"<ClassificationResult '{self.category_string}' (Primary: {primary})>"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return (
                self.category_string.lower() == other.lower()
                or self.get("primary_category", "").lower() == other.lower()
            )
        return super().__eq__(other)

    def split(self, sep=None, maxsplit=-1):
        return self.category_string.split(sep, maxsplit)


class ClassificationAgent:
    """
    AgentOS Classification Agent.
    Executes a structured agentic workflow to analyze, extract entities from,
    and categorize incoming emails with confidence scoring, explainable reasoning,
    caching, and extensible JSON category configurations.
    """

    def __init__(self, config_path: Optional[str] = None, confidence_threshold: float = 0.60) -> None:
        self.confidence_threshold = confidence_threshold
        self._cache: Dict[str, ClassificationResult] = {}
        
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "categories.json")
        self.config_path = config_path
        self.category_config = self._load_config(config_path)

    def _load_config(self, path: str) -> List[Dict[str, Any]]:
        """Loads extensible category configuration from JSON."""
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("categories", [])
            except Exception as e:
                print(f"Warning: Failed to load category config from {path}: {e}")

        # Fallback default categories
        return [
            {
                "name": "Meeting",
                "keywords": ["meeting", "google meet", "zoom call", "teams meeting", "webex", "skype call", "huddle", "sync call", "standup call", "video call", "calendar invite"],
                "description": "Live video meetings, calls, webinars, or calendar invites"
            },
            {
                "name": "Form",
                "keywords": ["form", "forms.gle", "docs.google.com/forms", "forms.office.com", "survey", "rsvp", "feedback", "fill out"],
                "description": "Circulated forms, surveys, or registration forms"
            },
            {
                "name": "Scholarship",
                "keywords": ["scholarship", "fellowship", "grant", "bursary", "financial aid"],
                "description": "Scholarships, grants, or financial aid announcements"
            },
            {
                "name": "Internship",
                "keywords": ["intern", "internship", "co-op", "apprentice"],
                "description": "Internship roles, co-op opportunities, or student trainee postings"
            },
            {
                "name": "Placement",
                "keywords": ["placement", "job offer", "recruitment", "hired", "career"],
                "description": "Campus placements, job offers, or recruitment drives"
            },
            {
                "name": "Contest",
                "keywords": ["contest", "competition", "codechef", "codeforces", "hackerearth", "prize", "unstop"],
                "description": "Coding contests or competitive challenges"
            },
            {
                "name": "Hackathon",
                "keywords": ["hackathon", "devpost", "devfolio", "dorahacks", "buildathon"],
                "description": "Hackathons, buildathons, or coding marathons"
            },
            {
                "name": "CFI",
                "keywords": ["cfi", "centre for innovation", "sri eshwar"],
                "description": "Centre for Innovation events and announcements"
            },
            {
                "name": "LeetCode",
                "keywords": ["leetcode", "weekly contest", "biweekly contest"],
                "description": "LeetCode challenges and contest notifications"
            }
        ]

    def _compute_hash(self, email: dict, categories: List[str]) -> str:
        """Calculates a unique SHA-256 hash for email caching."""
        key = f"{email.get('id', '')}:{email.get('subject', '')}:{email.get('body', '')}:{sorted(categories)}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def _preprocess(self, email: dict) -> Tuple[str, str, str, str]:
        """Preprocesses email once into normalized single text string."""
        subject = email.get("subject", "") or ""
        sender = email.get("sender", "") or ""
        body = email.get("body", "") or ""
        full_text = f"Subject: {subject}\nSender: {sender}\nBody: {body}"
        return subject, sender, body, full_text.lower()

    def _extract_entities(self, full_text_lower: str, sender: str) -> Dict[str, Any]:
        """Extracts metadata entities (URLs, video meeting platforms, dates, times) in one pass."""
        links = re.findall(r"https?://[^\s\"'>]+", full_text_lower)
        
        from app.agents.meeting_validator import is_video_meeting_url, extract_video_meeting_link
        video_link, video_platform = extract_video_meeting_link(full_text_lower)

        date_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", full_text_lower)
        meeting_date = date_match.group(1) if date_match else None

        time_matches = re.findall(r"\b(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)\b", full_text_lower)
        start_time = time_matches[0] if time_matches else None

        return {
            "meeting_platform": video_platform if is_video_meeting_url(video_link) else None,
            "meeting_link": video_link if is_video_meeting_url(video_link) else None,
            "links": links,
            "meeting_time": f"{meeting_date}T{start_time}" if meeting_date and start_time else meeting_date or start_time,
            "date": meeting_date,
            "start_time": start_time,
            "organizer": sender,
            "deadline": meeting_date,
        }

    def _classify_llm(self, text: str, categories: List[str]) -> Optional[Dict[str, Any]]:
        """Calls Groq or Gemini with structured AgentOS classification prompt."""
        groq_key = os.getenv("GROQ_API_KEY")
        api_key = os.getenv("GEMINI_API_KEY")
        categories_str = ", ".join(categories)

        prompt = (
            "You are the Classification Agent of AgentOS.\n"
            "Your responsibility is to analyze the email, extract key entities, and classify it into one or more relevant categories.\n"
            f"Allowed Categories: {categories_str}\n\n"
            "Respond ONLY with a valid JSON object with the following schema:\n"
            "{\n"
            '  "agent_thought": "Brief step-by-step reasoning explaining the classification decision.",\n'
            '  "categories": [\n'
            "    {\n"
            '      "name": "CategoryName",\n'
            '      "confidence": 0.95,\n'
            '      "reason": "Specific evidence supporting this category."\n'
            "    }\n"
            "  ],\n"
            '  "entities": {\n'
            '    "meeting_platform": "Google Meet or null",\n'
            '    "meeting_time": "YYYY-MM-DDTHH:MM or null",\n'
            '    "deadline": "YYYY-MM-DD or null",\n'
            '    "organizer": "sender email or null",\n'
            '    "links": ["url1", "url2"]\n'
            "  }\n"
            "}\n\n"
            f"Email Content:\n{text}"
        )

        try:
            import sys
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            
            from groq_rotation import groq_chat_sync
            content = groq_chat_sync(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                response_format={"type": "json_object"}
            )
            if content:
                return json.loads(content)
        except Exception:
            pass

        if api_key and genai:
            try:
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
                        continue

                if content:
                    if content.startswith("```json"):
                        content = content[7:-3].strip()
                    return json.loads(content)
            except Exception:
                pass

        return None

    def _heuristic_classify(
        self, full_text_lower: str, subject: str, categories: List[str], entities: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Heuristic rule-based category scoring with confidence and reasoning."""
        scored_categories = []
        is_video = bool(entities.get("meeting_platform"))
        subject_lower = subject.lower()

        # Build config lookup
        config_map = {c["name"]: c for c in self.category_config}

        for cat_name in categories:
            confidence = 0.0
            reasons = []

            cfg = config_map.get(cat_name, {"keywords": [cat_name.lower()]})
            keywords = cfg.get("keywords", [cat_name.lower()])

            # Check keyword matches in subject or body
            subject_matches = [kw for kw in keywords if kw in subject_lower]
            body_matches = [kw for kw in keywords if kw in full_text_lower]

            if subject_matches:
                confidence = max(confidence, 0.85)
                reasons.append(f"Subject matched keywords: {', '.join(subject_matches)}.")

            if body_matches:
                confidence = max(confidence, 0.75)
                reasons.append(f"Content matched keywords: {', '.join(body_matches[:3])}.")

            # Platform and domain specific rule boosts
            if cat_name == "Meeting":
                if is_video:
                    confidence = 0.98
                    reasons = [f"Detected live video meeting platform: {entities.get('meeting_platform')}."]
                elif "meeting" in subject_lower:
                    confidence = max(confidence, 0.85)
                    reasons.append("Subject explicitly announces a meeting.")
                else:
                    # Penalize Meeting if no video link
                    confidence = 0.20
                    reasons.append("No video call link detected in email body.")

            elif cat_name == "Form" and (any(k in full_text_lower for k in ["form", "forms.gle", "docs.google.com/forms", "forms.office.com", "survey"])):
                confidence = max(confidence, 0.90)
                reasons.append("Form / survey URL or registration terms detected.")

            elif cat_name == "Contest" and (any(k in full_text_lower for k in ["contest", "competition", "codechef", "codeforces", "hackerearth", "unstop"])):
                confidence = max(confidence, 0.92)
                reasons.append("Contest platform link or challenge terms detected.")

            elif cat_name == "Hackathon" and (any(k in full_text_lower for k in ["hackathon", "devpost", "devfolio", "dorahacks", "buildathon"])):
                confidence = max(confidence, 0.94)
                reasons.append("Hackathon or buildathon terms detected.")

            elif cat_name == "Scholarship" and (any(k in full_text_lower for k in ["scholarship", "fellowship", "grant", "bursary", "financial aid"])):
                confidence = max(confidence, 0.90)
                reasons.append("Scholarship or fellowship terms detected.")

            elif cat_name == "Internship" and (any(k in full_text_lower for k in ["intern", "internship", "co-op", "apprentice"])):
                confidence = max(confidence, 0.90)
                reasons.append("Internship or apprentice terms detected.")

            elif cat_name == "Placement" and (any(k in full_text_lower for k in ["placement", "job offer", "recruitment", "career"])):
                confidence = max(confidence, 0.90)
                reasons.append("Placement or job recruitment terms detected.")

            elif cat_name == "CFI" and (any(k in full_text_lower for k in ["cfi", "centre for innovation", "sri eshwar"])):
                confidence = max(confidence, 0.95)
                reasons.append("Centre for Innovation branding detected.")

            elif cat_name == "LeetCode" and (any(k in full_text_lower for k in ["leetcode"])):
                confidence = max(confidence, 0.95)
                reasons.append("LeetCode contest branding detected.")

            confidence = round(min(1.0, max(0.0, confidence)), 2)

            if confidence >= self.confidence_threshold:
                scored_categories.append({
                    "name": cat_name,
                    "confidence": confidence,
                    "reason": " ".join(reasons) or f"Match criteria met for {cat_name}."
                })

        return scored_categories

    def classify(self, email: dict, categories: List[str]) -> ClassificationResult:
        """
        Executes the Classification Agent Workflow:
        Receive Email -> Preprocess -> Extract Links & Entities -> LLM / Heuristic Classification
        -> Score Validation -> Thought Generation -> Cache -> Return ClassificationResult.
        """
        # Step 1: Cache Check
        email_hash = self._compute_hash(email, categories)
        if email_hash in self._cache:
            return self._cache[email_hash]

        # Step 2: Preprocess & Extract Entities
        subject, sender, body, full_text_lower = self._preprocess(email)
        extracted_entities = self._extract_entities(full_text_lower, sender)

        # Step 3: Classification Engine (LLM with Heuristic Fallback)
        raw_llm_data = self._classify_llm(f"Subject: {subject}\nSender: {sender}\nBody: {body}", categories)
        
        final_categories = []
        agent_thought = ""

        if raw_llm_data and "categories" in raw_llm_data:
            agent_thought = raw_llm_data.get("agent_thought", "LLM classified email based on semantic analysis.")
            llm_cats = raw_llm_data.get("categories", [])
            for item in llm_cats:
                c_name = item.get("name")
                c_conf = float(item.get("confidence", 0.0))
                c_reason = item.get("reason", "Identified by LLM.")
                
                # Match ignoring case
                matched_category = next((cat for cat in categories if cat.lower() == str(c_name).lower()), None)
                
                # Enforce confidence threshold
                if matched_category and c_conf >= self.confidence_threshold:
                    # Enforce strict video meeting rule
                    if matched_category == "Meeting" and not extracted_entities.get("meeting_platform") and "meeting" not in subject.lower():
                        continue
                    final_categories.append({
                        "name": matched_category,
                        "confidence": c_conf,
                        "reason": c_reason
                    })
            
            # Merge extracted entities
            llm_entities = raw_llm_data.get("entities", {})
            if isinstance(llm_entities, dict):
                for k, v in llm_entities.items():
                    if v and not extracted_entities.get(k):
                        extracted_entities[k] = v

        # Fallback to Heuristic engine if LLM returned no acceptable categories
        if not final_categories:
            final_categories = self._heuristic_classify(full_text_lower, subject, categories, extracted_entities)
            reasons_summary = "; ".join([f"{c['name']} ({c['confidence']*100:.0f}%: {c['reason']})" for c in final_categories])
            agent_thought = f"Agent analyzed email text and extracted entities. Matches: {reasons_summary or 'No categories met threshold.'}"

        # Sort categories by confidence descending
        final_categories.sort(key=lambda x: x["confidence"], reverse=True)

        # Select primary category
        primary_category = final_categories[0]["name"] if final_categories else "Other"
        category_names = [c["name"] for c in final_categories] if final_categories else ["Other"]
        category_string = ", ".join(category_names)

        # Final Agent Thought
        if not agent_thought:
            agent_thought = f"Identified primary category '{primary_category}' with categories [{category_string}]."

        result = ClassificationResult({
            "categories": final_categories,
            "primary_category": primary_category,
            "category_string": category_string,
            "confidence_threshold": self.confidence_threshold,
            "entities": extracted_entities,
            "agent_thought": agent_thought
        })

        # Cache result
        self._cache[email_hash] = result
        return result
