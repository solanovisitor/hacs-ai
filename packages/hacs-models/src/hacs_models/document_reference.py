"""
DocumentReference model for HACS.

Lightweight, HACS-native model inspired by FHIR R4 DocumentReference.
Suitable for indexing clinical notes, certificates, and other binary content
with minimal required fields and safe defaults.
"""

from typing import Any, Literal

from pydantic import Field

from .base_resource import DomainResource


class DocumentReference(DomainResource):
    """
    Minimal document reference for HACS.

    Fields intentionally simplified for early usage:
    - status: current | superseded | entered-in-error (free string)
    - doc_status: preliminary | final | amended | entered-in-error (free string)
    - type_text/category_text: simple text descriptors for kind and category
    - subject_ref/author_ref/custodian_ref: FHIR-style reference strings
    - date: ISO 8601 string
    - description: human-readable description
    - attachment_url/content_type: where to access the document and its MIME type
    - attachment_text: inline textual content (e.g., markdown)
    - attachment_data_base64: inline base64-encoded binary content (e.g., PDF)
    """

    resource_type: Literal["DocumentReference"] = Field(default="DocumentReference")

    status: str = Field(default="current", description="current | superseded | entered-in-error")
    doc_status: str | None = Field(
        default="final", description="preliminary | final | amended | entered-in-error"
    )

    type_text: str | None = Field(
        default=None, description="Kind of document (LOINC text if available)"
    )
    category_text: str | None = Field(
        default=None, description="High-level categorization of document"
    )

    subject_ref: str | None = Field(
        default=None, description="Reference to the subject (e.g., Patient/xyz)"
    )
    author_ref: list[str] = Field(
        default_factory=list, description="Author references (e.g., Practitioner/xyz)"
    )
    custodian_ref: str | None = Field(
        default=None, description="Organization maintaining the document"
    )

    date: str | None = Field(
        default=None, description="When this document reference was created (ISO 8601)"
    )
    description: str | None = Field(default=None, description="Human-readable description")

    attachment_url: str | None = Field(default=None, description="Where to access the document")
    attachment_content_type: str | None = Field(
        default=None, description="MIME type of the document"
    )

    # Optional inline content
    attachment_text: str | None = Field(
        default=None, description="Inline textual content (e.g., markdown)"
    )
    attachment_data_base64: str | None = Field(
        default=None, description="Inline base64-encoded content (e.g., PDF)"
    )

    # Simple author/title fields for convenience
    title: str | None = Field(default=None, description="Document title")

    # --- LLM-friendly extractable facade overrides ---
    @classmethod
    def get_extractable_fields(cls) -> list[str]:  # type: ignore[override]
        """Return fields that should be extracted by LLMs (3-4 key fields only)."""
        return [
            "status",
            "type_text",
            "title", 
            "description",
        ]

    @classmethod
    def get_canonical_defaults(cls) -> dict[str, Any]:
        """Default values for system/required fields during extraction."""
        return {
            "status": "current",
            "subject_ref": "Patient/UNKNOWN",
        }

    @classmethod
    def llm_hints(cls) -> list[str]:  # type: ignore[override]
        """Provide LLM-specific extraction hints."""
        return [
            "Extract the document kind (type_text) when mentioned",
            "Prefer literal document titles from the text",
            "Provide a brief description when available",
            "Use 'current' status unless explicitly stated otherwise",
        ]
