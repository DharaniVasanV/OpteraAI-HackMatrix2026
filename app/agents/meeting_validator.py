import re
from typing import Dict, Optional, Tuple

VIDEO_MEETING_PATTERNS = [
    ("Google Meet", r"https://meet\.google\.com/[a-z0-9-]+"),
    ("Microsoft Teams", r"https://teams\.(microsoft|live)\.com/[^\s\"'>]+"),
    ("Zoom", r"https://([a-z0-9\-]+\.)?zoom\.us/(j|my|w)/[^\s\"'>]+"),
    ("Cisco Webex", r"https://([a-z0-9\-]+\.)?webex\.com/[^\s\"'>]+"),
    ("Skype", r"https://join\.skype\.com/[^\s\"'>]+"),
    ("GoToMeeting", r"https://(gotomeet\.me|global\.gotomeeting\.com/join)/[^\s\"'>]+"),
    ("Whereby", r"https://whereby\.com/[^\s\"'>]+"),
    ("Jitsi", r"https://meet\.jit\.si/[^\s\"'>]+"),
]

FORM_PATTERNS = [
    ("Google Forms", r"https://(forms\.gle|docs\.google\.com/forms)/[^\s\"'>]+"),
    ("Microsoft Forms", r"https://forms\.(office|microsoft)\.com/[^\s\"'>]+"),
    ("Typeform", r"https://[a-z0-9\-]+\.typeform\.com/[^\s\"'>]+"),
    ("Jotform", r"https://(form\.)?jotform\.com/[^\s\"'>]+"),
    ("SurveyMonkey", r"https://[a-z0-9\-]+\.surveymonkey\.com/[^\s\"'>]+"),
]


def clean_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    return url.rstrip(".,;:!?()[]{}<>\"'")


def extract_video_meeting_link(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extracts ONLY genuine video meeting links (Google Meet, Zoom, MS Teams, Webex, Skype, etc.)
    """
    for platform_name, pattern in VIDEO_MEETING_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return clean_url(match.group(0)), platform_name
    return None, None


def extract_form_link(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extracts form/survey/registration links (Google Forms, MS Forms, Typeform, etc.).
    """
    for platform_name, pattern in FORM_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return clean_url(match.group(0)), platform_name
    return None, None


APPLICATION_PATTERNS = [
    ("Unstop", r"https://(?:www\.)?unstop\.com/[^\s\"'>]+"),
    ("Devfolio", r"https://(?:[a-z0-9\-]+\.)?devfolio\.co/[^\s\"'>]+"),
    ("Devpost", r"https://(?:[a-z0-9\-]+\.)?devpost\.com/[^\s\"'>]+"),
    ("DoraHacks", r"https://(?:www\.)?dorahacks\.io/[^\s\"'>]+"),
    ("LeetCode", r"https://(?:www\.)?leetcode\.com/[^\s\"'>]+"),
    ("HackerEarth", r"https://(?:www\.)?hackerearth\.com/[^\s\"'>]+"),
    ("HackerRank", r"https://(?:www\.)?hackerrank\.com/[^\s\"'>]+"),
    ("Internshala", r"https://(?:www\.)?internshala\.com/[^\s\"'>]+"),
    ("LinkedIn", r"https://(?:www\.)?linkedin\.com/jobs/[^\s\"'>]+"),
]


def extract_application_link(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extracts application/platform links (Unstop, Devfolio, LeetCode, etc.).
    """
    for platform_name, pattern in APPLICATION_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return clean_url(match.group(0)), platform_name
    return None, None


def extract_any_actionable_link(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extracts the best actionable link from text. Priority: video meeting > form > application > first generic URL.
    """
    # 1. Try video meeting link first
    link, platform = extract_video_meeting_link(text)
    if link:
        return link, platform

    # 2. Try form link
    link, platform = extract_form_link(text)
    if link:
        return link, platform

    # 3. Try application platform link
    link, platform = extract_application_link(text)
    if link:
        return link, platform

    # 4. Fallback: extract first generic HTTP(S) URL
    generic_match = re.search(r"https?://[^\s\"'>]+", text, re.IGNORECASE)
    if generic_match:
        url = clean_url(generic_match.group(0))
        # Skip common non-actionable URLs
        skip_domains = ['google.com/search', 'mail.google.com', 'accounts.google.com', 'support.google.com']
        if not any(d in url.lower() for d in skip_domains):
            return url, None

    return None, None


def extract_meeting_link(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extracts ONLY genuine video meeting links. Returns (None, None) for forms, LeetCode, or generic web links.
    """
    return extract_video_meeting_link(text)


def is_video_meeting_url(url: Optional[str]) -> bool:
    if not url:
        return False
    url_lower = url.lower()
    meeting_domains = ["meet.google.com", "zoom.us", "teams.microsoft.com", "teams.live.com", "webex.com", "join.skype.com", "gotomeet.me", "gotomeeting.com", "whereby.com", "meet.jit.si"]
    return any(domain in url_lower for domain in meeting_domains)


def validate_meeting(email: dict) -> Dict[str, object]:
    subject = email.get("subject", "")
    body = email.get("body", "")
    full_text = f"{subject}\n{body}"

    video_link, video_platform = extract_video_meeting_link(full_text)
    is_video = bool(video_link)

    # Check for form platform links if no video link
    form_platform = None
    if not video_link:
        for p_name, pattern in FORM_PATTERNS:
            if re.search(pattern, full_text, re.IGNORECASE):
                form_platform = p_name
                break

    has_calendar_invite = "BEGIN:VCALENDAR" in full_text or ".ics" in full_text.lower()
    has_form_keyword = any(kw in full_text.lower() for kw in ["google form", "ms form", "feedback form", "registration form", "survey form", "fill out", "rsvp"])
    has_other_keywords = any(kw in full_text.lower() for kw in ["scholarship", "fellowship", "grant", "bursary", "financial aid", "intern", "placement", "job", "contest", "hackathon", "competition", "leetcode"])
    has_meeting_keyword = any(kw in full_text.lower() for kw in ["meeting", "zoom call", "google meet", "teams meeting", "webex", "huddle", "sync", "standup", "discussion"])

    is_valid = is_video or has_calendar_invite or has_form_keyword or has_other_keywords or has_meeting_keyword

    platform_name = video_platform or (
        "Google Calendar" if has_calendar_invite else (
            form_platform or (
                "Registration Form" if has_form_keyword else (
                    "Application Portal" if has_other_keywords else None
                )
            )
        )
    )

    return {
        "valid": is_valid,
        "platform": platform_name,
        "meeting_link": video_link,  # STRICT: ONLY video meeting links
        "is_video_meeting": is_video,
    }

