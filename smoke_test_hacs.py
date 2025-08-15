#!/usr/bin/env python3
"""
HACS Smoke Test Suite
Comprehensive validation of HACS models, tools, and integrations.
Designed for CI/CD and development validation.
"""

import os
import sys
import time
import traceback
from typing import Dict, List, Any, Tuple


def setup_environment():
    """Set up the test environment."""
    os.environ.setdefault("PYTHONPATH", ".")
    
    # Add packages to path if needed
    packages_path = os.path.join(os.getcwd(), "packages")
    if packages_path not in sys.path:
        for pkg in ["hacs-models", "hacs-core", "hacs-tools", "hacs-registry", "hacs-utils"]:
            pkg_path = os.path.join(packages_path, pkg, "src")
            if os.path.exists(pkg_path) and pkg_path not in sys.path:
                sys.path.insert(0, pkg_path)


def run_test_suite(verbose: bool = False) -> Tuple[bool, Dict[str, Any]]:
    """
    Run the comprehensive HACS smoke test suite.
    
    Returns:
        Tuple of (success, results_dict)
    """
    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tests": {},
        "summary": {"passed": 0, "failed": 0, "total": 0},
        "errors": []
    }
    
    def log(message: str, level: str = "INFO"):
        if verbose:
            print(f"[{level}] {message}")
    
    def run_test(test_name: str, test_func) -> bool:
        """Run a single test and record results."""
        log(f"Running {test_name}...")
        try:
            start_time = time.time()
            test_result = test_func()
            duration = time.time() - start_time
            
            results["tests"][test_name] = {
                "status": "PASSED" if test_result else "FAILED",
                "duration": round(duration, 3),
                "details": getattr(test_func, '_last_result', None)
            }
            
            if test_result:
                results["summary"]["passed"] += 1
                log(f"✅ {test_name} PASSED ({duration:.3f}s)")
            else:
                results["summary"]["failed"] += 1
                log(f"❌ {test_name} FAILED ({duration:.3f}s)", "ERROR")
            
            results["summary"]["total"] += 1
            return test_result
            
        except Exception as e:
            duration = time.time() - start_time if 'start_time' in locals() else 0
            error_msg = f"{test_name}: {str(e)}"
            results["errors"].append(error_msg)
            results["tests"][test_name] = {
                "status": "ERROR",
                "duration": round(duration, 3),
                "error": str(e),
                "traceback": traceback.format_exc()
            }
            results["summary"]["failed"] += 1
            results["summary"]["total"] += 1
            log(f"💥 {test_name} ERROR: {e}", "ERROR")
            if verbose:
                log(traceback.format_exc(), "DEBUG")
            return False
    
    # Test 1: Model Registry Validation
    def test_model_registry():
        from hacs_models import get_model_registry, validate_model_compatibility
        
        registry = get_model_registry()
        if len(registry) < 20:  # We should have at least 20 models
            return False
        
        compatibility = validate_model_compatibility()
        test_model_registry._last_result = {
            "model_count": len(registry),
            "compatibility": compatibility,
            "models": list(registry.keys())
        }
        return compatibility
    
    # Test 2: Schema Discovery 
    def test_schema_discovery():
        from hacs_tools.domains import schema_discovery
        
        core_models = ["Patient", "Observation", "Encounter", "Condition", 
                      "MedicationRequest", "Medication", "Procedure", "Goal",
                      "ServiceRequest", "DiagnosticReport"]
        
        results_data = {}
        all_passed = True
        
        for model in core_models:
            result = schema_discovery.get_hacs_resource_schema(
                model, include_examples=False, include_validation_rules=True
            )
            results_data[model] = {
                "success": result.success,
                "field_count": result.field_count
            }
            if not result.success or result.field_count <= 0:
                all_passed = False
        
        test_schema_discovery._last_result = results_data
        return all_passed
    
    # Test 3: Resource Management CRUD
    def test_resource_management():
        from hacs_tools.domains import resource_management
        
        test_cases = [
            ("Patient", {"full_name": "Smoke Test Patient", "gender": "other"}),
            ("Observation", {
                "status": "final",
                "code": {"text": "Test Observation"},
                "value_string": "Test Value"
            }),
            ("MedicationRequest", {
                "status": "active", 
                "intent": "order",
                "subject": "Patient/smoke-test",
                "medication_codeable_concept": {"text": "Test Medication"}
            }),
            ("Procedure", {
                "status": "completed",
                "code": {"text": "Test Procedure"},
                "subject": "Patient/smoke-test"
            })
        ]
        
        results_data = {}
        all_passed = True
        
        for resource_type, data in test_cases:
            result = resource_management.create_hacs_record(
                actor_name="SmokeTest",
                resource_type=resource_type,
                resource_data=data
            )
            results_data[resource_type] = {
                "success": result.success,
                "message": result.message
            }
            if not result.success:
                all_passed = False
        
        test_resource_management._last_result = results_data
        return all_passed
    
    # Test 4: Complex Data Structures
    def test_complex_structures():
        from hacs_tools.domains import resource_management
        
        complex_observation = {
            "status": "final",
            "code": {
                "text": "Complex Blood Panel",
                "coding": [{"system": "http://loinc.org", "code": "24323-8"}]
            },
            "category": [{"text": "laboratory"}],
            "value_quantity": {"value": 4.5, "unit": "10*12/L"},
            "reference_range": [{
                "low": {"value": 4.0, "unit": "10*12/L"},
                "high": {"value": 6.0, "unit": "10*12/L"},
                "text": "Normal range"
            }],
            "agent_context": {
                "lab_section": "hematology",
                "analyzer": "automated",
                "quality_flags": ["normal_sample", "no_interference"]
            }
        }
        
        result = resource_management.create_hacs_record(
            actor_name="SmokeTest",
            resource_type="Observation", 
            resource_data=complex_observation
        )
        
        test_complex_structures._last_result = {
            "success": result.success,
            "message": result.message
        }
        return result.success
    
    # Test 5: Validation Error Handling
    def test_validation_errors():
        from hacs_tools.domains import resource_management
        
        # Test that invalid data properly fails
        invalid_cases = [
            ("InvalidResource", {}),  # Invalid resource type
            ("MedicationRequest", {}),  # Missing required fields
            ("Observation", {"status": "invalid_status", "code": {"text": "Test"}})  # Invalid enum
        ]
        
        results_data = {}
        all_handled_correctly = True
        
        for resource_type, data in invalid_cases:
            result = resource_management.create_hacs_record(
                actor_name="SmokeTest",
                resource_type=resource_type,
                resource_data=data
            )
            results_data[f"{resource_type}_invalid"] = {
                "correctly_failed": not result.success,
                "message": result.message
            }
            # These should all fail - if any succeed, that's wrong
            if result.success:
                all_handled_correctly = False
        
        test_validation_errors._last_result = results_data
        return all_handled_correctly
    
    # Test 6: Performance Benchmarks
    def test_performance():
        from hacs_tools.domains import resource_management, schema_discovery
        import time
        
        # Benchmark schema discovery
        start = time.time()
        for _ in range(10):
            schema_discovery.get_hacs_resource_schema("Patient")
        schema_time = (time.time() - start) / 10
        
        # Benchmark resource creation
        start = time.time()
        for i in range(20):
            resource_management.create_hacs_record(
                actor_name="PerfTest",
                resource_type="Patient",
                resource_data={"full_name": f"Perf Test {i}", "gender": "other"}
            )
        create_time = (time.time() - start) / 20
        
        test_performance._last_result = {
            "schema_discovery_ms": round(schema_time * 1000, 2),
            "resource_creation_ms": round(create_time * 1000, 2)
        }
        
        # Performance thresholds (generous for CI)
        return schema_time < 0.5 and create_time < 0.1
    
    # Run all tests
    log("🚀 Starting HACS Smoke Test Suite")
    log("="*50)
    
    success = True
    success &= run_test("Model Registry Validation", test_model_registry)
    success &= run_test("Schema Discovery", test_schema_discovery)
    success &= run_test("Resource Management CRUD", test_resource_management)
    success &= run_test("Complex Data Structures", test_complex_structures)
    success &= run_test("Validation Error Handling", test_validation_errors)
    success &= run_test("Performance Benchmarks", test_performance)
    
    log("="*50)
    log(f"🎯 Test Summary: {results['summary']['passed']}/{results['summary']['total']} passed")
    
    if results["errors"]:
        log(f"❌ Errors encountered: {len(results['errors'])}")
        for error in results["errors"]:
            log(f"   - {error}", "ERROR")
    
    if success:
        log("✅ All smoke tests PASSED!")
    else:
        log("❌ Some smoke tests FAILED!")
    
    return success, results


def main():
    """Main entry point for smoke tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="HACS Smoke Test Suite")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--sleep", type=float, default=2.0, help="Sleep time for log analysis (default: 2.0s)")
    
    args = parser.parse_args()
    
    setup_environment()
    
    print("🎯 HACS Smoke Test Suite")
    print("🔧 Validating models, tools, and integrations...")
    
    success, results = run_test_suite(verbose=args.verbose)
    
    if args.json:
        import json
        print(json.dumps(results, indent=2))
    
    # Sleep for log analysis as requested
    if args.sleep > 0:
        print(f"\n⏱️  Sleeping for {args.sleep}s to allow log analysis...")
        time.sleep(args.sleep)
        print("⏰ Sleep completed")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
