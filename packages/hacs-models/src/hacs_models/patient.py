"""
Patient model for healthcare data representation.

This module provides a comprehensive, FHIR-compliant Patient model optimized 
for AI agent communication and healthcare workflows. Features automatic data 
parsing, flexible name handling, and comprehensive validation.

Key Features:
    - FHIR R4/R5 compliant structure
    - Automatic name parsing from full_name
    - Smart contact information handling
    - Age calculation and validation
    - Comprehensive identifier management
    - AI-optimized field structure

Design Philosophy:
    - Flexible input formats for AI agents
    - Strict validation for data integrity
    - Rich computed properties for convenience
    - Immutable design with update tracking
"""

from datetime import date
from typing import Any, Literal

from pydantic import Field, computed_field, field_validator

from .base_resource import DomainResource
from .types import Gender, ContactPointSystem, ContactPointUse, IdentifierUse, AddressUse, NameUse


class HumanName(DomainResource):
    """
    Structured representation of a human name.
    
    Follows FHIR HumanName structure with extensions for AI-friendly parsing.
    Supports automatic parsing from full name strings while maintaining
    structured data integrity.
    """
    
    resource_type: Literal["HumanName"] = Field(
        default="HumanName",
        description="Resource type identifier"
    )
    
    use: NameUse | None = Field(
        default=None,
        description="Purpose of this name (usual, official, nickname, etc.)",
        examples=["usual", "official", "maiden"]
    )
    
    family: str | None = Field(
        default=None,
        description="Family name (surname, last name)",
        examples=["Smith", "Johnson", "García", "O'Connor"],
        max_length=100
    )
    
    given: list[str] = Field(
        default_factory=list,
        description="Given names (first, middle names)",
        examples=[["John"], ["Mary", "Jane"], ["José", "María"]],
        max_length=5  # Reasonable limit on given names
    )
    
    prefix: list[str] = Field(
        default_factory=list,
        description="Parts that come before the name (titles, prefixes)",
        examples=[["Dr."], ["Mr.", "Prof."], ["Ms.", "PhD"]],
        max_length=3
    )
    
    suffix: list[str] = Field(
        default_factory=list,
        description="Parts that come after the name (suffixes)",
        examples=[["Jr."], ["III"], ["MD", "PhD"]],
        max_length=3  
    )
    
    @field_validator("given", "prefix", "suffix")
    @classmethod
    def validate_name_parts(cls, v: list[str]) -> list[str]:
        """Validate and clean name part lists."""
        if not v:
            return []
        
        # Clean and validate each part
        cleaned = []
        for part in v:
            if not isinstance(part, str):
                raise ValueError("All name parts must be strings")
            
            clean_part = part.strip()
            if not clean_part:
                continue  # Skip empty strings
                
            if len(clean_part) > 50:
                raise ValueError("Individual name parts cannot exceed 50 characters")
                
            cleaned.append(clean_part)
        
        return cleaned
    
    @field_validator("family")
    @classmethod
    def validate_family_name(cls, v: str | None) -> str | None:
        """Validate family name."""
        if v is None:
            return None
            
        family = v.strip()
        if not family:
            return None
            
        if len(family) > 100:
            raise ValueError("Family name cannot exceed 100 characters")
            
        return family
    
    @computed_field
    @property
    def full_name(self) -> str:
        """Compute full name from components."""
        parts = []
        
        if self.prefix:
            parts.extend(self.prefix)
        if self.given:
            parts.extend(self.given)  
        if self.family:
            parts.append(self.family)
        if self.suffix:
            parts.extend(self.suffix)
            
        return " ".join(parts) if parts else "Unknown"
    
    @computed_field
    @property
    def display_name(self) -> str:
        """Compute display name (given + family only)."""
        parts = []
        
        if self.given:
            parts.extend(self.given)
        if self.family:
            parts.append(self.family)
            
        return " ".join(parts) if parts else self.full_name


class ContactPoint(DomainResource):
    """
    Contact information (phone, email, etc.) for a person or organization.
    
    Follows FHIR ContactPoint structure with validation for common
    contact methods and usage patterns.
    """
    
    resource_type: Literal["ContactPoint"] = Field(
        default="ContactPoint",
        description="Resource type identifier" 
    )
    
    system: ContactPointSystem = Field(
        description="Contact method type (phone, email, fax, etc.)",
        examples=["phone", "email", "fax"]
    )
    
    value: str = Field(
        description="The actual contact point value",
        examples=["+1-555-123-4567", "patient@example.com", "https://example.com"],
        min_length=1,
        max_length=255
    )
    
    use: ContactPointUse | None = Field(
        default=None,
        description="Purpose of this contact point",
        examples=["home", "work", "mobile"]
    )
    
    rank: int | None = Field(
        default=None,
        description="Preference order (1 = highest priority)",
        ge=1,
        le=10
    )
    
    @field_validator("value")
    @classmethod
    def validate_contact_value(cls, v: str, info) -> str:
        """Validate contact value based on system type."""
        value = v.strip()
        if not value:
            raise ValueError("Contact value cannot be empty")
        
        # Get system from validation info if available
        system = info.data.get("system") if hasattr(info, "data") and info.data else None
        
        # Basic validation based on system type
        if system == "email" and "@" not in value:
            raise ValueError("Email must contain @ symbol")
        elif system == "phone" and len(value) < 7:
            raise ValueError("Phone number must be at least 7 characters")
        elif system == "url" and not (value.startswith("http://") or value.startswith("https://")):
            if "." in value:  # Assume it's a domain without protocol
                value = f"https://{value}"
            else:
                raise ValueError("URL must be a valid web address")
        
        return value


class Address(DomainResource):
    """
    Physical or postal address for a person or organization.
    
    Follows FHIR Address structure with support for international
    addressing formats and automatic parsing from text.
    """
    
    resource_type: Literal["Address"] = Field(
        default="Address",
        description="Resource type identifier"
    )
    
    use: AddressUse | None = Field(
        default=None,
        description="Purpose of this address",
        examples=["home", "work", "billing"]
    )
    
    type_: str | None = Field(
        default=None,
        alias="type",
        description="Type of address (postal, physical, both)",
        examples=["postal", "physical", "both"]
    )
    
    text: str | None = Field(
        default=None,
        description="Full address as a single string",
        examples=["123 Main St, Anytown, CA 12345, USA"],
        max_length=500
    )
    
    line: list[str] = Field(
        default_factory=list,
        description="Street address lines",
        examples=[["123 Main Street"], ["456 Oak Ave", "Suite 200"]],
        max_length=4  # FHIR allows up to 4 lines
    )
    
    city: str | None = Field(
        default=None,
        description="City name",
        examples=["New York", "Los Angeles", "Boston"],
        max_length=100
    )
    
    district: str | None = Field(
        default=None,
        description="District/county name",
        examples=["Manhattan", "Orange County", "Suffolk"],
        max_length=100
    )
    
    state: str | None = Field(
        default=None,
        description="State/province code or name",
        examples=["CA", "NY", "Texas", "Ontario"],
        max_length=50
    )
    
    postal_code: str | None = Field(
        default=None,
        description="Postal/ZIP code",
        examples=["12345", "90210", "SW1A 1AA"],
        max_length=20
    )
    
    country: str | None = Field(
        default=None,
        description="Country code or name",
        examples=["US", "CA", "GB", "United States"],
        max_length=50
    )
    
    @field_validator("line")
    @classmethod
    def validate_address_lines(cls, v: list[str]) -> list[str]:
        """Validate address lines."""
        if not v:
            return []
        
        cleaned = []
        for line in v:
            if not isinstance(line, str):
                raise ValueError("Address lines must be strings")
            
            clean_line = line.strip()
            if clean_line:  # Only keep non-empty lines
                if len(clean_line) > 100:
                    raise ValueError("Address lines cannot exceed 100 characters")
                cleaned.append(clean_line)
        
        return cleaned
    
    @computed_field 
    @property
    def formatted_address(self) -> str:
        """Compute formatted address string."""
        if self.text:
            return self.text
        
        parts = []
        
        if self.line:
            parts.extend(self.line)
        
        city_state = []
        if self.city:
            city_state.append(self.city)
        if self.state:
            city_state.append(self.state)
        if self.postal_code:
            city_state.append(self.postal_code)
        
        if city_state:
            parts.append(" ".join(city_state))
        
        if self.country:
            parts.append(self.country)
        
        return ", ".join(parts) if parts else "No address provided"


class Identifier(DomainResource):
    """
    Identifier for a person or organization.
    
    Follows FHIR Identifier structure with support for various
    healthcare identifier types (MRN, SSN, etc.).
    """
    
    resource_type: Literal["Identifier"] = Field(
        default="Identifier",
        description="Resource type identifier"
    )
    
    use: IdentifierUse | None = Field(
        default=None,
        description="Purpose of this identifier",
        examples=["usual", "official", "secondary"]
    )
    
    type_code: str | None = Field(
        default=None,
        description="Type of identifier (MR, SSN, DL, etc.)",
        examples=["MR", "SSN", "DL", "PPN"],
        max_length=10
    )
    
    system: str | None = Field(
        default=None, 
        description="System that assigned the identifier",
        examples=["http://hospital.example.com/mrn", "http://hl7.org/fhir/sid/us-ssn"],
        max_length=255
    )
    
    value: str = Field(
        description="The identifier value",
        examples=["123456789", "555-12-3456", "DL123456"],
        min_length=1,
        max_length=100
    )
    
    assigner: str | None = Field(
        default=None,
        description="Organization that assigned the identifier",
        examples=["Example Hospital", "DMV", "Social Security Administration"],
        max_length=200
    )
    
    @field_validator("value")
    @classmethod
    def validate_identifier_value(cls, v: str) -> str:
        """Validate identifier value."""
        value = v.strip()
        if not value:
            raise ValueError("Identifier value cannot be empty")
        return value


class Patient(DomainResource):
    """
    Patient demographics and administrative information.
    
    Comprehensive patient model following FHIR Patient resource structure
    with AI-optimized features for flexible data input and automatic parsing.
    
    Key Features:
        - Automatic name parsing from full_name string
        - Flexible contact information handling  
        - Age calculation and validation
        - Comprehensive identifier management
        - Care team tracking
        - Agent context for AI workflows
    
    Example:
        >>> patient = Patient(
        ...     full_name="Dr. John Michael Smith Jr.",
        ...     birth_date="1985-03-15",
        ...     gender="male",
        ...     phone="+1-555-123-4567",
        ...     email="john.smith@example.com"
        ... )
        >>> print(patient.display_name)  # "John Michael Smith"
        >>> print(patient.age_years)     # Calculated from birth_date
    """
    
    resource_type: Literal["Patient"] = Field(
        default="Patient",
        description="Resource type identifier"
    )
    
    # Name information - flexible input options
    name: list[HumanName] = Field(
        default_factory=list,
        description="Patient names (structured format)",
        max_length=5  # Reasonable limit on names
    )
    
    # AI-friendly convenience fields for name input
    full_name: str | None = Field(
        default=None,
        description="Complete name as single string (auto-parsed into structured format)",
        examples=["Dr. John Michael Smith Jr.", "Mary Jane Johnson", "José María García"],
        max_length=200
    )
    
    # Demographics
    gender: Gender | None = Field(
        default=None,
        description="Administrative gender", 
        examples=["male", "female", "other", "unknown"]
    )
    
    birth_date: date | None = Field(
        default=None,
        description="Date of birth",
        examples=["1985-03-15", "1992-12-01"]
    )
    
    # AI-friendly age input (will calculate birth_date if not provided)
    age: int | None = Field(
        default=None,
        description="Age in years (will estimate birth_date if not provided)",
        examples=[39, 25, 67],
        ge=0,
        le=150
    )
    
    deceased_boolean: bool = Field(
        default=False,
        description="Whether the patient is deceased"
    )
    
    deceased_date_time: date | None = Field(
        default=None,
        description="Date of death if deceased"
    )
    
    # Contact information
    telecom: list[ContactPoint] = Field(
        default_factory=list,
        description="Contact points (phone, email, etc.)",
        max_length=10  # Reasonable limit
    )
    
    # AI-friendly convenience fields for contact input
    phone: str | None = Field(
        default=None,
        description="Primary phone number (auto-added to telecom)",
        examples=["+1-555-123-4567", "555-123-4567", "(555) 123-4567"],
        max_length=50
    )
    
    email: str | None = Field(
        default=None,
        description="Primary email address (auto-added to telecom)",
        examples=["patient@example.com", "john.smith@email.com"],
        max_length=255
    )
    
    # Address information
    address: list[Address] = Field(
        default_factory=list,
        description="Patient addresses",
        max_length=5  # Reasonable limit
    )
    
    # AI-friendly convenience field for address input
    address_text: str | None = Field(
        default=None,
        description="Simple address as text (auto-parsed into structured format)",
        examples=["123 Main St, Anytown, CA 12345", "456 Oak Ave, Suite 200, Boston, MA 02101"],
        max_length=500
    )
    
    # Marital status
    marital_status: str | None = Field(
        default=None,
        description="Marital status code (M=Married, S=Single, D=Divorced, W=Widowed, U=Unknown)",
        examples=["M", "S", "D", "W", "U"],
        max_length=10
    )
    
    # Language and communication preferences
    communication: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Languages and communication preferences",
        examples=[[{"language": "en-US", "preferred": True}]]
    )
    
    # AI-friendly language input
    language: str | None = Field(
        default=None,
        description="Primary language (auto-added to communication)",
        examples=["English", "Spanish", "en-US", "es-ES"],
        max_length=50
    )
    
    # Identifiers
    identifier: list[Identifier] = Field(
        default_factory=list,
        description="Patient identifiers (MRN, SSN, etc.)",
        max_length=10  # Reasonable limit
    )
    
    # Care management
    care_provider: list[str] = Field(
        default_factory=list,
        description="References to care providers and team members",
        examples=[["Practitioner/dr-smith", "Organization/hospital-main"]],
        max_length=20
    )
    
    # Emergency contacts
    contact: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Emergency contact information",
        examples=[[{
            "relationship": "spouse",
            "name": {"family": "Smith", "given": ["Jane"]},
            "telecom": [{"system": "phone", "value": "+1-555-123-4568"}]
        }]]
    )
    
    # Administrative
    active: bool = Field(
        default=True,
        description="Whether this patient record is active"
    )
    
    # AI agent context
    agent_context: dict[str, Any] = Field(
        default_factory=dict,
        description="Agent-specific context and metadata for AI workflows",
        examples=[{
            "last_interaction": "2024-08-03T12:00:00Z",
            "preferred_agent": "primary-care-assistant",
            "interaction_count": 5,
            "care_plan_status": "active"
        }]
    )
    
    def model_post_init(self, __context: Any) -> None:
        """Post-initialization processing for AI-friendly features."""
        super().model_post_init(__context)
        
        # Parse full_name into structured format if provided
        if self.full_name and not self.name:
            parsed_name = self._parse_full_name(self.full_name)
            self.name.append(parsed_name)
        
        # Ensure we have at least some name information
        if not self.name and not self.full_name:
            raise ValueError("Patient must have at least a name (full_name or structured name)")
        
        # Calculate birth_date from age if needed
        if self.age is not None and self.birth_date is None:
            current_year = date.today().year
            estimated_birth_year = current_year - self.age
            self.birth_date = date(estimated_birth_year, 1, 1)  # Estimate as Jan 1
        
        # Add convenience contact info to structured format
        if self.phone:
            phone_contact = ContactPoint(
                system="phone",
                value=self.phone,
                use="home",
                rank=1
            )
            # Check if phone already exists
            if not any(cp.system == "phone" and cp.value == self.phone for cp in self.telecom):
                self.telecom.append(phone_contact)
        
        if self.email:
            email_contact = ContactPoint(
                system="email", 
                value=self.email,
                use="home",
                rank=1
            )
            # Check if email already exists
            if not any(cp.system == "email" and cp.value == self.email for cp in self.telecom):
                self.telecom.append(email_contact)
        
        # Parse address_text if provided
        if self.address_text and not self.address:
            parsed_address = self._parse_address_text(self.address_text)
            self.address.append(parsed_address)
        
        # Add language to communication if provided
        if self.language and not self.communication:
            # Normalize common language names
            lang_map = {
                "english": "en-US",
                "spanish": "es-ES", 
                "french": "fr-FR",
                "german": "de-DE",
                "chinese": "zh-CN",
                "japanese": "ja-JP",
                "portuguese": "pt-BR",
                "italian": "it-IT",
                "russian": "ru-RU",
                "arabic": "ar-SA"
            }
            
            lang_code = lang_map.get(self.language.lower(), self.language)
            self.communication.append({
                "language": lang_code,
                "preferred": True
            })
    
    def _parse_full_name(self, full_name: str) -> HumanName:
        """Parse full name string into structured HumanName."""
        if not full_name:
            raise ValueError("Full name cannot be empty")
        
        name_parts = full_name.strip().split()
        
        # Common prefixes and suffixes
        prefixes = ["Dr.", "Dr", "Mr.", "Mr", "Ms.", "Ms", "Mrs.", "Mrs", "Prof.", "Prof"]
        suffixes = ["Jr.", "Jr", "Sr.", "Sr", "III", "II", "IV", "MD", "PhD", "RN", "NP"]
        
        parsed_prefix = []
        parsed_suffix = []
        
        # Extract prefixes
        while name_parts and any(name_parts[0].rstrip(".").lower() == p.rstrip(".").lower() for p in prefixes):
            parsed_prefix.append(name_parts.pop(0))
        
        # Extract suffixes
        while name_parts and any(name_parts[-1].rstrip(".").upper() == s.rstrip(".").upper() for s in suffixes):
            parsed_suffix.insert(0, name_parts.pop())  # Insert at beginning to maintain order
        
        if not name_parts:
            raise ValueError("Full name must contain at least one actual name part")
        
        # Remaining parts: last is family, rest are given
        family_name = name_parts[-1] if name_parts else None
        given_names = name_parts[:-1] if len(name_parts) > 1 else name_parts
        
        return HumanName(
            use="usual",
            family=family_name,
            given=given_names,
            prefix=parsed_prefix,
            suffix=parsed_suffix
        )
    
    def _parse_address_text(self, address_text: str) -> Address:
        """Parse address text into structured Address."""
        parts = [part.strip() for part in address_text.split(",")]
        
        address = Address(
            use="home",
            text=address_text
        )
        
        if len(parts) >= 1:
            address.line = [parts[0]]
        
        if len(parts) >= 2:
            address.city = parts[1]
        
        if len(parts) >= 3:
            # Try to parse "State ZIP" format
            state_zip = parts[2].strip().split()
            if state_zip:
                address.state = state_zip[0]
                if len(state_zip) > 1:
                    address.postal_code = " ".join(state_zip[1:])
        
        if len(parts) >= 4:
            address.country = parts[3]
        
        return address
    
    @computed_field
    @property
    def display_name(self) -> str:
        """Compute primary display name."""
        if self.name:
            return self.name[0].display_name
        elif self.full_name:
            # Simple parsing for display
            parts = self.full_name.split()
            if len(parts) >= 2:
                return f"{parts[0]} {parts[-1]}"
            return self.full_name
        return "Unknown Patient"
    
    @computed_field
    @property 
    def age_years(self) -> int | None:
        """Compute current age in years."""
        if self.age is not None:
            return self.age
        
        if self.birth_date is None:
            return None
        
        end_date = self.deceased_date_time if self.deceased_boolean and self.deceased_date_time else date.today()
        age = end_date.year - self.birth_date.year
        
        # Adjust if birthday hasn't occurred this year
        if end_date.month < self.birth_date.month or (
            end_date.month == self.birth_date.month and end_date.day < self.birth_date.day
        ):
            age -= 1
        
        return max(0, age)
    
    def add_identifier(self, value: str, type_code: str | None = None, 
                      use: IdentifierUse = "usual", system: str | None = None) -> None:
        """Add an identifier to the patient."""
        identifier = Identifier(
            use=use,
            type_code=type_code,
            value=value,
            system=system
        )
        self.identifier.append(identifier)
        self.update_timestamp()
    
    def get_identifier_by_type(self, type_code: str) -> Identifier | None:
        """Get identifier by type code."""
        for identifier in self.identifier:
            if identifier.type_code == type_code:
                return identifier
        return None
    
    def add_care_provider(self, provider_reference: str) -> None:
        """Add a care provider reference."""
        if provider_reference not in self.care_provider:
            self.care_provider.append(provider_reference)
            self.update_timestamp()
    
    def update_agent_context(self, key: str, value: Any) -> None:
        """Update agent-specific context."""
        self.agent_context[key] = value
        self.update_timestamp()
    
    def deactivate(self, reason: str | None = None) -> None:
        """Deactivate patient record."""
        self.active = False
        if reason:
            self.update_agent_context("deactivation_reason", reason)
        self.update_timestamp()
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        age_str = f", age {self.age_years}" if self.age_years is not None else ""
        return f"Patient('{self.display_name}'{age_str}, {self.gender or 'unknown gender'})"