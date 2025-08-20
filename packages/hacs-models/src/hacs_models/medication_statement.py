"""
MedicationStatement model for HACS.

HACS-native minimal version inspired by FHIR R4 MedicationStatement, focused on
capturing medications reported as being taken (vs. prescribed).
"""

from typing import Literal

from pydantic import Field

from .base_resource import DomainResource


class MedicationStatement(DomainResource):
    resource_type: Literal["MedicationStatement"] = Field(default="MedicationStatement")

    status: str = Field(
        default="active",
        description="active | completed | intended | stopped | on-hold | unknown | not-taken",
    )
    medication_text: str | None = Field(
        default=None, description="Free text medication description"
    )
    subject_ref: str | None = Field(default=None, description="Reference to Patient or Group")
    effective_datetime: str | None = Field(
        default=None, description="When the medication is/was taken (ISO 8601)"
    )
    reason_text: str | None = Field(default=None, description="Reason for taking the medication")
    note: list[str] = Field(default_factory=list, description="Additional notes")
