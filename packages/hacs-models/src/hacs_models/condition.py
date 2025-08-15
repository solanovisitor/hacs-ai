"""
Condition model for HACS (comprehensive).

HACS-native, FHIR-inspired Condition representing detailed information about
conditions, problems, diagnoses, or clinical issues. Optimized for LLM context
engineering with rich descriptive metadata and clinical workflow support.
"""

from datetime import datetime, date
from typing import Any, Literal
from pydantic import Field

from .base_resource import DomainResource
from .types import ConditionClinicalStatus, ConditionVerificationStatus


class ConditionStage(DomainResource):
    """Stage or grade of a condition."""
    
    resource_type: Literal["ConditionStage"] = Field(default="ConditionStage")
    
    summary: dict[str, Any] | None = Field(
        default=None,
        description="Simple summary of the stage, such as Stage IIIA",
        examples=[{"coding": [{"system": "http://snomed.info/sct", "code": "258219007", "display": "Stage IIIA"}]}]
    )
    
    assessment: list[str] = Field(
        default_factory=list,
        description="Formal record of assessment used to determine the stage/grade",
        examples=[["DiagnosticReport/pathology-123", "Observation/tumor-size"]]
    )
    
    type_: dict[str, Any] | None = Field(
        default=None,
        alias="type",
        description="Kind of staging (TNM, clinical, pathologic, etc.)",
        examples=[{"coding": [{"system": "staging-type", "code": "clinical", "display": "Clinical staging"}]}]
    )


class ConditionEvidence(DomainResource):
    """Supporting evidence for the condition."""
    
    resource_type: Literal["ConditionEvidence"] = Field(default="ConditionEvidence")
    
    code: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Manifestation/symptom codes that support the condition",
        examples=[[{"coding": [{"system": "http://snomed.info/sct", "code": "25064002", "display": "Headache"}]}]]
    )
    
    detail: list[str] = Field(
        default_factory=list,
        description="Links to other relevant information supporting the condition",
        examples=[["Observation/blood-pressure-high", "DiagnosticReport/ecg-abnormal"]]
    )


class Condition(DomainResource):
    """
    Detailed information about conditions, problems, or diagnoses.
    
    Records conditions, problems, diagnoses, or other clinical issues that are
    clinically significant and can impact the patient's health. Optimized for
    LLM context engineering withFHIR-aligned metadata.
    
    Key Features:
        - Rich clinical status and verification tracking
        - Temporal onset and resolution support
        - Severity and stage classification
        - Evidence and manifestation linking
        - Care team and encounter association
        
    Example Use Cases:
        - Primary and secondary diagnoses
        - Chronic conditions and comorbidities
        - Symptoms and clinical findings
        - Problem lists and care plans
        - Quality reporting and analytics
    """
    
    resource_type: Literal["Condition"] = Field(default="Condition")
    
    # Identifiers
    identifier: list[dict[str, Any]] = Field(
        default_factory=list,
        description="External identifiers for this condition",
        examples=[[{"system": "http://hospital.example.org/condition-ids", "value": "COND-12345"}]]
    )
    
    # Status fields (critical for clinical decision making)
    clinical_status: ConditionClinicalStatus | None = Field(
        default=None,
        description="Active | recurrence | relapse | inactive | remission | resolved"
    )
    
    verification_status: ConditionVerificationStatus | None = Field(
        default=None,
        description="Unconfirmed | provisional | differential | confirmed | refuted | entered-in-error"
    )
    
    # Classification and coding
    category: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Category of the condition (problem-list-item, encounter-diagnosis, etc.)",
        examples=[[{"coding": [{"system": "condition-category", "code": "problem-list-item", "display": "Problem List Item"}]}]]
    )
    
    severity: dict[str, Any] | None = Field(
        default=None,
        description="Subjective severity of condition",
        examples=[{"coding": [{"system": "http://snomed.info/sct", "code": "24484000", "display": "Severe"}]}]
    )
    
    code: dict[str, Any] | None = Field(
        default=None,
        description="Identification of the condition, problem or diagnosis",
        examples=[{"coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": "I10", "display": "Essential hypertension"}]}]
    )
    
    body_site: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Anatomical location of the condition",
        examples=[[{"coding": [{"system": "http://snomed.info/sct", "code": "80891009", "display": "Heart structure"}]}]]
    )
    
    # Subject and context
    subject: str | None = Field(
        default=None,
        description="Who has the condition (Patient reference)",
        examples=["Patient/patient-123"]
    )
    
    encounter: str | None = Field(
        default=None,
        description="Encounter when condition first asserted",
        examples=["Encounter/encounter-456"]
    )
    
    # Temporal information
    onset_date_time: datetime | None = Field(
        default=None,
        description="Estimated or actual date, date-time when condition began"
    )
    
    onset_age: dict[str, Any] | None = Field(
        default=None,
        description="Estimated or actual age when condition began",
        examples=[{"value": 45, "unit": "years", "system": "http://unitsofmeasure.org", "code": "a"}]
    )
    
    onset_period: dict[str, datetime] | None = Field(
        default=None,
        description="Period when condition began",
        examples=[{"start": "2024-01-01T00:00:00Z", "end": "2024-01-31T23:59:59Z"}]
    )
    
    onset_range: dict[str, Any] | None = Field(
        default=None,
        description="Range when condition began"
    )
    
    onset_string: str | None = Field(
        default=None,
        description="Estimated or actual time when condition began (text)",
        examples=["childhood", "during pregnancy", "after surgery"]
    )
    
    abatement_date_time: datetime | None = Field(
        default=None,
        description="When condition resolved"
    )
    
    abatement_age: dict[str, Any] | None = Field(
        default=None,
        description="Age when condition resolved"
    )
    
    abatement_period: dict[str, datetime] | None = Field(
        default=None,
        description="Period when condition resolved"
    )
    
    abatement_range: dict[str, Any] | None = Field(
        default=None,
        description="Range when condition resolved"
    )
    
    abatement_string: str | None = Field(
        default=None,
        description="When condition resolved (text)",
        examples=["resolved with treatment", "spontaneous resolution"]
    )
    
    # Recording information
    recorded_date: datetime | None = Field(
        default=None,
        description="Date record was first recorded"
    )
    
    recorder: str | None = Field(
        default=None,
        description="Who recorded the condition",
        examples=["Practitioner/dr-smith", "Patient/patient-123"]
    )
    
    asserter: str | None = Field(
        default=None,
        description="Person who asserts this condition",
        examples=["Practitioner/dr-jones", "Patient/patient-123"]
    )
    
    # Clinical details
    stage: list[ConditionStage] = Field(
        default_factory=list,
        description="Stage/grade of the condition"
    )
    
    evidence: list[ConditionEvidence] = Field(
        default_factory=list,
        description="Supporting evidence for the condition"
    )
    
    note: list[str] = Field(
        default_factory=list,
        description="Additional information about the condition",
        examples=[["Patient reports symptoms worse in morning", "Family history positive for similar condition"]]
    )
    
    def add_evidence(self, detail_ref: str, code: dict[str, Any] | None = None) -> ConditionEvidence:
        """Add evidence supporting this condition."""
        evidence = ConditionEvidence(
            detail=[detail_ref],
            code=[code] if code else []
        )
        self.evidence.append(evidence)
        self.update_timestamp()
        return evidence
    
    def add_stage(self, summary: dict[str, Any], assessment_refs: list[str] | None = None) -> ConditionStage:
        """Add staging information for this condition."""
        stage = ConditionStage(
            summary=summary,
            assessment=assessment_refs or []
        )
        self.stage.append(stage)
        self.update_timestamp()
        return stage
    
    def add_note(self, note: str) -> None:
        """Add a note about this condition."""
        if note.strip():
            self.note.append(note.strip())
            self.update_timestamp()
    
    def set_resolved(self, resolution_date: datetime | None = None, resolution_note: str | None = None) -> None:
        """Mark the condition as resolved."""
        self.clinical_status = ConditionClinicalStatus.RESOLVED
        if resolution_date:
            self.abatement_date_time = resolution_date
        if resolution_note:
            self.add_note(f"Resolution: {resolution_note}")
        self.update_timestamp()
    
    def set_inactive(self, reason: str | None = None) -> None:
        """Mark the condition as inactive."""
        self.clinical_status = ConditionClinicalStatus.INACTIVE
        if reason:
            self.add_note(f"Inactive: {reason}")
        self.update_timestamp()
    
    def is_active(self) -> bool:
        """Check if the condition is currently active."""
        return self.clinical_status in [
            ConditionClinicalStatus.ACTIVE,
            ConditionClinicalStatus.RECURRENCE,
            ConditionClinicalStatus.RELAPSE
        ]
    
    def is_resolved(self) -> bool:
        """Check if the condition is resolved."""
        return self.clinical_status in [
            ConditionClinicalStatus.RESOLVED,
            ConditionClinicalStatus.REMISSION
        ]
    
    def get_display_text(self) -> str:
        """Get human-readable display text for the condition."""
        if self.code and isinstance(self.code, dict):
            # Try to get display text from coding
            coding = self.code.get("coding", [])
            if coding and len(coding) > 0:
                return coding[0].get("display", "Unknown condition")
            # Fall back to text
            return self.code.get("text", "Unknown condition")
        return "Unknown condition"
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        condition_text = self.get_display_text()
        status_str = f" ({self.clinical_status})" if self.clinical_status else ""
        return f"Condition('{condition_text}'{status_str})"