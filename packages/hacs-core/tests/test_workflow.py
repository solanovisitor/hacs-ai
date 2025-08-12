"""
Test suite for Workflow and related components.
"""

import pytest
from datetime import datetime, timezone

from hacs_core.models import (
    # Base Patterns
    WorkflowDefinition,
    WorkflowRequest,
    WorkflowEvent,
    # Enums
    WorkflowStatus,
    WorkflowRequestIntent as RequestIntent,
    WorkflowRequestPriority as RequestPriority,
    EventStatus,
    WorkflowTaskStatus as TaskStatus,
    WorkflowTaskIntent as TaskIntent,
    WorkflowActivityDefinitionKind as ActivityDefinitionKind,
    # Core Resources
    WorkflowTaskResource as Task,
    WorkflowActivityDefinition as ActivityDefinition,
    WorkflowPlanDefinition as PlanDefinition,
    WorkflowPlanDefinitionAction as PlanDefinitionAction,
    WorkflowServiceRequest as ServiceRequest,
    WorkflowExecution,
    # Supporting Types
    WorkflowParticipant,
    # Factory Functions
    create_simple_task,
    create_document_processing_workflow,
    create_clinical_workflow_execution,
)


class TestWorkflowPatterns:
    """Test base workflow patterns."""

    def test_workflow_definition_creation(self):
        """Test WorkflowDefinition base pattern."""
        definition = WorkflowDefinition(
            name="TestDefinition",
            title="Test Workflow Definition",
            status=WorkflowStatus.ACTIVE,
            version="1.0.0",
            description="A test workflow definition"
        )
        
        assert definition.name == "TestDefinition"
        assert definition.title == "Test Workflow Definition"
        assert definition.status == WorkflowStatus.ACTIVE
        assert definition.version == "1.0.0"
        assert definition.resource_type == "WorkflowDefinition"

    def test_workflow_request_creation(self):
        """Test WorkflowRequest base pattern."""
        request = WorkflowRequest(
            status=WorkflowStatus.ACTIVE,
            intent=RequestIntent.ORDER,
            subject="patient-001",
            priority=RequestPriority.URGENT
        )
        
        assert request.status == WorkflowStatus.ACTIVE
        assert request.intent == RequestIntent.ORDER
        assert request.subject == "patient-001"
        assert request.priority == RequestPriority.URGENT
        assert request.resource_type == "WorkflowRequest"

    def test_workflow_event_creation(self):
        """Test WorkflowEvent base pattern."""
        event = WorkflowEvent(
            status=EventStatus.COMPLETED,
            subject="patient-001"
        )
        
        assert event.status == EventStatus.COMPLETED
        assert event.subject == "patient-001"
        assert event.resource_type == "WorkflowEvent"
        assert event.recorded is not None


class TestTask:
    """Test Task resource functionality."""

    def test_basic_task_creation(self):
        """Test basic Task creation."""
        task = Task(
            code="process-document",
            description="Process clinical document",
            status=TaskStatus.REQUESTED,
            intent=TaskIntent.ORDER,
            subject="patient-001"
        )
        
        assert task.code == "process-document"
        assert task.description == "Process clinical document"
        assert task.status == TaskStatus.REQUESTED
        assert task.intent == TaskIntent.ORDER
        assert task.subject == "patient-001"
        assert task.resource_type == "Task"

    def test_task_input_output(self):
        """Test task input and output management."""
        task = Task(
            code="validate-document",
            status=TaskStatus.REQUESTED,
            intent=TaskIntent.ORDER,
            subject="patient-001"
        )
        
        # Add inputs
        task.add_input("document_id", "doc-123", "string")
        task.add_input("validation_level", "strict", "string")
        
        # Add outputs
        task.add_output("validation_result", "boolean", "Whether document is valid")
        task.add_output("error_count", "integer", "Number of validation errors")
        
        assert len(task.input) == 2
        assert len(task.output) == 2
        
        assert task.input[0].name == "document_id"
        assert task.input[0].default_value == "doc-123"
        assert task.output[0].name == "validation_result"
        assert task.output[0].type == "boolean"

    def test_task_completion(self):
        """Test task completion workflow."""
        task = Task(
            code="process-data",
            status=TaskStatus.IN_PROGRESS,
            intent=TaskIntent.ORDER,
            subject="patient-001"
        )
        
        # Complete the task
        outputs = {"result": "success", "records_processed": 42}
        task.complete(outputs)
        
        assert task.status == TaskStatus.COMPLETED
        assert task.execution_period_end is not None
        assert task.last_modified is not None

    def test_task_failure(self):
        """Test task failure handling."""
        task = Task(
            code="process-data",
            status=TaskStatus.IN_PROGRESS,
            intent=TaskIntent.ORDER,
            subject="patient-001"
        )
        
        # Fail the task
        task.fail("Invalid data format")
        
        assert task.status == TaskStatus.FAILED
        assert task.execution_period_end is not None
        assert "Task failed: Invalid data format" in task.note

    def test_task_chaining(self):
        """Test task method chaining."""
        task = (Task(
            code="complex-task",
            status=TaskStatus.REQUESTED,
            intent=TaskIntent.ORDER,
            subject="patient-001"
        )
        .add_input("param1", "value1")
        .add_input("param2", 42, "integer")
        .add_output("result", "string"))
        
        assert len(task.input) == 2
        assert len(task.output) == 1
        assert task.input[0].name == "param1"
        assert task.input[1].default_value == 42


class TestActivityDefinition:
    """Test ActivityDefinition functionality."""

    def test_activity_definition_creation(self):
        """Test ActivityDefinition creation."""
        activity = ActivityDefinition(
            name="DocumentValidation",
            title="Clinical Document Validation",
            status=WorkflowStatus.ACTIVE,
            kind=ActivityDefinitionKind.TASK,
            description="Validate clinical document against standards",
            purpose="Ensure document quality and compliance"
        )
        
        assert activity.name == "DocumentValidation"
        assert activity.title == "Clinical Document Validation"
        assert activity.status == WorkflowStatus.ACTIVE
        assert activity.kind == ActivityDefinitionKind.TASK
        assert activity.resource_type == "ActivityDefinition"

    def test_activity_definition_participants(self):
        """Test activity definition participants."""
        activity = ActivityDefinition(
            name="ReviewProcess",
            status=WorkflowStatus.ACTIVE,
            kind=ActivityDefinitionKind.TASK
        )
        
        # Add participants
        participant1 = WorkflowParticipant(
            name="Dr. Smith",
            role="reviewer",
            actor_type="Person",
            required=True
        )
        
        participant2 = WorkflowParticipant(
            name="System Validator",
            role="validator",
            actor_type="Device",
            required=False
        )
        
        activity.participant = [participant1, participant2]
        
        assert len(activity.participant) == 2
        assert activity.participant[0].name == "Dr. Smith"
        assert activity.participant[0].required is True
        assert activity.participant[1].actor_type == "Device"

    def test_create_task_from_activity_definition(self):
        """Test creating a Task from an ActivityDefinition."""
        activity = ActivityDefinition(
            name="DataProcessing",
            title="Process Clinical Data",
            status=WorkflowStatus.ACTIVE,
            kind=ActivityDefinitionKind.TASK,
            code="process-data",
            description="Process and validate clinical data"
        )
        
        task = activity.create_task(
            subject="patient-001",
            requester="physician-001"
        )
        
        assert task.code == "process-data"
        assert task.description == "Process and validate clinical data"
        assert task.subject == "patient-001"
        assert task.requester == "physician-001"
        assert task.status == TaskStatus.REQUESTED
        assert task.intent == TaskIntent.ORDER
        assert activity.id in task.instantiates_canonical


class TestPlanDefinition:
    """Test PlanDefinition functionality."""

    def test_plan_definition_creation(self):
        """Test PlanDefinition creation."""
        plan = PlanDefinition(
            name="ClinicalWorkflow",
            title="Clinical Document Workflow",
            status=WorkflowStatus.ACTIVE,
            description="Complete workflow for clinical document processing",
            type="workflow-definition"
        )
        
        assert plan.name == "ClinicalWorkflow"
        assert plan.title == "Clinical Document Workflow"
        assert plan.status == WorkflowStatus.ACTIVE
        assert plan.type == "workflow-definition"
        assert plan.resource_type == "PlanDefinition"

    def test_plan_definition_goals(self):
        """Test plan definition goals management."""
        plan = PlanDefinition(
            name="QualityWorkflow",
            status=WorkflowStatus.ACTIVE
        )
        
        plan.add_goal("Ensure data quality", "quality", "high")
        plan.add_goal("Maintain compliance", "compliance", "medium")
        
        assert len(plan.goal) == 2
        assert plan.goal[0]["description"] == "Ensure data quality"
        assert plan.goal[0]["category"] == "quality"
        assert plan.goal[0]["priority"] == "high"

    def test_plan_definition_actions(self):
        """Test plan definition actions management."""
        plan = PlanDefinition(
            name="ProcessingWorkflow",
            status=WorkflowStatus.ACTIVE
        )
        
        plan.add_action(
            title="Validate Input",
            code="validate",
            description="Validate input data",
            definition_canonical="ActivityDefinition/input-validation"
        )
        
        plan.add_action(
            title="Process Data",
            code="process",
            description="Process validated data",
            definition_canonical="ActivityDefinition/data-processing"
        )
        
        assert len(plan.action) == 2
        assert plan.action[0].title == "Validate Input"
        assert plan.action[0].code == "validate"
        assert plan.action[1].definition_canonical == "ActivityDefinition/data-processing"

    def test_nested_plan_actions(self):
        """Test nested actions in plan definitions."""
        action = PlanDefinitionAction(
            title="Main Process",
            code="main-process",
            description="Main processing workflow"
        )
        
        # Add nested actions
        sub_action1 = PlanDefinitionAction(
            title="Sub Process 1",
            code="sub-1",
            description="First sub-process"
        )
        
        sub_action2 = PlanDefinitionAction(
            title="Sub Process 2", 
            code="sub-2",
            description="Second sub-process"
        )
        
        action.action = [sub_action1, sub_action2]
        
        assert len(action.action) == 2
        assert action.action[0].title == "Sub Process 1"
        assert action.action[1].code == "sub-2"


class TestServiceRequest:
    """Test ServiceRequest functionality."""

    def test_service_request_creation(self):
        """Test ServiceRequest creation."""
        request = ServiceRequest(
            code="document-analysis",
            status=WorkflowStatus.ACTIVE,
            intent=RequestIntent.ORDER,
            subject="patient-001",
            requester="physician-001"
        )
        
        assert request.code == "document-analysis"
        assert request.status == WorkflowStatus.ACTIVE
        assert request.intent == RequestIntent.ORDER
        assert request.subject == "patient-001"
        assert request.requester == "physician-001"
        assert request.resource_type == "ServiceRequest"

    def test_service_request_details(self):
        """Test service request additional details."""
        request = ServiceRequest(
            code="lab-analysis",
            status=WorkflowStatus.ACTIVE,
            intent=RequestIntent.ORDER,
            subject="patient-001"
        )
        
        request.order_detail = ["urgent", "fasting-required"]
        request.specimen = ["blood-sample-001"]
        request.body_site = ["left-arm"]
        request.patient_instruction = ["Fast for 12 hours before test"]
        
        assert "urgent" in request.order_detail
        assert "blood-sample-001" in request.specimen
        assert "left-arm" in request.body_site
        assert len(request.patient_instruction) == 1


class TestWorkflowExecution:
    """Test WorkflowExecution functionality."""

    def test_workflow_execution_creation(self):
        """Test WorkflowExecution creation."""
        execution = WorkflowExecution(
            workflow_definition="PlanDefinition/clinical-workflow",
            subject="patient-001",
            total_steps=5
        )
        
        assert execution.workflow_definition == "PlanDefinition/clinical-workflow"
        assert execution.subject == "patient-001"
        assert execution.total_steps == 5
        assert execution.current_step == 0
        assert execution.status == EventStatus.PREPARATION
        assert execution.resource_type == "WorkflowExecution"

    def test_workflow_execution_lifecycle(self):
        """Test workflow execution lifecycle."""
        execution = WorkflowExecution(
            workflow_definition="PlanDefinition/test-workflow",
            subject="patient-001",
            total_steps=3
        )
        
        # Start execution
        input_params = {"document_id": "doc-123", "priority": "high"}
        execution.start_execution(input_params)
        
        assert execution.status == EventStatus.IN_PROGRESS
        assert execution.started is not None
        assert execution.input_parameters["document_id"] == "doc-123"
        
        # Complete steps
        execution.complete_step(0, {"step1_result": "success"})
        assert 0 in execution.completed_steps
        assert execution.current_step == 1
        
        execution.complete_step(1, {"step2_result": "validated"})
        execution.complete_step(2, {"step3_result": "integrated"})
        
        # Should auto-complete when all steps done
        assert execution.status == EventStatus.COMPLETED
        assert execution.ended is not None

    def test_workflow_execution_failure(self):
        """Test workflow execution failure handling."""
        execution = WorkflowExecution(
            workflow_definition="PlanDefinition/test-workflow",
            subject="patient-001"
        )
        
        execution.start_execution()
        execution.fail_execution("Critical validation error")
        
        assert execution.status == EventStatus.STOPPED
        assert execution.ended is not None
        assert "Critical validation error" in execution.errors

    def test_workflow_task_management(self):
        """Test workflow task management."""
        execution = WorkflowExecution(
            workflow_definition="PlanDefinition/task-workflow",
            subject="patient-001"
        )
        
        # Add tasks
        execution.add_task("task-001", active=True)
        execution.add_task("task-002", active=False)
        execution.add_task("task-003", active=True)
        
        assert len(execution.tasks) == 3
        assert len(execution.active_tasks) == 2
        assert "task-001" in execution.active_tasks
        assert "task-002" not in execution.active_tasks


class TestFactoryFunctions:
    """Test workflow factory functions."""

    def test_create_simple_task(self):
        """Test create_simple_task factory function."""
        task = create_simple_task(
            code="validate-data",
            description="Validate patient data",
            subject="patient-001",
            requester="system",
            priority=RequestPriority.URGENT
        )
        
        assert task.code == "validate-data"
        assert task.description == "Validate patient data"
        assert task.subject == "patient-001"
        assert task.requester == "system"
        assert task.priority == RequestPriority.URGENT
        assert task.status == TaskStatus.REQUESTED
        assert task.intent == TaskIntent.ORDER

    def test_create_document_processing_workflow(self):
        """Test create_document_processing_workflow factory function."""
        workflow = create_document_processing_workflow()
        
        assert workflow.name == "DocumentProcessingWorkflow"
        assert workflow.title == "Clinical Document Processing Workflow"
        assert workflow.status == WorkflowStatus.ACTIVE
        assert len(workflow.goal) == 4
        assert len(workflow.action) == 4
        
        # Check goals
        goal_descriptions = [goal["description"] for goal in workflow.goal]
        assert "Validate document structure and content" in goal_descriptions
        assert "Extract clinical information" in goal_descriptions
        
        # Check actions
        action_codes = [action.code for action in workflow.action]
        assert "validate-document" in action_codes
        assert "extract-content" in action_codes
        assert "assess-quality" in action_codes
        assert "integrate-document" in action_codes

    def test_create_clinical_workflow_execution(self):
        """Test create_clinical_workflow_execution factory function."""
        input_params = {"document_id": "doc-123", "patient_id": "patient-001"}
        
        execution = create_clinical_workflow_execution(
            workflow_definition="PlanDefinition/clinical-workflow",
            subject="patient-001",
            input_parameters=input_params
        )
        
        assert execution.workflow_definition == "PlanDefinition/clinical-workflow"
        assert execution.subject == "patient-001"
        assert execution.total_steps == 4
        assert execution.status == EventStatus.IN_PROGRESS
        assert execution.input_parameters["document_id"] == "doc-123"
        assert execution.started is not None


class TestWorkflowIntegration:
    """Test workflow integration scenarios."""

    def test_activity_to_task_to_execution(self):
        """Test full workflow from ActivityDefinition to Task to Execution."""
        # Create ActivityDefinition
        activity = ActivityDefinition(
            name="DocumentReview",
            title="Clinical Document Review",
            status=WorkflowStatus.ACTIVE,
            kind=ActivityDefinitionKind.TASK,
            code="review-document",
            description="Review clinical document for accuracy"
        )
        
        # Create Task from ActivityDefinition
        task = activity.create_task(
            subject="patient-001",
            requester="physician-001"
        )
        
        # Create WorkflowExecution and add Task
        execution = WorkflowExecution(
            workflow_definition="PlanDefinition/review-workflow",
            subject="patient-001",
            total_steps=1
        )
        
        execution.start_execution()
        execution.add_task(task.id)
        
        # Complete task and step
        task.complete({"review_status": "approved"})
        execution.complete_step(0, {"task_result": "completed"})
        
        assert task.status == TaskStatus.COMPLETED
        assert execution.status == EventStatus.COMPLETED
        assert task.id in execution.tasks

    def test_plan_definition_to_execution(self):
        """Test creating execution from PlanDefinition."""
        # Create PlanDefinition
        plan = PlanDefinition(
            name="QualityAssurance",
            title="Quality Assurance Workflow",
            status=WorkflowStatus.ACTIVE,
            description="Complete quality assurance process"
        )
        
        plan.add_goal("Ensure data quality")
        plan.add_action("validate", "validate-input", "Validate input data")
        plan.add_action("analyze", "analyze-content", "Analyze content quality")
        plan.add_action("report", "generate-report", "Generate quality report")
        
        # Create execution
        execution = WorkflowExecution(
            workflow_definition=f"PlanDefinition/{plan.id}",
            subject="patient-001",
            total_steps=len(plan.action)
        )
        
        execution.start_execution({"quality_threshold": 0.95})
        
        assert execution.total_steps == 3
        assert execution.input_parameters["quality_threshold"] == 0.95
        assert plan.id in execution.workflow_definition

    def test_multi_task_workflow(self):
        """Test workflow with multiple concurrent tasks."""
        execution = WorkflowExecution(
            workflow_definition="PlanDefinition/parallel-workflow",
            subject="patient-001",
            total_steps=2
        )
        
        # Create multiple tasks for parallel execution
        task1 = create_simple_task(
            "validate-structure",
            "Validate document structure",
            "patient-001"
        )
        
        task2 = create_simple_task(
            "validate-content", 
            "Validate document content",
            "patient-001"
        )
        
        task3 = create_simple_task(
            "generate-summary",
            "Generate document summary",
            "patient-001"
        )
        
        execution.start_execution()
        execution.add_task(task1.id, active=True)
        execution.add_task(task2.id, active=True)
        execution.add_task(task3.id, active=False)  # Will be activated later
        
        # Complete parallel tasks
        task1.complete({"structure_valid": True})
        task2.complete({"content_valid": True})
        execution.complete_step(0, {"validation_complete": True})
        
        # Activate summary task
        execution.active_tasks.append(task3.id)
        task3.complete({"summary": "Document is valid and complete"})
        execution.complete_step(1, {"summary_complete": True})
        
        assert execution.status == EventStatus.COMPLETED
        assert len(execution.tasks) == 3
        assert len(execution.completed_steps) == 2


class TestWorkflowValidation:
    """Test workflow validation and error handling."""

    def test_task_validation(self):
        """Test task validation rules."""
        # Test required fields
        with pytest.raises(ValueError):
            Task(
                # Missing required fields
                status=TaskStatus.REQUESTED,
                intent=TaskIntent.ORDER
                # Missing subject
            )

    def test_workflow_status_transitions(self):
        """Test valid workflow status transitions."""
        task = Task(
            code="test-task",
            status=TaskStatus.DRAFT,
            intent=TaskIntent.PROPOSAL,
            subject="patient-001"
        )
        
        # Valid transitions
        task.status = TaskStatus.REQUESTED
        task.status = TaskStatus.ACCEPTED
        task.status = TaskStatus.IN_PROGRESS
        task.status = TaskStatus.COMPLETED
        
        assert task.status == TaskStatus.COMPLETED

    def test_execution_error_handling(self):
        """Test workflow execution error handling."""
        execution = WorkflowExecution(
            workflow_definition="PlanDefinition/error-test",
            subject="patient-001"
        )
        
        execution.start_execution()
        
        # Add multiple errors
        execution.errors.append("Validation failed")
        execution.warnings.append("Data quality warning")
        execution.fail_execution("Critical system error")
        
        assert len(execution.errors) == 2
        assert len(execution.warnings) == 1
        assert execution.status == EventStatus.STOPPED
        assert "Critical system error" in execution.errors


class TestWorkflowRelationships:
    """Test workflow resource relationships."""

    def test_request_event_relationships(self):
        """Test relationships between requests and events."""
        # Create a ServiceRequest
        request = ServiceRequest(
            code="lab-test",
            status=WorkflowStatus.ACTIVE,
            intent=RequestIntent.ORDER,
            subject="patient-001"
        )
        
        # Create a WorkflowEvent based on the request
        event = WorkflowEvent(
            status=EventStatus.COMPLETED,
            subject="patient-001"
        )
        
        # Link event to request
        event.based_on.append(f"ServiceRequest/{request.id}")
        
        assert f"ServiceRequest/{request.id}" in event.based_on
        assert event.subject == request.subject

    def test_definition_instantiation(self):
        """Test definition instantiation relationships."""
        # Create ActivityDefinition
        definition = ActivityDefinition(
            name="TestActivity",
            status=WorkflowStatus.ACTIVE,
            kind=ActivityDefinitionKind.TASK
        )
        
        # Create Task that instantiates the definition
        task = Task(
            code="test-task",
            status=TaskStatus.REQUESTED,
            intent=TaskIntent.ORDER,
            subject="patient-001"
        )
        
        task.instantiates_canonical.append(f"ActivityDefinition/{definition.id}")
        
        assert f"ActivityDefinition/{definition.id}" in task.instantiates_canonical

    def test_hierarchical_relationships(self):
        """Test hierarchical relationships between workflow resources."""
        # Create parent task
        parent_task = Task(
            code="parent-process",
            status=TaskStatus.IN_PROGRESS,
            intent=TaskIntent.ORDER,
            subject="patient-001"
        )
        
        # Create child tasks
        child_task1 = Task(
            code="sub-process-1",
            status=TaskStatus.REQUESTED,
            intent=TaskIntent.ORDER,
            subject="patient-001"
        )
        
        child_task2 = Task(
            code="sub-process-2",
            status=TaskStatus.REQUESTED,
            intent=TaskIntent.ORDER,
            subject="patient-001"
        )
        
        # Establish relationships
        child_task1.part_of.append(f"Task/{parent_task.id}")
        child_task2.part_of.append(f"Task/{parent_task.id}")
        
        assert f"Task/{parent_task.id}" in child_task1.part_of
        assert f"Task/{parent_task.id}" in child_task2.part_of