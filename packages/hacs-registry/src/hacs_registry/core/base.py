"""
Base Abstractions Following SOLID Principles

This module defines the fundamental abstractions that form the foundation 
of the HACS Registry architecture. Each interface follows the Interface 
Segregation Principle with focused, single-purpose contracts.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import (
    TypeVar, Generic, List, Optional, Dict, Any, 
    Protocol, runtime_checkable, Union, Awaitable
)
from dataclasses import dataclass, field
from uuid import uuid4

logger = logging.getLogger(__name__)

# Type variables for generic interfaces
T = TypeVar('T')
TEntity = TypeVar('TEntity', bound='Entity')
TEvent = TypeVar('TEvent', bound='DomainEvent')
TAggregate = TypeVar('TAggregate', bound='AggregateRoot')


@dataclass(frozen=True)
class EntityId:
    """Value object for entity identifiers."""
    value: str
    
    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Entity ID cannot be empty")
    
    @classmethod
    def generate(cls) -> 'EntityId':
        """Generate a new unique entity ID."""
        return cls(str(uuid4()))
    
    def __str__(self) -> str:
        return self.value


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
class Entity(ABC):
    """
    Base class for entities with identity.
    
    SOLID Compliance:
    - S: Single responsibility - provides identity and equality
    - O: Open/closed - extensible through inheritance
    - L: Liskov substitution - all entities have consistent identity behavior
    """
    
    id: EntityId
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = field(default=1)
    
    def __post_init__(self):
        if not isinstance(self.id, EntityId):
            # Auto-convert string IDs to EntityId
            if isinstance(self.id, str):
                object.__setattr__(self, 'id', EntityId(self.id))
            else:
                raise ValueError("Entity ID must be EntityId instance or string")
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Entity):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
    
    def update_timestamp(self):
        """Update the last modified timestamp."""
        object.__setattr__(self, 'updated_at', datetime.now(timezone.utc))
        object.__setattr__(self, 'version', self.version + 1)


class DomainEvent(ABC):
    """
    Base class for domain events.
    
    SOLID Compliance:
    - S: Single responsibility - represents something that happened in the domain
    - I: Interface segregation - minimal interface for events
    """
    
    def __init__(self, aggregate_id: EntityId, event_version: int = 1):
        self.event_id = EntityId.generate()
        self.aggregate_id = aggregate_id
        self.event_version = event_version
        self.occurred_at = datetime.now(timezone.utc)
        self.metadata: Dict[str, Any] = {}
    
    @property
    @abstractmethod
    def event_type(self) -> str:
        """Unique identifier for the event type."""
        pass
    
    @property
    @abstractmethod
    def aggregate_type(self) -> str:
        """Type of aggregate that produced this event."""
        pass
    
    def add_metadata(self, key: str, value: Any) -> 'DomainEvent':
        """Add metadata to the event."""
        self.metadata[key] = value
        return self


class AggregateRoot(Entity):
    """
    Base class for aggregate roots in DDD.
    
    SOLID Compliance:
    - S: Single responsibility - maintains consistency and publishes events
    - O: Open/closed - extensible for domain-specific aggregates
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._domain_events: List[DomainEvent] = []
    
    def add_domain_event(self, event: DomainEvent):
        """Add a domain event to be published."""
        self._domain_events.append(event)
        logger.debug(f"Domain event added: {event.event_type} for {self.id}")
    
    def get_domain_events(self) -> List[DomainEvent]:
        """Get all pending domain events."""
        return self._domain_events.copy()
    
    def clear_domain_events(self):
        """Clear all pending domain events."""
        self._domain_events.clear()
    
    @property
    @abstractmethod
    def aggregate_type(self) -> str:
        """Type identifier for this aggregate."""
        pass


# SOLID Principle: Interface Segregation - Small, focused interfaces

@runtime_checkable
class Repository(Protocol, Generic[TAggregate]):
    """
    Repository interface for aggregate persistence.
    
    SOLID Compliance:
    - I: Interface segregation - focused on persistence operations only
    - D: Dependency inversion - abstracts data access details
    """
    
    async def save(self, aggregate: TAggregate) -> TAggregate:
        """Save an aggregate and return the saved instance."""
        ...
    
    async def find_by_id(self, aggregate_id: EntityId) -> Optional[TAggregate]:
        """Find an aggregate by its ID."""
        ...
    
    async def exists(self, aggregate_id: EntityId) -> bool:
        """Check if an aggregate exists."""
        ...
    
    async def delete(self, aggregate_id: EntityId) -> bool:
        """Delete an aggregate by ID. Returns True if deleted."""
        ...


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
            self.logger.debug(f"Published {len(events)} events from {aggregate.aggregate_type}:{aggregate.id}")


# SOLID Principle: Single Responsibility - Specialized query interfaces

@runtime_checkable
class QueryRepository(Protocol, Generic[T]):
    """
    Read-only repository for queries (CQRS pattern).
    
    SOLID Compliance:
    - S: Single responsibility - read operations only
    - I: Interface segregation - separate from write operations
    """
    
    async def find_all(self, limit: Optional[int] = None, offset: int = 0) -> List[T]:
        """Find all entities with optional pagination."""
        ...
    
    async def find_by_criteria(self, criteria: Dict[str, Any]) -> List[T]:
        """Find entities matching the given criteria."""
        ...
    
    async def count(self, criteria: Optional[Dict[str, Any]] = None) -> int:
        """Count entities matching optional criteria."""
        ...


@runtime_checkable
class Specification(Protocol, Generic[T]):
    """
    Specification pattern for encapsulating business rules.
    
    SOLID Compliance:
    - S: Single responsibility - encapsulates one business rule
    - O: Open/closed - new specifications without modifying existing code
    """
    
    def is_satisfied_by(self, entity: T) -> bool:
        """Check if the entity satisfies this specification."""
        ...
    
    def and_(self, other: 'Specification[T]') -> 'Specification[T]':
        """Combine with another specification using AND logic."""
        ...
    
    def or_(self, other: 'Specification[T]') -> 'Specification[T]':
        """Combine with another specification using OR logic."""
        ...
    
    def not_(self) -> 'Specification[T]':
        """Negate this specification."""
        ...


# Concrete specification implementations for composition

class AndSpecification(Generic[T]):
    """Combines two specifications with AND logic."""
    
    def __init__(self, left: Specification[T], right: Specification[T]):
        self.left = left
        self.right = right
    
    def is_satisfied_by(self, entity: T) -> bool:
        return self.left.is_satisfied_by(entity) and self.right.is_satisfied_by(entity)
    
    def and_(self, other: Specification[T]) -> Specification[T]:
        return AndSpecification(self, other)
    
    def or_(self, other: Specification[T]) -> Specification[T]:
        return OrSpecification(self, other)
    
    def not_(self) -> Specification[T]:
        return NotSpecification(self)


class OrSpecification(Generic[T]):
    """Combines two specifications with OR logic."""
    
    def __init__(self, left: Specification[T], right: Specification[T]):
        self.left = left
        self.right = right
    
    def is_satisfied_by(self, entity: T) -> bool:
        return self.left.is_satisfied_by(entity) or self.right.is_satisfied_by(entity)
    
    def and_(self, other: Specification[T]) -> Specification[T]:
        return AndSpecification(self, other)
    
    def or_(self, other: Specification[T]) -> Specification[T]:
        return OrSpecification(self, other)
    
    def not_(self) -> Specification[T]:
        return NotSpecification(self)


class NotSpecification(Generic[T]):
    """Negates a specification."""
    
    def __init__(self, spec: Specification[T]):
        self.spec = spec
    
    def is_satisfied_by(self, entity: T) -> bool:
        return not self.spec.is_satisfied_by(entity)
    
    def and_(self, other: Specification[T]) -> Specification[T]:
        return AndSpecification(self, other)
    
    def or_(self, other: Specification[T]) -> Specification[T]:
        return OrSpecification(self, other)
    
    def not_(self) -> Specification[T]:
        return self.spec  # Double negation


@runtime_checkable
class UnitOfWork(Protocol):
    """
    Unit of Work pattern for transaction management.
    
    SOLID Compliance:
    - S: Single responsibility - manages transactions
    - I: Interface segregation - focused transaction interface
    """
    
    async def __aenter__(self) -> 'UnitOfWork':
        """Start a new unit of work."""
        ...
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Complete or rollback the unit of work."""
        ...
    
    async def commit(self) -> None:
        """Commit all changes."""
        ...
    
    async def rollback(self) -> None:
        """Rollback all changes."""
        ...
    
    def register_new(self, entity: Entity) -> None:
        """Register a new entity to be inserted."""
        ...
    
    def register_dirty(self, entity: Entity) -> None:
        """Register an entity to be updated."""
        ...
    
    def register_deleted(self, entity: Entity) -> None:
        """Register an entity to be deleted."""
        ...


# Factory interfaces following SOLID principles

@runtime_checkable
class Factory(Protocol, Generic[T]):
    """
    Abstract factory interface.
    
    SOLID Compliance:
    - S: Single responsibility - creates objects of type T
    - O: Open/closed - new factories without modifying existing code
    - D: Dependency inversion - abstracts object creation
    """
    
    def create(self, **kwargs) -> T:
        """Create an instance of type T."""
        ...
    
    def can_create(self, type_identifier: str) -> bool:
        """Check if this factory can create the given type."""
        ...


@runtime_checkable
class AsyncFactory(Protocol, Generic[T]):
    """Asynchronous factory interface."""
    
    async def create(self, **kwargs) -> T:
        """Asynchronously create an instance of type T."""
        ...
    
    def can_create(self, type_identifier: str) -> bool:
        """Check if this factory can create the given type."""
        ...


# Type aliases for common patterns
RepositoryType = Repository[AggregateRoot]
QueryRepositoryType = QueryRepository[Entity]
EventHandlerType = EventHandler[DomainEvent]
SpecificationType = Specification[Entity]