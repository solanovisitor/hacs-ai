from __future__ import annotations

from typing import Dict, Any, Optional, List


def track_goal_progress_util(goal: Dict[str, Any], current_value: Optional[float] = None) -> Dict[str, Any]:
    targets = goal.get("target") or []
    return {"targets": len(targets), "current_value": current_value}


def update_goal_status_util(goal: Dict[str, Any], status: str) -> Dict[str, Any]:
    goal["lifecycleStatus"] = status
    return goal


def measure_goal_achievement_util(goal: Dict[str, Any], observations: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"supporting_observations": len(observations or [])}


def link_goal_to_careplan_util(goal: Dict[str, Any], care_plan_ref: str) -> Dict[str, Any]:
    refs = goal.get("partOf") or []
    if care_plan_ref not in refs:
        refs.append(care_plan_ref)
    goal["partOf"] = refs
    return goal


