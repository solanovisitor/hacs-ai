"""
HACS Terminology Models (FHIR-inspired)

This module provides lightweight, agent-friendly terminology models aligned with
FHIR Terminology resources (CodeSystem, ValueSet, ConceptMap) to support
code resolution, value set composition, and concept mapping.
"""

from __future__ import annotations

from typing import List, Optional, Literal, Dict
from pydantic import Field

from .base_resource import DomainResource


class TerminologySystem(DomainResource):
    """Represents a terminology code system (e.g., SNOMED CT, LOINC, RxNorm, UMLS)."""

    resource_type: Literal["TerminologySystem"] = Field(default="TerminologySystem")

    name: str = Field(description="Human-friendly name of the terminology system")
    system_uri: str = Field(description="Canonical URI identifying the code system")
    version: Optional[str] = Field(default=None, description="System version")
    publisher: Optional[str] = Field(default=None, description="Organization publishing the system")
    description: Optional[str] = Field(default=None, description="Short description of the system")
    jurisdiction: Optional[str] = Field(default=None, description="Jurisdiction(s) for use")
    tooling: Optional[str] = Field(default=None, description="Preferred tooling/integration (e.g., umls)")


class TerminologyConcept(DomainResource):
    """A single coded concept from a terminology system."""

    resource_type: Literal["TerminologyConcept"] = Field(default="TerminologyConcept")

    system_uri: str = Field(description="Code system URI of this concept")
    code: str = Field(description="Code symbol defined by the code system")
    display: Optional[str] = Field(default=None, description="Human-readable display")
    definition: Optional[str] = Field(default=None, description="Formal definition")
    version: Optional[str] = Field(default=None, description="Code system version for this concept")
    synonyms: List[str] = Field(default_factory=list, description="Alternate labels/synonyms")
    parents: List[str] = Field(default_factory=list, description="Parent codes (isa) if applicable")
    children: List[str] = Field(default_factory=list, description="Child codes (isa) if applicable")
    relations: Dict[str, List[str]] = Field(default_factory=dict, description="Other relations: {relation: [codes]}")


class ValueSet(DomainResource):
    """A set of concepts drawn from one or more code systems."""

    resource_type: Literal["ValueSet"] = Field(default="ValueSet")

    url: Optional[str] = Field(default=None, description="Canonical URL for this value set")
    name: Optional[str] = Field(default=None, description="Name for this value set")
    version: Optional[str] = Field(default=None, description="Business version")
    description: Optional[str] = Field(default=None, description="What this value set is for")

    # Compose: includes and optional filters
    include_systems: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of {system_uri, version?} to include"
    )
    include_concepts: List[TerminologyConcept] = Field(
        default_factory=list, description="Inline explicit concepts to include"
    )

    # Expansion (materialized for agent usage)
    expansion_timestamp: Optional[str] = Field(default=None, description="When expansion was generated")
    expanded_concepts: List[TerminologyConcept] = Field(
        default_factory=list, description="Expanded concepts for fast agent lookups"
    )


class ConceptMapElement(DomainResource):
    resource_type: Literal["ConceptMapElement"] = Field(default="ConceptMapElement")
    source: str = Field(description="Source code system URI")
    source_code: str = Field(description="Source code")
    target: str = Field(description="Target code system URI")
    target_code: str = Field(description="Target code")
    equivalence: str = Field(default="related-to", description="Mapping equivalence: related-to|equivalent|narrower|broader|inexact|unmatched")
    comment: Optional[str] = Field(default=None, description="Mapping rationale/notes")


class ConceptMap(DomainResource):
    """Mappings between concepts in two code systems."""

    resource_type: Literal["ConceptMap"] = Field(default="ConceptMap")

    name: Optional[str] = Field(default=None, description="Name of the concept map")
    source: str = Field(description="Source system URI")
    target: str = Field(description="Target system URI")
    version: Optional[str] = Field(default=None, description="Version label for this concept map")
    group: List[ConceptMapElement] = Field(default_factory=list, description="List of mapping elements")


