"""
HACS Persistence Adapter Tools

Thin adapters exposing persistence operations. No business logic.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from hacs_models import HACSResult, BaseResource
from hacs_core.tool_protocols import hacs_tool, ToolCategory


async def _get_adapter(database_url: Optional[str] = None):
    from hacs_persistence.adapter import create_postgres_adapter
    # create_postgres_adapter reads DATABASE_URL from settings; database_url optional override not wired yet
    return await create_postgres_adapter()


@hacs_tool(
    name="persist_hacs_resource",
    description="Persist a HACS resource using configured PostgreSQL adapter (async)",
    category=ToolCategory.ADMIN_OPERATIONS,
    domains=["persistence"]
)
async def persist_hacs_resource(
    actor_name: str,
    resource: Dict[str, Any],
    database_url: Optional[str] = None,
) -> HACSResult:
    try:
        adapter = await _get_adapter(database_url)
        # Lazy import to avoid tight coupling
        from hacs_models import get_model_registry
        registry = get_model_registry()
        model_name = resource.get("resource_type") or resource.get("resourceType")
        model_cls = registry.get(model_name)
        if model_cls is None:
            return HACSResult(success=False, message=f"Unknown model '{model_name}'", error="model_not_found", actor_id=actor_name)
        instance: BaseResource = model_cls(**resource)  # type: ignore[call-arg]
        # Minimal actor stub
        from hacs_models import Actor
        actor = Actor(name=actor_name)
        saved = await adapter.save(instance, actor)
        # Optional semantic indexing after persist
        try:
            from hacs_utils.semantic_index import index_resource
            # Use default vector store hook (if configured by caller via adapter or env)
            # Fire-and-forget: do not block on indexing failures
            await index_resource(saved)
        except Exception:
            pass
        return HACSResult(success=True, message="Resource persisted", data={"id": saved.id, "resource_type": saved.resource_type}, actor_id=actor_name)
    except Exception as e:
        return HACSResult(success=False, message="Persistence failed", error=str(e), actor_id=actor_name)


@hacs_tool(
    name="read_hacs_resource",
    description="Read a HACS resource by id and type (async)",
    category=ToolCategory.ADMIN_OPERATIONS,
    domains=["persistence"]
)
async def read_hacs_resource(
    actor_name: str,
    resource_type: str,
    resource_id: str,
    database_url: Optional[str] = None,
) -> HACSResult:
    try:
        adapter = await _get_adapter(database_url)
        from hacs_models import get_model_registry, Actor
        registry = get_model_registry()
        model_cls = registry.get(resource_type)
        if model_cls is None:
            return HACSResult(success=False, message=f"Unknown model '{resource_type}'", error="model_not_found", actor_id=actor_name)
        actor = Actor(name=actor_name)
        instance = await adapter.read(model_cls, resource_id, actor)
        return HACSResult(success=True, message="Resource read", data=instance.model_dump(), actor_id=actor_name)
    except Exception as e:
        return HACSResult(success=False, message="Read failed", error=str(e), actor_id=actor_name)


__all__ = [
    "persist_hacs_resource",
    "read_hacs_resource",
]


