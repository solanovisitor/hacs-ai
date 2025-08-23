from __future__ import annotations

from typing import Dict, Any, List
from datetime import datetime


def validate_document_metadata(document_ref: Dict[str, Any]) -> Dict[str, Any]:
    issues: List[str] = []
    if not document_ref.get("status"):
        issues.append("missing status")
    if not document_ref.get("type"):
        issues.append("missing type")
    if not document_ref.get("subject"):
        issues.append("missing subject")
    contents = document_ref.get("content", [])
    if not contents or not any("attachment" in c for c in contents):
        issues.append("missing content.attachment")
    return {"valid": len(issues) == 0, "issues": issues}


def resolve_document_location(document_ref: Dict[str, Any]) -> List[str]:
    urls: List[str] = []
    for c in document_ref.get("content", []) or []:
        att = c.get("attachment") or {}
        url = att.get("url")
        if url:
            urls.append(url)
    return urls


def register_external_document(document_ref: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.now().isoformat()
    return {
        "document_id": document_ref.get("id"),
        "subject": document_ref.get("subject"),
        "registered_at": now,
        "locations": resolve_document_location(document_ref),
        "status": document_ref.get("status"),
    }


def link_document_to_record(document_ref: Dict[str, Any], target_reference: str) -> Dict[str, Any]:
    relates = document_ref.get("relatesTo") or []
    relates.append({"code": "appends", "target": {"reference": target_reference}})
    document_ref["relatesTo"] = relates
    document_ref["updated_at"] = datetime.now().isoformat()
    return document_ref


