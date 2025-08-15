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
        examples=["treatment", "dietary", "safety", "behavioral"]
    )
    
    description: str = Field(
        description="Human-readable description of the goal",
        examples=["Reduce blood pressure to <140/90 mmHg", "Maintain HbA1c <7%"]
    )
    
    priority: str | None = Field(
        default=None,
        description="Priority of the goal (high, medium, low)",
        examples=["high", "medium", "low"]
    )
    
    start: str | None = Field(
        default=None,
        description="When the goal should start being pursued",
        examples=["immediately", "after-diagnosis", "day-3"]
    )
    
    addresses: list[str] = Field(
        default_factory=list,
        description="Conditions or issues this goal addresses",
        examples=[["Condition/hypertension", "Condition/diabetes"]]
    )
    
    documentation: list[str] = Field(
        default_factory=list,
        description="Supporting documentation for the goal",
        examples=[["Evidence shows target BP reduces cardiovascular risk"]]
    )
    
    target: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Target outcome for the goal",
        examples=[[{"measure": "systolic-bp", "detail": {"value": 140, "unit": "mmHg", "comparator": "<"}}]]
    )


class PlanDefinitionAction(DomainResource):
    """Action defined by the plan definition."""
    
    resource_type: Literal["PlanDefinitionAction"] = Field(default="PlanDefinitionAction")
    
    prefix: str | None = Field(
        default=None,
        description="User-visible prefix for the action (e.g., Step 1)",
        examples=["Step 1", "A.", "Initial"]
    )
    
    title: str | None = Field(
        default=None,
        description="User-visible title for the action",
        examples=["Assess Blood Pressure", "Order Laboratory Tests", "Prescribe Medication"]
    )
    
    description: str | None = Field(
        default=None,
        description="Brief description of the action",
        max_length=1000
    )
    
    text_equivalent: str | None = Field(
        default=None,
        description="Text equivalent of the action",
        examples=["Measure blood pressure using appropriate cuff size"]
    )
    
    priority: str | None = Field(
        default=None,
        description="Priority of the action (routine, urgent, asap, stat)",
        examples=["routine", "urgent", "asap", "stat"]
    )
    
    code: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Code/identifier for the action",
        examples=[[{"system": "http://snomed.info/sct", "code": "271649006", "display": "Systolic blood pressure"}]]
    )
    
    reason: list[str] = Field(
        default_factory=list,
        description="Why the action should be performed",
        examples=[["Patient has hypertension", "Baseline assessment required"]]
    )
    
    documentation: list[str] = Field(
        default_factory=list,
        description="Supporting documentation for the action",
        examples=[["AHA/ACC 2017 Guidelines recommend regular monitoring"]]
    )
    
    goal_id: list[str] = Field(
        default_factory=list,
        description="Goals that this action supports",
        examples=[["goal-1", "goal-blood-pressure"]]
    )
    
    trigger: list[dict[str, Any]] = Field(
        default_factory=list,
        description="When the action should be triggered",
        examples=[[{"type": "periodic", "name": "daily-assessment"}]]
    )
    
    condition: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Conditions that apply to the action",
        examples=[[{"kind": "applicability", "expression": "systolic_bp > 140"}]]
    )
    
    input: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Input data requirements",
        examples=[[{"type": "Patient", "profile": "blood-pressure-capable"}]]
    )
    
    output: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Output data definition",
        examples=[[{"type": "Observation", "profile": "blood-pressure-measurement"}]]
    )
    
    related_action: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Relationship to other actions",
        examples=[[{"action_id": "assess-bp", "relationship": "before"}]]
    )
    
    timing: dict[str, Any] | None = Field(
        default=None,
        description="When the action should occur",
        examples=[{"repeat": {"frequency": 1, "period": 1, "period_unit": "d"}}]
    )
    
    participant: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Who should participate in the action",
        examples=[[{"type": "practitioner", "role": "primary-care-physician"}]]
    )
    
    type_: str | None = Field(
        default=None,
        alias="type",
        description="Type of action (create, update, remove, fire-event)",
        examples=["create", "update", "remove", "fire-event"]
    )
    
    grouping_behavior: str | None = Field(
        default=None,
        description="Defines the grouping behavior for the action",
        examples=["visual-group", "logical-group", "sentence-group"]
    )
    
    selection_behavior: str | None = Field(
        default=None,
        description="Defines the selection behavior for the action",
        examples=["any", "all", "all-or-none", "exactly-one", "at-most-one", "one-or-more"]
    )
    
    required_behavior: str | None = Field(
        default=None,
        description="Defines the required behavior for the action",
        examples=["must", "could", "must-unless-documented"]
    )
    
    precheck_behavior: str | None = Field(
        default=None,
        description="Defines whether the action should be preselected",
        examples=["yes", "no"]
    )
    
    cardinality_behavior: str | None = Field(
        default=None,
        description="Defines whether the action can be selected multiple times",
        examples=["single", "multiple"]
    )
    
    definition_canonical: str | None = Field(
        default=None,
        description="Description of the activity to be performed",
        examples=["http://example.org/fhir/ActivityDefinition/blood-pressure-measurement"]
    )
    
    transform: str | None = Field(
        default=None,
        description="Transform to apply to the resource",
        examples=["http://example.org/fhir/StructureMap/patient-summary"]
    )
    
    dynamic_value: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Dynamic values for the action",
        examples=[[{"path": "dosage.dose", "expression": "patient.weight * 0.1"}]]
    )
    
    action: list["PlanDefinitionAction"] = Field(
        default_factory=list,
        description="Sub-actions that are part of this action"
    )


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
    
    # Identifiers and metadata
    url: str | None = Field(
        default=None,
        description="Canonical identifier for this plan definition",
        examples=["http://example.org/fhir/PlanDefinition/hypertension-management"]
    )
    
    identifier: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Additional identifier for the plan definition",
        examples=[[{"system": "http://example.org/plan-ids", "value": "HTN-MGMT-2024"}]]
    )
    
    version: str = Field(
        default="1.0.0",
        description="Business version of the plan definition",
        examples=["1.0.0", "2.1.5", "draft"]
    )
    
    name: str | None = Field(
        default=None,
        description="Name for this plan definition (computer friendly)",
        examples=["HypertensionManagement", "DiabetesCarePlan", "PreOpProtocol"]
    )
    
    title: str | None = Field(
        default=None,
        description="Human-friendly title of the plan definition",
        examples=["Hypertension Management Protocol", "Adult Diabetes Care Plan", "Pre-Operative Assessment"]
    )
    
    subtitle: str | None = Field(
        default=None,
        description="Subordinate title for the plan definition",
        examples=["Primary Care Protocol", "Evidence-Based Guidelines"]
    )
    
    # Publication and status
    status: str = Field(
        default="draft",
        description="Publication status (draft, active, retired, unknown)",
        examples=["draft", "active", "retired", "unknown"]
    )
    
    experimental: bool = Field(
        default=False,
        description="Whether this plan definition is for testing purposes"
    )
    
    date: datetime | None = Field(
        default=None,
        description="Date last changed"
    )
    
    publisher: str | None = Field(
        default=None,
        description="Name of the publisher (organization or individual)",
        examples=["American Heart Association", "Mayo Clinic", "NHS England"]
    )
    
    contact: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Contact details for the publisher",
        examples=[[{"name": "Clinical Guidelines Team", "telecom": [{"system": "email", "value": "guidelines@example.org"}]}]]
    )
    
    # Content and purpose
    description: str | None = Field(
        default=None,
        description="Natural language description of the plan definition",
        examples=["Evidence-based protocol for management of hypertension in primary care settings"]
    )
    
    use_context: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Context the content is intended to support",
        examples=[[{"code": {"system": "usage-context-type", "code": "venue"}, "valueCodeableConcept": {"text": "primary care"}}]]
    )
    
    jurisdiction: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Intended jurisdiction for plan definition",
        examples=[[{"coding": [{"system": "urn:iso:std:iso:3166", "code": "US", "display": "United States"}]}]]
    )
    
    purpose: str | None = Field(
        default=None,
        description="Why this plan definition is defined",
        examples=["Standardize hypertension care across primary care practices"]
    )
    
    usage: str | None = Field(
        default=None,
        description="Describes the clinical usage of the plan definition",
        examples=["Use for all adult patients with newly diagnosed hypertension"]
    )
    
    copyright: str | None = Field(
        default=None,
        description="Use and/or publishing restrictions"
    )
    
    approval_date: datetime | None = Field(
        default=None,
        description="When the plan definition was approved by publisher"
    )
    
    last_review_date: datetime | None = Field(
        default=None,
        description="When the plan definition was last reviewed"
    )
    
    effective_period: dict[str, datetime] | None = Field(
        default=None,
        description="When the plan definition is expected to be used",
        examples=[{"start": "2024-01-01T00:00:00Z", "end": "2024-12-31T23:59:59Z"}]
    )
    
    # Clinical content
    topic: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Type of individual the plan definition is focused on",
        examples=[[{"coding": [{"system": "http://snomed.info/sct", "code": "38341003", "display": "Hypertension"}]}]]
    )
    
    author: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Who authored the content",
        examples=[[{"name": "Dr. Jane Smith", "telecom": [{"system": "email", "value": "jane.smith@example.org"}]}]]
    )
    
    editor: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Who edited the content"
    )
    
    reviewer: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Who reviewed the content"
    )
    
    endorser: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Who endorsed the content"
    )
    
    related_artifact: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Additional documentation, citations, etc.",
        examples=[[{"type": "citation", "display": "2017 ACC/AHA Hypertension Guidelines", "url": "https://example.org/guidelines"}]]
    )
    
    library: list[str] = Field(
        default_factory=list,
        description="Logic libraries used by the plan definition",
        examples=[["Library/hypertension-logic"]]
    )
    
    # Goals and actions
    goal: list[PlanDefinitionGoal] = Field(
        default_factory=list,
        description="Goals that describe what the activities within the plan are intended to achieve"
    )
    
    action: list[PlanDefinitionAction] = Field(
        default_factory=list,
        description="Actions or action groups that comprise the plan definition"
    )
    
    # Plan definition type and subject
    type_: dict[str, Any] | None = Field(
        default=None,
        alias="type",
        description="Type of plan definition (order-set, clinical-protocol, eca-rule, workflow-definition)",
        examples=[{"coding": [{"system": "plan-definition-type", "code": "clinical-protocol"}]}]
    )
    
    subject_codeable_concept: dict[str, Any] | None = Field(
        default=None,
        description="Type of individual the plan is focused on",
        examples=[{"coding": [{"system": "http://hl7.org/fhir/resource-types", "code": "Patient"}]}]
    )
    
    subject_reference: str | None = Field(
        default=None,
        description="Individual the plan is focused on",
        examples=["Group/adult-hypertension-patients"]
    )
    
    def add_goal(self, description: str, category: str | None = None, priority: str | None = None) -> PlanDefinitionGoal:
        """Add a goal to the plan definition."""
        goal = PlanDefinitionGoal(
            description=description,
            category=category,
            priority=priority
        )
        self.goal.append(goal)
        self.update_timestamp()
        return goal
    
    def add_action(self, title: str, description: str | None = None, priority: str | None = None) -> PlanDefinitionAction:
        """Add an action to the plan definition."""
        action = PlanDefinitionAction(
            title=title,
            description=description,
            priority=priority
        )
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
