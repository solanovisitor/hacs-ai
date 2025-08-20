"""
UMLS Terminology Client (minimal)

Centralizes auth and HTTP calls to the UMLS Metathesaurus service.
Respects UMLS_API_KEY from environment. All methods are safe to import when
key is missing; network calls will return structured errors in that case.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from dotenv import dotenv_values

UMLS_BASE = "https://uts-ws.nlm.nih.gov/rest"


def get_umls_api_key() -> Optional[str]:
    # Read from .env without relying on process environment
    values = dotenv_values()
    return values.get("UMLS_API_KEY")


def system_uri_to_source(system_uri: str) -> Optional[str]:
    """Map common system URIs/names to UMLS source abbreviations."""
    if not system_uri:
        return None
    uri = system_uri.lower()
    if "snomed" in uri:
        return "SNOMEDCT_US"
    if "loinc" in uri:
        return "LOINC"
    if "rxnorm" in uri or "umls/rxnorm" in uri:
        return "RXNORM"
    if "icd-10" in uri or "icd10" in uri:
        return "ICD10CM"
    if uri.startswith("http"):
        return None
    # Fallback for common names
    name = system_uri.upper()
    if name in {"SNOMED", "SNOMEDCT", "SNOMEDCT_US"}:
        return "SNOMEDCT_US"
    if name in {"LOINC"}:
        return "LOINC"
    if name in {"RXNORM"}:
        return "RXNORM"
    return None


class UMLSClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = UMLS_BASE):
        self.api_key = api_key or get_umls_api_key()
        self.base_url = base_url.rstrip("/")

    def _ensure_key(self) -> Optional[str]:
        return self.api_key

    def search(
        self, term_or_code: str, version: str = "current", page_size: int = 5
    ) -> Dict[str, Any]:
        """/search/{version}?string=..."""
        key = self._ensure_key()
        if not key:
            return {"success": False, "error": "Missing UMLS_API_KEY", "results": []}
        try:
            import requests

            params = {"string": term_or_code, "pageSize": page_size, "apiKey": key}
            resp = requests.get(f"{self.base_url}/search/{version}", params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json() or {}
            results = (data.get("result") or {}).get("results") or []
            return {"success": True, "results": results}
        except Exception as e:
            return {"success": False, "error": str(e), "results": []}

    def get_cui(self, cui: str, version: str = "current") -> Dict[str, Any]:
        key = self._ensure_key()
        if not key:
            return {"success": False, "error": "Missing UMLS_API_KEY"}
        try:
            import requests

            resp = requests.get(
                f"{self.base_url}/content/{version}/CUI/{cui}", params={"apiKey": key}, timeout=15
            )
            resp.raise_for_status()
            return {"success": True, "data": resp.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def crosswalk(self, source: str, code: str, version: str = "current") -> Dict[str, Any]:
        key = self._ensure_key()
        if not key:
            return {"success": False, "error": "Missing UMLS_API_KEY"}
        try:
            import requests

            resp = requests.get(
                f"{self.base_url}/crosswalk/{version}/source/{source}/{code}",
                params={"apiKey": key},
                timeout=15,
            )
            resp.raise_for_status()
            return {"success": True, "data": resp.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_definitions(self, cui: str, version: str = "current") -> Dict[str, Any]:
        key = self._ensure_key()
        if not key:
            return {"success": False, "error": "Missing UMLS_API_KEY"}
        try:
            import requests

            resp = requests.get(
                f"{self.base_url}/content/{version}/CUI/{cui}/definitions",
                params={"apiKey": key},
                timeout=15,
            )
            resp.raise_for_status()
            return {"success": True, "data": resp.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def source_lookup(self, source: str, code: str, version: str = "current") -> Dict[str, Any]:
        key = self._ensure_key()
        if not key:
            return {"success": False, "error": "Missing UMLS_API_KEY"}
        try:
            import requests

            resp = requests.get(
                f"{self.base_url}/content/{version}/source/{source}/{code}",
                params={"apiKey": key},
                timeout=15,
            )
            resp.raise_for_status()
            return {"success": True, "data": resp.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def source_relatives(
        self, source: str, code: str, rel: str, version: str = "current"
    ) -> Dict[str, Any]:
        """Relatives: parents|children|ancestors|descendants|relations|attributes"""
        key = self._ensure_key()
        if not key:
            return {"success": False, "error": "Missing UMLS_API_KEY"}
        try:
            import requests

            rel = rel.strip("/")
            resp = requests.get(
                f"{self.base_url}/content/{version}/source/{source}/{code}/{rel}",
                params={"apiKey": key},
                timeout=15,
            )
            resp.raise_for_status()
            return {"success": True, "data": resp.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}
