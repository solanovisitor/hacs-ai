"""
PostgreSQL Adapter for HACS Persistence (Async)

This module provides a complete asynchronous implementation of the PersistenceProvider protocol
using psycopg (v3) for high-performance, non-blocking database operations.
"""

import json
import logging
from typing import Any

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from hacs_core import (
    Actor,
    AdapterNotFoundError,
    BaseAdapter,
    BaseResource,
    PersistenceProvider,
    get_settings,
)

logger = logging.getLogger(__name__)


class PostgreSQLAdapter(BaseAdapter, PersistenceProvider):
    """
    Asynchronous PostgreSQL adapter implementing the PersistenceProvider protocol using
    psycopg (v3) for non-blocking database operations.

    Features:
    - Async-native implementation with psycopg and psycopg_pool
    - Automatic, asynchronous table creation and schema management
    - Efficient JSONB storage for complex HACS resources
    - Robust error handling and logging
    - Built-in asynchronous connection pooling
    """

    def __init__(
        self,
        database_url: str,
        schema_name: str = "public",
        pool_size: int = 10,
    ):
        super().__init__(name="PostgreSQL (Async)", version="2.0.0")

        self.database_url = database_url
        self.schema_name = schema_name
        self.pool_size = pool_size
        self.pool: AsyncConnectionPool = None

        logger.info(f"PostgreSQLAdapter (Async) configured for schema '{schema_name}'")

    async def connect(self):
        """Initialize the asynchronous connection pool and database tables."""
        if self.pool:
            return

        try:
            self.pool = AsyncConnectionPool(
                conninfo=self.database_url,
                min_size=2,
                max_size=self.pool_size,
                open=True,
                row_factory=dict_row,
            )
            await self.pool.wait()
            await self._initialize_tables()
            logger.info("Async connection pool established and tables initialized.")
        except Exception as e:
            logger.error(f"Failed to establish async connection pool: {e}")
            raise RuntimeError(f"Async database initialization failed: {e}") from e

    async def disconnect(self):
        """Close the asynchronous connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("Async connection pool closed.")

    async def _initialize_tables(self):
        """Initialize the HACS resources table asynchronously."""
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    create_table_sql = f"""
                    CREATE TABLE IF NOT EXISTS {self.schema_name}.hacs_resources (
                        id TEXT PRIMARY KEY,
                        resource_type TEXT NOT NULL,
                        data JSONB NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        created_by TEXT,
                        updated_by TEXT
                    );

                    CREATE INDEX IF NOT EXISTS idx_hacs_resources_type
                    ON {self.schema_name}.hacs_resources(resource_type);

                    CREATE INDEX IF NOT EXISTS idx_hacs_resources_created_at
                    ON {self.schema_name}.hacs_resources(created_at);

                    CREATE INDEX IF NOT EXISTS idx_hacs_resources_data_gin
                    ON {self.schema_name}.hacs_resources USING GIN (data);
                    """
                    await cursor.execute(create_table_sql)
                    logger.info("HACS resources table checked/created successfully")
        except Exception as e:
            logger.error(f"Failed to initialize tables: {e}")
            raise RuntimeError(f"Database initialization failed: {e}") from e

    async def save(self, resource: BaseResource, actor: Actor) -> BaseResource:
        """Save a new resource using async PostgreSQL insert/upsert."""
        await self.connect()
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    resource_data = resource.model_dump(mode="json")
                    insert_sql = f"""
                    INSERT INTO {self.schema_name}.hacs_resources
                    (id, resource_type, data, created_by, updated_by)
                    VALUES (%(id)s, %(resource_type)s, %(data)s, %(created_by)s, %(updated_by)s)
                    ON CONFLICT (id) DO UPDATE SET
                        data = EXCLUDED.data,
                        updated_at = NOW(),
                        updated_by = EXCLUDED.updated_by
                    """
                    await cursor.execute(
                        insert_sql,
                        {
                            "id": resource.id,
                            "resource_type": resource.resource_type,
                            "data": json.dumps(resource_data),
                            "created_by": actor.id,
                            "updated_by": actor.id,
                        },
                    )
                    logger.info(
                        f"Resource {resource.resource_type}/{resource.id} saved successfully"
                    )
                    return resource
        except Exception as e:
            logger.error(f"Failed to save resource {resource.id}: {e}")
            raise RuntimeError(f"Database error while saving resource: {e}") from e

    async def read(
        self, resource_type: type[BaseResource], resource_id: str, actor: Actor
    ) -> BaseResource:
        """Read a resource using async PostgreSQL select."""
        await self.connect()
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    select_sql = f"""
                    SELECT data FROM {self.schema_name}.hacs_resources
                    WHERE id = %(id)s AND resource_type = %(resource_type)s
                    """
                    await cursor.execute(
                        select_sql,
                        {"id": resource_id, "resource_type": resource_type.__name__},
                    )
                    result = await cursor.fetchone()

                    if not result:
                        raise ValueError(
                            f"Resource {resource_type.__name__}/{resource_id} not found"
                        )

                    resource_data = result["data"]
                    resource_instance = resource_type(**resource_data)
                    logger.info(
                        f"Resource {resource_type.__name__}/{resource_id} read successfully"
                    )
                    return resource_instance
        except Exception as e:
            logger.error(f"Failed to read resource {resource_id}: {e}")
            raise RuntimeError(f"Database error while reading resource: {e}") from e

    async def update(self, resource: BaseResource, actor: Actor) -> BaseResource:
        """Update an existing resource using async PostgreSQL update."""
        await self.connect()
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    resource_data = resource.model_dump(mode="json")
                    update_sql = f"""
                    UPDATE {self.schema_name}.hacs_resources
                    SET data = %(data)s, updated_at = NOW(), updated_by = %(updated_by)s
                    WHERE id = %(id)s AND resource_type = %(resource_type)s
                    """
                    await cursor.execute(
                        update_sql,
                        {
                            "data": json.dumps(resource_data),
                            "updated_by": actor.id,
                            "id": resource.id,
                            "resource_type": resource.resource_type,
                        },
                    )

                    if cursor.rowcount == 0:
                        raise ValueError(
                            f"Resource {resource.resource_type}/{resource.id} not found for update"
                        )
                    logger.info(
                        f"Resource {resource.resource_type}/{resource.id} updated successfully"
                    )
                    return resource
        except Exception as e:
            logger.error(f"Failed to update resource {resource.id}: {e}")
            raise RuntimeError(f"Database error while updating resource: {e}") from e

    async def delete(
        self, resource_type: type[BaseResource], resource_id: str, actor: Actor
    ) -> bool:
        """Delete a resource using async PostgreSQL delete."""
        await self.connect()
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    delete_sql = f"""
                    DELETE FROM {self.schema_name}.hacs_resources
                    WHERE id = %(id)s AND resource_type = %(resource_type)s
                    """
                    await cursor.execute(
                        delete_sql,
                        {"id": resource_id, "resource_type": resource_type.__name__},
                    )

                    if cursor.rowcount > 0:
                        logger.info(
                            f"Resource {resource_type.__name__}/{resource_id} deleted successfully"
                        )
                        return True
                    else:
                        logger.warning(
                            f"Resource {resource_type.__name__}/{resource_id} not found for deletion"
                        )
                        return False
        except Exception as e:
            logger.error(f"Failed to delete resource {resource_id}: {e}")
            raise RuntimeError(f"Database error while deleting resource: {e}") from e

    async def search(
        self,
        resource_type: type[BaseResource],
        actor: Actor,
        filters: dict[str, Any] | None = None,
        limit: int = 100,
    ) -> list[BaseResource]:
        """Search for resources using async PostgreSQL JSON queries."""
        await self.connect()
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    where_conditions = ["resource_type = %(resource_type)s"]
                    params = {"resource_type": resource_type.__name__, "limit": limit}

                    if filters:
                        for key, value in filters.items():
                            param_key = f"filter_{key}"
                            if key.endswith(("_gt", "_gte", "_lt", "_lte")):
                                field = key.rsplit("_", 1)[0]
                                op_map = {"_gt": ">", "_gte": ">=", "_lt": "<", "_lte": "<="}
                                op = op_map[key[len(field):]]
                                where_conditions.append(
                                    f"(data->>'{field}')::numeric {op} %({param_key})s"
                                )
                                params[param_key] = value
                            elif key.endswith("_like"):
                                field = key[:-5]
                                where_conditions.append(f"data->>'{field}' ILIKE %({param_key})s")
                                params[param_key] = f"%{value}%"
                            elif key.endswith("_in"):
                                field = key[:-3]
                                where_conditions.append(f"data->>'{field}' = ANY(%({param_key})s)")
                                params[param_key] = value
                            else:
                                where_conditions.append(f"data->>'{key}' = %({param_key})s")
                                params[param_key] = str(value)

                    where_clause = " AND ".join(where_conditions)
                    search_sql = f"""
                    SELECT data FROM {self.schema_name}.hacs_resources
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT %(limit)s
                    """

                    await cursor.execute(search_sql, params)
                    results = await cursor.fetchall()

                    resources = []
                    for result in results:
                        try:
                            resource_data = result["data"]
                            resource_instance = resource_type(**resource_data)
                            resources.append(resource_instance)
                        except (json.JSONDecodeError, TypeError) as e:
                            logger.warning(f"Skipping corrupted resource data: {e}")
                            continue

                    logger.info(
                        f"Search found {len(resources)} {resource_type.__name__} resources"
                    )
                    return resources
        except Exception as e:
            logger.error(f"Failed to search resources: {e}")
            raise RuntimeError(f"Database error while searching resources: {e}") from e

    async def health_check(self) -> bool:
        """Check the health of the PostgreSQL connection pool."""
        if not self.pool or self.pool.closed:
            return False
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT 1")
                    return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def get_database_stats(self) -> dict[str, Any]:
        """Get database statistics asynchronously."""
        await self.connect()
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    stats_sql = f"""
                    SELECT
                        resource_type,
                        COUNT(*) as count,
                        MIN(created_at) as earliest,
                        MAX(created_at) as latest
                    FROM {self.schema_name}.hacs_resources
                    GROUP BY resource_type
                    ORDER BY count DESC
                    """
                    await cursor.execute(stats_sql)
                    results = await cursor.fetchall()

                    stats = {
                        "total_resources": sum(row["count"] for row in results),
                        "connection_status": "healthy",
                        "adapter_version": self.version,
                        "resource_types": {
                            row["resource_type"]: {
                                "count": row["count"],
                                "earliest": row["earliest"].isoformat() if row["earliest"] else None,
                                "latest": row["latest"].isoformat() if row["latest"] else None,
                            }
                            for row in results
                        },
                    }
                    return stats
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {"error": str(e), "connection_status": "unhealthy"}


async def create_postgres_adapter() -> PostgreSQLAdapter:
    """Factory function to create and connect a PostgreSQLAdapter."""
    settings = get_settings()
    if not settings.postgres_enabled:
        raise AdapterNotFoundError(
            "PostgreSQL is not configured. Please set DATABASE_URL."
        )

    config = settings.get_postgres_config()
    database_url = config.get("database_url") or config.get("url")
    if not database_url:
        raise AdapterNotFoundError("No database URL found. Please set DATABASE_URL.")

    adapter = PostgreSQLAdapter(
        database_url=database_url,
        schema_name=config["schema_name"],
    )
    await adapter.connect()
    return adapter
