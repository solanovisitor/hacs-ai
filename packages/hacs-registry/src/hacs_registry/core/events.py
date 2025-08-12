"""
Event System Following SOLID Principles

This module implements a comprehensive event system that follows SOLID principles:

S - Single Responsibility: Each event class has one purpose
O - Open/Closed: Easy to add new event types without modification
L - Liskov Substitution: All events are substitutable
I - Interface Segregation: Focused event interfaces
D - Dependency Inversion: Depends on abstractions, not concretions

Event Types:
    📋 Registry Events - System-level registry operations
    🏥 Resource Events - Healthcare resource lifecycle
    🤖 Agent Events - AI agent management
    🔐 IAM Events - Security and access control
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Set, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum

from .base import DomainEvent, EventPublisher, EventHandler, EntityId

logger = logging.getLogger(__name__)


class EventSeverity(str, Enum):
    """Severity levels for events."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EventCategory(str, Enum):
    """Categories for event classification."""
    SYSTEM = "system"
    DOMAIN = "domain"
    INTEGRATION = "integration"
    SECURITY = "security"
    AUDIT = "audit"
    COMPLIANCE = "compliance"


# Base Event Classes (Single Responsibility Principle)

class RegistryEvent(DomainEvent):
    """
    Base class for all registry-related events.
    
    SOLID Compliance:
    - S: Single responsibility - registry event data
    - L: Liskov substitution - all registry events behave consistently
    """
    
    def __init__(self, aggregate_id: EntityId, event_version: int = 1, **kwargs):
        super().__init__(aggregate_id, event_version)
        self.severity = kwargs.get('severity', EventSeverity.INFO)
        self.category = kwargs.get('category', EventCategory.SYSTEM)
        self.actor_id = kwargs.get('actor_id')
        self.correlation_id = kwargs.get('correlation_id')
    
    @property
    def aggregate_type(self) -> str:
        return "Registry"


class ResourceEvent(DomainEvent):
    """
    Base class for resource-related events.
    
    SOLID Compliance:
    - S: Single responsibility - resource event data
    - O: Open/closed - extensible for new resource event types
    """
    
    def __init__(self, resource_id: EntityId, resource_type: str, **kwargs):
        super().__init__(resource_id)
        self.resource_type = resource_type
        self.resource_version = kwargs.get('resource_version', '1.0.0')
        self.actor_id = kwargs.get('actor_id')
        self.category = EventCategory.DOMAIN
    
    @property
    def aggregate_type(self) -> str:
        return "Resource"


class AgentEvent(DomainEvent):
    """
    Base class for agent-related events.
    
    SOLID Compliance:
    - S: Single responsibility - agent event data
    - O: Open/closed - extensible for new agent event types
    """
    
    def __init__(self, agent_id: EntityId, agent_type: str, **kwargs):
        super().__init__(agent_id)
        self.agent_type = agent_type
        self.domain = kwargs.get('domain')
        self.role = kwargs.get('role')
        self.actor_id = kwargs.get('actor_id')
        self.category = EventCategory.DOMAIN
    
    @property
    def aggregate_type(self) -> str:
        return "Agent"


class IAMEvent(DomainEvent):
    """
    Base class for IAM/security-related events.
    
    SOLID Compliance:
    - S: Single responsibility - IAM event data
    - O: Open/closed - extensible for new IAM event types
    """
    
    def __init__(self, subject_id: EntityId, **kwargs):
        super().__init__(subject_id)
        self.actor_id = kwargs.get('actor_id')
        self.resource_id = kwargs.get('resource_id')
        self.action = kwargs.get('action')
        self.result = kwargs.get('result', 'unknown')
        self.category = EventCategory.SECURITY
        self.severity = kwargs.get('severity', EventSeverity.INFO)
    
    @property
    def aggregate_type(self) -> str:
        return "IAM"


# Specific Event Implementations (Open/Closed Principle)

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


class ResourceDeprecatedEvent(ResourceEvent):
    """Event fired when a resource is deprecated."""
    
    def __init__(self, resource_id: EntityId, resource_type: str, reason: str, **kwargs):
        super().__init__(resource_id, resource_type, **kwargs)
        self.reason = reason
        self.severity = EventSeverity.WARNING
    
    @property
    def event_type(self) -> str:
        return "resource.deprecated"


class ResourceDeletedEvent(ResourceEvent):
    """Event fired when a resource is deleted."""
    
    def __init__(self, resource_id: EntityId, resource_type: str, **kwargs):
        super().__init__(resource_id, resource_type, **kwargs)
        self.severity = EventSeverity.WARNING
    
    @property
    def event_type(self) -> str:
        return "resource.deleted"


class AgentCreatedEvent(AgentEvent):
    """Event fired when an agent is created."""
    
    @property
    def event_type(self) -> str:
        return "agent.created"


class AgentConfiguredEvent(AgentEvent):
    """Event fired when an agent configuration is updated."""
    
    def __init__(self, agent_id: EntityId, agent_type: str, config_changes: Dict[str, Any], **kwargs):
        super().__init__(agent_id, agent_type, **kwargs)
        self.config_changes = config_changes
    
    @property
    def event_type(self) -> str:
        return "agent.configured"


class AgentDeployedEvent(AgentEvent):
    """Event fired when an agent is deployed."""
    
    def __init__(self, agent_id: EntityId, agent_type: str, environment: str, **kwargs):
        super().__init__(agent_id, agent_type, **kwargs)
        self.environment = environment
    
    @property
    def event_type(self) -> str:
        return "agent.deployed"


class AgentRetiredEvent(AgentEvent):
    """Event fired when an agent is retired."""
    
    def __init__(self, agent_id: EntityId, agent_type: str, reason: str, **kwargs):
        super().__init__(agent_id, agent_type, **kwargs)
        self.reason = reason
        self.severity = EventSeverity.WARNING
    
    @property
    def event_type(self) -> str:
        return "agent.retired"


class PermissionGrantedEvent(IAMEvent):
    """Event fired when a permission is granted."""
    
    def __init__(self, permission_id: EntityId, grantee_id: str, permission_type: str, **kwargs):
        super().__init__(permission_id, **kwargs)
        self.grantee_id = grantee_id
        self.permission_type = permission_type
        self.result = 'granted'
    
    @property
    def event_type(self) -> str:
        return "iam.permission.granted"


class PermissionRevokedEvent(IAMEvent):
    """Event fired when a permission is revoked."""
    
    def __init__(self, permission_id: EntityId, grantee_id: str, permission_type: str, reason: str, **kwargs):
        super().__init__(permission_id, **kwargs)
        self.grantee_id = grantee_id
        self.permission_type = permission_type
        self.reason = reason
        self.result = 'revoked'
        self.severity = EventSeverity.WARNING
    
    @property
    def event_type(self) -> str:
        return "iam.permission.revoked"


class AccessAttemptEvent(IAMEvent):
    """Event fired when access is attempted."""
    
    def __init__(self, subject_id: EntityId, access_granted: bool, **kwargs):
        super().__init__(subject_id, **kwargs)
        self.access_granted = access_granted
        self.result = 'granted' if access_granted else 'denied'
        self.category = EventCategory.AUDIT
        if not access_granted:
            self.severity = EventSeverity.WARNING
    
    @property
    def event_type(self) -> str:
        return "iam.access.attempted"


class EmergencyAccessEvent(IAMEvent):
    """Event fired when emergency access is granted."""
    
    def __init__(self, subject_id: EntityId, justification: str, **kwargs):
        super().__init__(subject_id, **kwargs)
        self.justification = justification
        self.result = 'emergency_granted'
        self.severity = EventSeverity.CRITICAL
        self.category = EventCategory.COMPLIANCE
    
    @property
    def event_type(self) -> str:
        return "iam.emergency.access"


class ComplianceViolationEvent(IAMEvent):
    """Event fired when a compliance violation is detected."""
    
    def __init__(self, subject_id: EntityId, violation_type: str, details: str, **kwargs):
        super().__init__(subject_id, **kwargs)
        self.violation_type = violation_type
        self.details = details
        self.result = 'violation'
        self.severity = EventSeverity.ERROR
        self.category = EventCategory.COMPLIANCE
    
    @property
    def event_type(self) -> str:
        return "iam.compliance.violation"


# Event Bus Implementation (Dependency Inversion Principle)

class EventBus:
    """
    In-memory event bus implementation.
    
    SOLID Compliance:
    - S: Single responsibility - event routing and delivery
    - O: Open/closed - new handlers can be added without modification
    - D: Dependency inversion - depends on EventHandler abstraction
    """
    
    def __init__(self):
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._global_handlers: List[EventHandler] = []
        self._middleware: List[Callable[[DomainEvent], Awaitable[DomainEvent]]] = []
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def subscribe(self, event_type: str, handler: EventHandler):
        """Subscribe a handler to a specific event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        self.logger.debug(f"Handler subscribed to {event_type}")
    
    def subscribe_all(self, handler: EventHandler):
        """Subscribe a handler to all events."""
        self._global_handlers.append(handler)
        self.logger.debug("Global handler subscribed")
    
    def unsubscribe(self, event_type: str, handler: EventHandler):
        """Unsubscribe a handler from an event type."""
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                self.logger.debug(f"Handler unsubscribed from {event_type}")
            except ValueError:
                self.logger.warning(f"Handler not found for {event_type}")
    
    def add_middleware(self, middleware: Callable[[DomainEvent], Awaitable[DomainEvent]]):
        """Add middleware to process events before delivery."""
        self._middleware.append(middleware)
    
    async def publish(self, event: DomainEvent) -> None:
        """Publish a single event to all relevant handlers."""
        try:
            # Apply middleware
            processed_event = event
            for middleware in self._middleware:
                processed_event = await middleware(processed_event)
            
            # Deliver to specific handlers
            specific_handlers = self._handlers.get(event.event_type, [])
            for handler in specific_handlers:
                try:
                    await handler.handle(processed_event)
                except Exception as e:
                    self.logger.error(f"Handler error for {event.event_type}: {e}")
            
            # Deliver to global handlers
            for handler in self._global_handlers:
                try:
                    if event.event_type in handler.supported_event_types:
                        await handler.handle(processed_event)
                except Exception as e:
                    self.logger.error(f"Global handler error for {event.event_type}: {e}")
            
            self.logger.debug(f"Event published: {event.event_type}")
            
        except Exception as e:
            self.logger.error(f"Event publishing failed: {e}")
            raise
    
    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """Publish multiple events."""
        for event in events:
            await self.publish(event)
    
    def get_handler_count(self, event_type: str) -> int:
        """Get the number of handlers for an event type."""
        return len(self._handlers.get(event_type, []))
    
    def get_total_handlers(self) -> int:
        """Get the total number of registered handlers."""
        specific_count = sum(len(handlers) for handlers in self._handlers.values())
        return specific_count + len(self._global_handlers)


# Event Publisher Implementation

class InMemoryEventPublisher:
    """
    In-memory event publisher using EventBus.
    
    SOLID Compliance:
    - S: Single responsibility - publishes events
    - D: Dependency inversion - can work with any event bus
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def publish(self, event: DomainEvent) -> None:
        """Publish a single event."""
        await self.event_bus.publish(event)
        self.logger.debug(f"Published event: {event.event_type}")
    
    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """Publish multiple events."""
        await self.event_bus.publish_batch(events)
        self.logger.debug(f"Published {len(events)} events")


# Event Handler Base Classes

class BaseEventHandler:
    """
    Base implementation for event handlers.
    
    SOLID Compliance:
    - S: Single responsibility - provides common handler functionality
    - L: Liskov substitution - all handlers can be used interchangeably
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @property
    @abstractmethod
    def supported_event_types(self) -> List[str]:
        """Event types this handler supports."""
        pass
    
    async def handle(self, event: DomainEvent) -> None:
        """Handle an event with error logging."""
        try:
            await self._handle_event(event)
            self.logger.debug(f"Handled event: {event.event_type}")
        except Exception as e:
            self.logger.error(f"Error handling {event.event_type}: {e}")
            raise
    
    @abstractmethod
    async def _handle_event(self, event: DomainEvent) -> None:
        """Override this method to implement event handling logic."""
        pass


class ResourceEventHandler(BaseEventHandler):
    """Handler for resource-related events."""
    
    @property
    def supported_event_types(self) -> List[str]:
        return [
            "resource.registered",
            "resource.updated", 
            "resource.deprecated",
            "resource.deleted"
        ]
    
    async def _handle_event(self, event: DomainEvent) -> None:
        if isinstance(event, ResourceEvent):
            self.logger.info(f"Resource {event.event_type}: {event.resource_type} {event.aggregate_id}")


class IAMEventHandler(BaseEventHandler):
    """Handler for IAM/security events."""
    
    @property
    def supported_event_types(self) -> List[str]:
        return [
            "iam.permission.granted",
            "iam.permission.revoked",
            "iam.access.attempted",
            "iam.emergency.access",
            "iam.compliance.violation"
        ]
    
    async def _handle_event(self, event: DomainEvent) -> None:
        if isinstance(event, IAMEvent):
            if event.severity in [EventSeverity.ERROR, EventSeverity.CRITICAL]:
                self.logger.warning(f"Critical IAM event: {event.event_type} - {event.result}")
            else:
                self.logger.info(f"IAM event: {event.event_type} - {event.result}")


# Event Middleware for Cross-Cutting Concerns

async def audit_middleware(event: DomainEvent) -> DomainEvent:
    """Middleware to add audit information to events."""
    event.add_metadata('audit_timestamp', datetime.now(timezone.utc).isoformat())
    event.add_metadata('audit_source', 'hacs_registry')
    return event


async def correlation_middleware(event: DomainEvent) -> DomainEvent:
    """Middleware to add correlation tracking."""
    if 'correlation_id' not in event.metadata:
        event.add_metadata('correlation_id', str(EntityId.generate()))
    return event


# Factory for creating event bus with default configuration

def create_default_event_bus() -> EventBus:
    """Create an event bus with standard configuration."""
    event_bus = EventBus()
    
    # Add default middleware
    event_bus.add_middleware(audit_middleware)
    event_bus.add_middleware(correlation_middleware)
    
    # Add default handlers
    event_bus.subscribe_all(ResourceEventHandler())
    event_bus.subscribe_all(IAMEventHandler())
    
    return event_bus