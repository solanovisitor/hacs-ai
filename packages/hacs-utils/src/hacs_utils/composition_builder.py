"""
CompositionBuilder: assemble HACS Composition with coded sections and entries.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from hacs_models.composition import Composition
from hacs_models.observation import CodeableConcept
from hacs_utils.document.attachments import create_markdown_document
from hacs_utils.document.section_codes import resolve_section_code


class CompositionBuilder:
    def __init__(self, title: str, subject_id: Optional[str] = None):
        self.composition = Composition(title=title, subject_id=subject_id)
        self._resources: List[Any] = []

    def add_section(
        self,
        title: str,
        markdown: Optional[str] = None,
        *,
        section_code: Optional[CodeableConcept] = None,
        entry_resources: Optional[List[Any]] = None,
        code: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        entry_refs = []
        for res in entry_resources or []:
            self._resources.append(res)
            if hasattr(res, "to_reference"):
                entry_refs.append(res.to_reference())
        # Auto-resolve section code if not provided
        resolved_code = section_code or resolve_section_code(title)
        if (markdown or "") or entry_refs:
            self.composition.add_section(
                title=title,
                text=markdown or "",
                code=code,
                metadata=metadata or {},
                section_code=resolved_code,
                entry_refs=entry_refs,
            )

    def build_bundle(self):
        return self.composition.to_document_bundle(self._resources)

    def add_attachment_to_section(
        self,
        section_title: str,
        *,
        markdown_text: Optional[str] = None,
        title: Optional[str] = None,
        subject_ref: Optional[str] = None,
    ) -> None:
        """Create a DocumentReference (markdown) and link it into the named section.

        - Creates the section if missing and content is provided.
        - Adds the DocumentReference to included resources and as an entry_ref.
        """
        if not markdown_text:
            return
        docref = create_markdown_document(markdown_text, title=title, subject_ref=subject_ref)
        # track resource for bundle inclusion
        self._resources.append(docref)

        # find or create section
        target = None
        for s in self.composition.sections:
            if s.title == section_title:
                target = s
                break
        if target is None:
            # create empty section first
            self.composition.add_section(title=section_title, text="")
            target = self.composition.sections[-1]

        # add reference
        if hasattr(docref, "to_reference"):
            target.entry_refs.append(docref.to_reference())


