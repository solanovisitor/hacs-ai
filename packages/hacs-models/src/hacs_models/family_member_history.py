"""
FamilyMemberHistory model for HACS (lightweight).

Captures significant conditions in family members relevant to patient care.
"""

from typing import Literal
from pydantic import Field

from .base_resource import DomainResource


class FamilyMemberHistory(DomainResource):
    resource_type: Literal["FamilyMemberHistory"] = Field(default="FamilyMemberHistory")

    status: str = Field(default="completed", description="partial | completed | entered-in-error | health-unknown")
    patient_ref: str | None = Field(default=None, description="Patient reference")
    relationship_text: str | None = Field(default=None, description="Relationship (e.g., mother, father, aunt)")
    name: str | None = Field(default=None, description="Family member name (optional)")
    sex: str | None = Field(default=None, description="male | female | other | unknown")
    condition_text: str | None = Field(default=None, description="Condition summary (free text)")
    outcome_text: str | None = Field(default=None, description="Outcome summary (free text)")
    contributed_to_death: bool | None = Field(default=None, description="Whether the condition contributed to death")


