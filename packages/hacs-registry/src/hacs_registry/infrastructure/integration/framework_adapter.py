"""
Framework Integration Adapter Following SOLID Principles

This module provides base adapters for integrating HACS with various frameworks.

SOLID Compliance:
- S: Single Responsibility - Handles framework integration contracts
- O: Open/Closed - Extensible for new frameworks
- L: Liskov Substitution - All adapters implement base contract
- I: Interface Segregation - Focused framework interfaces
- D: Dependency Inversion - Depends on abstractions
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ...core.base import EntityId
from ...core.exceptions import InfrastructureException

logger = logging.getLogger(__name__)


class FrameworkAdapter(ABC):
    """
    Base class for framework adapters.
    
    SOLID Compliance:
    - S: Single responsibility - defines framework integration contract
    - O: Open/closed - extensible for new framework types
    - I: Interface segregation - minimal framework interface
    """
    
    def __init__(self, framework_name: str):
        self.framework_name = framework_name
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{framework_name}")
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the framework adapter."""
        pass
    
    @abstractmethod
    async def convert_resource(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Convert HACS resource to framework-specific format."""
        pass
    
    @abstractmethod
    async def create_integration(self, config: Dict[str, Any]) -> Any:
        """Create framework integration."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up framework resources."""
        pass
    
    def is_initialized(self) -> bool:
        """Check if adapter is initialized."""
        return self._initialized


class GenericFrameworkAdapter(FrameworkAdapter):
    """
    Generic framework adapter for unknown frameworks.
    
    SOLID Compliance:
    - S: Single responsibility - handles generic framework integration
    - L: Liskov substitution - implements FrameworkAdapter contract
    """
    
    def __init__(self, framework_name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(framework_name)
        self.config = config or {}
    
    async def initialize(self) -> None:
        """Initialize the generic framework adapter."""
        if not self._initialized:
            self._initialized = True
            self.logger.info(f"Generic framework adapter initialized: {self.framework_name}")
    
    async def convert_resource(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Convert HACS resource to generic format."""
        try:
            # Generic conversion - just pass through with metadata
            converted = {
                "source": "hacs",
                "framework": self.framework_name,
                "resource": resource,
                "converted_at": "2024-01-01T00:00:00Z"  # Placeholder timestamp
            }
            
            self.logger.debug(f"Converted resource for {self.framework_name}")
            return converted
            
        except Exception as e:
            self.logger.error(f"Failed to convert resource for {self.framework_name}: {e}")
            raise InfrastructureException(f"Resource conversion failed: {e}")
    
    async def create_integration(self, config: Dict[str, Any]) -> Any:
        """Create generic framework integration."""
        try:
            integration = {
                "framework": self.framework_name,
                "config": config,
                "status": "created",
                "type": "generic"
            }
            
            self.logger.info(f"Created integration for {self.framework_name}")
            return integration
            
        except Exception as e:
            self.logger.error(f"Failed to create integration for {self.framework_name}: {e}")
            raise InfrastructureException(f"Integration creation failed: {e}")
    
    async def cleanup(self) -> None:
        """Clean up generic framework resources."""
        self._initialized = False
        self.logger.info(f"Generic framework adapter cleaned up: {self.framework_name}")