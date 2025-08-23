"""
CareTeam model for HACS (minimal).

HACS-native, FHIR-inspired CareTeam representing participants involved in care.
"""

from typing import Any, Literal

from pydantic import Field

from .base_resource import DomainResource


class CareTeam(DomainResource):
    resource_type: Literal["CareTeam"] = Field(default="CareTeam")

    status: str = Field(
        default="active", description="proposed|active|suspended|inactive|entered-in-error"
    )
    name: str | None = Field(default=None, description="Name of the care team")
    subject_ref: str | None = Field(default=None, description="Patient reference")
    participant_refs: list[str] = Field(
        default_factory=list, description="Members (Practitioner/RelatedPerson/Organization)"
    )
    note: list[str] = Field(default_factory=list, description="Notes")

    # --- LLM-friendly extractable facade overrides ---
    @classmethod
    def get_extractable_fields(cls) -> list[str]:  # type: ignore[override]
        """Return fields that should be extracted by LLMs (3-4 key fields only)."""
        return [
            "status",
            "name",
            "participant_refs",
            "note",
        ]

    @classmethod
    def get_canonical_defaults(cls) -> dict[str, Any]:
        return {
            "status": "active",
            "subject_ref": "Patient/UNKNOWN",
        }

    @classmethod
    def llm_hints(cls) -> list[str]:  # type: ignore[override]
        return [
            "Extract a simple care team name if available",
            "List key participants only when explicitly mentioned",
            "Use 'active' status unless specified otherwise",
        ]
