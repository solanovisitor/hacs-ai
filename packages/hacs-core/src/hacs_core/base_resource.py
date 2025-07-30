"""
Base resource model for all HACS resources.

This module provides the foundational BaseResource class that all HACS models inherit from.
It includes core fields, validation, and serialization capabilities.
Optimized for LLM generation with auto-generated IDs and flexible validation.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Type

from pydantic import BaseModel, ConfigDict, Field, create_model


class BaseResource(BaseModel):
    """
    Base class for all HACS resources.

    Provides core functionality including:
    - Resource type identification
    - Unique ID management (auto-generated if not provided)
    - Timestamp tracking
    - JSON Schema generation
    - Pretty printing
    - View model creation with pick()

    LLM-Friendly Features:
    - Auto-generates IDs if not provided
    - Flexible validation
    - Smart defaults
    - Create subset views with pick()
    """

    model_config = ConfigDict(
        # Enable validation on assignment
        validate_assignment=True,
        # Use enum values in serialization
        use_enum_values=True,
        # Allow extra fields for extensibility
        extra="allow",
        # Generate JSON schema with examples
        json_schema_extra={
            "examples": [
                {
                    "id": "resource-001",
                    "resource_type": "BaseResource",
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:30:00Z",
                }
            ]
        },
    )

    # LLM-FRIENDLY: ID is now optional with auto-generation
    id: str | None = Field(
        default=None,
        description="Unique identifier for this resource - Auto-generated if not provided",
        examples=["patient-001", "obs-bp-123", "mem-episode-456"],
    )

    resource_type: str | Any = Field(
        description="Resource type identifier (Patient, Observation, etc.)",
        examples=["Patient", "Observation", "MemoryBlock"],
    )

    created_at: datetime | None = Field(
        default=None,
        description="When this resource was created - Auto-generated if not provided",
        examples=["2024-01-15T10:30:00Z"],
    )

    updated_at: datetime | None = Field(
        default=None,
        description="When this resource was last updated - Auto-generated on changes",
        examples=["2024-01-15T10:30:00Z"],
    )

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization hook to set defaults."""
        current_time = datetime.now(timezone.utc)

        # Auto-generate ID if not provided
        if self.id is None:
            self.id = f"{self.resource_type.lower()}-{str(uuid.uuid4())[:8]}"

        # Auto-set created_at if not provided
        if self.created_at is None:
            self.created_at = current_time

        # Auto-set updated_at if not provided
        if self.updated_at is None:
            self.updated_at = current_time

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp to current time."""
        self.updated_at = datetime.now(timezone.utc)

    def is_newer_than(self, other: "BaseResource") -> bool:
        """Check if this resource is newer than another resource."""
        if self.updated_at is None or other.updated_at is None:
            return False
        return self.updated_at > other.updated_at

    @classmethod
    def pick(cls, *fields: str) -> Type["BaseResource"]:
        """
        Create a subset model with only the specified fields.

        This is LLM-friendly - create lightweight models for specific use cases.
        Perfect for structured output generation where you only need certain fields.

        Args:
            *fields: Names of fields to include in the subset model

        Returns:
            New Pydantic model class with only the specified fields

        Example:
            >>> PatientSummary = Patient.pick("full_name", "age", "gender")
            >>> summary = PatientSummary(full_name="John Doe", age=45, gender="male")
        """
        # Get the original model's field definitions
        model_fields = cls.model_fields
        config = cls.model_config

        # Filter to only the requested fields (keeping id, resource_type, timestamps by default)
        essential_fields = {"id", "resource_type", "created_at", "updated_at"}
        selected_fields = set(fields) | essential_fields

        # Build the new field dict
        new_fields = {}
        for field_name in selected_fields:
            if field_name in model_fields:
                new_fields[field_name] = model_fields[field_name]

        # Create the new model class
        subset_model = create_model(
            f"{cls.__name__}Subset",
            **new_fields,
            __config__=config,
            __base__=cls,
        )

        return subset_model

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.resource_type}(id={self.id})"

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        field_strs = []
        for field_name in self.model_fields:
            value = getattr(self, field_name, None)
            if value is not None:
                # Truncate long values
                if isinstance(value, str) and len(value) > 50:
                    value = f"{value[:47]}..."
                # Shorten field names for repr
                display_name = field_name
                if field_name == "created_at":
                    display_name = "created"
                elif field_name == "updated_at":
                    display_name = "updated"
                field_strs.append(f"{display_name}={repr(value)}")

        fields_str = ", ".join(field_strs[:5])  # Show max 5 fields
        if len(field_strs) > 5:
            fields_str += "..."

        return f"{self.__class__.__name__}({fields_str})"
