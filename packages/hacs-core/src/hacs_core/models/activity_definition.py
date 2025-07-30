"""
ActivityDefinition model for definitional resources.

Based on FHIR R5 ActivityDefinition resource with HACS enhancements.
Defines activities that can be requested, recommended, or performed in clinical workflows.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from ..base_resource import BaseResource
from pydantic import Field


class ActivityDefinitionStatus(str, Enum):
    """Status of the activity definition."""

    DRAFT = "draft"
    ACTIVE = "active"
    RETIRED = "retired"
    UNKNOWN = "unknown"


class ActivityDefinitionKind(str, Enum):
    """Kind of activity definition."""

    APPOINTMENT = "Appointment"
    APPOINTMENT_RESPONSE = "AppointmentResponse"
    CARE_PLAN = "CarePlan"
    COMMUNICATION = "Communication"
    COMMUNICATION_REQUEST = "CommunicationRequest"
    DEVICE_REQUEST = "DeviceRequest"
    DIAGNOSTIC_REPORT = "DiagnosticReport"
    MEDICATION_REQUEST = "MedicationRequest"
    NUTRITION_ORDER = "NutritionOrder"
    PROCEDURE = "Procedure"
    PROCEDURE_REQUEST = "ProcedureRequest"
    REFERRAL_REQUEST = "ReferralRequest"
    SERVICE_REQUEST = "ServiceRequest"
    SUPPLY_REQUEST = "SupplyRequest"
    TASK = "Task"
    VISION_PRESCRIPTION = "VisionPrescription"


class RequestIntent(str, Enum):
    """Intent of the request."""

    PROPOSAL = "proposal"
    PLAN = "plan"
    DIRECTIVE = "directive"
    ORDER = "order"
    ORIGINAL_ORDER = "original-order"
    REFLEX_ORDER = "reflex-order"
    FILLER_ORDER = "filler-order"
    INSTANCE_ORDER = "instance-order"
    OPTION = "option"


class RequestPriority(str, Enum):
    """Priority of the request."""

    ROUTINE = "routine"
    URGENT = "urgent"
    ASAP = "asap"
    STAT = "stat"


class ParticipantType(str, Enum):
    """Type of participant."""

    PATIENT = "patient"
    PRACTITIONER = "practitioner"
    RELATED_PERSON = "related-person"
    DEVICE = "device"


class ActivityDefinition(BaseResource):
    """
    Represents an activity definition for clinical workflows.

    Based on FHIR R5 ActivityDefinition with HACS enhancements for healthcare agents.
    Defines activities that can be requested, recommended, or performed.
    """

    resource_type: Literal["ActivityDefinition"] = Field(
        default="ActivityDefinition", description="Resource type identifier"
    )

    # Basic metadata
    url: str | None = Field(
        default=None, description="Canonical identifier for this activity definition"
    )

    identifier: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Additional identifier for the activity definition",
    )

    version: str | None = Field(
        default=None, description="Business version of the activity definition"
    )

    name: str | None = Field(
        default=None, description="Computer-friendly name for the activity definition"
    )

    title: str | None = Field(
        default=None, description="Human-friendly title for the activity definition"
    )

    subtitle: str | None = Field(
        default=None, description="Subordinate title for the activity definition"
    )

    status: ActivityDefinitionStatus = Field(
        default=ActivityDefinitionStatus.DRAFT,
        description="Current status of the activity definition",
    )

    experimental: bool = Field(
        default=False, description="For testing purposes, not real usage"
    )

    # Dates
    date: datetime | None = Field(default=None, description="Date last changed")

    # Publishing information
    publisher: str | None = Field(default=None, description="Name of the publisher")

    contact: list[dict[str, Any]] = Field(
        default_factory=list, description="Contact details for the publisher"
    )

    description: str | None = Field(
        default=None,
        description="Natural language description of the activity definition",
    )

    use_context: list[dict[str, Any]] = Field(
        default_factory=list, description="Context the content is intended to support"
    )

    jurisdiction: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Intended jurisdiction for activity definition",
    )

    purpose: str | None = Field(
        default=None, description="Why this activity definition is defined"
    )

    usage: str | None = Field(
        default=None,
        description="Describes the clinical usage of the activity definition",
    )

    copyright: str | None = Field(
        default=None, description="Use and/or publishing restrictions"
    )

    copyright_label: str | None = Field(
        default=None, description="Copyright holder and year(s)"
    )

    approval_date: datetime | None = Field(
        default=None,
        description="When the activity definition was approved by publisher",
    )

    last_review_date: datetime | None = Field(
        default=None, description="When the activity definition was last reviewed"
    )

    effective_period: dict[str, Any] | None = Field(
        default=None, description="When the activity definition is expected to be used"
    )

    # Clinical metadata
    topic: list[dict[str, Any]] = Field(
        default_factory=list, description="E.g. Education, Treatment, Assessment"
    )

    author: list[dict[str, Any]] = Field(
        default_factory=list, description="Who authored the content"
    )

    editor: list[dict[str, Any]] = Field(
        default_factory=list, description="Who edited the content"
    )

    reviewer: list[dict[str, Any]] = Field(
        default_factory=list, description="Who reviewed the content"
    )

    endorser: list[dict[str, Any]] = Field(
        default_factory=list, description="Who endorsed the content"
    )

    related_artifact: list[dict[str, Any]] = Field(
        default_factory=list, description="Additional documentation, citations, etc."
    )

    # Libraries and dependencies
    library: list[str] = Field(
        default_factory=list,
        description="Logic libraries used by this activity definition",
    )

    # Activity definition specific fields
    kind: ActivityDefinitionKind | None = Field(
        default=None, description="Kind of resource this activity definition defines"
    )

    profile: str | None = Field(
        default=None, description="What profile the resource needs to conform to"
    )

    code: dict[str, Any] | None = Field(
        default=None, description="Detail type of activity"
    )

    intent: RequestIntent | None = Field(
        default=None,
        description="Proposal | plan | directive | order | original-order | reflex-order | filler-order | instance-order | option",
    )

    priority: RequestPriority | None = Field(
        default=None, description="Routine | urgent | asap | stat"
    )

    do_not_perform: bool | None = Field(
        default=None, description="True if the activity should not be performed"
    )

    # Timing
    timing_timing: dict[str, Any] | None = Field(
        default=None, description="When activity is to occur"
    )

    timing_datetime: datetime | None = Field(
        default=None, description="When activity is to occur"
    )

    timing_age: dict[str, Any] | None = Field(
        default=None, description="When activity is to occur"
    )

    timing_period: dict[str, Any] | None = Field(
        default=None, description="When activity is to occur"
    )

    timing_range: dict[str, Any] | None = Field(
        default=None, description="When activity is to occur"
    )

    timing_duration: dict[str, Any] | None = Field(
        default=None, description="When activity is to occur"
    )

    # Location
    location: str | None = Field(default=None, description="Where it should happen")

    # Participants
    participant: list[dict[str, Any]] = Field(
        default_factory=list, description="Who should participate in the action"
    )

    # Product
    product_reference: str | None = Field(
        default=None, description="What's administered/supplied"
    )

    product_codeable_concept: dict[str, Any] | None = Field(
        default=None, description="What's administered/supplied"
    )

    # Quantity
    quantity: dict[str, Any] | None = Field(
        default=None, description="How much is administered/consumed/supplied"
    )

    # Dosage (for medications)
    dosage: list[dict[str, Any]] = Field(
        default_factory=list, description="Detailed dosage instructions"
    )

    # Body site
    body_site: list[dict[str, Any]] = Field(
        default_factory=list, description="What part of body to perform on"
    )

    # Specimen requirements
    specimen_requirement: list[str] = Field(
        default_factory=list,
        description="What specimens are required to perform this action",
    )

    # Observation requirements
    observation_requirement: list[str] = Field(
        default_factory=list,
        description="What observations are required to perform this action",
    )

    # Observation result requirements
    observation_result_requirement: list[str] = Field(
        default_factory=list,
        description="What observations must be produced by this action",
    )

    # Transform
    transform: str | None = Field(
        default=None, description="Transform to apply the template"
    )

    # Dynamic values
    dynamic_value: list[dict[str, Any]] = Field(
        default_factory=list, description="Dynamic values for the action"
    )

    # HACS-specific enhancements
    agent_context: dict[str, Any] = Field(
        default_factory=dict, description="Agent-specific context and configuration"
    )

    execution_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata about activity execution and performance",
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "id": "blood-pressure-measurement",
                    "resource_type": "ActivityDefinition",
                    "title": "Blood Pressure Measurement",
                    "status": "active",
                    "kind": "Observation",
                    "description": "Standard blood pressure measurement procedure",
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": "85354-9",
                                "display": "Blood pressure panel with all children optional",
                            }
                        ]
                    },
                    "participant": [
                        {
                            "type": "practitioner",
                            "role": {
                                "coding": [
                                    {
                                        "system": "http://snomed.info/sct",
                                        "code": "223366009",
                                        "display": "Healthcare professional",
                                    }
                                ]
                            },
                        }
                    ],
                }
            ]
        }
