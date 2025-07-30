"""
HACS Pinecone Vector Store Implementation

Provides PineconeVectorStore class for vector storage and retrieval using Pinecone v7.x SDK.
"""

import hashlib
import os
import time
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

# Import core dependencies with graceful degradation
try:
    from pinecone import Pinecone, ServerlessSpec
    _has_pinecone_sdk = True
except ImportError as e:
    # Handle pinecone package naming conflicts
    if "pinecone-client" in str(e):
        # User has old pinecone-client package installed
        Pinecone = None
        ServerlessSpec = None
        _has_pinecone_sdk = False
    else:
        # Regular import error
        Pinecone = None
        ServerlessSpec = None
        _has_pinecone_sdk = False

# Optional imports for type hints only
if TYPE_CHECKING:
    pass  # Remove unused imports to fix linter errors


class PineconeVectorStore:
    """Pinecone vector store implementation for HACS."""

    def __init__(
        self,
        index_name: str = "hacs-vectors",
        api_key: str | None = None,
        dimension: int = 1536,
        metric: str = "cosine",
        cloud: str = "aws",
        region: str = "us-east-1",
        create_if_not_exists: bool = True,
        delete_if_exists: bool = False,
        auto_embed: bool = True,
        embedding_model: str = "text-embedding-3-small",
    ):
        """
        Initialize Pinecone vector store with v7.x SDK.

        Args:
            index_name: Name of the Pinecone index (or pass just the name for convenience)
            api_key: Pinecone API key (defaults to PINECONE_API_KEY env var)
            dimension: Vector dimension (default: 1536 for OpenAI embeddings)
            metric: Distance metric (cosine, euclidean, dotproduct)
            cloud: Cloud provider (aws, gcp, azure)
            region: Cloud region
            create_if_not_exists: Create index if it doesn't exist
            delete_if_exists: Delete index if it exists (useful for testing)
            auto_embed: Automatically create embeddings when storing HACS models
            embedding_model: OpenAI embedding model to use
        """
        if not _has_pinecone_sdk:
            raise ImportError(
                "Pinecone SDK not available. Either:\n"
                "1. Install with: pip install pinecone\n"
                "2. Or if you have 'pinecone-client' installed, uninstall it first:\n"
                "   pip uninstall pinecone-client && pip install pinecone"
            )

        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Pinecone API key not found. Set PINECONE_API_KEY environment variable or pass api_key parameter."
            )

        self.index_name = index_name
        self.dimension = dimension
        self.metric = metric
        self.cloud = cloud
        self.region = region
        self.auto_embed = auto_embed
        self.embedding_model = embedding_model

        # Initialize Pinecone client with v7.x SDK
        try:
            self.pc = Pinecone(api_key=self.api_key)
        except Exception as e:
            raise ValueError(f"Failed to initialize Pinecone client: {e}")

        # Store classes for use in methods
        self.Pinecone = Pinecone
        self.ServerlessSpec = ServerlessSpec
        self.index = None
        self.vectorizer = None

        # Handle index creation/deletion
        if delete_if_exists and self._index_exists():
            self._delete_index()

        if create_if_not_exists and not self._index_exists():
            self._create_index()

        # Connect to index
        if self._index_exists():
            self.index = self.pc.Index(self.index_name)
        else:
            print(f"Warning: Index '{self.index_name}' does not exist")

        # Initialize vectorizer if auto_embed is enabled
        if self.auto_embed:
            self._init_vectorizer()

    def _init_vectorizer(self):
        """Initialize the vectorizer for auto-embedding."""
        try:
            # Try to use OpenAI embedding from the integrations
            from ..openai import create_openai_embedding

            embedding_model = create_openai_embedding(model=self.embedding_model)
            # We'll need to adapt this to work with HACS vectorizer when available
            self.embedding_model_instance = embedding_model
        except ImportError:
            print("Warning: OpenAI integration not available. Auto-embedding disabled.")
            self.auto_embed = False

    def store(self, resources: list[Any] | Any) -> bool:
        """
        Store HACS resources with automatic vectorization.

        Args:
            resources: Single resource or list of resources to store

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.auto_embed:
            print("Auto-embedding is disabled. Use store_vector() directly.")
            return False

        if not hasattr(self, 'embedding_model_instance'):
            print("Embedding model not initialized. Cannot store resources.")
            return False

        # Convert single resource to list
        if not isinstance(resources, list):
            resources = [resources]

        try:
            # Store each resource
            for resource in resources:
                # Get text content from the resource for embedding
                if hasattr(resource, "model_dump"):
                    # Pydantic model - convert to dict then to text
                    resource_dict = resource.model_dump()
                    text_content = self._extract_text_from_dict(resource_dict)
                elif hasattr(resource, "dict"):
                    # Older Pydantic models
                    resource_dict = resource.dict()
                    text_content = self._extract_text_from_dict(resource_dict)
                else:
                    # Fallback to string representation
                    text_content = str(resource)
                    resource_dict = {"content": text_content}

                # Generate embedding
                try:
                    embedding = self.embedding_model_instance.embed(text_content)
                except Exception as e:
                    print(f"Warning: Failed to generate embedding: {e}")
                    return False

                # Create metadata for Pinecone
                metadata = {
                    "resource_type": resource.__class__.__name__
                    if hasattr(resource, "__class__")
                    else "unknown",
                    "resource_id": getattr(resource, "id", f"resource_{uuid.uuid4()}"),
                    "content_hash": hashlib.sha256(text_content.encode()).hexdigest(),
                    "content_length": len(text_content),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }

                # Add specific fields based on resource type
                if hasattr(resource, "subject"):
                    metadata["subject"] = str(resource.subject)
                if hasattr(resource, "code") and isinstance(resource.code, dict):
                    metadata["code_text"] = resource.code.get("text", "")
                if hasattr(resource, "value_string"):
                    metadata["value"] = str(resource.value_string)
                if hasattr(resource, "name") and isinstance(resource.name, list):
                    # Handle FHIR name structure
                    names = []
                    for name in resource.name:
                        if isinstance(name, dict):
                            given = name.get("given", [])
                            family = name.get("family", "")
                            if given or family:
                                full_name = " ".join(given + [family]).strip()
                                names.append(full_name)
                    if names:
                        metadata["patient_name"] = ", ".join(names)
                if hasattr(resource, "gender"):
                    metadata["gender"] = str(resource.gender)
                if hasattr(resource, "birth_date"):
                    metadata["birth_date"] = str(resource.birth_date)
                if hasattr(resource, "content"):
                    metadata["message_content"] = str(resource.content)
                if hasattr(resource, "confidence_score"):
                    metadata["confidence_score"] = float(resource.confidence_score)

                # Store the vector
                vector_id = f"{metadata['resource_type'].lower()}_{metadata['resource_id']}"
                success = self.store_vector(vector_id, embedding, metadata)

                if not success:
                    print(f"Failed to store {metadata['resource_type']} {metadata['resource_id']}")
                    return False

            return True
        except Exception as e:
            print(f"Error storing resources: {e}")
            return False

    def _extract_text_from_dict(self, data: dict) -> str:
        """Extract meaningful text content from a resource dictionary."""
        import json

        # For Patient resources
        if "name" in data:
            parts = []
            if isinstance(data["name"], list):
                for name in data["name"]:
                    if isinstance(name, dict):
                        given = name.get("given", [])
                        family = name.get("family", "")
                        parts.extend(given)
                        if family:
                            parts.append(family)
            if "gender" in data:
                parts.append(f"gender: {data['gender']}")
            if "birth_date" in data:
                parts.append(f"birth date: {data['birth_date']}")
            return " ".join(parts)

        # For Observation resources
        if "code" in data and "value_string" in data:
            code_text = (
                data["code"].get("text", "")
                if isinstance(data["code"], dict)
                else str(data["code"])
            )
            return f"{code_text}: {data['value_string']}"

        # For AgentMessage resources
        if "content" in data:
            parts = [data["content"]]
            if "confidence_score" in data:
                parts.append(f"confidence: {data['confidence_score']}")
            if "reasoning_trace" in data:
                reasoning = data["reasoning_trace"]
                if isinstance(reasoning, list):
                    reasoning_text = " ".join([str(step) for step in reasoning])
                    parts.append(f"reasoning: {reasoning_text}")
            return " ".join(parts)

        # Fallback: convert entire dict to text
        return json.dumps(data, default=str)

    def search(
        self, query: str, top_k: int = 10, resource_type: str | None = None, **kwargs
    ) -> list[tuple[str, float, dict]]:
        """
        Search stored resources using natural language query.

        Args:
            query: Natural language search query
            top_k: Number of results to return
            resource_type: Filter by resource type (e.g., "Patient", "Observation")

        Returns:
            List of (resource_id, score, metadata) tuples
        """
        if not hasattr(self, 'embedding_model_instance'):
            print("Warning: Embedding model not available for query embedding.")
            return []

        try:
            # Generate embedding for the query
            query_embedding = self.embedding_model_instance.embed(query)
        except Exception as e:
            print(f"Warning: Failed to generate query embedding: {e}")
            return []

        try:
            # Create filter if resource_type is specified
            filter_dict = None
            if resource_type:
                filter_dict = {"resource_type": resource_type}

            return self.search_vectors(query_embedding, top_k=top_k, filter_dict=filter_dict)
        except Exception as e:
            print(f"Error searching: {e}")
            return []

    def _index_exists(self) -> bool:
        """Check if the index exists."""
        try:
            indexes = self.pc.list_indexes()
            return any(idx["name"] == self.index_name for idx in indexes)
        except Exception:
            return False

    def _create_index(self) -> bool:
        """Create a new Pinecone index with v7.x SDK."""
        try:
            print(f"Creating Pinecone index '{self.index_name}' with dimension {self.dimension}")

            self.pc.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric=self.metric,
                spec=self.ServerlessSpec(cloud=self.cloud, region=self.region),
            )

            # Wait for index to be ready
            max_wait = 60  # seconds
            wait_time = 0
            while wait_time < max_wait:
                try:
                    # Try to get index stats to check if it's ready
                    index = self.pc.Index(self.index_name)
                    index.describe_index_stats()
                    print(f"Index '{self.index_name}' is ready!")
                    return True
                except Exception:
                    pass

                time.sleep(2)
                wait_time += 2
                print(f"Waiting for index to be ready... ({wait_time}s)")

            print(f"Warning: Index creation may still be in progress after {max_wait}s")
            return True

        except Exception as e:
            print(f"Error creating index: {e}")
            return False

    def _delete_index(self) -> bool:
        """Delete the Pinecone index."""
        try:
            print(f"Deleting Pinecone index '{self.index_name}'")
            self.pc.delete_index(self.index_name)

            # Wait for deletion to complete
            max_wait = 30
            wait_time = 0
            while self._index_exists() and wait_time < max_wait:
                time.sleep(1)
                wait_time += 1

            print(f"Index '{self.index_name}' deleted")
            return True

        except Exception as e:
            print(f"Error deleting index: {e}")
            return False

    def store_vector(
        self, vector_id: str, embedding: list[float], metadata: dict[str, Any]
    ) -> bool:
        """Store a vector in Pinecone."""
        if not self.index:
            print("Error: Index not initialized")
            return False

        try:
            # Ensure vector_id is a string
            if not isinstance(vector_id, str):
                vector_id = str(vector_id)

            # Validate embedding dimension
            if len(embedding) != self.dimension:
                print(
                    f"Error: Embedding dimension {len(embedding)} doesn't match index dimension {self.dimension}"
                )
                return False

            # Flatten metadata for Pinecone (only accepts string, number, boolean, list of strings)
            def flatten_for_pinecone(data, prefix=""):
                flat = {}
                for key, value in data.items():
                    full_key = f"{prefix}{key}" if prefix else key

                    if value is None:
                        continue  # Skip None values
                    elif isinstance(value, str | int | float | bool):
                        flat[full_key] = value
                    elif isinstance(value, list):
                        if all(isinstance(item, str) for item in value):
                            # Convert list to comma-separated string
                            flat[full_key] = ",".join(value) if value else ""
                        else:
                            # Convert non-string lists to string representation
                            flat[full_key] = str(value)
                    elif isinstance(value, dict):
                        # Recursively flatten nested dictionaries
                        nested = flatten_for_pinecone(value, f"{full_key}_")
                        flat.update(nested)
                    else:
                        # Convert other types to string
                        flat[full_key] = str(value)

                return flat

            pinecone_metadata = flatten_for_pinecone(metadata)

            # Ensure we have valid metadata
            if not pinecone_metadata:
                pinecone_metadata = {"resource_type": "unknown"}

            self.index.upsert(
                [{"id": vector_id, "values": embedding, "metadata": pinecone_metadata}]
            )
            return True

        except Exception as e:
            print(f"Error storing vector in Pinecone: {e}")
            return False

    def search_vectors(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filter_dict: dict[str, Any] | None = None,
    ) -> list[tuple[str, float, dict[str, Any]]]:
        """Search for similar vectors in Pinecone."""
        if not self.index:
            print("Error: Index not initialized")
            return []

        try:
            # Validate embedding dimension
            if len(query_embedding) != self.dimension:
                print(
                    f"Error: Query embedding dimension {len(query_embedding)} doesn't match index dimension {self.dimension}"
                )
                return []

            results = self.index.query(
                vector=query_embedding, top_k=top_k, filter=filter_dict, include_metadata=True
            )

            return [(match.id, match.score, match.metadata or {}) for match in results.matches]

        except Exception as e:
            print(f"Error searching in Pinecone: {e}")
            return []

    def get_vector(self, vector_id: str) -> tuple[list[float], dict[str, Any]] | None:
        """Retrieve a specific vector by ID."""
        if not self.index:
            print("Error: Index not initialized")
            return None

        try:
            result = self.index.fetch([str(vector_id)])
            if str(vector_id) in result.vectors:
                vector_data = result.vectors[str(vector_id)]
                return (vector_data.values, vector_data.metadata or {})
            return None

        except Exception as e:
            print(f"Error retrieving vector from Pinecone: {e}")
            return None

    def delete_vector(self, vector_id: str) -> bool:
        """Delete a vector from Pinecone."""
        if not self.index:
            print("Error: Index not initialized")
            return False

        try:
            self.index.delete([str(vector_id)])
            return True

        except Exception as e:
            print(f"Error deleting vector from Pinecone: {e}")
            return False

    def get_stats(self) -> dict[str, Any]:
        """Get index statistics."""
        if not self.index:
            return {"error": "Index not initialized"}

        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
                "namespaces": dict(stats.namespaces) if stats.namespaces else {},
            }
        except Exception as e:
            return {"error": str(e)}

    def cleanup(self) -> bool:
        """Clean up resources (delete index if it exists)."""
        try:
            if self._index_exists():
                return self._delete_index()
            return True
        except Exception as e:
            print(f"Error during cleanup: {e}")
            return False


# Convenience functions
def create_pinecone_store(
    api_key: str, index_name: str = "hacs-vectors", dimension: int = 1536, **kwargs
) -> PineconeVectorStore:
    """Create a Pinecone vector store with v7.x SDK."""
    return PineconeVectorStore(
        api_key=api_key, index_name=index_name, dimension=dimension, **kwargs
    )


def create_test_pinecone_store(api_key: str) -> PineconeVectorStore:
    """Create a test Pinecone store with cleanup enabled."""
    import time

    test_index_name = f"test-hacs-{int(time.time())}"

    return PineconeVectorStore(
        api_key=api_key,
        index_name=test_index_name,
        dimension=1536,
        create_if_not_exists=True,
        delete_if_exists=True,
    )