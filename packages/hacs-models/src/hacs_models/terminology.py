"""
HACS Terminology Models (FHIR-inspired)

This module provides lightweight, agent-friendly terminology models aligned with
FHIR Terminology resources (CodeSystem, ValueSet, ConceptMap) to support
code resolution, value set composition, and concept mapping.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from .base_resource import DomainResource


class TerminologySystem(DomainResource):
    """Represents a terminology code system (e.g., SNOMED CT, LOINC, RxNorm, UMLS)."""

    resource_type: Literal["TerminologySystem"] = Field(default="TerminologySystem")

    name: str = Field(description="Human-friendly name of the terminology system")
    system_uri: str = Field(description="Canonical URI identifying the code system")
    version: str | None = Field(default=None, description="System version")
    publisher: str | None = Field(default=None, description="Organization publishing the system")
    description: str | None = Field(default=None, description="Short description of the system")
    jurisdiction: str | None = Field(default=None, description="Jurisdiction(s) for use")
    tooling: str | None = Field(
        default=None, description="Preferred tooling/integration (e.g., umls)"
    )


class TerminologyConcept(DomainResource):
    """A single coded concept from a terminology system."""

    resource_type: Literal["TerminologyConcept"] = Field(default="TerminologyConcept")

    system_uri: str = Field(description="Code system URI of this concept")
    code: str = Field(description="Code symbol defined by the code system")
    display: str | None = Field(default=None, description="Human-readable display")
    definition: str | None = Field(default=None, description="Formal definition")
    version: str | None = Field(default=None, description="Code system version for this concept")
    synonyms: list[str] = Field(default_factory=list, description="Alternate labels/synonyms")
    parents: list[str] = Field(default_factory=list, description="Parent codes (isa) if applicable")
    children: list[str] = Field(default_factory=list, description="Child codes (isa) if applicable")
    relations: dict[str, list[str]] = Field(
        default_factory=dict, description="Other relations: {relation: [codes]}"
    )


class ValueSet(DomainResource):
    """A set of concepts drawn from one or more code systems."""

    resource_type: Literal["ValueSet"] = Field(default="ValueSet")

    url: str | None = Field(default=None, description="Canonical URL for this value set")
    name: str | None = Field(default=None, description="Name for this value set")
    version: str | None = Field(default=None, description="Business version")
    description: str | None = Field(default=None, description="What this value set is for")

    # Compose: includes and optional filters
    include_systems: list[dict[str, str]] = Field(
        default_factory=list, description="List of {system_uri, version?} to include"
    )
    include_concepts: list[TerminologyConcept] = Field(
        default_factory=list, description="Inline explicit concepts to include"
    )

    # Expansion (materialized for agent usage)
    expansion_timestamp: str | None = Field(
        default=None, description="When expansion was generated"
    )
    expanded_concepts: list[TerminologyConcept] = Field(
        default_factory=list, description="Expanded concepts for fast agent lookups"
    )


class ConceptMapElement(DomainResource):
    resource_type: Literal["ConceptMapElement"] = Field(default="ConceptMapElement")
    source: str = Field(description="Source code system URI")
    source_code: str = Field(description="Source code")
    target: str = Field(description="Target code system URI")
    target_code: str = Field(description="Target code")
    equivalence: str = Field(
        default="related-to",
        description="Mapping equivalence: related-to|equivalent|narrower|broader|inexact|unmatched",
    )
    comment: str | None = Field(default=None, description="Mapping rationale/notes")


class ConceptMap(DomainResource):
    """Mappings between concepts in two code systems."""

    resource_type: Literal["ConceptMap"] = Field(default="ConceptMap")

    name: str | None = Field(default=None, description="Name of the concept map")
    source: str = Field(description="Source system URI")
    target: str = Field(description="Target system URI")
    version: str | None = Field(default=None, description="Version label for this concept map")
    group: list[ConceptMapElement] = Field(
        default_factory=list, description="List of mapping elements"
    )
