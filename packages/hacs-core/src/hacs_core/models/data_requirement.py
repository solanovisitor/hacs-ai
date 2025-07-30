"""
DataRequirement model for expression logic and knowledge asset data requirements.

Based on FHIR R5 DataRequirement datatype with HACS enhancements.
Represents data requirements for knowledge assets like decision support rules and quality measures.
"""

from enum import Enum
from typing import Any, Literal

from ..base_resource import BaseResource
from pydantic import Field


class SortDirection(str, Enum):
    """Direction for sorting."""

    ASCENDING = "ascending"
    DESCENDING = "descending"


class DataRequirement(BaseResource):
    """
    Represents a data requirement for knowledge assets.

    Based on FHIR R5 DataRequirement with HACS enhancements for healthcare agents.
    Describes data needed for decision support rules, quality measures, and other knowledge artifacts.
    """

    resource_type: Literal["DataRequirement"] = Field(
        default="DataRequirement", description="Resource type identifier"
    )

    # Core requirement
    type: str = Field(
        description="The type of the required data",
        examples=["Patient", "Observation", "Condition", "MedicationRequest"],
    )

    profile: list[str] = Field(
        default_factory=list, description="The profile of the required data"
    )

    subject_codeable_concept: dict[str, Any] | None = Field(
        default=None,
        description="E.g. Patient, Practitioner, RelatedPerson, Organization, Location, Device",
    )

    subject_reference: str | None = Field(
        default=None,
        description="E.g. Patient, Practitioner, RelatedPerson, Organization, Location, Device",
    )

    must_support: list[str] = Field(
        default_factory=list,
        description="Indicates specific structure elements that are referenced by the knowledge module",
    )

    # Code filter
    code_filter: list[dict[str, Any]] = Field(
        default_factory=list, description="What codes are expected"
    )

    # Date filter
    date_filter: list[dict[str, Any]] = Field(
        default_factory=list, description="What dates/date ranges are expected"
    )

    # Value filter
    value_filter: list[dict[str, Any]] = Field(
        default_factory=list, description="What values are expected"
    )

    # Limit
    limit: int | None = Field(default=None, description="Number of results", ge=1)

    # Sort
    sort: list[dict[str, Any]] = Field(
        default_factory=list, description="Order of the results"
    )

    # HACS-specific enhancements
    description: str | None = Field(
        default=None, description="Human-readable description of the data requirement"
    )

    required: bool = Field(
        default=True, description="Whether this data is required or optional"
    )

    priority: int = Field(
        default=1, description="Priority of this data requirement (1=highest)", ge=1
    )

    # Expression logic support
    expression: str | None = Field(
        default=None,
        description="FHIRPath or CQL expression defining the data requirement",
    )

    expression_language: str | None = Field(
        default=None,
        description="Language of the expression (FHIRPath, CQL, etc.)",
        examples=["FHIRPath", "CQL", "JavaScript"],
    )

    # Context information
    context_path: str | None = Field(
        default=None, description="Path to the context element within the resource"
    )

    context_expression: str | None = Field(
        default=None, description="Expression defining the context"
    )

    # Aggregation
    aggregate_method: str | None = Field(
        default=None,
        description="How to aggregate multiple results",
        examples=["count", "sum", "average", "min", "max", "first", "last"],
    )

    # Quality and confidence
    min_confidence: float | None = Field(
        default=None,
        description="Minimum confidence required for the data",
        ge=0.0,
        le=1.0,
    )

    # Agent context
    agent_context: dict[str, Any] = Field(
        default_factory=dict, description="Agent-specific context for data retrieval"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "id": "blood-pressure-requirement",
                    "resource_type": "DataRequirement",
                    "type": "Observation",
                    "description": "Recent blood pressure measurements",
                    "code_filter": [
                        {
                            "path": "code",
                            "valueSet": "http://hl7.org/fhir/ValueSet/observation-vitalsignresult",
                        }
                    ],
                    "date_filter": [
                        {
                            "path": "effectiveDateTime",
                            "valuePeriod": {"start": "2024-01-01", "end": "2024-12-31"},
                        }
                    ],
                    "limit": 5,
                    "sort": [{"path": "effectiveDateTime", "direction": "descending"}],
                    "required": True,
                    "priority": 1,
                }
            ]
        }
