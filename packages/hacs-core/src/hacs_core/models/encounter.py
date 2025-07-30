"""
Encounter model for healthcare encounters and visits.

This module provides the Encounter model with FHIR-compliant fields,
participant management, and agent-centric features for healthcare workflows.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from ..base_resource import BaseResource
from pydantic import Field, computed_field, field_validator, model_validator


class EncounterStatus(str, Enum):
    """FHIR-compliant encounter status codes."""

    PLANNED = "planned"
    ARRIVED = "arrived"
    TRIAGED = "triaged"
    IN_PROGRESS = "in-progress"
    ONLEAVE = "onleave"
    FINISHED = "finished"
    CANCELLED = "cancelled"
    ENTERED_IN_ERROR = "entered-in-error"
    UNKNOWN = "unknown"


class EncounterClass(str, Enum):
    """FHIR-compliant encounter class codes."""

    AMB = "AMB"  # ambulatory
    EMER = "EMER"  # emergency
    FLD = "FLD"  # field
    HH = "HH"  # home health
    IMP = "IMP"  # inpatient encounter
    ACUTE = "ACUTE"  # inpatient acute
    NONAC = "NONAC"  # inpatient non-acute
    OBSENC = "OBSENC"  # observation encounter
    PRENC = "PRENC"  # pre-admission
    SS = "SS"  # short stay
    VR = "VR"  # virtual


class ParticipantType(str, Enum):
    """Types of encounter participants."""

    ATTENDING = "attending"
    CONSULTANT = "consultant"
    PRIMARY_CARE = "primary_care"
    ADMITTER = "admitter"
    DISCHARGER = "discharger"
    EMERGENCY = "emergency"
    AGENT = "agent"
    PATIENT = "patient"
    FAMILY = "family"
    CAREGIVER = "caregiver"
    TRANSLATOR = "translator"


class LocationStatus(str, Enum):
    """Status of location during encounter."""

    PLANNED = "planned"
    ACTIVE = "active"
    RESERVED = "reserved"
    COMPLETED = "completed"


class Encounter(BaseResource):
    """
    Represents a healthcare encounter or visit.

    This model includes comprehensive encounter information with FHIR compliance,
    participant management, and agent-centric features for healthcare workflows.
    """

    resource_type: Literal["Encounter"] = Field(
        default="Encounter", description="Resource type identifier"
    )

    # Core encounter fields
    status: EncounterStatus = Field(
        description="Current status of the encounter",
        examples=["planned", "in-progress", "finished"],
    )

    class_fhir: EncounterClass = Field(
        alias="class",
        description="Classification of patient encounter",
        examples=["AMB", "EMER", "IMP"],
    )

    type: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Specific type of encounter",
        examples=[
            [
                {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "185349003",
                            "display": "Encounter for check up",
                        }
                    ]
                }
            ]
        ],
    )

    priority: dict[str, Any] | None = Field(
        default=None,
        description="Indicates the urgency of the encounter",
        examples=[
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ActPriority",
                        "code": "R",
                        "display": "routine",
                    }
                ]
            }
        ],
    )

    # Subject and participants
    subject: str = Field(
        description="The patient present at the encounter",
        examples=["patient-001", "patient-123"],
    )

    participants: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of participants involved in the encounter",
        examples=[
            [
                {
                    "type": "attending",
                    "individual": "practitioner-001",
                    "period": {
                        "start": "2024-01-15T09:00:00Z",
                        "end": "2024-01-15T10:30:00Z",
                    },
                },
                {
                    "type": "agent",
                    "individual": "agent-primary-care",
                    "period": {"start": "2024-01-15T09:00:00Z"},
                },
            ]
        ],
    )

    # Timing
    period: dict[str, Any] = Field(
        description="The start and end time of the encounter",
        examples=[{"start": "2024-01-15T09:00:00Z", "end": "2024-01-15T10:30:00Z"}],
    )

    length: dict[str, Any] | None = Field(
        default=None,
        description="Quantity of time the encounter lasted",
        examples=[
            {
                "value": 90,
                "unit": "min",
                "system": "http://unitsofmeasure.org",
                "code": "min",
            }
        ],
    )

    # Reason and diagnosis
    reason_code: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Coded reason the encounter takes place",
        examples=[
            [
                {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "25064002",
                            "display": "Headache",
                        }
                    ]
                }
            ]
        ],
    )

    reason_reference: list[str] = Field(
        default_factory=list,
        description="References to conditions or procedures that are the reason for the encounter",
        examples=[["condition-001", "procedure-002"]],
    )

    diagnosis: list[dict[str, Any]] = Field(
        default_factory=list,
        description="The list of diagnosis relevant to this encounter",
        examples=[
            [
                {
                    "condition": "condition-001",
                    "use": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/diagnosis-role",
                                "code": "AD",
                                "display": "Admission diagnosis",
                            }
                        ]
                    },
                    "rank": 1,
                }
            ]
        ],
    )

    # Location
    location: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of locations where the patient has been",
        examples=[
            [
                {
                    "location": "location-001",
                    "status": "active",
                    "period": {
                        "start": "2024-01-15T09:00:00Z",
                        "end": "2024-01-15T10:30:00Z",
                    },
                }
            ]
        ],
    )

    # Service provider
    service_provider: str | None = Field(
        default=None,
        description="The organization responsible for this encounter",
        examples=["organization-001", None],
    )

    # Agent-centric fields
    agent_context: dict[str, Any] = Field(
        default_factory=dict,
        description="Agent-specific context and metadata",
        examples=[
            {
                "primary_agent": "agent-cardiology",
                "agent_handoffs": 2,
                "automated_tasks": ["vitals_monitoring", "medication_reminders"],
                "decision_support_used": True,
                "ai_recommendations": [
                    {
                        "type": "diagnostic_suggestion",
                        "confidence": 0.85,
                        "content": "Consider ECG based on chest pain symptoms",
                    }
                ],
            }
        ],
    )

    # Workflow and administrative
    appointment: str | None = Field(
        default=None,
        description="The appointment that scheduled this encounter",
        examples=["appointment-001", None],
    )

    based_on: list[str] = Field(
        default_factory=list,
        description="The request this encounter satisfies",
        examples=[["service-request-001", "care-plan-002"]],
    )

    part_of: str | None = Field(
        default=None,
        description="Another encounter this encounter is part of",
        examples=["encounter-parent-001", None],
    )

    # Clinical metadata
    account: list[str] = Field(
        default_factory=list,
        description="The set of accounts that may be used for billing",
        examples=[["account-001", "account-insurance-002"]],
    )

    hospitalization: dict[str, Any] | None = Field(
        default=None,
        description="Details about the admission to a healthcare service",
        examples=[
            {
                "pre_admission_identifier": "pre-admit-001",
                "origin": "location-emergency",
                "admit_source": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/admit-source",
                            "code": "emd",
                            "display": "From accident/emergency department",
                        }
                    ]
                },
                "re_admission": False,
                "discharge_disposition": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/discharge-disposition",
                            "code": "home",
                            "display": "Home",
                        }
                    ]
                },
            }
        ],
    )

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, v: str) -> str:
        """Ensure subject is not empty."""
        if not v.strip():
            raise ValueError("Subject (patient) cannot be empty")
        return v.strip()

    @field_validator("period")
    @classmethod
    def validate_period(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate period structure."""
        if not isinstance(v, dict):
            raise ValueError("Period must be a dictionary")
        if "start" not in v:
            raise ValueError("Period must have a 'start' field")
        return v

    @model_validator(mode="after")
    def validate_period_consistency(self) -> "Encounter":
        """Validate that period end is after start if both are provided."""
        if (
            isinstance(self.period, dict)
            and "start" in self.period
            and "end" in self.period
        ):
            try:
                start = datetime.fromisoformat(
                    self.period["start"].replace("Z", "+00:00")
                )
                end = datetime.fromisoformat(self.period["end"].replace("Z", "+00:00"))
                if end <= start:
                    raise ValueError("Encounter end time must be after start time")
            except ValueError as ve:
                # Re-raise ValueError for validation errors, catch only parsing errors
                if "Encounter end time must be after start time" in str(ve):
                    raise
                # If we can't parse the dates, let it pass (will be caught elsewhere)
                pass
        return self

    @computed_field
    @property
    def is_active(self) -> bool:
        """Computed field indicating if encounter is currently active."""
        active_statuses = [
            EncounterStatus.ARRIVED,
            EncounterStatus.TRIAGED,
            EncounterStatus.IN_PROGRESS,
            EncounterStatus.ONLEAVE,
        ]
        return self.status in active_statuses

    @computed_field
    @property
    def is_completed(self) -> bool:
        """Computed field indicating if encounter is completed."""
        completed_statuses = [
            EncounterStatus.FINISHED,
            EncounterStatus.CANCELLED,
            EncounterStatus.ENTERED_IN_ERROR,
        ]
        return self.status in completed_statuses

    @computed_field
    @property
    def duration_minutes(self) -> float | None:
        """Computed field for encounter duration in minutes."""
        if not isinstance(self.period, dict) or "start" not in self.period:
            return None

        try:
            start = datetime.fromisoformat(self.period["start"].replace("Z", "+00:00"))

            if "end" in self.period:
                end = datetime.fromisoformat(self.period["end"].replace("Z", "+00:00"))
            else:
                # If no end time and encounter is active, use current time
                if self.is_active:
                    end = datetime.now(timezone.utc)
                else:
                    return None

            duration = end - start
            return duration.total_seconds() / 60
        except (ValueError, TypeError):
            return None

    @computed_field
    @property
    def participant_count(self) -> int:
        """Computed field for number of participants."""
        return len(self.participants)

    def add_participant(
        self,
        participant_type: str,
        individual_id: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> None:
        """
        Add a participant to the encounter.

        Args:
            participant_type: Type of participant (attending, agent, etc.)
            individual_id: ID of the individual
            start_time: When participation started
            end_time: When participation ended
        """
        participant = {
            "type": participant_type,
            "individual": individual_id,
            "period": {},
        }

        if start_time:
            participant["period"]["start"] = start_time.isoformat()
        if end_time:
            participant["period"]["end"] = end_time.isoformat()

        self.participants.append(participant)
        self.update_timestamp()

    def remove_participant(self, individual_id: str) -> bool:
        """
        Remove a participant from the encounter.

        Args:
            individual_id: ID of the individual to remove

        Returns:
            True if participant was removed, False if not found
        """
        original_count = len(self.participants)
        self.participants = [
            p for p in self.participants if p.get("individual") != individual_id
        ]

        if len(self.participants) < original_count:
            self.update_timestamp()
            return True
        return False

    def update_status(
        self, new_status: EncounterStatus, timestamp: datetime | None = None
    ) -> None:
        """
        Update the encounter status.

        Args:
            new_status: New status for the encounter
            timestamp: Timestamp of status change (defaults to now)
        """
        old_status = self.status
        self.status = new_status

        # Update agent context with status change
        if "status_history" not in self.agent_context:
            self.agent_context["status_history"] = []

        status_change = {
            "from": old_status,
            "to": new_status,
            "timestamp": (timestamp or datetime.now(timezone.utc)).isoformat(),
        }
        self.agent_context["status_history"].append(status_change)

        # If finishing the encounter, set end time if not already set
        if (
            new_status == EncounterStatus.FINISHED
            and isinstance(self.period, dict)
            and "end" not in self.period
        ):
            self.period["end"] = (timestamp or datetime.now(timezone.utc)).isoformat()

        self.update_timestamp()

    def link_to_agent_session(
        self, agent_id: str, session_data: dict[str, Any]
    ) -> None:
        """
        Link encounter to an agent session.

        Args:
            agent_id: ID of the agent
            session_data: Session metadata
        """
        if "agent_sessions" not in self.agent_context:
            self.agent_context["agent_sessions"] = []

        session_info = {
            "agent_id": agent_id,
            "session_start": datetime.now(timezone.utc).isoformat(),
            **session_data,
        }
        self.agent_context["agent_sessions"].append(session_info)
        self.update_timestamp()

    def get_duration(self, as_of_time: datetime | None = None) -> float | None:
        """
        Get encounter duration in minutes.

        Args:
            as_of_time: Time to calculate duration as of (defaults to now)

        Returns:
            Duration in minutes, or None if start time not available
        """
        if not isinstance(self.period, dict) or "start" not in self.period:
            return None

        try:
            start = datetime.fromisoformat(self.period["start"].replace("Z", "+00:00"))

            # Use as_of_time if provided, otherwise use end time from period, otherwise use now
            if as_of_time is not None:
                end = as_of_time
            elif "end" in self.period:
                end = datetime.fromisoformat(self.period["end"].replace("Z", "+00:00"))
            else:
                end = datetime.now(timezone.utc)

            duration = end - start
            return duration.total_seconds() / 60
        except (ValueError, TypeError):
            return None

    def add_diagnosis(
        self, condition_id: str, diagnosis_role: str = "AD", rank: int | None = None
    ) -> None:
        """
        Add a diagnosis to the encounter.

        Args:
            condition_id: ID of the condition
            diagnosis_role: Role of the diagnosis (AD=admission, DD=discharge, etc.)
            rank: Ranking of the diagnosis
        """
        diagnosis = {
            "condition": condition_id,
            "use": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/diagnosis-role",
                        "code": diagnosis_role,
                        "display": "Diagnosis",
                    }
                ]
            },
        }

        if rank is not None:
            diagnosis["rank"] = rank

        self.diagnosis.append(diagnosis)
        self.update_timestamp()

    def add_location(
        self,
        location_id: str,
        status: LocationStatus = LocationStatus.ACTIVE,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> None:
        """
        Add a location to the encounter.

        Args:
            location_id: ID of the location
            status: Status at this location
            start_time: When patient arrived at location
            end_time: When patient left location
        """
        location_entry = {"location": location_id, "status": status, "period": {}}

        if start_time:
            location_entry["period"]["start"] = start_time.isoformat()
        if end_time:
            location_entry["period"]["end"] = end_time.isoformat()

        self.location.append(location_entry)
        self.update_timestamp()

    def update_agent_context(self, key: str, value: Any) -> None:
        """
        Update agent-specific context.

        Args:
            key: Context key
            value: Context value
        """
        self.agent_context[key] = value
        self.update_timestamp()

    def get_participants_by_type(self, participant_type: str) -> list[dict[str, Any]]:
        """
        Get participants by type.

        Args:
            participant_type: Type of participant to filter by

        Returns:
            List of matching participants
        """
        return [p for p in self.participants if p.get("type") == participant_type]

    def get_primary_agent(self) -> str | None:
        """
        Get the primary agent for this encounter.

        Returns:
            Agent ID or None if no primary agent set
        """
        return self.agent_context.get("primary_agent")

    def set_primary_agent(self, agent_id: str) -> None:
        """
        Set the primary agent for this encounter.

        Args:
            agent_id: ID of the primary agent
        """
        self.agent_context["primary_agent"] = agent_id
        self.update_timestamp()

    def is_emergency(self) -> bool:
        """
        Check if this is an emergency encounter.

        Returns:
            True if encounter class is emergency
        """
        return self.class_fhir == EncounterClass.EMER

    def is_inpatient(self) -> bool:
        """
        Check if this is an inpatient encounter.

        Returns:
            True if encounter class is inpatient
        """
        inpatient_classes = [
            EncounterClass.IMP,
            EncounterClass.ACUTE,
            EncounterClass.NONAC,
        ]
        return self.class_fhir in inpatient_classes

    def __repr__(self) -> str:
        """Enhanced representation including status, class, and duration."""
        duration_str = (
            f", {self.duration_minutes:.0f}min" if self.duration_minutes else ""
        )
        status_indicator = (
            "🟢" if self.is_active else "🔵" if self.is_completed else "⚪"
        )
        return f"Encounter(id='{self.id}', subject='{self.subject}', class='{self.class_fhir}', status='{self.status}'{status_indicator}{duration_str})"
