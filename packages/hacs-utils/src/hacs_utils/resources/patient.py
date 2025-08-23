from __future__ import annotations

from typing import Dict, Any, Optional, Union
from datetime import date, datetime


def calculate_patient_age(
    birth_date: Union[str, date], reference_date: Optional[Union[str, date]] = None
) -> Optional[int]:
    try:
        if isinstance(birth_date, str):
            if "{{" in birth_date and "}}" in birth_date:
                return None
            birth_date = datetime.fromisoformat(birth_date.replace("Z", "+00:00")).date()
        if reference_date is None:
            reference_date = date.today()
        elif isinstance(reference_date, str):
            reference_date = datetime.fromisoformat(reference_date.replace("Z", "+00:00")).date()
        age = reference_date.year - birth_date.year
        if (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day):
            age -= 1
        return max(0, age)
    except (ValueError, TypeError, AttributeError):
        return None


def add_patient_identifier(
    patient_data: Dict[str, Any],
    value: str,
    type_code: Optional[str] = None,
    use: str = "usual",
    system: Optional[str] = None,
) -> Dict[str, Any]:
    if "identifier" not in patient_data:
        patient_data["identifier"] = []
    identifier = {"use": use, "value": value}
    if type_code:
        identifier["type_code"] = type_code
    if system:
        identifier["system"] = system
    patient_data["identifier"].append(identifier)
    patient_data["updated_at"] = datetime.now().isoformat()
    return patient_data


def get_patient_identifier_by_type(patient_data: Dict[str, Any], type_code: str) -> Optional[Dict[str, Any]]:
    for identifier in patient_data.get("identifier", []):
        if identifier.get("type_code") == type_code:
            return identifier
    return None


def add_patient_care_provider(patient_data: Dict[str, Any], provider_reference: str) -> Dict[str, Any]:
    if "care_provider" not in patient_data:
        patient_data["care_provider"] = []
    if provider_reference not in patient_data["care_provider"]:
        patient_data["care_provider"].append(provider_reference)
        patient_data["updated_at"] = datetime.now().isoformat()
    return patient_data


def deactivate_patient(patient_data: Dict[str, Any], reason: Optional[str] = None) -> Dict[str, Any]:
    patient_data["active"] = False
    if reason:
        if "agent_context" not in patient_data:
            patient_data["agent_context"] = {}
        patient_data["agent_context"]["deactivation_reason"] = reason
    patient_data["updated_at"] = datetime.now().isoformat()
    return patient_data


