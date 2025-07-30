"""
PostgreSQL Schema Management for HACS Resources

This module provides comprehensive schema management for creating dedicated
tables for each HACS resource type with proper relational structure.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class HACSSchemaManager:
    """
    Manages PostgreSQL schemas for HACS resources with dedicated tables
    for each resource type providing better performance and relational structure.
    """

    def __init__(self, schema_name: str = "public"):
        self.schema_name = schema_name
        self.resource_schemas = {
            "Patient": self._get_patient_schema(),
            "Observation": self._get_observation_schema(),
            "Encounter": self._get_encounter_schema(),
            "AgentMessage": self._get_agent_message_schema(),
            "Memory": self._get_memory_schema(),
            "KnowledgeItem": self._get_knowledge_item_schema(),
            "ScratchpadEntry": self._get_scratchpad_entry_schema(),
            "ContextSummary": self._get_context_summary_schema(),
        }

    def _get_patient_schema(self) -> dict[str, Any]:
        """Define the Patient table schema."""
        return {
            "table_name": "patients",
            "columns": {
                # Base resource fields
                "id": "TEXT PRIMARY KEY",
                "resource_type": "TEXT NOT NULL DEFAULT 'Patient'",
                "created_at": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
                "updated_at": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
                "created_by": "TEXT",
                "updated_by": "TEXT",
                # Name fields
                "given_names": "TEXT[]",  # Array for multiple given names
                "family_name": "TEXT",
                "full_name": "TEXT",
                "name_prefix": "TEXT[]",  # Array for titles
                "name_suffix": "TEXT[]",  # Array for suffixes
                # Demographics
                "gender": "TEXT",
                "birth_date": "DATE",
                "age": "INTEGER",
                "deceased": "BOOLEAN DEFAULT FALSE",
                "deceased_date": "DATE",
                # Contact information (simplified/extracted)
                "primary_phone": "TEXT",
                "primary_email": "TEXT",
                # Complex structured data as JSONB
                "identifiers": "JSONB DEFAULT '[]'::jsonb",
                "telecom": "JSONB DEFAULT '[]'::jsonb",
                "address": "JSONB DEFAULT '[]'::jsonb",
                "contact": "JSONB DEFAULT '[]'::jsonb",
                "communication": "JSONB DEFAULT '[]'::jsonb",
                "general_practitioner": "JSONB DEFAULT '[]'::jsonb",
                "managing_organization": "TEXT",
                # Agent-specific fields
                "agent_context": "JSONB DEFAULT '{}'::jsonb",
                "memory_references": "TEXT[]",
                "evidence_references": "TEXT[]",
                # Photos and attachments
                "photo": "JSONB DEFAULT '[]'::jsonb",
                # Active status
                "active": "BOOLEAN DEFAULT TRUE",
                # Full resource data (for complex queries and migration)
                "full_resource": "JSONB NOT NULL",
            },
            "indexes": [
                "CREATE INDEX IF NOT EXISTS idx_patients_family_name ON {schema}.patients(family_name)",
                "CREATE INDEX IF NOT EXISTS idx_patients_full_name ON {schema}.patients(full_name)",
                "CREATE INDEX IF NOT EXISTS idx_patients_birth_date ON {schema}.patients(birth_date)",
                "CREATE INDEX IF NOT EXISTS idx_patients_gender ON {schema}.patients(gender)",
                "CREATE INDEX IF NOT EXISTS idx_patients_email ON {schema}.patients(primary_email)",
                "CREATE INDEX IF NOT EXISTS idx_patients_phone ON {schema}.patients(primary_phone)",
                "CREATE INDEX IF NOT EXISTS idx_patients_active ON {schema}.patients(active)",
                "CREATE INDEX IF NOT EXISTS idx_patients_identifiers_gin ON {schema}.patients USING GIN (identifiers)",
                "CREATE INDEX IF NOT EXISTS idx_patients_full_resource_gin ON {schema}.patients USING GIN (full_resource)",
                "CREATE INDEX IF NOT EXISTS idx_patients_created_at ON {schema}.patients(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_patients_updated_at ON {schema}.patients(updated_at)",
            ],
        }

    def _get_observation_schema(self) -> dict[str, Any]:
        """Define the Observation table schema."""
        return {
            "table_name": "observations",
            "columns": {
                # Base resource fields
                "id": "TEXT PRIMARY KEY",
                "resource_type": "TEXT NOT NULL DEFAULT 'Observation'",
                "created_at": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
                "updated_at": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
                "created_by": "TEXT",
                "updated_by": "TEXT",
                # Core observation fields
                "status": "TEXT NOT NULL DEFAULT 'final'",
                "subject": "TEXT NOT NULL",  # Patient reference
                "encounter": "TEXT",  # Encounter reference
                # Observation type and coding
                "code_text": "TEXT",  # Simple code description
                "code": "JSONB",  # Full coded value
                "category": "JSONB DEFAULT '[]'::jsonb",
                # Timing
                "effective_datetime": "TIMESTAMP WITH TIME ZONE",
                "effective_period": "JSONB",
                "issued": "TIMESTAMP WITH TIME ZONE",
                # Values (simplified extracted fields)
                "value_numeric": "DECIMAL",
                "value_string": "TEXT",
                "value_boolean": "BOOLEAN",
                "value_integer": "INTEGER",
                "unit": "TEXT",
                # Interpretations (simplified)
                "interpretation_text": "TEXT",
                "note_text": "TEXT",
                "body_site_text": "TEXT",
                # Complex structured data as JSONB
                "value_quantity": "JSONB",
                "value_codeable_concept": "JSONB",
                "value_range": "JSONB",
                "interpretation": "JSONB DEFAULT '[]'::jsonb",
                "note": "JSONB DEFAULT '[]'::jsonb",
                "body_site": "JSONB",
                "method": "JSONB",
                "reference_range": "JSONB DEFAULT '[]'::jsonb",
                "component": "JSONB DEFAULT '[]'::jsonb",
                # References
                "specimen": "TEXT",
                "device": "TEXT",
                "performer": "TEXT[]",
                "has_member": "TEXT[]",
                "derived_from": "TEXT[]",
                # Agent-specific fields
                "evidence_references": "TEXT[]",
                "agent_context": "JSONB DEFAULT '{}'::jsonb",
                # Full resource data
                "full_resource": "JSONB NOT NULL",
            },
            "indexes": [
                "CREATE INDEX IF NOT EXISTS idx_observations_subject ON {schema}.observations(subject)",
                "CREATE INDEX IF NOT EXISTS idx_observations_encounter ON {schema}.observations(encounter)",
                "CREATE INDEX IF NOT EXISTS idx_observations_status ON {schema}.observations(status)",
                "CREATE INDEX IF NOT EXISTS idx_observations_code_text ON {schema}.observations(code_text)",
                "CREATE INDEX IF NOT EXISTS idx_observations_effective_datetime ON {schema}.observations(effective_datetime)",
                "CREATE INDEX IF NOT EXISTS idx_observations_value_numeric ON {schema}.observations(value_numeric)",
                "CREATE INDEX IF NOT EXISTS idx_observations_unit ON {schema}.observations(unit)",
                "CREATE INDEX IF NOT EXISTS idx_observations_interpretation_text ON {schema}.observations(interpretation_text)",
                "CREATE INDEX IF NOT EXISTS idx_observations_code_gin ON {schema}.observations USING GIN (code)",
                "CREATE INDEX IF NOT EXISTS idx_observations_full_resource_gin ON {schema}.observations USING GIN (full_resource)",
                "CREATE INDEX IF NOT EXISTS idx_observations_created_at ON {schema}.observations(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_observations_updated_at ON {schema}.observations(updated_at)",
                # Performance indexes for common queries
                "CREATE INDEX IF NOT EXISTS idx_observations_subject_datetime ON {schema}.observations(subject, effective_datetime)",
                "CREATE INDEX IF NOT EXISTS idx_observations_subject_code_text ON {schema}.observations(subject, code_text)",
            ],
        }

    def _get_encounter_schema(self) -> dict[str, Any]:
        """Define the Encounter table schema."""
        return {
            "table_name": "encounters",
            "columns": {
                # Base resource fields
                "id": "TEXT PRIMARY KEY",
                "resource_type": "TEXT NOT NULL DEFAULT 'Encounter'",
                "created_at": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
                "updated_at": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
                "created_by": "TEXT",
                "updated_by": "TEXT",
                # Core encounter fields
                "status": "TEXT NOT NULL",
                "class": "TEXT NOT NULL",  # AMB, EMER, IMP, etc.
                "subject": "TEXT NOT NULL",  # Patient reference
                # Timing
                "period_start": "TIMESTAMP WITH TIME ZONE",
                "period_end": "TIMESTAMP WITH TIME ZONE",
                "length_value": "DECIMAL",
                "length_unit": "TEXT",
                # Complex structured data as JSONB
                "type": "JSONB DEFAULT '[]'::jsonb",
                "priority": "JSONB",
                "participants": "JSONB DEFAULT '[]'::jsonb",
                "period": "JSONB NOT NULL",
                "length": "JSONB",
                "reason_code": "JSONB DEFAULT '[]'::jsonb",
                "reason_reference": "TEXT[]",
                "diagnosis": "JSONB DEFAULT '[]'::jsonb",
                "account": "TEXT[]",
                "hospitalization": "JSONB",
                "location": "JSONB DEFAULT '[]'::jsonb",
                "service_provider": "TEXT",
                # Agent-specific fields
                "agent_context": "JSONB DEFAULT '{}'::jsonb",
                "memory_references": "TEXT[]",
                "evidence_references": "TEXT[]",
                # Full resource data
                "full_resource": "JSONB NOT NULL",
            },
            "indexes": [
                "CREATE INDEX IF NOT EXISTS idx_encounters_subject ON {schema}.encounters(subject)",
                "CREATE INDEX IF NOT EXISTS idx_encounters_status ON {schema}.encounters(status)",
                "CREATE INDEX IF NOT EXISTS idx_encounters_class ON {schema}.encounters(class)",
                "CREATE INDEX IF NOT EXISTS idx_encounters_period_start ON {schema}.encounters(period_start)",
                "CREATE INDEX IF NOT EXISTS idx_encounters_period_end ON {schema}.encounters(period_end)",
                "CREATE INDEX IF NOT EXISTS idx_encounters_service_provider ON {schema}.encounters(service_provider)",
                "CREATE INDEX IF NOT EXISTS idx_encounters_participants_gin ON {schema}.encounters USING GIN (participants)",
                "CREATE INDEX IF NOT EXISTS idx_encounters_reason_code_gin ON {schema}.encounters USING GIN (reason_code)",
                "CREATE INDEX IF NOT EXISTS idx_encounters_full_resource_gin ON {schema}.encounters USING GIN (full_resource)",
                "CREATE INDEX IF NOT EXISTS idx_encounters_created_at ON {schema}.encounters(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_encounters_updated_at ON {schema}.encounters(updated_at)",
                # Performance indexes for common queries
                "CREATE INDEX IF NOT EXISTS idx_encounters_subject_period ON {schema}.encounters(subject, period_start, period_end)",
                "CREATE INDEX IF NOT EXISTS idx_encounters_status_class ON {schema}.encounters(status, class)",
            ],
        }

    def _get_agent_message_schema(self) -> dict[str, Any]:
        """Define the AgentMessage table schema."""
        return {
            "table_name": "agent_messages",
            "columns": {
                # Base resource fields
                "id": "TEXT PRIMARY KEY",
                "resource_type": "TEXT NOT NULL DEFAULT 'AgentMessage'",
                "created_at": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
                "updated_at": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
                "created_by": "TEXT",
                "updated_by": "TEXT",
                # Core message fields
                "role": "TEXT NOT NULL",
                "content": "TEXT NOT NULL",
                "message_type": "TEXT NOT NULL DEFAULT 'response'",
                "priority": "TEXT NOT NULL DEFAULT 'normal'",
                # Message threading
                "parent_message_id": "TEXT",
                "in_reply_to": "TEXT",
                "thread_id": "TEXT",
                "summary": "TEXT",
                # Relationships
                "related_to": "TEXT[]",
                # Agent-specific fields
                "memory_handles": "TEXT[]",
                "evidence_references": "TEXT[]",
                "confidence_score": "DECIMAL DEFAULT 0.8",
                # Complex structured data as JSONB
                "provenance": "JSONB DEFAULT '{}'::jsonb",
                "tool_calls": "JSONB DEFAULT '[]'::jsonb",
                "reasoning_chain": "JSONB DEFAULT '[]'::jsonb",
                "metadata": "JSONB DEFAULT '{}'::jsonb",
                "attachments": "JSONB DEFAULT '[]'::jsonb",
                "annotations": "JSONB DEFAULT '[]'::jsonb",
                # Embedding and vectorization
                "content_hash": "TEXT",  # For deduplication
                # Performance and routing
                "processed": "BOOLEAN DEFAULT FALSE",
                "routed_to": "TEXT[]",
                "acknowledgments": "JSONB DEFAULT '[]'::jsonb",
                # Full resource data
                "full_resource": "JSONB NOT NULL",
            },
            "indexes": [
                "CREATE INDEX IF NOT EXISTS idx_agent_messages_role ON {schema}.agent_messages(role)",
                "CREATE INDEX IF NOT EXISTS idx_agent_messages_message_type ON {schema}.agent_messages(message_type)",
                "CREATE INDEX IF NOT EXISTS idx_agent_messages_priority ON {schema}.agent_messages(priority)",
                "CREATE INDEX IF NOT EXISTS idx_agent_messages_thread_id ON {schema}.agent_messages(thread_id)",
                "CREATE INDEX IF NOT EXISTS idx_agent_messages_parent_message_id ON {schema}.agent_messages(parent_message_id)",
                "CREATE INDEX IF NOT EXISTS idx_agent_messages_in_reply_to ON {schema}.agent_messages(in_reply_to)",
                "CREATE INDEX IF NOT EXISTS idx_agent_messages_confidence_score ON {schema}.agent_messages(confidence_score)",
                "CREATE INDEX IF NOT EXISTS idx_agent_messages_processed ON {schema}.agent_messages(processed)",
                "CREATE INDEX IF NOT EXISTS idx_agent_messages_content_hash ON {schema}.agent_messages(content_hash)",
                "CREATE INDEX IF NOT EXISTS idx_agent_messages_content_text ON {schema}.agent_messages USING GIN (to_tsvector('english', content))",  # Full-text search
                "CREATE INDEX IF NOT EXISTS idx_agent_messages_related_to_gin ON {schema}.agent_messages USING GIN (related_to)",
                "CREATE INDEX IF NOT EXISTS idx_agent_messages_memory_handles_gin ON {schema}.agent_messages USING GIN (memory_handles)",
                "CREATE INDEX IF NOT EXISTS idx_agent_messages_tool_calls_gin ON {schema}.agent_messages USING GIN (tool_calls)",
                "CREATE INDEX IF NOT EXISTS idx_agent_messages_full_resource_gin ON {schema}.agent_messages USING GIN (full_resource)",
                "CREATE INDEX IF NOT EXISTS idx_agent_messages_created_at ON {schema}.agent_messages(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_agent_messages_updated_at ON {schema}.agent_messages(updated_at)",
                # Performance indexes for common queries
                "CREATE INDEX IF NOT EXISTS idx_agent_messages_thread_created ON {schema}.agent_messages(thread_id, created_at)",
                "CREATE INDEX IF NOT EXISTS idx_agent_messages_role_type ON {schema}.agent_messages(role, message_type)",
            ],
        }

    def _get_memory_schema(self) -> dict[str, Any]:
        """Define the Memory table schema for long-term agent memory."""
        return {
            "table_name": "memories",
            "columns": {
                # Base resource fields
                "id": "TEXT PRIMARY KEY",
                "resource_type": "TEXT NOT NULL DEFAULT 'Memory'",
                "created_at": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
                "updated_at": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
                "created_by": "TEXT",
                "updated_by": "TEXT",
                # Memory-specific fields
                "memory_type": "TEXT NOT NULL",  # semantic, episodic, procedural
                "content": "TEXT NOT NULL",
                "actor_id": "TEXT",
                "importance": "DECIMAL(3,2) DEFAULT 0.5",  # 0.0 to 1.0
                "last_accessed": "TIMESTAMP WITH TIME ZONE",
                # Complex data as JSONB
                "metadata": "JSONB DEFAULT '{}'",
                # Full resource preservation
                "full_resource": "JSONB NOT NULL",
            },
            "indexes": [
                "CREATE INDEX IF NOT EXISTS idx_memories_actor_id ON {schema}.memories (actor_id)",
                "CREATE INDEX IF NOT EXISTS idx_memories_memory_type ON {schema}.memories (memory_type)",
                "CREATE INDEX IF NOT EXISTS idx_memories_importance ON {schema}.memories (importance DESC)",
                "CREATE INDEX IF NOT EXISTS idx_memories_last_accessed ON {schema}.memories (last_accessed DESC)",
                "CREATE INDEX IF NOT EXISTS idx_memories_content_gin ON {schema}.memories USING GIN (to_tsvector('english', content))",
                "CREATE INDEX IF NOT EXISTS idx_memories_metadata_gin ON {schema}.memories USING GIN (metadata)",
                "CREATE INDEX IF NOT EXISTS idx_memories_full_resource_gin ON {schema}.memories USING GIN (full_resource)",
            ],
        }

    def _get_knowledge_item_schema(self) -> dict[str, Any]:
        """Define the KnowledgeItem table schema for RAG knowledge base."""
        return {
            "table_name": "knowledge_items",
            "columns": {
                # Base resource fields
                "id": "TEXT PRIMARY KEY",
                "resource_type": "TEXT NOT NULL DEFAULT 'KnowledgeItem'",
                "created_at": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
                "updated_at": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
                "created_by": "TEXT",
                "updated_by": "TEXT",
                # Knowledge-specific fields
                "content": "TEXT NOT NULL",
                "source": "TEXT",
                "content_hash": "TEXT",  # For deduplication
                # Vector embedding (pgvector support enabled)
                "embedding": "vector(1536)",  # Default OpenAI text-embedding-3-small dimensions
                # Complex data as JSONB
                "metadata": "JSONB DEFAULT '{}'",
                # Full resource preservation
                "full_resource": "JSONB NOT NULL",
            },
            "indexes": [
                "CREATE INDEX IF NOT EXISTS idx_knowledge_items_source ON {schema}.knowledge_items (source)",
                "CREATE INDEX IF NOT EXISTS idx_knowledge_items_content_hash ON {schema}.knowledge_items (content_hash)",
                "CREATE INDEX IF NOT EXISTS idx_knowledge_items_content_gin ON {schema}.knowledge_items USING GIN (to_tsvector('english', content))",
                "CREATE INDEX IF NOT EXISTS idx_knowledge_items_metadata_gin ON {schema}.knowledge_items USING GIN (metadata)",
                "CREATE INDEX IF NOT EXISTS idx_knowledge_items_full_resource_gin ON {schema}.knowledge_items USING GIN (full_resource)",
                # Vector similarity index (pgvector enabled)
                "CREATE INDEX IF NOT EXISTS idx_knowledge_items_embedding ON {schema}.knowledge_items USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)",
                # Alternative HNSW index for better performance (commented out - choose one)
                # "CREATE INDEX IF NOT EXISTS idx_knowledge_items_embedding_hnsw ON {schema}.knowledge_items USING hnsw (embedding vector_cosine_ops)",
            ],
        }

    def _get_scratchpad_entry_schema(self) -> dict[str, Any]:
        """Define the ScratchpadEntry table schema for agent working memory."""
        return {
            "table_name": "scratchpad_entries",
            "columns": {
                # Base resource fields
                "id": "TEXT PRIMARY KEY",
                "resource_type": "TEXT NOT NULL DEFAULT 'ScratchpadEntry'",
                "created_at": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
                "updated_at": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
                "created_by": "TEXT",
                "updated_by": "TEXT",
                # Scratchpad-specific fields
                "content": "TEXT NOT NULL",
                "actor_id": "TEXT",
                "session_id": "TEXT",
                # Complex data as JSONB
                "metadata": "JSONB DEFAULT '{}'",
                # Full resource preservation
                "full_resource": "JSONB NOT NULL",
            },
            "indexes": [
                "CREATE INDEX IF NOT EXISTS idx_scratchpad_entries_actor_id ON {schema}.scratchpad_entries (actor_id)",
                "CREATE INDEX IF NOT EXISTS idx_scratchpad_entries_session_id ON {schema}.scratchpad_entries (session_id)",
                "CREATE INDEX IF NOT EXISTS idx_scratchpad_entries_created_at ON {schema}.scratchpad_entries (created_at DESC)",
                "CREATE INDEX IF NOT EXISTS idx_scratchpad_entries_content_gin ON {schema}.scratchpad_entries USING GIN (to_tsvector('english', content))",
                "CREATE INDEX IF NOT EXISTS idx_scratchpad_entries_metadata_gin ON {schema}.scratchpad_entries USING GIN (metadata)",
                "CREATE INDEX IF NOT EXISTS idx_scratchpad_entries_full_resource_gin ON {schema}.scratchpad_entries USING GIN (full_resource)",
            ],
        }

    def _get_context_summary_schema(self) -> dict[str, Any]:
        """Define the ContextSummary table schema for compressed context storage."""
        return {
            "table_name": "context_summaries",
            "columns": {
                # Base resource fields
                "id": "TEXT PRIMARY KEY",
                "resource_type": "TEXT NOT NULL DEFAULT 'ContextSummary'",
                "created_at": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
                "updated_at": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
                "created_by": "TEXT",
                "updated_by": "TEXT",
                # Summary-specific fields
                "summary_content": "TEXT NOT NULL",
                "source_resource_ids": "TEXT[]",  # Array of source resource IDs
                "actor_id": "TEXT",
                # Complex data as JSONB
                "metadata": "JSONB DEFAULT '{}'",
                # Full resource preservation
                "full_resource": "JSONB NOT NULL",
            },
            "indexes": [
                "CREATE INDEX IF NOT EXISTS idx_context_summaries_actor_id ON {schema}.context_summaries (actor_id)",
                "CREATE INDEX IF NOT EXISTS idx_context_summaries_source_resource_ids ON {schema}.context_summaries USING GIN (source_resource_ids)",
                "CREATE INDEX IF NOT EXISTS idx_context_summaries_created_at ON {schema}.context_summaries (created_at DESC)",
                "CREATE INDEX IF NOT EXISTS idx_context_summaries_summary_content_gin ON {schema}.context_summaries USING GIN (to_tsvector('english', summary_content))",
                "CREATE INDEX IF NOT EXISTS idx_context_summaries_metadata_gin ON {schema}.context_summaries USING GIN (metadata)",
                "CREATE INDEX IF NOT EXISTS idx_context_summaries_full_resource_gin ON {schema}.context_summaries USING GIN (full_resource)",
            ],
        }

    def get_create_table_sql(self, resource_type: str) -> str:
        """Generate CREATE TABLE SQL for a specific resource type."""
        if resource_type not in self.resource_schemas:
            raise ValueError(f"Unknown resource type: {resource_type}")

        schema = self.resource_schemas[resource_type]
        table_name = schema["table_name"]
        columns = schema["columns"]

        # Build column definitions
        column_defs = []
        for col_name, col_type in columns.items():
            column_defs.append(f"    {col_name} {col_type}")

        columns_sql = ",\n".join(column_defs)
        sql = f"""CREATE TABLE IF NOT EXISTS {self.schema_name}.{table_name} (
{columns_sql}
);"""

        return sql

    def get_create_indexes_sql(self, resource_type: str) -> list[str]:
        """Generate CREATE INDEX SQL statements for a specific resource type."""
        if resource_type not in self.resource_schemas:
            raise ValueError(f"Unknown resource type: {resource_type}")

        schema = self.resource_schemas[resource_type]
        indexes = schema["indexes"]

        # Format indexes with schema name
        formatted_indexes = []
        for index_sql in indexes:
            formatted_sql = index_sql.format(schema=self.schema_name)
            formatted_indexes.append(formatted_sql)

        return formatted_indexes

    def get_all_create_statements(self) -> dict[str, dict[str, Any]]:
        """Generate all CREATE TABLE and INDEX statements for all resource types."""
        statements = {}

        for resource_type in self.resource_schemas.keys():
            statements[resource_type] = {
                "table": self.get_create_table_sql(resource_type),
                "indexes": self.get_create_indexes_sql(resource_type),
            }

        return statements

    def create_all_tables(self, cursor) -> None:
        """Create all tables and indexes using the provided database cursor."""
        logger.info(f"Creating HACS resource tables in schema '{self.schema_name}'")

        # Create schema if it doesn't exist
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {self.schema_name}")

        # Create tables
        for resource_type in self.resource_schemas.keys():
            logger.info(f"Creating table for {resource_type}")

            # Create table
            table_sql = self.get_create_table_sql(resource_type)
            cursor.execute(table_sql)

            # Create indexes
            index_sqls = self.get_create_indexes_sql(resource_type)
            for index_sql in index_sqls:
                try:
                    cursor.execute(index_sql)
                except Exception as e:
                    # Some indexes might fail (e.g., vector extension not available)
                    logger.warning(f"Failed to create index: {e}")
                    continue

        logger.info("All HACS resource tables created successfully")

    def get_table_name(self, resource_type: str) -> str:
        """Get the table name for a specific resource type."""
        if resource_type not in self.resource_schemas:
            raise ValueError(f"Unknown resource type: {resource_type}")
        return self.resource_schemas[resource_type]["table_name"]
