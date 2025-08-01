"""
HACS Registry Definitions

Domain models for versioned healthcare resource definitions, templates, and workflows.
This module provides the schema and structure definitions for HACS resources.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Union
import inspect
import logging

from pydantic import Field

from hacs_core import BaseResource

logger = logging.getLogger(__name__)


class DefinitionStatus(str, Enum):
    """Status of a definition in the registry."""
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class ResourceDefinition(BaseResource):
    """
    Definition for a healthcare resource schema.

    This represents the schema/template for a healthcare resource type,
    defining the structure, validation rules, and metadata for HACS resources.
    """

    resource_type: str = Field(default="ResourceDefinition", description="Type identifier")

    name: str = Field(description="Human-readable name for this resource schema")
    version: str = Field(description="Semantic version (e.g., '1.0.0')")
    description: str = Field(description="Detailed description of this resource schema")

    schema_definition: Dict[str, Any] = Field(
        description="JSON Schema definition for this resource type"
    )

    status: DefinitionStatus = Field(
        default=DefinitionStatus.DRAFT,
        description="Current status of this resource schema"
    )

    category: str = Field(
        default="general",
        description="Category classification (clinical, administrative, workflow, etc.)"
    )

    tags: List[str] = Field(
        default_factory=list,
        description="Searchable tags for categorization"
    )

    author: str = Field(description="Author/organization that created this schema")

    dependencies: List[str] = Field(
        default_factory=list,
        description="List of other resource schemas this depends on"
    )

    validation_rules: List[str] = Field(
        default_factory=list,
        description="Additional validation rules beyond JSON Schema"
    )

    examples: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Example instances of this resource type"
    )

    published_at: Optional[datetime] = Field(
        default=None,
        description="When this schema was published"
    )

    deprecated_at: Optional[datetime] = Field(
        default=None,
        description="When this schema was deprecated"
    )

    def publish(self) -> None:
        """Mark this resource schema as published."""
        self.status = DefinitionStatus.PUBLISHED
        self.published_at = datetime.utcnow()

    def deprecate(self) -> None:
        """Mark this resource schema as deprecated."""
        self.status = DefinitionStatus.DEPRECATED
        self.deprecated_at = datetime.utcnow()


class PromptDefinition(BaseResource):
    """Definition for prompt templates used in healthcare AI workflows."""

    resource_type: str = Field(default="PromptDefinition", description="Type identifier")

    name: str = Field(description="Name of the prompt template")
    version: str = Field(description="Version of this prompt template")
    description: str = Field(description="Description of prompt purpose and usage")

    template: str = Field(description="The prompt template with placeholders")
    variables: List[str] = Field(
        default_factory=list,
        description="List of variable names used in the template"
    )

    use_case: str = Field(description="Primary use case for this prompt")
    category: str = Field(
        default="general",
        description="Category (assessment, diagnosis, treatment, etc.)"
    )

    tags: List[str] = Field(default_factory=list, description="Searchable tags")


class WorkflowDefinition(BaseResource):
    """Definition for healthcare workflow processes."""

    resource_type: str = Field(default="WorkflowDefinition", description="Type identifier")

    name: str = Field(description="Name of the workflow")
    version: str = Field(description="Version of this workflow")
    description: str = Field(description="Description of workflow purpose")

    steps: List[Dict[str, Any]] = Field(
        description="Ordered list of workflow steps"
    )

    inputs: List[str] = Field(
        default_factory=list,
        description="Required inputs for this workflow"
    )

    outputs: List[str] = Field(
        default_factory=list,
        description="Expected outputs from this workflow"
    )

    category: str = Field(
        default="clinical",
        description="Workflow category (clinical, administrative, etc.)"
    )

    tags: List[str] = Field(default_factory=list, description="Searchable tags")


class ToolDefinition(BaseResource):
    """
    Definition for a HACS tool with metadata and capabilities.
    
    This represents a discoverable tool that can be used by AI agents,
    with comprehensive metadata about its purpose, parameters, and usage.
    """
    
    resource_type: str = Field(default="ToolDefinition", description="Type identifier")
    
    name: str = Field(description="Tool name (must be unique)")
    version: str = Field(default="1.0.0", description="Tool version")
    description: str = Field(description="Human-readable description of tool purpose")
    
    # Tool function and execution
    function: Optional[Callable] = Field(
        default=None,
        description="The actual tool function (not serialized)",
        exclude=True
    )
    
    module_path: str = Field(description="Full module path where tool is defined")
    function_name: str = Field(description="Name of the function")
    
    # Categorization and discovery
    category: str = Field(
        description="Primary category (resource_management, clinical_workflows, etc.)"
    )
    
    domain: str = Field(
        description="Domain module where tool is defined"
    )
    
    tags: List[str] = Field(
        default_factory=list,
        description="Searchable tags for categorization"
    )
    
    # Tool metadata
    input_schema: Optional[Dict[str, Any]] = Field(
        default=None,
        description="JSON schema for tool inputs"
    )
    
    output_schema: Optional[Dict[str, Any]] = Field(
        default=None,
        description="JSON schema for tool outputs"
    )
    
    # Usage and capabilities
    requires_actor: bool = Field(
        default=False,
        description="Whether tool requires actor_name parameter"
    )
    
    requires_db: bool = Field(
        default=False,
        description="Whether tool requires database adapter"
    )
    
    requires_vector_store: bool = Field(
        default=False,
        description="Whether tool requires vector store"
    )
    
    is_async: bool = Field(
        default=False,
        description="Whether tool function is async"
    )
    
    # Documentation and examples
    examples: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Usage examples with inputs and expected outputs"
    )
    
    use_cases: List[str] = Field(
        default_factory=list,
        description="Common use cases for this tool"
    )
    
    # Framework compatibility
    supports_langchain: bool = Field(
        default=True,
        description="Whether tool can be used with LangChain"
    )
    
    supports_mcp: bool = Field(
        default=True,
        description="Whether tool can be used with MCP"
    )
    
    # Status and lifecycle
    status: DefinitionStatus = Field(
        default=DefinitionStatus.PUBLISHED,
        description="Current status of this tool"
    )
    
    deprecated_in_favor_of: Optional[str] = Field(
        default=None,
        description="Name of replacement tool if deprecated"
    )
    
    def get_signature(self) -> Optional[inspect.Signature]:
        """Get the function signature if function is available."""
        if self.function:
            return inspect.signature(self.function)
        return None
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get parameter information from function signature."""
        if not self.function:
            return {}
        
        sig = inspect.signature(self.function)
        params = {}
        
        for name, param in sig.parameters.items():
            param_info = {
                "name": name,
                "required": param.default == inspect.Parameter.empty,
                "default": param.default if param.default != inspect.Parameter.empty else None,
                "annotation": str(param.annotation) if param.annotation != inspect.Parameter.empty else None
            }
            params[name] = param_info
        
        return params
    
    def is_compatible_with(self, framework: str) -> bool:
        """Check if tool is compatible with a specific framework."""
        framework_lower = framework.lower()
        if framework_lower == "langchain":
            return self.supports_langchain
        elif framework_lower == "mcp":
            return self.supports_mcp
        return True
    
    class Config:
        arbitrary_types_allowed = True


# Backwards compatibility alias
ModelDefinition = ResourceDefinition
