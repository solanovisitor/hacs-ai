from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from .base_resource import DomainResource
from .types import ConfidentialityLevel, DocumentStatus, DocumentType


class CompositionAuthor(DomainResource):
    resource_type: Literal["CompositionAuthor"] = Field(default="CompositionAuthor")
    name: str | None = None
    role: str | None = None
    organization: str | None = None
    specialty: str | None = None


class CompositionAttester(DomainResource):
    resource_type: Literal["CompositionAttester"] = Field(default="CompositionAttester")
    mode: Literal["professional", "legal", "official", "personal"] = "professional"
    party_name: str | None = None
    party_id: str | None = None
    organization: str | None = None
    signature: str | None = None


class CompositionSection(DomainResource):
    resource_type: Literal["CompositionSection"] = Field(default="CompositionSection")
    title: str
    text: str
    code: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    sections: list[CompositionSection] = Field(
        default_factory=list, description="Nested sections"
    )


class CompositionEncounter(DomainResource):
    resource_type: Literal["CompositionEncounter"] = Field(default="CompositionEncounter")
    encounter_id: str | None = None
    encounter_reference: str | None = None


class Composition(DomainResource):
    resource_type: Literal["Composition"] = Field(default="Composition")
    document_type: DocumentType | None = None
    title: str | None = None
    subject_id: str | None = None
    subject_name: str | None = None
    status: DocumentStatus = Field(default=DocumentStatus.PRELIMINARY)
    confidentiality: ConfidentialityLevel = Field(default=ConfidentialityLevel.NORMAL)
    document_identifier: str | None = Field(default=None)
    authors: list[CompositionAuthor] = Field(default_factory=list)
    attesters: list[CompositionAttester] = Field(default_factory=list)
    sections: list[CompositionSection] = Field(default_factory=list)
    encounter: CompositionEncounter | None = None

    def add_section(
        self,
        title: str,
        text: str,
        code: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.sections.append(
            CompositionSection(title=title, text=text, code=code, metadata=metadata or {})
        )

    def add_author(
        self,
        name: str,
        role: str | None = None,
        organization: str | None = None,
        specialty: str | None = None,
    ) -> None:
        self.authors.append(
            CompositionAuthor(name=name, role=role, organization=organization, specialty=specialty)
        )

    def add_attester(
        self,
        mode: str,
        party_name: str,
        party_id: str,
        organization: str | None = None,
        signature: str | None = None,
    ) -> None:
        self.attesters.append(
            CompositionAttester(
                mode=mode,
                party_name=party_name,
                party_id=party_id,
                organization=organization,
                signature=signature,
            )
        )

    def to_resource_bundle(self) -> ResourceBundle:
        from .resource_bundle import BundleStatus, BundleType, ResourceBundle

        bundle = ResourceBundle(
            title=self.title,
            bundle_type=BundleType.DOCUMENT,
            status=BundleStatus.ACTIVE,
            version=self.version,
        )
        # If we had embedded resources we could add them here. For now, sections carry text.
        # Enforce at least one entry to satisfy document constraints, add self as entry.
        bundle.add_entry(self, title=self.title or "Composition")
        return bundle


# Backward-compatible Document API overlaying Composition
class Document(Composition):
    resource_type: Literal["Document"] = Field(default="Document")

    def get_word_count(self) -> int:
        # Naive tokenization by whitespace across title/sections
        text_blocks: list[str] = []
        if self.title:
            text_blocks.append(self.title)
        for s in self.sections:
            text_blocks.append(s.title)
            text_blocks.append(s.text)
        return len(" ".join(text_blocks).split())

    # Simple LC shims (optional)
    def to_langchain_document(self):  # pragma: no cover
        return {
            "page_content": self.text() if hasattr(self, "text") else self.get_full_text(),
            "metadata": {"title": self.title},
        }

    @classmethod
    def from_langchain_document(cls, lc_doc):  # pragma: no cover
        return cls(
            document_type=DocumentType.PROGRESS_NOTE,
            title=lc_doc.get("metadata", {}).get("title"),
            subject_id=None,
        )

    def to_langchain_documents(self):  # pragma: no cover
        return [{"page_content": s.text, "metadata": {"title": s.title}} for s in self.sections]
