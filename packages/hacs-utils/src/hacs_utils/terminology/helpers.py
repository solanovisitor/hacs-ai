"""
Terminology helpers: LOINC constants and UMLS-backed lookups.

Provides small, dependency-light helpers to map common vital/anthropometric
metrics to LOINC and to look up ICD-10 (and other systems) via UMLS.
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List

from hacs_models.observation import CodeableConcept, Coding
from hacs_utils.terminology.client import UMLSClient, system_uri_to_source


# Canonical LOINC codes for common vitals/anthropometrics
LOINC = {
    "body_weight": ("http://loinc.org", "29463-7", "Body weight") ,
    "body_height": ("http://loinc.org", "8302-2", "Body height") ,
    "bmi": ("http://loinc.org", "39156-5", "Body mass index (BMI)") ,
    "waist_circumference": ("http://loinc.org", "8280-0", "Waist circumference") ,
    "systolic_bp": ("http://loinc.org", "8480-6", "Systolic blood pressure") ,
    "diastolic_bp": ("http://loinc.org", "8462-4", "Diastolic blood pressure") ,
    "heart_rate": ("http://loinc.org", "8867-4", "Heart rate") ,
    "resp_rate": ("http://loinc.org", "9279-1", "Respiratory rate") ,
    "temperature": ("http://loinc.org", "8310-5", "Body temperature") ,
    "spo2": ("http://loinc.org", "59408-5", "Oxygen saturation in Arterial blood by Pulse oximetry") ,
}


def codeable_concept(system: str, code: str, display: Optional[str] = None) -> CodeableConcept:
    """Create a CodeableConcept object for the given system/code.

    Returns a HACS `CodeableConcept` instance from `hacs_models.observation`.
    """
    cc = CodeableConcept(text=display)
    cc.coding = [Coding(system=system, code=code, display=display)]
    return cc


def loinc_for(metric_key: str) -> Optional[CodeableConcept]:
    """Return CodeableConcept for a known vital/anthropometric metric key."""
    item = LOINC.get(metric_key)
    if not item:
        return None
    system, code, display = item
    return codeable_concept(system, code, display)


def lookup_icd10(term_or_code: str, *, page_size: int = 3) -> Optional[CodeableConcept]:
    """Lookup ICD-10 code via UMLS; return best CodeableConcept if found.

    - Prefers results whose rootSource looks like ICD10CM.
    - Falls back to the top result if no ICD10CM match.
    """
    client = UMLSClient()
    res = client.search(term_or_code, page_size=page_size)
    if not res.get("success"):
        return None
    results = res.get("results") or []
    if not results:
        return None
    # Try to pick ICD10CM result
    pick: Optional[Dict] = None
    for r in results:
        if (r.get("rootSource") or "").upper().startswith("ICD10"):
            pick = r
            break
    if pick is None:
        pick = results[0]
    code = pick.get("ui")
    display = pick.get("name")
    if not code:
        return None
    return codeable_concept("http://hl7.org/fhir/sid/icd-10", code, display)


def crosswalk(system_uri: str, code: str) -> Optional[dict]:
    """Use UMLS crosswalk for a given source system URI and code.

    Returns raw payload dict if success; None otherwise.
    """
    source = system_uri_to_source(system_uri)
    if not source:
        return None
    client = UMLSClient()
    res = client.crosswalk(source, code)
    if not res.get("success"):
        return None
    return res.get("data")


def normalize_system_uri(system: str) -> str:
    """Normalize common system names to canonical URIs."""
    mapping = {
        "SNOMED": "http://snomed.info/sct",
        "SNOMEDCT": "http://snomed.info/sct",
        "LOINC": "http://loinc.org",
        "RxNorm": "http://www.nlm.nih.gov/research/umls/rxnorm",
        "UMLS": "http://identifiers.org/umls",
    }
    return mapping.get(system, system)


def make_terminology_concept(system: str, code: str, display: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
    """Legacy dict-shaped concept for tools; prefer hacs_models.terminology types in code."""
    return {
        "resource_type": "TerminologyConcept",
        "system_uri": normalize_system_uri(system),
        "code": code,
        "display": display,
        **kwargs,
    }


def scan_codable_concepts(obj: Any, code_fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Recursively scan an object for CodeableConcept-like fields and collect coding entries."""
    targets = set(code_fields or ["code", "category", "type", "method", "interpretation"])
    found: List[Dict[str, Any]] = []

    def _walk(node: Any):
        if isinstance(node, dict):
            for k, v in node.items():
                if k in targets and isinstance(v, dict) and v.get("coding"):
                    for c in v.get("coding", []) or []:
                        found.append(
                            {
                                "field": k,
                                "system": (c or {}).get("system"),
                                "code": (c or {}).get("code"),
                                "display": (c or {}).get("display"),
                            }
                        )
                _walk(v)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(obj)
    return found


