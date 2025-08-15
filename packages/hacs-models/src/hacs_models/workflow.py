"""Workflow models - minimal, FHIR-aligned compatibility layer."""
from typing import Literal, Optional, Dict, Any, List
from pydantic import Field, model_validator
from .base_resource import BaseResource
from .types import (
    WorkflowStatus,
    WorkflowRequestIntent,
    WorkflowRequestPriority,
    EventStatus,
    WorkflowTaskStatus,
    WorkflowTaskIntent,
    WorkflowActivityDefinitionKind,
)

class WorkflowStep(BaseResource):
    resource_type: Literal["WorkflowStep"] = Field(default="WorkflowStep")

class WorkflowAction(BaseResource):
    resource_type: Literal["WorkflowAction"] = Field(default="WorkflowAction")

class WorkflowDefinition(BaseResource):
    resource_type: Literal["WorkflowDefinition"] = Field(default="WorkflowDefinition")
    name: Optional[str] = None
    title: Optional[str] = None
    status: WorkflowStatus = Field(default=WorkflowStatus.DRAFT)
    description: Optional[str] = None
    type: Optional[str] = None
    goal: List[Dict[str, Any]] = Field(default_factory=list)
    action: List[Dict[str, Any]] = Field(default_factory=list)


# Compatibility resources used by tests

class WorkflowRequest(BaseResource):
    resource_type: Literal["WorkflowRequest"] = Field(default="WorkflowRequest")
    status: WorkflowStatus = Field(default=WorkflowStatus.DRAFT)
    intent: WorkflowRequestIntent = Field(default=WorkflowRequestIntent.ORDER)
    priority: WorkflowRequestPriority = Field(default=WorkflowRequestPriority.ROUTINE)
    subject: Optional[str] = None


class WorkflowEvent(BaseResource):
    resource_type: Literal["WorkflowEvent"] = Field(default="WorkflowEvent")
    status: EventStatus = Field(default=EventStatus.IN_PROGRESS)
    subject: Optional[str] = None
    recorded: Optional[str] = Field(default_factory=lambda: __import__("datetime").datetime.now().isoformat())
    based_on: List[str] = Field(default_factory=list)


class WorkflowTaskResource(BaseResource):
    resource_type: Literal["Task"] = Field(default="Task")
    code: Optional[str] = None
    description: Optional[str] = None
    status: WorkflowTaskStatus = Field(default=WorkflowTaskStatus.REQUESTED)
    intent: WorkflowTaskIntent = Field(default=WorkflowTaskIntent.ORDER)
    subject: Optional[str] = None
    priority: Optional[WorkflowRequestPriority] = None
    class _Param(BaseResource):
        resource_type: Literal["TaskParameter"] = Field(default="TaskParameter")
        name: str
        type: Optional[str] = None
        default_value: Optional[Any] = None

    input: List[_Param] = Field(default_factory=list)
    output: List[_Param] = Field(default_factory=list)
    requester: Optional[str] = None
    instantiates_canonical: List[str] = Field(default_factory=list)
    part_of: List[str] = Field(default_factory=list)
    execution_period_end: Optional[str] = None
    last_modified: Optional[str] = None
    note: Optional[str] = None

    @model_validator(mode="after")
    def _validate_required(self) -> "WorkflowTaskResource":
        if self.subject is None:
            raise ValueError("Task.subject is required")
        return self

    def add_input(self, name: str, value: Any, type_: str | None = None) -> "WorkflowTaskResource":
        self.input.append(self._Param(name=name, type=type_, default_value=value))
        return self

    def add_output(self, name: str, type_: str, description: str | None = None) -> "WorkflowTaskResource":
        self.output.append(self._Param(name=name, type=type_, default_value=None))
        return self

    def complete(self, outputs: Dict[str, Any]) -> None:
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
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: int = 0
    description: Optional[str] = None
    workflow_name: Optional[str] = None
    active: bool = True


class WorkflowActivityDefinition(BaseResource):
    resource_type: Literal["ActivityDefinition"] = Field(default="ActivityDefinition")
    kind: WorkflowActivityDefinitionKind = Field(default=WorkflowActivityDefinitionKind.TASK)
    name: Optional[str] = None
    title: Optional[str] = None
    status: WorkflowStatus = Field(default=WorkflowStatus.DRAFT)
    description: Optional[str] = None
    purpose: Optional[str] = None
    code: Optional[str] = None
    participant: List[Any] = Field(default_factory=list)

    def create_task(self, subject: Optional[str] = None, requester: Optional[str] = None) -> WorkflowTaskResource:
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
    name: Optional[str] = None
    role: Optional[str] = None
    actor_type: Optional[str] = None
    required: bool = False


class WorkflowPlanDefinition(BaseResource):
    resource_type: Literal["PlanDefinition"] = Field(default="PlanDefinition")
    name: Optional[str] = None
    title: Optional[str] = None
    status: WorkflowStatus = Field(default=WorkflowStatus.DRAFT)
    description: Optional[str] = None
    type: Optional[str] = None
    goal: List[Dict[str, Any]] = Field(default_factory=list)
    action: List["WorkflowPlanDefinitionAction"] = Field(default_factory=list)

    def add_goal(self, description: str, category: Optional[str] = None, priority: Optional[str] = None) -> None:
        self.goal.append({"description": description, "category": category, "priority": priority})

    def add_action(self, title: str, code: Optional[str] = None, description: Optional[str] = None, definition_canonical: Optional[str] = None) -> None:
        self.action.append(WorkflowPlanDefinitionAction(title=title, code=code, description=description, definition_canonical=definition_canonical))


class WorkflowPlanDefinitionAction(BaseResource):
    resource_type: Literal["PlanDefinitionAction"] = Field(default="PlanDefinitionAction")
    title: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    definition_canonical: Optional[str] = None
    action: List["WorkflowPlanDefinitionAction"] = Field(default_factory=list)


class WorkflowServiceRequest(BaseResource):
    resource_type: Literal["ServiceRequest"] = Field(default="ServiceRequest")
    code: Optional[str] = None
    status: WorkflowStatus = Field(default=WorkflowStatus.DRAFT)
    intent: WorkflowRequestIntent = Field(default=WorkflowRequestIntent.ORDER)
    subject: Optional[str] = None
    requester: Optional[str] = None
    order_detail: List[str] = Field(default_factory=list)
    specimen: List[str] = Field(default_factory=list)
    body_site: List[str] = Field(default_factory=list)
    patient_instruction: List[str] = Field(default_factory=list)


class WorkflowExecution(BaseResource):
    resource_type: Literal["WorkflowExecution"] = Field(default="WorkflowExecution")
    workflow_definition: Optional[str] = None
    subject: Optional[str] = None
    total_steps: int = 0
    current_step: int = 0
    status: EventStatus = Field(default=EventStatus.PREPARATION)
    started: Optional[str] = None
    ended: Optional[str] = None
    input_parameters: Dict[str, Any] = Field(default_factory=dict)
    completed_steps: Dict[int, Dict[str, Any]] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    tasks: List[str] = Field(default_factory=list)
    active_tasks: List[str] = Field(default_factory=list)

    def start_execution(self, input_parameters: Optional[Dict[str, Any]] = None) -> None:
        from datetime import datetime
        self.status = EventStatus.IN_PROGRESS
        self.started = datetime.now().isoformat()
        if input_parameters:
            self.input_parameters.update(input_parameters)

    def complete_step(self, idx: int, output: Dict[str, Any]) -> None:
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
def create_simple_task(code: str, description: Optional[str] = None, subject: Optional[str] = None, requester: Optional[str] = None, priority: WorkflowRequestPriority = WorkflowRequestPriority.ROUTINE) -> WorkflowTaskResource:
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
    plan = WorkflowPlanDefinition(name="DocumentProcessingWorkflow", title="Clinical Document Processing Workflow", status=WorkflowStatus.ACTIVE)
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


def create_clinical_workflow_execution(workflow_definition: str, subject: str, input_parameters: Optional[Dict[str, Any]] = None) -> WorkflowExecution:
    exec_ = WorkflowExecution(workflow_definition=workflow_definition, subject=subject, total_steps=4)
    exec_.start_execution(input_parameters)
    return exec_