"""
HACS Event - FHIR Event Pattern Inspired Resource

This module defines a generic Event resource aligned with the FHIR R4 Event pattern.
It provides common fields that appear across event-like resources (Procedure,
MedicationAdministration, DiagnosticReport, etc.) for agent-centric workflows.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from .base_resource import DomainResource
from .observation import CodeableConcept


class EventPerformer(DomainResource):
    resource_type: Literal["EventPerformer"] = Field(default="EventPerformer")

    role: CodeableConcept | None = Field(default=None, description="Role of the performer")
    actor: str | None = Field(
        default=None, description="Reference to the performer (Practitioner/Organization)"
    )


class Event(DomainResource):
    """
    Event resource representing an occurrence in time related to a subject.

    This is a generic HACS resource inspired by the FHIR Event pattern and intended
    for agent workflows that need a lightweight, uniform representation of events.
    """

    resource_type: Literal["Event"] = Field(default="Event", description="Resource type identifier")

    # Ordering / provenance
    instantiates_canonical: list[str] = Field(
        default_factory=list, description="Instantiates canonical definitions"
    )
    instantiates_uri: list[str] = Field(
        default_factory=list, description="Instantiates external definitions by URI"
    )
    based_on: list[str] = Field(
        default_factory=list, description="Fulfills orders/proposals (ServiceRequest, etc.)"
    )
    part_of: list[str] = Field(default_factory=list, description="Part of larger event")

    # Status and classification
    status: str = Field(default="in-progress", description="Status of the event")
    status_reason: CodeableConcept | None = Field(
        default=None, description="Reason for current status"
    )
    category: CodeableConcept | None = Field(
        default=None, description="High-level categorization of the event"
    )
    code: CodeableConcept | None = Field(default=None, description="What the event is")

    # Clinical context
    subject: str | None = Field(
        default=None, description="Who/what the event is about (e.g., Patient/123)"
    )
    focus: str | None = Field(
        default=None, description="The focus of the event if different from subject"
    )
    encounter: str | None = Field(
        default=None, description="Encounter during which the event occurred"
    )

    # Occurrence
    occurrence_date_time: str | None = Field(default=None, description="When the event occurred")
    occurrence_start: str | None = Field(default=None, description="Start time if an interval")
    occurrence_end: str | None = Field(default=None, description="End time if an interval")
    recorded: str | None = Field(
        default=None, description="When this record was created/recorded"
    )

    # Participants and reasons
    performer: list[EventPerformer] = Field(
        default_factory=list, description="Who performed the event"
    )
    reason_code: list[CodeableConcept] = Field(
        default_factory=list, description="Why the event happened"
    )
    reason_reference: list[str] = Field(
        default_factory=list, description="References to justifications for event"
    )

    # Other context
    location: str | None = Field(default=None, description="Where the event occurred")
    supporting_info: list[str] = Field(
        default_factory=list, description="Additional supporting information"
    )
    note: list[str] = Field(default_factory=list, description="Comments about the event")

    @model_validator(mode="after")
    def _validate_occurrence(self) -> Event:
        # Ensure either point-in-time or interval is represented
        if self.occurrence_start and self.occurrence_end:
            # Basic lexical check; ignore detailed datetime validation for flexibility
            if self.occurrence_start > self.occurrence_end:
                raise ValueError("occurrence_start must be <= occurrence_end")
        return self

    # Convenience methods for agents
    def add_note(self, note: str) -> None:
        n = (note or "").strip()
        if n:
            self.note.append(n)
            self.update_timestamp()

    def add_performer(self, actor_ref: str, role_text: str | None = None) -> None:
        role = CodeableConcept(text=role_text) if role_text else None
        self.performer.append(EventPerformer(actor=actor_ref, role=role))
        self.update_timestamp()

    def set_status(self, status: str, reason_text: str | None = None) -> None:
        self.status = (status or "").strip() or self.status
        if reason_text:
            self.status_reason = CodeableConcept(text=reason_text)
        self.update_timestamp()

    def link_part_of(self, ref: str) -> None:
        if ref and ref not in self.part_of:
            self.part_of.append(ref)
            self.update_timestamp()

    def schedule(
        self, when: str | None = None, start: str | None = None, end: str | None = None
    ) -> None:
        if when:
            self.occurrence_date_time = when
            self.occurrence_start = None
            self.occurrence_end = None
        else:
            self.occurrence_start = start
            self.occurrence_end = end
            self.occurrence_date_time = None
        self.update_timestamp()

    def summarize(self) -> str:
        subject = self.subject or "Unknown"
        code_text = (
            (self.code.text if isinstance(self.code, CodeableConcept) else None)
            if self.code
            else None
        )
        status = self.status
        when = self.occurrence_date_time or (self.occurrence_start or "")
        return f"Event[{status}] for {subject}: {code_text or 'unspecified'} at {when or 'unspecified time'}"
