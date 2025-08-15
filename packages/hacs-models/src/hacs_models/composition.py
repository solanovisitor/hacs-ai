from __future__ import annotations

from typing import Any, Dict, List, Optional, Literal
from pydantic import Field

from .base_resource import DomainResource
from .types import DocumentStatus, DocumentType, ConfidentialityLevel


class CompositionAuthor(DomainResource):
    resource_type: Literal["CompositionAuthor"] = Field(default="CompositionAuthor")
    name: Optional[str] = None
    role: Optional[str] = None
    organization: Optional[str] = None
    specialty: Optional[str] = None


class CompositionAttester(DomainResource):
    resource_type: Literal["CompositionAttester"] = Field(default="CompositionAttester")
    mode: Literal["professional", "legal", "official", "personal"] = "professional"
    party_name: Optional[str] = None
    party_id: Optional[str] = None
    organization: Optional[str] = None
    signature: Optional[str] = None


class CompositionSection(DomainResource):
    resource_type: Literal["CompositionSection"] = Field(default="CompositionSection")
    title: str
    text: str
    code: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    sections: List["CompositionSection"] = Field(default_factory=list, description="Nested sections")


class CompositionEncounter(DomainResource):
    resource_type: Literal["CompositionEncounter"] = Field(default="CompositionEncounter")
    encounter_id: Optional[str] = None
    encounter_reference: Optional[str] = None


class Composition(DomainResource):
    resource_type: Literal["Composition"] = Field(default="Composition")
    document_type: Optional[DocumentType] = None
    title: Optional[str] = None
    subject_id: Optional[str] = None
    subject_name: Optional[str] = None
    status: DocumentStatus = Field(default=DocumentStatus.PRELIMINARY)
    confidentiality: ConfidentialityLevel = Field(default=ConfidentialityLevel.NORMAL)
    document_identifier: Optional[str] = Field(default=None)
    authors: List[CompositionAuthor] = Field(default_factory=list)
    attesters: List[CompositionAttester] = Field(default_factory=list)
    sections: List[CompositionSection] = Field(default_factory=list)
    encounter: Optional[CompositionEncounter] = None

    def add_section(self, title: str, text: str, code: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.sections.append(CompositionSection(title=title, text=text, code=code, metadata=metadata or {}))

    def add_author(self, name: str, role: Optional[str] = None, organization: Optional[str] = None, specialty: Optional[str] = None) -> None:
        self.authors.append(CompositionAuthor(name=name, role=role, organization=organization, specialty=specialty))

    def add_attester(self, mode: str, party_name: str, party_id: str, organization: Optional[str] = None, signature: Optional[str] = None) -> None:
        self.attesters.append(CompositionAttester(mode=mode, party_name=party_name, party_id=party_id, organization=organization, signature=signature))

    def to_resource_bundle(self) -> "ResourceBundle":
        from .resource_bundle import ResourceBundle, BundleType, BundleStatus
        bundle = ResourceBundle(title=self.title, bundle_type=BundleType.DOCUMENT, status=BundleStatus.ACTIVE, version=self.version)
        # If we had embedded resources we could add them here. For now, sections carry text.
        # Enforce at least one entry to satisfy document constraints, add self as entry.
        bundle.add_entry(self, title=self.title or "Composition")
        return bundle


# Backward-compatible Document API overlaying Composition
class Document(Composition):
    resource_type: Literal["Document"] = Field(default="Document")

    def get_word_count(self) -> int:
        # Naive tokenization by whitespace across title/sections
        text_blocks: List[str] = []
        if self.title:
            text_blocks.append(self.title)
        for s in self.sections:
            text_blocks.append(s.title)
            text_blocks.append(s.text)
        return len(" ".join(text_blocks).split())

    # Simple LC shims (optional)
    def to_langchain_document(self):  # pragma: no cover
        return {"page_content": self.text() if hasattr(self, "text") else self.get_full_text(), "metadata": {"title": self.title}}

    @classmethod
    def from_langchain_document(cls, lc_doc):  # pragma: no cover
        return cls(document_type=DocumentType.PROGRESS_NOTE, title=lc_doc.get("metadata", {}).get("title"), subject_id=None)

    def to_langchain_documents(self):  # pragma: no cover
        return [{"page_content": s.text, "metadata": {"title": s.title}} for s in self.sections]


