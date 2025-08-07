"""
Base Abstractions Following SOLID Principles

This module defines the registry-specific abstractions that build upon
the foundational protocols from hacs-core. All persistence-related protocols
are now imported from hacs-core to ensure consistency across HACS packages.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import (
    TypeVar, Generic, List, Optional, Dict, Any,
    Protocol, runtime_checkable, Union, Awaitable
)
from dataclasses import dataclass, field

# Import core persistence protocols from hacs-core
try:
    from hacs_core.persistence_protocols import (
        EntityId, Entity, AggregateRoot, Repository, UnitOfWork
    )
except ImportError:
    # Fallback for development - import from hacs-core main module
    from hacs_core import (
        EntityId, Entity, AggregateRoot, Repository, UnitOfWork
    )

logger = logging.getLogger(__name__)

# Type variables for generic interfaces
T = TypeVar('T')
TEntity = TypeVar('TEntity', bound=Entity)
TEvent = TypeVar('TEvent', bound='DomainEvent')
TAggregate = TypeVar('TAggregate', bound=AggregateRoot)


class ValueObject(ABC):
    """
    Base class for value objects.

    SOLID Compliance:
    - S: Single responsibility - represents a value
    - L: Liskov substitution - all value objects are immutable and comparable
    """

    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __hash__(self) -> int:
        return hash(tuple(sorted(self.__dict__.items())))


@dataclass
class DomainEvent(ValueObject):
    """
    Base class for domain events in the registry.

    SOLID Compliance:
    - S: Single responsibility - represents something that happened
    - O: Open/closed - extensible for specific event types
    """

    aggregate_id: EntityId
    event_type: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_version: int = field(default=1)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.event_type:
            raise ValueError("Event type cannot be empty")


@runtime_checkable
class EventPublisher(Protocol):
    """
    Event publisher interface.

    SOLID Compliance:
    - S: Single responsibility - publishes events
    - I: Interface segregation - minimal event publishing interface
    - D: Dependency inversion - abstracts event infrastructure
    """

    async def publish(self, event: DomainEvent) -> None:
        """Publish a single domain event."""
        ...

    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """Publish multiple domain events as a batch."""
        ...


@runtime_checkable
class EventHandler(Protocol, Generic[TEvent]):
    """
    Event handler interface.

    SOLID Compliance:
    - S: Single responsibility - handles specific event types
    - I: Interface segregation - minimal handler interface
    """

    async def handle(self, event: TEvent) -> None:
        """Handle a domain event."""
        ...

    @property
    def supported_event_types(self) -> List[str]:
        """Event types this handler can process."""
        ...


@runtime_checkable
class LifecycleAware(Protocol):
    """
    Interface for components that have lifecycle management.

    SOLID Compliance:
    - I: Interface segregation - only for components that need lifecycle
    """

    async def initialize(self) -> None:
        """Initialize the component."""
        ...

    async def start(self) -> None:
        """Start the component."""
        ...

    async def stop(self) -> None:
        """Stop the component."""
        ...

    async def cleanup(self) -> None:
        """Clean up resources."""
        ...


class DomainService(ABC):
    """
    Base class for domain services.

    SOLID Compliance:
    - S: Single responsibility - encapsulates domain logic that doesn't belong to entities
    - D: Dependency inversion - depends on interfaces, not implementations
    """

    def __init__(self, event_publisher: Optional[EventPublisher] = None):
        self.event_publisher = event_publisher

    async def publish_event(self, event: DomainEvent):
        """Publish a domain event if publisher is available."""
        if self.event_publisher:
            await self.event_publisher.publish(event)


class ApplicationService(ABC):
    """
    Base class for application services.

    SOLID Compliance:
    - S: Single responsibility - orchestrates use cases
    - D: Dependency inversion - depends on domain abstractions
    """

    def __init__(self, event_publisher: Optional[EventPublisher] = None):
        self.event_publisher = event_publisher
        self.logger = logging.getLogger(self.__class__.__name__)

    async def publish_events_from_aggregate(self, aggregate: AggregateRoot):
        """Publish all pending events from an aggregate."""
        if not self.event_publisher:
            return

        events = aggregate.get_domain_events()
        if events:
            await self.event_publisher.publish_batch(events)
            aggregate.clear_domain_events()


@runtime_checkable
class QueryRepository(Protocol, Generic[T]):
    """
    Read-only repository for queries (CQRS pattern).

    SOLID Compliance:
    - S: Single responsibility - read-only data access
    - I: Interface segregation - separate from command repository
    - D: Dependency inversion - abstracts query implementation
    """

    async def find_by_id(self, entity_id: EntityId) -> Optional[T]:
        """Find an entity by its ID."""
        ...

    async def find_all(self, limit: Optional[int] = None, offset: int = 0) -> List[T]:
        """Find all entities with optional pagination."""
        ...

    async def find_by_criteria(self, criteria: Dict[str, Any]) -> List[T]:
        """Find entities matching specific criteria."""
        ...

    async def count(self, criteria: Optional[Dict[str, Any]] = None) -> int:
        """Count entities matching criteria."""
        ...


@runtime_checkable
class Specification(Protocol, Generic[T]):
    """
    Specification pattern for encapsulating business rules.

    SOLID Compliance:
    - S: Single responsibility - represents one business rule
    - O: Open/closed - combinable specifications
    - D: Dependency inversion - abstracts rule evaluation
    """

    def is_satisfied_by(self, entity: T) -> bool:
        """Check if entity satisfies the specification."""
        ...

    def and_specification(self, other: 'Specification[T]') -> 'Specification[T]':
        """Combine with another specification using AND."""
        ...

    def or_specification(self, other: 'Specification[T]') -> 'Specification[T]':
        """Combine with another specification using OR."""
        ...

    def not_specification(self) -> 'Specification[T]':
        """Negate this specification."""
        ...


# Registry-specific aggregate root that extends the base
class RegistryAggregateRoot(AggregateRoot):
    """
    Registry-specific aggregate root with additional functionality.

    SOLID Compliance:
    - S: Single responsibility - registry-specific aggregate behavior
    - L: Liskov substitution - extends base aggregate root
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._registry_metadata: Dict[str, Any] = {}

    def set_registry_metadata(self, key: str, value: Any):
        """Set registry-specific metadata."""
        self._registry_metadata[key] = value

    def get_registry_metadata(self, key: str, default: Any = None) -> Any:
        """Get registry-specific metadata."""
        return self._registry_metadata.get(key, default)


# Type aliases for better readability
RepositoryType = Repository[AggregateRoot]
QueryRepositoryType = QueryRepository[Entity]

__all__ = [
    # Re-exported from hacs-core
    "EntityId",
    "Entity",
    "AggregateRoot",
    "Repository",
    "UnitOfWork",

    # Registry-specific abstractions
    "ValueObject",
    "DomainEvent",
    "EventPublisher",
    "EventHandler",
    "LifecycleAware",
    "DomainService",
    "ApplicationService",
    "QueryRepository",
    "Specification",
    "RegistryAggregateRoot",

    # Type aliases
    "RepositoryType",
    "QueryRepositoryType",
]