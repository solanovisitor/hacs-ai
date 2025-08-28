"""
Organization model for HACS.

This module provides a FHIR R4-compliant Organization resource model,
which is essential for healthcare facility representation and organizational management.

FHIR R4 Specification:
https://hl7.org/fhir/R4/organization.html
"""

from typing import Any, Literal

from pydantic import Field, field_validator

from .base_resource import DomainResource
from .observation import CodeableConcept
from .patient import Address, ContactPoint, Identifier
from .types import ResourceReference


class OrganizationContact(DomainResource):
    """
    Organization contact details.

    Contact information for specific purposes (billing, administration, etc.)
    within an organization.
    """

    resource_type: Literal["OrganizationContact"] = Field(
        default="OrganizationContact", description="Resource type identifier"
    )

    # Purpose of the contact
    purpose: CodeableConcept | None = Field(
        None, description="The type of contact (billing, admin, hr, payor, etc.)"
    )

    # Contact name
    name: str | None = Field(None, description="Name of an individual to contact", max_length=200)

    # Contact methods
    telecom: list[ContactPoint] = Field(
        default_factory=list, description="Contact details (phone, email, etc.) for the contact"
    )

    # Contact address
    address: Address | None = Field(
        None, description="Visiting or postal addresses for the contact"
    )


class Organization(DomainResource):
    """
    Organization resource for healthcare facility representation.

    A formally or informally recognized grouping of people or organizations
    formed for the purpose of achieving some form of collective action.
    Includes companies, institutions, corporations, departments, community groups,
    healthcare practice groups, payer/insurer, etc.
    """

    resource_type: Literal["Organization"] = Field(
        default="Organization", description="Resource type identifier"
    )

    # Business identifiers for the organization
    identifier: list[Identifier] = Field(
        default_factory=list, description="Identifies this organization across multiple systems"
    )

    # Whether this organization's record is in active use
    active: bool | None = Field(
        None, description="Whether the organization's record is still in active use"
    )

    # Type of organization
    type: list[CodeableConcept] = Field(
        default_factory=list, description="Kind of organization (hospital, clinic, dept, etc.)"
    )

    # Name used for the organization
    name: str | None = Field(None, description="Name used for the organization", max_length=200)

    # Alternative names (aliases)
    alias: list[str] = Field(
        default_factory=list, description="Alternative names the organization is known as"
    )

    # Description of the organization
    description: str | None = Field(
        None, description="Additional details about the organization that could be displayed"
    )

    # Contact information
    telecom: list[ContactPoint] = Field(
        default_factory=list, description="Contact details for the organization"
    )

    # Addresses for the organization
    address: list[Address] = Field(
        default_factory=list, description="Address(es) for the organization"
    )

    # Organization hierarchy
    part_of: ResourceReference | None = Field(
        None, description="The organization this organization forms a part of"
    )

    # Specific contacts for various purposes
    contact: list[OrganizationContact] = Field(
        default_factory=list, description="Contact for the organization for a certain purpose"
    )

    # Technical endpoints providing access to services
    endpoint: list[ResourceReference] = Field(
        default_factory=list,
        description="Technical endpoints providing access to services operated for the organization",
    )

    # Anonymous organization support for analytics
    anonymous: bool = Field(
        default=False,
        description="Whether this is an anonymous organization record (relaxes name requirements)",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate organization name."""
        if v is not None:
            name = v.strip()
            if not name:
                return None
            if len(name) > 200:
                raise ValueError("Organization name cannot exceed 200 characters")
            return name
        return v

    @property
    def is_active(self) -> bool:
        """Check if organization is active (defaults to True if not specified)."""
        return self.active if self.active is not None else True

    @property
    def display_name(self) -> str:
        """Get display name for the organization."""
        # Handle anonymous organizations
        if self.anonymous and not self.name and not self.alias:
            return "Anonymous Organization"

        if self.name:
            return self.name
        elif self.alias:
            return self.alias[0]
        return f"Organization {self.id or 'Unknown'}"

    @property
    def primary_address(self) -> Address | None:
        """Get the primary address for this organization."""
        if not self.address:
            return None

        # Look for work address first
        for addr in self.address:
            if hasattr(addr, "use") and addr.use == "work":
                return addr

        # Return first address
        return self.address[0] if self.address else None

    @property
    def primary_contact(self) -> ContactPoint | None:
        """Get the primary contact point for this organization."""
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
    def organization_types(self) -> list[str]:
        """Get list of organization type descriptions."""
        types = []
        for org_type in self.type:
            if hasattr(org_type, "text") and org_type.text:
                types.append(org_type.text)
            elif hasattr(org_type, "coding") and org_type.coding:
                for coding in org_type.coding:
                    if hasattr(coding, "display") and coding.display:
                        types.append(coding.display)
                        break
        return types

    @property
    def is_healthcare_provider(self) -> bool:
        """Check if this is a healthcare provider organization."""
        healthcare_keywords = ["hospital", "clinic", "medical", "health", "care", "practice"]
        org_types = [t.lower() for t in self.organization_types]
        name_lower = self.name.lower() if self.name else ""

        # Check organization types
        for keyword in healthcare_keywords:
            if any(keyword in org_type for org_type in org_types):
                return True

        # Check name
        for keyword in healthcare_keywords:
            if keyword in name_lower:
                return True

        return False

    def add_type(self, type_text: str) -> CodeableConcept:
        """Add an organization type."""
        org_type = CodeableConcept(text=type_text)
        self.type.append(org_type)
        return org_type

    def add_contact_info(
        self, system: str, value: str, use: str = "work", **kwargs
    ) -> ContactPoint:
        """Add contact information to this organization."""
        contact = ContactPoint(system=system, value=value, use=use, **kwargs)
        self.telecom.append(contact)
        return contact

    def add_contact_person(
        self,
        name: str,
        purpose: str | None = None,
        phone: str | None = None,
        email: str | None = None,
    ) -> OrganizationContact:
        """Add a contact person for this organization."""
        contact = OrganizationContact(
            name=name, purpose=CodeableConcept(text=purpose) if purpose else None
        )

        if phone:
            contact.telecom.append(ContactPoint(system="phone", value=phone, use="work"))
        if email:
            contact.telecom.append(ContactPoint(system="email", value=email, use="work"))

        self.contact.append(contact)
        return contact

    def get_contacts_by_purpose(self, purpose: str) -> list[OrganizationContact]:
        """Get contacts by purpose (e.g., 'billing', 'admin', 'emergency')."""
        matching = []
        for contact in self.contact:
            if contact.purpose and hasattr(contact.purpose, "text"):
                if purpose.lower() in contact.purpose.text.lower():
                    matching.append(contact)
        return matching

    # --- LLM-friendly extractable facade overrides ---
    @classmethod
    def get_extractable_fields(cls) -> list[str]:  # type: ignore[override]
        # Focus on essential organization info LLMs can reliably extract
        return [
            "name",           # Primary organization name
            "type",           # Organization type/specialty
            "anonymous",      # Flag for anonymous facilities
            "description",    # Brief description when mentioned
        ]

    @classmethod
    def get_required_extractables(cls) -> list[str]:
        """Fields that are absolutely required for a valid Organization extraction."""
        return []  # No fields strictly required - allow anonymous organizations

    @classmethod
    def get_canonical_defaults(cls) -> dict[str, Any]:
        """Default values for system/required fields during extraction."""
        return {
            "active": True,  # Default to active organization
            "anonymous": False,  # Required by facades for extraction
        }

    @classmethod
    def get_extraction_examples(cls) -> dict[str, Any]:
        """Return extraction examples showing different extractable field scenarios."""
        # Named healthcare organization
        named_example = {
            "name": "Hospital Santa Casa",
            "type": [{"text": "hospital"}],
            "anonymous": False,
        }

        # Anonymous healthcare facility
        anonymous_example = {
            "type": [{"text": "clínica"}],
            "anonymous": True,
        }

        # Specialized facility with description
        specialized_example = {
            "name": "Centro de Cardiologia",
            "type": [{"text": "specialty clinic"}],
            "description": "Centro especializado em cardiologia",
            "anonymous": False,
        }

        return {
            "object": named_example,
            "array": [named_example, anonymous_example, specialized_example],
            "scenarios": {
                "named": named_example,
                "anonymous": anonymous_example,
                "specialized": specialized_example,
            }
        }

    @classmethod
    def llm_hints(cls) -> list[str]:  # type: ignore[override]
        return [
            "- Extract organization name from: 'Hospital', 'Clínica', 'Centro Médico', facility mentions",
            "- Set anonymous=true if healthcare facility mentioned but no identifiable name given",
            "- Include organization type/specialty in type field (hospital, clinic, pharmacy)",
            "- Extract only when a healthcare organization/facility is explicitly mentioned",
            "- Focus on healthcare facilities, not general businesses or personal names",
        ]

    @classmethod
    def get_facades(cls) -> dict[str, "FacadeSpec"]:
        """Return available extraction facades for Organization."""
        from .base_resource import FacadeSpec
        
        return {
            "info": FacadeSpec(
                fields=["name", "type", "anonymous", "description"],
                required_fields=["anonymous"],
                field_examples={
                    "name": "Hospital Santa Casa",
                    "type": [{"text": "hospital"}],
                    "anonymous": False,
                    "description": "Regional teaching hospital"
                },
                field_types={
                    "name": "str | None",
                    "type": "list[CodeableConcept]",
                    "anonymous": "bool",
                    "description": "str | None"
                },
                description="Core organization identification and classification",
                llm_guidance="Use this facade for extracting basic organization identity from clinical notes or documents. Focus on healthcare facilities mentioned in context.",
                conversational_prompts=[
                    "What healthcare organizations are mentioned?",
                    "Where did this encounter take place?",
                    "Which hospital or clinic was involved?"
                ]
            ),
            
            "contact": FacadeSpec(
                fields=["name", "telecom", "address", "anonymous"],
                required_fields=["anonymous"],
                field_examples={
                    "name": "Centro Médico Regional",
                    "telecom": [{"system": "phone", "value": "(11) 9999-9999", "use": "work"}],
                    "address": [{"use": "work", "line": ["Rua das Flores, 123"], "city": "São Paulo"}],
                    "anonymous": False
                },
                field_types={
                    "name": "str | None",
                    "telecom": "list[ContactPoint]",
                    "address": "list[Address]",
                    "anonymous": "bool"
                },
                description="Organization contact and location information",
                llm_guidance="Extract contact details when organization location, phone, or address information is mentioned in the text.",
                conversational_prompts=[
                    "What is the organization's contact information?",
                    "Where is this facility located?",
                    "How can this organization be reached?"
                ]
            ),
            
            "hierarchy": FacadeSpec(
                fields=["name", "type", "part_of", "anonymous"],
                required_fields=["anonymous"],
                field_examples={
                    "name": "Cardiology Department",
                    "type": [{"text": "department"}],
                    "part_of": {"reference": "Organization/hospital-main"},
                    "anonymous": False
                },
                field_types={
                    "name": "str | None",
                    "type": "list[CodeableConcept]",
                    "part_of": "ResourceReference | None", 
                    "anonymous": "bool"
                },
                description="Organization structure and parent relationships",
                llm_guidance="Use when extracting departmental or subsidiary organization information that shows hierarchical relationships.",
                conversational_prompts=[
                    "Which department or unit is involved?",
                    "What is the organizational structure?",
                    "Which facility is this part of?"
                ]
            ),
            
            "identity": FacadeSpec(
                fields=["name", "identifier", "alias", "active", "anonymous"],
                required_fields=["anonymous"],
                field_examples={
                    "name": "Hospital das Clínicas",
                    "identifier": [{"value": "1234567890", "type": "NPI"}],
                    "alias": ["HC", "Hospital das Clínicas SP"],
                    "active": True,
                    "anonymous": False
                },
                field_types={
                    "name": "str | None",
                    "identifier": "list[Identifier]",
                    "alias": "list[str]",
                    "active": "bool | None",
                    "anonymous": "bool"
                },
                description="Complete organization identification and alternative names",
                llm_guidance="Extract comprehensive organization identity when multiple names, codes, or identifiers are mentioned.",
                conversational_prompts=[
                    "What are all the names this organization is known by?",
                    "What are the organization's official identifiers?",
                    "Is this organization currently active?"
                ]
            )
        }


# Convenience functions for common organization types


def create_hospital(
    name: str, npi: str | None = None, phone: str | None = None, **kwargs
) -> Organization:
    """Create a hospital organization."""
    hospital = Organization(name=name, active=True, **kwargs)

    # Add hospital type
    hospital.add_type("Hospital")

    # Add NPI identifier if provided
    if npi:
        hospital.identifier.append(
            Identifier(value=npi, type_code="NPI", system="http://hl7.org/fhir/sid/us-npi")
        )

    # Add phone if provided
    if phone:
        hospital.add_contact_info("phone", phone, "work")

    return hospital


def create_clinic(
    name: str, specialty: str | None = None, npi: str | None = None, **kwargs
) -> Organization:
    """Create a clinic organization."""
    clinic = Organization(name=name, active=True, **kwargs)

    # Add clinic type
    if specialty:
        clinic.add_type(f"{specialty} Clinic")
    else:
        clinic.add_type("Clinic")

    # Add NPI identifier if provided
    if npi:
        clinic.identifier.append(
            Identifier(value=npi, type_code="NPI", system="http://hl7.org/fhir/sid/us-npi")
        )

    return clinic


def create_department(
    name: str,
    parent_organization: ResourceReference | None = None,
    department_type: str = "Department",
    **kwargs,
) -> Organization:
    """Create a department organization."""
    department = Organization(name=name, active=True, part_of=parent_organization, **kwargs)

    # Add department type
    department.add_type(department_type)

    return department


def create_insurance_organization(name: str, payer_id: str | None = None, **kwargs) -> Organization:
    """Create an insurance/payer organization."""
    insurer = Organization(name=name, active=True, **kwargs)

    # Add insurance type
    insurer.add_type("Insurance Company")
    insurer.add_type("Payer")

    # Add payer identifier if provided
    if payer_id:
        insurer.identifier.append(Identifier(value=payer_id, type_code="PAYOR"))

    return insurer


def create_pharmacy(
    name: str, ncpdp: str | None = None, npi: str | None = None, **kwargs
) -> Organization:
    """Create a pharmacy organization."""
    pharmacy = Organization(name=name, active=True, **kwargs)

    # Add pharmacy type
    pharmacy.add_type("Pharmacy")

    # Add NCPDP identifier if provided
    if ncpdp:
        pharmacy.identifier.append(Identifier(value=ncpdp, type_code="NCPDP"))

    # Add NPI identifier if provided
    if npi:
        pharmacy.identifier.append(
            Identifier(value=npi, type_code="NPI", system="http://hl7.org/fhir/sid/us-npi")
        )

    return pharmacy
