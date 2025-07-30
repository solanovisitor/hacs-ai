"""
HACS Qdrant Vector Store Implementation

This package provides Qdrant vector store integration for HACS vectorization.
"""

from typing import Any

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, PointStruct, VectorParams
except ImportError:
    QdrantClient = None
    Distance = None
    PointStruct = None
    VectorParams = None


class QdrantVectorStore:
    """Qdrant vector store implementation for HACS."""

    def __init__(
        self,
        client=None,
        collection_name: str = "hacs_vectors",
        dimension: int = 1536,
        distance_metric: str = "Cosine",
        url: str | None = None,
        api_key: str | None = None,
        create_if_not_exists: bool = True,
        delete_if_exists: bool = False,
    ):
        """
        Initialize Qdrant vector store.

        Args:
            client: Existing QdrantClient instance (optional)
            collection_name: Name of the collection to create/use
            dimension: Vector dimension (default: 1536 for OpenAI embeddings)
            distance_metric: Distance metric (Cosine, Euclidean, Dot)
            url: Qdrant server URL (optional, for hosted instances)
            api_key: API key for Qdrant Cloud (optional)
            create_if_not_exists: Whether to create collection if it doesn't exist
            delete_if_exists: Whether to delete existing collection (for testing)
        """
        if QdrantClient is None:
            raise ImportError("Qdrant client not available. Install with: pip install qdrant-client")

        # Initialize client
        if client is not None:
            self.client = client
        elif url and api_key:
            # Qdrant Cloud
            self.client = QdrantClient(url=url, api_key=api_key)
        elif url:
            # Custom server
            self.client = QdrantClient(url=url)
        else:
            # In-memory client for testing
            self.client = QdrantClient(":memory:")

        self.collection_name = collection_name
        self.dimension = dimension

        # Store classes for use in methods
        self.Distance = Distance
        self.VectorParams = VectorParams
        self.PointStruct = PointStruct

        # Map distance metric strings to Qdrant enums
        self.distance_mapping = {
            "Cosine": Distance.COSINE,
            "Euclidean": Distance.EUCLID,
            "Dot": Distance.DOT,
        }
        self.distance_metric = self.distance_mapping.get(distance_metric, Distance.COSINE)

        # Handle collection creation/deletion
        if delete_if_exists and self._collection_exists():
            self._delete_collection()

        if create_if_not_exists and not self._collection_exists():
            self._create_collection()

    def _collection_exists(self) -> bool:
        """Check if the collection exists."""
        try:
            collections = self.client.get_collections()
            return any(
                collection.name == self.collection_name for collection in collections.collections
            )
        except Exception:
            return False

    def _create_collection(self) -> bool:
        """Create a new collection."""
        try:
            print(
                f"Creating Qdrant collection '{self.collection_name}' with dimension {self.dimension}"
            )

            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=self.VectorParams(
                    size=self.dimension, distance=self.distance_metric
                ),
            )

            print(f"Collection '{self.collection_name}' created successfully")
            return True

        except Exception as e:
            print(f"Error creating collection: {e}")
            return False

    def _delete_collection(self) -> bool:
        """Delete the collection."""
        try:
            self.client.delete_collection(self.collection_name)
            print(f"Collection '{self.collection_name}' deleted")
            return True

        except Exception as e:
            print(f"Error deleting collection: {e}")
            return False

    def store_vector(
        self, vector_id: str, embedding: list[float], metadata: dict[str, Any]
    ) -> bool:
        """Store a vector with metadata."""
        try:
            # Ensure vector_id is a string
            if not isinstance(vector_id, str):
                vector_id = str(vector_id)

            # Validate embedding dimension
            if len(embedding) != self.dimension:
                print(
                    f"Error: Embedding dimension {len(embedding)} doesn't match collection dimension {self.dimension}"
                )
                return False

            # Update collection if dimensions don't match (for dynamic collections)
            try:
                collection_info = self.client.get_collection(self.collection_name)
                if collection_info.config.params.vectors.size != self.dimension:
                    print(
                        f"Updating collection dimension from {collection_info.config.params.vectors.size} to {self.dimension}"
                    )
                    # Note: Qdrant doesn't support dimension updates, so we'd need to recreate
                    # For now, just log the mismatch
                    print("Warning: Collection dimension mismatch")
            except Exception:
                pass  # Collection might not exist yet

            # Store the vector
            self.client.upsert(
                collection_name=self.collection_name,
                points=[self.PointStruct(id=vector_id, vector=embedding, payload=metadata)],
            )
            return True

        except Exception as e:
            print(f"Error storing vector in Qdrant: {e}")
            return False

    def search_vectors(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filter_dict: dict[str, Any] | None = None,
    ) -> list[tuple[str, float, dict[str, Any]]]:
        """Search for similar vectors."""
        try:
            # Validate embedding dimension
            if len(query_embedding) != self.dimension:
                print(
                    f"Error: Query embedding dimension {len(query_embedding)} doesn't match collection dimension {self.dimension}"
                )
                return []

            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=filter_dict,
            )

            return [
                (str(result.id), result.score, result.payload)
                for result in results
            ]

        except Exception as e:
            print(f"Error searching in Qdrant: {e}")
            return []

    def get_vector(self, vector_id: str) -> tuple[list[float], dict[str, Any]] | None:
        """Retrieve a specific vector by ID."""
        try:
            results = self.client.retrieve(
                collection_name=self.collection_name, ids=[vector_id], with_vectors=True
            )
            if results:
                result = results[0]
                return (result.vector, result.payload)
            return None

        except Exception as e:
            print(f"Error retrieving vector from Qdrant: {e}")
            return None

    def delete_vector(self, vector_id: str) -> bool:
        """Delete a vector by ID."""
        try:
            self.client.delete(collection_name=self.collection_name, points_selector=[vector_id])
            return True

        except Exception as e:
            print(f"Error deleting vector from Qdrant: {e}")
            return False

    def get_stats(self) -> dict[str, Any]:
        """Get collection statistics."""
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return {
                "points_count": collection_info.points_count,
                "segments_count": collection_info.segments_count,
                "disk_data_size": collection_info.disk_data_size,
                "ram_data_size": collection_info.ram_data_size,
                "config": {
                    "dimension": collection_info.config.params.vectors.size,
                    "distance": collection_info.config.params.vectors.distance.name,
                },
            }
        except Exception as e:
            return {"error": str(e)}

    def cleanup(self) -> bool:
        """Clean up resources (delete collection if it exists)."""
        try:
            if self._collection_exists():
                return self._delete_collection()
            return True
        except Exception as e:
            print(f"Error during cleanup: {e}")
            return False


# Convenience functions
def create_qdrant_store(
    collection_name: str = "hacs_vectors", dimension: int = 1536, **kwargs
) -> QdrantVectorStore:
    """Create a Qdrant vector store."""
    return QdrantVectorStore(collection_name=collection_name, dimension=dimension, **kwargs)


def create_test_qdrant_store() -> QdrantVectorStore:
    """Create a test Qdrant store with in-memory client."""
    import time

    test_collection_name = f"test_hacs_{int(time.time())}"

    return QdrantVectorStore(
        collection_name=test_collection_name,
        dimension=1536,
        create_if_not_exists=True,
        delete_if_exists=True,
    )


def create_cloud_qdrant_store(
    url: str, api_key: str, collection_name: str = "hacs_vectors", dimension: int = 1536
) -> QdrantVectorStore:
    """Create a Qdrant Cloud vector store."""
    return QdrantVectorStore(
        url=url,
        api_key=api_key,
        collection_name=collection_name,
        dimension=dimension,
        create_if_not_exists=True,
    )