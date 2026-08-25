import os

# Isolate unit tests to an in-memory SQLite database so they never touch meetings.db
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.agents.database_manager import MeetingStore
from app.agents.duplicate_detector import find_duplicate, merge_meeting
from app.agents.email_classifier import classify_email
from app.agents.information_extractor import extract_meeting
from app.agents.meeting_validator import validate_meeting, extract_meeting_link
from app.agents.notification_agent import NotificationAgent


def test_pipeline_extracts_and_deduplicates_meetings():
    sample_email = {
        "id": "email-101",
        "subject": "Quarterly Planning Review 2026-07-25",
        "sender": "alex@example.com",
        "body": "Join meeting at https://meet.google.com/abc-defg-hij at 09:00 UTC",
        "timestamp": "2026-07-25T09:00:00",
    }

    classification = classify_email(sample_email)
    assert classification["is_meeting"] is True

    validation = validate_meeting(sample_email)
    assert validation["valid"] is True

    extracted = extract_meeting(sample_email)
    assert extracted["title"] == "Quarterly Planning Review 2026-07-25"
    assert extracted["meeting_link"] == "https://meet.google.com/abc-defg-hij"

    store = MeetingStore()
    first_record = store.add_meeting(extracted)

    duplicate = find_duplicate(store, extracted)
    assert duplicate is not None

    merged = merge_meeting(first_record, {**extracted, "start_time": "11:00"})
    assert merged["status"] == "updated"
    updated_record = store.add_meeting(merged)
    assert updated_record["start_time"] == "11:00"


def test_multi_platform_validation():
    zoom_text = "Join Zoom Meeting https://us02web.zoom.us/j/123456789"
    link, platform = extract_meeting_link(zoom_text)
    assert platform == "Zoom"
    assert "zoom.us" in link

    teams_text = "Join Microsoft Teams Meeting https://teams.microsoft.com/l/meetup-join/123"
    link, platform = extract_meeting_link(teams_text)
    assert platform == "Microsoft Teams"

    webex_text = "Join Cisco Webex https://company.webex.com/meet/user"
    link, platform = extract_meeting_link(webex_text)
    assert platform == "Cisco Webex"

    # Non-video meeting links (e.g. Google Forms / MS Forms) return None for meeting link
    gforms_text = "Please fill out this survey https://forms.gle/xyz123"
    link, platform = extract_meeting_link(gforms_text)
    assert link is None
    assert platform is None


def test_notifications():
    store = MeetingStore()
    store.add_meeting({
        "title": "Cancelled Sync",
        "status": "cancelled",
        "organizer": "alice@example.com"
    })
    agent = NotificationAgent(store)
    notifs = agent.get_upcoming_notifications()
    assert len(notifs) >= 1
    assert any("Cancelled" in n["title"] for n in notifs)


def test_scholarship_classification_and_extraction():
    scholarship_email = {
        "id": "email-202",
        "subject": "Graduate Fellowship Program 2026",
        "sender": "fellowships@institution.org",
        "body": "Apply for the fellowship grant at https://institution.org/fellowship by 2026-09-01.",
        "timestamp": "2026-07-29T12:00:00",
    }
    classification = classify_email(scholarship_email)
    assert classification["category"] == "scholarship"

    validation = validate_meeting(scholarship_email)
    assert validation["valid"] is True
    # Non-video meeting links return None for meeting_link
    assert validation["meeting_link"] is None

    extracted = extract_meeting(scholarship_email)
    assert extracted["meeting_link"] is None


def test_classification_agent():
    from Classification_Agent import ClassificationAgent
    agent = ClassificationAgent()
    
    categories = ["Meeting", "Form", "Scholarship", "Internship", "Placement", "Contest", "LeetCode", "CFI", "Hackathons"]
    
    internship_email = {
        "subject": "Summer UX Research Intern 2026",
        "body": "Apply for the internship role using Google Forms."
    }
    category = agent.classify(internship_email, categories)
    cats_list = [c.strip() for c in category.split(",")]
    assert "Internship" in cats_list
    assert "Form" in cats_list

    contest_email = {
        "subject": "National Coding Competition 2026",
        "body": "Participate in the hackathon challenge and win prizes!"
    }
    category = agent.classify(contest_email, categories)
    cats_list = [c.strip() for c in category.split(",")]
    assert "Contest" in cats_list

    leetcode_email = {
        "subject": "LeetCode Weekly Contest 390",
        "body": "Join the coding challenge on LeetCode this Sunday."
    }
    category = agent.classify(leetcode_email, categories)
    cats_list = [c.strip() for c in category.split(",")]
    assert "LeetCode" in cats_list
    assert "Contest" in cats_list

    cfi_email = {
        "sender": "CFI Sece",
        "subject": "Build for India hackathon event details",
        "body": "Submit your innovations and win cash prizes."
    }
    category = agent.classify(cfi_email, categories)
    cats_list = [c.strip() for c in category.split(",")]
    assert "CFI" in cats_list
    assert "Contest" in cats_list

    embedded_cfi_email = {
        "sender": "external-partner@example.com",
        "subject": "Innovation opportunities next week",
        "body": "Greetings from the team. We are hosting this event together with cfi."
    }
    category = agent.classify(embedded_cfi_email, categories)
    cats_list = [c.strip() for c in category.split(",")]
    assert "CFI" in cats_list


def test_meeting_link_extracted_for_other_mail_category():
    from Classification_Agent import ClassificationAgent
    from app.agents.meeting_validator import validate_meeting
    agent = ClassificationAgent()
    categories = ["Meeting", "Scholarship", "Internship"]

    # Email is primarily about a scholarship, but contains a Google Meet link for Q&A
    scholarship_meeting_email = {
        "id": "email-303",
        "subject": "Scholarship Guidance Q&A Session",
        "sender": "grant@edu.org",
        "body": "Join our live scholarship info session at https://meet.google.com/xyz-1234-abc on 2026-08-10.",
        "timestamp": "2026-07-30T10:00:00"
    }

    validation = validate_meeting(scholarship_meeting_email)
    assert validation["valid"] is True
    assert validation["is_video_meeting"] is True
    assert validation["meeting_link"] == "https://meet.google.com/xyz-1234-abc"
    assert validation["platform"] == "Google Meet"

    classified_cat = agent.classify(scholarship_meeting_email, categories)
    cats = [c.strip() for c in classified_cat.split(",")]
    assert "Scholarship" in cats
    assert "Meeting" in cats


def test_hackathon_email_classified_as_form_and_contest_not_meeting():
    from Classification_Agent import ClassificationAgent
    from app.agents.meeting_validator import validate_meeting
    agent = ClassificationAgent()
    categories = ["Meeting", "Form", "Scholarship", "Internship", "Placement", "Contest", "LeetCode", "CFI"]

    hackathon_email = {
        "id": "email-404",
        "subject": "Hackathon registration ending July 31st - Sri Eshwar",
        "sender": "batch2024@sece.ac.in",
        "body": "Dear Students, Please go through below listed hackathons: ETHGlobal Lisbon https://forms.gle/yvXRs43bRnibcwhX9, DIVE 2026 https://forms.gle/xwjnqL73xe3rJqwZ6. Centre for Innovation, Sri Eshwar College of Engineering.",
        "timestamp": "2026-07-30T10:00:00"
    }

    validation = validate_meeting(hackathon_email)
    assert validation["is_video_meeting"] is False
    assert validation["meeting_link"] is None

    category_res = agent.classify(hackathon_email, categories)
    cats = [c.strip() for c in category_res.split(",")]
    
    assert "Form" in cats or "Contest" in cats or "CFI" in cats
    assert "Meeting" not in cats


def test_priority_agent():
    from Priority_Agent import PriorityAgent
    agent = PriorityAgent()

    hackathon_email = {
        "subject": "ETHGlobal Lisbon Hackathon Registration Deadline",
        "sender": "noreply@ethglobal.com",
        "body": "Hi student, the deadline to register for ETHGlobal Lisbon is tomorrow. Solve problems and win from a ₹2 Lakh prize pool!"
    }
    existing = [
        {"title": "Low priority newsletter", "priority_score": 10, "priority": "Low", "date": "2026-07-28"}
    ]

    prio_res = agent.analyze_priority(hackathon_email, existing)
    assert prio_res["priority"] in ["High", "Emergency", "Medium"]
    assert prio_res["priority_score"] > 50
    assert prio_res["overall_rank"] == 1
    assert "Hackathons" in prio_res["category"] or "Company Emails" in prio_res["category"]
    assert len(prio_res["reason_for_priority"]) >= 1


