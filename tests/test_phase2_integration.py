"""
Phase 2 Integration Tests - Persistence, Security, and Vector Operations

Tests the core functionality implemented in Phase 2:
- Persistence layer activation with connection factory
- Security integration with actor-based permissions
- Vector search integration with multiple interfaces
- End-to-end tool execution with all components
"""

import pytest
import os
from unittest.mock import MagicMock, patch

# Core HACS imports
try:
    from hacs_persistence import (
        HACSConnectionFactory,
        get_default_adapter,
        ensure_database_ready,
    )

    PERSISTENCE_AVAILABLE = True
except ImportError:
    PERSISTENCE_AVAILABLE = False

try:
    from hacs_auth import ToolSecurityContext, create_secure_actor, ActorRole

    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False

from hacs_models import Actor
from hacs_models import MemoryResult, HACSResult, VectorStoreResult
from hacs_registry import execute_hacs_tool


class MockVectorStore:
    """Mock vector store for testing vector operations."""

    def __init__(self):
        self.vectors = {}
        self.metadata = {}

    def add_vectors(self, ids, vectors, metadata_list):
        """Mock add_vectors interface."""
        for i, (vector_id, vector, metadata) in enumerate(
            zip(ids, vectors, metadata_list)
        ):
            self.vectors[vector_id] = vector
            self.metadata[vector_id] = metadata

    def similarity_search(self, query, limit=10):
        """Mock similarity search."""
        results = []
        for vector_id, metadata in list(self.metadata.items())[:limit]:
            results.append(
                {
                    "id": vector_id,
                    "resource_id": metadata.get("resource_id", vector_id),
                    "content": metadata.get("content", "Mock content"),
                    "similarity_score": 0.85,
                    "metadata": metadata,
                }
            )
        return results

    def generate_embedding(self, text):
        """Mock embedding generation."""
        import hashlib

        hash_value = int(hashlib.md5(text.encode()).hexdigest(), 16)
        return [(hash_value >> i) % 100 / 100.0 for i in range(384)]


class MockDBAdapter:
    """Mock database adapter for testing persistence operations."""

    def __init__(self):
        self.resources = {}
        self.connection_active = True

    def save_resource(self, resource_data):
        """Mock save_resource method."""
        resource_id = resource_data.get("id", f"mock-{len(self.resources)}")
        self.resources[resource_id] = resource_data
        return {"id": resource_id, "saved": True}

    def create_resource(self, resource):
        """Mock create_resource method."""
        resource_data = (
            resource.model_dump() if hasattr(resource, "model_dump") else resource
        )
        resource_id = resource_data.get("id", f"mock-{len(self.resources)}")
        self.resources[resource_id] = resource_data
        return resource_id

    def get_resource(self, resource_type, resource_id):
        """Mock get_resource method."""
        return self.resources.get(resource_id)

    def execute_query(self, query, params=None):
        """Mock query execution."""
        return [{"id": "query-result-1", "status": "success"}]


@pytest.fixture
def mock_vector_store():
    """Provide a mock vector store for testing."""
    return MockVectorStore()


@pytest.fixture
def mock_db_adapter():
    """Provide a mock database adapter for testing."""
    return MockDBAdapter()


@pytest.fixture
def test_actor():
    """Provide a test actor for security testing."""
    actor = Actor(
        name="Test Doctor",
        role="physician",
        permissions=["read:*", "write:*", "admin:tools"],
        session_status="active",
    )
    actor.start_session("test-session-123")
    return actor


class TestPersistenceIntegration:
    """Test persistence layer integration."""

    @pytest.mark.skipif(
        not PERSISTENCE_AVAILABLE, reason="hacs-persistence not available"
    )
    def test_connection_factory_singleton(self):
        """Test that connection factory implements singleton pattern."""
        factory1 = HACSConnectionFactory()
        factory2 = HACSConnectionFactory()
        assert factory1 is factory2

    @pytest.mark.skipif(
        not PERSISTENCE_AVAILABLE, reason="hacs-persistence not available"
    )
    def test_connection_factory_adapter_caching(self):
        """Test that connection factory caches adapters properly."""
        with patch.dict(
            os.environ, {"DATABASE_URL": "postgresql://test:test@localhost/test"}
        ):
            with patch(
                "hacs_persistence.connection_factory.create_postgres_adapter"
            ) as mock_create:
                mock_adapter = MagicMock()
                mock_create.return_value = mock_adapter

                # Mock migration status and run_migration
                with patch(
                    "hacs_persistence.connection_factory.get_migration_status"
                ) as mock_status:
                    with patch(
                        "hacs_persistence.connection_factory.run_migration"
                    ) as mock_migration:
                        mock_status.return_value = {"schemas_exist": False}
                        mock_migration.return_value = True

                        # Get adapter twice
                        adapter1 = HACSConnectionFactory.get_adapter()
                        adapter2 = HACSConnectionFactory.get_adapter()

                        # Should be the same instance (cached)
                        assert adapter1 is adapter2
                        # create_postgres_adapter should only be called once
                        assert mock_create.call_count == 1

    def test_memory_tool_persistence_integration(
        self, mock_db_adapter, mock_vector_store
    ):
        """Test memory operations tool with real persistence integration."""

        # Import the actual tool function
        from hacs_tools.domains.memory_operations import create_hacs_memory

        # Execute memory creation with persistence
        result = create_hacs_memory(
            actor_name="Test Doctor",
            memory_content="Patient shows positive response to ACE inhibitors",
            memory_type="episodic",
            clinical_context="cardiology",
            confidence_score=0.9,
            patient_id="patient-123",
            db_adapter=mock_db_adapter,
            vector_store=mock_vector_store,
        )

        # Verify successful execution
        assert isinstance(result, MemoryResult)
        assert result.success is True
        assert "storage_status" in result.message

        # Verify database persistence
        assert len(mock_db_adapter.resources) > 0

        # Verify vector storage
        assert len(mock_vector_store.vectors) > 0

        # Verify consolidation summary includes status
        assert "database_status" in result.consolidation_summary
        assert "vector_status" in result.consolidation_summary

    def test_resource_tool_persistence_integration(self, mock_db_adapter):
        """Test resource management tool with database persistence."""

        # Updated import: resource_management removed; use developer agent integration or database/modeling tools
        from examples.hacs_developer_agent.hacs_tools_integration import create_record

        # Create a patient record
        patient_data = {
            "full_name": "John Doe",
            "birth_date": "1990-01-01",
            "gender": "male",
        }

        result = create_record(
            actor_name="Test Doctor",
            resource_type="Patient",
            resource_data=patient_data,
            db_adapter=mock_db_adapter,
        )

        # Verify successful execution
        assert isinstance(result, HACSResult)
        assert result.success is True
        assert "persistence_status" in result.data

        # Verify database storage
        assert len(mock_db_adapter.resources) > 0
        stored_resource = list(mock_db_adapter.resources.values())[0]
        assert stored_resource["full_name"] == "John Doe"


class TestSecurityIntegration:
    """Test security integration with tool execution."""

    @pytest.mark.skipif(not AUTH_AVAILABLE, reason="hacs-auth not available")
    def test_secure_actor_creation(self):
        """Test secure actor creation with session management."""

        actor = create_secure_actor(
            actor_name="Test Physician",
            role=ActorRole.PHYSICIAN,
            permissions=["read:patient", "write:observation"],
            session_duration_hours=8,
        )

        assert actor.name == "Test Physician"
        assert actor.role == ActorRole.PHYSICIAN
        assert actor.has_active_session()
        assert actor.has_permission("read:patient")
        assert actor.has_permission("write:observation")

    @pytest.mark.skipif(not AUTH_AVAILABLE, reason="hacs-auth not available")
    def test_tool_security_context_validation(self, test_actor):
        """Test tool security context permission validation."""

        security_context = ToolSecurityContext(test_actor)

        # Test successful permission validation
        result = security_context.validate_tool_permission(
            "test_tool", ["read:patient"]
        )
        assert result is True

        # Test permission denial
        with pytest.raises(PermissionError):
            security_context.validate_tool_permission(
                "restricted_tool", ["admin:delete_all"]
            )

    @pytest.mark.skipif(not AUTH_AVAILABLE, reason="hacs-auth not available")
    def test_data_access_permission_validation(self, test_actor):
        """Test data access permission validation."""

        security_context = ToolSecurityContext(test_actor)

        # Test successful data access
        result = security_context.validate_data_access_permissions("Patient", "read")
        assert result is True

        # Test wildcard permission matching
        result = security_context.validate_data_access_permissions(
            "Observation", "write"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_tool_execution_with_security_integration(
        self, mock_db_adapter, test_actor
    ):
        """Test end-to-end tool execution with security validation."""

        # Test tool execution through registry integration
        result = await execute_hacs_tool(
            tool_name="create_hacs_memory",
            params={
                "memory_content": "Test memory with security",
                "memory_type": "episodic",
                "clinical_context": "test",
            },
            actor_name=test_actor.name,
            db_adapter=mock_db_adapter,
        )

        # Verify execution
        assert result.success is True
        assert "actor_name" in result.metadata
        assert result.metadata["security_validated"] is True


class TestVectorIntegration:
    """Test vector search integration."""

    def test_vector_embedding_generation(self, mock_vector_store):
        """Test vector embedding generation with different methods."""

        from hacs_tools.domains.vector_search import store_embedding

        result = store_embedding(
            actor_name="Test Researcher",
            content="Clinical protocol for hypertension management",
            collection_name="clinical_protocols",
            metadata={"specialty": "cardiology", "urgency": "routine"},
            clinical_context="cardiology",
            vector_store=mock_vector_store,
        )

        # Verify successful storage
        assert isinstance(result, VectorStoreResult)
        assert result.success is True
        assert "storage_status" in result.message

        # Verify vector was stored
        assert len(mock_vector_store.vectors) > 0

        # Verify metadata was preserved
        stored_metadata = list(mock_vector_store.metadata.values())[0]
        assert stored_metadata["specialty"] == "cardiology"
        assert stored_metadata["clinical_context"] == "cardiology"

    def test_memory_vector_search_integration(self, mock_vector_store):
        """Test memory search with vector store integration."""

        # First, store some test memories
        mock_vector_store.add_vectors(
            ["mem-1", "mem-2"],
            [[0.1] * 384, [0.2] * 384],
            [
                {
                    "resource_id": "mem-1",
                    "content": "Patient responds well to ACE inhibitors",
                    "memory_type": "episodic",
                    "clinical_context": "cardiology",
                    "actor_name": "Dr. Smith",
                },
                {
                    "resource_id": "mem-2",
                    "content": "Standard hypertension protocol",
                    "memory_type": "procedural",
                    "clinical_context": "cardiology",
                    "actor_name": "Dr. Johnson",
                },
            ],
        )

        from hacs_tools.domains.memory_operations import search_hacs_memories

        result = search_hacs_memories(
            actor_name="Test Doctor",
            query="hypertension treatment",
            memory_type="episodic",
            clinical_context="cardiology",
            limit=5,
            vector_store=mock_vector_store,
        )

        # Verify search results
        assert isinstance(result, MemoryResult)
        assert result.success is True
        assert result.memory_count > 0
        assert "vector search" in result.message

        # Verify result structure
        memories = result.retrieval_matches
        assert len(memories) > 0
        assert all("memory_id" in memory for memory in memories)
        assert all("content" in memory for memory in memories)


class TestEndToEndIntegration:
    """Test complete end-to-end workflows."""

    @pytest.mark.asyncio
    async def test_complete_memory_workflow(
        self, mock_db_adapter, mock_vector_store, test_actor
    ):
        """Test complete memory creation and search workflow."""

        # Step 1: Create a memory
        create_result = await execute_hacs_tool(
            tool_name="create_hacs_memory",
            params={
                "memory_content": "Patient shows excellent response to beta-blockers for hypertension",
                "memory_type": "episodic",
                "clinical_context": "cardiology",
                "confidence_score": 0.95,
                "patient_id": "patient-456",
            },
            actor_name=test_actor.name,
            db_adapter=mock_db_adapter,
            vector_store=mock_vector_store,
        )

        assert create_result.success is True

        # Step 2: Search for the memory
        search_result = await execute_hacs_tool(
            tool_name="search_hacs_memories",
            params={
                "query": "beta-blockers hypertension",
                "memory_type": "episodic",
                "clinical_context": "cardiology",
                "limit": 5,
            },
            actor_name=test_actor.name,
            vector_store=mock_vector_store,
        )

        assert search_result.success is True

        # Verify workflow completion
        assert create_result.metadata["security_validated"] is True
        assert search_result.metadata["security_validated"] is True

    @pytest.mark.asyncio
    async def test_complete_resource_workflow(self, mock_db_adapter, test_actor):
        """Test complete resource creation and retrieval workflow."""

        # Step 1: Create a patient resource
        patient_data = {
            "full_name": "Jane Smith",
            "birth_date": "1985-05-15",
            "gender": "female",
            "contact_info": {"email": "jane.smith@example.com", "phone": "+1-555-0123"},
        }

        create_result = await execute_hacs_tool(
            tool_name="create_record",
            params={
                "resource_type": "Patient",
                "resource_data": patient_data,
                "auto_generate_id": True,
                "validate_fhir": True,
            },
            actor_name=test_actor.name,
            db_adapter=mock_db_adapter,
        )

        assert create_result.success is True
        assert "persistence_status" in create_result.data["data"]

        # Step 2: Retrieve the resource
        resource_id = create_result.data["data"]["resource_id"]

        retrieve_result = await execute_hacs_tool(
            tool_name="get_record",
            params={
                "resource_type": "Patient",
                "resource_id": resource_id,
                "include_audit_trail": True,
            },
            actor_name=test_actor.name,
            db_adapter=mock_db_adapter,
        )

        assert retrieve_result.success is True

        # Verify workflow completion
        assert create_result.metadata["security_validated"] is True
        assert retrieve_result.metadata["security_validated"] is True


if __name__ == "__main__":
    # Run tests with detailed output
    pytest.main([__file__, "-v", "-s"])
