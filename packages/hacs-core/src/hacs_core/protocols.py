"""
HACS Protocol Definitions

This module defines abstract protocols and interfaces that infrastructure
adapters must implement to integrate with HACS.
"""

from abc import ABC, abstractmethod
from typing import Any, Protocol, TypeVar, runtime_checkable

from .actor import Actor
from .base_resource import BaseResource

T = TypeVar("T", bound=BaseResource)


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for LLM provider integrations."""

    def generate_structured(
        self,
        prompt: str,
        response_model: type[BaseResource],
        actor: Actor,
        **kwargs: Any,
    ) -> BaseResource:
        """Generate structured output from an LLM.

        Args:
            prompt: The prompt to send to the LLM
            response_model: The Pydantic model to structure the response
            actor: The actor making the request
            **kwargs: Additional provider-specific arguments

        Returns:
            A structured response instance of response_model
        """
        ...

    def embed_text(self, text: str, **kwargs: Any) -> list[float]:
        """Generate embeddings for text.

        Args:
            text: The text to embed
            **kwargs: Additional provider-specific arguments

        Returns:
            A list of float values representing the embedding
        """
        ...


@runtime_checkable
class VectorStore(Protocol):
    """Protocol for vector store integrations."""

    def store_embedding(
        self,
        resource: BaseResource,
        embedding: list[float],
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Store an embedding with associated resource.

        Args:
            resource: The HACS resource to associate with the embedding
            embedding: The vector embedding
            metadata: Additional metadata to store

        Returns:
            A unique identifier for the stored embedding
        """
        ...

    def search_similar(
        self,
        query_embedding: list[float],
        limit: int = 10,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar embeddings.

        Args:
            query_embedding: The query embedding to search for
            limit: Maximum number of results to return
            filter_metadata: Optional metadata filters

        Returns:
            A list of search results with scores and metadata
        """
        ...


@runtime_checkable
class AgentFramework(Protocol):
    """Protocol for agent framework integrations."""

    def create_agent_state(
        self,
        workflow_type: str,
        actor: Actor,
        resources: list[BaseResource] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create an agent state for a workflow.

        Args:
            workflow_type: The type of workflow to create state for
            actor: The actor running the workflow
            resources: Optional initial resources for the state
            **kwargs: Additional framework-specific arguments

        Returns:
            A framework-specific state dictionary
        """
        ...

    def convert_resource(
        self, resource: BaseResource, target_format: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Convert a HACS resource to framework format.

        Args:
            resource: The HACS resource to convert
            target_format: The target format name
            **kwargs: Additional conversion arguments

        Returns:
            The converted resource in framework format
        """
        ...


@runtime_checkable
class PersistenceProvider(Protocol):
    """
    Protocol for persistence providers, defining a standard interface
    for CRUD operations on HACS resources.
    """

    def save(self, resource: BaseResource, actor: Actor) -> BaseResource:
        """
        Save a new resource to the persistence layer.

        Args:
            resource: The HACS resource to save.
            actor: The actor performing the save operation.

        Returns:
            The saved resource, potentially updated with an ID or version.
        """
        ...

    def read(self, resource_type: type[T], resource_id: str, actor: Actor) -> T:
        """
        Read a resource from the persistence layer by its ID.

        Args:
            resource_type: The class of the resource to read (e.g., Patient).
            resource_id: The unique ID of the resource.
            actor: The actor performing the read operation.

        Returns:
            An instance of the requested resource.

        Raises:
            ResourceNotFoundError: If the resource is not found.
        """
        ...

    def update(self, resource: BaseResource, actor: Actor) -> BaseResource:
        """
        Update an existing resource in the persistence layer.

        Args:
            resource: The resource with updated values.
            actor: The actor performing the update.

        Returns:
            The updated resource.
        """
        ...

    def delete(self, resource_type: type[T], resource_id: str, actor: Actor) -> bool:
        """
        Delete a resource from the persistence layer.

        Args:
            resource_type: The class of the resource to delete.
            resource_id: The unique ID of the resource.
            actor: The actor performing the delete operation.

        Returns:
            True if the deletion was successful, False otherwise.
        """
        ...

    def search(
        self,
        resource_type: type[T],
        actor: Actor,
        filters: dict[str, Any] | None = None,
        limit: int = 100,
    ) -> list[T]:
        """
        Search for resources based on a set of filters.

        Args:
            resource_type: The class of the resource to search for.
            actor: The actor performing the search.
            filters: A dictionary of filters to apply to the search.
            limit: The maximum number of results to return.

        Returns:
            A list of resources matching the criteria.
        """
        ...


class BaseAdapter(ABC):
    """Abstract base class for HACS adapters.

    Provides common functionality for all adapter implementations.
    """

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the adapter is healthy and ready to use.

        Returns:
            True if the adapter is healthy, False otherwise
        """
        pass

    def get_info(self) -> dict[str, str]:
        """Get adapter information.

        Returns:
            A dictionary with adapter name and version
        """
        return {
            "name": self.name,
            "version": self.version,
            "type": self.__class__.__name__,
        }
