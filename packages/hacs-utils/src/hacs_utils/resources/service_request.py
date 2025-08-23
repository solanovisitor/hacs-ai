from __future__ import annotations

from typing import Optional

from hacs_models.types import ServiceRequestStatus, ServiceRequestIntent
from hacs_models.observation import CodeableConcept


def normalize_intent(value: str) -> ServiceRequestIntent:
    v = (value or "").lower()
    if v in {"referral", "refer", "encaminhamento"}:
        return ServiceRequestIntent.ORDER
    try:
        return ServiceRequestIntent(v)  # type: ignore[arg-type]
    except Exception:
        return ServiceRequestIntent.ORDER


def create_referral(
    subject_ref: str,
    reason_text: Optional[str] = None,
    *,
    code_text: Optional[str] = None,
) -> dict:
    """Create a minimal ServiceRequest for referral with normalized intent and active status."""
    payload: dict = {
        "resource_type": "ServiceRequest",
        "status": ServiceRequestStatus.ACTIVE.value,
        "intent": ServiceRequestIntent.ORDER.value,
        "subject": subject_ref,
    }
    if code_text:
        payload["code"] = CodeableConcept(text=code_text).model_dump()
    if reason_text:
        payload["reasonCode"] = [CodeableConcept(text=reason_text).model_dump()]
    return payload


def validate_service_request(sr: dict) -> dict:
    """Minimal dict-level validation for ServiceRequest."""
    issues: list[str] = []
    if not sr.get("status"):
        issues.append("missing status")
    if not sr.get("intent"):
        issues.append("missing intent")
    if not sr.get("subject"):
        issues.append("missing subject")
    if not sr.get("code"):
        issues.append("missing code")
    return {"valid": len(issues) == 0, "issues": issues}


def route_service_request(sr: dict) -> dict:
    """Suggest a routing destination based on textual code/category (heuristic)."""
    code_text = ((sr.get("code") or {}).get("text") or "").lower()
    destination = "general"
    if any(k in code_text for k in ["x-ray", "ct", "mri", "radiograph", "imaging"]):
        destination = "radiology"
    elif any(k in code_text for k in ["cbc", "lab", "blood", "urinalysis", "panel"]):
        destination = "laboratory"
    elif any(k in code_text for k in ["consult", "consultation", "referral"]):
        destination = "referrals"
    return {"destination": destination}


