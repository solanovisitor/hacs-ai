"""
Protocol Implementation Mixins for HACS

This module provides concrete implementations of the protocols defined in protocols.py
as mixins that can be added to Pydantic models to ensure protocol compliance.

These mixins bridge the gap between abstract protocols and concrete model implementations,
enabling true type-safe, protocol-based programming throughout HACS.

Usage:
    class MyResource(IdentifiableMixin, TimestampedMixin, BaseModel):
        name: str
        # Now MyResource implements Identifiable and Timestamped protocols
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, ClassVar, Type

from pydantic import BaseModel, Field


class IdentifiableMixin(BaseModel):
    """
    Mixin implementing the Identifiable protocol.

    Provides automatic ID generation with smart defaults based on the model class name.
    """

    id: str = Field(
        default_factory=lambda: None,  # Will be set in model_post_init
        description="Unique identifier for this resource. Auto-generated if not provided.",
        min_length=1,
        max_length=64,
    )

    def model_post_init(self, __context: Any) -> None:
        """Generate ID if not provided."""
        if self.id is None:
            # Generate ID based on class name and UUID
            class_name = self.__class__.__name__.lower()
            short_uuid = str(uuid.uuid4())[:8]
            self.id = f"{class_name}-{short_uuid}"
        super().model_post_init(__context)


class TimestampedMixin(BaseModel):
    """
    Mixin implementing the Timestamped protocol.

    Provides automatic timestamp management for created_at and updated_at fields.
    """

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="ISO 8601 timestamp when this resource was created",
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="ISO 8601 timestamp when this resource was last updated",
    )

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp to current time."""
        self.updated_at = datetime.now(timezone.utc)


class VersionedMixin(BaseModel):
    """
    Mixin implementing the Versioned protocol.

    Provides version tracking for resources.
    """

    version: str = Field(
        default="1.0.0",
        description="Version of the resource",
        pattern=r"^\d+\.\d+\.\d+$",
    )


class SerializableMixin(BaseModel):
    """
    Mixin implementing the Serializable protocol.

    Provides standardized serialization methods using Pydantic's built-in capabilities.
    """

    def to_dict(self) -> Dict[str, Any]:
        """Convert object to dictionary representation."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SerializableMixin':
        """Create object from dictionary representation."""
        return cls(**data)


class ValidatableMixin(BaseModel):
    """
    Mixin implementing the Validatable protocol.

    Provides validation capabilities using Pydantic's validation system.
    """

    def validate(self) -> List[str]:
        """Validate the object and return list of errors."""
        try:
            self.model_validate(self.model_dump())
            return []
        except Exception as e:
            return [str(e)]

    def is_valid(self) -> bool:
        """Check if the object is valid."""
        return len(self.validate()) == 0


class ClinicalResourceMixin(BaseModel):
    """
    Mixin implementing the ClinicalResource protocol.

    Provides fields and methods common to all clinical healthcare resources.
    """

    resource_type: str = Field(
        description="Type identifier for this resource",
        min_length=1,
        max_length=50,
    )

    status: str = Field(
        default="active",
        description="Current status of the resource",
        examples=["active", "inactive", "draft", "entered-in-error"],
    )

    def get_patient_id(self) -> Optional[str]:
        """Get the patient ID associated with this resource."""
        # Default implementation - can be overridden by subclasses
        if hasattr(self, 'patient_id'):
            return getattr(self, 'patient_id')
        elif hasattr(self, 'subject') and hasattr(self.subject, 'id'):
            return self.subject.id
        return None


class ActorCapabilityMixin(BaseModel):
    """
    Mixin implementing the ActorCapability protocol.

    Provides actor capability management for authentication and authorization.
    """

    actor_type: str = Field(
        description="Type of the actor (human, agent, system)",
        examples=["human", "agent", "system"],
    )

    capabilities: List[str] = Field(
        default_factory=list,
        description="List of capabilities this actor has",
        examples=[["read:patient", "write:observation"], ["admin:*"]],
    )

    def can_perform(self, action: str) -> bool:
        """Check if the actor can perform an action."""
        # Check for wildcard permissions
        if f"{action.split(':')[0]}:*" in self.capabilities:
            return True
        # Check for exact match
        return action in self.capabilities


class ConfigurationProviderMixin(BaseModel):
    """
    Mixin implementing the ConfigurationProvider protocol.

    Provides configuration management capabilities.
    """

    def get_config(self, key: str) -> Any:
        """Get a configuration value by key."""
        # Default implementation - looks for key as attribute
        return getattr(self, key, None)

    def set_config(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        # Default implementation - sets as attribute if field exists
        if key in self.model_fields:
            setattr(self, key, value)

    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration as a dictionary."""
        return self.model_dump()


# Composite mixins for common combinations

class CoreResourceMixin(
    IdentifiableMixin,
    TimestampedMixin,
    VersionedMixin,
    SerializableMixin,
    ValidatableMixin
):
    """
    Composite mixin implementing all core resource protocols.

    Use this for resources that need full protocol compliance.
    """
    pass


class ClinicalEntityMixin(
    CoreResourceMixin,
    ClinicalResourceMixin
):
    """
    Composite mixin for clinical entities.

    Implements Identifiable, Timestamped, Versioned, ClinicalResource protocols.
    """
    pass


class ConfigurableActorMixin(
    ActorCapabilityMixin,
    ConfigurationProviderMixin
):
    """
    Composite mixin for configurable actors.

    Implements ActorCapability and ConfigurationProvider protocols.
    """
    pass


# Export all mixins
__all__ = [
    # Individual protocol mixins
    "IdentifiableMixin",
    "TimestampedMixin",
    "VersionedMixin",
    "SerializableMixin",
    "ValidatableMixin",
    "ClinicalResourceMixin",
    "ActorCapabilityMixin",
    "ConfigurationProviderMixin",

    # Composite mixins
    "CoreResourceMixin",
    "ClinicalEntityMixin",
    "ConfigurableActorMixin",
]