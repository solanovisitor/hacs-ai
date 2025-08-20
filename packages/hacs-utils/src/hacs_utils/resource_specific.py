"""
Resource-specific utilities for HACS models.

This module provides specialized utility functions for working with specific HACS resources.
These utilities are wrapped as tools in hacs-tools for LLM usage.
"""

from typing import Dict, Any, Optional, List, Union
from datetime import date, datetime
import logging

logger = logging.getLogger(__name__)


# Patient-specific utilities
def calculate_patient_age(
    birth_date: Union[str, date], reference_date: Optional[Union[str, date]] = None
) -> Optional[int]:
    """
    Calculate patient age in years from birth date.

    Args:
        birth_date: Patient's birth date (string or date object)
        reference_date: Reference date for calculation (defaults to today)

    Returns:
        Age in years, or None if birth_date is invalid
    """
    try:
        if isinstance(birth_date, str):
            # Handle templated strings
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
    """
    Add an identifier to patient data.

    Args:
        patient_data: Patient resource data dictionary
        value: Identifier value
        type_code: Type code (MR, SSN, etc.)
        use: Identifier use (usual, official, etc.)
        system: System that assigned the identifier

    Returns:
        Updated patient data
    """
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


def get_patient_identifier_by_type(
    patient_data: Dict[str, Any], type_code: str
) -> Optional[Dict[str, Any]]:
    """
    Get patient identifier by type code.

    Args:
        patient_data: Patient resource data dictionary
        type_code: Type code to search for

    Returns:
        Identifier dictionary or None if not found
    """
    identifiers = patient_data.get("identifier", [])
    for identifier in identifiers:
        if identifier.get("type_code") == type_code:
            return identifier
    return None


def add_patient_care_provider(
    patient_data: Dict[str, Any], provider_reference: str
) -> Dict[str, Any]:
    """
    Add a care provider reference to patient data.

    Args:
        patient_data: Patient resource data dictionary
        provider_reference: Reference to care provider

    Returns:
        Updated patient data
    """
    if "care_provider" not in patient_data:
        patient_data["care_provider"] = []

    if provider_reference not in patient_data["care_provider"]:
        patient_data["care_provider"].append(provider_reference)
        patient_data["updated_at"] = datetime.now().isoformat()

    return patient_data


def deactivate_patient(
    patient_data: Dict[str, Any], reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Deactivate a patient record.

    Args:
        patient_data: Patient resource data dictionary
        reason: Optional reason for deactivation

    Returns:
        Updated patient data
    """
    patient_data["active"] = False

    if reason:
        if "agent_context" not in patient_data:
            patient_data["agent_context"] = {}
        patient_data["agent_context"]["deactivation_reason"] = reason

    patient_data["updated_at"] = datetime.now().isoformat()

    return patient_data


# Observation-specific utilities


def get_observation_value_summary(observation_data: Dict[str, Any]) -> str:
    """
    Get a summary of the observation value.

    Args:
        observation_data: Observation resource data dictionary

    Returns:
        Human-readable value summary
    """
    if "value_quantity" in observation_data:
        qty = observation_data["value_quantity"]
        value = qty.get("value")
        unit = qty.get("unit", "")
        if value is not None:
            return f"{value} {unit}".strip()

    if "value_string" in observation_data:
        return str(observation_data["value_string"])

    if "value_boolean" in observation_data:
        return "Yes" if observation_data["value_boolean"] else "No"

    if "value_codeable_concept" in observation_data:
        concept = observation_data["value_codeable_concept"]
        if isinstance(concept, dict) and "text" in concept:
            return concept["text"]

    return "No value recorded"


# Document-specific utilities


def get_document_full_text(document_data: Dict[str, Any]) -> str:
    """
    Get the full text content of a document.

    Args:
        document_data: Document resource data dictionary

    Returns:
        Full text content
    """
    text_parts = []

    # Add title
    title = document_data.get("title", "")
    if title:
        text_parts.append(title)

    # Add section text
    sections = document_data.get("section", [])
    for section in sections:
        section_title = section.get("title", "")
        if section_title:
            text_parts.append(section_title)

        section_text = section.get("text", "")
        if section_text:
            text_parts.append(section_text)

    return "\n\n".join(text_parts)


# Condition-specific utilities
def add_condition_stage(
    condition_data: Dict[str, Any], stage_summary: str, assessment: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Add a stage to condition data.

    Args:
        condition_data: Condition resource data dictionary
        stage_summary: Summary of the condition stage
        assessment: List of assessment references

    Returns:
        Updated condition data
    """
    if "stage" not in condition_data:
        condition_data["stage"] = []

    stage = {"stage_summary": stage_summary}

    if assessment:
        stage["assessment"] = [{"reference": ref} for ref in assessment]

    condition_data["stage"].append(stage)
    condition_data["updated_at"] = datetime.now().isoformat()

    return condition_data


# DocumentReference utilities
def validate_document_metadata(document_ref: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate required metadata fields for a DocumentReference.
    Checks status, type, subject, and at least one content attachment.
    """
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
    return {
        "valid": len(issues) == 0,
        "issues": issues,
    }


def resolve_document_location(document_ref: Dict[str, Any]) -> List[str]:
    """
    Extract available locations/URLs from DocumentReference.content.attachments.
    """
    urls: List[str] = []
    for c in document_ref.get("content", []) or []:
        att = c.get("attachment") or {}
        url = att.get("url")
        if url:
            urls.append(url)
    return urls


def register_external_document(document_ref: Dict[str, Any]) -> Dict[str, Any]:
    """
    Register an external document for later retrieval/indexing.
    Adds a timestamp marker and returns a registration payload.
    # TODO: integrate with persistence/indexing layer to store metadata and content pointer.
    """
    now = datetime.now().isoformat()
    payload = {
        "document_id": document_ref.get("id"),
        "subject": document_ref.get("subject"),
        "registered_at": now,
        "locations": resolve_document_location(document_ref),
        "status": document_ref.get("status"),
    }
    return payload


def link_document_to_record(document_ref: Dict[str, Any], target_reference: str) -> Dict[str, Any]:
    """
    Link a DocumentReference to another record using relatesTo.
    """
    relates = document_ref.get("relatesTo") or []
    relates.append({"code": "appends", "target": {"reference": target_reference}})
    document_ref["relatesTo"] = relates
    document_ref["updated_at"] = datetime.now().isoformat()
    return document_ref


# Practitioner utilities
def verify_practitioner_credential(practitioner: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify practitioner has at least one qualification entry.
    # TODO: integrate with credential verification services / registries.
    """
    quals = practitioner.get("qualification", [])
    valid = bool(quals)
    return {"valid": valid, "qualification_count": len(quals)}


def link_practitioner_to_organization(
    practitioner: Dict[str, Any], organization_ref: str
) -> Dict[str, Any]:
    orgs = practitioner.get("organization") or []
    if organization_ref not in orgs:
        orgs.append(organization_ref)
    practitioner["organization"] = orgs
    practitioner["updated_at"] = datetime.now().isoformat()
    return practitioner


def update_practitioner_affiliation(
    practitioner: Dict[str, Any], organization_ref: str, active: bool = True
) -> Dict[str, Any]:
    affiliations = practitioner.get("affiliations") or []
    affiliations = [a for a in affiliations if a.get("organization") != organization_ref]
    affiliations.append(
        {
            "organization": organization_ref,
            "active": active,
            "updated_at": datetime.now().isoformat(),
        }
    )
    practitioner["affiliations"] = affiliations
    practitioner["updated_at"] = datetime.now().isoformat()
    return practitioner


# Organization utilities
def register_organization(organization: Dict[str, Any]) -> Dict[str, Any]:
    organization["registered_at"] = datetime.now().isoformat()
    return organization


def link_organization_affiliation(
    organization: Dict[str, Any], parent_org_ref: str
) -> Dict[str, Any]:
    organization["partOf"] = parent_org_ref
    organization["updated_at"] = datetime.now().isoformat()
    return organization


def manage_service_locations(organization: Dict[str, Any], locations: List[str]) -> Dict[str, Any]:
    organization["locations"] = list(locations)
    organization["updated_at"] = datetime.now().isoformat()
    return organization


# ServiceRequest utilities
def validate_service_request(sr: Dict[str, Any]) -> Dict[str, Any]:
    """
    Minimal validation for ServiceRequest: checks status, intent, subject, and code.
    """
    issues: List[str] = []
    if not sr.get("status"):
        issues.append("missing status")
    if not sr.get("intent"):
        issues.append("missing intent")
    if not sr.get("subject"):
        issues.append("missing subject")
    if not sr.get("code"):
        issues.append("missing code")
    return {"valid": len(issues) == 0, "issues": issues}


def route_service_request(sr: Dict[str, Any]) -> Dict[str, Any]:
    """
    Suggest a routing destination based on the request code/category.
    """
    code_text = ((sr.get("code") or {}).get("text") or "").lower()
    destination = "general"
    if any(k in code_text for k in ["x-ray", "ct", "mri", "radiograph", "imaging"]):
        destination = "radiology"
    elif any(k in code_text for k in ["cbc", "lab", "blood", "urinalysis", "panel"]):
        destination = "laboratory"
    elif any(k in code_text for k in ["consult", "consultation", "referral"]):
        destination = "referrals"
    return {"destination": destination}


# DiagnosticReport utilities
def summarize_diagnostic_report(report: Dict[str, Any]) -> str:
    if report.get("conclusion"):
        return str(report["conclusion"]).strip()
    results = report.get("result", [])
    if results:
        return f"Report contains {len(results)} observation results"
    presented = report.get("presentedForm", [])
    if presented:
        return f"Report contains {len(presented)} attached documents"
    return "No summary available"


def link_report_observations(report: Dict[str, Any]) -> List[str]:
    return [str(r) for r in report.get("result", [])]


def attach_report_media(
    report: Dict[str, Any], media_entries: List[Dict[str, Any]]
) -> Dict[str, Any]:
    media = report.get("media") or []
    media.extend(media_entries or [])
    report["media"] = media
    report["updated_at"] = datetime.now().isoformat()
    return report


def validate_report_completeness(report: Dict[str, Any]) -> Dict[str, Any]:
    issues: List[str] = []
    for req in ("status", "code", "subject"):
        if not report.get(req):
            issues.append(f"missing {req}")
    if not report.get("result") and not report.get("presentedForm"):
        issues.append("missing results or presentedForm")
    return {"complete": len(issues) == 0, "issues": issues}


# Medication/Prescription utilities
def validate_prescription(rx: Dict[str, Any]) -> Dict[str, Any]:
    issues: List[str] = []
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


def route_prescription(rx: Dict[str, Any]) -> Dict[str, Any]:
    priority = (rx.get("priority") or "routine").lower()
    dest = "standard_pharmacy"
    if priority in ("stat", "urgent"):
        dest = "expedite_pharmacy"
    return {"destination": dest}


def check_allergy_contraindications(
    rx: Dict[str, Any], allergies: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Simple text-based contraindication checker comparing medication text to allergy codes.
    # TODO: replace with terminology-backed checks (e.g., RxNorm ↔ Allergy code mapping).
    """
    med_text = "".join(
        [
            ((rx.get("medicationCodeableConcept") or {}).get("text") or ""),
            (
                (rx.get("medicationCodeableConcept") or {}).get("coding", [{}])[0].get("display")
                or ""
            ),
        ]
    ).lower()
    hits: List[str] = []
    for a in allergies or []:
        code = (a.get("code") or {}).get("text") or ""
        if code and code.lower() in med_text:
            hits.append(code)
    return {"contraindicated": len(hits) > 0, "matches": hits}


def check_drug_interactions(meds: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Check for potential interactions among a list of medications.
    # TODO: integrate with a real interaction knowledge base. Currently returns unknown.
    """
    return {"evaluated": False, "interactions": [], "note": "Integration required"}


# Event utilities
def create_event(
    subject: str, code_text: Optional[str] = None, when: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a minimal Event-like dict for quick agent usage.
    """
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


def update_event_status_util(
    event_obj: Dict[str, Any], status: str, reason: Optional[str] = None
) -> Dict[str, Any]:
    event_obj["status"] = status
    if reason:
        event_obj["statusReason"] = {"text": reason}
    event_obj["updated_at"] = datetime.now().isoformat()
    return event_obj


def add_event_performer_util(
    event_obj: Dict[str, Any], actor_ref: str, role_text: Optional[str] = None
) -> Dict[str, Any]:
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
    when = (
        event_obj.get("occurrenceDateTime")
        or event_obj.get("occurrenceStart")
        or "unspecified time"
    )
    return f"Event[{status}] for {subject}: {code_text} at {when}"


# Appointment utilities
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
        appt["participant"].append(
            {"actor": practitioner_ref, "required": "required", "status": "accepted"}
        )
    if kind:
        appt["appointmentType"] = {"text": kind}
    return appt


def reschedule_appointment_util(
    appt: Dict[str, Any], new_start: str, new_end: str
) -> Dict[str, Any]:
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


def check_appointment_conflicts_util(
    appt: Dict[str, Any], existing: List[Dict[str, Any]]
) -> Dict[str, Any]:
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


def send_appointment_reminders_util(
    appt: Dict[str, Any], channels: Optional[List[str]] = None
) -> Dict[str, Any]:
    # TODO: integrate with messaging service; currently returns a plan
    plan = [{"channel": ch, "scheduled_at": appt.get("start")} for ch in (channels or ["email"])]
    return {"reminders": plan}


# CarePlan utilities
def create_care_plan_util(
    patient_ref: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    goals: Optional[List[str]] = None,
    activities: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    cp = {
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
    return cp


def update_care_plan_progress_util(care_plan: Dict[str, Any], progress_note: str) -> Dict[str, Any]:
    notes = care_plan.get("note") or []
    notes.append({"text": progress_note, "time": datetime.now().isoformat()})
    care_plan["note"] = notes
    care_plan["updated_at"] = datetime.now().isoformat()
    return care_plan


def coordinate_care_activities_util(
    care_plan: Dict[str, Any], activities: List[Dict[str, Any]]
) -> Dict[str, Any]:
    cur = care_plan.get("activity") or []
    cur.extend(activities or [])
    care_plan["activity"] = cur
    care_plan["updated_at"] = datetime.now().isoformat()
    return care_plan


def track_care_plan_goals_util(care_plan: Dict[str, Any]) -> Dict[str, Any]:
    goals = care_plan.get("goal") or []
    return {"goal_count": len(goals), "goals": goals}


# CareTeam utilities
def assemble_care_team_util(
    patient_ref: str, participants: List[Dict[str, Any]], name: Optional[str] = None
) -> Dict[str, Any]:
    ct = {
        "resource_type": "CareTeam",
        "status": "active",
        "subject": patient_ref,
        "name": name,
        "participant": participants or [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    return ct


def assign_team_roles_util(
    care_team: Dict[str, Any], member_ref: str, role_text: str
) -> Dict[str, Any]:
    parts = care_team.get("participant") or []
    parts.append({"member": member_ref, "role": [{"text": role_text}]})
    care_team["participant"] = parts
    care_team["updated_at"] = datetime.now().isoformat()
    return care_team


def coordinate_team_communication_util(care_team: Dict[str, Any], message: str) -> Dict[str, Any]:
    # TODO: integrate with messaging/logging services
    log = care_team.get("communicationLog") or []
    log.append({"message": message, "time": datetime.now().isoformat()})
    care_team["communicationLog"] = log
    care_team["updated_at"] = datetime.now().isoformat()
    return care_team


def track_team_responsibilities_util(care_team: Dict[str, Any]) -> Dict[str, Any]:
    parts = care_team.get("participant") or []
    mapping = []
    for p in parts:
        mapping.append(
            {"member": p.get("member"), "roles": [r.get("text") for r in (p.get("role") or [])]}
        )
    return {"responsibilities": mapping}


def update_team_membership_util(
    care_team: Dict[str, Any],
    add: Optional[List[Dict[str, Any]]] = None,
    remove_members: Optional[List[str]] = None,
) -> Dict[str, Any]:
    parts = care_team.get("participant") or []
    if remove_members:
        parts = [p for p in parts if p.get("member") not in set(remove_members)]
    if add:
        parts.extend(add)
    care_team["participant"] = parts
    care_team["updated_at"] = datetime.now().isoformat()
    return care_team


# Goal utilities
def track_goal_progress_util(
    goal: Dict[str, Any], current_value: Optional[float] = None
) -> Dict[str, Any]:
    targets = goal.get("target") or []
    summary = {"targets": len(targets), "current_value": current_value}
    return summary


def update_goal_status_util(goal: Dict[str, Any], status: str) -> Dict[str, Any]:
    goal["lifecycleStatus"] = status
    goal["updated_at"] = datetime.now().isoformat()
    return goal


def measure_goal_achievement_util(
    goal: Dict[str, Any], observations: List[Dict[str, Any]]
) -> Dict[str, Any]:
    # TODO: implement real target measure mapping; returns count of supporting observations
    return {"supporting_observations": len(observations or [])}


def link_goal_to_careplan_util(goal: Dict[str, Any], care_plan_ref: str) -> Dict[str, Any]:
    refs = goal.get("partOf") or []
    if care_plan_ref not in refs:
        refs.append(care_plan_ref)
    goal["partOf"] = refs
    goal["updated_at"] = datetime.now().isoformat()
    return goal


# NutritionOrder utilities
def create_therapeutic_diet_order_util(
    patient_ref: str, diet_text: str, restrictions: Optional[List[str]] = None
) -> Dict[str, Any]:
    order = {
        "resource_type": "NutritionOrder",
        "status": "active",
        "subject": patient_ref,
        "oralDiet": {"type": [{"text": diet_text}]},
        "allergyIntolerance": [(r or "") for r in (restrictions or [])],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    return order


def manage_nutrition_restrictions_util(
    nutrition_order: Dict[str, Any], allergies: List[Dict[str, Any]]
) -> Dict[str, Any]:
    # Simple merge between order restrictions and allergy text list
    allergy_texts = [
        ((a.get("code") or {}).get("text") or "")
        for a in (allergies or [])
        if (a.get("code") or {}).get("text")
    ]
    cur = set(nutrition_order.get("allergyIntolerance") or [])
    cur.update(allergy_texts)
    nutrition_order["allergyIntolerance"] = list(cur)
    nutrition_order["updated_at"] = datetime.now().isoformat()
    return nutrition_order


def calculate_nutritional_requirements_util(
    weight_kg: float, height_cm: float, age_years: int, sex: str
) -> Dict[str, Any]:
    # Mifflin-St Jeor estimation (rough)
    s = 5 if (sex or "").lower().startswith("m") else -161
    bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age_years + s
    kcal = round(bmr * 1.2)  # sedentary multiplier
    protein_g = round(weight_kg * 0.8)
    return {"estimated_kcal_per_day": kcal, "estimated_protein_g_per_day": protein_g}


def coordinate_feeding_protocols_util(
    nutrition_order: Dict[str, Any], route_text: str, schedule: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    nutrition_order["enteralFormula"] = nutrition_order.get("enteralFormula") or {}
    nutrition_order["enteralFormula"]["routeofAdministration"] = {"text": route_text}
    if schedule:
        nutrition_order["enteralFormula"]["administration"] = [schedule]
    nutrition_order["updated_at"] = datetime.now().isoformat()
    return nutrition_order


# --- Terminology helpers (UMLS-ready stubs) ---
def normalize_system_uri(system: str) -> str:
    mapping = {
        "SNOMED": "http://snomed.info/sct",
        "LOINC": "http://loinc.org",
        "RxNorm": "http://www.nlm.nih.gov/research/umls/rxnorm",
        "UMLS": "http://identifiers.org/umls",
    }
    return mapping.get(system, system)


def make_terminology_concept(
    system: str, code: str, display: Optional[str] = None, **kwargs: Any
) -> Dict[str, Any]:
    return {
        "resource_type": "TerminologyConcept",
        "system_uri": normalize_system_uri(system),
        "code": code,
        "display": display,
        **kwargs,
    }


def make_value_set(
    name: str,
    systems: Optional[List[Dict[str, str]]] = None,
    concepts: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    return {
        "resource_type": "ValueSet",
        "name": name,
        "include_systems": systems or [],
        "include_concepts": concepts or [],
    }


def scan_codable_concepts(
    obj: Any, code_fields: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Recursively scan an object for CodeableConcept-like fields and collect coding entries.

    Returns a list of {field, system, code, display} items.
    """
    targets = set(
        code_fields or ["code", "category", "type", "method", "interpretation"]
    )  # common concept fields
    found: List[Dict[str, Any]] = []

    def _walk(node: Any):
        if isinstance(node, dict):
            for k, v in node.items():
                if k in targets and isinstance(v, dict) and v.get("coding"):
                    for c in v.get("coding", []) or []:
                        found.append(
                            {
                                "field": k,
                                "system": (c or {}).get("system"),
                                "code": (c or {}).get("code"),
                                "display": (c or {}).get("display"),
                            }
                        )
                _walk(v)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(obj)
    return found
