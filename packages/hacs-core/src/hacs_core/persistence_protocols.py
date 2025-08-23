"""
HACS Core Persistence Protocols

This module defines the fundamental persistence abstractions for HACS.
These protocols provide clean separation between domain logic and data persistence,
following SOLID principles for dependency inversion.

Key Principles:
- Single Responsibility: Each protocol has one clear purpose
- Interface Segregation: Minimal, focused interfaces
- Dependency Inversion: Abstractions for all persistence concerns

Author: HACS Development Team
License: MIT
"""

import logging
from abc import ABC
from datetime import datetime, timezone
from typing import (
    TypeVar,
    Generic,
    List,
    Optional,
    Dict,
    Any,
    Protocol,
    runtime_checkable,
)
from dataclasses import dataclass, field
from uuid import uuid4

logger = logging.getLogger(__name__)

# Type variables for generic interfaces
T = TypeVar("T")
TEntity = TypeVar("TEntity", bound="Entity")
TAggregate = TypeVar("TAggregate", bound="AggregateRoot")


@dataclass(frozen=True)
class EntityId:
    """Value object for entity identifiers."""

    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Entity ID cannot be empty")

    @classmethod
    def generate(cls) -> "EntityId":
        """Generate a new unique entity ID."""
        return cls(str(uuid4()))

    def __str__(self) -> str:
        return self.value


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
                object.__setattr__(self, "id", EntityId(self.id))
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
        object.__setattr__(self, "updated_at", datetime.now(timezone.utc))
        object.__setattr__(self, "version", self.version + 1)


class AggregateRoot(Entity):
    """
    Base class for aggregate roots in Domain-Driven Design.

    SOLID Compliance:
    - S: Single responsibility - manages domain events and aggregate consistency
    - O: Open/closed - extensible for domain-specific aggregates
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._domain_events: List[Any] = []  # DomainEvent type not imported

    def add_domain_event(self, event: Any):  # DomainEvent type not imported
        """Add a domain event to be published."""
        self._domain_events.append(event)

    def get_domain_events(self) -> List[Any]:  # DomainEvent type not imported
        """Get all pending domain events."""
        return self._domain_events.copy()

    def clear_domain_events(self):
        """Clear all pending domain events."""
        self._domain_events.clear()


@runtime_checkable
class PersistenceProvider(Protocol):
    """
    Abstract persistence provider protocol.

    SOLID Compliance:
    - S: Single responsibility - defines persistence contract
    - I: Interface segregation - minimal persistence interface
    - D: Dependency inversion - abstraction for all storage types
    """

    async def save(
        self, aggregate_type: str, aggregate_id: EntityId, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Save aggregate data."""
        ...

    async def load(
        self, aggregate_type: str, aggregate_id: EntityId
    ) -> Optional[Dict[str, Any]]:
        """Load aggregate data."""
        ...

    async def delete(self, aggregate_type: str, aggregate_id: EntityId) -> bool:
        """Delete aggregate data."""
        ...

    async def exists(self, aggregate_type: str, aggregate_id: EntityId) -> bool:
        """Check if aggregate exists."""
        ...

    async def list_all(
        self, aggregate_type: str, limit: Optional[int] = None, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List all aggregates of given type."""
        ...

    async def find_by_criteria(
        self, aggregate_type: str, criteria: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find aggregates matching criteria."""
        ...

    async def initialize(self) -> None:
        """Initialize the persistence provider."""
        ...

    async def cleanup(self) -> None:
        """Clean up persistence resources."""
        ...


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

    async def find_all(
        self, limit: Optional[int] = None, offset: int = 0
    ) -> List[TAggregate]:
        """Find all aggregates with optional pagination."""
        ...

    async def find_by_criteria(self, criteria: Dict[str, Any]) -> List[TAggregate]:
        """Find aggregates matching specific criteria."""
        ...


@runtime_checkable
class UnitOfWork(Protocol):
    """
    Unit of Work interface for transaction management.

    SOLID Compliance:
    - S: Single responsibility - manages transaction boundary
    - I: Interface segregation - minimal transaction interface
    - D: Dependency inversion - abstraction for all transaction types
    """

    async def __aenter__(self):
        """Enter the transaction context."""
        ...

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the transaction context."""
        ...

    async def commit(self) -> None:
        """Commit the transaction."""
        ...

    async def rollback(self) -> None:
        """Rollback the transaction."""
        ...

    async def add_repository(self, name: str, repository: Repository) -> None:
        """Add a repository to the unit of work."""
        ...

    def get_repository(self, name: str) -> Optional[Repository]:
        """Get a repository by name."""
        ...


@runtime_checkable
class SchemaManager(Protocol):
    """
    Schema management interface for database operations.

    SOLID Compliance:
    - S: Single responsibility - manages database schema
    - I: Interface segregation - focused on schema operations
    - D: Dependency inversion - abstracts schema management details
    """

    async def create_tables(self, resource_types: List[str]) -> None:
        """Create tables for specified resource types."""
        ...

    async def drop_tables(self, resource_types: List[str]) -> None:
        """Drop tables for specified resource types."""
        ...

    async def get_schema_info(self, resource_type: str) -> Dict[str, Any]:
        """Get schema information for a resource type."""
        ...

    async def migrate_schema(self, from_version: str, to_version: str) -> None:
        """Migrate schema from one version to another."""
        ...

    async def validate_schema(self, resource_type: str) -> bool:
        """Validate schema for a resource type."""
        ...


@runtime_checkable
class TransactionManager(Protocol):
    """
    Transaction management interface.

    SOLID Compliance:
    - S: Single responsibility - manages database transactions
    - I: Interface segregation - focused on transaction control
    - D: Dependency inversion - abstracts transaction details
    """

    async def begin_transaction(self) -> UnitOfWork:
        """Begin a new transaction."""
        ...

    async def create_savepoint(self, name: str) -> None:
        """Create a savepoint within current transaction."""
        ...

    async def rollback_to_savepoint(self, name: str) -> None:
        """Rollback to a specific savepoint."""
        ...

    async def release_savepoint(self, name: str) -> None:
        """Release a savepoint."""
        ...


# Backward compatibility with existing HACS protocols
try:
    from .protocols import BaseAdapter as _BaseAdapter

    # Re-export existing protocols for compatibility
    BaseAdapter = _BaseAdapter
except ImportError:
    # Define minimal BaseAdapter if not available
    @runtime_checkable
    class BaseAdapter(Protocol):
        """Base adapter protocol for backward compatibility."""

        name: str
        version: str

        async def initialize(self) -> None:
            """Initialize the adapter."""
            ...

        async def cleanup(self) -> None:
            """Clean up adapter resources."""
            ...


__all__ = [
    # Core entities and value objects
    "EntityId",
    "Entity",
    "AggregateRoot",
    # Persistence protocols
    "PersistenceProvider",
    "Repository",
    "UnitOfWork",
    "SchemaManager",
    "TransactionManager",
    # Backward compatibility
    "BaseAdapter",
]
