"""
CareTeam model for HACS (minimal).

HACS-native, FHIR-inspired CareTeam representing participants involved in care.
"""

from typing import Literal

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
