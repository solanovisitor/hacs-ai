"""
Core Protocols and Interfaces Following SOLID Principles

This module defines the fundamental protocols and interfaces that establish
the contracts for HACS components, following SOLID design principles.

SOLID Compliance:
- S: Single Responsibility - Each protocol defines one clear contract
- O: Open/Closed - Extensible through protocol implementation
- L: Liskov Substitution - All implementations are substitutable
- I: Interface Segregation - Small, focused protocol interfaces
- D: Dependency Inversion - Depend on protocols, not implementations
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, TypeVar, Generic, runtime_checkable
from datetime import datetime

# Type variables for generic protocols
T = TypeVar('T')
TResource = TypeVar('TResource')
TContext = TypeVar('TContext')


@runtime_checkable
class Identifiable(Protocol):
    """Protocol for objects that have an identity."""
    
    @property
    def id(self) -> str:
        """Unique identifier for the object."""
        ...


@runtime_checkable
class Timestamped(Protocol):
    """Protocol for objects that track creation and modification times."""
    
    @property
    def created_at(self) -> datetime:
        """When the object was created."""
        ...
    
    @property
    def updated_at(self) -> datetime:
        """When the object was last updated."""
        ...


@runtime_checkable
class Versioned(Protocol):
    """Protocol for objects that have version information."""
    
    @property
    def version(self) -> str:
        """Version of the object."""
        ...


@runtime_checkable
class Serializable(Protocol):
    """Protocol for objects that can be serialized."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert object to dictionary representation."""
        ...
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Serializable':
        """Create object from dictionary representation."""
        ...


@runtime_checkable
class Validatable(Protocol):
    """Protocol for objects that can validate themselves."""
    
    def validate(self) -> List[str]:
        """Validate the object and return list of errors."""
        ...
    
    def is_valid(self) -> bool:
        """Check if the object is valid."""
        ...


@runtime_checkable
class ClinicalResource(Protocol):
    """Protocol for clinical healthcare resources."""
    
    @property
    def resource_type(self) -> str:
        """Type of the clinical resource."""
        ...
    
    @property
    def status(self) -> str:
        """Current status of the resource."""
        ...
    
    def get_patient_id(self) -> Optional[str]:
        """Get the patient ID associated with this resource."""
        ...


@runtime_checkable
class ClinicalValidator(Protocol):
    """Protocol for clinical validation services."""
    
    def validate_clinical_data(self, data: Dict[str, Any]) -> List[str]:
        """Validate clinical data and return errors."""
        ...
    
    def check_clinical_rules(self, resource: ClinicalResource) -> List[str]:
        """Check clinical business rules."""
        ...


@runtime_checkable
class ClinicalReasoning(Protocol):
    """Protocol for clinical reasoning capabilities."""
    
    def analyze_symptoms(self, symptoms: List[str]) -> Dict[str, Any]:
        """Analyze symptoms and provide insights."""
        ...
    
    def suggest_diagnoses(self, patient_data: Dict[str, Any]) -> List[str]:
        """Suggest potential diagnoses."""
        ...
    
    def recommend_treatments(self, diagnosis: str, patient_data: Dict[str, Any]) -> List[str]:
        """Recommend treatments for a diagnosis."""
        ...


@runtime_checkable
class EvidenceProvider(Protocol):
    """Protocol for evidence-based healthcare providers."""
    
    def get_evidence(self, topic: str) -> List[Dict[str, Any]]:
        """Get evidence for a clinical topic."""
        ...
    
    def get_guidelines(self, condition: str) -> List[Dict[str, Any]]:
        """Get clinical guidelines for a condition."""
        ...


@runtime_checkable
class WorkflowEngine(Protocol):
    """Protocol for workflow execution engines."""
    
    def execute_workflow(self, workflow_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a clinical workflow."""
        ...
    
    def get_workflow_status(self, execution_id: str) -> str:
        """Get the status of a workflow execution."""
        ...


@runtime_checkable
class MemoryStore(Protocol, Generic[T]):
    """Protocol for memory storage systems."""
    
    def store(self, key: str, value: T) -> None:
        """Store a value with a key."""
        ...
    
    def retrieve(self, key: str) -> Optional[T]:
        """Retrieve a value by key."""
        ...
    
    def search(self, query: str) -> List[T]:
        """Search for values matching a query."""
        ...


@runtime_checkable
class ActorCapability(Protocol):
    """Protocol for actor capabilities in the system."""
    
    @property
    def actor_type(self) -> str:
        """Type of the actor (human, agent, system)."""
        ...
    
    @property
    def capabilities(self) -> List[str]:
        """List of capabilities this actor has."""
        ...
    
    def can_perform(self, action: str) -> bool:
        """Check if the actor can perform an action."""
        ...


@runtime_checkable
class ConfigurationProvider(Protocol):
    """Protocol for configuration providers."""
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        ...
    
    def set_config(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        ...
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration values."""
        ...


# Abstract base classes for common patterns

class BaseResourceProcessor(ABC):
    """
    Abstract base class for resource processors.
    
    SOLID Compliance:
    - S: Single responsibility - processes one type of resource
    - O: Open/closed - extensible for new processing logic
    """
    
    @abstractmethod
    def process(self, resource: ClinicalResource) -> Dict[str, Any]:
        """Process a clinical resource."""
        pass
    
    @abstractmethod
    def can_process(self, resource_type: str) -> bool:
        """Check if this processor can handle the resource type."""
        pass


class BaseValidator(ABC):
    """
    Abstract base class for validators.
    
    SOLID Compliance:
    - S: Single responsibility - validates one aspect
    - O: Open/closed - extensible for new validation rules
    """
    
    @abstractmethod
    def validate(self, target: Any) -> List[str]:
        """Validate the target and return errors."""
        pass
    
    @property
    @abstractmethod
    def validation_type(self) -> str:
        """Type of validation this validator performs."""
        pass


class BaseWorkflowStep(ABC):
    """
    Abstract base class for workflow steps.
    
    SOLID Compliance:
    - S: Single responsibility - executes one workflow step
    - O: Open/closed - extensible for new step types
    """
    
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow step."""
        pass
    
    @property
    @abstractmethod
    def step_type(self) -> str:
        """Type of workflow step."""
        pass
    
    @property
    @abstractmethod
    def required_inputs(self) -> List[str]:
        """List of required input parameters."""
        pass


# Framework integration protocols

@runtime_checkable
class AgentFramework(Protocol):
    """Protocol for agent framework integrations."""
    
    def create_agent(self, config: Dict[str, Any]) -> Any:
        """Create an agent with the given configuration."""
        ...
    
    def run_agent(self, agent: Any, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run an agent with input data."""
        ...


@runtime_checkable
class BaseAdapter(Protocol):
    """Base protocol for adapters."""
    
    def adapt(self, source: Any, target_type: str) -> Any:
        """Adapt source to target type."""
        ...


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for LLM providers."""
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt."""
        ...
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Chat with the LLM."""
        ...


@runtime_checkable
class PersistenceProvider(Protocol):
    """Protocol for persistence providers."""
    
    def save(self, key: str, data: Any) -> None:
        """Save data with key."""
        ...
    
    def load(self, key: str) -> Any:
        """Load data by key."""
        ...


@runtime_checkable
class VectorStore(Protocol):
    """Protocol for vector stores."""
    
    def add(self, vectors: List[List[float]], metadata: List[Dict[str, Any]]) -> None:
        """Add vectors with metadata."""
        ...
    
    def search(self, query_vector: List[float], k: int = 10) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        ...


# Composite protocols for complex behaviors

@runtime_checkable
class ClinicalEntity(Identifiable, Timestamped, Versioned, ClinicalResource, Protocol):
    """Composite protocol for clinical entities."""
    pass


@runtime_checkable
class ProcessableResource(ClinicalResource, Serializable, Validatable, Protocol):
    """Composite protocol for resources that can be processed."""
    pass


@runtime_checkable
class ConfigurableActor(ActorCapability, ConfigurationProvider, Protocol):
    """Composite protocol for configurable actors."""
    pass