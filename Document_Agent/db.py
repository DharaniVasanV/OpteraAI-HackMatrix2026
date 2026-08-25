import json
from pathlib import Path

INDEX_PATH = Path(__file__).with_name("document_index.json")


def init_db():
    if not INDEX_PATH.exists():
        INDEX_PATH.write_text("{}", encoding="utf-8")
    return True


def _load_index() -> dict:
    if not INDEX_PATH.exists():
        return {}
    try:
        return json.loads(INDEX_PATH.read_text(encoding="utf-8")) or {}
    except json.JSONDecodeError:
        return {}


def _save_index(data: dict):
    INDEX_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def save_document(doc_hash: str, result: dict, raw_input: str):
    data = _load_index()
    existing = data.get(doc_hash, {}) if isinstance(data.get(doc_hash), dict) else {}
    
    # Check for versioning if document_name matches but hash differs
    doc_name = result.get("document_name")
    version = 1
    if doc_name:
        same_name_docs = [v for k, v in data.items() if v.get("document_name") == doc_name and k != doc_hash]
        if same_name_docs:
            version = max([int(doc.get("version", 1)) for doc in same_name_docs]) + 1
            
    merged = dict(existing)
    merged.update(result)
    merged["doc_hash"] = doc_hash
    merged["raw_input"] = raw_input
    merged["version"] = merged.get("version", version)
    merged["reference_count"] = int(merged.get("reference_count", 1))
    
    if result.get("duplicate"):
        merged["duplicate"] = True
        merged["reference_count"] += 1
        
    data[doc_hash] = merged
    _save_index(data)


def get_all_documents() -> list:
    rows = list(_load_index().values())
    rows.sort(key=lambda item: item.get("date_indexed", ""), reverse=True)
    return rows


def search_documents(query: str) -> list:
    query_lower = query.lower()
    rows = []
    for item in _load_index().values():
        searchable = " ".join([
            item.get("document_name", ""),
            item.get("summary", ""),
            item.get("preview_text", ""),
            item.get("document_type", ""),
            item.get("reason", ""),
            item.get("raw_input", ""),
            " ".join(item.get("category", [])),
        ]).lower()
        if query_lower in searchable:
            rows.append(item)
    rows.sort(key=lambda item: item.get("date_indexed", ""), reverse=True)
    return rows


def clear_documents():
    _save_index({})


def get_stats() -> dict:
    rows = list(_load_index().values())
    by_priority = {}
    by_category = {}
    for item in rows:
        priority = item.get("priority", "Unknown")
        by_priority[priority] = by_priority.get(priority, 0) + 1
        for cat in item.get("category", []):
            by_category[cat] = by_category.get(cat, 0) + 1
    return {
        "total": len(rows),
        "duplicates": sum(1 for item in rows if item.get("duplicate")),
        "by_priority": by_priority,
        "by_category": by_category,
    }
