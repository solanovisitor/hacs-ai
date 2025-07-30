"""
HACS Appointment Model - FHIR R5 Compliant

This module implements the FHIR R5 Appointment resource with full compliance
to the healthcare interoperability standard. The Appointment resource represents
a booking of a healthcare event among patient(s), practitioner(s), related person(s)
and/or device(s) for a specific date/time.

FHIR R5 Appointment Resource:
https://hl7.org/fhir/R5/appointment.html

Key Features:
- Full FHIR R5 compliance with all 45+ fields
- Comprehensive validation rules and constraints
- Support for recurring appointments and series
- Participant management with roles and statuses
- Virtual service integration
- Waitlist and cancellation workflows
- LLM-friendly fields for AI applications
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from ..base_resource import BaseResource


class AppointmentStatus(str, Enum):
    """FHIR R5 Appointment Status codes."""
    PROPOSED = "proposed"
    PENDING = "pending"
    BOOKED = "booked"
    ARRIVED = "arrived"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"
    NOSHOW = "noshow"
    ENTERED_IN_ERROR = "entered-in-error"
    CHECKED_IN = "checked-in"
    WAITLIST = "waitlist"


class AppointmentCancellationReason(str, Enum):
    """Common appointment cancellation reasons."""
    PATIENT_REQUEST = "patient-request"
    PROVIDER_UNAVAILABLE = "provider-unavailable"
    EMERGENCY = "emergency"
    WEATHER = "weather"
    SYSTEM_ERROR = "system-error"
    NO_SHOW = "no-show"
    RESCHEDULED = "rescheduled"
    INSURANCE_ISSUE = "insurance-issue"
    FACILITY_CLOSURE = "facility-closure"
    OTHER = "other"


class ParticipantType(str, Enum):
    """FHIR R5 Participant Type codes."""
    PATIENT = "patient"
    PRACTITIONER = "practitioner"
    RELATED_PERSON = "related-person"
    LOCATION = "location"
    DEVICE = "device"
    HEALTHCARE_SERVICE = "healthcare-service"
    CARE_TEAM = "care-team"
    PRIMARY_PERFORMER = "primary-performer"
    TRANSLATOR = "translator"
    EMERGENCY_CONTACT = "emergency-contact"
    RESPONSIBLE_PARTY = "responsible-party"


class ParticipationStatus(str, Enum):
    """FHIR R5 Participation Status codes."""
    ACCEPTED = "accepted"
    DECLINED = "declined"
    TENTATIVE = "tentative"
    NEEDS_ACTION = "needs-action"


class AppointmentRecurrenceType(str, Enum):
    """Appointment recurrence pattern types."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class WeekOfMonth(str, Enum):
    """Week of month enumeration."""
    FIRST = "first"
    SECOND = "second"
    THIRD = "third"
    FOURTH = "fourth"
    LAST = "last"


class DaysOfWeek(str, Enum):
    """Days of the week enumeration."""
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class AppointmentPriority(str, Enum):
    """Appointment priority levels."""
    ROUTINE = "routine"
    URGENT = "urgent"
    ASAP = "asap"
    STAT = "stat"
    EMERGENCY = "emergency"


class VirtualServiceDetail(BaseModel):
    """Virtual service connection details."""
    channel_type: Optional[dict[str, Any]] = Field(
        None, description="Type of virtual service (video, phone, etc.)"
    )
    address_url: Optional[str] = Field(
        None, description="Contact address/number for virtual service"
    )
    address_string: Optional[str] = Field(
        None, description="Alternative string format address"
    )
    address_contact_point: Optional[dict[str, Any]] = Field(
        None, description="Contact point for virtual service"
    )
    address_extended_contact_detail: Optional[dict[str, Any]] = Field(
        None, description="Extended contact details"
    )
    additional_info: Optional[list[str]] = Field(
        None, description="Additional connection info"
    )
    max_participants: Optional[int] = Field(
        None, description="Maximum number of participants"
    )
    session_key: Optional[str] = Field(
        None, description="Session key/password if required"
    )


class WeeklyTemplate(BaseModel):
    """Weekly recurrence template."""
    monday: Optional[bool] = Field(None, description="Recurs on Mondays")
    tuesday: Optional[bool] = Field(None, description="Recurs on Tuesday")
    wednesday: Optional[bool] = Field(None, description="Recurs on Wednesday")
    thursday: Optional[bool] = Field(None, description="Recurs on Thursday")
    friday: Optional[bool] = Field(None, description="Recurs on Friday")
    saturday: Optional[bool] = Field(None, description="Recurs on Saturday")
    sunday: Optional[bool] = Field(None, description="Recurs on Sunday")
    week_interval: Optional[int] = Field(
        None, ge=1, description="Recurs every nth week"
    )


class MonthlyTemplate(BaseModel):
    """Monthly recurrence template."""
    day_of_month: Optional[int] = Field(
        None, ge=1, le=31, description="Recurs on a specific day of the month"
    )
    nth_week_of_month: Optional[WeekOfMonth] = Field(
        None, description="Indicates which week of the month"
    )
    day_of_week: Optional[DaysOfWeek] = Field(
        None, description="Indicates which day of the week"
    )
    month_interval: int = Field(
        1, ge=1, description="Recurs every nth month"
    )


class YearlyTemplate(BaseModel):
    """Yearly recurrence template."""
    year_interval: int = Field(
        1, ge=1, description="Recurs every nth year"
    )


class RecurrenceTemplate(BaseModel):
    """Appointment recurrence template."""
    timezone: Optional[dict[str, Any]] = Field(
        None, description="The timezone of the occurrences"
    )
    recurrence_type: AppointmentRecurrenceType = Field(
        ..., description="The frequency of the recurrence"
    )
    last_occurrence_date: Optional[datetime] = Field(
        None, description="The date when the recurrence should end"
    )
    occurrence_count: Optional[int] = Field(
        None, ge=1, description="The number of planned occurrences"
    )
    occurrence_date: Optional[list[datetime]] = Field(
        None, description="Specific dates for recurring appointments"
    )
    weekly_template: Optional[WeeklyTemplate] = Field(
        None, description="Information about weekly recurring appointments"
    )
    monthly_template: Optional[MonthlyTemplate] = Field(
        None, description="Information about monthly recurring appointments"
    )
    yearly_template: Optional[YearlyTemplate] = Field(
        None, description="Information about yearly recurring appointments"
    )
    excluding_date: Optional[list[datetime]] = Field(
        None, description="Any dates that should be excluded from the series"
    )
    excluding_recurrence_id: Optional[list[int]] = Field(
        None, description="Any recurrence IDs that should be excluded"
    )


class AppointmentParticipant(BaseModel):
    """Participant in an appointment."""
    type: Optional[list[dict[str, Any]]] = Field(
        None, description="Role of participant in the appointment"
    )
    period: Optional[dict[str, Any]] = Field(
        None, description="Participation period of the actor"
    )
    actor: Optional[dict[str, Any]] = Field(
        None, description="The individual, device, location, or service participating"
    )
    required: Optional[bool] = Field(
        None, description="The participant is required to attend"
    )
    status: ParticipationStatus = Field(
        ..., description="Participation status"
    )

    # LLM-friendly fields
    participant_name: Optional[str] = Field(
        None, description="Display name of the participant"
    )
    participant_role: Optional[str] = Field(
        None, description="Primary role description"
    )
    is_required: Optional[bool] = Field(
        None, description="Whether this participant must attend"
    )
    contact_info: Optional[str] = Field(
        None, description="Contact information for the participant"
    )

    @model_validator(mode="after")
    def validate_participant(self) -> "AppointmentParticipant":
        """Validate that either type or actor is specified."""
        if not self.type and not self.actor:
            raise ValueError("Either type or actor must be specified for participant")
        return self


class Appointment(BaseResource):
    """
    FHIR R5 Appointment Resource

    A booking of a healthcare event among patient(s), practitioner(s),
    related person(s) and/or device(s) for a specific date/time.
    """

    resource_type: Literal["Appointment"] = Field(
        default="Appointment", description="Resource type identifier"
    )

    # FHIR R5 Core Fields
    identifier: Optional[list[dict[str, Any]]] = Field(
        None, description="External Ids for this item"
    )
    status: AppointmentStatus = Field(
        ..., description="Current status of the appointment"
    )
    cancellation_reason: Optional[dict[str, Any]] = Field(
        None, description="The coded reason for the appointment being cancelled"
    )
    class_: Optional[list[dict[str, Any]]] = Field(
        None, alias="class", description="Classification when becoming an encounter"
    )
    service_category: Optional[list[dict[str, Any]]] = Field(
        None, description="A broad categorization of the service"
    )
    service_type: Optional[list[dict[str, Any]]] = Field(
        None, description="The specific service to be performed"
    )
    specialty: Optional[list[dict[str, Any]]] = Field(
        None, description="The specialty of a practitioner required"
    )
    appointment_type: Optional[dict[str, Any]] = Field(
        None, description="The style of appointment or patient type"
    )
    reason: Optional[list[dict[str, Any]]] = Field(
        None, description="Reason this appointment is scheduled"
    )
    priority: Optional[dict[str, Any]] = Field(
        None, description="Used to make informed decisions if needing to re-prioritize"
    )
    description: Optional[str] = Field(
        None, description="Shown on a subject line in a meeting request"
    )
    replaces: Optional[list[dict[str, Any]]] = Field(
        None, description="Appointment replaced by this Appointment"
    )
    virtual_service: Optional[list[VirtualServiceDetail]] = Field(
        None, description="Connection details of a virtual service"
    )
    supporting_information: Optional[list[dict[str, Any]]] = Field(
        None, description="Additional information to support the appointment"
    )
    previous_appointment: Optional[dict[str, Any]] = Field(
        None, description="The previous appointment in a series"
    )
    originating_appointment: Optional[dict[str, Any]] = Field(
        None, description="The originating appointment in a recurring set"
    )
    start: Optional[datetime] = Field(
        None, description="When appointment is to take place"
    )
    end: Optional[datetime] = Field(
        None, description="When appointment is to conclude"
    )
    minutes_duration: Optional[int] = Field(
        None, ge=1, description="Can be less than start/end (e.g. estimate)"
    )
    requested_period: Optional[list[dict[str, Any]]] = Field(
        None, description="Potential date/time interval(s) requested"
    )
    slot: Optional[list[dict[str, Any]]] = Field(
        None, description="The slots that this appointment is filling"
    )
    account: Optional[list[dict[str, Any]]] = Field(
        None, description="The set of accounts that may be used for billing"
    )
    created: Optional[datetime] = Field(
        None, description="The date that this appointment was initially created"
    )
    cancellation_date: Optional[datetime] = Field(
        None, description="When the appointment was cancelled"
    )
    note: Optional[list[dict[str, Any]]] = Field(
        None, description="Additional comments"
    )
    patient_instruction: Optional[list[dict[str, Any]]] = Field(
        None, description="Detailed information and instructions for the patient"
    )
    based_on: Optional[list[dict[str, Any]]] = Field(
        None, description="The request this appointment is allocated to assess"
    )
    subject: Optional[dict[str, Any]] = Field(
        None, description="The patient or group associated with the appointment"
    )
    participant: list[AppointmentParticipant] = Field(
        ..., min_length=1, description="Participants involved in appointment"
    )
    recurrence_id: Optional[int] = Field(
        None, ge=1, description="The sequence number in the recurrence"
    )
    occurrence_changed: Optional[bool] = Field(
        None, description="Indicates that this appointment varies from a recurrence pattern"
    )
    recurrence_template: Optional[list[RecurrenceTemplate]] = Field(
        None, description="Details of the recurrence pattern/template"
    )

    # LLM-friendly fields
    appointment_title: Optional[str] = Field(
        None, description="Human-readable title for the appointment"
    )
    patient_name: Optional[str] = Field(
        None, description="Primary patient name for display"
    )
    provider_name: Optional[str] = Field(
        None, description="Primary provider name for display"
    )
    location_name: Optional[str] = Field(
        None, description="Location name for display"
    )
    duration_minutes: Optional[int] = Field(
        None, ge=1, description="Total duration in minutes"
    )
    is_virtual: Optional[bool] = Field(
        None, description="Whether this is a virtual appointment"
    )
    is_recurring: Optional[bool] = Field(
        None, description="Whether this is part of a recurring series"
    )
    urgency_level: Optional[AppointmentPriority] = Field(
        None, description="Clinical urgency level"
    )
    preparation_required: Optional[bool] = Field(
        None, description="Whether patient preparation is required"
    )
    confirmation_required: Optional[bool] = Field(
        None, description="Whether confirmation is needed"
    )
    can_reschedule: Optional[bool] = Field(
        None, description="Whether appointment can be rescheduled"
    )
    estimated_cost: Optional[float] = Field(
        None, ge=0, description="Estimated cost for the appointment"
    )
    insurance_required: Optional[bool] = Field(
        None, description="Whether insurance verification is required"
    )

    def __init__(self, **data):
        if "id" not in data:
            data["id"] = str(uuid.uuid4())
        if "created" not in data:
            data["created"] = datetime.now(timezone.utc)
        super().__init__(**data)

    @field_validator("start", "end", "created", "cancellation_date")
    @classmethod
    def validate_datetime_timezone(cls, v):
        """Ensure datetime fields are timezone-aware."""
        if v and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    @model_validator(mode="after")
    def validate_appointment_constraints(self) -> "Appointment":
        """Validate FHIR R5 appointment constraints."""
        # Rule: Either start and end are specified, or neither
        start_exists = self.start is not None
        end_exists = self.end is not None
        if start_exists != end_exists:
            raise ValueError("Either both start and end must be specified, or neither")

        # Rule: Only proposed/cancelled/waitlist appointments can be missing start/end dates
        if not start_exists and self.status not in [
            AppointmentStatus.PROPOSED,
            AppointmentStatus.CANCELLED,
            AppointmentStatus.WAITLIST
        ]:
            raise ValueError(
                "Only proposed, cancelled, or waitlist appointments can be missing start/end dates"
            )

        # Rule: Cancellation reason is only used for cancelled/noshow appointments
        if self.cancellation_reason and self.status not in [
            AppointmentStatus.CANCELLED,
            AppointmentStatus.NOSHOW
        ]:
            raise ValueError(
                "Cancellation reason can only be used for cancelled or noshow appointments"
            )

        # Rule: Cancellation date is only used for cancelled/noshow appointments
        if self.cancellation_date and self.status not in [
            AppointmentStatus.CANCELLED,
            AppointmentStatus.NOSHOW
        ]:
            raise ValueError(
                "Cancellation date can only be used for cancelled or noshow appointments"
            )

        # Rule: The start must be less than or equal to the end
        if self.start and self.end and self.start > self.end:
            raise ValueError("Start time must be less than or equal to end time")

        return self

    # Helper properties
    @property
    def display_name(self) -> str:
        """Human-readable display name for the appointment."""
        if self.appointment_title:
            return self.appointment_title
        if self.description:
            return self.description

        # Build from components
        parts = []
        if self.patient_name:
            parts.append(f"Patient: {self.patient_name}")
        if self.provider_name:
            parts.append(f"Provider: {self.provider_name}")
        if self.service_type and len(self.service_type) > 0:
            service = self.service_type[0]
            if isinstance(service, dict) and service.get("text"):
                parts.append(f"Service: {service['text']}")

        return " | ".join(parts) if parts else f"Appointment {self.id[:8]}"

    @property
    def duration_display(self) -> str:
        """Human-readable duration display."""
        if self.minutes_duration:
            hours = self.minutes_duration // 60
            minutes = self.minutes_duration % 60
            if hours > 0:
                return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
            return f"{minutes}m"

        if self.start and self.end:
            delta = self.end - self.start
            total_minutes = int(delta.total_seconds() / 60)
            hours = total_minutes // 60
            minutes = total_minutes % 60
            if hours > 0:
                return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
            return f"{minutes}m"

        return "Duration unknown"

    @property
    def time_display(self) -> str:
        """Human-readable time display."""
        if self.start:
            if self.end:
                return f"{self.start.strftime('%Y-%m-%d %H:%M')} - {self.end.strftime('%H:%M')}"
            return f"{self.start.strftime('%Y-%m-%d %H:%M')}"
        return "Time TBD"

    @property
    def status_display(self) -> str:
        """Human-readable status display."""
        status_map = {
            AppointmentStatus.PROPOSED: "Proposed",
            AppointmentStatus.PENDING: "Pending Confirmation",
            AppointmentStatus.BOOKED: "Confirmed",
            AppointmentStatus.ARRIVED: "Patient Arrived",
            AppointmentStatus.FULFILLED: "Completed",
            AppointmentStatus.CANCELLED: "Cancelled",
            AppointmentStatus.NOSHOW: "No Show",
            AppointmentStatus.ENTERED_IN_ERROR: "Error",
            AppointmentStatus.CHECKED_IN: "Checked In",
            AppointmentStatus.WAITLIST: "Waitlisted"
        }
        return status_map.get(self.status, str(self.status))

    # Helper methods
    def get_patient_participant(self) -> Optional[AppointmentParticipant]:
        """Get the patient participant from the appointment."""
        for participant in self.participant:
            if participant.type:
                for ptype in participant.type:
                    if isinstance(ptype, dict) and ptype.get("text") and "patient" in ptype["text"].lower():
                        return participant
            if participant.participant_role and "patient" in participant.participant_role.lower():
                return participant
        return None

    def get_provider_participants(self) -> list[AppointmentParticipant]:
        """Get all provider participants from the appointment."""
        providers = []
        for participant in self.participant:
            if participant.type:
                for ptype in participant.type:
                    if isinstance(ptype, dict) and ptype.get("text"):
                        if any(role in ptype["text"].lower() for role in ["practitioner", "provider", "doctor", "nurse"]):
                            providers.append(participant)
                            break
            elif participant.participant_role and any(role in participant.participant_role.lower() for role in ["practitioner", "provider", "doctor", "nurse"]):
                providers.append(participant)
        return providers

    def get_location_participant(self) -> Optional[AppointmentParticipant]:
        """Get the location participant from the appointment."""
        for participant in self.participant:
            if participant.type:
                for ptype in participant.type:
                    if isinstance(ptype, dict) and ptype.get("text") and "location" in ptype["text"].lower():
                        return participant
            if participant.participant_role and "location" in participant.participant_role.lower():
                return participant
        return None

    def is_confirmed(self) -> bool:
        """Check if appointment is confirmed."""
        return self.status == AppointmentStatus.BOOKED

    def is_cancelled(self) -> bool:
        """Check if appointment is cancelled."""
        return self.status in [AppointmentStatus.CANCELLED, AppointmentStatus.NOSHOW]

    def is_completed(self) -> bool:
        """Check if appointment is completed."""
        return self.status == AppointmentStatus.FULFILLED

    def can_be_cancelled(self) -> bool:
        """Check if appointment can be cancelled."""
        return self.status in [
            AppointmentStatus.PROPOSED,
            AppointmentStatus.PENDING,
            AppointmentStatus.BOOKED,
            AppointmentStatus.ARRIVED,
            AppointmentStatus.CHECKED_IN,
            AppointmentStatus.WAITLIST
        ]

    def requires_confirmation(self) -> bool:
        """Check if appointment requires confirmation."""
        return self.status in [AppointmentStatus.PROPOSED, AppointmentStatus.PENDING]

    def get_service_summary(self) -> str:
        """Get a summary of services for this appointment."""
        services = []

        if self.service_category:
            for category in self.service_category:
                if isinstance(category, dict) and category.get("text"):
                    services.append(f"Category: {category['text']}")

        if self.service_type:
            for service in self.service_type:
                if isinstance(service, dict) and service.get("text"):
                    services.append(f"Type: {service['text']}")

        if self.specialty:
            for spec in self.specialty:
                if isinstance(spec, dict) and spec.get("text"):
                    services.append(f"Specialty: {spec['text']}")

        return " | ".join(services) if services else "General Appointment"

    def get_participants_summary(self) -> str:
        """Get a summary of all participants."""
        summary = []

        patient = self.get_patient_participant()
        if patient and patient.participant_name:
            summary.append(f"Patient: {patient.participant_name}")

        providers = self.get_provider_participants()
        for provider in providers:
            if provider.participant_name:
                role = provider.participant_role or "Provider"
                summary.append(f"{role}: {provider.participant_name}")

        location = self.get_location_participant()
        if location and location.participant_name:
            summary.append(f"Location: {location.participant_name}")

        return " | ".join(summary) if summary else f"{len(self.participant)} participants"

    def to_calendar_summary(self) -> dict[str, Any]:
        """Convert appointment to calendar-friendly summary."""
        return {
            "id": self.id,
            "title": self.display_name,
            "start": self.start.isoformat() if self.start else None,
            "end": self.end.isoformat() if self.end else None,
            "duration": self.duration_display,
            "status": self.status_display,
            "description": self.description,
            "location": self.location_name,
            "participants": self.get_participants_summary(),
            "service": self.get_service_summary(),
            "virtual": bool(self.virtual_service),
            "recurring": bool(self.recurrence_template),
            "urgency": self.urgency_level.value if self.urgency_level else None,
        }

    def to_clinical_summary(self) -> dict[str, Any]:
        """Convert appointment to clinical summary format."""
        return {
            "appointment_id": self.id,
            "patient": self.patient_name or "Unknown Patient",
            "provider": self.provider_name or "Unknown Provider",
            "scheduled_time": self.time_display,
            "duration": self.duration_display,
            "service_type": self.get_service_summary(),
            "status": self.status_display,
            "location": self.location_name or "Location TBD",
            "virtual_appointment": bool(self.virtual_service),
            "urgency": self.urgency_level.value if self.urgency_level else "routine",
            "preparation_required": bool(self.preparation_required),
            "confirmation_needed": self.requires_confirmation(),
            "cancellation_reason": self.cancellation_reason.get("text") if self.cancellation_reason else None,
            "notes": [note.get("text") for note in (self.note or []) if isinstance(note, dict) and note.get("text")],
            "created_date": self.created.isoformat() if self.created else None,
        }


# Type aliases for different appointment contexts
MedicalAppointment = Appointment
TelehealthAppointment = Appointment
ConsultationAppointment = Appointment
FollowUpAppointment = Appointment
EmergencyAppointment = Appointment