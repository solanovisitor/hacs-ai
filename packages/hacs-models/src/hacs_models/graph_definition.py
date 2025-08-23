from __future__ import annotations

from typing import Literal

from pydantic import Field

from .base_resource import DomainResource


class GraphDefinitionLinkTarget(DomainResource):
    resource_type: Literal["GraphDefinitionLinkTarget"] = Field(default="GraphDefinitionLinkTarget")
    type: str = Field(description="Type of resource this link points to (e.g., 'Patient')")
    params: str | None = Field(
        default=None, description="Criteria (search parameters) for the target"
    )


class GraphDefinitionLink(DomainResource):
    resource_type: Literal["GraphDefinitionLink"] = Field(default="GraphDefinitionLink")
    path: str = Field(description="Focal resource path (e.g., 'Patient')")
    sliceName: str | None = Field(
        default=None, description="Which slice (if slicing) is referred to"
    )
    min: int | None = Field(default=None, description="Minimum occurrences for this link")
    max: str | None = Field(
        default=None, description="Maximum occurrences for this link ('*' for many)"
    )
    description: str | None = Field(default=None, description="Why this link is included")
    target: list[GraphDefinitionLinkTarget] = Field(
        default_factory=list, description="Potential targets for this link"
    )


class GraphDefinition(DomainResource):
    """
    Minimal GraphDefinition aligned with FHIR to describe traversals between resources.
    This enables declaring how to navigate between linked records.
    """

    resource_type: Literal["GraphDefinition"] = Field(default="GraphDefinition")
    name: str = Field(description="Human-readable name")
    status: str = Field(default="active", description="Status of the graph definition")
    start: str = Field(description="Type of the starting resource (e.g., 'Patient')")
    description: str | None = Field(default=None, description="Markdown description")
    link: list[GraphDefinitionLink] = Field(
        default_factory=list, description="Links this graph makes rules about"
    )
