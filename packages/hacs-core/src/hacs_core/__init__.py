"""
HACS Core - Protocol definitions and core abstractions.

This package provides the foundational protocols and interfaces for the
Healthcare Agent Communication Standard (HACS). It defines contracts that
other HACS packages implement, ensuring a decoupled and extensible architecture.

Key Features:
- Core business logic protocols (Identifiable, Timestamped, ClinicalResource, etc.)
- Tool framework protocols for healthcare AI agents
- Clinical reasoning protocols for evidence-based care
- Exception hierarchy for all HACS packages
- Configuration protocols for system settings

This package contains NO concrete implementations - only protocols and abstractions.
"""

# Core Protocols - The foundation of HACS architecture
from .protocols import (
    # Core Infrastructure Protocols
    Identifiable, Timestamped, Versioned, Serializable, Validatable,
    ClinicalResource, ClinicalValidator, ClinicalReasoning,
    EvidenceProvider, WorkflowEngine, MemoryStore, ActorCapability,
    ConfigurationProvider, ClinicalEntity, ProcessableResource, ConfigurableActor,

    # Framework Protocols
    AgentFramework,
    BaseAdapter,
    LLMProvider,
    PersistenceProvider,
    VectorStore,
)

# Persistence Protocols - Clean data layer abstractions
from .persistence_protocols import (
    # Core Entities and Value Objects
    EntityId, Entity, AggregateRoot,

    # Persistence Abstractions
    Repository, UnitOfWork, SchemaManager, TransactionManager,
)

# Tool Framework Protocols - Essential for HACS tools
from .tool_protocols import (
    ToolCategory, ToolMetadata, ToolDecorator, ToolRegistry, InMemoryToolRegistry
)

# Clinical Reasoning Protocols - For evidence-based healthcare AI
from .clinical_reasoning import (
    KnowledgeRepository,
    ClinicalDecisionSupportService,
    ClinicalReasoningEngine,
    ClinicalReasoningOperations,
    ExpressionEngine,
    HACSClinicalReasoningExtensions,
    MeasureProcessor,
)

# Protocol Utilities and Dependency Injection
from .protocol_utils import (
    # Utility functions
    ensure_identifiable, ensure_clinical_resource, extract_ids, sort_by_timestamp,
    filter_by_patient, validate_resources, serialize_resources, find_newer_resources,

    # Protocol registry and dependency injection
    ProtocolRegistry, register_provider, get_provider, get_providers,
    inject_persistence_provider, inject_memory_store, inject_evidence_provider, inject_clinical_validator,
)

# Core Exception Hierarchy
from .exceptions import (
    HACSError, AdapterError, AdapterNotFoundError, AuthenticationError, AuthorizationError,
    ValidationError, ConfigurationError, ResourceError, ResourceNotFoundError,
    MemoryError, VectorStoreError
)

# Configuration Protocols
from .config import HACSSettings, configure_hacs, get_settings

# Authentication Protocols and Core Components
from .auth import AuthConfig, AuthError, AuthManager, TokenData, get_auth_manager, init_auth, require_auth

# Import models from their proper packages with backwards compatibility
import warnings
warnings.warn(
    "Importing models from hacs_core is deprecated. Use their specific packages instead:\n"
    "- from hacs_models import Actor, Patient, Observation, Evidence\n"
    "- from hacs_utils import HealthcareDomain, AgentRole",
    DeprecationWarning,
    stacklevel=2
)

# Backwards compatibility imports (deprecated)
try:
    from hacs_models import Actor, BaseResource, Evidence, MemoryBlock, Patient, Observation, Encounter
    from hacs_utils import HealthcareDomain, AgentRole
    _models_available = True
except ImportError:
    _models_available = False

# Version info
__version__ = "0.3.0"
__author__ = "HACS Development Team"
__license__ = "MIT"

# Clean exports - Only protocols, abstractions, and utilities
__all__ = [
    # Core Infrastructure Protocols
    "Identifiable", "Timestamped", "Versioned", "Serializable", "Validatable",
    "ClinicalResource", "ClinicalValidator", "ClinicalReasoning",
    "EvidenceProvider", "WorkflowEngine", "MemoryStore", "ActorCapability",
    "ConfigurationProvider", "ClinicalEntity", "ProcessableResource", "ConfigurableActor",

    # Framework Protocols
    "AgentFramework", "BaseAdapter", "LLMProvider", "PersistenceProvider", "VectorStore",

    # Persistence Protocols
    "EntityId", "Entity", "AggregateRoot", "Repository", "UnitOfWork", "SchemaManager", "TransactionManager",

    # Tool Framework Protocols
    "ToolCategory", "ToolMetadata", "ToolDecorator", "ToolRegistry", "InMemoryToolRegistry",

    # Clinical Reasoning Protocols
    "KnowledgeRepository", "ClinicalDecisionSupportService", "ClinicalReasoningEngine",
    "ClinicalReasoningOperations", "ExpressionEngine", "HACSClinicalReasoningExtensions",
    "MeasureProcessor",

    # Protocol Utilities
    "ensure_identifiable", "ensure_clinical_resource", "extract_ids", "sort_by_timestamp",
    "filter_by_patient", "validate_resources", "serialize_resources", "find_newer_resources",
    "ProtocolRegistry", "register_provider", "get_provider", "get_providers",
    "inject_persistence_provider", "inject_memory_store", "inject_evidence_provider", "inject_clinical_validator",

    # Exceptions
    "HACSError", "AdapterError", "AdapterNotFoundError", "AuthenticationError", "AuthorizationError",
    "ValidationError", "ConfigurationError", "ResourceError", "ResourceNotFoundError",
    "MemoryError", "VectorStoreError",

    # Configuration
    "HACSSettings", "configure_hacs", "get_settings",

    # Authentication
    "AuthConfig", "AuthError", "AuthManager", "TokenData", "get_auth_manager", "init_auth", "require_auth",
]

# Add deprecated models to exports if available (with warnings)
if _models_available:
    __all__.extend([
        "Actor", "BaseResource", "Evidence", "MemoryBlock", "Patient", "Observation", "Encounter", "HealthcareDomain", "AgentRole"
    ])

# Package metadata for introspection
PACKAGE_INFO = {
    "name": "hacs-core",
    "version": __version__,
    "description": "Healthcare Agent Communication Standard - Core protocols and abstractions",
    "author": __author__,
    "license": __license__,
    "type": "protocol_definitions",
    "provides": [
        "Core business logic protocols",
        "Tool framework protocols",
        "Clinical reasoning protocols",
        "Exception hierarchy",
        "Configuration protocols",
        "Authentication protocols"
    ],
    "depends_on": [],
    "documentation": "https://hacs.readthedocs.io/",
    "repository": "https://github.com/your-org/hacs",
}

def get_protocol_info():
    """
    Get information about available protocols in this package.

    Returns:
        Dictionary with protocol categories and their protocols
    """
    return {
        "core_protocols": [
            "Identifiable", "Timestamped", "Versioned", "Serializable", "Validatable"
        ],
        "clinical_protocols": [
            "ClinicalResource", "ClinicalValidator", "ClinicalReasoning", "EvidenceProvider"
        ],
        "framework_protocols": [
            "AgentFramework", "BaseAdapter", "LLMProvider", "PersistenceProvider", "VectorStore"
        ],
        "tool_protocols": [
            "Tool", "ToolCategory", "ToolRegistry", "HealthcareTool", "HACSToolResult"
        ],
        "workflow_protocols": [
            "WorkflowEngine", "MemoryStore", "ConfigurationProvider"
        ]
    }

def validate_protocol_compliance(obj, protocol_name: str) -> bool:
    """
    Validate that an object implements the specified protocol.

    Args:
        obj: Object to validate
        protocol_name: Name of the protocol to check

    Returns:
        True if object implements the protocol

    Raises:
        ValueError: If protocol_name is not recognized
    """
    protocol_map = {
        "Identifiable": Identifiable,
        "Timestamped": Timestamped,
        "Versioned": Versioned,
        "Serializable": Serializable,
        "Validatable": Validatable,
        "ClinicalResource": ClinicalResource,
        "ActorCapability": ActorCapability,
        "ConfigurationProvider": ConfigurationProvider,
    }

    if protocol_name not in protocol_map:
        available = ", ".join(protocol_map.keys())
        raise ValueError(f"Unknown protocol '{protocol_name}'. Available: {available}")

    protocol = protocol_map[protocol_name]
    return isinstance(obj, protocol)

# Mark this as a protocol-only package
__protocol_package__ = True