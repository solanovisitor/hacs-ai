"""
Integration Tests for HACS Utils

Tests for all external service integrations including OpenAI, Pinecone, Qdrant, etc.
"""

import os
import pytest
from unittest.mock import Mock, patch

# Test that basic imports work
def test_basic_imports():
    """Test that the main package imports work."""
    import hacs_utils

    # Check that package has the expected attributes
    assert hasattr(hacs_utils, '__version__')
    assert hasattr(hacs_utils, 'list_available_integrations')
    assert hasattr(hacs_utils, 'get_integration_info')

    # Check backward compatibility exports
    assert hasattr(hacs_utils, 'CrewAIAdapter')
    assert hasattr(hacs_utils, 'CrewAIAgentRole')


def test_integration_detection():
    """Test integration detection functions."""
    from hacs_utils import list_available_integrations, get_integration_info

    available = list_available_integrations()
    assert isinstance(available, list)

    info = get_integration_info()
    assert isinstance(info, dict)
    assert 'openai' in info
    assert 'pinecone' in info
    assert 'qdrant' in info
    assert 'crewai' in info


class TestOpenAIIntegration:
    """Test OpenAI integration."""

    def test_openai_import(self):
        """Test that OpenAI integration can be imported."""
        try:
            from hacs_utils.integrations import openai
            assert openai is not None
        except ImportError:
            pytest.skip("OpenAI dependencies not installed")

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_openai_embedding_creation(self):
        """Test OpenAI embedding model creation."""
        try:
            from hacs_utils.integrations.openai import OpenAIEmbedding

            # Test creation without actual API call
            embedding = OpenAIEmbedding(api_key='test-key')
            assert embedding.model == "text-embedding-3-small"
            assert embedding.get_dimension() == 1536

        except ImportError:
            pytest.skip("OpenAI dependencies not installed")

    def test_openai_client_creation(self):
        """Test OpenAI client creation."""
        try:
            from hacs_utils.integrations.openai import OpenAIClient

            client = OpenAIClient(api_key='test-key')
            assert client.model == "gpt-4.1"
            assert client.temperature == 0.7

        except ImportError:
            pytest.skip("OpenAI dependencies not installed")

    def test_openai_factory_functions(self):
        """Test OpenAI factory functions."""
        try:
            from hacs_utils.integrations.openai import (
                create_openai_client,
                create_openai_embedding,
                create_structured_generator
            )

            # Test that functions exist and can be called
            assert callable(create_openai_client)
            assert callable(create_openai_embedding)
            assert callable(create_structured_generator)

        except ImportError:
            pytest.skip("OpenAI dependencies not installed")


class TestPineconeIntegration:
    """Test Pinecone integration."""

    def test_pinecone_import(self):
        """Test that Pinecone integration can be imported."""
        try:
            from hacs_utils.integrations import pinecone
            assert pinecone is not None
        except ImportError:
            pytest.skip("Pinecone dependencies not installed")

    @patch.dict(os.environ, {'PINECONE_API_KEY': 'test-key'})
    def test_pinecone_store_creation(self):
        """Test Pinecone vector store creation."""
        try:
            from hacs_utils.integrations.pinecone import PineconeVectorStore

            # Mock Pinecone client to avoid actual API calls
            with patch('hacs_utils.integrations.pinecone.store.Pinecone') as mock_pinecone:
                mock_client = Mock()
                mock_pinecone.return_value = mock_client
                mock_client.list_indexes.return_value = []

                store = PineconeVectorStore(
                    api_key='test-key',
                    create_if_not_exists=False
                )
                assert store.index_name == "hacs-vectors"
                assert store.dimension == 1536

        except ImportError:
            pytest.skip("Pinecone dependencies not installed")

    def test_pinecone_factory_functions(self):
        """Test Pinecone factory functions."""
        try:
            from hacs_utils.integrations.pinecone import (
                create_pinecone_store,
                create_test_pinecone_store
            )

            assert callable(create_pinecone_store)
            assert callable(create_test_pinecone_store)

        except ImportError:
            pytest.skip("Pinecone dependencies not installed")


class TestQdrantIntegration:
    """Test Qdrant integration."""

    def test_qdrant_import(self):
        """Test that Qdrant integration can be imported."""
        try:
            from hacs_utils.integrations import qdrant
            assert qdrant is not None
        except ImportError:
            pytest.skip("Qdrant dependencies not installed")

    def test_qdrant_store_creation(self):
        """Test Qdrant vector store creation."""
        try:
            from hacs_utils.integrations.qdrant import QdrantVectorStore

            # Mock Qdrant client to avoid actual setup
            with patch('hacs_utils.integrations.qdrant.store.QdrantClient') as mock_qdrant:
                mock_client = Mock()
                mock_qdrant.return_value = mock_client
                mock_client.get_collections.return_value = Mock(collections=[])

                store = QdrantVectorStore(
                    client=mock_client,
                    create_if_not_exists=False
                )
                assert store.collection_name == "hacs_vectors"
                assert store.dimension == 1536

        except ImportError:
            pytest.skip("Qdrant dependencies not installed")

    def test_qdrant_factory_functions(self):
        """Test Qdrant factory functions."""
        try:
            from hacs_utils.integrations.qdrant import (
                create_qdrant_store,
                create_test_qdrant_store,
                create_cloud_qdrant_store
            )

            assert callable(create_qdrant_store)
            assert callable(create_test_qdrant_store)
            assert callable(create_cloud_qdrant_store)

        except ImportError:
            pytest.skip("Qdrant dependencies not installed")


class TestCrewAIIntegration:
    """Test CrewAI integration (backward compatibility)."""

    def test_crewai_backward_compatibility(self):
        """Test that CrewAI exports are available at package level."""
        import hacs_utils

        # Test backward compatibility imports
        assert hasattr(hacs_utils, 'CrewAIAdapter')
        assert hasattr(hacs_utils, 'CrewAIAgentRole')
        assert hasattr(hacs_utils, 'CrewAITaskType')
        assert hasattr(hacs_utils, 'create_agent_binding')

    def test_crewai_adapter_creation(self):
        """Test CrewAI adapter creation."""
        from hacs_utils import CrewAIAdapter, CrewAIAgentRole

        adapter = CrewAIAdapter()
        assert hasattr(adapter, 'task_registry')
        assert hasattr(adapter, 'agent_registry')

        # Test that roles are available
        assert hasattr(CrewAIAgentRole, 'CLINICAL_ASSESSOR')
        assert hasattr(CrewAIAgentRole, 'TREATMENT_PLANNER')

    def test_crewai_integration_module(self):
        """Test CrewAI integration module."""
        try:
            from hacs_utils.integrations import crewai
            assert crewai is not None
        except ImportError:
            pytest.skip("CrewAI integration not available")


class TestIntegrationCompatibility:
    """Test integration compatibility and error handling."""

    def test_missing_dependencies_graceful_degradation(self):
        """Test that missing dependencies are handled gracefully."""
        from hacs_utils import list_available_integrations

        # This should not raise an error even if some dependencies are missing
        available = list_available_integrations()
        assert isinstance(available, list)

    def test_integration_info_accuracy(self):
        """Test that integration info matches actual availability."""
        from hacs_utils import get_integration_info, list_available_integrations

        info = get_integration_info()
        available = list_available_integrations()

        # Check that reported availability matches actual availability
        for integration in available:
            assert info[integration]['available'] is True

    def test_import_error_handling(self):
        """Test that import errors are handled properly."""
        # Try importing from integrations that might not be installed
        try:
            from hacs_utils.integrations import openai
            # If successful, openai should not be None
            if openai is not None:
                assert hasattr(openai, '__version__')
        except ImportError:
            # This is expected if dependencies aren't installed
            pass


if __name__ == "__main__":
    pytest.main([__file__])