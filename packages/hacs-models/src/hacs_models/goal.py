"""
Goal model for HACS (comprehensive).

HACS-native, FHIR-inspired Goal representing intended objectives for patients,
groups, or organizations. Optimized for LLM context engineering with rich
descriptive metadata and care planning workflow support.
"""

from datetime import date
from typing import Any, Literal

from pydantic import Field

from .base_resource import DomainResource
from .types import GoalLifecycleStatus


class GoalTarget(DomainResource):
    """Target outcome for the goal."""

    resource_type: Literal["GoalTarget"] = Field(default="GoalTarget")

    measure: dict[str, Any] | None = Field(
        default=None,
        description="The parameter whose value is being tracked",
        examples=[
            {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "33747-0",
                        "display": "General appearance finding",
                    }
                ]
            }
        ],
    )

    detail_quantity: dict[str, Any] | None = Field(
        default=None,
        description="Target value to be achieved as a quantity",
        examples=[
            {"value": 140, "unit": "mmHg", "system": "http://unitsofmeasure.org", "code": "mm[Hg]"}
        ],
    )

    detail_range: dict[str, Any] | None = Field(
        default=None,
        description="Target value to be achieved as a range",
        examples=[{"low": {"value": 120, "unit": "mmHg"}, "high": {"value": 140, "unit": "mmHg"}}],
    )

    detail_codeable_concept: dict[str, Any] | None = Field(
        default=None,
        description="Target value to be achieved as a coded concept",
        examples=[
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "182840001",
                        "display": "Drug treatment stopped",
                    }
                ]
            }
        ],
    )

    detail_string: str | None = Field(
        default=None,
        description="Target value to be achieved as a string",
        examples=["Complete independence in activities of daily living"],
    )

    detail_boolean: bool | None = Field(
        default=None, description="Target value to be achieved as a boolean"
    )

    detail_integer: int | None = Field(
        default=None, description="Target value to be achieved as an integer"
    )

    detail_ratio: dict[str, Any] | None = Field(
        default=None, description="Target value to be achieved as a ratio"
    )

    due_date: date | None = Field(default=None, description="Reach goal on or before this date")

    due_duration: dict[str, Any] | None = Field(
        default=None,
        description="Reach goal within this duration",
        examples=[
            {"value": 30, "unit": "days", "system": "http://unitsofmeasure.org", "code": "d"}
        ],
    )


class Goal(DomainResource):
    """
    Describes intended objectives for a patient, group, or organization.

    Goals describe the intended objectives for patients, groups, or organizations
    that are being tracked and measured as part of care planning and management.
    Optimized for LLM context engineering withFHIR-aligned metadata.

    Key Features:
        -lifecycle status tracking
        - Measurable target outcomes with deadlines
        - Category and priority classification
        - Achievement status and progress tracking
        - Care team and subject association

    Example Use Cases:
        - Care plan goals and objectives
        - Clinical quality measures
        - Patient self-management goals
        - Population health targets
        - Quality improvement initiatives
    """

    resource_type: Literal["Goal"] = Field(default="Goal")

    # Identifiers
    identifier: list[dict[str, Any]] = Field(
        default_factory=list,
        description="External identifiers for this goal",
        examples=[[{"system": "http://hospital.example.org/goal-ids", "value": "GOAL-12345"}]],
    )

    # Status and lifecycle
    lifecycle_status: GoalLifecycleStatus = Field(
        default=GoalLifecycleStatus.PROPOSED,
        description="Proposed | planned | accepted | active | on-hold | completed | cancelled | entered-in-error | rejected",
    )

    achievement_status: dict[str, Any] | None = Field(
        default=None,
        description="Indicates whether the goal has been reached and is still being targeted",
        examples=[
            {
                "coding": [
                    {"system": "goal-achievement", "code": "in-progress", "display": "In Progress"}
                ]
            }
        ],
    )

    # Classification
    category: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Category of the goal (dietary, safety, behavioral, etc.)",
        examples=[
            [{"coding": [{"system": "goal-category", "code": "dietary", "display": "Dietary"}]}]
        ],
    )

    priority: dict[str, Any] | None = Field(
        default=None,
        description="Priority of the goal (high, medium, low)",
        examples=[
            {
                "coding": [
                    {"system": "goal-priority", "code": "high-priority", "display": "High Priority"}
                ]
            }
        ],
    )

    # Description and details
    description: dict[str, Any] = Field(
        description="Code or text describing goal",
        examples=[{"text": "Target weight is 160 to 180 lbs."}],
    )

    # Subject and context
    subject: str = Field(
        description="Who this goal is intended for (Patient, Group, Organization)",
        examples=["Patient/patient-123", "Group/diabetes-patients"],
    )

    start_date: date | None = Field(default=None, description="When goal pursuit begins")

    start_codeable_concept: dict[str, Any] | None = Field(
        default=None,
        description="When goal pursuit begins (coded)",
        examples=[
            {
                "coding": [
                    {
                        "system": "goal-start-event",
                        "code": "discharge",
                        "display": "After discharge",
                    }
                ]
            }
        ],
    )

    # Targets and outcomes
    target: list[GoalTarget] = Field(
        default_factory=list, description="Target outcome for the goal"
    )

    status_date: date | None = Field(default=None, description="When goal status took effect")

    status_reason: str | None = Field(
        default=None,
        description="Reason for current status",
        examples=["Patient not motivated", "Clinical improvement achieved"],
    )

    # Source and ownership
    expressed_by: str | None = Field(
        default=None,
        description="Who's responsible for creating Goal",
        examples=["Patient/patient-123", "Practitioner/dr-smith"],
    )

    addresses: list[str] = Field(
        default_factory=list,
        description="Issues addressed by this goal",
        examples=[["Condition/diabetes", "Observation/high-blood-pressure"]],
    )

    note: list[str] = Field(
        default_factory=list,
        description="Comments about the goal",
        examples=[
            ["Patient expressed strong motivation to achieve this goal", "Requires family support"]
        ],
    )

    outcome_code: list[dict[str, Any]] = Field(
        default_factory=list,
        description="What result was achieved regarding the goal",
        examples=[
            [
                {
                    "coding": [
                        {"system": "goal-outcome", "code": "achieved", "display": "Goal achieved"}
                    ]
                }
            ]
        ],
    )

    outcome_reference: list[str] = Field(
        default_factory=list,
        description="Observation that resulted from goal",
        examples=[["Observation/weight-measurement", "DiagnosticReport/lab-results"]],
    )

    def add_target(
        self,
        measure: dict[str, Any] | None = None,
        detail: Any = None,
        due_date: date | None = None,
    ) -> GoalTarget:
        """Add a target outcome for this goal."""
        target = GoalTarget(measure=measure, due_date=due_date)

        # Set the appropriate detail field based on type
        if isinstance(detail, str):
            target.detail_string = detail
        elif isinstance(detail, bool):
            target.detail_boolean = detail
        elif isinstance(detail, int):
            target.detail_integer = detail
        elif isinstance(detail, dict):
            if "value" in detail and "unit" in detail:
                target.detail_quantity = detail
            elif "low" in detail or "high" in detail:
                target.detail_range = detail
            elif "coding" in detail:
                target.detail_codeable_concept = detail
            else:
                target.detail_ratio = detail

        self.target.append(target)
        self.update_timestamp()
        return target

    def add_note(self, note: str) -> None:
        """Add a note about this goal."""
        if note.strip():
            self.note.append(note.strip())
            self.update_timestamp()

    def set_status(self, status: GoalLifecycleStatus, reason: str | None = None) -> None:
        """Update the lifecycle status of the goal."""
        self.lifecycle_status = status
        self.status_date = date.today()
        if reason:
            self.status_reason = reason
        self.update_timestamp()

    def mark_completed(self, completion_note: str | None = None) -> None:
        """Mark the goal as completed."""
        self.set_status(GoalLifecycleStatus.COMPLETED, completion_note)
        if completion_note:
            self.add_note(f"Completed: {completion_note}")

    def mark_cancelled(self, reason: str | None = None) -> None:
        """Mark the goal as cancelled."""
        self.set_status(GoalLifecycleStatus.CANCELLED, reason)
        if reason:
            self.add_note(f"Cancelled: {reason}")

    def add_outcome(self, outcome_ref: str, outcome_code: dict[str, Any] | None = None) -> None:
        """Add an outcome observation for this goal."""
        self.outcome_reference.append(outcome_ref)
        if outcome_code:
            self.outcome_code.append(outcome_code)
        self.update_timestamp()

    def is_active(self) -> bool:
        """Check if the goal is currently active."""
        return self.lifecycle_status in [GoalLifecycleStatus.ACCEPTED, GoalLifecycleStatus.ACTIVE]

    def is_completed(self) -> bool:
        """Check if the goal has been completed."""
        return self.lifecycle_status == GoalLifecycleStatus.COMPLETED

    def get_display_text(self) -> str:
        """Get human-readable display text for the goal."""
        if isinstance(self.description, dict):
            if "text" in self.description:
                return self.description["text"]
            elif "coding" in self.description and len(self.description["coding"]) > 0:
                return self.description["coding"][0].get("display", "Unknown goal")
        elif isinstance(self.description, str):
            return self.description
        return "Unknown goal"

    def __str__(self) -> str:
        """Human-readable string representation."""
        goal_text = self.get_display_text()
        status_str = f" ({self.lifecycle_status})" if self.lifecycle_status else ""
        return f"Goal('{goal_text}'{status_str})"

    # --- LLM-friendly extractable facade overrides ---
    @classmethod
    def get_extractable_fields(cls) -> list[str]:  # type: ignore[override]
        """Return fields that should be extracted by LLMs (3-4 key fields only)."""
        return [
            "lifecycle_status",
            "description",
            "target",
            "start_date",
        ]

    @classmethod
    def get_required_extractables(cls) -> list[str]:
        """Fields that must be provided for valid extraction."""
        return ["description"]

    @classmethod
    def get_canonical_defaults(cls) -> dict[str, Any]:
        """Default values for system/required fields during extraction."""
        return {
            "lifecycle_status": "active",
            "subject": "Patient/UNKNOWN",
            "description": {"text": ""},  # Will be filled by LLM
        }

    @classmethod
    def coerce_extractable(cls, payload: dict[str, Any], relax: bool = True) -> dict[str, Any]:
        """Coerce extractable payload to proper types with relaxed validation."""
        coerced = payload.copy()

        # Coerce description to CodeableConcept if it's a string
        if "description" in coerced and isinstance(coerced["description"], str):
            coerced["description"] = {"text": coerced["description"]}

        # Coerce target to list if it's a single dict
        if "target" in coerced and isinstance(coerced["target"], dict):
            coerced["target"] = [coerced["target"]]

        return coerced

    @classmethod
    def get_extraction_examples(cls) -> dict[str, Any]:
        """Return extraction examples showing different extractable field scenarios."""
        # Weight loss goal with target
        weight_loss_example = {
            "lifecycle_status": "active",
            "description": {"text": "perder peso"},
            "target": [{"measure": {"text": "peso corporal"}, "detail_quantity": {"value": 80, "unit": "kg"}}],
            "start_date": "2024-08-15",
        }

        # Blood pressure control goal
        bp_example = {
            "lifecycle_status": "active",
            "description": {"text": "controlar pressão arterial"},
            "target": [{"measure": {"text": "pressão arterial"}, "detail_string": "abaixo de 130/80"}],
        }

        # Simple goal without measurable target
        simple_example = {
            "lifecycle_status": "proposed",
            "description": {"text": "melhorar qualidade do sono"},
            "start_date": "2024-09-01",
        }

        return {
            "object": weight_loss_example,
            "array": [weight_loss_example, bp_example, simple_example],
            "scenarios": {
                "weight_loss": weight_loss_example,
                "blood_pressure": bp_example,
                "simple": simple_example,
            }
        }

    @classmethod
    def llm_hints(cls) -> list[str]:  # type: ignore[override]
        """Provide LLM-specific extraction hints."""
        return [
            "Extract goal description (what the patient wants to achieve)",
            "Include target outcomes with measurable values when mentioned",
            "Capture start date or timeline when specified",
            "Status should be: proposed, accepted, active, completed, or cancelled"
        ]
