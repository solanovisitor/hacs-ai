"""
MedicationRequest model for HACS.

This module provides a comprehensive, FHIR-compliant MedicationRequest resource model
for prescription and medication ordering workflows. Essential for clinical decision
support and medication management.

FHIR R4 Specification:
https://hl7.org/fhir/R4/medicationrequest.html
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import Field, field_validator

from .base_resource import DomainResource
from .observation import CodeableConcept
from .types import (
    MedicationRequestIntent,
    MedicationRequestPriority,
    MedicationRequestStatus,
    ResourceReference,
    TimestampStr,
)


class Dosage(DomainResource):
    """
    Dosage instructions for medication administration.

    Provides detailed information about how a medication should be taken,
    including dose, frequency, timing, and administration method.
    """

    resource_type: Literal["Dosage"] = Field(default="Dosage")

    # Sequence of dosage instruction
    sequence: int | None = Field(
        default=None, description="Order of administration instructions", examples=[1, 2, 3], ge=1
    )

    # Free text dosage instruction
    text: str | None = Field(
        default=None,
        description="Free text dosage instruction (e.g., 'Take with food')",
        examples=["Take one tablet twice daily with meals", "Apply thin layer to affected area"],
        max_length=500,
    )

    # Additional instruction (e.g., "with meals")
    additional_instruction: list[CodeableConcept] = Field(
        default_factory=list, description="Supplemental instruction - e.g., 'with meals'"
    )

    # Patient or consumer oriented instructions
    patient_instruction: str | None = Field(
        default=None,
        description="Patient instructions for the medication",
        examples=["Take with plenty of water", "Do not drive while taking this medication"],
        max_length=1000,
    )

    # When medication should be administered
    timing: dict[str, Any] | None = Field(
        default=None,
        description="When medication should be administered",
        examples=[
            {
                "repeat": {
                    "frequency": 2,
                    "period": 1,
                    "periodUnit": "d",  # per day
                }
            }
        ],
    )

    # Body site to administer
    site: CodeableConcept | None = Field(
        default=None, description="Body site to administer medication"
    )

    # How drug should enter body
    route: CodeableConcept | None = Field(
        default=None, description="How drug should enter body (oral, injection, topical, etc.)"
    )

    # Technique for administering medication
    method: CodeableConcept | None = Field(
        default=None, description="Technique for administering medication"
    )

    # Amount of medication per dose
    dose_and_rate: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Amount of medication administered",
        examples=[
            [
                {
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/dose-rate-type",
                                "code": "ordered",
                                "display": "Ordered",
                            }
                        ]
                    },
                    "doseQuantity": {
                        "value": 500,
                        "unit": "mg",
                        "system": "http://unitsofmeasure.org",
                    },
                }
            ]
        ],
    )

    # Upper limit on medication per unit of time
    max_dose_per_period: dict[str, Any] | None = Field(
        default=None, description="Upper limit on medication per unit of time"
    )

    # Upper limit on medication per administration
    max_dose_per_administration: dict[str, Any] | None = Field(
        default=None, description="Upper limit on medication per administration"
    )

    # Upper limit on medication per lifetime of patient
    max_dose_per_lifetime: dict[str, Any] | None = Field(
        default=None, description="Upper limit on medication per lifetime of patient"
    )


class MedicationRequestSubstitution(DomainResource):
    """Substitution details for the medication request."""

    resource_type: Literal["MedicationRequestSubstitution"] = Field(
        default="MedicationRequestSubstitution"
    )

    # Whether substitution is allowed
    allowed_boolean: bool | None = Field(
        default=None, description="Whether substitution is allowed or not"
    )

    # Whether substitution is allowed (coded)
    allowed_codeable_concept: CodeableConcept | None = Field(
        default=None, description="Whether substitution is allowed (coded)"
    )

    # Why substitution is/is not allowed
    reason: CodeableConcept | None = Field(
        default=None, description="Why should (not) substitution be made"
    )


class MedicationRequest(DomainResource):
    """
    MedicationRequest resource for prescription and medication ordering.

    An order or request for both supply of the medication and the instructions
    for administration of the medication to a patient. Used for prescriptions,
    medication orders, and other medication-related requests.

    This is a SAFETY-CRITICAL resource in healthcare systems for medication management.
    """

    resource_type: Literal["MedicationRequest"] = Field(default="MedicationRequest")

    # Canonical defaults for extraction and fallback
    _canonical_defaults: dict[str, Any] = {
        "status": MedicationRequestStatus.ACTIVE,
        "intent": MedicationRequestIntent.ORDER,
        "subject": "Patient/placeholder",
        "medication_codeable_concept": {"text": ""},
        "dosage_instruction": [{"text": ""}],
    }

    # Business identifiers
    identifier: list[str] = Field(
        default_factory=list,
        description="External identifiers for this medication request",
        examples=[["urn:oid:1.2.3.4.5.6.7.8.9|12345", "prescription-number-67890"]],
    )

    # Status of the medication request - REQUIRED for safety
    status: MedicationRequestStatus = Field(
        description="Status of the medication request (active, completed, cancelled, etc.)"
    )

    # Whether request is a proposal, plan, or original order
    intent: MedicationRequestIntent = Field(
        description="Intent of the medication request (proposal, plan, order, etc.)"
    )

    # Type of medication usage
    category: list[CodeableConcept] = Field(
        default_factory=list,
        description="Type of medication usage (inpatient, outpatient, community, etc.)",
        examples=[
            [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/medicationrequest-category",
                            "code": "outpatient",
                            "display": "Outpatient",
                        }
                    ],
                    "text": "Outpatient",
                }
            ]
        ],
    )

    # Routine, urgent, ASAP, etc.
    priority: MedicationRequestPriority | None = Field(
        default=None, description="Routine | urgent | asap | stat"
    )

    # True if request is prohibiting action
    do_not_perform: bool | None = Field(
        default=None, description="True if medication must not be performed"
    )

    # Medication to be taken - REQUIRED
    medication_codeable_concept: CodeableConcept | None = Field(
        default=None, description="Medication to be taken (coded)"
    )

    medication_reference: ResourceReference | None = Field(
        default=None, description="Reference to medication resource"
    )

    # Who the medication is for - REQUIRED for safety
    subject: ResourceReference = Field(description="Who or group medication request is for")

    # Encounter created as part of
    encounter: ResourceReference | None = Field(
        default=None, description="Encounter created as part of"
    )

    # When request was initially authored
    authored_on: TimestampStr | None = Field(
        default=None, description="When request was initially authored"
    )

    # Who/what requested the medication
    requester: ResourceReference | None = Field(
        default=None, description="Who/what requested the medication"
    )

    # Intended performer of administration
    performer: ResourceReference | None = Field(
        default=None, description="Intended performer of administration"
    )

    # Reason for request
    reason_code: list[CodeableConcept] = Field(
        default_factory=list, description="Reason or indication for ordering the medication"
    )

    # Condition or observation that supports the prescription
    reason_reference: list[ResourceReference] = Field(
        default_factory=list,
        description="Condition or observation that supports why the medication was ordered",
    )

    # Information about the prescription
    note: list[str] = Field(
        default_factory=list, description="Information about the prescription", max_length=10
    )

    # How medication should be taken
    dosage_instruction: list[Dosage] = Field(
        default_factory=list, description="How medication should be taken"
    )

    # Medication supply authorization
    dispense_request: dict[str, Any] | None = Field(
        default=None,
        description="Medication supply authorization",
        examples=[
            {
                "initial_fill": {
                    "quantity": {"value": 30, "unit": "tablets"},
                    "duration": {"value": 30, "unit": "days"},
                },
                "dispense_interval": {"value": 30, "unit": "days"},
                "validity_period": {"start": "2024-01-01T00:00:00Z", "end": "2024-12-31T23:59:59Z"},
                "number_of_repeats_allowed": 5,
                "quantity": {"value": 100, "unit": "tablets"},
                "expected_supply_duration": {"value": 30, "unit": "days"},
                "performer": "Organization/pharmacy-123",
            }
        ],
    )

    # Any restrictions on medication substitution
    substitution: MedicationRequestSubstitution | None = Field(
        default=None, description="Any restrictions on medication substitution"
    )

    @field_validator("status")
    @classmethod
    def validate_status_required(cls, v):
        """Ensure status is provided for safety."""
        if not v:
            raise ValueError("Status is required for MedicationRequest (patient safety)")
        return v

    @field_validator("intent")
    @classmethod
    def validate_intent_required(cls, v):
        """Ensure intent is provided."""
        if not v:
            raise ValueError("Intent is required for MedicationRequest")
        return v

    @field_validator("subject")
    @classmethod
    def validate_subject_required(cls, v):
        """Ensure subject is provided for safety."""
        if not v:
            raise ValueError("Subject is required for MedicationRequest (patient safety)")
        return v

    @property
    def is_active(self) -> bool:
        """Check if medication request is active."""
        return self.status == MedicationRequestStatus.ACTIVE

    @property
    def is_completed(self) -> bool:
        """Check if medication request is completed."""
        return self.status == MedicationRequestStatus.COMPLETED

    @property
    def is_cancelled(self) -> bool:
        """Check if medication request is cancelled."""
        return self.status == MedicationRequestStatus.CANCELLED

    def get_medication_display(self) -> str:
        """Get display name for the medication."""
        if self.medication_codeable_concept:
            if (
                hasattr(self.medication_codeable_concept, "text")
                and self.medication_codeable_concept.text
            ):
                return self.medication_codeable_concept.text
            elif (
                hasattr(self.medication_codeable_concept, "coding")
                and self.medication_codeable_concept.coding
            ):
                first_coding = self.medication_codeable_concept.coding[0]
                if hasattr(first_coding, "display") and first_coding.display:
                    return first_coding.display
        elif self.medication_reference:
            return self.medication_reference
        return "Unknown medication"

    def add_dosage_instruction(
        self,
        text: str,
        dose_quantity: float | None = None,
        dose_unit: str | None = None,
        frequency: int | None = None,
        period: int = 1,
        period_unit: str = "d",
    ) -> Dosage:
        """Add a dosage instruction to the medication request."""
        dosage = Dosage(text=text, sequence=len(self.dosage_instruction) + 1)

        if dose_quantity and dose_unit:
            dosage.dose_and_rate = [
                {
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/dose-rate-type",
                                "code": "ordered",
                                "display": "Ordered",
                            }
                        ]
                    },
                    "doseQuantity": {
                        "value": dose_quantity,
                        "unit": dose_unit,
                        "system": "http://unitsofmeasure.org",
                    },
                }
            ]

        if frequency:
            dosage.timing = {
                "repeat": {"frequency": frequency, "period": period, "periodUnit": period_unit}
            }

        self.dosage_instruction.append(dosage)
        return dosage

    def add_reason_code(
        self, code: str, display: str, system: str = "http://snomed.info/sct"
    ) -> CodeableConcept:
        """Add a reason code for the medication request."""
        reason = CodeableConcept(
            text=display, coding=[{"system": system, "code": code, "display": display}]
        )
        self.reason_code.append(reason)
        return reason

    # --- LLM-friendly extractable facade overrides ---
    @classmethod
    def get_extractable_fields(cls) -> list[str]:  # type: ignore[override]
        """Return fields that should be extracted by LLMs (3-4 key fields only)."""
        return [
            "status",
            "medication_codeable_concept",
            "dosage_instruction",
            "reason_code",
        ]

    @classmethod
    def get_required_extractables(cls) -> list[str]:
        """Fields that must be provided for valid extraction."""
        return ["medication_codeable_concept"]

    @classmethod
    def get_canonical_defaults(cls) -> dict[str, Any]:
        """Default values for system/required fields during extraction."""
        return {
            "status": "active",
            "intent": "order",
            "subject": "Patient/UNKNOWN",
            "medication_codeable_concept": {"text": ""},  # Will be filled by LLM
        }

    @classmethod
    def coerce_extractable(cls, payload: dict[str, Any], relax: bool = True) -> dict[str, Any]:
        """Coerce extractable payload to proper types with relaxed validation."""
        coerced = payload.copy()

        # Coerce medication_codeable_concept to CodeableConcept if it's a string
        if "medication_codeable_concept" in coerced and isinstance(coerced["medication_codeable_concept"], str):
            coerced["medication_codeable_concept"] = {"text": coerced["medication_codeable_concept"]}

        # Coerce dosage_instruction to list of Dosage if it's a string or dict
        if "dosage_instruction" in coerced:
            dosage = coerced["dosage_instruction"]
            if isinstance(dosage, str):
                coerced["dosage_instruction"] = [{"text": dosage}]
            elif isinstance(dosage, dict):
                coerced["dosage_instruction"] = [dosage]
            elif not isinstance(dosage, list):
                coerced["dosage_instruction"] = []

        # Coerce reason_code to list of CodeableConcept if it's a string or dict
        if "reason_code" in coerced:
            reason = coerced["reason_code"]
            if isinstance(reason, str):
                coerced["reason_code"] = [{"text": reason}]
            elif isinstance(reason, dict):
                coerced["reason_code"] = [reason]
            elif not isinstance(reason, list):
                coerced["reason_code"] = []

        return coerced

    @classmethod
    def llm_hints(cls) -> list[str]:  # type: ignore[override]
        """Provide LLM-specific extraction hints."""
        return [
            "Extract medication name/code from prescription text",
            "Include dosage instructions (dose, frequency, duration)",
            "Capture reason for prescription when mentioned",
            "Status should be: active, completed, cancelled, or stopped"
        ]


# Convenience functions for common medication request types


def create_prescription(
    medication_text: str,
    patient_ref: ResourceReference,
    prescriber_ref: ResourceReference | None = None,
    dosage_text: str | None = None,
    **kwargs,
) -> MedicationRequest:
    """Create a prescription medication request."""
    request = MedicationRequest(
        status=MedicationRequestStatus.ACTIVE,
        intent=MedicationRequestIntent.ORDER,
        medication_codeable_concept=CodeableConcept(text=medication_text),
        subject=patient_ref,
        requester=prescriber_ref,
        authored_on=datetime.now().isoformat(),
        **kwargs,
    )

    if dosage_text:
        request.add_dosage_instruction(dosage_text)

    return request


def create_medication_order(
    medication_text: str,
    patient_ref: ResourceReference,
    dose_quantity: float,
    dose_unit: str,
    frequency: int,
    prescriber_ref: ResourceReference | None = None,
    **kwargs,
) -> MedicationRequest:
    """Create a structured medication order."""
    request = MedicationRequest(
        status=MedicationRequestStatus.ACTIVE,
        intent=MedicationRequestIntent.ORDER,
        medication_codeable_concept=CodeableConcept(text=medication_text),
        subject=patient_ref,
        requester=prescriber_ref,
        authored_on=datetime.now().isoformat(),
        **kwargs,
    )

    request.add_dosage_instruction(
        text=f"Take {dose_quantity} {dose_unit} {frequency} times daily",
        dose_quantity=dose_quantity,
        dose_unit=dose_unit,
        frequency=frequency,
    )

    return request
