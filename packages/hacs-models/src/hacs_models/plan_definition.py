"""
PlanDefinition model for HACS (comprehensive).

HACS-native, FHIR-inspired PlanDefinition representing pre-defined sets of actions
for clinical protocols, decision support rules, and care workflows.
Optimized for LLM context engineering with rich descriptive metadata.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from .base_resource import DomainResource


class PlanDefinitionGoal(DomainResource):
    """Goal described by the plan definition."""

    resource_type: Literal["PlanDefinitionGoal"] = Field(default="PlanDefinitionGoal")

    category: str | None = Field(
        default=None,
        description="Category of the goal (e.g., treatment, dietary, safety)",
        examples=["treatment", "dietary", "safety", "behavioral"],
    )

    description: str = Field(
        description="Human-readable description of the goal",
        examples=["Reduce blood pressure to <140/90 mmHg", "Maintain HbA1c <7%"],
    )

    priority: str | None = Field(
        default=None,
        description="Priority of the goal (high, medium, low)",
        examples=["high", "medium", "low"],
    )

    start: str | None = Field(
        default=None,
        description="When the goal should start being pursued",
        examples=["immediately", "after-diagnosis", "day-3"],
    )

    addresses: list[str] = Field(
        default_factory=list,
        description="Conditions or issues this goal addresses",
        examples=[["Condition/hypertension", "Condition/diabetes"]],
    )

    documentation: list[str] = Field(
        default_factory=list,
        description="Supporting documentation for the goal",
        examples=[["Evidence shows target BP reduces cardiovascular risk"]],
    )

    target: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Target outcome for the goal",
        examples=[
            [
                {
                    "measure": "systolic-bp",
                    "detail": {"value": 140, "unit": "mmHg", "comparator": "<"},
                }
            ]
        ],
    )

    # --- LLM-friendly extractable facade overrides ---
    @classmethod
    def get_extractable_fields(cls) -> list[str]:  # type: ignore[override]
        """Return fields that should be extracted by LLMs (3-4 key fields only)."""
        return [
            "category",
            "description",
            "priority",
            "target",
        ]

    @classmethod
    def get_canonical_defaults(cls) -> dict[str, Any]:
        return {"priority": "medium"}

    @classmethod
    def llm_hints(cls) -> list[str]:  # type: ignore[override]
        return [
            "Provide a concise goal description",
            "Include measurable target(s) when available",
            "Use simple categories like treatment/dietary/safety",
        ]


class PlanDefinitionAction(DomainResource):
    """Action defined by the plan definition."""

    resource_type: Literal["PlanDefinitionAction"] = Field(default="PlanDefinitionAction")

    prefix: str | None = Field(
        default=None,
        description="User-visible prefix for the action (e.g., Step 1)",
        examples=["Step 1", "A.", "Initial"],
    )

    title: str | None = Field(
        default=None,
        description="User-visible title for the action",
        examples=["Assess Blood Pressure", "Order Laboratory Tests", "Prescribe Medication"],
    )

    description: str | None = Field(
        default=None, description="Brief description of the action", max_length=1000
    )

    text_equivalent: str | None = Field(
        default=None,
        description="Text equivalent of the action",
        examples=["Measure blood pressure using appropriate cuff size"],
    )

    priority: str | None = Field(
        default=None,
        description="Priority of the action (routine, urgent, asap, stat)",
        examples=["routine", "urgent", "asap", "stat"],
    )

    code: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Code/identifier for the action",
        examples=[
            [
                {
                    "system": "http://snomed.info/sct",
                    "code": "271649006",
                    "display": "Systolic blood pressure",
                }
            ]
        ],
    )

    reason: list[str] = Field(
        default_factory=list,
        description="Why the action should be performed",
        examples=[["Patient has hypertension", "Baseline assessment required"]],
    )

    documentation: list[str] = Field(
        default_factory=list,
        description="Guideline or documentation for the action",
        examples=[["NICE Hypertension Guideline"], ["AHA BP Measurement Protocol"]],
    )

    timing_timing: dict[str, Any] | None = Field(
        default=None,
        description="When the action should happen",
        examples=[{"event": ["2024-01-01T09:00:00Z"]}],
    )

    participant: list[str] = Field(
        default_factory=list,
        description="Who should perform the action",
        examples=[["Practitioner/cardiologist-1"], ["Organization/lab-123"]],
    )

    type: str | None = Field(default=None, description="create | update | remove | fire-event")

    group_behavior: str | None = Field(
        default=None,
        description="all | any | all-or-none | exactly-one | at-most-one | one-or-more",
    )

    selection_behavior: str | None = Field(
        default=None,
        description="any | all | all-or-none | exactly-one | at-most-one | one-or-more",
    )

    required_behavior: str | None = Field(
        default=None,
        description="must | could | must-unless-documented",
    )

    precheck_behavior: str | None = Field(
        default=None,
        description="yes | no",
    )

    cardinality_behavior: str | None = Field(
        default=None,
        description="single | multiple",
    )

    transform: str | None = Field(
        default=None,
        description="Transform to apply to the resource",
        examples=["http://example.org/fhir/StructureMap/patient-summary"],
    )

    dynamic_value: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Dynamic values for the action",
        examples=[[{"path": "dosage.dose", "expression": "patient.weight * 0.1"}]],
    )

    action: list["PlanDefinitionAction"] = Field(
        default_factory=list, description="Sub-actions that are part of this action"
    )

    # --- LLM-friendly extractable facade overrides ---
    @classmethod
    def get_extractable_fields(cls) -> list[str]:  # type: ignore[override]
        """Return fields that should be extracted by LLMs (3-4 key fields only)."""
        return [
            "title",
            "description",
            "code",
            "timing_timing",
        ]

    @classmethod
    def get_canonical_defaults(cls) -> dict[str, Any]:
        return {"priority": "routine"}

    @classmethod
    def llm_hints(cls) -> list[str]:  # type: ignore[override]
        return [
            "Prefer short action titles",
            "Include succinct descriptions for clarity",
            "Map to a simple code when obvious (SNOMED/LOINC text ok)",
            "Include when to perform the action if specified",
        ]


class PlanDefinition(DomainResource):
    """
    Definition of a plan for a series of actions.

    Represents pre-defined sets of actions for clinical protocols, decision support rules,
    order sets, and other healthcare workflows. Optimized for LLM context engineering
    withFHIR-aligned metadata and descriptive information.

    Key Features:
        - Rich metadata for LLM context understanding
        - Hierarchical action structures with dependencies
        - Goal-driven planning with measurable targets
        - Flexible triggering and conditional logic
        - Support for various clinical domains and use cases

    Example Use Cases:
        - Clinical practice guidelines
        - Order sets and protocols
        - Decision support rules
        - Care pathways and workflows
        - Quality measures and indicators
    """

    resource_type: Literal["PlanDefinition"] = Field(default="PlanDefinition")

    url: str | None = Field(default=None, description="Canonical URL for this plan definition")
    identifier: list[str] = Field(default_factory=list, description="Identifiers for this plan")
    version: str | None = Field(default=None, description="Business version of the plan")
    name: str | None = Field(default=None, description="Computer-friendly name")
    title: str | None = Field(default=None, description="Human-readable name")
    subtitle: str | None = Field(default=None, description="Subordinate title of the plan")

    status: str = Field(
        default="draft",
        description="Publication status (draft, active, retired, unknown)",
    )

    experimental: bool | None = Field(default=None, description="For testing purposes, not real usage")
    date: datetime | None = Field(default=None, description="Date last changed")
    publisher: str | None = Field(default=None, description="Name of the publisher")
    contact: list[str] = Field(default_factory=list, description="Contact details for the publisher")

    description: str | None = Field(default=None, description="Natural language description")
    purpose: str | None = Field(
        default=None,
        description="Why this plan definition is defined",
    )

    use_context: list[str] = Field(default_factory=list, description="Context the content is intended for")
    jurisdiction: list[str] = Field(default_factory=list, description="Intended jurisdiction")
    copyright: str | None = Field(default=None, description="Use and/or publishing restrictions")

    approval_date: datetime | None = Field(default=None, description="When the plan was approved")
    last_review_date: datetime | None = Field(default=None, description="When the plan was last reviewed")
    effective_period: dict[str, Any] | None = Field(default=None, description="When the plan is effective")

    topic: list[str] = Field(default_factory=list, description="E.g., Education, Treatment, Assessment, etc.")

    author: list[str] = Field(default_factory=list, description="Who authored the content")
    editor: list[str] = Field(default_factory=list, description="Who edited the content")
    reviewer: list[str] = Field(default_factory=list, description="Who reviewed the content")
    endorser: list[str] = Field(default_factory=list, description="Who endorsed the content")

    related_artifact: list[str] = Field(default_factory=list, description="Additional documentation, citations")

    library: list[str] = Field(default_factory=list, description="Logic used by the plan definition")

    goal: list[PlanDefinitionGoal] = Field(default_factory=list, description="What the plan is trying to accomplish")
    action: list[PlanDefinitionAction] = Field(default_factory=list, description="Action defined by the plan")

    def add_goal(self, description: str, category: str | None = None, priority: str | None = None) -> PlanDefinitionGoal:
        goal = PlanDefinitionGoal(description=description, category=category, priority=priority)
        self.goal.append(goal)
        self.update_timestamp()
        return goal

    def add_action(self, title: str, description: str | None = None, priority: str | None = None) -> PlanDefinitionAction:
        action = PlanDefinitionAction(title=title, description=description, priority=priority)
        self.action.append(action)
        self.update_timestamp()
        return action

    def get_action_by_title(self, title: str) -> PlanDefinitionAction | None:
        """Get an action by its title."""
        for action in self.action:
            if action.title == title:
                return action
        return None

    def get_goals_by_category(self, category: str) -> list[PlanDefinitionGoal]:
        """Get all goals with a specific category."""
        return [goal for goal in self.goal if goal.category == category]

    def __str__(self) -> str:
        """Human-readable string representation."""
        title_str = self.title or self.name or "Unnamed Plan"
        goal_count = len(self.goal)
        action_count = len(self.action)
        return f"PlanDefinition('{title_str}', {goal_count} goals, {action_count} actions)"

    # --- LLM-friendly extractable facade overrides ---
    @classmethod
    def get_extractable_fields(cls) -> list[str]:  # type: ignore[override]
        """Return fields that should be extracted by LLMs (3-4 key fields only)."""
        return [
            "status",
            "title",
            "description",
            "purpose",
        ]

    @classmethod
    def get_canonical_defaults(cls) -> dict[str, Any]:
        return {"status": "draft"}

    @classmethod
    def llm_hints(cls) -> list[str]:  # type: ignore[override]
        return [
            "Extract a short human-readable title",
            "Summarize the purpose in one sentence when present",
            "Use 'draft' status unless explicitly stated otherwise",
        ]
