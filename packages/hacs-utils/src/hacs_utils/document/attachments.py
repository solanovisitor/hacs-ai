from __future__ import annotations

from typing import Optional

from hacs_models.document_reference import DocumentReference


def create_markdown_document(
    markdown_text: str,
    *,
    title: Optional[str] = None,
    subject_ref: Optional[str] = None,
) -> DocumentReference:
    """Create a DocumentReference carrying inline markdown content."""
    return DocumentReference(
        title=title or "Markdown",
        subject_ref=subject_ref,
        attachment_content_type="text/markdown",
        attachment_text=markdown_text,
        description=(markdown_text[:1024] if markdown_text else None),
    )


