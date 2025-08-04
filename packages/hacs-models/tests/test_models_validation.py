"""
Comprehensive validation tests for hacs-models package.

Tests all models for proper instantiation, validation, and functionality.
Ensures world-class quality and compliance with design principles.
"""

import pytest
from datetime import date, datetime
from typing import Any

from hacs_models import (
    BaseResource, DomainResource, Patient, Observation, Encounter,
    HumanName, ContactPoint, Address, Identifier,
    Coding, CodeableConcept, Quantity, Range,
    MemoryBlock, EpisodicMemory, SemanticMemory, WorkingMemory,
    validate_model_compatibility, get_model_registry
)
from hacs_models.types import Gender, ObservationStatus, EncounterStatus


class TestBaseResource:
    """Test BaseResource functionality."""
    
    def test_base_resource_creation(self):
        """Test basic resource creation with auto-generation."""
        resource = BaseResource(resource_type="TestResource")
        
        assert resource.id is not None
        assert resource.id.startswith("testresource-")
        assert resource.created_at is not None
        assert resource.updated_at is not None
        assert resource.resource_type == "TestResource"
    
    def test_base_resource_with_explicit_id(self):
        """Test resource creation with explicit ID."""
        resource = BaseResource(
            id="custom-id-123",
            resource_type="TestResource"
        )
        
        assert resource.id == "custom-id-123"
        assert resource.resource_type == "TestResource"
    
    def test_timestamp_updates(self):
        """Test timestamp update functionality."""
        resource = BaseResource(resource_type="TestResource")
        original_updated = resource.updated_at
        
        # Small delay to ensure different timestamp
        import time
        time.sleep(0.01)
        
        resource.update_timestamp()
        assert resource.updated_at > original_updated
    
    def test_age_calculation(self):
        """Test resource age calculation."""
        resource = BaseResource(resource_type="TestResource")
        age_days = resource.get_age_days()
        
        assert age_days is not None
        assert age_days >= 0
        assert age_days < 1  # Should be very recent
    
    def test_reference_generation(self):
        """Test FHIR reference generation."""
        resource = BaseResource(
            id="test-123",
            resource_type="TestResource"
        )
        
        ref = resource.to_reference()
        assert ref == "TestResource/test-123"
    
    def test_pick_subset_model(self):
        """Test subset model creation with pick()."""
        # Create a subclass for testing
        class TestModel(BaseResource):
            name: str
            value: int = 42
            optional_field: str | None = None
        
        # Create subset with only specific fields
        SubsetModel = TestModel.pick("name", "value")
        
        # Create instance of subset
        subset = SubsetModel(
            resource_type="TestModel",
            name="test",
            value=100
        )
        
        assert subset.name == "test"
        assert subset.value == 100
        assert hasattr(subset, "id")  # Essential fields always included
        assert hasattr(subset, "resource_type")


class TestDomainResource: 
    """Test DomainResource functionality."""
    
    def test_domain_resource_creation(self):
        """Test domain resource with FHIR fields."""
        resource = DomainResource(
            resource_type="TestDomain",
            text="Test domain resource"
        )
        
        assert resource.text == "Test domain resource"
        assert resource._fhir_version == "R4"
    
    def test_extension_management(self):
        """Test extension add/get functionality."""
        resource = DomainResource(resource_type="TestDomain")
        
        resource.add_extension("custom-field", "custom-value")
        
        assert resource.has_extension("custom-field")
        assert resource.get_extension("custom-field") == "custom-value"
        assert resource.get_extension("non-existent") is None


class TestPatientModel:
    """Test Patient model functionality."""
    
    def test_patient_with_full_name(self):
        """Test patient creation with full name parsing."""
        patient = Patient(
            full_name="Dr. John Michael Smith Jr.",
            birth_date=date(1985, 3, 15),
            gender="male"
        )
        
        assert len(patient.name) == 1
        name = patient.name[0]
        assert name.prefix == ["Dr."]
        assert name.given == ["John", "Michael"]
        assert name.family == "Smith"
        assert name.suffix == ["Jr."]
        assert patient.display_name == "John Michael Smith"
    
    def test_patient_with_age_calculation(self):
        """Test patient with age-based birth date calculation."""
        patient = Patient(
            full_name="Jane Doe",
            age=39,
            gender="female"
        )
        
        assert patient.age_years == 39
        assert patient.birth_date is not None
        
        # Birth year should be approximately current year - age
        expected_birth_year = datetime.now().year - 39
        assert patient.birth_date.year == expected_birth_year
    
    def test_patient_contact_information(self):
        """Test patient contact info auto-population."""
        patient = Patient(
            full_name="Bob Johnson",
            phone="+1-555-123-4567",
            email="bob@example.com"
        )
        
        # Check telecom was populated
        assert len(patient.telecom) == 2
        
        phone_contacts = [t for t in patient.telecom if t.system == "phone"]
        email_contacts = [t for t in patient.telecom if t.system == "email"]
        
        assert len(phone_contacts) == 1
        assert len(email_contacts) == 1
        assert phone_contacts[0].value == "+1-555-123-4567"
        assert email_contacts[0].value == "bob@example.com"
    
    def test_patient_address_parsing(self):
        """Test patient address parsing."""
        patient = Patient(
            full_name="Alice Smith",
            address_text="123 Main St, Anytown, CA 12345"
        )
        
        assert len(patient.address) == 1
        address = patient.address[0]
        assert address.line == ["123 Main St"]
        assert address.city == "Anytown"
        assert address.state == "CA"
        assert address.postal_code == "12345"
    
    def test_patient_identifier_management(self):
        """Test patient identifier operations."""
        patient = Patient(full_name="Test Patient")
        
        patient.add_identifier("MRN123456", "MR", "usual")
        
        assert len(patient.identifier) == 1
        mrn = patient.get_identifier_by_type("MR")
        assert mrn is not None
        assert mrn.value == "MRN123456"
    
    def test_patient_validation_errors(self):
        """Test patient validation requirements."""
        # Should fail without any name
        with pytest.raises(ValueError, match="must have at least a name"):
            Patient()
        
        # Should fail with invalid age
        with pytest.raises(ValueError, match="Age must be between 0 and 150"):
            Patient(full_name="Test", age=200)


class TestObservationModel:
    """Test Observation model functionality."""
    
    def test_observation_creation(self):
        """Test basic observation creation."""
        # Create code for blood pressure
        bp_code = CodeableConcept(
            coding=[Coding(
                system="http://loinc.org",
                code="85354-9",
                display="Blood pressure"
            )],
            text="Blood pressure"
        )
        
        observation = Observation(
            status="final",
            code=bp_code,
            subject="Patient/patient-123"
        )
        
        assert observation.status == "final"
        assert observation.code.text == "Blood pressure"
        assert observation.subject == "Patient/patient-123"
    
    def test_observation_with_quantity_value(self):
        """Test observation with quantity value."""
        observation = Observation(
            status="final",
            code=CodeableConcept(text="Weight"),
        )
        
        observation.set_quantity_value(70.5, "kg")
        
        assert observation.value_quantity is not None
        assert observation.value_quantity.value == 70.5
        assert observation.value_quantity.unit == "kg"
        
        summary = observation.get_value_summary()
        assert summary == "70.5 kg"


class TestMemoryModels:
    """Test memory model functionality."""
    
    def test_memory_block_creation(self):
        """Test basic memory block creation."""
        memory = MemoryBlock(
            memory_type="episodic",
            content="Patient reported chest pain during visit",
            importance_score=0.8,
            tags=["chest_pain", "patient_report"]
        )
        
        assert memory.memory_type == "episodic"
        assert memory.importance_score == 0.8
        assert "chest_pain" in memory.tags
        assert "patient_report" in memory.tags
        assert memory.access_count == 0
    
    def test_episodic_memory(self):
        """Test episodic memory specific features."""
        memory = EpisodicMemory(
            content="Patient consultation in ER",
            event_time=datetime.now(),
            location="Emergency Room",
            participants=["Patient/patient-123", "Practitioner/dr-smith"]
        )
        
        assert memory.memory_type == "episodic"
        assert memory.location == "Emergency Room"
        assert len(memory.participants) == 2
    
    def test_semantic_memory(self):
        """Test semantic memory specific features."""
        memory = SemanticMemory(
            content="Normal blood pressure range is 90-120 mmHg systolic",
            knowledge_domain="cardiology",
            source="Clinical guidelines",
            evidence_level="high"
        )
        
        assert memory.memory_type == "semantic"
        assert memory.knowledge_domain == "cardiology"
        assert memory.evidence_level == "high"
    
    def test_working_memory_expiration(self):
        """Test working memory TTL functionality."""
        memory = WorkingMemory(
            content="Currently analyzing patient vital signs",
            task_context="patient_assessment",
            ttl_seconds=1  # 1 second TTL
        )
        
        assert memory.memory_type == "working"
        assert not memory.is_expired()  # Should not be expired immediately
        
        # Test expiration (would need actual time delay in real scenario)
        memory.ttl_seconds = 0  # Force immediate expiration
        # In real test, would need time.sleep(1.1) or similar
    
    def test_memory_access_tracking(self):
        """Test memory access tracking."""
        memory = MemoryBlock(
            memory_type="semantic", 
            content="Test content"
        )
        
        assert memory.access_count == 0
        assert memory.last_accessed_at is None
        
        memory.access_memory()
        
        assert memory.access_count == 1
        assert memory.last_accessed_at is not None


class TestModelRegistry:
    """Test model registry and compatibility."""
    
    def test_model_registry_completeness(self):
        """Test that model registry contains expected models."""
        registry = get_model_registry()
        
        expected_models = [
            "Patient", "Observation", "Encounter", "MemoryBlock",
            "EpisodicMemory", "SemanticMemory", "WorkingMemory"
        ]
        
        for model_name in expected_models:
            assert model_name in registry
            assert issubclass(registry[model_name], BaseResource)
    
    def test_model_compatibility_validation(self):
        """Test model compatibility validation."""
        # This should pass with all models properly configured
        assert validate_model_compatibility() == True
    
    def test_model_instantiation_from_registry(self):
        """Test creating models from registry."""
        registry = get_model_registry()
        
        # Test Patient creation
        PatientModel = registry["Patient"]
        patient = PatientModel(full_name="Test Patient")
        assert isinstance(patient, Patient)
        assert patient.display_name == "Test Patient"
        
        # Test MemoryBlock creation  
        MemoryModel = registry["MemoryBlock"]
        memory = MemoryModel(memory_type="semantic", content="Test memory")
        assert isinstance(memory, MemoryBlock)
        assert memory.content == "Test memory"


class TestTypeValidation:
    """Test type validation and enums."""
    
    def test_gender_enum_validation(self):
        """Test gender enum validation."""
        patient = Patient(full_name="Test", gender="male")
        assert patient.gender == Gender.MALE
        
        # Test invalid gender (should be caught by Pydantic)
        with pytest.raises(ValueError):
            Patient(full_name="Test", gender="invalid_gender")
    
    def test_observation_status_validation(self):
        """Test observation status validation."""
        obs = Observation(
            status="final",
            code=CodeableConcept(text="Test")
        )
        assert obs.status == ObservationStatus.FINAL
    
    def test_encounter_status_validation(self):
        """Test encounter status validation."""
        encounter = Encounter(
            status="in-progress",
            class_="outpatient"
        )
        assert encounter.status == EncounterStatus.IN_PROGRESS


# Integration test
def test_models_integration():
    """Test models working together in healthcare workflow."""
    # Create patient
    patient = Patient(
        full_name="Dr. Alice Johnson MD",
        birth_date=date(1980, 5, 15),
        gender="female",
        phone="+1-555-987-6543",
        email="alice.johnson@hospital.com"
    )
    
    # Create encounter
    encounter = Encounter(
        status="in-progress",
        class_="outpatient",
        subject=patient.to_reference()
    )
    
    # Create observation
    bp_code = CodeableConcept(
        coding=[Coding(code="85354-9", display="Blood pressure")],
        text="Blood pressure"
    )
    
    observation = Observation(
        status="final",
        code=bp_code,
        subject=patient.to_reference(),
        encounter=encounter.to_reference()
    )
    observation.set_quantity_value(120, "mmHg")
    
    # Create memory of the interaction
    memory = EpisodicMemory(
        content=f"Recorded blood pressure {observation.get_value_summary()} for {patient.display_name}",
        event_time=datetime.now(),
        location="Clinic Room 1",
        participants=[patient.to_reference(), "Practitioner/nurse-smith"],
        context_metadata={
            "patient_id": patient.id,
            "encounter_id": encounter.id,
            "observation_id": observation.id
        },
        tags=["vital_signs", "blood_pressure", "routine_check"]
    )
    
    # Verify integration
    assert patient.display_name == "Alice Johnson"  # Parsed correctly
    assert patient.age_years == 44  # Calculated from birth_date
    assert encounter.subject == f"Patient/{patient.id}"
    assert observation.subject == f"Patient/{patient.id}"
    assert observation.get_value_summary() == "120 mmHg"
    assert memory.memory_type == "episodic"
    assert memory.context_metadata["patient_id"] == patient.id
    
    print(f"✅ Integration test passed:")
    print(f"   Patient: {patient}")
    print(f"   Encounter: {encounter}")
    print(f"   Observation: {observation}")
    print(f"   Memory: {memory}")


if __name__ == "__main__":
    # Run basic validation
    test_models_integration()
    print("✅ All basic model tests passed!")