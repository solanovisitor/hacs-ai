"""
HACS Resource-Specific Tools

This domain provides specialized tools for working with specific HACS resources.
These tools focus on broader, meaningful use cases rather than micro-level field updates.
They wrap resource-specific utilities from hacs-utils and are organized by resource type.
"""

import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from hacs_models import HACSResult
from hacs_utils import (
    calculate_patient_age, add_patient_identifier, get_patient_identifier_by_type,
    add_patient_care_provider, deactivate_patient, get_observation_value_summary,
    get_document_full_text, add_condition_stage,
    validate_document_metadata, resolve_document_location, register_external_document, link_document_to_record,
    validate_service_request, route_service_request,
    summarize_diagnostic_report, link_report_observations, attach_report_media, validate_report_completeness,
    validate_prescription, route_prescription, check_allergy_contraindications, check_drug_interactions,
    create_event, update_event_status_util, add_event_performer_util, schedule_event_util, summarize_event_util,
    # Appointment
    schedule_appointment_util, reschedule_appointment_util, cancel_appointment_util,
    check_appointment_conflicts_util, send_appointment_reminders_util,
    # CarePlan
    create_care_plan_util, update_care_plan_progress_util, coordinate_care_activities_util, track_care_plan_goals_util,
    # CareTeam
    assemble_care_team_util, assign_team_roles_util, coordinate_team_communication_util, track_team_responsibilities_util, update_team_membership_util,
    # Goal
    track_goal_progress_util, update_goal_status_util, measure_goal_achievement_util, link_goal_to_careplan_util,
    # NutritionOrder
    create_therapeutic_diet_order_util, manage_nutrition_restrictions_util, calculate_nutritional_requirements_util, coordinate_feeding_protocols_util,
)

logger = logging.getLogger(__name__)


# Patient-specific tools
def calculate_age(patient_data: Dict[str, Any], reference_date: Optional[str] = None) -> HACSResult:
    """
    Calculate patient age in years from birth date.
    
    Args:
        patient_data: Patient resource data dictionary
        reference_date: Reference date for calculation (defaults to today)
        
    Returns:
        HACSResult with calculated age
    """
    try:
        birth_date = patient_data.get("birth_date")
        if not birth_date:
            return HACSResult(
                success=False,
                message="No birth_date found in patient data",
                error="birth_date field is required for age calculation"
            )
        
        age = calculate_patient_age(birth_date, reference_date)
        
        if age is None:
            return HACSResult(
                success=False,
                message="Could not calculate age",
                error="Invalid birth_date format or templated value"
            )
        
        return HACSResult(
            success=True,
            message=f"Successfully calculated patient age: {age} years",
            data={"age_years": age, "birth_date": birth_date}
        )
        
    except Exception as e:
        return HACSResult(
            success=False,
            message="Failed to calculate patient age",
            error=str(e)
        )


def add_identifier(patient_data: Dict[str, Any], value: str, type_code: Optional[str] = None, 
                  use: str = "usual", system: Optional[str] = None) -> HACSResult:
    """
    Add an identifier to patient data.
    
    Args:
        patient_data: Patient resource data dictionary
        value: Identifier value
        type_code: Type code (MR, SSN, etc.)
        use: Identifier use (usual, official, etc.)
        system: System that assigned the identifier
        
    Returns:
        HACSResult with updated patient data
    """
    try:
        updated_data = add_patient_identifier(patient_data, value, type_code, use, system)
        
        return HACSResult(
            success=True,
            message=f"Successfully added identifier {value}",
            data={"patient": updated_data, "identifier_added": {"value": value, "type_code": type_code}}
        )
        
    except Exception as e:
        return HACSResult(
            success=False,
            message="Failed to add patient identifier",
            error=str(e)
        )


def find_identifier_by_type(patient_data: Dict[str, Any], type_code: str) -> HACSResult:
    """
    Find patient identifier by type code.
    
    Args:
        patient_data: Patient resource data dictionary
        type_code: Type code to search for
        
    Returns:
        HACSResult with found identifier or None
    """
    try:
        identifier = get_patient_identifier_by_type(patient_data, type_code)
        
        if identifier:
            return HACSResult(
                success=True,
                message=f"Found identifier of type {type_code}",
                data={"identifier": identifier, "type_code": type_code}
            )
        else:
            return HACSResult(
                success=False,
                message=f"No identifier found with type {type_code}",
                data={"identifier": None, "type_code": type_code}
            )
        
    except Exception as e:
        return HACSResult(
            success=False,
            message="Failed to search for patient identifier",
            error=str(e)
        )


def add_care_provider(patient_data: Dict[str, Any], provider_reference: str) -> HACSResult:
    """
    Add a care provider reference to patient data.
    
    Args:
        patient_data: Patient resource data dictionary
        provider_reference: Reference to care provider
        
    Returns:
        HACSResult with updated patient data
    """
    try:
        updated_data = add_patient_care_provider(patient_data, provider_reference)
        
        return HACSResult(
            success=True,
            message=f"Successfully added care provider {provider_reference}",
            data={"patient": updated_data, "provider_added": provider_reference}
        )
        
    except Exception as e:
        return HACSResult(
            success=False,
            message="Failed to add care provider",
            error=str(e)
        )


def deactivate_record(patient_data: Dict[str, Any], reason: Optional[str] = None) -> HACSResult:
    """
    Deactivate a patient record.
    
    Args:
        patient_data: Patient resource data dictionary
        reason: Optional reason for deactivation
        
    Returns:
        HACSResult with updated patient data
    """
    try:
        updated_data = deactivate_patient(patient_data, reason)
        
        return HACSResult(
            success=True,
            message="Successfully deactivated patient record",
            data={"patient": updated_data, "deactivation_reason": reason}
        )
        
    except Exception as e:
        return HACSResult(
            success=False,
            message="Failed to deactivate patient record",
            error=str(e)
        )


# Observation-specific tools
def summarize_observation_value(observation_data: Dict[str, Any]) -> HACSResult:
    """
    Get a human-readable summary of the observation value for clinical context.
    
    Args:
        observation_data: Observation resource data dictionary
        
    Returns:
        HACSResult with value summary
    """
    try:
        summary = get_observation_value_summary(observation_data)
        
        return HACSResult(
            success=True,
            message="Successfully generated observation value summary",
            data={"summary": summary, "observation_id": observation_data.get("id")}
        )
        
    except Exception as e:
        return HACSResult(
            success=False,
            message="Failed to generate observation value summary",
            error=str(e)
        )


# Document-specific tools  
def extract_document_text(document_data: Dict[str, Any]) -> HACSResult:
    """
    Extract the full text content of a clinical document for analysis or processing.
    
    Args:
        document_data: Document resource data dictionary
        
    Returns:
        HACSResult with full text content
    """
    try:
        full_text = get_document_full_text(document_data)
        
        return HACSResult(
            success=True,
            message="Successfully extracted document text",
            data={"full_text": full_text, "document_id": document_data.get("id"), "text_length": len(full_text)}
        )
        
    except Exception as e:
        return HACSResult(
            success=False,
            message="Failed to extract document text",
            error=str(e)
        )


# Condition-specific tools
def add_condition_stage(condition_data: Dict[str, Any], stage_summary: str, 
                       assessment: Optional[List[str]] = None) -> HACSResult:
    """
    Add a clinical stage to a condition for disease progression tracking.
    
    Args:
        condition_data: Condition resource data dictionary
        stage_summary: Summary of the condition stage
        assessment: List of assessment references supporting the stage
        
    Returns:
        HACSResult with updated condition data
    """
    try:
        updated_data = add_condition_stage(condition_data, stage_summary, assessment)
        
        return HACSResult(
            success=True,
            message=f"Successfully added condition stage: {stage_summary}",
            data={"condition": updated_data, "stage_added": {"summary": stage_summary, "assessment": assessment}}
        )
    except Exception as e:
        return HACSResult(
            success=False,
            message="Failed to add condition stage",
            error=str(e)
        )


# DocumentReference tools
def validate_document_reference(document_ref: Dict[str, Any]) -> HACSResult:
    try:
        res = validate_document_metadata(document_ref)
        return HACSResult(success=res["valid"], message="DocumentReference metadata validated", data=res)
    except Exception as e:
        return HACSResult(success=False, message="Validation failed", error=str(e))


def list_document_locations(document_ref: Dict[str, Any]) -> HACSResult:
    try:
        urls = resolve_document_location(document_ref)
        return HACSResult(success=True, message=f"Found {len(urls)} locations", data={"locations": urls})
    except Exception as e:
        return HACSResult(success=False, message="Failed to resolve locations", error=str(e))


def register_document(document_ref: Dict[str, Any]) -> HACSResult:
    try:
        payload = register_external_document(document_ref)
        return HACSResult(success=True, message="Document registered", data=payload)
    except Exception as e:
        return HACSResult(success=False, message="Document registration failed", error=str(e))


def link_document(document_ref: Dict[str, Any], target_reference: str) -> HACSResult:
    try:
        updated = link_document_to_record(document_ref, target_reference)
        return HACSResult(success=True, message="Document linked to record", data={"document": updated})
    except Exception as e:
        return HACSResult(success=False, message="Failed to link document", error=str(e))


# ServiceRequest tools
def validate_service_request_tool(sr: Dict[str, Any]) -> HACSResult:
    try:
        res = validate_service_request(sr)
        return HACSResult(success=res["valid"], message="ServiceRequest validated", data=res)
    except Exception as e:
        return HACSResult(success=False, message="Validation failed", error=str(e))


def route_service_request_tool(sr: Dict[str, Any]) -> HACSResult:
    try:
        dest = route_service_request(sr)
        return HACSResult(success=True, message="ServiceRequest routed", data=dest)
    except Exception as e:
        return HACSResult(success=False, message="Routing failed", error=str(e))


# DiagnosticReport tools
def summarize_report_tool(report: Dict[str, Any]) -> HACSResult:
    try:
        summary = summarize_diagnostic_report(report)
        return HACSResult(success=True, message="Report summarized", data={"summary": summary})
    except Exception as e:
        return HACSResult(success=False, message="Summary failed", error=str(e))


def link_report_results_tool(report: Dict[str, Any]) -> HACSResult:
    try:
        links = link_report_observations(report)
        return HACSResult(success=True, message="Report results linked", data={"results": links})
    except Exception as e:
        return HACSResult(success=False, message="Linking failed", error=str(e))


def attach_report_media_tool(report: Dict[str, Any], media_entries: List[Dict[str, Any]]) -> HACSResult:
    try:
        updated = attach_report_media(report, media_entries)
        return HACSResult(success=True, message="Media attached to report", data={"report": updated})
    except Exception as e:
        return HACSResult(success=False, message="Attach media failed", error=str(e))


def validate_report_completeness_tool(report: Dict[str, Any]) -> HACSResult:
    try:
        res = validate_report_completeness(report)
        return HACSResult(success=res["complete"], message="Report completeness validated", data=res)
    except Exception as e:
        return HACSResult(success=False, message="Validation failed", error=str(e))


# MedicationRequest tools
def validate_prescription_tool(rx: Dict[str, Any]) -> HACSResult:
    try:
        res = validate_prescription(rx)
        return HACSResult(success=res["valid"], message="Prescription validated", data=res)
    except Exception as e:
        return HACSResult(success=False, message="Validation failed", error=str(e))


def route_prescription_tool(rx: Dict[str, Any]) -> HACSResult:
    try:
        res = route_prescription(rx)
        return HACSResult(success=True, message="Prescription routed", data=res)
    except Exception as e:
        return HACSResult(success=False, message="Routing failed", error=str(e))


def check_contraindications_tool(rx: Dict[str, Any], allergies: List[Dict[str, Any]]) -> HACSResult:
    try:
        res = check_allergy_contraindications(rx, allergies)
        return HACSResult(success=True, message="Contraindications evaluated", data=res)
    except Exception as e:
        return HACSResult(success=False, message="Contraindication check failed", error=str(e))


def check_drug_interactions_tool(medications: List[Dict[str, Any]]) -> HACSResult:
    try:
        res = check_drug_interactions(medications)
        return HACSResult(success=True, message="Drug interactions evaluated", data=res)
    except Exception as e:
        return HACSResult(success=False, message="Interaction check failed", error=str(e))


# Event tools
def create_event_tool(subject: str, code_text: Optional[str] = None, when: Optional[str] = None) -> HACSResult:
    try:
        payload = create_event(subject, code_text, when)
        return HACSResult(success=True, message="Event created", data={"event": payload})
    except Exception as e:
        return HACSResult(success=False, message="Create event failed", error=str(e))


def update_event_status_tool(event_obj: Dict[str, Any], status: str, reason: Optional[str] = None) -> HACSResult:
    try:
        updated = update_event_status_util(event_obj, status, reason)
        return HACSResult(success=True, message="Event status updated", data={"event": updated})
    except Exception as e:
        return HACSResult(success=False, message="Update status failed", error=str(e))


def add_event_performer_tool(event_obj: Dict[str, Any], actor_ref: str, role_text: Optional[str] = None) -> HACSResult:
    try:
        updated = add_event_performer_util(event_obj, actor_ref, role_text)
        return HACSResult(success=True, message="Event performer added", data={"event": updated})
    except Exception as e:
        return HACSResult(success=False, message="Add performer failed", error=str(e))


def schedule_event_tool(event_obj: Dict[str, Any], when: Optional[str] = None, start: Optional[str] = None, end: Optional[str] = None) -> HACSResult:
    try:
        updated = schedule_event_util(event_obj, when, start, end)
        return HACSResult(success=True, message="Event scheduled", data={"event": updated})
    except Exception as e:
        return HACSResult(success=False, message="Schedule event failed", error=str(e))


def summarize_event_tool(event_obj: Dict[str, Any]) -> HACSResult:
    try:
        summary = summarize_event_util(event_obj)
        return HACSResult(success=True, message="Event summarized", data={"summary": summary})
    except Exception as e:
        return HACSResult(success=False, message="Summarize event failed", error=str(e))


# Appointment tools
def schedule_appointment(patient_ref: str, practitioner_ref: Optional[str], start: str, end: str, kind: Optional[str] = None) -> HACSResult:
    try:
        appt = schedule_appointment_util(patient_ref, practitioner_ref, start, end, kind)
        return HACSResult(success=True, message="Appointment scheduled", data={"appointment": appt})
    except Exception as e:
        return HACSResult(success=False, message="Schedule appointment failed", error=str(e))


def reschedule_appointment(appointment: Dict[str, Any], new_start: str, new_end: str) -> HACSResult:
    try:
        appt = reschedule_appointment_util(appointment, new_start, new_end)
        return HACSResult(success=True, message="Appointment rescheduled", data={"appointment": appt})
    except Exception as e:
        return HACSResult(success=False, message="Reschedule appointment failed", error=str(e))


def cancel_appointment(appointment: Dict[str, Any], reason: Optional[str] = None) -> HACSResult:
    try:
        appt = cancel_appointment_util(appointment, reason)
        return HACSResult(success=True, message="Appointment cancelled", data={"appointment": appt})
    except Exception as e:
        return HACSResult(success=False, message="Cancel appointment failed", error=str(e))


def check_appointment_conflicts(appointment: Dict[str, Any], existing: List[Dict[str, Any]]) -> HACSResult:
    try:
        res = check_appointment_conflicts_util(appointment, existing)
        return HACSResult(success=True, message="Appointment conflicts checked", data=res)
    except Exception as e:
        return HACSResult(success=False, message="Check appointment conflicts failed", error=str(e))


def send_appointment_reminders(appointment: Dict[str, Any], channels: Optional[List[str]] = None) -> HACSResult:
    try:
        plan = send_appointment_reminders_util(appointment, channels)
        return HACSResult(success=True, message="Appointment reminders planned", data=plan)
    except Exception as e:
        return HACSResult(success=False, message="Send reminders failed", error=str(e))


# CarePlan tools
def create_care_plan(patient_ref: str, title: Optional[str] = None, description: Optional[str] = None,
                     goals: Optional[List[str]] = None, activities: Optional[List[Dict[str, Any]]] = None) -> HACSResult:
    try:
        cp = create_care_plan_util(patient_ref, title, description, goals, activities)
        return HACSResult(success=True, message="CarePlan created", data={"care_plan": cp})
    except Exception as e:
        return HACSResult(success=False, message="Create CarePlan failed", error=str(e))


def update_care_plan_progress(care_plan: Dict[str, Any], progress_note: str) -> HACSResult:
    try:
        updated = update_care_plan_progress_util(care_plan, progress_note)
        return HACSResult(success=True, message="CarePlan progress updated", data={"care_plan": updated})
    except Exception as e:
        return HACSResult(success=False, message="Update CarePlan progress failed", error=str(e))


def coordinate_care_activities(care_plan: Dict[str, Any], activities: List[Dict[str, Any]]) -> HACSResult:
    try:
        updated = coordinate_care_activities_util(care_plan, activities)
        return HACSResult(success=True, message="CarePlan activities coordinated", data={"care_plan": updated})
    except Exception as e:
        return HACSResult(success=False, message="Coordinate activities failed", error=str(e))


def track_care_plan_goals(care_plan: Dict[str, Any]) -> HACSResult:
    try:
        res = track_care_plan_goals_util(care_plan)
        return HACSResult(success=True, message="CarePlan goals summarized", data=res)
    except Exception as e:
        return HACSResult(success=False, message="Track goals failed", error=str(e))


# CareTeam tools
def assemble_care_team(patient_ref: str, participants: List[Dict[str, Any]], name: Optional[str] = None) -> HACSResult:
    try:
        ct = assemble_care_team_util(patient_ref, participants, name)
        return HACSResult(success=True, message="CareTeam assembled", data={"care_team": ct})
    except Exception as e:
        return HACSResult(success=False, message="Assemble CareTeam failed", error=str(e))


def assign_team_roles(care_team: Dict[str, Any], member_ref: str, role_text: str) -> HACSResult:
    try:
        updated = assign_team_roles_util(care_team, member_ref, role_text)
        return HACSResult(success=True, message="Team role assigned", data={"care_team": updated})
    except Exception as e:
        return HACSResult(success=False, message="Assign role failed", error=str(e))


def coordinate_team_communication(care_team: Dict[str, Any], message: str) -> HACSResult:
    try:
        updated = coordinate_team_communication_util(care_team, message)
        return HACSResult(success=True, message="Team communication logged", data={"care_team": updated})
    except Exception as e:
        return HACSResult(success=False, message="Coordinate team communication failed", error=str(e))


def track_team_responsibilities(care_team: Dict[str, Any]) -> HACSResult:
    try:
        res = track_team_responsibilities_util(care_team)
        return HACSResult(success=True, message="Team responsibilities summarized", data=res)
    except Exception as e:
        return HACSResult(success=False, message="Track responsibilities failed", error=str(e))


def update_team_membership(care_team: Dict[str, Any], add: Optional[List[Dict[str, Any]]] = None,
                           remove_members: Optional[List[str]] = None) -> HACSResult:
    try:
        updated = update_team_membership_util(care_team, add, remove_members)
        return HACSResult(success=True, message="CareTeam membership updated", data={"care_team": updated})
    except Exception as e:
        return HACSResult(success=False, message="Update membership failed", error=str(e))


# Goal tools
def track_goal_progress(goal: Dict[str, Any], current_value: Optional[float] = None) -> HACSResult:
    try:
        res = track_goal_progress_util(goal, current_value)
        return HACSResult(success=True, message="Goal progress summarized", data=res)
    except Exception as e:
        return HACSResult(success=False, message="Track goal progress failed", error=str(e))


def update_goal_status(goal: Dict[str, Any], status: str) -> HACSResult:
    try:
        updated = update_goal_status_util(goal, status)
        return HACSResult(success=True, message="Goal status updated", data={"goal": updated})
    except Exception as e:
        return HACSResult(success=False, message="Update goal status failed", error=str(e))


def measure_goal_achievement(goal: Dict[str, Any], observations: List[Dict[str, Any]]) -> HACSResult:
    try:
        res = measure_goal_achievement_util(goal, observations)
        return HACSResult(success=True, message="Goal achievement measured", data=res)
    except Exception as e:
        return HACSResult(success=False, message="Measure goal achievement failed", error=str(e))


def link_goal_to_careplan(goal: Dict[str, Any], care_plan_ref: str) -> HACSResult:
    try:
        updated = link_goal_to_careplan_util(goal, care_plan_ref)
        return HACSResult(success=True, message="Goal linked to CarePlan", data={"goal": updated})
    except Exception as e:
        return HACSResult(success=False, message="Link goal failed", error=str(e))


# NutritionOrder tools
def create_therapeutic_diet_order(patient_ref: str, diet_text: str, restrictions: Optional[List[str]] = None) -> HACSResult:
    try:
        order = create_therapeutic_diet_order_util(patient_ref, diet_text, restrictions)
        return HACSResult(success=True, message="Therapeutic diet order created", data={"nutrition_order": order})
    except Exception as e:
        return HACSResult(success=False, message="Create diet order failed", error=str(e))


def manage_nutrition_restrictions(nutrition_order: Dict[str, Any], allergies: List[Dict[str, Any]]) -> HACSResult:
    try:
        updated = manage_nutrition_restrictions_util(nutrition_order, allergies)
        return HACSResult(success=True, message="Nutrition restrictions managed", data={"nutrition_order": updated})
    except Exception as e:
        return HACSResult(success=False, message="Manage restrictions failed", error=str(e))


def calculate_nutritional_requirements(weight_kg: float, height_cm: float, age_years: int, sex: str) -> HACSResult:
    try:
        res = calculate_nutritional_requirements_util(weight_kg, height_cm, age_years, sex)
        return HACSResult(success=True, message="Nutritional requirements estimated", data=res)
    except Exception as e:
        return HACSResult(success=False, message="Calculate requirements failed", error=str(e))


def coordinate_feeding_protocols(nutrition_order: Dict[str, Any], route_text: str, schedule: Optional[Dict[str, Any]] = None) -> HACSResult:
    try:
        updated = coordinate_feeding_protocols_util(nutrition_order, route_text, schedule)
        return HACSResult(success=True, message="Feeding protocols coordinated", data={"nutrition_order": updated})
    except Exception as e:
        return HACSResult(success=False, message="Coordinate feeding protocols failed", error=str(e))


# Tool exports for plugin discovery
__all__ = [
    # Patient tools - focused on meaningful clinical operations
    "calculate_age",
    "add_identifier", 
    "find_identifier_by_type",
    "add_care_provider",
    "deactivate_record",
    # Observation tools - focused on clinical interpretation
    "summarize_observation_value",
    # Document tools - focused on content extraction and analysis
    "extract_document_text",
    # DocumentReference tools
    "validate_document_reference",
    "list_document_locations",
    "register_document",
    "link_document",
    # Condition tools - focused on clinical management
    "add_condition_stage",
    # ServiceRequest tools
    "validate_service_request_tool",
    "route_service_request_tool",
    # DiagnosticReport tools
    "summarize_report_tool",
    "link_report_results_tool",
    "attach_report_media_tool",
    "validate_report_completeness_tool",
    # MedicationRequest tools
    "validate_prescription_tool",
    "route_prescription_tool",
    "check_contraindications_tool",
    "check_drug_interactions_tool",
    # Event tools
    "create_event_tool",
    "update_event_status_tool",
    "add_event_performer_tool",
    "schedule_event_tool",
    "summarize_event_tool",
    # Appointment tools
    "schedule_appointment",
    "reschedule_appointment",
    "cancel_appointment",
    "check_appointment_conflicts",
    "send_appointment_reminders",
    # CarePlan tools
    "create_care_plan",
    "update_care_plan_progress",
    "coordinate_care_activities",
    "track_care_plan_goals",
    # CareTeam tools
    "assemble_care_team",
    "assign_team_roles",
    "coordinate_team_communication",
    "track_team_responsibilities",
    "update_team_membership",
    # Goal tools
    "track_goal_progress",
    "update_goal_status",
    "measure_goal_achievement",
    "link_goal_to_careplan",
    # NutritionOrder tools
    "create_therapeutic_diet_order",
    "manage_nutrition_restrictions",
    "calculate_nutritional_requirements",
    "coordinate_feeding_protocols",
]
