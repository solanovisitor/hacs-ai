"""
Protocols and interfaces for HACS infrastructure components.

This module defines the fundamental protocols that establish contracts
for infrastructure components, following SOLID design principles.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from enum import Enum


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
    
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the component with settings."""
        ...
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        ...


@runtime_checkable
class HealthCheckable(Protocol):
    """Protocol for components that support health checking."""
    
    def health_check(self) -> bool:
        """
        Perform health check.
        
        Returns:
            True if component is healthy, False otherwise
        """
        ...
    
    def get_health_details(self) -> Dict[str, Any]:
        """
        Get detailed health information.
        
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
    
    def get_dependencies(self) -> List[type]:
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
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get component metrics."""
        ...
    
    def get_events(self) -> List[Dict[str, Any]]:
        """Get recent events from the component."""
        ...


@runtime_checkable
class Cacheable(Protocol):
    """Protocol for components that support caching."""
    
    def cache_get(self, key: str) -> Any:
        """Get value from cache."""
        ...
    
    def cache_set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
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
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """Get service provider version."""
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the service provider."""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if service provider is healthy."""
        pass


class LLMProvider(ServiceProvider):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        """Generate text using the LLM."""
        pass
    
    @abstractmethod
    async def generate_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None,
        **kwargs: Any
    ) -> List[List[float]]:
        """Generate embeddings for texts."""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        pass


class VectorStore(ServiceProvider):
    """Abstract base class for vector stores."""
    
    @abstractmethod
    async def create_collection(
        self,
        name: str,
        dimension: int,
        distance_metric: str = "cosine"
    ) -> None:
        """Create a new collection."""
        pass
    
    @abstractmethod
    async def insert_vectors(
        self,
        collection: str,
        vectors: List[List[float]],
        ids: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Insert vectors into collection."""
        pass
    
    @abstractmethod
    async def search_vectors(
        self,
        collection: str,
        query_vector: List[float],
        limit: int = 10,
        filter_expr: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        pass
    
    @abstractmethod
    async def delete_vectors(
        self,
        collection: str,
        ids: List[str]
    ) -> None:
        """Delete vectors by IDs."""
        pass


class PersistenceProvider(ServiceProvider):
    """Abstract base class for persistence providers."""
    
    @abstractmethod
    async def save(self, key: str, data: Any) -> None:
        """Save data with key."""
        pass
    
    @abstractmethod
    async def load(self, key: str) -> Any:
        """Load data by key."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete data by key."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass
    
    @abstractmethod
    async def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List all keys with optional prefix filter."""
        pass


class EventBusProvider(ServiceProvider):
    """Abstract base class for event bus providers."""
    
    @abstractmethod
    async def publish(self, topic: str, event: Dict[str, Any]) -> None:
        """Publish event to topic."""
        pass
    
    @abstractmethod
    async def subscribe(self, topic: str, handler: callable) -> str:
        """Subscribe to topic with handler. Returns subscription ID."""
        pass
    
    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from topic."""
        pass


class AgentFramework(ServiceProvider):
    """Abstract base class for agent frameworks."""
    
    @abstractmethod
    async def create_agent(
        self,
        name: str,
        config: Dict[str, Any]
    ) -> str:
        """Create new agent. Returns agent ID."""
        pass
    
    @abstractmethod
    async def execute_agent(
        self,
        agent_id: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute agent with input data."""
        pass
    
    @abstractmethod
    async def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get agent status and metadata."""
        pass
    
    @abstractmethod
    async def delete_agent(self, agent_id: str) -> None:
        """Delete agent."""
        pass


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
    
    def get_config(self) -> Dict[str, Any]:
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
    
    def validate(self, data: Any) -> List[str]:
        """
        Validate data and return list of errors.
        
        Args:
            data: Data to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        ...
    
    def is_valid(self, data: Any) -> bool:
        """
        Check if data is valid.
        
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