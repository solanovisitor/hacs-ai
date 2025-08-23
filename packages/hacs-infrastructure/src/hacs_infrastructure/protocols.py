"""Protocols and interfaces for HACS infrastructure components.

This module defines the fundamental protocols that establish contracts
for infrastructure components, following SOLID design principles.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class ComponentStatus(str, Enum):
    """Status of infrastructure components."""

    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    UNKNOWN = "unknown"


@runtime_checkable
class Configurable(Protocol):
    """Protocol for components that can be configured."""

    def configure(self, config: dict[str, Any]) -> None:
        """Configure the component with settings."""
        ...

    def get_config(self) -> dict[str, Any]:
        """Get current configuration."""
        ...


@runtime_checkable
class HealthCheckable(Protocol):
    """Protocol for components that support health checking."""

    def health_check(self) -> bool:
        """Perform health check.

        Returns:
            True if component is healthy, False otherwise
        """
        ...

    def get_health_details(self) -> dict[str, Any]:
        """Get detailed health information.

        Returns:
            Dictionary with health details
        """
        ...


@runtime_checkable
class Startable(Protocol):
    """Protocol for components that can be started."""

    async def start(self) -> None:
        """Start the component."""
        ...

    def get_status(self) -> ComponentStatus:
        """Get current component status."""
        ...


@runtime_checkable
class Stoppable(Protocol):
    """Protocol for components that can be stopped."""

    async def stop(self) -> None:
        """Stop the component."""
        ...

    async def graceful_shutdown(self, timeout: float = 30.0) -> None:
        """Perform graceful shutdown with timeout."""
        ...


@runtime_checkable
class Injectable(Protocol):
    """Protocol for components that support dependency injection."""

    def inject_dependencies(self, **dependencies: Any) -> None:
        """Inject dependencies into the component."""
        ...

    def get_dependencies(self) -> list[type]:
        """Get list of required dependency types."""
        ...


@runtime_checkable
class Disposable(Protocol):
    """Protocol for components that need cleanup."""

    def dispose(self) -> None:
        """Clean up resources used by the component."""
        ...


@runtime_checkable
class Observable(Protocol):
    """Protocol for components that can be observed/monitored."""

    def get_metrics(self) -> dict[str, Any]:
        """Get component metrics."""
        ...

    def get_events(self) -> list[dict[str, Any]]:
        """Get recent events from the component."""
        ...


@runtime_checkable
class Cacheable(Protocol):
    """Protocol for components that support caching."""

    def cache_get(self, key: str) -> Any:
        """Get value from cache."""
        ...

    def cache_set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache with optional TTL."""
        ...

    def cache_delete(self, key: str) -> None:
        """Delete value from cache."""
        ...

    def cache_clear(self) -> None:
        """Clear all cached values."""
        ...


class ServiceProvider(ABC):
    """Abstract base class for service providers."""

    @abstractmethod
    def get_name(self) -> str:
        """Get service provider name."""

    @abstractmethod
    def get_version(self) -> str:
        """Get service provider version."""

    @abstractmethod
    def initialize(self, config: dict[str, Any]) -> None:
        """Initialize the service provider."""

    @abstractmethod
    def health_check(self) -> bool:
        """Check if service provider is healthy."""


class LLMProvider(ServiceProvider):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text using the LLM."""

    @abstractmethod
    async def generate_embeddings(
        self, texts: list[str], model: str | None = None, **kwargs: Any
    ) -> list[list[float]]:
        """Generate embeddings for texts."""

    @abstractmethod
    def get_available_models(self) -> list[str]:
        """Get list of available models."""


class VectorStore(ServiceProvider):
    """Abstract base class for vector stores."""

    @abstractmethod
    async def create_collection(
        self, name: str, dimension: int, distance_metric: str = "cosine"
    ) -> None:
        """Create a new collection."""

    @abstractmethod
    async def insert_vectors(
        self,
        collection: str,
        vectors: list[list[float]],
        ids: list[str],
        metadata: list[dict[str, Any]] | None = None,
    ) -> None:
        """Insert vectors into collection."""

    @abstractmethod
    async def search_vectors(
        self,
        collection: str,
        query_vector: list[float],
        limit: int = 10,
        filter_expr: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors."""

    @abstractmethod
    async def delete_vectors(self, collection: str, ids: list[str]) -> None:
        """Delete vectors by IDs."""


class PersistenceProvider(ServiceProvider):
    """Abstract base class for persistence providers."""

    @abstractmethod
    async def save(self, key: str, data: Any) -> None:
        """Save data with key."""

    @abstractmethod
    async def load(self, key: str) -> Any:
        """Load data by key."""

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete data by key."""

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists."""

    @abstractmethod
    async def list_keys(self, prefix: str | None = None) -> list[str]:
        """List all keys with optional prefix filter."""


class EventBusProvider(ServiceProvider):
    """Abstract base class for event bus providers."""

    @abstractmethod
    async def publish(self, topic: str, event: dict[str, Any]) -> None:
        """Publish event to topic."""

    @abstractmethod
    async def subscribe(self, topic: str, handler: callable) -> str:
        """Subscribe to topic with handler. Returns subscription ID."""

    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from topic."""


class AgentFramework(ServiceProvider):
    """Abstract base class for agent frameworks."""

    @abstractmethod
    async def create_agent(self, name: str, config: dict[str, Any]) -> str:
        """Create new agent. Returns agent ID."""

    @abstractmethod
    async def execute_agent(self, agent_id: str, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute agent with input data."""

    @abstractmethod
    async def get_agent_status(self, agent_id: str) -> dict[str, Any]:
        """Get agent status and metadata."""

    @abstractmethod
    async def delete_agent(self, agent_id: str) -> None:
        """Delete agent."""


@runtime_checkable
class AdapterProtocol(Protocol):
    """Protocol for HACS adapters."""

    @property
    def name(self) -> str:
        """Adapter name."""
        ...

    @property
    def version(self) -> str:
        """Adapter version."""
        ...

    def health_check(self) -> bool:
        """Check adapter health."""
        ...

    def get_config(self) -> dict[str, Any]:
        """Get adapter configuration."""
        ...


@runtime_checkable
class MiddlewareProtocol(Protocol):
    """Protocol for middleware components."""

    async def process_request(self, request: Any) -> Any:
        """Process incoming request."""
        ...

    async def process_response(self, response: Any) -> Any:
        """Process outgoing response."""
        ...

    def get_priority(self) -> int:
        """Get middleware priority (lower = higher priority)."""
        ...


@runtime_checkable
class ValidatorProtocol(Protocol):
    """Protocol for validators."""

    def validate(self, data: Any) -> list[str]:
        """Validate data and return list of errors.

        Args:
            data: Data to validate

        Returns:
            List of validation errors (empty if valid)
        """
        ...

    def is_valid(self, data: Any) -> bool:
        """Check if data is valid.

        Args:
            data: Data to validate

        Returns:
            True if data is valid
        """
        ...


@runtime_checkable
class SerializerProtocol(Protocol):
    """Protocol for serializers."""

    def serialize(self, obj: Any) -> str:
        """Serialize object to string."""
        ...

    def deserialize(self, data: str, obj_type: type) -> Any:
        """Deserialize string to object of specified type."""
        ...

    def get_content_type(self) -> str:
        """Get content type for serialized data."""
        ...
