from __future__ import annotations

from typing import Any, Dict, Iterator, List, Optional

from hacs_models import (
    AnnotationWorkflowResource,
    PromptTemplateResource,
    ExtractionSchemaResource,
    MappingSpec,
    StackTemplate,
    instantiate_stack_template,
    ResourceBundle,
    BundleEntry,
)

from .data import Document, AnnotatedDocument, FormatType
from .chunking import ChunkIterator, make_batches_of_textchunk
from .prompting import PromptTemplateStructured, QAPromptGenerator
from .inference import BaseLanguageModel, OpenAILanguageModel
from .resolver import AbstractResolver


class Annotator:
    def __init__(
        self,
        language_model: BaseLanguageModel,
        prompt_template: PromptTemplateStructured,
        *,
        format_type: FormatType = FormatType.JSON,
        fenced_output: bool = True,
    ) -> None:
        self._language_model = language_model
        self._prompt_generator = QAPromptGenerator(
            template=prompt_template,
            format_type=format_type,
            fenced_output=fenced_output,
        )

    def annotate_text(
        self,
        text: str,
        resolver: AbstractResolver,
        *,
        max_char_buffer: int = 4000,
        chunk_overlap: int = 0,
        batch_length: int = 4,
        variables: Dict[str, Any] | None = None,
    ) -> AnnotatedDocument:
        doc = Document(text=text)
        chunks = ChunkIterator(doc, max_char_buffer=max_char_buffer, chunk_overlap=chunk_overlap)
        batches = make_batches_of_textchunk(iter(chunks), batch_length)

        all_extractions: list = []
        char_offset = 0
        for batch in batches:
            prompts: list[str] = []
            for ch in batch:
                v = variables or {}
                prompts.append(self._prompt_generator.render(**v, question=ch.chunk_text))

            model_outputs = self._language_model.infer(prompts)
            for ch, outputs in zip(batch, model_outputs):
                if not outputs:
                    char_offset += len(ch.chunk_text) - 0
                    continue
                top = outputs[0].output or ""
                parsed = resolver.parse(top)
                extractions = resolver.resolve(parsed)
                # Align to source chunk to produce CharInterval and AlignmentStatus
                if hasattr(resolver, "align"):
                    try:
                        extractions = resolver.align(extractions, ch.chunk_text, char_offset=ch.start_index)
                    except Exception:
                        # Best-effort: keep unaligned if align fails
                        pass
                all_extractions.extend(extractions)
                # Update running offset conservatively (chunk iterator provides indices)
            # No need to update char_offset here since align uses ch.start_index

        return AnnotatedDocument(document_id=doc.document_id, extractions=all_extractions, text=text)


