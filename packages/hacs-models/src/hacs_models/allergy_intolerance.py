"""
AllergyIntolerance model for HACS.

This module provides a FHIR R4-compliant AllergyIntolerance resource model,
which is critical for patient safety in healthcare applications.

FHIR R4 Specification:
https://hl7.org/fhir/R4/allergyintolerance.html
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import Field, field_validator

from .base_resource import DomainResource
from .observation import CodeableConcept
from .types import (
    AllergyCriticality,
    AllergyIntoleranceStatus,
    AllergyIntoleranceType,
    AllergyReactionSeverity,
    ResourceReference,
    TimestampStr,
)


class AllergyIntoleranceReaction(DomainResource):
    """
    Allergy intolerance reaction details.

    Represents an adverse reaction associated with the allergy/intolerance.
    """

    resource_type: Literal["AllergyIntoleranceReaction"] = Field(
        default="AllergyIntoleranceReaction", description="Resource type identifier"
    )

    # Substance that caused the reaction
    substance: CodeableConcept | None = Field(
        None, description="Specific substance considered to be responsible for event"
    )

    # Clinical manifestation of the reaction
    manifestation: list[CodeableConcept] = Field(
        default_factory=list, description="Clinical symptoms/signs associated with the event"
    )

    # Description of the reaction
    description: str | None = Field(None, description="Description of the adverse reaction")

    # When the reaction occurred
    onset: TimestampStr | None = Field(None, description="Date(/time) when manifestations showed")

    # Severity of the reaction
    severity: AllergyReactionSeverity | None = Field(
        None, description="Clinical assessment of the severity of the reaction event"
    )

    # Route of exposure to the substance
    exposure_route: CodeableConcept | None = Field(
        None, description="How the subject was exposed to the substance"
    )

    # Additional text note about the reaction
    note: str | None = Field(None, description="Text about event not captured in other fields")


class AllergyIntolerance(DomainResource):
    """
    AllergyIntolerance resource for patient safety.

    Risk of harmful or undesirable, physiological response which is unique
    to an individual and associated with exposure to a substance.

    This is a SAFETY-CRITICAL resource in healthcare systems.
    """

    resource_type: Literal["AllergyIntolerance"] = Field(
        default="AllergyIntolerance", description="Resource type identifier"
    )

    # Business identifiers
    identifier: list[str] = Field(
        default_factory=list, description="External identifiers for this item"
    )

    # Clinical status - REQUIRED for safety
    clinical_status: AllergyIntoleranceStatus = Field(description="Active | inactive | resolved")

    # Verification status
    verification_status: str | None = Field(
        None, description="Assertion about certainty associated with the propensity"
    )

    # Type of allergy/intolerance
    type: AllergyIntoleranceType | None = Field(
        None,
        description="Allergy or Intolerance (generally food, medication, environment, biologic)",
    )

    # Category of allergy/intolerance
    category: list[AllergyIntoleranceType] = Field(
        default_factory=list, description="Food | medication | environment | biologic"
    )

    # Estimate of potential clinical harm
    criticality: AllergyCriticality | None = Field(
        None, description="Estimate of potential clinical harm"
    )

    # Code for allergy or intolerance
    code: CodeableConcept | None = Field(
        None, description="Code that identifies the allergy or intolerance"
    )

    # Patient reference - REQUIRED for safety
    patient: ResourceReference = Field(description="Who the allergy or intolerance is for")

    # Encounter when the allergy was first noted
    encounter: ResourceReference | None = Field(
        None, description="Encounter when the allergy or intolerance was asserted"
    )

    # When allergy or intolerance was identified
    onset_datetime: TimestampStr | None = Field(
        None, description="When allergy or intolerance was identified"
    )

    # Date(/time) of last known occurrence of a reaction
    last_occurrence: TimestampStr | None = Field(
        None, description="Date(/time) of last known occurrence of a reaction"
    )

    # Source of the information about the allergy
    recorder: ResourceReference | None = Field(
        None, description="Individual who recorded the record and takes responsibility"
    )

    # Source of the information about allergy
    asserter: ResourceReference | None = Field(
        None, description="Source of the information about the allergy"
    )

    # Adverse reaction details
    reaction: list[AllergyIntoleranceReaction] = Field(
        default_factory=list, description="Adverse reaction events linked to exposure to substance"
    )

    # Additional text note
    note: str | None = Field(None, description="Additional text not captured in other fields")

    @field_validator("patient")
    @classmethod
    def validate_patient_reference(cls, v):
        """Validate patient reference format."""
        if v and not v.startswith(("Patient/", "urn:uuid:")):
            raise ValueError("Patient reference must start with 'Patient/' or 'urn:uuid:'")
        return v

    @field_validator("clinical_status")
    @classmethod
    def validate_clinical_status_required(cls, v):
        """Ensure clinical status is provided for safety."""
        if not v:
            raise ValueError("Clinical status is required for AllergyIntolerance (patient safety)")
        return v

    @property
    def is_active(self) -> bool:
        """Check if allergy is currently active."""
        return self.clinical_status == AllergyIntoleranceStatus.ACTIVE

    @property
    def is_high_risk(self) -> bool:
        """Check if allergy is high risk."""
        return self.criticality == AllergyCriticality.HIGH

    @property
    def has_severe_reactions(self) -> bool:
        """Check if any recorded reactions were severe."""
        return any(
            reaction.severity == AllergyReactionSeverity.SEVERE
            for reaction in self.reaction
            if reaction.severity
        )

    def get_display_name(self) -> str:
        """Get a human-readable display name for the allergy."""
        if self.code and hasattr(self.code, "text") and self.code.text:
            return self.code.text
        elif self.code and hasattr(self.code, "coding") and self.code.coding:
            # Try to get display from first coding
            first_coding = self.code.coding[0] if self.code.coding else None
            if first_coding and hasattr(first_coding, "display"):
                return first_coding.display
        return f"Allergy/Intolerance {self.id or 'Unknown'}"

    def add_reaction(
        self,
        manifestation: list[CodeableConcept],
        severity: AllergyReactionSeverity | None = None,
        substance: CodeableConcept | None = None,
        description: str | None = None,
    ) -> AllergyIntoleranceReaction:
        """Add a new reaction to this allergy/intolerance."""
        reaction = AllergyIntoleranceReaction(
            manifestation=manifestation,
            severity=severity,
            substance=substance,
            description=description,
            onset=datetime.now().isoformat(),
        )
        self.reaction.append(reaction)
        return reaction

    # --- LLM-friendly extractable facade overrides ---
    @classmethod
    def get_extractable_fields(cls) -> list[str]:  # type: ignore[override]
        """Return fields that should be extracted by LLMs - SAFETY-FOCUSED."""
        return [
            "clinical_status",     # Required for safety
            "code",               # What the allergy is to
            "category",           # Type classification
            "criticality",        # Risk level
            "patient",            # Who has the allergy
            "type",               # Allergy vs intolerance
            "reaction",           # Previous reactions
            "onset_datetime",     # When identified
            "last_occurrence",    # Last reaction
            "note",               # Additional context
        ]

    @classmethod
    def get_required_extractables(cls) -> list[str]:
        """Fields that MUST be provided for patient safety."""
        return ["clinical_status", "code", "patient"]

    @classmethod
    def get_canonical_defaults(cls) -> dict[str, Any]:
        """Default values for system/required fields during extraction."""
        return {
            "clinical_status": "active",  # Safe default for extraction
            "code": {"text": ""},  # Minimal code structure - must be filled by LLM
            "patient": "Patient/UNKNOWN",  # Safe placeholder reference
        }

    @classmethod
    def coerce_extractable(cls, payload: dict[str, Any], relax: bool = True) -> dict[str, Any]:
        """Coerce extractable payload to proper types with safety validation."""
        coerced = payload.copy()

        # Coerce code to CodeableConcept if it's a string
        if "code" in coerced and isinstance(coerced["code"], str):
            coerced["code"] = {"text": coerced["code"]}

        # Ensure category is a list
        if "category" in coerced and isinstance(coerced["category"], str):
            coerced["category"] = [coerced["category"]]

        # Ensure patient reference format
        if "patient" in coerced and isinstance(coerced["patient"], str):
            if not coerced["patient"].startswith(("Patient/", "urn:uuid:")):
                coerced["patient"] = f"Patient/{coerced['patient']}"

        return coerced

    @classmethod
    def llm_hints(cls) -> list[str]:  # type: ignore[override]
        """Provide LLM-specific extraction hints for SAFETY-CRITICAL allergies."""
        return [
            "SAFETY CRITICAL: Always extract allergy/intolerance information when mentioned",
            "Clinical status REQUIRED: active, inactive, or resolved",
            "Include specific allergen name (medication, food, environmental)",
            "Capture reaction severity: mild, moderate, severe",
            "Note category: medication, food, environment, biologic",
            "Include criticality: low, high, unable-to-assess",
            "Document any previous reactions or symptoms",
            "Extract onset timing when mentioned"
        ]

    @classmethod
    def get_facades(cls) -> dict[str, "FacadeSpec"]:
        """Return available extraction facades for AllergyIntolerance."""
        from .base_resource import FacadeSpec
        
        return {
            "critical": FacadeSpec(
                fields=["clinical_status", "code", "patient", "criticality", "category"],
                required_fields=["clinical_status", "code", "patient"],
                field_examples={
                    "clinical_status": "active",
                    "code": {"text": "penicillin"},
                    "patient": "Patient/patient-123",
                    "criticality": "high",
                    "category": ["medication"]
                },
                field_types={
                    "clinical_status": "AllergyIntoleranceStatus",
                    "code": "CodeableConcept | None",
                    "patient": "ResourceReference",
                    "criticality": "AllergyCriticality | None",
                    "category": "list[AllergyIntoleranceType]"
                },
                description="SAFETY-CRITICAL: Essential allergy information for patient safety",
                llm_guidance="ALWAYS use this facade when any allergy or intolerance is mentioned. This is safety-critical information that must be captured accurately.",
                conversational_prompts=[
                    "What allergies does the patient have?",
                    "Are there any drug allergies?",
                    "What should we avoid giving this patient?"
                ]
            ),
            
            "reactions": FacadeSpec(
                fields=["clinical_status", "code", "patient", "reaction", "last_occurrence"],
                required_fields=["clinical_status", "code", "patient"],
                field_examples={
                    "clinical_status": "active",
                    "code": {"text": "shellfish"},
                    "patient": "Patient/patient-456",
                    "reaction": [{"manifestation": [{"text": "hives"}], "severity": "moderate"}],
                    "last_occurrence": "2024-06-15"
                },
                field_types={
                    "clinical_status": "AllergyIntoleranceStatus",
                    "code": "CodeableConcept | None",
                    "patient": "ResourceReference",
                    "reaction": "list[AllergyIntoleranceReaction]",
                    "last_occurrence": "TimestampStr | None"
                },
                description="Allergy reaction history and manifestations",
                llm_guidance="Use when specific reaction details, symptoms, or reaction history are documented. Include severity and manifestations.",
                conversational_prompts=[
                    "What happens when the patient is exposed to this allergen?",
                    "What were the symptoms of the allergic reaction?",
                    "When was the last allergic reaction?"
                ]
            ),
            
            "medication": FacadeSpec(
                fields=["clinical_status", "code", "patient", "category", "criticality", "reaction", "note"],
                required_fields=["clinical_status", "code", "patient"],
                field_examples={
                    "clinical_status": "active",
                    "code": {"text": "aspirin"},
                    "patient": "Patient/patient-789",
                    "category": ["medication"],
                    "criticality": "high",
                    "reaction": [{"manifestation": [{"text": "anaphylaxis"}], "severity": "severe"}],
                    "note": "Severe reaction requiring epinephrine"
                },
                field_types={
                    "clinical_status": "AllergyIntoleranceStatus",
                    "code": "CodeableConcept | None",
                    "patient": "ResourceReference",
                    "category": "list[AllergyIntoleranceType]",
                    "criticality": "AllergyCriticality | None",
                    "reaction": "list[AllergyIntoleranceReaction]",
                    "note": "str | None"
                },
                description="Drug allergies and medication intolerances",
                llm_guidance="CRITICAL for medication safety. Extract all drug allergies, intolerances, and adverse drug reactions mentioned.",
                conversational_prompts=[
                    "What medications is the patient allergic to?",
                    "Are there any drug allergies or adverse reactions?",
                    "What medications should be avoided?"
                ]
            ),
            
            "food": FacadeSpec(
                fields=["clinical_status", "code", "patient", "category", "type", "reaction", "onset_datetime"],
                required_fields=["clinical_status", "code", "patient"],
                field_examples={
                    "clinical_status": "active",
                    "code": {"text": "peanuts"},
                    "patient": "Patient/patient-321",
                    "category": ["food"],
                    "type": "allergy",
                    "reaction": [{"manifestation": [{"text": "swelling"}, {"text": "difficulty breathing"}]}],
                    "onset_datetime": "2020-03-15"
                },
                field_types={
                    "clinical_status": "AllergyIntoleranceStatus",
                    "code": "CodeableConcept | None",
                    "patient": "ResourceReference",
                    "category": "list[AllergyIntoleranceType]",
                    "type": "AllergyIntoleranceType | None",
                    "reaction": "list[AllergyIntoleranceReaction]",
                    "onset_datetime": "TimestampStr | None"
                },
                description="Food allergies and dietary restrictions",
                llm_guidance="Extract food allergies and intolerances that affect dietary planning and food service.",
                conversational_prompts=[
                    "What food allergies does the patient have?",
                    "Are there any dietary restrictions?",
                    "What foods should be avoided?"
                ]
            ),
            
            "environmental": FacadeSpec(
                fields=["clinical_status", "code", "patient", "category", "type", "onset_datetime", "reaction"],
                required_fields=["clinical_status", "code", "patient"],
                field_examples={
                    "clinical_status": "active",
                    "code": {"text": "pollen"},
                    "patient": "Patient/patient-654",
                    "category": ["environment"],
                    "type": "allergy",
                    "onset_datetime": "2023-04-01",
                    "reaction": [{"manifestation": [{"text": "sneezing"}, {"text": "runny nose"}], "severity": "mild"}]
                },
                field_types={
                    "clinical_status": "AllergyIntoleranceStatus",
                    "code": "CodeableConcept | None",
                    "patient": "ResourceReference",
                    "category": "list[AllergyIntoleranceType]",
                    "type": "AllergyIntoleranceType | None",
                    "onset_datetime": "TimestampStr | None",
                    "reaction": "list[AllergyIntoleranceReaction]"
                },
                description="Environmental allergies and sensitivities",
                llm_guidance="Extract environmental allergies like pollen, dust, pet dander, seasonal allergies, and environmental triggers.",
                conversational_prompts=[
                    "Does the patient have any environmental allergies?",
                    "Are there seasonal allergies or sensitivities?",
                    "What environmental triggers affect the patient?"
                ]
            ),
            
            "complete": FacadeSpec(
                fields=["clinical_status", "code", "patient", "category", "type", "criticality", "reaction", "onset_datetime", "last_occurrence", "recorder", "note"],
                required_fields=["clinical_status", "code", "patient"],
                field_examples={
                    "clinical_status": "active",
                    "code": {"text": "latex"},
                    "patient": "Patient/patient-654",
                    "category": ["environment"],
                    "type": "allergy",
                    "criticality": "high",
                    "reaction": [{"manifestation": [{"text": "contact dermatitis"}], "severity": "moderate"}],
                    "onset_datetime": "2019-08-20",
                    "last_occurrence": "2024-01-10",
                    "recorder": "Practitioner/dr-smith",
                    "note": "Occupational exposure risk"
                },
                field_types={
                    "clinical_status": "AllergyIntoleranceStatus",
                    "code": "CodeableConcept | None",
                    "patient": "ResourceReference",
                    "category": "list[AllergyIntoleranceType]",
                    "type": "AllergyIntoleranceType | None",
                    "criticality": "AllergyCriticality | None",
                    "reaction": "list[AllergyIntoleranceReaction]",
                    "onset_datetime": "TimestampStr | None",
                    "last_occurrence": "TimestampStr | None",
                    "recorder": "ResourceReference | None",
                    "note": "str | None"
                },
                description="Comprehensive allergy documentation with full clinical details",
                llm_guidance="Use for complete allergy documentation when extensive details about timing, reactions, and clinical context are available.",
                conversational_prompts=[
                    "Can you document the complete allergy history?",
                    "What are all the details about this patient's allergies?",
                    "Provide comprehensive allergy information for the medical record"
                ]
            )
        }


# Convenience functions for common allergy types


def create_food_allergy(
    patient_ref: ResourceReference,
    allergen: CodeableConcept,
    clinical_status: AllergyIntoleranceStatus = AllergyIntoleranceStatus.ACTIVE,
    criticality: AllergyCriticality = AllergyCriticality.HIGH,
    **kwargs,
) -> AllergyIntolerance:
    """Create a food allergy/intolerance."""
    return AllergyIntolerance(
        patient=patient_ref,
        clinical_status=clinical_status,
        type=AllergyIntoleranceType.FOOD,
        category=[AllergyIntoleranceType.FOOD],
        code=allergen,
        criticality=criticality,
        **kwargs,
    )


def create_medication_allergy(
    patient_ref: ResourceReference,
    medication: CodeableConcept,
    clinical_status: AllergyIntoleranceStatus = AllergyIntoleranceStatus.ACTIVE,
    criticality: AllergyCriticality = AllergyCriticality.HIGH,
    **kwargs,
) -> AllergyIntolerance:
    """Create a medication allergy/intolerance."""
    return AllergyIntolerance(
        patient=patient_ref,
        clinical_status=clinical_status,
        type=AllergyIntoleranceType.MEDICATION,
        category=[AllergyIntoleranceType.MEDICATION],
        code=medication,
        criticality=criticality,
        **kwargs,
    )


def create_environmental_allergy(
    patient_ref: ResourceReference,
    allergen: CodeableConcept,
    clinical_status: AllergyIntoleranceStatus = AllergyIntoleranceStatus.ACTIVE,
    criticality: AllergyCriticality = AllergyCriticality.LOW,
    **kwargs,
) -> AllergyIntolerance:
    """Create an environmental allergy/intolerance."""
    return AllergyIntolerance(
        patient=patient_ref,
        clinical_status=clinical_status,
        type=AllergyIntoleranceType.ENVIRONMENT,
        category=[AllergyIntoleranceType.ENVIRONMENT],
        code=allergen,
        criticality=criticality,
        **kwargs,
    )
