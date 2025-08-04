"""
Unit of Work Pattern Implementation Following SOLID Principles

This module implements the Unit of Work pattern to manage transactions
and coordinate multiple repository operations.

SOLID Compliance:
- S: Single Responsibility - Each UoW manages one transaction boundary
- O: Open/Closed - Extensible for new repository types
- L: Liskov Substitution - All UoW implementations are substitutable
- I: Interface Segregation - Focused transaction interface
- D: Dependency Inversion - Depends on repository abstractions

Unit of Work Benefits:
    🔄 Manages transaction boundaries
    📊 Coordinates multiple repositories
    ⚡ Optimizes database operations
    🔒 Ensures data consistency
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from ...core.base import EntityId, Repository, AggregateRoot
from ...core.events import DomainEvent
from ...core.exceptions import PersistenceException
from .adapters import PersistenceAdapter

logger = logging.getLogger(__name__)


class UnitOfWork(ABC):
    """
    Abstract base class for Unit of Work implementations.
    
    SOLID Compliance:
    - S: Single responsibility - manages transaction boundary
    - I: Interface segregation - minimal transaction interface
    - D: Dependency inversion - abstraction for all UoW types
    """
    
    @abstractmethod
    async def __aenter__(self):
        """Enter the transaction context."""
        pass
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the transaction context."""
        pass
    
    @abstractmethod
    async def commit(self) -> None:
        """Commit the transaction."""
        pass
    
    @abstractmethod
    async def rollback(self) -> None:
        """Rollback the transaction."""
        pass
    
    @abstractmethod
    def get_repository(self, repository_type: str) -> Repository:
        """Get a repository for the current transaction."""
        pass
    
    @abstractmethod
    def collect_events(self) -> List[DomainEvent]:
        """Collect all domain events from tracked aggregates."""
        pass


class InMemoryUnitOfWork(UnitOfWork):
    """
    In-memory implementation of Unit of Work.
    
    SOLID Compliance:
    - S: Single responsibility - manages in-memory transactions
    - L: Liskov substitution - implements UnitOfWork contract
    """
    
    def __init__(self, adapter: PersistenceAdapter):
        self.adapter = adapter
        self._repositories: Dict[str, Repository] = {}
        self._tracked_aggregates: List[AggregateRoot] = []
        self._committed = False
        self._rolled_back = False
    
    async def __aenter__(self):
        """Enter the transaction context."""
        # For in-memory, we don't need real transactions
        # but we track operations for consistency
        self._committed = False
        self._rolled_back = False
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the transaction context."""
        if exc_type is not None and not self._rolled_back:
            await self.rollback()
        elif not self._committed and not self._rolled_back:
            await self.commit()
    
    async def commit(self) -> None:
        """Commit the transaction."""
        if self._committed or self._rolled_back:
            return
        
        try:
            # In memory implementation: operations are already applied
            # In a real database implementation, this would flush changes
            
            # Collect and publish domain events
            events = self.collect_events()
            
            # Mark as committed
            self._committed = True
            
            # Clear tracked aggregates
            self._tracked_aggregates.clear()
            
            logger.debug(f"Transaction committed with {len(events)} domain events")
            
        except Exception as e:
            logger.error(f"Failed to commit transaction: {e}")
            await self.rollback()
            raise PersistenceException("Transaction commit failed", operation="commit") from e
    
    async def rollback(self) -> None:
        """Rollback the transaction."""
        if self._committed or self._rolled_back:
            return
        
        try:
            # In memory implementation: we'd need to restore previous state
            # For now, just clear tracking
            self._tracked_aggregates.clear()
            self._rolled_back = True
            
            logger.debug("Transaction rolled back")
            
        except Exception as e:
            logger.error(f"Failed to rollback transaction: {e}")
            raise PersistenceException("Transaction rollback failed", operation="rollback") from e
    
    def get_repository(self, repository_type: str) -> Repository:
        """Get a repository for the current transaction."""
        if repository_type not in self._repositories:
            # Import repositories here to avoid circular imports
            from .repositories import (
                InMemoryResourceRepository, InMemoryAgentRepository,
                InMemoryIAMRepository, InMemoryToolRepository
            )
            
            repository_classes = {
                "resource": InMemoryResourceRepository,
                "agent": InMemoryAgentRepository, 
                "iam": InMemoryIAMRepository,
                "tool": InMemoryToolRepository,
            }
            
            if repository_type not in repository_classes:
                raise ValueError(f"Unknown repository type: {repository_type}")
            
            repository_class = repository_classes[repository_type]
            repository = repository_class(self.adapter)
            
            # Wrap repository to track aggregates
            wrapped_repository = TrackingRepositoryWrapper(repository, self)
            self._repositories[repository_type] = wrapped_repository
        
        return self._repositories[repository_type]
    
    def track_aggregate(self, aggregate: AggregateRoot) -> None:
        """Track an aggregate for event collection."""
        if aggregate not in self._tracked_aggregates:
            self._tracked_aggregates.append(aggregate)
    
    def collect_events(self) -> List[DomainEvent]:
        """Collect all domain events from tracked aggregates."""
        events = []
        for aggregate in self._tracked_aggregates:
            events.extend(aggregate.get_domain_events())
            aggregate.clear_domain_events()
        return events


class TrackingRepositoryWrapper:
    """
    Wrapper that tracks aggregates for the Unit of Work.
    
    SOLID Compliance:
    - S: Single responsibility - tracks aggregates for UoW
    - D: Dependency inversion - wraps repository abstraction
    """
    
    def __init__(self, repository: Repository, unit_of_work: InMemoryUnitOfWork):
        self.repository = repository
        self.unit_of_work = unit_of_work
    
    async def save(self, aggregate: AggregateRoot) -> AggregateRoot:
        """Save aggregate and track it."""
        result = await self.repository.save(aggregate)
        self.unit_of_work.track_aggregate(aggregate)
        return result
    
    async def find_by_id(self, aggregate_id: EntityId) -> Optional[AggregateRoot]:
        """Find aggregate by ID."""
        return await self.repository.find_by_id(aggregate_id)
    
    async def exists(self, aggregate_id: EntityId) -> bool:
        """Check if aggregate exists."""
        return await self.repository.exists(aggregate_id)
    
    async def delete(self, aggregate_id: EntityId) -> bool:
        """Delete aggregate."""
        return await self.repository.delete(aggregate_id)
    
    async def find_all(self, limit: Optional[int] = None, offset: int = 0) -> List[AggregateRoot]:
        """Find all aggregates."""
        return await self.repository.find_all(limit, offset)
    
    async def find_by_criteria(self, criteria: Dict[str, Any]) -> List[AggregateRoot]:
        """Find aggregates by criteria."""
        return await self.repository.find_by_criteria(criteria)


class UnitOfWorkManager:
    """
    Manager for creating and coordinating Unit of Work instances.
    
    SOLID Compliance:
    - S: Single responsibility - manages UoW lifecycle
    - O: Open/closed - extensible for new UoW types
    - D: Dependency inversion - depends on UoW abstractions
    """
    
    def __init__(self, adapter: PersistenceAdapter):
        self.adapter = adapter
        self._active_units: List[UnitOfWork] = []
    
    @asynccontextmanager
    async def begin_transaction(self):
        """Begin a new unit of work transaction."""
        unit_of_work = InMemoryUnitOfWork(self.adapter)
        self._active_units.append(unit_of_work)
        
        try:
            async with unit_of_work:
                yield unit_of_work
        finally:
            if unit_of_work in self._active_units:
                self._active_units.remove(unit_of_work)
    
    async def cleanup_all(self) -> None:
        """Clean up all active units of work."""
        for unit_of_work in self._active_units.copy():
            try:
                await unit_of_work.rollback()
            except Exception as e:
                logger.warning(f"Failed to rollback unit of work: {e}")
        
        self._active_units.clear()
        logger.info("All units of work cleaned up")
    
    def get_active_count(self) -> int:
        """Get the number of active units of work."""
        return len(self._active_units)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the UoW manager."""
        return {
            "active_units": len(self._active_units),
            "adapter_type": type(self.adapter).__name__,
            "status": "healthy"
        }