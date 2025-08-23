from __future__ import annotations

from typing import Dict, Any, Optional, List
from datetime import datetime


def assemble_care_team_util(patient_ref: str, participants: List[Dict[str, Any]], name: Optional[str] = None) -> Dict[str, Any]:
    return {
        "resource_type": "CareTeam",
        "status": "active",
        "subject": patient_ref,
        "name": name,
        "participant": participants or [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


def assign_team_roles_util(care_team: Dict[str, Any], member_ref: str, role_text: str) -> Dict[str, Any]:
    parts = care_team.get("participant") or []
    parts.append({"member": member_ref, "role": [{"text": role_text}]})
    care_team["participant"] = parts
    care_team["updated_at"] = datetime.now().isoformat()
    return care_team


def coordinate_team_communication_util(care_team: Dict[str, Any], message: str) -> Dict[str, Any]:
    log = care_team.get("communicationLog") or []
    log.append({"message": message, "time": datetime.now().isoformat()})
    care_team["communicationLog"] = log
    care_team["updated_at"] = datetime.now().isoformat()
    return care_team


def track_team_responsibilities_util(care_team: Dict[str, Any]) -> Dict[str, Any]:
    parts = care_team.get("participant") or []
    mapping = []
    for p in parts:
        mapping.append({"member": p.get("member"), "roles": [r.get("text") for r in (p.get("role") or [])]})
    return {"responsibilities": mapping}


def update_team_membership_util(care_team: Dict[str, Any], add: Optional[List[Dict[str, Any]]] = None, remove_members: Optional[List[str]] = None) -> Dict[str, Any]:
    parts = care_team.get("participant") or []
    if remove_members:
        parts = [p for p in parts if p.get("member") not in set(remove_members)]
    if add:
        parts.extend(add)
    care_team["participant"] = parts
    care_team["updated_at"] = datetime.now().isoformat()
    return care_team


