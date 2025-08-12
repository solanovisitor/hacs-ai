from __future__ import annotations

from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field

from .base_resource import BaseResource


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

    max_chars: int = Field(default=4000)
    sentence_aware: bool = Field(default=True)
    fenced_output: bool = Field(default=True)


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
    model_config: ModelConfig = Field(default_factory=ModelConfig)
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
