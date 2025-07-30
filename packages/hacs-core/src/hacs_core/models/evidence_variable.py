"""
EvidenceVariable and ArtifactAssessment models for enhanced evidence framework.

Based on FHIR R5 EvidenceVariable and ArtifactAssessment resources with HACS enhancements.
Supports PICO elements and knowledge artifact quality assessments.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from ..base_resource import BaseResource
from pydantic import Field


class EvidenceVariableStatus(str, Enum):
    """Status of the evidence variable."""

    DRAFT = "draft"
    ACTIVE = "active"
    RETIRED = "retired"
    UNKNOWN = "unknown"


class EvidenceVariableHandling(str, Enum):
    """How the evidence variable is handled."""

    CONTINUOUS = "continuous"
    DICHOTOMOUS = "dichotomous"
    ORDINAL = "ordinal"
    POLYCHOTOMOUS = "polychotomous"


class ArtifactAssessmentWorkflowStatus(str, Enum):
    """Workflow status of the assessment."""

    SUBMITTED = "submitted"
    TRIAGED = "triaged"
    WAITING_FOR_INPUT = "waiting-for-input"
    RESOLVED_NO_CHANGE = "resolved-no-change"
    RESOLVED_CHANGE_REQUIRED = "resolved-change-required"
    DEFERRED = "deferred"
    DUPLICATE = "duplicate"
    APPLIED = "applied"
    PUBLISHED = "published"


class ArtifactAssessmentDisposition(str, Enum):
    """Disposition of the assessment."""

    UNRESOLVED = "unresolved"
    NOT_PERSUASIVE = "not-persuasive"
    PERSUASIVE = "persuasive"
    PERSUASIVE_WITH_MODIFICATION = "persuasive-with-modification"
    NOT_PERSUASIVE_WITH_MODIFICATION = "not-persuasive-with-modification"


class EvidenceVariable(BaseResource):
    """
    Represents a variable used in evidence research (e.g., PICO elements).

    Based on FHIR R5 EvidenceVariable with HACS enhancements for healthcare agents.
    Represents elements that evidence is about, such as the elements of a PICO question.
    """

    resource_type: Literal["EvidenceVariable"] = Field(
        default="EvidenceVariable", description="Resource type identifier"
    )

    # Basic metadata
    url: str | None = Field(
        default=None, description="Canonical identifier for this evidence variable"
    )

    identifier: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Additional identifier for the evidence variable",
    )

    version: str | None = Field(
        default=None, description="Business version of the evidence variable"
    )

    name: str | None = Field(
        default=None, description="Computer-friendly name for the evidence variable"
    )

    title: str | None = Field(
        default=None, description="Human-friendly title for the evidence variable"
    )

    short_title: str | None = Field(
        default=None, description="Title for use in informal contexts"
    )

    subtitle: str | None = Field(
        default=None, description="Subordinate title for the evidence variable"
    )

    status: EvidenceVariableStatus = Field(
        default=EvidenceVariableStatus.DRAFT,
        description="Current status of the evidence variable",
    )

    experimental: bool = Field(
        default=False, description="For testing purposes, not real usage"
    )

    # Dates
    date: datetime | None = Field(default=None, description="Date last changed")

    # Publishing information
    publisher: str | None = Field(default=None, description="Name of the publisher")

    contact: list[dict[str, Any]] = Field(
        default_factory=list, description="Contact details for the publisher"
    )

    description: str | None = Field(
        default=None,
        description="Natural language description of the evidence variable",
    )

    note: list[dict[str, Any]] = Field(
        default_factory=list, description="Used for footnotes or explanatory notes"
    )

    use_context: list[dict[str, Any]] = Field(
        default_factory=list, description="Context the content is intended to support"
    )

    purpose: str | None = Field(
        default=None, description="Why this evidence variable is defined"
    )

    copyright: str | None = Field(
        default=None, description="Use and/or publishing restrictions"
    )

    # Clinical metadata
    author: list[dict[str, Any]] = Field(
        default_factory=list, description="Who authored the content"
    )

    editor: list[dict[str, Any]] = Field(
        default_factory=list, description="Who edited the content"
    )

    reviewer: list[dict[str, Any]] = Field(
        default_factory=list, description="Who reviewed the content"
    )

    endorser: list[dict[str, Any]] = Field(
        default_factory=list, description="Who endorsed the content"
    )

    related_artifact: list[dict[str, Any]] = Field(
        default_factory=list, description="Additional documentation, citations, etc."
    )

    # Variable definition
    actual: bool | None = Field(default=None, description="Actual or conceptual")

    characteristic_combination: str | None = Field(
        default=None, description="intersection | union"
    )

    characteristic: list[dict[str, Any]] = Field(
        default_factory=list,
        description="What defines the members of the evidence element",
    )

    handling: EvidenceVariableHandling | None = Field(
        default=None, description="continuous | dichotomous | ordinal | polychotomous"
    )

    category: list[dict[str, Any]] = Field(
        default_factory=list,
        description="A grouping for ordinal or polychotomous variables",
    )

    # HACS-specific enhancements
    pico_element: str | None = Field(
        default=None,
        description="PICO element this variable represents",
        examples=["Population", "Intervention", "Comparison", "Outcome"],
    )

    measurement_type: str | None = Field(
        default=None,
        description="Type of measurement for this variable",
        examples=["binary", "continuous", "time-to-event", "ordinal"],
    )

    clinical_significance: str | None = Field(
        default=None, description="Clinical significance of this variable"
    )

    # Agent context
    agent_context: dict[str, Any] = Field(
        default_factory=dict, description="Agent-specific context and configuration"
    )


class ArtifactAssessment(BaseResource):
    """
    Represents an assessment of a knowledge artifact.

    Based on FHIR R5 ArtifactAssessment with HACS enhancements for healthcare agents.
    Captures assessments like ratings, classifiers, reviews, and comments for knowledge artifacts.
    """

    resource_type: Literal["ArtifactAssessment"] = Field(
        default="ArtifactAssessment", description="Resource type identifier"
    )

    # Basic identification
    identifier: list[dict[str, Any]] = Field(
        default_factory=list, description="Additional identifier for the assessment"
    )

    title: str | None = Field(
        default=None, description="A short title for the assessment"
    )

    # What is being assessed
    artifact_reference: str | None = Field(
        default=None, description="The artifact being assessed (reference)"
    )

    artifact_canonical: str | None = Field(
        default=None, description="The artifact being assessed (canonical)"
    )

    artifact_uri: str | None = Field(
        default=None, description="The artifact being assessed (uri)"
    )

    # Assessment content
    content: list[dict[str, Any]] = Field(
        default_factory=list, description="Comment, classifier, or rating content"
    )

    # Workflow status
    workflow_status: ArtifactAssessmentWorkflowStatus | None = Field(
        default=None,
        description="submitted | triaged | waiting-for-input | resolved-no-change | resolved-change-required | deferred | duplicate | applied | published",
    )

    disposition: ArtifactAssessmentDisposition | None = Field(
        default=None,
        description="unresolved | not-persuasive | persuasive | persuasive-with-modification | not-persuasive-with-modification",
    )

    # Dates
    date: datetime | None = Field(default=None, description="Date last changed")

    last_review_date: datetime | None = Field(
        default=None, description="When the assessment was last reviewed"
    )

    # Author information
    copyright: str | None = Field(
        default=None, description="Use and/or publishing restrictions"
    )

    approval_date: datetime | None = Field(
        default=None, description="When the assessment was approved by publisher"
    )

    # HACS-specific enhancements
    assessment_type: str | None = Field(
        default=None,
        description="Type of assessment",
        examples=["quality", "rating", "review", "comment", "classification"],
    )

    overall_score: float | None = Field(
        default=None,
        description="Overall assessment score (0.0 to 1.0)",
        ge=0.0,
        le=1.0,
    )

    quality_criteria: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured quality assessment criteria and scores",
    )

    recommendations: list[dict[str, Any]] = Field(
        default_factory=list, description="Specific recommendations for improvement"
    )

    evidence_quality: str | None = Field(
        default=None,
        description="Quality of evidence assessment",
        examples=["high", "moderate", "low", "very-low"],
    )

    strength_of_recommendation: str | None = Field(
        default=None,
        description="Strength of recommendation",
        examples=["strong", "weak", "conditional"],
    )

    # Agent context
    agent_context: dict[str, Any] = Field(
        default_factory=dict, description="Agent-specific context and configuration"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "id": "hypertension-guideline-assessment",
                    "resource_type": "ArtifactAssessment",
                    "title": "Quality Assessment of Hypertension Management Guideline",
                    "artifact_canonical": "http://example.org/fhir/PlanDefinition/hypertension-protocol",
                    "assessment_type": "quality",
                    "overall_score": 0.85,
                    "workflow_status": "published",
                    "disposition": "persuasive",
                    "quality_criteria": {
                        "evidence_quality": 0.9,
                        "methodology": 0.8,
                        "clarity": 0.85,
                        "applicability": 0.9,
                    },
                    "evidence_quality": "high",
                    "strength_of_recommendation": "strong",
                    "date": "2024-01-15T10:30:00Z",
                }
            ]
        }
