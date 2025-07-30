"""
GuidanceResponse and RequestOrchestration models for clinical decision support.

Based on FHIR R5 GuidanceResponse and RequestOrchestration resources with HACS enhancements.
Supports clinical decision support responses and orchestrated clinical requests.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from ..base_resource import BaseResource
from pydantic import Field


class GuidanceResponseStatus(str, Enum):
    """Status of the guidance response."""

    SUCCESS = "success"
    DATA_REQUESTED = "data-requested"
    DATA_REQUIRED = "data-required"
    IN_PROGRESS = "in-progress"
    FAILURE = "failure"
    ENTERED_IN_ERROR = "entered-in-error"


class RequestStatus(str, Enum):
    """Status of the request orchestration."""

    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on-hold"
    REVOKED = "revoked"
    COMPLETED = "completed"
    ENTERED_IN_ERROR = "entered-in-error"
    UNKNOWN = "unknown"


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


class GuidanceResponse(BaseResource):
    """
    Represents the response from a clinical decision support service.

    Based on FHIR R5 GuidanceResponse with HACS enhancements for healthcare agents.
    Contains the guidance provided by a decision support service.
    """

    resource_type: Literal["GuidanceResponse"] = Field(
        default="GuidanceResponse", description="Resource type identifier"
    )

    # Request identification
    request_identifier: str | None = Field(
        default=None,
        description="Identifier of the request associated with this response",
    )

    identifier: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Business identifier for the guidance response",
    )

    # Knowledge module
    module_uri: str | None = Field(
        default=None, description="What guidance was requested (URI)"
    )

    module_canonical: str | None = Field(
        default=None, description="What guidance was requested (canonical reference)"
    )

    module_codeable_concept: dict[str, Any] | None = Field(
        default=None, description="What guidance was requested (coded concept)"
    )

    # Response metadata
    status: GuidanceResponseStatus = Field(
        description="Current status of the guidance response"
    )

    subject: str | None = Field(
        default=None, description="Patient the guidance response is for"
    )

    encounter: str | None = Field(
        default=None, description="Encounter during which the guidance was requested"
    )

    occurrence_datetime: datetime | None = Field(
        default=None, description="When the guidance response was processed"
    )

    performer: str | None = Field(
        default=None,
        description="Device/person/organization that provided the guidance",
    )

    # Reason for guidance
    reason_code: list[dict[str, Any]] = Field(
        default_factory=list, description="Why guidance is needed"
    )

    reason_reference: list[str] = Field(
        default_factory=list, description="Why guidance is needed"
    )

    # Notes and evaluation
    note: list[dict[str, Any]] = Field(
        default_factory=list, description="Additional notes about the guidance"
    )

    evaluation_message: list[str] = Field(
        default_factory=list,
        description="Messages resulting from the evaluation of the artifact or artifacts",
    )

    # Output parameters
    output_parameters: str | None = Field(
        default=None, description="The output parameters of the evaluation, if any"
    )

    # Result
    result: str | None = Field(default=None, description="Proposed actions, if any")

    # Data requirements
    data_requirement: list[dict[str, Any]] = Field(
        default_factory=list, description="Additional required data"
    )

    # HACS-specific enhancements
    guidance_content: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured guidance content for agent processing",
    )

    confidence_score: float | None = Field(
        default=None,
        description="Confidence score for the guidance (0.0 to 1.0)",
        ge=0.0,
        le=1.0,
    )

    recommendations: list[dict[str, Any]] = Field(
        default_factory=list, description="Specific clinical recommendations"
    )

    alerts: list[dict[str, Any]] = Field(
        default_factory=list, description="Clinical alerts and warnings"
    )

    agent_context: dict[str, Any] = Field(
        default_factory=dict, description="Agent-specific context and configuration"
    )

    execution_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata about guidance execution and performance",
    )


class RequestOrchestrationAction(BaseResource):
    """
    Represents an action within a request orchestration.

    Actions represent specific requests or recommendations.
    """

    resource_type: Literal["RequestOrchestrationAction"] = Field(
        default="RequestOrchestrationAction", description="Resource type identifier"
    )

    # Action identification
    prefix: str | None = Field(
        default=None,
        description="User-visible prefix for the action (e.g., '1.', 'a.')",
    )

    title: str | None = Field(
        default=None, description="User-visible title for the action"
    )

    description: str | None = Field(
        default=None, description="Brief description of the action"
    )

    text_equivalent: str | None = Field(
        default=None, description="Static text equivalent of the action"
    )

    priority: str | None = Field(
        default=None, description="Indicates how quickly the action should be addressed"
    )

    # Action code
    code: list[dict[str, Any]] = Field(
        default_factory=list, description="Code representing the action to be performed"
    )

    # Documentation
    documentation: list[dict[str, Any]] = Field(
        default_factory=list, description="Supporting documentation for the action"
    )

    # Conditions
    condition: list[dict[str, Any]] = Field(
        default_factory=list, description="Conditions that apply to the action"
    )

    # Input/Output
    input: list[dict[str, Any]] = Field(
        default_factory=list, description="Input data requirements"
    )

    output: list[dict[str, Any]] = Field(
        default_factory=list, description="Output data definition"
    )

    # Related actions
    related_action: list[dict[str, Any]] = Field(
        default_factory=list, description="Relationship to other actions"
    )

    # Timing
    timing_datetime: datetime | None = Field(
        default=None, description="When the action should take place"
    )

    timing_age: dict[str, Any] | None = Field(
        default=None, description="Age-based timing"
    )

    timing_period: dict[str, Any] | None = Field(
        default=None, description="Period-based timing"
    )

    timing_duration: dict[str, Any] | None = Field(
        default=None, description="Duration-based timing"
    )

    timing_range: dict[str, Any] | None = Field(
        default=None, description="Range-based timing"
    )

    timing_timing: dict[str, Any] | None = Field(
        default=None, description="Complex timing specification"
    )

    # Location
    location: str | None = Field(
        default=None, description="Where the action should take place"
    )

    # Participants
    participant: list[dict[str, Any]] = Field(
        default_factory=list, description="Who should participate in the action"
    )

    # Action type
    type_coding: dict[str, Any] | None = Field(
        default=None, description="The type of action to perform"
    )

    # Grouping behavior
    grouping_behavior: str | None = Field(
        default=None, description="Defines the grouping behavior for the action"
    )

    selection_behavior: str | None = Field(
        default=None, description="Defines the selection behavior for the action"
    )

    required_behavior: str | None = Field(
        default=None, description="Defines the required behavior for the action"
    )

    precheck_behavior: str | None = Field(
        default=None, description="Defines whether the action should be preselected"
    )

    cardinality_behavior: str | None = Field(
        default=None,
        description="Defines whether the action can be selected multiple times",
    )

    # Resource reference
    resource: str | None = Field(default=None, description="The target of the action")

    # Nested actions
    action: list["RequestOrchestrationAction"] = Field(
        default_factory=list, description="Sub-actions within this action"
    )


class RequestOrchestration(BaseResource):
    """
    Represents a group of related requests that can be used to capture intended activities.

    Based on FHIR R5 RequestOrchestration with HACS enhancements for healthcare agents.
    Often the result of applying a PlanDefinition to a particular patient.
    """

    resource_type: Literal["RequestOrchestration"] = Field(
        default="RequestOrchestration", description="Resource type identifier"
    )

    # Business identifiers
    identifier: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Business identifier for the request orchestration",
    )

    # Canonical reference
    instantiates_canonical: list[str] = Field(
        default_factory=list, description="Instantiates FHIR protocol or definition"
    )

    instantiates_uri: list[str] = Field(
        default_factory=list, description="Instantiates external protocol or definition"
    )

    # Based on
    based_on: list[str] = Field(
        default_factory=list, description="What request orchestration this is based on"
    )

    replaces: list[str] = Field(
        default_factory=list, description="Request orchestration this replaces"
    )

    # Request group identifier
    group_identifier: dict[str, Any] | None = Field(
        default=None, description="Composite request this is part of"
    )

    # Status and intent
    status: RequestStatus = Field(
        description="Current status of the request orchestration"
    )

    intent: RequestIntent = Field(
        description="Indicates the level of authority/intentionality associated with the request orchestration"
    )

    priority: RequestPriority | None = Field(
        default=None,
        description="Indicates how quickly the request orchestration should be addressed",
    )

    # Code
    code: dict[str, Any] | None = Field(
        default=None, description="What's being requested/ordered"
    )

    # Subject and context
    subject: str | None = Field(
        default=None, description="Who the request orchestration is for"
    )

    encounter: str | None = Field(
        default=None, description="Created during encounter/admission/stay"
    )

    # Timing
    authored_on: datetime | None = Field(
        default=None, description="When the request orchestration was authored"
    )

    # Participants
    author: str | None = Field(
        default=None,
        description="Device/person/organization that authored the request orchestration",
    )

    # Reason
    reason_code: list[dict[str, Any]] = Field(
        default_factory=list, description="Why the request orchestration is needed"
    )

    reason_reference: list[str] = Field(
        default_factory=list, description="Why the request orchestration is needed"
    )

    # Goals
    goal: list[str] = Field(
        default_factory=list,
        description="What goals this request orchestration addresses",
    )

    # Notes
    note: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Additional notes about the request orchestration",
    )

    # Actions - the core of the request orchestration
    action: list[RequestOrchestrationAction] = Field(
        default_factory=list, description="Proposed actions, if any"
    )

    # HACS-specific enhancements
    source_plan_definition: str | None = Field(
        default=None, description="PlanDefinition that generated this orchestration"
    )

    guidance_context: dict[str, Any] = Field(
        default_factory=dict,
        description="Context from the guidance that generated this orchestration",
    )

    agent_context: dict[str, Any] = Field(
        default_factory=dict, description="Agent-specific context and configuration"
    )

    execution_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata about orchestration execution and performance",
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "id": "hypertension-care-requests",
                    "resource_type": "RequestOrchestration",
                    "status": "active",
                    "intent": "plan",
                    "subject": "patient-123",
                    "authored_on": "2024-01-15T10:30:00Z",
                    "code": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "38341003",
                                "display": "Hypertensive disorder",
                            }
                        ]
                    },
                    "action": [
                        {
                            "title": "Schedule Follow-up",
                            "description": "Schedule follow-up appointment in 4 weeks",
                            "timing_period": {
                                "start": "2024-02-12T00:00:00Z",
                                "end": "2024-02-19T23:59:59Z",
                            },
                        }
                    ],
                }
            ]
        }


# Update the forward reference
RequestOrchestrationAction.model_rebuild()
