from __future__ import annotations

from typing import Dict, Any, Optional
from datetime import datetime


def create_event(subject: str, code_text: Optional[str] = None, when: Optional[str] = None) -> Dict[str, Any]:
    payload = {
        "resource_type": "Event",
        "subject": subject,
        "status": "in-progress",
        "code": {"text": code_text} if code_text else None,
        "occurrenceDateTime": when,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    return payload


def update_event_status_util(event_obj: Dict[str, Any], status: str, reason: Optional[str] = None) -> Dict[str, Any]:
    event_obj["status"] = status
    if reason:
        event_obj["statusReason"] = {"text": reason}
    event_obj["updated_at"] = datetime.now().isoformat()
    return event_obj


def add_event_performer_util(event_obj: Dict[str, Any], actor_ref: str, role_text: Optional[str] = None) -> Dict[str, Any]:
    performers = event_obj.get("performer") or []
    entry = {"actor": actor_ref}
    if role_text:
        entry["role"] = {"text": role_text}
    performers.append(entry)
    event_obj["performer"] = performers
    event_obj["updated_at"] = datetime.now().isoformat()
    return event_obj


def schedule_event_util(
    event_obj: Dict[str, Any],
    when: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> Dict[str, Any]:
    if when:
        event_obj["occurrenceDateTime"] = when
        event_obj.pop("occurrenceStart", None)
        event_obj.pop("occurrenceEnd", None)
    else:
        if start:
            event_obj["occurrenceStart"] = start
        if end:
            event_obj["occurrenceEnd"] = end
        event_obj.pop("occurrenceDateTime", None)
    event_obj["updated_at"] = datetime.now().isoformat()
    return event_obj


def summarize_event_util(event_obj: Dict[str, Any]) -> str:
    subject = event_obj.get("subject") or "Unknown"
    status = event_obj.get("status") or "unknown"
    code_text = ((event_obj.get("code") or {}).get("text")) or "unspecified"
    when = event_obj.get("occurrenceDateTime") or event_obj.get("occurrenceStart") or "unspecified time"
    return f"Event[{status}] for {subject}: {code_text} at {when}"


