"""
AllergyIntolerance model based on FHIR US Core AllergyIntolerance Profile.

This model represents allergies and intolerances with comprehensive clinical information,
optimized for structured outputs and LLM interactions.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from ..base_resource import BaseResource
from pydantic import Field


class AllergyIntoleranceType(str, Enum):
    """Type of allergy or intolerance."""

    ALLERGY = "allergy"
    INTOLERANCE = "intolerance"


class AllergyIntoleranceCategory(str, Enum):
    """Category of the allergy or intolerance."""

    FOOD = "food"
    MEDICATION = "medication"
    ENVIRONMENT = "environment"
    BIOLOGIC = "biologic"


class AllergyIntoleranceCriticality(str, Enum):
    """Criticality of the allergy or intolerance."""

    LOW = "low"
    HIGH = "high"
    UNABLE_TO_ASSESS = "unable-to-assess"


class AllergyIntoleranceStatus(str, Enum):
    """Clinical status of the allergy or intolerance."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    RESOLVED = "resolved"


class AllergyIntoleranceVerificationStatus(str, Enum):
    """Verification status of the allergy or intolerance."""

    UNCONFIRMED = "unconfirmed"
    PROVISIONAL = "provisional"
    CONFIRMED = "confirmed"
    REFUTED = "refuted"
    ENTERED_IN_ERROR = "entered-in-error"


class ReactionSeverity(str, Enum):
    """Severity of the allergic reaction."""

    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class AllergyIntoleranceReaction(BaseResource):
    """
    Represents an allergic reaction.

    Captures details about adverse reactions including manifestations, severity, and timing.
    """

    resource_type: Literal["AllergyIntoleranceReaction"] = Field(
        default="AllergyIntoleranceReaction", description="Resource type identifier"
    )

    # Substance that caused the reaction
    substance: dict[str, Any] | None = Field(
        default=None,
        description="Specific substance or pharmaceutical product considered responsible",
    )

    # LLM-FRIENDLY: Simple substance name
    substance_name: str | None = Field(
        default=None,
        description="Simple name of the substance (e.g., 'Penicillin', 'Peanuts')",
        examples=["Penicillin", "Peanuts", "Shellfish", "Latex", "Pollen"],
    )

    # Manifestations
    manifestation: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Clinical symptoms/signs associated with the reaction",
    )

    # LLM-FRIENDLY: Simple manifestations list
    symptoms: list[str] = Field(
        default_factory=list,
        description="List of symptoms or manifestations",
        examples=[
            ["Hives", "Swelling", "Difficulty breathing"],
            ["Nausea", "Vomiting", "Diarrhea"],
            ["Rash", "Itching"],
        ],
    )

    description: str | None = Field(
        default=None, description="Text description of the reaction"
    )

    onset: datetime | None = Field(
        default=None, description="Date/time when manifestations showed"
    )

    severity: ReactionSeverity | None = Field(
        default=None, description="Clinical assessment of the severity of the reaction"
    )

    exposure_route: dict[str, Any] | None = Field(
        default=None, description="How the subject was exposed to the substance"
    )

    # LLM-FRIENDLY: Simple exposure route
    how_exposed: str | None = Field(
        default=None,
        description="How the patient was exposed",
        examples=["Oral", "Intravenous", "Topical", "Inhalation", "Contact"],
    )

    note: list[dict[str, Any]] = Field(
        default_factory=list, description="Additional text about the reaction"
    )


class AllergyIntolerance(BaseResource):
    """
    Represents an allergy or intolerance.

    Based on FHIR US Core AllergyIntolerance Profile with HACS enhancements.
    Optimized for structured outputs and LLM interactions.
    """

    resource_type: Literal["AllergyIntolerance"] = Field(
        default="AllergyIntolerance", description="Resource type identifier"
    )

    # Identifiers
    identifier: list[dict[str, Any]] = Field(
        default_factory=list,
        description="External identifiers for this allergy/intolerance",
    )

    # Clinical status - required
    clinical_status: AllergyIntoleranceStatus = Field(
        description="Current clinical status of the allergy or intolerance"
    )

    verification_status: AllergyIntoleranceVerificationStatus | None = Field(
        default=None,
        description="Assertion about certainty associated with the propensity, or potential risk",
    )

    # Type and category
    type: AllergyIntoleranceType | None = Field(
        default=None,
        description="Allergy or Intolerance (generally the type is a guess unless the reaction is confirmed by testing)",
    )

    category: list[AllergyIntoleranceCategory] = Field(
        default_factory=list, description="Category of the identified substance"
    )

    # LLM-FRIENDLY: Simple category
    allergy_type: str | None = Field(
        default=None,
        description="Simple category of allergy",
        examples=["Food allergy", "Drug allergy", "Environmental allergy", "Unknown"],
    )

    criticality: AllergyIntoleranceCriticality | None = Field(
        default=None,
        description="Estimate of the potential clinical harm, or seriousness, of the reaction",
    )

    # Code for the allergy/intolerance - required in US Core
    code: dict[str, Any] = Field(
        description="Code that identifies the allergy or intolerance"
    )

    # LLM-FRIENDLY: Simple allergen name
    allergen_name: str | None = Field(
        default=None,
        description="Simple name of the allergen or substance",
        examples=[
            "Penicillin",
            "Peanuts",
            "Shellfish",
            "Latex",
            "Pollen",
            "Dust mites",
        ],
    )

    allergen_description: str | None = Field(
        default=None, description="Detailed description of the allergen"
    )

    # Patient reference - required
    patient: str = Field(description="Who the sensitivity is for (Patient reference)")

    # Encounter context
    encounter: str | None = Field(
        default=None,
        description="Encounter when the allergy or intolerance was asserted",
    )

    # Timing
    onset_datetime: datetime | None = Field(
        default=None, description="When allergy or intolerance was identified"
    )

    onset_age: dict[str, Any] | None = Field(
        default=None, description="Age when allergy or intolerance was identified"
    )

    onset_period: dict[str, Any] | None = Field(
        default=None, description="Period when allergy or intolerance was identified"
    )

    onset_range: dict[str, Any] | None = Field(
        default=None,
        description="Range of time when allergy or intolerance was identified",
    )

    onset_string: str | None = Field(
        default=None, description="Simple string describing when the allergy started"
    )

    # LLM-FRIENDLY: Simple onset
    started_when: str | None = Field(
        default=None,
        description="When the allergy or intolerance started",
        examples=["Childhood", "2 years ago", "After surgery", "Unknown", "Birth"],
    )

    recorded_date: datetime | None = Field(
        default=None,
        description="Date first version of the resource instance was recorded",
    )

    # Who recorded/asserted
    recorder: str | None = Field(
        default=None,
        description="Individual who recorded the record and takes responsibility for its content",
    )

    asserter: str | None = Field(
        default=None, description="Source of the information about the allergy"
    )

    # LLM-FRIENDLY: Simple source
    reported_by: str | None = Field(
        default=None,
        description="Who reported this allergy",
        examples=["Patient", "Family member", "Previous doctor", "Hospital records"],
    )

    last_occurrence: datetime | None = Field(
        default=None, description="Date(/time) of last known occurrence of a reaction"
    )

    note: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Additional narrative about the allergy or intolerance",
    )

    # LLM-FRIENDLY: Simple notes
    notes: str | None = Field(
        default=None, description="Additional notes about the allergy or intolerance"
    )

    # Reactions
    reaction: list[AllergyIntoleranceReaction] = Field(
        default_factory=list,
        description="Adverse reaction events linked to exposure to substance",
    )

    # HACS-specific enhancements
    severity_assessment: str | None = Field(
        default=None,
        description="Overall severity assessment",
        examples=["Mild", "Moderate", "Severe", "Life-threatening"],
    )

    management_plan: str | None = Field(
        default=None, description="How to manage this allergy or intolerance"
    )

    emergency_action: str | None = Field(
        default=None, description="Emergency actions to take if exposed"
    )

    carries_epinephrine: bool | None = Field(
        default=None, description="Whether patient carries epinephrine auto-injector"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "id": "allergy-penicillin-001",
                    "resource_type": "AllergyIntolerance",
                    "clinical_status": "active",
                    "verification_status": "confirmed",
                    "type": "allergy",
                    "category": ["medication"],
                    "criticality": "high",
                    "allergen_name": "Penicillin",
                    "allergy_type": "Drug allergy",
                    "patient": "Patient/patient-123",
                    "started_when": "Childhood",
                    "reported_by": "Patient",
                    "severity_assessment": "Severe",
                    "symptoms": ["Hives", "Swelling", "Difficulty breathing"],
                    "notes": "Patient reports severe reaction with hives and breathing difficulty when taking penicillin",
                    "emergency_action": "Administer epinephrine, call 911",
                    "carries_epinephrine": True,
                    "code": {
                        "coding": [
                            {
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": "7980",
                                "display": "Penicillin",
                            }
                        ],
                        "text": "Penicillin",
                    },
                },
                {
                    "id": "allergy-peanuts-002",
                    "resource_type": "AllergyIntolerance",
                    "clinical_status": "active",
                    "verification_status": "confirmed",
                    "type": "allergy",
                    "category": ["food"],
                    "criticality": "high",
                    "allergen_name": "Peanuts",
                    "allergy_type": "Food allergy",
                    "patient": "Patient/patient-456",
                    "started_when": "Age 3",
                    "reported_by": "Family member",
                    "severity_assessment": "Life-threatening",
                    "symptoms": ["Anaphylaxis", "Hives", "Vomiting"],
                    "notes": "Severe peanut allergy diagnosed in childhood. Has had multiple emergency room visits.",
                    "emergency_action": "Use EpiPen immediately, call 911",
                    "carries_epinephrine": True,
                    "code": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "256349002",
                                "display": "Allergy to peanut",
                            }
                        ],
                        "text": "Peanut allergy",
                    },
                },
            ]
        }
