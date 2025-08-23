"""
Base resource model for all HACS healthcare models.

This module provides the foundational BaseResource and DomainResource classes
that all HACS models inherit from. Designed for world-class development quality
with full type safety,validation, and AI-optimized features.

Key Features:
    - Automatic ID generation with smart defaults
    - Timestamp management (created_at, updated_at)
    - Type-safe field validation with Pydantic v2
    - JSON Schema generation with examples
    - Subset model creation with pick() method
    - FHIR-compliant base structure
    - Performance optimized for AI agent communication

Design Principles:
    - Pure data models (no business logic)
    - Immutable by design (use copy() for updates)
    - Rich type annotations for perfect IDE support
    -docstrings for maintainability
    - Zero external dependencies beyond Pydantic
"""

import inspect
import uuid
from datetime import UTC, datetime
from typing import Any, ClassVar, TypeVar

from pydantic import BaseModel, ConfigDict, Field, create_model

# Import protocols (interfaces only, not implementations) to avoid circular imports
try:
    from hacs_core.protocols import (
        ClinicalResource,
        Identifiable,
        Serializable,
        Timestamped,
        Validatable,
        Versioned,
    )

    _has_protocols = True
except ImportError:
    # Create dummy protocols for standalone usage
    _has_protocols = False
    from typing import Protocol, runtime_checkable

    @runtime_checkable
    class Identifiable(Protocol):
        @property
        def id(self) -> str: ...

    @runtime_checkable
    class Timestamped(Protocol):
        @property
        def created_at(self) -> datetime: ...
        @property
        def updated_at(self) -> datetime: ...

    @runtime_checkable
    class Versioned(Protocol):
        @property
        def version(self) -> str: ...

    @runtime_checkable
    class Serializable(Protocol):
        def to_dict(self) -> dict: ...
        @classmethod
        def from_dict(cls, data: dict): ...

    @runtime_checkable
    class Validatable(Protocol):
        def validate(self) -> list: ...
        def is_valid(self) -> bool: ...

    @runtime_checkable
    class ClinicalResource(Protocol):
        @property
        def resource_type(self) -> str: ...
        @property
        def status(self) -> str: ...
        def get_patient_id(self) -> str | None: ...


# Type variable for generic base resource operations
T = TypeVar("T", bound="BaseResource")


class CharInterval(BaseModel):
    """Character interval in source text for grounding."""

    start_pos: int | None = Field(default=None, description="Start character index")
    end_pos: int | None = Field(default=None, description="End character index (exclusive)")


class AgentMeta(BaseModel):
    """
    Standardized agent-derived metadata for reasoning and provenance.

    Keep this focused and typed; use agent_context for app-specific payloads.
    """

    reasoning: str | None = Field(default=None, description="LLM reasoning or justification text")
    citations: list[str] | None = Field(default=None, description="Evidence snippets")
    char_intervals: list[CharInterval] | None = Field(
        default=None, description="Character spans of evidence in source text"
    )
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    model_id: str | None = Field(default=None, description="Model identifier used")
    provider: str | None = Field(default=None, description="Provider name")
    generated_at: datetime | None = Field(default=None, description="Generation timestamp")
    recipe_id: str | None = Field(default=None, description="Extraction recipe identifier")
    window_ids: list[str] | None = Field(default=None, description="IDs of windows used")


class BaseResource(BaseModel):
    """
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
    """

    # Pydantic v2 configuration for optimal performance and validation
    model_config = ConfigDict(
        # Core validation settings
        validate_assignment=True,  # Validate on field assignment
        validate_default=True,  # Validate default values
        use_enum_values=True,  # Serialize enums as values
        # Performance optimizations
        extra="forbid",  # Strict field validation (world-class quality)
        frozen=False,  # Allow field updates for timestamps
        str_strip_whitespace=True,  # Auto-strip whitespace
        # Developer experience
        arbitrary_types_allowed=False,  # Strict type checking
        # JSON Schema generation
        json_schema_extra={
            "examples": [
                {
                    "id": "resource-a1b2c3d4",
                    "resource_type": "BaseResource",
                    "created_at": "2024-08-03T12:00:00Z",
                    "updated_at": "2024-08-03T12:00:00Z",
                    "language": "pt-BR",
                    "meta_profile": ["http://example.org/fhir/StructureDefinition/MyProfile"],
                    "meta_tag": ["llm-context", "summary"],
                }
            ],
            "title": "Base Healthcare Resource",
            "description": "Foundation for all HACS healthcare data models with FHIR-inspired identity and metadata for LLM context engineering",
        },
    )

    # Protocol Implementation Fields

    # Identifiable protocol
    id: str | None = Field(
        default=None,  # Will be set in model_post_init
        description="Unique identifier for this resource. Auto-generated if not provided.",
        min_length=1,
        max_length=64,
    )

    # Timestamped protocol
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="ISO 8601 timestamp when this resource was created",
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="ISO 8601 timestamp when this resource was last updated",
    )

    # Versioned protocol
    version: str = Field(
        default="1.0.0",
        description="Version of the resource",
        pattern=r"^\d+\.\d+\.\d+$",
    )

    # FHIR Resource-level identity and metadata (for rich context engineering)
    identifier: list[str] = Field(
        default_factory=list,
        description="External identifiers for the resource (e.g., MRN, accession, system-specific IDs)",
        examples=[["MRN:12345", "local:abc-001"]],
    )

    language: str | None = Field(
        default=None,
        description="Base language of the resource content (BCP-47, e.g., en, pt-BR)",
        examples=["en", "pt-BR"],
    )

    implicit_rules: str | None = Field(
        default=None,
        description="Reference to rules followed when constructing the resource (URI)",
        examples=["http://example.org/implicit-rules/v1"],
    )

    meta_profile: list[str] = Field(
        default_factory=list,
        description="Profiles asserting conformance of this resource (URIs)",
        examples=[["http://hl7.org/fhir/StructureDefinition/Observation"]],
    )

    meta_source: str | None = Field(
        default=None,
        description="Source system that produced the resource",
        examples=["ehr-system-x"],
    )

    meta_security: list[str] = Field(
        default_factory=list,
        description="Security labels applicable to this resource (policy/label codes)",
        examples=[["very-sensitive", "phi"]],
    )

    meta_tag: list[str] = Field(
        default_factory=list,
        description="User or system-defined tags for search and grouping",
        examples=[["triage", "llm-context", "draft"]],
    )

    # Resource type field (required for all resources)
    resource_type: str = Field(
        description="Type identifier for this resource (Patient, Observation, etc.)",
        examples=["Patient", "Observation", "MemoryBlock", "WorkflowDefinition"],
        min_length=1,
        max_length=50,
    )

    # Generic agent context for free-form annotations or LLM-structured data
    agent_context: dict[str, Any] | None = Field(
        default=None,
        description="Arbitrary, agent-provided context payload for this resource",
        examples=[{"section_key": "free text content"}],
    )

    # Standardized, typed agent metadata
    agent_meta: AgentMeta | None = Field(
        default=None, description="Standardized agent reasoning, citations and provenance"
    )

    # Class-level metadata for introspection
    _hacs_version: ClassVar[str] = "0.1.0"
    _fhir_version: ClassVar[str | None] = None  # Override in FHIR resources

    # Optional documentation metadata (class-level), for agent discovery and registry overrides
    _doc_scope_usage: ClassVar[str | None] = None
    _doc_boundaries: ClassVar[str | None] = None
    _doc_relationships: ClassVar[list[str]] = []
    _doc_references: ClassVar[list[str]] = []
    _doc_tools: ClassVar[list[str]] = []
    _doc_examples: ClassVar[list[dict[str, Any]]] = []
    # Canonical defaults used for extraction prompts and fallbacks
    _canonical_defaults: ClassVar[dict[str, Any]] = {}

    def model_post_init(self, __context: Any) -> None:
        """
        Post-initialization hook for auto-generation of required fields.

        Called automatically after model creation to set:
        - Auto-generated ID if not provided
        - Resource-type prefix for ID clarity

        Args:
            __context: Pydantic validation context (unused)
        """
        # Generate ID with resource-type prefix for clarity
        if self.id is None:
            resource_prefix = self.resource_type.lower().replace(" ", "-")
            unique_suffix = str(uuid.uuid4())[:8]
            self.id = f"{resource_prefix}-{unique_suffix}"

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp to current time."""
        self.updated_at = datetime.now(UTC)

    # Serializable protocol methods
    def to_dict(self) -> dict[str, Any]:
        """Convert object to dictionary representation."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaseResource":
        """Create object from dictionary representation."""
        return cls(**data)

    # Validatable protocol methods
    def validate(self) -> list[str]:
        """Validate the object and return list of errors."""
        try:
            self.model_validate(self.model_dump())
            return []
        except Exception as e:
            return [str(e)]

    def is_valid(self) -> bool:
        """Check if the object is valid."""
        return len(self.validate()) == 0

    def is_newer_than(self, other: "BaseResource") -> bool:
        """
        Compare timestamps to determine if this resource is newer.

        Args:
            other: Another BaseResource to compare against

        Returns:
            True if this resource was updated more recently

        Example:
            >>> resource1 = MyResource(resource_type="Test", name="first")
            >>> # ... time passes ...
            >>> resource2 = MyResource(resource_type="Test", name="second")
            >>> resource2.is_newer_than(resource1)  # True
        """
        if self.updated_at is None or other.updated_at is None:
            return False
        return self.updated_at > other.updated_at

    @classmethod
    def pick(cls: type[T], *fields: str) -> type[T]:
        """
        Create a subset Pydantic model containing only specified fields.

        - Always includes essentials: id, resource_type, created_at, updated_at
        - Allows extra fields (extensions) on the subset for forward-compatibility
        - Uses the original field annotations and defaults where available

        Returns a new Pydantic model class suitable for schema generation and validation
        of lightweight payloads (e.g., prompts, APIs).
        """
        from pydantic import ConfigDict as PydConfig
        from pydantic import Field as PydField

        essential_fields = {"id", "resource_type", "created_at", "updated_at"}
        selected_fields = set(fields) | essential_fields

        new_fields: dict[str, tuple[Any, Any]] = {}
        original_fields = getattr(cls, "model_fields", {})

        for name in selected_fields:
            if name not in original_fields:
                continue
            f = original_fields[name]
            annotation = getattr(f, "annotation", Any) or Any
            # Determine default: required (ellipsis), explicit default, or default_factory
            default: Any
            try:
                if getattr(f, "default_factory", None) is not None:
                    default = PydField(
                        default_factory=f.default_factory,
                        description=getattr(f, "description", None),
                    )
                elif getattr(f, "is_required", False):
                    # Auto-generate id for subsets; keep resource_type default if present
                    if name == "id":
                        default = PydField(
                            default=None, description=getattr(f, "description", None)
                        )
                    else:
                        default = ...
                else:
                    default = getattr(f, "default", None)
            except Exception:
                default = getattr(f, "default", None)
            new_fields[name] = (annotation, default)

        # Subset config: allow extras to support extensions while keeping other defaults sane
        subset_config = PydConfig(extra="allow")

        subset_model = create_model(
            f"{cls.__name__}Subset",
            __config__=subset_config,
            **new_fields,
        )

        return subset_model  # type: ignore[return-value]

    def get_age_days(self) -> float | None:
        """
        Calculate age of this resource in days since creation.

        Returns:
            Number of days since created_at, or None if no creation time

        Example:
            >>> resource = MyResource(resource_type="Test")
            >>> # ... some time later ...
            >>> age = resource.get_age_days()  # e.g., 1.5 days
        """
        if self.created_at is None:
            return None

        now = datetime.now(UTC)
        delta = now - self.created_at
        return delta.total_seconds() / 86400  # Convert seconds to days

    def to_reference(self) -> str:
        """
        Create a FHIR-style reference string for this resource.

        Returns:
            Reference string in format "ResourceType/id"

        Example:
            >>> patient = Patient(resource_type="Patient", full_name="John Doe")
            >>> ref = patient.to_reference()  # "Patient/patient-a1b2c3d4"
        """
        return f"{self.resource_type}/{self.id}"

    @classmethod
    def get_descriptive_schema(cls) -> dict[str, Any]:
        """
        Lightweight descriptive schema for LLM orchestration and MCP discovery.

        Returns a dict containing title, docstring summary, and field descriptions.
        """
        try:
            doc = inspect.getdoc(cls) or ""
        except Exception:
            doc = ""
        fields: dict[str, Any] = {}
        try:
            for name, field in getattr(cls, "model_fields", {}).items():
                info: dict[str, Any] = {
                    "type": str(getattr(field, "annotation", "")),
                    "description": getattr(field, "description", None),
                    "examples": getattr(field, "examples", None),
                }
                # Enums / Literals → list allowed values
                try:
                    from enum import Enum
                    from typing import get_args, get_origin

                    ann = getattr(field, "annotation", None)
                    if ann is not None:
                        if get_origin(ann) is Literal:  # type: ignore[name-defined]
                            info["enum_values"] = list(get_args(ann))
                        elif isinstance(ann, type) and issubclass(ann, Enum):
                            info["enum_values"] = [getattr(e, "value", e) for e in list(ann)]
                except Exception:
                    pass
                fields[name] = info
        except Exception:
            pass
        # Required fields from JSON schema when available
        try:
            required = list((cls.model_json_schema() or {}).get("required", []) or [])
        except Exception:
            required = []
        return {
            "title": cls.__name__,
            "description": doc,
            "fields": fields,
            "required": required,
            "canonical_defaults": cls.get_canonical_defaults(),
        }

    # --- LLM-facing facades and helpers ---
    @classmethod
    def get_system_fields(cls) -> list[str]:
        """Return fields considered system-owned (not LLM-generated)."""
        return [
            "id",
            "created_at",
            "updated_at",
            "version",
            "identifier",
            "language",
            "implicit_rules",
            "meta_profile",
            "meta_source",
            "meta_security",
            "meta_tag",
        ]

    @classmethod
    def get_extractable_fields(cls) -> list[str]:
        """Default extractable fields for LLM extraction (override in subclasses)."""
        system = set(cls.get_system_fields())
        # Exclude internals, agent containers, and frozen resource_type by default
        excluded = system | {"agent_context", "agent_meta", "resource_type"}
        fields: list[str] = []
        try:
            for name in getattr(cls, "model_fields", {}) or {}:
                if name.startswith("_"):
                    continue
                if name in excluded:
                    continue
                fields.append(name)
        except Exception:
            pass
        return fields

    @classmethod
    def get_llm_schema(cls, minimal: bool = True) -> dict[str, Any]:
        """LLM-friendly schema with a compact example of extractable fields."""
        example: dict[str, Any] = {"resource_type": getattr(cls, "__name__", "Resource")}
        try:
            defaults = cls.get_canonical_defaults() or {}
            extractable = set(cls.get_extractable_fields())
            # Seed with defaults that intersect extractables
            for k, v in defaults.items():
                if k in extractable and v is not None:
                    example[k] = v
        except Exception:
            pass
        # Keep minimal nested structure if available from extraction examples
        try:
            examples = cls.get_extraction_examples() or {}
            obj = examples.get("object")
            if isinstance(obj, dict):
                for k in list(obj.keys()):
                    if k in ("resource_type",) or k in extractable:
                        example.setdefault(k, obj[k])
        except Exception:
            pass
        return {"title": getattr(cls, "__name__", "Resource"), "example": example}

    @classmethod
    def llm_hints(cls) -> list[str]:
        """Resource-specific guidance for extraction prompts."""
        return []

    @classmethod
    def get_required_extractables(cls) -> list[str]:
        """Fields that must be provided for valid extraction (override in subclasses)."""
        return []

    @classmethod
    def get_canonical_defaults(cls) -> dict[str, Any]:
        """Default values for system/required fields during extraction (override in subclasses)."""
        return {}

    @classmethod
    def coerce_extractable(cls, payload: dict[str, Any], relax: bool = True) -> dict[str, Any]:
        """Coerce extractable payload to proper types with relaxed validation (override in subclasses)."""
        return payload.copy()

    def to_facade(self, view: str = "full") -> dict[str, Any]:
        """Return a dict view of the resource for a given facade.

        - full: model_dump()
        - system: only system fields
        - extractable: only extractable fields (+ resource_type)
        """
        data = self.model_dump()
        if view == "full":
            return data
        if view == "system":
            keys = set(self.get_system_fields()) | {"resource_type"}
            return {k: v for k, v in data.items() if k in keys}
        if view == "extractable":
            keys = set(self.get_extractable_fields()) | {"resource_type"}
            return {k: v for k, v in data.items() if k in keys}
        return data

    @classmethod
    def validate_extractable(cls: type[T], payload: dict[str, Any]) -> T:
        """Validate a minimal extractable payload into a full model instance.

        - Filters unknown keys
        - Seeds canonical defaults
        - Injects resource_type if missing
        """
        filtered: dict[str, Any] = {}
        try:
            model_fields = getattr(cls, "model_fields", {}) or {}
            for k, v in (payload or {}).items():
                if k in model_fields:
                    filtered[k] = v
        except Exception:
            filtered = dict(payload or {})
        # Resource type
        filtered.setdefault("resource_type", getattr(cls, "__name__", "Resource"))
        # Seed defaults
        try:
            defaults = cls.get_canonical_defaults() or {}
            for k, v in defaults.items():
                filtered.setdefault(k, v)
        except Exception:
            pass
        return cls(**filtered)

    @classmethod
    def get_specifications(cls, language: str | None = None) -> dict[str, Any]:
        """
        Return a structured definition for agents and registries, including docs and field schema.
        Language parameter reserved for future localization via registry overrides.
        """
        base = cls.get_descriptive_schema()
        docs = {
            "scope_usage": cls._doc_scope_usage,
            "boundaries": cls._doc_boundaries,
            "relationships": list(cls._doc_relationships or []),
            "references": list(cls._doc_references or []),
            "tools": list(cls._doc_tools or []),
            "examples": list(cls._doc_examples or []),
        }
        base["documentation"] = docs
        if language:
            base["language"] = language
        return base

    # --- Canonical defaults and extraction examples ---
    @classmethod
    def get_canonical_defaults(cls) -> dict[str, Any]:
        """Return canonical defaults for extraction and fallback seeding."""
        try:
            return dict(cls._canonical_defaults or {})
        except Exception:
            return {}

    @classmethod
    def get_extraction_examples(cls) -> dict[str, Any]:
        """Return minimal extraction examples: object and array forms.

        The object form is a minimal JSON-like dict using canonical defaults
        and resource_type; the array form is a single-element list.
        """
        example_obj: dict[str, Any] = {"resource_type": getattr(cls, "__name__", "Resource")}
        try:
            example_obj.update(
                {k: v for k, v in cls.get_canonical_defaults().items() if v is not None}
            )
        except Exception:
            pass
        return {"object": example_obj, "array": [example_obj]}

    def __str__(self) -> str:
        """
        Human-readable string representation.

        Returns:
            Simple string showing resource type and ID
        """
        return f"{self.resource_type}(id={self.id})"

    def __repr__(self) -> str:
        """
        Developer-friendly detailed representation.

        Shows up to 5 most important fields with values,
        truncating long strings for readability.
        """
        field_strs = []

        # Always show essential fields first
        essential_order = ["id", "resource_type", "created_at", "updated_at"]
        other_fields = [f for f in self.model_fields if f not in essential_order]
        ordered_fields = essential_order + other_fields

        for field_name in ordered_fields:
            value = getattr(self, field_name, None)
            if value is not None:
                # Truncate long values for readability
                if isinstance(value, str) and len(value) > 40:
                    value = f"{value[:37]}..."
                elif isinstance(value, datetime):
                    value = value.isoformat()

                # Shorten common field names
                display_name = field_name
                if field_name == "created_at":
                    display_name = "created"
                elif field_name == "updated_at":
                    display_name = "updated"
                elif field_name == "resource_type":
                    display_name = "type"

                field_strs.append(f"{display_name}={value!r}")

        # Show max 5 fields to keep repr concise
        fields_display = ", ".join(field_strs[:5])
        if len(field_strs) > 5:
            fields_display += f", +{len(field_strs) - 5} more"

        return f"{self.__class__.__name__}({fields_display})"


class DomainResource(BaseResource):
    """
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
    """

    # Clinical resource status (implements ClinicalResource protocol)
    status: str = Field(
        default="active",
        description="Current status of the resource",
        examples=["active", "inactive", "draft", "entered-in-error"],
    )

    # FHIR DomainResource fields
    text: str | None = Field(
        default=None,
        description="Human-readable summary of the resource content",
        examples=["Patient John Doe, 45 years old", "Blood pressure reading: 120/80 mmHg"],
        max_length=2048,
    )

    contained: list[BaseResource] | None = Field(
        default=None,
        description="Resources contained within this resource",
        examples=[],
    )

    # Extension support for additional data
    extension: dict[str, Any] | None = Field(
        default=None,
        description="Additional content defined by implementations",
        examples=[{"url": "custom-field", "valueString": "custom-value"}],
    )

    modifier_extension: dict[str, Any] | None = Field(
        default=None,
        description="Extensions that cannot be ignored",
        examples=[{"url": "critical-field", "valueBoolean": True}],
    )

    # Override FHIR version for domain resources
    _fhir_version: ClassVar[str] = "R4"

    def summary(self) -> str:
        """
        Get or generate a human-readable text summary.

        Returns the explicit text field if set, otherwise generates
        a basic summary from the resource type and ID.

        Returns:
            Human-readable summary string
        """
        if self.text:
            return self.text
        return f"{self.resource_type} {self.id}"

    def add_extension(self, url: str, value: Any) -> None:
        """
        Add an extension to this resource.

        Args:
            url: Extension URL/identifier
            value: Extension value

        Example:
            >>> resource.add_extension("custom-flag", True)
        """
        if self.extension is None:
            self.extension = {}
        self.extension[url] = value
        self.update_timestamp()

    def get_extension(self, url: str) -> Any | None:
        """
        Get an extension value by URL.

        Args:
            url: Extension URL/identifier

        Returns:
            Extension value or None if not found
        """
        if self.extension is None:
            return None
        return self.extension.get(url)

    def has_extension(self, url: str) -> bool:
        """
        Check if an extension exists.

        Args:
            url: Extension URL/identifier

        Returns:
            True if extension exists
        """
        return self.extension is not None and url in self.extension

    def get_patient_id(self) -> str | None:
        """
        Get the patient ID associated with this resource.

        Implements the ClinicalResource protocol method. Default implementation
        looks for common patient reference patterns. Override in subclasses
        for resource-specific logic.

        Returns:
            Patient ID if found, None otherwise
        """
        # Check for direct patient_id field
        if hasattr(self, "patient_id"):
            return self.patient_id

        # Check for subject field (common in FHIR resources)
        if hasattr(self, "subject"):
            subject = self.subject
            if hasattr(subject, "id"):
                return subject.id
            elif isinstance(subject, str):
                return subject

        # Check for patient field
        if hasattr(self, "patient"):
            patient = self.patient
            if hasattr(patient, "id"):
                return patient.id
            elif isinstance(patient, str):
                return patient

        return None
