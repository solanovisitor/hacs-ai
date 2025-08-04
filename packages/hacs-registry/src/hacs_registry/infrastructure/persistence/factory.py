"""
Persistence Factory Following SOLID Principles

This module provides factory classes for creating persistence-related objects,
implementing the Factory pattern to promote loose coupling and extensibility.

SOLID Compliance:
- S: Single Responsibility - Each factory creates one type of object
- O: Open/Closed - Extensible through factory registration
- L: Liskov Substitution - All created objects implement their contracts
- I: Interface Segregation - Focused factory interfaces
- D: Dependency Inversion - Factories create abstractions
"""

import logging
from pathlib import Path
from typing import Dict, Type, Any, Optional

from .adapters import PersistenceAdapter, MemoryAdapter, FileAdapter, DatabaseAdapter
from .repositories import (
    BaseRepository, InMemoryResourceRepository, InMemoryAgentRepository,
    InMemoryIAMRepository, InMemoryToolRepository
)

logger = logging.getLogger(__name__)


class PersistenceFactory:
    """
    Factory for creating persistence components.
    
    SOLID Compliance:
    - S: Single responsibility - creates persistence objects
    - O: Open/closed - extensible through registration
    - D: Dependency inversion - creates abstractions
    """
    
    _adapter_types = {
        "memory": MemoryAdapter,
        "file": FileAdapter,
        "database": DatabaseAdapter,
    }
    
    _repository_types = {
        "resource": InMemoryResourceRepository,
        "agent": InMemoryAgentRepository,
        "iam": InMemoryIAMRepository,
        "tool": InMemoryToolRepository,
    }
    
    @classmethod
    def create_adapter(cls, adapter_type: str, **config) -> PersistenceAdapter:
        """Create a persistence adapter of the specified type."""
        if adapter_type not in cls._adapter_types:
            raise ValueError(f"Unknown adapter type: {adapter_type}")
        
        adapter_class = cls._adapter_types[adapter_type]
        
        if adapter_type == "memory":
            return adapter_class()
        elif adapter_type == "file":
            base_path = config.get("base_path", "./data")
            file_format = config.get("file_format", "json")
            return adapter_class(Path(base_path), file_format)
        elif adapter_type == "database":
            connection_string = config.get("connection_string", "")
            database_type = config.get("database_type", "postgresql")
            return adapter_class(connection_string, database_type)
        else:
            return adapter_class(**config)
    
    @classmethod
    def create_repository(cls, repository_type: str, adapter: PersistenceAdapter) -> BaseRepository:
        """Create a repository of the specified type."""
        if repository_type not in cls._repository_types:
            raise ValueError(f"Unknown repository type: {repository_type}")
        
        repository_class = cls._repository_types[repository_type]
        return repository_class(adapter)
    
    @classmethod
    def register_adapter_type(cls, adapter_type: str, adapter_class: Type[PersistenceAdapter]):
        """Register a new adapter type."""
        cls._adapter_types[adapter_type] = adapter_class
        logger.info(f"Registered adapter type: {adapter_type}")
    
    @classmethod
    def register_repository_type(cls, repository_type: str, repository_class: Type[BaseRepository]):
        """Register a new repository type."""
        cls._repository_types[repository_type] = repository_class
        logger.info(f"Registered repository type: {repository_type}")
    
    @classmethod
    def get_supported_adapters(cls) -> list[str]:
        """Get list of supported adapter types."""
        return list(cls._adapter_types.keys())
    
    @classmethod
    def get_supported_repositories(cls) -> list[str]:
        """Get list of supported repository types."""
        return list(cls._repository_types.keys())


class PersistenceManager:
    """
    Manager for coordinating persistence operations across repositories.
    
    SOLID Compliance:
    - S: Single responsibility - manages persistence coordination
    - O: Open/closed - extensible through repository registration
    - D: Dependency inversion - depends on repository abstractions
    """
    
    def __init__(self, adapter: PersistenceAdapter):
        self.adapter = adapter
        self._repositories: Dict[str, BaseRepository] = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the persistence manager."""
        if not self._initialized:
            await self.adapter.initialize()
            self._initialized = True
            logger.info("Persistence manager initialized")
    
    async def cleanup(self) -> None:
        """Clean up persistence resources."""
        if self._initialized:
            await self.adapter.cleanup()
            self._repositories.clear()
            self._initialized = False
            logger.info("Persistence manager cleaned up")
    
    def get_repository(self, repository_type: str) -> BaseRepository:
        """Get or create a repository of the specified type."""
        if repository_type not in self._repositories:
            self._repositories[repository_type] = PersistenceFactory.create_repository(
                repository_type, self.adapter
            )
        return self._repositories[repository_type]
    
    def register_repository(self, repository_type: str, repository: BaseRepository) -> None:
        """Register a custom repository instance."""
        self._repositories[repository_type] = repository
        logger.info(f"Registered custom repository: {repository_type}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the persistence layer."""
        try:
            # Test basic adapter operations
            from ...core import EntityId
            test_id = EntityId.generate()
            test_data = {"test": "health_check"}
            
            # Save and load test data
            await self.adapter.save("HealthCheck", test_id, test_data)
            loaded = await self.adapter.load("HealthCheck", test_id)
            await self.adapter.delete("HealthCheck", test_id)
            
            return {
                "status": "healthy",
                "adapter_type": type(self.adapter).__name__,
                "repositories": list(self._repositories.keys()),
                "operations_working": loaded is not None
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "adapter_type": type(self.adapter).__name__,
                "repositories": list(self._repositories.keys())
            }


# Convenience functions for common patterns

def create_memory_persistence() -> PersistenceManager:
    """Create a memory-based persistence manager."""
    adapter = PersistenceFactory.create_adapter("memory")
    return PersistenceManager(adapter)


def create_file_persistence(base_path: str = "./data", file_format: str = "json") -> PersistenceManager:
    """Create a file-based persistence manager."""
    adapter = PersistenceFactory.create_adapter("file", base_path=base_path, file_format=file_format)
    return PersistenceManager(adapter)


def create_database_persistence(connection_string: str, database_type: str = "postgresql") -> PersistenceManager:
    """Create a database-based persistence manager."""
    adapter = PersistenceFactory.create_adapter("database", 
                                                connection_string=connection_string,
                                                database_type=database_type)
    return PersistenceManager(adapter)