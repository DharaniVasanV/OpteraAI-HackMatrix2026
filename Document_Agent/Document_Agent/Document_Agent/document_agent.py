import hashlib
import json
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

GROK_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROK_MODEL = "llama-3.3-70b-versatile"


def get_grok_api_key() -> str:
    value = os.getenv("GROK_API_KEY", "").strip()
    if not value:
        raise ValueError(
            "Missing GROK_API_KEY. Create a .env file from .env.example and add your Groq API key."
        )
    return value

DOCUMENT_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".ppt", ".pptx", ".xls", ".xlsx",
    ".csv", ".zip", ".png", ".jpg", ".jpeg"
}

PRIORITY_MAP = {
    "offer letter": ("Emergency", 95),
    "problem statement": ("High", 80),
    "certificate": ("Medium", 60),
    "brochure": ("Low", 30),
    "rulebook": ("High", 75),
    "invoice": ("High", 78),
    "bill": ("High", 77),
    "report": ("Medium", 55),
    "research": ("Medium", 58),
    "assignment": ("High", 72),
    "form": ("Medium", 50),
}

CATEGORY_KEYWORDS = {
    "Certificates": ["certificate", "certification", "credential", "badge", "issued"],
    "Resumes": ["resume", "cv", "curriculum vitae", "portfolio"],
    "Meeting Notes": ["meeting", "transcript", "minutes", "agenda", "zoom", "teams"],
    "Hackathon Rulebooks": ["hackathon", "hack", "problem statement", "rulebook", "prize", "team"],
    "Offer Letters": ["internship", "intern", "stipend", "offer letter", "joining", "placement", "campus", "recruitment", "interview", "offer"],
    "Bills & Invoices": ["bill", "utility", "electricity", "water", "gas", "invoice", "payment", "receipt", "tax", "gst"],
    "Reports": ["report", "research", "paper", "journal", "study", "abstract", "arxiv", "company", "policy", "nda", "agreement", "contract"]
}

AGENT_MAP = {
    "Meeting Notes": ["Meeting Agent", "Calendar Agent"],
    "Hackathon Rulebooks": ["Application Agent", "Notification Agent", "Calendar Agent"],
    "Offer Letters": ["Priority Agent", "Notification Agent", "Calendar Agent", "Application Agent"],
    "Certificates": ["Certificate Agent"],
    "Reports": ["Research Agent"],
    "Resumes": ["Priority Agent"],
    "Bills & Invoices": ["Priority Agent", "Notification Agent"],
}

DOWNLOAD_DIR = Path("d:/Document Agent/downloads")


def compute_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


def extract_urls(text: str) -> list:
    return re.findall(r'https?://[^\s\'"<>]+', text)


def detect_document_type(name: str, url: str = "") -> str:
    combined = (name + " " + url).lower()
    for keyword in ["certificate", "offer letter", "invoice", "bill", "rulebook",
                    "brochure", "problem statement", "report", "research", "assignment",
                    "form", "transcript", "resume", "white paper"]:
        if keyword in combined:
            return keyword.title()
    ext = Path(name).suffix.lower()
    return {
        ".pdf": "PDF Document", ".docx": "Word Document", ".doc": "Word Document",
        ".ppt": "Presentation", ".pptx": "Presentation",
        ".xls": "Spreadsheet", ".xlsx": "Spreadsheet",
        ".csv": "CSV Data", ".zip": "Archive",
        ".png": "Image", ".jpg": "Image", ".jpeg": "Image",
    }.get(ext, "Document")


def classify_categories(text: str) -> list:
    text_lower = text.lower()
    return [cat for cat, keywords in CATEGORY_KEYWORDS.items()
            if any(kw in text_lower for kw in keywords)] or ["Personal"]


def get_priority(doc_type: str, categories: list) -> tuple:
    combined = (doc_type + " " + " ".join(categories)).lower()
    for keyword, (priority, score) in PRIORITY_MAP.items():
        if keyword in combined:
            return priority, score
    return "Low", 25


def extract_metadata(text: str) -> dict:
    meta = {
        "organizer": "", "company": "", "author": "", "issue_date": "",
        "expiry_date": "", "registration_link": "", "application_link": "",
        "contact_email": "", "website": ""
    }
    emails = re.findall(r'[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}', text)
    if emails:
        meta["contact_email"] = emails[0]
    dates = re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b', text)
    if dates:
        meta["issue_date"] = dates[0]
        if len(dates) > 1:
            meta["expiry_date"] = dates[-1]
    for url in extract_urls(text):
        if any(kw in url.lower() for kw in ["register", "apply", "signup", "form"]):
            meta["registration_link"] = meta["registration_link"] or url
            meta["application_link"] = meta["application_link"] or url
        elif not meta["website"]:
            meta["website"] = url
    org_match = re.search(r'(?:organized by|by|from|company)[:\s]+([A-Z][A-Za-z\s&.]+)', text)
    if org_match:
        meta["organizer"] = org_match.group(1).strip()
        meta["company"] = meta["organizer"]
    return meta


def extract_deadlines(text: str) -> list:
    deadlines = []
    for pattern in [
        r'(?:deadline|due|submit by|last date|closes?)[:\s]+([^\n.]+)',
        r'(?:register by|apply by)[:\s]+([^\n.]+)',
    ]:
        deadlines.extend(m.strip() for m in re.findall(pattern, text, re.IGNORECASE))
    return deadlines


def extract_tasks(text: str) -> list:
    tasks = []
    for line in text.splitlines():
        line = line.strip()
        if re.match(r'^[-•*]\s+', line) or re.match(r'^\d+\.\s+', line):
            task = re.sub(r'^[-•*\d.]\s+', '', line).strip()
            if task:
                tasks.append(task)
    return tasks[:10]


def grok_summary(text: str, doc_type: str, categories: list) -> str:
    prompt = (
        f"You are a document analysis AI. Analyze this document text and return a concise 2-3 sentence summary.\n"
        f"Document Type: {doc_type}\nCategories: {', '.join(categories)}\n\nText:\n{text[:2000]}\n\n"
        f"Return only the summary, no extra text."
    )
    # Fallback: rule-based summary
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 30]
    base = f"[{doc_type}] " + " ".join(sentences[:3])
    fallback_summary = base[:400] + "..." if len(base) > 400 else base

    try:
        api_key = get_grok_api_key()
    except ValueError:
        return fallback_summary

    try:
        resp = requests.post(
            GROK_API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": GROK_MODEL, "messages": [{"role": "user", "content": prompt}], "max_tokens": 200},
            timeout=15
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        pass
    return fallback_summary


def find_document_links(text: str) -> list:
    docs = []
    for url in extract_urls(text):
        path = urlparse(url).path.lower()
        ext = Path(path).suffix
        name = Path(path).name or "document"
        if ext in DOCUMENT_EXTENSIONS or any(
            kw in url.lower() for kw in ["download", "file", "doc", "pdf", "certificate", "attachment"]
        ):
            docs.append({"url": url, "name": name, "ext": ext})
    return docs


def is_safe_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def process(input_text: str, auto_download: bool = False, local_file_path: str = None) -> dict:
    from db import save_document, get_all_documents
    from file_processor import extract_text, generate_preview

    doc_hash = compute_hash(input_text + (local_file_path or ""))

    # Duplicate check via DB
    all_docs = get_all_documents()
    for doc in all_docs:
        if doc.get("doc_hash") == doc_hash:
            doc["duplicate"] = True
            doc["reference_count"] = doc.get("reference_count", 1) + 1
            save_document(doc_hash, doc, input_text)
            return doc

    if local_file_path:
        document_found = True
        safe = True
        doc_name = Path(local_file_path).name
        download_url = ""
        doc_links = [{"url": "", "name": doc_name, "ext": Path(doc_name).suffix}]
    else:
        doc_links = find_document_links(input_text)
        document_found = bool(doc_links)
        primary = doc_links[0] if doc_links else {"url": "", "name": "Untitled", "ext": ""}
        doc_name = primary["name"]
        download_url = primary["url"]
        suspicious_terms = ["example.com", "test.com", "fake", "password protected", "password-protected"]
        safe = is_safe_url(download_url) if download_url else False
        safe = safe and not any(term in (input_text.lower() + " " + download_url.lower()) for term in suspicious_terms)

    doc_type = detect_document_type(doc_name, input_text)
    categories = classify_categories(input_text)
    priority, priority_score = get_priority(doc_type, categories)

    download_status = "Not Downloaded"
    file_size = ""
    extracted_doc_text = ""
    
    if document_found and not safe and not local_file_path:
        download_status = "Skipped"
    elif local_file_path:
        download_status = "Local File"
        file_size = str(os.path.getsize(local_file_path)) if os.path.exists(local_file_path) else ""
        extracted_doc_text = extract_text(local_file_path)
    elif auto_download and safe and document_found:
        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        if priority in {"Emergency", "High", "Medium"}:
            success, status_message, local_path, fetched_size = download_document(download_url, doc_name)
            if success:
                download_status = "Downloaded"
                file_size = fetched_size
                extracted_doc_text = extract_text(local_path)
            else:
                download_status = status_message
        else:
            download_status = "Queued"
    elif safe and document_found:
        download_status = "Queued"

    analysis_text = extracted_doc_text if extracted_doc_text else input_text
    preview_text = generate_preview(doc_name, extracted_doc_text)
    
    metadata = extract_metadata(analysis_text)
    deadlines = extract_deadlines(analysis_text)
    tasks = extract_tasks(analysis_text)
    summary = grok_summary(analysis_text, doc_type, categories)
    important_links = list({d["url"] for d in doc_links})

    result = {
        "document_found": document_found,
        "document_name": doc_name,
        "document_type": doc_type,
        "category": categories,
        "importance": priority,
        "priority": priority,
        "priority_score": priority_score,
        "source": metadata.get("website") or download_url,
        "download_url": download_url,
        "download_status": download_status,
        "duplicate": False,
        "safe_to_download": safe,
        "pages": 0,
        "file_size": file_size,
        "summary": summary,
        "preview_text": preview_text,
        "extracted_text": extracted_doc_text,
        "highlights": deadlines[:3],
        "deadlines": deadlines,
        "tasks": tasks,
        "important_links": important_links,
        "metadata": metadata,
        "recommended_actions": _get_actions(priority, categories),
        "required_agents": _get_agents(categories),
        "reason": f"Classified as {doc_type} under {', '.join(categories)}.",
        "confidence": min(95, 50 + priority_score // 5),
        "document_id": str(uuid.uuid4()),
        "date_indexed": datetime.utcnow().isoformat() + "Z",
        "reference_count": 1,
    }

    save_document(doc_hash, result, input_text)
    return result


def download_document(url: str, doc_name: str) -> tuple:
    if not is_safe_url(url):
        return False, "Skipped", "", ""

    try:
        response = requests.get(url, stream=True, timeout=20)
        response.raise_for_status()
        safe_name = re.sub(r'[^A-Za-z0-9._-]+', '_', Path(doc_name).name or "document") or "document"
        destination = DOWNLOAD_DIR / safe_name
        with destination.open("wb") as handle:
            for chunk in response.iter_content(8192):
                if chunk:
                    handle.write(chunk)
        size = response.headers.get("Content-Length") or ""
        return True, "Downloaded", str(destination), size
    except Exception as exc:
        return False, f"Download failed: {exc}", "", ""


def _get_agents(categories: list) -> list:
    agents = set()
    for cat in categories:
        agents.update(AGENT_MAP.get(cat, []))
    return list(agents) or ["Notification Agent"]


def _get_actions(priority: str, categories: list) -> list:
    actions = ["Preview", "Save"]
    if priority in ("Emergency", "High"):
        actions = ["Download", "Open", "Notify User"] + actions
    if any(c in categories for c in ["Hackathon Rulebooks", "Offer Letters"]):
        actions += ["Apply", "Register", "Add to Calendar"]
    if "Meeting Notes" in categories:
        actions += ["Add to Calendar", "Summarize"]
    if "Certificates" in categories:
        actions += ["Archive"]
    return list(dict.fromkeys(actions))


def search_index(query: str) -> list:
    from db import search_documents
    return search_documents(query)
