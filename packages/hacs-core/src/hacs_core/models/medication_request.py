"""
MedicationRequest model based on FHIR US Core MedicationRequest Profile.

This model represents medication prescriptions and orders with comprehensive clinical information,
optimized for structured outputs and LLM interactions.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from ..base_resource import BaseResource
from pydantic import Field


class MedicationRequestStatus(str, Enum):
    """Status of the medication request."""

    ACTIVE = "active"
    ON_HOLD = "on-hold"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    ENTERED_IN_ERROR = "entered-in-error"
    STOPPED = "stopped"
    DRAFT = "draft"
    UNKNOWN = "unknown"


class MedicationRequestIntent(str, Enum):
    """Intent of the medication request."""

    PROPOSAL = "proposal"
    PLAN = "plan"
    ORDER = "order"
    ORIGINAL_ORDER = "original-order"
    REFLEX_ORDER = "reflex-order"
    FILLER_ORDER = "filler-order"
    INSTANCE_ORDER = "instance-order"
    OPTION = "option"


class MedicationRequestPriority(str, Enum):
    """Priority of the medication request."""

    ROUTINE = "routine"
    URGENT = "urgent"
    ASAP = "asap"
    STAT = "stat"


class MedicationRequestCategory(str, Enum):
    """Category of the medication request."""

    INPATIENT = "inpatient"
    OUTPATIENT = "outpatient"
    COMMUNITY = "community"
    DISCHARGE = "discharge"


class MedicationRequest(BaseResource):
    """
    Represents a medication prescription or order.

    Based on FHIR US Core MedicationRequest Profile with HACS enhancements.
    Optimized for structured outputs and LLM interactions.
    """

    resource_type: Literal["MedicationRequest"] = Field(
        default="MedicationRequest", description="Resource type identifier"
    )

    # Identifiers
    identifier: list[dict[str, Any]] = Field(
        default_factory=list,
        description="External identifiers for this medication request",
    )

    # Status - required
    status: MedicationRequestStatus = Field(
        description="A code specifying the current state of the order"
    )

    status_reason: dict[str, Any] | None = Field(
        default=None, description="Reason for current status"
    )

    # LLM-FRIENDLY: Simple status reason
    status_note: str | None = Field(
        default=None,
        description="Why the prescription has this status",
        examples=[
            "Patient request",
            "Side effects",
            "Therapy complete",
            "Changed to different medication",
        ],
    )

    intent: MedicationRequestIntent = Field(
        description="Whether the request is a proposal, plan, or an original order"
    )

    category: list[dict[str, Any]] = Field(
        default_factory=list, description="Type of medication usage"
    )

    # LLM-FRIENDLY: Simple category
    prescription_type: MedicationRequestCategory | None = Field(
        default=None, description="Where this medication will be used"
    )

    priority: MedicationRequestPriority | None = Field(
        default=None, description="Routine | urgent | asap | stat"
    )

    do_not_perform: bool | None = Field(
        default=None, description="True if medication was not requested"
    )

    # Medication - required (choice of Reference(Medication) or CodeableConcept)
    medication_reference: str | None = Field(
        default=None, description="Reference to Medication resource"
    )

    medication_codeable_concept: dict[str, Any] | None = Field(
        default=None, description="Medication as a coded concept"
    )

    # LLM-FRIENDLY: Simple medication info
    medication_name: str | None = Field(
        default=None,
        description="Name of the prescribed medication",
        examples=["Lisinopril 10mg", "Metformin 500mg", "Amoxicillin 250mg"],
    )

    generic_name: str | None = Field(
        default=None, description="Generic name of the medication"
    )

    brand_name: str | None = Field(
        default=None, description="Brand name of the medication"
    )

    # Subject - required
    subject: str = Field(
        description="Who medication request is for (Patient reference)"
    )

    # Encounter context
    encounter: str | None = Field(
        default=None, description="Encounter created as part of this request"
    )

    # Supporting information
    supporting_information: list[str] = Field(
        default_factory=list,
        description="Information to support ordering of the medication",
    )

    # Timing
    authored_on: datetime | None = Field(
        default=None, description="When request was initially authored"
    )

    # Requester
    requester: str | None = Field(
        default=None, description="Who/What requested the medication"
    )

    # LLM-FRIENDLY: Simple requester
    prescribed_by: str | None = Field(
        default=None,
        description="Who prescribed this medication",
        examples=[
            "Dr. Smith",
            "Primary care physician",
            "Cardiologist",
            "Emergency physician",
        ],
    )

    # Performer
    performer: str | None = Field(
        default=None, description="Specified performer of the medication treatment"
    )

    performer_type: dict[str, Any] | None = Field(
        default=None,
        description="Desired kind of performer of the medication treatment",
    )

    # LLM-FRIENDLY: Simple performer
    to_be_given_by: str | None = Field(
        default=None,
        description="Who should administer this medication",
        examples=["Patient", "Nurse", "Family member", "Home health aide", "Pharmacy"],
    )

    recorder: str | None = Field(
        default=None, description="Person who entered the request"
    )

    # Reason
    reason_code: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Reason or indication for ordering or not ordering the medication",
    )

    reason_reference: list[str] = Field(
        default_factory=list,
        description="Reference to condition or observation that supports why the medication was ordered",
    )

    # LLM-FRIENDLY: Simple reason
    prescribed_for: str | None = Field(
        default=None,
        description="What condition this medication is treating",
        examples=["Hypertension", "Type 2 diabetes", "Infection", "Pain", "Depression"],
    )

    prescribed_for_details: str | None = Field(
        default=None, description="Detailed reason for prescription"
    )

    # Instantiates
    instantiates_canonical: list[str] = Field(
        default_factory=list, description="Instantiates FHIR protocol or definition"
    )

    instantiates_uri: list[str] = Field(
        default_factory=list, description="Instantiates external protocol or definition"
    )

    # Based on
    based_on: list[str] = Field(
        default_factory=list, description="What request fulfills"
    )

    # Group identifier
    group_identifier: dict[str, Any] | None = Field(
        default=None, description="Composite request this is part of"
    )

    # Course of therapy
    course_of_therapy_type: dict[str, Any] | None = Field(
        default=None, description="Overall pattern of medication administration"
    )

    # LLM-FRIENDLY: Simple course type
    treatment_plan: str | None = Field(
        default=None,
        description="Type of treatment plan",
        examples=[
            "One-time dose",
            "Short course",
            "Long-term therapy",
            "As needed",
            "Maintenance therapy",
        ],
    )

    # Insurance
    insurance: list[str] = Field(
        default_factory=list, description="Associated insurance coverage"
    )

    # Note
    note: list[dict[str, Any]] = Field(
        default_factory=list, description="Information about the prescription"
    )

    # LLM-FRIENDLY: Simple notes
    instructions: str | None = Field(
        default=None, description="Instructions for the patient"
    )

    pharmacy_notes: str | None = Field(
        default=None, description="Special instructions for the pharmacy"
    )

    # Dosage instruction
    dosage_instruction: list[dict[str, Any]] = Field(
        default_factory=list, description="How the medication should be taken"
    )

    # LLM-FRIENDLY: Simple dosage
    dosage: str | None = Field(
        default=None,
        description="How much and how often to take",
        examples=[
            "Take 1 tablet twice daily",
            "5ml every 8 hours",
            "Apply thin layer twice daily",
            "1 puff as needed",
        ],
    )

    route: str | None = Field(
        default=None,
        description="How the medication should be taken",
        examples=["By mouth", "Topical", "Injection", "Inhalation", "Sublingual"],
    )

    # Dispense request
    dispense_request: dict[str, Any] | None = Field(
        default=None, description="Medication supply authorization"
    )

    # LLM-FRIENDLY: Simple dispense info
    quantity_to_dispense: str | None = Field(
        default=None,
        description="How much to give the patient",
        examples=["30 tablets", "90 day supply", "1 tube", "100ml"],
    )

    refills_remaining: int | None = Field(
        default=None, description="Number of refills remaining"
    )

    days_supply: int | None = Field(
        default=None, description="Number of days this prescription should last"
    )

    # Substitution
    substitution: dict[str, Any] | None = Field(
        default=None, description="Any restrictions on medication substitution"
    )

    generic_substitution_allowed: bool | None = Field(
        default=None, description="Whether generic substitution is allowed"
    )

    # Prior prescription
    prior_prescription: str | None = Field(
        default=None,
        description="Reference to an order/prescription that is being replaced",
    )

    # Detection issue
    detected_issue: list[str] = Field(
        default_factory=list, description="Clinical issue with action"
    )

    # LLM-FRIENDLY: Issues and alerts
    drug_interactions: list[str] = Field(
        default_factory=list, description="Potential drug interactions"
    )

    allergies_checked: bool | None = Field(
        default=None, description="Whether allergies were checked"
    )

    contraindications: list[str] = Field(
        default_factory=list, description="Reasons this medication should not be given"
    )

    # Event history
    event_history: list[str] = Field(
        default_factory=list,
        description="A list of events of interest in the lifecycle",
    )

    # HACS-specific enhancements
    cost_estimate: str | None = Field(
        default=None, description="Estimated cost to patient"
    )

    covered_by_insurance: bool | None = Field(
        default=None, description="Whether insurance covers this medication"
    )

    therapeutic_goal: str | None = Field(
        default=None, description="What we hope to achieve with this medication"
    )

    monitoring_required: bool | None = Field(
        default=None, description="Whether lab monitoring is needed"
    )

    monitoring_schedule: str | None = Field(
        default=None, description="When to check labs or other monitoring"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "id": "med-request-lisinopril-001",
                    "resource_type": "MedicationRequest",
                    "status": "active",
                    "intent": "order",
                    "prescription_type": "outpatient",
                    "priority": "routine",
                    "medication_name": "Lisinopril 10mg",
                    "generic_name": "Lisinopril",
                    "subject": "Patient/patient-123",
                    "prescribed_by": "Dr. Sarah Smith",
                    "prescribed_for": "Hypertension",
                    "dosage": "Take 1 tablet once daily",
                    "route": "By mouth",
                    "quantity_to_dispense": "30 tablets",
                    "refills_remaining": 5,
                    "days_supply": 30,
                    "generic_substitution_allowed": True,
                    "instructions": "Take with or without food. Monitor blood pressure regularly.",
                    "therapeutic_goal": "Reduce blood pressure to target <130/80",
                    "monitoring_required": True,
                    "monitoring_schedule": "Check blood pressure in 2 weeks, labs in 1 month",
                    "medication_codeable_concept": {
                        "coding": [
                            {
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": "314077",
                                "display": "Lisinopril 10 MG Oral Tablet",
                            }
                        ],
                        "text": "Lisinopril 10mg tablet",
                    },
                },
                {
                    "id": "med-request-amoxicillin-002",
                    "resource_type": "MedicationRequest",
                    "status": "completed",
                    "intent": "order",
                    "prescription_type": "outpatient",
                    "priority": "routine",
                    "medication_name": "Amoxicillin 500mg",
                    "generic_name": "Amoxicillin",
                    "subject": "Patient/patient-456",
                    "prescribed_by": "Dr. John Doe",
                    "prescribed_for": "Strep throat",
                    "dosage": "Take 1 capsule three times daily",
                    "route": "By mouth",
                    "quantity_to_dispense": "21 capsules",
                    "refills_remaining": 0,
                    "days_supply": 7,
                    "treatment_plan": "Short course",
                    "instructions": "Take with food to reduce stomach upset. Complete full course even if feeling better.",
                    "therapeutic_goal": "Clear strep throat infection",
                    "allergies_checked": True,
                    "medication_codeable_concept": {
                        "coding": [
                            {
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": "308192",
                                "display": "Amoxicillin 500 MG Oral Capsule",
                            }
                        ],
                        "text": "Amoxicillin 500mg capsule",
                    },
                },
            ]
        }
