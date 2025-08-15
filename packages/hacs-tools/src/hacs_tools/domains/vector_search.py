"""
DEPRECATED: Generic Vector Search Tools

This module remains as a thin compatibility shim. Prefer context-specific tools
such as `evidence_tools` (e.g., `index_evidence`, `check_evidence`).
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from hacs_core.tool_protocols import hacs_tool, ToolCategory
from hacs_models import VectorStoreResult, HACSResult
from hacs_utils.vector_ops import (
    store_embedding as _store_embedding,
    vector_similarity_search as _vector_similarity_search,
    vector_hybrid_search as _vector_hybrid_search,
    get_vector_collection_stats as _get_vector_collection_stats,
    optimize_vector_collection as _optimize_vector_collection,
)


@hacs_tool(
    name="store_embedding",
    description="[Deprecated] Store content as vector embedding. Prefer context-specific tools (e.g., index_evidence).",
    category=ToolCategory.VECTOR_SEARCH,
    domains=["general"]
)
def store_embedding(
    actor_name: str,
    content: str,
    collection_name: str = "healthcare_general",
    metadata: Optional[Dict[str, Any]] = None,
    clinical_context: Optional[str] = None,
    db_adapter: Any | None = None,
    vector_store: Any | None = None,
) -> VectorStoreResult:
    return _store_embedding(
        actor_name=actor_name,
        content=content,
        collection_name=collection_name,
        metadata=metadata,
        clinical_context=clinical_context,
        db_adapter=db_adapter,
        vector_store=vector_store,
    )


@hacs_tool(
    name="vector_similarity_search",
    description="[Deprecated] Semantic similarity search. Prefer context-specific tools.",
    category=ToolCategory.VECTOR_SEARCH,
    domains=["general"]
)
def vector_similarity_search(
    actor_name: str,
    query: str,
    collection_name: str = "healthcare_general",
    limit: int = 10,
    similarity_threshold: float = 0.7,
    clinical_filter: Optional[str] = None,
    vector_store: Any | None = None,
) -> VectorStoreResult:
    return _vector_similarity_search(
        actor_name=actor_name,
        query=query,
        collection_name=collection_name,
        limit=limit,
        similarity_threshold=similarity_threshold,
        clinical_filter=clinical_filter,
        vector_store=vector_store,
    )


@hacs_tool(
    name="vector_hybrid_search",
    description="[Deprecated] Hybrid search. Prefer context-specific tools.",
    category=ToolCategory.VECTOR_SEARCH,
    domains=["general"]
)
def vector_hybrid_search(
    actor_name: str,
    query: str,
    collection_name: str = "healthcare_general",
    keyword_weight: float = 0.3,
    semantic_weight: float = 0.7,
    limit: int = 10,
    clinical_filter: Optional[str] = None,
    vector_store: Any | None = None,
) -> VectorStoreResult:
    return _vector_hybrid_search(
        actor_name=actor_name,
        query=query,
        collection_name=collection_name,
        keyword_weight=keyword_weight,
        semantic_weight=semantic_weight,
        limit=limit,
        clinical_filter=clinical_filter,
        vector_store=vector_store,
    )


@hacs_tool(
    name="get_vector_collection_stats",
    description="[Deprecated] Get vector collection statistics.",
    category=ToolCategory.VECTOR_SEARCH,
    domains=["general"]
)
def get_vector_collection_stats(
    actor_name: str,
    collection_name: str = "healthcare_general",
    include_clinical_breakdown: bool = True,
) -> VectorStoreResult:
    return _get_vector_collection_stats(
        actor_name=actor_name,
        collection_name=collection_name,
        include_clinical_breakdown=include_clinical_breakdown,
    )


@hacs_tool(
    name="optimize_vector_collection",
    description="[Deprecated] Optimize vector collection.",
    category=ToolCategory.VECTOR_SEARCH,
    domains=["general"]
)
def optimize_vector_collection(
    actor_name: str,
    collection_name: str,
    optimization_strategy: str = "clinical_relevance",
) -> HACSResult:
    return _optimize_vector_collection(
        actor_name=actor_name,
        collection_name=collection_name,
        optimization_strategy=optimization_strategy,
    )


__all__ = [
    "store_embedding",
    "vector_similarity_search",
    "vector_hybrid_search",
    "get_vector_collection_stats",
    "optimize_vector_collection",
]


