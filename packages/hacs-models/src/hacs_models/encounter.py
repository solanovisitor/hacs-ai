"""
Encounter model for healthcare visits and interactions.

This module provides FHIR-compliant Encounter models for recording
healthcare visits, appointments, and patient interactions.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from .base_resource import DomainResource
from .types import EncounterStatus


class EncounterParticipant(DomainResource):
    """Participant in an encounter."""
    
    resource_type: Literal["EncounterParticipant"] = Field(default="EncounterParticipant")
    
    type_: list[str] = Field(
        default_factory=list,
        alias="type",
        description="Role of participant in encounter"
    )
    
    individual: str | None = Field(
        default=None,
        description="Persons involved in the encounter other than the patient"
    )


class EncounterDiagnosis(DomainResource):
    """Diagnosis relevant to the encounter."""
    
    resource_type: Literal["EncounterDiagnosis"] = Field(default="EncounterDiagnosis")
    
    condition: str = Field(
        description="The diagnosis or procedure relevant to the encounter"
    )
    
    use: str | None = Field(
        default=None,
        description="Role that this diagnosis has within the encounter"
    )
    
    rank: int | None = Field(
        default=None,
        description="Ranking of the diagnosis (for each role type)",
        ge=1
    )


class Encounter(DomainResource):
    """
    An interaction between a patient and healthcare provider(s).
    
    Encounters include visits, appointments, and other healthcare
    interactions between a patient and healthcare providers.
    """
    
    resource_type: Literal["Encounter"] = Field(default="Encounter")
    
    # Required fields
    status: EncounterStatus = Field(
        description="Current state of the encounter"
    )
    
    class_: str = Field(
        alias="class",
        description="Classification of patient encounter",
        examples=["inpatient", "outpatient", "ambulatory", "emergency"]
    )
    
    # Subject
    subject: str | None = Field(
        default=None,
        description="The patient present at the encounter",
        examples=["Patient/patient-123"]
    )
    
    # Participants
    participant: list[EncounterParticipant] = Field(
        default_factory=list,
        description="List of participants involved in the encounter"
    )
    
    # Timing
    period_start: datetime | None = Field(
        default=None,
        description="The start time of the encounter"
    )
    
    period_end: datetime | None = Field(
        default=None,
        description="The end time of the encounter"
    )
    
    # Length
    length: dict[str, Any] | None = Field(
        default=None,
        description="Quantity of time the encounter lasted"
    )
    
    # Reason
    reason_code: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Coded reason the encounter takes place"
    )
    
    reason_reference: list[str] = Field(
        default_factory=list,
        description="Reason the encounter takes place (reference)"
    )
    
    # Diagnosis
    diagnosis: list[EncounterDiagnosis] = Field(
        default_factory=list,
        description="The list of diagnosis relevant to this encounter"
    )
    
    # Service provider
    service_provider: str | None = Field(
        default=None,
        description="The organization responsible for this encounter",
        examples=["Organization/hospital-main"]
    )
    
    def add_participant(self, individual_ref: str, role_types: list[str] | None = None) -> None:
        """Add a participant to the encounter."""
        participant = EncounterParticipant(
            individual=individual_ref,
            type_=role_types or ["primary"]
        )
        self.participant.append(participant)
        self.update_timestamp()
    
    def add_diagnosis(self, condition_ref: str, use: str | None = None, rank: int | None = None) -> None:
        """Add a diagnosis to the encounter."""
        diagnosis = EncounterDiagnosis(
            condition=condition_ref,
            use=use,
            rank=rank
        )
        self.diagnosis.append(diagnosis)
        self.update_timestamp()
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"Encounter({self.class_}, {self.status})"