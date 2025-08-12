"""
Test suite for ResourceBundle and related components.
"""

import pytest
from datetime import datetime, timezone

from hacs_core.models import (
    ResourceBundle,
    BundleType,
    BundleStatus,
    WorkflowBindingType,
    LinkRelation,
    BundleEntry,
    WorkflowBinding,
    UseCase,
    BundleUpdate,
    Patient,
    Observation,
    create_resource_stack,
    create_search_results_bundle,
    create_workflow_template_bundle,
)


class TestResourceBundle:
    """Test ResourceBundle core functionality."""

    def test_basic_bundle_creation(self):
        """Test basic ResourceBundle creation and attributes."""
        bundle = ResourceBundle(
            title="Test Bundle",
            bundle_type=BundleType.COLLECTION,
            version="1.0.0",
            description="A test bundle for validation"
        )
        
        assert bundle.title == "Test Bundle"
        assert bundle.bundle_type == BundleType.COLLECTION
        assert bundle.version == "1.0.0"
        assert bundle.resource_type == "ResourceBundle"
        assert bundle.status == BundleStatus.DRAFT
        assert len(bundle.entries) == 0

    def test_add_resource(self):
        """Test adding resources to bundle."""
        bundle = ResourceBundle(
            bundle_type=BundleType.COLLECTION,
            version="1.0.0"
        )
        
        patient = Patient(
            id="patient-001",
            full_name="John Doe",
            birth_date="1990-01-01"
        )
        
        bundle.add_resource(
            resource=patient,
            title="Primary Patient",
            tags=["primary", "test"],
            priority=1
        )
        
        assert len(bundle.entries) == 1
        assert bundle.entries[0].resource.id == "patient-001"
        assert bundle.entries[0].title == "Primary Patient"
        assert "primary" in bundle.entries[0].tags
        assert bundle.entries[0].priority == 1

    def test_add_workflow_binding(self):
        """Test adding workflow bindings."""
        bundle = ResourceBundle(
            bundle_type=BundleType.STACK,
            version="1.0.0"
        )
        
        bundle.add_workflow_binding(
            workflow_id="test-workflow",
            workflow_name="Test Workflow",
            binding_type=WorkflowBindingType.INPUT_FILTER,
            parameters={"param1": "value1"},
            priority=1,
            description="Test binding"
        )
        
        assert len(bundle.workflow_bindings) == 1
        binding = bundle.workflow_bindings[0]
        assert binding.workflow_id == "test-workflow"
        assert binding.binding_type == WorkflowBindingType.INPUT_FILTER
        assert binding.parameters["param1"] == "value1"
        assert binding.active is True

    def test_add_use_case(self):
        """Test adding use cases."""
        bundle = ResourceBundle(
            bundle_type=BundleType.STACK,
            version="1.0.0"
        )
        
        bundle.add_use_case(
            name="Test Use Case",
            description="A test use case",
            examples=["Example 1", "Example 2"],
            prerequisites=["Prerequisite 1"],
            outcomes=["Outcome 1"],
            tags=["test", "example"]
        )
        
        assert len(bundle.use_cases) == 1
        use_case = bundle.use_cases[0]
        assert use_case.name == "Test Use Case"
        assert len(use_case.examples) == 2
        assert "test" in use_case.tags

    def test_add_update_record(self):
        """Test adding update records."""
        bundle = ResourceBundle(
            bundle_type=BundleType.STACK,
            version="1.0.0"
        )
        
        bundle.add_update_record(
            version="1.1.0",
            summary="Added new features",
            author="Test Author",
            details="Detailed changes",
            breaking_changes=False
        )
        
        assert len(bundle.updates) == 1
        update = bundle.updates[0]
        assert update.version == "1.1.0"
        assert update.author == "Test Author"
        assert update.breaking_changes is False

    def test_get_resources_by_type(self):
        """Test filtering resources by type."""
        bundle = ResourceBundle(
            bundle_type=BundleType.COLLECTION,
            version="1.0.0"
        )
        
        patient = Patient(id="patient-001", full_name="John Doe", birth_date="1990-01-01")
        observation = Observation(id="obs-001", status="final", category="vital-signs", code="BP", subject="patient-001")
        
        bundle.add_resource(patient)
        bundle.add_resource(observation)
        
        patients = bundle.get_resources_by_type("Patient")
        observations = bundle.get_resources_by_type("Observation")
        
        assert len(patients) == 1
        assert len(observations) == 1
        assert patients[0].id == "patient-001"
        assert observations[0].id == "obs-001"

    def test_get_resources_by_tag(self):
        """Test filtering resources by tag."""
        bundle = ResourceBundle(
            bundle_type=BundleType.COLLECTION,
            version="1.0.0"
        )
        
        patient = Patient(id="patient-001", full_name="John Doe", birth_date="1990-01-01")
        bundle.add_resource(patient, tags=["primary", "important"])
        
        observation = Observation(id="obs-001", status="final", category="vital-signs", code="BP", subject="patient-001")
        bundle.add_resource(observation, tags=["secondary"])
        
        primary_resources = bundle.get_resources_by_tag("primary")
        important_resources = bundle.get_resources_by_tag("important")
        secondary_resources = bundle.get_resources_by_tag("secondary")
        
        assert len(primary_resources) == 1
        assert len(important_resources) == 1
        assert len(secondary_resources) == 1
        assert primary_resources[0].id == "patient-001"

    def test_get_workflow_bindings_by_type(self):
        """Test filtering workflow bindings by type."""
        bundle = ResourceBundle(
            bundle_type=BundleType.STACK,
            version="1.0.0"
        )
        
        bundle.add_workflow_binding("workflow1", WorkflowBindingType.INPUT_FILTER)
        bundle.add_workflow_binding("workflow2", WorkflowBindingType.OUTPUT_TEMPLATE)
        bundle.add_workflow_binding("workflow3", WorkflowBindingType.INPUT_FILTER)
        
        input_filters = bundle.get_workflow_bindings_by_type(WorkflowBindingType.INPUT_FILTER)
        output_templates = bundle.get_workflow_bindings_by_type(WorkflowBindingType.OUTPUT_TEMPLATE)
        
        assert len(input_filters) == 2
        assert len(output_templates) == 1

    def test_validate_bundle_integrity(self):
        """Test bundle integrity validation."""
        bundle = ResourceBundle(
            bundle_type=BundleType.STACK,
            version="1.0.0",
            status=BundleStatus.ACTIVE
        )
        
        # Add resources
        patient1 = Patient(id="patient-001", full_name="John Doe", birth_date="1990-01-01")
        patient2 = Patient(id="patient-002", full_name="Jane Doe", birth_date="1990-01-01")
        bundle.add_resource(patient1)
        bundle.add_resource(patient2)
        
        # Add workflow binding
        bundle.add_workflow_binding("test-workflow", WorkflowBindingType.INPUT_FILTER)
        
        # Add use case
        bundle.add_use_case("Test Case", "Test description")
        
        validation = bundle.validate_bundle_integrity()
        
        assert validation["valid"] is True
        assert validation["entry_count"] == 2
        assert validation["workflow_binding_count"] == 1
        assert validation["use_case_count"] == 1
        assert len(validation["issues"]) == 0

    def test_bundle_with_duplicate_ids_validation(self):
        """Test validation catches duplicate resource IDs."""
        bundle = ResourceBundle(
            bundle_type=BundleType.COLLECTION,
            version="1.0.0"
        )
        
        # Add resources with same ID
        patient1 = Patient(id="duplicate-id", full_name="John Doe", birth_date="1990-01-01")
        patient2 = Patient(id="duplicate-id", full_name="Jane Doe", birth_date="1990-01-01")
        bundle.add_resource(patient1)
        bundle.add_resource(patient2)
        
        validation = bundle.validate_bundle_integrity()
        
        assert validation["valid"] is False
        assert "Duplicate resource IDs found in bundle" in validation["issues"]


class TestBundleValidation:
    """Test ResourceBundle validation rules."""

    def test_total_only_for_searchset(self):
        """Test that total field is only valid for searchset bundles."""
        # Should work for searchset
        bundle = ResourceBundle(
            bundle_type=BundleType.SEARCHSET,
            version="1.0.0",
            total=10
        )
        assert bundle.total == 10
        
        # Should fail for other types
        with pytest.raises(ValueError, match="total field is only valid for searchset bundles"):
            ResourceBundle(
                bundle_type=BundleType.COLLECTION,
                version="1.0.0", 
                total=10
            )

    def test_document_must_have_entries(self):
        """Test that document bundles must have entries."""
        with pytest.raises(ValueError, match="document bundles must contain at least one entry"):
            ResourceBundle(
                bundle_type=BundleType.DOCUMENT,
                version="1.0.0"
            )

    def test_stack_must_have_entries(self):
        """Test that stack bundles must have entries."""
        with pytest.raises(ValueError, match="stack bundles must contain at least one entry"):
            ResourceBundle(
                bundle_type=BundleType.STACK,
                version="1.0.0"
            )

    def test_unique_workflow_ids(self):
        """Test that workflow bindings must have unique workflow IDs."""
        bundle = ResourceBundle(
            bundle_type=BundleType.STACK,
            version="1.0.0"
        )
        
        patient = Patient(id="patient-001", full_name="Test", birth_date="1990-01-01")
        bundle.add_resource(patient)
        
        # First binding should work
        bundle.add_workflow_binding("workflow1", WorkflowBindingType.INPUT_FILTER)
        
        # Duplicate workflow ID should fail during validation
        bundle.workflow_bindings.append(
            WorkflowBinding(
                workflow_id="workflow1",  # Duplicate
                binding_type=WorkflowBindingType.OUTPUT_TEMPLATE
            )
        )
        
        with pytest.raises(ValueError, match="Workflow bindings must have unique workflow_ids"):
            bundle.model_validate(bundle.model_dump())


class TestFactoryFunctions:
    """Test factory functions for creating bundles."""

    def test_create_resource_stack(self):
        """Test create_resource_stack factory function."""
        patient = Patient(id="patient-001", full_name="John Doe", birth_date="1990-01-01")
        observation = Observation(id="obs-001", status="final", category="vital-signs", code="BP", subject="patient-001")
        
        bundle = create_resource_stack(
            stack_name="Test Stack",
            version="1.0.0",
            description="Test description",
            resources=[patient, observation],
            publisher="Test Publisher"
        )
        
        assert bundle.title == "Test Stack"
        assert bundle.bundle_type == BundleType.STACK
        assert bundle.version == "1.0.0"
        assert bundle.publisher == "Test Publisher"
        assert len(bundle.entries) == 2
        assert bundle.status == BundleStatus.ACTIVE

    def test_create_search_results_bundle(self):
        """Test create_search_results_bundle factory function."""
        patients = [
            Patient(id=f"patient-{i}", full_name=f"Patient {i}", birth_date="1990-01-01")
            for i in range(3)
        ]
        
        bundle = create_search_results_bundle(
            resources=patients,
            total=10,
            search_url="https://example.com/search"
        )
        
        assert bundle.bundle_type == BundleType.SEARCHSET
        assert bundle.total == 10
        assert len(bundle.entries) == 3
        assert len(bundle.links) == 1
        assert bundle.links[0].relation == LinkRelation.SELF

    def test_create_workflow_template_bundle(self):
        """Test create_workflow_template_bundle factory function."""
        template_patient = Patient(id="template", full_name="{{name}}", birth_date="{{birth_date}}")
        
        bundle = create_workflow_template_bundle(
            template_name="Test Template",
            version="1.0.0",
            workflow_id="test-workflow",
            template_resources=[template_patient],
            description="Test template"
        )
        
        assert bundle.title == "Test Template"
        assert bundle.bundle_type == BundleType.TEMPLATE
        assert len(bundle.entries) == 1
        assert len(bundle.workflow_bindings) == 1
        assert bundle.workflow_bindings[0].workflow_id == "test-workflow"
        assert bundle.workflow_bindings[0].binding_type == WorkflowBindingType.OUTPUT_TEMPLATE


class TestBundleTypes:
    """Test different bundle type behaviors."""

    def test_collection_bundle(self):
        """Test collection bundle behavior."""
        bundle = ResourceBundle(
            bundle_type=BundleType.COLLECTION,
            version="1.0.0"
        )
        
        # Collection bundles can be empty
        assert len(bundle.entries) == 0
        
        # Can add any resources
        patient = Patient(id="patient-001", full_name="John Doe", birth_date="1990-01-01")
        bundle.add_resource(patient)
        assert len(bundle.entries) == 1

    def test_searchset_bundle(self):
        """Test searchset bundle behavior."""
        bundle = ResourceBundle(
            bundle_type=BundleType.SEARCHSET,
            version="1.0.0",
            total=5
        )
        
        # Can have total
        assert bundle.total == 5
        
        # Can add search metadata to entries
        patient = Patient(id="patient-001", full_name="John Doe", birth_date="1990-01-01")
        bundle.add_resource(
            patient,
            metadata={"search": {"mode": "match", "score": 0.95}}
        )
        
        assert bundle.entries[0].metadata["search"]["score"] == 0.95

    def test_template_bundle(self):
        """Test template bundle behavior."""
        bundle = ResourceBundle(
            bundle_type=BundleType.TEMPLATE,
            version="1.0.0"
        )
        
        # Template bundles are typically used with workflow bindings
        bundle.add_workflow_binding(
            "template-workflow",
            WorkflowBindingType.OUTPUT_TEMPLATE
        )
        
        assert len(bundle.workflow_bindings) == 1


class TestBundleMetadata:
    """Test bundle metadata and registry features."""

    def test_keywords_and_categories(self):
        """Test keywords and categories functionality."""
        bundle = ResourceBundle(
            bundle_type=BundleType.STACK,
            version="1.0.0"
        )
        
        patient = Patient(id="patient-001", full_name="Test", birth_date="1990-01-01")
        bundle.add_resource(patient)
        
        bundle.keywords = ["healthcare", "clinical", "assessment"]
        bundle.categories = ["clinical-workflow", "patient-care"]
        
        assert "healthcare" in bundle.keywords
        assert "clinical-workflow" in bundle.categories

    def test_versioning_and_updates(self):
        """Test versioning and update tracking."""
        bundle = ResourceBundle(
            bundle_type=BundleType.STACK,
            version="2.0.0"
        )
        
        patient = Patient(id="patient-001", full_name="Test", birth_date="1990-01-01")
        bundle.add_resource(patient)
        
        bundle.add_update_record(
            version="2.0.0",
            summary="Major update",
            breaking_changes=True,
            migration_notes="See migration guide"
        )
        
        bundle.add_update_record(
            version="1.0.0",
            summary="Initial release",
            breaking_changes=False
        )
        
        assert len(bundle.updates) == 2
        assert bundle.updates[0].version == "2.0.0"
        assert bundle.updates[0].breaking_changes is True

    def test_quality_and_maturity(self):
        """Test quality and maturity tracking."""
        bundle = ResourceBundle(
            bundle_type=BundleType.STACK,
            version="1.0.0"
        )
        
        patient = Patient(id="patient-001", full_name="Test", birth_date="1990-01-01")
        bundle.add_resource(patient)
        
        bundle.quality_score = 0.95
        bundle.maturity_level = "stable"
        bundle.experimental = False
        
        assert bundle.quality_score == 0.95
        assert bundle.maturity_level == "stable"
        assert bundle.experimental is False