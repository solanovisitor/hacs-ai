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

from .base_resource import DomainResource, FacadeSpec
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
    def get_extraction_examples(cls) -> dict[str, Any]:
        """Return extraction examples showing different extractable field scenarios."""
        # Complete medication request
        complete_example = {            "status": "active",
            "medication_codeable_concept": {"text": "Losartana 50mg"},
            "dosage_instruction": [{"text": "1 comprimido pela manhã"}],
            "reason_code": [{"text": "hipertensão"}],
        }

        # Simple medication without dosage
        simple_example = {            "status": "active",
            "medication_codeable_concept": {"text": "Paracetamol"},
        }

        # Medication with dosage but no reason
        dosage_example = {            "status": "active",
            "medication_codeable_concept": {"text": "Metformina 850mg"},
            "dosage_instruction": [{"text": "2 vezes ao dia"}],
        }

        return {
            "object": complete_example,
            "array": [complete_example, simple_example, dosage_example],
            "scenarios": {
                "complete": complete_example,
                "simple": simple_example,
                "with_dosage": dosage_example,
            }
        }

    @classmethod
    def llm_hints(cls) -> list[str]:  # type: ignore[override]
        """Provide LLM-specific extraction hints."""
        return [
            "Extract medication name/code from prescription text",
            "Include dosage instructions (dose, frequency, duration)",
            "Capture reason for prescription when mentioned (reason_code.text)",
            "Status should be: active, completed, cancelled, or stopped"
        ]

    @classmethod
    def get_facades(cls) -> dict[str, FacadeSpec]:
        """Return available extraction facades for MedicationRequest."""
        return {
            "medication": FacadeSpec(
                fields=["medication_codeable_concept", "medication_reference", "medication_text"],
                required_fields=["medication_codeable_concept"],
                field_hints={
                    "medication_codeable_concept": "Medication name and strength (e.g., 'losartana 50mg', 'paracetamol 500mg')",
                    "medication_reference": "Reference to a Medication resource if available",
                    "medication_text": "Free text description of the medication",
                },
                field_examples={
                    "medication_codeable_concept": {"text": "losartana 50mg"},
                    "medication_reference": {"reference": "Medication/losartan-50mg"},
                    "medication_text": "Losartana potássica 50mg comprimidos"
                },
                field_types={
                    "medication_codeable_concept": "CodeableConcept",
                    "medication_reference": "Reference[Medication]",
                    "medication_text": "string"
                },
                description="Medication identification and coding",
                llm_guidance="Extract the specific medication being prescribed, including name, strength, and formulation. Focus on the active ingredient and dosage form.",
                conversational_prompts=[
                    "What medication is being prescribed?",
                    "What is the strength or dose of this medication?",
                    "What is the brand name or generic name?",
                    "What formulation is this (tablet, capsule, liquid)?"
                ],
                strict=False,
            ),
            
            "dosage": FacadeSpec(
                fields=["dosage_instruction", "dose_and_rate", "frequency", "timing", "route"],
                required_fields=[],
                field_hints={
                    "dosage_instruction": "Free text dosage instructions as written by prescriber",
                    "dose_and_rate": "Structured dose amount and administration rate",
                    "frequency": "How often to take medication (e.g., '2x daily', 'every 8 hours')",
                    "timing": "Structured timing information for administration",
                    "route": "Route of administration (oral, injectable, topical, etc.)",
                },
                field_examples={
                    "dosage_instruction": [{"text": "Tomar 1 comprimido 2 vezes ao dia após as refeições"}],
                    "dose_and_rate": [{"dose_quantity": {"value": 50, "unit": "mg"}}],
                    "frequency": "2x ao dia",
                    "route": {"text": "oral"},
                    "timing": {"repeat": {"frequency": 2, "period": 1, "period_unit": "d"}}
                },
                field_types={
                    "dosage_instruction": "array[DosageInstruction]",
                    "dose_and_rate": "array[DoseAndRate]",
                    "frequency": "string",
                    "timing": "Timing",
                    "route": "CodeableConcept"
                },
                description="Dosage instructions and administration details",
                llm_guidance="Extract how the medication should be taken: dose amount, frequency, timing, and route. Include both structured and free-text instructions.",
                conversational_prompts=[
                    "How much of this medication should be taken?",
                    "How often should this medication be taken?",
                    "When should this medication be taken?",
                    "How should this medication be administered?"
                ],
                strict=False,
            ),
            
            "intent": FacadeSpec(
                fields=["intent", "category", "priority", "status"],
                required_fields=["intent"],
                field_hints={
                    "intent": "Prescription intent: 'proposal', 'plan', 'order', 'original-order'",
                    "category": "Prescription category: 'inpatient', 'outpatient', 'community', 'discharge'",
                    "priority": "Request priority: 'routine', 'urgent', 'asap', 'stat'",
                    "status": "Current status: 'active', 'on-hold', 'cancelled', 'completed'",
                },
                field_examples={
                    "intent": "order",
                    "category": [{"text": "outpatient"}],
                    "priority": "routine",
                    "status": "active"
                },
                field_types={
                    "intent": "enum(proposal|plan|order|original-order|reflex-order|filler-order|instance-order|option)",
                    "category": "array[CodeableConcept]",
                    "priority": "enum(routine|urgent|asap|stat)",
                    "status": "enum(active|on-hold|cancelled|completed|entered-in-error|stopped|draft|unknown)"
                },
                description="Request intent and administrative status",
                llm_guidance="Extract the clinical intent behind the medication request and its administrative priority and status.",
                conversational_prompts=[
                    "Is this a firm order or just a plan/proposal?",
                    "What is the urgency of this prescription?",
                    "What is the current status of this prescription?",
                    "Is this for inpatient or outpatient use?"
                ],
                strict=False,
            ),
            
            "authorship": FacadeSpec(
                fields=["requester", "authored_on", "encounter", "reason_code", "note"],
                required_fields=[],
                field_hints={
                    "requester": "Healthcare professional who prescribed the medication",
                    "authored_on": "Date/time when prescription was written",
                    "encounter": "Clinical encounter when prescription was made",
                    "reason_code": "Indication for prescription (diagnosis, symptom, condition)",
                    "note": "Additional notes or instructions about the prescription",
                },
                field_examples={
                    "requester": {"reference": "Practitioner/dr-silva"},
                    "authored_on": "2024-01-15T10:30:00",
                    "encounter": {"reference": "Encounter/visit-20240115"},
                    "reason_code": [{"text": "hipertensão arterial"}],
                    "note": [{"text": "Continuar monitoramento da pressão arterial"}]
                },
                field_types={
                    "requester": "Reference[Practitioner|PractitionerRole]",
                    "authored_on": "datetime",
                    "encounter": "Reference[Encounter]",
                    "reason_code": "array[CodeableConcept]",
                    "note": "array[Annotation]"
                },
                description="Prescriber information and clinical context",
                llm_guidance="Extract information about who prescribed the medication, when, and why. Include clinical rationale and any special instructions.",
                conversational_prompts=[
                    "Who prescribed this medication?",
                    "When was this prescription written?",
                    "Why was this medication prescribed?",
                    "Are there any special notes about this prescription?"
                ],
                strict=False,
            ),
        }


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
