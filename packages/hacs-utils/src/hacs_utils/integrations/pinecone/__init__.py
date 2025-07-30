"""
HACS Pinecone Integration

Provides PineconeVectorStore class for vector storage and retrieval using Pinecone v7.x SDK.
"""

import importlib.util

# Check if Pinecone is available without importing it
_has_pinecone = importlib.util.find_spec("pinecone") is not None

if _has_pinecone:
    try:
        # Only import our store if pinecone is available
        from .store import PineconeVectorStore

        # Factory functions for graceful degradation
        def create_pinecone_store(*args, **kwargs):
            """Create PineconeVectorStore instance if available."""
            return PineconeVectorStore(*args, **kwargs)

        def create_test_pinecone_store(*args, **kwargs):
            """Create test PineconeVectorStore instance if available."""
            return PineconeVectorStore(*args, **kwargs)

    except Exception as e:
        # Handle package conflicts at store level
        import warnings
        if "pinecone-client" in str(e):
            warnings.warn(
                "Pinecone package conflict detected. Please uninstall 'pinecone-client' "
                "and install 'pinecone' instead. Vector storage will be disabled.",
                UserWarning
            )
        # Graceful degradation when store import fails
        PineconeVectorStore = None
        _has_pinecone = False

        def create_pinecone_store(*args, **kwargs):
            """Create PineconeVectorStore instance if available."""
            raise ImportError(
                "Pinecone not available. Either:\n"
                "1. Install with: pip install pinecone\n"
                "2. Or if you have 'pinecone-client' installed, uninstall it first:\n"
                "   pip uninstall pinecone-client && pip install pinecone"
            )

        def create_test_pinecone_store(*args, **kwargs):
            """Create test PineconeVectorStore instance if available."""
            raise ImportError(
                "Pinecone not available. Either:\n"
                "1. Install with: pip install pinecone\n"
                "2. Or if you have 'pinecone-client' installed, uninstall it first:\n"
                "   pip uninstall pinecone-client && pip install pinecone"
            )
else:
    # Pinecone not available at all
    PineconeVectorStore = None

    def create_pinecone_store(*args, **kwargs):
        """Create PineconeVectorStore instance if available."""
        raise ImportError("Pinecone not available. Install with: pip install pinecone")

    def create_test_pinecone_store(*args, **kwargs):
        """Create test PineconeVectorStore instance if available."""
        raise ImportError("Pinecone not available. Install with: pip install pinecone")

__version__ = "0.2.0"
__all__ = [
    "PineconeVectorStore",
    "create_pinecone_store",
    "create_test_pinecone_store",
]