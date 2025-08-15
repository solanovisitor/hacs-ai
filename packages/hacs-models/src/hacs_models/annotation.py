from __future__ import annotations

from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum
from uuid import uuid4

from .base_resource import BaseResource
from .types import DocumentStatus, DocumentType, ConfidentialityLevel
from .composition import (
    Composition as _Composition,
    CompositionAuthor as _CompositionAuthor,
    CompositionAttester as _CompositionAttester,
    CompositionSection as _CompositionSection,
    CompositionEncounter as _CompositionEncounter,
)


class PromptTemplateResource(BaseResource):
    """Registry-registered prompt template for annotation workflows.

    Stores the raw template text and metadata needed to render prompts.
    """

    resource_type: Literal["PromptTemplateResource"] = Field(
        default="PromptTemplateResource"
    )
    name: str = Field(description="Template name")
    version: str = Field(default="1.0.0", description="Template version")
    template_text: str = Field(description="Template text with variables")
    variables: List[str] = Field(
        default_factory=list, description="Variable names used by the template"
    )
    format: Literal["json", "yaml"] = Field(default="json")
    fenced_output: bool = Field(
        default=True, description="Whether model should return fenced code output"
    )


class ExtractionSchemaResource(BaseResource):
    """Registry-registered schema describing the LLM structured output."""

    resource_type: Literal["ExtractionSchemaResource"] = Field(
        default="ExtractionSchemaResource"
    )
    name: str = Field(description="Schema name")
    version: str = Field(default="1.0.0", description="Schema version")
    response_schema: Dict[str, Any] = Field(
        description="JSON Schema describing expected LLM output"
    )


class TransformSpec(BaseModel):
    """Declarative transform to apply to a source value before assignment."""

    id: str = Field(description="Transform identifier")
    params: Dict[str, Any] = Field(default_factory=dict)


class SourceBinding(BaseModel):
    """Binding from LLM output or variables into a target field path.

    One of:
    - from: JSONPath-like path (e.g., $.patient.full_name)
    - var: variable name coming from the prompt/template variables
    """

    from_: Optional[str] = Field(default=None, alias="from")
    var: Optional[str] = None
    transform: Optional[TransformSpec] = None
    required: bool = Field(default=False)


class OutputSpec(BaseModel):
    """Defines one output operation (resource or stack instantiation)."""

    resource: str = Field(
        description="Target resource name (e.g., Patient, Observation, StackTemplate)"
    )
    operation: Literal["create", "update", "upsert", "instantiate"] = Field(
        default="create"
    )
    match: Dict[str, Any] | None = Field(
        default=None, description="Criteria to identify existing resource for update/upsert"
    )
    fields: Dict[str, SourceBinding] = Field(
        default_factory=dict, description="Target field path -> binding"
    )
    links: Dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Late-binding references to previously created outputs,"
            " e.g., subject.reference: 'Patient/${Patient.id}'"
        ),
    )


class MappingSpec(BaseModel):
    """Declarative mapping from LLM output to HACS resources or StackTemplate vars."""

    outputs: List[OutputSpec] = Field(default_factory=list)


class ChunkingPolicy(BaseModel):
    """Chunking policy for large inputs."""

    strategy: Literal[
        "char",
        "token",
        "recursive",
        "markdown",
        "html",
        "code",
        "semantic",
    ] = Field(default="char")
    max_chars: int = Field(default=4000)
    chunk_overlap: int = Field(default=0)
    sentence_aware: bool = Field(default=True)
    fenced_output: bool = Field(default=True)
    encoding_name: Optional[str] = Field(default=None, description="tiktoken encoding name for token-based splitters")


class ModelConfig(BaseModel):
    """LLM model configuration."""

    provider: Literal["openai", "anthropic", "auto"] = Field(default="auto")
    model: str = Field(default="gpt-4o-mini")
    temperature: float = Field(default=0.3)
    max_tokens: Optional[int] = None


class PersistencePolicy(BaseModel):
    """Persistence behavior for workflow outputs."""

    save: bool = Field(default=False)
    as_bundle: bool = Field(default=True, description="Persist as ResourceBundle")
    database_url: Optional[str] = None


class AnnotationWorkflowResource(BaseResource):
    """Registry-registered annotation workflow.

    Binds prompt template + extraction schema + mapping spec and policies.
    """

    resource_type: Literal["AnnotationWorkflowResource"] = Field(
        default="AnnotationWorkflowResource"
    )
    name: str = Field(description="Workflow name")
    version: str = Field(default="1.0.0")
    prompt_template_ref: str = Field(
        description="Reference to PromptTemplateResource (name:version)"
    )
    extraction_schema_ref: str = Field(
        description="Reference to ExtractionSchemaResource (name:version)"
    )
    chunking_policy: ChunkingPolicy = Field(default_factory=ChunkingPolicy)
    llm_config: ModelConfig = Field(default_factory=ModelConfig)
    mapping_spec: MappingSpec = Field(default_factory=MappingSpec)
    persistence_policy: PersistencePolicy = Field(default_factory=PersistencePolicy)
    stack_template_ref: Optional[str] = Field(
        default=None, description="Optional reference to a StackTemplate (name:version)"
    )



class TextChunk(BaseModel):
    """Abstract representation of a chunk of text within a document.

    Utilities in hacs-utils compute the text and do splitting; this model only
    carries positional metadata so it can be serialized and referenced.
    """

    resource_type: Literal["TextChunk"] = Field(default="TextChunk")
    start_pos: int = Field(description="Start character position (inclusive)")
    end_pos: int = Field(description="End character position (exclusive)")
    document_id: Optional[str] = Field(default=None, description="Source document ID")
    additional_context: Optional[str] = Field(default=None, description="Optional prompt context")
    token_start_idx: Optional[int] = Field(default=None, description="Start token index if tokenization used")
    token_end_idx: Optional[int] = Field(default=None, description="End token index (exclusive) if tokenization used")
    chunk_index: Optional[int] = Field(default=None, description="Sequential chunk index")


class AlignmentStatus(str, Enum):
    MATCH_EXACT = "match_exact"
    MATCH_GREATER = "match_greater"
    MATCH_LESSER = "match_lesser"
    MATCH_FUZZY = "match_fuzzy"


class CharInterval(BaseModel):
    start_pos: Optional[int] = None
    end_pos: Optional[int] = None


class Extraction(BaseModel):
    extraction_class: str
    extraction_text: str
    char_interval: Optional[CharInterval] = None
    alignment_status: Optional[AlignmentStatus] = None
    extraction_index: Optional[int] = None
    group_index: Optional[int] = None
    description: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None


class FormatType(str, Enum):
    YAML = "yaml"
    JSON = "json"


class Document(_Composition):
    text: str = Field(default="")
    additional_context: Optional[str] = None
    document_id: str = Field(default_factory=lambda: f"doc_{uuid4().hex[:8]}")
    document_identifier: Optional[str] = Field(default_factory=lambda: f"doc-{uuid4().hex[:8]}")

    # Minimal helpers expected by tests (no-op implementations where applicable)
    def add_section(self, title: str, text: str, code: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        super().add_section(title=title, text=text, code=code, metadata=metadata)

    def add_author(self, name: str, role: Optional[str] = None, organization: Optional[str] = None, specialty: Optional[str] = None) -> None:
        super().add_author(name=name, role=role, organization=organization, specialty=specialty)

    # Compatibility aliases for tests
    @property
    def DocumentAuthor(self):  # pragma: no cover
        return getattr(self, "authors", [])

    def add_attester(self, mode: str, party_name: str, party_id: str, organization: Optional[str] = None, signature: Optional[str] = None) -> None:
        super().add_attester(mode=mode, party_name=party_name, party_id=party_id, organization=organization, signature=signature)

    def get_full_text(self) -> str:
        parts = [f"Document: {self.title}" if getattr(self, "title", None) else "Document"]
        if getattr(self, "subject_name", None):
            parts.append(f"Subject: {self.subject_name}")
        if hasattr(self, "authors") and self.authors:
            parts.append(f"Authors: {', '.join(a.name for a in self.authors if getattr(a, 'name', None))}")
        if hasattr(self, "sections"):
            for s in self.sections:
                parts.append(s.title)
                parts.append(s.text)
        return "\n".join(parts)

    def get_section_by_title(self, title: str):
        for s in getattr(self, "sections", []):
            if s.title == title:
                return s
        return None

    def get_sections_by_code(self, code: str):
        return [s for s in getattr(self, "sections", []) if getattr(s, "code", None) == code]

    def get_word_count(self) -> int:
        text = " ".join([getattr(self, "text", "")] + [getattr(s, "text", "") for s in getattr(self, "sections", [])])
        return len([w for w in text.split() if w])

    def get_content_hash(self) -> str:
        import hashlib
        canonical = (self.title or "") + "\n" + "\n".join([getattr(s, "text", "") for s in getattr(self, "sections", [])])
        return hashlib.md5(canonical.encode()).hexdigest()


# ----------------------------------------------------------------------------
# FHIR-aligned minimal composition types (compatibility)
# ----------------------------------------------------------------------------

class DocumentAuthor(BaseModel):
    name: str
    role: Optional[str] = None
    organization: Optional[str] = None
    specialty: Optional[str] = None


class DocumentAttester(BaseModel):
    mode: Literal["professional", "legal", "official", "personal"] = "professional"
    party_name: Optional[str] = None
    party_id: Optional[str] = None
    organization: Optional[str] = None
    signature: Optional[str] = None


class DocumentSection(BaseModel):
    title: str
    text: str
    code: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentEncounter(BaseModel):
    encounter_id: Optional[str] = None
    encounter_reference: Optional[str] = None


# ----------------------------------------------------------------------------
# Minimal factory helpers for tests
# ----------------------------------------------------------------------------

def create_progress_note(title: str = "Progress Note", subject_id: Optional[str] = None, subject_name: Optional[str] = None) -> Document:
    return Document(
        document_type=DocumentType.PROGRESS_NOTE,
        title=title,
        subject_id=subject_id,
        subject_name=subject_name,
        status=DocumentStatus.PRELIMINARY,
    )


def create_discharge_summary(title: str = "Discharge Summary", subject_id: Optional[str] = None, subject_name: Optional[str] = None) -> Document:
    return Document(
        document_type=DocumentType.DISCHARGE_SUMMARY,
        title=title,
        subject_id=subject_id,
        subject_name=subject_name,
        status=DocumentStatus.FINAL,
    )


def create_consultation_note(title: str = "Consultation Note", subject_id: Optional[str] = None, subject_name: Optional[str] = None) -> Document:
    return Document(
        document_type=DocumentType.CONSULTATION_NOTE,
        title=title,
        subject_id=subject_id,
        subject_name=subject_name,
        status=DocumentStatus.PRELIMINARY,
    )


def create_clinical_summary(title: str = "Clinical Summary", subject_id: Optional[str] = None, subject_name: Optional[str] = None) -> Document:
    return Document(
        document_type=DocumentType.CLINICAL_SUMMARY,
        title=title,
        subject_id=subject_id,
        subject_name=subject_name,
        status=DocumentStatus.FINAL,
    )


class AnnotatedDocument(BaseModel):
    document_id: str = Field(default_factory=lambda: f"doc_{uuid4().hex[:8]}")
    extractions: Optional[List[Extraction]] = None
    text: Optional[str] = None
