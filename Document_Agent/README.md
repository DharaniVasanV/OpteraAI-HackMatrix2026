# Document Agent — AgentOS

Intelligently discovers, validates, organizes, summarizes, and indexes documents from emails, meetings, hackathons, internships, certifications, placements, and more.

---

## Files

| File | Purpose |
|---|---|
| `document_agent.py` | Core agent — all 12 processing steps |
| `main.py` | CLI / AgentOS entry point |
| `document_index.json` | Auto-generated local search index |
| `downloads/` | Auto-created folder for queued downloads |

---

## How It Works (12 Steps)

| Step | Action |
|---|---|
| 1 | Discover all downloadable document URLs in input |
| 2 | Validate safety, type, and source |
| 3 | Download (if auto_download=True and URL is safe) |
| 4 | Classify into categories (Hackathon, Internship, etc.) |
| 5 | Extract metadata (emails, dates, links, organizer) |
| 6 | Generate AI summary |
| 7 | Index with searchable metadata |
| 8 | Detect and skip duplicates |
| 9 | Assign priority (Emergency / High / Medium / Low) |
| 10 | Recommend downstream agents |
| 11 | Recommend user actions |
| 12 | Return structured JSON output |

---

## Usage

```bash
# Demo (Internship offer letter sample)
python main.py

# Process any text
python main.py process "Download rulebook: https://example.com/rulebook.pdf Deadline: 30/07/2025"

# Process with auto-download enabled
python main.py process "https://example.com/offer_letter.pdf" --auto

# Search the local index
python main.py search "hackathon"
```

---

## Output Schema

```json
{
  "document_found": true,
  "document_name": "",
  "document_type": "",
  "category": [],
  "importance": "",
  "priority": "",
  "priority_score": 0,
  "source": "",
  "download_url": "",
  "download_status": "",
  "duplicate": false,
  "safe_to_download": true,
  "pages": 0,
  "file_size": "",
  "summary": "",
  "highlights": [],
  "deadlines": [],
  "tasks": [],
  "important_links": [],
  "metadata": {
    "organizer": "",
    "company": "",
    "author": "",
    "issue_date": "",
    "expiry_date": "",
    "registration_link": "",
    "application_link": "",
    "contact_email": "",
    "website": ""
  },
  "recommended_actions": [],
  "required_agents": [],
  "reason": "",
  "confidence": 0
}
```

---

## Priority Levels

| Priority | Example Documents |
|---|---|
| Emergency | Offer Letters, Acceptance Deadlines |
| High | Problem Statements, Invoices, Assignments |
| Medium | Certificates, Reports, Research Papers |
| Low | Brochures, General Info |

---

## Supported Document Types

PDF, DOCX, DOC, PPT, PPTX, XLS, XLSX, CSV, ZIP, PNG, JPG, JPEG

---

## Integration with AgentOS

Call `process(text, auto_download)` from any AgentOS agent and pass the returned JSON to downstream agents listed in `required_agents`.
