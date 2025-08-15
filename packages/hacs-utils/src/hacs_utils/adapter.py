"""
Adapter base classes for external integrations.

Concrete framework-specific adapters (e.g., CrewAI) live under
`hacs_utils.integrations.*`. This module provides common adapter base types.
"""

import uuid
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AdapterConfig(BaseModel):
    """Base configuration for external adapters."""

    name: str = Field(description="Adapter name")
    version: str = Field(default="1.0.0", description="Adapter version")
    enabled: bool = Field(default=True, description="Whether adapter is enabled")
    config: dict[str, Any] = Field(default_factory=dict, description="Adapter-specific configuration")


class AbstractAdapter(ABC):
    """Abstract base class for external service adapters."""

    def __init__(self, config: AdapterConfig):
        """Initialize adapter with configuration."""
        self.config = config

    @abstractmethod
    def connect(self) -> bool:
        """Connect to external service."""
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from external service."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the adapter is healthy."""
        pass


class AdapterNotImplemented(RuntimeError):
    """Raised when an adapter method is not implemented by a subclass."""
    pass


class AdapterBinding(BaseModel):
    """Generic binding for adapter-managed entities (override per integration)."""
    binding_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AdapterStub:
    """Stub base for adapters. Use concrete integrations under hacs_utils.integrations.*"""
    pass
