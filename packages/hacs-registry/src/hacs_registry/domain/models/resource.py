"""
Resource Domain Models Following SOLID Principles

This module defines domain models for healthcare resource management,
implementing the Aggregate pattern from Domain-Driven Design.

SOLID Compliance:
- S: Single Responsibility - Each model represents one business concept
- O: Open/Closed - Extensible through inheritance and composition
- L: Liskov Substitution - All aggregates follow the same contract
- I: Interface Segregation - Focused model interfaces
- D: Dependency Inversion - Models depend on abstractions

Domain Patterns:
    🏗️ Aggregate Root - ResourceAggregate manages consistency
    💎 Value Objects - ResourceMetadata, ResourceVersion, ResourceTag
    📏 Specifications - Business rules for resource validation
    📢 Domain Events - Resource lifecycle notifications
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from hacs_core import BaseResource

from ...core.base import EntityId, AggregateRoot, ValueObject
from ...core.events import ResourceEvent
from ...core.exceptions import ResourceException, ValidationException


class ResourceStatus(str, Enum):
    """Status values for resources in their lifecycle."""
    DRAFT = "draft"
    REVIEW = "review" 
    APPROVED = "approved"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    RETIRED = "retired"
    SUSPENDED = "suspended"


class ResourceCategory(str, Enum):
    """Categories for organizing resources."""
    CLINICAL = "clinical"
    WORKFLOW = "workflow"
    ADMINISTRATIVE = "administrative"
    COMMUNICATION = "communication"
    EVIDENCE = "evidence"
    MEMORY = "memory"
    CUSTOM = "custom"


@dataclass(frozen=True)
class ResourceVersion(ValueObject):
    """
    Value object representing a semantic version.
    
    SOLID Compliance:
    - S: Single responsibility - represents version information
    - L: Liskov substitution - all versions behave consistently
    """
    
    major: int
    minor: int
    patch: int
    pre_release: Optional[str] = None
    
    def __post_init__(self):
        if self.major < 0 or self.minor < 0 or self.patch < 0:
            raise ValueError("Version numbers must be non-negative")
    
    @classmethod
    def parse(cls, version_string: str) -> 'ResourceVersion':
        """Parse a version string like '1.2.3' or '1.2.3-alpha'."""
        if not version_string:
            raise ValueError("Version string cannot be empty")
        
        # Split pre-release if present
        if '-' in version_string:
            version_part, pre_release = version_string.split('-', 1)
        else:
            version_part, pre_release = version_string, None
        
        # Parse major.minor.patch
        parts = version_part.split('.')
        if len(parts) != 3:
            raise ValueError("Version must be in format 'major.minor.patch'")
        
        try:
            major, minor, patch = map(int, parts)
        except ValueError:
            raise ValueError("Version parts must be integers")
        
        return cls(major, minor, patch, pre_release)
    
    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self.pre_release:
            return f"{base}-{self.pre_release}"
        return base
    
    def is_compatible_with(self, other: 'ResourceVersion') -> bool:
        """Check if this version is compatible with another version."""
        # Same major version is compatible
        return self.major == other.major
    
    def is_newer_than(self, other: 'ResourceVersion') -> bool:
        """Check if this version is newer than another version."""
        if self.major != other.major:
            return self.major > other.major
        if self.minor != other.minor:
            return self.minor > other.minor
        if self.patch != other.patch:
            return self.patch > other.patch
        
        # Handle pre-release versions
        if self.pre_release is None and other.pre_release is not None:
            return True  # Release is newer than pre-release
        if self.pre_release is not None and other.pre_release is None:
            return False  # Pre-release is older than release
        
        return False  # Same version


@dataclass(frozen=True)
class ResourceTag(ValueObject):
    """
    Value object representing a resource tag.
    
    SOLID Compliance:
    - S: Single responsibility - represents tag information
    """
    
    name: str
    category: Optional[str] = None
    
    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("Tag name cannot be empty")
        
        # Normalize tag name
        object.__setattr__(self, 'name', self.name.strip().lower())


@dataclass(frozen=True)
class ResourceMetadata(ValueObject):
    """
    Value object containing resource metadata.
    
    SOLID Compliance:
    - S: Single responsibility - encapsulates resource metadata
    - I: Interface segregation - focused metadata interface
    """
    
    name: str
    version: ResourceVersion
    description: str
    category: ResourceCategory
    tags: Set[ResourceTag] = field(default_factory=set)
    author: Optional[str] = None
    organization: Optional[str] = None
    license: Optional[str] = None
    documentation_url: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("Resource name cannot be empty")
        if not self.description or not self.description.strip():
            raise ValueError("Resource description cannot be empty")
        
        # Ensure tags is a set
        if not isinstance(self.tags, set):
            object.__setattr__(self, 'tags', set(self.tags))
    
    def add_tag(self, tag: ResourceTag) -> 'ResourceMetadata':
        """Create a new metadata instance with an additional tag."""
        new_tags = self.tags.copy()
        new_tags.add(tag)
        return dataclass.replace(self, tags=new_tags)
    
    def remove_tag(self, tag: ResourceTag) -> 'ResourceMetadata':
        """Create a new metadata instance with a tag removed."""
        new_tags = self.tags.copy()
        new_tags.discard(tag)
        return dataclass.replace(self, tags=new_tags)
    
    def update_version(self, new_version: ResourceVersion) -> 'ResourceMetadata':
        """Create a new metadata instance with updated version."""
        return dataclass.replace(self, version=new_version)


class ResourceRegisteredEvent(ResourceEvent):
    """Event fired when a resource is registered."""
    
    @property
    def event_type(self) -> str:
        return "resource.registered"


class ResourceUpdatedEvent(ResourceEvent):
    """Event fired when a resource is updated."""
    
    def __init__(self, resource_id: EntityId, resource_type: str, changes: Dict[str, Any], **kwargs):
        super().__init__(resource_id, resource_type, **kwargs)
        self.changes = changes
    
    @property
    def event_type(self) -> str:
        return "resource.updated"


class ResourceStatusChangedEvent(ResourceEvent):
    """Event fired when resource status changes."""
    
    def __init__(self, resource_id: EntityId, resource_type: str, old_status: ResourceStatus, new_status: ResourceStatus, **kwargs):
        super().__init__(resource_id, resource_type, **kwargs)
        self.old_status = old_status
        self.new_status = new_status
    
    @property
    def event_type(self) -> str:
        return "resource.status.changed"


class ResourceAggregate(AggregateRoot):
    """
    Aggregate root for healthcare resources.
    
    SOLID Compliance:
    - S: Single responsibility - manages resource lifecycle and consistency
    - O: Open/closed - extensible for new resource types
    - L: Liskov substitution - implements AggregateRoot contract
    - D: Dependency inversion - depends on abstractions
    
    This aggregate wraps HACS core resources with registry functionality,
    providing versioning, metadata, and lifecycle management.
    """
    
    def __init__(
        self,
        id: EntityId,
        metadata: ResourceMetadata,
        hacs_resource_class: str,
        instance_data: Optional[Dict[str, Any]] = None,
        status: ResourceStatus = ResourceStatus.DRAFT
    ):
        super().__init__(id=id)
        self._metadata = metadata
        self._hacs_resource_class = hacs_resource_class
        self._instance_data = instance_data or {}
        self._status = status
        self._validation_errors: List[str] = []
        
        # Publish registration event
        self.add_domain_event(ResourceRegisteredEvent(
            resource_id=self.id,
            resource_type=hacs_resource_class,
            resource_version=str(metadata.version)
        ))
    
    @property
    def aggregate_type(self) -> str:
        return "Resource"
    
    @property
    def metadata(self) -> ResourceMetadata:
        """Get resource metadata."""
        return self._metadata
    
    @property
    def hacs_resource_class(self) -> str:
        """Get the HACS resource class name."""
        return self._hacs_resource_class
    
    @property
    def instance_data(self) -> Dict[str, Any]:
        """Get the resource instance data."""
        return self._instance_data.copy()
    
    @property
    def status(self) -> ResourceStatus:
        """Get current resource status."""
        return self._status
    
    @property
    def validation_errors(self) -> List[str]:
        """Get current validation errors."""
        return self._validation_errors.copy()
    
    def update_metadata(self, new_metadata: ResourceMetadata) -> None:
        """Update resource metadata."""
        if new_metadata.name != self._metadata.name:
            raise ResourceException("Cannot change resource name after creation")
        
        old_metadata = self._metadata
        self._metadata = new_metadata
        self.update_timestamp()
        
        # Publish update event
        changes = {
            "old_version": str(old_metadata.version),
            "new_version": str(new_metadata.version),
            "description_changed": old_metadata.description != new_metadata.description,
            "tags_changed": old_metadata.tags != new_metadata.tags
        }
        
        self.add_domain_event(ResourceUpdatedEvent(
            resource_id=self.id,
            resource_type=self._hacs_resource_class,
            changes=changes
        ))
    
    def update_instance_data(self, new_data: Dict[str, Any]) -> None:
        """Update resource instance data."""
        old_data = self._instance_data.copy()
        self._instance_data = new_data.copy()
        self.update_timestamp()
        
        # Publish update event
        self.add_domain_event(ResourceUpdatedEvent(
            resource_id=self.id,
            resource_type=self._hacs_resource_class,
            changes={"instance_data_updated": True}
        ))
    
    def change_status(self, new_status: ResourceStatus, reason: Optional[str] = None) -> None:
        """Change resource status."""
        if new_status == self._status:
            return  # No change needed
        
        # Validate status transition (simplified - in practice would use lifecycle manager)
        if not self._is_valid_status_transition(self._status, new_status):
            raise ResourceException(f"Invalid status transition from {self._status} to {new_status}")
        
        old_status = self._status
        self._status = new_status
        self.update_timestamp()
        
        # Publish status change event
        self.add_domain_event(ResourceStatusChangedEvent(
            resource_id=self.id,
            resource_type=self._hacs_resource_class,
            old_status=old_status,
            new_status=new_status,
            reason=reason
        ))
    
    def add_validation_error(self, error: str) -> None:
        """Add a validation error."""
        if error not in self._validation_errors:
            self._validation_errors.append(error)
    
    def clear_validation_errors(self) -> None:
        """Clear all validation errors."""
        self._validation_errors.clear()
    
    def is_valid(self) -> bool:
        """Check if the resource is currently valid."""
        return len(self._validation_errors) == 0
    
    def can_be_published(self) -> bool:
        """Check if the resource can be published."""
        return (
            self.is_valid() and 
            self._status in [ResourceStatus.APPROVED] and
            self._metadata.version.major > 0
        )
    
    def get_hacs_resource_instance(self) -> Optional[BaseResource]:
        """Get an instance of the wrapped HACS resource."""
        try:
            # This would normally use a factory to create the actual HACS resource
            # For now, return None as we don't have the full factory implementation
            return None
        except Exception as e:
            self.add_validation_error(f"Failed to instantiate HACS resource: {e}")
            return None
    
    def _is_valid_status_transition(self, from_status: ResourceStatus, to_status: ResourceStatus) -> bool:
        """Check if a status transition is valid."""
        # Simplified transition rules - in practice would be more complex
        valid_transitions = {
            ResourceStatus.DRAFT: [ResourceStatus.REVIEW, ResourceStatus.SUSPENDED],
            ResourceStatus.REVIEW: [ResourceStatus.APPROVED, ResourceStatus.DRAFT],
            ResourceStatus.APPROVED: [ResourceStatus.PUBLISHED, ResourceStatus.REVIEW],
            ResourceStatus.PUBLISHED: [ResourceStatus.DEPRECATED, ResourceStatus.SUSPENDED],
            ResourceStatus.DEPRECATED: [ResourceStatus.RETIRED],
            ResourceStatus.SUSPENDED: [ResourceStatus.DRAFT, ResourceStatus.REVIEW, ResourceStatus.PUBLISHED],
            ResourceStatus.RETIRED: []  # No transitions from retired
        }
        
        return to_status in valid_transitions.get(from_status, [])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert aggregate to dictionary representation."""
        return {
            "id": self.id.value,
            "metadata": {
                "name": self._metadata.name,
                "version": str(self._metadata.version),
                "description": self._metadata.description,
                "category": self._metadata.category.value,
                "tags": [{"name": tag.name, "category": tag.category} for tag in self._metadata.tags],
                "author": self._metadata.author,
                "organization": self._metadata.organization,
                "license": self._metadata.license,
                "documentation_url": self._metadata.documentation_url,
                "created_at": self._metadata.created_at.isoformat()
            },
            "hacs_resource_class": self._hacs_resource_class,
            "instance_data": self._instance_data,
            "status": self._status.value,
            "validation_errors": self._validation_errors,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version
        }