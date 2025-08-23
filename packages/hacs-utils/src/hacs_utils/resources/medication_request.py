from __future__ import annotations

from typing import Optional

from hacs_models.medication_request import MedicationRequest, create_prescription
from hacs_models.types import ResourceReference


def create_simple_prescription(
    medication_text: str,
    subject_ref: ResourceReference,
    *,
    dosage_text: Optional[str] = None,
) -> MedicationRequest:
    return create_prescription(
        medication_text=medication_text,
        patient_ref=subject_ref,
        dosage_text=dosage_text,
    )


def validate_prescription(rx: dict) -> dict:
    issues: list[str] = []
    if not rx.get("status"):
        issues.append("missing status")
    if not rx.get("intent"):
        issues.append("missing intent")
    if not rx.get("subject"):
        issues.append("missing subject")
    med = rx.get("medicationCodeableConcept") or rx.get("medicationReference")
    if not med:
        issues.append("missing medication")
    if not rx.get("dosageInstruction"):
        issues.append("missing dosageInstruction")
    return {"valid": len(issues) == 0, "issues": issues}


def route_prescription(rx: dict) -> dict:
    priority = (rx.get("priority") or "routine").lower()
    dest = "standard_pharmacy"
    if priority in ("stat", "urgent"):
        dest = "expedite_pharmacy"
    return {"destination": dest}


def check_allergy_contraindications(rx: dict, allergies: list[dict]) -> dict:
    med_text = "".join([
        ((rx.get("medicationCodeableConcept") or {}).get("text") or ""),
        ((rx.get("medicationCodeableConcept") or {}).get("coding", [{}])[0].get("display") or ""),
    ]).lower()
    hits: list[str] = []
    for a in allergies or []:
        code = (a.get("code") or {}).get("text") or ""
        if code and code.lower() in med_text:
            hits.append(code)
    return {"contraindicated": len(hits) > 0, "matches": hits}


def check_drug_interactions(meds: list[dict]) -> dict:
    return {"evaluated": False, "interactions": [], "note": "Integration required"}


