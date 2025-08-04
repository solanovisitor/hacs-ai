"""
HACS Models - Pure Healthcare Data Models

This package provides type-safe, FHIR-compliant healthcare data models 
optimized for AI agent communication and healthcare application development.

Design Philosophy:
    - Pure data models with no business logic
    - Full type safety with mypy strict mode
    - FHIR R4/R5 compliance
    - Minimal dependencies (Pydantic only)
    - AI-optimized structures

Key Features:
    - Automatic ID generation
    - Timestamp management
    - Type-safe field validation
    - JSON Schema generation
    - Subset model creation with pick()
    - Immutable design patterns

Author: HACS Development Team
License: MIT
Version: 0.1.0
"""

# Base classes - Foundation for all models
from .base_resource import BaseResource, DomainResource
from .types import (
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

# Core healthcare models
from .patient import Patient, HumanName, ContactPoint, Address, Identifier
from .observation import Observation, Quantity, CodeableConcept, Coding, Range
from .encounter import Encounter, EncounterParticipant, EncounterDiagnosis
from .condition import Condition, ConditionStage, ConditionEvidence
from .medication import Medication, MedicationIngredient
from .medication_request import MedicationRequest, Dosage, DosageInstruction
from .procedure import Procedure, ProcedurePerformer, ProcedureFocalDevice
from .goal import Goal, GoalTarget

# Specialized models for AI agents
from .memory import MemoryBlock, EpisodicMemory, SemanticMemory, WorkingMemory
from .agent_message import AgentMessage, MessageRole, MessageType
from .resource_bundle import ResourceBundle, BundleEntry, BundleType
from .workflow import WorkflowDefinition, WorkflowStep, WorkflowAction

# Version info
__version__ = "0.1.0"
__author__ = "HACS Development Team"
__license__ = "MIT"

# Public API - Core Models
__all__ = [
    # Base classes
    "BaseResource",
    "DomainResource",
    
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
    
    # Patient and related structures
    "Patient",
    "HumanName",
    "ContactPoint", 
    "Address",
    "Identifier",
    
    # Observation and clinical data
    "Observation",
    "Quantity",
    "CodeableConcept",
    "Coding",
    "Range",
    
    # Encounter management
    "Encounter",
    "EncounterParticipant",
    "EncounterDiagnosis",
    
    # Condition tracking
    "Condition",
    "ConditionStage",
    "ConditionEvidence",
    
    # Medication management
    "Medication",
    "MedicationIngredient",
    "MedicationRequest",
    "Dosage",
    "DosageInstruction",
    
    # Procedure documentation
    "Procedure",
    "ProcedurePerformer",
    "ProcedureFocalDevice",
    
    # Goal management
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
]

# Package metadata for introspection
PACKAGE_INFO = {
    "name": "hacs-models",
    "version": __version__,
    "description": "Pure healthcare data models for AI agent systems",
    "author": __author__,
    "license": __license__,
    "python_requires": ">=3.11",
    "dependencies": ["pydantic>=2.11.7"],
    "homepage": "https://github.com/your-org/hacs",
    "documentation": "https://hacs.readthedocs.io/",
    "repository": "https://github.com/your-org/hacs",
}

def get_model_registry() -> dict[str, type[BaseResource]]:
    """
    Get registry of all available healthcare models.
    
    Returns:
        Dictionary mapping model names to model classes
        
    Example:
        >>> registry = get_model_registry()
        >>> PatientModel = registry["Patient"]
        >>> patient = PatientModel(full_name="John Doe")
    """
    return {
        "Patient": Patient,
        "Observation": Observation,
        "Encounter": Encounter,
        "Condition": Condition,
        "Medication": Medication,
        "MedicationRequest": MedicationRequest,
        "Procedure": Procedure,
        "Goal": Goal,
        "MemoryBlock": MemoryBlock,
        "EpisodicMemory": EpisodicMemory,
        "SemanticMemory": SemanticMemory,
        "WorkingMemory": WorkingMemory,
        "AgentMessage": AgentMessage,
        "ResourceBundle": ResourceBundle,
        "WorkflowDefinition": WorkflowDefinition,
    }

def get_fhir_resources() -> list[type[BaseResource]]:
    """
    Get list of FHIR-compliant resource models.
    
    Returns:
        List of model classes that comply with FHIR standards
    """
    return [
        Patient,
        Observation,
        Encounter,
        Condition,
        Medication,
        MedicationRequest,
        Procedure,
        Goal,
    ]

def validate_model_compatibility() -> bool:
    """
    Validate that all models are properly configured and compatible.
    
    Returns:
        True if all models pass validation checks
        
    Raises:
        ValueError: If model configuration issues are found
    """
    try:
        # Test model instantiation
        registry = get_model_registry()
        
        for model_name, model_class in registry.items():
            # Verify model has required base fields
            required_fields = {"id", "resource_type", "created_at", "updated_at"}
            if not required_fields.issubset(model_class.model_fields.keys()):
                missing = required_fields - set(model_class.model_fields.keys())
                raise ValueError(f"{model_name} missing required fields: {missing}")
            
            # Verify model can be instantiated with minimal data
            try:
                # Special handling for models with specific requirements
                if model_name == "Patient":
                    instance = model_class(resource_type=model_name, full_name="Test Patient")
                elif model_name == "MemoryBlock":
                    instance = model_class(resource_type="MemoryBlock", memory_type="semantic", content="Test content")
                elif model_name == "EpisodicMemory":
                    instance = model_class(memory_type="episodic", content="Test content")
                elif model_name == "SemanticMemory":
                    instance = model_class(memory_type="semantic", content="Test content")
                elif model_name == "WorkingMemory":
                    instance = model_class(memory_type="working", content="Test content")
                elif model_name == "Observation":
                    from .observation import CodeableConcept, Coding
                    test_code = CodeableConcept(coding=[Coding(code="test", display="Test")])
                    instance = model_class(resource_type=model_name, status="final", code=test_code)
                elif model_name == "Encounter":
                    # Use proper field name (class not class_)
                    kwargs = {"resource_type": model_name, "status": "planned"}
                    kwargs["class"] = "outpatient"  # Direct assignment to avoid alias issues
                    instance = model_class(**kwargs)
                else:
                    instance = model_class(resource_type=model_name)
                
                if not instance.id or not instance.created_at:
                    raise ValueError(f"{model_name} auto-generation not working")
            except Exception as e:
                raise ValueError(f"{model_name} instantiation failed: {e}") from e
        
        return True
        
    except Exception as e:
        raise ValueError(f"Model compatibility validation failed: {e}") from e