"""
Protocol-Based Utilities for HACS

This module provides utility functions that work with protocol-based interfaces,
enabling type-safe, contract-based programming throughout the HACS ecosystem.

These utilities demonstrate how to leverage protocols for:
- Type-safe resource operations
- Framework-agnostic implementations
- Contract-based validation
- Dependency injection
"""

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
)
from datetime import datetime

# Import protocols
from .protocols import (
    Identifiable,
    Timestamped,
    Serializable,
    Validatable,
    ClinicalResource,
    ClinicalValidator,
    MemoryStore,
    PersistenceProvider,
    EvidenceProvider,
)

# Type variables for generic functions
T = TypeVar("T")
IdentifiableT = TypeVar("IdentifiableT", bound=Identifiable)
TimestampedT = TypeVar("TimestampedT", bound=Timestamped)
ClinicalT = TypeVar("ClinicalT", bound=ClinicalResource)


def ensure_identifiable(obj: Any) -> Identifiable:
    """
    Ensure an object implements the Identifiable protocol.

    Args:
        obj: Object to check

    Returns:
        The object cast as Identifiable

    Raises:
        TypeError: If object doesn't implement Identifiable
    """
    if not isinstance(obj, Identifiable):
        raise TypeError(f"Object {type(obj)} does not implement Identifiable protocol")
    return obj


def ensure_clinical_resource(obj: Any) -> ClinicalResource:
    """
    Ensure an object implements the ClinicalResource protocol.

    Args:
        obj: Object to check

    Returns:
        The object cast as ClinicalResource

    Raises:
        TypeError: If object doesn't implement ClinicalResource
    """
    if not isinstance(obj, ClinicalResource):
        raise TypeError(
            f"Object {type(obj)} does not implement ClinicalResource protocol"
        )
    return obj


def extract_ids(resources: List[Identifiable]) -> List[str]:
    """
    Extract IDs from a list of identifiable resources.

    Args:
        resources: List of objects implementing Identifiable

    Returns:
        List of resource IDs
    """
    return [resource.id for resource in resources]


def sort_by_timestamp(
    resources: List[TimestampedT], descending: bool = True
) -> List[TimestampedT]:
    """
    Sort timestamped resources by creation time.

    Args:
        resources: List of objects implementing Timestamped
        descending: If True, newest first; if False, oldest first

    Returns:
        Sorted list of resources
    """
    return sorted(resources, key=lambda r: r.created_at, reverse=descending)


def filter_by_patient(resources: List[ClinicalT], patient_id: str) -> List[ClinicalT]:
    """
    Filter clinical resources by patient ID.

    Args:
        resources: List of clinical resources
        patient_id: Patient ID to filter by

    Returns:
        Filtered list of resources
    """
    return [
        resource for resource in resources if resource.get_patient_id() == patient_id
    ]


def validate_resources(resources: List[Validatable]) -> Dict[str, List[str]]:
    """
    Validate a list of resources and return validation errors.

    Args:
        resources: List of validatable resources

    Returns:
        Dictionary mapping resource index to validation errors
    """
    validation_results = {}
    for i, resource in enumerate(resources):
        errors = resource.validate()
        if errors:
            validation_results[str(i)] = errors
    return validation_results


def serialize_resources(resources: List[Serializable]) -> List[Dict[str, Any]]:
    """
    Serialize a list of resources to dictionaries.

    Args:
        resources: List of serializable resources

    Returns:
        List of serialized resource dictionaries
    """
    return [resource.to_dict() for resource in resources]


def find_newer_resources(
    resources: List[TimestampedT], since: datetime
) -> List[TimestampedT]:
    """
    Find resources created after a specific timestamp.

    Args:
        resources: List of timestamped resources
        since: Timestamp to compare against

    Returns:
        Resources created after the given timestamp
    """
    return [resource for resource in resources if resource.created_at > since]


class ProtocolRegistry:
    """
    Registry for protocol-compliant objects.

    Provides a centralized way to register and discover objects that implement
    specific protocols, enabling dependency injection and plugin architectures.
    """

    def __init__(self):
        self._providers: Dict[Type, List[Any]] = {}

    def register_provider(self, protocol: Type[T], provider: T) -> None:
        """
        Register a provider for a specific protocol.

        Args:
            protocol: The protocol interface
            provider: Object implementing the protocol
        """
        if not isinstance(provider, protocol):
            raise TypeError(f"Provider {type(provider)} does not implement {protocol}")

        if protocol not in self._providers:
            self._providers[protocol] = []

        self._providers[protocol].append(provider)

    def get_providers(self, protocol: Type[T]) -> List[T]:
        """
        Get all providers for a specific protocol.

        Args:
            protocol: The protocol interface

        Returns:
            List of providers implementing the protocol
        """
        return self._providers.get(protocol, [])

    def get_provider(self, protocol: Type[T]) -> Optional[T]:
        """
        Get the first provider for a specific protocol.

        Args:
            protocol: The protocol interface

        Returns:
            First provider implementing the protocol, or None
        """
        providers = self.get_providers(protocol)
        return providers[0] if providers else None


# Global protocol registry instance
_global_protocol_registry = ProtocolRegistry()


def register_provider(protocol: Type[T], provider: T) -> None:
    """
    Register a provider with the global protocol registry.

    Args:
        protocol: The protocol interface
        provider: Object implementing the protocol
    """
    _global_protocol_registry.register_provider(protocol, provider)


def get_provider(protocol: Type[T]) -> Optional[T]:
    """
    Get a provider from the global protocol registry.

    Args:
        protocol: The protocol interface

    Returns:
        Provider implementing the protocol, or None
    """
    return _global_protocol_registry.get_provider(protocol)


def get_providers(protocol: Type[T]) -> List[T]:
    """
    Get all providers from the global protocol registry.

    Args:
        protocol: The protocol interface

    Returns:
        List of providers implementing the protocol
    """
    return _global_protocol_registry.get_providers(protocol)


# Protocol-based dependency injection helpers


def inject_persistence_provider() -> Optional[PersistenceProvider]:
    """Get registered persistence provider."""
    return get_provider(PersistenceProvider)


def inject_memory_store() -> Optional[MemoryStore]:
    """Get registered memory store."""
    return get_provider(MemoryStore)


def inject_evidence_provider() -> Optional[EvidenceProvider]:
    """Get registered evidence provider."""
    return get_provider(EvidenceProvider)


def inject_clinical_validator() -> Optional[ClinicalValidator]:
    """Get registered clinical validator."""
    return get_provider(ClinicalValidator)


# Export all utilities
__all__ = [
    # Type checking utilities
    "ensure_identifiable",
    "ensure_clinical_resource",
    # Collection utilities
    "extract_ids",
    "sort_by_timestamp",
    "filter_by_patient",
    "validate_resources",
    "serialize_resources",
    "find_newer_resources",
    # Protocol registry
    "ProtocolRegistry",
    "register_provider",
    "get_provider",
    "get_providers",
    # Dependency injection helpers
    "inject_persistence_provider",
    "inject_memory_store",
    "inject_evidence_provider",
    "inject_clinical_validator",
]
