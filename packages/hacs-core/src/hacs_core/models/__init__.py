"""
HACS Models - Pydantic models for healthcare agent applications.

This package provides comprehensive healthcare data models optimized for
structured outputs and LLM interactions.
"""

from hacs_core.utils import VersionManager

__version__ = VersionManager.CORE_VERSION

# US Core Models
# Clinical Reasoning Models
from .activity_definition import (
    ActivityDefinition,
    ActivityDefinitionKind,
    ActivityDefinitionStatus,
    ParticipantType,
    RequestIntent,
    RequestPriority,
)

# Core Models
from .agent_message import AgentMessage, MessagePriority, MessageRole, MessageType
from .appointment import (
    Appointment,
    AppointmentStatus,
    AppointmentCancellationReason,
    ParticipantType as AppointmentParticipantType,
    ParticipationStatus,
    AppointmentRecurrenceType,
    WeekOfMonth,
    DaysOfWeek,
    AppointmentPriority,
    VirtualServiceDetail,
    WeeklyTemplate,
    MonthlyTemplate,
    YearlyTemplate,
    RecurrenceTemplate,
    AppointmentParticipant,
    MedicalAppointment,
    TelehealthAppointment,
    ConsultationAppointment,
    FollowUpAppointment,
    EmergencyAppointment,
)
from .allergy_intolerance import (
    AllergyIntolerance,
    AllergyIntoleranceCategory,
    AllergyIntoleranceCriticality,
    AllergyIntoleranceReaction,
    AllergyIntoleranceStatus,
    AllergyIntoleranceType,
    AllergyIntoleranceVerificationStatus,
    ReactionSeverity,
)
from .condition import (
    Condition,
    ConditionCategory,
    ConditionClinicalStatus,
    ConditionSeverity,
    ConditionVerificationStatus,
    ConditionBodySite,
    ConditionStageType,
    Problem,  # Alias for Condition
)
from .context import ContextSummary, ScratchpadEntry
from .data_requirement import DataRequirement, SortDirection
from .encounter import (
    Encounter,
    EncounterClass,
    EncounterStatus,
    LocationStatus,
)
from .encounter import (
    ParticipantType as EncounterParticipantType,
)
from .evidence_variable import (
    ArtifactAssessment,
    ArtifactAssessmentDisposition,
    ArtifactAssessmentWorkflowStatus,
    EvidenceVariable,
    EvidenceVariableHandling,
    EvidenceVariableStatus,
)
from .family_member_history import (
    FamilyMemberHistory,
    FamilyHistoryStatus,
    FamilyHistoryAbsentReason,
    FamilyMemberRelationship,
    AdministrativeGender as FamilyAdministrativeGender,
    ConditionOutcome as FamilyConditionOutcome,
    ParticipationFunction,
    FamilyMemberHistoryParticipant,
    FamilyMemberCondition,
    FamilyMemberProcedure,
    FamilyHistory,
    GeneticHistory,
    FamilialRiskAssessment,
)
from .guidance_response import (
    GuidanceResponse,
    GuidanceResponseStatus,
    RequestOrchestration,
    RequestOrchestrationAction,
    RequestStatus,
)
from .guidance_response import (
    RequestIntent as GuidanceRequestIntent,
)
from .guidance_response import (
    RequestPriority as GuidanceRequestPriority,
)
from .goal import (
    Goal,
    GoalLifecycleStatus,
    GoalAchievementStatus,
    GoalCategory,
    GoalPriority,
    GoalTimeframe,
    GoalMeasureType,
    CareGoal,
    PatientGoal,
    TreatmentGoal,
)
from .knowledge import KnowledgeItem
from .library import (
    AttachmentContentType,
    Library,
    LibraryStatus,
    LibraryType,
)
from .medication import (
    Medication,
    MedicationForm,
    MedicationStatus,
)
from .medication_request import (
    MedicationRequest,
    MedicationRequestCategory,
    MedicationRequestIntent,
    MedicationRequestPriority,
    MedicationRequestStatus,
)
from .memory import Memory, MemoryType
from .observation import (
    DataAbsentReason,
    Observation,
    ObservationCategory,
    ObservationStatus,
)
from .patient import (
    AdministrativeGender,
    ContactPointSystem,
    ContactPointUse,
    IdentifierType,
    IdentifierUse,
    Patient,
)
from .plan_definition import (
    ActionCardinalityBehavior,
    ActionConditionKind,
    ActionPrecheckBehavior,
    ActionRelationshipType,
    ActionRequiredBehavior,
    ActionSelectionBehavior,
    PlanDefinition,
    PlanDefinitionAction,
    PlanDefinitionStatus,
    PlanDefinitionType,
)
from .procedure import (
    Procedure,
    ProcedureStatus,
    ProcedureCategory,
    ProcedureBodySite,
    ProcedureOutcome,
    ProcedureUrgency,
)
from .service_request import (
    ServiceRequest,
    RequestStatus as ServiceRequestStatus,
    RequestIntent as ServiceRequestIntent,
    RequestPriority as ServiceRequestPriority,
    ServiceCategory,
    PerformerRole,
    ServiceRequestOrderDetail,
    ServiceRequestParameter,
    ServiceRequestPatientInstruction,
    DiagnosticOrder,
    ProcedureRequest,
    ReferralRequest,
    TherapyOrder,
    ConsultationRequest,
)
from .task import (
    Task,
    TaskStatus,
    TaskIntent,
    TaskPriority,
    TaskCode,
    TaskPerformerFunction,
    TaskBusinessStatus,
    TaskPerformer,
    TaskRestriction,
    TaskInput,
    TaskOutput,
    WorkflowTask,
    FulfillmentTask,
    ApprovalTask,
    ReviewTask,
    SchedulingTask,
)
from .risk_assessment import (
    RiskAssessment,
    RiskAssessmentPrediction,
    ObservationStatus as RiskObservationStatus,
    RiskAssessmentMethod,
    RiskAssessmentCode,
    RiskProbability,
    RiskOutcome,
    RiskTimeframe,
    GeneticRiskAssessment,
    CardiacRiskAssessment,
    CancerRiskAssessment,
    SurgicalRiskAssessment,
    ClinicalRiskAssessment,
)
from .resource_bundle import (
    ResourceBundle,
    BundleType,
    BundleStatus,
    WorkflowBindingType,
    LinkRelation,
    BundleLink,
    WorkflowBinding,
    BundleSearchInfo,
    BundleEntry,
    UseCase,
    Misuse,
    BundleUpdate,
    create_resource_stack,
    create_search_results_bundle,
    create_workflow_template_bundle,
)
from .organization import Organization, OrganizationContact, OrganizationQualification
from .document import (
    Document,
    DocumentStatus,
    DocumentType,
    ConfidentialityLevel,
    DocumentAuthor,
    DocumentAttester,
    DocumentSection,
    DocumentEncounter,
    create_discharge_summary,
    create_progress_note,
    create_consultation_note,
    create_clinical_summary,
)
from .workflow import (
    # Base Workflow Patterns
    WorkflowDefinition,
    WorkflowRequest,
    WorkflowEvent,
    # Enums (using aliases to avoid conflicts)
    WorkflowStatus,
    RequestIntent as WorkflowRequestIntent,
    RequestPriority as WorkflowRequestPriority,
    EventStatus,
    TaskStatus as WorkflowTaskStatus,
    TaskIntent as WorkflowTaskIntent,
    ActivityDefinitionKind as WorkflowActivityDefinitionKind,
    # Core Resources (using aliases to avoid conflicts)
    Task as WorkflowTaskResource,
    ActivityDefinition as WorkflowActivityDefinition,
    PlanDefinition as WorkflowPlanDefinition,
    PlanDefinitionAction as WorkflowPlanDefinitionAction,
    ServiceRequest as WorkflowServiceRequest,
    WorkflowExecution,
    # Supporting Types
    WorkflowParticipant,
    WorkflowInput,
    WorkflowOutput,
    # Factory Functions
    create_simple_task,
    create_document_processing_workflow,
    create_clinical_workflow_execution,
)

__all__ = [
    # Patient model and enums
    "Patient",
    "AdministrativeGender",
    "IdentifierUse",
    "IdentifierType",
    "ContactPointSystem",
    "ContactPointUse",
    # AgentMessage model and enums
    "AgentMessage",
    "MessageRole",
    "MessageType",
    "MessagePriority",
    # Encounter model and enums
    "Encounter",
    "EncounterStatus",
    "EncounterClass",
    "EncounterParticipantType",
    "LocationStatus",
    # Observation model and enums
    "Observation",
    "ObservationStatus",
    "ObservationCategory",
    "DataAbsentReason",
    # Memory model and enums
    "Memory",
    "MemoryType",
    # Knowledge model
    "KnowledgeItem",
    # Context models
    "ScratchpadEntry",
    "ContextSummary",
    # US Core Models - AllergyIntolerance
    "AllergyIntolerance",
    "AllergyIntoleranceReaction",
    "AllergyIntoleranceType",
    "AllergyIntoleranceCategory",
    "AllergyIntoleranceCriticality",
    "AllergyIntoleranceStatus",
    "AllergyIntoleranceVerificationStatus",
    "ReactionSeverity",
    # US Core Models - Condition
    "Condition",
    "ConditionClinicalStatus",
    "ConditionVerificationStatus",
    "ConditionCategory",
    "ConditionSeverity",
    "ConditionBodySite",
    "ConditionStageType",
    "Problem",
    # US Core Models - Medication
    "Medication",
    "MedicationStatus",
    "MedicationForm",
    # US Core Models - MedicationRequest
    "MedicationRequest",
    "MedicationRequestStatus",
    "MedicationRequestIntent",
    "MedicationRequestPriority",
    "MedicationRequestCategory",
    # Clinical Reasoning models - PlanDefinition
    "PlanDefinition",
    "PlanDefinitionAction",
    "PlanDefinitionStatus",
    "PlanDefinitionType",
    "ActionCardinalityBehavior",
    "ActionConditionKind",
    "ActionPrecheckBehavior",
    "ActionRelationshipType",
    "ActionRequiredBehavior",
    "ActionSelectionBehavior",
    # Clinical Reasoning models - ActivityDefinition
    "ActivityDefinition",
    "ActivityDefinitionKind",
    "ActivityDefinitionStatus",
    "ParticipantType",
    "RequestIntent",
    "RequestPriority",
    # Clinical Reasoning models - Library
    "Library",
    "LibraryStatus",
    "LibraryType",
    "AttachmentContentType",
    # Clinical Reasoning models - Guidance and Orchestration
    "GuidanceResponse",
    "GuidanceResponseStatus",
    "RequestOrchestration",
    "RequestOrchestrationAction",
    "GuidanceRequestIntent",
    "GuidanceRequestPriority",
    "RequestStatus",
    # Clinical Reasoning models - Data Requirements
    "DataRequirement",
    "SortDirection",
    # Enhanced Evidence Framework
    "EvidenceVariable",
    "EvidenceVariableStatus",
    "EvidenceVariableHandling",
    "ArtifactAssessment",
    "ArtifactAssessmentWorkflowStatus",
    "ArtifactAssessmentDisposition",
    # Procedure model and enums
    "Procedure",
    "ProcedureStatus",
    "ProcedureCategory",
    "ProcedureBodySite",
    "ProcedureOutcome",
    "ProcedureUrgency",
    # Goal model and enums
    "Goal",
    "GoalLifecycleStatus",
    "GoalAchievementStatus",
    "GoalCategory",
    "GoalPriority",
    "GoalTimeframe",
    "GoalMeasureType",
    "CareGoal",
    "PatientGoal",
    "TreatmentGoal",
    # Appointment model and enums
    "Appointment",
    "AppointmentStatus",
    "AppointmentCancellationReason",
    "AppointmentParticipantType",
    "ParticipationStatus",
    "AppointmentRecurrenceType",
    "WeekOfMonth",
    "DaysOfWeek",
    "AppointmentPriority",
    "VirtualServiceDetail",
    "WeeklyTemplate",
    "MonthlyTemplate",
    "YearlyTemplate",
    "RecurrenceTemplate",
    "AppointmentParticipant",
    "MedicalAppointment",
    "TelehealthAppointment",
    "ConsultationAppointment",
    "FollowUpAppointment",
    "EmergencyAppointment",
    # FamilyMemberHistory model and enums
    "FamilyMemberHistory",
    "FamilyHistoryStatus",
    "FamilyHistoryAbsentReason",
    "FamilyMemberRelationship",
    "FamilyAdministrativeGender",
    "FamilyConditionOutcome",
    "ParticipationFunction",
    "FamilyMemberHistoryParticipant",
    "FamilyMemberCondition",
    "FamilyMemberProcedure",
    "FamilyHistory",
    "GeneticHistory",
    "FamilialRiskAssessment",
    # ServiceRequest model and enums
    "ServiceRequest",
    "ServiceRequestStatus",
    "ServiceRequestIntent",
    "ServiceRequestPriority",
    "ServiceCategory",
    "PerformerRole",
    "ServiceRequestOrderDetail",
    "ServiceRequestParameter",
    "ServiceRequestPatientInstruction",
    "DiagnosticOrder",
    "ProcedureRequest",
    "ReferralRequest",
    "TherapyOrder",
    "ConsultationRequest",
    # Task model and enums
    "Task",
    "TaskStatus",
    "TaskIntent",
    "TaskPriority",
    "TaskCode",
    "TaskPerformerFunction",
    "TaskBusinessStatus",
    "TaskPerformer",
    "TaskRestriction",
    "TaskInput",
    "TaskOutput",
    "WorkflowTask",
    "FulfillmentTask",
    "ApprovalTask",
    "ReviewTask",
    "SchedulingTask",
    # RiskAssessment model and enums
    "RiskAssessment",
    "RiskAssessmentPrediction",
    "RiskObservationStatus",
    "RiskAssessmentMethod",
    "RiskAssessmentCode",
    "RiskProbability",
    "RiskOutcome",
    "RiskTimeframe",
    "GeneticRiskAssessment",
    "CardiacRiskAssessment",
    "CancerRiskAssessment",
    "SurgicalRiskAssessment",
    "ClinicalRiskAssessment",
    # ResourceBundle model and related types
    "ResourceBundle",
    "BundleType",
    "BundleStatus",
    "WorkflowBindingType",
    "LinkRelation",
    "BundleLink",
    "WorkflowBinding",
    "BundleSearchInfo",
    "BundleEntry",
    "UseCase",
    "Misuse",
    "BundleUpdate",
    "create_resource_stack",
    "create_search_results_bundle",
    "create_workflow_template_bundle",
    "Organization",
    "OrganizationContact",
    "OrganizationQualification",
    # Document model and related types
    "Document",
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
    # Workflow model and related types
    "WorkflowDefinition",
    "WorkflowRequest",
    "WorkflowEvent",
    "WorkflowStatus",
    "WorkflowRequestIntent",
    "WorkflowRequestPriority",
    "EventStatus",
    "WorkflowTaskStatus",
    "WorkflowTaskIntent",
    "WorkflowActivityDefinitionKind",
    "WorkflowTaskResource",
    "WorkflowActivityDefinition",
    "WorkflowPlanDefinition",
    "WorkflowPlanDefinitionAction",
    "WorkflowServiceRequest",
    "WorkflowExecution",
    "WorkflowParticipant",
    "WorkflowInput",
    "WorkflowOutput",
    "create_simple_task",
    "create_document_processing_workflow",
    "create_clinical_workflow_execution",
]


def hello() -> str:
    return "Hello from hacs-models!"
