"""
PlanDefinition model for clinical protocols, order sets, and decision support rules.

Based on FHIR R5 PlanDefinition resource with HACS enhancements for healthcare agents.
Supports Event-Condition-Action rules, clinical protocols, and order sets.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from ..base_resource import BaseResource
from pydantic import Field


class PlanDefinitionStatus(str, Enum):
    """Status of the plan definition."""

    DRAFT = "draft"
    ACTIVE = "active"
    RETIRED = "retired"
    UNKNOWN = "unknown"


class PlanDefinitionType(str, Enum):
    """Type of plan definition."""

    ORDER_SET = "order-set"
    CLINICAL_PROTOCOL = "clinical-protocol"
    ECA_RULE = "eca-rule"  # Event-Condition-Action rule
    WORKFLOW_DEFINITION = "workflow-definition"


class ActionConditionKind(str, Enum):
    """Kind of condition for actions."""

    APPLICABILITY = "applicability"
    START = "start"
    STOP = "stop"


class ActionRelationshipType(str, Enum):
    """Relationship between actions."""

    BEFORE_START = "before-start"
    BEFORE = "before"
    BEFORE_END = "before-end"
    CONCURRENT_WITH_START = "concurrent-with-start"
    CONCURRENT = "concurrent"
    CONCURRENT_WITH_END = "concurrent-with-end"
    AFTER_START = "after-start"
    AFTER = "after"
    AFTER_END = "after-end"


class ActionSelectionBehavior(str, Enum):
    """Selection behavior for action groups."""

    ANY = "any"
    ALL = "all"
    ALL_OR_NONE = "all-or-none"
    EXACTLY_ONE = "exactly-one"
    AT_MOST_ONE = "at-most-one"
    ONE_OR_MORE = "one-or-more"


class ActionRequiredBehavior(str, Enum):
    """Required behavior for actions."""

    MUST = "must"
    COULD = "could"
    MUST_UNLESS_DOCUMENTED = "must-unless-documented"


class ActionPrecheckBehavior(str, Enum):
    """Precheck behavior for actions."""

    YES = "yes"
    NO = "no"


class ActionCardinalityBehavior(str, Enum):
    """Cardinality behavior for actions."""

    SINGLE = "single"
    MULTIPLE = "multiple"


class PlanDefinitionAction(BaseResource):
    """
    Represents an action within a plan definition.

    Actions can be nested to create complex workflows and protocols.
    """

    resource_type: Literal["PlanDefinitionAction"] = Field(
        default="PlanDefinitionAction", description="Resource type identifier"
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

    # Action behavior
    selection_behavior: ActionSelectionBehavior | None = Field(
        default=None, description="Defines the selection behavior for action groups"
    )

    required_behavior: ActionRequiredBehavior | None = Field(
        default=None, description="Defines the required behavior for the action"
    )

    precheck_behavior: ActionPrecheckBehavior | None = Field(
        default=None, description="Defines whether the action should be preselected"
    )

    cardinality_behavior: ActionCardinalityBehavior | None = Field(
        default=None,
        description="Defines whether the action can be selected multiple times",
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

    # Participants
    participant: list[dict[str, Any]] = Field(
        default_factory=list, description="Who should participate in the action"
    )

    # Action type
    type_coding: dict[str, Any] | None = Field(
        default=None, description="The type of action to perform"
    )

    # Action definition
    definition_canonical: str | None = Field(
        default=None,
        description="Description of the activity to be performed (ActivityDefinition reference)",
    )

    definition_uri: str | None = Field(
        default=None, description="Description of the activity to be performed (URI)"
    )

    # Transform
    transform: str | None = Field(
        default=None, description="Transform to apply the template"
    )

    # Dynamic values
    dynamic_value: list[dict[str, Any]] = Field(
        default_factory=list, description="Dynamic values for the action"
    )

    # Nested actions
    action: list["PlanDefinitionAction"] = Field(
        default_factory=list, description="Sub-actions within this action"
    )


class PlanDefinition(BaseResource):
    """
    Represents a plan definition for clinical protocols, order sets, and decision support rules.

    Based on FHIR R5 PlanDefinition with HACS enhancements for healthcare agents.
    Supports complex clinical workflows, decision support rules, and care protocols.
    """

    resource_type: Literal["PlanDefinition"] = Field(
        default="PlanDefinition", description="Resource type identifier"
    )

    # Basic metadata
    url: str | None = Field(
        default=None, description="Canonical identifier for this plan definition"
    )

    identifier: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Additional identifier for the plan definition",
    )

    version: str | None = Field(
        default=None, description="Business version of the plan definition"
    )

    name: str | None = Field(
        default=None, description="Computer-friendly name for the plan definition"
    )

    title: str | None = Field(
        default=None, description="Human-friendly title for the plan definition"
    )

    subtitle: str | None = Field(
        default=None, description="Subordinate title for the plan definition"
    )

    status: PlanDefinitionStatus = Field(
        default=PlanDefinitionStatus.DRAFT,
        description="Current status of the plan definition",
    )

    experimental: bool = Field(
        default=False, description="For testing purposes, not real usage"
    )

    type_coding: dict[str, Any] | None = Field(
        default=None,
        description="Type of plan definition (order-set, clinical-protocol, etc.)",
    )

    # LLM-FRIENDLY: Simple type alternative
    plan_type: PlanDefinitionType | None = Field(
        default=None, description="Simple type classification for the plan definition"
    )

    subject_codeable_concept: dict[str, Any] | None = Field(
        default=None, description="Type of individual the plan definition is focused on"
    )

    subject_reference: str | None = Field(
        default=None, description="Individual the plan definition is focused on"
    )

    subject_canonical: str | None = Field(
        default=None, description="Canonical reference to subject"
    )

    # Dates
    date: datetime | None = Field(default=None, description="Date last changed")

    # Publishing information
    publisher: str | None = Field(default=None, description="Name of the publisher")

    contact: list[dict[str, Any]] = Field(
        default_factory=list, description="Contact details for the publisher"
    )

    description: str | None = Field(
        default=None, description="Natural language description of the plan definition"
    )

    use_context: list[dict[str, Any]] = Field(
        default_factory=list, description="Context the content is intended to support"
    )

    jurisdiction: list[dict[str, Any]] = Field(
        default_factory=list, description="Intended jurisdiction for plan definition"
    )

    purpose: str | None = Field(
        default=None, description="Why this plan definition is defined"
    )

    usage: str | None = Field(
        default=None, description="Describes the clinical usage of the plan definition"
    )

    copyright: str | None = Field(
        default=None, description="Use and/or publishing restrictions"
    )

    copyright_label: str | None = Field(
        default=None, description="Copyright holder and year(s)"
    )

    approval_date: datetime | None = Field(
        default=None, description="When the plan definition was approved by publisher"
    )

    last_review_date: datetime | None = Field(
        default=None, description="When the plan definition was last reviewed"
    )

    effective_period: dict[str, Any] | None = Field(
        default=None, description="When the plan definition is expected to be used"
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
        default_factory=list, description="Logic libraries used by this plan definition"
    )

    # Goals
    goal: list[dict[str, Any]] = Field(
        default_factory=list, description="What the plan is trying to accomplish"
    )

    # Actions - the core of the plan definition
    action: list[PlanDefinitionAction] = Field(
        default_factory=list, description="Action defined by the plan"
    )

    # HACS-specific enhancements
    agent_context: dict[str, Any] = Field(
        default_factory=dict, description="Agent-specific context and configuration"
    )

    execution_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata about plan execution and performance",
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "id": "hypertension-protocol-001",
                    "resource_type": "PlanDefinition",
                    "title": "Hypertension Management Protocol",
                    "status": "active",
                    "plan_type": "clinical-protocol",
                    "description": "Evidence-based protocol for managing hypertension in primary care",
                    "action": [
                        {
                            "title": "Initial Assessment",
                            "description": "Perform initial hypertension assessment",
                            "required_behavior": "must",
                        },
                        {
                            "title": "Lifestyle Counseling",
                            "description": "Provide lifestyle modification counseling",
                            "required_behavior": "could",
                        },
                    ],
                }
            ]
        }


# Update the forward reference
PlanDefinitionAction.model_rebuild()
