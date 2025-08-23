"""
Practitioner model for HACS.

This module provides a FHIR R4-compliant Practitioner resource model,
which is essential for healthcare provider representation and care team management.

FHIR R4 Specification:
https://hl7.org/fhir/R4/practitioner.html
"""

from datetime import date
from typing import Literal

from pydantic import Field, field_validator

from .base_resource import DomainResource
from .observation import CodeableConcept
from .patient import Address, ContactPoint, HumanName, Identifier
from .types import (
    Gender,
    ResourceReference,
    TimestampStr,
)


class PractitionerQualification(DomainResource):
    """
    Practitioner qualification details.

    Qualifications, certifications, accreditations, licenses, training, etc.
    pertaining to the provision of care.
    """

    resource_type: Literal["PractitionerQualification"] = Field(
        default="PractitionerQualification", description="Resource type identifier"
    )

    # Business identifiers for the qualification
    identifier: list[Identifier] = Field(
        default_factory=list, description="External identifier for the qualification"
    )

    # Coded representation of the qualification
    code: CodeableConcept = Field(description="Coded representation of the qualification")

    # Period during which the qualification is valid
    period_start: TimestampStr | None = Field(
        None, description="Period start when the qualification is/was valid"
    )

    period_end: TimestampStr | None = Field(
        None, description="Period end when the qualification is/was valid"
    )

    # Organization that regulates and issues the qualification
    issuer: ResourceReference | None = Field(
        None, description="Organization that regulates and issues the qualification"
    )


class Practitioner(DomainResource):
    """
    Practitioner resource for healthcare provider representation.

    A person who is directly or indirectly involved in the provisioning of healthcare.
    This includes physicians, nurses, therapists, administrators, and other healthcare workers.
    """

    resource_type: Literal["Practitioner"] = Field(
        default="Practitioner", description="Resource type identifier"
    )

    # Business identifiers for the practitioner
    identifier: list[Identifier] = Field(
        default_factory=list, description="External identifiers for this practitioner"
    )

    # Whether this practitioner's record is in active use
    active: bool | None = Field(
        None, description="Whether this practitioner's record is in active use"
    )

    # Practitioner name(s)
    name: list[HumanName] = Field(
        default_factory=list, description="The name(s) associated with the practitioner"
    )

    # Contact details for the practitioner
    telecom: list[ContactPoint] = Field(
        default_factory=list, description="Contact details that are available outside of a role"
    )

    # Address(es) of the practitioner
    address: list[Address] = Field(
        default_factory=list,
        description="Address(es) of the practitioner that are not role specific",
    )

    # Administrative gender
    gender: Gender | None = Field(
        None, description="Administrative Gender - male | female | other | unknown"
    )

    # Date of birth
    birth_date: date | None = Field(None, description="The date of birth for the practitioner")

    # Image of the practitioner
    photo: list[str] = Field(
        default_factory=list, description="Image of the practitioner (base64 encoded or URL)"
    )

    # Qualifications, certifications, accreditations, licenses, training
    qualification: list[PractitionerQualification] = Field(
        default_factory=list,
        description="Certification, licenses, or training pertaining to the provision of care",
    )

    # Communication languages
    communication: list[CodeableConcept] = Field(
        default_factory=list,
        description="A language the practitioner can use in patient communication",
    )

    @field_validator("active")
    @classmethod
    def validate_active_status(cls, v):
        """Validate active status is reasonable."""
        # Active can be None, True, or False - all are valid
        return v

    @property
    def is_active(self) -> bool:
        """Check if practitioner is active (defaults to True if not specified)."""
        return self.active if self.active is not None else True

    @property
    def primary_name(self) -> HumanName | None:
        """Get the primary name for this practitioner."""
        if not self.name:
            return None

        # Look for official name first
        for name in self.name:
            if hasattr(name, "use") and name.use == "official":
                return name

        # Fall back to usual name
        for name in self.name:
            if hasattr(name, "use") and name.use == "usual":
                return name

        # Return first name if no specific use
        return self.name[0] if self.name else None

    @property
    def display_name(self) -> str:
        """Get a display name for the practitioner."""
        primary = self.primary_name
        if primary and hasattr(primary, "text") and primary.text:
            return primary.text

        if primary:
            # Build name from parts
            parts = []
            if hasattr(primary, "prefix") and primary.prefix:
                parts.extend(primary.prefix)
            if hasattr(primary, "given") and primary.given:
                parts.extend(primary.given)
            if hasattr(primary, "family") and primary.family:
                parts.append(primary.family)
            if hasattr(primary, "suffix") and primary.suffix:
                parts.extend(primary.suffix)

            if parts:
                return " ".join(parts)

        return f"Practitioner {self.id or 'Unknown'}"

    @property
    def primary_contact(self) -> ContactPoint | None:
        """Get the primary contact point for this practitioner."""
        if not self.telecom:
            return None

        # Look for work phone first
        for contact in self.telecom:
            if (
                hasattr(contact, "system")
                and contact.system == "phone"
                and hasattr(contact, "use")
                and contact.use == "work"
            ):
                return contact

        # Look for any work contact
        for contact in self.telecom:
            if hasattr(contact, "use") and contact.use == "work":
                return contact

        # Return first contact
        return self.telecom[0] if self.telecom else None

    @property
    def has_qualifications(self) -> bool:
        """Check if practitioner has any qualifications."""
        return bool(self.qualification)

    @property
    def specialty_codes(self) -> list[CodeableConcept]:
        """Get specialty codes from qualifications."""
        specialties = []
        for qual in self.qualification:
            if qual.code and hasattr(qual.code, "coding"):
                # Check if this is a specialty qualification
                if qual.code.coding:
                    for coding in qual.code.coding:
                        if hasattr(coding, "system") and "specialty" in str(coding.system).lower():
                            specialties.append(qual.code)
                            break
        return specialties

    def add_name(
        self,
        family: str | None = None,
        given: list[str] | None = None,
        use: str = "usual",
        **kwargs,
    ) -> HumanName:
        """Add a name to this practitioner."""
        name = HumanName(family=family, given=given or [], use=use, **kwargs)
        self.name.append(name)
        return name

    def add_contact(self, system: str, value: str, use: str = "work", **kwargs) -> ContactPoint:
        """Add a contact point to this practitioner."""
        contact = ContactPoint(system=system, value=value, use=use, **kwargs)
        self.telecom.append(contact)
        return contact

    def add_qualification(
        self,
        code: CodeableConcept,
        issuer: ResourceReference | None = None,
        period_start: TimestampStr | None = None,
        period_end: TimestampStr | None = None,
    ) -> PractitionerQualification:
        """Add a qualification to this practitioner."""
        qualification = PractitionerQualification(
            code=code, issuer=issuer, period_start=period_start, period_end=period_end
        )
        self.qualification.append(qualification)
        return qualification

    def get_qualifications_by_type(
        self, qualification_type: str
    ) -> list[PractitionerQualification]:
        """Get qualifications by type (e.g., 'license', 'certification', 'degree')."""
        matching = []
        for qual in self.qualification:
            if qual.code and hasattr(qual.code, "text"):
                if qualification_type.lower() in qual.code.text.lower():
                    matching.append(qual)
            elif qual.code and hasattr(qual.code, "coding"):
                for coding in qual.code.coding:
                    if (
                        hasattr(coding, "display")
                        and qualification_type.lower() in coding.display.lower()
                    ):
                        matching.append(qual)
                        break
        return matching

    @classmethod
    def get_extractable_fields(cls) -> list[str]:
        """Return fields that should be extracted by LLMs (3-4 key fields only)."""
        return ["name"]

    @classmethod
    def llm_hints(cls) -> list[str]:
        """Return LLM-specific extraction hints for Practitioner."""
        return [
            "Fill name with the explicit name text (e.g., 'doutora Ivi')",
            "Extract only when a healthcare provider is explicitly mentioned",
        ]


# Convenience functions for common practitioner types


def create_physician(
    family_name: str,
    given_names: list[str],
    specialty: str | None = None,
    license_number: str | None = None,
    **kwargs,
) -> Practitioner:
    """Create a physician practitioner."""
    practitioner = Practitioner(active=True, **kwargs)

    # Add name
    practitioner.add_name(family=family_name, given=given_names, use="official")

    # Add specialty if provided
    if specialty:
        practitioner.add_qualification(
            code=CodeableConcept(text=f"{specialty} Specialty"),
        )

    # Add license if provided
    if license_number:
        practitioner.add_qualification(
            code=CodeableConcept(text="Medical License"),
        )
        # Add license number as identifier
        if hasattr(practitioner, "identifier"):
            practitioner.identifier.append(Identifier(value=license_number, type_code="LIC"))

    return practitioner


def create_nurse(
    family_name: str,
    given_names: list[str],
    license_number: str | None = None,
    certification: str | None = None,
    **kwargs,
) -> Practitioner:
    """Create a nurse practitioner."""
    practitioner = Practitioner(active=True, **kwargs)

    # Add name
    practitioner.add_name(family=family_name, given=given_names, use="official")

    # Add nursing license
    practitioner.add_qualification(
        code=CodeableConcept(text="Registered Nurse License"),
    )

    # Add license number as identifier
    if license_number and hasattr(practitioner, "identifier"):
        practitioner.identifier.append(Identifier(value=license_number, type_code="LIC"))

    # Add certification if provided
    if certification:
        practitioner.add_qualification(
            code=CodeableConcept(text=f"{certification} Certification"),
        )

    return practitioner


def create_therapist(
    family_name: str,
    given_names: list[str],
    therapy_type: str,
    license_number: str | None = None,
    **kwargs,
) -> Practitioner:
    """Create a therapist practitioner."""
    practitioner = Practitioner(active=True, **kwargs)

    # Add name
    practitioner.add_name(family=family_name, given=given_names, use="official")

    # Add therapy qualification
    practitioner.add_qualification(
        code=CodeableConcept(text=f"{therapy_type} Therapy License"),
    )

    # Add license number as identifier
    if license_number and hasattr(practitioner, "identifier"):
        practitioner.identifier.append(Identifier(value=license_number, type_code="LIC"))

    return practitioner
