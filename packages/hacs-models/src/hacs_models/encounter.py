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
        default_factory=list, alias="type", description="Role of participant in encounter"
    )

    individual: str | None = Field(
        default=None, description="Persons involved in the encounter other than the patient"
    )


class EncounterDiagnosis(DomainResource):
    """Diagnosis relevant to the encounter."""

    resource_type: Literal["EncounterDiagnosis"] = Field(default="EncounterDiagnosis")

    condition: str = Field(description="The diagnosis or procedure relevant to the encounter")

    use: str | None = Field(
        default=None, description="Role that this diagnosis has within the encounter"
    )

    rank: int | None = Field(
        default=None, description="Ranking of the diagnosis (for each role type)", ge=1
    )


class Encounter(DomainResource):
    """
    An interaction between a patient and healthcare provider(s).

    Encounters include visits, appointments, and other healthcare
    interactions between a patient and healthcare providers.
    """

    resource_type: Literal["Encounter"] = Field(default="Encounter")

    # Required fields
    status: EncounterStatus = Field(description="Current state of the encounter")

    class_: str = Field(
        alias="class",
        description="Classification of patient encounter",
        examples=["inpatient", "outpatient", "ambulatory", "emergency"],
    )

    # Subject
    subject: str | None = Field(
        default=None,
        description="The patient present at the encounter",
        examples=["Patient/patient-123"],
    )

    # Participants
    participant: list[EncounterParticipant] = Field(
        default_factory=list, description="List of participants involved in the encounter"
    )

    # Timing
    period_start: datetime | None = Field(
        default=None, description="The start time of the encounter"
    )

    period_end: datetime | None = Field(default=None, description="The end time of the encounter")

    # Length
    length: dict[str, Any] | None = Field(
        default=None, description="Quantity of time the encounter lasted"
    )

    # Reason
    reason_code: list[dict[str, Any]] = Field(
        default_factory=list, description="Coded reason the encounter takes place"
    )

    reason_reference: list[str] = Field(
        default_factory=list, description="Reason the encounter takes place (reference)"
    )

    # Diagnosis
    diagnosis: list[EncounterDiagnosis] = Field(
        default_factory=list, description="The list of diagnosis relevant to this encounter"
    )

    # Service provider
    service_provider: str | None = Field(
        default=None,
        description="The organization responsible for this encounter",
        examples=["Organization/hospital-main"],
    )

    def add_participant(self, individual_ref: str, role_types: list[str] | None = None) -> None:
        """Add a participant to the encounter."""
        participant = EncounterParticipant(
            individual=individual_ref, type_=role_types or ["primary"]
        )
        self.participant.append(participant)
        self.update_timestamp()

    def add_diagnosis(
        self, condition_ref: str, use: str | None = None, rank: int | None = None
    ) -> None:
        """Add a diagnosis to the encounter."""
        diagnosis = EncounterDiagnosis(condition=condition_ref, use=use, rank=rank)
        self.diagnosis.append(diagnosis)
        self.update_timestamp()

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"Encounter({self.class_}, {self.status})"

    # --- LLM-friendly extractable facade overrides ---
    @classmethod
    def get_extractable_fields(cls) -> list[str]:  # type: ignore[override]
        """Return fields that should be extracted by LLMs - expanded for better context."""
        return [
            "status",           # Encounter status (in-progress, finished, etc.)
            "class",            # Encounter class (inpatient, outpatient, emergency)
            "period_start",     # Start date/time when mentioned
            "period_end",       # End date/time when mentioned
            "reason_code",      # Chief complaint or reason for visit
            "type",             # Type of encounter (consultation, followup, etc.)
        ]

    @classmethod
    def get_required_extractables(cls) -> list[str]:
        """Fields that must be provided for valid extraction."""
        return ["status", "class"]

    @classmethod
    def get_canonical_defaults(cls) -> dict[str, Any]:
        """Default values for system/required fields during extraction."""
        return {
            "status": "finished",
            "class": "outpatient",  # Use alias, not field name
            "subject": "Patient/UNKNOWN",
        }

    @classmethod
    def coerce_extractable(cls, payload: dict[str, Any], relax: bool = True) -> dict[str, Any]:
        """Coerce extractable payload to proper types with relaxed validation."""
        coerced = payload.copy()

        # Handle field alias: class_ field should be accessed as 'class'
        if "class_" in coerced and "class" not in coerced:
            coerced["class"] = coerced.pop("class_")

        # Coerce reason_code to list of CodeableConcept if it's a string or dict
        if "reason_code" in coerced:
            reason = coerced["reason_code"]
            if isinstance(reason, str):
                coerced["reason_code"] = [{"text": reason}]
            elif isinstance(reason, dict):
                coerced["reason_code"] = [reason]
            elif not isinstance(reason, list):
                coerced["reason_code"] = []

        # Remove system fields that shouldn't be LLM-generated
        system_fields = ["id", "created_at", "updated_at", "version", "meta_tag"]
        for field in system_fields:
            coerced.pop(field, None)

        return coerced

    @classmethod
    def get_extraction_examples(cls) -> dict[str, Any]:
        """Return extraction examples showing different extractable field scenarios."""
        # Outpatient consultation
        outpatient_example = {
            "status": "finished",
            "class_": "outpatient",
            "type": [{"text": "consulta de rotina"}],
            "reason_code": [{"text": "hipertensão"}],
            "period_start": "2024-08-15T09:00:00",
            "period_end": "2024-08-15T09:30:00",
        }

        # Emergency visit
        emergency_example = {
            "status": "finished",
            "class_": "emergency",
            "type": [{"text": "atendimento de emergência"}],
            "reason_code": [{"text": "dor no peito"}],
            "period_start": "2024-08-15T14:30:00",
        }

        # In-progress hospitalization
        inpatient_example = {
            "status": "in-progress",
            "class_": "inpatient",
            "reason_code": [{"text": "cirurgia programada"}],
            "period_start": "2024-08-15T07:00:00",
        }

        return {
            "object": outpatient_example,
            "array": [outpatient_example, emergency_example, inpatient_example],
            "scenarios": {
                "outpatient": outpatient_example,
                "emergency": emergency_example,
                "inpatient": inpatient_example,
            }
        }

    @classmethod
    def llm_hints(cls) -> list[str]:  # type: ignore[override]
        """Provide LLM-specific extraction hints."""
        return [
            "Extract encounter type (inpatient, outpatient, emergency, ambulatory)",
            "Status should be: planned, arrived, in-progress, finished, cancelled",
            "Include start time when mentioned",
            "Capture reason for visit in reason_code"
        ]

    @classmethod
    def get_facades(cls) -> dict[str, "FacadeSpec"]:
        """Return available extraction facades for Encounter."""
        from .base_resource import FacadeSpec
        
        return {
            "basic": FacadeSpec(
                fields=["status", "class", "reason_code", "period_start"],
                required_fields=["status", "class"],
                field_examples={
                    "status": "finished",
                    "class": "outpatient",
                    "reason_code": [{"text": "routine checkup"}],
                    "period_start": "2024-08-15T09:00:00"
                },
                field_types={
                    "status": "EncounterStatus",
                    "class": "str",
                    "reason_code": "list[dict[str, Any]]",
                    "period_start": "datetime | None"
                },
                description="Essential encounter information and visit reason",
                llm_guidance="Use this facade for extracting basic encounter details from clinical notes. Focus on visit type, status, and chief complaint.",
                conversational_prompts=[
                    "What type of visit was this?",
                    "Why did the patient come in?",
                    "When did the encounter take place?"
                ]
            ),
            
            "timing": FacadeSpec(
                fields=["status", "class", "period_start", "period_end", "length"],
                required_fields=["status", "class"],
                field_examples={
                    "status": "finished",
                    "class": "outpatient",
                    "period_start": "2024-08-15T14:00:00",
                    "period_end": "2024-08-15T14:45:00",
                    "length": {"value": 45, "unit": "minutes"}
                },
                field_types={
                    "status": "EncounterStatus",
                    "class": "str",
                    "period_start": "datetime | None",
                    "period_end": "datetime | None",
                    "length": "dict[str, Any] | None"
                },
                description="Encounter timing and duration information",
                llm_guidance="Extract detailed timing information when appointment schedules, duration, or visit time periods are documented.",
                conversational_prompts=[
                    "How long was the appointment?",
                    "What time did the visit start and end?",
                    "When was this encounter scheduled?"
                ]
            ),
            
            "participants": FacadeSpec(
                fields=["status", "class", "subject", "participant", "service_provider"],
                required_fields=["status", "class"],
                field_examples={
                    "status": "finished",
                    "class": "outpatient",
                    "subject": "Patient/patient-123",
                    "participant": [{"individual": "Practitioner/dr-smith", "type_": ["primary"]}],
                    "service_provider": "Organization/clinic-main"
                },
                field_types={
                    "status": "EncounterStatus",
                    "class": "str",
                    "subject": "str | None",
                    "participant": "list[EncounterParticipant]",
                    "service_provider": "str | None"
                },
                description="Encounter participants and service providers",
                llm_guidance="Use when extracting information about who was involved in the encounter - patients, providers, and organizations.",
                conversational_prompts=[
                    "Who participated in this encounter?",
                    "Which healthcare providers were involved?",
                    "Where did this encounter take place?"
                ]
            ),
            
            "clinical": FacadeSpec(
                fields=["status", "class", "reason_code", "reason_reference", "diagnosis"],
                required_fields=["status", "class"],
                field_examples={
                    "status": "finished",
                    "class": "outpatient",
                    "reason_code": [{"text": "chest pain"}, {"text": "shortness of breath"}],
                    "reason_reference": ["Condition/hypertension-001"],
                    "diagnosis": [{"condition": "Condition/angina-002", "use": "primary", "rank": 1}]
                },
                field_types={
                    "status": "EncounterStatus",
                    "class": "str",
                    "reason_code": "list[dict[str, Any]]",
                    "reason_reference": "list[str]",
                    "diagnosis": "list[EncounterDiagnosis]"
                },
                description="Clinical reasons and diagnoses for the encounter",
                llm_guidance="Extract comprehensive clinical information when diagnoses, medical conditions, or detailed reasons for the visit are documented.",
                conversational_prompts=[
                    "What diagnoses were made during this encounter?",
                    "What were the clinical reasons for this visit?",
                    "What conditions were addressed?"
                ]
            ),
            
            "complete": FacadeSpec(
                fields=["status", "class", "subject", "period_start", "period_end", "reason_code", "diagnosis", "participant", "service_provider"],
                required_fields=["status", "class"],
                field_examples={
                    "status": "finished",
                    "class": "inpatient",
                    "subject": "Patient/patient-456",
                    "period_start": "2024-08-15T08:00:00",
                    "period_end": "2024-08-17T12:00:00",
                    "reason_code": [{"text": "elective surgery"}],
                    "diagnosis": [{"condition": "Condition/appendicitis", "use": "primary"}],
                    "participant": [{"individual": "Practitioner/surgeon-jones", "type_": ["surgeon"]}],
                    "service_provider": "Organization/hospital-general"
                },
                field_types={
                    "status": "EncounterStatus",
                    "class": "str",
                    "subject": "str | None",
                    "period_start": "datetime | None",
                    "period_end": "datetime | None",
                    "reason_code": "list[dict[str, Any]]",
                    "diagnosis": "list[EncounterDiagnosis]",
                    "participant": "list[EncounterParticipant]",
                    "service_provider": "str | None"
                },
                description="Comprehensive encounter information with all key details",
                llm_guidance="Use for extracting complete encounter documentation when comprehensive visit information including timing, participants, diagnoses, and clinical details are available.",
                conversational_prompts=[
                    "Can you provide a complete summary of this encounter?",
                    "What are all the details about this healthcare visit?",
                    "Document the full encounter information"
                ]
            )
        }
