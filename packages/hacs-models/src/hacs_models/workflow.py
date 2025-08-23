"""Workflow models - minimal, FHIR-aligned compatibility layer."""

from typing import Any, Literal

from pydantic import Field, model_validator

from .base_resource import BaseResource
from .types import (
    EventStatus,
    WorkflowActivityDefinitionKind,
    WorkflowRequestIntent,
    WorkflowRequestPriority,
    WorkflowStatus,
    WorkflowTaskIntent,
    WorkflowTaskStatus,
)


class WorkflowStep(BaseResource):
    resource_type: Literal["WorkflowStep"] = Field(default="WorkflowStep")


class WorkflowAction(BaseResource):
    resource_type: Literal["WorkflowAction"] = Field(default="WorkflowAction")


class WorkflowDefinition(BaseResource):
    resource_type: Literal["WorkflowDefinition"] = Field(default="WorkflowDefinition")
    name: str | None = None
    title: str | None = None
    status: WorkflowStatus = Field(default=WorkflowStatus.DRAFT)
    description: str | None = None
    type: str | None = None
    goal: list[dict[str, Any]] = Field(default_factory=list)
    action: list[dict[str, Any]] = Field(default_factory=list)


# Compatibility resources used by tests


class WorkflowRequest(BaseResource):
    resource_type: Literal["WorkflowRequest"] = Field(default="WorkflowRequest")
    status: WorkflowStatus = Field(default=WorkflowStatus.DRAFT)
    intent: WorkflowRequestIntent = Field(default=WorkflowRequestIntent.ORDER)
    priority: WorkflowRequestPriority = Field(default=WorkflowRequestPriority.ROUTINE)
    subject: str | None = None


class WorkflowEvent(BaseResource):
    resource_type: Literal["WorkflowEvent"] = Field(default="WorkflowEvent")
    status: EventStatus = Field(default=EventStatus.IN_PROGRESS)
    subject: str | None = None
    recorded: str | None = Field(
        default_factory=lambda: __import__("datetime").datetime.now().isoformat()
    )
    based_on: list[str] = Field(default_factory=list)


class WorkflowTaskResource(BaseResource):
    resource_type: Literal["Task"] = Field(default="Task")
    code: str | None = None
    description: str | None = None
    status: WorkflowTaskStatus = Field(default=WorkflowTaskStatus.REQUESTED)
    intent: WorkflowTaskIntent = Field(default=WorkflowTaskIntent.ORDER)
    subject: str | None = None
    priority: WorkflowRequestPriority | None = None

    class _Param(BaseResource):
        resource_type: Literal["TaskParameter"] = Field(default="TaskParameter")
        name: str
        type: str | None = None
        default_value: Any | None = None

    input: list[_Param] = Field(default_factory=list)
    output: list[_Param] = Field(default_factory=list)
    requester: str | None = None
    instantiates_canonical: list[str] = Field(default_factory=list)
    part_of: list[str] = Field(default_factory=list)
    execution_period_end: str | None = None
    last_modified: str | None = None
    note: str | None = None

    @model_validator(mode="after")
    def _validate_required(self) -> "WorkflowTaskResource":
        if self.subject is None:
            raise ValueError("Task.subject is required")
        return self

    def add_input(self, name: str, value: Any, type_: str | None = None) -> "WorkflowTaskResource":
        self.input.append(self._Param(name=name, type=type_, default_value=value))
        return self

    def add_output(
        self, name: str, type_: str, description: str | None = None
    ) -> "WorkflowTaskResource":
        self.output.append(self._Param(name=name, type=type_, default_value=None))
        return self

    def complete(self, outputs: dict[str, Any]) -> None:
        self.status = WorkflowTaskStatus.COMPLETED
        from datetime import datetime

        self.execution_period_end = datetime.now().isoformat()
        self.last_modified = self.execution_period_end
        self.note = f"Task completed with outputs: {list(outputs.keys())}"

    def fail(self, message: str) -> None:
        self.status = WorkflowTaskStatus.FAILED
        from datetime import datetime

        self.execution_period_end = datetime.now().isoformat()
        self.note = f"Task failed: {message}"


class LinkRelation:
    SELF = "self"


class WorkflowBindingType:
    INPUT_FILTER = "input_filter"
    OUTPUT_TEMPLATE = "output_template"


class WorkflowBinding(BaseResource):
    resource_type: Literal["WorkflowBinding"] = Field(default="WorkflowBinding")
    workflow_id: str
    binding_type: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    priority: int = 0
    description: str | None = None
    workflow_name: str | None = None
    active: bool = True


class WorkflowActivityDefinition(BaseResource):
    resource_type: Literal["ActivityDefinition"] = Field(default="ActivityDefinition")
    kind: WorkflowActivityDefinitionKind = Field(default=WorkflowActivityDefinitionKind.TASK)
    name: str | None = None
    title: str | None = None
    status: WorkflowStatus = Field(default=WorkflowStatus.DRAFT)
    description: str | None = None
    purpose: str | None = None
    code: str | None = None
    participant: list[Any] = Field(default_factory=list)

    def create_task(
        self, subject: str | None = None, requester: str | None = None
    ) -> WorkflowTaskResource:
        task = WorkflowTaskResource(
            code=self.code,
            description=self.description,
            status=WorkflowTaskStatus.REQUESTED,
            intent=WorkflowTaskIntent.ORDER,
            subject=subject,
            requester=requester,
        )
        # Tests compare to raw id; add both forms
        task.instantiates_canonical.append(self.id)
        task.instantiates_canonical.append(f"ActivityDefinition/{self.id}")
        return task


class WorkflowParticipant(BaseResource):
    resource_type: Literal["WorkflowParticipant"] = Field(default="WorkflowParticipant")
    name: str | None = None
    role: str | None = None
    actor_type: str | None = None
    required: bool = False


class WorkflowPlanDefinition(BaseResource):
    resource_type: Literal["PlanDefinition"] = Field(default="PlanDefinition")
    name: str | None = None
    title: str | None = None
    status: WorkflowStatus = Field(default=WorkflowStatus.DRAFT)
    description: str | None = None
    type: str | None = None
    goal: list[dict[str, Any]] = Field(default_factory=list)
    action: list["WorkflowPlanDefinitionAction"] = Field(default_factory=list)

    def add_goal(
        self, description: str, category: str | None = None, priority: str | None = None
    ) -> None:
        self.goal.append({"description": description, "category": category, "priority": priority})

    def add_action(
        self,
        title: str,
        code: str | None = None,
        description: str | None = None,
        definition_canonical: str | None = None,
    ) -> None:
        self.action.append(
            WorkflowPlanDefinitionAction(
                title=title,
                code=code,
                description=description,
                definition_canonical=definition_canonical,
            )
        )


class WorkflowPlanDefinitionAction(BaseResource):
    resource_type: Literal["PlanDefinitionAction"] = Field(default="PlanDefinitionAction")
    title: str | None = None
    code: str | None = None
    description: str | None = None
    definition_canonical: str | None = None
    action: list["WorkflowPlanDefinitionAction"] = Field(default_factory=list)


class WorkflowServiceRequest(BaseResource):
    resource_type: Literal["ServiceRequest"] = Field(default="ServiceRequest")
    code: str | None = None
    status: WorkflowStatus = Field(default=WorkflowStatus.DRAFT)
    intent: WorkflowRequestIntent = Field(default=WorkflowRequestIntent.ORDER)
    subject: str | None = None
    requester: str | None = None
    order_detail: list[str] = Field(default_factory=list)
    specimen: list[str] = Field(default_factory=list)
    body_site: list[str] = Field(default_factory=list)
    patient_instruction: list[str] = Field(default_factory=list)


class WorkflowExecution(BaseResource):
    resource_type: Literal["WorkflowExecution"] = Field(default="WorkflowExecution")
    workflow_definition: str | None = None
    subject: str | None = None
    total_steps: int = 0
    current_step: int = 0
    status: EventStatus = Field(default=EventStatus.PREPARATION)
    started: str | None = None
    ended: str | None = None
    input_parameters: dict[str, Any] = Field(default_factory=dict)
    completed_steps: dict[int, dict[str, Any]] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    tasks: list[str] = Field(default_factory=list)
    active_tasks: list[str] = Field(default_factory=list)

    def start_execution(self, input_parameters: dict[str, Any] | None = None) -> None:
        from datetime import datetime

        self.status = EventStatus.IN_PROGRESS
        self.started = datetime.now().isoformat()
        if input_parameters:
            self.input_parameters.update(input_parameters)

    def complete_step(self, idx: int, output: dict[str, Any]) -> None:
        self.completed_steps[idx] = output
        if idx >= self.current_step:
            self.current_step = idx + 1
        if self.current_step >= self.total_steps:
            self.status = EventStatus.COMPLETED
            from datetime import datetime

            self.ended = datetime.now().isoformat()

    def fail_execution(self, message: str) -> None:
        self.status = EventStatus.STOPPED
        from datetime import datetime

        self.ended = datetime.now().isoformat()
        self.errors.append(message)

    def add_task(self, task_id: str, active: bool = True) -> None:
        self.tasks.append(task_id)
        if active:
            self.active_tasks.append(task_id)


# Factory helpers for tests
def create_simple_task(
    code: str,
    description: str | None = None,
    subject: str | None = None,
    requester: str | None = None,
    priority: WorkflowRequestPriority = WorkflowRequestPriority.ROUTINE,
) -> WorkflowTaskResource:
    return WorkflowTaskResource(
        code=code,
        description=description,
        status=WorkflowTaskStatus.REQUESTED,
        intent=WorkflowTaskIntent.ORDER,
        subject=subject,
        requester=requester,
        priority=priority,
    )


def create_document_processing_workflow() -> WorkflowPlanDefinition:
    plan = WorkflowPlanDefinition(
        name="DocumentProcessingWorkflow",
        title="Clinical Document Processing Workflow",
        status=WorkflowStatus.ACTIVE,
    )
    # Add sample goals and actions
    plan.add_goal("Validate document structure and content")
    plan.add_goal("Extract clinical information")
    plan.add_goal("Assess document quality")
    plan.add_goal("Integrate into patient record")
    plan.add_action("Validate Document", code="validate-document")
    plan.add_action("Extract Content", code="extract-content")
    plan.add_action("Assess Quality", code="assess-quality")
    plan.add_action("Integrate Document", code="integrate-document")
    return plan


def create_clinical_workflow_execution(
    workflow_definition: str, subject: str, input_parameters: dict[str, Any] | None = None
) -> WorkflowExecution:
    exec_ = WorkflowExecution(
        workflow_definition=workflow_definition, subject=subject, total_steps=4
    )
    exec_.start_execution(input_parameters)
    return exec_
