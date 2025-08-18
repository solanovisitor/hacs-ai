# HACS Resource Catalog

Generated on 2025-08-18T17:00:45.103207Z

This comprehensive catalog documents every HACS resource organized by domain and purpose. Each resource includes detailed specifications and interactive examples.

---

## Core Models

Foundation classes and base structures that all HACS models inherit from

### BaseResource

**Scope & Usage**

BaseResource is the foundational class for all HACS healthcare resources, providing essential infrastructure for healthcare data modeling in AI agent systems. It establishes the core patterns for resource identification, lifecycle management, and data interchange that all HACS resources inherit.

**Boundaries**

BaseResource is an abstract foundation class that should not be instantiated directly in production systems. Use domain-specific resources (Patient, Observation, etc.) or extend BaseResource to create custom resource types.

**Key Capabilities**

- Automatic Identity Management: Generates unique, human-readable IDs with resource-type prefixes
- Lifecycle Tracking: Automatic created_at and updated_at timestamp management
- Version Control: Built-in version field for resource evolution and change tracking
- Protocol Compliance: Implements Identifiable, Timestamped, Versioned, Serializable, and Validatable protocols
- Type Safety: Full Pydantic v2 validation with rich type annotations
- Schema Generation: Automatic JSON Schema generation for API documentation
- Subset Creation: pick() method for creating lightweight models with specific fields

**Relationships**

- Parent of: All HACS resources inherit from BaseResource either directly or through DomainResource
- Implements: Identifiable, Timestamped, Versioned, Serializable, Validatable protocols
- Used by: All HACS tools, persistence layers, and validation systems

**Related Tools**

- save_record: Persists BaseResource instances to HACS database
- read_record: Retrieves BaseResource instances by ID and type
- validate_resource: Validates BaseResource instances against schemas
- create_reference: Creates Reference objects pointing to BaseResource instances

**Example**

=== "Rendered"

    #### ExampleResource

    | Field | Value |
    |---|---|
    | resource_type | ExampleResource |
    | id | exampleresource-76dace31 |
    | name | Sample Healthcare Resource |
    | created_at | 2025-08-18T17:00:45.104249Z |
    | updated_at | 2025-08-18T17:00:45.104252Z |

=== "JSON"

    ```json
    {
      "id": "exampleresource-76dace31",
      "created_at": "2025-08-18T17:00:45.104249Z",
      "updated_at": "2025-08-18T17:00:45.104252Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "ExampleResource",
      "agent_context": null,
      "name": "Sample Healthcare Resource",
      "value": 42
    }
    ```

=== "YAML"

    ```yaml
    id: exampleresource-76dace31
    created_at: '2025-08-18T17:00:45.104249Z'
    updated_at: '2025-08-18T17:00:45.104252Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: ExampleResource
    agent_context: null
    name: Sample Healthcare Resource
    value: 42
    
    ```

=== "Schema"

    #### ExampleResource Schema

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
    | value | <class 'int'> | None |



### DomainResource

**Scope & Usage**

DomainResource extends BaseResource to provide the foundation for all clinical and healthcare domain-specific resources in HACS. It implements the FHIR DomainResource pattern, adding essential fields and functionality required for healthcare interoperability.

**Boundaries**

DomainResource is designed specifically for healthcare and clinical domain resources. Use BaseResource directly for non-clinical resources like Actor, MessageDefinition, or infrastructure components.

**Key Capabilities**

- Clinical Status Management: Built-in status field with standard healthcare status values
- Human-Readable Narratives: text field for clinical review and patient communication
- Contained Resources: Support for resources that exist only within the parent resource context
- Extension Framework: Structured extension fields for additional healthcare data
- FHIR R4 Compliance: Follows FHIR DomainResource patterns for maximum interoperability

**Relationships**

- Inherits from: BaseResource (gains all foundation capabilities)
- Parent of: Patient, Observation, Procedure, Condition, DiagnosticReport, and all clinical resources
- Implements: ClinicalResource protocol patterns for clinical workflows

**Related Tools**

- save_clinical_record: Specialized persistence for domain resources
- validate_clinical_resource: Clinical-specific validation including status transitions
- generate_narrative: Automatic generation of human-readable text summaries

**Example**

=== "Rendered"

    #### ExampleDomain

    | Field | Value |
    |---|---|
    | resource_type | ExampleDomain |
    | id | exampledomain-acb0e08e |
    | status | active |
    | created_at | 2025-08-18T17:00:45.106700Z |
    | updated_at | 2025-08-18T17:00:45.106705Z |

=== "JSON"

    ```json
    {
      "id": "exampledomain-acb0e08e",
      "created_at": "2025-08-18T17:00:45.106700Z",
      "updated_at": "2025-08-18T17:00:45.106705Z",
      "version": "1.0.0",
      "identifier": [],
      "language": null,
      "implicit_rules": null,
      "meta_profile": [],
      "meta_source": null,
      "meta_security": [],
      "meta_tag": [],
      "resource_type": "ExampleDomain",
      "agent_context": null,
      "status": "active",
      "text": "Clinical protocol for patient care",
      "contained": null,
      "extension": null,
      "modifier_extension": null,
      "title": "Clinical Protocol",
      "description": "Standard operating procedure"
    }
    ```

=== "YAML"

    ```yaml
    id: exampledomain-acb0e08e
    created_at: '2025-08-18T17:00:45.106700Z'
    updated_at: '2025-08-18T17:00:45.106705Z'
    version: 1.0.0
    identifier: []
    language: null
    implicit_rules: null
    meta_profile: []
    meta_source: null
    meta_security: []
    meta_tag: []
    resource_type: ExampleDomain
    agent_context: null
    status: active
    text: Clinical protocol for patient care
    contained: null
    extension: null
    modifier_extension: null
    title: Clinical Protocol
    description: Standard operating procedure
    
    ```

=== "Schema"

    #### ExampleDomainResource Schema

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
    | description | <class 'str'> | None |



### Reference

**Scope & Usage**

Reference provides a standardized mechanism for linking between HACS resources, enabling the creation of interconnected healthcare data networks. It implements FHIR-compliant reference patterns.

**Boundaries**

Reference is designed specifically for resource-to-resource relationships and should not be used for general-purpose linking or URL management.

**Key Capabilities**

- FHIR-Compliant Referencing: Standard reference format "ResourceType/id"
- Type Safety: Explicit resource type specification for validation
- Display Names: Human-readable display text for UI presentation
- Cross-System References: Support for references to external systems

**Related Tools**

- resolve_reference: Retrieve the actual resource instance from a Reference
- create_reference: Generate Reference objects from resource instances
- validate_reference: Check reference integrity and target existence

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

ResourceBundle provides a container mechanism for grouping related HACS resources into cohesive collections, supporting batch operations and logical grouping of healthcare data.

**Boundaries**

ResourceBundle is designed for grouping actual HACS resources, not for general-purpose data collection or arbitrary object containers.

**Key Capabilities**

- Multiple Bundle Types: Document, message, transaction, collection, and searchset bundles
- Atomic Operations: Support for transactional updates across multiple resources
- Reference Resolution: Automatic resolution of references within bundle context
- Integrity Validation: Cross-resource validation and referential integrity checking

**Related Tools**

- create_bundle: Generate ResourceBundle instances from resource collections
- validate_bundle: Comprehensive bundle validation
- execute_bundle: Process transaction bundles with atomic operations

**Example**

=== "Rendered"

    #### ResourceBundle

    | Field | Value |
    |---|---|
    | resource_type | ResourceBundle |
    | id | resourcebundle-2d2c321a |
    | status | draft |
    | created_at | 2025-08-18T17:00:45.107857Z |
    | updated_at | 2025-08-18T17:00:45.107858Z |

=== "JSON"

    ```json
    {
      "id": "resourcebundle-2d2c321a",
      "created_at": "2025-08-18T17:00:45.107857Z",
      "updated_at": "2025-08-18T17:00:45.107858Z",
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
    id: resourcebundle-2d2c321a
    created_at: '2025-08-18T17:00:45.107857Z'
    updated_at: '2025-08-18T17:00:45.107858Z'
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

**Related Tools**

- authenticate_actor
- authorize_action


**Example**

=== "Rendered"

    #### Actor

    | Field | Value |
    |---|---|
    | resource_type | Actor |
    | id | actor-1607d657 |
    | name | Dr. Sarah Chen |
    | created_at | 2025-08-18T17:00:45.108583Z |
    | updated_at | 2025-08-18T17:00:45.108584Z |

=== "JSON"

    ```json
    {
      "id": "actor-1607d657",
      "created_at": "2025-08-18T17:00:45.108583Z",
      "updated_at": "2025-08-18T17:00:45.108584Z",
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
    id: actor-1607d657
    created_at: '2025-08-18T17:00:45.108583Z'
    updated_at: '2025-08-18T17:00:45.108584Z'
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

**Related Tools**

- consult_preferences
- inject_preferences


**Example**

=== "Rendered"

    #### ActorPreference

    | Field | Value |
    |---|---|
    | resource_type | ActorPreference |
    | id | actorpreference-2624bed0 |
    | created_at | 2025-08-18T17:00:45.109290Z |
    | updated_at | 2025-08-18T17:00:45.109291Z |

=== "JSON"

    ```json
    {
      "id": "actorpreference-2624bed0",
      "created_at": "2025-08-18T17:00:45.109290Z",
      "updated_at": "2025-08-18T17:00:45.109291Z",
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
    id: actorpreference-2624bed0
    created_at: '2025-08-18T17:00:45.109290Z'
    updated_at: '2025-08-18T17:00:45.109291Z'
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

**Related Tools**

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
    | id | patient-0cf31f9a |
    | status | active |
    | full_name | Maria Rodriguez |
    | gender | female |
    | birth_date | 1985-03-15 |
    | phone | +1-555-0101 |
    | created_at | 2025-08-18T17:00:45.109704Z |
    | updated_at | 2025-08-18T17:00:45.109704Z |

=== "JSON"

    ```json
    {
      "id": "patient-0cf31f9a",
      "created_at": "2025-08-18T17:00:45.109704Z",
      "updated_at": "2025-08-18T17:00:45.109704Z",
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
          "id": "humanname-abc3d07a",
          "created_at": "2025-08-18T17:00:45.109755Z",
          "updated_at": "2025-08-18T17:00:45.109755Z",
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
          "id": "contactpoint-ae39e43a",
          "created_at": "2025-08-18T17:00:45.109781Z",
          "updated_at": "2025-08-18T17:00:45.109781Z",
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
    id: patient-0cf31f9a
    created_at: '2025-08-18T17:00:45.109704Z'
    updated_at: '2025-08-18T17:00:45.109704Z'
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
    - id: humanname-abc3d07a
      created_at: '2025-08-18T17:00:45.109755Z'
      updated_at: '2025-08-18T17:00:45.109755Z'
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
    - id: contactpoint-ae39e43a
      created_at: '2025-08-18T17:00:45.109781Z'
      updated_at: '2025-08-18T17:00:45.109781Z'
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

**Related Tools**

- summarize_observation_value


**Example**

=== "Rendered"

    #### Observation

    | Field | Value |
    |---|---|
    | resource_type | Observation |
    | id | observation-9d4512fe |
    | status | final |
    | code | Blood Pressure |
    | value.quantity | 128.0 mmHg |
    | subject | Patient/123 |
    | performer | [] |
    | created_at | 2025-08-18T17:00:45.110968Z |
    | updated_at | 2025-08-18T17:00:45.110968Z |

=== "JSON"

    ```json
    {
      "id": "observation-9d4512fe",
      "created_at": "2025-08-18T17:00:45.110968Z",
      "updated_at": "2025-08-18T17:00:45.110968Z",
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
        "id": "codeableconcept-2f4176e8",
        "created_at": "2025-08-18T17:00:45.110920Z",
        "updated_at": "2025-08-18T17:00:45.110921Z",
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
      "subject": "Patient/123",
      "encounter": null,
      "effective_date_time": null,
      "issued": null,
      "performer": [],
      "value_quantity": {
        "id": "quantity-0033fcda",
        "created_at": "2025-08-18T17:00:45.110946Z",
        "updated_at": "2025-08-18T17:00:45.110947Z",
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
    id: observation-9d4512fe
    created_at: '2025-08-18T17:00:45.110968Z'
    updated_at: '2025-08-18T17:00:45.110968Z'
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
      id: codeableconcept-2f4176e8
      created_at: '2025-08-18T17:00:45.110920Z'
      updated_at: '2025-08-18T17:00:45.110921Z'
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
    subject: Patient/123
    encounter: null
    effective_date_time: null
    issued: null
    performer: []
    value_quantity:
      id: quantity-0033fcda
      created_at: '2025-08-18T17:00:45.110946Z'
      updated_at: '2025-08-18T17:00:45.110947Z'
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

**Related Tools**

- add_condition_stage


**Example**

=== "Rendered"

    #### Condition

    | Field | Value |
    |---|---|
    | resource_type | Condition |
    | id | condition-326031c8 |
    | status | active |
    | created_at | 2025-08-18T17:00:45.112029Z |
    | updated_at | 2025-08-18T17:00:45.112029Z |

=== "JSON"

    ```json
    {
      "id": "condition-326031c8",
      "created_at": "2025-08-18T17:00:45.112029Z",
      "updated_at": "2025-08-18T17:00:45.112029Z",
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
    id: condition-326031c8
    created_at: '2025-08-18T17:00:45.112029Z'
    updated_at: '2025-08-18T17:00:45.112029Z'
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

=== "JSON"

    ```json
    {
      "resource_type": "Procedure"
    }
    ```

=== "YAML"

    ```yaml
    resource_type: Procedure
    
    ```

=== "Schema"

    _No schema available_


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

**Related Tools**

- pin_resource
- validate_resource
- describe_model
- list_model_fields
- save_record
- read_record
- update_record


**Example**

=== "Rendered"

    #### DiagnosticReport

    | Field | Value |
    |---|---|
    | resource_type | DiagnosticReport |

=== "JSON"

    ```json
    {
      "resource_type": "DiagnosticReport"
    }
    ```

=== "YAML"

    ```yaml
    resource_type: DiagnosticReport
    
    ```

=== "Schema"

    _No schema available_


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

**Related Tools**

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

=== "JSON"

    ```json
    {
      "resource_type": "AllergyIntolerance"
    }
    ```

=== "YAML"

    ```yaml
    resource_type: AllergyIntolerance
    
    ```

=== "Schema"

    _No schema available_


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

**Related Tools**

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
    | id | familymemberhistory-874a8cfb |
    | status | completed |
    | created_at | 2025-08-18T17:00:45.113142Z |
    | updated_at | 2025-08-18T17:00:45.113143Z |

=== "JSON"

    ```json
    {
      "id": "familymemberhistory-874a8cfb",
      "created_at": "2025-08-18T17:00:45.113142Z",
      "updated_at": "2025-08-18T17:00:45.113143Z",
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
    id: familymemberhistory-874a8cfb
    created_at: '2025-08-18T17:00:45.113142Z'
    updated_at: '2025-08-18T17:00:45.113143Z'
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

**Related Tools**

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
    | id | immunization-74d7fbb0 |
    | status | completed |
    | created_at | 2025-08-18T17:00:45.113537Z |
    | updated_at | 2025-08-18T17:00:45.113537Z |

=== "JSON"

    ```json
    {
      "id": "immunization-74d7fbb0",
      "created_at": "2025-08-18T17:00:45.113537Z",
      "updated_at": "2025-08-18T17:00:45.113537Z",
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
    id: immunization-74d7fbb0
    created_at: '2025-08-18T17:00:45.113537Z'
    updated_at: '2025-08-18T17:00:45.113537Z'
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

**Related Tools**

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
    | id | medication-c50c38d7 |
    | created_at | 2025-08-18T17:00:45.114495Z |
    | updated_at | 2025-08-18T17:00:45.114497Z |

=== "JSON"

    ```json
    {
      "id": "medication-c50c38d7",
      "created_at": "2025-08-18T17:00:45.114495Z",
      "updated_at": "2025-08-18T17:00:45.114497Z",
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
    id: medication-c50c38d7
    created_at: '2025-08-18T17:00:45.114495Z'
    updated_at: '2025-08-18T17:00:45.114497Z'
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

**Related Tools**

- validate_prescription
- check_allergy_contraindications
- check_drug_interactions
- route_prescription


**Example**

=== "Rendered"

    #### MedicationRequest

    | Field | Value |
    |---|---|
    | resource_type | MedicationRequest |

=== "JSON"

    ```json
    {
      "resource_type": "MedicationRequest"
    }
    ```

=== "YAML"

    ```yaml
    resource_type: MedicationRequest
    
    ```

=== "Schema"

    _No schema available_


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

**Related Tools**

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
    | id | appointment-78bc0eea |
    | status | booked |
    | created_at | 2025-08-18T17:00:45.115187Z |
    | updated_at | 2025-08-18T17:00:45.115188Z |

=== "JSON"

    ```json
    {
      "id": "appointment-78bc0eea",
      "created_at": "2025-08-18T17:00:45.115187Z",
      "updated_at": "2025-08-18T17:00:45.115188Z",
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
    id: appointment-78bc0eea
    created_at: '2025-08-18T17:00:45.115187Z'
    updated_at: '2025-08-18T17:00:45.115188Z'
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

**Related Tools**

- create_lab_request
- create_imaging_request
- create_referral_request
- validate_service_request
- route_service_request


**Example**

=== "Rendered"

    #### ServiceRequest

    | Field | Value |
    |---|---|
    | resource_type | ServiceRequest |

=== "JSON"

    ```json
    {
      "resource_type": "ServiceRequest"
    }
    ```

=== "YAML"

    ```yaml
    resource_type: ServiceRequest
    
    ```

=== "Schema"

    _No schema available_


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

**Related Tools**

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
    | id | careplan-aefa47c4 |
    | status | active |
    | intent | plan |
    | created_at | 2025-08-18T17:00:45.115765Z |
    | updated_at | 2025-08-18T17:00:45.115765Z |

=== "JSON"

    ```json
    {
      "id": "careplan-aefa47c4",
      "created_at": "2025-08-18T17:00:45.115765Z",
      "updated_at": "2025-08-18T17:00:45.115765Z",
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
    id: careplan-aefa47c4
    created_at: '2025-08-18T17:00:45.115765Z'
    updated_at: '2025-08-18T17:00:45.115765Z'
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

**Related Tools**

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
    | id | careteam-dcaad0f3 |
    | status | active |
    | created_at | 2025-08-18T17:00:45.117223Z |
    | updated_at | 2025-08-18T17:00:45.117224Z |

=== "JSON"

    ```json
    {
      "id": "careteam-dcaad0f3",
      "created_at": "2025-08-18T17:00:45.117223Z",
      "updated_at": "2025-08-18T17:00:45.117224Z",
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
    id: careteam-dcaad0f3
    created_at: '2025-08-18T17:00:45.117223Z'
    updated_at: '2025-08-18T17:00:45.117224Z'
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

**Related Tools**

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
    | id | nutritionorder-bfa1a545 |
    | status | active |
    | intent | order |
    | created_at | 2025-08-18T17:00:45.117560Z |
    | updated_at | 2025-08-18T17:00:45.117560Z |

=== "JSON"

    ```json
    {
      "id": "nutritionorder-bfa1a545",
      "created_at": "2025-08-18T17:00:45.117560Z",
      "updated_at": "2025-08-18T17:00:45.117560Z",
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
    id: nutritionorder-bfa1a545
    created_at: '2025-08-18T17:00:45.117560Z'
    updated_at: '2025-08-18T17:00:45.117560Z'
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

**Related Tools**

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
    | id | plandefinition-f67e5573 |
    | status | draft |
    | created_at | 2025-08-18T17:00:45.117970Z |
    | updated_at | 2025-08-18T17:00:45.117971Z |

=== "JSON"

    ```json
    {
      "id": "plandefinition-f67e5573",
      "created_at": "2025-08-18T17:00:45.117970Z",
      "updated_at": "2025-08-18T17:00:45.117971Z",
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
    id: plandefinition-f67e5573
    created_at: '2025-08-18T17:00:45.117970Z'
    updated_at: '2025-08-18T17:00:45.117971Z'
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

**Related Tools**

- verify_practitioner_credential
- link_practitioner_to_organization
- update_practitioner_affiliation


**Example**

=== "Rendered"

    #### Practitioner

    | Field | Value |
    |---|---|
    | resource_type | Practitioner |
    | id | practitioner-805976e1 |
    | status | active |
    | name | [] |
    | created_at | 2025-08-18T17:00:45.118545Z |
    | updated_at | 2025-08-18T17:00:45.118545Z |

=== "JSON"

    ```json
    {
      "id": "practitioner-805976e1",
      "created_at": "2025-08-18T17:00:45.118545Z",
      "updated_at": "2025-08-18T17:00:45.118545Z",
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
    id: practitioner-805976e1
    created_at: '2025-08-18T17:00:45.118545Z'
    updated_at: '2025-08-18T17:00:45.118545Z'
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

**Related Tools**

- register_organization
- link_organization_affiliation
- manage_service_locations


**Example**

=== "Rendered"

    #### Organization

    | Field | Value |
    |---|---|
    | resource_type | Organization |
    | id | organization-2378d6eb |
    | status | active |
    | created_at | 2025-08-18T17:00:45.118932Z |
    | updated_at | 2025-08-18T17:00:45.118933Z |

=== "JSON"

    ```json
    {
      "id": "organization-2378d6eb",
      "created_at": "2025-08-18T17:00:45.118932Z",
      "updated_at": "2025-08-18T17:00:45.118933Z",
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
    id: organization-2378d6eb
    created_at: '2025-08-18T17:00:45.118932Z'
    updated_at: '2025-08-18T17:00:45.118933Z'
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

**Related Tools**

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
    | id | documentreference-fef5ed8c |
    | status | current |
    | created_at | 2025-08-18T17:00:45.119332Z |
    | updated_at | 2025-08-18T17:00:45.119332Z |

=== "JSON"

    ```json
    {
      "id": "documentreference-fef5ed8c",
      "created_at": "2025-08-18T17:00:45.119332Z",
      "updated_at": "2025-08-18T17:00:45.119332Z",
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
    id: documentreference-fef5ed8c
    created_at: '2025-08-18T17:00:45.119332Z'
    updated_at: '2025-08-18T17:00:45.119332Z'
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
    | id | evidence-93b94b1b |
    | created_at | 2025-08-18T17:00:45.119934Z |
    | updated_at | 2025-08-18T17:00:45.119935Z |

=== "JSON"

    ```json
    {
      "id": "evidence-93b94b1b",
      "created_at": "2025-08-18T17:00:45.119934Z",
      "updated_at": "2025-08-18T17:00:45.119935Z",
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
    id: evidence-93b94b1b
    created_at: '2025-08-18T17:00:45.119934Z'
    updated_at: '2025-08-18T17:00:45.119935Z'
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

**Related Tools**

- standardize_messages
- semantic_tool_loadout


**Example**

=== "Rendered"

    #### AgentMessage

    | Field | Value |
    |---|---|
    | resource_type | AgentMessage |

=== "JSON"

    ```json
    {
      "resource_type": "AgentMessage"
    }
    ```

=== "YAML"

    ```yaml
    resource_type: AgentMessage
    
    ```

=== "Schema"

    _No schema available_


### MessageDefinition

**Scope & Usage**

Standardized agent message envelope and definition for inter-agent/tool communication.

**Boundaries**

Not a clinical document; represents transport of instructions, content, and tool calls.

**Relationships**

- Referenced by: AgentMessage as runtime specialization

**Related Tools**

- standardize_messages
- log_llm_request


**Example**

=== "Rendered"

    #### MessageDefinition

    | Field | Value |
    |---|---|
    | resource_type | MessageDefinition |

=== "JSON"

    ```json
    {
      "resource_type": "MessageDefinition"
    }
    ```

=== "YAML"

    ```yaml
    resource_type: MessageDefinition
    
    ```

=== "Schema"

    _No schema available_


### MemoryBlock

**Scope & Usage**

Agent memory item (episodic, semantic, working) for context engineering.

**Boundaries**

Not a clinical record; may link to clinical resources as context.

**Relationships**

- Referenced by: Agents; Indexed for retrieval

**Related Tools**

- store_memory
- retrieve_memories


**Example**

=== "Rendered"

    #### MemoryBlock

    | Field | Value |
    |---|---|
    | resource_type | MemoryBlock |

=== "JSON"

    ```json
    {
      "resource_type": "MemoryBlock"
    }
    ```

=== "YAML"

    ```yaml
    resource_type: MemoryBlock
    
    ```

=== "Schema"

    _No schema available_


### EpisodicMemory

**Scope & Usage**

Time-stamped event memory used by agents to recall episodes.

**Boundaries**

Use SemanticMemory for facts/concepts; WorkingMemory for short-lived context.

**Relationships**

- Subtype of: MemoryBlock

**Related Tools**

- store_memory
- retrieve_memories


**Example**

=== "Rendered"

    #### EpisodicMemory

    | Field | Value |
    |---|---|
    | resource_type | EpisodicMemory |

=== "JSON"

    ```json
    {
      "resource_type": "EpisodicMemory"
    }
    ```

=== "YAML"

    ```yaml
    resource_type: EpisodicMemory
    
    ```

=== "Schema"

    _No schema available_


### SemanticMemory

**Scope & Usage**

Long-lived knowledge/facts to guide agent behavior and preferences.

**Boundaries**

Not clinical truth; may be derived and should be auditable.

**Relationships**

- Subtype of: MemoryBlock

**Related Tools**

- store_memory
- retrieve_memories


**Example**

=== "Rendered"

    #### SemanticMemory

    | Field | Value |
    |---|---|
    | resource_type | SemanticMemory |

=== "JSON"

    ```json
    {
      "resource_type": "SemanticMemory"
    }
    ```

=== "YAML"

    ```yaml
    resource_type: SemanticMemory
    
    ```

=== "Schema"

    _No schema available_


### WorkingMemory

**Scope & Usage**

Short-term, task-scoped memory for in-flight agent steps.

**Boundaries**

Should be pruned/expired to avoid context poisoning.

**Relationships**

- Subtype of: MemoryBlock

**Related Tools**

- store_memory
- retrieve_memories
- prune_state


**Example**

=== "Rendered"

    #### WorkingMemory

    | Field | Value |
    |---|---|
    | resource_type | WorkingMemory |

=== "JSON"

    ```json
    {
      "resource_type": "WorkingMemory"
    }
    ```

=== "YAML"

    ```yaml
    resource_type: WorkingMemory
    
    ```

=== "Schema"

    _No schema available_


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

**Related Tools**

- describe_model
- list_model_fields


**Example**

=== "Rendered"

    #### WorkflowDefinition

    | Field | Value |
    |---|---|
    | resource_type | WorkflowDefinition |
    | id | workflowdefinition-7d3d62f9 |
    | status | draft |
    | created_at | 2025-08-18T17:00:45.126463Z |
    | updated_at | 2025-08-18T17:00:45.126464Z |

=== "JSON"

    ```json
    {
      "id": "workflowdefinition-7d3d62f9",
      "created_at": "2025-08-18T17:00:45.126463Z",
      "updated_at": "2025-08-18T17:00:45.126464Z",
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
    id: workflowdefinition-7d3d62f9
    created_at: '2025-08-18T17:00:45.126463Z'
    updated_at: '2025-08-18T17:00:45.126464Z'
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

**Related Tools**

- create_event
- update_event_status
- add_event_performer
- schedule_event
- summarize_event


**Example**

=== "Rendered"

    #### Event

    | Field | Value |
    |---|---|
    | resource_type | Event |
    | id | event-e01ef92c |
    | status | in-progress |
    | performer | [] |
    | based_on | [] |
    | created_at | 2025-08-18T17:00:45.126906Z |
    | updated_at | 2025-08-18T17:00:45.126906Z |

=== "JSON"

    ```json
    {
      "id": "event-e01ef92c",
      "created_at": "2025-08-18T17:00:45.126906Z",
      "updated_at": "2025-08-18T17:00:45.126906Z",
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
    id: event-e01ef92c
    created_at: '2025-08-18T17:00:45.126906Z'
    updated_at: '2025-08-18T17:00:45.126906Z'
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

**Related Tools**

- follow_graph
- describe_model


**Example**

=== "Rendered"

    #### GraphDefinition

    | Field | Value |
    |---|---|
    | resource_type | GraphDefinition |

=== "JSON"

    ```json
    {
      "resource_type": "GraphDefinition"
    }
    ```

=== "YAML"

    ```yaml
    resource_type: GraphDefinition
    
    ```

=== "Schema"

    _No schema available_


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

**Related Tools**

- get_possible_codes
- expand_value_set


**Example**

=== "Rendered"

    #### TerminologySystem

    | Field | Value |
    |---|---|
    | resource_type | TerminologySystem |

=== "JSON"

    ```json
    {
      "resource_type": "TerminologySystem"
    }
    ```

=== "YAML"

    ```yaml
    resource_type: TerminologySystem
    
    ```

=== "Schema"

    _No schema available_


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

**Related Tools**

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

**Related Tools**

- expand_value_set
- validate_code_in_valueset


**Example**

=== "Rendered"

    #### ValueSet

    | Field | Value |
    |---|---|
    | resource_type | ValueSet |
    | id | valueset-18e3b5c9 |
    | status | active |
    | created_at | 2025-08-18T17:00:45.127984Z |
    | updated_at | 2025-08-18T17:00:45.127985Z |

=== "JSON"

    ```json
    {
      "id": "valueset-18e3b5c9",
      "created_at": "2025-08-18T17:00:45.127984Z",
      "updated_at": "2025-08-18T17:00:45.127985Z",
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
    id: valueset-18e3b5c9
    created_at: '2025-08-18T17:00:45.127984Z'
    updated_at: '2025-08-18T17:00:45.127985Z'
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

_No documentation available_

**Example**

=== "Rendered"

    #### ConceptMap

    | Field | Value |
    |---|---|
    | resource_type | ConceptMap |

=== "JSON"

    ```json
    {
      "resource_type": "ConceptMap"
    }
    ```

=== "YAML"

    ```yaml
    resource_type: ConceptMap
    
    ```

=== "Schema"

    _No schema available_


---
