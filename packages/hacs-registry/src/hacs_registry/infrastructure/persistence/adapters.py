"""
Persistence Adapters Following SOLID Principles

This module implements the Adapter pattern for different persistence mechanisms,
allowing the repository layer to be decoupled from specific storage technologies.

SOLID Compliance:
- S: Single Responsibility - Each adapter handles one storage type
- O: Open/Closed - New storage types via new adapters
- L: Liskov Substitution - All adapters implement same interface
- I: Interface Segregation - Focused adapter interfaces
- D: Dependency Inversion - Adapters implement abstract interfaces
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar
try:
    import aiofiles
    HAS_AIOFILES = True
except ImportError:
    HAS_AIOFILES = False
    # Fallback for environments without aiofiles
    class MockAioFiles:
        @staticmethod
        def open(*args, **kwargs):
            raise ImportError("aiofiles not available - install with: pip install aiofiles")
    aiofiles = MockAioFiles()

from ...core.base import EntityId, AggregateRoot
from ...core.exceptions import PersistenceException

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=AggregateRoot)


class PersistenceAdapter(ABC):
    """
    Abstract base class for persistence adapters.
    
    SOLID Compliance:
    - S: Single responsibility - defines persistence contract
    - I: Interface segregation - minimal persistence interface
    - D: Dependency inversion - abstraction for all storage types
    """
    
    @abstractmethod
    async def save(self, aggregate_type: str, aggregate_id: EntityId, data: Dict[str, Any]) -> Dict[str, Any]:
        """Save aggregate data."""
        pass
    
    @abstractmethod
    async def load(self, aggregate_type: str, aggregate_id: EntityId) -> Optional[Dict[str, Any]]:
        """Load aggregate data."""
        pass
    
    @abstractmethod
    async def delete(self, aggregate_type: str, aggregate_id: EntityId) -> bool:
        """Delete aggregate data."""
        pass
    
    @abstractmethod
    async def exists(self, aggregate_type: str, aggregate_id: EntityId) -> bool:
        """Check if aggregate exists."""
        pass
    
    @abstractmethod
    async def list_all(self, aggregate_type: str, limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
        """List all aggregates of given type."""
        pass
    
    @abstractmethod
    async def find_by_criteria(self, aggregate_type: str, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find aggregates matching criteria."""
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the adapter."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources."""
        pass


class MemoryAdapter(PersistenceAdapter):
    """
    In-memory persistence adapter for development and testing.
    
    SOLID Compliance:
    - S: Single responsibility - in-memory storage only
    - L: Liskov substitution - implements PersistenceAdapter contract
    """
    
    def __init__(self):
        self._data: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the memory adapter."""
        if not self._initialized:
            self._data = {}
            self._initialized = True
            logger.info("Memory adapter initialized")
    
    async def save(self, aggregate_type: str, aggregate_id: EntityId, data: Dict[str, Any]) -> Dict[str, Any]:
        """Save data to memory."""
        if not self._initialized:
            await self.initialize()
        
        if aggregate_type not in self._data:
            self._data[aggregate_type] = {}
        
        # Add metadata
        enriched_data = {
            **data,
            "_saved_at": datetime.now(timezone.utc).isoformat(),
            "_aggregate_id": aggregate_id.value,
            "_aggregate_type": aggregate_type
        }
        
        self._data[aggregate_type][aggregate_id.value] = enriched_data
        logger.debug(f"Saved {aggregate_type}:{aggregate_id.value} to memory")
        return enriched_data
    
    async def load(self, aggregate_type: str, aggregate_id: EntityId) -> Optional[Dict[str, Any]]:
        """Load data from memory."""
        if not self._initialized:
            await self.initialize()
        
        return self._data.get(aggregate_type, {}).get(aggregate_id.value)
    
    async def delete(self, aggregate_type: str, aggregate_id: EntityId) -> bool:
        """Delete data from memory."""
        if not self._initialized:
            await self.initialize()
        
        if aggregate_type in self._data and aggregate_id.value in self._data[aggregate_type]:
            del self._data[aggregate_type][aggregate_id.value]
            logger.debug(f"Deleted {aggregate_type}:{aggregate_id.value} from memory")
            return True
        return False
    
    async def exists(self, aggregate_type: str, aggregate_id: EntityId) -> bool:
        """Check if data exists in memory."""
        if not self._initialized:
            await self.initialize()
        
        return aggregate_id.value in self._data.get(aggregate_type, {})
    
    async def list_all(self, aggregate_type: str, limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
        """List all data of given type from memory."""
        if not self._initialized:
            await self.initialize()
        
        all_data = list(self._data.get(aggregate_type, {}).values())
        
        # Apply pagination
        if offset > 0:
            all_data = all_data[offset:]
        if limit is not None:
            all_data = all_data[:limit]
        
        return all_data
    
    async def find_by_criteria(self, aggregate_type: str, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find data matching criteria in memory."""
        if not self._initialized:
            await self.initialize()
        
        all_data = self._data.get(aggregate_type, {}).values()
        matched = []
        
        for data in all_data:
            match = True
            for key, value in criteria.items():
                if key not in data or data[key] != value:
                    match = False
                    break
            if match:
                matched.append(data)
        
        return matched
    
    async def cleanup(self) -> None:
        """Clean up memory."""
        self._data.clear()
        self._initialized = False
        logger.info("Memory adapter cleaned up")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory adapter statistics."""
        stats = {
            "total_types": len(self._data),
            "by_type": {}
        }
        
        for aggregate_type, type_data in self._data.items():
            stats["by_type"][aggregate_type] = len(type_data)
        
        return stats


class FileAdapter(PersistenceAdapter):
    """
    File-based persistence adapter using JSON files.
    
    SOLID Compliance:
    - S: Single responsibility - file storage only
    - L: Liskov substitution - implements PersistenceAdapter contract
    """
    
    def __init__(self, base_path: Path, file_format: str = "json"):
        self.base_path = Path(base_path)
        self.file_format = file_format.lower()
        self._initialized = False
        
        if self.file_format not in ["json", "yaml"]:
            raise ValueError(f"Unsupported file format: {file_format}")
        
        if not HAS_AIOFILES:
            logger.warning("aiofiles not available - file operations will be synchronous")
    
    async def initialize(self) -> None:
        """Initialize the file adapter."""
        if not self._initialized:
            self.base_path.mkdir(parents=True, exist_ok=True)
            self._initialized = True
            logger.info(f"File adapter initialized at {self.base_path}")
    
    def _get_file_path(self, aggregate_type: str, aggregate_id: EntityId) -> Path:
        """Get file path for an aggregate."""
        type_dir = self.base_path / aggregate_type.lower()
        type_dir.mkdir(exist_ok=True)
        return type_dir / f"{aggregate_id.value}.{self.file_format}"
    
    def _get_index_path(self, aggregate_type: str) -> Path:
        """Get index file path for an aggregate type."""
        return self.base_path / f"{aggregate_type.lower()}_index.{self.file_format}"
    
    async def _load_json(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load JSON data from file."""
        try:
            if not file_path.exists():
                return None
            
            if HAS_AIOFILES:
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    return json.loads(content) if content.strip() else None
            else:
                # Fallback to synchronous file operations
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    return json.loads(content) if content.strip() else None
        except Exception as e:
            logger.error(f"Failed to load JSON from {file_path}: {e}")
            return None
    
    async def _save_json(self, file_path: Path, data: Dict[str, Any]) -> None:
        """Save JSON data to file."""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            if HAS_AIOFILES:
                async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(data, indent=2, default=str))
            else:
                # Fallback to synchronous file operations
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(json.dumps(data, indent=2, default=str))
        except Exception as e:
            logger.error(f"Failed to save JSON to {file_path}: {e}")
            raise PersistenceException(f"File save failed: {e}", operation="save")
    
    async def _update_index(self, aggregate_type: str, aggregate_id: EntityId, operation: str = "add"):
        """Update the index file for an aggregate type."""
        index_path = self._get_index_path(aggregate_type)
        index_data = await self._load_json(index_path) or {"items": [], "updated_at": None}
        
        if operation == "add":
            if aggregate_id.value not in index_data["items"]:
                index_data["items"].append(aggregate_id.value)
        elif operation == "remove":
            if aggregate_id.value in index_data["items"]:
                index_data["items"].remove(aggregate_id.value)
        
        index_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await self._save_json(index_path, index_data)
    
    async def save(self, aggregate_type: str, aggregate_id: EntityId, data: Dict[str, Any]) -> Dict[str, Any]:
        """Save data to file."""
        if not self._initialized:
            await self.initialize()
        
        file_path = self._get_file_path(aggregate_type, aggregate_id)
        
        # Add metadata
        enriched_data = {
            **data,
            "_saved_at": datetime.now(timezone.utc).isoformat(),
            "_aggregate_id": aggregate_id.value,
            "_aggregate_type": aggregate_type,
            "_file_path": str(file_path)
        }
        
        await self._save_json(file_path, enriched_data)
        await self._update_index(aggregate_type, aggregate_id, "add")
        
        logger.debug(f"Saved {aggregate_type}:{aggregate_id.value} to {file_path}")
        return enriched_data
    
    async def load(self, aggregate_type: str, aggregate_id: EntityId) -> Optional[Dict[str, Any]]:
        """Load data from file."""
        if not self._initialized:
            await self.initialize()
        
        file_path = self._get_file_path(aggregate_type, aggregate_id)
        return await self._load_json(file_path)
    
    async def delete(self, aggregate_type: str, aggregate_id: EntityId) -> bool:
        """Delete data file."""
        if not self._initialized:
            await self.initialize()
        
        file_path = self._get_file_path(aggregate_type, aggregate_id)
        
        try:
            if file_path.exists():
                file_path.unlink()
                await self._update_index(aggregate_type, aggregate_id, "remove")
                logger.debug(f"Deleted {aggregate_type}:{aggregate_id.value} from {file_path}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete {file_path}: {e}")
            raise PersistenceException(f"File delete failed: {e}", operation="delete")
        
        return False
    
    async def exists(self, aggregate_type: str, aggregate_id: EntityId) -> bool:
        """Check if data file exists."""
        if not self._initialized:
            await self.initialize()
        
        file_path = self._get_file_path(aggregate_type, aggregate_id)
        return file_path.exists()
    
    async def list_all(self, aggregate_type: str, limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
        """List all data of given type from files."""
        if not self._initialized:
            await self.initialize()
        
        index_path = self._get_index_path(aggregate_type)
        index_data = await self._load_json(index_path)
        
        if not index_data or "items" not in index_data:
            return []
        
        items = index_data["items"][offset:]
        if limit is not None:
            items = items[:limit]
        
        results = []
        for item_id in items:
            data = await self.load(aggregate_type, EntityId(item_id))
            if data:
                results.append(data)
        
        return results
    
    async def find_by_criteria(self, aggregate_type: str, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find data matching criteria in files."""
        all_data = await self.list_all(aggregate_type)
        matched = []
        
        for data in all_data:
            match = True
            for key, value in criteria.items():
                if key not in data or data[key] != value:
                    match = False
                    break
            if match:
                matched.append(data)
        
        return matched
    
    async def cleanup(self) -> None:
        """Clean up file resources."""
        # For file adapter, cleanup means removing lock files, temp files, etc.
        # We don't delete the actual data files
        self._initialized = False
        logger.info("File adapter cleaned up")


class DatabaseAdapter(PersistenceAdapter):
    """
    Database persistence adapter (placeholder for SQL/NoSQL databases).
    
    SOLID Compliance:
    - S: Single responsibility - database storage only
    - L: Liskov substitution - implements PersistenceAdapter contract
    """
    
    def __init__(self, connection_string: str, database_type: str = "postgresql"):
        self.connection_string = connection_string
        self.database_type = database_type
        self._connection = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize database connection."""
        if not self._initialized:
            # TODO: Implement actual database connection
            # This is a placeholder for now
            logger.info(f"Database adapter initialized ({self.database_type})")
            self._initialized = True
    
    async def save(self, aggregate_type: str, aggregate_id: EntityId, data: Dict[str, Any]) -> Dict[str, Any]:
        """Save data to database."""
        if not self._initialized:
            await self.initialize()
        
        # TODO: Implement actual database save
        enriched_data = {
            **data,
            "_saved_at": datetime.now(timezone.utc).isoformat(),
            "_aggregate_id": aggregate_id.value,
            "_aggregate_type": aggregate_type
        }
        
        logger.debug(f"Would save {aggregate_type}:{aggregate_id.value} to database")
        return enriched_data
    
    async def load(self, aggregate_type: str, aggregate_id: EntityId) -> Optional[Dict[str, Any]]:
        """Load data from database."""
        if not self._initialized:
            await self.initialize()
        
        # TODO: Implement actual database load
        logger.debug(f"Would load {aggregate_type}:{aggregate_id.value} from database")
        return None
    
    async def delete(self, aggregate_type: str, aggregate_id: EntityId) -> bool:
        """Delete data from database."""
        if not self._initialized:
            await self.initialize()
        
        # TODO: Implement actual database delete
        logger.debug(f"Would delete {aggregate_type}:{aggregate_id.value} from database")
        return False
    
    async def exists(self, aggregate_type: str, aggregate_id: EntityId) -> bool:
        """Check if data exists in database."""
        if not self._initialized:
            await self.initialize()
        
        # TODO: Implement actual database exists check
        return False
    
    async def list_all(self, aggregate_type: str, limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
        """List all data from database."""
        if not self._initialized:
            await self.initialize()
        
        # TODO: Implement actual database list
        return []
    
    async def find_by_criteria(self, aggregate_type: str, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find data matching criteria in database."""
        if not self._initialized:
            await self.initialize()
        
        # TODO: Implement actual database search
        return []
    
    async def cleanup(self) -> None:
        """Clean up database connection."""
        if self._connection:
            # TODO: Close actual database connection
            self._connection = None
        self._initialized = False
        logger.info("Database adapter cleaned up")


# Adapter Factory (Factory Pattern + SOLID)

class AdapterFactory:
    """
    Factory for creating persistence adapters.
    
    SOLID Compliance:
    - S: Single responsibility - creates adapters
    - O: Open/closed - new adapter types via registration
    - D: Dependency inversion - depends on adapter abstractions
    """
    
    _adapters = {
        "memory": MemoryAdapter,
        "file": FileAdapter,
        "database": DatabaseAdapter,
    }
    
    @classmethod
    def create(cls, adapter_type: str, **config) -> PersistenceAdapter:
        """Create a persistence adapter of the specified type."""
        if adapter_type not in cls._adapters:
            raise ValueError(f"Unknown adapter type: {adapter_type}")
        
        adapter_class = cls._adapters[adapter_type]
        
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
    def register_adapter(cls, adapter_type: str, adapter_class: Type[PersistenceAdapter]):
        """Register a new adapter type."""
        cls._adapters[adapter_type] = adapter_class
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """Get list of supported adapter types."""
        return list(cls._adapters.keys())