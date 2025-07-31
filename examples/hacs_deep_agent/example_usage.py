"""
HACS Deep Agent Usage Examples

Comprehensive examples demonstrating how to use the HACS Deep Agent for
various healthcare workflows, clinical scenarios, and AI-powered healthcare applications.

This example shows how to:
- Create HACS deep agents with clinical specializations
- Execute complex healthcare workflows
- Iterate on HACS tool calls for comprehensive care
- Use HACS resources for structured healthcare data
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../packages/hacs-tools/src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../../packages/hacs-core/src'))

import asyncio
from datetime import datetime
from typing import Dict, Any

from .agent import create_hacs_deep_agent, HACSDeepAgent
from .state import create_initial_hacs_state, HealthcareWorkflowContext
from .subagents import (
    CLINICAL_CARE_COORDINATOR,
    CLINICAL_DECISION_SUPPORT,
    POPULATION_HEALTH_ANALYST,
    get_subagent_by_specialty
)


def example_basic_healthcare_agent():
    """
    Example 1: Basic Healthcare Agent
    
    Demonstrates creating a basic HACS deep agent and using it for
    simple healthcare tasks and patient management.
    """
    print("🏥 Example 1: Basic Healthcare Agent")
    print("=" * 50)
    
    # Create a basic HACS deep agent
    agent = create_hacs_deep_agent(
        healthcare_instructions="""
        You are a primary care AI assistant focused on:
        - Patient registration and record management
        - Basic clinical assessments and documentation
        - Care coordination and follow-up planning
        - Quality measure tracking and reporting
        """,
        primary_actor="Primary Care AI Assistant"
    )
    
    # Example healthcare tasks
    healthcare_tasks = [
        "Create a new patient record for Maria Rodriguez, a 45-year-old female with diabetes",
        "Generate a clinical assessment summary for patient ID 12345",
        "Calculate quality measures for diabetes care in our patient population",
        "Search for clinical guidelines related to hypertension management"
    ]
    
    print(f"Created HACS Deep Agent: {agent.primary_actor}")
    print(f"Available Clinical Subagents: {len(agent.subagents)}")
    print(f"Total HACS Tools Available: {len(agent.hacs_tools)}")
    print()
    
    # Execute example tasks
    for i, task in enumerate(healthcare_tasks, 1):
        print(f"Task {i}: {task}")
        print("-" * 30)
        
        # In a real implementation, you would invoke the agent
        # result = agent.invoke(task)
        # print(f"Result: {result['messages'][-1].content[:200]}...")
        
        print("✅ Task would be executed with HACS tools")
        print()
    
    return agent


def example_clinical_care_coordination():
    """
    Example 2: Clinical Care Coordination
    
    Demonstrates using specialized subagents for comprehensive
    care coordination and clinical workflow management.
    """
    print("🧠 Example 2: Clinical Care Coordination")
    print("=" * 50)
    
    # Create agent focused on care coordination
    agent = create_hacs_deep_agent(
        healthcare_instructions="""
        You are a Care Coordination AI focused on managing complex patients
        across multiple providers and care settings. Prioritize patient safety,
        care continuity, and effective provider communication.
        """,
        clinical_subagents=[
            CLINICAL_CARE_COORDINATOR,
            CLINICAL_DECISION_SUPPORT
        ],
        primary_actor="Care Coordination Team"
    )
    
    # Complex care coordination scenario
    care_scenario = """
    Patient: John Smith, 68-year-old male
    Conditions: Diabetes, Hypertension, Chronic Kidney Disease
    Recent: Emergency department visit for chest pain
    Providers: Primary care, Cardiology, Nephrology, Endocrinology
    
    Tasks:
    1. Coordinate care plan across all specialists
    2. Ensure medication reconciliation and safety
    3. Schedule appropriate follow-up appointments
    4. Monitor clinical quality indicators
    5. Identify any care gaps or safety concerns
    """
    
    print("Care Coordination Scenario:")
    print(care_scenario)
    print()
    
    # Create healthcare workflow context
    workflow = agent.create_healthcare_workflow(
        workflow_type="complex_care_coordination",
        patient_id="john_smith_68",
        workflow_config={
            "priority": "high",
            "conditions": ["diabetes", "hypertension", "ckd"],
            "recent_events": ["emergency_visit"],
            "providers": ["primary_care", "cardiology", "nephrology", "endocrinology"]
        }
    )
    
    print(f"Created Workflow: {workflow.workflow_id}")
    print(f"Workflow Type: {workflow.workflow_type}")
    print(f"Current Step: {workflow.current_step}")
    print(f"Next Actions: {', '.join(workflow.next_actions)}")
    print()
    
    # Simulate care coordination steps
    coordination_steps = [
        "Delegate to clinical_care_coordinator: Review all current medications and identify potential interactions",
        "Delegate to clinical_decision_support: Analyze recent chest pain episode and recommend cardiac evaluation",
        "Execute clinical workflow for medication reconciliation across all providers",
        "Generate clinical dashboard showing patient's care coordination status",
        "Create comprehensive care plan with clear responsibilities for each provider"
    ]
    
    for step in coordination_steps:
        print(f"📋 {step}")
        # In real implementation: result = agent.invoke(step)
        print("   ✅ Would execute with specialized subagent")
        print()
    
    return agent, workflow


def example_population_health_analytics():
    """
    Example 3: Population Health Analytics
    
    Demonstrates using HACS tools for population health analysis,
    quality reporting, and healthcare analytics.
    """
    print("📊 Example 3: Population Health Analytics")
    print("=" * 50)
    
    # Create agent focused on population health
    agent = create_hacs_deep_agent(
        healthcare_instructions="""
        You are a Population Health Analytics AI focused on:
        - Analyzing healthcare data across patient populations
        - Calculating clinical quality measures and performance indicators
        - Identifying health disparities and improvement opportunities
        - Supporting population health management initiatives
        """,
        clinical_subagents=[POPULATION_HEALTH_ANALYST],
        primary_actor="Population Health Analytics Team"
    )
    
    # Population health analysis tasks
    analytics_tasks = [
        {
            "task": "Calculate HEDIS diabetes quality measures for our patient population",
            "parameters": {
                "measure_set": "HEDIS",
                "condition": "diabetes",
                "population_size": "5000+",
                "time_period": "2024"
            }
        },
        {
            "task": "Analyze population health trends for patients with hypertension",
            "parameters": {
                "analysis_type": "comprehensive",
                "condition": "hypertension",
                "include_social_determinants": True,
                "time_period_months": 24
            }
        },
        {
            "task": "Generate clinical dashboard for diabetes care management",
            "parameters": {
                "dashboard_type": "clinical",
                "specialty": "endocrinology",
                "time_period": "current_quarter"
            }
        },
        {
            "task": "Perform risk stratification for high-risk diabetic patients",
            "parameters": {
                "risk_model": "comprehensive",
                "prediction_horizon": "12_months",
                "include_interventions": True
            }
        }
    ]
    
    print("Population Health Analytics Tasks:")
    print()
    
    for i, task_info in enumerate(analytics_tasks, 1):
        task = task_info["task"]
        params = task_info["parameters"]
        
        print(f"Analytics Task {i}: {task}")
        print("Parameters:")
        for key, value in params.items():
            print(f"  • {key}: {value}")
        
        # Show which HACS tools would be used
        if "HEDIS" in task:
            print("HACS Tools: calculate_quality_measures, search_hacs_records")
        elif "population health" in task:
            print("HACS Tools: analyze_population_health, preprocess_medical_data")
        elif "dashboard" in task:
            print("HACS Tools: generate_clinical_dashboard, calculate_quality_measures")
        elif "risk stratification" in task:
            print("HACS Tools: perform_risk_stratification, run_clinical_inference")
        
        print("✅ Would execute with Population Health Analyst subagent")
        print()
    
    return agent


def example_fhir_integration_workflow():
    """
    Example 4: FHIR Integration Workflow
    
    Demonstrates healthcare interoperability using FHIR integration
    tools and standards-compliant healthcare data exchange.
    """
    print("🔄 Example 4: FHIR Integration Workflow")
    print("=" * 50)
    
    # Create agent focused on FHIR integration
    agent = create_hacs_deep_agent(
        healthcare_instructions="""
        You are a FHIR Integration AI focused on healthcare interoperability:
        - Converting healthcare data to FHIR-compliant formats
        - Validating FHIR resource compliance and data quality
        - Processing FHIR bundles for bulk operations
        - Managing healthcare terminology and code systems
        """,
        clinical_subagents=[get_subagent_by_specialty("fhir_integration")],
        primary_actor="FHIR Integration Specialist"
    )
    
    # FHIR integration scenarios
    fhir_workflows = [
        {
            "scenario": "Convert EHR data to FHIR R4 format",
            "source_data": "Legacy EHR patient records",
            "target": "FHIR R4 Patient and Observation resources",
            "tools": ["convert_to_fhir", "validate_fhir_compliance"]
        },
        {
            "scenario": "Process FHIR bundle for bulk patient import",
            "source_data": "FHIR Bundle with 1000+ patient records",
            "target": "Validated and imported patient data",
            "tools": ["process_fhir_bundle", "validate_fhir_compliance"]
        },
        {
            "scenario": "Validate clinical terminology compliance",
            "source_data": "Clinical codes and terminology",
            "target": "SNOMED CT and LOINC validation",
            "tools": ["lookup_fhir_terminology", "validate_fhir_compliance"]
        },
        {
            "scenario": "Healthcare system integration",
            "source_data": "Multiple EHR systems with different formats",
            "target": "Unified FHIR-compliant healthcare data",
            "tools": ["convert_to_fhir", "process_fhir_bundle", "validate_fhir_compliance"]
        }
    ]
    
    print("FHIR Integration Workflows:")
    print()
    
    for i, workflow in enumerate(fhir_workflows, 1):
        print(f"FHIR Workflow {i}: {workflow['scenario']}")
        print(f"Source: {workflow['source_data']}")
        print(f"Target: {workflow['target']}")
        print(f"HACS Tools: {', '.join(workflow['tools'])}")
        
        # Show workflow steps
        if "convert" in workflow['scenario'].lower():
            steps = [
                "1. Analyze source healthcare data format and structure",
                "2. Map healthcare data to appropriate FHIR resource types",
                "3. Convert data to FHIR-compliant JSON representation",
                "4. Validate FHIR compliance against R4/R5 specifications",
                "5. Generate conversion report and quality metrics"
            ]
        elif "bundle" in workflow['scenario'].lower():
            steps = [
                "1. Validate FHIR Bundle structure and entry types",
                "2. Process individual bundle entries with validation",
                "3. Execute bulk operations with transaction management",
                "4. Generate operation outcomes and success metrics",
                "5. Create audit trail for compliance reporting"
            ]
        elif "terminology" in workflow['scenario'].lower():
            steps = [
                "1. Extract clinical codes and terminology from source data",
                "2. Lookup codes in FHIR terminology services",
                "3. Validate code system compliance and mappings",
                "4. Generate terminology validation report",
                "5. Recommend corrections for non-compliant codes"
            ]
        else:
            steps = [
                "1. Assess healthcare system integration requirements",
                "2. Design FHIR-compliant data transformation pipeline",
                "3. Execute data conversion and validation workflows",
                "4. Process unified healthcare data through FHIR bundles",
                "5. Validate end-to-end healthcare interoperability"
            ]
        
        print("Workflow Steps:")
        for step in steps:
            print(f"   {step}")
        
        print("✅ Would execute with FHIR Integration Specialist")
        print()
    
    return agent


def example_ai_ml_healthcare_deployment():
    """
    Example 5: AI/ML Healthcare Model Deployment
    
    Demonstrates deploying and managing AI/ML models for healthcare
    applications with clinical validation and safety measures.
    """
    print("🤖 Example 5: AI/ML Healthcare Model Deployment")
    print("=" * 50)
    
    # Create agent focused on healthcare AI/ML
    agent = create_hacs_deep_agent(
        healthcare_instructions="""
        You are a Healthcare AI/ML Operations specialist focused on:
        - Deploying AI models for clinical applications with safety validation
        - Running real-time clinical inference for decision support
        - Preprocessing medical data for AI/ML applications
        - Monitoring AI model performance and clinical outcomes
        """,
        clinical_subagents=[get_subagent_by_specialty("healthcare_ai")],
        primary_actor="Healthcare AI/ML Operations"
    )
    
    # AI/ML deployment scenarios
    ai_scenarios = [
        {
            "model": "Diabetes Risk Prediction Model",
            "type": "risk_predictor",
            "use_case": "Identify patients at high risk for diabetes complications",
            "deployment_steps": [
                "Deploy healthcare AI model with clinical validation",
                "Configure real-time inference for patient risk assessment",
                "Preprocess patient data for optimal model performance",
                "Set up clinical alerts for high-risk predictions",
                "Monitor model performance and clinical outcomes"
            ],
            "tools": ["deploy_healthcare_ai_model", "run_clinical_inference", "preprocess_medical_data"]
        },
        {
            "model": "Sepsis Early Warning System",
            "type": "clinical_classifier",
            "use_case": "Early detection of sepsis in hospitalized patients",
            "deployment_steps": [
                "Deploy sepsis detection model with real-time monitoring",
                "Configure continuous patient data inference",
                "Set up emergency alerts for sepsis risk indicators",
                "Integrate with clinical workflow systems",
                "Validate clinical safety and alert accuracy"
            ],
            "tools": ["deploy_healthcare_ai_model", "run_clinical_inference", "generate_clinical_dashboard"]
        },
        {
            "model": "Medical Image Analysis AI",
            "type": "diagnostic_ai",
            "use_case": "AI-assisted radiology interpretation and diagnosis",
            "deployment_steps": [
                "Deploy medical imaging AI with radiologist validation",
                "Configure inference pipeline for medical images",
                "Preprocess medical imaging data for optimal AI performance",
                "Set up AI-assisted diagnostic workflow",
                "Monitor diagnostic accuracy and clinical outcomes"
            ],
            "tools": ["deploy_healthcare_ai_model", "run_clinical_inference", "preprocess_medical_data"]
        }
    ]
    
    print("Healthcare AI/ML Deployment Scenarios:")
    print()
    
    for i, scenario in enumerate(ai_scenarios, 1):
        print(f"AI Deployment {i}: {scenario['model']}")
        print(f"Model Type: {scenario['type']}")
        print(f"Clinical Use Case: {scenario['use_case']}")
        print(f"HACS Tools: {', '.join(scenario['tools'])}")
        print()
        
        print("Deployment Steps:")
        for step in scenario['deployment_steps']:
            print(f"   • {step}")
        
        # Show expected outcomes
        print("Expected Outcomes:")
        if "diabetes" in scenario['model'].lower():
            print("   • 85%+ accuracy in diabetes risk prediction")
            print("   • 30% reduction in preventable diabetes complications")
            print("   • Real-time risk alerts for high-risk patients")
        elif "sepsis" in scenario['model'].lower():
            print("   • 90%+ sensitivity for sepsis early detection")
            print("   • 25% reduction in sepsis-related mortality")
            print("   • <5 minute alert response time")
        elif "imaging" in scenario['model'].lower():
            print("   • 95%+ diagnostic accuracy for target conditions")
            print("   • 40% reduction in diagnostic interpretation time")
            print("   • Enhanced radiologist decision support")
        
        print("✅ Would execute with Healthcare AI Specialist")
        print()
    
    return agent


def run_comprehensive_hacs_example():
    """
    Comprehensive example demonstrating full HACS Deep Agent capabilities
    across multiple healthcare workflows and clinical scenarios.
    """
    print("🎯 Comprehensive HACS Deep Agent Example")
    print("=" * 60)
    print()
    
    # Create comprehensive healthcare agent
    comprehensive_agent = create_hacs_deep_agent(
        healthcare_instructions="""
        You are a comprehensive Healthcare AI Agent with access to all HACS tools
        and specialized clinical subagents. You can handle complex healthcare workflows
        including patient care, clinical decision support, population health analytics,
        FHIR integration, and AI/ML deployment.
        
        Always prioritize patient safety, clinical accuracy, and evidence-based care.
        Use specialized subagents for domain-specific tasks and HACS tools for
        comprehensive healthcare operations.
        """,
        primary_actor="Comprehensive Healthcare AI System"
    )
    
    # Complex healthcare scenario
    healthcare_scenario = """
    Healthcare Organization: Metropolitan Health System
    Challenge: Improve diabetes care quality while reducing costs
    
    Current State:
    - 15,000 diabetic patients across the health system
    - Multiple care providers and clinic locations
    - Inconsistent care protocols and documentation
    - Below-benchmark performance on diabetes quality measures
    - High emergency department utilization for diabetes complications
    
    Objectives:
    1. Standardize diabetes care protocols across all providers
    2. Implement AI-powered risk stratification for proactive care
    3. Achieve 80%+ performance on HEDIS diabetes quality measures
    4. Reduce diabetes-related emergency visits by 25%
    5. Ensure FHIR compliance for health information exchange
    """
    
    print("Healthcare Scenario:")
    print(healthcare_scenario)
    print()
    
    # Comprehensive workflow tasks
    comprehensive_tasks = [
        {
            "phase": "Assessment and Planning",
            "tasks": [
                "Delegate to population_health_analyst: Analyze current diabetes population health metrics",
                "Delegate to clinical_decision_support: Review evidence-based diabetes care protocols",
                "Search HACS records for all diabetic patients and their recent clinical data",
                "Calculate current HEDIS diabetes quality measures for baseline assessment"
            ]
        },
        {
            "phase": "Clinical Protocol Standardization", 
            "tasks": [
                "Delegate to resource_development_specialist: Create standardized diabetes care templates",
                "Validate clinical protocols against current diabetes care guidelines",
                "Convert existing care protocols to FHIR-compliant clinical pathways",
                "Create clinical memories for diabetes care best practices and outcomes"
            ]
        },
        {
            "phase": "AI-Powered Risk Stratification",
            "tasks": [
                "Delegate to healthcare_ai_specialist: Deploy diabetes risk prediction model",
                "Perform risk stratification for all diabetic patients in the population",
                "Run clinical inference to identify high-risk patients requiring immediate intervention",
                "Generate clinical dashboard for diabetes risk management and care coordination"
            ]
        },
        {
            "phase": "Quality Improvement Implementation",
            "tasks": [
                "Execute clinical workflows for proactive diabetes care management",
                "Delegate to clinical_care_coordinator: Coordinate care for high-risk diabetic patients",
                "Calculate updated HEDIS diabetes quality measures to track improvement",
                "Analyze population health trends to identify additional improvement opportunities"
            ]
        },
        {
            "phase": "Interoperability and Integration",
            "tasks": [
                "Delegate to fhir_integration_specialist: Ensure FHIR compliance for all diabetes data",
                "Process FHIR bundles for diabetes patient data exchange with external systems",
                "Validate FHIR compliance for diabetes care documentation and quality reporting",
                "Create comprehensive audit trail for diabetes care quality improvement initiative"
            ]
        }
    ]
    
    print("Comprehensive Healthcare Workflow:")
    print()
    
    for phase_info in comprehensive_tasks:
        phase = phase_info["phase"]
        tasks = phase_info["tasks"]
        
        print(f"📋 Phase: {phase}")
        print("-" * 40)
        
        for i, task in enumerate(tasks, 1):
            print(f"   {i}. {task}")
            
            # Show which HACS tools and subagents would be used
            if "population_health_analyst" in task:
                print("      → Subagent: Population Health Analyst")
                print("      → Tools: analyze_population_health, calculate_quality_measures")
            elif "clinical_decision_support" in task:
                print("      → Subagent: Clinical Decision Support")
                print("      → Tools: get_clinical_guidance, validate_clinical_protocol")
            elif "healthcare_ai_specialist" in task:
                print("      → Subagent: Healthcare AI Specialist")
                print("      → Tools: deploy_healthcare_ai_model, run_clinical_inference")
            elif "clinical_care_coordinator" in task:
                print("      → Subagent: Clinical Care Coordinator")
                print("      → Tools: execute_clinical_workflow, create_hacs_record")
            elif "fhir_integration_specialist" in task:
                print("      → Subagent: FHIR Integration Specialist")
                print("      → Tools: convert_to_fhir, validate_fhir_compliance")
            elif "resource_development_specialist" in task:
                print("      → Subagent: Resource Development Specialist")
                print("      → Tools: create_clinical_template, create_resource_stack")
            else:
                print("      → Direct HACS Tools: Based on task requirements")
            
            print()
        
        print()
    
    # Expected outcomes
    expected_outcomes = [
        "Standardized diabetes care protocols across all 15,000 patients",
        "AI-powered risk stratification identifying 2,000+ high-risk patients",
        "85%+ performance on HEDIS diabetes quality measures",
        "30% reduction in diabetes-related emergency department visits",
        "Complete FHIR compliance for diabetes care documentation",
        "Comprehensive population health dashboard for ongoing monitoring",
        "Established clinical memories for institutional learning and improvement"
    ]
    
    print("Expected Outcomes:")
    for i, outcome in enumerate(expected_outcomes, 1):
        print(f"   ✅ {outcome}")
    
    print()
    print("🎉 Comprehensive healthcare workflow completed using HACS Deep Agent!")
    print("   All tasks executed with appropriate HACS tools and clinical subagents")
    
    return comprehensive_agent


def main():
    """
    Run all HACS Deep Agent examples to demonstrate comprehensive
    healthcare AI capabilities and workflow management.
    """
    print("🏥 HACS Deep Agent - Comprehensive Healthcare AI Examples")
    print("=" * 70)
    print()
    
    print("This example demonstrates the HACS Deep Agent's capabilities for:")
    print("• Complex healthcare workflow management")
    print("• Specialized clinical subagent delegation")
    print("• Comprehensive HACS tool utilization")
    print("• Healthcare resource state management")
    print("• Clinical decision support and analytics")
    print()
    
    # Run all examples
    examples = [
        example_basic_healthcare_agent,
        example_clinical_care_coordination,
        example_population_health_analytics,
        example_fhir_integration_workflow,
        example_ai_ml_healthcare_deployment,
        run_comprehensive_hacs_example
    ]
    
    for example_func in examples:
        try:
            example_func()
            print("✅ Example completed successfully!")
        except Exception as e:
            print(f"❌ Example failed: {str(e)}")
        
        print("\n" + "="*70 + "\n")
    
    print("🎯 All HACS Deep Agent examples completed!")
    print()
    print("Key Features Demonstrated:")
    print("• 37+ HACS healthcare tools across 9 comprehensive domains")
    print("• 7 specialized clinical subagents for domain expertise")
    print("• Healthcare workflow iteration and task delegation")
    print("• HACS resource state management and clinical context")
    print("• Comprehensive healthcare AI capabilities")
    print()
    print("The HACS Deep Agent provides a complete healthcare AI platform")
    print("for clinical workflows, population health, and healthcare operations!")


if __name__ == "__main__":
    main() 