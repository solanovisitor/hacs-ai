"""
Procedure model based on FHIR US Core Procedure Profile.

This model represents medical procedures with comprehensive clinical information,
optimized for structured outputs and LLM interactions.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from ..base_resource import BaseResource
from pydantic import Field


class ProcedureStatus(str, Enum):
    """Status of the procedure."""

    PREPARATION = "preparation"
    IN_PROGRESS = "in-progress"
    NOT_DONE = "not-done"
    ON_HOLD = "on-hold"
    STOPPED = "stopped"
    COMPLETED = "completed"
    ENTERED_IN_ERROR = "entered-in-error"
    UNKNOWN = "unknown"


class ProcedureCategory(str, Enum):
    """Category of the procedure."""

    SURGICAL = "surgical"
    DIAGNOSTIC = "diagnostic"
    THERAPEUTIC = "therapeutic"
    PREVENTIVE = "preventive"
    EMERGENCY = "emergency"
    REHABILITATION = "rehabilitation"
    COSMETIC = "cosmetic"
    PALLIATIVE = "palliative"
    SCREENING = "screening"
    MONITORING = "monitoring"


class ProcedureBodySite(str, Enum):
    """Common body sites for procedures."""

    HEAD = "head"
    NECK = "neck"
    CHEST = "chest"
    ABDOMEN = "abdomen"
    PELVIS = "pelvis"
    BACK = "back"
    UPPER_EXTREMITY = "upper_extremity"
    LOWER_EXTREMITY = "lower_extremity"
    CARDIOVASCULAR = "cardiovascular"
    RESPIRATORY = "respiratory"
    GASTROINTESTINAL = "gastrointestinal"
    GENITOURINARY = "genitourinary"
    NEUROLOGICAL = "neurological"
    MUSCULOSKELETAL = "musculoskeletal"
    SKIN = "skin"
    OTHER = "other"


class ProcedureOutcome(str, Enum):
    """Outcome of the procedure."""

    SUCCESSFUL = "successful"
    PARTIALLY_SUCCESSFUL = "partially_successful"
    UNSUCCESSFUL = "unsuccessful"
    CANCELLED = "cancelled"
    POSTPONED = "postponed"
    COMPLICATED = "complicated"
    UNKNOWN = "unknown"


class ProcedureUrgency(str, Enum):
    """Urgency level of the procedure."""

    ROUTINE = "routine"
    URGENT = "urgent"
    EMERGENCY = "emergency"
    ELECTIVE = "elective"
    STAT = "stat"


class Procedure(BaseResource):
    """
    Represents a medical procedure.

    Based on FHIR R4 Procedure Resource with HACS enhancements.
    Fully compliant with FHIR specification while optimized for LLM interactions.
    """

    resource_type: Literal["Procedure"] = Field(
        default="Procedure", description="Resource type identifier"
    )

    # Identifiers
    identifier: list[dict[str, Any]] = Field(
        default_factory=list, description="External identifiers for this procedure"
    )

    # FHIR: Instantiation information
    instantiates_canonical: list[str] = Field(
        default_factory=list,
        description="Instantiates FHIR protocol or definition (PlanDefinition, ActivityDefinition, etc.)"
    )

    instantiates_uri: list[str] = Field(
        default_factory=list,
        description="Instantiates external protocol or definition"
    )

    # FHIR: Based on and part of relationships
    based_on: list[dict[str, Any]] = Field(
        default_factory=list,
        description="A request for this procedure (CarePlan, ServiceRequest)"
    )

    part_of: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Part of referenced event (Procedure, Observation, MedicationAdministration)"
    )

    # Status - required in FHIR
    status: ProcedureStatus = Field(
        description="preparation | in-progress | not-done | on-hold | stopped | completed | entered-in-error | unknown"
    )

    # FHIR: Status reason
    status_reason: dict[str, Any] | None = Field(
        default=None,
        description="Reason for current status (CodeableConcept)"
    )

    # Category - FHIR allows multiple categories (0..*)
    category: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Classification of the procedure (CodeableConcept)"
    )

    # LLM-FRIENDLY: Simple category
    procedure_category: ProcedureCategory | None = Field(
        default=None,
        description="Simple classification of the procedure type"
    )

    # Code - FHIR (0..1)
    code: dict[str, Any] | None = Field(
        default=None,
        description="Identification of the procedure (CodeableConcept)"
    )

    # Subject - required in FHIR (1..1)
    subject: dict[str, Any] = Field(
        description="Individual or entity the procedure was performed on (Reference)"
    )

    # FHIR: Focus - who is the target when not the subject
    focus: dict[str, Any] | None = Field(
        default=None,
        description="Who is the target of the procedure when it is not the subject of record only"
    )

    # FHIR: Encounter context
    encounter: dict[str, Any] | None = Field(
        default=None,
        description="The Encounter during which this Procedure was created"
    )

    # FHIR: Occurrence (renamed from performed for FHIR compliance)
    occurrence_date_time: datetime | None = Field(
        default=None,
        description="When the procedure occurred (dateTime)"
    )

    occurrence_period: dict[str, Any] | None = Field(
        default=None,
        description="When the procedure occurred (Period)"
    )

    occurrence_string: str | None = Field(
        default=None,
        description="When the procedure occurred (string)"
    )

    occurrence_age: dict[str, Any] | None = Field(
        default=None,
        description="When the procedure occurred (Age)"
    )

    occurrence_range: dict[str, Any] | None = Field(
        default=None,
        description="When the procedure occurred (Range)"
    )

    occurrence_timing: dict[str, Any] | None = Field(
        default=None,
        description="When the procedure occurred (Timing)"
    )

    # FHIR: Recording information
    recorded: datetime | None = Field(
        default=None,
        description="When the procedure was first captured in the subject's record"
    )

    recorder: dict[str, Any] | None = Field(
        default=None,
        description="Who recorded the procedure"
    )

    # FHIR: Reported information
    reported_boolean: bool | None = Field(
        default=None,
        description="Reported rather than primary record (boolean)"
    )

    reported_reference: dict[str, Any] | None = Field(
        default=None,
        description="Reported rather than primary record (Reference)"
    )

    # FHIR: Performer information (full structure)
    performer: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Who performed the procedure and what they did"
    )

    # FHIR: Location reference
    location: dict[str, Any] | None = Field(
        default=None,
        description="Where the procedure happened (Reference to Location)"
    )

    # FHIR: Reason
    reason: list[dict[str, Any]] = Field(
        default_factory=list,
        description="The justification that the procedure was performed (CodeableReference)"
    )

    # Legacy fields for backward compatibility
    reason_code: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Coded reason why this procedure was performed (deprecated, use reason)"
    )

    reason_reference: list[dict[str, Any]] = Field(
        default_factory=list,
        description="The justification that the procedure was performed (deprecated, use reason)"
    )

    # FHIR: Body site
    body_site: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Target body sites (CodeableConcept)"
    )

    # FHIR: Outcome
    outcome: dict[str, Any] | None = Field(
        default=None,
        description="The result of procedure (CodeableConcept)"
    )

    # FHIR: Report
    report: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Any report resulting from the procedure"
    )

    # FHIR: Complication (structured)
    complication: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Complication following the procedure (CodeableReference)"
    )

    # FHIR: Follow up (structured)
    follow_up: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Instructions for follow up (CodeableConcept)"
    )

    # FHIR: Note
    note: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Additional information about the procedure (Annotation)"
    )

    # FHIR: Focal device
    focal_device: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Manipulated, implanted, or removed device"
    )

    # FHIR: Used items
    used: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Items used during procedure (CodeableReference)"
    )

    # Legacy field for backward compatibility
    used_reference: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Device that was used (deprecated, use 'used')"
    )

    # FHIR: Supporting information
    supporting_info: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Extra information relevant to the procedure"
    )

    # ========================================
    # LLM-FRIENDLY FIELDS (HACS Extensions)
    # ========================================

    # Simple procedure identification
    procedure_name: str | None = Field(
        default=None,
        description="Common name of the procedure",
        examples=[
            "Appendectomy",
            "Colonoscopy",
            "Blood pressure measurement",
            "X-ray chest",
            "MRI brain",
            "Cardiac catheterization"
        ],
    )

    procedure_description: str | None = Field(
        default=None,
        description="Detailed description of what was done",
        examples=[
            "Laparoscopic removal of appendix due to acute appendicitis",
            "Diagnostic colonoscopy with biopsy of suspicious polyp",
            "Routine blood pressure check using automated cuff"
        ]
    )

    # Simple clinical context
    indication: str | None = Field(
        default=None,
        description="Why this procedure was needed",
        examples=[
            "Acute appendicitis",
            "Screening for colorectal cancer",
            "Suspected pneumonia",
            "Routine preventive care"
        ]
    )

    clinical_reasoning: str | None = Field(
        default=None,
        description="Clinical justification for performing this procedure"
    )

    # Simple body site
    anatomical_location: ProcedureBodySite | None = Field(
        default=None,
        description="Main body area where procedure was performed"
    )

    # Simple outcome
    procedure_outcome: ProcedureOutcome | None = Field(
        default=None,
        description="How the procedure turned out"
    )

    outcome_description: str | None = Field(
        default=None,
        description="Detailed description of the procedure outcome",
        examples=[
            "Procedure completed successfully without complications",
            "Appendix removed laparoscopically, patient recovering well",
            "Biopsy obtained, results pending pathology review"
        ]
    )

    # Simple performer info
    performing_physician: str | None = Field(
        default=None,
        description="Name of the main physician who performed the procedure",
        examples=["Dr. Smith", "Dr. Johnson, MD", "Surgical Team"]
    )

    # Simple location
    facility: str | None = Field(
        default=None,
        description="Where the procedure was performed",
        examples=[
            "General Hospital Operating Room 3",
            "Outpatient Surgery Center",
            "Emergency Department",
            "Physician Office"
        ]
    )

    # Timing and duration
    duration_minutes: int | None = Field(
        default=None,
        description="How long the procedure took in minutes",
        examples=[45, 90, 120, 15]
    )

    urgency: ProcedureUrgency | None = Field(
        default=None,
        description="How urgent/emergent this procedure was"
    )

    # Simple complications
    complications: list[str] = Field(
        default_factory=list,
        description="Any complications that occurred (simple text)",
        examples=[
            ["Mild bleeding", "Post-operative nausea"],
            ["No complications"],
            ["Infection at incision site"]
        ]
    )

    # Simple follow-up
    follow_up_required: bool | None = Field(
        default=None,
        description="Whether follow-up care is needed"
    )

    follow_up_instructions: list[str] = Field(
        default_factory=list,
        description="Instructions for post-procedure care (simple text)",
        examples=[
            ["Return in 2 weeks for wound check", "Take antibiotics as prescribed"],
            ["No lifting >10 lbs for 6 weeks", "Call if fever >101°F"]
        ]
    )

    # Simple equipment
    equipment_used: list[str] = Field(
        default_factory=list,
        description="Equipment or devices used during the procedure (simple text)",
        examples=[
            ["Laparoscope", "Electrocautery device"],
            ["Ultrasound machine"],
            ["Cardiac catheter", "Contrast dye"]
        ]
    )

    # Anesthesia
    anesthesia_type: str | None = Field(
        default=None,
        description="Type of anesthesia used",
        examples=[
            "General anesthesia",
            "Local anesthesia",
            "Sedation",
            "Regional anesthesia",
            "None"
        ]
    )

    # Simple notes
    procedure_notes: str | None = Field(
        default=None,
        description="Free-text notes about the procedure"
    )

    # Consent and authorization
    consent_obtained: bool | None = Field(
        default=None,
        description="Whether informed consent was obtained"
    )

    # Quality metrics
    patient_satisfaction: int | None = Field(
        default=None,
        description="Patient satisfaction rating (1-10)",
        ge=1,
        le=10
    )

    # Cost information
    estimated_cost: str | None = Field(
        default=None,
        description="Estimated cost of the procedure"
    )

    # ========================================
    # BACKWARD COMPATIBILITY PROPERTIES
    # ========================================

    @property
    def performed_date_time(self) -> datetime | None:
        """Get performed date time for backward compatibility."""
        return self.occurrence_date_time

    @performed_date_time.setter
    def performed_date_time(self, value: datetime | None):
        """Set performed date time for backward compatibility."""
        self.occurrence_date_time = value

    @property
    def performed_period(self) -> dict[str, Any] | None:
        """Get performed period for backward compatibility."""
        return self.occurrence_period

    @performed_period.setter
    def performed_period(self, value: dict[str, Any] | None):
        """Set performed period for backward compatibility."""
        self.occurrence_period = value

    @property
    def category_simple(self) -> ProcedureCategory | None:
        """Get simple category for backward compatibility."""
        return self.procedure_category

    @category_simple.setter
    def category_simple(self, value: ProcedureCategory | None):
        """Set simple category for backward compatibility."""
        self.procedure_category = value

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        name = self.procedure_name or "Unknown procedure"
        status = self.status if isinstance(self.status, str) else (
            self.status.value if self.status else "unknown status"
        )
        return f"{name} ({status})"

    @property
    def display_name(self) -> str:
        """Get a display-friendly name for the procedure."""
        if self.procedure_name:
            return self.procedure_name
        if self.code and "text" in self.code:
            return self.code["text"]
        return f"Procedure {self.id}"

    @property
    def is_completed(self) -> bool:
        """Check if the procedure is completed."""
        return self.status == ProcedureStatus.COMPLETED if self.status else False

    @property
    def is_in_progress(self) -> bool:
        """Check if the procedure is currently in progress."""
        return self.status == ProcedureStatus.IN_PROGRESS if self.status else False

    @property
    def has_complications(self) -> bool:
        """Check if the procedure had complications."""
        return bool(self.complications) or (
            self.procedure_outcome == ProcedureOutcome.COMPLICATED
            if self.procedure_outcome else False
        )

    def get_performer_names(self) -> list[str]:
        """Get list of performer names."""
        names = []
        if self.performing_physician:
            names.append(self.performing_physician)
        for performer in self.performer:
            if "display" in performer:
                names.append(performer["display"])
        return names

    def get_duration_display(self) -> str:
        """Get human-readable duration."""
        if not self.duration_minutes:
            return "Unknown duration"

        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60

        if hours > 0:
            return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
        else:
            return f"{minutes}m"