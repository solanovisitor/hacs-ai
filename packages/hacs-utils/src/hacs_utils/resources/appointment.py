from __future__ import annotations

from typing import Dict, Any, Optional, List
from datetime import datetime


def schedule_appointment_util(
    patient_ref: str,
    practitioner_ref: Optional[str],
    start: str,
    end: str,
    kind: Optional[str] = None,
) -> Dict[str, Any]:
    appt = {
        "resource_type": "Appointment",
        "status": "booked",
        "start": start,
        "end": end,
        "participant": [{"actor": patient_ref, "required": "required", "status": "accepted"}],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    if practitioner_ref:
        appt["participant"].append({"actor": practitioner_ref, "required": "required", "status": "accepted"})
    if kind:
        appt["appointmentType"] = {"text": kind}
    return appt


def reschedule_appointment_util(appt: Dict[str, Any], new_start: str, new_end: str) -> Dict[str, Any]:
    appt["start"] = new_start
    appt["end"] = new_end
    appt["status"] = "booked"
    appt["updated_at"] = datetime.now().isoformat()
    return appt


def cancel_appointment_util(appt: Dict[str, Any], reason: Optional[str] = None) -> Dict[str, Any]:
    appt["status"] = "cancelled"
    if reason:
        appt["cancelationReason"] = {"text": reason}
    appt["updated_at"] = datetime.now().isoformat()
    return appt


def check_appointment_conflicts_util(appt: Dict[str, Any], existing: List[Dict[str, Any]]) -> Dict[str, Any]:
    s = appt.get("start")
    e = appt.get("end")
    conflicts = []
    for other in existing or []:
        os = other.get("start")
        oe = other.get("end")
        if not s or not e or not os or not oe:
            continue
        if not (e <= os or s >= oe):
            conflicts.append({"start": os, "end": oe})
    return {"has_conflicts": len(conflicts) > 0, "conflicts": conflicts}


def send_appointment_reminders_util(appt: Dict[str, Any], channels: Optional[List[str]] = None) -> Dict[str, Any]:
    plan = [{"channel": ch, "scheduled_at": appt.get("start")} for ch in (channels or ["email"])]
    return {"reminders": plan}


