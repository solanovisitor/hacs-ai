"""
Evidence Tools - Context-engineered tools for clinical evidence operations

These tools provide healthcare-specific operations tailored for LLM usage,
wrapping generic vector capabilities from hacs-utils to index and retrieve
clinical evidence with appropriate schemas and metadata.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from hacs_core.tool_protocols import hacs_tool, ToolCategory
from hacs_models import HACSResult
from hacs_models.evidence import Evidence, EvidenceType
from hacs_utils.vector_ops import store_embedding, vector_similarity_search


@hacs_tool(
    name="index_evidence",
    description="Index clinical evidence (content + citation) and return structured Evidence with embedding reference",
    category=ToolCategory.CLINICAL_WORKFLOWS,
    healthcare_domains=["knowledge_management", "clinical_guidelines"]
)
def index_evidence(
    actor_name: str,
    citation: str,
    content: str,
    evidence_type: str = "clinical_note",
    clinical_context: Optional[str] = None,
    tags: Optional[List[str]] = None,
    linked_resources: Optional[List[str]] = None,
    vector_store: Any | None = None,
) -> HACSResult:
    """
    Create an Evidence resource and store its content as a vector embedding for retrieval.

    Returns a HACSResult containing the Evidence payload and embedding reference.
    """
    # Map string to EvidenceType with fallback
    try:
        etype = EvidenceType(evidence_type)
    except Exception:
        etype = EvidenceType.CLINICAL_NOTE

    # Store embedding first to get vector id
    meta = {
        "evidence_type": etype.value,
        "citation": citation,
        "tags": (tags or []),
    }
    vec = store_embedding(
        actor_name=actor_name,
        content=content,
        collection_name="clinical_evidence",
        metadata=meta,
        clinical_context=clinical_context,
        vector_store=vector_store,
    )

    vector_id = None
    try:
        if vec and vec.search_results:
            vector_id = vec.search_results[0].get("embedding_id")
    except Exception:
        vector_id = None

    evidence = Evidence(
        resource_type="Evidence",
        citation=citation,
        content=content,
        evidence_type=etype,
        vector_id=vector_id,
        provenance={"indexed_by": actor_name},
        linked_resources=list(linked_resources or []),
        tags=list(tags or []),
    )

    data = {
        "evidence": evidence.model_dump(),
        "vector_embedding_id": vector_id,
        "collection": "clinical_evidence",
    }
    return HACSResult(success=True, message=vec.message if hasattr(vec, "message") else "Evidence indexed", data=data, actor_id=actor_name)


@hacs_tool(
    name="check_evidence",
    description="Retrieve semantically relevant clinical evidence for a query (returns structured Evidence list)",
    category=ToolCategory.CLINICAL_WORKFLOWS,
    healthcare_domains=["knowledge_management", "clinical_guidelines"]
)
def check_evidence(
    actor_name: str,
    query: str,
    clinical_context: Optional[str] = None,
    limit: int = 5,
    vector_store: Any | None = None,
) -> HACSResult:
    """
    Perform semantic retrieval over the evidence collection and return structured Evidence items.
    """
    res = vector_similarity_search(
        actor_name=actor_name,
        query=query,
        collection_name="clinical_evidence",
        limit=limit,
        clinical_filter=clinical_context,
        vector_store=vector_store,
    )

    items: List[Dict[str, Any]] = []
    for r in res.search_results or []:
        md = r.get("metadata", {})
        # Heuristic mapping
        src = md.get("source") or md.get("citation") or "Unknown Source"
        etype = EvidenceType.GUIDELINE if "guideline" in (src.lower()) else EvidenceType.CLINICAL_NOTE
        ev = Evidence(
            resource_type="Evidence",
            citation=str(src),
            content=r.get("content") or "",
            evidence_type=etype,
            vector_id=r.get("embedding_id"),
            provenance={"retrieved_by": actor_name},
            tags=list(md.get("tags", [])),
        )
        items.append(ev.model_dump())

    data = {
        "query": query,
        "clinical_context": clinical_context,
        "results_count": len(items),
        "evidence": items,
        "collection": "clinical_evidence",
    }
    return HACSResult(success=True, message=res.message, data=data, actor_id=actor_name)


__all__ = [
    "index_evidence",
    "check_evidence",
]


