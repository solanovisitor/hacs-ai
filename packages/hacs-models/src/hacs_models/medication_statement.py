"""
MedicationStatement model for HACS.

HACS-native minimal version inspired by FHIR R4 MedicationStatement, focused on
capturing medications reported as being taken (vs. prescribed).
"""

from typing import Literal

from pydantic import Field, field_validator

from .base_resource import DomainResource
from .observation import CodeableConcept
from .types import (
    MedicationStatementStatus,
    ResourceReference,
    TimestampStr,
)
from .medication_request import Dosage


class MedicationStatement(DomainResource):
    resource_type: Literal["MedicationStatement"] = Field(default="MedicationStatement")

    # Core
    status: MedicationStatementStatus = Field(
        default=MedicationStatementStatus.ACTIVE, description="MedicationStatement status"
    )

    # medication[x]
    medication_codeable_concept: CodeableConcept | None = Field(
        default=None, description="Medication as coded concept"
    )
    medication_reference: ResourceReference | None = Field(
        default=None, description="Reference to Medication resource"
    )

    # Subject
    subject_ref: ResourceReference | None = Field(
        default=None, description="Reference to Patient or Group"
    )

    # Category and context
    category: list[CodeableConcept] = Field(
        default_factory=list, description="Type of medication statement (category)"
    )
    encounter_ref: ResourceReference | None = Field(
        default=None, description="Encounter during which this statement was made"
    )

    # effective[x]
    effective_date_time: TimestampStr | None = Field(
        default=None, description="When the medication is/was taken (ISO 8601)"
    )
    effective_period_start: TimestampStr | None = Field(
        default=None, description="Start of period medication was taken"
    )
    effective_period_end: TimestampStr | None = Field(
        default=None, description="End of period medication was taken"
    )

    # Assertion & provenance
    date_asserted: TimestampStr | None = Field(
        default=None, description="Date when this statement was asserted"
    )
    information_source: ResourceReference | None = Field(
        default=None, description="Who provided the information"
    )
    derived_from: list[ResourceReference] = Field(
        default_factory=list, description="Other resources used to derive this statement"
    )

    # Reason
    reason_code: list[CodeableConcept] = Field(
        default_factory=list, description="Reason for taking the medication (coded)"
    )
    reason_reference: list[ResourceReference] = Field(
        default_factory=list, description="Reason for taking the medication (references)"
    )
    status_reason: list[CodeableConcept] = Field(
        default_factory=list, description="Reason for current status (e.g., non-adherence)"
    )

    # Dosage and narrative
    dosage: list[Dosage] = Field(default_factory=list, description="How medication is/was taken")
    note: list[str] = Field(default_factory=list, description="Additional notes")

    # Convenience narrative (HACS-only)
    medication_text: str | None = Field(
        default=None, description="Free text medication description (fallback)"
    )
    reason_text: str | None = Field(default=None, description="Reason (free text)")

    @field_validator("subject_ref")
    @classmethod
    def validate_subject_required(cls, v):
        # Enforce presence when constructing production-grade statements
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ValueError("subject_ref is required for MedicationStatement")
        return v

    # Helpers
    def add_dosage_instruction(
        self,
        text: str,
        dose_quantity: float | None = None,
        dose_unit: str | None = None,
        frequency: int | None = None,
        period: int = 1,
        period_unit: str = "d",
    ) -> Dosage:
        d = Dosage(text=text, sequence=len(self.dosage) + 1)
        if dose_quantity is not None and dose_unit:
            d.dose_and_rate = [
                {
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/dose-rate-type",
                                "code": "ordered",
                                "display": "Ordered",
                            }
                        ]
                    },
                    "doseQuantity": {
                        "value": dose_quantity,
                        "unit": dose_unit,
                        "system": "http://unitsofmeasure.org",
                    },
                }
            ]
        if frequency:
            d.timing = {"repeat": {"frequency": frequency, "period": period, "periodUnit": period_unit}}
        self.dosage.append(d)
        return d

    def add_status_reason(self, text: str, code: str | None = None, system: str | None = None) -> None:
        cc = CodeableConcept(text=text)
        if code and system:
            # Build a Coding instance via CodeableConcept schema typing
            coding_type = type(cc).model_fields["coding"].annotation.__args__[0]  # type: ignore[attr-defined]
            cc.coding = [coding_type(system=system, code=code, display=text)]  # type: ignore[assignment]
        self.status_reason.append(cc)
        self.update_timestamp()

    @property
    def is_non_adherent(self) -> bool:
        """Heuristic helper to flag likely non-adherence.

        True if status indicates interruption (stopped/on-hold) or
        any status_reason mentions non-adherence semantics.
        """
        if self.status in {MedicationStatementStatus.STOPPED, MedicationStatementStatus.ON_HOLD}:
            return True
        for cc in self.status_reason:
            if getattr(cc, "text", ""):
                t = cc.text.lower()
                if "non-adher" in t or "adherence" in t or "não ader" in t:
                    return True
        return False

    # --- LLM-friendly extractable facade overrides ---
    @classmethod
    def get_extractable_fields(cls) -> list[str]:  # type: ignore[override]
        """Return fields that should be extracted by LLMs (3-4 key fields only)."""
        return [
            "medication_codeable_concept",
            "dosage",
            "effective_date_time",
        ]

    @classmethod
    def llm_hints(cls) -> list[str]:  # type: ignore[override]
        """Return LLM-specific extraction hints for MedicationStatement."""
        return [
            "If a medication name is explicit, fill medication_codeable_concept.text and leave dosage.text=null when absent",
            "Use effective_date_time for when the medication was taken",
        ]
