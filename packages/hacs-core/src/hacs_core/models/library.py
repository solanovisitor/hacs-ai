"""
Library model for knowledge artifact containers and logic libraries.

Based on FHIR R5 Library resource with HACS enhancements.
Provides a container for knowledge artifacts including logic libraries, model definitions, and asset collections.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from ..base_resource import BaseResource
from pydantic import Field


class LibraryStatus(str, Enum):
    """Status of the library."""

    DRAFT = "draft"
    ACTIVE = "active"
    RETIRED = "retired"
    UNKNOWN = "unknown"


class LibraryType(str, Enum):
    """Type of library."""

    LOGIC_LIBRARY = "logic-library"
    MODEL_DEFINITION = "model-definition"
    ASSET_COLLECTION = "asset-collection"


class AttachmentContentType(str, Enum):
    """Content types for library attachments."""

    TEXT_CQL = "text/cql"
    APPLICATION_ELM_JSON = "application/elm+json"
    APPLICATION_ELM_XML = "application/elm+xml"
    TEXT_FHIRPATH = "text/fhirpath"
    APPLICATION_JSON = "application/json"
    APPLICATION_XML = "application/xml"
    TEXT_PLAIN = "text/plain"


class Library(BaseResource):
    """
    Represents a library for knowledge artifacts and logic.

    Based on FHIR R5 Library with HACS enhancements for healthcare agents.
    Provides a container for knowledge artifacts including logic libraries, model definitions, and asset collections.
    """

    resource_type: Literal["Library"] = Field(
        default="Library", description="Resource type identifier"
    )

    # Basic metadata
    url: str | None = Field(
        default=None, description="Canonical identifier for this library"
    )

    identifier: list[dict[str, Any]] = Field(
        default_factory=list, description="Additional identifier for the library"
    )

    version: str | None = Field(
        default=None, description="Business version of the library"
    )

    name: str | None = Field(
        default=None, description="Computer-friendly name for the library"
    )

    title: str | None = Field(
        default=None, description="Human-friendly title for the library"
    )

    subtitle: str | None = Field(
        default=None, description="Subordinate title for the library"
    )

    status: LibraryStatus = Field(
        default=LibraryStatus.DRAFT, description="Current status of the library"
    )

    experimental: bool = Field(
        default=False, description="For testing purposes, not real usage"
    )

    type_coding: dict[str, Any] | None = Field(
        default=None,
        description="Type of library (logic-library, model-definition, etc.)",
    )

    # LLM-FRIENDLY: Simple type alternative
    library_type: LibraryType | None = Field(
        default=None, description="Simple type classification for the library"
    )

    subject_codeable_concept: dict[str, Any] | None = Field(
        default=None, description="Type of individual the library is focused on"
    )

    subject_reference: str | None = Field(
        default=None, description="Individual the library is focused on"
    )

    subject_canonical: str | None = Field(
        default=None, description="Canonical reference to subject"
    )

    # Dates
    date: datetime | None = Field(default=None, description="Date last changed")

    # Publishing information
    publisher: str | None = Field(default=None, description="Name of the publisher")

    contact: list[dict[str, Any]] = Field(
        default_factory=list, description="Contact details for the publisher"
    )

    description: str | None = Field(
        default=None, description="Natural language description of the library"
    )

    use_context: list[dict[str, Any]] = Field(
        default_factory=list, description="Context the content is intended to support"
    )

    jurisdiction: list[dict[str, Any]] = Field(
        default_factory=list, description="Intended jurisdiction for library"
    )

    purpose: str | None = Field(default=None, description="Why this library is defined")

    usage: str | None = Field(
        default=None, description="Describes the clinical usage of the library"
    )

    copyright: str | None = Field(
        default=None, description="Use and/or publishing restrictions"
    )

    copyright_label: str | None = Field(
        default=None, description="Copyright holder and year(s)"
    )

    approval_date: datetime | None = Field(
        default=None, description="When the library was approved by publisher"
    )

    last_review_date: datetime | None = Field(
        default=None, description="When the library was last reviewed"
    )

    effective_period: dict[str, Any] | None = Field(
        default=None, description="When the library is expected to be used"
    )

    # Clinical metadata
    topic: list[dict[str, Any]] = Field(
        default_factory=list, description="E.g. Education, Treatment, Assessment"
    )

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

    # Library-specific fields
    parameter: list[dict[str, Any]] = Field(
        default_factory=list, description="Parameters defined by the library"
    )

    data_requirement: list[dict[str, Any]] = Field(
        default_factory=list, description="What data is required for this library"
    )

    content: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Contents of the library, either embedded or referenced",
    )

    # HACS-specific enhancements for logic libraries
    logic_language: str | None = Field(
        default=None,
        description="Language used for logic expressions (e.g., CQL, FHIRPath, JavaScript)",
        examples=["CQL", "FHIRPath", "JavaScript", "Python"],
    )

    logic_content: str | None = Field(
        default=None, description="Direct logic content for simple libraries"
    )

    dependencies: list[str] = Field(
        default_factory=list, description="Other libraries this library depends on"
    )

    functions: list[dict[str, Any]] = Field(
        default_factory=list, description="Functions defined in this library"
    )

    constants: dict[str, Any] = Field(
        default_factory=dict, description="Constants defined in this library"
    )

    # Agent-specific metadata
    agent_context: dict[str, Any] = Field(
        default_factory=dict, description="Agent-specific context and configuration"
    )

    execution_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata about library execution and performance",
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "id": "blood-pressure-logic",
                    "resource_type": "Library",
                    "title": "Blood Pressure Assessment Logic",
                    "status": "active",
                    "library_type": "logic-library",
                    "description": "Logic library for blood pressure assessment and classification",
                    "logic_language": "CQL",
                    "logic_content": """
define "Hypertensive":
  BP.systolic >= 140 or BP.diastolic >= 90

define "Normal":
  BP.systolic < 120 and BP.diastolic < 80
""",
                    "functions": [
                        {
                            "name": "ClassifyBloodPressure",
                            "description": "Classifies blood pressure reading",
                            "parameters": ["systolic", "diastolic"],
                            "return_type": "string",
                        }
                    ],
                }
            ]
        }
