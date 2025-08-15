"""
Appointment model for HACS (minimal).

HACS-native, FHIR-inspired Appointment resource for scheduling and documenting
booked visits. Kept lightweight with safe defaults.
"""

from typing import Literal
from pydantic import Field

from .base_resource import DomainResource


class Appointment(DomainResource):
    resource_type: Literal["Appointment"] = Field(default="Appointment")

    status: str = Field(default="booked", description="proposed|pending|booked|arrived|fulfilled|cancelled|noshow|entered-in-error|checked-in|waitlist")
    description: str | None = Field(default=None, description="Additional information about the appointment")

    # Timing
    start: str | None = Field(default=None, description="Start time (ISO 8601)")
    end: str | None = Field(default=None, description="End time (ISO 8601)")

    # Participants
    patient_ref: str | None = Field(default=None, description="Reference to Patient")
    participant_refs: list[str] = Field(default_factory=list, description="Other participant references (Practitioner/RelatedPerson)")

    # Reason
    reason_text: str | None = Field(default=None, description="Reason for the appointment (free text)")


