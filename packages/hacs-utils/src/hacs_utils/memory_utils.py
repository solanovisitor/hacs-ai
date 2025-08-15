from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple

from hacs_models import MemoryBlock


def merge_memories(
    *sources: Iterable[MemoryBlock] | Iterable[Dict[str, Any]]
) -> List[MemoryBlock]:
    """
    Merge multiple sources of MemoryBlock instances or dicts into a unified list.
    Non-parsable items are skipped. No deduplication performed.
    """
    merged: List[MemoryBlock] = []
    for src in sources:
        for item in src:
            if isinstance(item, MemoryBlock):
                merged.append(item)
            else:
                try:
                    merged.append(MemoryBlock(**item))
                except Exception:
                    continue
    return merged


def filter_memories(
    memories: Iterable[MemoryBlock],
    *,
    patient_id: Optional[str] = None,
    memory_type: Optional[str] = None,
    min_importance: Optional[float] = None,
    tags_any: Optional[Iterable[str]] = None,
) -> List[MemoryBlock]:
    """
    Filter memories by common fields; returns a new list.
    """
    result: List[MemoryBlock] = []
    tag_set = set(tags_any or [])
    for m in memories:
        if patient_id and (m.context_metadata or {}).get("patient_id") != patient_id:
            continue
        if memory_type and m.memory_type != memory_type:
            continue
        if min_importance is not None and (getattr(m, "importance_score", 0.0) or 0.0) < min_importance:
            continue
        if tag_set:
            mtags = set(getattr(m, "tags", []) or [])
            if mtags.isdisjoint(tag_set):
                continue
        result.append(m)
    return result


async def gather_memories(
    *,
    db_adapter: Any,
    actor_name: str = "memory-utils",
    limit: int = 200,
    filters: Optional[Dict[str, Any]] = None,
) -> List[MemoryBlock]:
    """
    Load MemoryBlock records via persistence adapter `.search`.
    """
    from hacs_models import Actor

    try:
        found = await db_adapter.search(MemoryBlock, Actor(name=actor_name), filters=filters or {}, limit=limit)
        return list(found or [])
    except Exception:
        return []


def feed_memories(memories: Iterable[MemoryBlock], max_items: int = 5) -> List[str]:
    """
    Render a few memory snippets for injection into prompts.
    """
    snippets: List[str] = []
    for m in list(memories)[:max_items]:
        content = (m.content or "").strip()
        context = (m.context_metadata or {})
        pid = context.get("patient_id")
        tag_str = ", ".join((m.tags or [])[:5]) if getattr(m, "tags", None) else ""
        prefix = f"[patient:{pid}] " if pid else ""
        suffix = f" (tags: {tag_str})" if tag_str else ""
        snippets.append(f"{prefix}{content}{suffix}")
    return snippets


