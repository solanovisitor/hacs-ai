from __future__ import annotations

# Import types from hacs-models for consistency

# Local Document wrapper used by chunkers (different from hacs_models Document)
class Document:
    def __init__(self, text: str, document_id: str | None = None, additional_context: dict | None = None):
        self.text = text
        self.document_id = document_id or "doc"
        self.additional_context = additional_context or {}
