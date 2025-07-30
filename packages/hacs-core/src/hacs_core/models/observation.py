"""
Observation model for healthcare measurements and findings.

This module provides the Observation model with FHIR-compliant fields,
code validation for LOINC/SNOMED CT, UCUM units, and agent-centric features.
Optimized for LLM generation with flexible validation and smart defaults.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal
import uuid

from ..base_resource import BaseResource
from pydantic import Field, computed_field, field_validator, model_validator


class ObservationStatus(str, Enum):
    """FHIR-compliant observation status codes."""

    REGISTERED = "registered"
    PRELIMINARY = "preliminary"
    FINAL = "final"
    AMENDED = "amended"
    CORRECTED = "corrected"
    CANCELLED = "cancelled"
    ENTERED_IN_ERROR = "entered-in-error"
    UNKNOWN = "unknown"


class ObservationCategory(str, Enum):
    """Common observation categories."""

    VITAL_SIGNS = "vital-signs"
    LABORATORY = "laboratory"
    IMAGING = "imaging"
    PROCEDURE = "procedure"
    SURVEY = "survey"
    EXAM = "exam"
    THERAPY = "therapy"
    ACTIVITY = "activity"


class DataAbsentReason(str, Enum):
    """Reasons why data might be absent."""

    UNKNOWN = "unknown"
    ASKED_UNKNOWN = "asked-unknown"
    TEMP_UNKNOWN = "temp-unknown"
    NOT_ASKED = "not-asked"
    ASKED_DECLINED = "asked-declined"
    MASKED = "masked"
    NOT_APPLICABLE = "not-applicable"
    UNSUPPORTED = "unsupported"
    AS_TEXT = "as-text"
    ERROR = "error"
    NOT_A_NUMBER = "not-a-number"
    NEGATIVE_INFINITY = "negative-infinity"
    POSITIVE_INFINITY = "positive-infinity"
    NOT_PERFORMED = "not-performed"
    NOT_PERMITTED = "not-permitted"


class Observation(BaseResource):
    """
    Represents a healthcare observation or measurement.

    This model includes comprehensive observation data with FHIR compliance,
    code validation, unit validation, and agent-centric features.

    LLM-Friendly Features:
    - Code field is optional with smart defaults
    - Simple string inputs are automatically converted to proper structures
    - Flexible validation that guides rather than blocks
    - Helper methods for common LLM use cases
    """

    resource_type: Literal["Observation"] = Field(
        default="Observation", description="Resource type identifier"
    )

    # Core observation fields
    status: ObservationStatus = Field(
        default=ObservationStatus.FINAL,
        description="Status of the observation (defaults to 'final')",
    )

    category: list[dict[str, Any]] = Field(
        default_factory=list, description="Classification of type of observation"
    )

    # LLM-FRIENDLY: Code is now optional with smart defaults
    code: dict[str, Any] | None = Field(
        default=None,
        description="Type of observation (LOINC, SNOMED CT, etc.) - Optional, will be auto-generated if not provided",
    )

    # LLM-FRIENDLY: Simple string alternative for code
    code_text: str | None = Field(
        default=None,
        description="Simple text description of what is being observed (e.g., 'blood pressure', 'temperature')",
    )

    subject: str = Field(description="Who/what the observation is about")

    encounter: str | None = Field(
        default=None,
        description="Healthcare encounter during which observation was made",
    )

    # Timing - LLM-FRIENDLY: More flexible
    effective_datetime: datetime | None = Field(
        default=None, description="Clinically relevant time/time-period for observation"
    )

    effective_period: dict[str, Any] | None = Field(
        default=None, description="Time period during which observation was made"
    )

    issued: datetime | None = Field(
        default=None, description="Date/time the observation was made available"
    )

    # Value and results - LLM-FRIENDLY: Simplified
    value_quantity: dict[str, Any] | None = Field(
        default=None, description="Actual result (Quantity)"
    )

    value_codeable_concept: dict[str, Any] | None = Field(
        default=None, description="Actual result (CodeableConcept)"
    )

    value_string: str | None = Field(default=None, description="Actual result (string)")

    value_boolean: bool | None = Field(
        default=None, description="Actual result (boolean)"
    )

    value_integer: int | None = Field(
        default=None, description="Actual result (integer)"
    )

    value_range: dict[str, Any] | None = Field(
        default=None, description="Actual result (Range)"
    )

    # LLM-FRIENDLY: Simple numeric value with unit
    value_numeric: float | None = Field(
        default=None,
        description="Simple numeric value (will be converted to value_quantity)",
    )

    unit_text: str | None = Field(
        default=None,
        description="Unit of measurement (e.g., 'mmHg', 'mg/dL', 'F') - pairs with value_numeric",
    )

    # LLM-FRIENDLY: Simple subject reference
    subject_reference: str | None = Field(
        default=None,
        description="Simple subject reference (e.g., 'Patient/123') - will be converted to subject",
    )

    # LLM-FRIENDLY: Normal range as text
    normal_range_text: str | None = Field(
        default=None,
        description="Normal range in human-readable format (e.g., '120-140 mmHg')",
    )

    data_absent_reason: DataAbsentReason | None = Field(
        default=None, description="Why the observation value is not present"
    )

    # Reference ranges
    reference_range: list[dict[str, Any]] = Field(
        default_factory=list, description="Provides guide for interpretation"
    )

    # Components for multi-component observations
    component: list[dict[str, Any]] = Field(
        default_factory=list, description="Component results"
    )

    # Additional HACS-specific fields for agents
    confidence: float | None = Field(
        default=None,
        description="Confidence level of the observation (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )

    source: str | None = Field(
        default=None, description="Source of the observation (device, manual, etc.)"
    )

    notes: str | None = Field(
        default=None, description="Additional notes about the observation"
    )

    def __init__(self, **data):
        # Auto-generate ID if not provided
        if "id" not in data:
            data["id"] = f"observation-{str(uuid.uuid4())[:8]}"

        super().__init__(**data)

    def model_post_init(self, __context) -> None:
        """Post-initialization processing for LLM-friendly auto-conversion."""
        super().model_post_init(__context)

        # Convert simple subject reference to complex structure
        if self.subject_reference and not hasattr(self, '_subject_converted'):
            if not isinstance(self.subject, str) or not self.subject.startswith(self.subject_reference):
                self.subject = self.subject_reference
                self._subject_converted = True

        # Auto-convert simple numeric value to value_quantity
        if self.value_numeric is not None and not self.value_quantity:
            self.value_quantity = {
                "value": self.value_numeric,
                "unit": self.unit_text or "",
                "system": "http://unitsofmeasure.org" if self.unit_text else ""
            }

        # Auto-generate code from code_text if needed
        if self.code_text and not self.code:
            self.code = {
                "text": self.code_text,
                "coding": [{
                    "display": self.code_text,
                    "code": self.code_text.lower().replace(" ", "-")
                }]
            }

        # Provide smart default for data_absent_reason if no value is provided
        if not any([
            self.value_quantity, self.value_codeable_concept, self.value_string,
            self.value_boolean, self.value_integer, self.value_range, self.data_absent_reason
        ]):
            self.data_absent_reason = DataAbsentReason.UNKNOWN

    @model_validator(mode="after")
    def validate_observation_requirements(self) -> "Observation":
        """Enhanced validation with helpful error messages."""

        # Check that either a value or data_absent_reason is provided
        has_value = any([
            self.value_quantity, self.value_codeable_concept, self.value_string,
            self.value_boolean, self.value_integer, self.value_range
        ])

        if not has_value and not self.data_absent_reason:
            raise ValueError(
                "Observation must have a value or reason for absence. You can provide:\n"
                "- value_numeric=123.4 with unit_text='mg/dL' for numeric values\n"
                "- value_string='Normal' for text values\n"
                "- value_boolean=True for yes/no values\n"
                "- data_absent_reason='unknown' if value is not available\n"
                "\nExample: Observation(subject_reference='Patient/123', code_text='Temperature', value_numeric=98.6, unit_text='F')"
            )

        return self

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, v: str) -> str:
        """Ensure subject is not empty."""
        if not v.strip():
            raise ValueError("Subject cannot be empty")
        return v.strip()

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        """Validate observation code structure - now optional and more flexible."""
        if v is None:
            return None

        if not isinstance(v, dict):
            raise ValueError("Code must be a dictionary")

        # More flexible validation - allow partial codes
        if "coding" in v:
            if not isinstance(v["coding"], list):
                raise ValueError("Code coding must be a list")
            # Allow empty coding list - will be populated later
            for coding in v["coding"]:
                if not isinstance(coding, dict):
                    raise ValueError("Each coding must be a dictionary")

        return v

    @model_validator(mode="after")
    def validate_and_normalize_values(self) -> "Observation":
        """LLM-FRIENDLY: Validate and normalize value fields with smart defaults."""
        # Convert simple numeric value to value_quantity
        if self.value_numeric is not None and self.value_quantity is None:
            self.value_quantity = {
                "value": self.value_numeric,
                "unit": self.unit_text or "",
                "system": "http://unitsofmeasure.org" if self.unit_text else "",
                "code": self.unit_text or "",
            }

        # Generate code from code_text if needed
        if self.code is None and self.code_text:
            self.code = self._generate_code_from_text(self.code_text)

        # Convert simple interpretation to structured format
        if self.interpretation_text and not self.interpretation:
            self.interpretation = [
                self._generate_interpretation_from_text(self.interpretation_text)
            ]

        # Convert simple note to structured format
        if self.note_text and not self.note:
            self.note = [{"text": self.note_text}]

        # Convert simple body site to structured format
        if self.body_site_text and self.body_site is None:
            self.body_site = {"text": self.body_site_text}

        # LLM-FRIENDLY: More flexible value validation
        value_fields = [
            self.value_quantity,
            self.value_codeable_concept,
            self.value_string,
            self.value_boolean,
            self.value_integer,
            self.value_range,
        ]

        non_none_values = [v for v in value_fields if v is not None]

        if len(non_none_values) > 1:
            raise ValueError("Only one value field can be set")

        # LLM-FRIENDLY: Allow observations without values if there's a reason
        if len(non_none_values) == 0 and self.data_absent_reason is None:
            # Don't require a value if this is just a text observation
            if not self.value_string and not self.note_text:
                raise ValueError(
                    "Either a value field or data_absent_reason must be provided"
                )

        return self

    def _generate_code_from_text(self, text: str) -> dict[str, Any]:
        """Generate a basic code structure from text description."""
        # Common mappings for LLM-friendly text to LOINC codes
        common_codes = {
            "blood pressure": {
                "system": "http://loinc.org",
                "code": "85354-9",
                "display": "Blood pressure panel",
            },
            "systolic blood pressure": {
                "system": "http://loinc.org",
                "code": "8480-6",
                "display": "Systolic blood pressure",
            },
            "diastolic blood pressure": {
                "system": "http://loinc.org",
                "code": "8462-4",
                "display": "Diastolic blood pressure",
            },
            "heart rate": {
                "system": "http://loinc.org",
                "code": "8867-4",
                "display": "Heart rate",
            },
            "temperature": {
                "system": "http://loinc.org",
                "code": "8310-5",
                "display": "Body temperature",
            },
            "weight": {
                "system": "http://loinc.org",
                "code": "29463-7",
                "display": "Body weight",
            },
            "height": {
                "system": "http://loinc.org",
                "code": "8302-2",
                "display": "Body height",
            },
            "oxygen saturation": {
                "system": "http://loinc.org",
                "code": "2708-6",
                "display": "Oxygen saturation",
            },
            "respiratory rate": {
                "system": "http://loinc.org",
                "code": "9279-1",
                "display": "Respiratory rate",
            },
            "pain score": {
                "system": "http://loinc.org",
                "code": "72133-2",
                "display": "Pain severity",
            },
        }

        text_lower = text.lower().strip()
        if text_lower in common_codes:
            coding = common_codes[text_lower]
        else:
            # Generic code for unknown observations
            coding = {
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "survey",
                "display": text,
            }

        return {"coding": [coding], "text": text}

    def _generate_interpretation_from_text(self, text: str) -> dict[str, Any]:
        """Generate interpretation structure from simple text."""
        # Common interpretation mappings
        interpretation_codes = {
            "high": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                "code": "H",
                "display": "High",
            },
            "low": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                "code": "L",
                "display": "Low",
            },
            "normal": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                "code": "N",
                "display": "Normal",
            },
            "abnormal": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                "code": "A",
                "display": "Abnormal",
            },
            "critical": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                "code": "HH",
                "display": "Critical high",
            },
            "very low": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                "code": "LL",
                "display": "Critical low",
            },
        }

        text_lower = text.lower().strip()
        if text_lower in interpretation_codes:
            coding = interpretation_codes[text_lower]
        else:
            # Generic interpretation
            coding = {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                "code": "N",
                "display": text,
            }

        return {"coding": [coding], "text": text}

    @model_validator(mode="after")
    def validate_effective_time(self) -> "Observation":
        """Ensure only one effective time field is set."""
        if self.effective_datetime is not None and self.effective_period is not None:
            raise ValueError(
                "Only one of effective_datetime or effective_period can be set"
            )
        return self

    @computed_field
    @property
    def has_value(self) -> bool:
        """Computed field indicating if observation has a value."""
        value_fields = [
            self.value_quantity,
            self.value_codeable_concept,
            self.value_string,
            self.value_boolean,
            self.value_integer,
            self.value_range,
        ]
        return any(v is not None for v in value_fields)

    @computed_field
    @property
    def primary_code(self) -> str | None:
        """Computed field for primary observation code."""
        if self.code and "coding" in self.code and len(self.code["coding"]) > 0:
            return self.code["coding"][0].get("code")
        return None

    @computed_field
    @property
    def primary_system(self) -> str | None:
        """Computed field for primary code system."""
        if self.code and "coding" in self.code and len(self.code["coding"]) > 0:
            return self.code["coding"][0].get("system")
        return None

    @computed_field
    @property
    def display_name(self) -> str:
        """LLM-FRIENDLY: Human-readable name for the observation."""
        if self.code_text:
            return self.code_text
        if self.code and "text" in self.code:
            return self.code["text"]
        if self.code and "coding" in self.code and len(self.code["coding"]) > 0:
            return self.code["coding"][0].get("display", "Unknown observation")
        return "Unknown observation"

    @computed_field
    @property
    def is_vital_sign(self) -> bool:
        """Computed field indicating if this is a vital sign."""
        for cat in self.category:
            if "coding" in cat:
                for coding in cat["coding"]:
                    if coding.get("code") == "vital-signs":
                        return True
        return False

    # LLM-FRIENDLY: Helper methods for common use cases
    def validate_code_system(self, system: str) -> bool:
        """
        Validate if the observation code belongs to a specific system.

        Args:
            system: Code system to validate against

        Returns:
            True if code belongs to the system
        """
        if not self.code or "coding" not in self.code:
            return False

        for coding in self.code["coding"]:
            if coding.get("system") == system:
                return True
        return False

    def is_loinc_code(self) -> bool:
        """Check if observation uses LOINC coding."""
        return self.validate_code_system("http://loinc.org")

    def is_snomed_code(self) -> bool:
        """Check if observation uses SNOMED CT coding."""
        return self.validate_code_system("http://snomed.info/sct")

    def add_component(
        self,
        code: dict[str, Any],
        value: dict[str, Any] | str | bool | int,
        data_absent_reason: str | None = None,
    ) -> None:
        """Add a component to this observation."""
        component: dict[str, Any] = {"code": code}

        if value is not None:
            if isinstance(value, dict):
                component["valueQuantity"] = value
            elif isinstance(value, str):
                component["valueString"] = value
            elif isinstance(value, bool):
                component["valueBoolean"] = value
            elif isinstance(value, int):
                component["valueInteger"] = value
        elif data_absent_reason:
            component["dataAbsentReason"] = {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/data-absent-reason",
                        "code": data_absent_reason,
                    }
                ]
            }

        self.component.append(component)
        self.update_timestamp()

    def set_reference_range(
        self,
        low: dict[str, Any] | None = None,
        high: dict[str, Any] | None = None,
        range_type: str = "normal",
        text: str | None = None,
    ) -> None:
        """Set reference range for the observation."""
        ref_range = {}

        if low is not None:
            ref_range["low"] = low
        if high is not None:
            ref_range["high"] = high
        if text:
            ref_range["text"] = text

        ref_range["type"] = {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/referencerange-meaning",
                    "code": range_type,
                    "display": range_type.title(),
                }
            ]
        }

        self.reference_range.append(ref_range)
        self.update_timestamp()

    def link_to_evidence(self, evidence_id: str) -> None:
        """Link this observation to evidence."""
        if evidence_id not in self.evidence_references:
            self.evidence_references.append(evidence_id)
            self.update_timestamp()

    def add_performer(self, performer_id: str) -> None:
        """Add a performer to this observation."""
        if performer_id not in self.performer:
            self.performer.append(performer_id)
            self.update_timestamp()

    def get_numeric_value(self) -> float | None:
        """Get numeric value from the observation."""
        if self.value_quantity and "value" in self.value_quantity:
            return float(self.value_quantity["value"])
        elif self.value_integer is not None:
            return float(self.value_integer)
        elif self.value_numeric is not None:
            return self.value_numeric
        return None

    def get_unit(self) -> str | None:
        """Get unit of measurement."""
        if self.value_quantity and "unit" in self.value_quantity:
            return self.value_quantity["unit"]
        elif self.unit_text:
            return self.unit_text
        return None

    def __repr__(self) -> str:
        """Enhanced representation including code and value."""
        code_str = self.display_name
        value_str = ""

        if self.value_quantity:
            val = self.value_quantity.get("value", "")
            unit = self.value_quantity.get("unit", "")
            value_str = f", value={val}{unit}"
        elif self.value_numeric is not None:
            unit = self.unit_text or ""
            value_str = f", value={self.value_numeric}{unit}"
        elif self.value_string:
            value_str = (
                f", value='{self.value_string[:20]}...'"
                if len(self.value_string) > 20
                else f", value='{self.value_string}'"
            )
        elif self.value_boolean is not None:
            value_str = f", value={self.value_boolean}"
        elif self.value_integer is not None:
            value_str = f", value={self.value_integer}"

        return f"Observation(id='{self.id}', code='{code_str}', status='{self.status}'{value_str})"
