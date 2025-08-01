"""
Resource Mapper for HACS PostgreSQL Integration

This module handles the conversion between HACS resources and the granular
PostgreSQL table structure, extracting key fields for relational queries
while preserving the full resource in JSONB.
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Any

from hacs_core import Actor, BaseResource

try:
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
except ImportError:
    # Fallback to hacs_core.models if hacs_models is not available
    try:
        from hacs_models import (
            AgentMessage,
            ContextSummary,
            Encounter,
            KnowledgeItem,
            Observation,
            Patient,
            ScratchpadEntry,
        )
        from hacs_models import (
            MemoryBlock as Memory,
        )
    except ImportError:
        # TODO: Implement proper model imports or create actual model definitions
        # The following models need proper implementations:
        class _PlaceholderModel:
            """Placeholder model - TODO: implement proper model definitions."""
            pass

        AgentMessage = _PlaceholderModel
        ContextSummary = _PlaceholderModel
        Encounter = _PlaceholderModel
        KnowledgeItem = _PlaceholderModel
        Memory = _PlaceholderModel
        Observation = _PlaceholderModel
        Patient = _PlaceholderModel
        ScratchpadEntry = _PlaceholderModel

logger = logging.getLogger(__name__)


class ResourceMapper:
    """
    Maps HACS resources to and from granular PostgreSQL table structures.

    This mapper extracts key fields for direct column storage while preserving
    the complete resource in JSONB for complex queries and future compatibility.
    """

    def __init__(self, schema_name: str = "public"):
        self.schema_name = schema_name

    def map_patient_to_columns(self, patient: Patient, actor: Actor) -> dict[str, Any]:
        """Map a Patient resource to database columns."""
        # Extract simple fields
        data = {
            "id": patient.id,
            "resource_type": patient.resource_type,
            "created_by": actor.id,
            "updated_by": actor.id,
            # Name fields
            "given_names": patient.given,
            "family_name": patient.family,
            "full_name": patient.full_name,
            "name_prefix": patient.prefix,
            "name_suffix": patient.suffix,
            # Demographics
            "gender": patient.gender
            if isinstance(patient.gender, str)
            else (patient.gender.value if patient.gender else None),
            "birth_date": patient.birth_date,
            "age": patient.age,
            "deceased": patient.deceased,
            "deceased_date": patient.deceased_date,
            # Contact (extract primary values)
            "primary_phone": patient.phone,
            "primary_email": patient.email,
            # Active status
            "active": getattr(patient, "active", True),
            # Complex fields as JSONB
            "identifiers": json.dumps(patient.identifiers)
            if patient.identifiers
            else "[]",
            "telecom": json.dumps(patient.telecom) if patient.telecom else "[]",
            "address": json.dumps(patient.address) if patient.address else "[]",
            "contact": json.dumps(getattr(patient, "contact", [])),
            "communication": json.dumps(getattr(patient, "communication", [])),
            "general_practitioner": json.dumps(
                getattr(patient, "general_practitioner", [])
            ),
            "managing_organization": getattr(patient, "managing_organization", None),
            "photo": json.dumps(getattr(patient, "photo", [])),
            # Agent-specific fields
            "agent_context": json.dumps(getattr(patient, "agent_context", {})),
            "memory_references": getattr(patient, "memory_references", []),
            "evidence_references": getattr(patient, "evidence_references", []),
            # Full resource for complex queries
            "full_resource": json.dumps(patient.model_dump(mode="json")),
        }

        return data

    def map_observation_to_columns(
        self, observation: Observation, actor: Actor
    ) -> dict[str, Any]:
        """Map an Observation resource to database columns."""
        data = {
            "id": observation.id,
            "resource_type": observation.resource_type,
            "created_by": actor.id,
            "updated_by": actor.id,
            # Core fields
            "status": observation.status
            if isinstance(observation.status, str)
            else (observation.status.value if observation.status else "final"),
            "subject": observation.subject,
            "encounter": observation.encounter,
            # Observation type
            "code_text": observation.code_text,
            "code": json.dumps(observation.code) if observation.code else None,
            "category": json.dumps(observation.category)
            if observation.category
            else "[]",
            # Timing
            "effective_datetime": observation.effective_datetime,
            "effective_period": json.dumps(observation.effective_period)
            if observation.effective_period
            else None,
            "issued": observation.issued,
            # Values (extracted)
            "value_numeric": observation.value_numeric,
            "value_string": observation.value_string,
            "value_boolean": observation.value_boolean,
            "value_integer": observation.value_integer,
            "unit": observation.unit,
            # Interpretations (extracted)
            "interpretation_text": observation.interpretation_text,
            "note_text": observation.note_text,
            "body_site_text": observation.body_site_text,
            # Complex values as JSONB
            "value_quantity": json.dumps(observation.value_quantity)
            if observation.value_quantity
            else None,
            "value_codeable_concept": json.dumps(observation.value_codeable_concept)
            if observation.value_codeable_concept
            else None,
            "value_range": json.dumps(observation.value_range)
            if observation.value_range
            else None,
            "interpretation": json.dumps(observation.interpretation)
            if observation.interpretation
            else "[]",
            "note": json.dumps(observation.note) if observation.note else "[]",
            "body_site": json.dumps(observation.body_site)
            if observation.body_site
            else None,
            "method": json.dumps(observation.method) if observation.method else None,
            "reference_range": json.dumps(observation.reference_range)
            if observation.reference_range
            else "[]",
            "component": json.dumps(observation.component)
            if observation.component
            else "[]",
            # References
            "specimen": observation.specimen,
            "device": observation.device,
            "performer": observation.performer,
            "has_member": observation.has_member,
            "derived_from": observation.derived_from,
            # Agent-specific fields
            "evidence_references": observation.evidence_references,
            "agent_context": json.dumps(observation.agent_context)
            if observation.agent_context
            else "{}",
            # Full resource
            "full_resource": json.dumps(observation.model_dump(mode="json")),
        }

        return data

    def map_encounter_to_columns(
        self, encounter: Encounter, actor: Actor
    ) -> dict[str, Any]:
        """Map an Encounter resource to database columns."""
        # Extract period start/end for easier querying
        period_start = None
        period_end = None
        if hasattr(encounter, "period") and encounter.period:
            if isinstance(encounter.period, dict):
                period_start = encounter.period.get("start")
                period_end = encounter.period.get("end")
                # Convert strings to datetime if needed
                if isinstance(period_start, str):
                    try:
                        period_start = datetime.fromisoformat(
                            period_start.replace("Z", "+00:00")
                        )
                    except (ValueError, TypeError):
                        period_start = None
                if isinstance(period_end, str):
                    try:
                        period_end = datetime.fromisoformat(
                            period_end.replace("Z", "+00:00")
                        )
                    except (ValueError, TypeError):
                        period_end = None

        # Extract length value and unit
        length_value = None
        length_unit = None
        if hasattr(encounter, "length") and encounter.length:
            if isinstance(encounter.length, dict):
                length_value = encounter.length.get("value")
                length_unit = encounter.length.get("unit")

        data = {
            "id": encounter.id,
            "resource_type": encounter.resource_type,
            "created_by": actor.id,
            "updated_by": actor.id,
            # Core fields
            "status": encounter.status.value if encounter.status else None,
            "class": encounter.class_fhir.value if encounter.class_fhir else None,
            "subject": encounter.subject,
            # Timing (extracted)
            "period_start": period_start,
            "period_end": period_end,
            "length_value": length_value,
            "length_unit": length_unit,
            # Complex fields as JSONB
            "type": json.dumps(encounter.type) if encounter.type else "[]",
            "priority": json.dumps(encounter.priority) if encounter.priority else None,
            "participants": json.dumps(encounter.participants)
            if encounter.participants
            else "[]",
            "period": json.dumps(encounter.period)
            if hasattr(encounter, "period") and encounter.period
            else "{}",
            "length": json.dumps(encounter.length)
            if hasattr(encounter, "length") and encounter.length
            else None,
            "reason_code": json.dumps(encounter.reason_code)
            if encounter.reason_code
            else "[]",
            "reason_reference": encounter.reason_reference,
            "diagnosis": json.dumps(getattr(encounter, "diagnosis", [])),
            "account": getattr(encounter, "account", []),
            "hospitalization": json.dumps(getattr(encounter, "hospitalization", None)),
            "location": json.dumps(getattr(encounter, "location", [])),
            "service_provider": getattr(encounter, "service_provider", None),
            # Agent-specific fields
            "agent_context": json.dumps(getattr(encounter, "agent_context", {})),
            "memory_references": getattr(encounter, "memory_references", []),
            "evidence_references": getattr(encounter, "evidence_references", []),
            # Full resource
            "full_resource": json.dumps(encounter.model_dump(mode="json")),
        }

        return data

    def map_agent_message_to_columns(
        self, message: AgentMessage, actor: Actor
    ) -> dict[str, Any]:
        """Map an AgentMessage resource to database columns."""
        # Generate content hash for deduplication
        content_hash = hashlib.sha256(message.content.encode("utf-8")).hexdigest()

        data = {
            "id": message.id,
            "resource_type": message.resource_type,
            "created_by": actor.id,
            "updated_by": actor.id,
            # Core message fields
            "role": message.role.value if message.role else None,
            "content": message.content,
            "message_type": message.message_type.value
            if message.message_type
            else "response",
            "priority": message.priority.value if message.priority else "normal",
            # Threading
            "parent_message_id": message.parent_message_id,
            "in_reply_to": message.in_reply_to,
            "thread_id": message.thread_id,
            "summary": message.summary,
            # Relationships
            "related_to": message.related_to,
            # Agent-specific fields
            "memory_handles": message.memory_handles,
            "evidence_references": message.evidence_references,
            "confidence_score": message.confidence_score,
            # Complex fields as JSONB
            "provenance": json.dumps(message.provenance)
            if message.provenance
            else "{}",
            "tool_calls": json.dumps(message.tool_calls)
            if message.tool_calls
            else "[]",
            "reasoning_chain": json.dumps(getattr(message, "reasoning_chain", [])),
            "metadata": json.dumps(getattr(message, "metadata", {})),
            "attachments": json.dumps(getattr(message, "attachments", [])),
            "annotations": json.dumps(getattr(message, "annotations", [])),
            # Performance fields
            "content_hash": content_hash,
            "processed": getattr(message, "processed", False),
            "routed_to": getattr(message, "routed_to", []),
            "acknowledgments": json.dumps(getattr(message, "acknowledgments", [])),
            # Full resource
            "full_resource": json.dumps(message.model_dump(mode="json")),
        }

        return data

    def map_memory_to_columns(self, memory: Memory, actor: Actor) -> dict[str, Any]:
        """Map a Memory resource to database columns."""
        data = {
            "id": memory.id,
            "resource_type": memory.resource_type,
            "created_by": actor.id,
            "updated_by": actor.id,
            # Memory-specific fields
            "memory_type": memory.memory_type.value
            if hasattr(memory.memory_type, "value")
            else memory.memory_type,
            "content": memory.content,
            "actor_id": memory.actor_id,
            "importance": memory.importance,
            "last_accessed": memory.last_accessed,
            # Complex data as JSONB
            "metadata": json.dumps(memory.metadata) if memory.metadata else "{}",
            # Full resource preservation
            "full_resource": json.dumps(memory.model_dump(mode="json")),
        }

        return data

    def map_knowledge_item_to_columns(
        self, knowledge_item: KnowledgeItem, actor: Actor
    ) -> dict[str, Any]:
        """Map a KnowledgeItem resource to database columns."""
        # Generate content hash for deduplication
        content_hash = hashlib.sha256(knowledge_item.content.encode()).hexdigest()

        data = {
            "id": knowledge_item.id,
            "resource_type": knowledge_item.resource_type,
            "created_by": actor.id,
            "updated_by": actor.id,
            # Knowledge-specific fields
            "content": knowledge_item.content,
            "source": knowledge_item.source,
            "content_hash": content_hash,
            # Complex data as JSONB
            "metadata": json.dumps(knowledge_item.metadata)
            if knowledge_item.metadata
            else "{}",
            # Full resource preservation
            "full_resource": json.dumps(knowledge_item.model_dump(mode="json")),
        }

        return data

    def map_scratchpad_entry_to_columns(
        self, scratchpad_entry: ScratchpadEntry, actor: Actor
    ) -> dict[str, Any]:
        """Map a ScratchpadEntry resource to database columns."""
        data = {
            "id": scratchpad_entry.id,
            "resource_type": scratchpad_entry.resource_type,
            "created_by": actor.id,
            "updated_by": actor.id,
            # Scratchpad-specific fields
            "content": scratchpad_entry.content,
            "actor_id": scratchpad_entry.actor_id,
            "session_id": scratchpad_entry.session_id,
            # Complex data as JSONB
            "metadata": json.dumps(scratchpad_entry.metadata)
            if scratchpad_entry.metadata
            else "{}",
            # Full resource preservation
            "full_resource": json.dumps(scratchpad_entry.model_dump(mode="json")),
        }

        return data

    def map_context_summary_to_columns(
        self, context_summary: ContextSummary, actor: Actor
    ) -> dict[str, Any]:
        """Map a ContextSummary resource to database columns."""
        data = {
            "id": context_summary.id,
            "resource_type": context_summary.resource_type,
            "created_by": actor.id,
            "updated_by": actor.id,
            # Summary-specific fields
            "summary_content": context_summary.summary_content,
            "source_resource_ids": context_summary.source_resource_ids,
            "actor_id": context_summary.actor_id,
            # Complex data as JSONB
            "metadata": json.dumps(context_summary.metadata)
            if context_summary.metadata
            else "{}",
            # Full resource preservation
            "full_resource": json.dumps(context_summary.model_dump(mode="json")),
        }

        return data

    def map_columns_to_resource(
        self, resource_type: str, row_data: dict[str, Any]
    ) -> BaseResource:
        """Convert database row data back to a HACS resource."""
        # Extract the full resource JSONB data
        if isinstance(row_data.get("full_resource"), str):
            full_data = json.loads(row_data["full_resource"])
        else:
            full_data = row_data.get("full_resource", {})

        # Map to appropriate resource type
        if resource_type == "Patient":
            return Patient(**full_data)
        elif resource_type == "Observation":
            return Observation(**full_data)
        elif resource_type == "Encounter":
            return Encounter(**full_data)
        elif resource_type == "AgentMessage":
            return AgentMessage(**full_data)
        else:
            raise ValueError(f"Unknown resource type: {resource_type}")

    def get_resource_mapper(self, resource_type: str):
        """Get the appropriate mapper function for a resource type."""
        mappers = {
            "Patient": self.map_patient_to_columns,
            "Observation": self.map_observation_to_columns,
            "Encounter": self.map_encounter_to_columns,
            "AgentMessage": self.map_agent_message_to_columns,
        }

        if resource_type not in mappers:
            raise ValueError(f"No mapper available for resource type: {resource_type}")

        return mappers[resource_type]

    def build_search_conditions(
        self, resource_type: str, filters: dict[str, Any]
    ) -> tuple[str, list[Any]]:
        """Build SQL WHERE conditions for search queries with granular fields."""
        conditions = []
        params = []

        for key, value in filters.items():
            if key.endswith("_gt"):
                field = key[:-3]
                # Map to appropriate column name
                column = self._map_filter_field_to_column(resource_type, field)
                if column:
                    conditions.append(f"{column} > %s")
                    params.append(value)
            elif key.endswith("_gte"):
                field = key[:-4]
                column = self._map_filter_field_to_column(resource_type, field)
                if column:
                    conditions.append(f"{column} >= %s")
                    params.append(value)
            elif key.endswith("_lt"):
                field = key[:-3]
                column = self._map_filter_field_to_column(resource_type, field)
                if column:
                    conditions.append(f"{column} < %s")
                    params.append(value)
            elif key.endswith("_lte"):
                field = key[:-4]
                column = self._map_filter_field_to_column(resource_type, field)
                if column:
                    conditions.append(f"{column} <= %s")
                    params.append(value)
            elif key.endswith("_like"):
                field = key[:-5]
                column = self._map_filter_field_to_column(resource_type, field)
                if column:
                    conditions.append(f"{column} ILIKE %s")
                    params.append(f"%{value}%")
            elif key.endswith("_in"):
                field = key[:-3]
                column = self._map_filter_field_to_column(resource_type, field)
                if column:
                    conditions.append(f"{column} = ANY(%s)")
                    params.append(value)
            else:
                # Exact match
                column = self._map_filter_field_to_column(resource_type, key)
                if column:
                    conditions.append(f"{column} = %s")
                    params.append(str(value))

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        return where_clause, params

    def _map_filter_field_to_column(self, resource_type: str, field: str) -> str | None:
        """Map a filter field to the appropriate database column."""
        # Define field mappings for each resource type
        mappings = {
            "Patient": {
                "name": "full_name",
                "family": "family_name",
                "given": "given_names",
                "gender": "gender",
                "age": "age",
                "birth_date": "birth_date",
                "phone": "primary_phone",
                "email": "primary_email",
                "active": "active",
            },
            "Observation": {
                "subject": "subject",
                "encounter": "encounter",
                "status": "status",
                "code_text": "code_text",
                "value_numeric": "value_numeric",
                "value_string": "value_string",
                "unit": "unit",
                "effective_datetime": "effective_datetime",
                "interpretation_text": "interpretation_text",
                "body_site_text": "body_site_text",
            },
            "Encounter": {
                "subject": "subject",
                "status": "status",
                "class": "class",
                "period_start": "period_start",
                "period_end": "period_end",
                "length_value": "length_value",
                "service_provider": "service_provider",
            },
            "AgentMessage": {
                "role": "role",
                "message_type": "message_type",
                "priority": "priority",
                "thread_id": "thread_id",
                "confidence_score": "confidence_score",
                "content": "content",
                "parent_message_id": "parent_message_id",
                "processed": "processed",
            },
        }

        resource_mapping = mappings.get(resource_type, {})
        return resource_mapping.get(
            field, field
        )  # Return field as-is if no mapping found
