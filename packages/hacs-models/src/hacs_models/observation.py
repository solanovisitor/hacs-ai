"""
Observation model for clinical measurements and findings.

This module provides FHIR-compliant Observation models for recording
clinical measurements, laboratory results, vital signs, and other
healthcare observations.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import Field, field_validator

from .base_resource import DomainResource
from .types import ObservationStatus


class Coding(DomainResource):
    """A coded value from a terminology system."""
    
    resource_type: Literal["Coding"] = Field(default="Coding")
    
    system: str | None = Field(
        default=None,
        description="Identity of the terminology system",
        examples=["http://loinc.org", "http://snomed.info/sct"]
    )
    
    version: str | None = Field(
        default=None,
        description="Version of the system",
        max_length=50
    )
    
    code: str = Field(
        description="Symbol in syntax defined by the system",
        examples=["85354-9", "271649006"],
        max_length=100
    )
    
    display: str | None = Field(
        default=None,
        description="Representation defined by the system",
        examples=["Blood pressure", "Systolic blood pressure"],
        max_length=255
    )


class CodeableConcept(DomainResource):
    """A concept that may be defined by one or more codes."""
    
    resource_type: Literal["CodeableConcept"] = Field(default="CodeableConcept")
    
    coding: list[Coding] = Field(
        default_factory=list,
        description="Code defined by a terminology system"
    )
    
    text: str | None = Field(
        default=None,
        description="Plain text representation of the concept",
        max_length=500
    )


class Quantity(DomainResource):
    """A measured amount."""
    
    resource_type: Literal["Quantity"] = Field(default="Quantity")
    
    value: float | None = Field(
        default=None,
        description="Numerical value (with implicit precision)"
    )
    
    comparator: str | None = Field(
        default=None,
        description="< | <= | >= | > - how to understand the value",
        max_length=2
    )
    
    unit: str | None = Field(
        default=None,
        description="Unit representation",
        examples=["kg", "mmHg", "mg/dL"],
        max_length=50
    )
    
    system: str | None = Field(
        default=None,
        description="System that defines coded unit form",
        examples=["http://unitsofmeasure.org"]
    )
    
    code: str | None = Field(
        default=None,
        description="Coded form of the unit", 
        max_length=50
    )


class Range(DomainResource):
    """A range of values."""
    
    resource_type: Literal["Range"] = Field(default="Range")
    
    low: Quantity | None = Field(
        default=None,
        description="Low limit"
    )
    
    high: Quantity | None = Field(
        default=None,
        description="High limit"
    )


class Observation(DomainResource):
    """
    Measurements and simple assertions made about a patient.
    
    Observations are a central element in healthcare, used to support
    diagnosis, monitor progress, determine baselines and patterns, and
    capture demographic characteristics.
    """
    
    resource_type: Literal["Observation"] = Field(default="Observation")
    
    # Required fields
    status: ObservationStatus = Field(
        description="Status of the observation result"
    )
    
    code: CodeableConcept = Field(
        description="Type of observation (code / type)"
    )
    
    # Subject reference
    subject: str | None = Field(
        default=None,
        description="Who/what this observation is about",
        examples=["Patient/patient-123"]
    )
    
    # Context
    encounter: str | None = Field(
        default=None,
        description="Healthcare encounter during which this observation was made",
        examples=["Encounter/encounter-456"]
    )
    
    # Timing
    effective_date_time: datetime | None = Field(
        default=None,
        description="Clinically relevant time/time-period for observation"
    )
    
    issued: datetime | None = Field(
        default=None,
        description="Date/Time this version was made available"
    )
    
    # Performer
    performer: list[str] = Field(
        default_factory=list,
        description="Who is responsible for the observation",
        examples=[["Practitioner/dr-smith"]]
    )
    
    # Value - multiple types possible
    value_quantity: Quantity | None = Field(
        default=None,
        description="Actual result as a quantity"
    )
    
    value_codeable_concept: CodeableConcept | None = Field(
        default=None,
        description="Actual result as a coded concept"
    )
    
    value_string: str | None = Field(
        default=None,
        description="Actual result as a string",
        max_length=1000
    )
    
    value_boolean: bool | None = Field(
        default=None,
        description="Actual result as a boolean"
    )
    
    value_integer: int | None = Field(
        default=None,
        description="Actual result as an integer"
    )
    
    value_range: Range | None = Field(
        default=None,
        description="Actual result as a range"
    )
    
    # Data quality
    data_absent_reason: CodeableConcept | None = Field(
        default=None,
        description="Why the observation value is missing"
    )
    
    interpretation: list[CodeableConcept] = Field(
        default_factory=list,
        description="High, low, normal, etc."
    )
    
    note: list[str] = Field(
        default_factory=list,
        description="Comments about the observation",
        max_length=10
    )
    
    # Reference ranges
    reference_range: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Provides guide for interpretation"
    )
    
    # Related observations
    has_member: list[str] = Field(
        default_factory=list,
        description="Related resource that belongs to the Observation group"
    )
    
    derived_from: list[str] = Field(
        default_factory=list,
        description="Related measurements the observation is made from"
    )
    
    @field_validator("note")
    @classmethod
    def validate_notes(cls, v: list[str]) -> list[str]:
        """Validate observation notes."""
        cleaned = []
        for note in v:
            if not isinstance(note, str):
                raise ValueError("Notes must be strings")
            clean_note = note.strip()
            if clean_note:
                if len(clean_note) > 2000:
                    raise ValueError("Individual notes cannot exceed 2000 characters")
                cleaned.append(clean_note)
        return cleaned
    
    def add_note(self, note: str) -> None:
        """Add a note to the observation."""
        if note.strip():
            self.note.append(note.strip())
            self.update_timestamp()
    
    def set_quantity_value(self, value: float, unit: str, system: str | None = None) -> None:
        """Set a quantity value for the observation."""
        self.value_quantity = Quantity(
            value=value,
            unit=unit,
            system=system or "http://unitsofmeasure.org"
        )
        self.update_timestamp()
    
    def set_string_value(self, value: str) -> None:
        """Set a string value for the observation."""
        self.value_string = value
        self.update_timestamp()
    
    def set_boolean_value(self, value: bool) -> None:
        """Set a boolean value for the observation."""
        self.value_boolean = value
        self.update_timestamp()
    
    def get_value_summary(self) -> str:
        """Get a summary of the observation value."""
        if self.value_quantity:
            unit_str = f" {self.value_quantity.unit}" if self.value_quantity.unit else ""
            return f"{self.value_quantity.value}{unit_str}"
        elif self.value_string:
            return self.value_string
        elif self.value_boolean is not None:
            return str(self.value_boolean)
        elif self.value_integer is not None:
            return str(self.value_integer)
        elif self.value_codeable_concept:
            return self.value_codeable_concept.text or "Coded value"
        elif self.data_absent_reason:
            return f"Data absent: {self.data_absent_reason.text}"
        else:
            return "No value recorded"
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        code_display = self.code.text if self.code.text else "Observation"
        value_summary = self.get_value_summary()
        return f"{code_display}: {value_summary}"