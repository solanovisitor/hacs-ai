"""
Event System for HACS Infrastructure

This module provides a comprehensive event system with pub/sub capabilities,
event filtering, and asynchronous event handling.
"""

import asyncio
import threading
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from weakref import WeakSet

from pydantic import BaseModel, Field


class EventPriority(str, Enum):
    """Event priority levels."""
    
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class Event(BaseModel):
    """Base event class for the event system."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique event identifier")
    type: str = Field(..., description="Event type")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Event timestamp")
    source: str = Field(..., description="Event source/publisher")
    priority: EventPriority = Field(EventPriority.NORMAL, description="Event priority")
    
    # Event data
    data: Dict[str, Any] = Field(default_factory=dict, description="Event data payload")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Event metadata")
    
    # Routing and filtering
    tags: Set[str] = Field(default_factory=set, description="Event tags for filtering")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for related events")
    
    def add_tag(self, tag: str) -> None:
        """Add tag to event."""
        self.tags.add(tag)
    
    def has_tag(self, tag: str) -> bool:
        """Check if event has specific tag."""
        return tag in self.tags
    
    def get_age(self) -> float:
        """Get event age in seconds."""
        return (datetime.now(timezone.utc) - self.timestamp).total_seconds()


class EventFilter:
    """Event filter for subscription filtering."""
    
    def __init__(
        self,
        event_types: Optional[Set[str]] = None,
        tags: Optional[Set[str]] = None,
        sources: Optional[Set[str]] = None,
        priority: Optional[EventPriority] = None,
        custom_filter: Optional[Callable[[Event], bool]] = None
    ):
        """
        Initialize event filter.
        
        Args:
            event_types: Set of event types to match
            tags: Set of tags to match (any)
            sources: Set of sources to match
            priority: Minimum priority level
            custom_filter: Custom filter function
        """
        self.event_types = event_types
        self.tags = tags
        self.sources = sources
        self.priority = priority
        self.custom_filter = custom_filter
    
    def matches(self, event: Event) -> bool:
        """Check if event matches filter criteria."""
        # Check event type
        if self.event_types and event.type not in self.event_types:
            return False
        
        # Check tags (any tag matches)
        if self.tags and not self.tags.intersection(event.tags):
            return False
        
        # Check source
        if self.sources and event.source not in self.sources:
            return False
        
        # Check priority
        if self.priority:
            priority_order = [EventPriority.LOW, EventPriority.NORMAL, EventPriority.HIGH, EventPriority.CRITICAL]
            if priority_order.index(event.priority) < priority_order.index(self.priority):
                return False
        
        # Check custom filter
        if self.custom_filter and not self.custom_filter(event):
            return False
        
        return True


EventHandler = Callable[[Event], None]
AsyncEventHandler = Callable[[Event], None]


class EventSubscription:
    """Represents an event subscription."""
    
    def __init__(
        self,
        subscription_id: str,
        handler: Callable[[Event], Any],
        event_filter: Optional[EventFilter] = None,
        is_async: bool = False
    ):
        """
        Initialize event subscription.
        
        Args:
            subscription_id: Unique subscription identifier
            handler: Event handler function
            event_filter: Event filter for this subscription
            is_async: Whether handler is async
        """
        self.id = subscription_id
        self.handler = handler
        self.filter = event_filter
        self.is_async = is_async
        self.created_at = datetime.now(timezone.utc)
        self.event_count = 0
        self.last_event_at: Optional[datetime] = None
    
    def matches_event(self, event: Event) -> bool:
        """Check if subscription matches event."""
        return self.filter.matches(event) if self.filter else True
    
    async def handle_event(self, event: Event) -> None:
        """Handle event with this subscription."""
        try:
            self.event_count += 1
            self.last_event_at = datetime.now(timezone.utc)
            
            if self.is_async:
                await self.handler(event)
            else:
                self.handler(event)
        except Exception as e:
            # Log error but don't propagate to avoid affecting other handlers
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Event handler failed for subscription {self.id}: {e}")


class EventError(Exception):
    """Event system related errors."""
    pass


class EventBus:
    """
    Comprehensive event bus with pub/sub capabilities, filtering,
    and asynchronous event handling.
    """
    
    def __init__(self, max_event_history: int = 1000):
        """
        Initialize event bus.
        
        Args:
            max_event_history: Maximum number of events to keep in history
        """
        self._subscriptions: Dict[str, EventSubscription] = {}
        self._event_history: List[Event] = []
        self._max_event_history = max_event_history
        self._lock = threading.RLock()
        
        # Event processing
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._processing_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Statistics
        self._total_events_published = 0
        self._total_events_processed = 0
    
    async def start(self) -> None:
        """Start event processing."""
        if self._running:
            return
        
        self._running = True
        self._event_queue = asyncio.Queue()
        self._processing_task = asyncio.create_task(self._process_events())
    
    async def stop(self) -> None:
        """Stop event processing."""
        if not self._running:
            return
        
        self._running = False
        
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
            self._processing_task = None
    
    def publish(self, event: Event) -> None:
        """
        Publish event to the bus.
        
        Args:
            event: Event to publish
        """
        with self._lock:
            # Add to history
            self._event_history.append(event)
            if len(self._event_history) > self._max_event_history:
                self._event_history.pop(0)
            
            self._total_events_published += 1
        
        # Queue for async processing
        if self._running:
            try:
                self._event_queue.put_nowait(event)
            except asyncio.QueueFull:
                # Log warning but don't block
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Event queue full, dropping event: {event.id}")
    
    def publish_event(
        self,
        event_type: str,
        source: str,
        data: Optional[Dict[str, Any]] = None,
        priority: EventPriority = EventPriority.NORMAL,
        tags: Optional[Set[str]] = None,
        correlation_id: Optional[str] = None
    ) -> str:
        """
        Publish event with specified parameters.
        
        Args:
            event_type: Type of event
            source: Event source
            data: Event data
            priority: Event priority
            tags: Event tags
            correlation_id: Correlation ID
            
        Returns:
            Event ID
        """
        event = Event(
            type=event_type,
            source=source,
            data=data or {},
            priority=priority,
            tags=tags or set(),
            correlation_id=correlation_id
        )
        
        self.publish(event)
        return event.id
    
    def subscribe(
        self,
        handler: Callable[[Event], Any],
        event_filter: Optional[EventFilter] = None,
        is_async: bool = False
    ) -> str:
        """
        Subscribe to events.
        
        Args:
            handler: Event handler function
            event_filter: Event filter for subscription
            is_async: Whether handler is async
            
        Returns:
            Subscription ID
        """
        subscription_id = str(uuid.uuid4())
        subscription = EventSubscription(subscription_id, handler, event_filter, is_async)
        
        with self._lock:
            self._subscriptions[subscription_id] = subscription
        
        return subscription_id
    
    def subscribe_to_type(
        self,
        event_type: str,
        handler: Callable[[Event], Any],
        is_async: bool = False
    ) -> str:
        """
        Subscribe to specific event type.
        
        Args:
            event_type: Event type to subscribe to
            handler: Event handler function
            is_async: Whether handler is async
            
        Returns:
            Subscription ID
        """
        event_filter = EventFilter(event_types={event_type})
        return self.subscribe(handler, event_filter, is_async)
    
    def subscribe_to_tags(
        self,
        tags: Set[str],
        handler: Callable[[Event], Any],
        is_async: bool = False
    ) -> str:
        """
        Subscribe to events with specific tags.
        
        Args:
            tags: Tags to subscribe to
            handler: Event handler function
            is_async: Whether handler is async
            
        Returns:
            Subscription ID
        """
        event_filter = EventFilter(tags=tags)
        return self.subscribe(handler, event_filter, is_async)
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from events.
        
        Args:
            subscription_id: Subscription ID to remove
            
        Returns:
            True if subscription was removed
        """
        with self._lock:
            return self._subscriptions.pop(subscription_id, None) is not None
    
    def get_subscription(self, subscription_id: str) -> Optional[EventSubscription]:
        """Get subscription by ID."""
        with self._lock:
            return self._subscriptions.get(subscription_id)
    
    def get_subscriptions(self) -> List[EventSubscription]:
        """Get all active subscriptions."""
        with self._lock:
            return list(self._subscriptions.values())
    
    async def _process_events(self) -> None:
        """Process events from queue."""
        while self._running:
            try:
                # Get event from queue with timeout
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                await self._dispatch_event(event)
                self._total_events_processed += 1
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error processing event: {e}")
    
    async def _dispatch_event(self, event: Event) -> None:
        """Dispatch event to matching subscriptions."""
        matching_subscriptions = []
        
        with self._lock:
            for subscription in self._subscriptions.values():
                if subscription.matches_event(event):
                    matching_subscriptions.append(subscription)
        
        # Handle events concurrently
        if matching_subscriptions:
            tasks = [
                subscription.handle_event(event)
                for subscription in matching_subscriptions
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_event_history(
        self,
        event_type: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 100
    ) -> List[Event]:
        """
        Get event history with optional filtering.
        
        Args:
            event_type: Filter by event type
            source: Filter by source
            limit: Maximum number of events to return
            
        Returns:
            List of events
        """
        with self._lock:
            events = self._event_history.copy()
        
        # Apply filters
        if event_type:
            events = [e for e in events if e.type == event_type]
        
        if source:
            events = [e for e in events if e.source == source]
        
        # Return most recent events first
        events.reverse()
        return events[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        with self._lock:
            return {
                "total_events_published": self._total_events_published,
                "total_events_processed": self._total_events_processed,
                "active_subscriptions": len(self._subscriptions),
                "event_history_size": len(self._event_history),
                "queue_size": self._event_queue.qsize() if self._running else 0,
                "is_running": self._running
            }
    
    def clear_history(self) -> None:
        """Clear event history."""
        with self._lock:
            self._event_history.clear()
    
    def get_events_by_correlation_id(self, correlation_id: str) -> List[Event]:
        """Get all events with specific correlation ID."""
        with self._lock:
            return [
                event for event in self._event_history
                if event.correlation_id == correlation_id
            ]


# Convenience functions for common event patterns

def create_system_event(
    event_type: str,
    data: Optional[Dict[str, Any]] = None,
    priority: EventPriority = EventPriority.NORMAL
) -> Event:
    """Create system event."""
    return Event(
        type=event_type,
        source="system",
        data=data or {},
        priority=priority,
        tags={"system"}
    )


def create_health_event(
    service_name: str,
    is_healthy: bool,
    details: Optional[Dict[str, Any]] = None
) -> Event:
    """Create health check event."""
    return Event(
        type="health_check",
        source=service_name,
        data={
            "service": service_name,
            "healthy": is_healthy,
            "details": details or {}
        },
        priority=EventPriority.HIGH if not is_healthy else EventPriority.NORMAL,
        tags={"health", "monitoring"}
    )


def create_error_event(
    source: str,
    error: Exception,
    context: Optional[Dict[str, Any]] = None
) -> Event:
    """Create error event."""
    return Event(
        type="error",
        source=source,
        data={
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        },
        priority=EventPriority.HIGH,
        tags={"error", "monitoring"}
    )