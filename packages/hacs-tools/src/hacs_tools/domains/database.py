"""
HACS Database Tools - Records CRUD vs Registry Definitions

This domain provides tools for data persistence and retrieval. There are two
distinct sub-areas that this module exposes clearly:

1) Records CRUD (filled resource records):
   - Operate on domain schemas like hacs_core, hacs_clinical, hacs_agents
   - Save/read/update/delete typed resources (or generic JSONB where needed)

2) Registry Definitions (resource definitions + metadata):
   - Operate on hacs_registry schema via the resource registry facade
   - Register/list/get/update resource definitions and their lifecycle

Additionally, this module provides vector search helpers and DB admin utilities.
"""

import logging
import os
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from hacs_models import HACSResult, BaseResource
from hacs_core import Actor
from hacs_models import get_model_registry
from hacs_persistence.adapter import PostgreSQLAdapter, create_postgres_adapter
from hacs_persistence.migrations import run_migration, get_migration_status
from hacs_utils.vector_ops import (
    store_embedding, vector_similarity_search, vector_hybrid_search,
    get_vector_collection_stats
)
from hacs_utils.preferences import merge_preferences
# Tool domain: database - Persistence and registry operations

logger = logging.getLogger(__name__)
from hacs_registry.plugin_discovery import register_tool


async def save_resource(
    resource: Dict[str, Any],
    as_typed: bool = True,
    schema: Optional[str] = None,
    index_semantic: bool = False
) -> HACSResult:
    """
    Save a HACS resource to the database using typed tables or generic JSONB storage.
    
    Args:
        resource: Dictionary representation of the resource to save
        as_typed: If True, use typed table; if False, use generic JSONB storage
        schema: Optional schema name override (defaults to appropriate schema)
        index_semantic: If True, create semantic embeddings for search
        
    Returns:
        HACSResult with saved resource ID and type
    """
    try:
        # Get resource type and validate
        resource_type = resource.get("resource_type")
        if not resource_type:
            return HACSResult(
                success=False,
                message="Save failed",
                error="Resource missing 'resource_type' field"
            )
        
        # Create adapter
        adapter = await create_postgres_adapter()
        
        # Instantiate resource object
        model_registry = get_model_registry()
        resource_class = model_registry.get(resource_type, BaseResource)
        instance = resource_class(**resource)
        
        # Create actor for audit
        actor = Actor(name="hacs_tools")
        
        if as_typed:
            # Use typed table via granular adapter
            try:
                from hacs_persistence.granular_adapter import save_typed_resource
                saved = await save_typed_resource(
                    instance, 
                    schema_name=schema or _get_default_schema(resource_type)
                )
            except ImportError:
                # Fallback to generic adapter
                logger.warning("Typed adapter not available, using generic storage")
                saved = await adapter.save(instance, actor)
        else:
            # Use generic JSONB storage
            saved = await adapter.save(instance, actor)
        
        # Optional semantic indexing
        if index_semantic:
            try:
                from hacs_utils.semantic_index import index_resource
                await index_resource(saved)
                logger.info(f"Created semantic index for {resource_type} {saved.id}")
            except Exception as e:
                logger.warning(f"Semantic indexing failed: {e}")
        
        return HACSResult(
            success=True,
            message=f"Successfully saved {resource_type}",
            data={
                "id": saved.id,
                "resource_type": saved.resource_type,
                "storage_type": "typed" if as_typed else "generic",
                "schema": schema or _get_default_schema(resource_type)
            }
        )
        
    except Exception as e:
        return HACSResult(
            success=False,
            message=f"Failed to save resource",
            error=str(e)
        )


async def read_resource(
    resource_type: str,
    resource_id: str,
    as_typed: bool = True,
    schema: Optional[str] = None
) -> HACSResult:
    """
    Read a HACS resource from the database.
    
    Args:
        resource_type: The HACS resource type
        resource_id: The resource ID to retrieve
        as_typed: If True, use typed table; if False, use generic storage
        schema: Optional schema name override
        
    Returns:
        HACSResult with the retrieved resource
    """
    try:
        # Create adapter
        adapter = await create_postgres_adapter()
        
        if as_typed:
            # Use typed table via granular adapter
            try:
                from hacs_persistence.granular_adapter import read_typed_resource
                resource = await read_typed_resource(
                    resource_type,
                    resource_id,
                    schema_name=schema or _get_default_schema(resource_type)
                )
            except ImportError:
                # Fallback to generic adapter
                logger.warning("Typed adapter not available, using generic storage")
                resource = await adapter.read(resource_id)
        else:
            # Use generic storage
            resource = await adapter.read(resource_id)
        
        if not resource:
            return HACSResult(
                success=False,
                message=f"Resource not found",
                error=f"{resource_type} with ID {resource_id} not found"
            )
        
        return HACSResult(
            success=True,
            message=f"Successfully retrieved {resource_type}",
            data={"resource": resource.model_dump() if hasattr(resource, 'model_dump') else resource}
        )
        
    except Exception as e:
        return HACSResult(
            success=False,
            message=f"Failed to read resource",
            error=str(e)
        )


async def update_resource(
    resource_type: str,
    resource_id: str,
    patch: Dict[str, Any],
    as_typed: bool = True,
    schema: Optional[str] = None
) -> HACSResult:
    """
    Update a HACS resource with partial data.
    
    Args:
        resource_type: The HACS resource type
        resource_id: The resource ID to update
        patch: Dictionary of fields to update
        as_typed: If True, use typed table; if False, use generic storage
        schema: Optional schema name override
        
    Returns:
        HACSResult with the updated resource
    """
    try:
        # First read the existing resource
        read_result = await read_resource(resource_type, resource_id, as_typed, schema)
        if not read_result.success:
            return read_result
        
        # Apply patch
        existing_data = read_result.data["resource"]
        existing_data.update(patch)
        
        # Save the updated resource
        save_result = await save_resource(existing_data, as_typed, schema)
        
        if save_result.success:
            return HACSResult(
                success=True,
                message=f"Successfully updated {resource_type}",
                data={"resource": existing_data}
            )
        else:
            return save_result
            
    except Exception as e:
        return HACSResult(
            success=False,
            message=f"Failed to update resource",
            error=str(e)
        )


async def delete_resource(
    resource_type: str,
    resource_id: str,
    schema: Optional[str] = None
) -> HACSResult:
    """
    Delete a HACS resource from the database.
    
    Args:
        resource_type: The HACS resource type
        resource_id: The resource ID to delete
        schema: Optional schema name override
        
    Returns:
        HACSResult with deletion status
    """
    try:
        # Create adapter
        adapter = await create_postgres_adapter()
        
        # Create actor for audit
        actor = Actor(name="hacs_tools")
        
        # Attempt deletion
        deleted = await adapter.delete(resource_id, actor)
        
        return HACSResult(
            success=True,
            message=f"Successfully deleted {resource_type} {resource_id}",
            data={"deleted": deleted, "resource_id": resource_id}
        )
        
    except Exception as e:
        return HACSResult(
            success=False,
            message=f"Failed to delete resource",
            error=str(e)
        )


async def register_model_version(
    resource_name: str,
    version: str,
    schema_def: Dict[str, Any],
    tags: Optional[List[str]] = None
) -> HACSResult:
    """
    Register a model version in the HACS registry.
    
    Args:
        resource_name: Name of the model to register
        version: Version string (e.g., "1.0.0")
        schema_def: JSON schema definition of the model
        tags: Optional tags for categorization
        
    Returns:
        HACSResult with registry ID
    """
    try:
        # This would typically use the hacs-registry persistence
        from hacs_registry import get_global_registry
        registry = get_global_registry()
        
        # Create model version entry
        model_version = {
            "resource_name": resource_name,
            "version": version,
            "schema_definition": schema_def,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        # For now, store as generic resource
        adapter = await create_postgres_adapter()
        actor = Actor(name="hacs_tools")
        
        # Create a BaseResource wrapper
        resource = BaseResource(
            resource_type="ModelVersion",
            **model_version
        )
        
        saved = await adapter.save(resource, actor)
        
        return HACSResult(
            success=True,
            message=f"Successfully registered model version {resource_name} v{version}",
            data={"registry_id": saved.id}
        )
        
    except Exception as e:
        return HACSResult(
            success=False,
            message=f"Failed to register model version",
            error=str(e)
        )


async def search_knowledge_items(
    query: str,
    top_k: int = 10,
    filters: Optional[Dict[str, Any]] = None,
    rerank: bool = False
) -> HACSResult:
    """
    Search knowledge items using vector similarity search with optional reranking.
    
    Args:
        query: Search query text
        top_k: Number of results to return
        filters: Optional filters to apply (e.g., {"source": "pubmed"})
        rerank: Whether to apply reranking for better relevance
        
    Returns:
        HACSResult with search results
    """
    try:
        # Use vector search utilities
        if rerank:
            search_result = await vector_hybrid_search(
                query_text=query,
                collection_name="knowledge_items",
                top_k=top_k,
                filters=filters
            )
        else:
            search_result = await vector_similarity_search(
                query_text=query,
                collection_name="knowledge_items", 
                top_k=top_k,
                filters=filters
            )
        
        if not search_result.success:
            return search_result
        
        # Format results for LLM consumption
        formatted_results = []
        for item in search_result.data.get("results", []):
            formatted_results.append({
                "id": item.get("id"),
                "score": item.get("score", 0.0),
                "content": item.get("content", ""),
                "metadata": item.get("metadata", {})
            })
        
        return HACSResult(
            success=True,
            message=f"Found {len(formatted_results)} knowledge items",
            data={"results": formatted_results}
        )
        
    except Exception as e:
        return HACSResult(
            success=False,
            message="Knowledge search failed",
            error=str(e)
        )


async def search_memories(
    actor_id: Optional[str] = None,
    query: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None,
    top_k: int = 10
) -> HACSResult:
    """
    Search agent memories using vector search and database filters.
    
    Args:
        actor_id: Optional actor ID to filter memories
        query: Optional semantic query for vector search
        filters: Optional additional filters (e.g., {"memory_type": "episodic"})
        top_k: Number of results to return
        
    Returns:
        HACSResult with memory search results
    """
    try:
        # Build comprehensive filters
        search_filters = filters or {}
        if actor_id:
            search_filters["actor_id"] = actor_id
        
        if query:
            # Use vector search for semantic matching
            search_result = await vector_similarity_search(
                query_text=query,
                collection_name="memory_blocks",
                top_k=top_k,
                filters=search_filters
            )
        else:
            # Direct database query for actor memories
            adapter = await create_postgres_adapter()
            
            # This would need proper memory table querying
            # For now, return empty results with filters applied
            search_result = HACSResult(
                success=True,
                data={"results": []}
            )
        
        if not search_result.success:
            return search_result
        
        memories = search_result.data.get("results", [])
        
        return HACSResult(
            success=True,
            message=f"Found {len(memories)} memories",
            data={"memories": memories}
        )
        
    except Exception as e:
        return HACSResult(
            success=False,
            message="Memory search failed",
            error=str(e)
        )


async def run_migrations(database_url: Optional[str] = None) -> HACSResult:
    """
    Run database migrations to ensure the schema is up to date.
    
    Args:
        database_url: Optional database URL override (uses environment if not provided)
        
    Returns:
        HACSResult with migration status
    """
    try:
        # Use provided URL or environment
        db_url = database_url or os.environ.get("DATABASE_URL")
        if not db_url:
            return HACSResult(
                success=False,
                message="Migration failed",
                error="No database URL provided and DATABASE_URL not set"
            )
        
        # Run migrations (handle bool or object return)
        migration_result = await run_migration(db_url)

        # Normalize to HACSResult fields
        if isinstance(migration_result, bool):
            return HACSResult(
                success=bool(migration_result),
                message="Migrations completed successfully" if migration_result else "Migrations reported failure",
                data={}
            )
        else:
            # Attempt to read common attributes; fall back gracefully
            success = getattr(migration_result, 'success', True)
            message = getattr(migration_result, 'message', 'Migrations finished')
            data = getattr(migration_result, 'data', None)
            return HACSResult(success=success, message=message, data=data)
        
    except Exception as e:
        return HACSResult(
            success=False,
            message="Migration failed",
            error=str(e)
        )


async def get_db_status(database_url: Optional[str] = None) -> HACSResult:
    """
    Get database connection status and migration state.
    
    Args:
        database_url: Optional database URL override
        
    Returns:
        HACSResult with database status information
    """
    try:
        # Use provided URL or environment
        db_url = database_url or os.environ.get("DATABASE_URL")
        if not db_url:
            return HACSResult(
                success=False,
                message="Status check failed",
                error="No database URL provided and DATABASE_URL not set"
            )
        
        # Check migration status
        migration_status = await get_migration_status(db_url)
        
        # Test connection
        try:
            adapter = await create_postgres_adapter(database_url=db_url)
            connection_status = "connected"
        except Exception as e:
            connection_status = f"failed: {str(e)}"
        
        return HACSResult(
            success=True,
            message="Database status retrieved",
            data={
                "connection_status": connection_status,
                "migration_status": migration_status,
                "database_url_configured": bool(db_url)
            }
        )
        
    except Exception as e:
        return HACSResult(
            success=False,
            message="Status check failed",
            error=str(e)
        )


def _get_default_schema(resource_type: str) -> str:
    """Get the default schema for a resource type."""
    # Map resource types to appropriate schemas
    clinical_types = {
        "Condition", "MedicationRequest", "Procedure", "Immunization",
        "DiagnosticReport", "MedicationStatement", "Practitioner",
        "Appointment", "CarePlan", "CareTeam", "NutritionOrder",
        "PlanDefinition", "ActivityDefinition", "Library", "EvidenceVariable"
    }
    
    core_types = {
        "Patient", "Observation", "Encounter", "Organization",
        "OrganizationContact", "OrganizationQualification"
    }
    
    if resource_type in clinical_types:
        return "hacs_clinical"
    elif resource_type in core_types:
        return "hacs_core"
    elif resource_type in {"ModelVersion"}:
        return "hacs_registry"
    elif resource_type in {"AgentMessage", "MemoryBlock", "ActorSession"}:
        return "hacs_agents"
    else:
        return "hacs_core"  # Default fallback


# -------------------------------
# Convenience aliases (records CRUD)
# -------------------------------

async def save_record(
    resource: Dict[str, Any],
    as_typed: bool = True,
    schema: Optional[str] = None,
    index_semantic: bool = False
) -> HACSResult:
    """Alias for save_resource for clarity that this persists filled records."""
    return await save_resource(resource, as_typed=as_typed, schema=schema, index_semantic=index_semantic)


async def read_record(
    resource_type: str,
    resource_id: str,
    as_typed: bool = True,
    schema: Optional[str] = None
) -> HACSResult:
    """Alias for read_resource for clarity that this reads filled records."""
    return await read_resource(resource_type, resource_id, as_typed=as_typed, schema=schema)


async def update_record(
    resource_type: str,
    resource_id: str,
    patch: Dict[str, Any],
    as_typed: bool = True,
    schema: Optional[str] = None
) -> HACSResult:
    """Alias for update_resource for clarity that this updates filled records."""
    return await update_resource(resource_type, resource_id, patch, as_typed=as_typed, schema=schema)


async def delete_record(
    resource_type: str,
    resource_id: str,
    schema: Optional[str] = None
) -> HACSResult:
    """Alias for delete_resource for clarity that this deletes filled records."""
    return await delete_resource(resource_type, resource_id, schema=schema)


# ---------------------------------------------
# Database reset utility (DANGER: drops schemas)
# ---------------------------------------------

async def reset_schemas(
    schemas: Optional[List[str]] = None,
    *,
    confirm: bool = False,
    database_url: Optional[str] = None,
) -> HACSResult:
    """
    Drop one or more HACS schemas and all contained objects, then they can be recreated by run_migrations.

    Safety: requires confirm=True to run.
    Default schemas: [hacs_core, hacs_clinical, hacs_registry, hacs_agents, hacs_admin, hacs_audit]
    """
    if not confirm:
        return HACSResult(success=False, message="Reset aborted: pass confirm=True to proceed")

    db_url = database_url or os.environ.get("DATABASE_URL")
    if not db_url:
        return HACSResult(success=False, message="Reset failed", error="No database URL provided and DATABASE_URL not set")

    target_schemas = schemas or [
        "hacs_core",
        "hacs_clinical",
        "hacs_registry",
        "hacs_agents",
        "hacs_admin",
        "hacs_audit",
    ]

    dropped: List[str] = []
    errors: Dict[str, str] = {}

    try:
        # Prefer synchronous psycopg for simple DDL
        try:
            import psycopg
            with psycopg.connect(db_url) as conn:
                conn.autocommit = True
                with conn.cursor() as cur:
                    for sch in target_schemas:
                        try:
                            cur.execute(f'DROP SCHEMA IF EXISTS "{sch}" CASCADE;')
                            dropped.append(sch)
                        except Exception as se:
                            errors[sch] = str(se)
        except ImportError as e:
            return HACSResult(success=False, message="Reset failed", error=f"psycopg not available: {e}")

        success = len(errors) == 0
        return HACSResult(
            success=success,
            message=("Schemas dropped" if success else "Schemas dropped with errors"),
            data={"dropped": dropped, "errors": errors}
        )
    except Exception as e:
        return HACSResult(success=False, message="Reset failed", error=str(e))


# ---------------------------------------------
# Registry Definitions (hacs_registry schema)
# ---------------------------------------------

@register_tool(
    name="register_resource_definition",
    domain="database",
    version="1.0.0",
    description="Register a resource definition (class + metadata) in the HACS registry",
    tags=["definitions", "registry", "resource", "document"]
)
def register_resource_definition(
    resource_type: str,
    name: str,
    version: str,
    description: str,
    category: str,
    tags: Optional[List[str]] = None,
    instance_data: Optional[Dict[str, Any]] = None,
    actor_id: Optional[str] = None,
) -> HACSResult:
    """
    Register a resource definition (class + metadata) in the HACS registry.
    Distinct from CRUD for filled records in hacs_core/hacs_clinical.
    """
    try:
        from hacs_registry.resource_registry import (
            register_hacs_resource,
            ResourceCategory,
        )
        from hacs_models import get_model_registry

        model_cls = get_model_registry().get(resource_type)
        if not model_cls:
            return HACSResult(success=False, message=f"Unknown resource type: {resource_type}")

        # Map category string to enum
        try:
            category_enum = ResourceCategory(category)
        except Exception:
            mapping = {c.value: c for c in ResourceCategory}
            category_enum = mapping.get(category.lower(), ResourceCategory.CUSTOM)

        registered = register_hacs_resource(
            resource_class=model_cls,
            name=name,
            version=version,
            description=description,
            category=category_enum,
            actor_id=actor_id,
            tags=tags or [],
        )

        if instance_data:
            # Attach a default instance payload to the definition wrapper
            registered.resource_instance = instance_data

        return HACSResult(
            success=True,
            message=f"Registered definition {registered.registry_id}",
            data={
                "registry_id": registered.registry_id,
                "resource_class": registered.resource_class,
                "metadata": registered.metadata.__dict__,
            }
        )
    except Exception as e:
        return HACSResult(success=False, message="Failed to register resource definition", error=str(e))


def get_resource_definition(registry_id: str) -> HACSResult:
    """Fetch a resource definition and metadata from the registry."""
    try:
        from hacs_registry.resource_registry import get_global_registry
        rr = get_global_registry().get_resource(registry_id)
        if not rr:
            return HACSResult(success=False, message="Registry item not found", error="not_found")
        return HACSResult(success=True, message="Definition retrieved", data={
            "registry_id": registry_id,
            "resource_class": rr.resource_class,
            "metadata": rr.metadata.__dict__,
            "resource_instance": rr.resource_instance,
        })
    except Exception as e:
        return HACSResult(success=False, message="Failed to get definition", error=str(e))


def list_resource_definitions(
    category: Optional[str] = None,
    resource_class: Optional[str] = None,
    status: Optional[str] = None,
) -> HACSResult:
    """List resource definitions with optional filters."""
    try:
        from hacs_registry.resource_registry import get_global_registry, ResourceCategory, ResourceStatus
        reg = get_global_registry()
        cat_enum = ResourceCategory(category) if category else None
        status_enum = ResourceStatus(status) if status else None
        results = reg.list_resources(category=cat_enum, resource_class=resource_class, status=status_enum)
        items = []
        for r in results:
            items.append({
                "registry_id": r.registry_id,
                "resource_class": r.resource_class,
                "metadata": r.metadata.__dict__,
            })
        return HACSResult(success=True, message=f"Found {len(items)} definitions", data={"items": items})
    except Exception as e:
        return HACSResult(success=False, message="Failed to list definitions", error=str(e))


def update_resource_definition_status(registry_id: str, new_status: str, reason: Optional[str] = None) -> HACSResult:
    """Update lifecycle status of a resource definition in the registry."""
    try:
        from hacs_registry.resource_registry import get_global_registry, ResourceStatus
        reg = get_global_registry()
        rr = reg.get_resource(registry_id)
        if not rr:
            return HACSResult(success=False, message="Registry item not found")
        try:
            status_enum = ResourceStatus(new_status)
        except Exception:
            return HACSResult(success=False, message=f"Unknown status: {new_status}")
        rr.update_status(status_enum, reason or "")
        return HACSResult(success=True, message="Status updated", data={"registry_id": registry_id, "status": rr.metadata.status.value})
    except Exception as e:
        return HACSResult(success=False, message="Failed to update status", error=str(e))


# ---------------------------------------------
# Preferences (records in hacs_agents or registry-backed)
# ---------------------------------------------

async def save_preference(preference: Dict[str, Any]) -> HACSResult:
    """Persist an ActorPreference record (schema defaults to hacs_agents)."""
    try:
        pref = {"resource_type": "ActorPreference", **preference}
        return await save_record(pref, as_typed=True, schema="hacs_agents")
    except Exception as e:
        return HACSResult(success=False, message="Failed to save preference", error=str(e))


async def read_preferences(actor_id: str, limit: int = 200) -> HACSResult:
    """Read ActorPreference records for an actor. Requires adapter.search; returns raw list."""
    try:
        adapter = await create_postgres_adapter()
        from hacs_models import Actor, ActorPreference
        prefs = await adapter.search(ActorPreference, Actor(name="pref-reader"), filters={"actor_id": actor_id}, limit=limit)
        data = [p.model_dump() if hasattr(p, "model_dump") else p for p in (prefs or [])]
        return HACSResult(success=True, message=f"Found {len(data)} preferences", data={"preferences": data})
    except Exception as e:
        return HACSResult(success=False, message="Failed to read preferences", error=str(e))


async def list_preferences(actor_id: str, *, organization_id: Optional[str] = None, workflow_id: Optional[str] = None, agent_id: Optional[str] = None, tool_name: Optional[str] = None, session_id: Optional[str] = None, in_memory: Optional[List[Dict[str, Any]]] = None) -> HACSResult:
    """Return effective preferences and raw list (DB + in-memory)."""
    try:
        in_memory = in_memory or []
        adapter = await create_postgres_adapter()
        effective, merged = await merge_preferences(
            actor_id=actor_id,
            organization_id=organization_id,
            workflow_id=workflow_id,
            agent_id=agent_id,
            tool_name=tool_name,
            session_id=session_id,
            in_memory_preferences=in_memory,
            db_adapter=adapter,
        )
        raw = [p.model_dump() if hasattr(p, "model_dump") else p for p in merged]
        return HACSResult(success=True, message="Resolved preferences", data={"effective": effective, "preferences": raw})
    except Exception as e:
        return HACSResult(success=False, message="Failed to list preferences", error=str(e))


# ---------------------------------------------
# Evidence (knowledge items; vector-backed)
# ---------------------------------------------

async def search_evidence(query: str, top_k: int = 10, filters: Optional[Dict[str, Any]] = None, rerank: bool = False) -> HACSResult:
    """Semantic search for evidence (registry knowledge_items)."""
    try:
        if rerank:
            res = await vector_hybrid_search(query_text=query, collection_name="knowledge_items", top_k=top_k, filters=filters)
        else:
            res = await vector_similarity_search(query_text=query, collection_name="knowledge_items", top_k=top_k, filters=filters)
        if not res.success:
            return res
        return HACSResult(success=True, message="Evidence search results", data=res.data)
    except Exception as e:
        return HACSResult(success=False, message="Evidence search failed", error=str(e))
# Export canonical tool names (without _tool suffix)
__all__ = [
    "save_resource",
    "read_resource", 
    "update_resource",
    "delete_resource",
    # Records CRUD aliases
    "save_record",
    "read_record",
    "update_record",
    "delete_record",
    # Registry definition ops
    "register_resource_definition",
    "get_resource_definition",
    "list_resource_definitions",
    "update_resource_definition_status",
    # Preferences
    "save_preference",
    "read_preferences",
    "list_preferences",
    # Evidence
    "search_evidence",
    "register_model_version",
    "search_knowledge_items",
    "search_memories",
    "run_migrations",
    "get_db_status"
]
