"""
AllergyIntolerance model for HACS.

This module provides a FHIR R4-compliant AllergyIntolerance resource model,
which is critical for patient safety in healthcare applications.

FHIR R4 Specification:
https://hl7.org/fhir/R4/allergyintolerance.html
"""

from datetime import datetime
from typing import Literal

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
        default="AllergyIntoleranceReaction",
        description="Resource type identifier"
    )

    # Substance that caused the reaction
    substance: CodeableConcept | None = Field(
        None,
        description="Specific substance considered to be responsible for event"
    )

    # Clinical manifestation of the reaction
    manifestation: list[CodeableConcept] = Field(
        default_factory=list,
        description="Clinical symptoms/signs associated with the event"
    )

    # Description of the reaction
    description: str | None = Field(
        None,
        description="Description of the adverse reaction"
    )

    # When the reaction occurred
    onset: TimestampStr | None = Field(
        None,
        description="Date(/time) when manifestations showed"
    )

    # Severity of the reaction
    severity: AllergyReactionSeverity | None = Field(
        None,
        description="Clinical assessment of the severity of the reaction event"
    )

    # Route of exposure to the substance
    exposure_route: CodeableConcept | None = Field(
        None,
        description="How the subject was exposed to the substance"
    )

    # Additional text note about the reaction
    note: str | None = Field(
        None,
        description="Text about event not captured in other fields"
    )


class AllergyIntolerance(DomainResource):
    """
    AllergyIntolerance resource for patient safety.

    Risk of harmful or undesirable, physiological response which is unique
    to an individual and associated with exposure to a substance.

    This is a SAFETY-CRITICAL resource in healthcare systems.
    """

    resource_type: Literal["AllergyIntolerance"] = Field(
        default="AllergyIntolerance",
        description="Resource type identifier"
    )

    # Business identifiers
    identifier: list[str] = Field(
        default_factory=list,
        description="External identifiers for this item"
    )

    # Clinical status - REQUIRED for safety
    clinical_status: AllergyIntoleranceStatus = Field(
        description="Active | inactive | resolved"
    )

    # Verification status
    verification_status: str | None = Field(
        None,
        description="Assertion about certainty associated with the propensity"
    )

    # Type of allergy/intolerance
    type: AllergyIntoleranceType | None = Field(
        None,
        description="Allergy or Intolerance (generally food, medication, environment, biologic)"
    )

    # Category of allergy/intolerance
    category: list[AllergyIntoleranceType] = Field(
        default_factory=list,
        description="Food | medication | environment | biologic"
    )

    # Estimate of potential clinical harm
    criticality: AllergyCriticality | None = Field(
        None,
        description="Estimate of potential clinical harm"
    )

    # Code for allergy or intolerance
    code: CodeableConcept | None = Field(
        None,
        description="Code that identifies the allergy or intolerance"
    )

    # Patient reference - REQUIRED for safety
    patient: ResourceReference = Field(
        description="Who the allergy or intolerance is for"
    )

    # Encounter when the allergy was first noted
    encounter: ResourceReference | None = Field(
        None,
        description="Encounter when the allergy or intolerance was asserted"
    )

    # When allergy or intolerance was identified
    onset_datetime: TimestampStr | None = Field(
        None,
        description="When allergy or intolerance was identified"
    )

    # Date(/time) of last known occurrence of a reaction
    last_occurrence: TimestampStr | None = Field(
        None,
        description="Date(/time) of last known occurrence of a reaction"
    )

    # Source of the information about the allergy
    recorder: ResourceReference | None = Field(
        None,
        description="Individual who recorded the record and takes responsibility"
    )

    # Source of the information about allergy
    asserter: ResourceReference | None = Field(
        None,
        description="Source of the information about the allergy"
    )

    # Adverse reaction details
    reaction: list[AllergyIntoleranceReaction] = Field(
        default_factory=list,
        description="Adverse reaction events linked to exposure to substance"
    )

    # Additional text note
    note: str | None = Field(
        None,
        description="Additional text not captured in other fields"
    )

    @field_validator('patient')
    @classmethod
    def validate_patient_reference(cls, v):
        """Validate patient reference format."""
        if v and not v.startswith(('Patient/', 'urn:uuid:')):
            raise ValueError("Patient reference must start with 'Patient/' or 'urn:uuid:'")
        return v

    @field_validator('clinical_status')
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
        if self.code and hasattr(self.code, 'text') and self.code.text:
            return self.code.text
        elif self.code and hasattr(self.code, 'coding') and self.code.coding:
            # Try to get display from first coding
            first_coding = self.code.coding[0] if self.code.coding else None
            if first_coding and hasattr(first_coding, 'display'):
                return first_coding.display
        return f"Allergy/Intolerance {self.id or 'Unknown'}"

    def add_reaction(
        self,
        manifestation: list[CodeableConcept],
        severity: AllergyReactionSeverity | None = None,
        substance: CodeableConcept | None = None,
        description: str | None = None
    ) -> AllergyIntoleranceReaction:
        """Add a new reaction to this allergy/intolerance."""
        reaction = AllergyIntoleranceReaction(
            manifestation=manifestation,
            severity=severity,
            substance=substance,
            description=description,
            onset=datetime.now().isoformat()
        )
        self.reaction.append(reaction)
        return reaction


# Convenience functions for common allergy types

def create_food_allergy(
    patient_ref: ResourceReference,
    allergen: CodeableConcept,
    clinical_status: AllergyIntoleranceStatus = AllergyIntoleranceStatus.ACTIVE,
    criticality: AllergyCriticality = AllergyCriticality.HIGH,
    **kwargs
) -> AllergyIntolerance:
    """Create a food allergy/intolerance."""
    return AllergyIntolerance(
        patient=patient_ref,
        clinical_status=clinical_status,
        type=AllergyIntoleranceType.FOOD,
        category=[AllergyIntoleranceType.FOOD],
        code=allergen,
        criticality=criticality,
        **kwargs
    )


def create_medication_allergy(
    patient_ref: ResourceReference,
    medication: CodeableConcept,
    clinical_status: AllergyIntoleranceStatus = AllergyIntoleranceStatus.ACTIVE,
    criticality: AllergyCriticality = AllergyCriticality.HIGH,
    **kwargs
) -> AllergyIntolerance:
    """Create a medication allergy/intolerance."""
    return AllergyIntolerance(
        patient=patient_ref,
        clinical_status=clinical_status,
        type=AllergyIntoleranceType.MEDICATION,
        category=[AllergyIntoleranceType.MEDICATION],
        code=medication,
        criticality=criticality,
        **kwargs
    )


def create_environmental_allergy(
    patient_ref: ResourceReference,
    allergen: CodeableConcept,
    clinical_status: AllergyIntoleranceStatus = AllergyIntoleranceStatus.ACTIVE,
    criticality: AllergyCriticality = AllergyCriticality.LOW,
    **kwargs
) -> AllergyIntolerance:
    """Create an environmental allergy/intolerance."""
    return AllergyIntolerance(
        patient=patient_ref,
        clinical_status=clinical_status,
        type=AllergyIntoleranceType.ENVIRONMENT,
        category=[AllergyIntoleranceType.ENVIRONMENT],
        code=allergen,
        criticality=criticality,
        **kwargs
    )