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
from typing import Any, Dict, List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field

from hacs_models import BaseResource
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
    STRICT = "strict"          # Exact type matching required
    FLEXIBLE = "flexible"      # Allow type coercion
    FUZZY = "fuzzy"           # Best-effort conversion
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

class ScratchpadTodo(BaseResource):
    """Healthcare-specific todo item for clinical task tracking.

    Extends BaseResource to provide full HACS functionality including:
    - Auto-generated IDs and timestamps
    - FHIR-compliant structure
    - Support for .pick() method
    - Clinical context integration

    Use this instead of basic TypedDict for better type safety and HACS integration.
    """

    resource_type: Literal["ScratchpadTodo"] = Field(
        default="ScratchpadTodo",
        description="Resource type identifier"
    )

    content: str = Field(
        description="The task or todo content",
        examples=[
            "Create patient record for John Doe",
            "Review medication list for contraindications",
            "Schedule follow-up appointment"
        ]
    )

    status: TodoStatus = Field(
        default=TodoStatus.PENDING,
        description="Current status of the todo item"
    )

    priority: TodoPriority = Field(
        default=TodoPriority.MEDIUM,
        description="Priority level for task completion"
    )

    clinical_urgency: ClinicalUrgency = Field(
        default=ClinicalUrgency.ROUTINE,
        description="Clinical urgency level for healthcare tasks"
    )

    assigned_actor: Optional[str] = Field(
        default=None,
        description="Actor/agent responsible for this task",
        examples=["Dr. Smith", "clinical_assistant_agent", "system"]
    )

    patient_id: Optional[str] = Field(
        default=None,
        description="Associated patient ID if task is patient-specific",
        examples=["patient-a1b2c3d4"]
    )

    encounter_id: Optional[str] = Field(
        default=None,
        description="Associated encounter ID if task is encounter-specific",
        examples=["encounter-b2c3d4e5"]
    )

    workflow_id: Optional[str] = Field(
        default=None,
        description="Associated workflow ID if task is part of a workflow",
        examples=["workflow-c3d4e5f6"]
    )

    estimated_duration_minutes: Optional[int] = Field(
        default=None,
        description="Estimated time to complete task in minutes",
        examples=[15, 30, 60]
    )

    required_permissions: List[str] = Field(
        default_factory=list,
        description="Required actor permissions to complete this task",
        examples=[["patient:read", "observation:write"], ["medication:review"]]
    )

    clinical_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Clinical context and metadata for healthcare tasks",
        examples=[
            {"department": "cardiology", "chief_complaint": "chest pain"},
            {"medication_review": True, "allergies_check": True}
        ]
    )

    due_date: Optional[datetime] = Field(
        default=None,
        description="Due date for task completion"
    )

    completed_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when task was completed"
    )

    notes: Optional[str] = Field(
        default=None,
        description="Additional notes or comments about the task",
        max_length=1000
    )

class AgentScratchpadEntry(BaseResource):
    """Generic scratchpad entry for agent working memory.

    Used for temporary notes, observations, and working data that agents
    need to track during task execution. Extends BaseResource for full HACS integration.
    """

    resource_type: Literal["AgentScratchpadEntry"] = Field(
        default="AgentScratchpadEntry",
        description="Resource type identifier"
    )

    entry_type: str = Field(
        description="Type of scratchpad entry",
        examples=["observation", "hypothesis", "plan", "note", "reminder"]
    )

    content: str = Field(
        description="The scratchpad entry content",
        examples=[
            "Patient reports 7/10 chest pain, radiating to left arm",
            "Hypothesis: Possible myocardial infarction - order ECG and troponins",
            "Plan: Start with basic vitals, then cardiac workup"
        ]
    )

    agent_id: str = Field(
        description="ID of the agent that created this entry",
        examples=["clinical_assistant", "diagnostic_agent", "triage_specialist"]
    )

    context_reference: Optional[str] = Field(
        default=None,
        description="Reference to related resource (patient, encounter, etc.)",
        examples=["Patient/patient-123", "Encounter/encounter-456"]
    )

    confidence_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score for this entry (0.0 to 1.0)"
    )

    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorizing and searching entries",
        examples=[["cardiac", "urgent"], ["medication", "allergy"]]
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the scratchpad entry"
    )

class AgentTask(BaseResource):
    """Structured task definition for agent execution.

    More formal than ScratchpadTodo, used for well-defined tasks with
    clear inputs, outputs, and execution parameters.
    """

    resource_type: Literal["AgentTask"] = Field(
        default="AgentTask",
        description="Resource type identifier"
    )

    task_name: str = Field(
        description="Name/title of the task",
        examples=["Patient Triage", "Medication Review", "Discharge Planning"]
    )

    task_type: str = Field(
        description="Type of task for categorization",
        examples=["clinical_assessment", "administrative", "documentation", "review"]
    )

    description: str = Field(
        description="Detailed description of the task",
        examples=[
            "Perform initial patient assessment including vitals and chief complaint",
            "Review current medications for interactions and contraindications"
        ]
    )

    status: TodoStatus = Field(
        default=TodoStatus.PENDING,
        description="Current task status"
    )

    priority: TodoPriority = Field(
        default=TodoPriority.MEDIUM,
        description="Task priority level"
    )

    assigned_agent: Optional[str] = Field(
        default=None,
        description="Agent assigned to execute this task",
        examples=["clinical_assistant", "medication_reviewer", "discharge_planner"]
    )

    input_parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Input parameters required for task execution",
        examples=[
            {"patient_id": "patient-123", "encounter_id": "encounter-456"},
            {"medication_list": [], "patient_allergies": []}
        ]
    )

    expected_output: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Expected output structure and format",
        examples=[
            {"assessment_complete": "boolean", "vitals": "object", "chief_complaint": "string"},
            {"review_complete": "boolean", "interactions_found": "array", "recommendations": "array"}
        ]
    )

    execution_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Context and environment for task execution",
        examples=[
            {"department": "emergency", "shift": "night", "bed_number": "A12"},
            {"pharmacy_system": "connected", "allergy_database": "available"}
        ]
    )

    dependencies: List[str] = Field(
        default_factory=list,
        description="Task IDs that must be completed before this task",
        examples=[["task-001", "task-002"], []]
    )

    estimated_duration_minutes: Optional[int] = Field(
        default=None,
        description="Estimated execution time in minutes"
    )

    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts on failure"
    )

    started_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when task execution started"
    )

    completed_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when task was completed"
    )

    result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Task execution result"
    )

    error_message: Optional[str] = Field(
        default=None,
        description="Error message if task failed"
    )

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Healthcare domain types
    'HealthcareDomain',
    'AgentRole',

    # Agent strategies
    'AgentInteractionStrategy',
    'AgentMemoryStrategy',
    'AgentChainStrategy',
    'AgentRetrievalStrategy',
    'VectorStoreType',
    'EmbeddingStrategy',
    'ConversionStrategy',

    # Validation types
    'ValidationSeverity',
    'ValidationCategory',

    # Agent scratchpad and task types
    'TodoPriority',
    'TodoStatus',
    'ClinicalUrgency',
    'ScratchpadTodo',
    'AgentScratchpadEntry',
    'AgentTask',
]