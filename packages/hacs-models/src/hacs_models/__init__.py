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
    # NEW - Critical Phase 1 additions
    AllergyIntoleranceStatus,
    AllergyIntoleranceType,
    AllergyCriticality,
    AllergyReactionSeverity,
    ServiceRequestStatus,
    ServiceRequestIntent,
    ServiceRequestPriority,
    DiagnosticReportStatus,
    MedicationStatus,
    MedicationRequestIntent,
    # Added for compatibility with legacy tests and FHIR alignment
    DocumentStatus,
    DocumentType,
    ConfidentialityLevel,
    BundleStatus,
    WorkflowStatus,
    WorkflowRequestIntent,
    WorkflowRequestPriority,
    EventStatus,
    WorkflowTaskStatus,
    WorkflowTaskIntent,
    WorkflowActivityDefinitionKind,
)

# Core healthcare models
from .patient import Patient, HumanName, ContactPoint, Address, Identifier
from .observation import Observation, Quantity, CodeableConcept, Coding, Range
from .encounter import Encounter, EncounterParticipant, EncounterDiagnosis
from .condition import Condition, ConditionStage, ConditionEvidence
from .medication import Medication, MedicationIngredient
from .medication_request import MedicationRequest, Dosage
from .procedure import Procedure, ProcedurePerformer, ProcedureFocalDevice
from .goal import Goal, GoalTarget
# NEW - Phase 1 critical resources
from .allergy_intolerance import (
    AllergyIntolerance,
    AllergyIntoleranceReaction,
    create_food_allergy,
    create_medication_allergy,
    create_environmental_allergy,
)
from .service_request import (
    ServiceRequest,
    create_lab_request,
    create_imaging_request,
    create_referral_request,
)
from .diagnostic_report import (
    DiagnosticReport,
    DiagnosticReportMedia,
    create_lab_report,
    create_imaging_report,
    create_pathology_report,
    create_microbiology_report,
)
from .practitioner import (
    Practitioner,
    PractitionerQualification,
    create_physician,
    create_nurse,
    create_therapist,
)
from .organization import (
    Organization,
    OrganizationContact,
    create_hospital,
    create_clinic,
    create_department,
    create_insurance_organization,
    create_pharmacy,
)
from .document_reference import DocumentReference
from .medication_statement import MedicationStatement
from .family_member_history import FamilyMemberHistory
from .immunization import Immunization
from .appointment import Appointment
from .service_request import ServiceRequest
from .care_plan import CarePlan
from .care_team import CareTeam
from .nutrition_order import NutritionOrder
from .plan_definition import PlanDefinition, PlanDefinitionGoal, PlanDefinitionAction

# Specialized models for AI agents
from .memory import MemoryBlock, EpisodicMemory, SemanticMemory, WorkingMemory
from .agent_message import AgentMessage, MessageRole, MessageType
from .message_definition import MessageDefinition
from .resource_bundle import ResourceBundle, BundleEntry, BundleType
from .reference import Reference
from .graph_definition import GraphDefinition, GraphDefinitionLink, GraphDefinitionLinkTarget
from .event import Event, EventPerformer
from .terminology import TerminologySystem, TerminologyConcept, ValueSet, ConceptMap
from .tool_definition import ToolDefinition
from .resource_bundle import WorkflowBindingType, WorkflowBinding, LinkRelation
from .resource_bundle import ResourceBundle as _RB
UseCase = _RB.UseCase
BundleUpdate = _RB.BundleUpdate
create_resource_stack = _RB.create_resource_stack
create_search_results_bundle = _RB.create_search_results_bundle
create_workflow_template_bundle = _RB.create_workflow_template_bundle
# Deprecated stack template API
from .stack_template import StackTemplate, LayerSpec, instantiate_stack_template
from .workflow import WorkflowDefinition, WorkflowStep, WorkflowAction
from .workflow import (
    WorkflowRequest,
    WorkflowEvent,
    WorkflowTaskResource,
    WorkflowActivityDefinition,
    WorkflowParticipant,
    WorkflowPlanDefinition,
    WorkflowPlanDefinitionAction,
    WorkflowServiceRequest,
    WorkflowExecution,
    create_simple_task,
    create_document_processing_workflow,
    create_clinical_workflow_execution,
)
from .annotation import (
    PromptTemplateResource,
    ExtractionSchemaResource,
    TransformSpec,
    SourceBinding,
    OutputSpec,
    MappingSpec,
    ChunkingPolicy,
    ModelConfig,
    PersistencePolicy,
    AnnotationWorkflowResource,
    TextChunk,
    AlignmentStatus,
    CharInterval,
    Extraction,
    FormatType,
    Document,
    AnnotatedDocument,
    # Minimal document-related types for compatibility
    DocumentAuthor,
    DocumentAttester,
    DocumentSection,
    DocumentEncounter,
    create_discharge_summary,
    create_progress_note,
    create_consultation_note,
    create_clinical_summary,
)
from .actor import Actor, ActorRole, PermissionLevel, SessionStatus
from .evidence import Evidence, EvidenceType
from .agent_resources import AgentTodo, ScratchpadEntry, AgentTask, ScratchpadTodo, AgentScratchpadEntry
from .actor_preference import ActorPreference, PreferenceScope
from .results import (
    HACSResult, ResourceSchemaResult, ResourceDiscoveryResult, FieldAnalysisResult,
    DataQueryResult, WorkflowResult, GuidanceResult, MemoryResult, VersionResult,
    ResourceStackResult, ResourceTemplateResult, VectorStoreResult
)

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
    # Added compatibility enums
    "DocumentStatus",
    "DocumentType",
    "ConfidentialityLevel",
    "BundleStatus",
    "WorkflowStatus",
    "WorkflowRequestIntent",
    "WorkflowRequestPriority",
    "EventStatus",
    "WorkflowTaskStatus",
    "WorkflowTaskIntent",
    "WorkflowActivityDefinitionKind",
    # NEW - Phase 1 critical types
    "AllergyIntoleranceStatus",
    "AllergyIntoleranceType",
    "AllergyCriticality",
    "AllergyReactionSeverity",
    "ServiceRequestStatus",
    "ServiceRequestIntent",
    "ServiceRequestPriority",
    "DiagnosticReportStatus",
    "MedicationStatus",

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

    # Procedure documentation
    "Procedure",
    "ProcedurePerformer",
    "ProcedureFocalDevice",

    # Goal management
    "Goal",
    "GoalTarget",

    # NEW - Phase 1 critical resources
    # Allergy/Intolerance management (safety-critical)
    "AllergyIntolerance",
    "AllergyIntoleranceReaction",
    "create_food_allergy",
    "create_medication_allergy",
    "create_environmental_allergy",
    # Service request management (care coordination)
    "ServiceRequest",
    "create_lab_request",
    "create_imaging_request",
    "create_referral_request",
    # Diagnostic reporting (clinical decisions)
    "DiagnosticReport",
    "DiagnosticReportMedia",
    "create_lab_report",
    "create_imaging_report",
    "create_pathology_report",
    "create_microbiology_report",
    # Healthcare provider management (care teams)
    "Practitioner",
    "PractitionerQualification",
    "create_physician",
    "create_nurse",
    "create_therapist",
    # Healthcare facility management (organizations)
    "Organization",
    "OrganizationContact",
    "create_hospital",
    "create_clinic",
    "create_department",
    "create_insurance_organization",
    "create_pharmacy",
    # Documents and context
    "DocumentReference",
    # Medication usage report
    "MedicationStatement",
    # Family history
    "FamilyMemberHistory",
    # Immunization (vaccines)
    "Immunization",
    # Scheduling and orders
    "Appointment",
    "ServiceRequest",
    "CarePlan",
    "CareTeam",
    "NutritionOrder",
    "PlanDefinition",
    "PlanDefinitionGoal", 
    "PlanDefinitionAction",

    # AI agent models
    "MemoryBlock",
    "EpisodicMemory",
    "SemanticMemory",
    "WorkingMemory",
    "AgentMessage",
    "MessageRole",
    "MessageType",
    "MessageDefinition",

    # Bundle and workflow
    "ResourceBundle",
    "BundleEntry",
    "BundleType",
    "Reference",
    "GraphDefinition",
    "GraphDefinitionLink",
    "GraphDefinitionLinkTarget",
    "Event",
    "EventPerformer",
    # Terminology
    "TerminologySystem",
    "TerminologyConcept",
    "ValueSet",
    "ConceptMap",
    "ConceptMapElement",
    "WorkflowBindingType",
    "WorkflowBinding",
    "LinkRelation",
    "UseCase",
    "BundleUpdate",
    "create_resource_stack",
    "create_search_results_bundle",
    "create_workflow_template_bundle",
    # Stack templates
    "StackTemplate",
    "LayerSpec",
    "instantiate_stack_template",
    "WorkflowDefinition",
    "WorkflowStep",
    "WorkflowAction",
    "WorkflowRequest",
    "WorkflowEvent",
    "WorkflowTaskResource",
    "WorkflowActivityDefinition",
    "WorkflowParticipant",
    "WorkflowPlanDefinition",
    "WorkflowPlanDefinitionAction",
    "WorkflowServiceRequest",
    "WorkflowExecution",
    "create_simple_task",
    "create_document_processing_workflow",
    "create_clinical_workflow_execution",
    # Annotation entities
    "PromptTemplateResource",
    "ExtractionSchemaResource",
    "TransformSpec",
    "SourceBinding",
    "OutputSpec",
    "MappingSpec",
    "ChunkingPolicy",
    "ModelConfig",
    "PersistencePolicy",
    "AnnotationWorkflowResource",
    "TextChunk",
    "AlignmentStatus",
    "CharInterval",
    "Extraction",
    "FormatType",
    "Document",
    "AnnotatedDocument",
    "DocumentAuthor",
    "DocumentAttester",
    "DocumentSection",
    "DocumentEncounter",
    "create_discharge_summary",
    "create_progress_note",
    "create_consultation_note",
    "create_clinical_summary",

    # Actor and authentication
    "Actor",
    "ActorRole",
    "PermissionLevel",
    "SessionStatus",

    # Evidence and clinical reasoning
    "Evidence",
    "EvidenceType",

    # Result types
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
    # Agent resources
    "AgentTodo",
    "ScratchpadEntry",
    "AgentTask",
    "ActorPreference",
    "PreferenceScope",
    # Compatibility agent resource aliases
    "ScratchpadTodo",
    "AgentScratchpadEntry",
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
        # Foundation classes
        "BaseResource": BaseResource,
        "DomainResource": DomainResource,
        # Security and messaging
        "Actor": Actor,
        "ActorPreference": ActorPreference,
        "MessageDefinition": MessageDefinition,
        "AgentMessage": AgentMessage,
        # Clinical and admin resources
        "Patient": Patient,
        "Observation": Observation,
        "Encounter": Encounter,
        "Document": Document,
        "Condition": Condition,
        "Medication": Medication,
        "MedicationRequest": MedicationRequest,
        "MedicationStatement": MedicationStatement,
        "Procedure": Procedure,
        "Goal": Goal,
        "ServiceRequest": ServiceRequest,
        "CarePlan": CarePlan,
        "CareTeam": CareTeam,
        "NutritionOrder": NutritionOrder,
        "PlanDefinition": PlanDefinition,
        "PlanDefinitionGoal": PlanDefinitionGoal,
        "PlanDefinitionAction": PlanDefinitionAction,
        "DiagnosticReport": DiagnosticReport,
        "DocumentReference": DocumentReference,
        "FamilyMemberHistory": FamilyMemberHistory,
        "Immunization": Immunization,
        "Appointment": Appointment,
        "ServiceRequest": ServiceRequest,
        "Practitioner": Practitioner,
        "Organization": Organization,
        "Evidence": Evidence,
        "AllergyIntolerance": AllergyIntolerance,
        "GraphDefinition": GraphDefinition,
        "MemoryBlock": MemoryBlock,
        "EpisodicMemory": EpisodicMemory,
        "SemanticMemory": SemanticMemory,
        "WorkingMemory": WorkingMemory,
        "Reference": Reference,
        "ResourceBundle": ResourceBundle,
        "WorkflowDefinition": WorkflowDefinition,
        "Event": Event,
        # Terminology resources
        "TerminologySystem": TerminologySystem,
        "TerminologyConcept": TerminologyConcept,
        "ValueSet": ValueSet,
        "ConceptMap": ConceptMap,
    }


def _seed_default_model_docs() -> None:
    """Seed default HACS documentation metadata for core models (overrideable by registry)."""
    docs: dict[str, dict] = {
        "BaseResource": {
            "scope_usage": "BaseResource is the foundational Pydantic model for all HACS healthcare resources, providing automatic ID generation, timestamp management, and type-safe validation. Every HACS resource (Patient, Observation, Actor, etc.) inherits from BaseResource to gain essential infrastructure: unique identification with resource-type prefixes, audit trails with created_at/updated_at timestamps, version tracking, and protocol compliance for serialization and validation. Designed specifically for LLM agent communication with JSON Schema generation, subset model creation via pick(), and optimized serialization for AI workflows.",
            "boundaries": "BaseResource is an abstract foundation class - extend it to create custom resource types, but use existing domain resources (Patient, Observation, etc.) for standard healthcare data. Contains only infrastructure (ID, timestamps, validation) - no clinical or business logic. Not for general-purpose data modeling outside healthcare contexts. All subclasses must provide a resource_type field for proper identification and routing.",
            "relationships": [
                "Extended by: All HACS resources either directly or through DomainResource",
                "Implements: Identifiable, Timestamped, Versioned, Serializable, Validatable protocols",
                "Used by: save_resource, read_resource, validate_resource, and all HACS persistence tools",
                "Referenced via: Reference objects using 'ResourceType/id' format",
                "Grouped in: ResourceBundle collections for batch operations"
            ],
            "references": [
                "Reference.reference field uses 'ResourceType/id' format pointing to BaseResource instances",
                "ResourceBundle.entry contains BaseResource instances",
                "All HACS database tools operate on BaseResource subclasses"
            ],
            "tools": [
                # BaseResource provides foundation - specific tools are in subclasses
            ],
            "examples": [
                {"id": "custom-12345", "resource_type": "CustomResource", "created_at": "2024-01-15T10:00:00Z", "updated_at": "2024-01-15T10:00:00Z", "version": "1.0.0"},
                {"resource_type": "HealthcareResource", "agent_context": {"llm_generated": True, "confidence": 0.95}, "meta_tag": ["ai-generated", "validated"]}
            ],
        },
        "DomainResource": {
            "scope_usage": "DomainResource extends BaseResource with FHIR R4-compliant fields for clinical and healthcare domain resources. Adds status tracking (active/inactive/draft), human-readable text narratives for clinical review, contained resource support, and extension mechanisms for additional healthcare data. All clinical HACS resources (Patient, Observation, Procedure, Condition, etc.) inherit from DomainResource to gain these healthcare-specific capabilities. Essential for LLM agents processing clinical data as it provides standardized status lifecycle, text summaries for context, and extension points for AI-generated metadata.",
            "boundaries": "Use DomainResource for clinical and healthcare domain resources that need status tracking, text narratives, or contained resources. Use BaseResource directly for non-clinical infrastructure resources (Actor, MessageDefinition, workflow definitions). DomainResource provides the healthcare domain patterns but not specific clinical logic - that belongs in concrete implementations like Patient or Observation.",
            "relationships": [
                "Inherits from: BaseResource (gains ID, timestamps, validation, protocols)",
                "Extended by: Patient, Observation, Procedure, Condition, DiagnosticReport, and all clinical resources",
                "Implements: ClinicalResource protocol with get_patient_id() method",
                "Contains: Other BaseResource instances via contained field",
                "Extends: Healthcare vocabularies and systems via extension mechanism"
            ],
            "references": [
                "Clinical resources inherit DomainResource patterns: status, text, contained, extension",
                "Contained resources are embedded DomainResource instances for inline data",
                "Extensions reference HL7 FHIR StructureDefinitions and custom healthcare vocabularies"
            ],
            "tools": [
                # DomainResource provides clinical foundation - specific tools are in subclasses
            ],
            "examples": [
                {"resource_type": "ClinicalProtocol", "status": "active", "text": "Diabetes management protocol with HbA1c monitoring", "extension": {"http://hl7.org/fhir/StructureDefinition/workflow-priority": {"valueCode": "high"}}},
                {"resource_type": "CareGuideline", "status": "draft", "text": "AI-generated care recommendations based on patient history", "agent_context": {"llm_confidence": 0.92, "source_evidence": ["pubmed:12345", "guideline:ada-2024"]}}
            ],
        },
        "Reference": {
            "scope_usage": "Reference implements FHIR-compliant resource linking using the standard 'ResourceType/id' format for connecting HACS resources without embedding full objects. Critical for LLM agents to understand resource relationships and navigate healthcare data graphs. Supports both internal references (Patient/123) and external absolute URLs (http://external.org/fhir/Patient/456). Includes optional display text for human-readable context and type field for validation. Essential for maintaining referential integrity in distributed healthcare systems while enabling efficient data exchange.",
            "boundaries": "Use Reference only for linking to actual HACS resources or well-defined external FHIR resources. Not for general URLs, user IDs, session tokens, or non-resource identifiers. References should point to resources that exist and are accessible within the system context. The reference format must follow FHIR patterns: 'ResourceType/id' for internal or absolute URLs for external.",
            "relationships": [
                "Points to: Any HACS BaseResource subclass (Patient, Observation, Practitioner, etc.)",
                "Used in: All clinical resources for subject, performer, author, organization fields",
                "Enables: Resource graph traversal and relationship queries without full object loading",
                "Supports: Both internal system references and external FHIR system references",
                "Validates: Reference format and type consistency during resource validation"
            ],
            "references": [
                "Patient.subject, Observation.subject, Procedure.subject - clinical resource associations",
                "Practitioner.performer, Observation.performer - healthcare provider associations",
                "Organization.managingOrganization, Patient.managingOrganization - facility associations",
                "External FHIR systems via absolute URL format"
            ],
            "tools": [
                # Reference is a data structure - no specific tools beyond general resource operations
            ],
            "examples": [
                {"reference": "Patient/patient-12345", "type": "Patient", "display": "Maria Rodriguez, DOB: 1985-03-15"},
                {"reference": "Practitioner/dr-smith-789", "type": "Practitioner", "display": "Dr. Robert Smith, MD - Cardiology"},
                {"reference": "http://external-ehr.org/fhir/Patient/ext-456", "type": "Patient", "display": "External Patient Record"}
            ],
        },
        "ResourceBundle": {
            "scope_usage": "ResourceBundle implements FHIR Bundle patterns for grouping related HACS resources into logical collections, enabling batch operations and maintaining referential integrity across multiple resources. Essential for LLM agents processing multiple related healthcare records (patient + observations + medications) as a cohesive unit. Supports different bundle types: 'collection' for search results, 'document' for clinical documents, 'transaction' for atomic updates. Each bundle contains BundleEntry objects that wrap individual resources with metadata for processing context.",
            "boundaries": "Use ResourceBundle only for grouping actual HACS BaseResource instances, not for general data collections or arbitrary objects. Each bundle must have a clear healthcare purpose (care episode, search results, clinical document, transaction set). Bundle entries should contain resources that are logically related and benefit from being processed together. Not for non-healthcare data or general-purpose list containers.",
            "relationships": [
                "Contains: Multiple BaseResource instances through BundleEntry wrappers",
                "Manages: Internal reference resolution within bundle scope for efficient processing",
                "Supports: Cross-resource validation and referential integrity across bundle contents",
                "Enables: Atomic batch operations and transactional updates via compose_bundle tool",
                "Implements: FHIR Bundle.type patterns (collection, document, transaction, message, searchset)"
            ],
            "references": [
                "BundleEntry.resource contains actual HACS resource instances",
                "BundleEntry.link provides navigation between related bundle entries", 
                "Internal bundle references are resolved within bundle scope for performance",
                "External references point to resources outside the current bundle"
            ],
            "tools": [
                "compose_bundle", "validate_bundle"
            ],
            "examples": [
                {"type": "collection", "total": 2, "entry": [{"resource": {"resource_type": "Patient", "full_name": "John Doe"}}, {"resource": {"resource_type": "Observation", "code": {"text": "Blood Pressure"}}}]},
                {"type": "document", "timestamp": "2024-01-15T10:00:00Z", "identifier": {"value": "clinical-summary-2024-001"}, "entry": [{"resource": {"resource_type": "Patient", "id": "patient-123"}}, {"resource": {"resource_type": "Observation", "subject": "Patient/patient-123"}}]},
                {"type": "transaction", "entry": [{"request": {"method": "POST", "url": "Patient"}, "resource": {"resource_type": "Patient", "full_name": "New Patient"}}, {"request": {"method": "PUT", "url": "Observation/obs-456"}, "resource": {"resource_type": "Observation", "status": "final"}}]}
            ],
        },
        "Patient": {
            "scope_usage": "Demographics and administrative information for a person or animal receiving care. Supports care providers, general practitioners, care teams, emergency contacts, and family relationships. Includes identity management, communication preferences, language requirements, and life status (deceased, active). Optimized for AI agent context engineering with automatic name parsing and flexible input formats.",
            "boundaries": "Patient resources do not contain clinical findings (use Observation/Condition), care plans (use CarePlan), appointments (use Appointment), or billing information (use Account/Coverage). Do not use for practitioners (use Practitioner) or organizations (use Organization). Patient linkage allows connecting related patients (family members, merged records).",
            "relationships": [
                "Referenced by: Observation.subject, Encounter.subject, Procedure.subject, MedicationRequest.subject, DiagnosticReport.subject, ServiceRequest.subject, Goal.subject, CarePlan.subject, CareTeam.subject, Condition.subject, AllergyIntolerance.patient, Immunization.patient, FamilyMemberHistory.patient",
                "Links to: Practitioner via generalPractitioner/careProvider, Organization via managingOrganization, RelatedPerson via contact, Patient via link (merged records, family relationships)"
            ],
            "references": [
                "Document.subject", "Encounter.subject", "all clinical resources via subject/patient field"
            ],
            "tools": [
                "calculate_age", "add_identifier", "find_identifier_by_type", "add_care_provider", "deactivate_record"
            ],
            "examples": [
                {"full_name": "Dr. John Michael Smith Jr.", "gender": "male", "birth_date": "1985-03-15", "phone": "+1-555-123-4567", "email": "john.smith@example.com"},
                {"name": [{"use": "official", "family": "Doe", "given": ["Jane", "Marie"]}], "gender": "female", "identifier": [{"use": "usual", "type_code": "MR", "value": "12345"}]}
            ],
        },
        "Observation": {
            "scope_usage": "Measurements and simple assertions made about a patient, device, or other subjects. Central element for capturing vital signs, laboratory results, imaging measurements, clinical assessments, and device readings. Supports numeric values, coded values, text, boolean, time, ranges, ratios, and complex data types. Includes categorization (vital-signs, laboratory, imaging, survey, social-history), interpretation codes, reference ranges, and quality/reliability indicators.",
            "boundaries": "Do not use for diagnoses/problems (use Condition), procedures performed (use Procedure), care plans (use CarePlan), or medication orders (use MedicationRequest). Do not store large binary data (use DocumentReference/Media). Focus on individual observations; use DiagnosticReport for grouped results and interpretations.",
            "relationships": [
                "Referenced by: DiagnosticReport.result, Condition.evidence.detail",
                "References: Patient/Subject via subject, Encounter via encounter, Practitioner via performer, Device via device, Specimen via specimen",
                "Groups: hasMember (for panels), derivedFrom (computed from other observations), focus (additional subject context)"
            ],
            "references": [
                "Patient.subject", "Encounter.encounter", "DiagnosticReport.result", "Condition.evidence"
            ],
            "tools": [
                "summarize_observation_value"
            ],
            "examples": [
                {"status": "final", "code": {"text": "Heart rate", "coding": [{"system": "http://loinc.org", "code": "8867-4"}]}, "value_quantity": {"value": 72, "unit": "beats/min"}, "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs"}]}]},
                {"status": "final", "code": {"text": "Blood pressure"}, "component": [{"code": {"text": "Systolic"}, "value_quantity": {"value": 120, "unit": "mmHg"}}, {"code": {"text": "Diastolic"}, "value_quantity": {"value": 80, "unit": "mmHg"}}]}
            ],
        },
        "Encounter": {
            "scope_usage": "Interaction between patient and healthcare service during which care is provided. Represents the context (time, location, participants) for all clinical activities. Covers inpatient stays, outpatient visits, emergency visits, home health visits, virtual consultations, and pre-admission processes. Tracks status lifecycle, class (inpatient/outpatient/emergency/home), priority, type, service providers, locations, and period.",
            "boundaries": "Do not include clinical content directly (reference Encounter from Observation/Procedure/etc.). Do not use for appointments/scheduling (use Appointment), billing/claims (use Account/Claim), or care planning (use CarePlan). Focus on actual interactions where care is provided, not potential or planned interactions.",
            "relationships": [
                "Referenced by: Observation.encounter, Procedure.encounter, Condition.encounter, MedicationRequest.encounter, DiagnosticReport.encounter, ServiceRequest.encounter",
                "References: Patient via subject, Practitioner via participant.individual, Organization via serviceProvider, Location via location.location",
                "Links: partOf (for sub-encounters), episodeOfCare (broader care context)"
            ],
            "references": [
                "Patient.subject", "all clinical resources via encounter field"
            ],
            "tools": [
                # No specific tools - use generic modeling/database tools
            ],
            "examples": [
                {"status": "in-progress", "class": "inpatient", "type": [{"text": "Routine admission"}], "subject": "Patient/123"},
                {"status": "finished", "class": "outpatient", "period": {"start": "2023-10-15T09:00:00Z", "end": "2023-10-15T10:30:00Z"}, "participant": [{"type": [{"text": "Primary care physician"}], "individual": "Practitioner/dr-smith"}]}
            ],
        },
        "Condition": {
            "scope_usage": "Problems, diagnoses, and health concerns relevant to patient care and clinical decision making. Represents clinical conditions, symptoms, findings, and diagnoses at varying levels of detail and certainty. Supports problem lists, discharge diagnoses, differential diagnoses, and clinical concerns. Includes verification status (confirmed, provisional, differential), clinical status (active, resolved, remission), severity, onset, and resolution information.",
            "boundaries": "Do not use for medications (use MedicationRequest/Statement), procedures (use Procedure), observations/measurements (use Observation), allergies/intolerances (use AllergyIntolerance), or care plans (use CarePlan). Focus on problems/diagnoses, not care activities or treatments. Do not duplicate family history (use FamilyMemberHistory).",
            "relationships": [
                "References: Patient via subject, Encounter via encounter, Practitioner via asserter/recorder",
                "Evidence: Observation via evidence.detail, DiagnosticReport via evidence.detail",
                "Stages: ConditionStage for progression tracking",
                "Referenced by: Goal.addresses, CarePlan.addresses, ServiceRequest.reasonReference"
            ],
            "references": [
                "Patient.subject", "Encounter.encounter", "Observation/DiagnosticReport in evidence"
            ],
            "tools": [
                "add_condition_stage"
            ],
            "examples": [
                {"code": {"text": "Essential hypertension", "coding": [{"system": "http://snomed.info/sct", "code": "59621000", "display": "Essential hypertension"}]}, "clinicalStatus": "active", "verificationStatus": "confirmed", "severity": {"text": "Moderate"}},
                {"code": {"text": "Type 2 diabetes mellitus"}, "clinicalStatus": "active", "onsetDateTime": "2020-03-15", "stage": [{"summary": {"text": "Well controlled"}, "assessment": [{"reference": "Observation/hba1c-result"}]}]}
            ],
        },
        "Procedure": {
            "scope_usage": "Actions performed on, with, or for a patient as part of care delivery. Includes surgical procedures, diagnostic procedures, therapeutic procedures, administrative procedures, and care delivery activities. Represents completed, in-progress, or stopped procedures with detailed information about performers, locations, devices used, and outcomes. Supports procedure hierarchies, staged procedures, and procedure reports.",
            "boundaries": "Do not use for orders/requests (use ServiceRequest), appointments (use Appointment), medication administration (use MedicationAdministration), or observations/measurements (use Observation). Focus on procedures actually performed, not planned or ordered. Do not use for care plans (use CarePlan) or goals (use Goal).",
            "relationships": [
                "References: Patient via subject, Encounter via encounter, Practitioner via performer.actor, Device via usedReference, Location via location",
                "Based on: ServiceRequest via basedOn, CarePlan via basedOn",
                "Parts: partOf (for procedure hierarchies), followUp (post-procedure care)",
                "Outcomes: Observation via report, Condition via reasonReference"
            ],
            "references": [
                "Patient.subject", "Encounter.encounter", "ServiceRequest.basedOn", "related Observations/Conditions"
            ],
            "tools": [
                # No specific tools - use generic modeling/database tools
            ],
            "examples": [
                {"status": "completed", "code": {"text": "Appendectomy", "coding": [{"system": "http://snomed.info/sct", "code": "80146002", "display": "Appendectomy"}]}, "subject": "Patient/123", "performedDateTime": "2023-10-15T14:30:00Z", "performer": [{"actor": "Practitioner/surgeon-jones"}]},
                {"status": "in-progress", "code": {"text": "Blood pressure measurement"}, "category": {"text": "Diagnostic procedure"}, "outcome": {"text": "Successful"}}
            ],
        },
        "MedicationRequest": {
            "scope_usage": "Order or authorization for supply and administration of medication to a patient. Represents prescriptions, medication orders, and medication authorizations with detailed dosing instructions, quantity, refills, and substitution rules. Supports complex dosing regimens, conditional orders, and medication reconciliation workflows. Includes prescriber information, pharmacy instructions, and administration context.",
            "boundaries": "Do not use for actual medication taking/administration (use MedicationStatement/MedicationAdministration), medication definitions (use Medication), or medication dispensing (use MedicationDispense). Focus on the intent/order, not the fulfillment. Do not use for medication history or adherence tracking.",
            "relationships": [
                "References: Patient via subject, Practitioner via requester, Medication via medicationReference, Encounter via encounter",
                "Based on: CarePlan via basedOn, ServiceRequest via basedOn",
                "Supports: MedicationDispense.authorizingPrescription, MedicationAdministration.request",
                "Groups: priorPrescription (medication changes), groupIdentifier (related orders)"
            ],
            "references": [
                "Patient.subject", "Practitioner.requester", "Medication.medicationReference", "Encounter.encounter"
            ],
            "tools": [
                "validate_prescription_tool", "route_prescription_tool", "check_contraindications_tool", "check_drug_interactions_tool"
            ],
            "methods": [
                "update_timestamp()", "dosage instruction management", "status lifecycle management"
            ],
            "examples": [
                {"status": "active", "intent": "order", "medicationCodeableConcept": {"text": "Lisinopril 10mg", "coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": "314076"}]}, "subject": "Patient/123", "dosageInstruction": [{"text": "Take 1 tablet daily", "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}}}]},
                {"status": "completed", "intent": "order", "medicationCodeableConcept": {"text": "Amoxicillin 500mg"}, "dispenseRequest": {"numberOfRepeatsAllowed": 0, "quantity": {"value": 21, "unit": "tablets"}}}
            ],
        },
        "DiagnosticReport": {
            "scope_usage": "Clinical report that groups and consolidates diagnostic test results with clinical interpretations and conclusions. Represents laboratory reports, imaging reports, pathology reports, and other diagnostic studies. Includes result aggregation, professional interpretations, clinical significance, recommendations, and quality indicators. Supports structured and narrative reporting with media attachments.",
            "boundaries": "Do not use for individual measurements (use Observation), procedure records (use Procedure), or document storage (use DocumentReference for large attachments). Focus on the report/interpretation, not the raw data. Do not use for care plans or treatment recommendations (use CarePlan).",
            "relationships": [
                "References: Patient via subject, Observation via result, ServiceRequest via basedOn, Practitioner via performer, Specimen via specimen",
                "Supports: grouped results, multi-part reports, amended reports",
                "Media: presentedForm (report documents), image attachments"
            ],
            "references": [
                "Patient.subject", "ServiceRequest.basedOn", "Observation.result", "Encounter.encounter"
            ],
            "tools": [
                "summarize_report_tool", "link_report_results_tool", "attach_report_media_tool", "validate_report_completeness_tool"
            ],
            "methods": [
                "update_timestamp()", "result grouping", "status lifecycle management", "media attachment handling"
            ],
            "examples": [
                {"status": "final", "code": {"text": "Complete Blood Count", "coding": [{"system": "http://loinc.org", "code": "58410-2"}]}, "subject": "Patient/123", "result": ["Observation/wbc", "Observation/rbc", "Observation/hgb"], "conclusion": "Normal CBC values"},
                {"status": "final", "code": {"text": "Chest X-Ray"}, "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0074", "code": "RAD"}]}], "conclusionCode": [{"text": "Normal chest"}]}
            ],
        },
        "ServiceRequest": {
            "scope_usage": "Request for services to be performed for patient including lab tests, imaging studies, consultations, procedures, and other clinical activities. Represents orders, referrals, and service requests with priority, timing, performer preferences, and clinical context. Supports order sets, standing orders, and conditional requests with detailed instructions and authorization requirements.",
            "boundaries": "Do not use for medication orders (use MedicationRequest), appointment scheduling (use Appointment), or recording what was actually done (use Procedure/DiagnosticReport/Observation). Focus on the request/order, not the execution. Do not use for care planning (use CarePlan) or supply requests (use SupplyRequest).",
            "relationships": [
                "References: Patient via subject, Practitioner via requester/performer, Encounter via encounter, Condition via reasonReference",
                "Supports: Procedure.basedOn, DiagnosticReport.basedOn, Observation.basedOn",
                "Groups: requisition (order sets), replaces (order changes), basedOn (protocols/guidelines)"
            ],
            "references": [
                "Patient.subject", "Practitioner.requester", "Encounter.encounter", "Condition/Observation in reasonReference"
            ],
            "tools": [
                "validate_service_request_tool", "route_service_request_tool"
            ],
            "methods": [
                "update_timestamp()", "status lifecycle management", "priority and timing management"
            ],
            "examples": [
                {"status": "active", "intent": "order", "code": {"text": "Chest X-Ray", "coding": [{"system": "http://snomed.info/sct", "code": "399208008"}]}, "subject": "Patient/123", "requester": "Practitioner/dr-smith", "reasonCode": [{"text": "Suspected pneumonia"}], "priority": "routine"},
                {"status": "active", "intent": "order", "code": {"text": "Complete Blood Count"}, "category": [{"coding": [{"system": "http://snomed.info/sct", "code": "108252007", "display": "Laboratory procedure"}]}]}
            ],
        },
        "Document": {
            "scope_usage": "Structured clinical document composition with hierarchical sections, narrative content, and metadata. Represents discharge summaries, progress notes, consultation reports, care plans, and other clinical documents. Supports rich clinical narratives, coded entries, authors, attesters, custodians, and workflow status. Based on FHIR Composition with HACS extensions for AI-friendly document processing.",
            "boundaries": "Do not use for external document references (use DocumentReference), binary attachments (use Media/DocumentReference), or simple text notes (use Observation.note). Focus on structured clinical documents with sections. Do not use for real-time messaging (use Communication) or orders (use ServiceRequest/MedicationRequest).",
            "relationships": [
                "References: Patient via subject, Practitioner via author/attester, Encounter via encounter, Organization via custodian",
                "Contains: sections with entries referencing other resources (Condition, Procedure, Observation, etc.)",
                "Groups: ResourceBundle for document transmission, DocumentReference for external storage"
            ],
            "references": [
                "Patient.subject", "Encounter.encounter", "all clinical resources via section entries"
            ],
            "tools": [
                "extract_document_text"
            ],
            "examples": [
                {"title": "Discharge Summary", "status": "final", "type": {"text": "Discharge summary"}, "subject": "Patient/123", "date": "2023-10-15T14:00:00Z", "author": [{"reference": "Practitioner/dr-jones"}], "section": [{"title": "History of Present Illness", "text": "Patient presented with chest pain..."}]},
                {"title": "Progress Note", "type": {"text": "Progress note"}, "section": [{"title": "Assessment", "text": "Patient is improving"}, {"title": "Plan", "text": "Continue current medications"}]}
            ],
        },
        "DocumentReference": {
            "scope_usage": "Metadata pointer to external clinical documents, images, and binary artifacts (e.g., PDFs, DICOM). Captures document identifiers, type, status, custodian, authorship, content attachments, and context. Used to reference content not represented as structured Composition/Document within the EHR.",
            "boundaries": "Do not store narrative clinical content here (use Document/Composition). Use ImagingStudy for study-level imaging metadata; use Media for simple images. DocumentReference focuses on pointers and metadata, not the narrative or structured content itself.",
            "relationships": [
                "References: Patient via subject, Practitioner/Organization via author/custodian, Encounter via context",
                "Links: to external repositories (e.g., PACS, CMS) via content.attachment",
                "May complement: DiagnosticReport, Composition"
            ],
            "references": [
                "Patient.subject", "Encounter.context", "custodian Organization", "author Practitioner/Organization"
            ],
            "tools": [
                "validate_document_metadata", "resolve_document_location", "register_external_document", "link_document_to_record"
            ],
            "examples": [{"status": "current", "type": {"text": "PDF"}}],
        },
        "ResourceBundle": {
            "scope_usage": "Logical grouping of resources for transfer or template.",
            "boundaries": "Not a long-term canonical store; persist individual resources.",
            "relationships": ["Contains entries with resources"],
            "references": [],
            "tools": ["add_bundle_entries", "validate_bundle"],
            "examples": [{"bundle_type": "DOCUMENT", "title": "Clinical Packet"}],
        },
        "Practitioner": {
            "scope_usage": "Individual healthcare professional involved in care delivery (e.g., physicians, nurses, therapists). Includes identifiers, names, qualifications, and contact details for clinical attribution and care coordination.",
            "boundaries": "Do not use for roles/assignments (use PractitionerRole when available) or for organizations (use Organization).",
            "relationships": [
                "Referenced by: Encounter.participant, Procedure.performer, ServiceRequest.requester",
                "References: Organization via affiliation/managed organization"
            ],
            "references": ["Organization affiliations, CareTeam membership"],
            "tools": [
                "verify_practitioner_credential", "link_practitioner_to_organization", "update_practitioner_affiliation"
            ],
            "examples": [{"name": [{"text": "Dr. Alice"}], "qualification": [{"code": {"text": "MD"}}]}],
        },
        "Organization": {
            "scope_usage": "Legal or administrative entity involved in healthcare delivery (e.g., hospitals, clinics, departments, insurers). Provides identity, contact, and hierarchical relationships used for care attribution, scheduling, billing, and coordination.",
            "boundaries": "Not for individuals (use Practitioner). Use Location for physical service sites. Use OrganizationAffiliation (if available) for relationships between organizations.",
            "relationships": [
                "Referenced by: Encounter.serviceProvider, Practitioner.organization, CareTeam.managingOrganization",
                "References: parent/child organizations, service locations"
            ],
            "references": ["Encounter.serviceProvider", "Practitioner.organization"],
            "tools": [
                "register_organization", "link_organization_affiliation", "manage_service_locations"
            ],
            "examples": [{"name": "General Hospital"}],
        },
        "Evidence": {
            "scope_usage": "Literature and knowledge evidence entry with bibliographic metadata.",
            "boundaries": "Clinical documentation belongs in Document; link Evidence from documents.",
            "relationships": ["Referenced by: Document sections (via citation)"] ,
            "references": [],
            "tools": [
                # No specific tools identified yet - implement evidence search and validation tools
            ],
            "examples": [{"title": "ACE inhibitors in hypertension", "year": 2020}],
        },
        "AllergyIntolerance": {
            "scope_usage": "SAFETY-CRITICAL documentation of allergies, intolerances, and adverse reactions to substances including medications, foods, and environmental factors. Essential for clinical decision support, medication ordering, and patient safety alerts. Includes severity assessment, reaction details, and verification status for comprehensive allergy management.",
            "boundaries": "Do not use for adverse events during treatment (use AdverseEvent), side effects of current medications (use Observation), or family history of allergies (use FamilyMemberHistory). Focus on patient's own confirmed or suspected allergies/intolerances that impact care decisions.",
            "relationships": [
                "References: Patient via patient (REQUIRED), Encounter via encounter, Practitioner via recorder/asserter",
                "Critical for: MedicationRequest contraindication checking, care planning, emergency alerts",
                "Safety links: medication ordering systems, clinical decision support, emergency care protocols"
            ],
            "references": [
                "Patient.patient (REQUIRED)", "medication and food ordering systems", "clinical decision support"
            ],
            "tools": [
                "check_allergy_contraindications", "validate_allergy_severity", "generate_allergy_alerts", "reconcile_allergy_history", "assess_cross_reactivity"
            ],
            "examples": [
                {"clinicalStatus": "active", "verificationStatus": "confirmed", "type": "allergy", "category": ["medication"], "criticality": "high", "code": {"text": "Penicillin"}, "patient": "Patient/123", "reaction": [{"manifestation": [{"text": "Anaphylaxis"}], "severity": "severe", "description": "Severe allergic reaction with difficulty breathing"}]},
                {"clinicalStatus": "active", "type": "intolerance", "category": ["food"], "code": {"text": "Lactose"}, "patient": "Patient/456", "reaction": [{"manifestation": [{"text": "Gastrointestinal upset"}], "severity": "mild"}]}
            ],
        },
        "Goal": {
            "scope_usage": "Desired health outcomes for patients that can be achieved through treatment, medication, therapy, or behavior modification. Includes measurable targets, deadlines, and progress tracking. Supports clinical goal setting, care planning, and outcome measurement with lifecycle management (proposed, planned, accepted, active, on-hold, completed, cancelled).",
            "boundaries": "Do not use for care activities (use CarePlan), orders (use ServiceRequest), or completed actions (use Procedure). Goals represent desired future states, not current conditions or past events. Do not duplicate treatment plans (use CarePlan) or appointments (use Appointment).",
            "relationships": [
                "References: Patient via subject, Condition via addresses (target condition), Observation via target.measure (measurable outcomes)",
                "Referenced by: CarePlan.goal, ServiceRequest.reasonReference",
                "Supports: care team coordination, outcome measurement, patient engagement"
            ],
            "references": [
                "Patient.subject", "CarePlan.goal", "Condition via addresses"
            ],
            "tools": [
                "track_goal_progress", "update_goal_status", "measure_goal_achievement", "link_goal_to_careplan"
            ],
            "examples": [
                {"lifecycleStatus": "active", "description": {"text": "Reduce HbA1c to below 7.0%"}, "target": [{"measure": {"text": "HbA1c"}, "detailQuantity": {"value": 7.0, "unit": "%", "comparator": "<"}}], "addresses": ["Condition/diabetes"]},
                {"lifecycleStatus": "planned", "description": {"text": "Achieve weight loss of 20 pounds"}, "subject": "Patient/123", "target": [{"measure": {"text": "Body weight"}, "detailQuantity": {"value": 20, "unit": "lb"}}]}
            ],
        },
        "Medication": {
            "scope_usage": "Detailed definition of a medication including active ingredients, strength, form, manufacturer, and batch information. Serves as the master catalog entry for pharmaceutical products used in orders, administration, and dispensing. Supports medication identification, strength calculations, and interaction checking.",
            "boundaries": "Do not use for prescriptions (use MedicationRequest), actual taking/administration (use MedicationStatement/MedicationAdministration), or inventory (use Medication with quantity extensions). Focus on the medication definition, not its usage context.",
            "relationships": [
                "Referenced by: MedicationRequest.medication, MedicationStatement.medication, MedicationAdministration.medication, MedicationDispense.medication",
                "Contains: ingredients, manufacturer details, packaging information",
                "Supports: drug interaction checking, allergy alerts, formulary management"
            ],
            "references": [
                "MedicationRequest.medication", "ingredient references to other Medication/Substance"
            ],
            "tools": [
                "check_drug_interactions", "validate_medication_coding", "calculate_dosage_equivalents", "check_allergy_contraindications"
            ],
            "examples": [
                {"code": {"coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": "314076", "display": "Lisinopril 10 MG Oral Tablet"}], "text": "Lisinopril 10mg"}, "form": {"text": "Tablet"}, "ingredient": [{"itemCodeableConcept": {"text": "Lisinopril"}, "strength": {"numerator": {"value": 10, "unit": "mg"}}}]},
                {"code": {"text": "Amoxicillin 500mg capsule"}, "status": "active", "manufacturer": {"reference": "Organization/pharma-co"}}
            ],
        },
        "MedicationStatement": {
            "scope_usage": "Patient's assertion or historical record of medication use, including self-reported medications, medication reconciliation, and adherence tracking. Captures what the patient is actually taking vs. what was prescribed, supporting medication history, adherence monitoring, and clinical decision making.",
            "boundaries": "Do not use for prescriptions/orders (use MedicationRequest), scheduled administrations (use MedicationAdministration), or medication definitions (use Medication). Focus on actual/reported usage, not intended/planned usage.",
            "relationships": [
                "References: Patient via subject, Medication via medication, MedicationRequest via basedOn, Practitioner via informationSource",
                "Supports: medication reconciliation, adherence tracking, clinical review",
                "Timeline: effective period for when medication was/is being taken"
            ],
            "references": [
                "Patient.subject", "Medication.medication", "MedicationRequest.basedOn"
            ],
            "tools": [
                "reconcile_medications", "track_medication_adherence", "detect_medication_gaps", "validate_medication_history"
            ],
            "examples": [
                {"status": "active", "medicationCodeableConcept": {"text": "Metformin 500mg twice daily"}, "subject": "Patient/123", "effectiveDateTime": "2023-01-15", "taken": "y", "dosage": [{"text": "500mg twice daily with meals"}]},
                {"status": "stopped", "medicationCodeableConcept": {"text": "Lisinopril"}, "statusReason": [{"text": "Patient reported side effects"}], "effectivePeriod": {"start": "2023-01-01", "end": "2023-06-15"}}
            ],
        },
        "FamilyMemberHistory": {
            "scope_usage": "Significant health conditions and risk factors for biological relatives of the patient, supporting genetic counseling, risk assessment, and preventive care planning. Includes hereditary conditions, familial patterns, age of onset, and outcomes. Critical for identifying genetic predispositions and informing screening recommendations.",
            "boundaries": "Do not record patient's own conditions (use Condition), non-biological relationships unless medically relevant, or general health information without clinical significance. Focus on conditions that impact patient's genetic risk or care planning.",
            "relationships": [
                "References: Patient via patient, Condition via condition (what condition the relative had)",
                "Supports: genetic risk assessment, preventive care planning, family history documentation",
                "Links: may reference genetic testing, screening recommendations"
            ],
            "references": [
                "Patient.patient", "Condition references for family member conditions"
            ],
            "tools": [
                "assess_genetic_risk", "generate_family_history_summary", "identify_hereditary_patterns", "recommend_genetic_screening"
            ],
            "examples": [
                {"status": "completed", "patient": "Patient/123", "relationship": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode", "code": "MTH", "display": "mother"}]}, "condition": [{"code": {"text": "Breast cancer"}, "onsetAge": {"value": 45, "unit": "years"}, "outcome": {"text": "deceased"}}]},
                {"status": "partial", "relationship": {"text": "Father"}, "condition": [{"code": {"text": "Type 2 diabetes"}, "onsetAge": {"value": 52, "unit": "years"}}], "note": [{"text": "Strong family history of diabetes on paternal side"}]}
            ],
        },
        "Immunization": {
            "scope_usage": "Documentation of immunization events including vaccines administered, lot numbers, administration details, and reaction monitoring. Supports immunization tracking, schedule management, contraindication checking, and public health reporting. Critical for preventive care and infectious disease control.",
            "boundaries": "Do not use for immunization orders (use ServiceRequest), adverse reactions (use AdverseEvent as separate resource), or vaccination schedules (use protocols/guidelines). Focus on actual administration events, not planning or reactions.",
            "relationships": [
                "References: Patient via patient, Practitioner via performer, Organization via location, Medication via vaccineCode",
                "Supports: immunization registry, schedule tracking, contraindication checking",
                "Links: may reference immunization recommendations, adverse events, lot tracking"
            ],
            "references": [
                "Patient.patient", "vaccination schedules, adverse event monitoring"
            ],
            "tools": [
                "check_immunization_schedule", "validate_vaccine_contraindications", "track_immunization_series", "generate_immunization_record"
            ],
            "examples": [
                {"status": "completed", "vaccineCode": {"coding": [{"system": "http://hl7.org/fhir/sid/cvx", "code": "208", "display": "COVID-19, mRNA, LNP-S, PF, 30 mcg/0.3 mL dose"}]}, "patient": "Patient/123", "occurrenceDateTime": "2023-10-15", "lotNumber": "ABC123", "performer": [{"actor": "Practitioner/nurse-jones"}]},
                {"status": "completed", "vaccineCode": {"text": "Influenza vaccine"}, "doseQuantity": {"value": 0.5, "unit": "mL"}, "site": {"text": "left deltoid"}, "route": {"text": "intramuscular"}}
            ],
        },
        "Appointment": {
            "scope_usage": "Scheduled time slots for healthcare services between patients and providers, including routine visits, procedures, consultations, and follow-ups. Supports appointment scheduling, resource allocation, calendar management, and care coordination. Includes cancellation handling, rescheduling, and no-show tracking.",
            "boundaries": "Do not use for recording what actually happened during the visit (use Encounter), completed procedures (use Procedure), or orders for future services (use ServiceRequest). Focus on the scheduling and time reservation, not the clinical content.",
            "relationships": [
                "References: Patient via participant, Practitioner via participant, ServiceRequest via supportingInformation, Location via location",
                "Generates: Encounter when appointment is fulfilled",
                "Supports: schedule management, resource planning, care coordination"
            ],
            "references": [
                "Patient/Practitioner via participant", "ServiceRequest for ordered services", "Location for venue"
            ],
            "tools": [
                "schedule_appointment", "reschedule_appointment", "cancel_appointment", "check_appointment_conflicts", "send_appointment_reminders"
            ],
            "examples": [
                {"status": "booked", "appointmentType": {"text": "Follow-up visit"}, "participant": [{"actor": "Patient/123", "required": "required"}, {"actor": "Practitioner/dr-smith", "required": "required"}], "start": "2023-11-15T10:00:00Z", "end": "2023-11-15T10:30:00Z", "minutesDuration": 30},
                {"status": "pending", "serviceCategory": [{"text": "Cardiology"}], "reasonCode": [{"text": "Chest pain evaluation"}], "priority": 5, "participant": [{"actor": "Patient/456", "status": "accepted"}]}
            ],
        },
        "CarePlan": {
            "scope_usage": "Comprehensive plan of care describing intended care activities, goals, and care team coordination for managing patient conditions. Integrates multiple care activities, tracks progress toward goals, and supports care coordination across providers. Includes both provider-driven and patient-driven care plans.",
            "boundaries": "Do not use for individual orders (use ServiceRequest), single goals (use Goal as separate resource), or appointments (use Appointment). CarePlan orchestrates but doesn't replace individual resources. Do not use for workflows or protocols (use PlanDefinition).",
            "relationships": [
                "References: Patient via subject, Goal via goal, Condition via addresses, ServiceRequest via activity.reference, CareTeam via careTeam",
                "Coordinates: multiple care activities, goals, care team members",
                "Supports: care coordination, progress tracking, multi-disciplinary care"
            ],
            "references": [
                "Patient.subject", "Goal.goal", "Condition.addresses", "ServiceRequest via activities"
            ],
            "tools": [
                "create_care_plan", "update_care_plan_progress", "coordinate_care_activities", "track_care_plan_goals", "assign_care_team_roles"
            ],
            "examples": [
                {"status": "active", "intent": "plan", "subject": "Patient/123", "addresses": ["Condition/diabetes"], "goal": ["Goal/hba1c-control"], "activity": [{"reference": {"reference": "ServiceRequest/glucose-monitoring"}}, {"detail": {"description": "Patient education on diabetes management"}}], "careTeam": ["CareTeam/diabetes-team"]},
                {"status": "active", "category": [{"text": "Chronic disease management"}], "title": "Hypertension Management Plan", "description": "Comprehensive plan for blood pressure control"}
            ],
        },
        "CareTeam": {
            "scope_usage": "Organized group of healthcare providers, support persons, and organizations responsible for coordinated delivery of care to a patient. Defines roles, responsibilities, communication patterns, and care coordination for multi-disciplinary care teams. Supports care coordination, responsibility assignment, and team communication.",
            "boundaries": "Do not use for individual practitioner details (use Practitioner/PractitionerRole), organizational hierarchy (use Organization), or care activities (use CarePlan). Focus on team composition and coordination, not individual capabilities or specific care plans.",
            "relationships": [
                "References: Patient via subject, Practitioner via participant.member, Organization via participant.member, CareTeam via managingOrganization",
                "Supports: CarePlan via careTeam, communication coordination, role assignments",
                "Enables: multi-disciplinary care, care coordination, responsibility tracking"
            ],
            "references": [
                "Patient.subject", "CarePlan.careTeam", "Practitioner/Organization via participants"
            ],
            "tools": [
                "assemble_care_team", "assign_team_roles", "coordinate_team_communication", "track_team_responsibilities", "update_team_membership"
            ],
            "examples": [
                {"status": "active", "name": "Diabetes Care Team", "subject": "Patient/123", "participant": [{"role": [{"text": "Primary care physician"}], "member": "Practitioner/dr-smith"}, {"role": [{"text": "Diabetes educator"}], "member": "Practitioner/educator-jones"}, {"role": [{"text": "Endocrinologist"}], "member": "Practitioner/endo-wilson"}], "managingOrganization": ["Organization/clinic-abc"]},
                {"status": "active", "category": [{"text": "Multidisciplinary"}], "participant": [{"role": [{"text": "Care coordinator"}], "member": "Practitioner/coordinator", "period": {"start": "2023-01-01"}}]}
            ],
        },
        "NutritionOrder": {
            "scope_usage": "Orders for therapeutic diets, enteral nutrition, oral supplements, and nutritional interventions tailored to patient medical conditions, allergies, and nutritional needs. Supports clinical nutrition management, dietary restrictions, feeding protocols, and nutritional therapy coordination.",
            "boundaries": "Do not use for nutritional assessments (use Observation), meal planning without medical indication, or nutritional intake recording (use Observation). Focus on medically-ordered nutritional interventions, not general dietary preferences or measured outcomes.",
            "relationships": [
                "References: Patient via subject, Practitioner via orderer, Condition via indication, AllergyIntolerance for restrictions",
                "Supports: clinical nutrition therapy, dietary management, feeding protocols",
                "Coordinates: with CarePlan, dietary services, clinical nutrition teams"
            ],
            "references": [
                "Patient.subject", "medical conditions requiring nutritional intervention", "allergy restrictions"
            ],
            "tools": [
                "create_therapeutic_diet_order", "manage_nutrition_restrictions", "calculate_nutritional_requirements", "coordinate_feeding_protocols"
            ],
            "examples": [
                {"status": "active", "patient": "Patient/123", "orderer": "Practitioner/dietitian", "oralDiet": {"type": [{"text": "Diabetic diet"}], "schedule": [{"repeat": {"frequency": 3, "period": 1, "periodUnit": "d"}}], "texture": [{"text": "Regular"}]}, "allergyIntolerance": ["AllergyIntolerance/gluten"]},
                {"status": "active", "enteralFormula": {"baseFormulaType": {"text": "High protein formula"}, "caloricDensity": {"value": 1.5, "unit": "kcal/mL"}, "routeofAdministration": {"text": "Nasogastric tube"}}}
            ],
        },
        "PlanDefinition": {
            "scope_usage": "Reusable definition of clinical workflows, protocols, order sets, and care pathways that can be applied across multiple patients. Defines structured knowledge about care processes, decision trees, and best practices. Supports evidence-based care standardization and protocol-driven care delivery.",
            "boundaries": "Do not use for patient-specific care plans (use CarePlan), individual orders (use ServiceRequest), or actual workflows in progress (use WorkflowDefinition for HACS workflows). Focus on reusable templates and protocols, not specific patient care instances.",
            "relationships": [
                "Referenced by: CarePlan.instantiatesCanonical, ServiceRequest.instantiatesCanonical, WorkflowDefinition for HACS integration",
                "Contains: goal definitions, action sequences, decision logic, triggers",
                "Supports: protocol-based care, clinical decision support, standardized workflows"
            ],
            "references": [
                "CarePlan when instantiated", "ServiceRequest when protocols generate orders"
            ],
            "tools": [
                "instantiate_clinical_protocol", "validate_protocol_adherence", "customize_protocol_for_patient", "track_protocol_outcomes"
            ],
            "examples": [
                {"title": "Hypertension Management Protocol", "type": {"text": "clinical-protocol"}, "status": "active", "goal": [{"description": "Achieve target BP <130/80"}], "action": [{"title": "Initial assessment", "condition": [{"kind": "applicability", "expression": {"language": "text/cql", "expression": "Patient has hypertension"}}]}, {"title": "Start ACE inhibitor", "type": {"text": "create"}, "definitionCanonical": "ActivityDefinition/start-ace-inhibitor"}]},
                {"title": "Diabetes Care Pathway", "useContext": [{"code": {"system": "http://terminology.hl7.org/CodeSystem/usage-context-type", "code": "focus"}, "valueCodeableConcept": {"text": "Type 2 Diabetes"}}]}
            ],
        },
        "PlanDefinitionGoal": {
            "scope_usage": "Reusable goal component within a PlanDefinition that describes desired outcomes when the protocol is applied.",
            "boundaries": "For patient-specific goals, use Goal resource.",
            "relationships": ["Part of: PlanDefinition"],
            "references": [],
            "tools": [
                # No specific tools; managed through PlanDefinition tools
            ],
            "examples": [{"description": "Reduce BP below 130/80"}],
        },
        "PlanDefinitionAction": {
            "scope_usage": "Action component within a PlanDefinition defining steps, conditions, timing, and activity definitions.",
            "boundaries": "Use ServiceRequest/ActivityDefinition for concrete orders/activities; this is a reusable definition component.",
            "relationships": ["Part of: PlanDefinition"],
            "references": [],
            "tools": [
                # No specific tools; managed through PlanDefinition tools
            ],
            "examples": [{"title": "Order basic metabolic panel"}],
        },
        "WorkflowDefinition": {
            "scope_usage": "HACS workflow and orchestration definition, complementing FHIR PlanDefinition.",
            "boundaries": "Not a FHIR resource; bridges AI agent workflows with clinical artifacts.",
            "relationships": ["May reference: PlanDefinition, ActivityDefinition"],
            "references": [],
            "tools": [
                # WorkflowDefinition is a structural resource - no specific operational tools
            ],
            "examples": [{"name": "Document Processing Workflow"}],
        },
        "Reference": {
            "scope_usage": "FHIR-style reference to another resource instance.",
            "boundaries": "Does not carry the target resource; use read tools to resolve.",
            "relationships": ["References: Any resource by type/id"],
            "references": [],
            "tools": [
                # Reference is a data structure - no specific tools beyond general resource operations
            ],
            "examples": [{"reference": "Patient/123", "display": "Jane Doe"}],
        },
        "GraphDefinition": {
            "scope_usage": "FHIR-aligned graph of resource relationships for traversal and validation.",
            "boundaries": "Describes structure; not data.",
            "relationships": ["Links: source → target by path/type"],
            "references": [],
            "tools": [
                # GraphDefinition is a structural resource - no specific operational tools
            ],
            "examples": [{"name": "Patient Care Graph"}],
        },
        "Event": {
            "scope_usage": "Generic event aligned with FHIR's Event pattern for representing occurrences involving a subject (e.g., actions performed, measurements taken, events recorded). Provides uniform fields for agents to track status, timing, performers, and context where a specialized resource is unnecessary or not yet modeled.",
            "boundaries": "Do not use when a more specific resource exists (e.g., Procedure, MedicationAdministration, DiagnosticReport). Event is intended as a lightweight, generic wrapper to enable workflows and logging when specificity is not required.",
            "relationships": [
                "References: Patient via subject, Encounter via encounter, related orders via basedOn",
                "Links: partOf to larger events, instantiatesCanonical to protocols"
            ],
            "references": [
                "Patient.subject", "Encounter.encounter", "ServiceRequest in basedOn"
            ],
            "tools": [
                "create_event_tool", "update_event_status_tool", "add_event_performer_tool", "schedule_event_tool", "summarize_event_tool"
            ],
            "examples": [
                {"status": "in-progress", "subject": "Patient/123", "code": {"text": "Data review"}, "occurrenceDateTime": "2025-01-01T10:00:00Z"}
            ],
        },
        "MemoryBlock": {
            "scope_usage": "Agent memory item (episodic, semantic, working) for context engineering.",
            "boundaries": "Not a clinical record; may link to clinical resources as context.",
            "relationships": ["Referenced by: Agents; Indexed for retrieval"],
            "references": [],
            "tools": ["store_memory", "retrieve_memories"],
            "examples": [{"memory_type": "semantic", "content": "Patient prefers phone calls."}],
        },
        "AgentMessage": {
            "scope_usage": "Standardized agent message with tool calls and metadata.",
            "boundaries": "Not a clinical document; acts as a communication envelope.",
            "relationships": ["Used by: Agents and workflows"],
            "references": [],
            "tools": ["summarize_context", "select_tools_for_task"],
            "examples": [{"role": "user", "content": "Summarize this note."}],
        },
        "EpisodicMemory": {
            "scope_usage": "Time-stamped event memory used by agents to recall episodes.",
            "boundaries": "Use SemanticMemory for facts/concepts; WorkingMemory for short-lived context.",
            "relationships": ["Subtype of: MemoryBlock"],
            "references": [],
            "tools": ["store_memory", "retrieve_memories"],
            "examples": [{"memory_type": "episodic", "content": "Follow-up scheduled for next week."}],
        },
        "SemanticMemory": {
            "scope_usage": "Long-lived knowledge/facts to guide agent behavior and preferences.",
            "boundaries": "Not clinical truth; may be derived and should be auditable.",
            "relationships": ["Subtype of: MemoryBlock"],
            "references": [],
            "tools": ["store_memory", "retrieve_memories"],
            "examples": [{"memory_type": "semantic", "content": "Patient prefers phone over email."}],
        },
        "WorkingMemory": {
            "scope_usage": "Short-term, task-scoped memory for in-flight agent steps.",
            "boundaries": "Should be pruned/expired to avoid context poisoning.",
            "relationships": ["Subtype of: MemoryBlock"],
            "references": [],
            "tools": ["store_memory", "retrieve_memories", "prune_state"],
            "examples": [{"memory_type": "working", "content": "Current tool: summarize_context"}],
        },
        # ------------------------------------------------------------
        # Terminology resources (FHIR-aligned)
        # ------------------------------------------------------------
        "TerminologySystem": {
            "scope_usage": "Represents a terminology code system (e.g., SNOMED CT, LOINC, RxNorm, UMLS) used to encode clinical data.",
            "boundaries": "Does not include the full content of a code system; use external services for term lookup/expansion.",
            "relationships": [
                "Referenced by: ValueSet.includeSystems, TerminologyConcept.system_uri",
                "Supports: coding in clinical resources (Observation, Condition, Medication, etc.)"
            ],
            "references": [
                "ValueSet.include.system_uri",
                "TerminologyConcept.system_uri"
            ],
            "tools": [
                "get_possible_codes",
                "expand_value_set"
            ],
            "examples": [
                {"name": "SNOMED CT", "system_uri": "http://snomed.info/sct", "version": "2024-09"}
            ]
        },
        "TerminologyConcept": {
            "scope_usage": "A single coded concept from a terminology system providing code, display, definition, and relations.",
            "boundaries": "Not a clinical record; acts as a coding primitive used inside CodeableConcept and ValueSets.",
            "relationships": [
                "References: TerminologySystem via system_uri",
                "Referenced by: ValueSet.expanded_concepts"
            ],
            "references": ["ValueSet.expanded_concepts"],
            "tools": ["get_possible_codes"],
            "examples": [
                {"system_uri": "http://loinc.org", "code": "85354-9", "display": "Blood pressure panel"}
            ]
        },
        "ValueSet": {
            "scope_usage": "A curated set of concepts drawn from one or more terminology systems for use in coding and validation.",
            "boundaries": "Does not define a code system; use TerminologySystem for system metadata. Expansion may be partial.",
            "relationships": [
                "Includes: TerminologySystem URIs and TerminologyConcepts",
                "Used by: validation and UI pick-lists"
            ],
            "references": ["TerminologySystem", "TerminologyConcept"],
            "tools": ["expand_value_set", "validate_code_in_valueset"],
            "examples": [
                {"url": "http://example.org/fhir/ValueSet/vital-signs", "include_systems": [{"system_uri": "http://loinc.org"}]}
            ]
        },
        # ------------------------------------------------------------
        # Security and messaging (HACS-specific)
        # ------------------------------------------------------------
        "Actor": {
            "scope_usage": "Identity (human or agent) with role, permissions, and session context for secure interactions.",
            "boundaries": "Not a clinical resource. Use Practitioner for clinical staff records; Organization for facilities.",
            "relationships": [
                "References: Organization via organization",
                "Used by: auth, auditing, and tool access policies"
            ],
            "references": ["Organization"],
            "tools": ["authenticate_actor", "authorize_action"],
            "examples": [
                {"name": "Dr. Sarah Chen", "role": "physician", "permissions": ["patient:read", "observation:write"]}
            ]
        },
        "ActorPreference": {
            "scope_usage": "Declarative preferences for actors to shape tool behavior and context (e.g., response format, defaults).",
            "boundaries": "This is metadata for orchestration, not a clinical artifact.",
            "relationships": ["References: Actor via actor_id"],
            "references": ["Actor"],
            "tools": ["consult_preferences", "inject_preferences"],
            "examples": [
                {"actor_id": "actor-123", "key": "response_format", "value": {"markdown": True}, "scope": "workflow"}
            ]
        },
        "MessageDefinition": {
            "scope_usage": "Standardized agent message envelope and definition for inter-agent/tool communication.",
            "boundaries": "Not a clinical document; represents transport of instructions, content, and tool calls.",
            "relationships": ["Referenced by: AgentMessage as runtime specialization"],
            "references": [],
            "tools": ["standardize_messages", "log_llm_request"],
            "examples": [
                {"content": "Summarize this note.", "role": "user", "message_type": "text"}
            ]
        },
        "AgentMessage": {
            "scope_usage": "Runtime agent message with content, role, tool calls, and attachments for LLM workflows.",
            "boundaries": "Not persisted as a clinical record. Use Document/Composition for clinical narratives.",
            "relationships": ["Subtype of: MessageDefinition"],
            "references": [],
            "tools": ["standardize_messages", "semantic_tool_loadout"],
            "examples": [
                {"role": "assistant", "content": "BP 120/80. No acute issues.", "tool_calls": []}
            ]
        },
    }

    reg = get_model_registry()
    for name, meta in docs.items():
        cls = reg.get(name)
        if not cls:
            continue
        try:
            if meta.get("scope_usage") is not None:
                setattr(cls, "_doc_scope_usage", meta["scope_usage"])
            if meta.get("boundaries") is not None:
                setattr(cls, "_doc_boundaries", meta["boundaries"])
            if meta.get("relationships") is not None:
                setattr(cls, "_doc_relationships", meta["relationships"])
            if meta.get("references") is not None:
                setattr(cls, "_doc_references", meta["references"])
            if meta.get("tools") is not None:
                setattr(cls, "_doc_tools", meta["tools"])
            if meta.get("examples") is not None:
                setattr(cls, "_doc_examples", meta["examples"])
        except Exception:
            # Non-fatal; allow partial seeding
            pass


# Seed on import (can be overridden later by registry)
try:
    _seed_default_model_docs()
except Exception:
    pass

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
        MedicationStatement,
        Procedure,
        ServiceRequest,
        DiagnosticReport,
        DocumentReference,
        FamilyMemberHistory,
        Immunization,
        Appointment,
        CarePlan,
        CareTeam,
        NutritionOrder,
        PlanDefinition,
        PlanDefinitionGoal,
        PlanDefinitionAction,
        Practitioner,
        Organization,
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

        for resource_name, resource_class in registry.items():
            # Verify model has required base fields
            required_fields = {"id", "resource_type", "created_at", "updated_at"}
            if not required_fields.issubset(resource_class.model_fields.keys()):
                missing = required_fields - set(resource_class.model_fields.keys())
                raise ValueError(f"{resource_name} missing required fields: {missing}")

            # Verify model can be instantiated with minimal data
            try:
                # Special handling for models with specific requirements
                if resource_name == "Patient":
                    instance = resource_class(resource_type=resource_name, full_name="Test Patient")
                elif resource_name == "MemoryBlock":
                    instance = resource_class(resource_type="MemoryBlock", memory_type="semantic", content="Test content")
                elif resource_name == "EpisodicMemory":
                    instance = resource_class(memory_type="episodic", content="Test content")
                elif resource_name == "SemanticMemory":
                    instance = resource_class(memory_type="semantic", content="Test content")
                elif resource_name == "WorkingMemory":
                    instance = resource_class(memory_type="working", content="Test content")
                elif resource_name == "Observation":
                    from .observation import CodeableConcept
                    test_code = CodeableConcept(text="Test")
                    instance = resource_class(resource_type=resource_name, status="final", code=test_code)
                elif resource_name == "Encounter":
                    # Use proper field name (class not class_)
                    kwargs = {"resource_type": resource_name, "status": "planned"}
                    kwargs["class"] = "outpatient"  # Direct assignment to avoid alias issues
                    instance = resource_class(**kwargs)
                elif resource_name == "MedicationRequest":
                    from .observation import CodeableConcept
                    instance = resource_class(
                        resource_type=resource_name,
                        status="active",
                        intent="order",
                        subject="Patient/test",
                        medication_codeable_concept=CodeableConcept(text="TestMed")
                    )
                elif resource_name == "Procedure":
                    from .observation import CodeableConcept
                    instance = resource_class(
                        resource_type=resource_name,
                        status="completed",
                        code=CodeableConcept(text="TestProcedure"),
                        subject="Patient/test"
                    )
                elif resource_name == "Goal":
                    instance = resource_class(
                        resource_type=resource_name,
                        lifecycle_status="active",
                        description={"text": "Test Goal"},
                        subject="Patient/test"
                    )
                elif resource_name == "ServiceRequest":
                    from .observation import CodeableConcept
                    instance = resource_class(
                        resource_type=resource_name,
                        status="active",
                        intent="order",
                        subject="Patient/test",
                        code=CodeableConcept(text="TestService")
                    )
                elif resource_name == "PlanDefinitionGoal":
                    instance = resource_class(resource_type=resource_name, description="Goal Desc")
                elif resource_name == "DiagnosticReport":
                    from .observation import CodeableConcept
                    instance = resource_class(
                        resource_type=resource_name,
                        status="final",
                        code=CodeableConcept(text="Test Report")
                    )
                else:
                    instance = resource_class(resource_type=resource_name)

                if not instance.id or not instance.created_at:
                    raise ValueError(f"{resource_name} auto-generation not working")
            except Exception as e:
                raise ValueError(f"{resource_name} instantiation failed: {e}") from e

        return True

    except Exception as e:
        raise ValueError(f"Model compatibility validation failed: {e}") from e