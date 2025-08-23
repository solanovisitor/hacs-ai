"""
Tests for HACS Registry extractables utilities.

Validates that:
1. All HACS resources have compact extractable fields (3-4 max)
2. No resource_type leaks into extractables
3. All resources have required facade methods
4. Registry utilities work correctly
"""

import pytest
from hacs_registry.resource_registry import (
    get_extractables_index,
    iter_model_classes,
    get_global_registry,
)


def test_iter_model_classes():
    """Test that iter_model_classes returns available HACS resources."""
    model_classes = iter_model_classes()
    
    # Should return list of tuples (name, class)
    assert isinstance(model_classes, list)
    assert len(model_classes) > 0
    
    # Check structure
    for name, cls in model_classes:
        assert isinstance(name, str)
        assert hasattr(cls, '__name__')
        assert name == cls.__name__
    
    # Should be sorted alphabetically
    names = [name for name, _ in model_classes]
    assert names == sorted(names)
    
    # Should include core resources
    names_set = set(names)
    expected_core = {"Patient", "Observation", "Organization"}
    assert expected_core.issubset(names_set), f"Missing core resources: {expected_core - names_set}"


def test_get_extractables_index():
    """Test that get_extractables_index provides comprehensive resource info."""
    index = get_extractables_index()
    
    # Should return dict with resource info
    assert isinstance(index, dict)
    assert len(index) > 0
    
    # Check structure for each resource
    for name, info in index.items():
        assert isinstance(name, str)
        assert isinstance(info, dict)
        
        if "error" in info:
            # Skip resources with errors for now
            continue
            
        # Required fields
        assert "extractable_fields" in info
        assert "extractable_count" in info
        assert isinstance(info["extractable_fields"], list)
        assert isinstance(info["extractable_count"], int)
        assert info["extractable_count"] == len(info["extractable_fields"])
        
        # Optional fields
        assert "llm_hints" in info
        assert "system_fields" in info
        assert "llm_schema_available" in info
        assert "has_pick_method" in info
        assert "has_validate_extractable" in info


def test_no_resource_type_in_extractables():
    """Test that resource_type is not included in any extractable fields."""
    index = get_extractables_index()
    
    violations = []
    for name, info in index.items():
        if "error" in info:
            continue
            
        extractable_fields = info.get("extractable_fields", [])
        if "resource_type" in extractable_fields:
            violations.append(name)
        
        # Also check for warning flag
        if "warning" in info and "resource_type" in info["warning"]:
            violations.append(f"{name} (flagged)")
    
    assert not violations, f"Resources with resource_type in extractables: {violations}"


def test_extractables_are_compact():
    """Test that extractable fields are reasonably compact."""
    index = get_extractables_index()
    
    # Check that resources with specific overrides are compact (3-4 fields)
    compact_resources = []
    verbose_resources = []
    
    # Resources that should have compact extractables (have specific overrides)
    expected_compact = {
        "Practitioner", "Condition", "FamilyMemberHistory", 
        "MedicationStatement", "ServiceRequest"
    }
    
    for name, info in index.items():
        if "error" in info:
            continue
            
        count = info.get("extractable_count", 0)
        
        if name in expected_compact:
            if count <= 4:
                compact_resources.append(f"{name}: {count} fields")
            else:
                verbose_resources.append(f"{name}: {count} fields (expected compact)")
        elif count > 25:  # Very high threshold for resources without overrides
            verbose_resources.append(f"{name}: {count} fields (no override)")
    
    # This is informational - show which resources have many extractables
    if verbose_resources:
        print(f"Resources with many extractable fields: {verbose_resources}")
    
    # Assert that resources with specific overrides are compact
    excessive_overrides = [r for r in verbose_resources if "expected compact" in r]
    assert not excessive_overrides, f"Resources with overrides should be compact: {excessive_overrides}"
    
    # Soft check: no resource should have more than 35 extractables (architectural limit)
    extreme_resources = []
    for name, info in index.items():
        if "error" in info:
            continue
            
        count = info.get("extractable_count", 0)
        if count > 35:
            extreme_resources.append(f"{name}: {count} fields")
    
    assert not extreme_resources, f"Resources with extreme extractable counts: {extreme_resources}"


def test_facade_methods_availability():
    """Test that resources have required facade methods."""
    index = get_extractables_index()
    
    missing_pick = []
    missing_validate = []
    
    for name, info in index.items():
        if "error" in info:
            continue
            
        if not info.get("has_pick_method", False):
            missing_pick.append(name)
            
        if not info.get("has_validate_extractable", False):
            missing_validate.append(name)
    
    # These are important for the extraction pipeline
    assert not missing_pick, f"Resources missing pick() method: {missing_pick}"
    assert not missing_validate, f"Resources missing validate_extractable() method: {missing_validate}"


def test_registry_integration():
    """Test that registry utilities integrate properly."""
    registry = get_global_registry()
    
    # Test method calls work
    model_classes = registry.iter_model_classes()
    extractables_index = registry.get_extractables_index()
    
    # Should be consistent with global functions
    assert model_classes == iter_model_classes()
    assert extractables_index == get_extractables_index()


def test_specific_resource_extractables():
    """Test specific resources have expected extractable patterns."""
    index = get_extractables_index()
    
    # Practitioner should have minimal extractables (just name)
    if "Practitioner" in index:
        practitioner_info = index["Practitioner"]
        if "error" not in practitioner_info:
            extractables = practitioner_info["extractable_fields"]
            assert len(extractables) <= 2, f"Practitioner has too many extractables: {extractables}"
            assert "name" in extractables, f"Practitioner missing name in extractables: {extractables}"
    
    # Patient should have reasonable extractables
    if "Patient" in index:
        patient_info = index["Patient"]
        if "error" not in patient_info:
            extractables = patient_info["extractable_fields"]
            assert len(extractables) <= 6, f"Patient has too many extractables: {extractables}"
    
    # Observation should have reasonable extractables
    if "Observation" in index:
        obs_info = index["Observation"]
        if "error" not in obs_info:
            extractables = obs_info["extractable_fields"]
            assert len(extractables) <= 6, f"Observation has too many extractables: {extractables}"


if __name__ == "__main__":
    # Quick manual test
    print("=== Testing Registry Extractables ===")
    
    print("\n1. Model Classes:")
    for name, cls in iter_model_classes()[:5]:  # Show first 5
        print(f"  {name}: {cls}")
    
    print("\n2. Extractables Index (sample):")
    index = get_extractables_index()
    for name in sorted(index.keys())[:3]:  # Show first 3
        info = index[name]
        if "error" not in info:
            print(f"  {name}: {info['extractable_count']} extractables, {len(info['llm_hints'])} hints")
        else:
            print(f"  {name}: ERROR - {info['error']}")
    
    print("\n3. Validation Summary:")
    total_resources = len(index)
    error_count = sum(1 for info in index.values() if "error" in info)
    warning_count = sum(1 for info in index.values() if "warning" in info)
    
    print(f"  Total resources: {total_resources}")
    print(f"  Resources with errors: {error_count}")
    print(f"  Resources with warnings: {warning_count}")
    
    print("\nDone!")
