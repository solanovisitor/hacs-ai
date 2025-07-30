"""
HACS Core - Comprehensive healthcare AI framework.

This package provides the complete foundational infrastructure for the
Healthcare Agent Communication Standard (HACS), including all models,
protocols, and core functionality.
"""

# Core Infrastructure
from .actor import Actor, ActorRole, PermissionLevel, SessionStatus
from .auth import AuthConfig, AuthError, AuthManager, TokenData, get_auth_manager, init_auth, require_auth
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

# Core Models - Import from models
from .models.encounter import Encounter, EncounterClass, EncounterStatus
from .models.observation import Observation, ObservationStatus
from .models.patient import Patient

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
]
