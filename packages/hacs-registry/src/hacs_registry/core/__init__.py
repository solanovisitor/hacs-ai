"""
HACS Registry Core - Foundational Abstractions

This module provides the core abstractions that follow SOLID principles:

S - Single Responsibility: Each interface has one clear purpose
O - Open/Closed: Extensible through inheritance, closed for modification
L - Liskov Substitution: All implementations are substitutable
I - Interface Segregation: Small, focused interfaces
D - Dependency Inversion: Depend on abstractions, not concretions

Core Patterns:
    🏗️ Repository Pattern - Data access abstraction
    📢 Event System - Decoupled communication
    🏭 Factory Pattern - Object creation abstraction
    🔍 Specification Pattern - Business rules encapsulation
"""

from .base import (
    # Re-exported from hacs-core
    EntityId,
    Entity,
    AggregateRoot,
    Repository,
    UnitOfWork,
    # Registry-specific abstractions
    ValueObject,
    DomainEvent,
    EventPublisher,
    EventHandler,
    LifecycleAware,
    DomainService,
    ApplicationService,
    QueryRepository,
    Specification,
    RegistryAggregateRoot,
    # Type aliases
    RepositoryType,
    QueryRepositoryType,
)

from .events import (
    RegistryEvent,
    ResourceEvent,
    AgentEvent,
    IAMEvent,
    EventBus,
)

from .lifecycle import (
    LifecycleState,
    LifecycleManager,
    LifecycleTransition,
)

from .exceptions import (
    RegistryException,
    DomainException,
    InfrastructureException,
    ValidationException,
    PermissionException,
)

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
    "RepositoryType",
    "QueryRepositoryType",
    # Event system
    "RegistryEvent",
    "ResourceEvent",
    "AgentEvent",
    "IAMEvent",
    "EventBus",
    # Lifecycle management
    "LifecycleState",
    "LifecycleManager",
    "LifecycleTransition",
    # Exceptions
    "RegistryException",
    "DomainException",
    "InfrastructureException",
    "ValidationException",
    "PermissionException",
]
