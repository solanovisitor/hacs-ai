"""
Workflow Models - FHIR-Compatible Workflow Management System.

This module provides comprehensive workflow modeling based on FHIR workflow patterns,
including Definitions, Requests, and Events with their standard relationships and
execution capabilities.

Features:
- FHIR-compatible workflow patterns (Request, Event, Definition)
- Workflow execution and state management
- Task orchestration and coordination
- Activity and plan definitions
- Standard workflow relationships and linkages
- Integration with HACS ecosystem
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict

from ..base_resource import BaseResource


class WorkflowStatus(str, Enum):
    """Standard workflow status values across all workflow resources."""
    DRAFT = "draft"  # The resource is still under development
    ACTIVE = "active"  # The resource is ready for use
    ON_HOLD = "on-hold"  # The resource is temporarily suspended
    REVOKED = "revoked"  # The resource has been withdrawn
    COMPLETED = "completed"  # The activity described by the resource has been completed
    ENTERED_IN_ERROR = "entered-in-error"  # The resource was created in error
    UNKNOWN = "unknown"  # The authoring system does not know the status


class RequestIntent(str, Enum):
    """Intent categories for workflow requests."""
    PROPOSAL = "proposal"  # The request is a suggestion made by someone/something
    PLAN = "plan"  # The request represents an intention to ensure something occurs
    DIRECTIVE = "directive"  # The request represents a request/demand and authorization for action
    ORDER = "order"  # The request represents a request/demand and authorization for action
    ORIGINAL_ORDER = "original-order"  # The request represents an original authorization for action
    REFLEX_ORDER = "reflex-order"  # The request represents an automatically generated order
    FILLER_ORDER = "filler-order"  # The request represents the view of an authorization
    INSTANCE_ORDER = "instance-order"  # An order created in fulfillment of a broader order
    OPTION = "option"  # The request represents a component or option for a RequestGroup


class RequestPriority(str, Enum):
    """Priority levels for workflow requests."""
    ROUTINE = "routine"  # The request has normal priority
    URGENT = "urgent"  # The request should be acted upon as soon as possible
    ASAP = "asap"  # The request should be acted upon as soon as possible
    STAT = "stat"  # The request should be acted upon immediately


class EventStatus(str, Enum):
    """Status values for workflow events."""
    PREPARATION = "preparation"  # The core event has not started yet
    IN_PROGRESS = "in-progress"  # The event is currently occurring
    NOT_DONE = "not-done"  # The event was terminated prior to any activity
    ON_HOLD = "on-hold"  # The event has been temporarily stopped
    STOPPED = "stopped"  # The event has been terminated prior to completion
    COMPLETED = "completed"  # The event has been completed
    ENTERED_IN_ERROR = "entered-in-error"  # The event was entered in error
    UNKNOWN = "unknown"  # The authoring system does not know the status


class TaskStatus(str, Enum):
    """Specific status values for Task resources."""
    DRAFT = "draft"  # The task is not yet ready to be acted upon
    REQUESTED = "requested"  # The task is ready to be acted upon
    RECEIVED = "received"  # A potential performer has claimed ownership of the task
    ACCEPTED = "accepted"  # The potential performer has agreed to execute the task
    REJECTED = "rejected"  # The potential performer has declined to execute the task
    READY = "ready"  # The task is ready to be performed
    CANCELLED = "cancelled"  # The task was not completed
    IN_PROGRESS = "in-progress"  # The task has been started but is not yet complete
    ON_HOLD = "on-hold"  # The task has been started but work has been paused
    FAILED = "failed"  # The task was attempted but could not be completed successfully
    COMPLETED = "completed"  # The task has been completed
    ENTERED_IN_ERROR = "entered-in-error"  # The task was entered in error


class TaskIntent(str, Enum):
    """Intent values for Task resources."""
    UNKNOWN = "unknown"  # The intent is not known
    PROPOSAL = "proposal"  # The task is a suggestion made by someone/something
    PLAN = "plan"  # The task represents an intention to ensure something occurs
    ORDER = "order"  # The task represents a request/demand and authorization for action
    ORIGINAL_ORDER = "original-order"  # The task represents the original authorization
    REFLEX_ORDER = "reflex-order"  # The task represents an automatically generated order
    FILLER_ORDER = "filler-order"  # The task represents the view of an authorization
    INSTANCE_ORDER = "instance-order"  # The task was created in fulfillment of a broader order


class ActivityDefinitionKind(str, Enum):
    """Types of activities that can be defined."""
    APPOINTMENT = "Appointment"
    COMMUNICATION_REQUEST = "CommunicationRequest"
    DEVICE_REQUEST = "DeviceRequest"
    DIAGNOSTIC_REPORT = "DiagnosticReport"
    MEDICATION_REQUEST = "MedicationRequest"
    NUTRITION_ORDER = "NutritionOrder"
    PROCEDURE = "Procedure"
    SERVICE_REQUEST = "ServiceRequest"
    SUPPLY_REQUEST = "SupplyRequest"
    TASK = "Task"
    VISION_PRESCRIPTION = "VisionPrescription"


class WorkflowParticipant(BaseModel):
    """Participant in a workflow process."""
    model_config = ConfigDict(validate_assignment=True)
    
    id: Optional[str] = Field(None, description="Participant identifier")
    name: str = Field(..., description="Participant name")
    role: str = Field(..., description="Role in the workflow")
    actor_type: str = Field("Person", description="Type of actor (Person, Device, Organization)")
    contact: Optional[str] = Field(None, description="Contact information")
    required: bool = Field(True, description="Whether this participant is required")


class WorkflowInput(BaseModel):
    """Input parameter for a workflow."""
    model_config = ConfigDict(validate_assignment=True)
    
    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter data type")
    description: Optional[str] = Field(None, description="Parameter description")
    required: bool = Field(True, description="Whether this parameter is required")
    default_value: Optional[Any] = Field(None, description="Default value if not provided")


class WorkflowOutput(BaseModel):
    """Output parameter from a workflow."""
    model_config = ConfigDict(validate_assignment=True)
    
    name: str = Field(..., description="Output name")
    type: str = Field(..., description="Output data type")
    description: Optional[str] = Field(None, description="Output description")


# Base Workflow Patterns (following FHIR patterns)

class WorkflowDefinition(BaseResource):
    """
    Base pattern for workflow definition resources.
    
    Represents activities that could be performed in a time and subject-independent
    manner such as protocols, order sets, clinical guidelines, etc.
    """
    
    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        extra="allow"
    )
    
    # Core Definition Elements
    url: Optional[str] = Field(None, description="Canonical identifier for this definition")
    identifier: Optional[str] = Field(None, description="Additional identifier for the definition")
    version: str = Field("1.0.0", description="Business version of the definition")
    name: Optional[str] = Field(None, description="Name for this definition (computer friendly)")
    title: Optional[str] = Field(None, description="Name for this definition (human friendly)")
    subtitle: Optional[str] = Field(None, description="Subordinate title of the definition")
    
    # Status and Lifecycle
    status: WorkflowStatus = Field(WorkflowStatus.DRAFT, description="Current status of the definition")
    experimental: bool = Field(False, description="For testing purposes, not real usage")
    
    # Metadata
    subject_type: Optional[str] = Field(None, description="Type of individual the definition applies to")
    date: Optional[datetime] = Field(None, description="Date last changed")
    publisher: Optional[str] = Field(None, description="Name of the publisher")
    contact: Optional[str] = Field(None, description="Contact details for the publisher")
    description: Optional[str] = Field(None, description="Natural language description")
    purpose: Optional[str] = Field(None, description="Why this definition is defined")
    usage: Optional[str] = Field(None, description="Describes the clinical usage of the definition")
    copyright: Optional[str] = Field(None, description="Use and/or publishing restrictions")
    
    # Content
    topic: List[str] = Field(default_factory=list, description="E.g. Education, Treatment, Assessment")
    author: List[str] = Field(default_factory=list, description="Who authored the content")
    editor: List[str] = Field(default_factory=list, description="Who edited the content")
    reviewer: List[str] = Field(default_factory=list, description="Who reviewed the content")
    endorser: List[str] = Field(default_factory=list, description="Who endorsed the content")
    
    # Related Artifacts
    related_artifact: List[str] = Field(default_factory=list, description="Additional documentation, citations")
    library: List[str] = Field(default_factory=list, description="Logic used by the definition")


class WorkflowRequest(BaseResource):
    """
    Base pattern for workflow request resources.
    
    Represents proposals, plans or orders for activities to occur.
    """
    
    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        extra="allow"
    )
    
    # Core Request Elements
    identifier: List[str] = Field(default_factory=list, description="External identifier")
    instantiates_canonical: List[str] = Field(default_factory=list, description="Instantiates FHIR protocol or definition")
    instantiates_uri: List[str] = Field(default_factory=list, description="Instantiates external protocol or definition")
    based_on: List[str] = Field(default_factory=list, description="What request fulfills")
    replaces: List[str] = Field(default_factory=list, description="What request replaces")
    
    # Request Classification
    status: WorkflowStatus = Field(..., description="Current status of the request")
    intent: RequestIntent = Field(..., description="Proposal, plan, original-order, etc.")
    category: List[str] = Field(default_factory=list, description="Classification of service")
    priority: RequestPriority = Field(RequestPriority.ROUTINE, description="Routine | urgent | asap | stat")
    do_not_perform: bool = Field(False, description="True if request is prohibiting action")
    
    # Request Context
    subject: str = Field(..., description="Individual or entity the request is for")
    encounter: Optional[str] = Field(None, description="Encounter created as part of")
    occurrence_datetime: Optional[datetime] = Field(None, description="When service should occur")
    occurrence_period_start: Optional[datetime] = Field(None, description="When service should occur - start")
    occurrence_period_end: Optional[datetime] = Field(None, description="When service should occur - end")
    as_needed: bool = Field(False, description="Preconditions for service")
    authored_on: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Date request signed")
    
    # Participants
    requester: Optional[str] = Field(None, description="Who/what is requesting service")
    performer_type: Optional[str] = Field(None, description="Performer role")
    performer: Optional[str] = Field(None, description="Requested performer")
    location_code: Optional[str] = Field(None, description="Requested location")
    location_reference: Optional[str] = Field(None, description="Requested location")
    
    # Supporting Information
    reason_code: List[str] = Field(default_factory=list, description="Explanation/Justification for procedure or service")
    reason_reference: List[str] = Field(default_factory=list, description="Explanation/Justification for service")
    insurance: List[str] = Field(default_factory=list, description="Associated insurance coverage")
    supporting_info: List[str] = Field(default_factory=list, description="Additional clinical information")
    note: List[str] = Field(default_factory=list, description="Comments")
    relevant_history: List[str] = Field(default_factory=list, description="Request provenance")


class WorkflowEvent(BaseResource):
    """
    Base pattern for workflow event resources.
    
    Represents ongoing or completed execution of activities or observations.
    """
    
    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        extra="allow"
    )
    
    # Core Event Elements
    identifier: List[str] = Field(default_factory=list, description="External identifier")
    instantiates_canonical: List[str] = Field(default_factory=list, description="Instantiates FHIR protocol or definition")
    instantiates_uri: List[str] = Field(default_factory=list, description="Instantiates external protocol or definition")
    based_on: List[str] = Field(default_factory=list, description="Fulfills plan, proposal or order")
    part_of: List[str] = Field(default_factory=list, description="Part of referenced event")
    
    # Event Classification
    status: EventStatus = Field(..., description="Current status of the event")
    status_reason: Optional[str] = Field(None, description="Reason for current status")
    category: List[str] = Field(default_factory=list, description="Classification of service")
    
    # Event Context
    subject: str = Field(..., description="Individual or entity the event is for")
    encounter: Optional[str] = Field(None, description="Healthcare event during which this occurred")
    occurrence_datetime: Optional[datetime] = Field(None, description="When event occurred")
    occurrence_period_start: Optional[datetime] = Field(None, description="When event occurred - start")
    occurrence_period_end: Optional[datetime] = Field(None, description="When event occurred - end")
    recorded: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="When event was recorded")
    
    # Participants
    performer: List[WorkflowParticipant] = Field(default_factory=list, description="Who performed event")
    location: Optional[str] = Field(None, description="Where event occurred")
    
    # Supporting Information
    reason_code: List[str] = Field(default_factory=list, description="Coded reason why event occurred")
    reason_reference: List[str] = Field(default_factory=list, description="Why event occurred")
    note: List[str] = Field(default_factory=list, description="Comments about the event")


# Specific Workflow Resources

class Task(WorkflowRequest):
    """
    A task resource describes an activity that can be performed and tracks the state of completion.
    
    Tasks have a dual nature - they can be both requests (asking for work to be done) and 
    events (tracking the state of work being done).
    """
    
    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        extra="allow",
        json_schema_extra={
            "examples": [
                {
                    "id": "task-001",
                    "resource_type": "Task",
                    "status": "requested",
                    "intent": "order",
                    "code": "process-clinical-document",
                    "description": "Process and validate clinical document",
                    "for": "patient-001",
                    "owner": "system-processor",
                    "input": [{"name": "document_id", "type": "string", "value": "doc-123"}],
                    "output": [{"name": "validation_result", "type": "boolean"}]
                }
            ]
        }
    )
    
    # Override resource_type
    resource_type: str = Field(default="Task", frozen=True)
    
    # Task-specific status
    status: TaskStatus = Field(..., description="Current status of the task")
    intent: TaskIntent = Field(..., description="Unknown | proposal | plan | order")
    
    # Task Definition
    code: str = Field(..., description="Task type or code")
    description: Optional[str] = Field(None, description="Human-readable description of task")
    focus: Optional[str] = Field(None, description="What task is acting on")
    for_resource: Optional[str] = Field(None, description="Beneficiary of the task", alias="for")
    
    # Task Context
    group_identifier: Optional[str] = Field(None, description="Requisition or grouper id")
    part_of: List[str] = Field(default_factory=list, description="Composite task")
    
    # Task Management
    business_status: Optional[str] = Field(None, description="E.g. 'Waiting for patient', 'Available'")
    owner: Optional[str] = Field(None, description="Responsible individual or organization")
    last_modified: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Task last modified date")
    
    # Task Execution
    execution_period_start: Optional[datetime] = Field(None, description="Start and end time of execution")
    execution_period_end: Optional[datetime] = Field(None, description="Start and end time of execution")
    restriction_period_start: Optional[datetime] = Field(None, description="When the task can be performed")
    restriction_period_end: Optional[datetime] = Field(None, description="When the task can be performed")
    restriction_recipients: List[str] = Field(default_factory=list, description="For whom is task restricted")
    
    # Task Parameters
    input: List[WorkflowInput] = Field(default_factory=list, description="Information used to perform task")
    output: List[WorkflowOutput] = Field(default_factory=list, description="Information produced by task")
    
    def add_input(self, name: str, value: Any, type_name: str = "string", required: bool = True) -> "Task":
        """Add an input parameter to the task."""
        input_param = WorkflowInput(
            name=name,
            type=type_name,
            required=required,
            default_value=value
        )
        self.input.append(input_param)
        return self
    
    def add_output(self, name: str, type_name: str = "string", description: Optional[str] = None) -> "Task":
        """Add an output parameter to the task."""
        output_param = WorkflowOutput(
            name=name,
            type=type_name,
            description=description
        )
        self.output.append(output_param)
        return self
    
    def complete(self, outputs: Optional[Dict[str, Any]] = None) -> "Task":
        """Mark the task as completed and set outputs."""
        self.status = TaskStatus.COMPLETED
        self.execution_period_end = datetime.now(timezone.utc)
        self.last_modified = datetime.now(timezone.utc)
        
        if outputs:
            for name, value in outputs.items():
                self.add_output(name, type(value).__name__)
        
        return self
    
    def fail(self, reason: Optional[str] = None) -> "Task":
        """Mark the task as failed."""
        self.status = TaskStatus.FAILED
        self.execution_period_end = datetime.now(timezone.utc)
        self.last_modified = datetime.now(timezone.utc)
        
        if reason:
            self.note.append(f"Task failed: {reason}")
        
        return self


class ActivityDefinition(WorkflowDefinition):
    """
    Resource that allows for the definition of some activity to be performed.
    
    Typically represents a single step in a larger workflow or protocol.
    """
    
    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        extra="allow",
        json_schema_extra={
            "examples": [
                {
                    "id": "activity-def-001",
                    "resource_type": "ActivityDefinition",
                    "name": "DocumentValidation",
                    "title": "Clinical Document Validation",
                    "status": "active",
                    "kind": "Task",
                    "description": "Validate clinical document against FHIR standards",
                    "purpose": "Ensure document quality and compliance"
                }
            ]
        }
    )
    
    # Override resource_type
    resource_type: str = Field(default="ActivityDefinition", frozen=True)
    
    # Activity Definition Specifics
    kind: ActivityDefinitionKind = Field(..., description="Kind of resource")
    profile: Optional[str] = Field(None, description="What profile the resource needs to conform to")
    code: Optional[str] = Field(None, description="Detail type of activity")
    intent: Optional[RequestIntent] = Field(None, description="Proposal | plan | directive | order")
    priority: Optional[RequestPriority] = Field(None, description="Routine | urgent | asap | stat")
    do_not_perform: bool = Field(False, description="True if the activity should not be performed")
    
    # Timing and Location
    timing_datetime: Optional[datetime] = Field(None, description="When activity is to occur")
    timing_period_start: Optional[datetime] = Field(None, description="When activity is to occur")
    timing_period_end: Optional[datetime] = Field(None, description="When activity is to occur")
    location: Optional[str] = Field(None, description="Where it should happen")
    
    # Participants
    participant: List[WorkflowParticipant] = Field(default_factory=list, description="Who should participate in the action")
    
    # Product and Dosage (for medication-related activities)
    product_reference: Optional[str] = Field(None, description="What's administered/supplied")
    product_code: Optional[str] = Field(None, description="What's administered/supplied")
    quantity: Optional[float] = Field(None, description="How much is administered/consumed/supplied")
    dosage: List[str] = Field(default_factory=list, description="Detailed dosage instructions")
    
    # Body Site and Specimen
    body_site: List[str] = Field(default_factory=list, description="What part of body to perform on")
    specimen_requirement: List[str] = Field(default_factory=list, description="What specimens are required")
    observation_requirement: List[str] = Field(default_factory=list, description="What observations are required")
    observation_result_requirement: List[str] = Field(default_factory=list, description="What observations must be produced")
    
    # Dynamic Values
    transform: Optional[str] = Field(None, description="Transform to apply the template")
    dynamic_value: Dict[str, Any] = Field(default_factory=dict, description="Dynamic aspects of the definition")
    
    def create_task(
        self,
        subject: str,
        requester: Optional[str] = None,
        **kwargs
    ) -> Task:
        """Create a Task based on this ActivityDefinition."""
        task = Task(
            code=self.code or self.name or "activity",
            description=self.description,
            status=TaskStatus.REQUESTED,
            intent=TaskIntent.ORDER,
            subject=subject,
            requester=requester,
            **kwargs
        )
        
        # Set references to this definition
        task.instantiates_canonical.append(self.url or self.id)
        
        return task


class PlanDefinition(WorkflowDefinition):
    """
    Resource that defines a plan for a series of actions to be taken.
    
    Represents complex workflows, protocols, guidelines, or care plans.
    """
    
    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        extra="allow",
        json_schema_extra={
            "examples": [
                {
                    "id": "plan-def-001",
                    "resource_type": "PlanDefinition",
                    "name": "ClinicalDocumentWorkflow",
                    "title": "Clinical Document Processing Workflow",
                    "status": "active",
                    "type": "workflow-definition",
                    "description": "Complete workflow for processing clinical documents",
                    "goal": [{"description": "Ensure document quality and compliance"}],
                    "action": [
                        {
                            "title": "Validate Document",
                            "code": "validate",
                            "timing_datetime": None,
                            "participant": [],
                            "type": "create",
                            "definition_canonical": "ActivityDefinition/document-validation"
                        }
                    ]
                }
            ]
        }
    )
    
    # Override resource_type
    resource_type: str = Field(default="PlanDefinition", frozen=True)
    
    # Plan Definition Specifics
    type: str = Field("workflow-definition", description="order-set | clinical-protocol | eca-rule | workflow-definition")
    subject_code: Optional[str] = Field(None, description="Type of individual the plan applies to")
    
    # Goals and Objectives
    goal: List[Dict[str, Any]] = Field(default_factory=list, description="What the plan is trying to accomplish")
    
    # Actions and Steps
    action: List["PlanDefinitionAction"] = Field(default_factory=list, description="Action defined by the plan")
    
    def add_goal(self, description: str, category: Optional[str] = None, priority: Optional[str] = None) -> "PlanDefinition":
        """Add a goal to the plan definition."""
        goal = {
            "description": description,
            "category": category,
            "priority": priority
        }
        self.goal.append(goal)
        return self
    
    def add_action(
        self,
        title: str,
        code: str,
        description: Optional[str] = None,
        definition_canonical: Optional[str] = None,
        **kwargs
    ) -> "PlanDefinition":
        """Add an action to the plan definition."""
        action = PlanDefinitionAction(
            title=title,
            code=code,
            description=description,
            definition_canonical=definition_canonical,
            **kwargs
        )
        self.action.append(action)
        return self


class PlanDefinitionAction(BaseModel):
    """An action defined by a PlanDefinition."""
    model_config = ConfigDict(validate_assignment=True, use_enum_values=True)
    
    # Action Identification
    prefix: Optional[str] = Field(None, description="User-visible prefix for the action")
    title: Optional[str] = Field(None, description="User-visible title")
    description: Optional[str] = Field(None, description="Brief description of the action")
    text_equivalent: Optional[str] = Field(None, description="Static text equivalent of the action")
    
    # Action Classification
    code: Optional[str] = Field(None, description="Code representing the meaning of the action")
    reason: List[str] = Field(default_factory=list, description="Why the action should be performed")
    documentation: List[str] = Field(default_factory=list, description="Supporting documentation for the action")
    
    # Action Triggers and Conditions
    trigger: List[str] = Field(default_factory=list, description="When the action should be triggered")
    condition: List[str] = Field(default_factory=list, description="Whether or not the action is applicable")
    
    # Action Relationships
    related_action: List[str] = Field(default_factory=list, description="Relationship to another action")
    
    # Action Timing
    timing_datetime: Optional[datetime] = Field(None, description="When the action should take place")
    timing_age: Optional[str] = Field(None, description="When the action should take place")
    timing_period_start: Optional[datetime] = Field(None, description="When the action should take place")
    timing_period_end: Optional[datetime] = Field(None, description="When the action should take place")
    timing_duration: Optional[str] = Field(None, description="How long the action should take place")
    timing_range: Optional[str] = Field(None, description="When the action should take place")
    
    # Participants
    participant: List[WorkflowParticipant] = Field(default_factory=list, description="Who should participate")
    
    # Action Type and Behavior
    type: Optional[str] = Field(None, description="create | update | remove | fire-event")
    grouping_behavior: Optional[str] = Field(None, description="visual-group | logical-group | sentence-group")
    selection_behavior: Optional[str] = Field(None, description="any | all | all-or-none | exactly-one | at-most-one | one-or-more")
    required_behavior: Optional[str] = Field(None, description="must | could | must-unless-documented")
    precheck_behavior: Optional[str] = Field(None, description="yes | no")
    cardinality_behavior: Optional[str] = Field(None, description="single | multiple")
    
    # Action Definition
    definition_canonical: Optional[str] = Field(None, description="Description of the activity to be performed")
    definition_uri: Optional[str] = Field(None, description="Description of the activity to be performed")
    transform: Optional[str] = Field(None, description="Transform to apply the template")
    
    # Dynamic Values
    dynamic_value: Dict[str, Any] = Field(default_factory=dict, description="Dynamic aspects of the definition")
    
    # Nested Actions
    action: List["PlanDefinitionAction"] = Field(default_factory=list, description="A sub-action")


# Forward reference resolution
PlanDefinitionAction.model_rebuild()


class ServiceRequest(WorkflowRequest):
    """
    A record of a request for a procedure or diagnostic or other service to be performed.
    """
    
    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        extra="allow",
        json_schema_extra={
            "examples": [
                {
                    "id": "service-request-001",
                    "resource_type": "ServiceRequest",
                    "status": "active",
                    "intent": "order",
                    "code": "document-analysis",
                    "subject": "patient-001",
                    "requester": "physician-001",
                    "occurrence_datetime": "2024-01-15T10:30:00Z"
                }
            ]
        }
    )
    
    # Override resource_type
    resource_type: str = Field(default="ServiceRequest", frozen=True)
    
    # Service Request Specifics
    code: str = Field(..., description="What is being requested/ordered")
    order_detail: List[str] = Field(default_factory=list, description="Additional order information")
    quantity_quantity: Optional[float] = Field(None, description="Service amount")
    quantity_ratio: Optional[str] = Field(None, description="Service amount")
    quantity_range: Optional[str] = Field(None, description="Service amount")
    
    # Specimen and Body Site
    specimen: List[str] = Field(default_factory=list, description="Procedure Samples")
    body_site: List[str] = Field(default_factory=list, description="Location on Body")
    
    # Service Context
    patient_instruction: List[str] = Field(default_factory=list, description="Patient or consumer-oriented instructions")


class WorkflowExecution(BaseResource):
    """
    Manages the execution state and coordination of complex workflows.
    
    Tracks the progress of PlanDefinition executions and coordinates Task activities.
    """
    
    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        extra="allow",
        json_schema_extra={
            "examples": [
                {
                    "id": "workflow-exec-001",
                    "resource_type": "WorkflowExecution",
                    "workflow_definition": "PlanDefinition/clinical-document-workflow",
                    "subject": "patient-001",
                    "status": "in-progress",
                    "started": "2024-01-15T10:30:00Z",
                    "current_step": 2,
                    "total_steps": 5
                }
            ]
        }
    )
    
    # Override resource_type
    resource_type: str = Field(default="WorkflowExecution", frozen=True)
    
    # Workflow Execution Context
    workflow_definition: str = Field(..., description="Reference to PlanDefinition being executed")
    subject: str = Field(..., description="Subject of the workflow execution")
    encounter: Optional[str] = Field(None, description="Healthcare encounter context")
    
    # Execution State
    status: EventStatus = Field(EventStatus.PREPARATION, description="Current execution status")
    started: Optional[datetime] = Field(None, description="When execution started")
    ended: Optional[datetime] = Field(None, description="When execution ended")
    
    # Progress Tracking
    current_step: int = Field(0, description="Current step in the workflow")
    total_steps: int = Field(0, description="Total number of steps")
    completed_steps: List[int] = Field(default_factory=list, description="List of completed step indices")
    
    # Task Management
    tasks: List[str] = Field(default_factory=list, description="Tasks created for this workflow execution")
    active_tasks: List[str] = Field(default_factory=list, description="Currently active tasks")
    
    # Execution Context
    input_parameters: Dict[str, Any] = Field(default_factory=dict, description="Input parameters for workflow")
    output_results: Dict[str, Any] = Field(default_factory=dict, description="Output results from workflow")
    execution_context: Dict[str, Any] = Field(default_factory=dict, description="Execution context and variables")
    
    # Error Handling
    errors: List[str] = Field(default_factory=list, description="Errors encountered during execution")
    warnings: List[str] = Field(default_factory=list, description="Warnings during execution")
    
    def start_execution(self, input_parameters: Optional[Dict[str, Any]] = None) -> "WorkflowExecution":
        """Start the workflow execution."""
        self.status = EventStatus.IN_PROGRESS
        self.started = datetime.now(timezone.utc)
        if input_parameters:
            self.input_parameters.update(input_parameters)
        return self
    
    def complete_execution(self, output_results: Optional[Dict[str, Any]] = None) -> "WorkflowExecution":
        """Complete the workflow execution."""
        self.status = EventStatus.COMPLETED
        self.ended = datetime.now(timezone.utc)
        if output_results:
            self.output_results.update(output_results)
        return self
    
    def fail_execution(self, error_message: str) -> "WorkflowExecution":
        """Fail the workflow execution."""
        self.status = EventStatus.STOPPED
        self.ended = datetime.now(timezone.utc)
        self.errors.append(error_message)
        return self
    
    def add_task(self, task_id: str, active: bool = True) -> "WorkflowExecution":
        """Add a task to this workflow execution."""
        self.tasks.append(task_id)
        if active:
            self.active_tasks.append(task_id)
        return self
    
    def complete_step(self, step_index: int, outputs: Optional[Dict[str, Any]] = None) -> "WorkflowExecution":
        """Complete a workflow step."""
        if step_index not in self.completed_steps:
            self.completed_steps.append(step_index)
        
        if outputs:
            self.execution_context.update(outputs)
        
        # Update current step to next incomplete step
        for i in range(self.total_steps):
            if i not in self.completed_steps:
                self.current_step = i
                break
        else:
            # All steps completed
            if len(self.completed_steps) == self.total_steps:
                self.complete_execution()
        
        return self


# Factory functions for common workflow patterns

def create_simple_task(
    code: str,
    description: str,
    subject: str,
    requester: Optional[str] = None,
    priority: RequestPriority = RequestPriority.ROUTINE,
    **kwargs
) -> Task:
    """Create a simple task with minimal configuration."""
    return Task(
        code=code,
        description=description,
        status=TaskStatus.REQUESTED,
        intent=TaskIntent.ORDER,
        subject=subject,
        requester=requester,
        priority=priority,
        **kwargs
    )


def create_document_processing_workflow() -> PlanDefinition:
    """Create a standard document processing workflow definition."""
    plan = PlanDefinition(
        name="DocumentProcessingWorkflow",
        title="Clinical Document Processing Workflow",
        status=WorkflowStatus.ACTIVE,
        description="Standard workflow for processing and validating clinical documents",
        purpose="Ensure document quality, compliance, and proper integration into patient records"
    )
    
    # Add workflow goals
    plan.add_goal("Validate document structure and content")
    plan.add_goal("Extract clinical information")
    plan.add_goal("Integrate with patient record")
    plan.add_goal("Ensure compliance with standards")
    
    # Add workflow actions
    plan.add_action(
        title="Document Validation",
        code="validate-document",
        description="Validate document against FHIR and clinical standards",
        definition_canonical="ActivityDefinition/document-validation"
    )
    
    plan.add_action(
        title="Content Extraction",
        code="extract-content", 
        description="Extract structured clinical information from document",
        definition_canonical="ActivityDefinition/content-extraction"
    )
    
    plan.add_action(
        title="Quality Assessment",
        code="assess-quality",
        description="Assess document quality and completeness",
        definition_canonical="ActivityDefinition/quality-assessment"
    )
    
    plan.add_action(
        title="Integration",
        code="integrate-document",
        description="Integrate document into patient record system",
        definition_canonical="ActivityDefinition/document-integration"
    )
    
    return plan


def create_clinical_workflow_execution(
    workflow_definition: str,
    subject: str,
    input_parameters: Optional[Dict[str, Any]] = None
) -> WorkflowExecution:
    """Create a workflow execution for clinical processes."""
    execution = WorkflowExecution(
        workflow_definition=workflow_definition,
        subject=subject,
        total_steps=4,  # Standard clinical workflow steps
        input_parameters=input_parameters or {}
    )
    
    execution.start_execution(input_parameters)
    return execution