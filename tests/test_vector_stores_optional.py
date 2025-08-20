import pytest


@pytest.mark.unit
def test_pinecone_optional_imports():
    try:
        from hacs_utils.integrations.pinecone import PineconeVectorStore, create_pinecone_store
        assert PineconeVectorStore is not None
        assert callable(create_pinecone_store)
    except ImportError:
        pytest.skip("pinecone not installed")


@pytest.mark.unit
def test_qdrant_optional_imports():
    try:
        from hacs_utils.integrations.qdrant import QdrantVectorStore, create_qdrant_store
        assert QdrantVectorStore is not None
        assert callable(create_qdrant_store)
    except ImportError:
        pytest.skip("qdrant not installed")


