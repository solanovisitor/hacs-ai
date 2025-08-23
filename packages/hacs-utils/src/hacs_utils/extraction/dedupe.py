"""
Deduplication logic for extracted HACS resources.

This module handles:
- Semantic deduplication based on resource type
- Key generation for different HACS resource types
- Grouping and organizing extracted records
"""

from __future__ import annotations

from typing import Any, Dict, List


def dedupe_by_semantic_key(
    resource_type: str, 
    items: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Apply semantic deduplication based on resource type.
    
    Args:
        resource_type: Name of the HACS resource type
        items: List of extraction results with 'record', 'citation', 'char_interval'
    
    Returns:
        Deduplicated list of items
    """
    seen: set[tuple] = set()
    deduped: List[Dict[str, Any]] = []
    
    for item in items:
        rec = item.get("record")
        citation_val = (item.get("citation") or "").strip().lower()
        
        try:
            data = rec.model_dump() if hasattr(rec, "model_dump") else dict(rec)  # type: ignore[arg-type]
        except Exception:
            data = {}
        
        # Generate semantic key based on resource type
        key = generate_semantic_key(resource_type, data, citation_val)
        
        if key in seen:
            continue
        
        seen.add(key)
        deduped.append(item)
    
    return deduped


def generate_semantic_key(
    resource_type: str, 
    data: Dict[str, Any], 
    citation_val: str
) -> tuple:
    """Generate a semantic deduplication key for a resource.
    
    Args:
        resource_type: Name of the HACS resource type
        data: Resource data dictionary
        citation_val: Citation text (normalized)
    
    Returns:
        Tuple key for deduplication
    """
    if resource_type in ("Organization", "Practitioner"):
        name = (data.get("name") or citation_val or "").strip().lower()
        return (resource_type, name)
    
    elif resource_type == "Observation":
        code_text = (((data.get("code") or {}).get("text")) or "").strip().lower()
        vq = (data.get("value_quantity") or {})
        val = vq.get("value")
        unit = (vq.get("unit") or "").strip().lower()
        vstr = (data.get("value_string") or "").strip().lower()
        return (resource_type, code_text, val, unit, vstr)
    
    elif resource_type == "Condition":
        code_text = (((data.get("code") or {}).get("text")) or "").strip().lower()
        return (resource_type, code_text, citation_val)
    
    elif resource_type == "Immunization":
        vtext = ((((data.get("vaccine_code") or {}).get("text")) or "").strip().lower())
        occ = (data.get("occurrence_date_time") or "").strip().lower() if isinstance(data.get("occurrence_date_time"), str) else str(data.get("occurrence_date_time"))
        dose = str(data.get("dose_number")) if data.get("dose_number") is not None else ""
        return (resource_type, vtext, occ, dose)
    
    elif resource_type == "DiagnosticReport":
        code_text = (((data.get("code") or {}).get("text")) or "").strip().lower()
        concl = (data.get("conclusion") or "").strip().lower()
        return (resource_type, code_text, concl)
    
    elif resource_type == "MedicationStatement":
        med_text = (((data.get("medication_codeable_concept") or {}).get("text")) or "").strip().lower()
        dosage_text = (((data.get("dosage") or {}).get("text")) or "").strip().lower()
        return (resource_type, med_text, dosage_text, citation_val)
    
    elif resource_type == "Procedure":
        code_text = (((data.get("code") or {}).get("text")) or "").strip().lower()
        performed = str(data.get("performed_date_time")) if data.get("performed_date_time") else ""
        return (resource_type, code_text, performed, citation_val)
    
    elif resource_type == "ServiceRequest":
        code_text = (((data.get("code") or {}).get("text")) or "").strip().lower()
        intent = (data.get("intent") or "").strip().lower()
        return (resource_type, code_text, intent, citation_val)
    
    else:
        # Generic fallback for other resource types
        return (resource_type, citation_val)


def group_records_by_type(records_with_spans: List[Dict[str, Any]]) -> Dict[str, List[Any]]:
    """Group returned records by their HACS resource_type.
    
    Args:
        records_with_spans: List of extraction results
    
    Returns:
        Dictionary mapping resource type to list of records
    """
    grouped: Dict[str, List[Any]] = {}
    for item in records_with_spans or []:
        rec = item.get("record")
        if rec is None:
            continue
        rtype = getattr(rec, "resource_type", None) or getattr(rec, "__class__", type("_", (), {})).__name__
        grouped.setdefault(str(rtype), []).append(rec)
    return grouped


def group_resource_type_citations(items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group resource type citations by type.
    
    Args:
        items: List of citation items with 'resource_type'
    
    Returns:
        Dictionary mapping resource type to list of citation items
    """
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for it in items or []:
        rt = str(it.get("resource_type") or "Unknown")
        grouped.setdefault(rt, []).append(it)
    return grouped
