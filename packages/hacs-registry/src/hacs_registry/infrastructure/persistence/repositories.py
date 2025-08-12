"""
Repository Implementations Following SOLID Principles

This module implements the Repository pattern for different domain aggregates,
providing a clean separation between domain logic and data persistence.

SOLID Compliance:
- S: Single Responsibility - Each repository manages one aggregate type
- O: Open/Closed - Extensible through inheritance and composition
- L: Liskov Substitution - All repositories implement Repository contract
- I: Interface Segregation - Focused repository interfaces
- D: Dependency Inversion - Depends on adapter abstractions

Repository Pattern Benefits:
    🏗️ Encapsulates data access logic
    🔄 Provides consistent interface across storage types
    🧪 Enables easy testing with mock adapters
    📊 Centralizes data access patterns
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from ...core.base import EntityId, Repository, AggregateRoot
from ...core.exceptions import (
    ResourceNotFoundError, AgentNotFoundError, PermissionException,
    PersistenceException
)
from .adapters import PersistenceAdapter

logger = logging.getLogger(__name__)


class BaseRepository(Repository[AggregateRoot]):
    """
    Base repository implementation with common functionality.
    
    SOLID Compliance:
    - S: Single responsibility - provides common repository operations
    - D: Dependency inversion - depends on PersistenceAdapter abstraction
    """
    
    def __init__(self, adapter: PersistenceAdapter, aggregate_type: str):
        self.adapter = adapter
        self.aggregate_type = aggregate_type
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
    
    async def _serialize_aggregate(self, aggregate: AggregateRoot) -> Dict[str, Any]:
        """Serialize aggregate to dictionary."""
        # Use aggregate's own serialization if available
        if hasattr(aggregate, 'to_dict'):
            return aggregate.to_dict()
        
        # Default serialization
        return {
            "id": aggregate.id.value,
            "created_at": aggregate.created_at.isoformat(),
            "updated_at": aggregate.updated_at.isoformat(),
            "version": aggregate.version,
            "aggregate_type": aggregate.aggregate_type,
        }
    
    async def _deserialize_aggregate(self, data: Dict[str, Any]) -> AggregateRoot:
        """Deserialize dictionary to aggregate."""
        # This is abstract - subclasses must implement
        raise NotImplementedError("Subclasses must implement _deserialize_aggregate")
    
    async def save(self, aggregate: AggregateRoot) -> AggregateRoot:
        """Save an aggregate to persistence."""
        try:
            # Serialize the aggregate
            data = await self._serialize_aggregate(aggregate)
            
            # Save through adapter
            saved_data = await self.adapter.save(self.aggregate_type, aggregate.id, data)
            
            # Update aggregate timestamps
            aggregate.update_timestamp()
            
            self.logger.debug(f"Saved {self.aggregate_type} {aggregate.id}")
            return aggregate
            
        except Exception as e:
            self.logger.error(f"Failed to save {self.aggregate_type} {aggregate.id}: {e}")
            raise PersistenceException(f"Save failed for {self.aggregate_type}", operation="save") from e
    
    async def find_by_id(self, aggregate_id: EntityId) -> Optional[AggregateRoot]:
        """Find an aggregate by its ID."""
        try:
            data = await self.adapter.load(self.aggregate_type, aggregate_id)
            
            if data is None:
                return None
            
            # Deserialize the aggregate
            aggregate = await self._deserialize_aggregate(data)
            
            self.logger.debug(f"Found {self.aggregate_type} {aggregate_id}")
            return aggregate
            
        except Exception as e:
            self.logger.error(f"Failed to find {self.aggregate_type} {aggregate_id}: {e}")
            raise PersistenceException(f"Find failed for {self.aggregate_type}", operation="find") from e
    
    async def exists(self, aggregate_id: EntityId) -> bool:
        """Check if an aggregate exists."""
        try:
            return await self.adapter.exists(self.aggregate_type, aggregate_id)
        except Exception as e:
            self.logger.error(f"Failed to check existence of {self.aggregate_type} {aggregate_id}: {e}")
            return False
    
    async def delete(self, aggregate_id: EntityId) -> bool:
        """Delete an aggregate by ID."""
        try:
            result = await self.adapter.delete(self.aggregate_type, aggregate_id)
            
            if result:
                self.logger.debug(f"Deleted {self.aggregate_type} {aggregate_id}")
            else:
                self.logger.warning(f"Failed to delete {self.aggregate_type} {aggregate_id} - not found")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to delete {self.aggregate_type} {aggregate_id}: {e}")
            raise PersistenceException(f"Delete failed for {self.aggregate_type}", operation="delete") from e
    
    async def find_all(self, limit: Optional[int] = None, offset: int = 0) -> List[AggregateRoot]:
        """Find all aggregates with pagination."""
        try:
            all_data = await self.adapter.list_all(self.aggregate_type, limit, offset)
            
            aggregates = []
            for data in all_data:
                try:
                    aggregate = await self._deserialize_aggregate(data)
                    aggregates.append(aggregate)
                except Exception as e:
                    self.logger.warning(f"Failed to deserialize {self.aggregate_type} data: {e}")
                    continue
            
            self.logger.debug(f"Found {len(aggregates)} {self.aggregate_type} aggregates")
            return aggregates
            
        except Exception as e:
            self.logger.error(f"Failed to find all {self.aggregate_type}: {e}")
            raise PersistenceException(f"Find all failed for {self.aggregate_type}", operation="find_all") from e
    
    async def find_by_criteria(self, criteria: Dict[str, Any]) -> List[AggregateRoot]:
        """Find aggregates matching criteria."""
        try:
            matching_data = await self.adapter.find_by_criteria(self.aggregate_type, criteria)
            
            aggregates = []
            for data in matching_data:
                try:
                    aggregate = await self._deserialize_aggregate(data)
                    aggregates.append(aggregate)
                except Exception as e:
                    self.logger.warning(f"Failed to deserialize {self.aggregate_type} data: {e}")
                    continue
            
            self.logger.debug(f"Found {len(aggregates)} {self.aggregate_type} matching criteria")
            return aggregates
            
        except Exception as e:
            self.logger.error(f"Failed to find {self.aggregate_type} by criteria: {e}")
            raise PersistenceException(f"Find by criteria failed for {self.aggregate_type}", operation="find_by_criteria") from e


# Specific Repository Implementations

class InMemoryResourceRepository(BaseRepository):
    """
    In-memory repository for resource aggregates.
    
    SOLID Compliance:
    - S: Single responsibility - manages resource persistence only
    - L: Liskov substitution - implements Repository[ResourceAggregate]
    """
    
    def __init__(self, adapter: PersistenceAdapter):
        super().__init__(adapter, "Resource")
    
    async def _deserialize_aggregate(self, data: Dict[str, Any]) -> AggregateRoot:
        """Deserialize data to ResourceAggregate."""
        # Import here to avoid circular imports
        from ...domain.models.resource import ResourceAggregate, ResourceMetadata
        
        # Create ResourceMetadata
        metadata = ResourceMetadata(
            name=data.get("name", ""),
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            category=data.get("category", "clinical"),
            tags=data.get("tags", [])
        )
        
        # Create ResourceAggregate
        aggregate = ResourceAggregate(
            id=EntityId(data["id"]),
            metadata=metadata,
            hacs_resource_class=data.get("hacs_resource_class", "BaseResource"),
            instance_data=data.get("instance_data", {})
        )
        
        # Set timestamps and version
        if "created_at" in data:
            object.__setattr__(aggregate, 'created_at', datetime.fromisoformat(data["created_at"]))
        if "updated_at" in data:
            object.__setattr__(aggregate, 'updated_at', datetime.fromisoformat(data["updated_at"]))
        if "version" in data:
            object.__setattr__(aggregate, 'version', data["version"])
        
        return aggregate
    
    async def find_by_category(self, category: str) -> List[AggregateRoot]:
        """Find resources by category."""
        return await self.find_by_criteria({"category": category})
    
    async def find_by_status(self, status: str) -> List[AggregateRoot]:
        """Find resources by status."""
        return await self.find_by_criteria({"status": status})


class InMemoryAgentRepository(BaseRepository):
    """
    In-memory repository for agent aggregates.
    
    SOLID Compliance:
    - S: Single responsibility - manages agent persistence only
    - L: Liskov substitution - implements Repository[AgentAggregate]
    """
    
    def __init__(self, adapter: PersistenceAdapter):
        super().__init__(adapter, "Agent")
    
    async def _deserialize_aggregate(self, data: Dict[str, Any]) -> AggregateRoot:
        """Deserialize data to AgentAggregate."""
        # Import here to avoid circular imports
        from ...domain.models.agent import AgentAggregate, AgentMetadata
        
        # Create AgentMetadata
        metadata = AgentMetadata(
            name=data.get("name", ""),
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            domain=data.get("domain", "general"),
            role=data.get("role", "clinical_assistant")
        )
        
        # Create AgentAggregate
        aggregate = AgentAggregate(
            id=EntityId(data["id"]),
            metadata=metadata,
            configuration=data.get("configuration", {}),
            status=data.get("status", "draft")
        )
        
        # Set timestamps and version
        if "created_at" in data:
            object.__setattr__(aggregate, 'created_at', datetime.fromisoformat(data["created_at"]))
        if "updated_at" in data:
            object.__setattr__(aggregate, 'updated_at', datetime.fromisoformat(data["updated_at"]))
        if "version" in data:
            object.__setattr__(aggregate, 'version', data["version"])
        
        return aggregate
    
    async def find_by_domain(self, domain: str) -> List[AggregateRoot]:
        """Find agents by healthcare domain."""
        return await self.find_by_criteria({"domain": domain})
    
    async def find_by_role(self, role: str) -> List[AggregateRoot]:
        """Find agents by role."""
        return await self.find_by_criteria({"role": role})


class InMemoryIAMRepository(BaseRepository):
    """
    In-memory repository for IAM aggregates (actors, permissions).
    
    SOLID Compliance:
    - S: Single responsibility - manages IAM persistence only
    - L: Liskov substitution - implements Repository[IAMAggregate]
    """
    
    def __init__(self, adapter: PersistenceAdapter):
        super().__init__(adapter, "IAM")
    
    async def _deserialize_aggregate(self, data: Dict[str, Any]) -> AggregateRoot:
        """Deserialize data to IAM aggregate."""
        # Import here to avoid circular imports
        from ...domain.models.iam import ActorAggregate
        
        # Create ActorAggregate (simplified for now)
        aggregate = ActorAggregate(
            id=EntityId(data["id"]),
            actor_type=data.get("actor_type", "human"),
            name=data.get("name", ""),
            credentials=data.get("credentials", []),
            permissions=data.get("permissions", [])
        )
        
        # Set timestamps and version
        if "created_at" in data:
            object.__setattr__(aggregate, 'created_at', datetime.fromisoformat(data["created_at"]))
        if "updated_at" in data:
            object.__setattr__(aggregate, 'updated_at', datetime.fromisoformat(data["updated_at"]))
        if "version" in data:
            object.__setattr__(aggregate, 'version', data["version"])
        
        return aggregate
    
    async def find_by_actor_type(self, actor_type: str) -> List[AggregateRoot]:
        """Find actors by type."""
        return await self.find_by_criteria({"actor_type": actor_type})
    
    async def find_by_permission(self, permission: str) -> List[AggregateRoot]:
        """Find actors with specific permission."""
        # This would need more complex querying in a real implementation
        all_actors = await self.find_all()
        return [actor for actor in all_actors if permission in getattr(actor, 'permissions', [])]


class InMemoryToolRepository(BaseRepository):
    """
    In-memory repository for tool aggregates.
    
    SOLID Compliance:
    - S: Single responsibility - manages tool persistence only
    - L: Liskov substitution - implements Repository[ToolAggregate]
    """
    
    def __init__(self, adapter: PersistenceAdapter):
        super().__init__(adapter, "Tool")
    
    async def _deserialize_aggregate(self, data: Dict[str, Any]) -> AggregateRoot:
        """Deserialize data to ToolAggregate."""
        # Import here to avoid circular imports
        from ...domain.models.tool import ToolAggregate, ToolMetadata
        
        # Create ToolMetadata
        metadata = ToolMetadata(
            name=data.get("name", ""),
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            category=data.get("category", "general")
        )
        
        # Create ToolAggregate
        aggregate = ToolAggregate(
            id=EntityId(data["id"]),
            metadata=metadata,
            function_definition=data.get("function_definition", {}),
            execution_context=data.get("execution_context", {})
        )
        
        # Set timestamps and version
        if "created_at" in data:
            object.__setattr__(aggregate, 'created_at', datetime.fromisoformat(data["created_at"]))
        if "updated_at" in data:
            object.__setattr__(aggregate, 'updated_at', datetime.fromisoformat(data["updated_at"]))
        if "version" in data:
            object.__setattr__(aggregate, 'version', data["version"])
        
        return aggregate
    
    async def find_by_category(self, category: str) -> List[AggregateRoot]:
        """Find tools by category."""
        return await self.find_by_criteria({"category": category})
    
    async def find_available_tools(self) -> List[AggregateRoot]:
        """Find all available (non-disabled) tools."""
        return await self.find_by_criteria({"status": "available"})