"""
Evidence models optimized for storing literature-based evidence.

This module provides a FHIR-inspired Evidence resource tailored for
literature references (papers, guidelines), while preserving backwards
compatibility with prior fields used by tools.
"""

from datetime import date
from enum import Enum
from typing import Any, Literal

from pydantic import Field, computed_field, field_validator

from .base_resource import BaseResource


class EvidenceType(str, Enum):
    """Types of evidence records."""

    RESEARCH_PAPER = "research_paper"
    GUIDELINE = "guideline"
    SYSTEMATIC_REVIEW = "systematic_review"
    META_ANALYSIS = "meta_analysis"
    CLINICAL_NOTE = "clinical_note"
    OBSERVATION = "observation"
    OTHER = "other"


class EvidenceLevel(str, Enum):
    """Simplified evidence levels (e.g., GRADE)."""

    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    VERY_LOW = "very_low"


class EvidenceAuthor(BaseResource):
    resource_type: Literal["EvidenceAuthor"] = Field(default="EvidenceAuthor")
    full_name: str = Field(description="Author full name")
    affiliation: str | None = Field(default=None, description="Author affiliation")


class PublicationVenue(BaseResource):
    resource_type: Literal["PublicationVenue"] = Field(default="PublicationVenue")
    name: str = Field(description="Journal or venue name")
    issn: str | None = Field(default=None, description="ISSN identifier")
    publisher: str | None = Field(default=None, description="Publisher name")


class Evidence(BaseResource):
    """
    Literature-focused Evidence resource with FHIR-inspired fields.

    Backwards-compatibility: retains legacy fields `citation`, `content`,
    `evidence_type`, `confidence_score`, `quality_score`, `vector_id`, `provenance`,
    `linked_resources`, `tags`, `review_status`.
    """

    resource_type: Literal["Evidence"] = Field(default="Evidence")

    # Core bibliographic fields (FHIR Citation inspired)
    title: str | None = Field(default=None, description="Title of the cited artifact")
    abstract: str | None = Field(default=None, description="Abstract or summary of the artifact")
    authors: list[EvidenceAuthor] = Field(default_factory=list, description="List of authors")
    journal: PublicationVenue | None = Field(default=None, description="Publication venue")
    publication_year: int | None = Field(default=None, description="Year of publication")
    publication_date: date | str | None = Field(
        default=None, description="Date of publication (date or templated string)"
    )
    doi: str | None = Field(default=None, description="Digital Object Identifier")
    pmid: str | None = Field(default=None, description="PubMed ID")
    url: str | None = Field(default=None, description="URL to the artifact")
    language: str | None = Field(default=None, description="Language (BCP-47, e.g., en, pt-BR)")
    volume: str | None = Field(default=None, description="Journal volume")
    issue: str | None = Field(default=None, description="Journal issue")
    pages: str | None = Field(default=None, description="Page range")
    keywords: list[str] = Field(default_factory=list, description="Keywords/MeSH terms")

    # Evidence grading and type
    evidence_level: EvidenceLevel | None = Field(
        default=None, description="Evidence level (e.g., GRADE)"
    )
    evidence_type: EvidenceType = Field(
        default=EvidenceType.RESEARCH_PAPER, description="Type of evidence"
    )

    # Legacy fields (kept for compatibility with tools and tests)
    citation: str | None = Field(default=None, description="Formatted citation string")
    content: str | None = Field(default=None, description="Legacy field for content or findings")

    # Quality and provenance
    confidence_score: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Confidence score (0.0-1.0)"
    )
    quality_score: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Quality assessment score (0.0-1.0)"
    )
    vector_id: str | None = Field(default=None, description="Vector embedding reference for RAG")
    provenance: dict[str, Any] = Field(
        default_factory=dict, description="Provenance info (source, collected_by, etc.)"
    )
    linked_resources: list[str] = Field(
        default_factory=list, description="Linked HACS resources (ids)"
    )
    tags: list[str] = Field(default_factory=list, description="Categorization tags")
    review_status: Literal["pending", "reviewed", "approved", "rejected"] = Field(
        default="pending", description="Review status"
    )

    @field_validator("title")
    @classmethod
    def _validate_title(cls, v: str | None) -> str | None:
        return v.strip() if isinstance(v, str) else v

    @field_validator("citation")
    @classmethod
    def _validate_citation(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        if not s:
            return None
        return s

    @field_validator("provenance")
    @classmethod
    def _validate_provenance(cls, v: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(v, dict):
            raise ValueError("Provenance must be a dictionary")
        return v

    @computed_field
    @property
    def overall_reliability(self) -> float:
        return (self.confidence_score + self.quality_score) / 2

    def add_vector_reference(self, vector_id: str) -> None:
        self.vector_id = vector_id
        self.update_timestamp()

    def update_provenance(self, key: str, value: Any) -> None:
        self.provenance[key] = value
        self.update_timestamp()

    def link_to_resource(self, resource_id: str) -> None:
        if resource_id not in self.linked_resources:
            self.linked_resources.append(resource_id)
            self.update_timestamp()

    def unlink_from_resource(self, resource_id: str) -> bool:
        if resource_id in self.linked_resources:
            self.linked_resources.remove(resource_id)
            self.update_timestamp()
            return True
        return False

    def set_confidence(self, score: float) -> None:
        if not 0.0 <= score <= 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        self.confidence_score = score
        self.update_timestamp()

    def set_quality(self, score: float) -> None:
        if not 0.0 <= score <= 1.0:
            raise ValueError("Quality score must be between 0.0 and 1.0")
        self.quality_score = score
        self.update_timestamp()

    def add_tag(self, tag: str) -> None:
        tag = tag.strip().lower()
        if tag and tag not in self.tags:
            self.tags.append(tag)
            self.update_timestamp()

    def remove_tag(self, tag: str) -> bool:
        tag = tag.strip().lower()
        if tag in self.tags:
            self.tags.remove(tag)
            self.update_timestamp()
            return True
        return False

    def update_review_status(
        self, status: Literal["pending", "reviewed", "approved", "rejected"]
    ) -> None:
        self.review_status = status
        self.update_timestamp()

    def is_high_quality(self, threshold: float = 0.8) -> bool:
        return self.overall_reliability >= threshold

    def to_citation_string(self) -> str:
        """Generate a simple formatted citation string from fields if `citation` is not provided."""
        if self.citation:
            return self.citation
        parts: list[str] = []
        if self.authors:
            parts.append(", ".join(a.full_name for a in self.authors if a.full_name))
        if self.publication_year:
            parts.append(f"({self.publication_year})")
        if self.title:
            parts.append(self.title)
        if self.journal and self.journal.name:
            j = self.journal.name
            vol = f" {self.volume}" if self.volume else ""
            iss = f"({self.issue})" if self.issue else ""
            pgs = f", {self.pages}" if self.pages else ""
            parts.append(f"{j}{vol}{iss}{pgs}")
        if self.doi:
            parts.append(f"doi:{self.doi}")
        return ". ".join([p for p in parts if p])

    @field_validator("publication_year")
    @classmethod
    def _ensure_year(cls, v: int | None, info):
        return v
