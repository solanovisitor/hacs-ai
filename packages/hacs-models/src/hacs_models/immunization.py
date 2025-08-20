"""
Immunization model for HACS (minimal).

HACS-native, FHIR-inspired resource for documenting vaccine administrations
or reported immunizations. Kept lightweight with safe defaults.
"""

from typing import Literal

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
