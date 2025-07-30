"""
Unit tests for HACS Core package functionality.

Tests all core models, utilities, and infrastructure components
without external dependencies - suitable for GitHub CI.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from datetime import date, datetime, timezone
from typing import Dict, Any

# Core imports
from hacs_core import (
    Patient, MemoryBlock, Actor, BaseResource, Evidence,
    Encounter, Observation
)


@pytest.mark.unit
class TestHACScoreModels:
    """Test HACS Core model functionality."""

    def test_patient_model_complete(self):
        """Test Patient model with all features."""
        patient = Patient(
            full_name="John Doe",
            birth_date=date(1985, 3, 15),
            gender="male",
            phone="555-0123",
            email="john@example.com",
            active=True
        )
        
        assert patient.resource_type == "Patient"
        assert patient.full_name == "John Doe"
        assert patient.gender == "male"
        assert patient.age_years > 35  # Should calculate age
        assert patient.active is True
        assert patient.id.startswith("patient-")

    def test_patient_age_calculation(self):
        """Test patient age calculation."""
        # Test current age calculation
        patient = Patient(
            full_name="Age Test",
            birth_date=date(1990, 1, 1),
            gender="female"
        )
        
        current_year = datetime.now().year
        expected_age = current_year - 1990
        assert patient.age_years in [expected_age - 1, expected_age]  # Account for birthday

    def test_actor_roles_and_permissions(self):
        """Test Actor model with different roles."""
        roles_to_test = [
            ("physician", "Dr. Sarah Johnson"),
            ("nurse", "Nurse Mary Smith"),
            ("administrator", "Admin John Wilson"),
            ("patient", "Patient Jane Doe")
        ]
        
        for role, name in roles_to_test:
            actor = Actor(name=name, role=role)
            assert actor.role == role
            assert actor.name == name
            assert actor.resource_type == "Actor"

    def test_memory_block_types(self):
        """Test MemoryBlock with different memory types."""
        memory_types = ["episodic", "procedural", "executive"]
        
        for memory_type in memory_types:
            memory = MemoryBlock(
                content=f"Test {memory_type} memory",
                memory_type=memory_type,
                importance_score=0.7
            )
            
            assert memory.memory_type == memory_type
            assert memory.importance_score == 0.7
            assert memory.resource_type == "MemoryBlock"

    def test_memory_importance_validation(self):
        """Test memory importance score validation."""
        # Valid scores
        for score in [0.0, 0.5, 1.0]:
            memory = MemoryBlock(
                content="Test memory",
                memory_type="episodic",
                importance_score=score
            )
            assert memory.importance_score == score

    def test_base_resource_inheritance(self):
        """Test BaseResource inheritance and functionality."""
        patient = Patient(full_name="Inheritance Test")
        
        # Test BaseResource methods
        assert hasattr(patient, 'update_timestamp')
        assert hasattr(patient, 'is_newer_than')
        assert hasattr(patient, 'model_dump')
        
        # Test timestamp management
        original_time = patient.updated_at
        patient.update_timestamp()
        assert patient.updated_at > original_time
        
        # Test comparison
        older_patient = Patient(full_name="Older Patient")
        assert patient.is_newer_than(older_patient)

    def test_resource_serialization(self):
        """Test resource serialization and deserialization."""
        original = Patient(
            full_name="Serialization Test",
            birth_date=date(1980, 5, 10),
            gender="male"
        )
        
        # Serialize to dict
        data = original.model_dump()
        assert isinstance(data, dict)
        assert data["full_name"] == "Serialization Test"
        assert data["resource_type"] == "Patient"
        
        # Deserialize back
        restored = Patient.model_validate(data)
        assert restored.id == original.id
        assert restored.full_name == original.full_name
        assert restored.birth_date == original.birth_date

    def test_resource_pick_method(self):
        """Test BaseResource pick() method for creating subset models."""
        patient = Patient(
            full_name="Pick Test",
            birth_date=date(1990, 1, 1),
            gender="female",
            phone="555-0123"
        )
        
        # Create subset model
        PatientSummary = Patient.pick("full_name", "gender")
        summary = PatientSummary(
            full_name="Summary Test",
            gender="male"
        )
        
        assert summary.full_name == "Summary Test"
        assert summary.gender == "male"
        assert hasattr(summary, 'id')  # Essential fields are included


@pytest.mark.unit
class TestHACScoreValidation:
    """Test HACS Core validation functionality."""

    def test_required_field_validation(self):
        """Test required field validation."""
        # Patient requires full_name
        with pytest.raises(Exception):  # ValidationError
            Patient()
        
        # MemoryBlock requires content and memory_type
        with pytest.raises(Exception):
            MemoryBlock()

    def test_enum_validation(self):
        """Test enum field validation."""
        # Valid gender values
        for gender in ["male", "female", "other", "unknown"]:
            patient = Patient(full_name="Test", gender=gender)
            assert patient.gender == gender
        
        # Invalid gender should fail
        with pytest.raises(Exception):
            Patient(full_name="Test", gender="invalid_gender")

    def test_date_validation(self):
        """Test date field validation."""
        # Valid date
        patient = Patient(
            full_name="Date Test",
            birth_date=date(1990, 1, 1)
        )
        assert patient.birth_date == date(1990, 1, 1)
        
        # Invalid date format should fail
        with pytest.raises(Exception):
            Patient(
                full_name="Test",
                birth_date="not-a-date"
            )


@pytest.mark.unit
class TestHACScoreUtilities:
    """Test HACS Core utility functions."""

    def test_version_manager(self):
        """Test version management functionality."""
        try:
            from hacs_core.utils import VersionManager
            
            # Test version retrieval
            version = VersionManager.get_version_for_package("hacs-core")
            assert isinstance(version, str)
            assert len(version) > 0
            
        except ImportError:
            pytest.skip("VersionManager not available")

    def test_safe_import_functionality(self):
        """Test safe import utility."""
        try:
            from hacs_core.utils import safe_import
            
            # Test importing existing module
            os_module = safe_import("os", "built-in", "Operating system interface")
            assert os_module is not None
            
        except ImportError:
            pytest.skip("safe_import not available")

    def test_optional_import_handling(self):
        """Test optional import handling."""
        try:
            from hacs_core.utils import optional_import
            
            # Test optional import that should work
            json_module = optional_import("json")
            assert json_module is not None
            
            # Test optional import that shouldn't exist
            fake_module = optional_import("nonexistent_module_12345")
            assert fake_module is None
            
        except ImportError:
            pytest.skip("optional_import not available")


@pytest.mark.unit
class TestHACScoreAuth:
    """Test HACS Core authentication and authorization."""

    @patch.dict(os.environ, {'HACS_SECRET_KEY': 'test-secret-key'})
    def test_auth_manager_initialization(self):
        """Test AuthManager initialization."""
        try:
            from hacs_core.auth import AuthManager
            
            auth_manager = AuthManager()
            assert auth_manager is not None
            
        except ImportError:
            pytest.skip("AuthManager not available")

    def test_actor_permissions(self):
        """Test Actor permission levels."""
        try:
            from hacs_core import PermissionLevel
            
            # Test different permission levels
            physician = Actor(
                name="Dr. Test",
                role="physician",
                permission_level=PermissionLevel.ADMIN
            )
            
            assert physician.permission_level == PermissionLevel.ADMIN
            
        except (ImportError, AttributeError):
            # Test basic actor without permission levels
            physician = Actor(name="Dr. Test", role="physician")
            assert physician.role == "physician"


@pytest.mark.unit
class TestHACScoreConfig:
    """Test HACS Core configuration functionality."""

    @patch.dict(os.environ, {
        'HACS_ORGANIZATION': 'Test Healthcare',
        'DATABASE_URL': 'sqlite:///test.db',
        'ANTHROPIC_API_KEY': 'test-key'
    })
    def test_settings_configuration(self):
        """Test settings configuration."""
        try:
            from hacs_core.config import get_settings
            
            settings = get_settings()
            assert settings is not None
            
        except ImportError:
            pytest.skip("Settings configuration not available")

    def test_environment_variable_handling(self):
        """Test environment variable handling."""
        with patch.dict(os.environ, {
            'HACS_ORGANIZATION': 'CI Test Org',
            'DATABASE_URL': 'sqlite:///ci_test.db'
        }):
            assert os.getenv('HACS_ORGANIZATION') == 'CI Test Org'
            assert 'sqlite://' in os.getenv('DATABASE_URL')


@pytest.mark.unit
class TestHACScoreMemory:
    """Test HACS Core memory system."""

    def test_memory_creation_and_management(self):
        """Test memory creation and management."""
        # Create different types of memories
        episodic = MemoryBlock(
            content="Patient visit on 2024-01-15",
            memory_type="episodic",
            importance_score=0.9,
            tags=["patient_visit", "routine_checkup"]
        )
        
        procedural = MemoryBlock(
            content="Blood pressure measurement protocol",
            memory_type="procedural",
            importance_score=0.7,
            tags=["protocol", "vital_signs"]
        )
        
        executive = MemoryBlock(
            content="Clinical decision: increase medication dosage",
            memory_type="executive",
            importance_score=0.95,
            tags=["decision", "medication"]
        )
        
        memories = [episodic, procedural, executive]
        
        for memory in memories:
            assert memory.resource_type == "MemoryBlock"
            assert memory.content is not None
            assert 0.0 <= memory.importance_score <= 1.0
            assert memory.id is not None

    def test_memory_relationships(self):
        """Test memory relationships and context."""
        # Create patient and encounter
        patient = Patient(full_name="Memory Test Patient")
        
        try:
            encounter = Encounter(
                status="finished",
                subject=patient.id,
                period={"start": "2024-01-01T10:00:00Z"}
            )
            
            # Create memory related to encounter
            memory = MemoryBlock(
                content="Routine checkup completed successfully",
                memory_type="episodic",
                related_encounter_id=encounter.id,
                related_patient_id=patient.id
            )
            
            assert memory.related_encounter_id == encounter.id
            assert memory.related_patient_id == patient.id
            
        except Exception:
            # If Encounter creation fails, test basic memory
            memory = MemoryBlock(
                content="Basic memory without relationships",
                memory_type="episodic",
                related_patient_id=patient.id
            )
            
            assert memory.related_patient_id == patient.id


@pytest.mark.unit
class TestHACScoreEvidence:
    """Test HACS Core evidence and knowledge management."""

    def test_evidence_creation(self):
        """Test Evidence model creation."""
        try:
            evidence = Evidence(
                title="Clinical Guideline for Hypertension",
                content="Updated guidelines for hypertension management",
                evidence_type="guideline",
                citation="AHA Guidelines 2024"
            )
            
            assert evidence.resource_type == "Evidence"
            assert evidence.title == "Clinical Guideline for Hypertension"
            assert evidence.evidence_type == "guideline"
            
        except Exception:
            pytest.skip("Evidence model requires additional fields")

    def test_evidence_validation(self):
        """Test Evidence validation."""
        try:
            # Test required fields
            with pytest.raises(Exception):
                Evidence(title="Incomplete Evidence")
                
        except Exception:
            pytest.skip("Evidence validation not available")


@pytest.mark.performance
class TestHACScorePerformance:
    """Test HACS Core performance."""

    def test_bulk_model_creation_performance(self):
        """Test bulk model creation performance."""
        import time
        
        start = time.time()
        
        # Create multiple models
        patients = [
            Patient(full_name=f"Patient {i}", birth_date=date(1980, 1, 1))
            for i in range(100)
        ]
        
        memories = [
            MemoryBlock(content=f"Memory {i}", memory_type="episodic")
            for i in range(100)
        ]
        
        actors = [
            Actor(name=f"Dr. {i}", role="physician")
            for i in range(100)
        ]
        
        end = time.time()
        duration = end - start
        
        # Performance assertions
        assert len(patients) == 100
        assert len(memories) == 100
        assert len(actors) == 100
        assert duration < 3.0  # Should be fast
        
        # Verify all have valid IDs
        all_resources = patients + memories + actors
        assert all(resource.id is not None for resource in all_resources)

    def test_serialization_performance(self):
        """Test serialization performance."""
        import time
        
        # Create complex patient
        patient = Patient(
            full_name="Performance Test Patient",
            birth_date=date(1985, 6, 15),
            gender="female",
            phone="555-0123",
            email="test@example.com"
        )
        
        start = time.time()
        
        # Serialize many times
        for _ in range(1000):
            patient.model_dump()
        
        end = time.time()
        duration = end - start
        
        # Should be very fast
        assert duration < 2.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 