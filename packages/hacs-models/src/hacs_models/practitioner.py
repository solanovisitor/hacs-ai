"""
Practitioner model for HACS.

This module provides a FHIR R4-compliant Practitioner resource model,
which is essential for healthcare provider representation and care team management.

FHIR R4 Specification:
https://hl7.org/fhir/R4/practitioner.html
"""

from datetime import date
from typing import Any, Literal

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

    # Anonymous practitioner support for analytics
    anonymous: bool = Field(
        default=False,
        description="Whether this is an anonymous practitioner record (relaxes name requirements)",
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
        # Handle anonymous practitioners
        if self.anonymous and not self.name:
            return "Anonymous Practitioner"

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
        return ["name", "anonymous"]

    @classmethod
    def get_required_extractables(cls) -> list[str]:
        """Fields that are absolutely required for a valid Practitioner extraction."""
        return []  # No fields strictly required - allow anonymous practitioners

    @classmethod
    def get_canonical_defaults(cls) -> dict[str, Any]:
        """Default values for system/required fields during extraction."""
        return {
            "active": True,  # Default to active practitioner
            "anonymous": False,  # Required by facades for extraction
        }

    @classmethod
    def coerce_extractable(cls, payload: dict[str, Any], relax: bool = True) -> dict[str, Any]:
        """Coerce extractable payload to proper Practitioner field types."""
        coerced = payload.copy()
        
        # Handle name field - ensure it's a list of HumanName objects
        if "name" in coerced:
            name_data = coerced["name"]
            if isinstance(name_data, str):
                # Convert string to proper HumanName structure
                name_parts = name_data.strip().split()
                if len(name_parts) >= 2:
                    family = name_parts[-1]
                    given = name_parts[:-1]
                    coerced["name"] = [{"family": family, "given": given, "use": "usual"}]
                else:
                    coerced["name"] = [{"given": [name_data.strip()], "use": "usual"}]
            elif isinstance(name_data, list):
                # Ensure each name is properly structured
                processed_names = []
                for name_item in name_data:
                    if isinstance(name_item, dict):
                        # Remove any extra fields that aren't valid HumanName fields
                        valid_fields = ["family", "given", "use", "prefix", "suffix"]
                        cleaned_name = {k: v for k, v in name_item.items() if k in valid_fields}
                        processed_names.append(cleaned_name)
                    elif isinstance(name_item, str):
                        # Parse string to proper structure
                        name_parts = name_item.strip().split()
                        if len(name_parts) >= 2:
                            family = name_parts[-1]
                            given = name_parts[:-1]
                            processed_names.append({"family": family, "given": given, "use": "usual"})
                        else:
                            processed_names.append({"given": [name_item.strip()], "use": "usual"})
                coerced["name"] = processed_names
        
        # Handle gender string conversion
        if "gender" in coerced and isinstance(coerced["gender"], str):
            gender_str = coerced["gender"].lower()
            if gender_str in ["masculino", "male", "m"]:
                coerced["gender"] = "male"
            elif gender_str in ["feminino", "female", "f"]:
                coerced["gender"] = "female"
            elif gender_str in ["outro", "other", "o"]:
                coerced["gender"] = "other"
            elif gender_str in ["desconhecido", "unknown", "u"]:
                coerced["gender"] = "unknown"
        
        # Handle identifier field - ensure proper structure
        if "identifier" in coerced and isinstance(coerced["identifier"], list):
            processed_identifiers = []
            for id_item in coerced["identifier"]:
                if isinstance(id_item, dict):
                    # Clean up identifier structure
                    valid_fields = ["value", "type", "use", "system"]
                    cleaned_id = {k: v for k, v in id_item.items() if k in valid_fields}
                    processed_identifiers.append(cleaned_id)
                elif isinstance(id_item, str):
                    processed_identifiers.append({"value": id_item, "use": "usual"})
            coerced["identifier"] = processed_identifiers
        
        # Handle qualification field - ensure proper structure
        if "qualification" in coerced and isinstance(coerced["qualification"], list):
            processed_qualifications = []
            for qual_item in coerced["qualification"]:
                if isinstance(qual_item, dict):
                    # Ensure qualification has required code field
                    if "code" in qual_item:
                        processed_qualifications.append(qual_item)
                    elif "text" in qual_item:
                        # Convert text to code structure
                        processed_qualifications.append({
                            "code": {"text": qual_item["text"]}
                        })
            coerced["qualification"] = processed_qualifications
        
        # Remove system fields that shouldn't be LLM-generated
        system_fields = ["id", "created_at", "updated_at", "version", "meta_tag"]
        for field in system_fields:
            coerced.pop(field, None)
        
        return coerced

    @classmethod
    def llm_hints(cls) -> list[str]:
        """Return LLM-specific extraction hints for Practitioner."""
        return [
            "- Extract practitioner name from: 'Dr.', 'doutora', 'médico', explicit healthcare provider mentions",
            "- Set anonymous=true if healthcare provider mentioned but no identifiable name given",
            "- Extract only when a healthcare provider is explicitly mentioned",
            "- Focus on doctors, nurses, therapists, not patients or family members",
        ]

    @classmethod
    def get_facades(cls) -> dict[str, "FacadeSpec"]:
        """Return available extraction facades for Practitioner."""
        from .base_resource import FacadeSpec
        
        return {
            "identity": FacadeSpec(
                fields=["name", "gender", "anonymous", "active"],
                required_fields=["anonymous"],
                field_examples={
                    "name": [{"family": "Santos", "given": ["Maria", "Clara"], "use": "official", "prefix": ["Dr."]}],
                    "gender": "female",
                    "anonymous": False,
                    "active": True
                },
                field_types={
                    "name": "list[HumanName]",
                    "gender": "Gender | None",
                    "anonymous": "bool", 
                    "active": "bool | None"
                },
                description="Core practitioner identification and basic demographics",
                llm_guidance="Use this facade for extracting healthcare provider identity from clinical documentation. Focus on names, titles, and basic information mentioned.",
                conversational_prompts=[
                    "Who is the attending physician?",
                    "Which doctor is providing care?",
                    "What healthcare providers are involved?"
                ]
            ),
            
            "contact": FacadeSpec(
                fields=["name", "telecom", "address", "anonymous"],
                required_fields=["anonymous"],
                field_examples={
                    "name": [{"text": "Dr. João Silva", "use": "official"}],
                    "telecom": [{"system": "phone", "value": "(11) 98765-4321", "use": "work"}],
                    "address": [{"use": "work", "line": ["Consultório Médico"], "city": "São Paulo"}],
                    "anonymous": False
                },
                field_types={
                    "name": "list[HumanName]",
                    "telecom": "list[ContactPoint]",
                    "address": "list[Address]",
                    "anonymous": "bool"
                },
                description="Practitioner contact and location information",
                llm_guidance="Extract contact details when provider contact information, office location, or communication details are mentioned.",
                conversational_prompts=[
                    "How can I contact my doctor?",
                    "What is the provider's office address?",
                    "Where can I reach the healthcare provider?"
                ]
            ),
            
            "qualifications": FacadeSpec(
                fields=["name", "qualification", "communication", "anonymous"],
                required_fields=["anonymous"],
                field_examples={
                    "name": [{"text": "Dr. Ana Cardiologista", "use": "professional"}],
                    "qualification": [{"code": {"text": "Cardiology Specialty"}}],
                    "communication": [{"text": "Portuguese"}, {"text": "English"}],
                    "anonymous": False
                },
                field_types={
                    "name": "list[HumanName]",
                    "qualification": "list[PractitionerQualification]",
                    "communication": "list[CodeableConcept]",
                    "anonymous": "bool"
                },
                description="Practitioner specialties, certifications, and languages",
                llm_guidance="Use when extracting provider specialties, board certifications, training, or language capabilities mentioned in documentation.",
                conversational_prompts=[
                    "What is the doctor's specialty?",
                    "What languages does the provider speak?",
                    "What are the provider's qualifications?"
                ]
            ),
            
            "professional": FacadeSpec(
                fields=["name", "identifier", "qualification", "active", "anonymous"],
                required_fields=["anonymous"],
                field_examples={
                    "name": [{"family": "Silva", "given": ["Roberto"], "prefix": ["Dr."], "use": "official"}],
                    "identifier": [{"value": "CRM-123456", "type": "license"}],
                    "qualification": [{"code": {"text": "Medical License"}}],
                    "active": True,
                    "anonymous": False
                },
                field_types={
                    "name": "list[HumanName]",
                    "identifier": "list[Identifier]",
                    "qualification": "list[PractitionerQualification]",
                    "active": "bool | None",
                    "anonymous": "bool"
                },
                description="Complete professional practitioner profile with licenses and credentials",
                llm_guidance="Extract comprehensive practitioner information when license numbers, professional credentials, or full professional identity is documented.",
                conversational_prompts=[
                    "What are the provider's professional credentials?",
                    "What is the practitioner's license information?",
                    "Who is the qualified healthcare professional?"
                ]
            )
        }


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
