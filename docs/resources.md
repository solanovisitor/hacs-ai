# HACS Resource Catalog

Generated on 2025-08-18T17:19:51.358969Z

This comprehensive catalog documents every HACS resource organized by domain and purpose. Each resource includes detailed specifications with resource-specific tools only, validated against the actual HACS implementation.

---

## Core Models

Foundation classes and base structures that all HACS models inherit from

### BaseResource

**Scope & Usage**

BaseResource is the foundational Pydantic model for all HACS healthcare resources, providing automatic ID generation, timestamp management, and type-safe validation. Every HACS resource (Patient, Observation, Actor, etc.) inherits from BaseResource to gain essential infrastructure: unique identification with resource-type prefixes, audit trails with created_at/updated_at timestamps, version tracking, and protocol compliance for serialization and validation. Designed specifically for LLM agent communication with JSON Schema generation, subset model creation via pick(), and optimized serialization for AI workflows.

**Boundaries**

BaseResource is an abstract foundation class - extend it to create custom resource types, but use existing domain resources (Patient, Observation, etc.) for standard healthcare data. Contains only infrastructure (ID, timestamps, validation) - no clinical or business logic. Not for general-purpose data modeling outside healthcare contexts. All subclasses must provide a resource_type field for proper identification and routing.

**Relationships**

- Extended by: All HACS resources either directly or through DomainResource
- Implements: Identifiable, Timestamped, Versioned, Serializable, Validatable protocols
- Used by: save_resource, read_resource, validate_resource, and all HACS persistence tools
- Referenced via: Reference objects using 'ResourceType/id' format
- Grouped in: ResourceBundle collections for batch operations

**References**

- Reference.reference field uses 'ResourceType/id' format pointing to BaseResource instances
- ResourceBundle.entry contains BaseResource instances
- All HACS database tools operate on BaseResource subclasses


**Example**

=== "Rendered"

    #### HealthcareResource

    | Field | Value |
    |---|---|
    | resource_type | HealthcareResource |
    | id | healthcareresource-b4e8e7c9 |
    | name | Clinical Data Point |
    | created_at | 2025-08-18T17:19:51.359925Z |
    | updated_at | 2025-08-18T17:19:51.359927Z |

=== "JSON"

    ```json
    {
      "id": "healthcareresource-b4e8e7c9",
      "created_at": "2025-08-18T17:19:51.359925Z",
      "updated_at": "2025-08-18T17:19:51.359927Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "HealthcareResource",
      "agent_context": null,
      "name": "Clinical Data Point",
      "category": "vital-signs"
    }
    ```

=== "YAML"

    ```yaml
    id: healthcareresource-b4e8e7c9
    created_at: '2025-08-18T17:19:51.359925Z'
    updated_at: '2025-08-18T17:19:51.359927Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: HealthcareResource
    agent_context: null
    name: Clinical Data Point
    category: vital-signs
    
    ```

=== "Schema"

    #### HealthcareResource Schema

    Foundation class for all HACS healthcare resources.

    Provides essential functionality for healthcare data models including
    automatic ID generation, timestamp management, and type-safe operations.

    This class follows FHIR R4/R5 base resource patterns while optimizing
    for AI agent communication and modern Python development practices.

    **Protocol Compliance:**
        Implements: Identifiable, Timestamped, Versioned, Serializable, Validatable

        This ensures all HACS resources follow standardized contracts for:
        - Unique identification (id field)
        - Audit trails (created_at, updated_at)
        - Version tracking (version field)
        - Data interchange (to_dict, from_dict)
        - Validation (validate, is_valid)

    Features:
        - Auto-generated UUIDs if ID not provided
        - Automatic timestamp management
        - Type-safe field access and validation
        - JSON Schema generation with examples
        - Subset model creation for specific use cases
        - Performance optimized serialization
        - Protocol-based interface contracts

    Example:
        >>> class MyResource(BaseResource):
        ...     name: str
        ...     value: int = 0
        >>>
        >>> resource = MyResource(resource_type="MyResource", name="test")
        >>> print(resource.id)  # Auto-generated: myresource-a1b2c3d4
        >>> print(resource.created_at)  # Auto-set to current time
        >>> isinstance(resource, Identifiable)  # True - protocol compliance

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Version of the resource |
    | identifier | list[str] | External identifiers for the resource (e.g., MRN, accession, system-specific IDs) (e.g., ['MRN:12345', 'local:abc-001']) |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | <class 'str'> | Type identifier for this resource (Patient, Observation, etc.) (e.g., Patient) |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | name | <class 'str'> | None |
    | category | <class 'str'> | None |



### DomainResource

**Scope & Usage**

DomainResource extends BaseResource with FHIR R4-compliant fields for clinical and healthcare domain resources. Adds status tracking (active/inactive/draft), human-readable text narratives for clinical review, contained resource support, and extension mechanisms for additional healthcare data. All clinical HACS resources (Patient, Observation, Procedure, Condition, etc.) inherit from DomainResource to gain these healthcare-specific capabilities. Essential for LLM agents processing clinical data as it provides standardized status lifecycle, text summaries for context, and extension points for AI-generated metadata.

**Boundaries**

Use DomainResource for clinical and healthcare domain resources that need status tracking, text narratives, or contained resources. Use BaseResource directly for non-clinical infrastructure resources (Actor, MessageDefinition, workflow definitions). DomainResource provides the healthcare domain patterns but not specific clinical logic - that belongs in concrete implementations like Patient or Observation.

**Relationships**

- Inherits from: BaseResource (gains ID, timestamps, validation, protocols)
- Extended by: Patient, Observation, Procedure, Condition, DiagnosticReport, and all clinical resources
- Implements: ClinicalResource protocol with get_patient_id() method
- Contains: Other BaseResource instances via contained field
- Extends: Healthcare vocabularies and systems via extension mechanism

**References**

- Clinical resources inherit DomainResource patterns: status, text, contained, extension
- Contained resources are embedded DomainResource instances for inline data
- Extensions reference HL7 FHIR StructureDefinitions and custom healthcare vocabularies


**Example**

=== "Rendered"

    #### ClinicalProtocol

    | Field | Value |
    |---|---|
    | resource_type | ClinicalProtocol |
    | id | clinicalprotocol-7e81f103 |
    | status | active |
    | created_at | 2025-08-18T17:19:51.361665Z |
    | updated_at | 2025-08-18T17:19:51.361665Z |

=== "JSON"

    ```json
    {
      "id": "clinicalprotocol-7e81f103",
      "created_at": "2025-08-18T17:19:51.361665Z",
      "updated_at": "2025-08-18T17:19:51.361665Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "ClinicalProtocol",
      "agent_context": null,
      "status": "active",
      "text": "HbA1c monitoring protocol with quarterly assessments",
      "contained": null,
      "extension": null,
      "modifier_extension": null,
      "title": "Diabetes Management Protocol"
    }
    ```

=== "YAML"

    ```yaml
    id: clinicalprotocol-7e81f103
    created_at: '2025-08-18T17:19:51.361665Z'
    updated_at: '2025-08-18T17:19:51.361665Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: ClinicalProtocol
    agent_context: null
    status: active
    text: HbA1c monitoring protocol with quarterly assessments
    contained: null
    extension: null
    modifier_extension: null
    title: Diabetes Management Protocol
    
    ```

=== "Schema"

    #### ClinicalProtocol Schema

    Base class for domain-specific healthcare resources.

    Extends BaseResource with additional fields and functionality
    specific to FHIR domain resources (Patient, Observation, etc.).

    This follows FHIR's DomainResource pattern where most clinical
    resources inherit common patterns like text, contained resources,
    extensions, and modifierExtensions.

    **Protocol Compliance:**
        Implements: ClinicalResource protocol patterns

        This ensures all clinical resources provide:
        - Patient ID association (get_patient_id method)
        - Status tracking (status field)
        - Resource type identification (inherited from BaseResource)

    Features:
        - Human-readable text representation
        - Support for contained resources
        - Extension mechanism for additional data
        - Modifier extensions for data that changes meaning
        - Clinical resource protocol compliance

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Version of the resource |
    | identifier | list[str] | External identifiers for the resource (e.g., MRN, accession, system-specific IDs) (e.g., ['MRN:12345', 'local:abc-001']) |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | <class 'str'> | Type identifier for this resource (Patient, Observation, etc.) (e.g., Patient) |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | status | <class 'str'> | Current status of the resource (e.g., active) |
    | text | str | None | Human-readable summary of the resource content (e.g., Patient John Doe, 45 years old) |
    | contained | list[hacs_models.base_resource.BaseResource] | None | Resources contained within this resource |
    | extension | dict[str, typing.Any] | None | Additional content defined by implementations (e.g., {'url': 'custom-field', 'valueString': 'custom-value'}) |
    | modifier_extension | dict[str, typing.Any] | None | Extensions that cannot be ignored (e.g., {'url': 'critical-field', 'valueBoolean': True}) |
    | title | <class 'str'> | None |



### Reference

**Scope & Usage**

FHIR-style reference to another resource instance.

**Boundaries**

Does not carry the target resource; use read tools to resolve.

**Relationships**

- References: Any resource by type/id


**Example**

=== "Rendered"

    #### Reference

    | Field | Value |
    |---|---|
    | resource_type | Reference |

=== "JSON"

    ```json
    {
      "reference": "Patient/patient-12345",
      "type": "Patient",
      "identifier": null,
      "display": "Maria Rodriguez"
    }
    ```

=== "YAML"

    ```yaml
    reference: Patient/patient-12345
    type: Patient
    identifier: null
    display: Maria Rodriguez
    
    ```

=== "Schema"

    #### Reference Schema

    Minimal FHIR-style Reference type used to point from one resource to another.

    Fields:
      - reference: Literal reference string (e.g., "Patient/123", relative/absolute URL, or internal "#id")
      - type: Type the reference refers to (e.g., "Patient")
      - identifier: Logical reference payload when literal reference is not known
      - display: Text alternative for the resource

    | Field | Type | Description |
    |---|---|---|
    | reference |  | Literal reference string (Type/id or URL) |
    | type |  | Type of the referenced resource, e.g., 'Patient' |
    | identifier |  | Logical reference when literal is unknown |
    | display |  | Text representation for display |



### ResourceBundle

**Scope & Usage**

Logical grouping of resources for transfer or template.

**Boundaries**

Not a long-term canonical store; persist individual resources.

**Relationships**

- Contains entries with resources

**Tools**

- add_bundle_entries
- validate_bundle


**Example**

=== "Rendered"

    #### ResourceBundle

    | Field | Value |
    |---|---|
    | resource_type | ResourceBundle |
    | id | resourcebundle-606fde34 |
    | status | draft |
    | created_at | 2025-08-18T17:19:51.362711Z |
    | updated_at | 2025-08-18T17:19:51.362712Z |

=== "JSON"

    ```json
    {
      "id": "resourcebundle-606fde34",
      "created_at": "2025-08-18T17:19:51.362711Z",
      "updated_at": "2025-08-18T17:19:51.362712Z",
      "version": null,
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "ResourceBundle",
      "agent_context": null,
      "title": null,
      "bundle_type": null,
      "entries": [],
      "status": "draft",
      "description": null,
      "publisher": null,
      "keywords": [],
      "categories": [],
      "total": null,
      "links": [],
      "workflow_bindings": [],
      "use_cases": [],
      "updates": [],
      "quality_score": null,
      "maturity_level": null,
      "experimental": null
    }
    ```

=== "YAML"

    ```yaml
    id: resourcebundle-606fde34
    created_at: '2025-08-18T17:19:51.362711Z'
    updated_at: '2025-08-18T17:19:51.362712Z'
    version: null
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: ResourceBundle
    agent_context: null
    title: null
    bundle_type: null
    entries: []
    status: draft
    description: null
    publisher: null
    keywords: []
    categories: []
    total: null
    links: []
    workflow_bindings: []
    use_cases: []
    updates: []
    quality_score: null
    maturity_level: null
    experimental: null
    
    ```

=== "Schema"

    #### ResourceBundle Schema

    Foundation class for all HACS healthcare resources.

    Provides essential functionality for healthcare data models including
    automatic ID generation, timestamp management, and type-safe operations.

    This class follows FHIR R4/R5 base resource patterns while optimizing
    for AI agent communication and modern Python development practices.

    **Protocol Compliance:**
        Implements: Identifiable, Timestamped, Versioned, Serializable, Validatable

        This ensures all HACS resources follow standardized contracts for:
        - Unique identification (id field)
        - Audit trails (created_at, updated_at)
        - Version tracking (version field)
        - Data interchange (to_dict, from_dict)
        - Validation (validate, is_valid)

    Features:
        - Auto-generated UUIDs if ID not provided
        - Automatic timestamp management
        - Type-safe field access and validation
        - JSON Schema generation with examples
        - Subset model creation for specific use cases
        - Performance optimized serialization
        - Protocol-based interface contracts

    Example:
        >>> class MyResource(BaseResource):
        ...     name: str
        ...     value: int = 0
        >>>
        >>> resource = MyResource(resource_type="MyResource", name="test")
        >>> print(resource.id)  # Auto-generated: myresource-a1b2c3d4
        >>> print(resource.created_at)  # Auto-set to current time
        >>> isinstance(resource, Identifiable)  # True - protocol compliance

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | typing.Optional[str] | None |
    | identifier | list[str] | External identifiers for the resource (e.g., MRN, accession, system-specific IDs) (e.g., ['MRN:12345', 'local:abc-001']) |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['ResourceBundle'] | None |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | title | typing.Optional[str] | Bundle title |
    | bundle_type | hacs_models.types.BundleType | None | None |
    | entries | typing.List[hacs_models.resource_bundle.BundleEntry] | Bundle entries |
    | status | <enum 'BundleStatus'> | Bundle lifecycle status |
    | description | typing.Optional[str] | None |
    | publisher | typing.Optional[str] | None |
    | keywords | typing.List[str] | None |
    | categories | typing.List[str] | None |
    | total | typing.Optional[int] | None |
    | links | typing.List[hacs_models.resource_bundle.Link] | None |
    | workflow_bindings | typing.List[typing.Any] | None |
    | use_cases | typing.List[hacs_models.resource_bundle.ResourceBundle.UseCase] | None |
    | updates | typing.List[typing.Any] | None |
    | quality_score | typing.Optional[float] | None |
    | maturity_level | typing.Optional[str] | None |
    | experimental | typing.Optional[bool] | None |



---

## Authentication & Security

User identity, permissions, and security contexts

### Actor

**Scope & Usage**

Identity (human or agent) with role, permissions, and session context for secure interactions.

**Boundaries**

Not a clinical resource. Use Practitioner for clinical staff records; Organization for facilities.

**Relationships**

- References: Organization via organization
- Used by: auth, auditing, and tool access policies

**References**

- Organization

**Tools**

- authenticate_actor
- authorize_action


**Example**

=== "Rendered"

    #### Actor

    | Field | Value |
    |---|---|
    | resource_type | Actor |
    | id | actor-bebafd90 |
    | name | Dr. Sarah Chen |
    | created_at | 2025-08-18T17:19:51.363367Z |
    | updated_at | 2025-08-18T17:19:51.363368Z |

=== "JSON"

    ```json
    {
      "id": "actor-bebafd90",
      "created_at": "2025-08-18T17:19:51.363367Z",
      "updated_at": "2025-08-18T17:19:51.363368Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "Actor",
      "agent_context": null,
      "name": "Dr. Sarah Chen",
      "role": "physician",
      "permissions": [
        "read:patient",
        "write:patient",
        "read:observation",
        "write:observation",
        "read:encounter",
        "write:encounter",
        "read:diagnosis",
        "write:diagnosis",
        "read:medication",
        "write:medication",
        "read:procedure",
        "write:procedure"
      ],
      "permission_level": null,
      "auth_context": {},
      "session_id": null,
      "session_status": "inactive",
      "last_activity": null,
      "organization": "General Hospital",
      "department": null,
      "contact_info": {},
      "email": null,
      "phone": null,
      "audit_trail": [],
      "is_active": true,
      "security_level": "medium",
      "is_authenticated": false,
      "permission_summary": {
        "read": [
          "patient",
          "observation",
          "encounter",
          "diagnosis",
          "medication",
          "procedure"
        ],
        "write": [
          "patient",
          "observation",
          "encounter",
          "diagnosis",
          "medication",
          "procedure"
        ]
      },
      "display_role": "Physician"
    }
    ```

=== "YAML"

    ```yaml
    id: actor-bebafd90
    created_at: '2025-08-18T17:19:51.363367Z'
    updated_at: '2025-08-18T17:19:51.363368Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: Actor
    agent_context: null
    name: Dr. Sarah Chen
    role: physician
    permissions:
    - read:patient
    - write:patient
    - read:observation
    - write:observation
    - read:encounter
    - write:encounter
    - read:diagnosis
    - write:diagnosis
    - read:medication
    - write:medication
    - read:procedure
    - write:procedure
    permission_level: null
    auth_context: {}
    session_id: null
    session_status: inactive
    last_activity: null
    organization: General Hospital
    department: null
    contact_info: {}
    email: null
    phone: null
    audit_trail: []
    is_active: true
    security_level: medium
    is_authenticated: false
    permission_summary:
      read:
      - patient
      - observation
      - encounter
      - diagnosis
      - medication
      - procedure
      write:
      - patient
      - observation
      - encounter
      - diagnosis
      - medication
      - procedure
    display_role: Physician
    
    ```

=== "Schema"

    #### Actor Schema

    Represents an actor (human or agent) in the healthcare system.

    Actors have roles, permissions, and authentication context for secure
    interactions with healthcare data and other agents.

    LLM-Friendly Features:
    - Simplified permission system with smart defaults
    - Flexible validation that guides rather than blocks
    - Helper methods for common use cases
    - Auto-generation of basic permissions based on role

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Version of the resource |
    | identifier | list[str] | External identifiers for the resource (e.g., MRN, accession, system-specific IDs) (e.g., ['MRN:12345', 'local:abc-001']) |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['Actor'] | Resource type identifier |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | name | <class 'str'> | Display name of the actor (e.g., Dr. Sarah Johnson) |
    | role | <enum 'ActorRole'> | Primary role of this actor (e.g., physician) |
    | permissions | list[str] | List of permissions granted to this actor - Auto-generated based on role if not provided (e.g., ['read:patient', 'write:observation', 'read:encounter']) |
    | permission_level | str | None | Simple permission level (read/write/admin) - Will generate detailed permissions (e.g., read) |
    | auth_context | dict[str, typing.Any] | Authentication and authorization context (e.g., {'auth_provider': 'oauth2', 'token_type': 'bearer', 'scope': ['patient:read', 'observation:write'], 'issued_at': '2024-01-15T10:30:00Z', 'expires_at': '2024-01-15T18:30:00Z'}) |
    | session_id | str | None | Current session identifier (e.g., sess_abc123) |
    | session_status | <enum 'SessionStatus'> | Current session status |
    | last_activity | datetime.datetime | None | Timestamp of last activity |
    | organization | str | None | Organization this actor belongs to (e.g., Mayo Clinic) |
    | department | str | None | Department within the organization (e.g., Cardiology) |
    | contact_info | dict[str, str] | Contact information for this actor (e.g., {'email': 'sarah.johnson@hospital.com', 'phone': '+1-555-0123', 'pager': '12345'}) |
    | email | str | None | Primary email address (will be added to contact_info) (e.g., sarah.johnson@hospital.com) |
    | phone | str | None | Primary phone number (will be added to contact_info) (e.g., +1-555-0123) |
    | audit_trail | list[dict[str, typing.Any]] | Audit trail of significant actions (e.g., [{'action': 'login', 'timestamp': '2024-01-15T10:30:00Z', 'ip_address': '192.168.1.100', 'user_agent': 'Mozilla/5.0...'}]) |
    | is_active | <class 'bool'> | Whether this actor is currently active |
    | security_level | typing.Literal['low', 'medium', 'high', 'critical'] | Security clearance level |



### ActorPreference

**Scope & Usage**

Declarative preferences for actors to shape tool behavior and context (e.g., response format, defaults).

**Boundaries**

This is metadata for orchestration, not a clinical artifact.

**Relationships**

- References: Actor via actor_id

**References**

- Actor

**Tools**

- consult_preferences
- inject_preferences


**Example**

=== "Rendered"

    #### ActorPreference

    | Field | Value |
    |---|---|
    | resource_type | ActorPreference |
    | id | actorpreference-d9c28443 |
    | created_at | 2025-08-18T17:19:51.364176Z |
    | updated_at | 2025-08-18T17:19:51.364177Z |

=== "JSON"

    ```json
    {
      "id": "actorpreference-d9c28443",
      "created_at": "2025-08-18T17:19:51.364176Z",
      "updated_at": "2025-08-18T17:19:51.364177Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "ActorPreference",
      "agent_context": null,
      "actor_id": "actor-123",
      "key": "notification_frequency",
      "value": "daily",
      "scope": "global",
      "target_id": null,
      "datatype": null,
      "tags": []
    }
    ```

=== "YAML"

    ```yaml
    id: actorpreference-d9c28443
    created_at: '2025-08-18T17:19:51.364176Z'
    updated_at: '2025-08-18T17:19:51.364177Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: ActorPreference
    agent_context: null
    actor_id: actor-123
    key: notification_frequency
    value: daily
    scope: global
    target_id: null
    datatype: null
    tags: []
    
    ```

=== "Schema"

    #### ActorPreference Schema

    Declarative actor preference for context engineering.

    Preferences are resolved by scope precedence in runtime (e.g., session > tool > workflow > agent > organization > global).
    This model is a low-level container and does not implement resolution logic; workflows or tools will resolve effective values.

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Version of the resource |
    | identifier | list[str] | External identifiers for the resource (e.g., MRN, accession, system-specific IDs) (e.g., ['MRN:12345', 'local:abc-001']) |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | <class 'str'> | None |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | actor_id | <class 'str'> | ID of the actor the preference belongs to |
    | key | <class 'str'> | Preference key, e.g., response_format |
    | value | typing.Union[typing.Dict[str, typing.Any], typing.List[typing.Any], str, int, float, bool, NoneType] | Preference value as JSON-compatible data |
    | scope | <enum 'PreferenceScope'> | Preference scope |
    | target_id | typing.Optional[str] | Target identifier for scoped preferences (e.g., workflow_id, agent_id, tool_name, org_id) |
    | datatype | typing.Optional[str] | Optional data type hint for value |
    | tags | typing.List[str] | None |



---

## Clinical Resources

Patient care, medical records, and clinical data

### Patient

**Scope & Usage**

Demographics and administrative information for a person or animal receiving care. Supports care providers, general practitioners, care teams, emergency contacts, and family relationships. Includes identity management, communication preferences, language requirements, and life status (deceased, active). Optimized for AI agent context engineering with automatic name parsing and flexible input formats.

**Boundaries**

Patient resources do not contain clinical findings (use Observation/Condition), care plans (use CarePlan), appointments (use Appointment), or billing information (use Account/Coverage). Do not use for practitioners (use Practitioner) or organizations (use Organization). Patient linkage allows connecting related patients (family members, merged records).

**Relationships**

- Referenced by: Observation.subject, Encounter.subject, Procedure.subject, MedicationRequest.subject, DiagnosticReport.subject, ServiceRequest.subject, Goal.subject, CarePlan.subject, CareTeam.subject, Condition.subject, AllergyIntolerance.patient, Immunization.patient, FamilyMemberHistory.patient
- Links to: Practitioner via generalPractitioner/careProvider, Organization via managingOrganization, RelatedPerson via contact, Patient via link (merged records, family relationships)

**References**

- Document.subject
- Encounter.subject
- all clinical resources via subject/patient field

**Tools**

- calculate_age
- add_identifier
- find_identifier_by_type
- add_care_provider
- deactivate_record


**Example**

=== "Rendered"

    #### Patient

    | Field | Value |
    |---|---|
    | resource_type | Patient |
    | id | patient-99ee93c1 |
    | status | active |
    | full_name | Maria Rodriguez |
    | gender | female |
    | birth_date | 1985-03-15 |
    | phone | +1-555-0101 |
    | created_at | 2025-08-18T17:19:51.364589Z |
    | updated_at | 2025-08-18T17:19:51.364590Z |

=== "JSON"

    ```json
    {
      "id": "patient-99ee93c1",
      "created_at": "2025-08-18T17:19:51.364589Z",
      "updated_at": "2025-08-18T17:19:51.364590Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "Patient",
      "agent_context": {},
      "status": "active",
      "text": null,
      "contained": null,
      "extension": null,
      "modifier_extension": null,
      "name": [
        {
          "id": "humanname-02f5fbdb",
          "created_at": "2025-08-18T17:19:51.364638Z",
          "updated_at": "2025-08-18T17:19:51.364638Z",
          "version": "1.0.0",
          "identifier": [],
          "language": null,
          "implicit_rules": null,
          "meta_profile": [],
          "meta_source": null,
          "meta_security": [],
          "meta_tag": [],
          "resource_type": "HumanName",
          "agent_context": null,
          "status": "active",
          "text": null,
          "contained": null,
          "extension": null,
          "modifier_extension": null,
          "use": "usual",
          "family": "Rodriguez",
          "given": [
            "Maria"
          ],
          "prefix": [],
          "suffix": [],
          "full_name": "Maria Rodriguez",
          "display_name": "Maria Rodriguez"
        }
      ],
      "full_name": "Maria Rodriguez",
      "gender": "female",
      "birth_date": "1985-03-15",
      "age": null,
      "deceased_boolean": false,
      "deceased_date_time": null,
      "multiple_birth_boolean": null,
      "multiple_birth_integer": null,
      "photo": [],
      "telecom": [
        {
          "id": "contactpoint-ac853330",
          "created_at": "2025-08-18T17:19:51.364666Z",
          "updated_at": "2025-08-18T17:19:51.364667Z",
          "version": "1.0.0",
          "identifier": [],
          "language": null,
          "implicit_rules": null,
          "meta_profile": [],
          "meta_source": null,
          "meta_security": [],
          "meta_tag": [],
          "resource_type": "ContactPoint",
          "agent_context": null,
          "status": "active",
          "text": null,
          "contained": null,
          "extension": null,
          "modifier_extension": null,
          "system": "phone",
          "value": "+1-555-0101",
          "use": "home",
          "rank": 1
        }
      ],
      "phone": "+1-555-0101",
      "email": null,
      "address": [],
      "address_text": null,
      "marital_status": null,
      "communication": [],
      "care_provider": [],
      "link": [],
      "communication_preference": null,
      "contact": [],
      "active": true,
      "display_name": "Maria Rodriguez",
      "age_years": null
    }
    ```

=== "YAML"

    ```yaml
    id: patient-99ee93c1
    created_at: '2025-08-18T17:19:51.364589Z'
    updated_at: '2025-08-18T17:19:51.364590Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: Patient
    agent_context: {}
    status: active
    text: null
    contained: null
    extension: null
    modifier_extension: null
    name:
    - id: humanname-02f5fbdb
      created_at: '2025-08-18T17:19:51.364638Z'
      updated_at: '2025-08-18T17:19:51.364638Z'
      version: 1.0.0
      identifier: []
      language: null
      implicit_rules: null
      meta_profile: []
      meta_source: null
      meta_security: []
      meta_tag: []
      resource_type: HumanName
      agent_context: null
      status: active
      text: null
      contained: null
      extension: null
      modifier_extension: null
      use: usual
      family: Rodriguez
      given:
      - Maria
      prefix: []
      suffix: []
      full_name: Maria Rodriguez
      display_name: Maria Rodriguez
    full_name: Maria Rodriguez
    gender: female
    birth_date: '1985-03-15'
    age: null
    deceased_boolean: false
    deceased_date_time: null
    multiple_birth_boolean: null
    multiple_birth_integer: null
    photo: []
    telecom:
    - id: contactpoint-ac853330
      created_at: '2025-08-18T17:19:51.364666Z'
      updated_at: '2025-08-18T17:19:51.364667Z'
      version: 1.0.0
      identifier: []
      language: null
      implicit_rules: null
      meta_profile: []
      meta_source: null
      meta_security: []
      meta_tag: []
      resource_type: ContactPoint
      agent_context: null
      status: active
      text: null
      contained: null
      extension: null
      modifier_extension: null
      system: phone
      value: +1-555-0101
      use: home
      rank: 1
    phone: +1-555-0101
    email: null
    address: []
    address_text: null
    marital_status: null
    communication: []
    care_provider: []
    link: []
    communication_preference: null
    contact: []
    active: true
    display_name: Maria Rodriguez
    age_years: null
    
    ```

=== "Schema"

    #### Patient Schema

    Patient demographics and administrative information.

    Patient model following FHIR Patient resource structure
    with AI-optimized features for flexible data input and automatic parsing.

    Key Features:
        - Automatic name parsing from full_name string
        - Flexible contact information handling
        - Age calculation and validation
        -identifier management
        - Care team tracking
        - Patient linkage and family relationships
        - Enhanced communication preferences and accessibility
        - Multiple birth tracking (twins, triplets)
        - Photo attachments support
        - Deceased patient tracking with date
        - Agent context for AI workflows

    Example:
        >>> patient = Patient(
        ...     full_name="Dr. John Michael Smith Jr.",
        ...     birth_date="1985-03-15",
        ...     gender="male",
        ...     phone="+1-555-123-4567",
        ...     email="john.smith@example.com"
        ... )
        >>> print(patient.display_name)  # "John Michael Smith"
        >>> print(patient.age_years)     # Calculated from birth_date

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Version of the resource |
    | identifier | list[hacs_models.patient.Identifier] | Patient identifiers (MRN, SSN, etc.) |
    | language | str | None | Primary language (auto-added to communication) (e.g., English) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['Patient'] | Resource type identifier |
    | agent_context | dict[str, typing.Any] | Agent-specific context and metadata for AI workflows (e.g., {'last_interaction': '2024-08-03T12:00:00Z', 'preferred_agent': 'primary-care-assistant', 'interaction_count': 5, 'care_plan_status': 'active'}) |
    | status | <class 'str'> | Current status of the resource (e.g., active) |
    | text | str | None | Human-readable summary of the resource content (e.g., Patient John Doe, 45 years old) |
    | contained | list[hacs_models.base_resource.BaseResource] | None | Resources contained within this resource |
    | extension | dict[str, typing.Any] | None | Additional content defined by implementations (e.g., {'url': 'custom-field', 'valueString': 'custom-value'}) |
    | modifier_extension | dict[str, typing.Any] | None | Extensions that cannot be ignored (e.g., {'url': 'critical-field', 'valueBoolean': True}) |
    | name | list[hacs_models.patient.HumanName] | Patient names (structured format) |
    | full_name | str | None | Complete name as single string (auto-parsed into structured format) (e.g., Dr. John Michael Smith Jr.) |
    | gender | hacs_models.types.Gender | None | Administrative gender (e.g., male) |
    | birth_date | datetime.date | str | None | Date of birth (e.g., 1985-03-15) |
    | age | int | None | Age in years (will estimate birth_date if not provided) (e.g., 39) |
    | deceased_boolean | <class 'bool'> | Whether the patient is deceased |
    | deceased_date_time | datetime.date | None | Date of death if deceased |
    | multiple_birth_boolean | bool | None | Whether patient is part of a multiple birth (twins, triplets, etc.) (e.g., True) |
    | multiple_birth_integer | int | None | Birth order for multiple births (1 for first twin, 2 for second, etc.) (e.g., 1) |
    | photo | list[str] | Patient photos (base64 encoded images or URLs) (e.g., ['data:image/jpeg;base64,/9j/4AAQ...', 'https://example.com/patient-photo.jpg']) |
    | telecom | list[hacs_models.patient.ContactPoint] | Contact points (phone, email, etc.) |
    | phone | str | None | Primary phone number (auto-added to telecom) (e.g., +1-555-123-4567) |
    | email | str | None | Primary email address (auto-added to telecom) (e.g., patient@example.com) |
    | address | list[hacs_models.patient.Address] | Patient addresses |
    | address_text | str | None | Simple address as text (auto-parsed into structured format) (e.g., 123 Main St, Anytown, CA 12345) |
    | marital_status | str | None | Marital status code (M=Married, S=Single, D=Divorced, W=Widowed, U=Unknown) (e.g., M) |
    | communication | list[dict[str, typing.Any]] | Languages and communication preferences (e.g., [{'language': 'en-US', 'preferred': True}]) |
    | care_provider | list[str] | References to care providers and team members (e.g., ['Practitioner/dr-smith', 'Organization/hospital-main']) |
    | link | list[dict[str, typing.Any]] | Links to other related Patient resources (family members, care partners, etc.) (e.g., [{'other': 'Patient/mother-123', 'type': 'seealso'}]) |
    | communication_preference | dict[str, typing.Any] | None | Specific communication preferences and accessibility needs (e.g., {'preferred_method': 'email', 'accessible_communication': ['sign-language'], 'interpreter_required': True, 'contact_person': 'Patient/spouse-456'}) |
    | contact | list[dict[str, typing.Any]] | Emergency contact information (e.g., [{'relationship': 'spouse', 'name': {'family': 'Smith', 'given': ['Jane']}, 'telecom': [{'system': 'phone', 'value': '+1-555-123-4568'}]}]) |
    | active | <class 'bool'> | Whether this patient record is active |



### Observation

**Scope & Usage**

Measurements and simple assertions made about a patient, device, or other subjects. Central element for capturing vital signs, laboratory results, imaging measurements, clinical assessments, and device readings. Supports numeric values, coded values, text, boolean, time, ranges, ratios, and complex data types. Includes categorization (vital-signs, laboratory, imaging, survey, social-history), interpretation codes, reference ranges, and quality/reliability indicators.

**Boundaries**

Do not use for diagnoses/problems (use Condition), procedures performed (use Procedure), care plans (use CarePlan), or medication orders (use MedicationRequest). Do not store large binary data (use DocumentReference/Media). Focus on individual observations; use DiagnosticReport for grouped results and interpretations.

**Relationships**

- Referenced by: DiagnosticReport.result, Condition.evidence.detail
- References: Patient/Subject via subject, Encounter via encounter, Practitioner via performer, Device via device, Specimen via specimen
- Groups: hasMember (for panels), derivedFrom (computed from other observations), focus (additional subject context)

**References**

- Patient.subject
- Encounter.encounter
- DiagnosticReport.result
- Condition.evidence

**Tools**

- summarize_observation_value


**Example**

=== "Rendered"

    #### Observation

    | Field | Value |
    |---|---|
    | resource_type | Observation |
    | id | observation-865f901f |
    | status | final |
    | code | Blood Pressure |
    | value.quantity | 128.0 mmHg |
    | subject | Patient/patient-12345 |
    | performer | [] |
    | created_at | 2025-08-18T17:19:51.365859Z |
    | updated_at | 2025-08-18T17:19:51.365860Z |

=== "JSON"

    ```json
    {
      "id": "observation-865f901f",
      "created_at": "2025-08-18T17:19:51.365859Z",
      "updated_at": "2025-08-18T17:19:51.365860Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "Observation",
      "agent_context": null,
      "status": "final",
      "text": null,
      "contained": null,
      "extension": null,
      "modifier_extension": null,
      "code": {
        "id": "codeableconcept-0434f2ed",
        "created_at": "2025-08-18T17:19:51.365811Z",
        "updated_at": "2025-08-18T17:19:51.365811Z",
        "version": "1.0.0",
        "identifier": [],
        "language": null,
        "implicit_rules": null,
        "meta_profile": [],
        "meta_source": null,
        "meta_security": [],
        "meta_tag": [],
        "resource_type": "CodeableConcept",
        "agent_context": null,
        "status": "active",
        "text": "Blood Pressure",
        "contained": null,
        "extension": null,
        "modifier_extension": null,
        "coding": []
      },
      "category": [],
      "method": null,
      "device": null,
      "subject": "Patient/patient-12345",
      "encounter": null,
      "effective_date_time": null,
      "issued": null,
      "performer": [],
      "value_quantity": {
        "id": "quantity-e6aecfaf",
        "created_at": "2025-08-18T17:19:51.365837Z",
        "updated_at": "2025-08-18T17:19:51.365838Z",
        "version": "1.0.0",
        "identifier": [],
        "language": null,
        "implicit_rules": null,
        "meta_profile": [],
        "meta_source": null,
        "meta_security": [],
        "meta_tag": [],
        "resource_type": "Quantity",
        "agent_context": null,
        "status": "active",
        "text": null,
        "contained": null,
        "extension": null,
        "modifier_extension": null,
        "value": 128.0,
        "comparator": null,
        "unit": "mmHg",
        "system": null,
        "code": null
      },
      "value_codeable_concept": null,
      "value_string": null,
      "value_boolean": null,
      "value_integer": null,
      "value_range": null,
      "data_absent_reason": null,
      "interpretation": [],
      "note": [],
      "reference_range": [],
      "interpretation_detail": null,
      "has_member": [],
      "derived_from": []
    }
    ```

=== "YAML"

    ```yaml
    id: observation-865f901f
    created_at: '2025-08-18T17:19:51.365859Z'
    updated_at: '2025-08-18T17:19:51.365860Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: Observation
    agent_context: null
    status: final
    text: null
    contained: null
    extension: null
    modifier_extension: null
    code:
      id: codeableconcept-0434f2ed
      created_at: '2025-08-18T17:19:51.365811Z'
      updated_at: '2025-08-18T17:19:51.365811Z'
      version: 1.0.0
      identifier: []
      language: null
      implicit_rules: null
      meta_profile: []
      meta_source: null
      meta_security: []
      meta_tag: []
      resource_type: CodeableConcept
      agent_context: null
      status: active
      text: Blood Pressure
      contained: null
      extension: null
      modifier_extension: null
      coding: []
    category: []
    method: null
    device: null
    subject: Patient/patient-12345
    encounter: null
    effective_date_time: null
    issued: null
    performer: []
    value_quantity:
      id: quantity-e6aecfaf
      created_at: '2025-08-18T17:19:51.365837Z'
      updated_at: '2025-08-18T17:19:51.365838Z'
      version: 1.0.0
      identifier: []
      language: null
      implicit_rules: null
      meta_profile: []
      meta_source: null
      meta_security: []
      meta_tag: []
      resource_type: Quantity
      agent_context: null
      status: active
      text: null
      contained: null
      extension: null
      modifier_extension: null
      value: 128.0
      comparator: null
      unit: mmHg
      system: null
      code: null
    value_codeable_concept: null
    value_string: null
    value_boolean: null
    value_integer: null
    value_range: null
    data_absent_reason: null
    interpretation: []
    note: []
    reference_range: []
    interpretation_detail: null
    has_member: []
    derived_from: []
    
    ```

=== "Schema"

    #### Observation Schema

    Measurements and simple assertions made about a patient.

    Observations are a central element in healthcare, used to support
    diagnosis, monitor progress, determine baselines and patterns, and
    capture demographic characteristics.

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Version of the resource |
    | identifier | list[str] | External identifiers for the resource (e.g., MRN, accession, system-specific IDs) (e.g., ['MRN:12345', 'local:abc-001']) |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['Observation'] | None |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | status | <enum 'ObservationStatus'> | Status of the observation result |
    | text | str | None | Human-readable summary of the resource content (e.g., Patient John Doe, 45 years old) |
    | contained | list[hacs_models.base_resource.BaseResource] | None | Resources contained within this resource |
    | extension | dict[str, typing.Any] | None | Additional content defined by implementations (e.g., {'url': 'custom-field', 'valueString': 'custom-value'}) |
    | modifier_extension | dict[str, typing.Any] | None | Extensions that cannot be ignored (e.g., {'url': 'critical-field', 'valueBoolean': True}) |
    | code | <class 'hacs_models.observation.CodeableConcept'> | Type of observation (code / type) |
    | category | list[hacs_models.observation.CodeableConcept] | Classification of type of observation (e.g., vital-signs, laboratory, imaging, survey) (e.g., [{'coding': [{'system': 'http://terminology.hl7.org/CodeSystem/observation-category', 'code': 'vital-signs', 'display': 'Vital Signs'}], 'text': 'Vital Signs'}]) |
    | method | hacs_models.observation.CodeableConcept | None | Method used to perform the observation (e.g., {'text': 'Automated blood pressure cuff', 'coding': [{'system': 'http://snomed.info/sct', 'code': '261241001', 'display': 'Arterial pressure monitoring'}]}) |
    | device | str | None | Reference to device used to perform observation (e.g., Device/blood-pressure-monitor-123) |
    | subject | str | None | Who/what this observation is about (e.g., Patient/patient-123) |
    | encounter | str | None | Healthcare encounter during which this observation was made (e.g., Encounter/encounter-456) |
    | effective_date_time | datetime.datetime | None | Clinically relevant time/time-period for observation |
    | issued | datetime.datetime | None | Date/Time this version was made available |
    | performer | list[str] | Who is responsible for the observation (e.g., ['Practitioner/dr-smith']) |
    | value_quantity | hacs_models.observation.Quantity | None | Actual result as a quantity |
    | value_codeable_concept | hacs_models.observation.CodeableConcept | None | Actual result as a coded concept |
    | value_string | str | None | Actual result as a string |
    | value_boolean | bool | None | Actual result as a boolean |
    | value_integer | int | None | Actual result as an integer |
    | value_range | hacs_models.observation.Range | None | Actual result as a range |
    | data_absent_reason | hacs_models.observation.CodeableConcept | None | Why the observation value is missing |
    | interpretation | list[hacs_models.observation.CodeableConcept] | High, low, normal, etc. |
    | note | list[str] | Comments about the observation |
    | reference_range | list[dict[str, typing.Any]] | Reference ranges for interpretation of observation values (e.g., [{'low': {'value': 120, 'unit': 'mmHg', 'system': 'http://unitsofmeasure.org'}, 'high': {'value': 140, 'unit': 'mmHg', 'system': 'http://unitsofmeasure.org'}, 'type': {'coding': [{'system': 'http://terminology.hl7.org/CodeSystem/referencerange-meaning', 'code': 'normal', 'display': 'Normal Range'}], 'text': 'Normal'}, 'applies_to': [{'coding': [{'system': 'http://snomed.info/sct', 'code': '248153007', 'display': 'Male'}], 'text': 'Male'}], 'age': {'low': {'value': 18, 'unit': 'years'}, 'high': {'value': 65, 'unit': 'years'}}, 'text': 'Normal blood pressure range for adult males'}]) |
    | interpretation_detail | dict[str, typing.Any] | None | Enhanced interpretation with clinical context and recommendations (e.g., {'overall_interpretation': 'abnormal', 'clinical_significance': 'high', 'trend_analysis': 'increasing', 'recommended_action': 'follow-up required', 'confidence_level': 'high', 'comparison_to_previous': '20% increase from last measurement', 'clinical_context': 'Patient on antihypertensive medication'}) |
    | has_member | list[str] | Related resource that belongs to the Observation group |
    | derived_from | list[str] | Related measurements the observation is made from |



### Condition

**Scope & Usage**

Problems, diagnoses, and health concerns relevant to patient care and clinical decision making. Represents clinical conditions, symptoms, findings, and diagnoses at varying levels of detail and certainty. Supports problem lists, discharge diagnoses, differential diagnoses, and clinical concerns. Includes verification status (confirmed, provisional, differential), clinical status (active, resolved, remission), severity, onset, and resolution information.

**Boundaries**

Do not use for medications (use MedicationRequest/Statement), procedures (use Procedure), observations/measurements (use Observation), allergies/intolerances (use AllergyIntolerance), or care plans (use CarePlan). Focus on problems/diagnoses, not care activities or treatments. Do not duplicate family history (use FamilyMemberHistory).

**Relationships**

- References: Patient via subject, Encounter via encounter, Practitioner via asserter/recorder
- Evidence: Observation via evidence.detail, DiagnosticReport via evidence.detail
- Stages: ConditionStage for progression tracking
- Referenced by: Goal.addresses, CarePlan.addresses, ServiceRequest.reasonReference

**References**

- Patient.subject
- Encounter.encounter
- Observation/DiagnosticReport in evidence

**Tools**

- add_condition_stage


**Example**

=== "Rendered"

    #### Condition

    | Field | Value |
    |---|---|
    | resource_type | Condition |
    | id | condition-761f828f |
    | status | active |
    | created_at | 2025-08-18T17:19:51.371085Z |
    | updated_at | 2025-08-18T17:19:51.371086Z |

=== "JSON"

    ```json
    {
      "id": "condition-761f828f",
      "created_at": "2025-08-18T17:19:51.371085Z",
      "updated_at": "2025-08-18T17:19:51.371086Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "Condition",
      "agent_context": null,
      "status": "active",
      "text": null,
      "contained": null,
      "extension": null,
      "modifier_extension": null,
      "clinical_status": null,
      "verification_status": null,
      "category": [],
      "severity": null,
      "code": null,
      "body_site": [],
      "subject": null,
      "encounter": null,
      "onset_date_time": null,
      "onset_age": null,
      "onset_period": null,
      "onset_range": null,
      "onset_string": null,
      "abatement_date_time": null,
      "abatement_age": null,
      "abatement_period": null,
      "abatement_range": null,
      "abatement_string": null,
      "recorded_date": null,
      "recorder": null,
      "asserter": null,
      "stage": [],
      "evidence": [],
      "note": []
    }
    ```

=== "YAML"

    ```yaml
    id: condition-761f828f
    created_at: '2025-08-18T17:19:51.371085Z'
    updated_at: '2025-08-18T17:19:51.371086Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: Condition
    agent_context: null
    status: active
    text: null
    contained: null
    extension: null
    modifier_extension: null
    clinical_status: null
    verification_status: null
    category: []
    severity: null
    code: null
    body_site: []
    subject: null
    encounter: null
    onset_date_time: null
    onset_age: null
    onset_period: null
    onset_range: null
    onset_string: null
    abatement_date_time: null
    abatement_age: null
    abatement_period: null
    abatement_range: null
    abatement_string: null
    recorded_date: null
    recorder: null
    asserter: null
    stage: []
    evidence: []
    note: []
    
    ```

=== "Schema"

    #### Condition Schema

    Detailed information about conditions, problems, or diagnoses.

    Records conditions, problems, diagnoses, or other clinical issues that are
    clinically significant and can impact the patient's health. Optimized for
    LLM context engineering withFHIR-aligned metadata.

    Key Features:
        - Rich clinical status and verification tracking
        - Temporal onset and resolution support
        - Severity and stage classification
        - Evidence and manifestation linking
        - Care team and encounter association

    Example Use Cases:
        - Primary and secondary diagnoses
        - Chronic conditions and comorbidities
        - Symptoms and clinical findings
        - Problem lists and care plans
        - Quality reporting and analytics

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Version of the resource |
    | identifier | list[dict[str, typing.Any]] | External identifiers for this condition (e.g., [{'system': 'http://hospital.example.org/condition-ids', 'value': 'COND-12345'}]) |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['Condition'] | None |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | status | <class 'str'> | Current status of the resource (e.g., active) |
    | text | str | None | Human-readable summary of the resource content (e.g., Patient John Doe, 45 years old) |
    | contained | list[hacs_models.base_resource.BaseResource] | None | Resources contained within this resource |
    | extension | dict[str, typing.Any] | None | Additional content defined by implementations (e.g., {'url': 'custom-field', 'valueString': 'custom-value'}) |
    | modifier_extension | dict[str, typing.Any] | None | Extensions that cannot be ignored (e.g., {'url': 'critical-field', 'valueBoolean': True}) |
    | clinical_status | hacs_models.types.ConditionClinicalStatus | None | Active | recurrence | relapse | inactive | remission | resolved |
    | verification_status | hacs_models.types.ConditionVerificationStatus | None | Unconfirmed | provisional | differential | confirmed | refuted | entered-in-error |
    | category | list[dict[str, typing.Any]] | Category of the condition (problem-list-item, encounter-diagnosis, etc.) (e.g., [{'coding': [{'system': 'condition-category', 'code': 'problem-list-item', 'display': 'Problem List Item'}]}]) |
    | severity | dict[str, typing.Any] | None | Subjective severity of condition (e.g., {'coding': [{'system': 'http://snomed.info/sct', 'code': '24484000', 'display': 'Severe'}]}) |
    | code | dict[str, typing.Any] | None | Identification of the condition, problem or diagnosis (e.g., {'coding': [{'system': 'http://hl7.org/fhir/sid/icd-10', 'code': 'I10', 'display': 'Essential hypertension'}]}) |
    | body_site | list[dict[str, typing.Any]] | Anatomical location of the condition (e.g., [{'coding': [{'system': 'http://snomed.info/sct', 'code': '80891009', 'display': 'Heart structure'}]}]) |
    | subject | str | None | Who has the condition (Patient reference) (e.g., Patient/patient-123) |
    | encounter | str | None | Encounter when condition first asserted (e.g., Encounter/encounter-456) |
    | onset_date_time | datetime.datetime | None | Estimated or actual date, date-time when condition began |
    | onset_age | dict[str, typing.Any] | None | Estimated or actual age when condition began (e.g., {'value': 45, 'unit': 'years', 'system': 'http://unitsofmeasure.org', 'code': 'a'}) |
    | onset_period | dict[str, datetime.datetime] | None | Period when condition began (e.g., {'start': '2024-01-01T00:00:00Z', 'end': '2024-01-31T23:59:59Z'}) |
    | onset_range | dict[str, typing.Any] | None | Range when condition began |
    | onset_string | str | None | Estimated or actual time when condition began (text) (e.g., childhood) |
    | abatement_date_time | datetime.datetime | None | When condition resolved |
    | abatement_age | dict[str, typing.Any] | None | Age when condition resolved |
    | abatement_period | dict[str, datetime.datetime] | None | Period when condition resolved |
    | abatement_range | dict[str, typing.Any] | None | Range when condition resolved |
    | abatement_string | str | None | When condition resolved (text) (e.g., resolved with treatment) |
    | recorded_date | datetime.datetime | None | Date record was first recorded |
    | recorder | str | None | Who recorded the condition (e.g., Practitioner/dr-smith) |
    | asserter | str | None | Person who asserts this condition (e.g., Practitioner/dr-jones) |
    | stage | list[hacs_models.condition.ConditionStage] | Stage/grade of the condition |
    | evidence | list[hacs_models.condition.ConditionEvidence] | Supporting evidence for the condition |
    | note | list[str] | Additional information about the condition (e.g., ['Patient reports symptoms worse in morning', 'Family history positive for similar condition']) |



### Procedure

**Scope & Usage**

Actions performed on, with, or for a patient as part of care delivery. Includes surgical procedures, diagnostic procedures, therapeutic procedures, administrative procedures, and care delivery activities. Represents completed, in-progress, or stopped procedures with detailed information about performers, locations, devices used, and outcomes. Supports procedure hierarchies, staged procedures, and procedure reports.

**Boundaries**

Do not use for orders/requests (use ServiceRequest), appointments (use Appointment), medication administration (use MedicationAdministration), or observations/measurements (use Observation). Focus on procedures actually performed, not planned or ordered. Do not use for care plans (use CarePlan) or goals (use Goal).

**Relationships**

- References: Patient via subject, Encounter via encounter, Practitioner via performer.actor, Device via usedReference, Location via location
- Based on: ServiceRequest via basedOn, CarePlan via basedOn
- Parts: partOf (for procedure hierarchies), followUp (post-procedure care)
- Outcomes: Observation via report, Condition via reasonReference

**References**

- Patient.subject
- Encounter.encounter
- ServiceRequest.basedOn
- related Observations/Conditions


**Example**

=== "Rendered"

    #### Procedure

    | Field | Value |
    |---|---|
    | resource_type | Procedure |
    | id | procedure-cc728712 |
    | status | completed |
    | code | Sample Procedure |
    | subject | Patient/patient-123 |
    | performer | [] |
    | created_at | 2025-08-18T17:19:51.376967Z |
    | updated_at | 2025-08-18T17:19:51.376968Z |

=== "JSON"

    ```json
    {
      "id": "procedure-cc728712",
      "created_at": "2025-08-18T17:19:51.376967Z",
      "updated_at": "2025-08-18T17:19:51.376968Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "Procedure",
      "agent_context": null,
      "status": "completed",
      "text": null,
      "contained": null,
      "extension": null,
      "modifier_extension": null,
      "status_reason": null,
      "category": null,
      "code": {
        "id": "codeableconcept-d4fdc6f6",
        "created_at": "2025-08-18T17:19:51.376943Z",
        "updated_at": "2025-08-18T17:19:51.376946Z",
        "version": "1.0.0",
        "identifier": [],
        "language": null,
        "implicit_rules": null,
        "meta_profile": [],
        "meta_source": null,
        "meta_security": [],
        "meta_tag": [],
        "resource_type": "CodeableConcept",
        "agent_context": null,
        "status": "active",
        "text": "Sample Procedure",
        "contained": null,
        "extension": null,
        "modifier_extension": null,
        "coding": []
      },
      "subject": "Patient/patient-123",
      "encounter": null,
      "performed_date_time": null,
      "performed_period_start": null,
      "performed_period_end": null,
      "performer": [],
      "location": null,
      "reason_code": [],
      "reason_reference": [],
      "body_site": [],
      "outcome": null,
      "report": [],
      "complication": [],
      "complication_detail": [],
      "follow_up": [],
      "note": [],
      "focal_device": [],
      "used_reference": [],
      "used_code": [],
      "duration_minutes": null
    }
    ```

=== "YAML"

    ```yaml
    id: procedure-cc728712
    created_at: '2025-08-18T17:19:51.376967Z'
    updated_at: '2025-08-18T17:19:51.376968Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: Procedure
    agent_context: null
    status: completed
    text: null
    contained: null
    extension: null
    modifier_extension: null
    status_reason: null
    category: null
    code:
      id: codeableconcept-d4fdc6f6
      created_at: '2025-08-18T17:19:51.376943Z'
      updated_at: '2025-08-18T17:19:51.376946Z'
      version: 1.0.0
      identifier: []
      language: null
      implicit_rules: null
      meta_profile: []
      meta_source: null
      meta_security: []
      meta_tag: []
      resource_type: CodeableConcept
      agent_context: null
      status: active
      text: Sample Procedure
      contained: null
      extension: null
      modifier_extension: null
      coding: []
    subject: Patient/patient-123
    encounter: null
    performed_date_time: null
    performed_period_start: null
    performed_period_end: null
    performer: []
    location: null
    reason_code: []
    reason_reference: []
    body_site: []
    outcome: null
    report: []
    complication: []
    complication_detail: []
    follow_up: []
    note: []
    focal_device: []
    used_reference: []
    used_code: []
    duration_minutes: null
    
    ```

=== "Schema"

    #### Procedure Schema

    Procedure resource for healthcare procedures and interventions.

    An action that is or was performed on or for a patient. This can be a
    physical intervention like an operation, or less invasive like long term
    services, counseling, or hypnotherapy.

    This resource is used to record procedures performed on patients, including
    surgical procedures, therapeutic procedures, diagnostic procedures, and
    administrative procedures.

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Version of the resource |
    | identifier | list[str] | External identifiers for this procedure (e.g., ['urn:oid:1.2.3.4.5.6.7.8.9|12345', 'procedure-123456']) |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['Procedure'] | None |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | status | <enum 'ProcedureStatus'> | Status of the procedure (preparation, in-progress, completed, etc.) |
    | text | str | None | Human-readable summary of the resource content (e.g., Patient John Doe, 45 years old) |
    | contained | list[hacs_models.base_resource.BaseResource] | None | Resources contained within this resource |
    | extension | dict[str, typing.Any] | None | Additional content defined by implementations (e.g., {'url': 'custom-field', 'valueString': 'custom-value'}) |
    | modifier_extension | dict[str, typing.Any] | None | Extensions that cannot be ignored (e.g., {'url': 'critical-field', 'valueBoolean': True}) |
    | status_reason | hacs_models.observation.CodeableConcept | None | Reason for current status |
    | category | hacs_models.observation.CodeableConcept | None | Classification of procedure (e.g., {'coding': [{'system': 'http://snomed.info/sct', 'code': '387713003', 'display': 'Surgical procedure'}], 'text': 'Surgical procedure'}) |
    | code | <class 'hacs_models.observation.CodeableConcept'> | Identification of the procedure |
    | subject | <class 'str'> | Who the procedure was performed on |
    | encounter | str | None | Encounter created as part of |
    | performed_date_time | str | None | When the procedure was performed |
    | performed_period_start | str | None | Start of when the procedure was performed |
    | performed_period_end | str | None | End of when the procedure was performed |
    | performer | list[hacs_models.procedure.ProcedurePerformer] | The people who performed the procedure |
    | location | str | None | Where the procedure happened |
    | reason_code | list[hacs_models.observation.CodeableConcept] | Coded reason procedure performed |
    | reason_reference | list[str] | The justification that the procedure was performed |
    | body_site | list[hacs_models.observation.CodeableConcept] | Target body sites |
    | outcome | hacs_models.observation.CodeableConcept | None | The result of procedure |
    | report | list[str] | Any report resulting from the procedure |
    | complication | list[hacs_models.observation.CodeableConcept] | Complication following the procedure |
    | complication_detail | list[str] | A condition that is a result of the procedure |
    | follow_up | list[hacs_models.observation.CodeableConcept] | Instructions for follow up |
    | note | list[str] | Additional information about the procedure |
    | focal_device | list[hacs_models.procedure.ProcedureFocalDevice] | Manipulated, implanted, or removed device |
    | used_reference | list[str] | Items used during procedure |
    | used_code | list[hacs_models.observation.CodeableConcept] | Coded items used during procedure |
    | duration_minutes | int | None | Duration of the procedure in minutes (e.g., 30) |



### DiagnosticReport

**Scope & Usage**

Clinical report that groups and consolidates diagnostic test results with clinical interpretations and conclusions. Represents laboratory reports, imaging reports, pathology reports, and other diagnostic studies. Includes result aggregation, professional interpretations, clinical significance, recommendations, and quality indicators. Supports structured and narrative reporting with media attachments.

**Boundaries**

Do not use for individual measurements (use Observation), procedure records (use Procedure), or document storage (use DocumentReference for large attachments). Focus on the report/interpretation, not the raw data. Do not use for care plans or treatment recommendations (use CarePlan).

**Relationships**

- References: Patient via subject, Observation via result, ServiceRequest via basedOn, Practitioner via performer, Specimen via specimen
- Supports: grouped results, multi-part reports, amended reports
- Media: presentedForm (report documents), image attachments

**References**

- Patient.subject
- ServiceRequest.basedOn
- Observation.result
- Encounter.encounter

**Tools**

- summarize_report_tool
- link_report_results_tool
- attach_report_media_tool
- validate_report_completeness_tool


**Example**

=== "Rendered"

    #### DiagnosticReport

    | Field | Value |
    |---|---|
    | resource_type | DiagnosticReport |
    | id | diagnosticreport-e953985e |
    | status | final |
    | code | Sample DiagnosticReport |
    | performer | [] |
    | based_on | [] |
    | result | [] |
    | created_at | 2025-08-18T17:19:51.381768Z |
    | updated_at | 2025-08-18T17:19:51.381768Z |

=== "JSON"

    ```json
    {
      "id": "diagnosticreport-e953985e",
      "created_at": "2025-08-18T17:19:51.381768Z",
      "updated_at": "2025-08-18T17:19:51.381768Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "DiagnosticReport",
      "agent_context": null,
      "status": "final",
      "text": null,
      "contained": null,
      "extension": null,
      "modifier_extension": null,
      "based_on": [],
      "category": [],
      "code": {
        "id": "codeableconcept-1310712c",
        "created_at": "2025-08-18T17:19:51.381756Z",
        "updated_at": "2025-08-18T17:19:51.381756Z",
        "version": "1.0.0",
        "identifier": [],
        "language": null,
        "implicit_rules": null,
        "meta_profile": [],
        "meta_source": null,
        "meta_security": [],
        "meta_tag": [],
        "resource_type": "CodeableConcept",
        "agent_context": null,
        "status": "active",
        "text": "Sample DiagnosticReport",
        "contained": null,
        "extension": null,
        "modifier_extension": null,
        "coding": []
      },
      "subject": null,
      "encounter": null,
      "effective_datetime": null,
      "effective_period": null,
      "issued": null,
      "performer": [],
      "results_interpreter": [],
      "specimen": [],
      "result": [],
      "imaging_study": [],
      "media": [],
      "conclusion": null,
      "conclusion_code": [],
      "presented_form": []
    }
    ```

=== "YAML"

    ```yaml
    id: diagnosticreport-e953985e
    created_at: '2025-08-18T17:19:51.381768Z'
    updated_at: '2025-08-18T17:19:51.381768Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: DiagnosticReport
    agent_context: null
    status: final
    text: null
    contained: null
    extension: null
    modifier_extension: null
    based_on: []
    category: []
    code:
      id: codeableconcept-1310712c
      created_at: '2025-08-18T17:19:51.381756Z'
      updated_at: '2025-08-18T17:19:51.381756Z'
      version: 1.0.0
      identifier: []
      language: null
      implicit_rules: null
      meta_profile: []
      meta_source: null
      meta_security: []
      meta_tag: []
      resource_type: CodeableConcept
      agent_context: null
      status: active
      text: Sample DiagnosticReport
      contained: null
      extension: null
      modifier_extension: null
      coding: []
    subject: null
    encounter: null
    effective_datetime: null
    effective_period: null
    issued: null
    performer: []
    results_interpreter: []
    specimen: []
    result: []
    imaging_study: []
    media: []
    conclusion: null
    conclusion_code: []
    presented_form: []
    
    ```

=== "Schema"

    #### DiagnosticReport Schema

    DiagnosticReport resource for clinical decisions.

    The findings and interpretation of diagnostic tests performed on patients,
    groups of patients, devices, and locations, and/or specimens derived from these.

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Version of the resource |
    | identifier | list[str] | Business identifier for report |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['DiagnosticReport'] | Resource type identifier |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | status | <enum 'DiagnosticReportStatus'> | Status of the diagnostic report |
    | text | str | None | Human-readable summary of the resource content (e.g., Patient John Doe, 45 years old) |
    | contained | list[hacs_models.base_resource.BaseResource] | None | Resources contained within this resource |
    | extension | dict[str, typing.Any] | None | Additional content defined by implementations (e.g., {'url': 'custom-field', 'valueString': 'custom-value'}) |
    | modifier_extension | dict[str, typing.Any] | None | Extensions that cannot be ignored (e.g., {'url': 'critical-field', 'valueBoolean': True}) |
    | based_on | list[str] | What was requested |
    | category | list[hacs_models.observation.CodeableConcept] | Service category |
    | code | <class 'hacs_models.observation.CodeableConcept'> | Name/Code for this diagnostic report |
    | subject | str | None | The subject of the report - usually, but not always, the patient |
    | encounter | str | None | Health care event when test ordered |
    | effective_datetime | str | None | Clinically relevant time/time-period for report |
    | effective_period | str | None | Clinically relevant time period for report |
    | issued | str | None | DateTime this version was made |
    | performer | list[str] | Responsible Diagnostic Service |
    | results_interpreter | list[str] | Primary result interpreter |
    | specimen | list[str] | Specimens this report is based on |
    | result | list[str] | Observations included in this report |
    | imaging_study | list[str] | Reference to full details of imaging associated with the diagnostic report |
    | media | list[hacs_models.diagnostic_report.DiagnosticReportMedia] | Key images associated with this report |
    | conclusion | str | None | Clinical conclusion (impression) summary |
    | conclusion_code | list[hacs_models.observation.CodeableConcept] | Codes for the clinical conclusion |
    | presented_form | list[str] | Entire report as issued |



### AllergyIntolerance

**Scope & Usage**

SAFETY-CRITICAL documentation of allergies, intolerances, and adverse reactions to substances including medications, foods, and environmental factors. Essential for clinical decision support, medication ordering, and patient safety alerts. Includes severity assessment, reaction details, and verification status for comprehensive allergy management.

**Boundaries**

Do not use for adverse events during treatment (use AdverseEvent), side effects of current medications (use Observation), or family history of allergies (use FamilyMemberHistory). Focus on patient's own confirmed or suspected allergies/intolerances that impact care decisions.

**Relationships**

- References: Patient via patient (REQUIRED), Encounter via encounter, Practitioner via recorder/asserter
- Critical for: MedicationRequest contraindication checking, care planning, emergency alerts
- Safety links: medication ordering systems, clinical decision support, emergency care protocols

**References**

- Patient.patient (REQUIRED)
- medication and food ordering systems
- clinical decision support

**Tools**

- check_allergy_contraindications
- validate_allergy_severity
- generate_allergy_alerts
- reconcile_allergy_history
- assess_cross_reactivity


**Example**

=== "Rendered"

    #### AllergyIntolerance

    | Field | Value |
    |---|---|
    | resource_type | AllergyIntolerance |
    | id | allergyintolerance-2e88495f |
    | status | active |
    | created_at | 2025-08-18T17:19:51.386972Z |
    | updated_at | 2025-08-18T17:19:51.386972Z |

=== "JSON"

    ```json
    {
      "id": "allergyintolerance-2e88495f",
      "created_at": "2025-08-18T17:19:51.386972Z",
      "updated_at": "2025-08-18T17:19:51.386972Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "AllergyIntolerance",
      "agent_context": null,
      "status": "active",
      "text": null,
      "contained": null,
      "extension": null,
      "modifier_extension": null,
      "clinical_status": "active",
      "verification_status": null,
      "type": null,
      "category": [],
      "criticality": null,
      "code": null,
      "patient": "Patient/patient-123",
      "encounter": null,
      "onset_datetime": null,
      "last_occurrence": null,
      "recorder": null,
      "asserter": null,
      "reaction": [],
      "note": null
    }
    ```

=== "YAML"

    ```yaml
    id: allergyintolerance-2e88495f
    created_at: '2025-08-18T17:19:51.386972Z'
    updated_at: '2025-08-18T17:19:51.386972Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: AllergyIntolerance
    agent_context: null
    status: active
    text: null
    contained: null
    extension: null
    modifier_extension: null
    clinical_status: active
    verification_status: null
    type: null
    category: []
    criticality: null
    code: null
    patient: Patient/patient-123
    encounter: null
    onset_datetime: null
    last_occurrence: null
    recorder: null
    asserter: null
    reaction: []
    note: null
    
    ```

=== "Schema"

    #### AllergyIntolerance Schema

    AllergyIntolerance resource for patient safety.

    Risk of harmful or undesirable, physiological response which is unique
    to an individual and associated with exposure to a substance.

    This is a SAFETY-CRITICAL resource in healthcare systems.

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Version of the resource |
    | identifier | list[str] | External identifiers for this item |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['AllergyIntolerance'] | Resource type identifier |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | status | <class 'str'> | Current status of the resource (e.g., active) |
    | text | str | None | Human-readable summary of the resource content (e.g., Patient John Doe, 45 years old) |
    | contained | list[hacs_models.base_resource.BaseResource] | None | Resources contained within this resource |
    | extension | dict[str, typing.Any] | None | Additional content defined by implementations (e.g., {'url': 'custom-field', 'valueString': 'custom-value'}) |
    | modifier_extension | dict[str, typing.Any] | None | Extensions that cannot be ignored (e.g., {'url': 'critical-field', 'valueBoolean': True}) |
    | clinical_status | <enum 'AllergyIntoleranceStatus'> | Active | inactive | resolved |
    | verification_status | str | None | Assertion about certainty associated with the propensity |
    | type | hacs_models.types.AllergyIntoleranceType | None | Allergy or Intolerance (generally food, medication, environment, biologic) |
    | category | list[hacs_models.types.AllergyIntoleranceType] | Food | medication | environment | biologic |
    | criticality | hacs_models.types.AllergyCriticality | None | Estimate of potential clinical harm |
    | code | hacs_models.observation.CodeableConcept | None | Code that identifies the allergy or intolerance |
    | patient | <class 'str'> | Who the allergy or intolerance is for |
    | encounter | str | None | Encounter when the allergy or intolerance was asserted |
    | onset_datetime | str | None | When allergy or intolerance was identified |
    | last_occurrence | str | None | Date(/time) of last known occurrence of a reaction |
    | recorder | str | None | Individual who recorded the record and takes responsibility |
    | asserter | str | None | Source of the information about the allergy |
    | reaction | list[hacs_models.allergy_intolerance.AllergyIntoleranceReaction] | Adverse reaction events linked to exposure to substance |
    | note | str | None | Additional text not captured in other fields |



### FamilyMemberHistory

**Scope & Usage**

Significant health conditions and risk factors for biological relatives of the patient, supporting genetic counseling, risk assessment, and preventive care planning. Includes hereditary conditions, familial patterns, age of onset, and outcomes. Critical for identifying genetic predispositions and informing screening recommendations.

**Boundaries**

Do not record patient's own conditions (use Condition), non-biological relationships unless medically relevant, or general health information without clinical significance. Focus on conditions that impact patient's genetic risk or care planning.

**Relationships**

- References: Patient via patient, Condition via condition (what condition the relative had)
- Supports: genetic risk assessment, preventive care planning, family history documentation
- Links: may reference genetic testing, screening recommendations

**References**

- Patient.patient
- Condition references for family member conditions

**Tools**

- assess_genetic_risk
- generate_family_history_summary
- identify_hereditary_patterns
- recommend_genetic_screening


**Example**

=== "Rendered"

    #### FamilyMemberHistory

    | Field | Value |
    |---|---|
    | resource_type | FamilyMemberHistory |
    | id | familymemberhistory-a4251201 |
    | status | completed |
    | created_at | 2025-08-18T17:19:51.388622Z |
    | updated_at | 2025-08-18T17:19:51.388622Z |

=== "JSON"

    ```json
    {
      "id": "familymemberhistory-a4251201",
      "created_at": "2025-08-18T17:19:51.388622Z",
      "updated_at": "2025-08-18T17:19:51.388622Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "FamilyMemberHistory",
      "agent_context": null,
      "status": "completed",
      "text": null,
      "contained": null,
      "extension": null,
      "modifier_extension": null,
      "patient_ref": null,
      "relationship_text": null,
      "name": null,
      "sex": null,
      "condition_text": null,
      "outcome_text": null,
      "contributed_to_death": null
    }
    ```

=== "YAML"

    ```yaml
    id: familymemberhistory-a4251201
    created_at: '2025-08-18T17:19:51.388622Z'
    updated_at: '2025-08-18T17:19:51.388622Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: FamilyMemberHistory
    agent_context: null
    status: completed
    text: null
    contained: null
    extension: null
    modifier_extension: null
    patient_ref: null
    relationship_text: null
    name: null
    sex: null
    condition_text: null
    outcome_text: null
    contributed_to_death: null
    
    ```

=== "Schema"

    #### FamilyMemberHistory Schema

    Base class for domain-specific healthcare resources.

    Extends BaseResource with additional fields and functionality
    specific to FHIR domain resources (Patient, Observation, etc.).

    This follows FHIR's DomainResource pattern where most clinical
    resources inherit common patterns like text, contained resources,
    extensions, and modifierExtensions.

    **Protocol Compliance:**
        Implements: ClinicalResource protocol patterns

        This ensures all clinical resources provide:
        - Patient ID association (get_patient_id method)
        - Status tracking (status field)
        - Resource type identification (inherited from BaseResource)

    Features:
        - Human-readable text representation
        - Support for contained resources
        - Extension mechanism for additional data
        - Modifier extensions for data that changes meaning
        - Clinical resource protocol compliance

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Version of the resource |
    | identifier | list[str] | External identifiers for the resource (e.g., MRN, accession, system-specific IDs) (e.g., ['MRN:12345', 'local:abc-001']) |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['FamilyMemberHistory'] | None |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | status | <class 'str'> | partial | completed | entered-in-error | health-unknown |
    | text | str | None | Human-readable summary of the resource content (e.g., Patient John Doe, 45 years old) |
    | contained | list[hacs_models.base_resource.BaseResource] | None | Resources contained within this resource |
    | extension | dict[str, typing.Any] | None | Additional content defined by implementations (e.g., {'url': 'custom-field', 'valueString': 'custom-value'}) |
    | modifier_extension | dict[str, typing.Any] | None | Extensions that cannot be ignored (e.g., {'url': 'critical-field', 'valueBoolean': True}) |
    | patient_ref | str | None | Patient reference |
    | relationship_text | str | None | Relationship (e.g., mother, father, aunt) |
    | name | str | None | Family member name (optional) |
    | sex | str | None | male | female | other | unknown |
    | condition_text | str | None | Condition summary (free text) |
    | outcome_text | str | None | Outcome summary (free text) |
    | contributed_to_death | bool | None | Whether the condition contributed to death |



### Immunization

**Scope & Usage**

Documentation of immunization events including vaccines administered, lot numbers, administration details, and reaction monitoring. Supports immunization tracking, schedule management, contraindication checking, and public health reporting. Critical for preventive care and infectious disease control.

**Boundaries**

Do not use for immunization orders (use ServiceRequest), adverse reactions (use AdverseEvent as separate resource), or vaccination schedules (use protocols/guidelines). Focus on actual administration events, not planning or reactions.

**Relationships**

- References: Patient via patient, Practitioner via performer, Organization via location, Medication via vaccineCode
- Supports: immunization registry, schedule tracking, contraindication checking
- Links: may reference immunization recommendations, adverse events, lot tracking

**References**

- Patient.patient
- vaccination schedules, adverse event monitoring

**Tools**

- check_immunization_schedule
- validate_vaccine_contraindications
- track_immunization_series
- generate_immunization_record


**Example**

=== "Rendered"

    #### Immunization

    | Field | Value |
    |---|---|
    | resource_type | Immunization |
    | id | immunization-2644ac97 |
    | status | completed |
    | created_at | 2025-08-18T17:19:51.392084Z |
    | updated_at | 2025-08-18T17:19:51.392084Z |

=== "JSON"

    ```json
    {
      "id": "immunization-2644ac97",
      "created_at": "2025-08-18T17:19:51.392084Z",
      "updated_at": "2025-08-18T17:19:51.392084Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "Immunization",
      "agent_context": null,
      "status": "completed",
      "text": null,
      "contained": null,
      "extension": null,
      "modifier_extension": null,
      "vaccine_code": null,
      "patient_ref": null,
      "occurrence_datetime": null,
      "recorded": null,
      "encounter_ref": null,
      "location_ref": null,
      "manufacturer_ref": null,
      "lot_number": null,
      "expiration_date": null,
      "site_text": null,
      "route_text": null,
      "dose_quantity": null,
      "note": [],
      "reason_text": []
    }
    ```

=== "YAML"

    ```yaml
    id: immunization-2644ac97
    created_at: '2025-08-18T17:19:51.392084Z'
    updated_at: '2025-08-18T17:19:51.392084Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: Immunization
    agent_context: null
    status: completed
    text: null
    contained: null
    extension: null
    modifier_extension: null
    vaccine_code: null
    patient_ref: null
    occurrence_datetime: null
    recorded: null
    encounter_ref: null
    location_ref: null
    manufacturer_ref: null
    lot_number: null
    expiration_date: null
    site_text: null
    route_text: null
    dose_quantity: null
    note: []
    reason_text: []
    
    ```

=== "Schema"

    #### Immunization Schema

    Base class for domain-specific healthcare resources.

    Extends BaseResource with additional fields and functionality
    specific to FHIR domain resources (Patient, Observation, etc.).

    This follows FHIR's DomainResource pattern where most clinical
    resources inherit common patterns like text, contained resources,
    extensions, and modifierExtensions.

    **Protocol Compliance:**
        Implements: ClinicalResource protocol patterns

        This ensures all clinical resources provide:
        - Patient ID association (get_patient_id method)
        - Status tracking (status field)
        - Resource type identification (inherited from BaseResource)

    Features:
        - Human-readable text representation
        - Support for contained resources
        - Extension mechanism for additional data
        - Modifier extensions for data that changes meaning
        - Clinical resource protocol compliance

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Version of the resource |
    | identifier | list[str] | External identifiers for the resource (e.g., MRN, accession, system-specific IDs) (e.g., ['MRN:12345', 'local:abc-001']) |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['Immunization'] | None |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | status | <class 'str'> | completed | entered-in-error | not-done |
    | text | str | None | Human-readable summary of the resource content (e.g., Patient John Doe, 45 years old) |
    | contained | list[hacs_models.base_resource.BaseResource] | None | Resources contained within this resource |
    | extension | dict[str, typing.Any] | None | Additional content defined by implementations (e.g., {'url': 'custom-field', 'valueString': 'custom-value'}) |
    | modifier_extension | dict[str, typing.Any] | None | Extensions that cannot be ignored (e.g., {'url': 'critical-field', 'valueBoolean': True}) |
    | vaccine_code | hacs_models.observation.CodeableConcept | None | Vaccine product administered |
    | patient_ref | str | None | Reference to Patient (e.g., Patient/123) |
    | occurrence_datetime | str | None | Date/time vaccine administered (ISO 8601) |
    | recorded | str | None | When the record was captured (ISO 8601) |
    | encounter_ref | str | None | Reference to Encounter |
    | location_ref | str | None | Reference to Location |
    | manufacturer_ref | str | None | Vaccine manufacturer Organization ref |
    | lot_number | str | None | Lot number |
    | expiration_date | str | None | Expiration date (YYYY-MM-DD) |
    | site_text | str | None | Body site (text) |
    | route_text | str | None | Administration route (text) |
    | dose_quantity | str | None | Dose quantity (text) |
    | note | list[str] | Additional notes about the immunization |
    | reason_text | list[str] | Reasons immunization occurred (text) |



---

## Medication Management

Drug information, prescriptions, and medication tracking

### Medication

**Scope & Usage**

Detailed definition of a medication including active ingredients, strength, form, manufacturer, and batch information. Serves as the master catalog entry for pharmaceutical products used in orders, administration, and dispensing. Supports medication identification, strength calculations, and interaction checking.

**Boundaries**

Do not use for prescriptions (use MedicationRequest), actual taking/administration (use MedicationStatement/MedicationAdministration), or inventory (use Medication with quantity extensions). Focus on the medication definition, not its usage context.

**Relationships**

- Referenced by: MedicationRequest.medication, MedicationStatement.medication, MedicationAdministration.medication, MedicationDispense.medication
- Contains: ingredients, manufacturer details, packaging information
- Supports: drug interaction checking, allergy alerts, formulary management

**References**

- MedicationRequest.medication
- ingredient references to other Medication/Substance

**Tools**

- check_drug_interactions
- validate_medication_coding
- calculate_dosage_equivalents
- check_allergy_contraindications


**Example**

=== "Rendered"

    #### Medication

    | Field | Value |
    |---|---|
    | resource_type | Medication |
    | id | medication-ba43d5aa |
    | created_at | 2025-08-18T17:19:51.397734Z |
    | updated_at | 2025-08-18T17:19:51.397735Z |

=== "JSON"

    ```json
    {
      "id": "medication-ba43d5aa",
      "created_at": "2025-08-18T17:19:51.397734Z",
      "updated_at": "2025-08-18T17:19:51.397735Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "Medication",
      "agent_context": null,
      "status": null,
      "text": null,
      "contained": null,
      "extension": null,
      "modifier_extension": null,
      "code": null,
      "manufacturer": null,
      "form": null,
      "amount": null,
      "ingredient": [],
      "batch": null,
      "category": [],
      "schedule": null,
      "strength_description": null,
      "special_handling": [],
      "ndc": null,
      "generic_name": null,
      "brand_name": null
    }
    ```

=== "YAML"

    ```yaml
    id: medication-ba43d5aa
    created_at: '2025-08-18T17:19:51.397734Z'
    updated_at: '2025-08-18T17:19:51.397735Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: Medication
    agent_context: null
    status: null
    text: null
    contained: null
    extension: null
    modifier_extension: null
    code: null
    manufacturer: null
    form: null
    amount: null
    ingredient: []
    batch: null
    category: []
    schedule: null
    strength_description: null
    special_handling: []
    ndc: null
    generic_name: null
    brand_name: null
    
    ```

=== "Schema"

    #### Medication Schema

    Medication resource for pharmaceutical product representation.

    A medication is a pharmaceutical product which may be consumable, injectable
    or other types of product. Used to represent branded products, generic products,
    investigational products, and clinical drugs.

    This resource covers all medications except blood products, which use BiologicallyDerivedProduct.

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Version of the resource |
    | identifier | list[str] | Business identifier for this medication (e.g., ['urn:oid:1.2.3.4.5.6.7.8.9|12345', 'NDC:0123-4567-89']) |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['Medication'] | None |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | status | hacs_models.types.MedicationStatus | None | Status of this medication (active, inactive, entered-in-error) |
    | text | str | None | Human-readable summary of the resource content (e.g., Patient John Doe, 45 years old) |
    | contained | list[hacs_models.base_resource.BaseResource] | None | Resources contained within this resource |
    | extension | dict[str, typing.Any] | None | Additional content defined by implementations (e.g., {'url': 'custom-field', 'valueString': 'custom-value'}) |
    | modifier_extension | dict[str, typing.Any] | None | Extensions that cannot be ignored (e.g., {'url': 'critical-field', 'valueBoolean': True}) |
    | code | hacs_models.observation.CodeableConcept | None | Codes that identify this medication (e.g., {'coding': [{'system': 'http://www.nlm.nih.gov/research/umls/rxnorm', 'code': '313782', 'display': 'Acetaminophen 325 MG Oral Tablet'}], 'text': 'Acetaminophen 325mg tablets'}) |
    | manufacturer | str | None | Manufacturer of the item (e.g., Organization/manufacturer-acme-pharma) |
    | form | hacs_models.observation.CodeableConcept | None | Form of the medication (tablet, capsule, liquid, etc.) (e.g., {'coding': [{'system': 'http://snomed.info/sct', 'code': '421026006', 'display': 'Oral tablet'}], 'text': 'Tablet'}) |
    | amount | dict[str, typing.Any] | None | Amount of drug in package (e.g., {'numerator': {'value': 100, 'unit': 'tablets'}, 'denominator': {'value': 1, 'unit': 'bottle'}}) |
    | ingredient | list[hacs_models.medication.MedicationIngredient] | Active or inactive ingredient |
    | batch | hacs_models.medication.MedicationBatch | None | Details about packaged medications |
    | category | list[hacs_models.observation.CodeableConcept] | Category or classification of the medication (e.g., [{'coding': [{'system': 'http://terminology.hl7.org/CodeSystem/medication-category', 'code': 'prescription', 'display': 'Prescription'}], 'text': 'Prescription Medication'}]) |
    | schedule | hacs_models.observation.CodeableConcept | None | Controlled substance schedule (e.g., {'coding': [{'system': 'http://terminology.hl7.org/CodeSystem/v3-substanceAdminSubstitution', 'code': 'C-II', 'display': 'Schedule II'}], 'text': 'Schedule II Controlled Substance'}) |
    | strength_description | str | None | Human-readable description of strength/concentration (e.g., 500mg) |
    | special_handling | list[hacs_models.observation.CodeableConcept] | Special handling requirements (refrigeration, light-sensitive, etc.) |
    | ndc | str | None | National Drug Code (US) (e.g., 0123-4567-89) |
    | generic_name | str | None | Generic or non-proprietary name (e.g., acetaminophen) |
    | brand_name | str | None | Brand or trade name (e.g., Tylenol) |



### MedicationRequest

**Scope & Usage**

Order or authorization for supply and administration of medication to a patient. Represents prescriptions, medication orders, and medication authorizations with detailed dosing instructions, quantity, refills, and substitution rules. Supports complex dosing regimens, conditional orders, and medication reconciliation workflows. Includes prescriber information, pharmacy instructions, and administration context.

**Boundaries**

Do not use for actual medication taking/administration (use MedicationStatement/MedicationAdministration), medication definitions (use Medication), or medication dispensing (use MedicationDispense). Focus on the intent/order, not the fulfillment. Do not use for medication history or adherence tracking.

**Relationships**

- References: Patient via subject, Practitioner via requester, Medication via medicationReference, Encounter via encounter
- Based on: CarePlan via basedOn, ServiceRequest via basedOn
- Supports: MedicationDispense.authorizingPrescription, MedicationAdministration.request
- Groups: priorPrescription (medication changes), groupIdentifier (related orders)

**References**

- Patient.subject
- Practitioner.requester
- Medication.medicationReference
- Encounter.encounter

**Tools**

- validate_prescription_tool
- route_prescription_tool
- check_contraindications_tool
- check_drug_interactions_tool


**Example**

=== "Rendered"

    #### MedicationRequest

    | Field | Value |
    |---|---|
    | resource_type | MedicationRequest |
    | id | medicationrequest-c795088e |
    | status | active |
    | subject | Patient/patient-123 |
    | dosage_instruction | [] |
    | intent | order |
    | created_at | 2025-08-18T17:19:51.403999Z |
    | updated_at | 2025-08-18T17:19:51.404000Z |

=== "JSON"

    ```json
    {
      "id": "medicationrequest-c795088e",
      "created_at": "2025-08-18T17:19:51.403999Z",
      "updated_at": "2025-08-18T17:19:51.404000Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "MedicationRequest",
      "agent_context": null,
      "status": "active",
      "text": null,
      "contained": null,
      "extension": null,
      "modifier_extension": null,
      "intent": "order",
      "category": [],
      "priority": null,
      "do_not_perform": null,
      "medication_codeable_concept": null,
      "medication_reference": null,
      "subject": "Patient/patient-123",
      "encounter": null,
      "authored_on": null,
      "requester": null,
      "performer": null,
      "reason_code": [],
      "reason_reference": [],
      "note": [],
      "dosage_instruction": [],
      "dispense_request": null,
      "substitution": null
    }
    ```

=== "YAML"

    ```yaml
    id: medicationrequest-c795088e
    created_at: '2025-08-18T17:19:51.403999Z'
    updated_at: '2025-08-18T17:19:51.404000Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: MedicationRequest
    agent_context: null
    status: active
    text: null
    contained: null
    extension: null
    modifier_extension: null
    intent: order
    category: []
    priority: null
    do_not_perform: null
    medication_codeable_concept: null
    medication_reference: null
    subject: Patient/patient-123
    encounter: null
    authored_on: null
    requester: null
    performer: null
    reason_code: []
    reason_reference: []
    note: []
    dosage_instruction: []
    dispense_request: null
    substitution: null
    
    ```

=== "Schema"

    #### MedicationRequest Schema

    MedicationRequest resource for prescription and medication ordering.

    An order or request for both supply of the medication and the instructions
    for administration of the medication to a patient. Used for prescriptions,
    medication orders, and other medication-related requests.

    This is a SAFETY-CRITICAL resource in healthcare systems for medication management.

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Version of the resource |
    | identifier | list[str] | External identifiers for this medication request (e.g., ['urn:oid:1.2.3.4.5.6.7.8.9|12345', 'prescription-number-67890']) |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['MedicationRequest'] | None |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | status | <enum 'MedicationRequestStatus'> | Status of the medication request (active, completed, cancelled, etc.) |
    | text | str | None | Human-readable summary of the resource content (e.g., Patient John Doe, 45 years old) |
    | contained | list[hacs_models.base_resource.BaseResource] | None | Resources contained within this resource |
    | extension | dict[str, typing.Any] | None | Additional content defined by implementations (e.g., {'url': 'custom-field', 'valueString': 'custom-value'}) |
    | modifier_extension | dict[str, typing.Any] | None | Extensions that cannot be ignored (e.g., {'url': 'critical-field', 'valueBoolean': True}) |
    | intent | <enum 'MedicationRequestIntent'> | Intent of the medication request (proposal, plan, order, etc.) |
    | category | list[hacs_models.observation.CodeableConcept] | Type of medication usage (inpatient, outpatient, community, etc.) (e.g., [{'coding': [{'system': 'http://terminology.hl7.org/CodeSystem/medicationrequest-category', 'code': 'outpatient', 'display': 'Outpatient'}], 'text': 'Outpatient'}]) |
    | priority | hacs_models.types.MedicationRequestPriority | None | Routine | urgent | asap | stat |
    | do_not_perform | bool | None | True if medication must not be performed |
    | medication_codeable_concept | hacs_models.observation.CodeableConcept | None | Medication to be taken (coded) |
    | medication_reference | str | None | Reference to medication resource |
    | subject | <class 'str'> | Who or group medication request is for |
    | encounter | str | None | Encounter created as part of |
    | authored_on | str | None | When request was initially authored |
    | requester | str | None | Who/what requested the medication |
    | performer | str | None | Intended performer of administration |
    | reason_code | list[hacs_models.observation.CodeableConcept] | Reason or indication for ordering the medication |
    | reason_reference | list[str] | Condition or observation that supports why the medication was ordered |
    | note | list[str] | Information about the prescription |
    | dosage_instruction | list[hacs_models.medication_request.Dosage] | How medication should be taken |
    | dispense_request | dict[str, typing.Any] | None | Medication supply authorization (e.g., {'initial_fill': {'quantity': {'value': 30, 'unit': 'tablets'}, 'duration': {'value': 30, 'unit': 'days'}}, 'dispense_interval': {'value': 30, 'unit': 'days'}, 'validity_period': {'start': '2024-01-01T00:00:00Z', 'end': '2024-12-31T23:59:59Z'}, 'number_of_repeats_allowed': 5, 'quantity': {'value': 100, 'unit': 'tablets'}, 'expected_supply_duration': {'value': 30, 'unit': 'days'}, 'performer': 'Organization/pharmacy-123'}) |
    | substitution | hacs_models.medication_request.MedicationRequestSubstitution | None | Any restrictions on medication substitution |



---

## Care Coordination

Scheduling, planning, and care team management

### Appointment

**Scope & Usage**

Scheduled time slots for healthcare services between patients and providers, including routine visits, procedures, consultations, and follow-ups. Supports appointment scheduling, resource allocation, calendar management, and care coordination. Includes cancellation handling, rescheduling, and no-show tracking.

**Boundaries**

Do not use for recording what actually happened during the visit (use Encounter), completed procedures (use Procedure), or orders for future services (use ServiceRequest). Focus on the scheduling and time reservation, not the clinical content.

**Relationships**

- References: Patient via participant, Practitioner via participant, ServiceRequest via supportingInformation, Location via location
- Generates: Encounter when appointment is fulfilled
- Supports: schedule management, resource planning, care coordination

**References**

- Patient/Practitioner via participant
- ServiceRequest for ordered services
- Location for venue

**Tools**

- schedule_appointment
- reschedule_appointment
- cancel_appointment
- check_appointment_conflicts
- send_appointment_reminders


**Example**

=== "Rendered"

    #### Appointment

    | Field | Value |
    |---|---|
    | resource_type | Appointment |
    | id | appointment-e4b715ab |
    | status | booked |
    | created_at | 2025-08-18T17:19:51.405663Z |
    | updated_at | 2025-08-18T17:19:51.405663Z |

=== "JSON"

    ```json
    {
      "id": "appointment-e4b715ab",
      "created_at": "2025-08-18T17:19:51.405663Z",
      "updated_at": "2025-08-18T17:19:51.405663Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "Appointment",
      "agent_context": null,
      "status": "booked",
      "text": null,
      "contained": null,
      "extension": null,
      "modifier_extension": null,
      "description": null,
      "start": null,
      "end": null,
      "patient_ref": null,
      "participant_refs": [],
      "reason_text": null
    }
    ```

=== "YAML"

    ```yaml
    id: appointment-e4b715ab
    created_at: '2025-08-18T17:19:51.405663Z'
    updated_at: '2025-08-18T17:19:51.405663Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: Appointment
    agent_context: null
    status: booked
    text: null
    contained: null
    extension: null
    modifier_extension: null
    description: null
    start: null
    end: null
    patient_ref: null
    participant_refs: []
    reason_text: null
    
    ```

=== "Schema"

    #### Appointment Schema

    Base class for domain-specific healthcare resources.

    Extends BaseResource with additional fields and functionality
    specific to FHIR domain resources (Patient, Observation, etc.).

    This follows FHIR's DomainResource pattern where most clinical
    resources inherit common patterns like text, contained resources,
    extensions, and modifierExtensions.

    **Protocol Compliance:**
        Implements: ClinicalResource protocol patterns

        This ensures all clinical resources provide:
        - Patient ID association (get_patient_id method)
        - Status tracking (status field)
        - Resource type identification (inherited from BaseResource)

    Features:
        - Human-readable text representation
        - Support for contained resources
        - Extension mechanism for additional data
        - Modifier extensions for data that changes meaning
        - Clinical resource protocol compliance

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Version of the resource |
    | identifier | list[str] | External identifiers for the resource (e.g., MRN, accession, system-specific IDs) (e.g., ['MRN:12345', 'local:abc-001']) |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['Appointment'] | None |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | status | <class 'str'> | proposed|pending|booked|arrived|fulfilled|cancelled|noshow|entered-in-error|checked-in|waitlist |
    | text | str | None | Human-readable summary of the resource content (e.g., Patient John Doe, 45 years old) |
    | contained | list[hacs_models.base_resource.BaseResource] | None | Resources contained within this resource |
    | extension | dict[str, typing.Any] | None | Additional content defined by implementations (e.g., {'url': 'custom-field', 'valueString': 'custom-value'}) |
    | modifier_extension | dict[str, typing.Any] | None | Extensions that cannot be ignored (e.g., {'url': 'critical-field', 'valueBoolean': True}) |
    | description | str | None | Additional information about the appointment |
    | start | str | None | Start time (ISO 8601) |
    | end | str | None | End time (ISO 8601) |
    | patient_ref | str | None | Reference to Patient |
    | participant_refs | list[str] | Other participant references (Practitioner/RelatedPerson) |
    | reason_text | str | None | Reason for the appointment (free text) |



### ServiceRequest

**Scope & Usage**

Request for services to be performed for patient including lab tests, imaging studies, consultations, procedures, and other clinical activities. Represents orders, referrals, and service requests with priority, timing, performer preferences, and clinical context. Supports order sets, standing orders, and conditional requests with detailed instructions and authorization requirements.

**Boundaries**

Do not use for medication orders (use MedicationRequest), appointment scheduling (use Appointment), or recording what was actually done (use Procedure/DiagnosticReport/Observation). Focus on the request/order, not the execution. Do not use for care planning (use CarePlan) or supply requests (use SupplyRequest).

**Relationships**

- References: Patient via subject, Practitioner via requester/performer, Encounter via encounter, Condition via reasonReference
- Supports: Procedure.basedOn, DiagnosticReport.basedOn, Observation.basedOn
- Groups: requisition (order sets), replaces (order changes), basedOn (protocols/guidelines)

**References**

- Patient.subject
- Practitioner.requester
- Encounter.encounter
- Condition/Observation in reasonReference

**Tools**

- validate_service_request_tool
- route_service_request_tool


**Example**

=== "Rendered"

    #### ServiceRequest

    | Field | Value |
    |---|---|
    | resource_type | ServiceRequest |
    | id | servicerequest-720aa227 |
    | status | active |
    | subject | Patient/patient-123 |
    | performer | [] |
    | based_on | [] |
    | intent | order |
    | created_at | 2025-08-18T17:19:51.444976Z |
    | updated_at | 2025-08-18T17:19:51.444981Z |

=== "JSON"

    ```json
    {
      "id": "servicerequest-720aa227",
      "created_at": "2025-08-18T17:19:51.444976Z",
      "updated_at": "2025-08-18T17:19:51.444981Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "ServiceRequest",
      "agent_context": null,
      "status": "active",
      "text": null,
      "contained": null,
      "extension": null,
      "modifier_extension": null,
      "instantiates_canonical": [],
      "instantiates_uri": [],
      "based_on": [],
      "replaces": [],
      "requisition": null,
      "intent": "order",
      "category": [],
      "priority": null,
      "do_not_perform": null,
      "code": null,
      "order_detail": [],
      "quantity_quantity": null,
      "quantity_ratio": null,
      "quantity_range": null,
      "subject": "Patient/patient-123",
      "encounter": null,
      "occurrence_datetime": null,
      "occurrence_period": null,
      "occurrence_timing": null,
      "as_needed_boolean": null,
      "as_needed_codeable_concept": null,
      "authored_on": null,
      "requester": null,
      "performer_type": null,
      "performer": [],
      "location_code": [],
      "location_reference": [],
      "reason_code": [],
      "reason_reference": [],
      "insurance": [],
      "supporting_info": [],
      "specimen": [],
      "body_site": [],
      "note": [],
      "patient_instruction": null,
      "relevant_history": []
    }
    ```

=== "YAML"

    ```yaml
    id: servicerequest-720aa227
    created_at: '2025-08-18T17:19:51.444976Z'
    updated_at: '2025-08-18T17:19:51.444981Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: ServiceRequest
    agent_context: null
    status: active
    text: null
    contained: null
    extension: null
    modifier_extension: null
    instantiates_canonical: []
    instantiates_uri: []
    based_on: []
    replaces: []
    requisition: null
    intent: order
    category: []
    priority: null
    do_not_perform: null
    code: null
    order_detail: []
    quantity_quantity: null
    quantity_ratio: null
    quantity_range: null
    subject: Patient/patient-123
    encounter: null
    occurrence_datetime: null
    occurrence_period: null
    occurrence_timing: null
    as_needed_boolean: null
    as_needed_codeable_concept: null
    authored_on: null
    requester: null
    performer_type: null
    performer: []
    location_code: []
    location_reference: []
    reason_code: []
    reason_reference: []
    insurance: []
    supporting_info: []
    specimen: []
    body_site: []
    note: []
    patient_instruction: null
    relevant_history: []
    
    ```

=== "Schema"

    #### ServiceRequest Schema

    ServiceRequest resource for care coordination.

    A record of a request for service such as diagnostic investigations,
    treatments, or operations to be performed.

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Version of the resource |
    | identifier | list[str] | External identifiers for this item |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['ServiceRequest'] | Resource type identifier |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | status | <enum 'ServiceRequestStatus'> | Draft | active | on-hold | revoked | completed | entered-in-error | unknown |
    | text | str | None | Human-readable summary of the resource content (e.g., Patient John Doe, 45 years old) |
    | contained | list[hacs_models.base_resource.BaseResource] | None | Resources contained within this resource |
    | extension | dict[str, typing.Any] | None | Additional content defined by implementations (e.g., {'url': 'custom-field', 'valueString': 'custom-value'}) |
    | modifier_extension | dict[str, typing.Any] | None | Extensions that cannot be ignored (e.g., {'url': 'critical-field', 'valueBoolean': True}) |
    | instantiates_canonical | list[str] | Instantiates FHIR protocol or definition |
    | instantiates_uri | list[str] | Instantiates external protocol or definition |
    | based_on | list[str] | What request fulfills |
    | replaces | list[str] | What request replaces |
    | requisition | str | None | Composite Request ID |
    | intent | <enum 'ServiceRequestIntent'> | Proposal | plan | directive | order | original-order | reflex-order | filler-order | instance-order | option |
    | category | list[hacs_models.observation.CodeableConcept] | Classification of service |
    | priority | hacs_models.types.ServiceRequestPriority | None | Routine | urgent | asap | stat |
    | do_not_perform | bool | None | True if service/procedure should not be performed |
    | code | hacs_models.observation.CodeableConcept | None | What is being requested/ordered |
    | order_detail | list[hacs_models.observation.CodeableConcept] | Additional order information |
    | quantity_quantity | hacs_models.observation.Quantity | None | Service amount as quantity |
    | quantity_ratio | str | None | Service amount as ratio |
    | quantity_range | str | None | Service amount as range |
    | subject | <class 'str'> | Individual or entity the service is ordered for |
    | encounter | str | None | Encounter in which the request was created |
    | occurrence_datetime | str | None | When service should occur |
    | occurrence_period | str | None | When service should occur (period) |
    | occurrence_timing | str | None | When service should occur (timing) |
    | as_needed_boolean | bool | None | Preconditions for service |
    | as_needed_codeable_concept | hacs_models.observation.CodeableConcept | None | Preconditions for service |
    | authored_on | str | None | Date request signed |
    | requester | str | None | Who/what is requesting service |
    | performer_type | hacs_models.observation.CodeableConcept | None | Performer role |
    | performer | list[str] | Requested performer |
    | location_code | list[hacs_models.observation.CodeableConcept] | Requested location |
    | location_reference | list[str] | Requested location reference |
    | reason_code | list[hacs_models.observation.CodeableConcept] | Explanation/Justification for procedure or service |
    | reason_reference | list[str] | Explanation/Justification for service or service |
    | insurance | list[str] | Associated insurance coverage |
    | supporting_info | list[str] | Additional clinical information |
    | specimen | list[str] | Procedure Samples |
    | body_site | list[hacs_models.observation.CodeableConcept] | Location on Body |
    | note | list[str] | Comments |
    | patient_instruction | str | None | Patient or consumer-oriented instructions |
    | relevant_history | list[str] | Request provenance |



### CarePlan

**Scope & Usage**

Comprehensive plan of care describing intended care activities, goals, and care team coordination for managing patient conditions. Integrates multiple care activities, tracks progress toward goals, and supports care coordination across providers. Includes both provider-driven and patient-driven care plans.

**Boundaries**

Do not use for individual orders (use ServiceRequest), single goals (use Goal as separate resource), or appointments (use Appointment). CarePlan orchestrates but doesn't replace individual resources. Do not use for workflows or protocols (use PlanDefinition).

**Relationships**

- References: Patient via subject, Goal via goal, Condition via addresses, ServiceRequest via activity.reference, CareTeam via careTeam
- Coordinates: multiple care activities, goals, care team members
- Supports: care coordination, progress tracking, multi-disciplinary care

**References**

- Patient.subject
- Goal.goal
- Condition.addresses
- ServiceRequest via activities

**Tools**

- create_care_plan
- update_care_plan_progress
- coordinate_care_activities
- track_care_plan_goals
- assign_care_team_roles


**Example**

=== "Rendered"

    #### CarePlan

    | Field | Value |
    |---|---|
    | resource_type | CarePlan |
    | id | careplan-9de116b1 |
    | status | active |
    | intent | plan |
    | created_at | 2025-08-18T17:19:51.447245Z |
    | updated_at | 2025-08-18T17:19:51.447247Z |

=== "JSON"

    ```json
    {
      "id": "careplan-9de116b1",
      "created_at": "2025-08-18T17:19:51.447245Z",
      "updated_at": "2025-08-18T17:19:51.447247Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "CarePlan",
      "agent_context": null,
      "status": "active",
      "text": null,
      "contained": null,
      "extension": null,
      "modifier_extension": null,
      "intent": "plan",
      "title": null,
      "description_text": null,
      "subject_ref": null,
      "encounter_ref": null,
      "goal_refs": [],
      "activity_text": [],
      "note": []
    }
    ```

=== "YAML"

    ```yaml
    id: careplan-9de116b1
    created_at: '2025-08-18T17:19:51.447245Z'
    updated_at: '2025-08-18T17:19:51.447247Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: CarePlan
    agent_context: null
    status: active
    text: null
    contained: null
    extension: null
    modifier_extension: null
    intent: plan
    title: null
    description_text: null
    subject_ref: null
    encounter_ref: null
    goal_refs: []
    activity_text: []
    note: []
    
    ```

=== "Schema"

    #### CarePlan Schema

    Base class for domain-specific healthcare resources.

    Extends BaseResource with additional fields and functionality
    specific to FHIR domain resources (Patient, Observation, etc.).

    This follows FHIR's DomainResource pattern where most clinical
    resources inherit common patterns like text, contained resources,
    extensions, and modifierExtensions.

    **Protocol Compliance:**
        Implements: ClinicalResource protocol patterns

        This ensures all clinical resources provide:
        - Patient ID association (get_patient_id method)
        - Status tracking (status field)
        - Resource type identification (inherited from BaseResource)

    Features:
        - Human-readable text representation
        - Support for contained resources
        - Extension mechanism for additional data
        - Modifier extensions for data that changes meaning
        - Clinical resource protocol compliance

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Version of the resource |
    | identifier | list[str] | External identifiers for the resource (e.g., MRN, accession, system-specific IDs) (e.g., ['MRN:12345', 'local:abc-001']) |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['CarePlan'] | None |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | status | <class 'str'> | draft|active|on-hold|revoked|completed|entered-in-error|unknown |
    | text | str | None | Human-readable summary of the resource content (e.g., Patient John Doe, 45 years old) |
    | contained | list[hacs_models.base_resource.BaseResource] | None | Resources contained within this resource |
    | extension | dict[str, typing.Any] | None | Additional content defined by implementations (e.g., {'url': 'custom-field', 'valueString': 'custom-value'}) |
    | modifier_extension | dict[str, typing.Any] | None | Extensions that cannot be ignored (e.g., {'url': 'critical-field', 'valueBoolean': True}) |
    | intent | <class 'str'> | proposal|plan|order|option |
    | title | str | None | Human-readable title |
    | description_text | str | None | Free-text description of the plan |
    | subject_ref | str | None | Patient reference |
    | encounter_ref | str | None | Encounter reference |
    | goal_refs | list[str] | References to Goal resources |
    | activity_text | list[str] | Planned activities (free text) |
    | note | list[str] | Notes and comments |



### CareTeam

**Scope & Usage**

Organized group of healthcare providers, support persons, and organizations responsible for coordinated delivery of care to a patient. Defines roles, responsibilities, communication patterns, and care coordination for multi-disciplinary care teams. Supports care coordination, responsibility assignment, and team communication.

**Boundaries**

Do not use for individual practitioner details (use Practitioner/PractitionerRole), organizational hierarchy (use Organization), or care activities (use CarePlan). Focus on team composition and coordination, not individual capabilities or specific care plans.

**Relationships**

- References: Patient via subject, Practitioner via participant.member, Organization via participant.member, CareTeam via managingOrganization
- Supports: CarePlan via careTeam, communication coordination, role assignments
- Enables: multi-disciplinary care, care coordination, responsibility tracking

**References**

- Patient.subject
- CarePlan.careTeam
- Practitioner/Organization via participants

**Tools**

- assemble_care_team
- assign_team_roles
- coordinate_team_communication
- track_team_responsibilities
- update_team_membership


**Example**

=== "Rendered"

    #### CareTeam

    | Field | Value |
    |---|---|
    | resource_type | CareTeam |
    | id | careteam-341fb885 |
    | status | active |
    | created_at | 2025-08-18T17:19:51.448839Z |
    | updated_at | 2025-08-18T17:19:51.448840Z |

=== "JSON"

    ```json
    {
      "id": "careteam-341fb885",
      "created_at": "2025-08-18T17:19:51.448839Z",
      "updated_at": "2025-08-18T17:19:51.448840Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "CareTeam",
      "agent_context": null,
      "status": "active",
      "text": null,
      "contained": null,
      "extension": null,
      "modifier_extension": null,
      "name": null,
      "subject_ref": null,
      "participant_refs": [],
      "note": []
    }
    ```

=== "YAML"

    ```yaml
    id: careteam-341fb885
    created_at: '2025-08-18T17:19:51.448839Z'
    updated_at: '2025-08-18T17:19:51.448840Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: CareTeam
    agent_context: null
    status: active
    text: null
    contained: null
    extension: null
    modifier_extension: null
    name: null
    subject_ref: null
    participant_refs: []
    note: []
    
    ```

=== "Schema"

    #### CareTeam Schema

    Base class for domain-specific healthcare resources.

    Extends BaseResource with additional fields and functionality
    specific to FHIR domain resources (Patient, Observation, etc.).

    This follows FHIR's DomainResource pattern where most clinical
    resources inherit common patterns like text, contained resources,
    extensions, and modifierExtensions.

    **Protocol Compliance:**
        Implements: ClinicalResource protocol patterns

        This ensures all clinical resources provide:
        - Patient ID association (get_patient_id method)
        - Status tracking (status field)
        - Resource type identification (inherited from BaseResource)

    Features:
        - Human-readable text representation
        - Support for contained resources
        - Extension mechanism for additional data
        - Modifier extensions for data that changes meaning
        - Clinical resource protocol compliance

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Version of the resource |
    | identifier | list[str] | External identifiers for the resource (e.g., MRN, accession, system-specific IDs) (e.g., ['MRN:12345', 'local:abc-001']) |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['CareTeam'] | None |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | status | <class 'str'> | proposed|active|suspended|inactive|entered-in-error |
    | text | str | None | Human-readable summary of the resource content (e.g., Patient John Doe, 45 years old) |
    | contained | list[hacs_models.base_resource.BaseResource] | None | Resources contained within this resource |
    | extension | dict[str, typing.Any] | None | Additional content defined by implementations (e.g., {'url': 'custom-field', 'valueString': 'custom-value'}) |
    | modifier_extension | dict[str, typing.Any] | None | Extensions that cannot be ignored (e.g., {'url': 'critical-field', 'valueBoolean': True}) |
    | name | str | None | Name of the care team |
    | subject_ref | str | None | Patient reference |
    | participant_refs | list[str] | Members (Practitioner/RelatedPerson/Organization) |
    | note | list[str] | Notes |



### NutritionOrder

**Scope & Usage**

Orders for therapeutic diets, enteral nutrition, oral supplements, and nutritional interventions tailored to patient medical conditions, allergies, and nutritional needs. Supports clinical nutrition management, dietary restrictions, feeding protocols, and nutritional therapy coordination.

**Boundaries**

Do not use for nutritional assessments (use Observation), meal planning without medical indication, or nutritional intake recording (use Observation). Focus on medically-ordered nutritional interventions, not general dietary preferences or measured outcomes.

**Relationships**

- References: Patient via subject, Practitioner via orderer, Condition via indication, AllergyIntolerance for restrictions
- Supports: clinical nutrition therapy, dietary management, feeding protocols
- Coordinates: with CarePlan, dietary services, clinical nutrition teams

**References**

- Patient.subject
- medical conditions requiring nutritional intervention
- allergy restrictions

**Tools**

- create_therapeutic_diet_order
- manage_nutrition_restrictions
- calculate_nutritional_requirements
- coordinate_feeding_protocols


**Example**

=== "Rendered"

    #### NutritionOrder

    | Field | Value |
    |---|---|
    | resource_type | NutritionOrder |
    | id | nutritionorder-45a9df10 |
    | status | active |
    | intent | order |
    | created_at | 2025-08-18T17:19:51.450405Z |
    | updated_at | 2025-08-18T17:19:51.450405Z |

=== "JSON"

    ```json
    {
      "id": "nutritionorder-45a9df10",
      "created_at": "2025-08-18T17:19:51.450405Z",
      "updated_at": "2025-08-18T17:19:51.450405Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "NutritionOrder",
      "agent_context": null,
      "status": "active",
      "text": null,
      "contained": null,
      "extension": null,
      "modifier_extension": null,
      "intent": "order",
      "patient_ref": null,
      "encounter_ref": null,
      "date_time": null,
      "oral_diet_text": null,
      "supplement_text": null,
      "enteral_formula_text": null
    }
    ```

=== "YAML"

    ```yaml
    id: nutritionorder-45a9df10
    created_at: '2025-08-18T17:19:51.450405Z'
    updated_at: '2025-08-18T17:19:51.450405Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: NutritionOrder
    agent_context: null
    status: active
    text: null
    contained: null
    extension: null
    modifier_extension: null
    intent: order
    patient_ref: null
    encounter_ref: null
    date_time: null
    oral_diet_text: null
    supplement_text: null
    enteral_formula_text: null
    
    ```

=== "Schema"

    #### NutritionOrder Schema

    Base class for domain-specific healthcare resources.

    Extends BaseResource with additional fields and functionality
    specific to FHIR domain resources (Patient, Observation, etc.).

    This follows FHIR's DomainResource pattern where most clinical
    resources inherit common patterns like text, contained resources,
    extensions, and modifierExtensions.

    **Protocol Compliance:**
        Implements: ClinicalResource protocol patterns

        This ensures all clinical resources provide:
        - Patient ID association (get_patient_id method)
        - Status tracking (status field)
        - Resource type identification (inherited from BaseResource)

    Features:
        - Human-readable text representation
        - Support for contained resources
        - Extension mechanism for additional data
        - Modifier extensions for data that changes meaning
        - Clinical resource protocol compliance

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Version of the resource |
    | identifier | list[str] | External identifiers for the resource (e.g., MRN, accession, system-specific IDs) (e.g., ['MRN:12345', 'local:abc-001']) |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['NutritionOrder'] | None |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | status | <class 'str'> | proposed|draft|active|on-hold|revoked|completed|entered-in-error|unknown |
    | text | str | None | Human-readable summary of the resource content (e.g., Patient John Doe, 45 years old) |
    | contained | list[hacs_models.base_resource.BaseResource] | None | Resources contained within this resource |
    | extension | dict[str, typing.Any] | None | Additional content defined by implementations (e.g., {'url': 'custom-field', 'valueString': 'custom-value'}) |
    | modifier_extension | dict[str, typing.Any] | None | Extensions that cannot be ignored (e.g., {'url': 'critical-field', 'valueBoolean': True}) |
    | intent | <class 'str'> | proposal|plan|order |
    | patient_ref | str | None | Patient reference |
    | encounter_ref | str | None | Encounter reference |
    | date_time | str | None | When the order was placed (ISO 8601) |
    | oral_diet_text | str | None | Free text oral diet instructions |
    | supplement_text | str | None | Free text supplement instructions |
    | enteral_formula_text | str | None | Free text enteral formula instructions |



### PlanDefinition

**Scope & Usage**

Reusable definition of clinical workflows, protocols, order sets, and care pathways that can be applied across multiple patients. Defines structured knowledge about care processes, decision trees, and best practices. Supports evidence-based care standardization and protocol-driven care delivery.

**Boundaries**

Do not use for patient-specific care plans (use CarePlan), individual orders (use ServiceRequest), or actual workflows in progress (use WorkflowDefinition for HACS workflows). Focus on reusable templates and protocols, not specific patient care instances.

**Relationships**

- Referenced by: CarePlan.instantiatesCanonical, ServiceRequest.instantiatesCanonical, WorkflowDefinition for HACS integration
- Contains: goal definitions, action sequences, decision logic, triggers
- Supports: protocol-based care, clinical decision support, standardized workflows

**References**

- CarePlan when instantiated
- ServiceRequest when protocols generate orders

**Tools**

- instantiate_clinical_protocol
- validate_protocol_adherence
- customize_protocol_for_patient
- track_protocol_outcomes


**Example**

=== "Rendered"

    #### PlanDefinition

    | Field | Value |
    |---|---|
    | resource_type | PlanDefinition |
    | id | plandefinition-bbcb8809 |
    | status | draft |
    | created_at | 2025-08-18T17:19:51.455863Z |
    | updated_at | 2025-08-18T17:19:51.455867Z |

=== "JSON"

    ```json
    {
      "id": "plandefinition-bbcb8809",
      "created_at": "2025-08-18T17:19:51.455863Z",
      "updated_at": "2025-08-18T17:19:51.455867Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "PlanDefinition",
      "agent_context": null,
      "status": "draft",
      "text": null,
      "contained": null,
      "extension": null,
      "modifier_extension": null,
      "url": null,
      "name": null,
      "title": null,
      "subtitle": null,
      "experimental": false,
      "date": null,
      "publisher": null,
      "contact": [],
      "description": null,
      "use_context": [],
      "jurisdiction": [],
      "purpose": null,
      "usage": null,
      "copyright": null,
      "approval_date": null,
      "last_review_date": null,
      "effective_period": null,
      "topic": [],
      "author": [],
      "editor": [],
      "reviewer": [],
      "endorser": [],
      "related_artifact": [],
      "library": [],
      "goal": [],
      "action": [],
      "type_": null,
      "subject_codeable_concept": null,
      "subject_reference": null
    }
    ```

=== "YAML"

    ```yaml
    id: plandefinition-bbcb8809
    created_at: '2025-08-18T17:19:51.455863Z'
    updated_at: '2025-08-18T17:19:51.455867Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: PlanDefinition
    agent_context: null
    status: draft
    text: null
    contained: null
    extension: null
    modifier_extension: null
    url: null
    name: null
    title: null
    subtitle: null
    experimental: false
    date: null
    publisher: null
    contact: []
    description: null
    use_context: []
    jurisdiction: []
    purpose: null
    usage: null
    copyright: null
    approval_date: null
    last_review_date: null
    effective_period: null
    topic: []
    author: []
    editor: []
    reviewer: []
    endorser: []
    related_artifact: []
    library: []
    goal: []
    action: []
    type_: null
    subject_codeable_concept: null
    subject_reference: null
    
    ```

=== "Schema"

    #### PlanDefinition Schema

    Definition of a plan for a series of actions.

    Represents pre-defined sets of actions for clinical protocols, decision support rules,
    order sets, and other healthcare workflows. Optimized for LLM context engineering
    withFHIR-aligned metadata and descriptive information.

    Key Features:
        - Rich metadata for LLM context understanding
        - Hierarchical action structures with dependencies
        - Goal-driven planning with measurable targets
        - Flexible triggering and conditional logic
        - Support for various clinical domains and use cases

    Example Use Cases:
        - Clinical practice guidelines
        - Order sets and protocols
        - Decision support rules
        - Care pathways and workflows
        - Quality measures and indicators

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Business version of the plan definition (e.g., 1.0.0) |
    | identifier | list[dict[str, typing.Any]] | Additional identifier for the plan definition (e.g., [{'system': 'http://example.org/plan-ids', 'value': 'HTN-MGMT-2024'}]) |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['PlanDefinition'] | None |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | status | <class 'str'> | Publication status (draft, active, retired, unknown) (e.g., draft) |
    | text | str | None | Human-readable summary of the resource content (e.g., Patient John Doe, 45 years old) |
    | contained | list[hacs_models.base_resource.BaseResource] | None | Resources contained within this resource |
    | extension | dict[str, typing.Any] | None | Additional content defined by implementations (e.g., {'url': 'custom-field', 'valueString': 'custom-value'}) |
    | modifier_extension | dict[str, typing.Any] | None | Extensions that cannot be ignored (e.g., {'url': 'critical-field', 'valueBoolean': True}) |
    | url | str | None | Canonical identifier for this plan definition (e.g., http://example.org/fhir/PlanDefinition/hypertension-management) |
    | name | str | None | Name for this plan definition (computer friendly) (e.g., HypertensionManagement) |
    | title | str | None | Human-friendly title of the plan definition (e.g., Hypertension Management Protocol) |
    | subtitle | str | None | Subordinate title for the plan definition (e.g., Primary Care Protocol) |
    | experimental | <class 'bool'> | Whether this plan definition is for testing purposes |
    | date | datetime.datetime | None | Date last changed |
    | publisher | str | None | Name of the publisher (organization or individual) (e.g., American Heart Association) |
    | contact | list[dict[str, typing.Any]] | Contact details for the publisher (e.g., [{'name': 'Clinical Guidelines Team', 'telecom': [{'system': 'email', 'value': 'guidelines@example.org'}]}]) |
    | description | str | None | Natural language description of the plan definition (e.g., Evidence-based protocol for management of hypertension in primary care settings) |
    | use_context | list[dict[str, typing.Any]] | Context the content is intended to support (e.g., [{'code': {'system': 'usage-context-type', 'code': 'venue'}, 'valueCodeableConcept': {'text': 'primary care'}}]) |
    | jurisdiction | list[dict[str, typing.Any]] | Intended jurisdiction for plan definition (e.g., [{'coding': [{'system': 'urn:iso:std:iso:3166', 'code': 'US', 'display': 'United States'}]}]) |
    | purpose | str | None | Why this plan definition is defined (e.g., Standardize hypertension care across primary care practices) |
    | usage | str | None | Describes the clinical usage of the plan definition (e.g., Use for all adult patients with newly diagnosed hypertension) |
    | copyright | str | None | Use and/or publishing restrictions |
    | approval_date | datetime.datetime | None | When the plan definition was approved by publisher |
    | last_review_date | datetime.datetime | None | When the plan definition was last reviewed |
    | effective_period | dict[str, datetime.datetime] | None | When the plan definition is expected to be used (e.g., {'start': '2024-01-01T00:00:00Z', 'end': '2024-12-31T23:59:59Z'}) |
    | topic | list[dict[str, typing.Any]] | Type of individual the plan definition is focused on (e.g., [{'coding': [{'system': 'http://snomed.info/sct', 'code': '38341003', 'display': 'Hypertension'}]}]) |
    | author | list[dict[str, typing.Any]] | Who authored the content (e.g., [{'name': 'Dr. Jane Smith', 'telecom': [{'system': 'email', 'value': 'jane.smith@example.org'}]}]) |
    | editor | list[dict[str, typing.Any]] | Who edited the content |
    | reviewer | list[dict[str, typing.Any]] | Who reviewed the content |
    | endorser | list[dict[str, typing.Any]] | Who endorsed the content |
    | related_artifact | list[dict[str, typing.Any]] | Additional documentation, citations, etc. (e.g., [{'type': 'citation', 'display': '2017 ACC/AHA Hypertension Guidelines', 'url': 'https://example.org/guidelines'}]) |
    | library | list[str] | Logic libraries used by the plan definition (e.g., ['Library/hypertension-logic']) |
    | goal | list[hacs_models.plan_definition.PlanDefinitionGoal] | Goals that describe what the activities within the plan are intended to achieve |
    | action | list[hacs_models.plan_definition.PlanDefinitionAction] | Actions or action groups that comprise the plan definition |
    | type_ | dict[str, typing.Any] | None | Type of plan definition (order-set, clinical-protocol, eca-rule, workflow-definition) (e.g., {'coding': [{'system': 'plan-definition-type', 'code': 'clinical-protocol'}]}) |
    | subject_codeable_concept | dict[str, typing.Any] | None | Type of individual the plan is focused on (e.g., {'coding': [{'system': 'http://hl7.org/fhir/resource-types', 'code': 'Patient'}]}) |
    | subject_reference | str | None | Individual the plan is focused on (e.g., Group/adult-hypertension-patients) |



---

## Healthcare Providers

Medical professionals and healthcare organizations

### Practitioner

**Scope & Usage**

Individual healthcare professional involved in care delivery (e.g., physicians, nurses, therapists). Includes identifiers, names, qualifications, and contact details for clinical attribution and care coordination.

**Boundaries**

Do not use for roles/assignments (use PractitionerRole when available) or for organizations (use Organization).

**Relationships**

- Referenced by: Encounter.participant, Procedure.performer, ServiceRequest.requester
- References: Organization via affiliation/managed organization

**References**

- Organization affiliations, CareTeam membership

**Tools**

- verify_practitioner_credential
- link_practitioner_to_organization
- update_practitioner_affiliation


**Example**

=== "Rendered"

    #### Practitioner

    | Field | Value |
    |---|---|
    | resource_type | Practitioner |
    | id | practitioner-47722625 |
    | status | active |
    | name | [] |
    | created_at | 2025-08-18T17:19:51.465793Z |
    | updated_at | 2025-08-18T17:19:51.465794Z |

=== "JSON"

    ```json
    {
      "id": "practitioner-47722625",
      "created_at": "2025-08-18T17:19:51.465793Z",
      "updated_at": "2025-08-18T17:19:51.465794Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "Practitioner",
      "agent_context": null,
      "status": "active",
      "text": null,
      "contained": null,
      "extension": null,
      "modifier_extension": null,
      "active": null,
      "name": [],
      "telecom": [],
      "address": [],
      "gender": null,
      "birth_date": null,
      "photo": [],
      "qualification": [],
      "communication": []
    }
    ```

=== "YAML"

    ```yaml
    id: practitioner-47722625
    created_at: '2025-08-18T17:19:51.465793Z'
    updated_at: '2025-08-18T17:19:51.465794Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: Practitioner
    agent_context: null
    status: active
    text: null
    contained: null
    extension: null
    modifier_extension: null
    active: null
    name: []
    telecom: []
    address: []
    gender: null
    birth_date: null
    photo: []
    qualification: []
    communication: []
    
    ```

=== "Schema"

    #### Practitioner Schema

    Practitioner resource for healthcare provider representation.

    A person who is directly or indirectly involved in the provisioning of healthcare.
    This includes physicians, nurses, therapists, administrators, and other healthcare workers.

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Version of the resource |
    | identifier | list[hacs_models.patient.Identifier] | External identifiers for this practitioner |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['Practitioner'] | Resource type identifier |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | status | <class 'str'> | Current status of the resource (e.g., active) |
    | text | str | None | Human-readable summary of the resource content (e.g., Patient John Doe, 45 years old) |
    | contained | list[hacs_models.base_resource.BaseResource] | None | Resources contained within this resource |
    | extension | dict[str, typing.Any] | None | Additional content defined by implementations (e.g., {'url': 'custom-field', 'valueString': 'custom-value'}) |
    | modifier_extension | dict[str, typing.Any] | None | Extensions that cannot be ignored (e.g., {'url': 'critical-field', 'valueBoolean': True}) |
    | active | bool | None | Whether this practitioner's record is in active use |
    | name | list[hacs_models.patient.HumanName] | The name(s) associated with the practitioner |
    | telecom | list[hacs_models.patient.ContactPoint] | Contact details that are available outside of a role |
    | address | list[hacs_models.patient.Address] | Address(es) of the practitioner that are not role specific |
    | gender | hacs_models.types.Gender | None | Administrative Gender - male | female | other | unknown |
    | birth_date | datetime.date | None | The date of birth for the practitioner |
    | photo | list[str] | Image of the practitioner (base64 encoded or URL) |
    | qualification | list[hacs_models.practitioner.PractitionerQualification] | Certification, licenses, or training pertaining to the provision of care |
    | communication | list[hacs_models.observation.CodeableConcept] | A language the practitioner can use in patient communication |



### Organization

**Scope & Usage**

Legal or administrative entity involved in healthcare delivery (e.g., hospitals, clinics, departments, insurers). Provides identity, contact, and hierarchical relationships used for care attribution, scheduling, billing, and coordination.

**Boundaries**

Not for individuals (use Practitioner). Use Location for physical service sites. Use OrganizationAffiliation (if available) for relationships between organizations.

**Relationships**

- Referenced by: Encounter.serviceProvider, Practitioner.organization, CareTeam.managingOrganization
- References: parent/child organizations, service locations

**References**

- Encounter.serviceProvider
- Practitioner.organization

**Tools**

- register_organization
- link_organization_affiliation
- manage_service_locations


**Example**

=== "Rendered"

    #### Organization

    | Field | Value |
    |---|---|
    | resource_type | Organization |
    | id | organization-35af4931 |
    | status | active |
    | created_at | 2025-08-18T17:19:51.473772Z |
    | updated_at | 2025-08-18T17:19:51.473775Z |

=== "JSON"

    ```json
    {
      "id": "organization-35af4931",
      "created_at": "2025-08-18T17:19:51.473772Z",
      "updated_at": "2025-08-18T17:19:51.473775Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "Organization",
      "agent_context": null,
      "status": "active",
      "text": null,
      "contained": null,
      "extension": null,
      "modifier_extension": null,
      "active": null,
      "type": [],
      "name": null,
      "alias": [],
      "description": null,
      "telecom": [],
      "address": [],
      "part_of": null,
      "contact": [],
      "endpoint": []
    }
    ```

=== "YAML"

    ```yaml
    id: organization-35af4931
    created_at: '2025-08-18T17:19:51.473772Z'
    updated_at: '2025-08-18T17:19:51.473775Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: Organization
    agent_context: null
    status: active
    text: null
    contained: null
    extension: null
    modifier_extension: null
    active: null
    type: []
    name: null
    alias: []
    description: null
    telecom: []
    address: []
    part_of: null
    contact: []
    endpoint: []
    
    ```

=== "Schema"

    #### Organization Schema

    Organization resource for healthcare facility representation.

    A formally or informally recognized grouping of people or organizations
    formed for the purpose of achieving some form of collective action.
    Includes companies, institutions, corporations, departments, community groups,
    healthcare practice groups, payer/insurer, etc.

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Version of the resource |
    | identifier | list[hacs_models.patient.Identifier] | Identifies this organization across multiple systems |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['Organization'] | Resource type identifier |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | status | <class 'str'> | Current status of the resource (e.g., active) |
    | text | str | None | Human-readable summary of the resource content (e.g., Patient John Doe, 45 years old) |
    | contained | list[hacs_models.base_resource.BaseResource] | None | Resources contained within this resource |
    | extension | dict[str, typing.Any] | None | Additional content defined by implementations (e.g., {'url': 'custom-field', 'valueString': 'custom-value'}) |
    | modifier_extension | dict[str, typing.Any] | None | Extensions that cannot be ignored (e.g., {'url': 'critical-field', 'valueBoolean': True}) |
    | active | bool | None | Whether the organization's record is still in active use |
    | type | list[hacs_models.observation.CodeableConcept] | Kind of organization (hospital, clinic, dept, etc.) |
    | name | str | None | Name used for the organization |
    | alias | list[str] | Alternative names the organization is known as |
    | description | str | None | Additional details about the organization that could be displayed |
    | telecom | list[hacs_models.patient.ContactPoint] | Contact details for the organization |
    | address | list[hacs_models.patient.Address] | Address(es) for the organization |
    | part_of | str | None | The organization this organization forms a part of |
    | contact | list[hacs_models.organization.OrganizationContact] | Contact for the organization for a certain purpose |
    | endpoint | list[str] | Technical endpoints providing access to services operated for the organization |



---

## Documentation & Records

Documents, reports, and information management

### DocumentReference

**Scope & Usage**

Metadata pointer to external clinical documents, images, and binary artifacts (e.g., PDFs, DICOM). Captures document identifiers, type, status, custodian, authorship, content attachments, and context. Used to reference content not represented as structured Composition/Document within the EHR.

**Boundaries**

Do not store narrative clinical content here (use Document/Composition). Use ImagingStudy for study-level imaging metadata; use Media for simple images. DocumentReference focuses on pointers and metadata, not the narrative or structured content itself.

**Relationships**

- References: Patient via subject, Practitioner/Organization via author/custodian, Encounter via context
- Links: to external repositories (e.g., PACS, CMS) via content.attachment
- May complement: DiagnosticReport, Composition

**References**

- Patient.subject
- Encounter.context
- custodian Organization
- author Practitioner/Organization

**Tools**

- validate_document_metadata
- resolve_document_location
- register_external_document
- link_document_to_record


**Example**

=== "Rendered"

    #### DocumentReference

    | Field | Value |
    |---|---|
    | resource_type | DocumentReference |
    | id | documentreference-1548d074 |
    | status | current |
    | created_at | 2025-08-18T17:19:51.475576Z |
    | updated_at | 2025-08-18T17:19:51.475577Z |

=== "JSON"

    ```json
    {
      "id": "documentreference-1548d074",
      "created_at": "2025-08-18T17:19:51.475576Z",
      "updated_at": "2025-08-18T17:19:51.475577Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "DocumentReference",
      "agent_context": null,
      "status": "current",
      "text": null,
      "contained": null,
      "extension": null,
      "modifier_extension": null,
      "doc_status": "final",
      "type_text": null,
      "category_text": null,
      "subject_ref": null,
      "author_ref": [],
      "custodian_ref": null,
      "date": null,
      "description": null,
      "attachment_url": null,
      "attachment_content_type": null,
      "title": null
    }
    ```

=== "YAML"

    ```yaml
    id: documentreference-1548d074
    created_at: '2025-08-18T17:19:51.475576Z'
    updated_at: '2025-08-18T17:19:51.475577Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: DocumentReference
    agent_context: null
    status: current
    text: null
    contained: null
    extension: null
    modifier_extension: null
    doc_status: final
    type_text: null
    category_text: null
    subject_ref: null
    author_ref: []
    custodian_ref: null
    date: null
    description: null
    attachment_url: null
    attachment_content_type: null
    title: null
    
    ```

=== "Schema"

    #### DocumentReference Schema

    Minimal document reference for HACS.

    Fields intentionally simplified for early usage:
    - status: current | superseded | entered-in-error (free string)
    - doc_status: preliminary | final | amended | entered-in-error (free string)
    - type_text/category_text: simple text descriptors for kind and category
    - subject_ref/author_ref/custodian_ref: FHIR-style reference strings
    - date: ISO 8601 string
    - description: human-readable description
    - attachment_url/content_type: where to access the document and its MIME type

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Version of the resource |
    | identifier | list[str] | External identifiers for the resource (e.g., MRN, accession, system-specific IDs) (e.g., ['MRN:12345', 'local:abc-001']) |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['DocumentReference'] | None |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | status | <class 'str'> | current | superseded | entered-in-error |
    | text | str | None | Human-readable summary of the resource content (e.g., Patient John Doe, 45 years old) |
    | contained | list[hacs_models.base_resource.BaseResource] | None | Resources contained within this resource |
    | extension | dict[str, typing.Any] | None | Additional content defined by implementations (e.g., {'url': 'custom-field', 'valueString': 'custom-value'}) |
    | modifier_extension | dict[str, typing.Any] | None | Extensions that cannot be ignored (e.g., {'url': 'critical-field', 'valueBoolean': True}) |
    | doc_status | str | None | preliminary | final | amended | entered-in-error |
    | type_text | str | None | Kind of document (LOINC text if available) |
    | category_text | str | None | High-level categorization of document |
    | subject_ref | str | None | Reference to the subject (e.g., Patient/xyz) |
    | author_ref | list[str] | Author references (e.g., Practitioner/xyz) |
    | custodian_ref | str | None | Organization maintaining the document |
    | date | str | None | When this document reference was created (ISO 8601) |
    | description | str | None | Human-readable description |
    | attachment_url | str | None | Where to access the document |
    | attachment_content_type | str | None | MIME type of the document |
    | title | str | None | Document title |



### Evidence

**Scope & Usage**

Literature and knowledge evidence entry with bibliographic metadata.

**Boundaries**

Clinical documentation belongs in Document; link Evidence from documents.

**Relationships**

- Referenced by: Document sections (via citation)


**Example**

=== "Rendered"

    #### Evidence

    | Field | Value |
    |---|---|
    | resource_type | Evidence |
    | id | evidence-c81c7241 |
    | created_at | 2025-08-18T17:19:51.478257Z |
    | updated_at | 2025-08-18T17:19:51.478258Z |

=== "JSON"

    ```json
    {
      "id": "evidence-c81c7241",
      "created_at": "2025-08-18T17:19:51.478257Z",
      "updated_at": "2025-08-18T17:19:51.478258Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "Evidence",
      "agent_context": null,
      "title": null,
      "abstract": null,
      "authors": [],
      "journal": null,
      "publication_year": null,
      "publication_date": null,
      "doi": null,
      "pmid": null,
      "url": null,
      "volume": null,
      "issue": null,
      "pages": null,
      "keywords": [],
      "evidence_level": null,
      "evidence_type": "research_paper",
      "citation": null,
      "content": null,
      "confidence_score": 0.8,
      "quality_score": 0.8,
      "vector_id": null,
      "provenance": {},
      "linked_resources": [],
      "tags": [],
      "review_status": "pending",
      "overall_reliability": 0.8
    }
    ```

=== "YAML"

    ```yaml
    id: evidence-c81c7241
    created_at: '2025-08-18T17:19:51.478257Z'
    updated_at: '2025-08-18T17:19:51.478258Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: Evidence
    agent_context: null
    title: null
    abstract: null
    authors: []
    journal: null
    publication_year: null
    publication_date: null
    doi: null
    pmid: null
    url: null
    volume: null
    issue: null
    pages: null
    keywords: []
    evidence_level: null
    evidence_type: research_paper
    citation: null
    content: null
    confidence_score: 0.8
    quality_score: 0.8
    vector_id: null
    provenance: {}
    linked_resources: []
    tags: []
    review_status: pending
    overall_reliability: 0.8
    
    ```

=== "Schema"

    #### Evidence Schema

    Literature-focused Evidence resource with FHIR-inspired fields.

    Backwards-compatibility: retains legacy fields `citation`, `content`,
    `evidence_type`, `confidence_score`, `quality_score`, `vector_id`, `provenance`,
    `linked_resources`, `tags`, `review_status`.

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Version of the resource |
    | identifier | list[str] | External identifiers for the resource (e.g., MRN, accession, system-specific IDs) (e.g., ['MRN:12345', 'local:abc-001']) |
    | language | typing.Optional[str] | Language (BCP-47, e.g., en, pt-BR) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['Evidence'] | None |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | title | typing.Optional[str] | Title of the cited artifact |
    | abstract | typing.Optional[str] | Abstract or summary of the artifact |
    | authors | typing.List[hacs_models.evidence.EvidenceAuthor] | List of authors |
    | journal | typing.Optional[hacs_models.evidence.PublicationVenue] | Publication venue |
    | publication_year | typing.Optional[int] | Year of publication |
    | publication_date | typing.Union[datetime.date, str, NoneType] | Date of publication (date or templated string) |
    | doi | typing.Optional[str] | Digital Object Identifier |
    | pmid | typing.Optional[str] | PubMed ID |
    | url | typing.Optional[str] | URL to the artifact |
    | volume | typing.Optional[str] | Journal volume |
    | issue | typing.Optional[str] | Journal issue |
    | pages | typing.Optional[str] | Page range |
    | keywords | typing.List[str] | Keywords/MeSH terms |
    | evidence_level | typing.Optional[hacs_models.evidence.EvidenceLevel] | Evidence level (e.g., GRADE) |
    | evidence_type | <enum 'EvidenceType'> | Type of evidence |
    | citation | typing.Optional[str] | Formatted citation string |
    | content | typing.Optional[str] | Legacy field for content or findings |
    | confidence_score | <class 'float'> | Confidence score (0.0-1.0) |
    | quality_score | <class 'float'> | Quality assessment score (0.0-1.0) |
    | vector_id | typing.Optional[str] | Vector embedding reference for RAG |
    | provenance | dict[str, typing.Any] | Provenance info (source, collected_by, etc.) |
    | linked_resources | list[str] | Linked HACS resources (ids) |
    | tags | list[str] | Categorization tags |
    | review_status | typing.Literal['pending', 'reviewed', 'approved', 'rejected'] | Review status |



---

## AI Agent Models

Memory systems, messaging, and agent communication

### AgentMessage

**Scope & Usage**

Runtime agent message with content, role, tool calls, and attachments for LLM workflows.

**Boundaries**

Not persisted as a clinical record. Use Document/Composition for clinical narratives.

**Relationships**

- Subtype of: MessageDefinition

**Tools**

- standardize_messages
- semantic_tool_loadout


**Example**

=== "Rendered"

    #### AgentMessage

    | Field | Value |
    |---|---|
    | resource_type | AgentMessage |
    | id | agentmessage-debb5be7 |
    | created_at | 2025-08-18T17:19:51.479659Z |
    | updated_at | 2025-08-18T17:19:51.479660Z |

=== "JSON"

    ```json
    {
      "id": "agentmessage-debb5be7",
      "created_at": "2025-08-18T17:19:51.479659Z",
      "updated_at": "2025-08-18T17:19:51.479660Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "AgentMessage",
      "agent_context": null,
      "content": "Sample AgentMessage content",
      "role": null,
      "message_type": null,
      "name": null,
      "additional_kwargs": {},
      "response_metadata": {},
      "tool_calls": [],
      "attachments": [],
      "url": null,
      "title": null,
      "status": null,
      "experimental": null,
      "publisher": null,
      "purpose": null,
      "description": null,
      "event_code": null,
      "event_system": null,
      "category": null
    }
    ```

=== "YAML"

    ```yaml
    id: agentmessage-debb5be7
    created_at: '2025-08-18T17:19:51.479659Z'
    updated_at: '2025-08-18T17:19:51.479660Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: AgentMessage
    agent_context: null
    content: Sample AgentMessage content
    role: null
    message_type: null
    name: null
    additional_kwargs: {}
    response_metadata: {}
    tool_calls: []
    attachments: []
    url: null
    title: null
    status: null
    experimental: null
    publisher: null
    purpose: null
    description: null
    event_code: null
    event_system: null
    category: null
    
    ```

=== "Schema"

    #### AgentMessage Schema

    Standard HACS message model for agent I/O and definitions.

    - Runtime fields: content, role, message_type, additional_kwargs,
      response_metadata, tool_calls, attachments
    - Definition fields (optional): url, version, name, title, status,
      publisher, description, purpose, event_code, event_system, category

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Version of the resource |
    | identifier | list[str] | External identifiers for the resource (e.g., MRN, accession, system-specific IDs) (e.g., ['MRN:12345', 'local:abc-001']) |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['AgentMessage'] | None |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | content | typing.Union[str, typing.List[typing.Union[str, typing.Dict[str, typing.Any]]]] | Message content as plain text or a list of blocks (strings or typed dicts). |
    | role | typing.Optional[hacs_models.types.MessageRole] | Message role (system, user, assistant, etc.) |
    | message_type | typing.Optional[hacs_models.types.MessageType] | Message content type (text, structured, etc.) |
    | name | typing.Optional[str] | Optional human-readable message label |
    | additional_kwargs | typing.Dict[str, typing.Any] | Provider-specific payload (tool calls, etc.) |
    | response_metadata | typing.Dict[str, typing.Any] | Response metadata (headers, logprobs, token counts, model) |
    | tool_calls | typing.List[typing.Dict[str, typing.Any]] | Tool/function calls encoded by the provider |
    | attachments | typing.List[typing.Dict[str, typing.Any]] | Attached files or references |
    | url | typing.Optional[str] | Canonical URL for message definition |
    | title | typing.Optional[str] | Title for the message definition |
    | status | typing.Optional[str] | draft | active | retired | unknown |
    | experimental | typing.Optional[bool] | None |
    | publisher | typing.Optional[str] | None |
    | purpose | typing.Optional[str] | None |
    | description | typing.Optional[str] | None |
    | event_code | typing.Optional[str] | Event code identifying the message trigger |
    | event_system | typing.Optional[str] | Code system for the event code |
    | category | typing.Optional[str] | consequence | currency | notification |



### MessageDefinition

**Scope & Usage**

Standardized agent message envelope and definition for inter-agent/tool communication.

**Boundaries**

Not a clinical document; represents transport of instructions, content, and tool calls.

**Relationships**

- Referenced by: AgentMessage as runtime specialization

**Tools**

- standardize_messages
- log_llm_request


**Example**

=== "Rendered"

    #### MessageDefinition

    | Field | Value |
    |---|---|
    | resource_type | MessageDefinition |
    | id | messagedefinition-ca395079 |
    | created_at | 2025-08-18T17:19:51.480912Z |
    | updated_at | 2025-08-18T17:19:51.480913Z |

=== "JSON"

    ```json
    {
      "id": "messagedefinition-ca395079",
      "created_at": "2025-08-18T17:19:51.480912Z",
      "updated_at": "2025-08-18T17:19:51.480913Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "MessageDefinition",
      "agent_context": null,
      "content": "Sample MessageDefinition content",
      "role": null,
      "message_type": null,
      "name": null,
      "additional_kwargs": {},
      "response_metadata": {},
      "tool_calls": [],
      "attachments": [],
      "url": null,
      "title": null,
      "status": null,
      "experimental": null,
      "publisher": null,
      "purpose": null,
      "description": null,
      "event_code": null,
      "event_system": null,
      "category": null
    }
    ```

=== "YAML"

    ```yaml
    id: messagedefinition-ca395079
    created_at: '2025-08-18T17:19:51.480912Z'
    updated_at: '2025-08-18T17:19:51.480913Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: MessageDefinition
    agent_context: null
    content: Sample MessageDefinition content
    role: null
    message_type: null
    name: null
    additional_kwargs: {}
    response_metadata: {}
    tool_calls: []
    attachments: []
    url: null
    title: null
    status: null
    experimental: null
    publisher: null
    purpose: null
    description: null
    event_code: null
    event_system: null
    category: null
    
    ```

=== "Schema"

    #### MessageDefinition Schema

    Standard HACS message model for agent I/O and definitions.

    - Runtime fields: content, role, message_type, additional_kwargs,
      response_metadata, tool_calls, attachments
    - Definition fields (optional): url, version, name, title, status,
      publisher, description, purpose, event_code, event_system, category

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Version of the resource |
    | identifier | list[str] | External identifiers for the resource (e.g., MRN, accession, system-specific IDs) (e.g., ['MRN:12345', 'local:abc-001']) |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['MessageDefinition'] | None |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | content | typing.Union[str, typing.List[typing.Union[str, typing.Dict[str, typing.Any]]]] | Message content as plain text or a list of blocks (strings or typed dicts). |
    | role | typing.Optional[hacs_models.types.MessageRole] | Message role (system, user, assistant, etc.) |
    | message_type | typing.Optional[hacs_models.types.MessageType] | Message content type (text, structured, etc.) |
    | name | typing.Optional[str] | Optional human-readable message label |
    | additional_kwargs | typing.Dict[str, typing.Any] | Provider-specific payload (tool calls, etc.) |
    | response_metadata | typing.Dict[str, typing.Any] | Response metadata (headers, logprobs, token counts, model) |
    | tool_calls | typing.List[typing.Dict[str, typing.Any]] | Tool/function calls encoded by the provider |
    | attachments | typing.List[typing.Dict[str, typing.Any]] | Attached files or references |
    | url | typing.Optional[str] | Canonical URL for message definition |
    | title | typing.Optional[str] | Title for the message definition |
    | status | typing.Optional[str] | draft | active | retired | unknown |
    | experimental | typing.Optional[bool] | None |
    | publisher | typing.Optional[str] | None |
    | purpose | typing.Optional[str] | None |
    | description | typing.Optional[str] | None |
    | event_code | typing.Optional[str] | Event code identifying the message trigger |
    | event_system | typing.Optional[str] | Code system for the event code |
    | category | typing.Optional[str] | consequence | currency | notification |



### MemoryBlock

**Scope & Usage**

Agent memory item (episodic, semantic, working) for context engineering.

**Boundaries**

Not a clinical record; may link to clinical resources as context.

**Relationships**

- Referenced by: Agents; Indexed for retrieval

**Tools**

- store_memory
- retrieve_memories


**Example**

=== "Rendered"

    #### MemoryBlock

    | Field | Value |
    |---|---|
    | resource_type | MemoryBlock |
    | id | memoryblock-f21657d1 |
    | created_at | 2025-08-18T17:19:51.481956Z |
    | updated_at | 2025-08-18T17:19:51.481956Z |

=== "JSON"

    ```json
    {
      "id": "memoryblock-f21657d1",
      "created_at": "2025-08-18T17:19:51.481956Z",
      "updated_at": "2025-08-18T17:19:51.481956Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "MemoryBlock",
      "agent_context": null,
      "memory_type": "semantic",
      "content": "Sample MemoryBlock content",
      "summary": null,
      "importance_score": 0.5,
      "confidence_score": 0.8,
      "context_metadata": {},
      "related_memories": [],
      "tags": [],
      "access_count": 0,
      "vector_id": null,
      "last_accessed": null,
      "last_summarized": null
    }
    ```

=== "YAML"

    ```yaml
    id: memoryblock-f21657d1
    created_at: '2025-08-18T17:19:51.481956Z'
    updated_at: '2025-08-18T17:19:51.481956Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: MemoryBlock
    agent_context: null
    memory_type: semantic
    content: Sample MemoryBlock content
    summary: null
    importance_score: 0.5
    confidence_score: 0.8
    context_metadata: {}
    related_memories: []
    tags: []
    access_count: 0
    vector_id: null
    last_accessed: null
    last_summarized: null
    
    ```

=== "Schema"

    #### MemoryBlock Schema

    Base memory block for AI agent cognition.

    Represents a unit of memory that can be stored, retrieved, and processed
    by AI agents in healthcare workflows. Supports multiple memory types
    based on cognitive science models.

    Features:
        - Typed memory categorization
        - Importance and confidence scoring
        - Context metadata for healthcare workflows
        - Memory relationship tracking
        - Tag-based organization

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Version of the resource |
    | identifier | list[str] | External identifiers for the resource (e.g., MRN, accession, system-specific IDs) (e.g., ['MRN:12345', 'local:abc-001']) |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['MemoryBlock'] | Resource type identifier |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | memory_type | typing.Literal['episodic', 'procedural', 'executive', 'semantic', 'working'] | Type of memory this block represents (e.g., episodic) |
    | content | <class 'str'> | The actual memory content or information (e.g., Patient John Doe expressed concern about chest pain during consultation) |
    | summary | str | None | Compressed summary of the memory content (e.g., Patient chest pain concern) |
    | importance_score | <class 'float'> | Importance score from 0.0 to 1.0 for memory prioritization |
    | confidence_score | <class 'float'> | Confidence in memory accuracy from 0.0 to 1.0 |
    | context_metadata | dict[str, typing.Any] | Structured context metadata (patient_id, encounter_id, etc.) (e.g., {'patient_id': 'patient-123', 'encounter_id': 'encounter-456'}) |
    | related_memories | list[str] | IDs of related memory blocks |
    | tags | list[str] | Tags for categorizing and searching memories (e.g., ['patient_interaction', 'vital_signs', 'diagnosis']) |
    | access_count | <class 'int'> | Number of times this memory has been accessed |
    | vector_id | str | None | Vector embedding ID for semantic search |
    | last_accessed | datetime.datetime | None | Timestamp of last access |
    | last_summarized | datetime.datetime | None | Timestamp when the summary was last updated |



### EpisodicMemory

**Scope & Usage**

Time-stamped event memory used by agents to recall episodes.

**Boundaries**

Use SemanticMemory for facts/concepts; WorkingMemory for short-lived context.

**Relationships**

- Subtype of: MemoryBlock

**Tools**

- store_memory
- retrieve_memories


**Example**

=== "Rendered"

    #### MemoryBlock

    | Field | Value |
    |---|---|
    | resource_type | MemoryBlock |
    | id | memoryblock-0d2b424e |
    | created_at | 2025-08-18T17:19:51.482970Z |
    | updated_at | 2025-08-18T17:19:51.482970Z |

=== "JSON"

    ```json
    {
      "id": "memoryblock-0d2b424e",
      "created_at": "2025-08-18T17:19:51.482970Z",
      "updated_at": "2025-08-18T17:19:51.482970Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "MemoryBlock",
      "agent_context": null,
      "memory_type": "episodic",
      "content": "Sample EpisodicMemory content",
      "summary": null,
      "importance_score": 0.5,
      "confidence_score": 0.8,
      "context_metadata": {},
      "related_memories": [],
      "tags": [],
      "access_count": 0,
      "vector_id": null,
      "last_accessed": null,
      "last_summarized": null,
      "event_time": null,
      "location": null,
      "participants": []
    }
    ```

=== "YAML"

    ```yaml
    id: memoryblock-0d2b424e
    created_at: '2025-08-18T17:19:51.482970Z'
    updated_at: '2025-08-18T17:19:51.482970Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: MemoryBlock
    agent_context: null
    memory_type: episodic
    content: Sample EpisodicMemory content
    summary: null
    importance_score: 0.5
    confidence_score: 0.8
    context_metadata: {}
    related_memories: []
    tags: []
    access_count: 0
    vector_id: null
    last_accessed: null
    last_summarized: null
    event_time: null
    location: null
    participants: []
    
    ```

=== "Schema"

    #### EpisodicMemory Schema

    Episodic memory for specific events and experiences.

    Stores memories of specific events, interactions, and experiences
    that occurred at particular times and places.

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Version of the resource |
    | identifier | list[str] | External identifiers for the resource (e.g., MRN, accession, system-specific IDs) (e.g., ['MRN:12345', 'local:abc-001']) |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['MemoryBlock'] | Resource type identifier |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | memory_type | typing.Literal['episodic'] | Episodic memory type |
    | content | <class 'str'> | The actual memory content or information (e.g., Patient John Doe expressed concern about chest pain during consultation) |
    | summary | str | None | Compressed summary of the memory content (e.g., Patient chest pain concern) |
    | importance_score | <class 'float'> | Importance score from 0.0 to 1.0 for memory prioritization |
    | confidence_score | <class 'float'> | Confidence in memory accuracy from 0.0 to 1.0 |
    | context_metadata | dict[str, typing.Any] | Structured context metadata (patient_id, encounter_id, etc.) (e.g., {'patient_id': 'patient-123', 'encounter_id': 'encounter-456'}) |
    | related_memories | list[str] | IDs of related memory blocks |
    | tags | list[str] | Tags for categorizing and searching memories (e.g., ['patient_interaction', 'vital_signs', 'diagnosis']) |
    | access_count | <class 'int'> | Number of times this memory has been accessed |
    | vector_id | str | None | Vector embedding ID for semantic search |
    | last_accessed | datetime.datetime | None | Timestamp of last access |
    | last_summarized | datetime.datetime | None | Timestamp when the summary was last updated |
    | event_time | datetime.datetime | None | When the remembered event occurred |
    | location | str | None | Where the remembered event occurred (e.g., Emergency Room) |
    | participants | list[str] | Who was involved in the remembered event (e.g., ['Patient/patient-123', 'Practitioner/dr-smith']) |



### SemanticMemory

**Scope & Usage**

Long-lived knowledge/facts to guide agent behavior and preferences.

**Boundaries**

Not clinical truth; may be derived and should be auditable.

**Relationships**

- Subtype of: MemoryBlock

**Tools**

- store_memory
- retrieve_memories


**Example**

=== "Rendered"

    #### MemoryBlock

    | Field | Value |
    |---|---|
    | resource_type | MemoryBlock |
    | id | memoryblock-a7e57c54 |
    | created_at | 2025-08-18T17:19:51.484115Z |
    | updated_at | 2025-08-18T17:19:51.484116Z |

=== "JSON"

    ```json
    {
      "id": "memoryblock-a7e57c54",
      "created_at": "2025-08-18T17:19:51.484115Z",
      "updated_at": "2025-08-18T17:19:51.484116Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "MemoryBlock",
      "agent_context": null,
      "memory_type": "semantic",
      "content": "Sample SemanticMemory content",
      "summary": null,
      "importance_score": 0.5,
      "confidence_score": 0.8,
      "context_metadata": {},
      "related_memories": [],
      "tags": [],
      "access_count": 0,
      "vector_id": null,
      "last_accessed": null,
      "last_summarized": null,
      "knowledge_domain": null,
      "source": null,
      "evidence_level": null
    }
    ```

=== "YAML"

    ```yaml
    id: memoryblock-a7e57c54
    created_at: '2025-08-18T17:19:51.484115Z'
    updated_at: '2025-08-18T17:19:51.484116Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: MemoryBlock
    agent_context: null
    memory_type: semantic
    content: Sample SemanticMemory content
    summary: null
    importance_score: 0.5
    confidence_score: 0.8
    context_metadata: {}
    related_memories: []
    tags: []
    access_count: 0
    vector_id: null
    last_accessed: null
    last_summarized: null
    knowledge_domain: null
    source: null
    evidence_level: null
    
    ```

=== "Schema"

    #### SemanticMemory Schema

    Semantic memory for general knowledge and facts.

    Stores factual information, general knowledge, and learned concepts
    that are not tied to specific experiences.

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Version of the resource |
    | identifier | list[str] | External identifiers for the resource (e.g., MRN, accession, system-specific IDs) (e.g., ['MRN:12345', 'local:abc-001']) |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['MemoryBlock'] | Resource type identifier |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | memory_type | typing.Literal['semantic'] | Semantic memory type |
    | content | <class 'str'> | The actual memory content or information (e.g., Patient John Doe expressed concern about chest pain during consultation) |
    | summary | str | None | Compressed summary of the memory content (e.g., Patient chest pain concern) |
    | importance_score | <class 'float'> | Importance score from 0.0 to 1.0 for memory prioritization |
    | confidence_score | <class 'float'> | Confidence in memory accuracy from 0.0 to 1.0 |
    | context_metadata | dict[str, typing.Any] | Structured context metadata (patient_id, encounter_id, etc.) (e.g., {'patient_id': 'patient-123', 'encounter_id': 'encounter-456'}) |
    | related_memories | list[str] | IDs of related memory blocks |
    | tags | list[str] | Tags for categorizing and searching memories (e.g., ['patient_interaction', 'vital_signs', 'diagnosis']) |
    | access_count | <class 'int'> | Number of times this memory has been accessed |
    | vector_id | str | None | Vector embedding ID for semantic search |
    | last_accessed | datetime.datetime | None | Timestamp of last access |
    | last_summarized | datetime.datetime | None | Timestamp when the summary was last updated |
    | knowledge_domain | str | None | Domain or field this knowledge belongs to (e.g., cardiology) |
    | source | str | None | Source of this knowledge (e.g., Medical textbook) |
    | evidence_level | str | None | Level of evidence supporting this knowledge (e.g., high) |



### WorkingMemory

**Scope & Usage**

Short-term, task-scoped memory for in-flight agent steps.

**Boundaries**

Should be pruned/expired to avoid context poisoning.

**Relationships**

- Subtype of: MemoryBlock

**Tools**

- store_memory
- retrieve_memories
- prune_state


**Example**

=== "Rendered"

    #### MemoryBlock

    | Field | Value |
    |---|---|
    | resource_type | MemoryBlock |
    | id | memoryblock-ee3c884c |
    | created_at | 2025-08-18T17:19:51.485183Z |
    | updated_at | 2025-08-18T17:19:51.485184Z |

=== "JSON"

    ```json
    {
      "id": "memoryblock-ee3c884c",
      "created_at": "2025-08-18T17:19:51.485183Z",
      "updated_at": "2025-08-18T17:19:51.485184Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "MemoryBlock",
      "agent_context": null,
      "memory_type": "working",
      "content": "Sample WorkingMemory content",
      "summary": null,
      "importance_score": 0.5,
      "confidence_score": 0.8,
      "context_metadata": {},
      "related_memories": [],
      "tags": [],
      "access_count": 0,
      "vector_id": null,
      "last_accessed": null,
      "last_summarized": null,
      "task_context": null,
      "processing_stage": null,
      "ttl_seconds": null
    }
    ```

=== "YAML"

    ```yaml
    id: memoryblock-ee3c884c
    created_at: '2025-08-18T17:19:51.485183Z'
    updated_at: '2025-08-18T17:19:51.485184Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: MemoryBlock
    agent_context: null
    memory_type: working
    content: Sample WorkingMemory content
    summary: null
    importance_score: 0.5
    confidence_score: 0.8
    context_metadata: {}
    related_memories: []
    tags: []
    access_count: 0
    vector_id: null
    last_accessed: null
    last_summarized: null
    task_context: null
    processing_stage: null
    ttl_seconds: null
    
    ```

=== "Schema"

    #### WorkingMemory Schema

    Working memory for temporary information processing.

    Stores information that is actively being processed or manipulated
    in current tasks and workflows.

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Version of the resource |
    | identifier | list[str] | External identifiers for the resource (e.g., MRN, accession, system-specific IDs) (e.g., ['MRN:12345', 'local:abc-001']) |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['MemoryBlock'] | Resource type identifier |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | memory_type | typing.Literal['working'] | Working memory type |
    | content | <class 'str'> | The actual memory content or information (e.g., Patient John Doe expressed concern about chest pain during consultation) |
    | summary | str | None | Compressed summary of the memory content (e.g., Patient chest pain concern) |
    | importance_score | <class 'float'> | Importance score from 0.0 to 1.0 for memory prioritization |
    | confidence_score | <class 'float'> | Confidence in memory accuracy from 0.0 to 1.0 |
    | context_metadata | dict[str, typing.Any] | Structured context metadata (patient_id, encounter_id, etc.) (e.g., {'patient_id': 'patient-123', 'encounter_id': 'encounter-456'}) |
    | related_memories | list[str] | IDs of related memory blocks |
    | tags | list[str] | Tags for categorizing and searching memories (e.g., ['patient_interaction', 'vital_signs', 'diagnosis']) |
    | access_count | <class 'int'> | Number of times this memory has been accessed |
    | vector_id | str | None | Vector embedding ID for semantic search |
    | last_accessed | datetime.datetime | None | Timestamp of last access |
    | last_summarized | datetime.datetime | None | Timestamp when the summary was last updated |
    | task_context | str | None | Current task context for this working memory (e.g., patient_assessment) |
    | processing_stage | str | None | Current processing stage (e.g., input) |
    | ttl_seconds | int | None | Time-to-live in seconds for this working memory (e.g., 300) |



---

## Workflow & Events

Process definitions and event tracking

### WorkflowDefinition

**Scope & Usage**

HACS workflow and orchestration definition, complementing FHIR PlanDefinition.

**Boundaries**

Not a FHIR resource; bridges AI agent workflows with clinical artifacts.

**Relationships**

- May reference: PlanDefinition, ActivityDefinition


**Example**

=== "Rendered"

    #### WorkflowDefinition

    | Field | Value |
    |---|---|
    | resource_type | WorkflowDefinition |
    | id | workflowdefinition-4bab59cd |
    | status | draft |
    | created_at | 2025-08-18T17:19:51.486207Z |
    | updated_at | 2025-08-18T17:19:51.486208Z |

=== "JSON"

    ```json
    {
      "id": "workflowdefinition-4bab59cd",
      "created_at": "2025-08-18T17:19:51.486207Z",
      "updated_at": "2025-08-18T17:19:51.486208Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "WorkflowDefinition",
      "agent_context": null,
      "name": null,
      "title": null,
      "status": "draft",
      "description": null,
      "type": null,
      "goal": [],
      "action": []
    }
    ```

=== "YAML"

    ```yaml
    id: workflowdefinition-4bab59cd
    created_at: '2025-08-18T17:19:51.486207Z'
    updated_at: '2025-08-18T17:19:51.486208Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: WorkflowDefinition
    agent_context: null
    name: null
    title: null
    status: draft
    description: null
    type: null
    goal: []
    action: []
    
    ```

=== "Schema"

    #### WorkflowDefinition Schema

    Foundation class for all HACS healthcare resources.

    Provides essential functionality for healthcare data models including
    automatic ID generation, timestamp management, and type-safe operations.

    This class follows FHIR R4/R5 base resource patterns while optimizing
    for AI agent communication and modern Python development practices.

    **Protocol Compliance:**
        Implements: Identifiable, Timestamped, Versioned, Serializable, Validatable

        This ensures all HACS resources follow standardized contracts for:
        - Unique identification (id field)
        - Audit trails (created_at, updated_at)
        - Version tracking (version field)
        - Data interchange (to_dict, from_dict)
        - Validation (validate, is_valid)

    Features:
        - Auto-generated UUIDs if ID not provided
        - Automatic timestamp management
        - Type-safe field access and validation
        - JSON Schema generation with examples
        - Subset model creation for specific use cases
        - Performance optimized serialization
        - Protocol-based interface contracts

    Example:
        >>> class MyResource(BaseResource):
        ...     name: str
        ...     value: int = 0
        >>>
        >>> resource = MyResource(resource_type="MyResource", name="test")
        >>> print(resource.id)  # Auto-generated: myresource-a1b2c3d4
        >>> print(resource.created_at)  # Auto-set to current time
        >>> isinstance(resource, Identifiable)  # True - protocol compliance

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Version of the resource |
    | identifier | list[str] | External identifiers for the resource (e.g., MRN, accession, system-specific IDs) (e.g., ['MRN:12345', 'local:abc-001']) |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['WorkflowDefinition'] | None |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | name | typing.Optional[str] | None |
    | title | typing.Optional[str] | None |
    | status | <enum 'WorkflowStatus'> | None |
    | description | typing.Optional[str] | None |
    | type | typing.Optional[str] | None |
    | goal | typing.List[typing.Dict[str, typing.Any]] | None |
    | action | typing.List[typing.Dict[str, typing.Any]] | None |



### Event

**Scope & Usage**

Generic event aligned with FHIR's Event pattern for representing occurrences involving a subject (e.g., actions performed, measurements taken, events recorded). Provides uniform fields for agents to track status, timing, performers, and context where a specialized resource is unnecessary or not yet modeled.

**Boundaries**

Do not use when a more specific resource exists (e.g., Procedure, MedicationAdministration, DiagnosticReport). Event is intended as a lightweight, generic wrapper to enable workflows and logging when specificity is not required.

**Relationships**

- References: Patient via subject, Encounter via encounter, related orders via basedOn
- Links: partOf to larger events, instantiatesCanonical to protocols

**References**

- Patient.subject
- Encounter.encounter
- ServiceRequest in basedOn

**Tools**

- create_event_tool
- update_event_status_tool
- add_event_performer_tool
- schedule_event_tool
- summarize_event_tool


**Example**

=== "Rendered"

    #### Event

    | Field | Value |
    |---|---|
    | resource_type | Event |
    | id | event-b5a78813 |
    | status | in-progress |
    | performer | [] |
    | based_on | [] |
    | created_at | 2025-08-18T17:19:51.490625Z |
    | updated_at | 2025-08-18T17:19:51.490625Z |

=== "JSON"

    ```json
    {
      "id": "event-b5a78813",
      "created_at": "2025-08-18T17:19:51.490625Z",
      "updated_at": "2025-08-18T17:19:51.490625Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "Event",
      "agent_context": null,
      "status": "in-progress",
      "text": null,
      "contained": null,
      "extension": null,
      "modifier_extension": null,
      "instantiates_canonical": [],
      "instantiates_uri": [],
      "based_on": [],
      "part_of": [],
      "status_reason": null,
      "category": null,
      "code": null,
      "subject": null,
      "focus": null,
      "encounter": null,
      "occurrence_date_time": null,
      "occurrence_start": null,
      "occurrence_end": null,
      "recorded": null,
      "performer": [],
      "reason_code": [],
      "reason_reference": [],
      "location": null,
      "supporting_info": [],
      "note": []
    }
    ```

=== "YAML"

    ```yaml
    id: event-b5a78813
    created_at: '2025-08-18T17:19:51.490625Z'
    updated_at: '2025-08-18T17:19:51.490625Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: Event
    agent_context: null
    status: in-progress
    text: null
    contained: null
    extension: null
    modifier_extension: null
    instantiates_canonical: []
    instantiates_uri: []
    based_on: []
    part_of: []
    status_reason: null
    category: null
    code: null
    subject: null
    focus: null
    encounter: null
    occurrence_date_time: null
    occurrence_start: null
    occurrence_end: null
    recorded: null
    performer: []
    reason_code: []
    reason_reference: []
    location: null
    supporting_info: []
    note: []
    
    ```

=== "Schema"

    #### Event Schema

    Event resource representing an occurrence in time related to a subject.

    This is a generic HACS resource inspired by the FHIR Event pattern and intended
    for agent workflows that need a lightweight, uniform representation of events.

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Version of the resource |
    | identifier | list[str] | External identifiers for the resource (e.g., MRN, accession, system-specific IDs) (e.g., ['MRN:12345', 'local:abc-001']) |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['Event'] | Resource type identifier |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | status | <class 'str'> | Status of the event |
    | text | str | None | Human-readable summary of the resource content (e.g., Patient John Doe, 45 years old) |
    | contained | list[hacs_models.base_resource.BaseResource] | None | Resources contained within this resource |
    | extension | dict[str, typing.Any] | None | Additional content defined by implementations (e.g., {'url': 'custom-field', 'valueString': 'custom-value'}) |
    | modifier_extension | dict[str, typing.Any] | None | Extensions that cannot be ignored (e.g., {'url': 'critical-field', 'valueBoolean': True}) |
    | instantiates_canonical | typing.List[str] | Instantiates canonical definitions |
    | instantiates_uri | typing.List[str] | Instantiates external definitions by URI |
    | based_on | typing.List[str] | Fulfills orders/proposals (ServiceRequest, etc.) |
    | part_of | typing.List[str] | Part of larger event |
    | status_reason | typing.Optional[hacs_models.observation.CodeableConcept] | Reason for current status |
    | category | typing.Optional[hacs_models.observation.CodeableConcept] | High-level categorization of the event |
    | code | typing.Optional[hacs_models.observation.CodeableConcept] | What the event is |
    | subject | typing.Optional[str] | Who/what the event is about (e.g., Patient/123) |
    | focus | typing.Optional[str] | The focus of the event if different from subject |
    | encounter | typing.Optional[str] | Encounter during which the event occurred |
    | occurrence_date_time | typing.Optional[str] | When the event occurred |
    | occurrence_start | typing.Optional[str] | Start time if an interval |
    | occurrence_end | typing.Optional[str] | End time if an interval |
    | recorded | typing.Optional[str] | When this record was created/recorded |
    | performer | typing.List[hacs_models.event.EventPerformer] | Who performed the event |
    | reason_code | typing.List[hacs_models.observation.CodeableConcept] | Why the event happened |
    | reason_reference | typing.List[str] | References to justifications for event |
    | location | typing.Optional[str] | Where the event occurred |
    | supporting_info | typing.List[str] | Additional supporting information |
    | note | typing.List[str] | Comments about the event |



### GraphDefinition

**Scope & Usage**

FHIR-aligned graph of resource relationships for traversal and validation.

**Boundaries**

Describes structure; not data.

**Relationships**

- Links: source → target by path/type


**Example**

=== "Rendered"

    #### GraphDefinition

    | Field | Value |
    |---|---|
    | resource_type | GraphDefinition |
    | id | graphdefinition-a6499317 |
    | status | active |
    | name | Sample GraphDefinition |
    | created_at | 2025-08-18T17:19:51.494187Z |
    | updated_at | 2025-08-18T17:19:51.494188Z |

=== "JSON"

    ```json
    {
      "id": "graphdefinition-a6499317",
      "created_at": "2025-08-18T17:19:51.494187Z",
      "updated_at": "2025-08-18T17:19:51.494188Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "GraphDefinition",
      "agent_context": null,
      "status": "active",
      "text": null,
      "contained": null,
      "extension": null,
      "modifier_extension": null,
      "name": "Sample GraphDefinition",
      "start": "Patient",
      "description": null,
      "link": []
    }
    ```

=== "YAML"

    ```yaml
    id: graphdefinition-a6499317
    created_at: '2025-08-18T17:19:51.494187Z'
    updated_at: '2025-08-18T17:19:51.494188Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: GraphDefinition
    agent_context: null
    status: active
    text: null
    contained: null
    extension: null
    modifier_extension: null
    name: Sample GraphDefinition
    start: Patient
    description: null
    link: []
    
    ```

=== "Schema"

    #### GraphDefinition Schema

    Minimal GraphDefinition aligned with FHIR to describe traversals between resources.
    This enables declaring how to navigate between linked records.

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | <class 'str'> | Version of the resource |
    | identifier | list[str] | External identifiers for the resource (e.g., MRN, accession, system-specific IDs) (e.g., ['MRN:12345', 'local:abc-001']) |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['GraphDefinition'] | None |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | status | <class 'str'> | Status of the graph definition |
    | text | str | None | Human-readable summary of the resource content (e.g., Patient John Doe, 45 years old) |
    | contained | list[hacs_models.base_resource.BaseResource] | None | Resources contained within this resource |
    | extension | dict[str, typing.Any] | None | Additional content defined by implementations (e.g., {'url': 'custom-field', 'valueString': 'custom-value'}) |
    | modifier_extension | dict[str, typing.Any] | None | Extensions that cannot be ignored (e.g., {'url': 'critical-field', 'valueBoolean': True}) |
    | name | <class 'str'> | Human-readable name |
    | start | <class 'str'> | Type of the starting resource (e.g., 'Patient') |
    | description | typing.Optional[str] | Markdown description |
    | link | typing.List[hacs_models.graph_definition.GraphDefinitionLink] | Links this graph makes rules about |



---

## Terminology & Standards

Code systems, value sets, and standardized vocabularies

### TerminologySystem

**Scope & Usage**

Represents a terminology code system (e.g., SNOMED CT, LOINC, RxNorm, UMLS) used to encode clinical data.

**Boundaries**

Does not include the full content of a code system; use external services for term lookup/expansion.

**Relationships**

- Referenced by: ValueSet.includeSystems, TerminologyConcept.system_uri
- Supports: coding in clinical resources (Observation, Condition, Medication, etc.)

**References**

- ValueSet.include.system_uri
- TerminologyConcept.system_uri

**Tools**

- get_possible_codes
- expand_value_set


**Example**

=== "Rendered"

    #### TerminologySystem

    | Field | Value |
    |---|---|
    | resource_type | TerminologySystem |
    | id | terminologysystem-1422a90e |
    | status | active |
    | name | Sample TerminologySystem |
    | created_at | 2025-08-18T17:19:51.495686Z |
    | updated_at | 2025-08-18T17:19:51.495687Z |

=== "JSON"

    ```json
    {
      "id": "terminologysystem-1422a90e",
      "created_at": "2025-08-18T17:19:51.495686Z",
      "updated_at": "2025-08-18T17:19:51.495687Z",
      "version": null,
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "TerminologySystem",
      "agent_context": null,
      "status": "active",
      "text": null,
      "contained": null,
      "extension": null,
      "modifier_extension": null,
      "name": "Sample TerminologySystem",
      "system_uri": "http://example.org/terminologysystem",
      "publisher": null,
      "description": null,
      "jurisdiction": null,
      "tooling": null
    }
    ```

=== "YAML"

    ```yaml
    id: terminologysystem-1422a90e
    created_at: '2025-08-18T17:19:51.495686Z'
    updated_at: '2025-08-18T17:19:51.495687Z'
    version: null
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: TerminologySystem
    agent_context: null
    status: active
    text: null
    contained: null
    extension: null
    modifier_extension: null
    name: Sample TerminologySystem
    system_uri: http://example.org/terminologysystem
    publisher: null
    description: null
    jurisdiction: null
    tooling: null
    
    ```

=== "Schema"

    #### TerminologySystem Schema

    Represents a terminology code system (e.g., SNOMED CT, LOINC, RxNorm, UMLS).

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | typing.Optional[str] | System version |
    | identifier | list[str] | External identifiers for the resource (e.g., MRN, accession, system-specific IDs) (e.g., ['MRN:12345', 'local:abc-001']) |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['TerminologySystem'] | None |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | status | <class 'str'> | Current status of the resource (e.g., active) |
    | text | str | None | Human-readable summary of the resource content (e.g., Patient John Doe, 45 years old) |
    | contained | list[hacs_models.base_resource.BaseResource] | None | Resources contained within this resource |
    | extension | dict[str, typing.Any] | None | Additional content defined by implementations (e.g., {'url': 'custom-field', 'valueString': 'custom-value'}) |
    | modifier_extension | dict[str, typing.Any] | None | Extensions that cannot be ignored (e.g., {'url': 'critical-field', 'valueBoolean': True}) |
    | name | <class 'str'> | Human-friendly name of the terminology system |
    | system_uri | <class 'str'> | Canonical URI identifying the code system |
    | publisher | typing.Optional[str] | Organization publishing the system |
    | description | typing.Optional[str] | Short description of the system |
    | jurisdiction | typing.Optional[str] | Jurisdiction(s) for use |
    | tooling | typing.Optional[str] | Preferred tooling/integration (e.g., umls) |



### TerminologyConcept

**Scope & Usage**

A single coded concept from a terminology system providing code, display, definition, and relations.

**Boundaries**

Not a clinical record; acts as a coding primitive used inside CodeableConcept and ValueSets.

**Relationships**

- References: TerminologySystem via system_uri
- Referenced by: ValueSet.expanded_concepts

**References**

- ValueSet.expanded_concepts

**Tools**

- get_possible_codes


**Example**

=== "Rendered"

    #### TerminologyConcept

    | Field | Value |
    |---|---|
    | resource_type | TerminologyConcept |

=== "JSON"

    ```json
    {
      "resource_type": "TerminologyConcept"
    }
    ```

=== "YAML"

    ```yaml
    resource_type: TerminologyConcept
    
    ```

=== "Schema"

    _No schema available_


### ValueSet

**Scope & Usage**

A curated set of concepts drawn from one or more terminology systems for use in coding and validation.

**Boundaries**

Does not define a code system; use TerminologySystem for system metadata. Expansion may be partial.

**Relationships**

- Includes: TerminologySystem URIs and TerminologyConcepts
- Used by: validation and UI pick-lists

**References**

- TerminologySystem
- TerminologyConcept

**Tools**

- expand_value_set
- validate_code_in_valueset


**Example**

=== "Rendered"

    #### ValueSet

    | Field | Value |
    |---|---|
    | resource_type | ValueSet |
    | id | valueset-85d76621 |
    | status | active |
    | created_at | 2025-08-18T17:19:51.499691Z |
    | updated_at | 2025-08-18T17:19:51.499691Z |

=== "JSON"

    ```json
    {
      "id": "valueset-85d76621",
      "created_at": "2025-08-18T17:19:51.499691Z",
      "updated_at": "2025-08-18T17:19:51.499691Z",
      "version": null,
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "ValueSet",
      "agent_context": null,
      "status": "active",
      "text": null,
      "contained": null,
      "extension": null,
      "modifier_extension": null,
      "url": null,
      "name": null,
      "description": null,
      "include_systems": [],
      "include_concepts": [],
      "expansion_timestamp": null,
      "expanded_concepts": []
    }
    ```

=== "YAML"

    ```yaml
    id: valueset-85d76621
    created_at: '2025-08-18T17:19:51.499691Z'
    updated_at: '2025-08-18T17:19:51.499691Z'
    version: null
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: ValueSet
    agent_context: null
    status: active
    text: null
    contained: null
    extension: null
    modifier_extension: null
    url: null
    name: null
    description: null
    include_systems: []
    include_concepts: []
    expansion_timestamp: null
    expanded_concepts: []
    
    ```

=== "Schema"

    #### ValueSet Schema

    A set of concepts drawn from one or more code systems.

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | typing.Optional[str] | Business version |
    | identifier | list[str] | External identifiers for the resource (e.g., MRN, accession, system-specific IDs) (e.g., ['MRN:12345', 'local:abc-001']) |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['ValueSet'] | None |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | status | <class 'str'> | Current status of the resource (e.g., active) |
    | text | str | None | Human-readable summary of the resource content (e.g., Patient John Doe, 45 years old) |
    | contained | list[hacs_models.base_resource.BaseResource] | None | Resources contained within this resource |
    | extension | dict[str, typing.Any] | None | Additional content defined by implementations (e.g., {'url': 'custom-field', 'valueString': 'custom-value'}) |
    | modifier_extension | dict[str, typing.Any] | None | Extensions that cannot be ignored (e.g., {'url': 'critical-field', 'valueBoolean': True}) |
    | url | typing.Optional[str] | Canonical URL for this value set |
    | name | typing.Optional[str] | Name for this value set |
    | description | typing.Optional[str] | What this value set is for |
    | include_systems | typing.List[typing.Dict[str, str]] | List of {system_uri, version?} to include |
    | include_concepts | typing.List[hacs_models.terminology.TerminologyConcept] | Inline explicit concepts to include |
    | expansion_timestamp | typing.Optional[str] | When expansion was generated |
    | expanded_concepts | typing.List[hacs_models.terminology.TerminologyConcept] | Expanded concepts for fast agent lookups |



### ConceptMap

**Scope & Usage**

DomainResource extends BaseResource with FHIR R4-compliant fields for clinical and healthcare domain resources. Adds status tracking (active/inactive/draft), human-readable text narratives for clinical review, contained resource support, and extension mechanisms for additional healthcare data. All clinical HACS resources (Patient, Observation, Procedure, Condition, etc.) inherit from DomainResource to gain these healthcare-specific capabilities. Essential for LLM agents processing clinical data as it provides standardized status lifecycle, text summaries for context, and extension points for AI-generated metadata.

**Boundaries**

Use DomainResource for clinical and healthcare domain resources that need status tracking, text narratives, or contained resources. Use BaseResource directly for non-clinical infrastructure resources (Actor, MessageDefinition, workflow definitions). DomainResource provides the healthcare domain patterns but not specific clinical logic - that belongs in concrete implementations like Patient or Observation.

**Relationships**

- Inherits from: BaseResource (gains ID, timestamps, validation, protocols)
- Extended by: Patient, Observation, Procedure, Condition, DiagnosticReport, and all clinical resources
- Implements: ClinicalResource protocol with get_patient_id() method
- Contains: Other BaseResource instances via contained field
- Extends: Healthcare vocabularies and systems via extension mechanism

**References**

- Clinical resources inherit DomainResource patterns: status, text, contained, extension
- Contained resources are embedded DomainResource instances for inline data
- Extensions reference HL7 FHIR StructureDefinitions and custom healthcare vocabularies


**Example**

=== "Rendered"

    #### ConceptMap

    | Field | Value |
    |---|---|
    | resource_type | ConceptMap |
    | id | conceptmap-a3469eb1 |
    | status | active |
    | created_at | 2025-08-18T17:19:51.502132Z |
    | updated_at | 2025-08-18T17:19:51.502132Z |

=== "JSON"

    ```json
    {
      "id": "conceptmap-a3469eb1",
      "created_at": "2025-08-18T17:19:51.502132Z",
      "updated_at": "2025-08-18T17:19:51.502132Z",
      "version": null,
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "ConceptMap",
      "agent_context": null,
      "status": "active",
      "text": null,
      "contained": null,
      "extension": null,
      "modifier_extension": null,
      "name": null,
      "source": "http://source.example.org",
      "target": "http://target.example.org",
      "group": []
    }
    ```

=== "YAML"

    ```yaml
    id: conceptmap-a3469eb1
    created_at: '2025-08-18T17:19:51.502132Z'
    updated_at: '2025-08-18T17:19:51.502132Z'
    version: null
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: ConceptMap
    agent_context: null
    status: active
    text: null
    contained: null
    extension: null
    modifier_extension: null
    name: null
    source: http://source.example.org
    target: http://target.example.org
    group: []
    
    ```

=== "Schema"

    #### ConceptMap Schema

    Mappings between concepts in two code systems.

    | Field | Type | Description |
    |---|---|---|
    | id | str | None | Unique identifier for this resource. Auto-generated if not provided. |
    | created_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was created |
    | updated_at | <class 'datetime.datetime'> | ISO 8601 timestamp when this resource was last updated |
    | version | typing.Optional[str] | Version label for this concept map |
    | identifier | list[str] | External identifiers for the resource (e.g., MRN, accession, system-specific IDs) (e.g., ['MRN:12345', 'local:abc-001']) |
    | language | str | None | Base language of the resource content (BCP-47, e.g., en, pt-BR) (e.g., en) |
    | implicit_rules | str | None | Reference to rules followed when constructing the resource (URI) (e.g., http://example.org/implicit-rules/v1) |
    | meta_profile | list[str] | Profiles asserting conformance of this resource (URIs) (e.g., ['http://hl7.org/fhir/StructureDefinition/Observation']) |
    | meta_source | str | None | Source system that produced the resource (e.g., ehr-system-x) |
    | meta_security | list[str] | Security labels applicable to this resource (policy/label codes) (e.g., ['very-sensitive', 'phi']) |
    | meta_tag | list[str] | User or system-defined tags for search and grouping (e.g., ['triage', 'llm-context', 'draft']) |
    | resource_type | typing.Literal['ConceptMap'] | None |
    | agent_context | dict[str, typing.Any] | None | Arbitrary, agent-provided context payload for this resource (e.g., {'section_key': 'free text content'}) |
    | status | <class 'str'> | Current status of the resource (e.g., active) |
    | text | str | None | Human-readable summary of the resource content (e.g., Patient John Doe, 45 years old) |
    | contained | list[hacs_models.base_resource.BaseResource] | None | Resources contained within this resource |
    | extension | dict[str, typing.Any] | None | Additional content defined by implementations (e.g., {'url': 'custom-field', 'valueString': 'custom-value'}) |
    | modifier_extension | dict[str, typing.Any] | None | Extensions that cannot be ignored (e.g., {'url': 'critical-field', 'valueBoolean': True}) |
    | name | typing.Optional[str] | Name of the concept map |
    | source | <class 'str'> | Source system URI |
    | target | <class 'str'> | Target system URI |
    | group | typing.List[hacs_models.terminology.ConceptMapElement] | List of mapping elements |



---
