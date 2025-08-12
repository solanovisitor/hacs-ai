from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, Sequence

from .data import Document, CharInterval
from hacs_models import TextChunk as TextChunkModel


@dataclass
class TextChunk:
    start_index: int
    end_index: int
    document: Document

    @property
    def chunk_text(self) -> str:
        return self.document.text[self.start_index : self.end_index]

    @property
    def char_interval(self) -> CharInterval:
        return CharInterval(start_pos=self.start_index, end_pos=self.end_index)

    def to_model(self, *, chunk_index: int | None = None) -> TextChunkModel:
        return TextChunkModel(
            start_pos=self.start_index,
            end_pos=self.end_index,
            document_id=self.document.document_id,
            additional_context=self.document.additional_context,
            chunk_index=chunk_index,
        )


def _sanitize(text: str) -> str:
    return " ".join(text.split())


def make_batches_of_textchunk(
    chunk_iter: Iterator[TextChunk], batch_length: int
) -> Iterable[Sequence[TextChunk]]:
    batch: list[TextChunk] = []
    for chunk in chunk_iter:
        batch.append(chunk)
        if len(batch) >= batch_length:
            yield list(batch)
            batch.clear()
    if batch:
        yield list(batch)


class ChunkIterator:
    """Simple char-length chunk iterator with optional sentence boundaries in future.

    For now, this keeps implementation minimal and dependency-free.
    """

    def __init__(self, document: Document, max_char_buffer: int = 4000, chunk_overlap: int = 0):
        self.document = document
        self.max_char_buffer = max_char_buffer
        self.chunk_overlap = max(0, min(chunk_overlap, max_char_buffer - 1))
        self._pos = 0
        self._n = len(document.text)
        self._index = 0

    def __iter__(self) -> Iterator[TextChunk]:
        return self

    def __next__(self) -> TextChunk:
        if self._pos >= self._n:
            raise StopIteration
        start = self._pos
        end = min(self._pos + self.max_char_buffer, self._n)
        # Advance with overlap
        self._pos = end - self.chunk_overlap if self.chunk_overlap > 0 else end
        chunk = TextChunk(start_index=start, end_index=end, document=self.document)
        self._index += 1
        return chunk


