from __future__ import annotations

# Re-export types from hacs-models to avoid duplication
try:
    from hacs_models import (
        FormatType,  # type: ignore
        ExtractionResults,  # type: ignore
        CharInterval,  # type: ignore
        AlignmentStatus,  # type: ignore
        Document,  # type: ignore
        AnnotatedDocument,  # type: ignore
    )
except Exception:  # pragma: no cover
    FormatType = None  # type: ignore
    ExtractionResults = None  # type: ignore
    CharInterval = None  # type: ignore
    AlignmentStatus = None  # type: ignore
    Document = None  # type: ignore
    AnnotatedDocument = None  # type: ignore

# Local Document wrapper used by chunkers
class Document:
    def __init__(self, text: str, document_id: str | None = None, additional_context: dict | None = None):
        self.text = text
        self.document_id = document_id or "doc"
        self.additional_context = additional_context or {}

class FormatType:
    JSON = "json"
    YAML = "yaml"
