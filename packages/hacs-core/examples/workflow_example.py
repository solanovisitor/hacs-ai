#!/usr/bin/env python3
"""
HACS Workflow System Example - FHIR-Compatible Workflow Management.

This example demonstrates comprehensive workflow capabilities in HACS,
including definitions, requests, events, and execution management.

Features demonstrated:
- FHIR-compatible workflow patterns (Request, Event, Definition)
- Task orchestration and coordination
- Activity and plan definitions
- Workflow execution and state management
- Standard workflow relationships
- Complex multi-step workflows
- Error handling and recovery
"""

from datetime import datetime, timezone
from typing import List, Dict, Any

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
    WorkflowServiceRequest as ServiceRequest,
    WorkflowExecution,
    # Supporting Types
    WorkflowParticipant,
    # Factory Functions
    create_simple_task,
    create_document_processing_workflow,
    create_clinical_workflow_execution,
)


def create_clinical_validation_activities() -> List[ActivityDefinition]:
    """Create a set of activity definitions for clinical validation."""
    
    activities = []
    
    # Document Structure Validation
    structure_validation = ActivityDefinition(
        name="DocumentStructureValidation",
        title="Validate Document Structure",
        status=WorkflowStatus.ACTIVE,
        kind=ActivityDefinitionKind.TASK,
        code="validate-structure",
        description="Validate clinical document structure against FHIR standards",
        purpose="Ensure document follows proper FHIR format and structure"
    )
    
    # Add participants
    structure_validation.participant = [
        WorkflowParticipant(
            name="FHIR Validator Service",
            role="validator",
            actor_type="Device",
            required=True
        )
    ]
    
    activities.append(structure_validation)
    
    # Content Validation
    content_validation = ActivityDefinition(
        name="DocumentContentValidation",
        title="Validate Document Content",
        status=WorkflowStatus.ACTIVE,
        kind=ActivityDefinitionKind.TASK,
        code="validate-content",
        description="Validate clinical content for completeness and accuracy",
        purpose="Ensure document content meets clinical standards"
    )
    
    content_validation.participant = [
        WorkflowParticipant(
            name="Clinical Validation Engine",
            role="content-validator",
            actor_type="Device",
            required=True
        ),
        WorkflowParticipant(
            name="Clinical Reviewer",
            role="reviewer",
            actor_type="Person",
            required=False
        )
    ]
    
    activities.append(content_validation)
    
    # Quality Assessment
    quality_assessment = ActivityDefinition(
        name="DocumentQualityAssessment",
        title="Assess Document Quality",
        status=WorkflowStatus.ACTIVE,
        kind=ActivityDefinitionKind.TASK,
        code="assess-quality",
        description="Assess overall document quality and completeness",
        purpose="Provide quality metrics for clinical documentation"
    )
    
    activities.append(quality_assessment)
    
    # Integration Task
    integration_task = ActivityDefinition(
        name="DocumentIntegration",
        title="Integrate Document into System",
        status=WorkflowStatus.ACTIVE,
        kind=ActivityDefinitionKind.TASK,
        code="integrate-document",
        description="Integrate validated document into patient record system",
        purpose="Ensure document becomes part of patient's medical record"
    )
    
    integration_task.participant = [
        WorkflowParticipant(
            name="EHR Integration Service",
            role="integrator",
            actor_type="Device",
            required=True
        )
    ]
    
    activities.append(integration_task)
    
    return activities


def create_comprehensive_clinical_workflow() -> PlanDefinition:
    """Create a comprehensive clinical document processing workflow."""
    
    workflow = PlanDefinition(
        name="ComprehensiveClinicalWorkflow",
        title="Comprehensive Clinical Document Processing Workflow",
        status=WorkflowStatus.ACTIVE,
        type="workflow-definition",
        description="Complete end-to-end workflow for processing clinical documents with validation, quality assessment, and integration",
        purpose="Ensure high-quality clinical documentation that meets all standards and integrates seamlessly into patient care"
    )
    
    # Add comprehensive goals
    workflow.add_goal(
        "Ensure FHIR Compliance",
        category="compliance",
        priority="high"
    )
    
    workflow.add_goal(
        "Validate Clinical Content",
        category="quality",
        priority="high"
    )
    
    workflow.add_goal(
        "Assess Documentation Quality",
        category="quality",
        priority="medium"
    )
    
    workflow.add_goal(
        "Integrate into Patient Record",
        category="integration",
        priority="high"
    )
    
    workflow.add_goal(
        "Maintain Audit Trail",
        category="compliance",
        priority="medium"
    )
    
    # Add detailed workflow actions
    workflow.add_action(
        title="Initial Document Validation",
        code="validate-structure",
        description="Validate document structure against FHIR standards and schemas",
        definition_canonical="ActivityDefinition/document-structure-validation"
    )
    
    workflow.add_action(
        title="Clinical Content Validation",
        code="validate-content",
        description="Validate clinical content for accuracy and completeness",
        definition_canonical="ActivityDefinition/document-content-validation"
    )
    
    workflow.add_action(
        title="Quality Assessment",
        code="assess-quality",
        description="Perform comprehensive quality assessment of the document",
        definition_canonical="ActivityDefinition/document-quality-assessment"
    )
    
    workflow.add_action(
        title="System Integration",
        code="integrate-document",
        description="Integrate validated document into patient record system",
        definition_canonical="ActivityDefinition/document-integration"
    )
    
    workflow.add_action(
        title="Audit and Notification",
        code="audit-notify",
        description="Create audit records and notify relevant stakeholders",
        definition_canonical="ActivityDefinition/audit-notification"
    )
    
    return workflow


def demonstrate_basic_workflow_patterns():
    """Demonstrate basic workflow patterns and relationships."""
    
    print("🔄 HACS Workflow System - Basic Patterns Demo\n")
    
    # 1. Create ActivityDefinition
    print("1. Creating Activity Definitions...")
    activities = create_clinical_validation_activities()
    
    for activity in activities:
        print(f"   📋 {activity.title}")
        print(f"      Code: {activity.code}")
        print(f"      Kind: {activity.kind}")
        print(f"      Participants: {len(activity.participant)}")
    
    # 2. Create Tasks from Activities
    print("\n2. Creating Tasks from Activity Definitions...")
    tasks = []
    
    for activity in activities:
        task = activity.create_task(
            subject="patient-001",
            requester="physician-001"
        )
        
        # Add some inputs based on activity type
        if "validate" in activity.code:
            task.add_input("document_id", "doc-123", "string")
            task.add_input("validation_level", "strict", "string")
            task.add_output("validation_result", "boolean")
            task.add_output("error_count", "integer")
        elif "assess" in activity.code:
            task.add_input("document_id", "doc-123", "string")
            task.add_output("quality_score", "decimal")
            task.add_output("completeness_score", "decimal")
        elif "integrate" in activity.code:
            task.add_input("validated_document", "doc-123", "string")
            task.add_input("patient_id", "patient-001", "string")
            task.add_output("integration_status", "string")
        
        tasks.append(task)
        
        print(f"   ✅ Task: {task.description}")
        print(f"      Status: {task.status}")
        print(f"      Inputs: {len(task.input)}")
        print(f"      Outputs: {len(task.output)}")
    
    # 3. Create ServiceRequest
    print("\n3. Creating Service Request...")
    service_request = ServiceRequest(
        code="clinical-document-processing",
        status=WorkflowStatus.ACTIVE,
        intent=RequestIntent.ORDER,
        subject="patient-001",
        requester="physician-001",
        priority=RequestPriority.URGENT
    )
    
    service_request.order_detail = ["comprehensive-validation", "quality-assessment"]
    service_request.patient_instruction = ["Document will be processed within 24 hours"]
    
    print(f"   📨 Service Request: {service_request.code}")
    print(f"      Priority: {service_request.priority}")
    print(f"      Order Details: {service_request.order_detail}")
    
    return {
        "activities": activities,
        "tasks": tasks,
        "service_request": service_request
    }


def demonstrate_workflow_execution():
    """Demonstrate comprehensive workflow execution."""
    
    print("\n\n🚀 Workflow Execution Demo\n")
    
    # 1. Create Plan Definition
    print("1. Creating Comprehensive Workflow Plan...")
    workflow_plan = create_comprehensive_clinical_workflow()
    
    print(f"   📋 Workflow: {workflow_plan.title}")
    print(f"   🎯 Goals: {len(workflow_plan.goal)}")
    print(f"   🔧 Actions: {len(workflow_plan.action)}")
    
    for i, goal in enumerate(workflow_plan.goal):
        print(f"      Goal {i+1}: {goal['description']} ({goal.get('priority', 'normal')} priority)")
    
    # 2. Create Workflow Execution
    print("\n2. Starting Workflow Execution...")
    execution = create_clinical_workflow_execution(
        workflow_definition=f"PlanDefinition/{workflow_plan.id}",
        subject="patient-001",
        input_parameters={
            "document_id": "doc-123",
            "patient_id": "patient-001",
            "priority": "urgent",
            "validation_level": "comprehensive"
        }
    )
    
    print(f"   🎬 Execution ID: {execution.id}")
    print(f"   📊 Status: {execution.status}")
    print(f"   📅 Started: {execution.started}")
    print(f"   📋 Total Steps: {execution.total_steps}")
    print(f"   📥 Input Parameters: {len(execution.input_parameters)}")
    
    # 3. Execute Steps
    print("\n3. Executing Workflow Steps...")
    
    # Step 1: Structure Validation
    task1 = create_simple_task(
        "validate-structure",
        "Validate document structure",
        "patient-001",
        priority=RequestPriority.URGENT
    )
    
    task1.add_input("document_id", "doc-123")
    task1.add_input("schema_version", "fhir-r4")
    
    execution.add_task(task1.id)
    
    print(f"   Step 1: {task1.description}")
    print(f"      Task Status: {task1.status}")
    
    # Simulate task execution
    task1.status = TaskStatus.IN_PROGRESS
    task1.execution_period_start = datetime.now(timezone.utc)
    
    # Complete task
    task1.complete({
        "validation_result": True,
        "structure_score": 0.98,
        "errors_found": 0
    })
    
    execution.complete_step(0, {
        "structure_validation": "passed",
        "structure_score": 0.98
    })
    
    print(f"      ✅ Completed: {task1.status}")
    print(f"      📊 Current Step: {execution.current_step}")
    
    # Step 2: Content Validation
    task2 = create_simple_task(
        "validate-content",
        "Validate clinical content",
        "patient-001",
        priority=RequestPriority.URGENT
    )
    
    task2.add_input("document_id", "doc-123")
    task2.add_input("validation_rules", "clinical-standards-v2")
    
    execution.add_task(task2.id)
    
    print(f"   Step 2: {task2.description}")
    
    # Simulate content validation
    task2.status = TaskStatus.IN_PROGRESS
    task2.complete({
        "content_valid": True,
        "clinical_score": 0.94,
        "warnings": 2
    })
    
    execution.complete_step(1, {
        "content_validation": "passed",
        "clinical_score": 0.94,
        "warnings": 2
    })
    
    print(f"      ✅ Completed: {task2.status}")
    
    # Step 3: Quality Assessment
    task3 = create_simple_task(
        "assess-quality",
        "Assess document quality",
        "patient-001"
    )
    
    execution.add_task(task3.id)
    
    task3.complete({
        "quality_score": 0.91,
        "completeness": 0.96,
        "overall_grade": "A-"
    })
    
    execution.complete_step(2, {
        "quality_assessment": "passed",
        "overall_quality": 0.91
    })
    
    print(f"   Step 3: {task3.description} ✅")
    
    # Step 4: Integration
    task4 = create_simple_task(
        "integrate-document",
        "Integrate into patient record",
        "patient-001"
    )
    
    execution.add_task(task4.id)
    
    task4.complete({
        "integration_status": "success",
        "record_id": "record-456",
        "integration_time": datetime.now(timezone.utc).isoformat()
    })
    
    execution.complete_step(3, {
        "integration": "success",
        "record_id": "record-456"
    })
    
    print(f"   Step 4: {task4.description} ✅")
    
    # Workflow should auto-complete
    print(f"\n   🎉 Workflow Status: {execution.status}")
    print(f"   ⏱️  Duration: {execution.ended - execution.started}")
    print(f"   📋 Completed Steps: {len(execution.completed_steps)}")
    print(f"   📊 Tasks Created: {len(execution.tasks)}")
    
    return {
        "workflow_plan": workflow_plan,
        "execution": execution,
        "tasks": [task1, task2, task3, task4]
    }


def demonstrate_complex_workflow_scenarios():
    """Demonstrate complex workflow scenarios and error handling."""
    
    print("\n\n🔧 Complex Workflow Scenarios Demo\n")
    
    # 1. Parallel Task Execution
    print("1. Parallel Task Execution Scenario...")
    
    parallel_execution = WorkflowExecution(
        workflow_definition="PlanDefinition/parallel-validation-workflow",
        subject="patient-001",
        total_steps=3
    )
    
    parallel_execution.start_execution({
        "document_id": "doc-456",
        "parallel_processing": True
    })
    
    # Create parallel validation tasks
    structure_task = create_simple_task(
        "validate-structure-parallel",
        "Parallel structure validation",
        "patient-001"
    )
    
    content_task = create_simple_task(
        "validate-content-parallel", 
        "Parallel content validation",
        "patient-001"
    )
    
    terminology_task = create_simple_task(
        "validate-terminology",
        "Validate medical terminology",
        "patient-001"
    )
    
    # Add all tasks to execution
    parallel_execution.add_task(structure_task.id)
    parallel_execution.add_task(content_task.id)
    parallel_execution.add_task(terminology_task.id)
    
    print(f"   🔄 Started parallel execution with {len(parallel_execution.active_tasks)} tasks")
    
    # Complete tasks in parallel (simulate)
    structure_task.complete({"structure_valid": True, "processing_time": 1.2})
    content_task.complete({"content_valid": True, "processing_time": 2.1})
    terminology_task.complete({"terminology_valid": True, "processing_time": 0.8})
    
    # Complete parallel validation step
    parallel_execution.complete_step(0, {
        "parallel_validation": "completed",
        "all_validations_passed": True,
        "total_processing_time": 2.1  # Max of parallel tasks
    })
    
    print(f"   ✅ Parallel validation completed")
    print(f"      Structure: {structure_task.status}")
    print(f"      Content: {content_task.status}")
    print(f"      Terminology: {terminology_task.status}")
    
    # 2. Error Handling and Recovery
    print("\n2. Error Handling and Recovery Scenario...")
    
    error_execution = WorkflowExecution(
        workflow_definition="PlanDefinition/error-handling-workflow",
        subject="patient-002",
        total_steps=4
    )
    
    error_execution.start_execution({"document_id": "doc-789"})
    
    # Create a task that will fail
    failing_task = create_simple_task(
        "risky-validation",
        "Validation that might fail",
        "patient-002"
    )
    
    error_execution.add_task(failing_task.id)
    
    # Simulate task failure
    failing_task.status = TaskStatus.IN_PROGRESS
    failing_task.fail("External validation service unavailable")
    
    print(f"   ❌ Task failed: {failing_task.note[-1]}")
    
    # Add error to execution
    error_execution.errors.append("Validation service unavailable")
    error_execution.warnings.append("Attempting fallback validation")
    
    # Create recovery task
    recovery_task = create_simple_task(
        "fallback-validation",
        "Fallback validation method",
        "patient-002"
    )
    
    error_execution.add_task(recovery_task.id)
    
    # Complete recovery
    recovery_task.complete({
        "validation_method": "fallback",
        "validation_result": True,
        "confidence": 0.85
    })
    
    error_execution.complete_step(0, {
        "validation": "completed-with-fallback",
        "method": "fallback",
        "confidence": 0.85
    })
    
    print(f"   🔄 Recovery successful: {recovery_task.status}")
    print(f"   ⚠️  Warnings: {len(error_execution.warnings)}")
    print(f"   ❌ Errors: {len(error_execution.errors)}")
    
    # 3. Conditional Workflow Execution
    print("\n3. Conditional Workflow Execution...")
    
    conditional_execution = WorkflowExecution(
        workflow_definition="PlanDefinition/conditional-workflow",
        subject="patient-003",
        total_steps=2
    )
    
    conditional_execution.start_execution({
        "document_type": "discharge-summary",
        "patient_age": 65,
        "requires_special_review": True
    })
    
    # Standard processing task
    standard_task = create_simple_task(
        "standard-processing",
        "Standard document processing",
        "patient-003"
    )
    
    conditional_execution.add_task(standard_task.id)
    standard_task.complete({"processing_result": "success"})
    conditional_execution.complete_step(0, {"standard_processing": "completed"})
    
    # Conditional special review (based on age > 60)
    if conditional_execution.input_parameters.get("patient_age", 0) > 60:
        special_review_task = create_simple_task(
            "geriatric-review",
            "Special geriatric review required",
            "patient-003"
        )
        
        conditional_execution.add_task(special_review_task.id)
        special_review_task.complete({
            "geriatric_assessment": "completed",
            "special_considerations": ["fall-risk", "medication-interactions"]
        })
        
        conditional_execution.complete_step(1, {
            "special_review": "completed",
            "review_type": "geriatric"
        })
        
        print(f"   🔍 Special review triggered: {special_review_task.description}")
        print(f"   📋 Considerations: {2} special considerations noted")
    
    print(f"   ✅ Conditional workflow completed: {conditional_execution.status}")
    
    return {
        "parallel_execution": parallel_execution,
        "error_execution": error_execution,
        "conditional_execution": conditional_execution
    }


def demonstrate_workflow_relationships():
    """Demonstrate workflow resource relationships and linkages."""
    
    print("\n\n🔗 Workflow Relationships Demo\n")
    
    # 1. Definition to Request to Event Chain
    print("1. Definition → Request → Event Chain...")
    
    # Create ActivityDefinition
    definition = ActivityDefinition(
        name="PatientDataReview",
        title="Patient Data Review Process",
        status=WorkflowStatus.ACTIVE,
        kind=ActivityDefinitionKind.TASK,
        code="review-patient-data",
        description="Comprehensive review of patient data for quality and completeness"
    )
    
    print(f"   📋 Definition: {definition.title}")
    print(f"      ID: {definition.id}")
    
    # Create ServiceRequest based on definition
    request = ServiceRequest(
        code="review-patient-data",
        status=WorkflowStatus.ACTIVE,
        intent=RequestIntent.ORDER,
        subject="patient-001",
        requester="physician-001"
    )
    
    # Link request to definition
    request.instantiates_canonical.append(f"ActivityDefinition/{definition.id}")
    
    print(f"   📨 Request: {request.code}")
    print(f"      Instantiates: {request.instantiates_canonical}")
    
    # Create Task to fulfill the request
    task = Task(
        code="review-patient-data",
        description="Execute patient data review",
        status=TaskStatus.REQUESTED,
        intent=TaskIntent.ORDER,
        subject="patient-001",
        requester="physician-001"
    )
    
    # Link task to both definition and request
    task.instantiates_canonical.append(f"ActivityDefinition/{definition.id}")
    task.based_on.append(f"ServiceRequest/{request.id}")
    
    print(f"   ✅ Task: {task.description}")
    print(f"      Based on: {task.based_on}")
    print(f"      Instantiates: {task.instantiates_canonical}")
    
    # 2. Hierarchical Task Relationships
    print("\n2. Hierarchical Task Relationships...")
    
    # Parent task
    parent_task = Task(
        code="comprehensive-patient-assessment",
        description="Complete patient assessment workflow",
        status=TaskStatus.IN_PROGRESS,
        intent=TaskIntent.ORDER,
        subject="patient-001"
    )
    
    print(f"   👑 Parent Task: {parent_task.description}")
    
    # Child tasks
    child_tasks = []
    child_codes = ["review-history", "physical-exam", "lab-analysis", "imaging-review"]
    
    for code in child_codes:
        child_task = Task(
            code=code,
            description=f"Execute {code.replace('-', ' ')}",
            status=TaskStatus.REQUESTED,
            intent=TaskIntent.ORDER,
            subject="patient-001"
        )
        
        # Link child to parent
        child_task.part_of.append(f"Task/{parent_task.id}")
        child_tasks.append(child_task)
        
        print(f"      └─ Child Task: {child_task.description}")
        print(f"         Part of: {child_task.part_of}")
    
    # 3. Replacement and Version Relationships
    print("\n3. Replacement and Version Relationships...")
    
    # Original definition
    original_def = ActivityDefinition(
        name="DocumentValidationV1",
        title="Document Validation V1",
        status=WorkflowStatus.REVOKED,
        version="1.0.0",
        kind=ActivityDefinitionKind.TASK
    )
    
    # Updated definition
    updated_def = ActivityDefinition(
        name="DocumentValidationV2",
        title="Document Validation V2 (Enhanced)",
        status=WorkflowStatus.ACTIVE,
        version="2.0.0",
        kind=ActivityDefinitionKind.TASK
    )
    
    # Establish replacement relationship
    # Note: In a full implementation, this would be handled by the system
    print(f"   📋 Original: {original_def.title} (v{original_def.version}) - {original_def.status}")
    print(f"   📋 Updated: {updated_def.title} (v{updated_def.version}) - {updated_def.status}")
    print(f"      Replaces: ActivityDefinition/{original_def.id}")
    
    return {
        "definition_chain": {
            "definition": definition,
            "request": request,
            "task": task
        },
        "hierarchical": {
            "parent": parent_task,
            "children": child_tasks
        },
        "versioning": {
            "original": original_def,
            "updated": updated_def
        }
    }


def demonstrate_workflow_integration_scenarios():
    """Demonstrate real-world workflow integration scenarios."""
    
    print("\n\n🏥 Clinical Integration Scenarios\n")
    
    # 1. Emergency Department Workflow
    print("1. Emergency Department Document Processing...")
    
    ed_workflow = PlanDefinition(
        name="EmergencyDepartmentWorkflow",
        title="Emergency Department Clinical Documentation",
        status=WorkflowStatus.ACTIVE,
        type="clinical-protocol",
        description="Rapid processing of emergency department clinical documents"
    )
    
    ed_workflow.add_goal("Rapid document processing", "efficiency", "critical")
    ed_workflow.add_goal("Ensure clinical accuracy", "quality", "high")
    ed_workflow.add_goal("Maintain compliance", "compliance", "high")
    
    # Add time-critical actions
    ed_workflow.add_action("triage-validation", "triage-validate", "Rapid triage validation")
    ed_workflow.add_action("clinical-review", "clinical-review", "Clinical content review")
    ed_workflow.add_action("integration", "rapid-integration", "Rapid system integration")
    
    # Create high-priority execution
    ed_execution = WorkflowExecution(
        workflow_definition=f"PlanDefinition/{ed_workflow.id}",
        subject="patient-emergency-001",
        total_steps=3
    )
    
    ed_execution.start_execution({
        "document_type": "emergency-note",
        "triage_level": "urgent",
        "priority": "stat"
    })
    
    print(f"   🚨 ED Workflow: {ed_workflow.title}")
    print(f"   ⚡ Priority: STAT")
    print(f"   📊 Goals: {len(ed_workflow.goal)}")
    print(f"   🎯 Focus: Rapid processing with quality assurance")
    
    # 2. Discharge Planning Workflow
    print("\n2. Discharge Planning Workflow...")
    
    discharge_workflow = PlanDefinition(
        name="DischargeplanningWorkflow",
        title="Comprehensive Discharge Planning",
        status=WorkflowStatus.ACTIVE,
        type="care-coordination",
        description="Complete discharge planning with documentation and coordination"
    )
    
    discharge_workflow.add_goal("Complete discharge documentation", "documentation", "high")
    discharge_workflow.add_goal("Coordinate care transitions", "coordination", "high")
    discharge_workflow.add_goal("Ensure patient education", "education", "medium")
    discharge_workflow.add_goal("Arrange follow-up care", "follow-up", "high")
    
    # Multi-disciplinary actions
    discharge_workflow.add_action("medical-summary", "create-medical-summary", "Medical team summary")
    discharge_workflow.add_action("nursing-assessment", "nursing-discharge-assessment", "Nursing discharge assessment")
    discharge_workflow.add_action("pharmacy-review", "medication-reconciliation", "Pharmacy medication review")
    discharge_workflow.add_action("social-work", "discharge-planning", "Social work discharge planning")
    discharge_workflow.add_action("care-coordination", "coordinate-follow-up", "Care coordination")
    
    print(f"   🏠 Discharge Workflow: {discharge_workflow.title}")
    print(f"   👥 Multi-disciplinary: {len(discharge_workflow.action)} team actions")
    print(f"   🎯 Focus: Comprehensive care transition")
    
    # 3. Quality Improvement Workflow
    print("\n3. Quality Improvement Workflow...")
    
    qi_workflow = PlanDefinition(
        name="QualityImprovementWorkflow",
        title="Clinical Documentation Quality Improvement",
        status=WorkflowStatus.ACTIVE,
        type="quality-improvement",
        description="Continuous quality improvement for clinical documentation"
    )
    
    qi_workflow.add_goal("Monitor documentation quality", "monitoring", "high")
    qi_workflow.add_goal("Identify improvement opportunities", "analysis", "medium")
    qi_workflow.add_goal("Implement quality measures", "improvement", "high")
    qi_workflow.add_goal("Track performance metrics", "metrics", "medium")
    
    # Analytics and improvement actions
    qi_workflow.add_action("quality-analysis", "analyze-documentation-quality", "Quality analysis")
    qi_workflow.add_action("trend-identification", "identify-quality-trends", "Trend identification")
    qi_workflow.add_action("improvement-planning", "plan-improvements", "Improvement planning")
    qi_workflow.add_action("implementation", "implement-quality-measures", "Implementation")
    qi_workflow.add_action("monitoring", "monitor-improvements", "Ongoing monitoring")
    
    print(f"   📊 QI Workflow: {qi_workflow.title}")
    print(f"   📈 Analytics-driven: {len(qi_workflow.action)} improvement actions")
    print(f"   🎯 Focus: Continuous quality enhancement")
    
    return {
        "emergency_department": {
            "workflow": ed_workflow,
            "execution": ed_execution
        },
        "discharge_planning": {
            "workflow": discharge_workflow
        },
        "quality_improvement": {
            "workflow": qi_workflow
        }
    }


if __name__ == "__main__":
    print("🔄 HACS Workflow System - Comprehensive Demonstration")
    print("=" * 60)
    
    # Run all demonstrations
    basic_results = demonstrate_basic_workflow_patterns()
    execution_results = demonstrate_workflow_execution()
    complex_results = demonstrate_complex_workflow_scenarios()
    relationship_results = demonstrate_workflow_relationships()
    integration_results = demonstrate_workflow_integration_scenarios()
    
    print("\n" + "=" * 60)
    print("🎉 Workflow System Demo Complete! Key Achievements:")
    print()
    print("✅ FHIR-Compatible Workflow Patterns")
    print("✅ Comprehensive Task Orchestration")
    print("✅ Activity and Plan Definitions")
    print("✅ Workflow Execution Management")
    print("✅ Standard Resource Relationships")
    print("✅ Error Handling and Recovery")
    print("✅ Parallel and Conditional Execution")
    print("✅ Clinical Integration Scenarios")
    print("✅ Quality Improvement Workflows")
    print("✅ Multi-disciplinary Coordination")
    print()
    print("🏥 Ready for Production Clinical Workflows!")
    
    # Summary statistics
    total_activities = len(basic_results["activities"])
    total_tasks = len(basic_results["tasks"]) + len(execution_results["tasks"])
    total_workflows = 3 + len(integration_results)  # Basic + integration scenarios
    
    print(f"\n📊 Demo Statistics:")
    print(f"   📋 Activity Definitions: {total_activities}")
    print(f"   ✅ Tasks Created: {total_tasks}")
    print(f"   🔄 Workflows Demonstrated: {total_workflows}")
    print(f"   🏥 Clinical Scenarios: {len(integration_results)}")
    print(f"   🔗 Relationship Types: 5+ (instantiation, fulfillment, hierarchy, versioning, conditional)")
    print(f"   ⚡ Execution Patterns: Parallel, Sequential, Conditional, Error Recovery")