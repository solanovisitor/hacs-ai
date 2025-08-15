#!/usr/bin/env python3
"""
Interactive debugging example for HACS models and tools.
This script demonstrates how to use pdb for step-by-step debugging.

To use pdb effectively:
1. Set breakpoints with pdb.set_trace()
2. Use 'n' (next) to step to next line
3. Use 's' (step) to step into function calls  
4. Use 'c' (continue) to continue execution
5. Use 'l' (list) to see current code
6. Use 'p variable_name' to print variable values
7. Use 'pp variable_name' for pretty print
8. Use 'h' (help) for all commands
"""

import os
import pdb
import time

# Set up environment
os.environ.setdefault("PYTHONPATH", ".")

def debug_model_creation():
    """Debug the creation of a complex HACS model step by step."""
    print("🔧 Starting interactive debugging session...")
    print("This will pause at breakpoints - use pdb commands to navigate")
    
    # Uncomment the next line to start debugging here
    # pdb.set_trace()
    
    from hacs_models import Patient, Observation, MedicationRequest
    from hacs_tools.domains import resource_management
    
    print("✅ Imports completed")
    
    # Debug patient creation
    patient_data = {
        "full_name": "Debug Patient",
        "gender": "female", 
        "birth_date": "1985-03-15",
        "active": True
    }
    
    print(f"📊 About to create patient with data: {patient_data}")
    
    # Uncomment to debug patient creation step by step
    # pdb.set_trace()
    
    try:
        # This will use the resource management tool
        result = resource_management.create_hacs_record(
            actor_name="DebugUser",
            resource_type="Patient",
            resource_data=patient_data
        )
        
        print(f"✅ Patient creation result: {result.success}")
        if not result.success:
            print(f"❌ Error: {result.message}")
            # Uncomment to debug failures
            # pdb.set_trace()
        
    except Exception as e:
        print(f"❌ Exception during patient creation: {e}")
        # Uncomment to debug exceptions
        # pdb.set_trace()
        raise
    
    # Debug complex observation creation
    observation_data = {
        "status": "final",
        "code": {
            "text": "Blood Pressure",
            "coding": [{"code": "BP", "system": "custom"}]
        },
        "value_quantity": {"value": 140, "unit": "mmHg"},
        "category": [{"text": "vital-signs"}],
        "reference_range": [
            {
                "low": {"value": 120, "unit": "mmHg"},
                "high": {"value": 140, "unit": "mmHg"},
                "text": "Normal range"
            }
        ],
        "agent_context": {
            "measurement_method": "automated_cuff",
            "patient_position": "sitting",
            "cuff_size": "standard_adult"
        }
    }
    
    print(f"📊 About to create complex observation...")
    
    # Uncomment to step through observation creation  
    # pdb.set_trace()
    
    try:
        obs_result = resource_management.create_hacs_record(
            actor_name="DebugUser", 
            resource_type="Observation",
            resource_data=observation_data
        )
        
        print(f"✅ Observation creation result: {obs_result.success}")
        
        # Let's examine the created observation in detail
        if obs_result.success and hasattr(obs_result, 'resource_data'):
            created_obs = obs_result.resource_data
            print(f"   📋 Created observation ID: {created_obs.id}")
            print(f"   📋 Status: {created_obs.status}")
            print(f"   📋 Value: {created_obs.value_quantity}")
            print(f"   📋 Context keys: {list(created_obs.agent_context.keys()) if created_obs.agent_context else 'None'}")
            
            # Uncomment to examine the full object
            # pdb.set_trace()
        
    except Exception as e:
        print(f"❌ Exception during observation creation: {e}")
        # Uncomment to debug exceptions
        # pdb.set_trace()
        raise
    
    print("🎯 Debug session completed successfully!")


def debug_schema_discovery():
    """Debug schema discovery with step-by-step analysis."""
    print("\n🔍 Debugging schema discovery...")
    
    from hacs_tools.domains import schema_discovery
    
    test_models = ["Patient", "Observation", "MedicationRequest", "InvalidModel"]
    
    for model_name in test_models:
        print(f"\n   Testing schema discovery for: {model_name}")
        
        # Uncomment to step through each model
        # pdb.set_trace()
        
        try:
            result = schema_discovery.get_hacs_resource_schema(
                model_name, 
                include_examples=True,
                include_validation_rules=True
            )
            
            print(f"      Success: {result.success}")
            print(f"      Field count: {result.field_count}")
            print(f"      Message: {result.message}")
            
            if result.success and result.schema:
                # Examine first few field names
                if hasattr(result.schema, 'get') and 'properties' in result.schema:
                    field_names = list(result.schema['properties'].keys())[:5]
                    print(f"      First 5 fields: {field_names}")
                    
                    # Uncomment to examine full schema
                    # pdb.set_trace()
        
        except Exception as e:
            print(f"      ❌ Exception: {e}")
            # Uncomment to debug schema discovery exceptions
            # pdb.set_trace()


def debug_validation_errors():
    """Debug validation errors with detailed analysis."""
    print("\n🚨 Debugging validation errors...")
    
    from hacs_models import MedicationRequest
    from pydantic import ValidationError
    
    # Intentionally create invalid data to debug validation
    invalid_data_cases = [
        {
            "name": "Missing required fields",
            "data": {"medication_codeable_concept": {"text": "Aspirin"}}
        },
        {
            "name": "Invalid enum value", 
            "data": {
                "status": "invalid_status",
                "intent": "order",
                "subject": "Patient/123"
            }
        },
        {
            "name": "Wrong data type",
            "data": {
                "status": "active",
                "intent": "order", 
                "subject": "Patient/123",
                "dosage_instruction": "wrong_type_should_be_list"
            }
        }
    ]
    
    for case in invalid_data_cases:
        print(f"\n   Testing: {case['name']}")
        
        # Uncomment to step through each validation case
        # pdb.set_trace()
        
        try:
            med_request = MedicationRequest(**case['data'])
            print(f"      ❌ Unexpected success - validation should have failed!")
            
        except ValidationError as e:
            print(f"      ✅ Caught expected ValidationError:")
            print(f"         Error count: {len(e.errors())}")
            
            for i, error in enumerate(e.errors()[:3]):  # Show first 3 errors
                print(f"         Error {i+1}:")
                print(f"           Field: {error['loc']}")
                print(f"           Type: {error['type']}")
                print(f"           Message: {error['msg']}")
            
            # Uncomment to examine validation errors in detail
            # pdb.set_trace()
        
        except Exception as e:
            print(f"      ❌ Unexpected exception: {type(e).__name__}: {e}")
            # Uncomment to debug unexpected errors
            # pdb.set_trace()


if __name__ == "__main__":
    print("🎯 HACS Interactive Debugging Example")
    print("="*50)
    print("💡 Tip: Edit this file and uncomment pdb.set_trace() lines to enable interactive debugging")
    print("💡 When pdb starts, use 'h' for help, 'n' for next line, 's' to step into functions")
    print("="*50)
    
    try:
        debug_model_creation()
        debug_schema_discovery()
        debug_validation_errors()
        
        print("\n✅ All debugging examples completed successfully!")
        print("💡 To debug interactively, uncomment pdb.set_trace() lines and re-run")
        
        # Add sleep for log analysis as preferred
        print("\n⏱️  Sleep for 3 seconds to allow log analysis...")
        time.sleep(3)
        print("⏰ Sleep completed")
        
    except KeyboardInterrupt:
        print("\n🛑 Debugging session interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error in debugging session: {e}")
        print("💡 This is where you'd set a breakpoint to investigate!")
        # Uncomment to debug the debugging script itself
        # pdb.set_trace()
        raise
