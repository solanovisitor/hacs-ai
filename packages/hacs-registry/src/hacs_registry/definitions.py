"""
HACS Registry Definitions

Domain models for versioned healthcare resource definitions, templates, and workflows.
This module provides the schema and structure definitions for HACS resources.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field

from hacs_core import BaseResource


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


# Backwards compatibility alias
ModelDefinition = ResourceDefinition
