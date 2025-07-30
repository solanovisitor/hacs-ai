"""
HACS FamilyMemberHistory Model - FHIR R5 Compliant

This module implements the FHIR R5 FamilyMemberHistory resource with full compliance
to the healthcare interoperability standard. The FamilyMemberHistory resource records
significant health conditions for a particular individual related to the subject.

FHIR R5 FamilyMemberHistory Resource:
https://hl7.org/fhir/R5/familymemberhistory.html

Key Features:
- Full FHIR R5 compliance with all 35+ fields
- Comprehensive validation rules and constraints (3 FHIR rules)
- Support for conditions, procedures, and family relationships
- Age, birth, and death information tracking
- LLM-friendly fields for AI applications
- Genetic and family history analysis support
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from ..base_resource import BaseResource


class FamilyHistoryStatus(str, Enum):
    """FHIR R5 Family History Status codes."""
    PARTIAL = "partial"
    COMPLETED = "completed"
    ENTERED_IN_ERROR = "entered-in-error"
    HEALTH_UNKNOWN = "health-unknown"


class FamilyHistoryAbsentReason(str, Enum):
    """Reasons why family member's history is not available."""
    SUBJECT_UNKNOWN = "subject-unknown"
    WITHHELD = "withheld"
    UNABLE_TO_OBTAIN = "unable-to-obtain"
    DEFERRED = "deferred"


class FamilyMemberRelationship(str, Enum):
    """Family member relationships."""
    MOTHER = "mother"
    FATHER = "father"
    PARENT = "parent"
    SIBLING = "sibling"
    BROTHER = "brother"
    SISTER = "sister"
    CHILD = "child"
    SON = "son"
    DAUGHTER = "daughter"
    SPOUSE = "spouse"
    GRANDPARENT = "grandparent"
    GRANDMOTHER = "grandmother"
    GRANDFATHER = "grandfather"
    GRANDCHILD = "grandchild"
    AUNT = "aunt"
    UNCLE = "uncle"
    COUSIN = "cousin"
    NEPHEW = "nephew"
    NIECE = "niece"
    STEP_PARENT = "step-parent"
    STEP_SIBLING = "step-sibling"
    ADOPTIVE_PARENT = "adoptive-parent"


class AdministrativeGender(str, Enum):
    """Administrative gender codes."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"


class ConditionOutcome(str, Enum):
    """Condition outcome codes."""
    RESOLVED = "resolved"
    IMPROVED = "improved"
    UNCHANGED = "unchanged"
    WORSENED = "worsened"
    DECEASED = "deceased"
    PERMANENT_DISABILITY = "permanent-disability"
    CHRONIC = "chronic"
    UNKNOWN = "unknown"


class ParticipationFunction(str, Enum):
    """Participation function types."""
    INFORMANT = "informant"
    REPORTER = "reporter"
    WITNESS = "witness"
    PROXY = "proxy"
    GUARDIAN = "guardian"
    CAREGIVER = "caregiver"


class FamilyMemberHistoryParticipant(BaseModel):
    """Participant in family member history activities."""
    function: Optional[dict[str, Any]] = Field(
        None, description="Type of involvement in the family history"
    )
    actor: dict[str, Any] = Field(
        ..., description="Who or what participated in the activities"
    )

    # LLM-friendly fields
    participant_name: Optional[str] = Field(
        None, description="Display name of the participant"
    )
    participant_role: Optional[str] = Field(
        None, description="Role description"
    )


class FamilyMemberCondition(BaseModel):
    """Condition that the family member had."""
    code: dict[str, Any] = Field(
        ..., description="Condition suffered by relation"
    )
    outcome: Optional[dict[str, Any]] = Field(
        None, description="Outcome of the condition (deceased, disability, etc.)"
    )
    contributed_to_death: Optional[bool] = Field(
        None, description="Whether the condition contributed to the cause of death"
    )
    onset_age: Optional[dict[str, Any]] = Field(
        None, description="Age when condition first manifested"
    )
    onset_range: Optional[dict[str, Any]] = Field(
        None, description="Age range when condition first manifested"
    )
    onset_period: Optional[dict[str, Any]] = Field(
        None, description="Period when condition first manifested"
    )
    onset_string: Optional[str] = Field(
        None, description="Approximate description of when condition started"
    )
    note: Optional[list[dict[str, Any]]] = Field(
        None, description="Extra information about condition"
    )

    # LLM-friendly fields
    condition_name: Optional[str] = Field(
        None, description="Human-readable condition name"
    )
    severity: Optional[str] = Field(
        None, description="Condition severity description"
    )
    age_at_onset: Optional[str] = Field(
        None, description="Age when condition started"
    )
    outcome_description: Optional[str] = Field(
        None, description="What happened with this condition"
    )
    is_fatal: Optional[bool] = Field(
        None, description="Whether this condition caused or contributed to death"
    )


class FamilyMemberProcedure(BaseModel):
    """Procedure that the family member had."""
    code: dict[str, Any] = Field(
        ..., description="Procedures performed on the related person"
    )
    outcome: Optional[dict[str, Any]] = Field(
        None, description="What happened following the procedure"
    )
    contributed_to_death: Optional[bool] = Field(
        None, description="Whether the procedure contributed to the cause of death"
    )
    performed_age: Optional[dict[str, Any]] = Field(
        None, description="Age when procedure was performed"
    )
    performed_range: Optional[dict[str, Any]] = Field(
        None, description="Age range when procedure was performed"
    )
    performed_period: Optional[dict[str, Any]] = Field(
        None, description="Period when procedure was performed"
    )
    performed_string: Optional[str] = Field(
        None, description="Approximate description of when procedure was done"
    )
    performed_date_time: Optional[datetime] = Field(
        None, description="Exact date and time when procedure was performed"
    )
    note: Optional[list[dict[str, Any]]] = Field(
        None, description="Extra information about the procedure"
    )

    # LLM-friendly fields
    procedure_name: Optional[str] = Field(
        None, description="Human-readable procedure name"
    )
    age_at_procedure: Optional[str] = Field(
        None, description="Age when procedure was performed"
    )
    outcome_description: Optional[str] = Field(
        None, description="Result of the procedure"
    )
    was_successful: Optional[bool] = Field(
        None, description="Whether the procedure was successful"
    )


class FamilyMemberHistory(BaseResource):
    """
    FHIR R5 FamilyMemberHistory Resource

    Information about patient's relatives, relevant for patient care.
    Records significant health conditions for a particular individual related to the subject.
    """

    resource_type: Literal["FamilyMemberHistory"] = Field(
        default="FamilyMemberHistory", description="Resource type identifier"
    )

    # FHIR R5 Core Fields
    identifier: Optional[list[dict[str, Any]]] = Field(
        None, description="External Id(s) for this record"
    )
    instantiates_canonical: Optional[list[str]] = Field(
        None, description="Instantiates FHIR protocol or definition"
    )
    instantiates_uri: Optional[list[str]] = Field(
        None, description="Instantiates external protocol or definition"
    )
    status: FamilyHistoryStatus = Field(
        ..., description="Status of the family history record"
    )
    data_absent_reason: Optional[dict[str, Any]] = Field(
        None, description="Reason why family member's history is not available"
    )
    patient: dict[str, Any] = Field(
        ..., description="Patient history is about"
    )
    date: Optional[datetime] = Field(
        None, description="When history was recorded or last updated"
    )
    participant: Optional[list[FamilyMemberHistoryParticipant]] = Field(
        None, description="Who or what participated in the activities"
    )
    name: Optional[str] = Field(
        None, description="The family member described"
    )
    relationship: dict[str, Any] = Field(
        ..., description="Relationship to the subject"
    )
    sex: Optional[dict[str, Any]] = Field(
        None, description="Male | female | other | unknown"
    )

    # Birth information (choice type - only one can be present)
    born_period: Optional[dict[str, Any]] = Field(
        None, description="Approximate birth period"
    )
    born_date: Optional[datetime] = Field(
        None, description="Birth date"
    )
    born_string: Optional[str] = Field(
        None, description="Approximate birth description"
    )

    # Age information (choice type - only one can be present)
    age_age: Optional[dict[str, Any]] = Field(
        None, description="Current age as Age type"
    )
    age_range: Optional[dict[str, Any]] = Field(
        None, description="Current age as range"
    )
    age_string: Optional[str] = Field(
        None, description="Current age as string"
    )
    estimated_age: Optional[bool] = Field(
        None, description="Age is estimated?"
    )

    # Death information (choice type - only one can be present)
    deceased_boolean: Optional[bool] = Field(
        None, description="Is the family member deceased?"
    )
    deceased_age: Optional[dict[str, Any]] = Field(
        None, description="Age at death"
    )
    deceased_range: Optional[dict[str, Any]] = Field(
        None, description="Age range at death"
    )
    deceased_date: Optional[datetime] = Field(
        None, description="Date of death"
    )
    deceased_string: Optional[str] = Field(
        None, description="Approximate description of death"
    )

    reason: Optional[list[dict[str, Any]]] = Field(
        None, description="Why was family member history performed?"
    )
    note: Optional[list[dict[str, Any]]] = Field(
        None, description="General note about related person"
    )
    condition: Optional[list[FamilyMemberCondition]] = Field(
        None, description="Condition that the related person had"
    )
    procedure: Optional[list[FamilyMemberProcedure]] = Field(
        None, description="Procedures that the related person had"
    )

    # LLM-friendly fields
    family_member_name: Optional[str] = Field(
        None, description="Display name of the family member"
    )
    relationship_description: Optional[str] = Field(
        None, description="Relationship to the patient in simple terms"
    )
    current_age_display: Optional[str] = Field(
        None, description="Current age in human-readable format"
    )
    birth_info_display: Optional[str] = Field(
        None, description="Birth information in human-readable format"
    )
    death_info_display: Optional[str] = Field(
        None, description="Death information in human-readable format"
    )
    gender_description: Optional[str] = Field(
        None, description="Gender in human-readable format"
    )
    living_status: Optional[bool] = Field(
        None, description="Whether the family member is currently living"
    )
    has_significant_history: Optional[bool] = Field(
        None, description="Whether this family member has significant medical history"
    )
    genetic_risk_factors: Optional[list[str]] = Field(
        None, description="Genetic risk factors from this family member"
    )
    summary_description: Optional[str] = Field(
        None, description="Brief summary of this family member's medical history"
    )

    def __init__(self, **data):
        if "id" not in data:
            data["id"] = str(uuid.uuid4())
        if "date" not in data:
            data["date"] = datetime.now(timezone.utc)
        super().__init__(**data)

    @field_validator("date", "born_date", "deceased_date")
    @classmethod
    def validate_datetime_timezone(cls, v):
        """Ensure datetime fields are timezone-aware."""
        if v and isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    @model_validator(mode="after")
    def validate_family_history_constraints(self) -> "FamilyMemberHistory":
        """Validate FHIR R5 family history constraints."""

        # Rule fhs-1: Can have age[x] or born[x], but not both
        age_fields = [self.age_age, self.age_range, self.age_string]
        born_fields = [self.born_period, self.born_date, self.born_string]

        has_age = any(field is not None for field in age_fields)
        has_born = any(field is not None for field in born_fields)

        if has_age and has_born:
            raise ValueError("Can have age[x] or born[x], but not both")

        # Rule fhs-2: Can only have estimatedAge if age[x] is present
        if self.estimated_age is not None and not has_age:
            raise ValueError("Can only have estimatedAge if age[x] is present")

        # Rule fhs-3: Can have age[x] or deceased[x], but not both
        deceased_fields = [
            self.deceased_boolean, self.deceased_age, self.deceased_range,
            self.deceased_date, self.deceased_string
        ]
        has_deceased = any(field is not None for field in deceased_fields)

        if has_age and has_deceased:
            raise ValueError("Can have age[x] or deceased[x], but not both")

        return self

    # Helper properties
    @property
    def display_name(self) -> str:
        """Human-readable display name for the family member."""
        if self.family_member_name:
            return self.family_member_name
        if self.name:
            return self.name

        # Build from relationship
        relationship_text = "Unknown Family Member"
        if isinstance(self.relationship, dict) and self.relationship.get("text"):
            relationship_text = self.relationship["text"]

        return relationship_text

    @property
    def age_display(self) -> str:
        """Human-readable age display."""
        if self.current_age_display:
            return self.current_age_display

        if self.age_string:
            return self.age_string
        elif self.age_age and isinstance(self.age_age, dict):
            if self.age_age.get("value") and self.age_age.get("unit"):
                estimated = " (estimated)" if self.estimated_age else ""
                return f"{self.age_age['value']} {self.age_age['unit']}{estimated}"
        elif self.age_range and isinstance(self.age_range, dict):
            low = self.age_range.get("low", {}).get("value", "?")
            high = self.age_range.get("high", {}).get("value", "?")
            return f"{low}-{high} years"

        return "Age unknown"

    @property
    def birth_display(self) -> str:
        """Human-readable birth information display."""
        if self.birth_info_display:
            return self.birth_info_display

        if self.born_string:
            return self.born_string
        elif self.born_date:
            return self.born_date.strftime("%Y-%m-%d")
        elif self.born_period and isinstance(self.born_period, dict):
            start = self.born_period.get("start", "?")
            end = self.born_period.get("end", "?")
            return f"Born between {start} and {end}"

        return "Birth date unknown"

    @property
    def death_display(self) -> str:
        """Human-readable death information display."""
        if self.death_info_display:
            return self.death_info_display

        if self.deceased_boolean is False:
            return "Living"
        elif self.deceased_boolean is True and not any([
            self.deceased_age, self.deceased_range, self.deceased_date, self.deceased_string
        ]):
            return "Deceased"
        elif self.deceased_string:
            return f"Deceased: {self.deceased_string}"
        elif self.deceased_date:
            return f"Deceased: {self.deceased_date.strftime('%Y-%m-%d')}"
        elif self.deceased_age and isinstance(self.deceased_age, dict):
            if self.deceased_age.get("value") and self.deceased_age.get("unit"):
                return f"Deceased at age {self.deceased_age['value']} {self.deceased_age['unit']}"
        elif self.deceased_range and isinstance(self.deceased_range, dict):
            low = self.deceased_range.get("low", {}).get("value", "?")
            high = self.deceased_range.get("high", {}).get("value", "?")
            return f"Deceased between ages {low}-{high}"

        return "Living status unknown"

    @property
    def gender_display(self) -> str:
        """Human-readable gender display."""
        if self.gender_description:
            return self.gender_description

        if isinstance(self.sex, dict) and self.sex.get("text"):
            return self.sex["text"]
        elif isinstance(self.sex, dict) and self.sex.get("coding"):
            coding = self.sex["coding"][0] if self.sex["coding"] else {}
            return coding.get("display", coding.get("code", "Unknown"))

        return "Gender unknown"

    @property
    def status_display(self) -> str:
        """Human-readable status display."""
        status_map = {
            FamilyHistoryStatus.PARTIAL: "Partial Information",
            FamilyHistoryStatus.COMPLETED: "Complete",
            FamilyHistoryStatus.ENTERED_IN_ERROR: "Error",
            FamilyHistoryStatus.HEALTH_UNKNOWN: "Health Status Unknown"
        }
        return status_map.get(self.status, str(self.status))

    # Helper methods
    def is_deceased(self) -> bool:
        """Check if the family member is deceased."""
        return bool(
            self.deceased_boolean or
            self.deceased_age or
            self.deceased_range or
            self.deceased_date or
            self.deceased_string
        )

    def is_living(self) -> bool:
        """Check if the family member is living."""
        if self.deceased_boolean is False:
            return True
        return not self.is_deceased()

    def get_significant_conditions(self) -> list[str]:
        """Get list of significant conditions."""
        conditions = []
        if self.condition:
            for cond in self.condition:
                if cond.condition_name:
                    conditions.append(cond.condition_name)
                elif isinstance(cond.code, dict) and cond.code.get("text"):
                    conditions.append(cond.code["text"])
        return conditions

    def get_significant_procedures(self) -> list[str]:
        """Get list of significant procedures."""
        procedures = []
        if self.procedure:
            for proc in self.procedure:
                if proc.procedure_name:
                    procedures.append(proc.procedure_name)
                elif isinstance(proc.code, dict) and proc.code.get("text"):
                    procedures.append(proc.code["text"])
        return procedures

    def get_fatal_conditions(self) -> list[str]:
        """Get conditions that contributed to death."""
        fatal_conditions = []
        if self.condition:
            for cond in self.condition:
                if cond.contributed_to_death:
                    if cond.condition_name:
                        fatal_conditions.append(cond.condition_name)
                    elif isinstance(cond.code, dict) and cond.code.get("text"):
                        fatal_conditions.append(cond.code["text"])
        return fatal_conditions

    def get_genetic_risk_indicators(self) -> list[str]:
        """Get potential genetic risk indicators."""
        risk_indicators = []

        # Add conditions that may have genetic components
        genetic_keywords = [
            "cancer", "diabetes", "heart", "cardiovascular", "hypertension",
            "alzheimer", "parkinson", "huntington", "cystic fibrosis",
            "sickle cell", "hemophilia", "muscular dystrophy"
        ]

        conditions = self.get_significant_conditions()
        for condition in conditions:
            condition_lower = condition.lower()
            for keyword in genetic_keywords:
                if keyword in condition_lower:
                    risk_indicators.append(condition)
                    break

        return risk_indicators

    def get_relationship_display(self) -> str:
        """Get human-readable relationship description."""
        if self.relationship_description:
            return self.relationship_description

        if isinstance(self.relationship, dict):
            if self.relationship.get("text"):
                return self.relationship["text"]
            elif self.relationship.get("coding"):
                coding = self.relationship["coding"][0] if self.relationship["coding"] else {}
                return coding.get("display", coding.get("code", "Unknown relationship"))

        return "Unknown relationship"

    def has_medical_history(self) -> bool:
        """Check if family member has significant medical history."""
        return bool(
            (self.condition and len(self.condition) > 0) or
            (self.procedure and len(self.procedure) > 0)
        )

    def get_age_at_condition_onset(self, condition_index: int = 0) -> Optional[str]:
        """Get age at onset for a specific condition."""
        if not self.condition or condition_index >= len(self.condition):
            return None

        cond = self.condition[condition_index]

        if cond.age_at_onset:
            return cond.age_at_onset
        elif cond.onset_string:
            return cond.onset_string
        elif cond.onset_age and isinstance(cond.onset_age, dict):
            if cond.onset_age.get("value") and cond.onset_age.get("unit"):
                return f"{cond.onset_age['value']} {cond.onset_age['unit']}"

        return None

    def to_family_tree_summary(self) -> dict[str, Any]:
        """Convert to family tree-friendly summary."""
        return {
            "id": self.id,
            "name": self.display_name,
            "relationship": self.get_relationship_display(),
            "gender": self.gender_display,
            "age": self.age_display,
            "birth_info": self.birth_display,
            "death_info": self.death_display,
            "is_living": self.is_living(),
            "significant_conditions": self.get_significant_conditions(),
            "significant_procedures": self.get_significant_procedures(),
            "genetic_risks": self.get_genetic_risk_indicators(),
            "has_medical_history": self.has_medical_history(),
            "status": self.status_display,
        }

    def to_genetic_summary(self) -> dict[str, Any]:
        """Convert to genetic analysis-friendly summary."""
        return {
            "family_member_id": self.id,
            "relationship": self.get_relationship_display(),
            "gender": self.gender_display,
            "age_info": self.age_display,
            "living_status": self.death_display,
            "genetic_risk_conditions": self.get_genetic_risk_indicators(),
            "fatal_conditions": self.get_fatal_conditions(),
            "all_conditions": self.get_significant_conditions(),
            "condition_details": [
                {
                    "condition": cond.condition_name or (cond.code.get("text") if isinstance(cond.code, dict) else "Unknown"),
                    "age_at_onset": cond.age_at_onset or cond.onset_string,
                    "outcome": cond.outcome_description,
                    "contributed_to_death": cond.contributed_to_death,
                } for cond in (self.condition or [])
            ],
            "data_quality": "complete" if self.status == FamilyHistoryStatus.COMPLETED else "partial"
        }

    def to_clinical_summary(self) -> dict[str, Any]:
        """Convert to clinical summary format."""
        return {
            "family_member_id": self.id,
            "name": self.display_name,
            "relationship": self.get_relationship_display(),
            "demographics": {
                "gender": self.gender_display,
                "age": self.age_display,
                "birth_info": self.birth_display,
                "living_status": self.death_display,
                "is_living": self.is_living()
            },
            "medical_history": {
                "has_history": self.has_medical_history(),
                "conditions": self.get_significant_conditions(),
                "procedures": self.get_significant_procedures(),
                "genetic_risks": self.get_genetic_risk_indicators(),
                "fatal_conditions": self.get_fatal_conditions(),
            },
            "data_status": {
                "status": self.status_display,
                "recorded_date": self.date.isoformat() if self.date else None,
                "absent_reason": self.data_absent_reason.get("text") if self.data_absent_reason else None,
            },
            "notes": [
                note.get("text") for note in (self.note or [])
                if isinstance(note, dict) and note.get("text")
            ],
        }


# Type aliases for different family history contexts
FamilyHistory = FamilyMemberHistory
GeneticHistory = FamilyMemberHistory
FamilialRiskAssessment = FamilyMemberHistory