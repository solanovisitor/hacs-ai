"""
Immunization model for HACS (minimal).

HACS-native, FHIR-inspired resource for documenting vaccine administrations
or reported immunizations. Kept lightweight with safe defaults.
"""

from typing import Any, Literal

from pydantic import Field

from .base_resource import DomainResource
from .observation import CodeableConcept


class Immunization(DomainResource):
    resource_type: Literal["Immunization"] = Field(default="Immunization")

    # Core
    status: str = Field(default="completed", description="completed | entered-in-error | not-done")
    vaccine_code: CodeableConcept | None = Field(
        default=None, description="Vaccine product administered"
    )
    patient_ref: str | None = Field(
        default=None, description="Reference to Patient (e.g., Patient/123)"
    )

    # Timing
    occurrence_datetime: str | None = Field(
        default=None, description="Date/time vaccine administered (ISO 8601)"
    )
    recorded: str | None = Field(
        default=None, description="When the record was captured (ISO 8601)"
    )

    # Context
    encounter_ref: str | None = Field(default=None, description="Reference to Encounter")
    location_ref: str | None = Field(default=None, description="Reference to Location")
    manufacturer_ref: str | None = Field(
        default=None, description="Vaccine manufacturer Organization ref"
    )

    # Details
    lot_number: str | None = Field(default=None, description="Lot number")
    expiration_date: str | None = Field(default=None, description="Expiration date (YYYY-MM-DD)")
    site_text: str | None = Field(default=None, description="Body site (text)")
    route_text: str | None = Field(default=None, description="Administration route (text)")
    dose_quantity: str | None = Field(default=None, description="Dose quantity (text)")

    # Notes/Reasons (kept simple)
    note: list[str] = Field(
        default_factory=list, description="Additional notes about the immunization"
    )
    reason_text: list[str] = Field(
        default_factory=list, description="Reasons immunization occurred (text)"
    )

    # --- LLM-friendly extractable facade overrides ---
    @classmethod
    def get_extractable_fields(cls) -> list[str]:  # type: ignore[override]
        # Focus on essential immunization info LLMs can extract reliably
        return [
            "status",              # Immunization status (completed, not-done, etc.)
            "vaccine_code",        # Vaccine name/type
            "occurrence_datetime", # Date of vaccination when mentioned
            "dose_quantity",       # Dose amount when specified
            "site_text",           # Injection site when mentioned
            "route_text",          # Route of administration when mentioned
            "reason_text",         # Reason for vaccination when given
        ]

    @classmethod
    def get_required_extractables(cls) -> list[str]:
        """Fields that must be provided for valid extraction."""
        return ["vaccine_code"]

    @classmethod
    def get_canonical_defaults(cls) -> dict[str, Any]:
        """Default values for system/required fields during extraction."""
        return {
            "status": "completed",
            "patient_ref": "Patient/UNKNOWN",
            "vaccine_code": {"text": ""},  # Will be filled by LLM
        }

    @classmethod
    def coerce_extractable(cls, payload: dict[str, Any], relax: bool = True) -> dict[str, Any]:
        """Coerce extractable payload to proper types with relaxed validation."""
        coerced = payload.copy()

        # Coerce vaccine_code to CodeableConcept if it's a string
        if "vaccine_code" in coerced and isinstance(coerced["vaccine_code"], str):
            coerced["vaccine_code"] = {"text": coerced["vaccine_code"]}

        # Ensure vaccine_code has text field
        if "vaccine_code" in coerced and isinstance(coerced["vaccine_code"], dict) and "text" not in coerced["vaccine_code"]:
            coerced["vaccine_code"]["text"] = ""

        return coerced

    @classmethod
    def get_extraction_examples(cls) -> dict[str, Any]:
        """Return extraction examples showing different extractable field scenarios."""
        # Complete vaccination record
        complete_example = {
            "status": "completed",
            "vaccine_code": {"text": "vacina COVID-19"},
            "occurrence_datetime": "2024-08-15T10:00:00",
            "dose_quantity": {"value": 0.5, "unit": "mL"},
            "site_text": "braço direito",
            "route_text": "intramuscular",
            "reason_text": ["prevenção COVID-19"],
        }

        # Simple vaccination
        simple_example = {
            "status": "completed",
            "vaccine_code": {"text": "pneumo 13"},
            "occurrence_datetime": "2024-08-10",
        }

        # Vaccination with site/route
        detailed_example = {
            "status": "completed",
            "vaccine_code": {"text": "influenza"},
            "site_text": "deltoide esquerdo",
            "route_text": "via intramuscular",
        }

        return {
            "object": complete_example,
            "array": [complete_example, simple_example, detailed_example],
            "scenarios": {
                "complete": complete_example,
                "simple": simple_example,
                "detailed": detailed_example,
            }
        }

    @classmethod
    def llm_hints(cls) -> list[str]:  # type: ignore[override]
        return [
            "- Accept textual vaccine names in vaccine_code.text (e.g., 'pneumo 13', 'meningo')",
            "- occurrence_datetime and dose may be null if not present",
        ]
