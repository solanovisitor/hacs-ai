"""
Goal model based on FHIR R5 Goal Resource.

This model represents intended objectives for a patient, group, or organization care,
such as weight loss, restoring activities of daily living, meeting process improvement
objectives, etc. Fully compliant with FHIR R5 specification while optimized for LLM interactions.
"""

from datetime import datetime, date, timezone
from enum import Enum
from typing import Any, Literal, Optional

from ..base_resource import BaseResource
from pydantic import Field, field_validator, model_validator
import uuid


class GoalLifecycleStatus(str, Enum):
    """Lifecycle status of the goal."""

    PROPOSED = "proposed"
    PLANNED = "planned"
    ACCEPTED = "accepted"
    ACTIVE = "active"
    ON_HOLD = "on-hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ENTERED_IN_ERROR = "entered-in-error"
    REJECTED = "rejected"


class GoalAchievementStatus(str, Enum):
    """Achievement status of the goal."""

    IN_PROGRESS = "in-progress"
    IMPROVING = "improving"
    WORSENING = "worsening"
    NO_CHANGE = "no-change"
    ACHIEVED = "achieved"
    SUSTAINING = "sustaining"
    NOT_ACHIEVED = "not-achieved"
    NO_PROGRESS = "no-progress"
    NOT_ATTAINABLE = "not-attainable"


class GoalCategory(str, Enum):
    """Category of the goal."""

    # FHIR standard categories
    TREATMENT = "treatment"
    DIETARY = "dietary"
    SAFETY = "safety"
    BEHAVIORAL = "behavioral"
    NURSING = "nursing"
    PHYSIOTHERAPY = "physiotherapy"

    # Additional LLM-friendly categories
    CLINICAL = "clinical"
    LIFESTYLE = "lifestyle"
    MEDICATION = "medication"
    EXERCISE = "exercise"
    NUTRITION = "nutrition"
    MENTAL_HEALTH = "mental-health"
    SOCIAL = "social"
    EDUCATIONAL = "educational"
    PREVENTIVE = "preventive"
    REHABILITATION = "rehabilitation"
    PAIN_MANAGEMENT = "pain-management"
    SELF_CARE = "self-care"
    COMMUNICATION = "communication"
    FUNCTIONAL = "functional"
    QUALITY_OF_LIFE = "quality-of-life"


class GoalPriority(str, Enum):
    """Priority level of the goal."""

    HIGH_PRIORITY = "high-priority"
    MEDIUM_PRIORITY = "medium-priority"
    LOW_PRIORITY = "low-priority"

    # Additional priority levels
    CRITICAL = "critical"
    URGENT = "urgent"
    ROUTINE = "routine"
    OPTIONAL = "optional"


class GoalTimeframe(str, Enum):
    """Common timeframes for goals."""

    SHORT_TERM = "short-term"  # Days to weeks
    MEDIUM_TERM = "medium-term"  # Weeks to months
    LONG_TERM = "long-term"  # Months to years
    ONGOING = "ongoing"  # Continuous/maintenance
    IMMEDIATE = "immediate"  # Today/this week
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class GoalMeasureType(str, Enum):
    """Types of goal measurements."""

    QUANTITATIVE = "quantitative"  # Numeric values
    QUALITATIVE = "qualitative"  # Descriptive assessments
    BINARY = "binary"  # Yes/No, Achieved/Not achieved
    FREQUENCY = "frequency"  # How often something happens
    DURATION = "duration"  # How long something takes
    SCALE = "scale"  # Rating scales (1-10, etc.)
    PERCENTAGE = "percentage"  # Percent improvement
    BEHAVIORAL = "behavioral"  # Behavior changes
    FUNCTIONAL = "functional"  # Functional improvements


class Goal(BaseResource):
    """
    Represents an intended objective for patient, group, or organization care.

    Based on FHIR R5 Goal Resource with HACS enhancements.
    Fully compliant with FHIR specification while optimized for LLM interactions.

    Can represent:
    - Clinical goals (e.g., blood pressure <140/90, weight loss of 10 lbs)
    - Functional goals (e.g., walk 30 minutes daily, return to work)
    - Behavioral goals (e.g., quit smoking, medication adherence)
    - Quality of life goals (e.g., reduce pain to 3/10, improve sleep)
    """

    resource_type: Literal["Goal"] = Field(
        default="Goal", description="Resource type identifier"
    )

    # ========================================
    # FHIR R5 REQUIRED FIELDS
    # ========================================

    # Lifecycle Status - required in FHIR (1..1)
    lifecycle_status: GoalLifecycleStatus = Field(
        ..., description="Current status of the goal"
    )

    # Description - required in FHIR (1..1)
    description: Optional[dict[str, Any]] = Field(
        None, description="Code or text describing goal"
    )

    # Subject - required in FHIR (1..1)
    subject: Optional[dict[str, Any]] = Field(
        None, description="Who this goal is intended for"
    )

    # ========================================
    # FHIR R5 OPTIONAL FIELDS
    # ========================================

    # Identifiers
    identifier: Optional[list[dict[str, Any]]] = Field(
        None, description="External Ids for this goal"
    )

    # Achievement Status
    achievement_status: Optional[GoalAchievementStatus] = Field(
        None, description="Achievement status of the goal"
    )

    # Category
    category: Optional[list[dict[str, Any]]] = Field(
        None, description="Goal category"
    )

    # Continuous
    continuous: Optional[bool] = Field(
        None, description="After meeting the goal, ongoing activity is needed"
    )

    # Priority
    priority: Optional[dict[str, Any]] = Field(
        None, description="Priority of the goal"
    )

    # Start
    start_date: Optional[datetime] = Field(
        None, description="When goal pursuit begins"
    )

    start_codeable_concept: Optional[dict[str, Any]] = Field(
        None, description="When goal pursuit begins"
    )

    # Target
    target: Optional[list[dict[str, Any]]] = Field(
        None, description="Target outcome for the goal"
    )

    # Status tracking
    status_date: Optional[datetime] = Field(
        None, description="When goal status took effect"
    )

    status_reason: Optional[str] = Field(
        None, description="Reason for current status"
    )

    # Source
    source: Optional[dict[str, Any]] = Field(
        None, description="Who's responsible for creating Goal?"
    )

    # Addresses
    addresses: Optional[list[dict[str, Any]]] = Field(
        None, description="Issues addressed by this goal"
    )

    # Note
    note: Optional[list[dict[str, Any]]] = Field(
        None, description="Comments about the goal"
    )

    # Outcome
    outcome: Optional[list[dict[str, Any]]] = Field(
        None, description="What result was achieved regarding the Goal?"
    )

    # ========================================
    # LLM-FRIENDLY FIELDS (HACS Extensions)
    # ========================================

    # Simple identification
    goal_name: str | None = Field(
        default=None,
        description="Simple, clear name of the goal",
        examples=[
            "Lose 20 pounds",
            "Reduce blood pressure",
            "Walk 30 minutes daily",
            "Quit smoking",
            "Improve diabetes control",
            "Return to work"
        ],
    )

    goal_description: str | None = Field(
        default=None,
        description="Detailed description of what the patient wants to achieve",
        examples=[
            "Patient wants to lose 20 pounds over 6 months through diet and exercise",
            "Reduce blood pressure to below 140/90 mmHg through medication and lifestyle changes",
            "Build endurance to walk 30 minutes daily without shortness of breath"
        ]
    )

    # Simple categorization
    goal_category: GoalCategory | None = Field(
        default=None,
        description="Simple classification of the goal type"
    )

    goal_priority: GoalPriority | None = Field(
        default=None,
        description="How important this goal is"
    )

    # Timing and targets
    goal_timeframe: GoalTimeframe | None = Field(
        default=None,
        description="When the goal should be achieved"
    )

    target_date: date | None = Field(
        default=None,
        description="Specific date when goal should be met"
    )

    target_value: Optional[str] = Field(
        default=None,
        description="Target value in simple format (e.g., '150 lbs')",
        examples=[
            "Weight: 180 lbs",
            "BP: <140/90 mmHg",
            "HbA1c: <7%",
            "Pain level: 3/10 or less",
            "Walk 10,000 steps daily",
            "Medication adherence: 95%"
        ]
    )

    current_value: str | None = Field(
        default=None,
        description="Current baseline value",
        examples=[
            "Weight: 200 lbs",
            "BP: 160/95 mmHg",
            "HbA1c: 8.5%",
            "Pain level: 7/10",
            "Walking: 3,000 steps daily"
        ]
    )

    measurement_method: GoalMeasureType | None = Field(
        default=None,
        description="How progress will be measured"
    )

    # Progress tracking
    progress_description: str | None = Field(
        default=None,
        description="Current progress toward the goal",
        examples=[
            "Lost 5 pounds in first month, on track",
            "Blood pressure improved to 145/88, still working toward target",
            "Can now walk 15 minutes without stopping, building up gradually"
        ]
    )

    percent_complete: int | None = Field(
        default=None,
        description="Percentage of goal completed (0-100)",
        ge=0,
        le=100
    )

    # Action plan
    action_steps: list[str] = Field(
        default_factory=list,
        description="Specific steps to achieve the goal",
        examples=[
            ["Reduce caloric intake by 500 calories/day", "Exercise 30 minutes 5x/week", "Weigh daily"],
            ["Take medication as prescribed", "Reduce sodium intake", "Monitor BP twice weekly"],
            ["Start with 10-minute walks", "Increase by 5 minutes weekly", "Use pedometer to track"]
        ]
    )

    success_criteria: Optional[list[str]] = Field(
        None, description="What defines success for this goal"
    )

    # Challenges and support
    barriers: Optional[list[str]] = Field(
        None, description="Potential barriers to achieving this goal"
    )

    support_needed: list[str] = Field(
        default_factory=list,
        description="Support needed to achieve the goal",
        examples=[
            ["Nutritionist consultation", "Gym membership", "Family support"],
            ["Medication monitoring", "Dietitian referral", "Stress management"],
            ["Physical therapy", "Walking group", "Exercise equipment"]
        ]
    )

    # Motivation and engagement
    patient_motivation: str | None = Field(
        default=None,
        description="Patient's motivation for this goal",
        examples=[
            "Wants to be healthy for grandchildren",
            "Tired of feeling tired all the time",
            "Doctor said it's necessary to avoid complications",
            "Wants to get back to activities I enjoy"
        ]
    )

    importance_to_patient: int | None = Field(
        default=None,
        description="How important this goal is to the patient (1-10 scale)",
        ge=1,
        le=10
    )

    confidence_level: int | None = Field(
        default=None,
        description="Patient's confidence in achieving this goal (1-10 scale)",
        ge=1,
        le=10
    )

    # Healthcare team involvement
    responsible_provider: str | None = Field(
        default=None,
        description="Healthcare provider overseeing this goal",
        examples=["Dr. Smith, MD", "Sarah Johnson, RN", "Physical Therapy Team"]
    )

    team_members: list[str] = Field(
        default_factory=list,
        description="Healthcare team members involved in achieving this goal",
        examples=[
            ["Primary care physician", "Nutritionist", "Exercise physiologist"],
            ["Cardiologist", "Pharmacist", "Dietitian"],
            ["Physical therapist", "Occupational therapist", "Social worker"]
        ]
    )

    # Review and monitoring
    review_frequency: str | None = Field(
        default=None,
        description="How often progress will be reviewed",
        examples=["Weekly", "Bi-weekly", "Monthly", "Quarterly", "As needed"]
    )

    monitoring_method: list[str] = Field(
        default_factory=list,
        description="How progress will be monitored",
        examples=[
            ["Daily weight checks", "Weekly visits", "Food diary"],
            ["Home BP monitoring", "Monthly lab work", "Medication adherence tracking"],
            ["Activity tracker", "Pain diary", "Functional assessments"]
        ]
    )

    # Related information
    related_conditions: list[str] = Field(
        default_factory=list,
        description="Conditions this goal addresses"
    )

    related_medications: list[str] = Field(
        default_factory=list,
        description="Medications related to this goal"
    )

    # Outcomes and results
    achievement_date: date | None = Field(
        default=None,
        description="Date when goal was achieved (if completed)"
    )

    final_result: str | None = Field(
        default=None,
        description="Final outcome when goal is completed",
        examples=[
            "Successfully lost 22 pounds, exceeded target",
            "Blood pressure now 135/85, close to target",
            "Can walk 45 minutes without stopping, goal exceeded"
        ]
    )

    lessons_learned: str | None = Field(
        default=None,
        description="What was learned from working toward this goal"
    )

    # Additional context
    goal_notes: Optional[str] = Field(
        None, description="Additional notes about the goal"
    )

    patient_feedback: str | None = Field(
        default=None,
        description="Patient's feedback about the goal and progress"
    )

    # ========================================
    # HELPER METHODS
    # ========================================

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        name = self.goal_name or "Unknown goal"
        status = self.lifecycle_status if isinstance(self.lifecycle_status, str) else (
            self.lifecycle_status.value if self.lifecycle_status else "unknown status"
        )
        return f"{name} ({status})"

    @property
    def display_name(self) -> str:
        """Get a display-friendly name for the goal."""
        if self.goal_name:
            return self.goal_name
        if self.description and "text" in self.description:
            return self.description["text"]
        return f"Goal {self.id}"

    @property
    def is_active(self) -> bool:
        """Check if the goal is currently active."""
        active_statuses = [
            GoalLifecycleStatus.ACTIVE,
            GoalLifecycleStatus.ACCEPTED,
            GoalLifecycleStatus.PLANNED
        ]
        return self.lifecycle_status in active_statuses if self.lifecycle_status else False

    @property
    def is_completed(self) -> bool:
        """Check if the goal is completed."""
        return self.lifecycle_status == GoalLifecycleStatus.COMPLETED if self.lifecycle_status else False

    @property
    def is_achieved(self) -> bool:
        """Check if the goal has been achieved."""
        return self.achievement_status == GoalAchievementStatus.ACHIEVED if self.achievement_status else False

    @property
    def is_on_track(self) -> bool:
        """Check if the goal is progressing well."""
        if not self.achievement_status:
            return False
        positive_statuses = [
            GoalAchievementStatus.IN_PROGRESS,
            GoalAchievementStatus.IMPROVING,
            GoalAchievementStatus.ACHIEVED,
            GoalAchievementStatus.SUSTAINING
        ]
        return self.achievement_status in positive_statuses

    @property
    def needs_attention(self) -> bool:
        """Check if the goal needs attention or intervention."""
        if not self.achievement_status:
            return False
        concerning_statuses = [
            GoalAchievementStatus.WORSENING,
            GoalAchievementStatus.NO_PROGRESS,
            GoalAchievementStatus.NOT_ACHIEVED,
            GoalAchievementStatus.NOT_ATTAINABLE
        ]
        return self.achievement_status in concerning_statuses

    @property
    def is_high_priority(self) -> bool:
        """Check if this is a high priority goal."""
        if self.goal_priority in [GoalPriority.HIGH_PRIORITY, GoalPriority.CRITICAL, GoalPriority.URGENT]:
            return True
        if self.priority and "coding" in self.priority:
            for coding in self.priority["coding"]:
                if coding.get("code") in ["high-priority", "critical", "urgent"]:
                    return True
        return False

    def get_priority_display(self) -> str:
        """Get human-readable priority information."""
        if self.goal_priority:
            priority = self.goal_priority if isinstance(self.goal_priority, str) else self.goal_priority.value
            return priority.replace("-", " ").replace("_", " ").title()
        if self.priority and "text" in self.priority:
            return self.priority["text"]
        return "Priority not specified"

    def get_timeframe_display(self) -> str:
        """Get human-readable timeframe information."""
        if self.target_date:
            return f"Target: {self.target_date.strftime('%Y-%m-%d')}"
        if self.goal_timeframe:
            timeframe = self.goal_timeframe if isinstance(self.goal_timeframe, str) else self.goal_timeframe.value
            return timeframe.replace("-", " ").replace("_", " ").title()
        return "No specific timeframe"

    def get_progress_display(self) -> str:
        """Get human-readable progress information."""
        if self.progress_description:
            return self.progress_description
        if self.percent_complete is not None:
            return f"{self.percent_complete}% complete"
        if self.achievement_status:
            status = self.achievement_status if isinstance(self.achievement_status, str) else self.achievement_status.value
            return status.replace("-", " ").replace("_", " ").title()
        return "Progress unknown"

    def get_team_members(self) -> list[str]:
        """Get list of team member names."""
        members = []
        if self.responsible_provider:
            members.append(self.responsible_provider)
        members.extend(self.team_members)
        if self.source and "display" in self.source:
            members.append(self.source["display"])
        return list(set(members))  # Remove duplicates

    def get_target_summary(self) -> str:
        """Get summary of target information."""
        if self.target_value:
            return self.target_value
        if self.target and len(self.target) > 0:
            target_info = self.target[0]
            if "detail" in target_info:
                detail = target_info["detail"]
                if isinstance(detail, dict) and "value" in detail:
                    unit = detail.get("unit", "")
                    return f"{detail['value']} {unit}".strip()
            if "measure" in target_info and "text" in target_info["measure"]:
                return target_info["measure"]["text"]
        return "Target not specified"

    def get_days_remaining(self) -> int | None:
        """Get number of days remaining to target date."""
        if not self.target_date:
            return None
        from datetime import date
        today = date.today()
        delta = self.target_date - today
        return delta.days

    def get_engagement_score(self) -> float | None:
        """Calculate patient engagement score based on importance and confidence."""
        if self.importance_to_patient is not None and self.confidence_level is not None:
            return (self.importance_to_patient + self.confidence_level) / 2.0
        return None

    def has_barriers(self) -> bool:
        """Check if there are identified barriers."""
        return bool(self.barriers)

    def needs_support(self) -> bool:
        """Check if additional support is needed."""
        return bool(self.support_needed) or self.needs_attention

    def is_overdue(self) -> bool:
        """Check if the goal is past its target date."""
        if not self.target_date:
            return False
        from datetime import date
        return date.today() > self.target_date and not self.is_completed

    def __init__(self, **data):
        if "id" not in data:
            data["id"] = str(uuid.uuid4())
        super().__init__(**data)

    def model_post_init(self, __context) -> None:
        """Post-initialization processing for LLM-friendly auto-conversion."""
        super().model_post_init(__context)

        # Auto-convert simple fields to FHIR structures
        if self.description_text and not self.description:
            self.description = {"text": self.description_text}

        if self.subject_reference and not self.subject:
            self.subject = {"reference": self.subject_reference}

        if self.category_text and not self.category:
            self.category = [{"text": self.category_text}]

        if self.priority_text and not self.priority:
            self.priority = {"text": self.priority_text}

    @field_validator("start_date", "status_date", "due_date", check_fields=False)
    @classmethod
    def validate_datetime_timezone(cls, v):
        """Ensure datetime fields are timezone-aware."""
        if v and isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    @model_validator(mode="after")
    def validate_goal_requirements(self) -> "Goal":
        """Enhanced validation with helpful error messages."""

        # Check that either description or description_text is provided
        if not self.description and not self.description_text:
            raise ValueError(
                "Goal must have a description. You can provide:\n"
                "- description_text='Lose 10 pounds' for simple usage\n"
                "- description={'text': 'Lose 10 pounds'} for FHIR compliance\n"
                "\nExample: Goal(lifecycle_status=GoalLifecycleStatus.ACTIVE, description_text='Lose weight', subject_reference='Patient/123')"
            )

        # Subject is optional for some use cases, but provide helpful guidance
        if not self.subject and not self.subject_reference:
            # Allow goals without subjects but warn in some contexts
            pass

        return self


# Create convenient type aliases
CareGoal = Goal
PatientGoal = Goal
TreatmentGoal = Goal