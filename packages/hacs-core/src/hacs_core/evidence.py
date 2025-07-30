"""
Evidence models for tracking and linking clinical evidence.

This module provides evidence-related models that enable agents to store,
track, and link clinical evidence with proper provenance and confidence scoring.
"""

from enum import Enum
from typing import Any, Literal

from pydantic import Field, computed_field, field_validator

from .base_resource import BaseResource


class EvidenceType(str, Enum):
    """Types of clinical evidence."""

    CLINICAL_NOTE = "clinical_note"
    LAB_RESULT = "lab_result"
    IMAGING = "imaging"
    MEDICATION = "medication"
    PROCEDURE = "procedure"
    DIAGNOSIS = "diagnosis"
    RESEARCH_PAPER = "research_paper"
    GUIDELINE = "guideline"
    PATIENT_REPORTED = "patient_reported"
    OBSERVATION = "observation"


class Evidence(BaseResource):
    """
    Represents a piece of clinical evidence with provenance and confidence tracking.

    Evidence can be linked to other resources and includes vector references
    for future RAG (Retrieval-Augmented Generation) integration.
    """

    resource_type: Literal["Evidence"] = Field(
        default="Evidence", description="Resource type identifier"
    )

    citation: str = Field(
        description="Citation or source reference for this evidence",
        examples=[
            "Smith, J. et al. (2024). Clinical Trial Results. NEJM, 380(1), 45-52.",
            "Patient Chart - John Doe - Encounter 2024-01-15",
            "WHO Clinical Guidelines for Hypertension Management (2023)",
        ],
    )

    content: str = Field(
        description="The actual evidence content or findings",
        examples=[
            "Patient exhibits elevated blood pressure readings consistently above 140/90 mmHg",
            "Lab results show HbA1c of 8.2%, indicating poor glycemic control",
            "MRI reveals no acute intracranial abnormalities",
        ],
    )

    evidence_type: EvidenceType = Field(
        description="Type of evidence this represents",
        examples=["clinical_note", "lab_result", "imaging"],
    )

    confidence_score: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Confidence score for this evidence (0.0 to 1.0)",
        examples=[0.95, 0.7, 0.85],
    )

    vector_id: str | None = Field(
        default=None,
        description="Reference to vector embedding for RAG integration",
        examples=["vec_abc123", "emb_456def", None],
    )

    provenance: dict[str, Any] = Field(
        default_factory=dict,
        description="Provenance information including source, collection method, etc.",
        examples=[
            {
                "source_system": "Epic EHR",
                "collected_by": "Dr. Smith",
                "collection_date": "2024-01-15T10:30:00Z",
                "verification_status": "verified",
            }
        ],
    )

    linked_resources: list[str] = Field(
        default_factory=list,
        description="IDs of resources this evidence is linked to",
        examples=[["patient-001", "encounter-123", "observation-456"]],
    )

    quality_score: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Quality assessment score for this evidence",
        examples=[0.9, 0.75, 0.6],
    )

    tags: list[str] = Field(
        default_factory=list,
        description="Tags for categorizing and searching evidence",
        examples=[["hypertension", "cardiology", "medication_review"]],
    )

    review_status: Literal["pending", "reviewed", "approved", "rejected"] = Field(
        default="pending", description="Review status of this evidence"
    )

    @field_validator("citation")
    @classmethod
    def validate_citation(cls, v: str) -> str:
        """Ensure citation is not empty and properly formatted."""
        if not v.strip():
            raise ValueError("Citation cannot be empty")
        return v.strip()

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Ensure content is not empty."""
        if not v.strip():
            raise ValueError("Evidence content cannot be empty")
        return v.strip()

    @field_validator("provenance")
    @classmethod
    def validate_provenance(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Ensure provenance is a valid dictionary."""
        if not isinstance(v, dict):
            raise ValueError("Provenance must be a dictionary")
        return v

    @computed_field
    @property
    def overall_reliability(self) -> float:
        """Computed field combining confidence and quality scores."""
        return (self.confidence_score + self.quality_score) / 2

    def add_vector_reference(self, vector_id: str) -> None:
        """
        Add or update vector embedding reference.

        Args:
            vector_id: ID of the vector embedding
        """
        self.vector_id = vector_id
        self.update_timestamp()

    def update_provenance(self, key: str, value: Any) -> None:
        """
        Update provenance information.

        Args:
            key: Provenance key
            value: Provenance value
        """
        self.provenance[key] = value
        self.update_timestamp()

    def link_to_resource(self, resource_id: str) -> None:
        """
        Link this evidence to another resource.

        Args:
            resource_id: ID of the resource to link to
        """
        if resource_id not in self.linked_resources:
            self.linked_resources.append(resource_id)
            self.update_timestamp()

    def unlink_from_resource(self, resource_id: str) -> bool:
        """
        Remove link to a resource.

        Args:
            resource_id: ID of the resource to unlink

        Returns:
            True if the resource was unlinked, False if it wasn't found
        """
        if resource_id in self.linked_resources:
            self.linked_resources.remove(resource_id)
            self.update_timestamp()
            return True
        return False

    def set_confidence(self, score: float) -> None:
        """
        Set the confidence score.

        Args:
            score: Confidence score between 0.0 and 1.0
        """
        if not 0.0 <= score <= 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        self.confidence_score = score
        self.update_timestamp()

    def set_quality(self, score: float) -> None:
        """
        Set the quality score.

        Args:
            score: Quality score between 0.0 and 1.0
        """
        if not 0.0 <= score <= 1.0:
            raise ValueError("Quality score must be between 0.0 and 1.0")
        self.quality_score = score
        self.update_timestamp()

    def add_tag(self, tag: str) -> None:
        """
        Add a tag if not already present.

        Args:
            tag: Tag to add
        """
        tag = tag.strip().lower()
        if tag and tag not in self.tags:
            self.tags.append(tag)
            self.update_timestamp()

    def remove_tag(self, tag: str) -> bool:
        """
        Remove a tag.

        Args:
            tag: Tag to remove

        Returns:
            True if the tag was removed, False if it wasn't found
        """
        tag = tag.strip().lower()
        if tag in self.tags:
            self.tags.remove(tag)
            self.update_timestamp()
            return True
        return False

    def update_review_status(
        self, status: Literal["pending", "reviewed", "approved", "rejected"]
    ) -> None:
        """
        Update the review status.

        Args:
            status: New review status
        """
        self.review_status = status
        self.update_timestamp()

    def is_high_quality(self, threshold: float = 0.8) -> bool:
        """
        Check if this evidence meets high quality standards.

        Args:
            threshold: Quality threshold (default 0.8)

        Returns:
            True if overall reliability is above threshold
        """
        return self.overall_reliability >= threshold

    def __repr__(self) -> str:
        """Enhanced representation including evidence type and reliability."""
        return f"Evidence(id='{self.id}', type='{self.evidence_type}', reliability={self.overall_reliability:.2f})"
