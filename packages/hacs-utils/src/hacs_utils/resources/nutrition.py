from __future__ import annotations

from typing import Dict, Any, Optional, List
from datetime import datetime


def create_therapeutic_diet_order_util(patient_ref: str, diet_text: str, restrictions: Optional[List[str]] = None) -> Dict[str, Any]:
    return {
        "resource_type": "NutritionOrder",
        "status": "active",
        "subject": patient_ref,
        "oralDiet": {"type": [{"text": diet_text}]},
        "allergyIntolerance": [(r or "") for r in (restrictions or [])],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


def manage_nutrition_restrictions_util(nutrition_order: Dict[str, Any], allergies: List[Dict[str, Any]]) -> Dict[str, Any]:
    allergy_texts = [((a.get("code") or {}).get("text") or "") for a in (allergies or []) if (a.get("code") or {}).get("text")]
    cur = set(nutrition_order.get("allergyIntolerance") or [])
    cur.update(allergy_texts)
    nutrition_order["allergyIntolerance"] = list(cur)
    nutrition_order["updated_at"] = datetime.now().isoformat()
    return nutrition_order


def calculate_nutritional_requirements_util(weight_kg: float, height_cm: float, age_years: int, sex: str) -> Dict[str, Any]:
    s = 5 if (sex or "").lower().startswith("m") else -161
    bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age_years + s
    kcal = round(bmr * 1.2)
    protein_g = round(weight_kg * 0.8)
    return {"estimated_kcal_per_day": kcal, "estimated_protein_g_per_day": protein_g}


def coordinate_feeding_protocols_util(nutrition_order: Dict[str, Any], route_text: str, schedule: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    nutrition_order["enteralFormula"] = nutrition_order.get("enteralFormula") or {}
    nutrition_order["enteralFormula"]["routeofAdministration"] = {"text": route_text}
    if schedule:
        nutrition_order["enteralFormula"]["administration"] = [schedule]
    nutrition_order["updated_at"] = datetime.now().isoformat()
    return nutrition_order


