"""
Base resource model for all HACS healthcare models.

This module provides the foundational BaseResource and DomainResource classes 
that all HACS models inherit from. Designed for world-class development quality
with full type safety, comprehensive validation, and AI-optimized features.

Key Features:
    - Automatic ID generation with smart defaults
    - Timestamp management (created_at, updated_at)
    - Type-safe field validation with Pydantic v2
    - JSON Schema generation with examples
    - Subset model creation with pick() method
    - FHIR-compliant base structure
    - Performance optimized for AI agent communication

Design Principles:
    - Pure data models (no business logic)
    - Immutable by design (use copy() for updates)
    - Rich type annotations for perfect IDE support
    - Comprehensive docstrings for maintainability
    - Zero external dependencies beyond Pydantic
"""

import uuid
from datetime import datetime, timezone
from typing import Any, ClassVar, Type, TypeVar

from pydantic import BaseModel, ConfigDict, Field, create_model

# Type variable for generic base resource operations
T = TypeVar('T', bound='BaseResource')


class BaseResource(BaseModel):
    """
    Foundation class for all HACS healthcare resources.

    Provides essential functionality for healthcare data models including
    automatic ID generation, timestamp management, and type-safe operations.
    
    This class follows FHIR R4/R5 base resource patterns while optimizing
    for AI agent communication and modern Python development practices.

    Features:
        - Auto-generated UUIDs if ID not provided
        - Automatic timestamp management
        - Type-safe field access and validation
        - JSON Schema generation with examples
        - Subset model creation for specific use cases
        - Performance optimized serialization

    Example:
        >>> class MyResource(BaseResource):
        ...     name: str
        ...     value: int = 0
        >>> 
        >>> resource = MyResource(resource_type="MyResource", name="test")
        >>> print(resource.id)  # Auto-generated: myresource-a1b2c3d4
        >>> print(resource.created_at)  # Auto-set to current time
    """

    # Pydantic v2 configuration for optimal performance and validation  
    model_config = ConfigDict(
        # Core validation settings
        validate_assignment=True,           # Validate on field assignment
        validate_default=True,             # Validate default values
        use_enum_values=True,              # Serialize enums as values
        
        # Performance optimizations
        extra="forbid",                    # Strict field validation (world-class quality)
        frozen=False,                      # Allow field updates for timestamps
        str_strip_whitespace=True,         # Auto-strip whitespace
        
        # Developer experience
        arbitrary_types_allowed=False,     # Strict type checking
        
        # JSON Schema generation
        json_schema_extra={
            "examples": [
                {
                    "id": "resource-a1b2c3d4",
                    "resource_type": "BaseResource", 
                    "created_at": "2024-08-03T12:00:00Z",
                    "updated_at": "2024-08-03T12:00:00Z",
                }
            ],
            "title": "Base Healthcare Resource",
            "description": "Foundation for all HACS healthcare data models",
        },
    )

    # Resource identification fields
    id: str | None = Field(
        default=None,
        description="Unique identifier for this resource. Auto-generated if not provided.",
        examples=["patient-a1b2c3d4", "observation-b2c3d4e5", "memory-c3d4e5f6"],
        min_length=1,
        max_length=64,
    )

    resource_type: str = Field(
        description="Type identifier for this resource (Patient, Observation, etc.)",
        examples=["Patient", "Observation", "MemoryBlock", "WorkflowDefinition"],
        min_length=1,
        max_length=50,
    )

    # Timestamp management  
    created_at: datetime | None = Field(
        default=None,
        description="ISO 8601 timestamp when this resource was created",
        examples=["2024-08-03T12:00:00Z", "2024-08-03T12:00:00.123456Z"],
    )

    updated_at: datetime | None = Field(
        default=None, 
        description="ISO 8601 timestamp when this resource was last updated",
        examples=["2024-08-03T12:30:00Z", "2024-08-03T12:30:00.654321Z"],
    )

    # Class-level metadata for introspection
    _hacs_version: ClassVar[str] = "0.1.0"
    _fhir_version: ClassVar[str | None] = None  # Override in FHIR resources

    def model_post_init(self, __context: Any) -> None:
        """
        Post-initialization hook for auto-generation of required fields.
        
        Called automatically after model creation to set:
        - Auto-generated ID if not provided
        - Created timestamp if not provided  
        - Updated timestamp if not provided
        
        Args:
            __context: Pydantic validation context (unused)
        """
        current_time = datetime.now(timezone.utc)

        # Generate ID with resource-type prefix for clarity
        if self.id is None:
            resource_prefix = self.resource_type.lower().replace(" ", "-")
            unique_suffix = str(uuid.uuid4())[:8]
            self.id = f"{resource_prefix}-{unique_suffix}"

        # Set creation timestamp
        if self.created_at is None:
            self.created_at = current_time

        # Set update timestamp  
        if self.updated_at is None:
            self.updated_at = current_time

    def update_timestamp(self) -> None:
        """
        Update the updated_at timestamp to current UTC time.
        
        Call this method when making modifications to track when
        the resource was last changed.
        
        Example:
            >>> resource.name = "New Name"
            >>> resource.update_timestamp()
        """
        self.updated_at = datetime.now(timezone.utc)

    def is_newer_than(self, other: "BaseResource") -> bool:
        """
        Compare timestamps to determine if this resource is newer.
        
        Args:
            other: Another BaseResource to compare against
            
        Returns:
            True if this resource was updated more recently
            
        Example:
            >>> resource1 = MyResource(resource_type="Test", name="first")
            >>> # ... time passes ...
            >>> resource2 = MyResource(resource_type="Test", name="second") 
            >>> resource2.is_newer_than(resource1)  # True
        """
        if self.updated_at is None or other.updated_at is None:
            return False
        return self.updated_at > other.updated_at

    @classmethod
    def pick(cls: Type[T], *fields: str) -> Type[T]:
        """
        Create a subset model containing only specified fields.
        
        Useful for creating lightweight models for specific use cases,
        API responses, or when you only need certain fields from a model.
        Essential fields (id, resource_type, timestamps) are always included.
        
        Args:
            *fields: Names of fields to include in the subset model
            
        Returns:
            New Pydantic model class with only the specified fields
            
        Example:
            >>> PatientSummary = Patient.pick("full_name", "birth_date", "gender")
            >>> summary = PatientSummary(
            ...     resource_type="Patient",
            ...     full_name="Jane Doe",
            ...     birth_date="1990-01-15", 
            ...     gender="female"
            ... )
            >>> # summary only has the picked fields plus essentials
        """
        # Essential fields that are always included
        essential_fields = {"id", "resource_type", "created_at", "updated_at"}
        selected_fields = set(fields) | essential_fields

        # Get field definitions from the original model
        model_fields = cls.model_fields
        config = cls.model_config

        # Build new field dictionary with only selected fields
        new_fields = {}
        for field_name in selected_fields:
            if field_name in model_fields:
                new_fields[field_name] = model_fields[field_name]

        # Create the subset model class
        subset_model = create_model(
            f"{cls.__name__}Subset",
            **new_fields,
            __config__=config,
            __base__=cls,
        )

        return subset_model  # type: ignore[return-value]

    def get_age_days(self) -> float | None:
        """
        Calculate age of this resource in days since creation.
        
        Returns:
            Number of days since created_at, or None if no creation time
            
        Example:
            >>> resource = MyResource(resource_type="Test")
            >>> # ... some time later ...
            >>> age = resource.get_age_days()  # e.g., 1.5 days
        """
        if self.created_at is None:
            return None
        
        now = datetime.now(timezone.utc)
        delta = now - self.created_at
        return delta.total_seconds() / 86400  # Convert seconds to days

    def to_reference(self) -> str:
        """
        Create a FHIR-style reference string for this resource.
        
        Returns:
            Reference string in format "ResourceType/id"
            
        Example:
            >>> patient = Patient(resource_type="Patient", full_name="John Doe")
            >>> ref = patient.to_reference()  # "Patient/patient-a1b2c3d4"
        """
        return f"{self.resource_type}/{self.id}"

    def __str__(self) -> str:
        """
        Human-readable string representation.
        
        Returns:
            Simple string showing resource type and ID
        """
        return f"{self.resource_type}(id={self.id})"

    def __repr__(self) -> str:
        """
        Developer-friendly detailed representation.
        
        Shows up to 5 most important fields with values,
        truncating long strings for readability.
        """
        field_strs = []
        
        # Always show essential fields first
        essential_order = ["id", "resource_type", "created_at", "updated_at"]
        other_fields = [f for f in self.model_fields if f not in essential_order]
        ordered_fields = essential_order + other_fields

        for field_name in ordered_fields:
            value = getattr(self, field_name, None)
            if value is not None:
                # Truncate long values for readability
                if isinstance(value, str) and len(value) > 40:
                    value = f"{value[:37]}..."
                elif isinstance(value, datetime):
                    value = value.isoformat()
                    
                # Shorten common field names
                display_name = field_name
                if field_name == "created_at":
                    display_name = "created"
                elif field_name == "updated_at":
                    display_name = "updated"
                elif field_name == "resource_type":
                    display_name = "type"
                    
                field_strs.append(f"{display_name}={repr(value)}")

        # Show max 5 fields to keep repr concise
        fields_display = ", ".join(field_strs[:5])
        if len(field_strs) > 5:
            fields_display += f", +{len(field_strs) - 5} more"

        return f"{self.__class__.__name__}({fields_display})"


class DomainResource(BaseResource):
    """
    Base class for domain-specific healthcare resources.
    
    Extends BaseResource with additional fields and functionality
    specific to FHIR domain resources (Patient, Observation, etc.).
    
    This follows FHIR's DomainResource pattern where most clinical
    resources inherit common patterns like text, contained resources,
    extensions, and modifierExtensions.
    
    Features:
        - Human-readable text representation
        - Support for contained resources  
        - Extension mechanism for additional data
        - Modifier extensions for data that changes meaning
    """

    # FHIR DomainResource fields
    text: str | None = Field(
        default=None,
        description="Human-readable summary of the resource content",
        examples=["Patient John Doe, 45 years old", "Blood pressure reading: 120/80 mmHg"],
        max_length=2048,
    )

    contained: list[BaseResource] | None = Field(
        default=None,
        description="Resources contained within this resource",
        examples=[],
    )

    # Extension support for additional data
    extension: dict[str, Any] | None = Field(
        default=None,
        description="Additional content defined by implementations",
        examples=[{"url": "custom-field", "valueString": "custom-value"}],
    )

    modifier_extension: dict[str, Any] | None = Field(
        default=None,
        description="Extensions that cannot be ignored",
        examples=[{"url": "critical-field", "valueBoolean": True}],
    )

    # Override FHIR version for domain resources
    _fhir_version: ClassVar[str] = "R4"

    def get_text_summary(self) -> str:
        """
        Get or generate a human-readable text summary.
        
        Returns the explicit text field if set, otherwise generates
        a basic summary from the resource type and ID.
        
        Returns:
            Human-readable summary string
        """
        if self.text:
            return self.text
        return f"{self.resource_type} {self.id}"

    def add_extension(self, url: str, value: Any) -> None:
        """
        Add an extension to this resource.
        
        Args:
            url: Extension URL/identifier
            value: Extension value
            
        Example:
            >>> resource.add_extension("custom-flag", True)
        """
        if self.extension is None:
            self.extension = {}
        self.extension[url] = value
        self.update_timestamp()

    def get_extension(self, url: str) -> Any | None:
        """
        Get an extension value by URL.
        
        Args:
            url: Extension URL/identifier
            
        Returns:
            Extension value or None if not found
        """
        if self.extension is None:
            return None
        return self.extension.get(url)

    def has_extension(self, url: str) -> bool:
        """
        Check if an extension exists.
        
        Args:
            url: Extension URL/identifier
            
        Returns:
            True if extension exists
        """
        return self.extension is not None and url in self.extension