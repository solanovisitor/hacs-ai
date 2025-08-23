from __future__ import annotations

from typing import Dict, Any, List, Optional
from datetime import datetime


def create_care_plan_util(
    patient_ref: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    goals: Optional[List[str]] = None,
    activities: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    return {
        "resource_type": "CarePlan",
        "status": "active",
        "intent": "plan",
        "subject": patient_ref,
        "title": title,
        "description": description,
        "goal": goals or [],
        "activity": activities or [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


def update_care_plan_progress_util(care_plan: Dict[str, Any], progress_note: str) -> Dict[str, Any]:
    notes = care_plan.get("note") or []
    notes.append({"text": progress_note, "time": datetime.now().isoformat()})
    care_plan["note"] = notes
    care_plan["updated_at"] = datetime.now().isoformat()
    return care_plan


def coordinate_care_activities_util(care_plan: Dict[str, Any], activities: List[Dict[str, Any]]) -> Dict[str, Any]:
    cur = care_plan.get("activity") or []
    cur.extend(activities or [])
    care_plan["activity"] = cur
    care_plan["updated_at"] = datetime.now().isoformat()
    return care_plan


def track_care_plan_goals_util(care_plan: Dict[str, Any]) -> Dict[str, Any]:
    goals = care_plan.get("goal") or []
    return {"goal_count": len(goals), "goals": goals}


