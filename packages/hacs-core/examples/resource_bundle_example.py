#!/usr/bin/env python3
"""
ResourceBundle Example - Demonstrates HACS Resource Bundle capabilities.

This example shows how to create and use ResourceBundle for:
- Creating resource stacks for specific use cases
- Binding bundles to workflows
- Managing registry information and versioning
- Searching and filtering resources
"""

from datetime import datetime, timezone
from hacs_core.models import (
    ResourceBundle, 
    BundleType, 
    BundleStatus,
    WorkflowBindingType,
    Patient,
    Observation,
    create_resource_stack,
    create_search_results_bundle,
    create_workflow_template_bundle
)


def create_psychiatric_assessment_stack():
    """
    Create a comprehensive psychiatric assessment resource stack.
    """
    # Create sample resources
    patient = Patient(
        id="patient-001",
        full_name="John Doe",
        birth_date="1985-06-15",
        gender="male",
        email="john.doe@example.com"
    )
    
    mood_observation = Observation(
        id="obs-mood-001",
        status="final",
        category="survey",
        code="Mood Assessment",
        subject="patient-001",
        value_string="Depressed mood reported"
    )
    
    anxiety_observation = Observation(
        id="obs-anxiety-001", 
        status="final",
        category="survey",
        code="Anxiety Assessment",
        subject="patient-001",
        value_string="Moderate anxiety symptoms"
    )
    
    # Create resource stack using factory function
    bundle = create_resource_stack(
        stack_name="Psychiatric Assessment Stack v2.1",
        version="2.1.0", 
        description="Comprehensive resource stack for psychiatric assessments including patient demographics, mood evaluations, and clinical observations",
        resources=[patient, mood_observation, anxiety_observation],
        publisher="HACS Clinical Team"
    )
    
    # Add detailed use cases
    bundle.add_use_case(
        name="Initial Psychiatric Evaluation",
        description="Complete psychiatric assessment for new patients including history, mental status exam, and initial observations",
        examples=[
            "First-time psychiatric consultation",
            "Emergency psychiatric evaluation", 
            "Pre-treatment assessment"
        ],
        prerequisites=[
            "Patient consent obtained",
            "Basic demographics collected",
            "Mental status examination completed"
        ],
        outcomes=[
            "Diagnostic impressions documented",
            "Treatment plan initiated",
            "Risk assessment completed"
        ],
        tags=["initial-assessment", "psychiatric", "comprehensive"]
    )
    
    bundle.add_use_case(
        name="Follow-up Assessment",
        description="Ongoing psychiatric monitoring and assessment of treatment progress",
        examples=[
            "Monthly therapy follow-up",
            "Medication effectiveness review",
            "Crisis intervention assessment"
        ],
        prerequisites=[
            "Previous assessment available",
            "Treatment plan in progress"
        ],
        outcomes=[
            "Treatment adjustment recommendations",
            "Progress documentation",
            "Next steps planned"
        ],
        tags=["follow-up", "monitoring", "treatment-response"]
    )
    
    # Add workflow bindings
    bundle.add_workflow_binding(
        workflow_id="psychiatric-evaluation-v1",
        workflow_name="Psychiatric Evaluation Workflow",
        binding_type=WorkflowBindingType.INPUT_FILTER,
        description="Use this bundle as input filter for psychiatric evaluation workflow",
        parameters={
            "required_observations": ["mood", "anxiety"],
            "min_age": 18,
            "assessment_type": "comprehensive"
        },
        priority=1
    )
    
    bundle.add_workflow_binding(
        workflow_id="clinical-documentation-v2", 
        workflow_name="Clinical Documentation Generator",
        binding_type=WorkflowBindingType.OUTPUT_TEMPLATE,
        description="Generate structured clinical documentation from assessment data",
        parameters={
            "format": "structured-narrative",
            "include_risk_assessment": True,
            "template_version": "2.1"
        },
        priority=2
    )
    
    # Add version history
    bundle.add_update_record(
        version="2.1.0",
        summary="Enhanced anxiety assessment components and workflow integration",
        author="Dr. Sarah Chen",
        details="Added specialized anxiety observation fields, updated workflow bindings for better clinical documentation, improved validation rules",
        breaking_changes=False,
        migration_notes="No migration required - all changes are backward compatible"
    )
    
    bundle.add_update_record(
        version="2.0.0", 
        summary="Major restructure with FHIR R4 compliance and workflow bindings",
        author="HACS Development Team",
        details="Complete overhaul to align with FHIR R4 standards, introduction of workflow binding capabilities, enhanced metadata support",
        breaking_changes=True,
        migration_notes="Resources need to be updated to FHIR R4 format. See migration guide at docs/migration-2.0.md"
    )
    
    # Set additional registry metadata
    bundle.keywords = ["psychiatric", "mental-health", "assessment", "clinical-evaluation"]
    bundle.categories = ["mental-health", "clinical-workflow", "assessment-tools"]
    bundle.license = "MIT"
    bundle.copyright = "© 2024 HACS Foundation"
    bundle.maturity_level = "stable"
    bundle.quality_score = 0.92
    
    # Add validation rules
    bundle.validation_rules = {
        "patient_required": True,
        "min_observations": 2,
        "assessment_completeness": {
            "mood": "required",
            "anxiety": "required", 
            "risk_assessment": "recommended"
        }
    }
    
    return bundle


def create_search_results_example():
    """
    Create an example search results bundle.
    """
    # Sample search results
    patients = [
        Patient(id=f"patient-{i:03d}", full_name=f"Patient {i}", birth_date=f"198{i%10}-01-01")
        for i in range(1, 6)
    ]
    
    bundle = create_search_results_bundle(
        resources=patients,
        total=25,  # Total matches across all pages
        search_url="https://api.hacs.org/Patient?name=Patient&_count=5"
    )
    
    bundle.title = "Patient Search Results"
    bundle.description = "Search results for patients matching query criteria"
    
    return bundle


def create_workflow_template_example():
    """
    Create a workflow template bundle example.
    """
    # Template resources for clinical documentation
    template_patient = Patient(
        id="template-patient",
        full_name="{{patient.name}}",
        birth_date="{{patient.birth_date}}",
        gender="{{patient.gender}}"
    )
    
    template_observation = Observation(
        id="template-observation",
        status="{{observation.status}}",
        category="{{observation.category}}", 
        code="{{observation.code}}",
        subject="{{patient.id}}",
        value_string="{{observation.value}}"
    )
    
    bundle = create_workflow_template_bundle(
        template_name="Clinical Documentation Template",
        version="1.0.0",
        workflow_id="clinical-doc-generator",
        template_resources=[template_patient, template_observation],
        description="Template for generating structured clinical documentation"
    )
    
    return bundle


def demonstrate_bundle_operations():
    """
    Demonstrate various ResourceBundle operations.
    """
    print("🏥 HACS ResourceBundle Demonstration\n")
    
    # Create psychiatric assessment stack
    print("1. Creating Psychiatric Assessment Stack...")
    psych_bundle = create_psychiatric_assessment_stack()
    print(f"   ✅ Created bundle: {psych_bundle.title}")
    print(f"   📦 Type: {psych_bundle.bundle_type}")
    print(f"   📊 Version: {psych_bundle.version}")
    print(f"   🔍 Resources: {len(psych_bundle.entries)}")
    print(f"   🔗 Workflow bindings: {len(psych_bundle.workflow_bindings)}")
    print(f"   📋 Use cases: {len(psych_bundle.use_cases)}")
    
    # Validate bundle integrity
    print("\n2. Validating Bundle Integrity...")
    validation = psych_bundle.validate_bundle_integrity()
    print(f"   ✅ Valid: {validation['valid']}")
    print(f"   📊 Entry count: {validation['entry_count']}")
    print(f"   🔗 Workflow bindings: {validation['workflow_binding_count']}")
    if validation['warnings']:
        print(f"   ⚠️  Warnings: {validation['warnings']}")
    
    # Demonstrate resource filtering
    print("\n3. Resource Filtering...")
    patients = psych_bundle.get_resources_by_type("Patient")
    observations = psych_bundle.get_resources_by_type("Observation")
    print(f"   👤 Patients: {len(patients)}")
    print(f"   📈 Observations: {len(observations)}")
    
    # Demonstrate workflow binding filtering
    print("\n4. Workflow Binding Operations...")
    input_filters = psych_bundle.get_workflow_bindings_by_type(WorkflowBindingType.INPUT_FILTER)
    output_templates = psych_bundle.get_workflow_bindings_by_type(WorkflowBindingType.OUTPUT_TEMPLATE)
    print(f"   🔍 Input filters: {len(input_filters)}")
    print(f"   📄 Output templates: {len(output_templates)}")
    
    # Create search results example
    print("\n5. Search Results Bundle...")
    search_bundle = create_search_results_example()
    print(f"   🔍 Search results: {search_bundle.title}")
    print(f"   📊 Total matches: {search_bundle.total}")
    print(f"   📦 This page: {len(search_bundle.entries)}")
    
    # Create workflow template example
    print("\n6. Workflow Template Bundle...")
    template_bundle = create_workflow_template_example()
    print(f"   📋 Template: {template_bundle.title}")
    print(f"   🔗 Workflow ID: {template_bundle.workflow_bindings[0].workflow_id}")
    print(f"   📄 Template resources: {len(template_bundle.entries)}")
    
    # Demonstrate JSON serialization
    print("\n7. JSON Serialization...")
    json_output = psych_bundle.model_dump_json(indent=2)
    print(f"   📄 JSON size: {len(json_output)} characters")
    print(f"   ✅ Successfully serialized to JSON")
    
    print("\n🎉 ResourceBundle demonstration completed!")
    print("\nKey Features Demonstrated:")
    print("   • Resource collection and organization")
    print("   • Registry metadata and versioning")
    print("   • Workflow binding capabilities")
    print("   • Use case documentation")
    print("   • Version history tracking")
    print("   • Resource filtering and search")
    print("   • Bundle validation and integrity checking")
    print("   • Factory functions for common patterns")


if __name__ == "__main__":
    demonstrate_bundle_operations()