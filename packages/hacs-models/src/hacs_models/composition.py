from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from .base_resource import DomainResource
from .observation import CodeableConcept
from .types import (
    ConfidentialityLevel,
    DocumentStatus,
    DocumentType,
    ResourceReference,
    TimestampStr,
)


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
    # FHIR-aligned additions: coded section and entries
    section_code: CodeableConcept | None = None
    entry_refs: list[ResourceReference] = Field(
        default_factory=list, description="References to resources in this section"
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
    # FHIR-aligned additions
    type_code: CodeableConcept | None = Field(default=None, description="Composition.type code")
    subject_ref: ResourceReference | None = Field(default=None, description="Subject reference")
    date: TimestampStr | None = Field(default=None, description="Document date/time")
    author_refs: list[ResourceReference] = Field(default_factory=list)
    custodian_ref: ResourceReference | None = Field(default=None)

    def add_section(
        self,
        title: str,
        text: str,
        code: str | None = None,
        metadata: dict[str, Any] | None = None,
        section_code: CodeableConcept | None = None,
        entry_refs: list[ResourceReference] | None = None,
    ) -> None:
        self.sections.append(
            CompositionSection(
                title=title,
                text=text,
                code=code,
                metadata=metadata or {},
                section_code=section_code,
                entry_refs=entry_refs or [],
            )
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

    def to_resource_bundle(self):
        from .resource_bundle import BundleEntry, BundleStatus, BundleType, ResourceBundle

        bundle = ResourceBundle(
            title=self.title,
            bundle_type=BundleType.DOCUMENT,
            status=BundleStatus.ACTIVE,
            version=self.version,
            entries=[
                BundleEntry(
                    title=self.title or "Composition",
                    resource=self,
                    contained_resource_id=getattr(self, "id", None),
                )
            ],
        )
        # Include referenced resources if provided via section.entry_refs
        for section in self.sections:
            for _ref in section.entry_refs:
                # In HACS, we don't dereference; callers should add resources explicitly.
                # Here we only track references; actual resource inclusion is handled by caller.
                # This method remains a convenience to build a document bundle shell.
                pass
        return bundle

    def to_document_bundle(self, included_resources: list[Any] | None = None):
        """Create a FHIR-like document bundle including Composition and provided resources.

        - Composition is inserted as the first entry (as required by FHIR).
        - All resources passed in included_resources are added as subsequent entries.
        - This helper does not attempt to resolve references automatically; callers
          should pass the exact resource objects they want included.
        """
        from .resource_bundle import BundleEntry, BundleStatus, BundleType, ResourceBundle

        bundle = ResourceBundle(
            title=self.title,
            bundle_type=BundleType.DOCUMENT,
            status=BundleStatus.ACTIVE,
            version=self.version,
            entries=[
                BundleEntry(
                    title=self.title or "Composition",
                    resource=self,
                    contained_resource_id=getattr(self, "id", None),
                )
            ],
        )
        for res in included_resources or []:
            bundle.add_entry(res, title=getattr(res, "resource_type", None))
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
