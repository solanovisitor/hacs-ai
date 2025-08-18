import os
import pdb
import pytest
from typing import Any


def test_debug_validation_edge_cases():
    """Test edge cases and error conditions with debugging support."""
    os.environ.setdefault("PYTHONPATH", ".")
    
    print("\n🚨 TESTING EDGE CASES AND ERROR CONDITIONS")
    print("="*60)
    
    from hacs_tools.domains import resource_management, schema_discovery
    
    # Test 1: Invalid resource type
    print("\n🔍 Test 1: Invalid resource type")
    try:
        result = resource_management.create_record(
            actor_name="Tester",
            resource_type="NonExistentResource",
            resource_data={"some": "data"}
        )
        print(f"   Result: success={result.success}, message='{result.message}'")
        assert not result.success, "Should fail for invalid resource type"
        
    except Exception as e:
        print(f"   Exception caught: {type(e).__name__}: {e}")
        # This is expected for invalid resource types
    
    # Test 2: Missing required fields
    print("\n🔍 Test 2: Missing required fields for MedicationRequest")
    try:
        result = resource_management.create_record(
            actor_name="Tester",
            resource_type="MedicationRequest",
            resource_data={"medication_codeable_concept": {"text": "Aspirin"}}  # Missing status, intent, subject
        )
        print(f"   Result: success={result.success}, message='{result.message}'")
        assert not result.success, "Should fail for missing required fields"
        
    except Exception as e:
        print(f"   Exception caught: {type(e).__name__}: {e}")
        # Uncomment to debug validation errors
        # pdb.set_trace()
    
    # Test 3: Invalid field values
    print("\n🔍 Test 3: Invalid field values")
    try:
        result = resource_management.create_record(
            actor_name="Tester", 
            resource_type="Observation",
            resource_data={
                "status": "invalid_status",  # Invalid enum value
                "code": {"text": "Test"},
                "value_string": "Some value"
            }
        )
        print(f"   Result: success={result.success}, message='{result.message}'")
        assert not result.success, "Should fail for invalid enum value"
        
    except Exception as e:
        print(f"   Exception caught: {type(e).__name__}: {e}")
    
    # Test 4: Schema discovery for non-existent model
    print("\n🔍 Test 4: Schema discovery for non-existent model")
    try:
        result = schema_discovery.get_hacs_resource_schema("NonExistentModel")
        print(f"   Result: success={result.success}, message='{result.message}'")
        assert not result.success, "Should fail for non-existent model"
        
    except Exception as e:
        print(f"   Exception caught: {type(e).__name__}: {e}")
    
    # Test 5: Empty data creation (should work with defaults)
    print("\n🔍 Test 5: Empty data creation")
    try:
        result = resource_management.create_record(
            actor_name="Tester",
            resource_type="Patient", 
            resource_data={}  # Empty data, should use defaults
        )
        print(f"   Result: success={result.success}, message='{result.message}'")
        # Patient should work with empty data due to defaults
        
    except Exception as e:
        print(f"   Exception caught: {type(e).__name__}: {e}")
    
    print("\n✅ Edge case testing completed")


def test_debug_complex_data_structures():
    """Test complex nested data structures with debugging."""
    os.environ.setdefault("PYTHONPATH", ".")
    
    print("\n🧬 TESTING COMPLEX DATA STRUCTURES")
    print("="*50)
    
    from hacs_tools.domains import resource_management
    
    # Complex nested observation with all optional fields
    complex_observation = {
        "status": "final",
        "code": {
            "text": "Complete Blood Count",
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "58410-2",
                    "display": "CBC panel - Blood by Automated count"
                }
            ]
        },
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category", 
                        "code": "laboratory",
                        "display": "Laboratory"
                    }
                ],
                "text": "Laboratory"
            }
        ],
        "value_quantity": {
            "value": 4.5,
            "unit": "10*6/uL",
            "system": "http://unitsofmeasure.org",
            "code": "10*6/uL"
        },
        "reference_range": [
            {
                "low": {"value": 4.0, "unit": "10*6/uL"},
                "high": {"value": 6.0, "unit": "10*6/uL"},
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/referencerange-meaning",
                            "code": "normal"
                        }
                    ]
                },
                "text": "Normal range for adult RBC count"
            }
        ],
        "interpretation_detail": {
            "overall_interpretation": "normal",
            "clinical_significance": "low",
            "recommendations": ["Continue current treatment"],
            "flags": ["in_range"]
        },
        "agent_context": {
            "lab_section": "hematology",
            "processing_time": "2 hours",
            "quality_control": "passed",
            "analyst_notes": "Sample processed without issues",
            "automated_analysis": True,
            "cross_references": ["previous_cbc_2023_01_15", "baseline_labs"]
        }
    }
    
    print("🔍 Creating complex observation with full nested structure...")
    try:
        result = resource_management.create_record(
            actor_name="ComplexTester",
            resource_type="Observation",
            resource_data=complex_observation
        )
        
        print(f"   Result: success={result.success}")
        print(f"   Message: {result.message}")
        
        if not result.success:
            print("   🚨 Complex structure creation failed!")
            # Uncomment to debug complex structure issues
            # pdb.set_trace()
        else:
            print("   ✅ Complex structure creation succeeded!")
            
        assert result.success, f"Complex observation creation failed: {result.message}"
        
    except Exception as e:
        print(f"   Exception: {type(e).__name__}: {e}")
        # Uncomment to debug exceptions in complex structures
        # pdb.set_trace()
        raise
    
    # Complex MedicationRequest
    complex_medication_request = {
        "status": "active",
        "intent": "order",
        "subject": "Patient/complex-test-123",
        "medication_codeable_concept": {
            "text": "Amoxicillin 500mg Capsules",
            "coding": [
                {
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "308182",
                    "display": "amoxicillin 500 MG Oral Capsule"
                }
            ]
        },
        "dosage_instruction": [
            {
                "text": "Take 1 capsule by mouth three times daily with food for 10 days",
                "timing": {
                    "repeat": {
                        "frequency": 3,
                        "period": 1,
                        "period_unit": "d"
                    }
                },
                "route": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "26643006",
                            "display": "Oral route"
                        }
                    ]
                },
                "dose_and_rate": [
                    {
                        "dose_quantity": {
                            "value": 1,
                            "unit": "capsule",
                            "system": "http://terminology.hl7.org/CodeSystem/v3-orderableDrugForm",
                            "code": "CAP"
                        }
                    }
                ]
            }
        ],
        "dispense_request": {
            "quantity": {
                "value": 30,
                "unit": "capsule",
                "system": "http://terminology.hl7.org/CodeSystem/v3-orderableDrugForm",
                "code": "CAP"
            },
            "expected_supply_duration": {
                "value": 10,
                "unit": "days",
                "system": "http://unitsofmeasure.org",
                "code": "d"
            }
        },
        "agent_context": {
            "prescriber_specialty": "family_medicine",
            "indication": "bacterial_infection",
            "allergy_checked": True,
            "drug_interactions_reviewed": True,
            "patient_education_provided": True,
            "prescription_confidence": 0.95
        }
    }
    
    print("\n🔍 Creating complex medication request...")
    try:
        result = resource_management.create_record(
            actor_name="ComplexTester",
            resource_type="MedicationRequest",
            resource_data=complex_medication_request
        )
        
        print(f"   Result: success={result.success}")
        print(f"   Message: {result.message}")
        
        assert result.success, f"Complex medication request creation failed: {result.message}"
        print("   ✅ Complex medication request creation succeeded!")
        
    except Exception as e:
        print(f"   Exception: {type(e).__name__}: {e}")
        raise
    
    print("\n✅ Complex data structure testing completed")


def test_debug_pydantic_validation_details():
    """Debug Pydantic validation with detailed error information."""
    os.environ.setdefault("PYTHONPATH", ".")
    
    print("\n🔬 DEBUGGING PYDANTIC VALIDATION DETAILS")
    print("="*55)
    
    try:
        from hacs_models import Observation, MedicationRequest
        from pydantic import ValidationError
        
        print("🔍 Testing direct Pydantic model validation...")
        
        # Test 1: Direct model creation with missing required fields
        print("\n   Test 1: MedicationRequest with missing fields")
        try:
            med_req = MedicationRequest(
                # Missing required fields: status, intent, subject
                medication_codeable_concept={"text": "Aspirin"}
            )
            print("   ❌ Should have failed but didn't!")
            
        except ValidationError as e:
            print(f"   ✅ Caught expected ValidationError:")
            for error in e.errors():
                print(f"      - Field: {error['loc']}, Type: {error['type']}, Message: {error['msg']}")
        
        # Test 2: Direct model creation with invalid enum
        print("\n   Test 2: Observation with invalid status enum")
        try:
            obs = Observation(
                status="invalid_status",  # Should be one of: registered, preliminary, final, etc.
                code={"text": "Test"}
            )
            print("   ❌ Should have failed but didn't!")
            
        except ValidationError as e:
            print(f"   ✅ Caught expected ValidationError:")
            for error in e.errors():
                print(f"      - Field: {error['loc']}, Type: {error['type']}, Message: {error['msg']}")
        
        # Test 3: Successful creation
        print("\n   Test 3: Valid model creation")
        try:
            valid_obs = Observation(
                status="final",
                code={"text": "Blood Pressure"},
                value_string="120/80 mmHg"
            )
            print(f"   ✅ Successfully created Observation with ID: {valid_obs.id}")
            print(f"      Status: {valid_obs.status}")
            print(f"      Code: {valid_obs.code}")
            
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            # Uncomment to debug unexpected validation issues
            # pdb.set_trace()
    
    except ImportError as e:
        print(f"❌ Import error: {e}")
    
    print("\n✅ Pydantic validation debugging completed")


if __name__ == "__main__":
    # Run tests directly for debugging
    test_debug_validation_edge_cases()
    test_debug_complex_data_structures() 
    test_debug_pydantic_validation_details()
