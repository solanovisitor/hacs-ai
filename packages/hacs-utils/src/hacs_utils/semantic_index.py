from __future__ import annotations

from typing import Any, Dict, List, Tuple

from hacs_models import BaseResource, DomainResource


def build_resource_document(resource: BaseResource) -> Tuple[str, Dict[str, Any]]:
    """
    Build a semantic content string and metadata for a HACS resource instance.
    The goal is to create a concise yet informative text for embedding.
    """
    parts: List[str] = []
    parts.append(f"ResourceType: {resource.resource_type}")
    parts.append(f"ResourceId: {resource.id}")

    # Prefer DomainResource text summary when available
    if isinstance(resource, DomainResource):
        try:
            summary = resource.summary()
            if summary:
                parts.append(f"Summary: {summary}")
        except Exception:
            pass

    # Descriptive schema for extra field context
    try:
        desc = resource.get_descriptive_schema()  # type: ignore[attr-defined]
        if isinstance(desc, dict):
            title = desc.get("title")
            if title:
                parts.append(f"Title: {title}")
            fields = desc.get("fields") or {}
            # Include a small set of field names to seed semantics
            if isinstance(fields, dict):
                field_names = ", ".join(list(fields.keys())[:25])
                if field_names:
                    parts.append(f"Fields: {field_names}")
    except Exception:
        pass

    # Include agent_context and selected properties if small
    try:
        dump = resource.model_dump()
        ac = dump.get("agent_context")
        if ac:
            parts.append(f"AgentContext: {str(ac)[:500]}")
    except Exception:
        pass

    content = "\n".join(parts)
    metadata = {
        "resource_type": resource.resource_type,
        "resource_id": resource.id,
        "collection": "hacs_resources",
        "content": content[:2000],
    }
    return content, metadata


def build_tool_documents() -> List[Dict[str, Any]]:
    """
    Build semantic docs for all registered tools: each doc has content + metadata.
    """
    try:
        from hacs_registry import get_global_tool_registry as get_global_registry
    except Exception:
        return []

    reg = get_global_registry()
    tools = reg.get_all_tools()
    docs: List[Dict[str, Any]] = []
    for t in tools:
        try:
            name = t.name
            desc = t.description or ""
            category = t.category or ""
            domain = t.domain or ""
            tags = ", ".join(t.tags or [])
            content = f"Tool: {name}\nCategory: {category}\nDomain: {domain}\nTags: {tags}\nDescription: {desc}"
            metadata = {
                "tool_name": name,
                "category": category,
                "domain": domain,
                "tags": list(t.tags or []),
                "collection": "hacs_tools",
            }
            docs.append({"content": content, "metadata": metadata})
        except Exception:
            continue
    return docs


async def index_resource(
    resource: BaseResource,
    *,
    vector_store: Any = None,
    collection_name: str = "hacs_resources",
    actor_name: str = "semantic-indexer",
) -> Dict[str, Any]:
    """
    Create and store an embedding for a resource instance.
    """
    from hacs_utils.vector_ops import store_embedding

    content, metadata = build_resource_document(resource)
    metadata = {**metadata, "collection": collection_name}
    result = store_embedding(
        actor_name=actor_name,
        content=content,
        collection_name=collection_name,
        metadata=metadata,
        vector_store=vector_store,
    )
    # Return minimal summary
    return {
        "success": result.success,
        "message": result.message,
        "search_results": result.search_results,
    }


async def index_tool_catalog(
    *,
    vector_store: Any = None,
    collection_name: str = "hacs_tools",
    actor_name: str = "semantic-indexer",
) -> List[str]:
    """
    Build an embedding catalog of all tools for semantic loadout.
    Returns list of embedding ids or tool names indexed.
    """
    from hacs_utils.vector_ops import store_embedding

    docs = build_tool_documents()
    ids: List[str] = []
    for d in docs:
        res = store_embedding(
            actor_name=actor_name,
            content=d["content"],
            collection_name=collection_name,
            metadata=d["metadata"],
            vector_store=vector_store,
        )
        if res and res.search_results:
            ids.append(res.search_results[0].get("embedding_id", ""))
    return ids


def semantic_tool_loadout(
    query: str,
    *,
    vector_store: Any = None,
    collection_name: str = "hacs_tools",
    limit: int = 5,
    actor_name: str = "semantic-indexer",
) -> List[str]:
    """
    Retrieve tool names semantically relevant to a query.
    """
    from hacs_utils.vector_ops import vector_similarity_search

    res = vector_similarity_search(
        actor_name=actor_name,
        query=query,
        collection_name=collection_name,
        limit=limit,
        vector_store=vector_store,
    )
    names: List[str] = []
    for r in res.search_results or []:
        meta = r.get("metadata", {})
        name = meta.get("tool_name")
        if name:
            names.append(name)
    return names


def semantic_resource_search(
    query: str,
    *,
    vector_store: Any = None,
    collection_name: str = "hacs_resources",
    limit: int = 10,
    actor_name: str = "semantic-indexer",
) -> List[Dict[str, Any]]:
    """
    Search resource embeddings and return resource references with metadata.
    """
    from hacs_utils.vector_ops import vector_similarity_search

    res = vector_similarity_search(
        actor_name=actor_name,
        query=query,
        collection_name=collection_name,
        limit=limit,
        vector_store=vector_store,
    )
    results: List[Dict[str, Any]] = []
    for r in res.search_results or []:
        meta = r.get("metadata", {})
        results.append(
            {
                "resource_type": meta.get("resource_type"),
                "resource_id": meta.get("resource_id"),
                "content": r.get("content"),
                "similarity_score": r.get("similarity_score"),
            }
        )
    return results
