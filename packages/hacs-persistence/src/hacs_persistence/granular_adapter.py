"""
Granular PostgreSQL Adapter for HACS Persistence

This module provides a comprehensive PostgreSQL adapter that creates dedicated
tables for each HACS resource type with proper relational structure and
high-performance queries while maintaining full FHIR compliance.
"""

import logging
from typing import Any

import psycopg2
import psycopg2.extras

from hacs_core import (
    Actor,
    AdapterNotFoundError,
    BaseAdapter,
    BaseResource,
    PersistenceProvider,
    get_settings,
)
from hacs_core.models import (
    AgentMessage,
    ContextSummary,
    Encounter,
    KnowledgeItem,
    Memory,
    Observation,
    Patient,
    ScratchpadEntry,
)

from .resource_mapper import ResourceMapper
from .schema import HACSSchemaManager

logger = logging.getLogger(__name__)


class GranularPostgreSQLAdapter(BaseAdapter, PersistenceProvider):
    """
    Granular PostgreSQL adapter with dedicated tables for each HACS resource type.

    Features:
    - Dedicated tables for Patient, Observation, Encounter, AgentMessage
    - Extracted key fields as columns for fast queries
    - Full resource preservation in JSONB for complex operations
    - Comprehensive indexing for high performance
    - Advanced search capabilities with relational and JSON queries
    """

    def __init__(
        self,
        database_url: str,
        schema_name: str = "public",
    ):
        super().__init__(name="GranularPostgreSQL", version="1.0.0")

        self.database_url = database_url
        self.schema_name = schema_name

        # Initialize schema manager and resource mapper
        self.schema_manager = HACSSchemaManager(schema_name)
        self.resource_mapper = ResourceMapper(schema_name)

        # Extract connection parameters from DATABASE_URL
        self.connection_params = self._extract_connection_params(database_url)

        # Initialize database tables with granular schema
        self._initialize_granular_tables()

        logger.info(f"GranularPostgreSQLAdapter initialized for schema '{schema_name}'")

    def _extract_connection_params(self, database_url: str) -> dict[str, str]:
        """Extract connection parameters from DATABASE_URL."""
        from urllib.parse import urlparse

        parsed = urlparse(database_url)
        return {
            "user": parsed.username,
            "password": parsed.password,
            "host": parsed.hostname,
            "port": str(parsed.port or 5432),
            "dbname": parsed.path.lstrip("/"),
        }

    def _get_connection(self):
        """Get a database connection using the extracted parameters."""
        return psycopg2.connect(**self.connection_params)

    def _initialize_granular_tables(self):
        """Initialize all HACS resource tables with granular schema."""
        try:
            with self._get_connection() as conn:
                conn.autocommit = True
                with conn.cursor() as cursor:
                    # Create all tables and indexes
                    self.schema_manager.create_all_tables(cursor)
                    logger.info(
                        "Granular HACS resource tables initialized successfully"
                    )

        except Exception as e:
            logger.error(f"Failed to initialize granular tables: {e}")
            raise RuntimeError(f"Database initialization failed: {e}") from e

    def _get_table_name(self, resource_type: str) -> str:
        """Get the table name for a given resource type."""
        table_mapping = {
            "Patient": "patients",
            "Observation": "observations",
            "Encounter": "encounters",
            "AgentMessage": "agent_messages",
            "Memory": "memories",
            "KnowledgeItem": "knowledge_items",
            "ScratchpadEntry": "scratchpad_entries",
            "ContextSummary": "context_summaries",
        }
        return table_mapping.get(resource_type, "hacs_resources")

    def save(self, resource: BaseResource, actor: Actor) -> BaseResource:
        """Save a resource using the appropriate granular table."""
        table_name = self._get_table_name(resource.resource_type)

        # Map resource to columns based on type
        if isinstance(resource, Patient):
            column_data = self.resource_mapper.map_patient_to_columns(resource, actor)
        elif isinstance(resource, Observation):
            column_data = self.resource_mapper.map_observation_to_columns(
                resource, actor
            )
        elif isinstance(resource, Encounter):
            column_data = self.resource_mapper.map_encounter_to_columns(resource, actor)
        elif isinstance(resource, AgentMessage):
            column_data = self.resource_mapper.map_agent_message_to_columns(
                resource, actor
            )
        elif isinstance(resource, Memory):
            column_data = self.resource_mapper.map_memory_to_columns(resource, actor)
        elif isinstance(resource, KnowledgeItem):
            column_data = self.resource_mapper.map_knowledge_item_to_columns(
                resource, actor
            )
        elif isinstance(resource, ScratchpadEntry):
            column_data = self.resource_mapper.map_scratchpad_entry_to_columns(
                resource, actor
            )
        elif isinstance(resource, ContextSummary):
            column_data = self.resource_mapper.map_context_summary_to_columns(
                resource, actor
            )
        else:
            raise ValueError(f"Unsupported resource type: {resource.resource_type}")

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Build INSERT/UPSERT SQL
                    columns = list(column_data.keys())
                    placeholders = ["%s"] * len(columns)
                    values = list(column_data.values())

                    # Create upsert query
                    insert_sql = f"""
                    INSERT INTO {self.schema_name}.{table_name}
                    ({", ".join(columns)})
                    VALUES ({", ".join(placeholders)})
                    ON CONFLICT (id) DO UPDATE SET
                        {", ".join([f"{col} = EXCLUDED.{col}" for col in columns if col != "id"])},
                        updated_at = NOW()
                    """

                    cursor.execute(insert_sql, values)
                    conn.commit()

                    logger.info(
                        f"Resource {resource.resource_type}/{resource.id} saved to {table_name}"
                    )
                    return resource

        except Exception as e:
            logger.error(f"Failed to save resource {resource.id}: {e}")
            raise RuntimeError(f"Database error while saving resource: {e}") from e

    def read(
        self, resource_type: type[BaseResource], resource_id: str, actor: Actor
    ) -> BaseResource:
        """Read a resource from the appropriate granular table."""
        try:
            with self._get_connection() as conn:
                with conn.cursor(
                    cursor_factory=psycopg2.extras.RealDictCursor
                ) as cursor:
                    # Get the appropriate table name
                    table_name = self.schema_manager.get_table_name(
                        resource_type.__name__
                    )

                    select_sql = f"""
                    SELECT * FROM {self.schema_name}.{table_name}
                    WHERE id = %s
                    """

                    cursor.execute(select_sql, (resource_id,))
                    result = cursor.fetchone()

                    if not result:
                        raise ValueError(
                            f"Resource {resource_type.__name__}/{resource_id} not found"
                        )

                    # Convert row data back to resource
                    resource_instance = self.resource_mapper.map_columns_to_resource(
                        resource_type.__name__, dict(result)
                    )

                    logger.info(
                        f"Resource {resource_type.__name__}/{resource_id} read from {table_name}"
                    )
                    return resource_instance

        except Exception as e:
            logger.error(f"Failed to read resource {resource_id}: {e}")
            raise RuntimeError(f"Database error while reading resource: {e}") from e

    def update(self, resource: BaseResource, actor: Actor) -> BaseResource:
        """Update an existing resource in the appropriate granular table."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Get the appropriate table name
                    table_name = self.schema_manager.get_table_name(
                        resource.resource_type
                    )

                    # Map resource to columns
                    mapper_func = self.resource_mapper.get_resource_mapper(
                        resource.resource_type
                    )
                    column_data = mapper_func(resource, actor)

                    # Build UPDATE SQL (exclude id and created fields)
                    update_columns = [
                        col
                        for col in column_data.keys()
                        if col not in ["id", "created_at", "created_by"]
                    ]
                    set_clauses = [f"{col} = %s" for col in update_columns]
                    values = [column_data[col] for col in update_columns]
                    values.append(resource.id)  # For WHERE clause

                    update_sql = f"""
                    UPDATE {self.schema_name}.{table_name}
                    SET {", ".join(set_clauses)}, updated_at = NOW()
                    WHERE id = %s
                    """

                    cursor.execute(update_sql, values)

                    if cursor.rowcount == 0:
                        raise ValueError(
                            f"Resource {resource.resource_type}/{resource.id} not found for update"
                        )

                    conn.commit()
                    logger.info(
                        f"Resource {resource.resource_type}/{resource.id} updated in {table_name}"
                    )
                    return resource

        except Exception as e:
            logger.error(f"Failed to update resource {resource.id}: {e}")
            raise RuntimeError(f"Database error while updating resource: {e}") from e

    def delete(
        self, resource_type: type[BaseResource], resource_id: str, actor: Actor
    ) -> bool:
        """Delete a resource from the appropriate granular table."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Get the appropriate table name
                    table_name = self.schema_manager.get_table_name(
                        resource_type.__name__
                    )

                    delete_sql = f"""
                    DELETE FROM {self.schema_name}.{table_name}
                    WHERE id = %s
                    """

                    cursor.execute(delete_sql, (resource_id,))

                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(
                            f"Resource {resource_type.__name__}/{resource_id} deleted from {table_name}"
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

    def search(
        self,
        resource_type: type[BaseResource],
        actor: Actor,
        filters: dict[str, Any] | None = None,
        limit: int = 100,
    ) -> list[BaseResource]:
        """Search for resources using granular table columns and advanced filtering."""
        try:
            with self._get_connection() as conn:
                with conn.cursor(
                    cursor_factory=psycopg2.extras.RealDictCursor
                ) as cursor:
                    # Get the appropriate table name
                    table_name = self.schema_manager.get_table_name(
                        resource_type.__name__
                    )

                    # Build search conditions using resource mapper
                    if filters:
                        where_clause, params = (
                            self.resource_mapper.build_search_conditions(
                                resource_type.__name__, filters
                            )
                        )
                    else:
                        where_clause = "1=1"
                        params = []

                    params.append(limit)

                    search_sql = f"""
                    SELECT * FROM {self.schema_name}.{table_name}
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT %s
                    """

                    cursor.execute(search_sql, params)
                    results = cursor.fetchall()

                    # Convert results back to resources
                    resources = []
                    for result in results:
                        try:
                            resource_instance = (
                                self.resource_mapper.map_columns_to_resource(
                                    resource_type.__name__, dict(result)
                                )
                            )
                            resources.append(resource_instance)
                        except Exception as e:
                            logger.warning(f"Skipping corrupted resource data: {e}")
                            continue

                    logger.info(
                        f"Search found {len(resources)} {resource_type.__name__} resources"
                    )
                    return resources

        except Exception as e:
            logger.error(f"Failed to search resources: {e}")
            raise RuntimeError(f"Database error while searching resources: {e}") from e

    def search_with_joins(
        self,
        primary_resource_type: type[BaseResource],
        join_conditions: list[dict[str, Any]],
        actor: Actor,
        filters: dict[str, Any] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Advanced search with JOINs across multiple resource tables.

        Example join_conditions:
        [
            {
                "resource_type": "Observation",
                "on": "patients.id = observations.subject",
                "fields": ["code_text", "value_numeric", "effective_datetime"]
            }
        ]
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor(
                    cursor_factory=psycopg2.extras.RealDictCursor
                ) as cursor:
                    # Get primary table
                    primary_table = self.schema_manager.get_table_name(
                        primary_resource_type.__name__
                    )

                    # Build JOIN clauses
                    join_clauses = []
                    select_fields = [f"{primary_table}.*"]

                    for join_condition in join_conditions:
                        join_resource_type = join_condition["resource_type"]
                        join_table = self.schema_manager.get_table_name(
                            join_resource_type
                        )
                        join_on = join_condition["on"]
                        join_fields = join_condition.get("fields", [])

                        join_clauses.append(
                            f"LEFT JOIN {self.schema_name}.{join_table} ON {join_on}"
                        )

                        # Add specific fields from joined table
                        for field in join_fields:
                            select_fields.append(
                                f"{join_table}.{field} AS {join_table}_{field}"
                            )

                    # Build WHERE clause
                    if filters:
                        where_clause, params = (
                            self.resource_mapper.build_search_conditions(
                                primary_resource_type.__name__, filters
                            )
                        )
                    else:
                        where_clause = "1=1"
                        params = []

                    params.append(limit)

                    # Complete query
                    search_sql = f"""
                    SELECT {", ".join(select_fields)}
                    FROM {self.schema_name}.{primary_table}
                    {" ".join(join_clauses)}
                    WHERE {where_clause}
                    ORDER BY {primary_table}.created_at DESC
                    LIMIT %s
                    """

                    cursor.execute(search_sql, params)
                    results = cursor.fetchall()

                    # Return raw results for complex joins
                    return [dict(result) for result in results]

        except Exception as e:
            logger.error(f"Failed to search with joins: {e}")
            raise RuntimeError(f"Database error while searching with joins: {e}") from e

    def get_resource_relationships(
        self, resource_type: type[BaseResource], resource_id: str, actor: Actor
    ) -> dict[str, list[dict[str, Any]]]:
        """Get related resources for a given resource using foreign key relationships."""
        try:
            relationships = {}

            if resource_type.__name__ == "Patient":
                # Get patient's observations
                from hacs_models import Observation

                observations = self.search(
                    Observation, actor, filters={"subject": resource_id}
                )
                relationships["observations"] = [
                    obs.model_dump(mode="json") for obs in observations
                ]

                # Get patient's encounters
                from hacs_models import Encounter

                encounters = self.search(
                    Encounter, actor, filters={"subject": resource_id}
                )
                relationships["encounters"] = [
                    enc.model_dump(mode="json") for enc in encounters
                ]

            elif resource_type.__name__ == "Encounter":
                # Get encounter's observations
                from hacs_models import Observation

                observations = self.search(
                    Observation, actor, filters={"encounter": resource_id}
                )
                relationships["observations"] = [
                    obs.model_dump(mode="json") for obs in observations
                ]

            return relationships

        except Exception as e:
            logger.error(f"Failed to get resource relationships: {e}")
            return {}

    def health_check(self) -> bool:
        """Check the health of the PostgreSQL connection and table structure."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Test basic connection
                    cursor.execute("SELECT 1")

                    # Verify all tables exist
                    for resource_type in [
                        "Patient",
                        "Observation",
                        "Encounter",
                        "AgentMessage",
                    ]:
                        table_name = self.schema_manager.get_table_name(resource_type)
                        cursor.execute(
                            """
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables
                                WHERE table_schema = %s AND table_name = %s
                            )
                        """,
                            (self.schema_name, table_name),
                        )

                        if not cursor.fetchone()[0]:
                            logger.error(f"Table {table_name} does not exist")
                            return False

                    return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def get_database_stats(self) -> dict[str, Any]:
        """Get comprehensive database statistics for all resource tables."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    stats = {
                        "connection_status": "healthy",
                        "adapter_version": self.version,
                        "schema_name": self.schema_name,
                        "resource_types": {},
                    }

                    total_resources = 0

                    # Get stats for each resource table
                    for resource_type in [
                        "Patient",
                        "Observation",
                        "Encounter",
                        "AgentMessage",
                    ]:
                        table_name = self.schema_manager.get_table_name(resource_type)

                        stats_sql = f"""
                        SELECT
                            COUNT(*) as count,
                            MIN(created_at) as earliest,
                            MAX(created_at) as latest,
                            MAX(updated_at) as last_updated
                        FROM {self.schema_name}.{table_name}
                        """

                        cursor.execute(stats_sql)
                        result = cursor.fetchone()

                        count, earliest, latest, last_updated = result
                        total_resources += count

                        stats["resource_types"][resource_type] = {
                            "table_name": table_name,
                            "count": count,
                            "earliest": earliest.isoformat() if earliest else None,
                            "latest": latest.isoformat() if latest else None,
                            "last_updated": last_updated.isoformat()
                            if last_updated
                            else None,
                        }

                    stats["total_resources"] = total_resources
                    return stats

        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {"error": str(e), "connection_status": "unhealthy"}


def create_granular_postgres_adapter() -> GranularPostgreSQLAdapter:
    """Factory function to create a GranularPostgreSQLAdapter from configuration."""
    settings = get_settings()

    if not settings.postgres_enabled:
        raise AdapterNotFoundError(
            "PostgreSQL is not configured. Please set DATABASE_URL."
        )

    config = settings.get_postgres_config()

    # Use DATABASE_URL if available, otherwise construct from individual components
    database_url = config.get("database_url") or config.get("url")

    if not database_url:
        raise AdapterNotFoundError("No database URL found. Please set DATABASE_URL.")

    return GranularPostgreSQLAdapter(
        database_url=database_url,
        schema_name=config["schema_name"],
    )
