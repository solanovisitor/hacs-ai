"""
Observation model for clinical measurements and findings.

This module provides FHIR-compliant Observation models for recording
clinical measurements, laboratory results, vital signs, and other
healthcare observations.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from .base_resource import DomainResource
from .types import ObservationStatus


class Coding(DomainResource):
    """A coded value from a terminology system."""

    resource_type: Literal["Coding"] = Field(default="Coding")

    system: str | None = Field(
        default=None,
        description="Identity of the terminology system",
        examples=["http://loinc.org", "http://snomed.info/sct"],
    )

    version: str | None = Field(default=None, description="Version of the system", max_length=50)

    code: str = Field(
        description="Symbol in syntax defined by the system",
        examples=["85354-9", "271649006"],
        max_length=100,
    )

    display: str | None = Field(
        default=None,
        description="Representation defined by the system",
        examples=["Blood pressure", "Systolic blood pressure", "Diastolic blood pressure", "Heart rate", "Respiratory rate", "Temperature", "Oxygen saturation", "Body weight", "Body height", "Body mass index"],
        max_length=255,
    )


class CodeableConcept(DomainResource):
    """A concept that may be defined by one or more codes."""

    resource_type: Literal["CodeableConcept"] = Field(default="CodeableConcept")

    coding: list[Coding] = Field(
        default_factory=list, description="Code defined by a terminology system"
    )

    text: str | None = Field(
        default=None, description="Plain text representation of the concept", max_length=500
    )


class Quantity(DomainResource):
    """A measured amount."""

    resource_type: Literal["Quantity"] = Field(default="Quantity")

    value: float | None = Field(
        default=None, description="Numerical value (with implicit precision)"
    )

    comparator: str | None = Field(
        default=None, description="< | <= | >= | > - how to understand the value", max_length=2
    )

    unit: str | None = Field(
        default=None,
        description="Unit representation",
        examples=["kg", "mmHg", "mg/dL"],
        max_length=50,
    )

    system: str | None = Field(
        default=None,
        description="System that defines coded unit form",
        examples=["http://unitsofmeasure.org"],
    )

    code: str | None = Field(default=None, description="Coded form of the unit", max_length=50)


class Range(DomainResource):
    """A range of values."""

    resource_type: Literal["Range"] = Field(default="Range")

    low: Quantity | None = Field(default=None, description="Low limit")

    high: Quantity | None = Field(default=None, description="High limit")


class Observation(DomainResource):
    """
    Measurements and simple assertions made about a patient.

    Observations are a central element in healthcare, used to support
    diagnosis, monitor progress, determine baselines and patterns, and
    capture demographic characteristics.
    """

    resource_type: Literal["Observation"] = Field(default="Observation")

    # Required fields
    status: ObservationStatus = Field(description="Status of the observation result")

    code: CodeableConcept = Field(description="Type of observation (code / type)")

    # FHIR R4 Enhanced Categorization
    category: list[CodeableConcept] = Field(
        default_factory=list,
        description="Classification of type of observation (e.g., vital-signs, laboratory, imaging, survey)",
        examples=[
            [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "vital-signs",
                            "display": "Vital Signs",
                        }
                    ],
                    "text": "Vital Signs",
                }
            ]
        ],
    )

    # Method used to perform the observation
    method: CodeableConcept | None = Field(
        default=None,
        description="Method used to perform the observation",
        examples=[
            {
                "text": "Automated blood pressure cuff",
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "261241001",
                        "display": "Arterial pressure monitoring",
                    }
                ],
            }
        ],
    )

    # Device used to perform the observation
    device: str | None = Field(
        default=None,
        description="Reference to device used to perform observation",
        examples=["Device/blood-pressure-monitor-123", "Device/thermometer-456"],
    )

    # Subject reference
    subject: str | None = Field(
        default=None,
        description="Who/what this observation is about",
        examples=["Patient/patient-123"],
    )

    # Context
    encounter: str | None = Field(
        default=None,
        description="Healthcare encounter during which this observation was made",
        examples=["Encounter/encounter-456"],
    )

    # Timing
    effective_date_time: datetime | None = Field(
        default=None, description="Clinically relevant time/time-period for observation"
    )

    issued: datetime | None = Field(
        default=None, description="Date/Time this version was made available"
    )

    # Performer
    performer: list[str] = Field(
        default_factory=list,
        description="Who is responsible for the observation",
        examples=[["Practitioner/dr-smith"]],
    )

    # Value - multiple types possible
    value_quantity: Quantity | None = Field(default=None, description="Actual result as a quantity")

    value_codeable_concept: CodeableConcept | None = Field(
        default=None, description="Actual result as a coded concept"
    )

    value_string: str | None = Field(default=None, description="Actual result as a string")

    value_boolean: bool | None = Field(default=None, description="Actual result as a boolean")

    value_integer: int | None = Field(default=None, description="Actual result as an integer")

    value_range: Range | None = Field(default=None, description="Actual result as a range")

    # Data quality
    data_absent_reason: CodeableConcept | None = Field(
        default=None, description="Why the observation value is missing"
    )

    interpretation: list[CodeableConcept] = Field(
        default_factory=list, description="High, low, normal, etc."
    )

    note: list[str] = Field(
        default_factory=list, description="Comments about the observation", max_length=10
    )

    # Enhanced Reference Ranges
    reference_range: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Reference ranges for interpretation of observation values",
        examples=[
            [
                {
                    "low": {"value": 120, "unit": "mmHg", "system": "http://unitsofmeasure.org"},
                    "high": {"value": 140, "unit": "mmHg", "system": "http://unitsofmeasure.org"},
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/referencerange-meaning",
                                "code": "normal",
                                "display": "Normal Range",
                            }
                        ],
                        "text": "Normal",
                    },
                    "applies_to": [
                        {
                            "coding": [
                                {
                                    "system": "http://snomed.info/sct",
                                    "code": "248153007",
                                    "display": "Male",
                                }
                            ],
                            "text": "Male",
                        }
                    ],
                    "age": {
                        "low": {"value": 18, "unit": "years"},
                        "high": {"value": 65, "unit": "years"},
                    },
                    "text": "Normal blood pressure range for adult males",
                }
            ]
        ],
    )

    # Enhanced Interpretation with detailed context
    interpretation_detail: dict[str, Any] | None = Field(
        default=None,
        description="Enhanced interpretation with clinical context and recommendations",
        examples=[
            {
                "overall_interpretation": "abnormal",
                "clinical_significance": "high",
                "trend_analysis": "increasing",
                "recommended_action": "follow-up required",
                "confidence_level": "high",
                "comparison_to_previous": "20% increase from last measurement",
                "clinical_context": "Patient on antihypertensive medication",
            }
        ],
    )

    # Related observations
    has_member: list[str] = Field(
        default_factory=list, description="Related resource that belongs to the Observation group"
    )

    derived_from: list[str] = Field(
        default_factory=list, description="Related measurements the observation is made from"
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
            value=value, unit=unit, system=system or "http://unitsofmeasure.org"
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

    def add_category(
        self,
        category_code: str,
        category_display: str,
        system: str = "http://terminology.hl7.org/CodeSystem/observation-category",
    ) -> None:
        """Add a category to the observation."""
        category = CodeableConcept(
            coding=[Coding(system=system, code=category_code, display=category_display)],
            text=category_display,
        )
        self.category.append(category)
        self.update_timestamp()

    def add_reference_range(
        self,
        low_value: float | None = None,
        high_value: float | None = None,
        unit: str | None = None,
        range_type: str = "normal",
        applies_to: str | None = None,
        text: str | None = None,
    ) -> None:
        """Add a reference range to the observation."""
        range_dict = {}

        if low_value is not None and unit:
            range_dict["low"] = {
                "value": low_value,
                "unit": unit,
                "system": "http://unitsofmeasure.org",
            }

        if high_value is not None and unit:
            range_dict["high"] = {
                "value": high_value,
                "unit": unit,
                "system": "http://unitsofmeasure.org",
            }

        range_dict["type"] = {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/referencerange-meaning",
                    "code": range_type,
                    "display": range_type.title(),
                }
            ],
            "text": range_type.title(),
        }

        if applies_to:
            range_dict["applies_to"] = [{"text": applies_to}]

        if text:
            range_dict["text"] = text

        self.reference_range.append(range_dict)
        self.update_timestamp()

    # ---------------------------------------------------------------------
    # Compatibility: allow simple strings for code and category for tests
    # ---------------------------------------------------------------------
    @model_validator(mode="before")
    @classmethod
    def _coerce_simple_fields(cls, values):  # type: ignore[override]
        if isinstance(values, dict):
            # code as string -> CodeableConcept{text=string}
            if isinstance(values.get("code"), str):
                values["code"] = CodeableConcept(text=values["code"])
            # category as string -> [CodeableConcept{text=string}]
            if isinstance(values.get("category"), str):
                values["category"] = [CodeableConcept(text=values["category"])]
        return values

    def is_within_normal_range(self) -> bool | None:
        """Check if the observation value is within normal reference ranges."""
        if not self.value_quantity or not self.reference_range:
            return None

        value = self.value_quantity.value

        for range_item in self.reference_range:
            # Check if this is a normal range
            range_type = range_item.get("type", {})
            if isinstance(range_type, dict):
                coding = range_type.get("coding", [])
                if any(c.get("code") == "normal" for c in coding if isinstance(c, dict)):
                    low = range_item.get("low", {})
                    high = range_item.get("high", {})

                    low_val = low.get("value") if isinstance(low, dict) else None
                    high_val = high.get("value") if isinstance(high, dict) else None

                    if low_val is not None and value < low_val:
                        return False
                    if high_val is not None and value > high_val:
                        return False

                    # If we have at least one bound and value is within it
                    if low_val is not None or high_val is not None:
                        return True

        return None  # Cannot determine

    def get_interpretation_summary(self) -> str:
        """Get a summary of the observation interpretation."""
        interpretations = []

        # Standard interpretation codes
        for interp in self.interpretation:
            if hasattr(interp, "text") and interp.text:
                interpretations.append(interp.text)
            elif hasattr(interp, "coding") and interp.coding:
                for coding in interp.coding:
                    if hasattr(coding, "display") and coding.display:
                        interpretations.append(coding.display)
                        break

        # Enhanced interpretation
        if self.interpretation_detail:
            overall = self.interpretation_detail.get("overall_interpretation")
            significance = self.interpretation_detail.get("clinical_significance")
            if overall:
                interpretations.append(overall)
            if significance and significance != "normal":
                interpretations.append(f"{significance} significance")

        # Reference range check
        within_normal = self.is_within_normal_range()
        if within_normal is not None:
            interpretations.append(
                "within normal range" if within_normal else "outside normal range"
            )

        return ", ".join(interpretations) if interpretations else "No interpretation available"

    def __str__(self) -> str:
        """Human-readable string representation."""
        code_display = self.code.text if self.code.text else "Observation"
        value_summary = self.get_value_summary()
        interpretation = self.get_interpretation_summary()

        result = f"{code_display}: {value_summary}"
        if interpretation and interpretation != "No interpretation available":
            result += f" ({interpretation})"

        return result

    # --- LLM-friendly extractable facade overrides ---
    @classmethod
    def get_extractable_fields(cls) -> list[str]:  # type: ignore[override]
        # Balanced set of clinically relevant extractable fields
        return [
            "status",
            "code",
            "value_quantity", 
            "value_string",
            "effective_date_time",
            "interpretation",
        ]

    @classmethod
    def get_required_extractables(cls) -> list[str]:
        """Fields that must be provided for valid extraction."""
        return ["code"]

    @classmethod
    def get_canonical_defaults(cls) -> dict[str, Any]:
        """Default values for system/required fields during extraction."""
        return {
            "status": "final",
            "subject": "Patient/UNKNOWN",
            "code": {"text": ""},  # Will be filled by LLM
        }

    @classmethod
    def coerce_extractable(cls, payload: dict[str, Any], relax: bool = True) -> dict[str, Any]:
        """Coerce extractable payload to proper types with relaxed validation."""
        coerced = payload.copy()
        
        # Coerce code to CodeableConcept if it's a string
        if "code" in coerced and isinstance(coerced["code"], str):
            coerced["code"] = {"text": coerced["code"]}
        
        # Ensure code has text field
        if "code" in coerced and isinstance(coerced["code"], dict) and "text" not in coerced["code"]:
            coerced["code"]["text"] = ""
            
        # Coerce value_quantity to proper structure
        if "value_quantity" in coerced and isinstance(coerced["value_quantity"], (int, float)):
            coerced["value_quantity"] = {"value": coerced["value_quantity"]}
            
        # Coerce interpretation to list of CodeableConcepts
        if "interpretation" in coerced and isinstance(coerced["interpretation"], str):
            coerced["interpretation"] = [{"text": coerced["interpretation"]}]
        elif "interpretation" in coerced and isinstance(coerced["interpretation"], dict):
            coerced["interpretation"] = [coerced["interpretation"]]
            
        return coerced

    @classmethod
    def llm_hints(cls) -> list[str]:  # type: ignore[override]
        return [
            "- Return ONE item per distinct measure (Weight, Height, Head circumference, Apgar, Gestational age, BP/TA, HR, RR, Temp, SpO2, BMI)",
            "- Prefer value_quantity for numeric values; use value_string for composites (e.g., '90/60')",
            "- If unit is not explicit, use unit=null; do not invent",
        ]
