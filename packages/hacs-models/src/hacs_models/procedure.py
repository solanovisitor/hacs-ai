"""
Procedure model for HACS.

This module provides a comprehensive, FHIR-compliant Procedure resource model
for recording healthcare procedures, surgeries, and interventions performed on patients.

FHIR R4 Specification:
https://hl7.org/fhir/R4/procedure.html
"""

from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator

from .base_resource import DomainResource
from .observation import CodeableConcept
from .types import (
    ProcedureStatus,
    ResourceReference,
    TimestampStr,
)


class ProcedurePerformer(DomainResource):
    """
    Performer of the procedure.

    Limited to "real" people rather than equipment, though may include assistants
    and other people involved in the procedure.
    """

    resource_type: Literal["ProcedurePerformer"] = Field(default="ProcedurePerformer")

    # Type of performance
    function: CodeableConcept | None = Field(
        default=None,
        description="Type of performance (surgeon, anesthesiologist, assistant, etc.)",
        examples=[
            {
                "coding": [
                    {"system": "http://snomed.info/sct", "code": "304292004", "display": "Surgeon"}
                ],
                "text": "Primary Surgeon",
            }
        ],
    )

    # The reference to the practitioner
    actor: ResourceReference = Field(description="The reference to the practitioner")

    # Organization the practitioner acted on behalf of
    on_behalf_of: ResourceReference | None = Field(
        default=None, description="Organization the practitioner acted on behalf of"
    )


class ProcedureFocalDevice(DomainResource):
    """
    Manipulated, implanted, or removed device.

    A device that is implanted, removed or otherwise manipulated (calibration,
    battery replacement, fitting a prosthesis, attaching a wound-vac, etc.)
    as a focal portion of the Procedure.
    """

    resource_type: Literal["ProcedureFocalDevice"] = Field(default="ProcedureFocalDevice")

    # Kind of change to device
    action: CodeableConcept | None = Field(
        default=None,
        description="Kind of change to device",
        examples=[
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "129334004",
                        "display": "Implantation",
                    }
                ],
                "text": "Implanted",
            }
        ],
    )

    # Device that was changed
    manipulated: ResourceReference = Field(description="Device that was changed")


class Procedure(DomainResource):
    """
    Procedure resource for healthcare procedures and interventions.

    An action that is or was performed on or for a patient. This can be a
    physical intervention like an operation, or less invasive like long term
    services, counseling, or hypnotherapy.

    This resource is used to record procedures performed on patients, including
    surgical procedures, therapeutic procedures, diagnostic procedures, and
    administrative procedures.
    """

    resource_type: Literal["Procedure"] = Field(default="Procedure")

    # Business identifiers
    identifier: list[str] = Field(
        default_factory=list,
        description="External identifiers for this procedure",
        examples=[["urn:oid:1.2.3.4.5.6.7.8.9|12345", "procedure-123456"]],
    )

    # Status of the procedure - REQUIRED
    status: ProcedureStatus = Field(
        description="Status of the procedure (preparation, in-progress, completed, etc.)"
    )

    # Reason for current status
    status_reason: CodeableConcept | None = Field(
        default=None, description="Reason for current status"
    )

    # Classification of procedure
    category: CodeableConcept | None = Field(
        default=None,
        description="Classification of procedure",
        examples=[
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "387713003",
                        "display": "Surgical procedure",
                    }
                ],
                "text": "Surgical procedure",
            }
        ],
    )

    # Identification of procedure - REQUIRED
    code: CodeableConcept = Field(description="Identification of the procedure")

    # Who the procedure was performed on - REQUIRED
    subject: ResourceReference = Field(description="Who the procedure was performed on")

    # Encounter created as part of
    encounter: ResourceReference | None = Field(
        default=None, description="Encounter created as part of"
    )

    # When the procedure was performed
    performed_date_time: TimestampStr | None = Field(
        default=None, description="When the procedure was performed"
    )

    # When the procedure was performed (period)
    performed_period_start: TimestampStr | None = Field(
        default=None, description="Start of when the procedure was performed"
    )

    performed_period_end: TimestampStr | None = Field(
        default=None, description="End of when the procedure was performed"
    )

    # The people who performed the procedure
    performer: list[ProcedurePerformer] = Field(
        default_factory=list, description="The people who performed the procedure"
    )

    # Where the procedure happened
    location: ResourceReference | None = Field(
        default=None, description="Where the procedure happened"
    )

    # Coded reason procedure performed
    reason_code: list[CodeableConcept] = Field(
        default_factory=list, description="Coded reason procedure performed"
    )

    # The justification that the procedure was performed
    reason_reference: list[ResourceReference] = Field(
        default_factory=list, description="The justification that the procedure was performed"
    )

    # Target body sites
    body_site: list[CodeableConcept] = Field(default_factory=list, description="Target body sites")

    # The result of procedure
    outcome: CodeableConcept | None = Field(default=None, description="The result of procedure")

    # Any report resulting from the procedure
    report: list[ResourceReference] = Field(
        default_factory=list, description="Any report resulting from the procedure"
    )

    # Complication following the procedure
    complication: list[CodeableConcept] = Field(
        default_factory=list, description="Complication following the procedure"
    )

    # A condition that is a result of the procedure
    complication_detail: list[ResourceReference] = Field(
        default_factory=list, description="A condition that is a result of the procedure"
    )

    # Instructions for follow up
    follow_up: list[CodeableConcept] = Field(
        default_factory=list, description="Instructions for follow up"
    )

    # Additional information about the procedure
    note: list[str] = Field(
        default_factory=list,
        description="Additional information about the procedure",
        max_length=10,
    )

    # Manipulated, implanted, or removed device
    focal_device: list[ProcedureFocalDevice] = Field(
        default_factory=list, description="Manipulated, implanted, or removed device"
    )

    # Items used during procedure
    used_reference: list[ResourceReference] = Field(
        default_factory=list, description="Items used during procedure"
    )

    # Coded items used during procedure
    used_code: list[CodeableConcept] = Field(
        default_factory=list, description="Coded items used during procedure"
    )

    # Duration of the procedure
    duration_minutes: int | None = Field(
        default=None,
        description="Duration of the procedure in minutes",
        examples=[30, 120, 240],
        ge=0,
    )

    @field_validator("status")
    @classmethod
    def validate_status_required(cls, v):
        """Ensure status is provided."""
        if not v:
            raise ValueError("Status is required for Procedure")
        return v

    @field_validator("code")
    @classmethod
    def validate_code_required(cls, v):
        """Ensure code is provided."""
        if not v:
            raise ValueError("Code is required for Procedure")
        return v

    @field_validator("subject")
    @classmethod
    def validate_subject_required(cls, v):
        """Ensure subject is provided."""
        if not v:
            raise ValueError("Subject is required for Procedure")
        return v

    @property
    def is_completed(self) -> bool:
        """Check if procedure is completed."""
        return self.status == ProcedureStatus.COMPLETED

    @property
    def is_in_progress(self) -> bool:
        """Check if procedure is in progress."""
        return self.status == ProcedureStatus.IN_PROGRESS

    @property
    def has_complications(self) -> bool:
        """Check if procedure had complications."""
        return bool(self.complication or self.complication_detail)

    def get_display_name(self) -> str:
        """Get a human-readable display name for the procedure."""
        if self.code:
            if hasattr(self.code, "text") and self.code.text:
                return self.code.text
            elif hasattr(self.code, "coding") and self.code.coding:
                first_coding = self.code.coding[0]
                if hasattr(first_coding, "display") and first_coding.display:
                    return first_coding.display
        return f"Procedure {self.id or 'Unknown'}"

    def add_performer(
        self,
        practitioner_ref: ResourceReference,
        function_text: str | None = None,
        function_code: str | None = None,
        organization_ref: ResourceReference | None = None,
    ) -> ProcedurePerformer:
        """Add a performer to the procedure."""
        performer = ProcedurePerformer(actor=practitioner_ref, on_behalf_of=organization_ref)

        if function_text or function_code:
            performer.function = CodeableConcept(text=function_text)
            if function_code:
                performer.function.coding = [
                    {
                        "system": "http://snomed.info/sct",
                        "code": function_code,
                        "display": function_text or function_code,
                    }
                ]

        self.performer.append(performer)
        return performer

    def add_body_site(
        self, site_text: str, site_code: str | None = None, system: str = "http://snomed.info/sct"
    ) -> CodeableConcept:
        """Add a body site to the procedure."""
        body_site = CodeableConcept(text=site_text)

        if site_code:
            body_site.coding = [{"system": system, "code": site_code, "display": site_text}]

        self.body_site.append(body_site)
        return body_site

    def add_complication(
        self, complication_text: str, complication_code: str | None = None
    ) -> CodeableConcept:
        """Add a complication to the procedure."""
        complication = CodeableConcept(text=complication_text)

        if complication_code:
            complication.coding = [
                {
                    "system": "http://snomed.info/sct",
                    "code": complication_code,
                    "display": complication_text,
                }
            ]

        self.complication.append(complication)
        return complication


# Convenience functions for common procedure types


def create_surgical_procedure(
    procedure_name: str,
    patient_ref: ResourceReference,
    surgeon_ref: ResourceReference | None = None,
    performed_date: str | None = None,
    **kwargs,
) -> Procedure:
    """Create a surgical procedure."""
    procedure = Procedure(
        status=ProcedureStatus.COMPLETED,
        code=CodeableConcept(text=procedure_name),
        subject=patient_ref,
        category=CodeableConcept(
            text="Surgical procedure",
            coding=[
                {
                    "system": "http://snomed.info/sct",
                    "code": "387713003",
                    "display": "Surgical procedure",
                }
            ],
        ),
        performed_date_time=performed_date or datetime.now().isoformat(),
        **kwargs,
    )

    if surgeon_ref:
        procedure.add_performer(surgeon_ref, "Primary Surgeon", "304292004")

    return procedure


def create_diagnostic_procedure(
    procedure_name: str, patient_ref: ResourceReference, performed_date: str | None = None, **kwargs
) -> Procedure:
    """Create a diagnostic procedure."""
    procedure = Procedure(
        status=ProcedureStatus.COMPLETED,
        code=CodeableConcept(text=procedure_name),
        subject=patient_ref,
        category=CodeableConcept(
            text="Diagnostic procedure",
            coding=[
                {
                    "system": "http://snomed.info/sct",
                    "code": "103693007",
                    "display": "Diagnostic procedure",
                }
            ],
        ),
        performed_date_time=performed_date or datetime.now().isoformat(),
        **kwargs,
    )

    return procedure
