from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, Sequence

from .data import Document, CharInterval


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

    def __init__(self, document: Document, max_char_buffer: int = 4000):
        self.document = document
        self.max_char_buffer = max_char_buffer
        self._pos = 0
        self._n = len(document.text)

    def __iter__(self) -> Iterator[TextChunk]:
        return self

    def __next__(self) -> TextChunk:
        if self._pos >= self._n:
            raise StopIteration
        start = self._pos
        end = min(self._pos + self.max_char_buffer, self._n)
        self._pos = end
        return TextChunk(start_index=start, end_index=end, document=self.document)


