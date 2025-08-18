from __future__ import annotations

from typing import Optional, List, Literal
from pydantic import Field

from .base_resource import DomainResource


class GraphDefinitionLinkTarget(DomainResource):
    resource_type: Literal["GraphDefinitionLinkTarget"] = Field(default="GraphDefinitionLinkTarget")
    type: str = Field(description="Type of resource this link points to (e.g., 'Patient')")
    params: Optional[str] = Field(default=None, description="Criteria (search parameters) for the target")


class GraphDefinitionLink(DomainResource):
    resource_type: Literal["GraphDefinitionLink"] = Field(default="GraphDefinitionLink")
    path: str = Field(description="Focal resource path (e.g., 'Patient')")
    sliceName: Optional[str] = Field(default=None, description="Which slice (if slicing) is referred to")
    min: Optional[int] = Field(default=None, description="Minimum occurrences for this link")
    max: Optional[str] = Field(default=None, description="Maximum occurrences for this link ('*' for many)")
    description: Optional[str] = Field(default=None, description="Why this link is included")
    target: List[GraphDefinitionLinkTarget] = Field(default_factory=list, description="Potential targets for this link")


class GraphDefinition(DomainResource):
    """
    Minimal GraphDefinition aligned with FHIR to describe traversals between resources.
    This enables declaring how to navigate between linked records.
    """

    resource_type: Literal["GraphDefinition"] = Field(default="GraphDefinition")
    name: str = Field(description="Human-readable name")
    status: str = Field(default="active", description="Status of the graph definition")
    start: str = Field(description="Type of the starting resource (e.g., 'Patient')")
    description: Optional[str] = Field(default=None, description="Markdown description")
    link: List[GraphDefinitionLink] = Field(default_factory=list, description="Links this graph makes rules about")


