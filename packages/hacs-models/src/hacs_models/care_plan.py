"""
CarePlan model for HACS (minimal).

HACS-native, FHIR-inspired CarePlan to represent planned care activities,
goals, and management for a patient. Lightweight with safe defaults.
"""

from typing import Literal
from pydantic import Field

from .base_resource import DomainResource


class CarePlan(DomainResource):
    resource_type: Literal["CarePlan"] = Field(default="CarePlan")

    status: str = Field(default="active", description="draft|active|on-hold|revoked|completed|entered-in-error|unknown")
    intent: str = Field(default="plan", description="proposal|plan|order|option")

    title: str | None = Field(default=None, description="Human-readable title")
    description_text: str | None = Field(default=None, description="Free-text description of the plan")

    subject_ref: str | None = Field(default=None, description="Patient reference")
    encounter_ref: str | None = Field(default=None, description="Encounter reference")

    goal_refs: list[str] = Field(default_factory=list, description="References to Goal resources")
    activity_text: list[str] = Field(default_factory=list, description="Planned activities (free text)")
    note: list[str] = Field(default_factory=list, description="Notes and comments")


