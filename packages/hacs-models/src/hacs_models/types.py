"""
Common types and enums for HACS healthcare models.

This module defines all the enumerations, type aliases, and common data structures
used across HACS models. Designed for type safety, FHIR compliance, and 
excellent developer experience.

Key Features:
    - FHIR-compliant enumerations
    - Type aliases for complex types
    - Rich enum support with descriptions
    - Healthcare domain-specific types
    - Full type annotation support

Design Principles:
    - Comprehensive enum coverage for healthcare domains
    - Clear, descriptive enum values  
    - Type-safe constants and aliases
    - Performance optimized for runtime use
"""

from enum import Enum
from typing import Literal, Union


class HealthcareDomain(str, Enum):
    """
    Healthcare specialty domains for organizing resources and workflows.
    
    Based on medical specialty classifications and healthcare domains
    commonly used in clinical practice and healthcare systems.
    """
    # Primary care and general medicine
    PRIMARY_CARE = "primary_care"
    FAMILY_MEDICINE = "family_medicine"
    INTERNAL_MEDICINE = "internal_medicine"
    
    # Medical specialties
    CARDIOLOGY = "cardiology"
    DERMATOLOGY = "dermatology"
    ENDOCRINOLOGY = "endocrinology"
    GASTROENTEROLOGY = "gastroenterology"
    HEMATOLOGY = "hematology"
    NEPHROLOGY = "nephrology"
    NEUROLOGY = "neurology"
    ONCOLOGY = "oncology"
    PULMONOLOGY = "pulmonology"
    RHEUMATOLOGY = "rheumatology"
    
    # Surgical specialties
    GENERAL_SURGERY = "general_surgery"
    CARDIAC_SURGERY = "cardiac_surgery"
    NEUROSURGERY = "neurosurgery"
    ORTHOPEDIC_SURGERY = "orthopedic_surgery"
    PLASTIC_SURGERY = "plastic_surgery"
    
    # Emergency and critical care
    EMERGENCY = "emergency"
    CRITICAL_CARE = "critical_care"
    TRAUMA = "trauma"
    
    # Women's and children's health
    OBSTETRICS_GYNECOLOGY = "obstetrics_gynecology"
    PEDIATRICS = "pediatrics"
    NEONATOLOGY = "neonatology"
    
    # Mental health
    PSYCHIATRY = "psychiatry"
    PSYCHOLOGY = "psychology"
    BEHAVIORAL_HEALTH = "behavioral_health"
    
    # Diagnostic and therapeutic
    RADIOLOGY = "radiology"
    PATHOLOGY = "pathology"
    LABORATORY = "laboratory"
    PHARMACY = "pharmacy"
    
    # Rehabilitation and therapy
    PHYSICAL_THERAPY = "physical_therapy"
    OCCUPATIONAL_THERAPY = "occupational_therapy"
    SPEECH_THERAPY = "speech_therapy"
    
    # Administrative and support
    ADMINISTRATION = "administration"
    QUALITY_ASSURANCE = "quality_assurance"
    RESEARCH = "research"
    
    # General/unspecified
    GENERAL = "general"


class Gender(str, Enum):
    """
    Gender values following FHIR AdministrativeGender value set.
    
    Based on FHIR R4/R5 AdministrativeGender:
    http://hl7.org/fhir/administrative-gender
    """
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"


class ObservationStatus(str, Enum):
    """
    Status of observation following FHIR ObservationStatus value set.
    
    Based on FHIR R4/R5 ObservationStatus:
    http://hl7.org/fhir/observation-status
    """
    REGISTERED = "registered"           # Pre-observation state
    PRELIMINARY = "preliminary"         # Early/interim result
    FINAL = "final"                    # Final result available
    AMENDED = "amended"                # Result has been modified
    CORRECTED = "corrected"            # Result has been corrected
    CANCELLED = "cancelled"            # Observation cancelled
    ENTERED_IN_ERROR = "entered-in-error"  # Error in entry
    UNKNOWN = "unknown"                # Status not known


class EncounterStatus(str, Enum):
    """
    Status of encounter following FHIR EncounterStatus value set.
    
    Based on FHIR R4/R5 EncounterStatus:
    http://hl7.org/fhir/encounter-status
    """
    PLANNED = "planned"                # Planned encounter
    ARRIVED = "arrived"                # Patient arrived
    TRIAGED = "triaged"               # Patient triaged
    IN_PROGRESS = "in-progress"        # Encounter in progress
    ONLEAVE = "onleave"               # Temporarily suspended
    FINISHED = "finished"             # Encounter completed
    CANCELLED = "cancelled"           # Encounter cancelled
    ENTERED_IN_ERROR = "entered-in-error"  # Error in entry
    UNKNOWN = "unknown"               # Status not known


class ConditionClinicalStatus(str, Enum):
    """
    Clinical status of condition following FHIR ConditionClinicalStatus.
    
    Based on FHIR R4/R5 ConditionClinicalStatus:
    http://terminology.hl7.org/CodeSystem/condition-clinical
    """
    ACTIVE = "active"                 # Condition is active
    RECURRENCE = "recurrence"         # Condition has recurred
    RELAPSE = "relapse"               # Condition has relapsed
    INACTIVE = "inactive"             # Condition is inactive
    REMISSION = "remission"           # Condition in remission
    RESOLVED = "resolved"             # Condition resolved


class ConditionVerificationStatus(str, Enum):
    """
    Verification status of condition following FHIR ConditionVerificationStatus.
    
    Based on FHIR R4/R5 ConditionVerificationStatus:
    http://terminology.hl7.org/CodeSystem/condition-ver-status
    """
    UNCONFIRMED = "unconfirmed"       # Condition unconfirmed
    PROVISIONAL = "provisional"        # Condition provisional
    DIFFERENTIAL = "differential"      # One of differential diagnoses
    CONFIRMED = "confirmed"           # Condition confirmed
    REFUTED = "refuted"               # Condition refuted
    ENTERED_IN_ERROR = "entered-in-error"  # Error in entry


class MedicationRequestStatus(str, Enum):
    """
    Status of medication request following FHIR MedicationRequestStatus.
    
    Based on FHIR R4/R5 MedicationRequestStatus:
    http://hl7.org/fhir/CodeSystem/medicationrequest-status
    """
    ACTIVE = "active"                 # Request is active
    ON_HOLD = "on-hold"              # Request on hold
    CANCELLED = "cancelled"           # Request cancelled
    COMPLETED = "completed"           # Request completed
    ENTERED_IN_ERROR = "entered-in-error"  # Error in entry
    STOPPED = "stopped"               # Request stopped
    DRAFT = "draft"                   # Request in draft
    UNKNOWN = "unknown"               # Status unknown


class ProcedureStatus(str, Enum):
    """
    Status of procedure following FHIR EventStatus value set.
    
    Based on FHIR R4/R5 EventStatus:
    http://hl7.org/fhir/event-status
    """
    PREPARATION = "preparation"        # Procedure in preparation
    IN_PROGRESS = "in-progress"        # Procedure in progress
    NOT_DONE = "not-done"             # Procedure not performed
    ON_HOLD = "on-hold"               # Procedure on hold
    STOPPED = "stopped"               # Procedure stopped
    COMPLETED = "completed"           # Procedure completed
    ENTERED_IN_ERROR = "entered-in-error"  # Error in entry
    UNKNOWN = "unknown"               # Status unknown


class GoalLifecycleStatus(str, Enum):
    """
    Lifecycle status of goal following FHIR GoalLifecycleStatus.
    
    Based on FHIR R4/R5 GoalLifecycleStatus:
    http://hl7.org/fhir/goal-status
    """
    PROPOSED = "proposed"             # Goal proposed
    PLANNED = "planned"               # Goal planned
    ACCEPTED = "accepted"             # Goal accepted
    ACTIVE = "active"                 # Goal active
    ON_HOLD = "on-hold"              # Goal on hold
    COMPLETED = "completed"           # Goal completed
    CANCELLED = "cancelled"           # Goal cancelled
    ENTERED_IN_ERROR = "entered-in-error"  # Error in entry
    REJECTED = "rejected"             # Goal rejected


class ContactPointSystem(str, Enum):
    """
    Contact point system following FHIR ContactPointSystem value set.
    
    Based on FHIR R4/R5 ContactPointSystem:
    http://hl7.org/fhir/contact-point-system
    """
    PHONE = "phone"                   # Phone number
    FAX = "fax"                       # Fax number
    EMAIL = "email"                   # Email address  
    PAGER = "pager"                   # Pager number
    URL = "url"                       # URL/website
    SMS = "sms"                       # SMS number
    OTHER = "other"                   # Other system


class ContactPointUse(str, Enum):
    """
    Contact point use following FHIR ContactPointUse value set.
    
    Based on FHIR R4/R5 ContactPointUse:
    http://hl7.org/fhir/contact-point-use
    """
    HOME = "home"                     # Home contact
    WORK = "work"                     # Work contact
    TEMP = "temp"                     # Temporary contact
    OLD = "old"                       # Old/incorrect contact
    MOBILE = "mobile"                 # Mobile contact


class AddressUse(str, Enum):
    """
    Address use following FHIR AddressUse value set.
    
    Based on FHIR R4/R5 AddressUse:
    http://hl7.org/fhir/address-use
    """
    HOME = "home"                     # Home address
    WORK = "work"                     # Work address
    TEMP = "temp"                     # Temporary address
    OLD = "old"                       # Old/incorrect address
    BILLING = "billing"               # Billing address


class AddressType(str, Enum):
    """
    Address type following FHIR AddressType value set.
    
    Based on FHIR R4/R5 AddressType:
    http://hl7.org/fhir/address-type
    """
    POSTAL = "postal"                 # Postal address
    PHYSICAL = "physical"             # Physical address
    BOTH = "both"                     # Both postal and physical


class IdentifierUse(str, Enum):
    """
    Identifier use following FHIR IdentifierUse value set.
    
    Based on FHIR R4/R5 IdentifierUse:
    http://hl7.org/fhir/identifier-use
    """
    USUAL = "usual"                   # Usual identifier
    OFFICIAL = "official"             # Official identifier
    TEMP = "temp"                     # Temporary identifier
    SECONDARY = "secondary"           # Secondary identifier
    OLD = "old"                       # Old/incorrect identifier


class NameUse(str, Enum):
    """
    Name use following FHIR NameUse value set.
    
    Based on FHIR R4/R5 NameUse:
    http://hl7.org/fhir/name-use
    """
    USUAL = "usual"                   # Usual name
    OFFICIAL = "official"             # Official name
    TEMP = "temp"                     # Temporary name
    NICKNAME = "nickname"             # Nickname
    ANONYMOUS = "anonymous"           # Anonymous name
    OLD = "old"                       # Old/incorrect name
    MAIDEN = "maiden"                 # Maiden name


class MessageRole(str, Enum):
    """
    Role of message sender in agent communication.
    
    Used for AI agent message routing and conversation management.
    """
    SYSTEM = "system"                 # System message
    USER = "user"                     # User/human message
    ASSISTANT = "assistant"           # AI assistant message
    AGENT = "agent"                   # AI agent message
    FUNCTION = "function"             # Function/tool response
    OBSERVER = "observer"             # Observer/monitoring message


class MessageType(str, Enum):
    """
    Type of message content in agent communication.
    
    Used for message processing and routing in AI agent systems.
    """
    TEXT = "text"                     # Plain text message
    STRUCTURED = "structured"         # Structured data message
    FUNCTION_CALL = "function_call"   # Function/tool call
    FUNCTION_RESULT = "function_result"  # Function/tool result
    MEMORY = "memory"                 # Memory operation
    WORKFLOW = "workflow"             # Workflow instruction
    ERROR = "error"                   # Error message
    STATUS = "status"                 # Status update


class BundleType(str, Enum):
    """
    Type of bundle following FHIR BundleType value set.
    
    Based on FHIR R4/R5 BundleType:
    http://hl7.org/fhir/bundle-type
    """
    DOCUMENT = "document"             # Document bundle
    MESSAGE = "message"               # Message bundle
    TRANSACTION = "transaction"       # Transaction bundle
    TRANSACTION_RESPONSE = "transaction-response"  # Transaction response
    BATCH = "batch"                   # Batch bundle
    BATCH_RESPONSE = "batch-response"  # Batch response
    HISTORY = "history"               # History bundle
    SEARCHSET = "searchset"           # Search result set
    COLLECTION = "collection"         # Collection bundle


# Type aliases for commonly used complex types
ResourceReference = str  # FHIR reference string like "Patient/123"
CodeValue = str         # Code value from terminology system
SystemUrl = str         # System URL for code systems
TimestampStr = str      # ISO 8601 timestamp string
UuidStr = str          # UUID string
UrlStr = str           # HTTP/HTTPS URL string

# Union types for flexibility  
StatusType = Union[
    ObservationStatus,
    EncounterStatus, 
    ConditionClinicalStatus,
    MedicationRequestStatus,
    ProcedureStatus,
    GoalLifecycleStatus,
]

ContactType = Union[ContactPointSystem, ContactPointUse]
AddressInfo = Union[AddressUse, AddressType]
IdentifierInfo = Union[IdentifierUse, NameUse]

# Literal types for specific use cases
GenderLiteral = Literal["male", "female", "other", "unknown"]
DomainLiteral = Literal[
    "primary_care", "cardiology", "dermatology", "emergency", 
    "pediatrics", "psychiatry", "general"
]