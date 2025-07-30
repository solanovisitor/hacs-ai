"""
HACS Task Model - FHIR R5 Compliant

This module implements the FHIR R5 Task resource with full compliance
to the healthcare interoperability standard. The Task resource describes
an activity that can be performed and tracks the state of completion of that activity.

FHIR R5 Task Resource:
https://hl7.org/fhir/R5/task.html

Key Features:
- Full FHIR R5 compliance with all 40+ fields
- Comprehensive validation rules and constraints (2 FHIR rules)
- Support for workflow management and task coordination
- Complex input/output parameter tracking
- LLM-friendly fields for AI applications
- Task state machine implementation
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from ..base_resource import BaseResource


class TaskStatus(str, Enum):
    """FHIR R5 Task Status codes following the task state machine."""
    DRAFT = "draft"
    REQUESTED = "requested"
    RECEIVED = "received"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    READY = "ready"
    CANCELLED = "cancelled"
    IN_PROGRESS = "in-progress"
    ON_HOLD = "on-hold"
    FAILED = "failed"
    COMPLETED = "completed"
    ENTERED_IN_ERROR = "entered-in-error"


class TaskIntent(str, Enum):
    """FHIR R5 Task Intent codes."""
    UNKNOWN = "unknown"
    PROPOSAL = "proposal"
    PLAN = "plan"
    ORDER = "order"
    ORIGINAL_ORDER = "original-order"
    REFLEX_ORDER = "reflex-order"
    FILLER_ORDER = "filler-order"
    INSTANCE_ORDER = "instance-order"
    OPTION = "option"


class TaskPriority(str, Enum):
    """FHIR R5 Task Priority codes."""
    ROUTINE = "routine"
    URGENT = "urgent"
    ASAP = "asap"
    STAT = "stat"


class TaskCode(str, Enum):
    """Common task type codes."""
    FULFILL = "fulfill"
    ABORT = "abort"
    REPLACE = "replace"
    CHANGE = "change"
    SUSPEND = "suspend"
    RESUME = "resume"
    APPROVE = "approve"
    REJECT = "reject"
    VERIFY = "verify"
    SIGN = "sign"
    REVIEW = "review"
    SCHEDULE = "schedule"
    COMPLETE = "complete"
    CANCEL = "cancel"
    ASSIGN = "assign"


class TaskPerformerFunction(str, Enum):
    """Task performer function codes."""
    REQUESTER = "requester"
    PERFORMER = "performer"
    VERIFIER = "verifier"
    RESPONSIBLE_PARTY = "responsible-party"
    REVIEWER = "reviewer"
    SCHEDULER = "scheduler"
    APPROVER = "approver"
    SUPERVISOR = "supervisor"
    COORDINATOR = "coordinator"


class TaskBusinessStatus(str, Enum):
    """Business status codes for tasks."""
    WAITING = "waiting"
    SCHEDULED = "scheduled"
    PERFORMING = "performing"
    DOCUMENTING = "documenting"
    VERIFYING = "verifying"
    SIGNING = "signing"
    SPECIMEN_COLLECTED = "specimen-collected"
    IV_PREPPED = "iv-prepped"
    RESULTS_PENDING = "results-pending"
    READY_FOR_REVIEW = "ready-for-review"


class TaskPerformer(BaseModel):
    """Who or what performed the task."""
    function: Optional[dict[str, Any]] = Field(
        None, description="Type of performance"
    )
    actor: dict[str, Any] = Field(
        ..., description="Who performed the task"
    )

    # LLM-friendly fields
    performer_name: Optional[str] = Field(
        None, description="Human-readable performer name"
    )
    performer_role: Optional[str] = Field(
        None, description="Role of the performer"
    )


class TaskRestriction(BaseModel):
    """Constraints on fulfillment tasks."""
    repetitions: Optional[int] = Field(
        None, description="How many times to repeat", ge=1
    )
    period: Optional[dict[str, Any]] = Field(
        None, description="When fulfillment is sought"
    )
    recipient: Optional[list[dict[str, Any]]] = Field(
        None, description="For whom is fulfillment sought?"
    )

    # LLM-friendly fields
    restriction_summary: Optional[str] = Field(
        None, description="Summary of restrictions"
    )
    is_time_limited: Optional[bool] = Field(
        None, description="Whether task has time restrictions"
    )


class TaskInput(BaseModel):
    """Information used to perform task."""
    type: dict[str, Any] = Field(
        ..., description="Label for the input"
    )

    # Value choice type - any type allowed
    value_base64_binary: Optional[str] = Field(
        None, description="Base64 binary input value"
    )
    value_boolean: Optional[bool] = Field(
        None, description="Boolean input value"
    )
    value_canonical: Optional[str] = Field(
        None, description="Canonical input value"
    )
    value_code: Optional[str] = Field(
        None, description="Code input value"
    )
    value_date: Optional[datetime] = Field(
        None, description="Date input value"
    )
    value_date_time: Optional[datetime] = Field(
        None, description="DateTime input value"
    )
    value_decimal: Optional[float] = Field(
        None, description="Decimal input value"
    )
    value_id: Optional[str] = Field(
        None, description="ID input value"
    )
    value_instant: Optional[datetime] = Field(
        None, description="Instant input value"
    )
    value_integer: Optional[int] = Field(
        None, description="Integer input value"
    )
    value_integer64: Optional[int] = Field(
        None, description="Integer64 input value"
    )
    value_markdown: Optional[str] = Field(
        None, description="Markdown input value"
    )
    value_oid: Optional[str] = Field(
        None, description="OID input value"
    )
    value_positive_int: Optional[int] = Field(
        None, description="Positive integer input value", ge=1
    )
    value_string: Optional[str] = Field(
        None, description="String input value"
    )
    value_time: Optional[str] = Field(
        None, description="Time input value"
    )
    value_unsigned_int: Optional[int] = Field(
        None, description="Unsigned integer input value", ge=0
    )
    value_uri: Optional[str] = Field(
        None, description="URI input value"
    )
    value_url: Optional[str] = Field(
        None, description="URL input value"
    )
    value_uuid: Optional[str] = Field(
        None, description="UUID input value"
    )
    value_address: Optional[dict[str, Any]] = Field(
        None, description="Address input value"
    )
    value_age: Optional[dict[str, Any]] = Field(
        None, description="Age input value"
    )
    value_annotation: Optional[dict[str, Any]] = Field(
        None, description="Annotation input value"
    )
    value_attachment: Optional[dict[str, Any]] = Field(
        None, description="Attachment input value"
    )
    value_codeable_concept: Optional[dict[str, Any]] = Field(
        None, description="CodeableConcept input value"
    )
    value_codeable_reference: Optional[dict[str, Any]] = Field(
        None, description="CodeableReference input value"
    )
    value_coding: Optional[dict[str, Any]] = Field(
        None, description="Coding input value"
    )
    value_contact_point: Optional[dict[str, Any]] = Field(
        None, description="ContactPoint input value"
    )
    value_count: Optional[dict[str, Any]] = Field(
        None, description="Count input value"
    )
    value_distance: Optional[dict[str, Any]] = Field(
        None, description="Distance input value"
    )
    value_duration: Optional[dict[str, Any]] = Field(
        None, description="Duration input value"
    )
    value_human_name: Optional[dict[str, Any]] = Field(
        None, description="HumanName input value"
    )
    value_identifier: Optional[dict[str, Any]] = Field(
        None, description="Identifier input value"
    )
    value_money: Optional[dict[str, Any]] = Field(
        None, description="Money input value"
    )
    value_period: Optional[dict[str, Any]] = Field(
        None, description="Period input value"
    )
    value_quantity: Optional[dict[str, Any]] = Field(
        None, description="Quantity input value"
    )
    value_range: Optional[dict[str, Any]] = Field(
        None, description="Range input value"
    )
    value_ratio: Optional[dict[str, Any]] = Field(
        None, description="Ratio input value"
    )
    value_ratio_range: Optional[dict[str, Any]] = Field(
        None, description="RatioRange input value"
    )
    value_reference: Optional[dict[str, Any]] = Field(
        None, description="Reference input value"
    )
    value_sampled_data: Optional[dict[str, Any]] = Field(
        None, description="SampledData input value"
    )
    value_signature: Optional[dict[str, Any]] = Field(
        None, description="Signature input value"
    )
    value_timing: Optional[dict[str, Any]] = Field(
        None, description="Timing input value"
    )
    value_contact_detail: Optional[dict[str, Any]] = Field(
        None, description="ContactDetail input value"
    )
    value_data_requirement: Optional[dict[str, Any]] = Field(
        None, description="DataRequirement input value"
    )
    value_expression: Optional[dict[str, Any]] = Field(
        None, description="Expression input value"
    )
    value_parameter_definition: Optional[dict[str, Any]] = Field(
        None, description="ParameterDefinition input value"
    )
    value_related_artifact: Optional[dict[str, Any]] = Field(
        None, description="RelatedArtifact input value"
    )
    value_trigger_definition: Optional[dict[str, Any]] = Field(
        None, description="TriggerDefinition input value"
    )
    value_usage_context: Optional[dict[str, Any]] = Field(
        None, description="UsageContext input value"
    )
    value_availability: Optional[dict[str, Any]] = Field(
        None, description="Availability input value"
    )
    value_extended_contact_detail: Optional[dict[str, Any]] = Field(
        None, description="ExtendedContactDetail input value"
    )
    value_dosage: Optional[dict[str, Any]] = Field(
        None, description="Dosage input value"
    )
    value_meta: Optional[dict[str, Any]] = Field(
        None, description="Meta input value"
    )

    # LLM-friendly fields
    input_name: Optional[str] = Field(
        None, description="Human-readable input name"
    )
    input_value_display: Optional[str] = Field(
        None, description="Human-readable input value"
    )
    is_required: Optional[bool] = Field(
        None, description="Whether this input is required"
    )


class TaskOutput(BaseModel):
    """Information produced as part of task."""
    type: dict[str, Any] = Field(
        ..., description="Label for output"
    )

    # Value choice type - same as TaskInput but for outputs
    value_base64_binary: Optional[str] = Field(
        None, description="Base64 binary output value"
    )
    value_boolean: Optional[bool] = Field(
        None, description="Boolean output value"
    )
    value_canonical: Optional[str] = Field(
        None, description="Canonical output value"
    )
    value_code: Optional[str] = Field(
        None, description="Code output value"
    )
    value_date: Optional[datetime] = Field(
        None, description="Date output value"
    )
    value_date_time: Optional[datetime] = Field(
        None, description="DateTime output value"
    )
    value_decimal: Optional[float] = Field(
        None, description="Decimal output value"
    )
    value_id: Optional[str] = Field(
        None, description="ID output value"
    )
    value_instant: Optional[datetime] = Field(
        None, description="Instant output value"
    )
    value_integer: Optional[int] = Field(
        None, description="Integer output value"
    )
    value_integer64: Optional[int] = Field(
        None, description="Integer64 output value"
    )
    value_markdown: Optional[str] = Field(
        None, description="Markdown output value"
    )
    value_oid: Optional[str] = Field(
        None, description="OID output value"
    )
    value_positive_int: Optional[int] = Field(
        None, description="Positive integer output value", ge=1
    )
    value_string: Optional[str] = Field(
        None, description="String output value"
    )
    value_time: Optional[str] = Field(
        None, description="Time output value"
    )
    value_unsigned_int: Optional[int] = Field(
        None, description="Unsigned integer output value", ge=0
    )
    value_uri: Optional[str] = Field(
        None, description="URI output value"
    )
    value_url: Optional[str] = Field(
        None, description="URL output value"
    )
    value_uuid: Optional[str] = Field(
        None, description="UUID output value"
    )
    value_address: Optional[dict[str, Any]] = Field(
        None, description="Address output value"
    )
    value_age: Optional[dict[str, Any]] = Field(
        None, description="Age output value"
    )
    value_annotation: Optional[dict[str, Any]] = Field(
        None, description="Annotation output value"
    )
    value_attachment: Optional[dict[str, Any]] = Field(
        None, description="Attachment output value"
    )
    value_codeable_concept: Optional[dict[str, Any]] = Field(
        None, description="CodeableConcept output value"
    )
    value_codeable_reference: Optional[dict[str, Any]] = Field(
        None, description="CodeableReference output value"
    )
    value_coding: Optional[dict[str, Any]] = Field(
        None, description="Coding output value"
    )
    value_contact_point: Optional[dict[str, Any]] = Field(
        None, description="ContactPoint output value"
    )
    value_count: Optional[dict[str, Any]] = Field(
        None, description="Count output value"
    )
    value_distance: Optional[dict[str, Any]] = Field(
        None, description="Distance output value"
    )
    value_duration: Optional[dict[str, Any]] = Field(
        None, description="Duration output value"
    )
    value_human_name: Optional[dict[str, Any]] = Field(
        None, description="HumanName output value"
    )
    value_identifier: Optional[dict[str, Any]] = Field(
        None, description="Identifier output value"
    )
    value_money: Optional[dict[str, Any]] = Field(
        None, description="Money output value"
    )
    value_period: Optional[dict[str, Any]] = Field(
        None, description="Period output value"
    )
    value_quantity: Optional[dict[str, Any]] = Field(
        None, description="Quantity output value"
    )
    value_range: Optional[dict[str, Any]] = Field(
        None, description="Range output value"
    )
    value_ratio: Optional[dict[str, Any]] = Field(
        None, description="Ratio output value"
    )
    value_ratio_range: Optional[dict[str, Any]] = Field(
        None, description="RatioRange output value"
    )
    value_reference: Optional[dict[str, Any]] = Field(
        None, description="Reference output value"
    )
    value_sampled_data: Optional[dict[str, Any]] = Field(
        None, description="SampledData output value"
    )
    value_signature: Optional[dict[str, Any]] = Field(
        None, description="Signature output value"
    )
    value_timing: Optional[dict[str, Any]] = Field(
        None, description="Timing output value"
    )
    value_contact_detail: Optional[dict[str, Any]] = Field(
        None, description="ContactDetail output value"
    )
    value_data_requirement: Optional[dict[str, Any]] = Field(
        None, description="DataRequirement output value"
    )
    value_expression: Optional[dict[str, Any]] = Field(
        None, description="Expression output value"
    )
    value_parameter_definition: Optional[dict[str, Any]] = Field(
        None, description="ParameterDefinition output value"
    )
    value_related_artifact: Optional[dict[str, Any]] = Field(
        None, description="RelatedArtifact output value"
    )
    value_trigger_definition: Optional[dict[str, Any]] = Field(
        None, description="TriggerDefinition output value"
    )
    value_usage_context: Optional[dict[str, Any]] = Field(
        None, description="UsageContext output value"
    )
    value_availability: Optional[dict[str, Any]] = Field(
        None, description="Availability output value"
    )
    value_extended_contact_detail: Optional[dict[str, Any]] = Field(
        None, description="ExtendedContactDetail output value"
    )
    value_dosage: Optional[dict[str, Any]] = Field(
        None, description="Dosage output value"
    )
    value_meta: Optional[dict[str, Any]] = Field(
        None, description="Meta output value"
    )

    # LLM-friendly fields
    output_name: Optional[str] = Field(
        None, description="Human-readable output name"
    )
    output_value_display: Optional[str] = Field(
        None, description="Human-readable output value"
    )
    is_final_result: Optional[bool] = Field(
        None, description="Whether this is the final result"
    )


class Task(BaseResource):
    """
    FHIR R5 Task Resource

    A task to be performed as part of a workflow and related information
    like inputs, outputs and execution progress.
    """

    resource_type: Literal["Task"] = Field(
        default="Task", description="Resource type identifier"
    )

    # FHIR R5 Core Fields
    identifier: Optional[list[dict[str, Any]]] = Field(
        None, description="Task Instance Identifier"
    )
    instantiates_canonical: Optional[str] = Field(
        None, description="Formal definition of task"
    )
    instantiates_uri: Optional[str] = Field(
        None, description="Formal definition of task"
    )
    based_on: Optional[list[dict[str, Any]]] = Field(
        None, description="Request fulfilled by this task"
    )
    group_identifier: Optional[dict[str, Any]] = Field(
        None, description="Requisition or grouper id"
    )
    part_of: Optional[list[dict[str, Any]]] = Field(
        None, description="Composite task"
    )
    status: TaskStatus = Field(
        ..., description="Current status of the task"
    )
    status_reason: Optional[dict[str, Any]] = Field(
        None, description="Reason for current status"
    )
    business_status: Optional[dict[str, Any]] = Field(
        None, description="E.g. 'Specimen collected', 'IV prepped'"
    )
    intent: TaskIntent = Field(
        ..., description="Intent of the task"
    )
    priority: Optional[TaskPriority] = Field(
        None, description="Priority of the task"
    )
    do_not_perform: Optional[bool] = Field(
        None, description="True if Task is prohibiting action"
    )
    code: Optional[dict[str, Any]] = Field(
        None, description="Task Type"
    )
    description: Optional[str] = Field(
        None, description="Human-readable explanation of task"
    )
    focus: Optional[dict[str, Any]] = Field(
        None, description="What task is acting on"
    )
    for_: Optional[dict[str, Any]] = Field(
        None, description="Beneficiary of the Task", alias="for"
    )
    encounter: Optional[dict[str, Any]] = Field(
        None, description="Healthcare event during which this task originated"
    )
    requested_period: Optional[dict[str, Any]] = Field(
        None, description="When the task should be performed"
    )
    execution_period: Optional[dict[str, Any]] = Field(
        None, description="Start and end time of execution"
    )
    authored_on: Optional[datetime] = Field(
        None, description="Task Creation Date"
    )
    last_modified: Optional[datetime] = Field(
        None, description="Task Last Modified Date"
    )
    requester: Optional[dict[str, Any]] = Field(
        None, description="Who is asking for task to be done"
    )
    requested_performer: Optional[list[dict[str, Any]]] = Field(
        None, description="Who should perform Task"
    )
    owner: Optional[dict[str, Any]] = Field(
        None, description="Responsible individual"
    )
    performer: Optional[list[TaskPerformer]] = Field(
        None, description="Who or what performed the task"
    )
    location: Optional[dict[str, Any]] = Field(
        None, description="Where task occurs"
    )
    reason: Optional[list[dict[str, Any]]] = Field(
        None, description="Why task is needed"
    )
    insurance: Optional[list[dict[str, Any]]] = Field(
        None, description="Associated insurance coverage"
    )
    note: Optional[list[dict[str, Any]]] = Field(
        None, description="Comments made about the task"
    )
    relevant_history: Optional[list[dict[str, Any]]] = Field(
        None, description="Key events in history of the Task"
    )
    restriction: Optional[TaskRestriction] = Field(
        None, description="Constraints on fulfillment tasks"
    )
    input: Optional[list[TaskInput]] = Field(
        None, description="Information used to perform task"
    )
    output: Optional[list[TaskOutput]] = Field(
        None, description="Information produced as part of task"
    )

    # LLM-friendly fields
    task_title: Optional[str] = Field(
        None, description="Human-readable task title"
    )
    task_summary: Optional[str] = Field(
        None, description="Brief summary of the task"
    )
    assigned_to: Optional[str] = Field(
        None, description="Who the task is assigned to"
    )
    created_by: Optional[str] = Field(
        None, description="Who created the task"
    )
    urgency_level: Optional[str] = Field(
        None, description="Urgency description"
    )
    completion_percentage: Optional[int] = Field(
        None, description="Percentage completion (0-100)", ge=0, le=100
    )
    estimated_duration: Optional[str] = Field(
        None, description="Estimated time to complete"
    )
    actual_duration: Optional[str] = Field(
        None, description="Actual time taken"
    )
    workflow_stage: Optional[str] = Field(
        None, description="Current stage in workflow"
    )
    dependencies: Optional[list[str]] = Field(
        None, description="Tasks that must be completed first"
    )
    deliverables: Optional[list[str]] = Field(
        None, description="Expected deliverables from this task"
    )
    quality_requirements: Optional[list[str]] = Field(
        None, description="Quality requirements for task completion"
    )

    def __init__(self, **data):
        if "id" not in data:
            data["id"] = str(uuid.uuid4())
        if "authored_on" not in data:
            data["authored_on"] = datetime.now(timezone.utc)
        if "last_modified" not in data:
            data["last_modified"] = datetime.now(timezone.utc)
        super().__init__(**data)

    @field_validator("authored_on", "last_modified")
    @classmethod
    def validate_datetime_timezone(cls, v):
        """Ensure datetime fields are timezone-aware."""
        if v and isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    @model_validator(mode="after")
    def validate_task_constraints(self) -> "Task":
        """Validate FHIR R5 task constraints."""

        # Rule tsk-1: Task.restriction is only allowed if the Task is seeking fulfillment and a focus is specified
        if self.restriction:
            # Check if task code is 'fulfill'
            has_fulfill_code = False
            if isinstance(self.code, dict) and self.code.get("coding"):
                for coding in self.code["coding"]:
                    if (coding.get("code") == "fulfill" and
                        coding.get("system") == "http://hl7.org/fhir/CodeSystem/task-code"):
                        has_fulfill_code = True
                        break

            if not (has_fulfill_code and self.focus):
                raise ValueError("Task.restriction is only allowed if the Task is seeking fulfillment and a focus is specified")

        # Rule inv-1: Last modified date must be greater than or equal to authored-on date
        if (self.last_modified and self.authored_on and
            self.last_modified < self.authored_on):
            raise ValueError("Last modified date must be greater than or equal to authored-on date")

        return self

    # Helper properties
    @property
    def display_name(self) -> str:
        """Human-readable display name for the task."""
        if self.task_title:
            return self.task_title

        if isinstance(self.code, dict) and self.code.get("text"):
            return self.code["text"]
        elif isinstance(self.code, dict) and self.code.get("coding"):
            coding = self.code["coding"][0] if self.code["coding"] else {}
            return coding.get("display", coding.get("code", "Task"))

        if self.description:
            return self.description[:50] + "..." if len(self.description) > 50 else self.description

        return f"Task {self.id[:8]}"

    @property
    def status_display(self) -> str:
        """Human-readable status display."""
        status_map = {
            TaskStatus.DRAFT: "Draft",
            TaskStatus.REQUESTED: "Requested",
            TaskStatus.RECEIVED: "Received",
            TaskStatus.ACCEPTED: "Accepted",
            TaskStatus.REJECTED: "Rejected",
            TaskStatus.READY: "Ready",
            TaskStatus.CANCELLED: "Cancelled",
            TaskStatus.IN_PROGRESS: "In Progress",
            TaskStatus.ON_HOLD: "On Hold",
            TaskStatus.FAILED: "Failed",
            TaskStatus.COMPLETED: "Completed",
            TaskStatus.ENTERED_IN_ERROR: "Entered in Error"
        }
        return status_map.get(self.status, str(self.status))

    @property
    def intent_display(self) -> str:
        """Human-readable intent display."""
        intent_map = {
            TaskIntent.UNKNOWN: "Unknown",
            TaskIntent.PROPOSAL: "Proposal",
            TaskIntent.PLAN: "Plan",
            TaskIntent.ORDER: "Order",
            TaskIntent.ORIGINAL_ORDER: "Original Order",
            TaskIntent.REFLEX_ORDER: "Reflex Order",
            TaskIntent.FILLER_ORDER: "Filler Order",
            TaskIntent.INSTANCE_ORDER: "Instance Order",
            TaskIntent.OPTION: "Option"
        }
        return intent_map.get(self.intent, str(self.intent))

    @property
    def priority_display(self) -> str:
        """Human-readable priority display."""
        if not self.priority:
            return "Routine"

        priority_map = {
            TaskPriority.ROUTINE: "Routine",
            TaskPriority.URGENT: "Urgent",
            TaskPriority.ASAP: "ASAP",
            TaskPriority.STAT: "STAT"
        }
        return priority_map.get(self.priority, str(self.priority))

    @property
    def urgency_description(self) -> str:
        """Get urgency description based on priority."""
        if self.urgency_level:
            return self.urgency_level

        if not self.priority:
            return "Standard priority - complete in normal timeframe"

        urgency_descriptions = {
            TaskPriority.ROUTINE: "Standard priority - complete in normal timeframe",
            TaskPriority.URGENT: "High priority - complete within 24 hours",
            TaskPriority.ASAP: "Very high priority - complete as soon as possible",
            TaskPriority.STAT: "Highest priority - complete immediately"
        }
        return urgency_descriptions.get(self.priority, "Standard priority")

    # Task State Machine Methods
    def is_terminal_state(self) -> bool:
        """Check if task is in a terminal state."""
        terminal_states = [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.ENTERED_IN_ERROR,
            TaskStatus.REJECTED
        ]
        return self.status in terminal_states

    def is_active(self) -> bool:
        """Check if task is currently active."""
        active_states = [
            TaskStatus.ACCEPTED,
            TaskStatus.READY,
            TaskStatus.IN_PROGRESS
        ]
        return self.status in active_states

    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.status == TaskStatus.COMPLETED

    def is_failed(self) -> bool:
        """Check if task failed."""
        return self.status == TaskStatus.FAILED

    def is_cancelled(self) -> bool:
        """Check if task was cancelled."""
        return self.status == TaskStatus.CANCELLED

    def is_urgent(self) -> bool:
        """Check if task is urgent."""
        return self.priority in [TaskPriority.URGENT, TaskPriority.ASAP, TaskPriority.STAT]

    def is_stat(self) -> bool:
        """Check if task is STAT priority."""
        return self.priority == TaskPriority.STAT

    def can_be_started(self) -> bool:
        """Check if task can be started."""
        startable_states = [TaskStatus.READY, TaskStatus.RECEIVED, TaskStatus.ACCEPTED]
        return self.status in startable_states

    def can_be_suspended(self) -> bool:
        """Check if task can be suspended."""
        suspendable_states = [TaskStatus.READY, TaskStatus.IN_PROGRESS]
        return self.status in suspendable_states

    def can_be_cancelled(self) -> bool:
        """Check if task can be cancelled."""
        return not self.is_terminal_state()

    # Helper methods
    def get_task_type(self) -> Optional[str]:
        """Get the primary task type."""
        if isinstance(self.code, dict):
            if self.code.get("text"):
                return self.code["text"]
            elif self.code.get("coding"):
                coding = self.code["coding"][0] if self.code["coding"] else {}
                return coding.get("display", coding.get("code"))

        return None

    def get_assigned_to(self) -> Optional[str]:
        """Get who the task is assigned to."""
        if self.assigned_to:
            return self.assigned_to

        if isinstance(self.owner, dict):
            if self.owner.get("display"):
                return self.owner["display"]
            elif self.owner.get("reference"):
                return self.owner["reference"]

        return None

    def get_created_by(self) -> Optional[str]:
        """Get who created the task."""
        if self.created_by:
            return self.created_by

        if isinstance(self.requester, dict):
            if self.requester.get("display"):
                return self.requester["display"]
            elif self.requester.get("reference"):
                return self.requester["reference"]

        return None

    def get_task_reasons(self) -> list[str]:
        """Get list of reasons for the task."""
        reasons = []

        if self.reason:
            for reason in self.reason:
                if isinstance(reason, dict):
                    if reason.get("text"):
                        reasons.append(reason["text"])
                    elif reason.get("coding"):
                        coding = reason["coding"][0] if reason["coding"] else {}
                        if coding.get("display"):
                            reasons.append(coding["display"])

        return reasons

    def get_input_summary(self) -> list[dict[str, Any]]:
        """Get summary of task inputs."""
        inputs = []

        if self.input:
            for inp in self.input:
                input_info = {
                    "name": inp.input_name or "Unknown Input",
                    "type": inp.type,
                    "value": inp.input_value_display or "Not specified",
                    "required": inp.is_required
                }
                inputs.append(input_info)

        return inputs

    def get_output_summary(self) -> list[dict[str, Any]]:
        """Get summary of task outputs."""
        outputs = []

        if self.output:
            for out in self.output:
                output_info = {
                    "name": out.output_name or "Unknown Output",
                    "type": out.type,
                    "value": out.output_value_display or "Not specified",
                    "is_final": out.is_final_result
                }
                outputs.append(output_info)

        return outputs

    def get_performers(self) -> list[dict[str, Any]]:
        """Get list of task performers."""
        performers = []

        if self.performer:
            for perf in self.performer:
                performer_info = {
                    "name": perf.performer_name or "Unknown Performer",
                    "role": perf.performer_role,
                    "function": perf.function,
                    "actor": perf.actor
                }
                performers.append(performer_info)

        return performers

    def get_execution_timeframe(self) -> Optional[str]:
        """Get execution timeframe description."""
        if self.execution_period and isinstance(self.execution_period, dict):
            start = self.execution_period.get("start")
            end = self.execution_period.get("end")

            if start and end:
                return f"From {start} to {end}"
            elif start:
                return f"Started {start}"
            elif end:
                return f"Due by {end}"

        if self.requested_period and isinstance(self.requested_period, dict):
            start = self.requested_period.get("start")
            end = self.requested_period.get("end")

            if start and end:
                return f"Requested between {start} and {end}"
            elif start:
                return f"Requested after {start}"
            elif end:
                return f"Requested before {end}"

        return None

    def has_restrictions(self) -> bool:
        """Check if task has restrictions."""
        return bool(self.restriction)

    def get_business_status_display(self) -> Optional[str]:
        """Get human-readable business status."""
        if isinstance(self.business_status, dict):
            if self.business_status.get("text"):
                return self.business_status["text"]
            elif self.business_status.get("coding"):
                coding = self.business_status["coding"][0] if self.business_status["coding"] else {}
                return coding.get("display", coding.get("code"))

        return None

    def to_task_summary(self) -> dict[str, Any]:
        """Convert to task summary format."""
        return {
            "id": self.id,
            "title": self.display_name,
            "status": self.status_display,
            "intent": self.intent_display,
            "priority": self.priority_display,
            "urgency": self.urgency_description,
            "type": self.get_task_type(),
            "assigned_to": self.get_assigned_to(),
            "created_by": self.get_created_by(),
            "business_status": self.get_business_status_display(),
            "reasons": self.get_task_reasons(),
            "execution_timeframe": self.get_execution_timeframe(),
            "is_terminal": self.is_terminal_state(),
            "is_active": self.is_active(),
            "can_be_started": self.can_be_started(),
            "can_be_cancelled": self.can_be_cancelled(),
            "authored_on": self.authored_on.isoformat() if self.authored_on else None,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
        }

    def to_workflow_summary(self) -> dict[str, Any]:
        """Convert to workflow management format."""
        return {
            "task_id": self.id,
            "workflow_stage": self.workflow_stage or self.status_display,
            "task_details": {
                "title": self.display_name,
                "description": self.description,
                "type": self.get_task_type(),
                "priority": self.priority_display,
                "business_status": self.get_business_status_display(),
            },
            "assignment": {
                "assigned_to": self.get_assigned_to(),
                "created_by": self.get_created_by(),
                "performers": self.get_performers(),
            },
            "execution": {
                "status": self.status_display,
                "timeframe": self.get_execution_timeframe(),
                "completion_percentage": self.completion_percentage,
                "estimated_duration": self.estimated_duration,
                "actual_duration": self.actual_duration,
            },
            "workflow_control": {
                "is_active": self.is_active(),
                "can_be_started": self.can_be_started(),
                "can_be_suspended": self.can_be_suspended(),
                "can_be_cancelled": self.can_be_cancelled(),
                "dependencies": self.dependencies or [],
                "has_restrictions": self.has_restrictions(),
            },
            "inputs": self.get_input_summary(),
            "outputs": self.get_output_summary(),
        }

    def to_performer_summary(self) -> dict[str, Any]:
        """Convert to performer-friendly summary."""
        return {
            "task_title": self.display_name,
            "task_description": self.description,
            "status": self.status_display,
            "priority": self.priority_display,
            "urgency": self.urgency_description,
            "assigned_to_me": self.get_assigned_to(),
            "what_to_do": self.get_task_type(),
            "why_needed": self.get_task_reasons(),
            "when_requested": self.get_execution_timeframe(),
            "inputs_needed": self.get_input_summary(),
            "expected_outputs": self.get_output_summary(),
            "completion_status": self.completion_percentage,
            "estimated_time": self.estimated_duration,
            "deliverables": self.deliverables or [],
            "quality_requirements": self.quality_requirements or [],
            "can_start_now": self.can_be_started(),
            "dependencies": self.dependencies or [],
            "special_instructions": self.description,
        }


# Type aliases for different task contexts
WorkflowTask = Task
FulfillmentTask = Task
ApprovalTask = Task
ReviewTask = Task
SchedulingTask = Task