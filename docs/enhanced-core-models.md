# Enhanced Core Models Documentation

Generated on 2025-08-18T15:41:47.793400Z

This section provides comprehensive documentation for HACS core models with real-world examples, method documentation, and usage patterns. Each model includes practical examples with realistic healthcare data and demonstrates available methods for manipulation and validation.

---

## BaseResource

### Overview

Foundation class for all HACS resources with ID generation, timestamps, and validation

### Class Documentation

```
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
...

*[Full documentation available in source code]*
```

### Key Methods

Available methods for this model:

- **`update_timestamp()`**: Update the updated_at timestamp to current time
- **`to_dict()`**: Convert object to dictionary representation
- **`from_dict()`**: Create object from dictionary representation (class method)
- **`validate()`**: Validate the object and return list of errors
- **`is_valid()`**: Check if the object is valid (returns boolean)
- **`is_newer_than()`**: Compare timestamps to determine if this resource is newer
- **`pick()`**: Create a subset model containing only specified fields (class method)
- **`get_age_days()`**: Calculate age of this resource in days since creation
- **`to_reference()`**: Create a FHIR-style reference string for this resource
- **`get_descriptive_schema()`**: Get lightweight schema for LLM orchestration (class method)
- **`get_specifications()`**: Return structured definition for agents and registries (class method)

### Comprehensive Examples

#### Basic Resource

=== "Rendered"

    ### ExampleResource

    | Field | Value |
    |---|---|
    | resource_type | ExampleResource |
    | id | exampleresource-8504aa92 |
    | name | Sample Resource |
    | created_at | 2025-08-18T15:41:47.794252Z |
    | updated_at | 2025-08-18T15:41:47.794254Z |

=== "JSON"

    ```json
    {
      "id": "exampleresource-8504aa92",
      "created_at": "2025-08-18T15:41:47.794252Z",
      "updated_at": "2025-08-18T15:41:47.794254Z",
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
      "name": "Sample Resource",
      "value": 42
    }
    ```

=== "YAML"

    ```yaml
    id: exampleresource-8504aa92
    created_at: '2025-08-18T15:41:47.794252Z'
    updated_at: '2025-08-18T15:41:47.794254Z'
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
    name: Sample Resource
    value: 42
    
    ```

=== "Schema"

    ### ExampleResource Schema

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



---

## DomainResource

### Overview

Extended base class for clinical domain resources with FHIR compliance

### Class Documentation

```
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
...

*[Full documentation available in source code]*
```

### Comprehensive Examples

#### Domain Resource Example

=== "Rendered"

    ### ExampleDomain

    | Field | Value |
    |---|---|
    | resource_type | ExampleDomain |
    | id | exampledomain-bc4d0084 |
    | status | active |
    | created_at | 2025-08-18T15:41:47.796305Z |
    | updated_at | 2025-08-18T15:41:47.796308Z |

=== "JSON"

    ```json
    {
      "id": "exampledomain-bc4d0084",
      "created_at": "2025-08-18T15:41:47.796305Z",
      "updated_at": "2025-08-18T15:41:47.796308Z",
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
      "text": "This is a clinical protocol for standardized patient care procedures.",
      "contained": null,
      "extension": null,
      "modifier_extension": null,
      "title": "Clinical Protocol",
      "description": "Standard operating procedure for patient care"
    }
    ```

=== "YAML"

    ```yaml
    id: exampledomain-bc4d0084
    created_at: '2025-08-18T15:41:47.796305Z'
    updated_at: '2025-08-18T15:41:47.796308Z'
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
    text: This is a clinical protocol for standardized patient care procedures.
    contained: null
    extension: null
    modifier_extension: null
    title: Clinical Protocol
    description: Standard operating procedure for patient care
    
    ```

=== "Schema"

    ### ExampleDomainResource Schema

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



---

## Patient

### Overview

Demographics and administrative information for healthcare recipients

### Class Documentation

```
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
...

*[Full documentation available in source code]*
```

### Key Methods

Available methods for this model:

- **`display_name()`**: Get display name from structured or full name
- **`age_years()`**: Calculate age in years from birth date
- **`add_identifier()`**: Add a new identifier with type and system
- **`get_identifier_by_type()`**: Retrieve identifier by type code
- **`add_care_provider()`**: Add a care provider reference
- **`update_agent_context()`**: Update agent context with key-value pair
- **`deactivate()`**: Deactivate patient record with optional reason

### Comprehensive Examples

#### Complete Patient Record

=== "Rendered"

    ### Patient

    | Field | Value |
    |---|---|
    | resource_type | Patient |
    | id | patient-7e4ff6c6 |
    | status | active |
    | full_name | Dr. Emily Johnson |
    | gender | female |
    | birth_date | 1985-03-15 |
    | phone | +1-555-0123 |
    | email | emily.johnson@email.com |
    | address_text | 123 Medical Plaza, Suite 200, Boston, MA 02101 |
    | created_at | 2025-08-18T15:41:47.796698Z |
    | updated_at | 2025-08-18T15:41:47.796698Z |

=== "JSON"

    ```json
    {
      "id": "patient-7e4ff6c6",
      "created_at": "2025-08-18T15:41:47.796698Z",
      "updated_at": "2025-08-18T15:41:47.796698Z",
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
          "id": "humanname-68cd745b",
          "created_at": "2025-08-18T15:41:47.797120Z",
          "updated_at": "2025-08-18T15:41:47.797120Z",
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
          "family": "Johnson",
          "given": [
            "Emily"
          ],
          "prefix": [
            "Dr."
          ],
          "suffix": [],
          "full_name": "Dr. Emily Johnson",
          "display_name": "Emily Johnson"
        }
      ],
      "full_name": "Dr. Emily Johnson",
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
          "id": "contactpoint-693f7c35",
          "created_at": "2025-08-18T15:41:47.797149Z",
          "updated_at": "2025-08-18T15:41:47.797149Z",
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
          "value": "+1-555-0123",
          "use": "home",
          "rank": 1
        },
        {
          "id": "contactpoint-5970fa17",
          "created_at": "2025-08-18T15:41:47.797186Z",
          "updated_at": "2025-08-18T15:41:47.797186Z",
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
          "system": "email",
          "value": "emily.johnson@email.com",
          "use": "home",
          "rank": 1
        }
      ],
      "phone": "+1-555-0123",
      "email": "emily.johnson@email.com",
      "address": [
        {
          "id": "address-5e235844",
          "created_at": "2025-08-18T15:41:47.797197Z",
          "updated_at": "2025-08-18T15:41:47.797198Z",
          "version": "1.0.0",
          "identifier": [],
          "language": null,
          "implicit_rules": null,
          "meta_profile": [],
          "meta_source": null,
          "meta_security": [],
          "meta_tag": [],
          "resource_type": "Address",
          "agent_context": null,
          "status": "active",
          "text": "123 Medical Plaza, Suite 200, Boston, MA 02101",
          "contained": null,
          "extension": null,
          "modifier_extension": null,
          "use": "home",
          "type_": null,
          "line": [
            "123 Medical Plaza"
          ],
          "city": "Suite 200",
          "district": null,
          "state": "Boston",
          "postal_code": null,
          "country": "MA 02101",
          "formatted_address": "123 Medical Plaza, Suite 200, Boston, MA 02101"
        }
      ],
      "address_text": "123 Medical Plaza, Suite 200, Boston, MA 02101",
      "marital_status": null,
      "communication": [],
      "care_provider": [],
      "link": [],
      "communication_preference": null,
      "contact": [],
      "active": true,
      "display_name": "Emily Johnson",
      "age_years": null
    }
    ```

=== "YAML"

    ```yaml
    id: patient-7e4ff6c6
    created_at: '2025-08-18T15:41:47.796698Z'
    updated_at: '2025-08-18T15:41:47.796698Z'
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
    - id: humanname-68cd745b
      created_at: '2025-08-18T15:41:47.797120Z'
      updated_at: '2025-08-18T15:41:47.797120Z'
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
      family: Johnson
      given:
      - Emily
      prefix:
      - Dr.
      suffix: []
      full_name: Dr. Emily Johnson
      display_name: Emily Johnson
    full_name: Dr. Emily Johnson
    gender: female
    birth_date: '1985-03-15'
    age: null
    deceased_boolean: false
    deceased_date_time: null
    multiple_birth_boolean: null
    multiple_birth_integer: null
    photo: []
    telecom:
    - id: contactpoint-693f7c35
      created_at: '2025-08-18T15:41:47.797149Z'
      updated_at: '2025-08-18T15:41:47.797149Z'
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
      value: +1-555-0123
      use: home
      rank: 1
    - id: contactpoint-5970fa17
      created_at: '2025-08-18T15:41:47.797186Z'
      updated_at: '2025-08-18T15:41:47.797186Z'
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
      system: email
      value: emily.johnson@email.com
      use: home
      rank: 1
    phone: +1-555-0123
    email: emily.johnson@email.com
    address:
    - id: address-5e235844
      created_at: '2025-08-18T15:41:47.797197Z'
      updated_at: '2025-08-18T15:41:47.797198Z'
      version: 1.0.0
      identifier: []
      language: null
      implicit_rules: null
      meta_profile: []
      meta_source: null
      meta_security: []
      meta_tag: []
      resource_type: Address
      agent_context: null
      status: active
      text: 123 Medical Plaza, Suite 200, Boston, MA 02101
      contained: null
      extension: null
      modifier_extension: null
      use: home
      type_: null
      line:
      - 123 Medical Plaza
      city: Suite 200
      district: null
      state: Boston
      postal_code: null
      country: MA 02101
      formatted_address: 123 Medical Plaza, Suite 200, Boston, MA 02101
    address_text: 123 Medical Plaza, Suite 200, Boston, MA 02101
    marital_status: null
    communication: []
    care_provider: []
    link: []
    communication_preference: null
    contact: []
    active: true
    display_name: Emily Johnson
    age_years: null
    
    ```

=== "Schema"

    ### Patient Schema

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



#### Patient with Structured Data

=== "Rendered"

    ### Patient

    | Field | Value |
    |---|---|
    | resource_type | Patient |
    | id | patient-190b347f |
    | status | active |
    | gender | female |
    | birth_date | 1978-11-22 |
    | created_at | 2025-08-18T15:41:47.797233Z |
    | updated_at | 2025-08-18T15:41:47.797234Z |

=== "JSON"

    ```json
    {
      "id": "patient-190b347f",
      "created_at": "2025-08-18T15:41:47.797233Z",
      "updated_at": "2025-08-18T15:41:47.797234Z",
      "version": "1.0.0",
      "identifier": [
        {
          "id": "identifier-541a3efc",
          "created_at": "2025-08-18T15:41:47.797235Z",
          "updated_at": "2025-08-18T15:41:47.797236Z",
          "version": "1.0.0",
          "identifier": [],
          "language": null,
          "implicit_rules": null,
          "meta_profile": [],
          "meta_source": null,
          "meta_security": [],
          "meta_tag": [],
          "resource_type": "Identifier",
          "agent_context": null,
          "status": "active",
          "text": null,
          "contained": null,
          "extension": null,
          "modifier_extension": null,
          "use": "usual",
          "type_code": "MR",
          "system": "http://hospital.org/mrn",
          "value": "MRN-987654",
          "assigner": null
        }
      ],
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
          "id": "humanname-a9894dd7",
          "created_at": "2025-08-18T15:41:47.797260Z",
          "updated_at": "2025-08-18T15:41:47.797261Z",
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
          "use": "official",
          "family": "Rodriguez",
          "given": [
            "Maria",
            "Carmen"
          ],
          "prefix": [
            "Dr."
          ],
          "suffix": [
            "MD",
            "PhD"
          ],
          "full_name": "Dr. Maria Carmen Rodriguez MD PhD",
          "display_name": "Maria Carmen Rodriguez"
        }
      ],
      "full_name": null,
      "gender": "female",
      "birth_date": "1978-11-22",
      "age": null,
      "deceased_boolean": false,
      "deceased_date_time": null,
      "multiple_birth_boolean": null,
      "multiple_birth_integer": null,
      "photo": [],
      "telecom": [],
      "phone": null,
      "email": null,
      "address": [
        {
          "id": "address-77565227",
          "created_at": "2025-08-18T15:41:47.797272Z",
          "updated_at": "2025-08-18T15:41:47.797272Z",
          "version": "1.0.0",
          "identifier": [],
          "language": null,
          "implicit_rules": null,
          "meta_profile": [],
          "meta_source": null,
          "meta_security": [],
          "meta_tag": [],
          "resource_type": "Address",
          "agent_context": null,
          "status": "active",
          "text": null,
          "contained": null,
          "extension": null,
          "modifier_extension": null,
          "use": "home",
          "type_": "physical",
          "line": [
            "456 Oak Street",
            "Apt 3B"
          ],
          "city": "San Francisco",
          "district": null,
          "state": "CA",
          "postal_code": "94102",
          "country": "US",
          "formatted_address": "456 Oak Street, Apt 3B, San Francisco CA 94102, US"
        }
      ],
      "address_text": null,
      "marital_status": null,
      "communication": [],
      "care_provider": [],
      "link": [],
      "communication_preference": null,
      "contact": [
        {
          "system": "email",
          "value": "maria.rodriguez@hospital.org",
          "use": "work"
        },
        {
          "system": "phone",
          "value": "+1-555-0987",
          "use": "mobile"
        }
      ],
      "active": true,
      "display_name": "Maria Carmen Rodriguez",
      "age_years": null
    }
    ```

=== "YAML"

    ```yaml
    id: patient-190b347f
    created_at: '2025-08-18T15:41:47.797233Z'
    updated_at: '2025-08-18T15:41:47.797234Z'
    version: 1.0.0
    identifier:
    - id: identifier-541a3efc
      created_at: '2025-08-18T15:41:47.797235Z'
      updated_at: '2025-08-18T15:41:47.797236Z'
      version: 1.0.0
      identifier: []
      language: null
      implicit_rules: null
      meta_profile: []
      meta_source: null
      meta_security: []
      meta_tag: []
      resource_type: Identifier
      agent_context: null
      status: active
      text: null
      contained: null
      extension: null
      modifier_extension: null
      use: usual
      type_code: MR
      system: http://hospital.org/mrn
      value: MRN-987654
      assigner: null
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
    - id: humanname-a9894dd7
      created_at: '2025-08-18T15:41:47.797260Z'
      updated_at: '2025-08-18T15:41:47.797261Z'
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
      use: official
      family: Rodriguez
      given:
      - Maria
      - Carmen
      prefix:
      - Dr.
      suffix:
      - MD
      - PhD
      full_name: Dr. Maria Carmen Rodriguez MD PhD
      display_name: Maria Carmen Rodriguez
    full_name: null
    gender: female
    birth_date: '1978-11-22'
    age: null
    deceased_boolean: false
    deceased_date_time: null
    multiple_birth_boolean: null
    multiple_birth_integer: null
    photo: []
    telecom: []
    phone: null
    email: null
    address:
    - id: address-77565227
      created_at: '2025-08-18T15:41:47.797272Z'
      updated_at: '2025-08-18T15:41:47.797272Z'
      version: 1.0.0
      identifier: []
      language: null
      implicit_rules: null
      meta_profile: []
      meta_source: null
      meta_security: []
      meta_tag: []
      resource_type: Address
      agent_context: null
      status: active
      text: null
      contained: null
      extension: null
      modifier_extension: null
      use: home
      type_: physical
      line:
      - 456 Oak Street
      - Apt 3B
      city: San Francisco
      district: null
      state: CA
      postal_code: '94102'
      country: US
      formatted_address: 456 Oak Street, Apt 3B, San Francisco CA 94102, US
    address_text: null
    marital_status: null
    communication: []
    care_provider: []
    link: []
    communication_preference: null
    contact:
    - system: email
      value: maria.rodriguez@hospital.org
      use: work
    - system: phone
      value: +1-555-0987
      use: mobile
    active: true
    display_name: Maria Carmen Rodriguez
    age_years: null
    
    ```

=== "Schema"

    ### Patient Schema

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



---

## Observation

### Overview

Measurements and assertions about patients, devices, or other subjects

### Class Documentation

```
Measurements and simple assertions made about a patient.

Observations are a central element in healthcare, used to support
diagnosis, monitor progress, determine baselines and patterns, and
capture demographic characteristics.
```

### Key Methods

Available methods for this model:

- **`add_note()`**: Add a note/annotation to the observation
- **`set_quantity_value()`**: Set a numeric value with unit and system
- **`set_string_value()`**: Set a text/string value
- **`set_boolean_value()`**: Set a boolean value
- **`get_value_summary()`**: Get human-readable summary of the value
- **`add_category()`**: Add a category classification
- **`add_reference_range()`**: Add reference range for interpretation
- **`is_within_normal_range()`**: Check if value is within normal range
- **`get_interpretation_summary()`**: Get summary of clinical interpretation

### Comprehensive Examples

#### Blood Pressure Reading

=== "Rendered"

    ### Observation

    | Field | Value |
    |---|---|
    | resource_type | Observation |
    | id | observation-f35b2fca |
    | status | final |
    | code | Blood Pressure |
    | value.quantity | 128.0 mmHg |
    | subject | Patient/patient-12345 |
    | effective_date_time | 2024-01-15T10:30:00Z |
    | performer | [] |
    | created_at | 2025-08-18T15:41:47.800420Z |
    | updated_at | 2025-08-18T15:41:47.800420Z |

=== "JSON"

    ```json
    {
      "id": "observation-f35b2fca",
      "created_at": "2025-08-18T15:41:47.800420Z",
      "updated_at": "2025-08-18T15:41:47.800420Z",
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
        "id": "codeableconcept-79e81542",
        "created_at": "2025-08-18T15:41:47.800371Z",
        "updated_at": "2025-08-18T15:41:47.800372Z",
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
        "coding": [
          {
            "id": "coding-da32c652",
            "created_at": "2025-08-18T15:41:47.800382Z",
            "updated_at": "2025-08-18T15:41:47.800382Z",
            "version": null,
            "identifier": [],
            "language": null,
            "implicit_rules": null,
            "meta_profile": [],
            "meta_source": null,
            "meta_security": [],
            "meta_tag": [],
            "resource_type": "Coding",
            "agent_context": null,
            "status": "active",
            "text": null,
            "contained": null,
            "extension": null,
            "modifier_extension": null,
            "system": "http://loinc.org",
            "code": "85354-9",
            "display": "Blood pressure panel with all children optional"
          }
        ]
      },
      "category": [
        {
          "id": "codeableconcept-76ebad0c",
          "created_at": "2025-08-18T15:41:47.800431Z",
          "updated_at": "2025-08-18T15:41:47.800431Z",
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
          "text": null,
          "contained": null,
          "extension": null,
          "modifier_extension": null,
          "coding": [
            {
              "id": "coding-f9fa7aa2",
              "created_at": "2025-08-18T15:41:47.800433Z",
              "updated_at": "2025-08-18T15:41:47.800433Z",
              "version": null,
              "identifier": [],
              "language": null,
              "implicit_rules": null,
              "meta_profile": [],
              "meta_source": null,
              "meta_security": [],
              "meta_tag": [],
              "resource_type": "Coding",
              "agent_context": null,
              "status": "active",
              "text": null,
              "contained": null,
              "extension": null,
              "modifier_extension": null,
              "system": "http://terminology.hl7.org/CodeSystem/observation-category",
              "code": "vital-signs",
              "display": "Vital Signs"
            }
          ]
        }
      ],
      "method": null,
      "device": null,
      "subject": "Patient/patient-12345",
      "encounter": null,
      "effective_date_time": "2024-01-15T10:30:00Z",
      "issued": null,
      "performer": [],
      "value_quantity": {
        "id": "quantity-80906162",
        "created_at": "2025-08-18T15:41:47.800401Z",
        "updated_at": "2025-08-18T15:41:47.800402Z",
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
        "system": "http://unitsofmeasure.org",
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
    id: observation-f35b2fca
    created_at: '2025-08-18T15:41:47.800420Z'
    updated_at: '2025-08-18T15:41:47.800420Z'
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
      id: codeableconcept-79e81542
      created_at: '2025-08-18T15:41:47.800371Z'
      updated_at: '2025-08-18T15:41:47.800372Z'
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
      coding:
      - id: coding-da32c652
        created_at: '2025-08-18T15:41:47.800382Z'
        updated_at: '2025-08-18T15:41:47.800382Z'
        version: null
        identifier: []
        language: null
        implicit_rules: null
        meta_profile: []
        meta_source: null
        meta_security: []
        meta_tag: []
        resource_type: Coding
        agent_context: null
        status: active
        text: null
        contained: null
        extension: null
        modifier_extension: null
        system: http://loinc.org
        code: 85354-9
        display: Blood pressure panel with all children optional
    category:
    - id: codeableconcept-76ebad0c
      created_at: '2025-08-18T15:41:47.800431Z'
      updated_at: '2025-08-18T15:41:47.800431Z'
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
      text: null
      contained: null
      extension: null
      modifier_extension: null
      coding:
      - id: coding-f9fa7aa2
        created_at: '2025-08-18T15:41:47.800433Z'
        updated_at: '2025-08-18T15:41:47.800433Z'
        version: null
        identifier: []
        language: null
        implicit_rules: null
        meta_profile: []
        meta_source: null
        meta_security: []
        meta_tag: []
        resource_type: Coding
        agent_context: null
        status: active
        text: null
        contained: null
        extension: null
        modifier_extension: null
        system: http://terminology.hl7.org/CodeSystem/observation-category
        code: vital-signs
        display: Vital Signs
    method: null
    device: null
    subject: Patient/patient-12345
    encounter: null
    effective_date_time: '2024-01-15T10:30:00Z'
    issued: null
    performer: []
    value_quantity:
      id: quantity-80906162
      created_at: '2025-08-18T15:41:47.800401Z'
      updated_at: '2025-08-18T15:41:47.800402Z'
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
      system: http://unitsofmeasure.org
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

    ### Observation Schema

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



#### Lab Result

=== "Rendered"

    ### Observation

    | Field | Value |
    |---|---|
    | resource_type | Observation |
    | id | observation-694d1522 |
    | status | final |
    | code | Hemoglobin |
    | value.quantity | 14.2 g/dL |
    | subject | Patient/patient-67890 |
    | effective_date_time | 2024-01-15T08:45:00Z |
    | performer | [] |
    | created_at | 2025-08-18T15:41:47.800468Z |
    | updated_at | 2025-08-18T15:41:47.800468Z |

=== "JSON"

    ```json
    {
      "id": "observation-694d1522",
      "created_at": "2025-08-18T15:41:47.800468Z",
      "updated_at": "2025-08-18T15:41:47.800468Z",
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
        "id": "codeableconcept-1623e293",
        "created_at": "2025-08-18T15:41:47.800452Z",
        "updated_at": "2025-08-18T15:41:47.800452Z",
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
        "text": "Hemoglobin",
        "contained": null,
        "extension": null,
        "modifier_extension": null,
        "coding": [
          {
            "id": "coding-3036da11",
            "created_at": "2025-08-18T15:41:47.800454Z",
            "updated_at": "2025-08-18T15:41:47.800454Z",
            "version": null,
            "identifier": [],
            "language": null,
            "implicit_rules": null,
            "meta_profile": [],
            "meta_source": null,
            "meta_security": [],
            "meta_tag": [],
            "resource_type": "Coding",
            "agent_context": null,
            "status": "active",
            "text": null,
            "contained": null,
            "extension": null,
            "modifier_extension": null,
            "system": "http://loinc.org",
            "code": "718-7",
            "display": "Hemoglobin [Mass/volume] in Blood"
          }
        ]
      },
      "category": [],
      "method": null,
      "device": null,
      "subject": "Patient/patient-67890",
      "encounter": null,
      "effective_date_time": "2024-01-15T08:45:00Z",
      "issued": null,
      "performer": [],
      "value_quantity": {
        "id": "quantity-3d66d5c2",
        "created_at": "2025-08-18T15:41:47.800462Z",
        "updated_at": "2025-08-18T15:41:47.800462Z",
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
        "value": 14.2,
        "comparator": null,
        "unit": "g/dL",
        "system": "http://unitsofmeasure.org",
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
    id: observation-694d1522
    created_at: '2025-08-18T15:41:47.800468Z'
    updated_at: '2025-08-18T15:41:47.800468Z'
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
      id: codeableconcept-1623e293
      created_at: '2025-08-18T15:41:47.800452Z'
      updated_at: '2025-08-18T15:41:47.800452Z'
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
      text: Hemoglobin
      contained: null
      extension: null
      modifier_extension: null
      coding:
      - id: coding-3036da11
        created_at: '2025-08-18T15:41:47.800454Z'
        updated_at: '2025-08-18T15:41:47.800454Z'
        version: null
        identifier: []
        language: null
        implicit_rules: null
        meta_profile: []
        meta_source: null
        meta_security: []
        meta_tag: []
        resource_type: Coding
        agent_context: null
        status: active
        text: null
        contained: null
        extension: null
        modifier_extension: null
        system: http://loinc.org
        code: 718-7
        display: Hemoglobin [Mass/volume] in Blood
    category: []
    method: null
    device: null
    subject: Patient/patient-67890
    encounter: null
    effective_date_time: '2024-01-15T08:45:00Z'
    issued: null
    performer: []
    value_quantity:
      id: quantity-3d66d5c2
      created_at: '2025-08-18T15:41:47.800462Z'
      updated_at: '2025-08-18T15:41:47.800462Z'
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
      value: 14.2
      comparator: null
      unit: g/dL
      system: http://unitsofmeasure.org
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

    ### Observation Schema

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



---

## Reference

### Overview

Reference to another resource with type and display information

### Class Documentation

```
Minimal FHIR-style Reference type used to point from one resource to another.

Fields:
  - reference: Literal reference string (e.g., "Patient/123", relative/absolute URL, or internal "#id")
  - type: Type the reference refers to (e.g., "Patient")
  - identifier: Logical reference payload when literal reference is not known
  - display: Text alternative for the resource
```

### Comprehensive Examples

#### Patient Reference

=== "Rendered"

    ### Resource

    | Field | Value |
    |---|---|
    | resource_type | Resource |

=== "JSON"

    ```json
    {
      "reference": "Patient/patient-12345",
      "type": "Patient",
      "identifier": null,
      "display": "Emily Johnson"
    }
    ```

=== "YAML"

    ```yaml
    reference: Patient/patient-12345
    type: Patient
    identifier: null
    display: Emily Johnson
    
    ```

=== "Schema"

    ### Reference Schema

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



#### Practitioner Reference

=== "Rendered"

    ### Resource

    | Field | Value |
    |---|---|
    | resource_type | Resource |

=== "JSON"

    ```json
    {
      "reference": "Practitioner/dr-smith-789",
      "type": "Practitioner",
      "identifier": null,
      "display": "Dr. Robert Smith, MD"
    }
    ```

=== "YAML"

    ```yaml
    reference: Practitioner/dr-smith-789
    type: Practitioner
    identifier: null
    display: Dr. Robert Smith, MD
    
    ```

=== "Schema"

    ### Reference Schema

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



---
