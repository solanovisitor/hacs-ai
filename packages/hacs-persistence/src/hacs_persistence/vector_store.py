"""
HACS Vector Store with pgvector (Async - Simplified)

This module provides asynchronous vector database operations for HACS using PostgreSQL with the pgvector extension.
Uses direct async connections for simplicity and reliability.
"""
import json
import logging
from datetime import datetime
from typing import Any

import numpy as np
import psycopg
from pgvector.psycopg import register_vector_async
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)

class HACSVectorStore:
    """
    Asynchronous vector store implementation using PostgreSQL with pgvector extension.
    Uses direct async connections for reliability and simplicity.
    """

    def __init__(
        self,
        database_url: str,
        schema_name: str = "hacs_registry",
        table_name: str = "knowledge_items",
        embedding_dimension: int = 1536
    ):
        self.database_url = database_url
        self.schema_name = schema_name
        self.table_name = table_name
        self.embedding_dimension = embedding_dimension
        self._connection = None

        logger.info(f"HACSVectorStore (Async) configured for {schema_name}.{table_name}")

    async def connect(self):
        """Initialize the asynchronous connection and verify pgvector support."""
        if self._connection:
            return

        try:
            self._connection = await psycopg.AsyncConnection.connect(
                self.database_url,
                autocommit=True
            )

            # Register vector types for async connection
            await register_vector_async(self._connection)

            await self._initialize_vector_support()
            logger.info("Async vector store connection established.")
        except Exception as e:
            logger.error(f"Failed to establish async vector store connection: {e}")
            raise RuntimeError(f"Async vector store initialization failed: {e}") from e

    async def disconnect(self):
        """Close the asynchronous connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None
            logger.info("Async vector store connection closed.")

    async def _initialize_vector_support(self):
        """Initialize pgvector support and verify table schema asynchronously."""
        try:
            # Ensure vector extension is enabled
            await self._connection.execute("CREATE EXTENSION IF NOT EXISTS vector;")

            # Verify table exists
            table_check_query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = %s AND table_name = %s
                );
            """

            async with self._connection.cursor() as cursor:
                await cursor.execute(table_check_query, (self.schema_name, self.table_name))
                table_exists = await cursor.fetchone()

                if not table_exists[0]:
                    logger.warning(f"Table {self.schema_name}.{self.table_name} does not exist")
                    return

                logger.info(f"Vector support initialized for {self.schema_name}.{self.table_name}")

        except Exception as e:
            logger.error(f"Failed to initialize vector support: {e}")
            raise

    async def store_embedding(
        self,
        content: str,
        embedding: list[float],
        metadata: dict[str, Any] | None = None,
        source: str | None = None
    ) -> str:
        """Store a single embedding with associated content and metadata asynchronously."""
        if not self._connection:
            await self.connect()

        try:
            embedding_id = f"knowledge_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(content) % 1000000:06d}"

            # Convert embedding to numpy array for pgvector
            embedding_array = np.array(embedding)

            insert_query = f"""
                INSERT INTO {self.schema_name}.{self.table_name}
                (id, title, content, metadata, source, embedding)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;
            """

            async with self._connection.cursor() as cursor:
                await cursor.execute(insert_query, (
                    embedding_id,
                    f"Embedding {embedding_id}",
                    content,
                    json.dumps(metadata or {}),
                    source,
                    embedding_array
                ))

                result = await cursor.fetchone()
                logger.info(f"Stored embedding with ID: {result[0]}")
                return result[0]

        except Exception as e:
            logger.error(f"Failed to store embedding: {e}")
            raise

    async def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        distance_metric: str = "cosine",
        metadata_filter: dict[str, Any] | None = None,
        source_filter: str | None = None
    ) -> list[dict[str, Any]]:
        """Perform similarity search using vector embeddings asynchronously."""
        if not self._connection:
            await self.connect()

        try:
            # Convert query embedding to numpy array
            query_array = np.array(query_embedding)

            # Choose distance operator based on metric
            distance_ops = {
                "cosine": "<=>",
                "l2": "<->",
                "inner_product": "<#>"
            }
            distance_op = distance_ops.get(distance_metric, "<=>")

            # Build query with optional filters
            base_query = f"""
                SELECT id, title, content, metadata, source,
                       embedding {distance_op} %s as distance
                FROM {self.schema_name}.{self.table_name}
            """

            where_conditions = []
            params = [query_array]

            if metadata_filter:
                for key, value in metadata_filter.items():
                    where_conditions.append(f"metadata->>{key} = %s")
                    params.append(str(value))

            if source_filter:
                where_conditions.append("source = %s")
                params.append(source_filter)

            if where_conditions:
                base_query += " WHERE " + " AND ".join(where_conditions)

            base_query += f" ORDER BY embedding {distance_op} %s LIMIT %s"
            params.extend([query_array, top_k])

            async with self._connection.cursor(row_factory=dict_row) as cursor:
                await cursor.execute(base_query, params)
                results = await cursor.fetchall()

                logger.info(f"Found {len(results)} similar embeddings")
                return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Failed to perform similarity search: {e}")
            raise

    async def get_collection_stats(self) -> dict[str, Any]:
        """Get statistics about the vector collection asynchronously."""
        if not self._connection:
            await self.connect()

        try:
            stats_query = f"""
                SELECT
                    COUNT(*) as total_embeddings,
                    COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as embeddings_with_vectors,
                    pg_size_pretty(pg_total_relation_size('{self.schema_name}.{self.table_name}')) as table_size
                FROM {self.schema_name}.{self.table_name}
            """

            async with self._connection.cursor(row_factory=dict_row) as cursor:
                await cursor.execute(stats_query)
                result = await cursor.fetchone()

                stats = dict(result) if result else {}
                stats.update({
                    "schema_name": self.schema_name,
                    "table_name": self.table_name,
                    "embedding_dimension": self.embedding_dimension,
                    "distance_metrics": ["cosine", "l2", "inner_product"]
                })

                logger.info(f"Collection stats: {stats['total_embeddings']} total embeddings")
                return stats

        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            raise

async def create_vector_store(
    database_url: str,
    schema_name: str = "hacs_registry",
    table_name: str = "knowledge_items",
    embedding_dimension: int = 1536
) -> HACSVectorStore:
    """Factory function to create and connect a HACSVectorStore instance."""
    vector_store = HACSVectorStore(
        database_url=database_url,
        schema_name=schema_name,
        table_name=table_name,
        embedding_dimension=embedding_dimension
    )
    await vector_store.connect()
    return vector_store
