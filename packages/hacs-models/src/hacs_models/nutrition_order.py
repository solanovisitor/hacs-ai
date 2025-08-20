"""
NutritionOrder model for HACS (minimal).

HACS-native, FHIR-inspired NutritionOrder to capture diet/feeding orders.
"""

from typing import Literal

from pydantic import Field

from .base_resource import DomainResource


class NutritionOrder(DomainResource):
    resource_type: Literal["NutritionOrder"] = Field(default="NutritionOrder")

    status: str = Field(
        default="active",
        description="proposed|draft|active|on-hold|revoked|completed|entered-in-error|unknown",
    )
    intent: str = Field(default="order", description="proposal|plan|order")

    patient_ref: str | None = Field(default=None, description="Patient reference")
    encounter_ref: str | None = Field(default=None, description="Encounter reference")
    date_time: str | None = Field(default=None, description="When the order was placed (ISO 8601)")

    oral_diet_text: str | None = Field(default=None, description="Free text oral diet instructions")
    supplement_text: str | None = Field(
        default=None, description="Free text supplement instructions"
    )
    enteral_formula_text: str | None = Field(
        default=None, description="Free text enteral formula instructions"
    )
