"""
HACS Terminology Tools (optional) - UMLS Metathesaurus integration ready

These tools provide optional terminology search/match utilities that can be used
by agents to look up and normalize codes in HACS resources. They are separate
from modeling tools to keep concerns isolated.
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List

from hacs_models import HACSResult


UMLS_BASE = "https://uts-ws.nlm.nih.gov/rest"


# Note: status helpers are kept as utils, not exposed as tools.


def normalize_code(system: str, code: str, display: Optional[str] = None) -> HACSResult:
    """Create a normalized TerminologyConcept payload without remote calls."""
    from hacs_utils.resource_specific import make_terminology_concept

    concept = make_terminology_concept(system, code, display)
    return HACSResult(success=True, message="Normalized concept", data={"concept": concept})


def search_umls(term_or_code: str, *, version: str = "current", pageSize: int = 5) -> HACSResult:
    """Search UMLS for CUIs by term or code (no auth call if key missing)."""
    try:
        from hacs_utils.terminology.client import UMLSClient

        client = UMLSClient()
        res = client.search(term_or_code, version=version, page_size=pageSize)
        if not res.get("success"):
            return HACSResult(success=False, message="UMLS search failed", error=res.get("error"))
        results = res.get("results") or []
        return HACSResult(
            success=True, message=f"Found {len(results)} matches", data={"results": results}
        )
    except Exception as e:
        return HACSResult(success=False, message="UMLS search failed", error=str(e))


def get_umls_cui(cui: str, *, version: str = "current") -> HACSResult:
    """Deprecated (tool too low-level): kept for backward compatibility. Use summarize/annotate tools."""
    try:
        from hacs_utils.terminology.client import UMLSClient

        client = UMLSClient()
        res = client.get_cui(cui, version=version)
        if not res.get("success"):
            return HACSResult(
                success=False, message="UMLS CUI lookup failed", error=res.get("error")
            )
        return HACSResult(success=True, message="CUI content", data=res.get("data"))
    except Exception as e:
        return HACSResult(success=False, message="UMLS CUI lookup failed", error=str(e))


def crosswalk_umls(source: str, code: str, *, version: str = "current") -> HACSResult:
    """Deprecated (tool too low-level): kept for backward compatibility. Use summarize/annotate tools."""
    try:
        from hacs_utils.terminology.client import UMLSClient

        client = UMLSClient()
        res = client.crosswalk(source, code, version=version)
        if not res.get("success"):
            return HACSResult(
                success=False, message="UMLS crosswalk failed", error=res.get("error")
            )
        return HACSResult(success=True, message="Crosswalk results", data=res.get("data"))
    except Exception as e:
        return HACSResult(success=False, message="UMLS crosswalk failed", error=str(e))


def suggest_resource_codings(
    resource: Dict[str, Any], *, code_fields: Optional[List[str]] = None
) -> HACSResult:
    """Inspect a HACS resource and return a list of candidate codes to normalize (no remote calls)."""
    code_fields = code_fields or ["code", "category", "method", "interpretation"]
    suggestions: List[Dict[str, Any]] = []
    for field in code_fields:
        value = resource.get(field)
        if isinstance(value, dict) and value.get("coding"):
            for c in value.get("coding", []):
                suggestions.append(
                    {
                        "field": field,
                        "system": c.get("system"),
                        "code": c.get("code"),
                        "display": c.get("display"),
                    }
                )
    return HACSResult(
        success=True,
        message=f"Found {len(suggestions)} coding candidates",
        data={"candidates": suggestions},
    )


def summarize_codable_concepts(
    resource: Dict[str, Any], *, query: Optional[str] = None, top_k: int = 3
) -> HACSResult:
    """
    Summarize best candidate codes across any HACS resource.

    - Recursively scans for CodeableConcept-like fields
    - Optionally runs UMLS search for a provided query to suggest top_k CUIs
    - Returns a concise text summary suitable for prompting
    """
    if not isinstance(resource, dict):
        return HACSResult(success=False, message="Expected resource as dict")

    # Local candidate scan (recursive) for any resource
    try:
        from hacs_utils.resource_specific import scan_codable_concepts

        candidates = (
            scan_codable_concepts(
                resource, code_fields=["code", "category", "type", "method", "interpretation"]
            )
            or []
        )
    except Exception:
        candidates = []

    # Optional UMLS search
    umls_items: List[Dict[str, Any]] = []
    if query:
        try:
            res = search_umls(query, pageSize=top_k)
            if res.success:
                umls_items = res.data.get("results", [])
        except Exception:
            pass

    # Build summary text
    lines: List[str] = []
    if candidates:
        lines.append("Local code candidates:")
        for c in candidates[: top_k * 2]:
            sys = c.get("system") or "unknown"
            code = c.get("code") or "?"
            disp = c.get("display") or ""
            lines.append(f"- {sys} {code} {('(' + disp + ')') if disp else ''}")
    if umls_items:
        lines.append("UMLS top matches:")
        for r in umls_items:
            name = r.get("name") or r.get("ui")
            cui = r.get("ui")
            source = (r.get("rootSource") or "").upper()
            lines.append(f"- {name} [CUI:{cui}] {source}")

    summary_text = "\n".join(lines) if lines else "No codable concepts found."
    return HACSResult(
        success=True,
        message="Summary generated",
        data={"summary": summary_text, "candidates": candidates, "umls": umls_items},
    )


def get_possible_codes(
    resource: Dict[str, Any], *, query: Optional[str] = None, top_k: int = 3
) -> HACSResult:
    """
    Return possible codings for a Composition, including a concise text summary.

    - Scans the Composition for local code candidates
    - Optionally queries UMLS for top matches
    - Returns HACSResult with: summary, candidates, umls, and composition_id
    """
    summary = summarize_codable_concepts(resource, query=query, top_k=top_k)
    if not summary.success:
        return summary
    return HACSResult(
        success=True,
        message="Possible codes computed",
        data={
            "resource_id": resource.get("id"),
            "summary": (summary.data or {}).get("summary"),
            "candidates": (summary.data or {}).get("candidates", []),
            "umls": (summary.data or {}).get("umls", []),
        },
    )


def map_terminology(
    resource: Dict[str, Any], source: str, target: str, *, top_k: int = 3
) -> HACSResult:
    """Task-level tool: suggest mappings from source to target across any HACS resource."""
    try:
        from hacs_utils.resource_specific import normalize_system_uri, scan_codable_concepts
        from hacs_utils.terminology.client import UMLSClient, system_uri_to_source
    except Exception as e:
        return HACSResult(success=False, message="Missing terminology utilities", error=str(e))

    candidates = scan_codable_concepts(resource)
    client = UMLSClient()
    src_abbrev = system_uri_to_source(normalize_system_uri(source)) or system_uri_to_source(source)
    tgt_abbrev = system_uri_to_source(normalize_system_uri(target)) or system_uri_to_source(target)
    if not src_abbrev or not tgt_abbrev:
        return HACSResult(success=False, message="Unsupported source/target system")

    mappings: List[Dict[str, Any]] = []
    for c in candidates:
        if (c.get("system") or "").lower().find(source.lower()) >= 0:
            code = c.get("code")
            if not code:
                continue
            # Crosswalk via CUI: find equivalents in target source
            cw = client.crosswalk(src_abbrev, code)
            out = []
            if cw.get("success"):
                items = (cw.get("data") or {}).get("result") or []
                for it in items:
                    if (it.get("rootSource") or "").upper() == tgt_abbrev.upper():
                        out.append({"code": it.get("ui"), "source": it.get("rootSource")})
            if out:
                mappings.append(
                    {
                        "field": c["field"],
                        "source": {"system": c["system"], "code": code},
                        "targets": out[:top_k],
                    }
                )

    return HACSResult(
        success=True, message=f"Computed {len(mappings)} mappings", data={"mappings": mappings}
    )


# Deprecated alias removed; use get_possible_codes()
