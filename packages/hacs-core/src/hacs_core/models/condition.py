"""
Condition model based on FHIR R5 Condition Resource.

This model represents clinical conditions, problems, diagnoses, or other events, situations,
issues, or clinical concepts that have risen to a level of concern. Fully compliant with
FHIR R5 specification while optimized for LLM interactions.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from ..base_resource import BaseResource
from pydantic import Field


class ConditionClinicalStatus(str, Enum):
    """Clinical status of the condition."""

    ACTIVE = "active"
    RECURRENCE = "recurrence"
    RELAPSE = "relapse"
    INACTIVE = "inactive"
    REMISSION = "remission"
    RESOLVED = "resolved"
    UNKNOWN = "unknown"


class ConditionVerificationStatus(str, Enum):
    """Verification status of the condition."""

    UNCONFIRMED = "unconfirmed"
    PROVISIONAL = "provisional"
    DIFFERENTIAL = "differential"
    CONFIRMED = "confirmed"
    REFUTED = "refuted"
    ENTERED_IN_ERROR = "entered-in-error"


class ConditionCategory(str, Enum):
    """Category of the condition."""

    PROBLEM_LIST_ITEM = "problem-list-item"
    ENCOUNTER_DIAGNOSIS = "encounter-diagnosis"

    # Additional common categories for LLM use
    CHIEF_COMPLAINT = "chief-complaint"
    WORKING_DIAGNOSIS = "working-diagnosis"
    FINAL_DIAGNOSIS = "final-diagnosis"
    DIFFERENTIAL_DIAGNOSIS = "differential-diagnosis"
    CHRONIC_CONDITION = "chronic-condition"
    ACUTE_CONDITION = "acute-condition"


class ConditionSeverity(str, Enum):
    """Severity of the condition."""

    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"
    FATAL = "fatal"

    # Additional severity levels
    MINIMAL = "minimal"
    LIFE_THREATENING = "life-threatening"
    UNKNOWN = "unknown"


class ConditionBodySite(str, Enum):
    """Common body sites for conditions."""

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
    ENDOCRINE = "endocrine"
    HEMATOLOGICAL = "hematological"
    IMMUNOLOGICAL = "immunological"
    PSYCHIATRIC = "psychiatric"
    SYSTEMIC = "systemic"
    OTHER = "other"


class ConditionStageType(str, Enum):
    """Type of condition staging."""

    TNM = "tnm"  # Tumor, Node, Metastasis staging
    CLINICAL = "clinical"
    PATHOLOGICAL = "pathological"
    FUNCTIONAL = "functional"
    SEVERITY = "severity"
    GRADE = "grade"
    STAGE = "stage"
    PHASE = "phase"
    OTHER = "other"


class Condition(BaseResource):
    """
    Represents a clinical condition, problem, diagnosis, or health concern.

    Based on FHIR R5 Condition Resource with HACS enhancements.
    Fully compliant with FHIR specification while optimized for LLM interactions.

    Can represent:
    - Clinical diagnoses (e.g., diabetes, hypertension)
    - Problems (e.g., pain, difficulty sleeping)
    - Health concerns (e.g., risk factors, family history)
    - Symptoms requiring management (e.g., chronic fatigue)
    """

    resource_type: Literal["Condition"] = Field(
        default="Condition", description="Resource type identifier"
    )

    # ========================================
    # FHIR R5 REQUIRED FIELDS
    # ========================================

    # Clinical Status - required in FHIR (1..1)
    clinical_status: ConditionClinicalStatus = Field(
        description="active | recurrence | relapse | inactive | remission | resolved | unknown"
    )

    # Subject - required in FHIR (1..1)
    subject: dict[str, Any] = Field(
        description="Who has the condition (Reference to Patient or Group)"
    )

    # ========================================
    # FHIR R5 OPTIONAL FIELDS
    # ========================================

    # Identifiers
    identifier: list[dict[str, Any]] = Field(
        default_factory=list, description="External identifiers for this condition"
    )

    # Verification Status
    verification_status: ConditionVerificationStatus | None = Field(
        default=None,
        description="unconfirmed | provisional | differential | confirmed | refuted | entered-in-error"
    )

    # Category (multiple allowed)
    category: list[dict[str, Any]] = Field(
        default_factory=list,
        description="problem-list-item | encounter-diagnosis (CodeableConcept)"
    )

    # Severity
    severity: dict[str, Any] | None = Field(
        default=None,
        description="Subjective severity of condition (CodeableConcept)"
    )

    # Code
    code: dict[str, Any] | None = Field(
        default=None,
        description="Identification of the condition, problem or diagnosis (CodeableConcept)"
    )

    # Body Site
    body_site: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Anatomical location, if relevant (CodeableConcept)"
    )

    # Encounter
    encounter: dict[str, Any] | None = Field(
        default=None,
        description="The Encounter during which this Condition was created"
    )

    # Onset (choice of types)
    onset_date_time: datetime | None = Field(
        default=None,
        description="Date and time of onset"
    )

    onset_age: dict[str, Any] | None = Field(
        default=None,
        description="Age at onset"
    )

    onset_period: dict[str, Any] | None = Field(
        default=None,
        description="Period of onset"
    )

    onset_range: dict[str, Any] | None = Field(
        default=None,
        description="Range of onset"
    )

    onset_string: str | None = Field(
        default=None,
        description="Onset description as string"
    )

    # Abatement (choice of types)
    abatement_date_time: datetime | None = Field(
        default=None,
        description="Date and time of resolution/remission"
    )

    abatement_age: dict[str, Any] | None = Field(
        default=None,
        description="Age at resolution"
    )

    abatement_period: dict[str, Any] | None = Field(
        default=None,
        description="Period of resolution"
    )

    abatement_range: dict[str, Any] | None = Field(
        default=None,
        description="Range of resolution"
    )

    abatement_string: str | None = Field(
        default=None,
        description="Resolution description as string"
    )

    # Recorded Date
    recorded_date: datetime | None = Field(
        default=None,
        description="Date condition was first recorded"
    )

    # Participant
    participant: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Who or what participated in activities related to the condition"
    )

    # Stage
    stage: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Stage/grade, usually assessed formally"
    )

    # Evidence
    evidence: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Supporting evidence for the verification status"
    )

    # Note
    note: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Additional information about the Condition (Annotation)"
    )

    # ========================================
    # LLM-FRIENDLY FIELDS (HACS Extensions)
    # ========================================

    # Simple identification
    condition_name: str | None = Field(
        default=None,
        description="Common name of the condition/problem",
        examples=[
            "Type 2 Diabetes",
            "Hypertension",
            "Chronic back pain",
            "Anxiety disorder",
            "Migraine headaches",
            "Pneumonia"
        ],
    )

    condition_description: str | None = Field(
        default=None,
        description="Detailed description of the condition",
        examples=[
            "Patient has well-controlled type 2 diabetes mellitus",
            "Essential hypertension with target BP <140/90",
            "Chronic lower back pain following injury 2 years ago"
        ]
    )

    # Simple categorization
    condition_category: ConditionCategory | None = Field(
        default=None,
        description="Simple classification of the condition"
    )

    condition_severity: ConditionSeverity | None = Field(
        default=None,
        description="Simple severity assessment"
    )

    # Simple body site
    anatomical_location: ConditionBodySite | None = Field(
        default=None,
        description="Main body area affected by the condition"
    )

    # Clinical context
    chief_complaint: str | None = Field(
        default=None,
        description="Primary symptom or concern as stated by patient",
        examples=[
            "Chest pain for 2 hours",
            "Difficulty breathing",
            "Severe headache",
            "Abdominal pain"
        ]
    )

    presenting_symptoms: list[str] = Field(
        default_factory=list,
        description="List of presenting symptoms",
        examples=[
            ["Chest pain", "Shortness of breath", "Nausea"],
            ["Fever", "Cough", "Fatigue"],
            ["Headache", "Sensitivity to light", "Nausea"]
        ]
    )

    risk_factors: list[str] = Field(
        default_factory=list,
        description="Known risk factors for this condition",
        examples=[
            ["Family history", "Smoking", "Obesity"],
            ["Age over 65", "Hypertension", "High cholesterol"],
            ["Stress", "Poor sleep", "Caffeine intake"]
        ]
    )

    # Timing information
    onset_description: str | None = Field(
        default=None,
        description="Description of when/how the condition started",
        examples=[
            "Gradual onset over 6 months",
            "Sudden onset 2 hours ago",
            "Progressive worsening since childhood",
            "Started after car accident last year"
        ]
    )

    duration_description: str | None = Field(
        default=None,
        description="How long the condition has been present",
        examples=[
            "3 days",
            "6 months",
            "Since childhood",
            "Chronic - ongoing for years"
        ]
    )

    # Progression and status
    progression_status: str | None = Field(
        default=None,
        description="How the condition is progressing",
        examples=[
            "Improving with treatment",
            "Stable on current medications",
            "Progressively worsening",
            "In remission",
            "Resolved"
        ]
    )

    current_status_description: str | None = Field(
        default=None,
        description="Current state of the condition in plain language"
    )

    # Treatment context
    current_treatment: list[str] = Field(
        default_factory=list,
        description="Current treatments for this condition",
        examples=[
            ["Metformin 500mg twice daily", "Diet modification", "Regular exercise"],
            ["Lisinopril 10mg daily", "Low sodium diet"],
            ["Physical therapy", "NSAIDs as needed", "Heat/ice therapy"]
        ]
    )

    treatment_response: str | None = Field(
        default=None,
        description="How well the condition is responding to treatment",
        examples=[
            "Good response to current medications",
            "Partial improvement with therapy",
            "No significant improvement",
            "Complete resolution with treatment"
        ]
    )

    # Complications and related conditions
    complications: list[str] = Field(
        default_factory=list,
        description="Known complications of this condition",
        examples=[
            ["Diabetic retinopathy", "Peripheral neuropathy"],
            ["Heart failure", "Kidney disease"],
            ["Chronic pain", "Limited mobility"]
        ]
    )

    related_conditions: list[str] = Field(
        default_factory=list,
        description="Other conditions related to or caused by this condition"
    )

    # Functional impact
    functional_impact: str | None = Field(
        default=None,
        description="How this condition affects daily functioning",
        examples=[
            "Mild impact on daily activities",
            "Significant limitation in physical activity",
            "Requires assistance with activities of daily living",
            "No functional limitations"
        ]
    )

    quality_of_life_impact: str | None = Field(
        default=None,
        description="Impact on patient's quality of life"
    )

    # Prognosis
    prognosis: str | None = Field(
        default=None,
        description="Expected course and outcome of the condition",
        examples=[
            "Excellent with proper management",
            "Good if treatment adhered to",
            "Progressive disease with symptomatic management",
            "Complete recovery expected"
        ]
    )

    # Provider information
    diagnosing_provider: str | None = Field(
        default=None,
        description="Healthcare provider who diagnosed this condition",
        examples=["Dr. Smith, MD", "Dr. Johnson, Cardiologist", "Emergency Department"]
    )

    managing_provider: str | None = Field(
        default=None,
        description="Healthcare provider currently managing this condition"
    )

    # Additional context
    condition_notes: str | None = Field(
        default=None,
        description="Additional notes about this condition"
    )

    patient_concerns: str | None = Field(
        default=None,
        description="Patient's specific concerns about this condition"
    )

    family_history_relevant: bool | None = Field(
        default=None,
        description="Whether family history is relevant to this condition"
    )

    # ========================================
    # HELPER METHODS
    # ========================================

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        name = self.condition_name or "Unknown condition"
        status = self.clinical_status if isinstance(self.clinical_status, str) else (
            self.clinical_status.value if self.clinical_status else "unknown status"
        )
        return f"{name} ({status})"

    @property
    def display_name(self) -> str:
        """Get a display-friendly name for the condition."""
        if self.condition_name:
            return self.condition_name
        if self.code and "text" in self.code:
            return self.code["text"]
        if self.chief_complaint:
            return self.chief_complaint
        return f"Condition {self.id}"

    @property
    def is_active(self) -> bool:
        """Check if the condition is currently active."""
        if not self.clinical_status:
            return False
        active_statuses = [
            ConditionClinicalStatus.ACTIVE,
            ConditionClinicalStatus.RECURRENCE,
            ConditionClinicalStatus.RELAPSE
        ]
        return self.clinical_status in active_statuses

    @property
    def is_resolved(self) -> bool:
        """Check if the condition is resolved."""
        return self.clinical_status == ConditionClinicalStatus.RESOLVED if self.clinical_status else False

    @property
    def is_chronic(self) -> bool:
        """Check if this appears to be a chronic condition."""
        if self.condition_category == ConditionCategory.CHRONIC_CONDITION:
            return True
        # Look for indicators in duration or description
        chronic_indicators = ["chronic", "ongoing", "long-term", "years", "permanent"]
        description_text = " ".join(filter(None, [
            self.condition_description,
            self.duration_description,
            self.progression_status
        ])).lower()
        return any(indicator in description_text for indicator in chronic_indicators)

    @property
    def has_complications(self) -> bool:
        """Check if the condition has known complications."""
        return bool(self.complications)

    @property
    def is_confirmed(self) -> bool:
        """Check if the condition is confirmed."""
        return self.verification_status == ConditionVerificationStatus.CONFIRMED if self.verification_status else False

    def get_onset_display(self) -> str:
        """Get human-readable onset information."""
        if self.onset_description:
            return self.onset_description
        if self.onset_date_time:
            return f"Started {self.onset_date_time.strftime('%Y-%m-%d')}"
        if self.onset_string:
            return self.onset_string
        return "Onset unknown"

    def get_duration_display(self) -> str:
        """Get human-readable duration information."""
        if self.duration_description:
            return self.duration_description
        if self.onset_date_time and not self.is_resolved:
            from datetime import datetime
            duration = datetime.now() - self.onset_date_time
            days = duration.days
            if days < 30:
                return f"{days} days"
            elif days < 365:
                months = days // 30
                return f"{months} month{'s' if months != 1 else ''}"
            else:
                years = days // 365
                return f"{years} year{'s' if years != 1 else ''}"
        return "Duration unknown"

    def get_severity_display(self) -> str:
        """Get human-readable severity information."""
        if self.condition_severity:
            severity = self.condition_severity if isinstance(self.condition_severity, str) else self.condition_severity.value
            return severity.replace("_", " ").title()
        if self.severity and "text" in self.severity:
            return self.severity["text"]
        return "Severity not specified"

    def get_participant_names(self) -> list[str]:
        """Get list of participant names."""
        names = []
        if self.diagnosing_provider:
            names.append(self.diagnosing_provider)
        if self.managing_provider and self.managing_provider != self.diagnosing_provider:
            names.append(self.managing_provider)
        for participant in self.participant:
            if "actor" in participant and "display" in participant["actor"]:
                names.append(participant["actor"]["display"])
        return list(set(names))  # Remove duplicates

    def get_body_sites(self) -> list[str]:
        """Get list of affected body sites."""
        sites = []
        if self.anatomical_location:
            location = self.anatomical_location if isinstance(self.anatomical_location, str) else self.anatomical_location.value
            sites.append(location.replace("_", " ").title())
        for site in self.body_site:
            if "text" in site:
                sites.append(site["text"])
        return sites

    def is_problem_list_item(self) -> bool:
        """Check if this is a problem list item."""
        if self.condition_category == ConditionCategory.PROBLEM_LIST_ITEM:
            return True
        for cat in self.category:
            if "coding" in cat:
                for coding in cat["coding"]:
                    if coding.get("code") == "problem-list-item":
                        return True
        return False

    def is_encounter_diagnosis(self) -> bool:
        """Check if this is an encounter diagnosis."""
        if self.condition_category == ConditionCategory.ENCOUNTER_DIAGNOSIS:
            return True
        for cat in self.category:
            if "coding" in cat:
                for coding in cat["coding"]:
                    if coding.get("code") == "encounter-diagnosis":
                        return True
        return False


# Alias for those who prefer "Problem" terminology
Problem = Condition
