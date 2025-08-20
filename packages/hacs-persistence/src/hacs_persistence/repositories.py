"""
Repository Pattern Implementations for HACS Persistence

This module implements the Repository pattern using the protocols defined in hacs-core.
Repositories provide a domain-oriented interface to data access, abstracting the
underlying storage implementation details.

SOLID Compliance:
- S: Single Responsibility - Each repository manages one aggregate type
- O: Open/Closed - Extensible through inheritance and adapter pattern
- L: Liskov Substitution - All repositories implement Repository protocol
- I: Interface Segregation - Focused repository interfaces
- D: Dependency Inversion - Depends on adapter abstractions from hacs-core

Author: HACS Development Team
License: MIT
"""

import logging
from datetime import datetime
from typing import Any, TypeVar

# Import persistence protocols from hacs-core
from hacs_core.persistence_protocols import (
    AggregateRoot,
    EntityId,
    PersistenceProvider,
    Repository,
)

# Import models from hacs_models
try:
    from hacs_models import Actor, BaseResource, Encounter, Observation, Patient
except ImportError:
    from hacs_core import BaseResource, Encounter, Observation, Patient

# Import existing adapters
from .adapter import PostgreSQLAdapter

logger = logging.getLogger(__name__)

# Type variables
TAggregate = TypeVar("TAggregate", bound=AggregateRoot)
TResource = TypeVar("TResource", bound=BaseResource)


class BaseRepository(Repository[TAggregate]):
    """
    Base repository implementation with common functionality.

    SOLID Compliance:
    - S: Single responsibility - provides common repository operations
    - D: Dependency inversion - depends on PersistenceProvider abstraction
    """

    def __init__(self, adapter: PersistenceProvider, aggregate_type: str):
        self.adapter = adapter
        self.aggregate_type = aggregate_type
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

    async def _serialize_aggregate(self, aggregate: TAggregate) -> dict[str, Any]:
        """Serialize aggregate to dictionary."""
        if hasattr(aggregate, "model_dump"):
            # Pydantic model
            return aggregate.model_dump()
        elif hasattr(aggregate, "to_dict"):
            # Custom serialization
            return aggregate.to_dict()
        elif hasattr(aggregate, "__dict__"):
            # Fallback to object dict
            data = aggregate.__dict__.copy()
            # Convert EntityId to string
            if "id" in data and hasattr(data["id"], "value"):
                data["id"] = data["id"].value
            # Convert datetime objects
            for key, value in data.items():
                if isinstance(value, datetime):
                    data[key] = value.isoformat()
            return data
        else:
            raise ValueError(f"Cannot serialize aggregate of type {type(aggregate)}")

    async def _deserialize_aggregate(
        self, data: dict[str, Any], aggregate_class: type[TAggregate]
    ) -> TAggregate:
        """Deserialize dictionary to aggregate."""
        try:
            # Convert id string back to EntityId if needed
            if "id" in data and isinstance(data["id"], str):
                data["id"] = EntityId(data["id"])

            # Convert datetime strings back to datetime objects
            for key, value in data.items():
                if isinstance(value, str) and key.endswith("_at"):
                    try:
                        data[key] = datetime.fromisoformat(value.replace("Z", "+00:00"))
                    except ValueError:
                        pass  # Keep as string if conversion fails

            # Create aggregate instance
            if hasattr(aggregate_class, "model_validate"):
                # Pydantic model
                return aggregate_class.model_validate(data)
            else:
                # Regular class
                return aggregate_class(**data)
        except Exception as e:
            self.logger.error(f"Failed to deserialize {aggregate_class.__name__}: {e}")
            raise

    async def save(self, aggregate: TAggregate) -> TAggregate:
        """Save an aggregate and return the saved instance."""
        try:
            data = await self._serialize_aggregate(aggregate)
            saved_data = await self.adapter.save(self.aggregate_type, aggregate.id, data)

            # Update aggregate with any changes from storage
            if saved_data != data:
                return await self._deserialize_aggregate(saved_data, type(aggregate))

            return aggregate
        except Exception as e:
            self.logger.error(f"Failed to save {self.aggregate_type} {aggregate.id}: {e}")
            raise

    async def find_by_id(self, aggregate_id: EntityId) -> TAggregate | None:
        """Find an aggregate by its ID."""
        try:
            data = await self.adapter.load(self.aggregate_type, aggregate_id)
            if data is None:
                return None

            # We need the aggregate class to deserialize
            # This will be overridden in concrete repositories
            raise NotImplementedError("Concrete repositories must implement find_by_id")
        except Exception as e:
            self.logger.error(f"Failed to find {self.aggregate_type} {aggregate_id}: {e}")
            raise

    async def exists(self, aggregate_id: EntityId) -> bool:
        """Check if an aggregate exists."""
        try:
            return await self.adapter.exists(self.aggregate_type, aggregate_id)
        except Exception as e:
            self.logger.error(
                f"Failed to check existence of {self.aggregate_type} {aggregate_id}: {e}"
            )
            raise

    async def delete(self, aggregate_id: EntityId) -> bool:
        """Delete an aggregate by ID. Returns True if deleted."""
        try:
            return await self.adapter.delete(self.aggregate_type, aggregate_id)
        except Exception as e:
            self.logger.error(f"Failed to delete {self.aggregate_type} {aggregate_id}: {e}")
            raise

    async def find_all(self, limit: int | None = None, offset: int = 0) -> list[TAggregate]:
        """Find all aggregates with optional pagination."""
        try:
            data_list = await self.adapter.list_all(self.aggregate_type, limit, offset)
            results = []
            for data in data_list:
                # This will be overridden in concrete repositories
                raise NotImplementedError("Concrete repositories must implement find_all")
            return results
        except Exception as e:
            self.logger.error(f"Failed to find all {self.aggregate_type}: {e}")
            raise

    async def find_by_criteria(self, criteria: dict[str, Any]) -> list[TAggregate]:
        """Find aggregates matching specific criteria."""
        try:
            data_list = await self.adapter.find_by_criteria(self.aggregate_type, criteria)
            results = []
            for data in data_list:
                # This will be overridden in concrete repositories
                raise NotImplementedError("Concrete repositories must implement find_by_criteria")
            return results
        except Exception as e:
            self.logger.error(f"Failed to find {self.aggregate_type} by criteria: {e}")
            raise


class ResourceRepository(BaseRepository[BaseResource]):
    """
    Generic repository for BaseResource aggregates.

    SOLID Compliance:
    - S: Single responsibility - manages BaseResource persistence
    - L: Liskov substitution - implements Repository contract
    """

    def __init__(self, adapter: PersistenceProvider, resource_class: type[BaseResource]):
        self.resource_class = resource_class
        super().__init__(adapter, resource_class.__name__)

    async def find_by_id(self, aggregate_id: EntityId) -> BaseResource | None:
        """Find a resource by its ID."""
        data = await self.adapter.load(self.aggregate_type, aggregate_id)
        if data is None:
            return None
        return await self._deserialize_aggregate(data, self.resource_class)

    async def find_all(self, limit: int | None = None, offset: int = 0) -> list[BaseResource]:
        """Find all resources with optional pagination."""
        data_list = await self.adapter.list_all(self.aggregate_type, limit, offset)
        results = []
        for data in data_list:
            aggregate = await self._deserialize_aggregate(data, self.resource_class)
            results.append(aggregate)
        return results

    async def find_by_criteria(self, criteria: dict[str, Any]) -> list[BaseResource]:
        """Find resources matching specific criteria."""
        data_list = await self.adapter.find_by_criteria(self.aggregate_type, criteria)
        results = []
        for data in data_list:
            aggregate = await self._deserialize_aggregate(data, self.resource_class)
            results.append(aggregate)
        return results


class PatientRepository(ResourceRepository):
    """
    Repository for Patient resources.

    SOLID Compliance:
    - S: Single responsibility - manages Patient-specific operations
    - L: Liskov substitution - extends ResourceRepository
    """

    def __init__(self, adapter: PersistenceProvider):
        super().__init__(adapter, Patient)

    async def find_by_mrn(self, mrn: str) -> Patient | None:
        """Find a patient by Medical Record Number."""
        results = await self.find_by_criteria({"medical_record_number": mrn})
        return results[0] if results else None

    async def find_by_name(self, family_name: str, given_names: list[str]) -> list[Patient]:
        """Find patients by name."""
        criteria = {"family_name": family_name, "given_names": given_names}
        return await self.find_by_criteria(criteria)


class ObservationRepository(ResourceRepository):
    """
    Repository for Observation resources.

    SOLID Compliance:
    - S: Single responsibility - manages Observation-specific operations
    - L: Liskov substitution - extends ResourceRepository
    """

    def __init__(self, adapter: PersistenceProvider):
        super().__init__(adapter, Observation)

    async def find_by_patient(self, patient_id: EntityId) -> list[Observation]:
        """Find observations for a specific patient."""
        return await self.find_by_criteria({"patient_id": patient_id.value})

    async def find_by_code(self, code: str) -> list[Observation]:
        """Find observations by observation code."""
        return await self.find_by_criteria({"code": code})


class EncounterRepository(ResourceRepository):
    """
    Repository for Encounter resources.

    SOLID Compliance:
    - S: Single responsibility - manages Encounter-specific operations
    - L: Liskov substitution - extends ResourceRepository
    """

    def __init__(self, adapter: PersistenceProvider):
        super().__init__(adapter, Encounter)

    async def find_by_patient(self, patient_id: EntityId) -> list[Encounter]:
        """Find encounters for a specific patient."""
        return await self.find_by_criteria({"patient_id": patient_id.value})

    async def find_active_encounters(self) -> list[Encounter]:
        """Find all active encounters."""
        return await self.find_by_criteria({"status": "active"})


class RepositoryFactory:
    """
    Factory for creating repository instances.

    SOLID Compliance:
    - S: Single responsibility - creates repository instances
    - O: Open/closed - extensible for new repository types
    - D: Dependency inversion - depends on adapter abstractions
    """

    def __init__(self, adapter: PersistenceProvider):
        self.adapter = adapter
        self._repositories: dict[str, Repository] = {}

    def get_repository(self, resource_class: type[BaseResource]) -> Repository:
        """Get a repository for a specific resource class."""
        class_name = resource_class.__name__

        if class_name not in self._repositories:
            if class_name == "Patient":
                self._repositories[class_name] = PatientRepository(self.adapter)
            elif class_name == "Observation":
                self._repositories[class_name] = ObservationRepository(self.adapter)
            elif class_name == "Encounter":
                self._repositories[class_name] = EncounterRepository(self.adapter)
            else:
                # Generic repository for other resource types
                self._repositories[class_name] = ResourceRepository(self.adapter, resource_class)

        return self._repositories[class_name]

    def get_patient_repository(self) -> PatientRepository:
        """Get a Patient repository."""
        return self.get_repository(Patient)

    def get_observation_repository(self) -> ObservationRepository:
        """Get an Observation repository."""
        return self.get_repository(Observation)

    def get_encounter_repository(self) -> EncounterRepository:
        """Get an Encounter repository."""
        return self.get_repository(Encounter)


# Convenience functions
async def create_repository_factory(database_url: str) -> RepositoryFactory:
    """Create a repository factory with PostgreSQL adapter."""
    adapter = PostgreSQLAdapter(database_url)
    await adapter.initialize()
    return RepositoryFactory(adapter)


__all__ = [
    "BaseRepository",
    "ResourceRepository",
    "PatientRepository",
    "ObservationRepository",
    "EncounterRepository",
    "RepositoryFactory",
    "create_repository_factory",
]
