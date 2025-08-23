"""
Appointment model for HACS (minimal).

HACS-native, FHIR-inspired Appointment resource for scheduling and documenting
booked visits. Kept lightweight with safe defaults.
"""

from typing import Any, Literal

from pydantic import Field

from .base_resource import DomainResource


class Appointment(DomainResource):
    resource_type: Literal["Appointment"] = Field(default="Appointment")

    status: str = Field(
        default="booked",
        description="proposed|pending|booked|arrived|fulfilled|cancelled|noshow|entered-in-error|checked-in|waitlist",
    )
    description: str | None = Field(
        default=None, description="Additional information about the appointment"
    )

    # Timing
    start: str | None = Field(default=None, description="Start time (ISO 8601)")
    end: str | None = Field(default=None, description="End time (ISO 8601)")

    # Participants
    patient_ref: str | None = Field(default=None, description="Reference to Patient")
    participant_refs: list[str] = Field(
        default_factory=list,
        description="Other participant references (Practitioner/RelatedPerson)",
    )

    # Reason
    reason_text: str | None = Field(
        default=None, description="Reason for the appointment (free text)"
    )

    # --- LLM-friendly extractable facade overrides ---
    @classmethod
    def get_extractable_fields(cls) -> list[str]:  # type: ignore[override]
        """Return fields that should be extracted by LLMs (3-4 key fields only)."""
        return [
            "status",
            "start",
            "reason_text",
            "description",
        ]

    @classmethod
    def get_required_extractables(cls) -> list[str]:
        """Fields that must be provided for valid extraction."""
        return ["status"]

    @classmethod
    def get_canonical_defaults(cls) -> dict[str, Any]:
        """Default values for system/required fields during extraction."""
        return {
            "status": "booked",
            "patient_ref": "Patient/UNKNOWN",
        }

    @classmethod
    def coerce_extractable(cls, payload: dict[str, Any], relax: bool = True) -> dict[str, Any]:
        """Coerce extractable payload to proper types with relaxed validation."""
        # Appointment fields are mostly strings, minimal coercion needed
        return payload.copy()

    @classmethod
    def llm_hints(cls) -> list[str]:  # type: ignore[override]
        """Provide LLM-specific extraction hints."""
        return [
            "Extract appointment status (booked, cancelled, fulfilled, etc.)",
            "Include start time when mentioned (ISO 8601 format preferred)",
            "Capture reason for appointment visit",
            "Include any additional appointment details in description"
        ]
