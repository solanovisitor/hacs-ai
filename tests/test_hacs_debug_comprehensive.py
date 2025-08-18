import os
import pdb
import json
import traceback
from typing import Any, Dict


def test_comprehensive_model_validation():
    """Comprehensive test with debugging to validate all HACS models and tools."""
    os.environ.setdefault("PYTHONPATH", ".")
    
    # Setup debugging helpers
    def debug_print(message: str, data: Any = None):
        print(f"🔍 DEBUG: {message}")
        if data is not None:
            print(f"   Data: {data}")
    
    def handle_error(operation: str, error: Exception, should_fail: bool = False):
        error_msg = f"❌ ERROR in {operation}: {str(error)}"
        print(error_msg)
        print(f"   Type: {type(error).__name__}")
        print(f"   Traceback: {traceback.format_exc()}")
        if not should_fail:
            # Uncomment the next line to pause execution for debugging
            # pdb.set_trace()  
            raise error
        return error_msg
    
    debug_print("StartingHACS validation")
    
    # Test 1: Model Registry Validation
    debug_print("Testing model registry...")
    try:
        from hacs_models import get_model_registry, validate_model_compatibility
        
        registry = get_model_registry()
        debug_print(f"Found {len(registry)} models in registry", list(registry.keys()))
        
        # Test model compatibility
        compatibility_result = validate_model_compatibility()
        debug_print(f"Model compatibility check: {compatibility_result}")
        
        assert compatibility_result, "Model compatibility validation failed"
        
    except Exception as e:
        handle_error("Model Registry Validation", e)
    
    # Test 2: Schema Discovery with Detailed Results
    debug_print("Testing schema discovery...")
    try:
        from hacs_tools.domains import schema_discovery
        
        test_models = [
            "Patient", "Observation", "Encounter", "Condition", 
            "Medication", "MedicationRequest", "Procedure", "Goal",
            "ServiceRequest", "DiagnosticReport"
        ]
        
        schema_results = {}
        for resource_name in test_models:
            debug_print(f"Testing schema for {resource_name}")
            
            result = schema_discovery.get_hacs_resource_schema(
                resource_name, 
                include_examples=True, 
                include_validation_rules=True
            )
            
            schema_results[resource_name] = {
                "success": result.success,
                "field_count": result.field_count,
                "has_schema": bool(result.schema),
                "message": result.message
            }
            
            if not result.success:
                debug_print(f"Schema discovery failed for {resource_name}: {result.message}")
                # Uncomment to debug specific failures
                # pdb.set_trace()
            
            assert result.success, f"Schema discovery failed for {resource_name}: {result.message}"
            assert result.field_count > 0, f"No fields found for {resource_name}"
        
        debug_print("Schema discovery results", schema_results)
        
    except Exception as e:
        handle_error("Schema Discovery", e)
    
    # Test 3: Resource Management CRUD Operations
    debug_print("Testing resource management CRUD operations...")
    try:
        from hacs_tools.domains import resource_management
        
        # Test cases with different complexity levels
        test_cases = [
            {
                "name": "Simple Patient",
                "resource_type": "Patient",
                "data": {"full_name": "John Debug", "gender": "male"}
            },
            {
                "name": "Complex Observation",
                "resource_type": "Observation", 
                "data": {
                    "status": "final",
                    "code": {"text": "Blood Pressure", "coding": [{"code": "BP", "system": "custom"}]},
                    "value_quantity": {"value": 120, "unit": "mmHg"},
                    "category": [{"text": "vital-signs"}],
                    "agent_context": {"source": "debugging_test", "priority": "high"}
                }
            },
            {
                "name": "Enhanced MedicationRequest",
                "resource_type": "MedicationRequest",
                "data": {
                    "status": "active",
                    "intent": "order", 
                    "subject": "Patient/debug-123",
                    "medication_codeable_concept": {
                        "text": "Amoxicillin 500mg",
                        "coding": [{"code": "27658006", "system": "http://snomed.info/sct"}]
                    },
                    "dosage_instruction": [{
                        "text": "Take 1 tablet twice daily",
                        "timing": {"repeat": {"frequency": 2, "period": 1, "period_unit": "d"}}
                    }],
                    "agent_context": {"prescriber_notes": "For debugging purposes"}
                }
            }
        ]
        
        crud_results = {}
        for test_case in test_cases:
            debug_print(f"Testing CRUD for {test_case['name']}")
            
            try:
                # Create resource
                create_result = resource_management.create_record(
                    actor_name="DebugTester",
                    resource_type=test_case["resource_type"],
                    resource_data=test_case["data"]
                )
                
                crud_results[test_case["name"]] = {
                    "create_success": create_result.success,
                    "create_message": create_result.message,
                    "resource_id": getattr(create_result, "resource_id", None)
                }
                
                debug_print(f"Create result for {test_case['name']}: {create_result.success}")
                if not create_result.success:
                    debug_print(f"Create error: {create_result.message}")
                    # Uncomment to debug creation failures
                    # pdb.set_trace()
                
                assert create_result.success, f"Failed to create {test_case['name']}: {create_result.message}"
                
            except Exception as e:
                handle_error(f"CRUD operations for {test_case['name']}", e)
                crud_results[test_case["name"]] = {"error": str(e)}
        
        debug_print("CRUD test results", crud_results)
        
    except Exception as e:
        handle_error("Resource Management CRUD", e)
    
    # Test 4: Integration Between Components
    debug_print("Testing integration between schema discovery and resource management...")
    try:
        # Get schema for Patient and create a resource based on it
        patient_schema = schema_discovery.get_hacs_resource_schema("Patient", include_examples=True)
        assert patient_schema.success, "Could not get Patient schema"
        
        # Use schema information to create a morepatient
        integration_patient_data = {
            "full_name": "Integration Test Patient",
            "gender": "other",
            "birth_date": "1990-01-01",
            "active": True,
            "deceased_boolean": False,
            "agent_context": {
                "test_type": "integration",
                "schema_field_count": patient_schema.field_count,
                "created_from_schema": True
            }
        }
        
        integration_result = resource_management.create_record(
            actor_name="IntegrationTester",
            resource_type="Patient", 
            resource_data=integration_patient_data
        )
        
        debug_print(f"Integration test result: {integration_result.success}")
        assert integration_result.success, f"Integration test failed: {integration_result.message}"
        
    except Exception as e:
        handle_error("Component Integration", e)
    
    debug_print("✅ Alltests passed!")
    
    # Test summary
    print("\n" + "="*80)
    print("🎯 TEST SUMMARY")
    print("="*80)
    print("✅ Model registry validation: PASSED")
    print("✅ Schema discovery: PASSED") 
    print("✅ Resource management CRUD: PASSED")
    print("✅ Component integration: PASSED")
    print("="*80)


def test_debug_specific_model_issues():
    """Debug specific model issues with detailed error handling."""
    os.environ.setdefault("PYTHONPATH", ".")
    
    print("\n🔧 DEBUGGING SPECIFIC MODEL ISSUES")
    print("="*50)
    
    # Test importing problematic models individually
    problematic_imports = [
        ("hacs_models", "MedicationRequest"),
        ("hacs_models", "Procedure"), 
        ("hacs_models", "Medication"),
        ("hacs_tools.domains.resource_management", "create_record"),
        ("hacs_tools.domains.schema_discovery", "get_hacs_resource_schema")
    ]
    
    for module_name, item_name in problematic_imports:
        try:
            module = __import__(module_name, fromlist=[item_name])
            item = getattr(module, item_name)
            print(f"✅ Successfully imported {item_name} from {module_name}")
            
            # For model classes, try to create a minimal instance
            if hasattr(item, 'model_fields'):
                print(f"   📋 {item_name} has {len(item.model_fields)} fields")
                required_fields = [
                    name for name, field in item.model_fields.items() 
                    if field.is_required()
                ]
                print(f"   🔒 Required fields: {required_fields}")
                
        except Exception as e:
            print(f"❌ Failed to import {item_name} from {module_name}: {e}")
            print(f"   Error type: {type(e).__name__}")
            # Uncomment to debug import issues
            # pdb.set_trace()


if __name__ == "__main__":
    # Run debug tests directly
    test_debug_specific_model_issues()
    test_comprehensive_model_validation()
