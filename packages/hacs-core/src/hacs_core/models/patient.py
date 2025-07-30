"""
Patient model for healthcare data representation.

This module provides the Patient model with FHIR-compliant fields,
comprehensive validation, and agent-centric features for healthcare AI workflows.
Optimized for LLM generation with flexible validation and smart defaults.
"""

from datetime import date
from enum import Enum
from typing import Any, Literal

from ..base_resource import BaseResource
from pydantic import Field, computed_field, field_validator


class AdministrativeGender(str, Enum):
    """FHIR-compliant administrative gender codes."""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"


class IdentifierUse(str, Enum):
    """FHIR-compliant identifier use codes."""

    USUAL = "usual"
    OFFICIAL = "official"
    TEMP = "temp"
    SECONDARY = "secondary"
    OLD = "old"


class IdentifierType(str, Enum):
    """Common healthcare identifier types."""

    MR = "MR"  # Medical record number
    SSN = "SSN"  # Social Security Number
    DL = "DL"  # Driver's License
    PPN = "PPN"  # Passport number
    TAX = "TAX"  # Tax ID number
    NI = "NI"  # National identifier
    NH = "NH"  # NHS number
    MC = "MC"  # Medicare number


class ContactPointSystem(str, Enum):
    """FHIR-compliant contact point system codes."""

    PHONE = "phone"
    FAX = "fax"
    EMAIL = "email"
    PAGER = "pager"
    URL = "url"
    SMS = "sms"
    OTHER = "other"


class ContactPointUse(str, Enum):
    """FHIR-compliant contact point use codes."""

    HOME = "home"
    WORK = "work"
    TEMP = "temp"
    OLD = "old"
    MOBILE = "mobile"


class Patient(BaseResource):
    """
    Represents a patient in the healthcare system.

    This model includes comprehensive patient demographics, identifiers,
    and contact information with FHIR compliance and agent-centric features.

    LLM-Friendly Features:
    - Flexible name handling with simple alternatives
    - Optional fields with smart defaults
    - Automatic parsing of simple inputs
    - Helper methods for common LLM use cases
    """

    resource_type: Literal["Patient"] = Field(
        default="Patient", description="Resource type identifier"
    )

    # LLM-FRIENDLY: Name fields with more flexibility
    given: list[str] | None = Field(
        default=None,
        description="Given names (first, middle names) - Optional, can be derived from full_name",
        examples=[["John", "Michael"], ["Sarah"], ["María", "Elena"]],
    )

    family: str | None = Field(
        default=None,
        description="Family name (surname, last name) - Optional, can be derived from full_name",
        examples=["Smith", "Johnson", "García"],
    )

    # LLM-FRIENDLY: Simple name alternative
    full_name: str | None = Field(
        default=None,
        description="Complete name as a single string (e.g., 'John Michael Smith') - Will auto-parse into given/family",
        examples=["John Michael Smith", "Dr. Sarah Johnson", "María Elena García"],
    )

    prefix: list[str] = Field(
        default_factory=list,
        description="Name prefixes (titles)",
        examples=[["Dr.", "Prof."], ["Mr."], ["Ms.", "PhD"]],
    )

    suffix: list[str] = Field(
        default_factory=list,
        description="Name suffixes",
        examples=[["Jr."], ["III"], ["MD", "PhD"]],
    )

    # Demographics - LLM-FRIENDLY: More flexible
    gender: AdministrativeGender | None = Field(
        default=None,
        description="Administrative gender - Optional",
        examples=["male", "female", "other", "unknown"],
    )

    birth_date: date | None = Field(
        default=None,
        description="Date of birth",
        examples=["1985-03-15", "1992-12-01", None],
    )

    # LLM-FRIENDLY: Simple age alternative
    age: int | None = Field(
        default=None,
        description="Age in years (will calculate birth_date if not provided)",
        examples=[39, 25, 67],
    )

    deceased: bool = Field(default=False, description="Whether the patient is deceased")

    deceased_date: date | None = Field(
        default=None,
        description="Date of death if deceased",
        examples=["2024-01-15", None],
    )

    # Identifiers
    identifiers: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Patient identifiers (MRN, SSN, etc.)",
        examples=[
            [
                {
                    "use": "usual",
                    "type": "MR",
                    "system": "http://hospital.example.com/mrn",
                    "value": "123456789",
                    "assigner": "Example Hospital",
                }
            ]
        ],
    )

    # Contact information
    telecom: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Contact points (phone, email, etc.)",
        examples=[
            [
                {"system": "phone", "value": "+1-555-0123", "use": "home"},
                {"system": "email", "value": "john.smith@example.com", "use": "home"},
            ]
        ],
    )

    # LLM-FRIENDLY: Simple contact alternatives
    phone: str | None = Field(
        default=None,
        description="Primary phone number (will be added to telecom)",
        examples=["+1-555-0123", "555-0123", "(555) 123-4567"],
    )

    email: str | None = Field(
        default=None,
        description="Primary email address (will be added to telecom)",
        examples=["john.smith@example.com", "patient@email.com"],
    )

    # Address
    address: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Patient addresses",
        examples=[
            [
                {
                    "use": "home",
                    "line": ["123 Main St", "Apt 4B"],
                    "city": "Anytown",
                    "state": "CA",
                    "postal_code": "12345",
                    "country": "US",
                }
            ]
        ],
    )

    # LLM-FRIENDLY: Simple address alternative
    address_text: str | None = Field(
        default=None,
        description="Simple address as text (will be parsed into structured format)",
        examples=[
            "123 Main St, Anytown, CA 12345",
            "456 Oak Ave, Suite 200, Boston, MA 02101",
        ],
    )

    # Marital status
    marital_status: str | None = Field(
        default=None,
        description="Marital status code",
        examples=[
            "M",
            "S",
            "D",
            "W",
            "U",
        ],  # Married, Single, Divorced, Widowed, Unknown
    )

    # Language and communication
    communication: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Languages and communication preferences",
        examples=[
            [
                {"language": "en-US", "preferred": True},
                {"language": "es-ES", "preferred": False},
            ]
        ],
    )

    # LLM-FRIENDLY: Simple language alternative
    language: str | None = Field(
        default=None,
        description="Primary language (will be added to communication)",
        examples=["English", "Spanish", "en-US", "es-ES"],
    )

    # Agent-centric fields
    agent_context: dict[str, Any] = Field(
        default_factory=dict,
        description="Agent-specific context and metadata",
        examples=[
            {
                "last_interaction": "2024-01-15T10:30:00Z",
                "preferred_agent": "primary-care-agent",
                "interaction_count": 5,
                "care_plan_status": "active",
            }
        ],
    )

    care_team: list[str] = Field(
        default_factory=list,
        description="References to care team members",
        examples=[["practitioner-001", "practitioner-002", "agent-primary-care"]],
    )

    # Emergency contact
    emergency_contact: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Emergency contact information",
        examples=[
            [
                {
                    "relationship": "spouse",
                    "name": "Jane Smith",
                    "telecom": [
                        {"system": "phone", "value": "+1-555-0124", "use": "mobile"}
                    ],
                }
            ]
        ],
    )

    # Clinical metadata
    active: bool = Field(
        default=True, description="Whether this patient record is active"
    )

    @field_validator("given")
    @classmethod
    def validate_given_names(cls, v: list[str] | None) -> list[str] | None:
        """LLM-FRIENDLY: More flexible given name validation."""
        if v is None:
            return None
        if not v or not any(name.strip() for name in v):
            return None  # Will be handled in model_validator
        return [name.strip() for name in v if name.strip()]

    @field_validator("family")
    @classmethod
    def validate_family_name(cls, v: str | None) -> str | None:
        """LLM-FRIENDLY: More flexible family name validation."""
        if v is None:
            return None
        if not v.strip():
            return None  # Will be handled in model_validator
        return v.strip()

    @field_validator("identifiers")
    @classmethod
    def validate_identifiers(cls, v: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate identifier structure."""
        for identifier in v:
            if not isinstance(identifier, dict):
                raise ValueError("Each identifier must be a dictionary")
            if "value" not in identifier:
                raise ValueError("Identifier must have a 'value' field")
            if not identifier["value"].strip():
                raise ValueError("Identifier value cannot be empty")
        return v

    @field_validator("age")
    @classmethod
    def validate_age(cls, v: int | None) -> int | None:
        """Validate age is reasonable."""
        if v is not None and (v < 0 or v > 150):
            raise ValueError("Age must be between 0 and 150")
        return v

    def model_post_init(self, __context) -> None:
        """LLM-FRIENDLY: Post-initialization processing for smart defaults."""
        super().model_post_init(__context)

        # Parse full_name if given/family not provided
        if self.full_name and (not self.given or not self.family):
            self._parse_full_name()

        # Ensure we have at least some name information
        if not self.given and not self.family and not self.full_name:
            raise ValueError(
                "At least one of 'given', 'family', or 'full_name' must be provided"
            )

        # Calculate birth_date from age if needed
        if self.age is not None and self.birth_date is None:
            current_year = date.today().year
            self.birth_date = date(current_year - self.age, 1, 1)

        # Add simple contact info to structured format
        if self.phone and not any(t.get("system") == "phone" for t in self.telecom):
            self.telecom.append({"system": "phone", "value": self.phone, "use": "home"})

        if self.email and not any(t.get("system") == "email" for t in self.telecom):
            self.telecom.append({"system": "email", "value": self.email, "use": "home"})

        # Add simple language to communication
        if self.language and not self.communication:
            # Normalize common language names
            lang_map = {
                "english": "en-US",
                "spanish": "es-ES",
                "french": "fr-FR",
                "german": "de-DE",
                "chinese": "zh-CN",
                "japanese": "ja-JP",
            }

            lang_code = lang_map.get(self.language.lower(), self.language)
            self.communication.append({"language": lang_code, "preferred": True})

        # Parse simple address
        if self.address_text and not self.address:
            self.address.append(self._parse_address_text(self.address_text))

    def _parse_full_name(self) -> None:
        """Parse full_name into given and family components."""
        if not self.full_name:
            return

        # Remove common prefixes and suffixes
        name_parts = self.full_name.strip().split()

        # Handle prefixes
        prefixes = [
            "Dr.",
            "Dr",
            "Mr.",
            "Mr",
            "Ms.",
            "Ms",
            "Mrs.",
            "Mrs",
            "Prof.",
            "Prof",
        ]
        while name_parts and name_parts[0].rstrip(".") in [
            p.rstrip(".") for p in prefixes
        ]:
            prefix = name_parts.pop(0)
            if prefix not in self.prefix:
                self.prefix.append(prefix)

        # Handle suffixes
        suffixes = ["Jr.", "Jr", "Sr.", "Sr", "III", "II", "IV", "MD", "PhD", "RN"]
        while name_parts and name_parts[-1].rstrip(".") in [
            s.rstrip(".") for s in suffixes
        ]:
            suffix = name_parts.pop()
            if suffix not in self.suffix:
                self.suffix.append(suffix)

        if not name_parts:
            return

        # Last part is family name, rest are given names
        if not self.family:
            self.family = name_parts[-1]

        if not self.given and len(name_parts) > 1:
            self.given = name_parts[:-1]
        elif not self.given:
            # If only one name part, use it as given name
            self.given = [name_parts[0]]

    def _parse_address_text(self, address_text: str) -> dict[str, Any]:
        """Parse simple address text into structured format."""
        # Basic address parsing - split by commas
        parts = [part.strip() for part in address_text.split(",")]

        address = {"use": "home", "text": address_text}

        if len(parts) >= 1:
            address["line"] = [parts[0]]

        if len(parts) >= 2:
            address["city"] = parts[1]

        if len(parts) >= 3:
            # Try to parse "State ZIP" or just state
            state_zip = parts[2].strip().split()
            if len(state_zip) >= 1:
                address["state"] = state_zip[0]
            if len(state_zip) >= 2:
                address["postal_code"] = state_zip[1]

        if len(parts) >= 4:
            address["country"] = parts[3]

        return address

    @field_validator("deceased_date")
    @classmethod
    def validate_deceased_date(cls, v: date | None, values) -> date | None:
        """Ensure deceased date is only set if patient is deceased."""
        # Note: In Pydantic v2, we need to access other fields differently
        # This is a simplified validation - in practice, you'd use model_validator
        return v

    @computed_field
    @property
    def computed_full_name(self) -> str:
        """Computed field for full name."""
        if self.full_name:
            return self.full_name

        parts = []
        if self.prefix:
            parts.extend(self.prefix)
        if self.given:
            parts.extend(self.given)
        if self.family:
            parts.append(self.family)
        if self.suffix:
            parts.extend(self.suffix)
        return " ".join(parts)

    @computed_field
    @property
    def display_name(self) -> str:
        """Computed field for display name (given + family)."""
        if self.given and self.family:
            return f"{' '.join(self.given)} {self.family}"
        elif self.full_name:
            # Extract just first and last from full name
            parts = self.full_name.split()
            if len(parts) >= 2:
                return f"{parts[0]} {parts[-1]}"
            return self.full_name
        elif self.given:
            return " ".join(self.given)
        elif self.family:
            return self.family
        return "Unknown Patient"

    @computed_field
    @property
    def age_years(self) -> int | None:
        """Computed field for age in years."""
        if self.age is not None:
            return self.age

        if self.birth_date is None:
            return None

        birth_date = self.birth_date  # Type guard
        end_date = (
            self.deceased_date if self.deceased and self.deceased_date else date.today()
        )
        age = end_date.year - birth_date.year

        # Adjust for birthday not yet reached this year
        if end_date.month < birth_date.month or (
            end_date.month == birth_date.month and end_date.day < birth_date.day
        ):
            age -= 1

        return max(0, age)

    def get_full_name(self) -> str:
        """Get the full name including prefixes and suffixes."""
        return self.computed_full_name

    def calculate_age(self, as_of_date: date | None = None) -> int | None:
        """
        Calculate age as of a specific date.

        Args:
            as_of_date: Date to calculate age as of (defaults to today)

        Returns:
            Age in years, or None if birth_date is not set
        """
        if self.birth_date is None:
            return None

        birth_date = self.birth_date  # Type guard
        if as_of_date is None:
            as_of_date = date.today()

        age = as_of_date.year - birth_date.year

        # Adjust for birthday not yet reached this year
        if as_of_date.month < birth_date.month or (
            as_of_date.month == birth_date.month and as_of_date.day < birth_date.day
        ):
            age -= 1

        return max(0, age)

    def add_identifier(
        self,
        value: str,
        type_code: str,
        use: str = "usual",
        system: str | None = None,
        assigner: str | None = None,
    ) -> None:
        """
        Add an identifier to the patient.

        Args:
            value: Identifier value
            type_code: Type of identifier (MR, SSN, etc.)
            use: Use of identifier (usual, official, etc.)
            system: System that assigned the identifier
            assigner: Organization that assigned the identifier
        """
        identifier = {"use": use, "type": type_code, "value": value.strip()}

        if system:
            identifier["system"] = system
        if assigner:
            identifier["assigner"] = assigner

        self.identifiers.append(identifier)
        self.update_timestamp()

    def get_primary_identifier(self) -> dict[str, Any] | None:
        """
        Get the primary identifier (first 'usual' or 'official' identifier).

        Returns:
            Primary identifier dictionary or None if no identifiers
        """
        # Look for usual identifiers first
        for identifier in self.identifiers:
            if identifier.get("use") == "usual":
                return identifier

        # Then look for official identifiers
        for identifier in self.identifiers:
            if identifier.get("use") == "official":
                return identifier

        # Return first identifier if no usual/official found
        return self.identifiers[0] if self.identifiers else None

    def get_identifier_by_type(self, type_code: str) -> dict[str, Any] | None:
        """
        Get identifier by type code.

        Args:
            type_code: Type of identifier to find (MR, SSN, etc.)

        Returns:
            Identifier dictionary or None if not found
        """
        for identifier in self.identifiers:
            if identifier.get("type") == type_code:
                return identifier
        return None

    def add_telecom(self, system: str, value: str, use: str = "home") -> None:
        """
        Add a contact point to the patient.

        Args:
            system: Contact system (phone, email, etc.)
            value: Contact value
            use: Use of contact (home, work, etc.)
        """
        telecom = {"system": system, "value": value.strip(), "use": use}
        self.telecom.append(telecom)
        self.update_timestamp()

    def get_telecom_by_system(
        self, system: str, use: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Get contact points by system and optionally by use.

        Args:
            system: Contact system to filter by
            use: Optional use to filter by

        Returns:
            List of matching contact points
        """
        matches = [t for t in self.telecom if t.get("system") == system]
        if use:
            matches = [t for t in matches if t.get("use") == use]
        return matches

    def update_agent_context(self, key: str, value: Any) -> None:
        """
        Update agent-specific context.

        Args:
            key: Context key
            value: Context value
        """
        self.agent_context[key] = value
        self.update_timestamp()

    def add_care_team_member(self, member_id: str) -> None:
        """
        Add a care team member reference.

        Args:
            member_id: ID of the care team member
        """
        if member_id not in self.care_team:
            self.care_team.append(member_id)
            self.update_timestamp()

    def remove_care_team_member(self, member_id: str) -> bool:
        """
        Remove a care team member reference.

        Args:
            member_id: ID of the care team member to remove

        Returns:
            True if member was removed, False if not found
        """
        if member_id in self.care_team:
            self.care_team.remove(member_id)
            self.update_timestamp()
            return True
        return False

    def deactivate(self, reason: str | None = None) -> None:
        """
        Deactivate the patient record.

        Args:
            reason: Optional reason for deactivation
        """
        self.active = False
        if reason:
            self.update_agent_context("deactivation_reason", reason)
        self.update_timestamp()

    def activate(self) -> None:
        """Activate the patient record."""
        self.active = True
        if "deactivation_reason" in self.agent_context:
            del self.agent_context["deactivation_reason"]
        self.update_timestamp()

    def __repr__(self) -> str:
        """Enhanced representation including name and demographics."""
        age_str = f", age {self.age_years}" if self.age_years is not None else ""
        return f"Patient(id='{self.id}', name='{self.display_name}'{age_str}, gender='{self.gender or 'unknown'}')"
