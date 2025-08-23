"""
NutritionOrder model for HACS (minimal).

HACS-native, FHIR-inspired NutritionOrder to capture diet/feeding orders.
"""

from typing import Any, Literal

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

    # --- LLM-friendly extractable facade overrides ---
    @classmethod
    def get_extractable_fields(cls) -> list[str]:  # type: ignore[override]
        """Return fields that should be extracted by LLMs (3-4 key fields only)."""
        return [
            "status",
            "oral_diet_text",
            "supplement_text",
            "enteral_formula_text",
        ]

    @classmethod
    def get_canonical_defaults(cls) -> dict[str, Any]:
        return {
            "status": "active",
            "intent": "order",
            "patient_ref": "Patient/UNKNOWN",
        }

    @classmethod
    def llm_hints(cls) -> list[str]:  # type: ignore[override]
        return [
            "Summarize diet/supplement/formula instructions when mentioned",
            "Prefer concise free-text rather than enumerating options",
            "Use 'active' status unless explicitly specified",
        ]
