"""
HACS Core - Comprehensive healthcare AI framework.

This package provides the complete foundational infrastructure for the
Healthcare Agent Communication Standard (HACS), including all models,
protocols, and core functionality.
"""

# Core Infrastructure - Import from hacs-auth for proper separation of concerns
from hacs_auth import Actor, ActorRole, PermissionLevel, SessionStatus
from .auth import AuthConfig, AuthError, AuthManager, TokenData, get_auth_manager, init_auth, require_auth
# Public Exception Types
from .exceptions import (
    HACSError, AdapterError, AdapterNotFoundError, AuthenticationError, AuthorizationError,
    ValidationError, ConfigurationError, ResourceError, ResourceNotFoundError, 
    MemoryError, VectorStoreError
)
from .base_resource import BaseResource  # BaseResource for backwards compatibility
from .clinical_reasoning import (
    ClinicalDecisionSupportService,
    ClinicalReasoningEngine,
    ClinicalReasoningOperations,
    ExpressionEngine,
    HACSClinicalReasoningExtensions,
    KnowledgeRepository,
    MeasureProcessor,
)
from .config import HACSSettings, configure_hacs, get_settings
from .container import (
    get_agent_framework,
    get_llm_provider,
    get_persistence_provider,
    get_registry,
    get_vector_store,
)
from .evidence import Evidence, EvidenceType
from .memory import MemoryBlock
from .protocols import (
    # SOLID Infrastructure Protocols
    Identifiable, Timestamped, Versioned, Serializable, Validatable,
    ClinicalResource, ClinicalValidator, ClinicalReasoning as IClinicalReasoning,
    EvidenceProvider, WorkflowEngine, MemoryStore, ActorCapability,
    ConfigurationProvider, ClinicalEntity, ProcessableResource, ConfigurableActor,
    
    # Framework Protocols  
    AgentFramework,
    BaseAdapter,
    LLMProvider,
    PersistenceProvider,
    VectorStore,
)
from .utils import (
    ClientConfig,
    RetryMixin,
    VersionManager,
    get_api_key,
    log_llm_request,
    optional_import,
    safe_import,
    standardize_messages,
    validate_response_model,
)

# Core Models - Import from hacs-models (with deprecation notice)
import warnings
warnings.warn(
    "Importing models from hacs_core is deprecated. Use hacs_models package instead: "
    "from hacs_models import Patient, Observation, Encounter",
    DeprecationWarning,
    stacklevel=2
)

# Import core models from hacs-models for backward compatibility
try:
    from hacs_models import Patient, Observation, Encounter
    from hacs_models import EncounterStatus, ObservationStatus
    # Create aliases for legacy compatibility
    EncounterClass = str  # Simplified compatibility alias
except ImportError:
    # Fallback for development/testing when hacs-models might not be available
    from .models.encounter import Encounter, EncounterClass, EncounterStatus
    from .models.observation import Observation, ObservationStatus
    from .models.patient import Patient

# Result Types - Standard results for all HACS operations
from .results import (
    HACSResult,
    ResourceSchemaResult,
    ResourceDiscoveryResult, 
    FieldAnalysisResult,
    DataQueryResult,
    WorkflowResult,
    GuidanceResult,
    MemoryResult,
    VersionResult,
    ResourceStackResult,
    ResourceTemplateResult,
    VectorStoreResult,
)

# Agent Types - Core types for all HACS agents
from .agent_types import (
    HealthcareDomain,
    AgentRole,
    AgentInteractionStrategy,
    AgentMemoryStrategy,
    AgentChainStrategy,
    AgentRetrievalStrategy,
    VectorStoreType,
    EmbeddingStrategy,
    ConversionStrategy,
    ValidationSeverity,
    ValidationCategory,
)

__version__ = VersionManager.CORE_VERSION

__all__ = [
    # Core Infrastructure
    "Actor",
    "ActorRole",
    "PermissionLevel",
    "SessionStatus",
    "AuthConfig",
    "AuthError",
    "AuthManager",
    "TokenData",
    "get_auth_manager",
    "init_auth",
    "require_auth",
    # Public Exception Types
    "HACSError",
    "AdapterError", 
    "AdapterNotFoundError",
    "AuthenticationError",
    "AuthorizationError",
    "ValidationError",
    "ConfigurationError",
    "ResourceError",
    "ResourceNotFoundError",
    "MemoryError",
    "VectorStoreError",
    "BaseResource",  # Primary export
    "ClinicalDecisionSupportService",
    "ClinicalReasoningEngine",
    "ClinicalReasoningOperations",
    "ExpressionEngine",
    "HACSClinicalReasoningExtensions",
    "KnowledgeRepository",
    "MeasureProcessor",
    "HACSSettings",
    "configure_hacs",
    "get_settings",
    "get_agent_framework",
    "get_llm_provider",
    "get_persistence_provider",
    "get_registry",
    "get_vector_store",
    "Evidence",
    "EvidenceType",
    "MemoryBlock",
    "AgentFramework",
    "BaseAdapter",
    "LLMProvider",
    "PersistenceProvider",
    "VectorStore",
    "ClientConfig",
    "RetryMixin",
    "VersionManager",
    "get_api_key",
    "log_llm_request",
    "optional_import",
    "safe_import",
    "standardize_messages",
    "validate_response_model",
    # Core Models
    "Encounter",
    "EncounterClass",
    "EncounterStatus",
    "Observation",
    "ObservationStatus",
    "Patient",
    
    # Result Types - Standard results for all HACS operations
    "HACSResult",
    "ResourceSchemaResult",
    "ResourceDiscoveryResult", 
    "FieldAnalysisResult",
    "DataQueryResult",
    "WorkflowResult",
    "GuidanceResult",
    "MemoryResult",
    "VersionResult",
    "ResourceStackResult",
    "ResourceTemplateResult",
    "VectorStoreResult",
    
    # Agent Types - Core types for all HACS agents
    "HealthcareDomain",
    "AgentRole",
    "AgentInteractionStrategy",
    "AgentMemoryStrategy",
    "AgentChainStrategy",
    "AgentRetrievalStrategy",
    "VectorStoreType",
    "EmbeddingStrategy",
    "ConversionStrategy",
    "ValidationSeverity",
    "ValidationCategory",
]
