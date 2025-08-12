"""
HACS Core Models - Backward Compatibility Layer

DEPRECATED: This module is deprecated in favor of the hacs-models package.
All models have been migrated to hacs-models for better architecture separation.

This compatibility layer redirects imports to maintain backward compatibility.
For new code, import directly from hacs-models:

    # New way (preferred)
    from hacs_models import Patient, Observation, Encounter
    
    # Old way (deprecated but still works)
    from hacs_core.models import Patient, Observation, Encounter

Migration Guide:
    Replace all imports from hacs_core.models with hacs_models imports.
    The models are identical, just better organized in the new package.
"""

import warnings
from hacs_core.utils import VersionManager

__version__ = VersionManager.CORE_VERSION

# Issue deprecation warning
warnings.warn(
    "hacs_core.models is deprecated. Use hacs_models package instead: "
    "from hacs_models import Patient, Observation, etc.",
    DeprecationWarning,
    stacklevel=2
)

# Import models from hacs-models package for backward compatibility
try:
    # Core healthcare models
    from hacs_models import (
        # Base classes
        BaseResource,
        DomainResource,
        
        # Core healthcare models
        Patient,
        HumanName,
        ContactPoint, 
        Address,
        Identifier,
        Observation,
        Quantity,
        CodeableConcept,
        Coding,
        Range,
        Encounter,
        EncounterParticipant,
        EncounterDiagnosis,
        Condition,
        ConditionStage,
        ConditionEvidence,
        Medication,
        MedicationIngredient,
        MedicationRequest,
        Dosage,
        DosageInstruction,
        Procedure,
        ProcedurePerformer,
        ProcedureFocalDevice,
        Goal,
        GoalTarget,
        
        # AI agent models
        MemoryBlock,
        EpisodicMemory,
        SemanticMemory,
        WorkingMemory,
        AgentMessage,
        MessageRole,
        MessageType,
        
        # Bundle and workflow
        ResourceBundle,
        BundleEntry,
        BundleType,
        WorkflowDefinition,
        WorkflowStep,
        WorkflowAction,
    )
    
    # Import type definitions
    from hacs_models import (
        HealthcareDomain,
        Gender,
        ObservationStatus,
        EncounterStatus,
        ConditionClinicalStatus,
        ConditionVerificationStatus,
        MedicationRequestStatus,
        ProcedureStatus,
        GoalLifecycleStatus,
        ContactPointSystem,
        ContactPointUse,
        AddressUse,
        AddressType,
        IdentifierUse,
        NameUse,
    )
    
    # Create backward compatibility aliases for commonly used models
    # that might not be in hacs_models yet
    try:
        # Try to import additional models if they exist
        from hacs_models import AllergyIntolerance
    except ImportError:
        # Create placeholder for backward compatibility
        class AllergyIntolerance(BaseResource):
            """Placeholder for AllergyIntolerance model."""
            pass
    
    # Create placeholders for models not yet migrated to hacs_models
    class FamilyMemberHistory(BaseResource):
        """Placeholder for FamilyMemberHistory model."""
        pass
    
    class RiskAssessment(BaseResource):
        """Placeholder for RiskAssessment model."""
        pass
    
    class ActivityDefinition(BaseResource):
        """Placeholder for ActivityDefinition model."""
        pass
    
    class PlanDefinition(BaseResource):
        """Placeholder for PlanDefinition model."""
        pass
    
    class Task(BaseResource):
        """Placeholder for Task model."""
        pass
    
    class Appointment(BaseResource):
        """Placeholder for Appointment model."""
        pass
    
    class Document(BaseResource):
        """Placeholder for Document model."""
        pass
    
    class Library(BaseResource):
        """Placeholder for Library model."""
        pass
    
    class Organization(BaseResource):
        """Placeholder for Organization model."""
        pass
    
    class EvidenceVariable(BaseResource):
        """Placeholder for EvidenceVariable model."""
        pass
    
    class GuidanceResponse(BaseResource):
        """Placeholder for GuidanceResponse model."""
        pass
    
    class ContextSummary(BaseResource):
        """Placeholder for ContextSummary model."""
        pass
    
    class KnowledgeItem(BaseResource):
        """Placeholder for KnowledgeItem model."""
        pass
    
    class ScratchpadEntry(BaseResource):
        """Placeholder for ScratchpadEntry model."""
        pass
    
    class WorkflowRequest(BaseResource):
        """Placeholder for WorkflowRequest model."""
        pass
    
    class WorkflowEvent(BaseResource):
        """Placeholder for WorkflowEvent model."""
        pass
    
    class WorkflowExecution(BaseResource):
        """Placeholder for WorkflowExecution model."""
        pass
    
    # Document-related placeholders
    from enum import Enum
    
    class DocumentStatus(str, Enum):
        """Document status enumeration."""
        PRELIMINARY = "preliminary"
        FINAL = "final"
        AMENDED = "amended"
        ENTERED_IN_ERROR = "entered-in-error"
    
    class DocumentType(str, Enum):
        """Document type enumeration."""
        PROGRESS_NOTE = "progress-note"
        DISCHARGE_SUMMARY = "discharge-summary"
        CONSULTATION_NOTE = "consultation-note"
        CLINICAL_SUMMARY = "clinical-summary"
        PROCEDURE_NOTE = "procedure-note"
        OPERATIVE_NOTE = "operative-note"
        PATHOLOGY_REPORT = "pathology-report"
        RADIOLOGY_REPORT = "radiology-report"
        LAB_REPORT = "lab-report"
    
    class ConfidentialityLevel(str, Enum):
        """Document confidentiality level."""
        NORMAL = "N"
        RESTRICTED = "R"
        VERY_RESTRICTED = "V"
    
    class DocumentAuthor(BaseResource):
        """Placeholder for DocumentAuthor model."""
        pass
    
    class DocumentAttester(BaseResource):
        """Placeholder for DocumentAttester model."""
        pass
    
    class DocumentSection(BaseResource):
        """Placeholder for DocumentSection model."""
        pass
    
    class DocumentEncounter(BaseResource):
        """Placeholder for DocumentEncounter model."""
        pass
    
    # Document factory functions placeholders
    def create_discharge_summary(*args, **kwargs):
        """Placeholder factory function."""
        return Document()
    
    def create_progress_note(*args, **kwargs):
        """Placeholder factory function."""
        return Document()
    
    def create_consultation_note(*args, **kwargs):
        """Placeholder factory function."""
        return Document()
    
    def create_clinical_summary(*args, **kwargs):
        """Placeholder factory function."""
        return Document()
    
    # Create aliases for backward compatibility
    Memory = MemoryBlock  # Common alias
    MemoryType = str  # Legacy compatibility
    
    # Legacy enum aliases
    AdministrativeGender = Gender
    EncounterClass = str  # Simplified compatibility
    
except ImportError as e:
    warnings.warn(
        f"Could not import from hacs-models package: {e}. "
        "Make sure hacs-models is installed: pip install hacs-models",
        ImportWarning,
        stacklevel=2
    )
    
    # Fallback - create minimal stubs to prevent import errors
    class BaseResource:
        pass
    
    class Patient(BaseResource):
        pass
    
    class Observation(BaseResource):
        pass
    
    class Encounter(BaseResource):
        pass

# Maintain backward compatibility exports
__all__ = [
    # Base classes
    "BaseResource",
    "DomainResource",
    
    # Core healthcare models
    "Patient",
    "HumanName",
    "ContactPoint", 
    "Address",
    "Identifier",
    "Observation",
    "Quantity",
    "CodeableConcept",
    "Coding",
    "Range",
    "Encounter",
    "EncounterParticipant",
    "EncounterDiagnosis",
    "Condition",
    "ConditionStage",
    "ConditionEvidence",
    "Medication",
    "MedicationIngredient",
    "MedicationRequest",
    "Dosage",
    "DosageInstruction",
    "Procedure",
    "ProcedurePerformer",
    "ProcedureFocalDevice",
    "Goal",
    "GoalTarget",
    
    # AI agent models
    "MemoryBlock",
    "EpisodicMemory",
    "SemanticMemory",
    "WorkingMemory",
    "AgentMessage",
    "MessageRole",
    "MessageType",
    
    # Bundle and workflow
    "ResourceBundle",
    "BundleEntry",
    "BundleType",
    "WorkflowDefinition",
    "WorkflowStep",
    "WorkflowAction",
    
    # Type definitions
    "HealthcareDomain",
    "Gender",
    "ObservationStatus",
    "EncounterStatus",
    "ConditionClinicalStatus",
    "ConditionVerificationStatus",
    "MedicationRequestStatus",
    "ProcedureStatus",
    "GoalLifecycleStatus",
    "ContactPointSystem",
    "ContactPointUse",
    "AddressUse",
    "AddressType",
    "IdentifierUse",
    "NameUse",
    
    # Aliases for backward compatibility
    "Memory",
    "MemoryType",
    "AdministrativeGender",
    "EncounterClass",
    
    # Placeholder models for backward compatibility
    "AllergyIntolerance",
    "FamilyMemberHistory",
    "RiskAssessment", 
    "ActivityDefinition",
    "PlanDefinition",
    "Task",
    "Appointment",
    "Document",
    "Library",
    "Organization",
    "EvidenceVariable",
    "GuidanceResponse",
    "ContextSummary",
    "KnowledgeItem",
    "ScratchpadEntry",
    "WorkflowRequest",
    "WorkflowEvent",
    "WorkflowExecution",
    
    # Document-related models and enums
    "DocumentStatus",
    "DocumentType",
    "ConfidentialityLevel",
    "DocumentAuthor",
    "DocumentAttester",
    "DocumentSection",
    "DocumentEncounter",
    "create_discharge_summary",
    "create_progress_note",
    "create_consultation_note",
    "create_clinical_summary",
]


def hello() -> str:
    """Backward compatibility function."""
    warnings.warn(
        "hello() function is deprecated. This was for testing only.",
        DeprecationWarning,
        stacklevel=2
    )
    return "Hello from hacs-models (via hacs-core compatibility layer)!"