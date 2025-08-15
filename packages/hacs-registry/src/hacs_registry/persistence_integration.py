"""
Persistence Integration for HACS Registry

This module implements dependency inversion between hacs-registry and hacs-persistence.
The registry uses persistence through the protocols defined in hacs-core, enabling
clean separation of concerns and testability.

SOLID Compliance:
- S: Single Responsibility - Integrates registry with persistence layer
- O: Open/Closed - Extensible for different persistence providers
- L: Liskov Substitution - Works with any PersistenceProvider implementation
- I: Interface Segregation - Uses focused persistence protocols
- D: Dependency Inversion - Depends on abstractions, not implementations

Author: HACS Development Team
License: MIT
"""

import logging
from typing import Optional, Dict, Any, List, Type
from contextlib import asynccontextmanager

# Import protocols from hacs-core
from hacs_core.persistence_protocols import (
    Repository, PersistenceProvider, UnitOfWork, EntityId
)

# Import registry types
from .core import RegistryAggregateRoot
from .resource_registry import RegisteredResource, HACSResourceRegistry
from .agent_registry import AgentConfiguration, HACSAgentRegistry
from .iam_registry import ActorIdentity, HACSIAMRegistry
from .tool_registry import ToolDefinition, HACSToolRegistry

logger = logging.getLogger(__name__)


class RegistryPersistenceService:
    """
    Service that integrates registry operations with persistence layer.

    SOLID Compliance:
    - S: Single responsibility - manages registry persistence integration
    - D: Dependency inversion - uses persistence abstractions
    """

    def __init__(self, persistence_provider: Optional[PersistenceProvider] = None):
        self.persistence_provider = persistence_provider
        self._repositories: Dict[str, Repository] = {}
        self.logger = logging.getLogger(self.__class__.__name__)

    def set_persistence_provider(self, provider: PersistenceProvider):
        """Set the persistence provider."""
        self.persistence_provider = provider
        self._repositories.clear()  # Clear cached repositories

    def _get_repository(self, aggregate_type: str) -> Optional[Repository]:
        """Get repository for aggregate type."""
        if self.persistence_provider is None:
            return None

        if aggregate_type not in self._repositories:
            # Create a generic repository wrapper
            self._repositories[aggregate_type] = RegistryRepositoryWrapper(
                self.persistence_provider, aggregate_type
            )

        return self._repositories[aggregate_type]

    async def save_registered_resource(self, resource: RegisteredResource) -> RegisteredResource:
        """Save a registered resource."""
        repository = self._get_repository("RegisteredResource")
        if repository is None:
            self.logger.warning("No persistence provider configured")
            return resource

        try:
            return await repository.save(resource)
        except Exception as e:
            self.logger.error(f"Failed to save registered resource: {e}")
            return resource

    async def find_registered_resource(self, resource_id: EntityId) -> Optional[RegisteredResource]:
        """Find a registered resource by ID."""
        repository = self._get_repository("RegisteredResource")
        if repository is None:
            return None

        try:
            return await repository.find_by_id(resource_id)
        except Exception as e:
            self.logger.error(f"Failed to find registered resource: {e}")
            return None

    async def save_agent_configuration(self, agent: AgentConfiguration) -> AgentConfiguration:
        """Save an agent configuration."""
        repository = self._get_repository("AgentConfiguration")
        if repository is None:
            self.logger.warning("No persistence provider configured")
            return agent

        try:
            return await repository.save(agent)
        except Exception as e:
            self.logger.error(f"Failed to save agent configuration: {e}")
            return agent

    async def save_actor_identity(self, actor: ActorIdentity) -> ActorIdentity:
        """Save an actor identity."""
        repository = self._get_repository("ActorIdentity")
        if repository is None:
            self.logger.warning("No persistence provider configured")
            return actor

        try:
            return await repository.save(actor)
        except Exception as e:
            self.logger.error(f"Failed to save actor identity: {e}")
            return actor

    async def save_tool_definition(self, tool: ToolDefinition) -> ToolDefinition:
        """Save a tool definition."""
        repository = self._get_repository("ToolDefinition")
        if repository is None:
            self.logger.warning("No persistence provider configured")
            return tool

        try:
            return await repository.save(tool)
        except Exception as e:
            self.logger.error(f"Failed to save tool definition: {e}")
            return tool

    @asynccontextmanager
    async def transaction(self):
        """Create a transaction context for multiple operations."""
        # Provide a best-effort transaction context
        if self.persistence_provider is None:
            yield
            return
        try:
            # Start transaction if provider supports it
            uow: UnitOfWork | None = None
            if hasattr(self.persistence_provider, "begin"):
                uow = await self.persistence_provider.begin()
            try:
                yield
                if uow and hasattr(uow, "commit"):
                    await uow.commit()
            except Exception:
                if uow and hasattr(uow, "rollback"):
                    await uow.rollback()
                raise
        except Exception as e:
            self.logger.error(f"Transaction failed: {e}")
            raise


class RegistryRepositoryWrapper:
    """
    Wrapper that adapts registry aggregates to repository pattern.

    SOLID Compliance:
    - S: Single responsibility - adapts registry objects to repository interface
    - L: Liskov substitution - implements Repository protocol
    """

    def __init__(self, persistence_provider: PersistenceProvider, aggregate_type: str):
        self.persistence_provider = persistence_provider
        self.aggregate_type = aggregate_type
        self.logger = logging.getLogger(f"RegistryRepo[{aggregate_type}]")

    async def save(self, aggregate: RegistryAggregateRoot) -> RegistryAggregateRoot:
        """Save an aggregate."""
        try:
            # Serialize aggregate
            if hasattr(aggregate, 'model_dump'):
                data = aggregate.model_dump()
            elif hasattr(aggregate, 'to_dict'):
                data = aggregate.to_dict()
            else:
                data = aggregate.__dict__.copy()

            # Save via persistence provider
            saved_data = await self.persistence_provider.save(
                self.aggregate_type, aggregate.id, data
            )

            # Return the aggregate (could be updated with saved data)
            return aggregate
        except Exception as e:
            self.logger.error(f"Failed to save {self.aggregate_type}: {e}")
            raise

    async def find_by_id(self, aggregate_id: EntityId) -> Optional[RegistryAggregateRoot]:
        """Find an aggregate by ID."""
        try:
            data = await self.persistence_provider.load(self.aggregate_type, aggregate_id)
            if data is None:
                return None

            # Best-effort reconstruction: return raw dict if model class is unknown
            aggregate_map = {
                "RegisteredResource": RegisteredResource,
                "AgentConfiguration": AgentConfiguration,
                "ActorIdentity": ActorIdentity,
                "ToolDefinition": ToolDefinition,
            }
            model_cls = aggregate_map.get(self.aggregate_type)
            if model_cls is None:
                return None
            if hasattr(model_cls, "model_validate"):
                return model_cls.model_validate(data)  # type: ignore
            return None
        except Exception as e:
            self.logger.error(f"Failed to find {self.aggregate_type}: {e}")
            return None

    async def exists(self, aggregate_id: EntityId) -> bool:
        """Check if aggregate exists."""
        try:
            return await self.persistence_provider.exists(self.aggregate_type, aggregate_id)
        except Exception as e:
            self.logger.error(f"Failed to check existence: {e}")
            return False

    async def delete(self, aggregate_id: EntityId) -> bool:
        """Delete an aggregate."""
        try:
            return await self.persistence_provider.delete(self.aggregate_type, aggregate_id)
        except Exception as e:
            self.logger.error(f"Failed to delete {self.aggregate_type}: {e}")
            return False


class RegistryPersistenceIntegration:
    """
    Main integration class that wires registry components with persistence.

    SOLID Compliance:
    - S: Single responsibility - integrates registry with persistence
    - D: Dependency inversion - configures dependencies via injection
    """

    def __init__(self):
        self.persistence_service: Optional[RegistryPersistenceService] = None
        self._resource_registry: Optional[HACSResourceRegistry] = None
        self._agent_registry: Optional[HACSAgentRegistry] = None
        self._iam_registry: Optional[HACSIAMRegistry] = None
        self._tool_registry: Optional[HACSToolRegistry] = None

    def configure_persistence(self, persistence_provider: PersistenceProvider):
        """Configure persistence for all registry components."""
        self.persistence_service = RegistryPersistenceService(persistence_provider)

        # Update existing registries if they exist
        if self._resource_registry:
            self._resource_registry.set_persistence_service(self.persistence_service)
        if self._agent_registry:
            self._agent_registry.set_persistence_service(self.persistence_service)
        if self._iam_registry:
            self._iam_registry.set_persistence_service(self.persistence_service)
        if self._tool_registry:
            self._tool_registry.set_persistence_service(self.persistence_service)

    def get_resource_registry(self) -> HACSResourceRegistry:
        """Get resource registry with persistence integration."""
        if self._resource_registry is None:
            self._resource_registry = HACSResourceRegistry()
            if self.persistence_service:
                self._resource_registry.set_persistence_service(self.persistence_service)
        return self._resource_registry

    def get_agent_registry(self) -> HACSAgentRegistry:
        """Get agent registry with persistence integration."""
        if self._agent_registry is None:
            self._agent_registry = HACSAgentRegistry()
            if self.persistence_service:
                self._agent_registry.set_persistence_service(self.persistence_service)
        return self._agent_registry

    def get_iam_registry(self) -> HACSIAMRegistry:
        """Get IAM registry with persistence integration."""
        if self._iam_registry is None:
            self._iam_registry = HACSIAMRegistry()
            if self.persistence_service:
                self._iam_registry.set_persistence_service(self.persistence_service)
        return self._iam_registry

    def get_tool_registry(self) -> HACSToolRegistry:
        """Get tool registry with persistence integration."""
        if self._tool_registry is None:
            self._tool_registry = HACSToolRegistry()
            if self.persistence_service:
                self._tool_registry.set_persistence_service(self.persistence_service)
        return self._tool_registry


# Global integration instance
_registry_integration = RegistryPersistenceIntegration()


def configure_registry_persistence(persistence_provider: PersistenceProvider):
    """Configure persistence for all HACS registries."""
    global _registry_integration
    _registry_integration.configure_persistence(persistence_provider)
    logger.info("Registry persistence integration configured")


def get_registry_integration() -> RegistryPersistenceIntegration:
    """Get the global registry integration instance."""
    return _registry_integration


# Convenience functions that use the integration
def get_persistent_resource_registry() -> HACSResourceRegistry:
    """Get resource registry with persistence support."""
    return _registry_integration.get_resource_registry()


def get_persistent_agent_registry() -> HACSAgentRegistry:
    """Get agent registry with persistence support."""
    return _registry_integration.get_agent_registry()


def get_persistent_iam_registry() -> HACSIAMRegistry:
    """Get IAM registry with persistence support."""
    return _registry_integration.get_iam_registry()


def get_persistent_tool_registry() -> HACSToolRegistry:
    """Get tool registry with persistence support."""
    return _registry_integration.get_tool_registry()


__all__ = [
    "RegistryPersistenceService",
    "RegistryRepositoryWrapper",
    "RegistryPersistenceIntegration",
    "configure_registry_persistence",
    "get_registry_integration",
    "get_persistent_resource_registry",
    "get_persistent_agent_registry",
    "get_persistent_iam_registry",
    "get_persistent_tool_registry",
]