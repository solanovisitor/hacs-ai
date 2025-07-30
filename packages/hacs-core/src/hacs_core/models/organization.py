"""
Organization Model for HACS - Healthcare Access Control System

Based on FHIR R5 Organization Resource:
A formally or informally recognized grouping of people or organizations
formed for the purpose of achieving some form of collective action.

Examples: companies, institutions, corporations, departments, community groups,
healthcare practice groups, payer/insurer, etc.
"""

from typing import Dict, List, Literal, Optional

from pydantic import Field, field_validator, computed_field

from ..base_resource import BaseResource


class OrganizationQualification(BaseResource):
    """
    Qualifications, certifications, accreditations, licenses, training, etc.
    pertaining to the provision of care by the organization.
    """

    resource_type: Literal["OrganizationQualification"] = Field(
        default="OrganizationQualification",
        description="Resource type identifier"
    )

    identifier: List[str] = Field(
        default_factory=list,
        description="Identifiers for this qualification",
        examples=[["license-123", "cert-456"], ["accred-789"]]
    )

    code: Dict[str, str] = Field(
        description="Coded representation of the qualification",
        examples=[
            {"code": "MD", "display": "Medical Doctor", "system": "http://terminology.hl7.org/CodeSystem/v2-0360"},
            {"code": "CERT-001", "display": "Hospital Accreditation", "system": "local"}
        ]
    )

    status: Optional[Dict[str, str]] = Field(
        default=None,
        description="Status/progress of the qualification",
        examples=[
            {"code": "active", "display": "Active"},
            {"code": "inactive", "display": "Inactive"},
            {"code": "pending", "display": "Pending"}
        ]
    )

    period_start: Optional[str] = Field(
        default=None,
        description="Start date of qualification validity (YYYY-MM-DD format)",
        examples=["2023-01-01", "2024-06-15"]
    )

    period_end: Optional[str] = Field(
        default=None,
        description="End date of qualification validity (YYYY-MM-DD format)",
        examples=["2025-12-31", "2026-06-14"]
    )

    issuer_organization_id: Optional[str] = Field(
        default=None,
        description="ID of organization that regulates and issues the qualification",
        examples=["org-medical-board", "org-state-health-dept"]
    )

    issuer_name: Optional[str] = Field(
        default=None,
        description="Name of issuing organization for display purposes",
        examples=["State Medical Board", "Joint Commission"]
    )


class OrganizationContact(BaseResource):
    """
    Official contact details for the Organization.
    Extended contact information including purpose, name, and contact details.
    """

    resource_type: Literal["OrganizationContact"] = Field(
        default="OrganizationContact",
        description="Resource type identifier"
    )

    purpose: Optional[Dict[str, str]] = Field(
        default=None,
        description="Purpose/type of contact",
        examples=[
            {"code": "ADMIN", "display": "Administrative"},
            {"code": "HR", "display": "Human Resource"},
            {"code": "PAYOR", "display": "Payor"},
            {"code": "PATINF", "display": "Patient Information"},
            {"code": "PRESS", "display": "Press"}
        ]
    )

    contact_name: Optional[str] = Field(
        default=None,
        description="Name of contact person or department",
        examples=["John Smith", "Patient Relations Department", "Emergency Contact"]
    )

    # Direct contact fields (HACS simplified approach)
    email: Optional[str] = Field(
        default=None,
        description="Primary email address",
        examples=["contact@hospital.org", "admin@clinic.com"]
    )

    phone: Optional[str] = Field(
        default=None,
        description="Primary phone number",
        examples=["+1-555-0123", "1-800-HOSPITAL"]
    )

    fax: Optional[str] = Field(
        default=None,
        description="Fax number",
        examples=["+1-555-0124", "1-800-FAX-HOSP"]
    )

    # Address fields (simplified)
    address_line: List[str] = Field(
        default_factory=list,
        description="Street address lines",
        examples=[["123 Main St", "Suite 100"], ["456 Hospital Dr"]]
    )

    city: Optional[str] = Field(
        default=None,
        description="City name",
        examples=["Boston", "New York", "Los Angeles"]
    )

    state: Optional[str] = Field(
        default=None,
        description="State or province",
        examples=["MA", "NY", "CA", "Massachusetts"]
    )

    postal_code: Optional[str] = Field(
        default=None,
        description="Postal or ZIP code",
        examples=["02101", "10001", "90210"]
    )

    country: Optional[str] = Field(
        default=None,
        description="Country",
        examples=["US", "USA", "United States"]
    )

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate email format."""
        if v and "@" not in v:
            raise ValueError("Email must contain @ symbol")
        return v

    @computed_field
    @property
    def full_address(self) -> str:
        """Get formatted full address."""
        parts = []
        if self.address_line:
            parts.extend(self.address_line)
        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.postal_code:
            parts.append(self.postal_code)
        if self.country:
            parts.append(self.country)
        return ", ".join(parts)


class Organization(BaseResource):
    """
    HACS Organization Model - A grouping of people or organizations with a common purpose.

    Based on FHIR R5 Organization Resource with HACS-specific optimizations.

    Key Features:
    - LLM-friendly field structure (direct fields vs nested FHIR arrays)
    - Healthcare-specific organization types and qualifications
    - Hierarchical organization support via part_of relationships
    - Contact information management
    - Active/inactive status tracking
    """

    resource_type: Literal["Organization"] = Field(
        default="Organization",
        description="Resource type identifier"
    )

    # Core identification
    identifier: List[str] = Field(
        default_factory=list,
        description="Business identifiers for this organization across multiple systems",
        examples=[["NPI-1234567890", "TIN-12-3456789"], ["DEA-AB1234567"]]
    )

    active: bool = Field(
        default=True,
        description="Whether the organization's record is still in active use"
    )

    # Organization type and classification
    organization_type: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Kind/type of organization",
        examples=[
            [{"code": "prov", "display": "Healthcare Provider", "system": "http://terminology.hl7.org/CodeSystem/organization-type"}],
            [{"code": "dept", "display": "Hospital Department"}, {"code": "edu", "display": "Educational Institute"}]
        ]
    )

    # Names and aliases
    name: Optional[str] = Field(
        default=None,
        description="Primary name used for the organization",
        examples=["General Hospital", "ABC Medical Center", "City Health Department"]
    )

    alias: List[str] = Field(
        default_factory=list,
        description="Alternate names that the organization is known as, or was known as in the past",
        examples=[["City General", "General"], ["ABC Medical", "ABC Health System"]]
    )

    # Description and details
    description: Optional[str] = Field(
        default=None,
        description="Additional details about the Organization beyond its name",
        examples=[
            "A 500-bed tertiary care hospital serving the greater metropolitan area",
            "Community health center providing primary care services to underserved populations"
        ]
    )

    # Hierarchy and relationships
    part_of_organization_id: Optional[str] = Field(
        default=None,
        description="ID of the parent organization this organization forms a part of",
        examples=["org-health-system", "org-university-medical"]
    )

    part_of_organization_name: Optional[str] = Field(
        default=None,
        description="Name of parent organization for display purposes",
        examples=["Metro Health System", "University Medical Center"]
    )

    # Contact information - primary organizational contact
    primary_email: Optional[str] = Field(
        default=None,
        description="Primary organizational email address",
        examples=["info@hospital.org", "contact@clinic.com"]
    )

    primary_phone: Optional[str] = Field(
        default=None,
        description="Primary organizational phone number",
        examples=["+1-555-0123", "1-800-HOSPITAL"]
    )

    website: Optional[str] = Field(
        default=None,
        description="Organization website URL",
        examples=["https://www.hospital.org", "https://clinic.com"]
    )

    # Address fields for primary location
    address_line: List[str] = Field(
        default_factory=list,
        description="Street address lines for primary location",
        examples=[["123 Hospital Drive", "Building A"], ["456 Medical Center Blvd"]]
    )

    city: Optional[str] = Field(
        default=None,
        description="City of primary location",
        examples=["Boston", "New York", "Los Angeles"]
    )

    state: Optional[str] = Field(
        default=None,
        description="State or province of primary location",
        examples=["MA", "NY", "CA", "Massachusetts"]
    )

    postal_code: Optional[str] = Field(
        default=None,
        description="Postal or ZIP code of primary location",
        examples=["02101", "10001", "90210"]
    )

    country: Optional[str] = Field(
        default=None,
        description="Country of primary location",
        examples=["US", "USA", "United States"]
    )

    # Extended contact details
    contacts: List[OrganizationContact] = Field(
        default_factory=list,
        description="Official contact details for specific purposes"
    )

    # Qualifications and certifications
    qualifications: List[OrganizationQualification] = Field(
        default_factory=list,
        description="Qualifications, certifications, accreditations, licenses, training, etc."
    )

    # Technical endpoints
    endpoint_urls: List[str] = Field(
        default_factory=list,
        description="Technical endpoints providing access to services operated for the organization",
        examples=[["https://api.hospital.org/fhir", "https://portal.hospital.org"]]
    )

    # Additional metadata
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorizing and searching organizations",
        examples=[["hospital", "emergency_care"], ["clinic", "primary_care", "pediatrics"]]
    )

    # FHIR Constraint validation
    @field_validator("name")
    @classmethod
    def validate_name_or_identifier_required(cls, v: Optional[str], info) -> Optional[str]:
        """Ensure organization has at least a name or identifier (FHIR org-1 constraint)."""
        # Note: This is a simplified validation - full validation would check both fields
        if not v and hasattr(info, 'data') and not info.data.get('identifier'):
            raise ValueError("Organization must have at least a name or identifier")
        return v

    @field_validator("primary_email")
    @classmethod
    def validate_email_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate email format."""
        if v and "@" not in v:
            raise ValueError("Email must contain @ symbol")
        return v

    @computed_field
    @property
    def display_name(self) -> str:
        """Get the best display name for this organization."""
        if self.name:
            return self.name
        elif self.alias:
            return self.alias[0]
        elif self.identifier:
            return f"Organization {self.identifier[0]}"
        else:
            return f"Organization {self.id or 'Unknown'}"

    @computed_field
    @property
    def primary_address(self) -> str:
        """Get formatted primary address."""
        parts = []
        if self.address_line:
            parts.extend(self.address_line)
        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.postal_code:
            parts.append(self.postal_code)
        if self.country:
            parts.append(self.country)
        return ", ".join(parts)

    @computed_field
    @property
    def organization_types_display(self) -> List[str]:
        """Get human-readable organization types."""
        return [org_type.get("display", org_type.get("code", "Unknown"))
                for org_type in self.organization_type]

    @computed_field
    @property
    def is_healthcare_provider(self) -> bool:
        """Check if this is a healthcare provider organization."""
        provider_codes = ["prov", "hospital", "clinic", "practice"]
        return any(
            org_type.get("code", "").lower() in provider_codes
            for org_type in self.organization_type
        )

    @computed_field
    @property
    def active_qualifications(self) -> List[OrganizationQualification]:
        """Get list of active qualifications."""
        return [
            qual for qual in self.qualifications
            if not qual.status or qual.status.get("code") == "active"
        ]

    def add_qualification(
        self,
        code: Dict[str, str],
        status: Optional[Dict[str, str]] = None,
        period_start: Optional[str] = None,
        period_end: Optional[str] = None,
        issuer_name: Optional[str] = None
    ) -> None:
        """Add a qualification to this organization."""
        qualification = OrganizationQualification(
            code=code,
            status=status or {"code": "active", "display": "Active"},
            period_start=period_start,
            period_end=period_end,
            issuer_name=issuer_name
        )
        self.qualifications.append(qualification)

    def add_contact(
        self,
        purpose: Optional[Dict[str, str]] = None,
        contact_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address_line: Optional[List[str]] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        postal_code: Optional[str] = None,
        country: Optional[str] = None
    ) -> None:
        """Add a contact to this organization."""
        contact = OrganizationContact(
            purpose=purpose,
            contact_name=contact_name,
            email=email,
            phone=phone,
            address_line=address_line or [],
            city=city,
            state=state,
            postal_code=postal_code,
            country=country
        )
        self.contacts.append(contact)

    def get_contacts_by_purpose(self, purpose_code: str) -> List[OrganizationContact]:
        """Get contacts filtered by purpose code."""
        return [
            contact for contact in self.contacts
            if contact.purpose and contact.purpose.get("code") == purpose_code
        ]

    def deactivate(self, reason: Optional[str] = None) -> None:
        """Deactivate this organization."""
        self.active = False
        if reason:
            self.tags.append(f"deactivated:{reason}")

    def activate(self) -> None:
        """Reactivate this organization."""
        self.active = True
        # Remove deactivation tags
        self.tags = [tag for tag in self.tags if not tag.startswith("deactivated:")]

    def __repr__(self) -> str:
        """String representation of Organization."""
        status = "Active" if self.active else "Inactive"
        return f"Organization(id={self.id}, name='{self.display_name}', status={status})"