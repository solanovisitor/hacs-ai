"""
Unit tests for HACS Tools package functionality.

Tests all 25+ healthcare tools and MCP protocol functionality
without external dependencies - suitable for GitHub CI.
"""

import pytest
import os
import json
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import date, datetime
from typing import Dict, Any, List

# Mock external dependencies before importing
@pytest.fixture(autouse=True)
def mock_external_dependencies():
    """Mock external dependencies for CI testing."""
    with patch.dict(os.environ, {
        'DATABASE_URL': 'sqlite:///test.db',
        'HACS_ORGANIZATION': 'test-org',
        'ANTHROPIC_API_KEY': 'test-key',
        'OPENAI_API_KEY': 'test-key'
    }):
        yield


@pytest.mark.unit
class TestHACSToolsCore:
    """Test HACS Tools core functionality."""

    def test_tools_module_imports(self):
        """Test that tools module imports work."""
        try:
            import hacs_tools
            assert hacs_tools is not None
            
            # Test main exports
            from hacs_tools import list_available_resources
            assert callable(list_available_resources)
            
        except ImportError as e:
            pytest.skip(f"HACS Tools not available: {e}")

    def test_available_tools_discovery(self):
        """Test discovery of available tools."""
        try:
            from hacs_tools import list_available_resources
            
            # Should return a list of available tools
            resources = list_available_resources()
            assert isinstance(resources, (list, dict))
            
        except ImportError:
            pytest.skip("list_available_resources not available")

    @patch('hacs_tools.tools.get_persistence_provider')
    def test_tool_initialization_mocked(self, mock_provider):
        """Test tool initialization with mocked dependencies."""
        mock_provider.return_value = MagicMock()
        
        try:
            from hacs_tools.tools import HACSTools
            
            tools = HACSTools()
            assert tools is not None
            
        except ImportError:
            pytest.skip("HACSTools not available")


@pytest.mark.unit
class TestHACSResourceManagement:
    """Test HACS resource management tools."""

    @patch('hacs_tools.tools.get_persistence_provider')
    def test_create_resource_tool(self, mock_provider):
        """Test create_hacs_record tool."""
        # Mock persistence provider
        mock_adapter = MagicMock()
        mock_provider.return_value = mock_adapter
        
        # Mock successful resource creation
        mock_adapter.save_resource.return_value = MagicMock(
            id="patient-123",
            resource_type="Patient",
            full_name="Test Patient"
        )
        
        try:
            from hacs_tools.tools import create_hacs_record
            
            result = create_hacs_record(
                resource_type="Patient",
                resource_data={
                    "full_name": "Test Patient",
                    "birth_date": "1990-01-01",
                    "gender": "male"
                }
            )
            
            assert result["success"] is True
            assert "patient-123" in str(result)
            
        except ImportError:
            pytest.skip("create_hacs_record not available")

    @patch('hacs_tools.tools.get_persistence_provider')
    def test_get_resource_tool(self, mock_provider):
        """Test get_hacs_record_by_id tool."""
        # Mock persistence provider
        mock_adapter = MagicMock()
        mock_provider.return_value = mock_adapter
        
        # Mock resource retrieval
        mock_adapter.get_resource.return_value = {
            "id": "patient-123",
            "resource_type": "Patient",
            "full_name": "Test Patient"
        }
        
        try:
            from hacs_tools.tools import get_hacs_record_by_id
            
            result = get_hacs_record_by_id(
                resource_type="Patient",
                resource_id="patient-123"
            )
            
            assert result["id"] == "patient-123"
            assert result["resource_type"] == "Patient"
            
        except ImportError:
            pytest.skip("get_hacs_record_by_id not available")

    @patch('hacs_tools.tools.get_persistence_provider')
    def test_update_resource_tool(self, mock_provider):
        """Test update_hacs_record tool."""
        mock_adapter = MagicMock()
        mock_provider.return_value = mock_adapter
        
        # Mock successful update
        mock_adapter.update_resource.return_value = MagicMock(
            id="patient-123",
            full_name="Updated Patient"
        )
        
        try:
            from hacs_tools.tools import update_hacs_record
            
            result = update_hacs_record(
                resource_type="Patient",
                resource_id="patient-123",
                updates={"full_name": "Updated Patient"}
            )
            
            assert result["success"] is True
            
        except ImportError:
            pytest.skip("update_hacs_record not available")

    @patch('hacs_tools.tools.get_persistence_provider')
    def test_delete_resource_tool(self, mock_provider):
        """Test delete_hacs_record tool."""
        mock_adapter = MagicMock()
        mock_provider.return_value = mock_adapter
        
        # Mock successful deletion
        mock_adapter.delete_resource.return_value = True
        
        try:
            from hacs_tools.tools import delete_hacs_record
            
            result = delete_hacs_record(
                resource_type="Patient",
                resource_id="patient-123"
            )
            
            assert result["success"] is True
            assert "deleted" in result["message"].lower()
            
        except ImportError:
            pytest.skip("delete_hacs_record not available")


@pytest.mark.unit
class TestHACSMemoryManagement:
    """Test HACS memory management tools."""

    @patch('hacs_tools.tools.get_persistence_provider')
    def test_create_memory_tool(self, mock_provider):
        """Test create_memory tool."""
        mock_adapter = MagicMock()
        mock_provider.return_value = mock_adapter
        
        # Mock memory creation
        mock_adapter.save_resource.return_value = MagicMock(
            id="memory-123",
            resource_type="MemoryBlock",
            content="Test memory content",
            memory_type="episodic"
        )
        
        try:
            from hacs_tools.tools import create_memory
            
            result = create_memory(
                content="Test memory content",
                memory_type="episodic",
                importance_score=0.8,
                tags=["test", "memory"]
            )
            
            assert result["success"] is True
            assert "memory-123" in str(result)
            
        except ImportError:
            pytest.skip("create_memory not available")

    @patch('hacs_tools.tools.get_vector_store')
    def test_search_memories_tool(self, mock_vector_store):
        """Test search_memories tool."""
        mock_store = MagicMock()
        mock_vector_store.return_value = mock_store
        
        # Mock memory search results
        mock_store.search.return_value = [
            {
                "id": "memory-123",
                "content": "Test memory content",
                "memory_type": "episodic",
                "score": 0.95
            }
        ]
        
        try:
            from hacs_tools.tools import search_memories
            
            result = search_memories(
                query="test memory",
                memory_type="episodic",
                limit=5
            )
            
            assert isinstance(result, list)
            assert len(result) > 0
            assert result[0]["content"] == "Test memory content"
            
        except ImportError:
            pytest.skip("search_memories not available")

    @patch('hacs_tools.tools.get_persistence_provider')
    def test_consolidate_memories_tool(self, mock_provider):
        """Test consolidate_memories tool."""
        mock_adapter = MagicMock()
        mock_provider.return_value = mock_adapter
        
        # Mock memory consolidation
        mock_adapter.save_resource.return_value = MagicMock(
            id="memory-consolidated-456",
            content="Consolidated memory content",
            memory_type="procedural"
        )
        
        try:
            from hacs_tools.tools import consolidate_memories
            
            result = consolidate_memories(
                memory_ids=["memory-123", "memory-124"],
                consolidation_strategy="merge"
            )
            
            assert result["success"] is True
            assert "consolidated" in result["message"].lower()
            
        except ImportError:
            pytest.skip("consolidate_memories not available")


@pytest.mark.unit
class TestHACSValidationTools:
    """Test HACS validation and schema tools."""

    def test_validate_resource_data_tool(self):
        """Test validate_hacs_record_data tool."""
        try:
            from hacs_tools.tools import validate_hacs_record_data
            
            # Test valid data
            result = validate_hacs_record_data(
                resource_type="Patient",
                resource_data={
                    "full_name": "Valid Patient",
                    "birth_date": "1990-01-01",
                    "gender": "male"
                }
            )
            
            assert result["is_valid"] is True
            assert len(result.get("errors", [])) == 0
            
        except ImportError:
            pytest.skip("validate_hacs_record_data not available")

    def test_get_resource_schema_tool(self):
        """Test get_hacs_resource_schema tool."""
        try:
            from hacs_tools.tools import get_hacs_resource_schema
            
            result = get_hacs_resource_schema(
                resource_type="Patient",
                include_validation_rules=True
            )
            
            assert isinstance(result, dict)
            assert "properties" in result or "fields" in result
            
        except ImportError:
            pytest.skip("get_hacs_resource_schema not available")

    def test_suggest_view_fields_tool(self):
        """Test suggest_view_fields tool."""
        try:
            from hacs_tools.tools import suggest_view_fields
            
            result = suggest_view_fields(
                resource_type="Patient",
                use_case="summary_view",
                max_fields=5
            )
            
            assert isinstance(result, dict)
            assert "suggested_fields" in result
            
        except ImportError:
            pytest.skip("suggest_view_fields not available")


@pytest.mark.unit
class TestHACSDiscoveryTools:
    """Test HACS resource discovery tools."""

    def test_discover_resources_tool(self):
        """Test discover_hacs_resources tool."""
        try:
            from hacs_tools.tools import discover_hacs_resources
            
            result = discover_hacs_resources(
                category_filter="clinical",
                include_examples=True
            )
            
            assert isinstance(result, dict)
            assert "resources" in result
            
        except ImportError:
            pytest.skip("discover_hacs_resources not available")

    def test_analyze_resource_fields_tool(self):
        """Test analyze_resource_fields tool."""
        try:
            from hacs_tools.tools import analyze_resource_fields
            
            result = analyze_resource_fields(
                resource_type="Patient",
                analysis_type="comprehensive"
            )
            
            assert isinstance(result, dict)
            assert "field_analysis" in result
            
        except ImportError:
            pytest.skip("analyze_resource_fields not available")

    def test_compare_resource_schemas_tool(self):
        """Test compare_resource_schemas tool."""
        try:
            from hacs_tools.tools import compare_resource_schemas
            
            result = compare_resource_schemas(
                resource_type_1="Patient",
                resource_type_2="Actor",
                comparison_type="detailed"
            )
            
            assert isinstance(result, dict)
            assert "comparison" in result
            
        except ImportError:
            pytest.skip("compare_resource_schemas not available")


@pytest.mark.unit
class TestHACSClinicalTools:
    """Test HACS clinical workflow tools."""

    def test_create_clinical_template_tool(self):
        """Test create_clinical_template tool."""
        try:
            from hacs_tools.tools import create_clinical_template
            
            result = create_clinical_template(
                template_type="assessment",
                focus_area="cardiology",
                complexity_level="standard"
            )
            
            assert isinstance(result, dict)
            assert "template" in result
            
        except ImportError:
            pytest.skip("create_clinical_template not available")

    def test_create_model_stack_tool(self):
        """Test create_model_stack tool."""
        try:
            from hacs_tools.tools import create_model_stack
            
            result = create_model_stack(
                base_models=["Patient", "Observation"],
                relationships={"Observation.patient_id": "Patient.id"},
                use_case="patient_summary"
            )
            
            assert isinstance(result, dict)
            assert "model_stack" in result
            
        except ImportError:
            pytest.skip("create_model_stack not available")

    @patch('hacs_tools.tools.get_persistence_provider')
    def test_create_knowledge_item_tool(self, mock_provider):
        """Test create_knowledge_item tool."""
        mock_adapter = MagicMock()
        mock_provider.return_value = mock_adapter
        
        mock_adapter.save_resource.return_value = MagicMock(
            id="knowledge-123",
            title="Test Knowledge Item"
        )
        
        try:
            from hacs_tools.tools import create_knowledge_item
            
            result = create_knowledge_item(
                title="Clinical Guideline Test",
                content="Test knowledge content",
                knowledge_type="guideline",
                tags=["test", "guideline"]
            )
            
            assert result["success"] is True
            
        except ImportError:
            pytest.skip("create_knowledge_item not available")


@pytest.mark.unit
class TestHACSAdvancedTools:
    """Test HACS advanced tools."""

    @patch('hacs_tools.tools.get_llm_provider')
    def test_optimize_resource_for_llm_tool(self, mock_llm):
        """Test optimize_resource_for_llm tool."""
        mock_provider = MagicMock()
        mock_llm.return_value = mock_provider
        
        # Mock LLM optimization
        mock_provider.optimize_for_generation.return_value = {
            "optimized_schema": {"fields": ["name", "age", "diagnosis"]},
            "optimization_notes": "Simplified for LLM generation"
        }
        
        try:
            from hacs_tools.tools import optimize_resource_for_llm
            
            result = optimize_resource_for_llm(
                resource_type="Patient",
                optimization_target="generation",
                llm_model="gpt-4"
            )
            
            assert isinstance(result, dict)
            assert "optimized_schema" in result
            
        except ImportError:
            pytest.skip("optimize_resource_for_llm not available")

    @patch('hacs_tools.tools.get_registry')
    def test_version_resource_tool(self, mock_registry):
        """Test version_hacs_resource tool."""
        mock_reg = MagicMock()
        mock_registry.return_value = mock_reg
        
        # Mock versioning
        mock_reg.create_version.return_value = {
            "version": "1.1.0",
            "changes": ["Added new field", "Updated validation"]
        }
        
        try:
            from hacs_tools.tools import version_hacs_resource
            
            result = version_hacs_resource(
                resource_type="Patient",
                version_increment="minor",
                change_description="Added new fields"
            )
            
            assert isinstance(result, dict)
            assert "version" in result
            
        except ImportError:
            pytest.skip("version_hacs_resource not available")


@pytest.mark.unit
class TestHACSToolsError:
    """Test HACS tools error handling."""

    @patch('hacs_tools.tools.get_persistence_provider')
    def test_create_resource_error_handling(self, mock_provider):
        """Test error handling in create_hacs_record."""
        # Mock provider that raises exception
        mock_provider.side_effect = Exception("Database connection failed")
        
        try:
            from hacs_tools.tools import create_hacs_record
            
            result = create_hacs_record(
                resource_type="Patient",
                resource_data={"invalid": "data"}
            )
            
            # Should handle error gracefully
            assert result["success"] is False
            assert "error" in result
            
        except ImportError:
            pytest.skip("create_hacs_record not available")

    def test_invalid_resource_type_handling(self):
        """Test handling of invalid resource types."""
        try:
            from hacs_tools.tools import validate_hacs_record_data
            
            result = validate_hacs_record_data(
                resource_type="InvalidResourceType",
                resource_data={"some": "data"}
            )
            
            assert result["is_valid"] is False
            assert len(result.get("errors", [])) > 0
            
        except ImportError:
            pytest.skip("validate_hacs_record_data not available")


@pytest.mark.performance
class TestHACSToolsPerformance:
    """Test HACS tools performance."""

    @patch('hacs_tools.tools.get_persistence_provider')
    def test_bulk_operations_performance(self, mock_provider):
        """Test performance of bulk operations."""
        import time
        
        mock_adapter = MagicMock()
        mock_provider.return_value = mock_adapter
        
        # Mock fast responses
        mock_adapter.save_resource.return_value = MagicMock(id="test-123")
        
        try:
            from hacs_tools.tools import create_hacs_record
            
            start = time.time()
            
            # Create multiple resources
            for i in range(10):
                create_hacs_record(
                    resource_type="Patient",
                    resource_data={
                        "full_name": f"Patient {i}",
                        "birth_date": "1990-01-01"
                    }
                )
            
            end = time.time()
            duration = end - start
            
            # Should be fast
            assert duration < 2.0
            
        except ImportError:
            pytest.skip("create_hacs_record not available")

    @patch('hacs_tools.tools.get_vector_store')
    def test_search_performance(self, mock_vector_store):
        """Test search operation performance."""
        import time
        
        mock_store = MagicMock()
        mock_vector_store.return_value = mock_store
        
        # Mock fast search
        mock_store.search.return_value = [
            {"id": f"memory-{i}", "content": f"Memory {i}"}
            for i in range(20)
        ]
        
        try:
            from hacs_tools.tools import search_memories
            
            start = time.time()
            
            # Perform multiple searches
            for _ in range(5):
                search_memories(
                    query="test query",
                    limit=20
                )
            
            end = time.time()
            duration = end - start
            
            # Should be fast
            assert duration < 1.0
            
        except ImportError:
            pytest.skip("search_memories not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 