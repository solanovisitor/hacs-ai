from __future__ import annotations

from typing import Any, Dict, List


def get_tool_catalog() -> List[Dict[str, Any]]:
    """
    Build a catalog of all registered HACS tools with minimal metadata.
    Returns list of {name, description, category, domain, tags}.
    """
    try:
        from hacs_registry import get_global_tool_registry as get_global_registry
    except Exception:
        return []

    reg = get_global_registry()
    tools = reg.get_all_tools()
    catalog: List[Dict[str, Any]] = []
    for t in tools:
        catalog.append(
            {
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "domain": t.domain,
                "tags": list(getattr(t, "tags", []) or []),
            }
        )
    return catalog


def _compute_embedding_fallback(text: str, dim: int = 384) -> List[float]:
    import hashlib

    h = int(hashlib.md5(text.encode()).hexdigest(), 16)
    return [(h >> i) % 100 / 100.0 for i in range(dim)]


def embed_tool_catalog(
    vector_store: Any,
    *,
    collection_name: str = "hacs_tools",
    include_domain_tag: bool = True,
) -> List[str]:
    """
    Embed the current tool catalog into the provided vector_store.
    Supports common interfaces: add_vectors / upsert / add / store_vector.
    Returns list of embedding IDs.
    """
    catalog = get_tool_catalog()
    ids: List[str] = []
    for tool in catalog:
        name = tool["name"]
        desc = tool.get("description") or ""
        domain = tool.get("domain") or "general"
        text = f"{name}: {desc} [domain={domain}]"
        # generate embedding
        embedding = None
        if hasattr(vector_store, "generate_embedding"):
            try:
                embedding = vector_store.generate_embedding(text)
            except Exception:
                embedding = None
        if embedding is None:
            embedding = _compute_embedding_fallback(text)
        meta = {
            "resource_type": "HACSTool",
            "name": name,
            "domain": domain,
            "category": tool.get("category"),
            "tags": tool.get("tags", []),
            "collection": collection_name,
        }
        if include_domain_tag:
            meta.setdefault("tags", []).append(f"domain:{domain}")
        emb_id = f"tool:{name}"
        # store
        if hasattr(vector_store, "add_vectors"):
            vector_store.add_vectors([emb_id], [embedding], [meta])
        elif hasattr(vector_store, "upsert"):
            vector_store.upsert(vectors=[(emb_id, embedding, meta)])
        elif hasattr(vector_store, "add"):
            vector_store.add(
                collection_name=collection_name,
                points=[{"id": emb_id, "vector": embedding, "payload": meta}],
            )
        elif hasattr(vector_store, "store_vector"):
            vector_store.store_vector(emb_id, embedding, meta)
        else:
            # cannot store
            continue
        ids.append(emb_id)
    return ids


def select_tools_semantic(
    vector_store: Any,
    *,
    query: str,
    collection_name: str = "hacs_tools",
    k: int = 5,
) -> List[str]:
    """
    Return top-k tool names by semantic similarity.
    Expects the vector_store to have similarity_search; falls back to empty.
    """
    results = []
    if hasattr(vector_store, "similarity_search"):
        try:
            results = vector_store.similarity_search(query, k)
        except Exception:
            results = []
    tool_names: List[str] = []
    for r in results or []:
        meta = r.get("metadata", {})
        nm = meta.get("name") or r.get("name")
        if nm:
            tool_names.append(nm)
    return tool_names[:k]
