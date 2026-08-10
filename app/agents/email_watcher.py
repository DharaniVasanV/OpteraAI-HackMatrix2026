import base64
import os
import re
from typing import Dict, List, Tuple

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
except ImportError:
    Credentials = None
    build = None


def _load_env_dict() -> Dict[str, str]:
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env_path = os.path.join(project_root, ".env")
    if not os.path.exists(env_path):
        return {}
    values = {}
    with open(env_path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            values[key.strip()] = val.strip()
    return values


def watch_inbox() -> List[Dict[str, object]]:
    env_dict = _load_env_dict()

    token = env_dict.get("GMAIL_ACCESS_TOKEN") or os.getenv("GMAIL_ACCESS_TOKEN")
    refresh_token = env_dict.get("GMAIL_REFRESH_TOKEN") or os.getenv("GMAIL_REFRESH_TOKEN")
    client_id = env_dict.get("GMAIL_CLIENT_ID") or os.getenv("GMAIL_CLIENT_ID")
    client_secret = env_dict.get("GMAIL_CLIENT_SECRET") or os.getenv("GMAIL_CLIENT_SECRET")

    if token and refresh_token and client_id and client_secret and Credentials and build:
        try:
            creds = Credentials(
                token=token,
                refresh_token=refresh_token,
                client_id=client_id,
                client_secret=client_secret,
                token_uri="https://oauth2.googleapis.com/token",
                scopes=["https://www.googleapis.com/auth/gmail.readonly"],
            )
            service = build("gmail", "v1", credentials=creds)
            def _safe_b64decode(data: str) -> str:
                if not data:
                    return ""
                try:
                    # Pad the base64 string to a multiple of 4 bytes
                    padded = data + "=" * ((4 - len(data) % 4) % 4)
                    return base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8", errors="ignore")
                except Exception as e:
                    print(f"Base64 decode error: {e}")
                    return ""

            def _extract_body(part) -> Tuple[str, str]:
                """Recursively extracts text/plain and text/html from message parts."""
                mime_type = part.get("mimeType", "")
                body_data = part.get("body", {}).get("data", "")
                
                text_content = ""
                html_content = ""
                
                if body_data and mime_type == "text/plain":
                    text_content = _safe_b64decode(body_data)
                elif body_data and mime_type == "text/html":
                    html_content = _safe_b64decode(body_data)
                
                parts = part.get("parts", [])
                for p in parts:
                    sub_text, sub_html = _extract_body(p)
                    if sub_text:
                        text_content += "\n" + sub_text
                    if sub_html:
                        html_content += "\n" + sub_html
                        
                return text_content.strip(), html_content.strip()

            def _strip_html(html_str: str) -> str:
                import html as html_lib
                # Remove style & script blocks
                html_str = re.sub(r"<(script|style).*?>.*?</\1>", "", html_str, flags=re.DOTALL | re.IGNORECASE)
                
                # Convert anchor tags to text representation containing target URL, e.g. TEXT (URL)
                def replace_anchor(match):
                    tag_attrs = match.group(1)
                    text_content = match.group(2)
                    href_match = re.search(r'href=["\']?([^"\'>\s]+)["\']?', tag_attrs, re.IGNORECASE)
                    if href_match:
                        url = href_match.group(1)
                        if url.startswith("http"):
                            return f"{text_content} ({url})"
                    return text_content
                
                html_str = re.sub(r'<a\s+([^>]*?)>(.*?)</a>', replace_anchor, html_str, flags=re.DOTALL | re.IGNORECASE)

                # Replace common tags with layout spacing
                html_str = re.sub(r"<br\s*/?>", "\n", html_str, flags=re.IGNORECASE)
                html_str = re.sub(r"</p>", "\n\n", html_str, flags=re.IGNORECASE)
                html_str = re.sub(r"<div.*?>", "\n", html_str, flags=re.IGNORECASE)
                html_str = re.sub(r"<li.*?>", "\n- ", html_str, flags=re.IGNORECASE)
                html_str = re.sub(r"<h[1-6].*?>", "\n\n", html_str, flags=re.IGNORECASE)
                # Strip remaining HTML tags
                plain = re.sub(r"<.*?>", "", html_str, flags=re.DOTALL)
                # Unescape HTML entities
                plain = html_lib.unescape(plain)
                
                # Format clean whitespace line gaps
                lines = [line.strip() for line in plain.splitlines()]
                clean_lines = []
                for line in lines:
                    if line:
                        clean_lines.append(line)
                    elif not clean_lines or clean_lines[-1] != "":
                        clean_lines.append("")
                return "\n".join(clean_lines).strip()

            # Query past inbox messages (fetch all recent up to maxResults so they can be classified)
            results = service.users().messages().list(userId="me", maxResults=50).execute()
            messages = results.get("messages", [])
            emails = []
            
            download_dir = os.path.join("d:\\", "Document Agent", "downloads")
            os.makedirs(download_dir, exist_ok=True)
            
            for msg in messages:
                full = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
                payload = full.get("payload", {})
                headers = {h["name"].lower(): h.get("value", "") for h in payload.get("headers", [])}
                
                plain_txt, html_txt = _extract_body(payload)
                if not plain_txt and html_txt:
                    plain_txt = _strip_html(html_txt)
                elif not plain_txt and payload.get("body", {}).get("data"):
                    # Single part fallback
                    data = _safe_b64decode(payload["body"]["data"])
                    if payload.get("mimeType") == "text/html":
                        plain_txt = _strip_html(data)
                    else:
                        plain_txt = data
                
                attachments = []
                
                def extract_attachments(part):
                    filename = part.get("filename")
                    mimeType = part.get("mimeType")
                    body = part.get("body", {})
                    if filename and body.get("attachmentId"):
                        # Only handle PDF and DOCX for now
                        if mimeType in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                            att_id = body.get("attachmentId")
                            att = service.users().messages().attachments().get(userId="me", messageId=msg["id"], id=att_id).execute()
                            att_data = att.get("data")
                            if att_data:
                                file_data = base64.urlsafe_b64decode(att_data.encode("UTF-8"))
                                safe_name = re.sub(r'[^A-Za-z0-9._-]+', '_', filename)
                                file_path = os.path.join(download_dir, f"{msg['id']}_{safe_name}")
                                with open(file_path, "wb") as f:
                                    f.write(file_data)
                                attachments.append(file_path)
                    
                    for subpart in part.get("parts", []):
                        extract_attachments(subpart)
                
                extract_attachments(payload)

                emails.append({
                    "id": full.get("id"),
                    "subject": headers.get("subject", ""),
                    "sender": headers.get("from", ""),
                    "body": plain_txt or html_txt or "",
                    "timestamp": headers.get("date", ""),
                    "attachments": attachments
                })
            return emails
        except Exception as exc:
            print(f"Error watching inbox via Gmail API: {exc}")
            pass

    # Fallback sample inbox containing meeting invitation, survey, scholarship with Q&A call, and hackathon emails
    return [
        {
            "id": "mock-email-1",
            "subject": "Sprint Kickoff Meeting Invitation",
            "sender": "manager@example.com",
            "body": "Hi team, please join the Sprint Kickoff video call at https://meet.google.com/abc-defg-hij on 2026-08-01 at 09:00 UTC.",
            "timestamp": "2026-07-29T09:00:00",
        },
        {
            "id": "mock-email-2",
            "subject": "Developer Feedback Survey",
            "sender": "surveys@example.com",
            "body": "Hi everyone, we value your feedback. Please fill out our developer experience survey at https://forms.gle/xyz123 by 2026-08-05.",
            "timestamp": "2026-07-29T10:00:00",
        },
        {
            "id": "mock-email-3",
            "subject": "Undergraduate Scholarship Q&A Info Session",
            "sender": "scholarships@university.edu",
            "body": "Dear Student, applications for the 2026 Undergraduate Merit Scholarship are open. Join our live Q&A meeting on Zoom: https://us02web.zoom.us/j/987654321 on 2026-08-15 at 14:00 UTC.",
            "timestamp": "2026-07-29T11:00:00",
        },
        {
            "id": "mock-email-4",
            "subject": "Innovate for India Challenge - Mentor Sync",
            "sender": "innovations@example.com",
            "body": "This challenge is organized in collaboration with cfi at Sri Eshwar. Join the mentor sync call at https://teams.microsoft.com/l/meetup-join/innovate-2026 by 2026-09-20.",
            "timestamp": "2026-07-29T12:00:00",
        }
    ]
