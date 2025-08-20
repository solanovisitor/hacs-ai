"""
DiagnosticReport model for HACS.

This module provides a FHIR R4-compliant DiagnosticReport resource model,
which is critical for clinical decision-making and reporting.

FHIR R4 Specification:
https://hl7.org/fhir/R4/diagnosticreport.html
"""

from typing import Literal

from pydantic import Field, field_validator

from .base_resource import DomainResource
from .observation import CodeableConcept
from .types import (
    DiagnosticReportStatus,
    ResourceReference,
    TimestampStr,
)


class DiagnosticReportMedia(DomainResource):
    """
    Diagnostic report media component.

    A list of key images associated with this report.
    """

    resource_type: Literal["DiagnosticReportMedia"] = Field(
        default="DiagnosticReportMedia", description="Resource type identifier"
    )

    # Comment about the image
    comment: str | None = Field(None, description="Comment about the image (e.g. explanation)")

    # Reference to the image source
    link: ResourceReference = Field(description="Reference to the image source")


class DiagnosticReport(DomainResource):
    """
    DiagnosticReport resource for clinical decisions.

    The findings and interpretation of diagnostic tests performed on patients,
    groups of patients, devices, and locations, and/or specimens derived from these.
    """

    resource_type: Literal["DiagnosticReport"] = Field(
        default="DiagnosticReport", description="Resource type identifier"
    )

    # Business identifiers
    identifier: list[str] = Field(
        default_factory=list, description="Business identifier for report"
    )

    # Based on reference
    based_on: list[ResourceReference] = Field(
        default_factory=list, description="What was requested"
    )

    # Status of the diagnostic report
    status: DiagnosticReportStatus = Field(description="Status of the diagnostic report")

    # Service category
    category: list[CodeableConcept] = Field(default_factory=list, description="Service category")

    # Name/Code for this diagnostic report
    code: CodeableConcept = Field(description="Name/Code for this diagnostic report")

    # The subject of the report
    subject: ResourceReference | None = Field(
        None, description="The subject of the report - usually, but not always, the patient"
    )

    # Health care event when test ordered
    encounter: ResourceReference | None = Field(
        None, description="Health care event when test ordered"
    )

    # Clinically relevant time/time-period for report
    effective_datetime: TimestampStr | None = Field(
        None, description="Clinically relevant time/time-period for report"
    )

    # Clinically relevant time period for report
    effective_period: str | None = Field(
        None, description="Clinically relevant time period for report"
    )

    # DateTime this version was made
    issued: TimestampStr | None = Field(None, description="DateTime this version was made")

    # Responsible Diagnostic Service
    performer: list[ResourceReference] = Field(
        default_factory=list, description="Responsible Diagnostic Service"
    )

    # Primary result interpreter
    results_interpreter: list[ResourceReference] = Field(
        default_factory=list, description="Primary result interpreter"
    )

    # Specimens this report is based on
    specimen: list[ResourceReference] = Field(
        default_factory=list, description="Specimens this report is based on"
    )

    # Observations included in this report
    result: list[ResourceReference] = Field(
        default_factory=list, description="Observations included in this report"
    )

    # Reference to full details of imaging associated with the diagnostic report
    imaging_study: list[ResourceReference] = Field(
        default_factory=list,
        description="Reference to full details of imaging associated with the diagnostic report",
    )

    # Key images associated with this report
    media: list[DiagnosticReportMedia] = Field(
        default_factory=list, description="Key images associated with this report"
    )

    # Clinical conclusion (impression) summary
    conclusion: str | None = Field(None, description="Clinical conclusion (impression) summary")

    # Codes for the clinical conclusion
    conclusion_code: list[CodeableConcept] = Field(
        default_factory=list, description="Codes for the clinical conclusion"
    )

    # Entire report as issued
    presented_form: list[str] = Field(default_factory=list, description="Entire report as issued")

    @field_validator("status")
    @classmethod
    def validate_status_required(cls, v):
        """Ensure status is provided."""
        if not v:
            raise ValueError("Status is required for DiagnosticReport")
        return v

    @field_validator("code")
    @classmethod
    def validate_code_required(cls, v):
        """Ensure code is provided."""
        if not v:
            raise ValueError("Code is required for DiagnosticReport")
        return v

    @property
    def is_final(self) -> bool:
        """Check if diagnostic report is final."""
        return self.status == DiagnosticReportStatus.FINAL

    @property
    def is_preliminary(self) -> bool:
        """Check if diagnostic report is preliminary."""
        return self.status == DiagnosticReportStatus.PRELIMINARY

    @property
    def is_cancelled(self) -> bool:
        """Check if diagnostic report is cancelled."""
        return self.status == DiagnosticReportStatus.CANCELLED

    @property
    def has_conclusion(self) -> bool:
        """Check if diagnostic report has a conclusion."""
        return bool(self.conclusion and self.conclusion.strip())

    @property
    def has_results(self) -> bool:
        """Check if diagnostic report has observation results."""
        return bool(self.result)

    def get_display_name(self) -> str:
        """Get a human-readable display name for the diagnostic report."""
        if self.code and hasattr(self.code, "text") and self.code.text:
            return self.code.text
        elif self.code and hasattr(self.code, "coding") and self.code.coding:
            # Try to get display from first coding
            first_coding = self.code.coding[0] if self.code.coding else None
            if first_coding and hasattr(first_coding, "display"):
                return first_coding.display
        return f"Diagnostic Report {self.id or 'Unknown'}"

    def add_result(self, observation_ref: ResourceReference) -> None:
        """Add an observation result to this diagnostic report."""
        if observation_ref and observation_ref not in self.result:
            self.result.append(observation_ref)

    def add_conclusion_code(self, code: CodeableConcept) -> None:
        """Add a conclusion code to this diagnostic report."""
        if code and code not in self.conclusion_code:
            self.conclusion_code.append(code)

    def add_media(
        self, media_ref: ResourceReference, comment: str | None = None
    ) -> DiagnosticReportMedia:
        """Add media to this diagnostic report."""
        media = DiagnosticReportMedia(link=media_ref, comment=comment)
        self.media.append(media)
        return media


# Convenience functions for common diagnostic report types


def create_lab_report(
    code: CodeableConcept,
    status: DiagnosticReportStatus = DiagnosticReportStatus.FINAL,
    subject_ref: ResourceReference | None = None,
    **kwargs,
) -> DiagnosticReport:
    """Create a laboratory diagnostic report."""
    return DiagnosticReport(
        status=status,
        code=code,
        subject=subject_ref,
        category=[CodeableConcept(text="Laboratory")],
        **kwargs,
    )


def create_imaging_report(
    code: CodeableConcept,
    status: DiagnosticReportStatus = DiagnosticReportStatus.FINAL,
    subject_ref: ResourceReference | None = None,
    **kwargs,
) -> DiagnosticReport:
    """Create an imaging diagnostic report."""
    return DiagnosticReport(
        status=status,
        code=code,
        subject=subject_ref,
        category=[CodeableConcept(text="Radiology")],
        **kwargs,
    )


def create_pathology_report(
    code: CodeableConcept,
    status: DiagnosticReportStatus = DiagnosticReportStatus.FINAL,
    subject_ref: ResourceReference | None = None,
    **kwargs,
) -> DiagnosticReport:
    """Create a pathology diagnostic report."""
    return DiagnosticReport(
        status=status,
        code=code,
        subject=subject_ref,
        category=[CodeableConcept(text="Pathology")],
        **kwargs,
    )


def create_microbiology_report(
    code: CodeableConcept,
    status: DiagnosticReportStatus = DiagnosticReportStatus.FINAL,
    subject_ref: ResourceReference | None = None,
    **kwargs,
) -> DiagnosticReport:
    """Create a microbiology diagnostic report."""
    return DiagnosticReport(
        status=status,
        code=code,
        subject=subject_ref,
        category=[CodeableConcept(text="Microbiology")],
        **kwargs,
    )
