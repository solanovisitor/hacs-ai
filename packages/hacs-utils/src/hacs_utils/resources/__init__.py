"""
HACS resource utilities for common operations on FHIR resources.

This module provides helper functions for working with HACS resources,
including observation creation, patient management, document handling,
and care coordination utilities.
"""

# Core utilities that are commonly used
from .observation import (
    set_quantity,
    add_category,
    ensure_code_text,
    create_vital_observation,
)
from .condition import add_stage, create_condition
from .service_request import normalize_intent, create_referral
from .medication_request import create_simple_prescription
from .patient import (
    calculate_patient_age,
    add_patient_identifier,
    get_patient_identifier_by_type,
    add_patient_care_provider,
    deactivate_patient,
)
from .document import get_document_full_text
from .document_reference import (
    validate_document_metadata,
    resolve_document_location,
    register_external_document,
    link_document_to_record,
)
from .diagnostic_report import (
    summarize_diagnostic_report,
    link_report_observations,
    attach_report_media,
    validate_report_completeness,
)
from .appointment import (
    schedule_appointment_util,
    reschedule_appointment_util,
    cancel_appointment_util,
    check_appointment_conflicts_util,
    send_appointment_reminders_util,
)
from .event import (
    create_event,
    update_event_status_util,
    add_event_performer_util,
    schedule_event_util,
    summarize_event_util,
)
from .care_plan import (
    create_care_plan_util,
    update_care_plan_progress_util,
    coordinate_care_activities_util,
    track_care_plan_goals_util,
)
from .care_team import (
    assemble_care_team_util,
    assign_team_roles_util,
    coordinate_team_communication_util,
    track_team_responsibilities_util,
    update_team_membership_util,
)
from .goal import (
    track_goal_progress_util,
    update_goal_status_util,
    measure_goal_achievement_util,
    link_goal_to_careplan_util,
)
from .nutrition import (
    create_therapeutic_diet_order_util,
    manage_nutrition_restrictions_util,
    calculate_nutritional_requirements_util,
    coordinate_feeding_protocols_util,
)

__all__ = [
    # Observation utilities
    "set_quantity",
    "add_category",
    "ensure_code_text",
    "create_vital_observation",
    
    # Condition utilities
    "add_stage",
    "create_condition",
    
    # Service request utilities
    "normalize_intent",
    "create_referral",
    
    # Medication utilities
    "create_simple_prescription",
    
    # Patient utilities
    "calculate_patient_age",
    "add_patient_identifier",
    "get_patient_identifier_by_type",
    "add_patient_care_provider",
    "deactivate_patient",
    
    # Document utilities
    "get_document_full_text",
    "validate_document_metadata",
    "resolve_document_location",
    "register_external_document",
    "link_document_to_record",
    
    # Diagnostic report utilities
    "summarize_diagnostic_report",
    "link_report_observations",
    "attach_report_media",
    "validate_report_completeness",
    
    # Appointment utilities
    "schedule_appointment_util",
    "reschedule_appointment_util",
    "cancel_appointment_util",
    "check_appointment_conflicts_util",
    "send_appointment_reminders_util",
    
    # Event utilities
    "create_event",
    "update_event_status_util",
    "add_event_performer_util",
    "schedule_event_util",
    "summarize_event_util",
    
    # Care plan utilities
    "create_care_plan_util",
    "update_care_plan_progress_util",
    "coordinate_care_activities_util",
    "track_care_plan_goals_util",
    
    # Care team utilities
    "assemble_care_team_util",
    "assign_team_roles_util",
    "coordinate_team_communication_util",
    "track_team_responsibilities_util",
    "update_team_membership_util",
    
    # Goal utilities
    "track_goal_progress_util",
    "update_goal_status_util",
    "measure_goal_achievement_util",
    "link_goal_to_careplan_util",
    
    # Nutrition utilities
    "create_therapeutic_diet_order_util",
    "manage_nutrition_restrictions_util",
    "calculate_nutritional_requirements_util",
    "coordinate_feeding_protocols_util",
]