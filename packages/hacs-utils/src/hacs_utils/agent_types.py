"""
HACS Core Agent Types

Fundamental types for HACS agents that are used across all packages.
These are the base types that all agent implementations should use for consistency.

Core principles:
    🤖 Foundation types for all healthcare agents
    🔄 Reusable across different frameworks and contexts
    📋 Version-controlled and persistent
    ⚙️ Framework-agnostic agent definitions
    🏥 Healthcare-specific agent specializations
"""

from enum import Enum


HACS_MODELS_AVAILABLE = True


class HealthcareDomain(str, Enum):
    """Healthcare domain specializations."""

    GENERAL = "general"
    CARDIOLOGY = "cardiology"
    ONCOLOGY = "oncology"
    NEUROLOGY = "neurology"
    PSYCHIATRY = "psychiatry"
    EMERGENCY = "emergency"
    ICU = "icu"
    SURGERY = "surgery"
    PEDIATRICS = "pediatrics"
    GERIATRICS = "geriatrics"
    RADIOLOGY = "radiology"
    PATHOLOGY = "pathology"
    PHARMACY = "pharmacy"
    NURSING = "nursing"
    ADMINISTRATION = "administration"
    RESEARCH = "research"
    EDUCATION = "education"


class AgentRole(str, Enum):
    """Agent role types for specialized functionality."""

    CLINICAL_ASSISTANT = "clinical_assistant"
    DIAGNOSTIC_ASSISTANT = "diagnostic_assistant"
    TREATMENT_PLANNER = "treatment_planner"
    CLINICAL_RESEARCHER = "clinical_researcher"
    PATIENT_EDUCATOR = "patient_educator"
    QUALITY_ASSESSOR = "quality_assessor"
    TRIAGE_SPECIALIST = "triage_specialist"
    MEDICATION_REVIEWER = "medication_reviewer"
    DOCUMENTATION_SPECIALIST = "documentation_specialist"
    CARE_COORDINATOR = "care_coordinator"
    CLINICAL_DECISION_SUPPORT = "clinical_decision_support"
    PROTOCOL_ADVISOR = "protocol_advisor"


class AgentInteractionStrategy(str, Enum):
    """Strategy types for different agent communication and interaction approaches."""

    CONVERSATIONAL = "conversational"
    WORKFLOW_BASED = "workflow_based"
    EVENT_DRIVEN = "event_driven"
    BATCH_PROCESSING = "batch_processing"
    REAL_TIME = "real_time"
    HYBRID = "hybrid"


class AgentMemoryStrategy(str, Enum):
    """Agent memory management strategies."""

    EPISODIC = "episodic"
    PROCEDURAL = "procedural"
    EXECUTIVE = "executive"
    CLINICAL = "clinical"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


class AgentChainStrategy(str, Enum):
    """Agent chain execution strategies."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    ITERATIVE = "iterative"
    HIERARCHICAL = "hierarchical"
    ADAPTIVE = "adaptive"


class AgentRetrievalStrategy(str, Enum):
    """Agent document retrieval strategies."""

    SEMANTIC = "semantic"
    TEMPORAL = "temporal"
    PATIENT_SPECIFIC = "patient_specific"
    ENCOUNTER_BASED = "encounter_based"
    MULTI_MODAL = "multi_modal"
    CLINICAL_CONTEXT = "clinical_context"
    SIMILARITY_BASED = "similarity_based"


class VectorStoreType(str, Enum):
    """Vector store implementation types."""

    CHROMA = "chroma"
    FAISS = "faiss"
    QDRANT = "qdrant"
    PGVECTOR = "pgvector"
    PINECONE = "pinecone"
    WEAVIATE = "weaviate"
    OPENSEARCH = "opensearch"


class EmbeddingStrategy(str, Enum):
    """Embedding strategy types."""

    CLINICAL = "clinical"
    GENERAL = "general"
    MULTILINGUAL = "multilingual"
    DOMAIN_SPECIFIC = "domain_specific"
    BIOMEDICAL = "biomedical"
    CUSTOM = "custom"


class ConversionStrategy(str, Enum):
    """Strategy enumeration for different conversion approaches."""

    STRICT = "strict"  # Exact type matching required
    FLEXIBLE = "flexible"  # Allow type coercion
    FUZZY = "fuzzy"  # Best-effort conversion
    METADATA_RICH = "metadata_rich"  # Preserve all metadata


class ValidationSeverity(str, Enum):
    """Severity levels for validation results."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationCategory(str, Enum):
    """Categories of validation checks."""

    TYPE_SAFETY = "type_safety"
    CONFIGURATION = "configuration"
    HEALTHCARE_COMPLIANCE = "healthcare_compliance"
    SECURITY = "security"
    PERFORMANCE = "performance"
    COMPATIBILITY = "compatibility"
    BUSINESS_RULES = "business_rules"


# ============================================================================
# SCRATCHPAD AND TODO TYPES - Common Agent Patterns
# ============================================================================


class TodoPriority(str, Enum):
    """Priority levels for agent todos and tasks."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    URGENT = "urgent"


class TodoStatus(str, Enum):
    """Status values for agent todos and tasks."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"
    ON_HOLD = "on_hold"


class ClinicalUrgency(str, Enum):
    """Clinical urgency levels for healthcare tasks."""

    ROUTINE = "routine"
    URGENT = "urgent"
    EMERGENCY = "emergency"
    CRITICAL = "critical"
    STAT = "stat"  # Immediate priority


from hacs_models import AgentTodo as ScratchpadTodo

from hacs_models import ScratchpadEntry as AgentScratchpadEntry

from hacs_models import AgentTask as AgentTask

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Healthcare domain types
    "HealthcareDomain",
    "AgentRole",
    # Agent strategies
    "AgentInteractionStrategy",
    "AgentMemoryStrategy",
    "AgentChainStrategy",
    "AgentRetrievalStrategy",
    "VectorStoreType",
    "EmbeddingStrategy",
    "ConversionStrategy",
    # Validation types
    "ValidationSeverity",
    "ValidationCategory",
    # Agent scratchpad and task types
    "TodoPriority",
    "TodoStatus",
    "ClinicalUrgency",
    "ScratchpadTodo",
    "AgentScratchpadEntry",
    "AgentTask",
]
