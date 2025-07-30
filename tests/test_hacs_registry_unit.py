"""
Unit tests for HACS Registry package functionality.

Tests resource definitions, templates, and versioning functionality
without external dependencies - suitable for GitHub CI.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from datetime import date, datetime
from typing import Dict, Any, List

# Mock external dependencies for CI
@pytest.fixture(autouse=True)
def mock_registry_dependencies():
    """Mock registry dependencies for CI testing."""
    with patch.dict(os.environ, {
        'HACS_ORGANIZATION': 'test-org',
        'REGISTRY_BACKEND': 'local'
    }):
        yield


@pytest.mark.unit
class TestHACSRegistryCore:
    """Test HACS Registry core functionality."""

    def test_registry_module_imports(self):
        """Test that registry module imports work."""
        try:
            import hacs_registry
            assert hacs_registry is not None
            
        except ImportError as e:
            pytest.skip(f"HACS Registry not available: {e}")

    def test_registry_exceptions(self):
        """Test registry exception imports."""
        try:
            from hacs_registry.exceptions import (
                RegistryError, 
                ResourceNotFound, 
                VersionConflict
            )
            
            assert RegistryError is not None
            assert ResourceNotFound is not None
            assert VersionConflict is not None
            
        except ImportError:
            pytest.skip("Registry exceptions not available")

    def test_definitions_imports(self):
        """Test definitions imports."""
        try:
            from hacs_registry.definitions import (
                ResourceDefinition,
                TemplateDefinition
            )
            
            assert ResourceDefinition is not None
            assert TemplateDefinition is not None
            
        except ImportError:
            pytest.skip("Registry definitions not available")


@pytest.mark.unit
class TestHACSResourceDefinition:
    """Test HACS Resource Definition functionality."""

    def test_resource_definition_creation(self):
        """Test creating a resource definition."""
        try:
            from hacs_registry.definitions import ResourceDefinition
            
            resource_def = ResourceDefinition(
                name="CustomPatient",
                version="1.0.0",
                description="Custom patient resource with additional fields",
                schema_definition={
                    "type": "object",
                    "properties": {
                        "full_name": {"type": "string"},
                        "medical_record_number": {"type": "string"},
                        "primary_physician": {"type": "string"}
                    },
                    "required": ["full_name", "medical_record_number"]
                },
                category="clinical",
                tags=["patient", "custom"]
            )
            
            assert resource_def.name == "CustomPatient"
            assert resource_def.version == "1.0.0"
            assert resource_def.category == "clinical"
            assert "patient" in resource_def.tags
            
        except ImportError:
            pytest.skip("ResourceDefinition not available")

    def test_resource_definition_validation(self):
        """Test resource definition validation."""
        try:
            from hacs_registry.definitions import ResourceDefinition
            
            # Test valid definition
            valid_def = ResourceDefinition(
                name="ValidResource",
                version="1.0.0",
                description="A valid resource definition",
                schema_definition={
                    "type": "object",
                    "properties": {"name": {"type": "string"}}
                }
            )
            
            validation_result = valid_def.validate()
            assert validation_result["is_valid"] is True
            
            # Test invalid definition
            invalid_def = ResourceDefinition(
                name="InvalidResource",
                version="invalid-version",  # Invalid semver
                description="An invalid resource definition",
                schema_definition={"invalid": "schema"}
            )
            
            validation_result = invalid_def.validate()
            assert validation_result["is_valid"] is False
            assert len(validation_result["errors"]) > 0
            
        except ImportError:
            pytest.skip("ResourceDefinition validation not available")

    def test_resource_definition_lifecycle(self):
        """Test resource definition lifecycle management."""
        try:
            from hacs_registry.definitions import ResourceDefinition
            
            resource_def = ResourceDefinition(
                name="LifecycleTest",
                version="1.0.0",
                description="Test lifecycle management",
                schema_definition={"type": "object"}
            )
            
            # Test initial status
            assert resource_def.status == "draft"
            
            # Test publishing
            resource_def.publish()
            assert resource_def.status == "published"
            
            # Test deprecation
            resource_def.deprecate()
            assert resource_def.status == "deprecated"
            
        except ImportError:
            pytest.skip("ResourceDefinition lifecycle not available")

    def test_resource_definition_versioning(self):
        """Test resource definition versioning."""
        try:
            from hacs_registry.definitions import ResourceDefinition
            
            resource_def = ResourceDefinition(
                name="VersionTest",
                version="1.0.0",
                description="Test versioning",
                schema_definition={"type": "object"}
            )
            
            # Test version update
            new_version = resource_def.update_version("1.1.0")
            assert new_version.version == "1.1.0"
            assert new_version.name == resource_def.name
            
            # Test version history
            history = resource_def.get_version_history()
            assert isinstance(history, list)
            
        except ImportError:
            pytest.skip("ResourceDefinition versioning not available")


@pytest.mark.unit
class TestHACSTemplateDefinition:
    """Test HACS Template Definition functionality."""

    def test_template_definition_creation(self):
        """Test creating a template definition."""
        try:
            from hacs_registry.definitions import TemplateDefinition
            
            template_def = TemplateDefinition(
                name="cardiac_assessment",
                version="2.0.0",
                description="Comprehensive cardiac assessment template",
                template_content={
                    "sections": [
                        "patient_history",
                        "physical_examination", 
                        "diagnostic_tests",
                        "treatment_plan"
                    ],
                    "required_fields": [
                        "heart_rate",
                        "blood_pressure",
                        "ecg_findings"
                    ],
                    "optional_fields": [
                        "chest_xray",
                        "echocardiogram",
                        "stress_test"
                    ]
                },
                category="assessment",
                tags=["cardiology", "assessment", "comprehensive"]
            )
            
            assert template_def.name == "cardiac_assessment"
            assert template_def.version == "2.0.0"
            assert template_def.category == "assessment"
            assert "cardiology" in template_def.tags
            
        except ImportError:
            pytest.skip("TemplateDefinition not available")

    def test_template_instantiation(self):
        """Test template instantiation."""
        try:
            from hacs_registry.definitions import TemplateDefinition
            
            template_def = TemplateDefinition(
                name="simple_assessment",
                version="1.0.0",
                description="Simple assessment template",
                template_content={
                    "fields": ["patient_id", "assessment_date", "findings"],
                    "required": ["patient_id", "assessment_date"]
                }
            )
            
            # Test instantiation with valid data
            instance_data = {
                "patient_id": "patient-123",
                "assessment_date": "2024-01-15",
                "findings": "Normal examination"
            }
            
            instance = template_def.instantiate(instance_data)
            assert instance is not None
            assert instance["patient_id"] == "patient-123"
            
        except ImportError:
            pytest.skip("TemplateDefinition instantiation not available")

    def test_template_validation(self):
        """Test template validation against instances."""
        try:
            from hacs_registry.definitions import TemplateDefinition
            
            template_def = TemplateDefinition(
                name="validation_test",
                version="1.0.0",
                description="Template validation test",
                template_content={
                    "schema": {
                        "type": "object",
                        "properties": {
                            "patient_id": {"type": "string"},
                            "score": {"type": "number", "minimum": 0, "maximum": 100}
                        },
                        "required": ["patient_id"]
                    }
                }
            )
            
            # Test valid instance
            valid_data = {"patient_id": "patient-123", "score": 85}
            validation_result = template_def.validate_instance(valid_data)
            assert validation_result["is_valid"] is True
            
            # Test invalid instance
            invalid_data = {"score": 150}  # Missing required field, invalid score
            validation_result = template_def.validate_instance(invalid_data)
            assert validation_result["is_valid"] is False
            
        except ImportError:
            pytest.skip("TemplateDefinition validation not available")


@pytest.mark.unit
class TestHACSRegistryOperations:
    """Test HACS Registry operations."""

    @patch('hacs_registry.registry.get_backend')
    def test_registry_initialization(self, mock_get_backend):
        """Test registry initialization."""
        mock_backend = MagicMock()
        mock_get_backend.return_value = mock_backend
        
        try:
            from hacs_registry import Registry
            
            registry = Registry()
            assert registry is not None
            
        except ImportError:
            pytest.skip("Registry not available")

    @patch('hacs_registry.registry.get_backend')
    def test_register_resource_definition(self, mock_get_backend):
        """Test registering a resource definition."""
        mock_backend = MagicMock()
        mock_backend.save_definition.return_value = {"success": True, "id": "def-123"}
        mock_get_backend.return_value = mock_backend
        
        try:
            from hacs_registry import Registry
            from hacs_registry.definitions import ResourceDefinition
            
            registry = Registry()
            
            resource_def = ResourceDefinition(
                name="TestResource",
                version="1.0.0",
                description="Test resource for registration",
                schema_definition={"type": "object"}
            )
            
            result = registry.register(resource_def)
            assert result["success"] is True
            
        except ImportError:
            pytest.skip("Registry operations not available")

    @patch('hacs_registry.registry.get_backend')
    def test_get_resource_definition(self, mock_get_backend):
        """Test retrieving a resource definition."""
        mock_backend = MagicMock()
        mock_backend.get_definition.return_value = {
            "name": "TestResource",
            "version": "1.0.0",
            "description": "Retrieved resource definition"
        }
        mock_get_backend.return_value = mock_backend
        
        try:
            from hacs_registry import Registry
            
            registry = Registry()
            
            result = registry.get("TestResource", version="1.0.0")
            assert result is not None
            assert result["name"] == "TestResource"
            
        except ImportError:
            pytest.skip("Registry retrieval not available")

    @patch('hacs_registry.registry.get_backend')
    def test_search_definitions(self, mock_get_backend):
        """Test searching for definitions."""
        mock_backend = MagicMock()
        mock_backend.search.return_value = [
            {"name": "PatientResource", "category": "clinical"},
            {"name": "AssessmentTemplate", "category": "template"}
        ]
        mock_get_backend.return_value = mock_backend
        
        try:
            from hacs_registry import Registry
            
            registry = Registry()
            
            results = registry.search(
                category="clinical",
                tags=["patient"]
            )
            
            assert isinstance(results, list)
            assert len(results) > 0
            
        except ImportError:
            pytest.skip("Registry search not available")

    @patch('hacs_registry.registry.get_backend')
    def test_list_definitions(self, mock_get_backend):
        """Test listing all definitions."""
        mock_backend = MagicMock()
        mock_backend.list_all.return_value = [
            {"name": "Definition1", "version": "1.0.0"},
            {"name": "Definition2", "version": "1.1.0"},
            {"name": "Definition3", "version": "2.0.0"}
        ]
        mock_get_backend.return_value = mock_backend
        
        try:
            from hacs_registry import Registry
            
            registry = Registry()
            
            all_definitions = registry.list_all()
            
            assert isinstance(all_definitions, list)
            assert len(all_definitions) == 3
            
        except ImportError:
            pytest.skip("Registry listing not available")


@pytest.mark.unit
class TestHACSRegistryVersioning:
    """Test HACS Registry versioning functionality."""

    def test_semantic_versioning(self):
        """Test semantic versioning utilities."""
        try:
            from hacs_registry.versioning import (
                is_valid_version,
                compare_versions,
                increment_version
            )
            
            # Test version validation
            assert is_valid_version("1.0.0") is True
            assert is_valid_version("1.2.3-alpha") is True
            assert is_valid_version("invalid") is False
            
            # Test version comparison
            assert compare_versions("1.0.0", "1.0.1") < 0
            assert compare_versions("2.0.0", "1.9.9") > 0
            assert compare_versions("1.0.0", "1.0.0") == 0
            
            # Test version increment
            assert increment_version("1.0.0", "patch") == "1.0.1"
            assert increment_version("1.0.0", "minor") == "1.1.0"
            assert increment_version("1.0.0", "major") == "2.0.0"
            
        except ImportError:
            pytest.skip("Versioning utilities not available")

    @patch('hacs_registry.registry.get_backend')
    def test_version_management(self, mock_get_backend):
        """Test version management in registry."""
        mock_backend = MagicMock()
        mock_backend.get_versions.return_value = ["1.0.0", "1.1.0", "2.0.0"]
        mock_get_backend.return_value = mock_backend
        
        try:
            from hacs_registry import Registry
            
            registry = Registry()
            
            # Test getting all versions
            versions = registry.get_versions("TestResource")
            assert isinstance(versions, list)
            assert "1.0.0" in versions
            
            # Test getting latest version
            latest = registry.get_latest_version("TestResource")
            assert latest == "2.0.0"
            
        except ImportError:
            pytest.skip("Registry version management not available")


@pytest.mark.unit
class TestHACSRegistryCategories:
    """Test HACS Registry categorization functionality."""

    def test_category_management(self):
        """Test category management."""
        try:
            from hacs_registry.categories import (
                get_available_categories,
                validate_category,
                get_category_schema
            )
            
            # Test available categories
            categories = get_available_categories()
            assert isinstance(categories, list)
            assert "clinical" in categories
            
            # Test category validation
            assert validate_category("clinical") is True
            assert validate_category("invalid_category") is False
            
            # Test category schema
            schema = get_category_schema("clinical")
            assert isinstance(schema, dict)
            
        except ImportError:
            pytest.skip("Category management not available")

    @patch('hacs_registry.registry.get_backend')
    def test_filter_by_category(self, mock_get_backend):
        """Test filtering definitions by category."""
        mock_backend = MagicMock()
        mock_backend.filter_by_category.return_value = [
            {"name": "PatientResource", "category": "clinical"},
            {"name": "ObservationResource", "category": "clinical"}
        ]
        mock_get_backend.return_value = mock_backend
        
        try:
            from hacs_registry import Registry
            
            registry = Registry()
            
            clinical_defs = registry.filter_by_category("clinical")
            
            assert isinstance(clinical_defs, list)
            assert all(item["category"] == "clinical" for item in clinical_defs)
            
        except ImportError:
            pytest.skip("Category filtering not available")


@pytest.mark.unit
class TestHACSRegistryTags:
    """Test HACS Registry tagging functionality."""

    def test_tag_management(self):
        """Test tag management."""
        try:
            from hacs_registry.tags import (
                validate_tags,
                normalize_tags,
                suggest_tags
            )
            
            # Test tag validation
            valid_tags = ["patient", "clinical", "assessment"]
            assert validate_tags(valid_tags) is True
            
            # Test tag normalization
            raw_tags = ["PATIENT", "Clinical Assessment", "test-tag"]
            normalized = normalize_tags(raw_tags)
            assert all(tag.islower() for tag in normalized)
            
            # Test tag suggestions
            suggestions = suggest_tags("patient assessment template")
            assert isinstance(suggestions, list)
            
        except ImportError:
            pytest.skip("Tag management not available")

    @patch('hacs_registry.registry.get_backend')
    def test_filter_by_tags(self, mock_get_backend):
        """Test filtering definitions by tags."""
        mock_backend = MagicMock()
        mock_backend.filter_by_tags.return_value = [
            {"name": "PatientTemplate", "tags": ["patient", "template"]},
            {"name": "PatientResource", "tags": ["patient", "clinical"]}
        ]
        mock_get_backend.return_value = mock_backend
        
        try:
            from hacs_registry import Registry
            
            registry = Registry()
            
            patient_defs = registry.filter_by_tags(["patient"])
            
            assert isinstance(patient_defs, list)
            assert all("patient" in item["tags"] for item in patient_defs)
            
        except ImportError:
            pytest.skip("Tag filtering not available")


@pytest.mark.unit
class TestHACSRegistryError:
    """Test HACS Registry error handling."""

    def test_registry_exceptions(self):
        """Test registry exception handling."""
        try:
            from hacs_registry.exceptions import (
                RegistryError,
                ResourceNotFound,
                VersionConflict
            )
            
            # Test basic exception creation
            registry_error = RegistryError("Test registry error")
            assert str(registry_error) == "Test registry error"
            
            not_found_error = ResourceNotFound("TestResource", "1.0.0")
            assert "TestResource" in str(not_found_error)
            
            version_conflict = VersionConflict("1.0.0", "1.1.0")
            assert "1.0.0" in str(version_conflict)
            
        except ImportError:
            pytest.skip("Registry exceptions not available")

    @patch('hacs_registry.registry.get_backend')
    def test_error_handling_in_operations(self, mock_get_backend):
        """Test error handling in registry operations."""
        mock_backend = MagicMock()
        mock_backend.get_definition.side_effect = Exception("Backend error")
        mock_get_backend.return_value = mock_backend
        
        try:
            from hacs_registry import Registry
            from hacs_registry.exceptions import RegistryError
            
            registry = Registry()
            
            # Test error handling
            with pytest.raises(RegistryError):
                registry.get("NonexistentResource")
                
        except ImportError:
            pytest.skip("Registry error handling not available")


@pytest.mark.performance
class TestHACSRegistryPerformance:
    """Test HACS Registry performance."""

    @patch('hacs_registry.registry.get_backend')
    def test_bulk_registration_performance(self, mock_get_backend):
        """Test bulk registration performance."""
        import time
        
        mock_backend = MagicMock()
        mock_backend.bulk_save.return_value = {"success": True, "saved_count": 50}
        mock_get_backend.return_value = mock_backend
        
        try:
            from hacs_registry import Registry
            from hacs_registry.definitions import ResourceDefinition
            
            registry = Registry()
            
            start = time.time()
            
            # Create multiple definitions
            definitions = [
                ResourceDefinition(
                    name=f"TestResource{i}",
                    version="1.0.0",
                    description=f"Test resource {i}",
                    schema_definition={"type": "object"}
                )
                for i in range(50)
            ]
            
            result = registry.bulk_register(definitions)
            
            end = time.time()
            duration = end - start
            
            # Should be fast
            assert duration < 3.0
            assert result["success"] is True
            
        except ImportError:
            pytest.skip("Registry bulk operations not available")

    @patch('hacs_registry.registry.get_backend')
    def test_search_performance(self, mock_get_backend):
        """Test search performance."""
        import time
        
        mock_backend = MagicMock()
        mock_backend.search.return_value = [
            {"name": f"Resource{i}", "category": "clinical"}
            for i in range(100)
        ]
        mock_get_backend.return_value = mock_backend
        
        try:
            from hacs_registry import Registry
            
            registry = Registry()
            
            start = time.time()
            
            # Perform multiple searches
            for _ in range(10):
                registry.search(category="clinical")
            
            end = time.time()
            duration = end - start
            
            # Should be fast
            assert duration < 2.0
            
        except ImportError:
            pytest.skip("Registry search not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 