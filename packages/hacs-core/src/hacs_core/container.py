"""
HACS Dependency Injection Container

This module provides a simple dependency injection container for managing
HACS adapters and their dependencies.
"""

import logging
from typing import TypeVar

from .config import get_settings
from .protocols import (
    AgentFramework,
    BaseAdapter,
    LLMProvider,
    PersistenceProvider,
    VectorStore,
)

T = TypeVar("T", bound=BaseAdapter)

logger = logging.getLogger(__name__)


class AdapterNotFoundError(Exception):
    """Raised when a requested adapter is not found."""

    pass


class AdapterRegistry:
    """Registry for HACS adapters with dependency injection."""

    def __init__(self):
        self._adapters: dict[type, BaseAdapter] = {}
        self._factories: dict[type, callable] = {}
        self._initialized = False

    def register_adapter(self, protocol: type[T], adapter: T) -> None:
        """Register an adapter instance for a protocol.

        Args:
            protocol: The protocol interface (e.g., LLMProvider)
            adapter: The adapter instance implementing the protocol
        """
        self._adapters[protocol] = adapter

    def register_factory(self, protocol: type[T], factory: callable) -> None:
        """Register a factory function for creating adapters.

        Args:
            protocol: The protocol interface
            factory: A callable that returns an adapter instance
        """
        self._factories[protocol] = factory

    def get_adapter(self, protocol: type[T]) -> T:
        """Get an adapter for the specified protocol.

        Args:
            protocol: The protocol interface to get an adapter for

        Returns:
            The adapter instance

        Raises:
            AdapterNotFoundError: If no adapter is registered for the protocol
        """
        # Return existing adapter if available
        if protocol in self._adapters:
            return self._adapters[protocol]

        # Try to create adapter using factory
        if protocol in self._factories:
            adapter = self._factories[protocol]()
            self._adapters[protocol] = adapter
            return adapter

        raise AdapterNotFoundError(
            f"No adapter registered for protocol {protocol.__name__}"
        )

    def get_llm_provider(self, provider: str = "auto") -> LLMProvider:
        """Get an LLM provider adapter.

        Args:
            provider: The provider name ("openai", "anthropic", or "auto")

        Returns:
            LLM provider adapter
        """
        if provider == "auto":
            # Auto-select based on available configuration
            settings = get_settings()
            if settings.openai_enabled:
                provider = "openai"
            elif settings.anthropic_enabled:
                provider = "anthropic"
            else:
                raise AdapterNotFoundError("No LLM provider configured")

        # Get adapter by provider name
        if provider == "openai":
            return self.get_adapter(LLMProvider)
        elif provider == "anthropic":
            return self.get_adapter(LLMProvider)
        else:
            raise AdapterNotFoundError(f"Unknown LLM provider: {provider}")

    def get_vector_store(self, store: str = "auto") -> VectorStore:
        """Get a vector store adapter.

        Args:
            store: The store name ("pinecone", "qdrant", or "auto")

        Returns:
            Vector store adapter
        """
        if store == "auto":
            # Auto-select based on available configuration
            settings = get_settings()
            if settings.pinecone_enabled:
                store = "pinecone"
            elif settings.qdrant_enabled:
                store = "qdrant"
            else:
                raise AdapterNotFoundError("No vector store configured")

        return self.get_adapter(VectorStore)

    def get_agent_framework(self, framework: str = "auto") -> AgentFramework:
        """Get an agent framework adapter.

        Args:
            framework: The framework name ("langgraph", "crewai", or "auto")

        Returns:
            Agent framework adapter
        """
        return self.get_adapter(AgentFramework)

    def initialize_default_adapters(self) -> None:
        """Initialize default adapters based on configuration.

        This method auto-configures adapters based on available settings
        and installed packages.
        """
        if self._initialized:
            return

        settings = get_settings()

        # Initialize OpenAI adapter if configured
        if settings.openai_enabled:
            try:
                from hacs_openai.adapter import create_openai_adapter

                def openai_factory():
                    return create_openai_adapter(**settings.get_openai_config())

                self.register_factory(LLMProvider, openai_factory)
            except ImportError:
                pass

        # Initialize Anthropic adapter if configured
        if settings.anthropic_enabled:
            try:
                from hacs_anthropic.adapter import create_anthropic_adapter

                def anthropic_factory():
                    return create_anthropic_adapter(**settings.get_anthropic_config())

                # Note: This would override OpenAI for LLMProvider if both are available
                # In a real implementation, you'd need a more sophisticated selection mechanism
                if not settings.openai_enabled:  # Only use if OpenAI not available
                    self.register_factory(LLMProvider, anthropic_factory)
            except ImportError:
                pass

        # Initialize Pinecone adapter if configured
        if settings.pinecone_enabled:
            try:
                # from hacs_pinecone.adapter import create_pinecone_adapter
                # self.register_factory(VectorStore, lambda: create_pinecone_adapter(**settings.get_pinecone_config()))
                pass  # Placeholder - would implement when Pinecone adapter is ready
            except ImportError:
                pass

        # Initialize Qdrant adapter if configured
        if settings.qdrant_enabled:
            try:
                # from hacs_qdrant.adapter import create_qdrant_adapter
                # self.register_factory(VectorStore, lambda: create_qdrant_adapter(**settings.get_qdrant_config()))
                pass  # Placeholder - would implement when Qdrant adapter is ready
            except ImportError:
                pass

        # Initialize PostgreSQL adapter if configured
        if settings.postgres_enabled:
            try:
                from hacs_postgres.adapter import create_postgres_adapter

                self.register_factory(
                    PersistenceProvider, lambda: create_postgres_adapter()
                )
                logger.info("PostgreSQL persistence provider registered")
            except ImportError:
                logger.warning("hacs-postgres package not available")
                pass

        self._initialized = True

    def health_check(self) -> dict[str, bool]:
        """Check the health of all registered adapters.

        Returns:
            Dictionary mapping adapter names to health status
        """
        health_status = {}

        for protocol, adapter in self._adapters.items():
            try:
                health_status[f"{protocol.__name__}:{adapter.name}"] = (
                    adapter.health_check()
                )
            except Exception:
                health_status[f"{protocol.__name__}:{adapter.name}"] = False

        return health_status

    def clear(self) -> None:
        """Clear all registered adapters and factories."""
        self._adapters.clear()
        self._factories.clear()
        self._initialized = False


# Global adapter registry
_registry: AdapterRegistry | None = None


def get_registry() -> AdapterRegistry:
    """Get the global adapter registry.

    Returns:
        The global adapter registry instance
    """
    global _registry
    if _registry is None:
        _registry = AdapterRegistry()
        _registry.initialize_default_adapters()
    return _registry


def reset_registry() -> None:
    """Reset the global adapter registry.

    Useful for testing or when configuration changes.
    """
    global _registry
    if _registry:
        _registry.clear()
    _registry = None


# Convenience functions for getting adapters
def get_llm_provider(provider: str = "auto") -> LLMProvider:
    """Get an LLM provider adapter.

    Args:
        provider: The provider name or "auto" for automatic selection

    Returns:
        LLM provider adapter
    """
    return get_registry().get_llm_provider(provider)


def get_vector_store(store: str = "auto") -> VectorStore:
    """Get a vector store adapter.

    Args:
        store: The store name or "auto" for automatic selection

    Returns:
        Vector store adapter
    """
    return get_registry().get_vector_store(store)


def get_agent_framework(framework: str = "auto") -> AgentFramework:
    """Get an agent framework adapter.

    Args:
        framework: The framework name or "auto" for automatic selection

    Returns:
        Agent framework adapter
    """
    return get_registry().get_agent_framework(framework)


def get_persistence_provider() -> PersistenceProvider:
    """
    Get the configured persistence provider adapter.

    Returns:
        The persistence provider adapter.
    """
    return get_registry().get_adapter(PersistenceProvider)


__all__ = [
    "AdapterRegistry",
    "AdapterNotFoundError",
    "get_registry",
    "reset_registry",
    "get_llm_provider",
    "get_vector_store",
    "get_agent_framework",
    "get_persistence_provider",
]
