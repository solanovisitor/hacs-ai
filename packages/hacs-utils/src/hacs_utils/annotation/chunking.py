from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, Sequence

from .data import Document, CharInterval
from hacs_models import TextChunk as TextChunkModel, ChunkingPolicy


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
        # Advance with overlap, ensuring forward progress even when the final chunk is shorter than overlap
        if self.chunk_overlap > 0:
            next_pos = end - self.chunk_overlap
            # Guarantee progress; if overlap would stall, advance to end (which will terminate next iteration)
            self._pos = next_pos if next_pos > self._pos else end
        else:
            self._pos = end
        chunk = TextChunk(start_index=start, end_index=end, document=self.document)
        self._index += 1
        return chunk


def split_by_characters(
    document: Document,
    *,
    chunk_size: int = 1000,
    chunk_overlap: int = 0,
    encoding_name: str | None = None,
) -> list[TextChunk]:
    """Optional LangChain token/character-based splitting.

    Falls back to simple char-based if langchain_text_splitters is unavailable.
    """
    try:
        from langchain_text_splitters import CharacterTextSplitter
    except Exception:
        it = ChunkIterator(document, max_char_buffer=chunk_size, chunk_overlap=chunk_overlap)
        return list(iter(it))

    if encoding_name:
        splitter = CharacterTextSplitter.from_tiktoken_encoder(
            encoding_name=encoding_name, chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
    else:
        splitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    texts = splitter.split_text(document.text)
    chunks: list[TextChunk] = []
    cursor = 0
    for t in texts:
        # find next occurrence from cursor to preserve order
        idx = document.text.find(t, cursor)
        if idx == -1:
            # fallback: search from start (risk duplicates)
            idx = document.text.find(t)
        if idx == -1:
            continue
        start = idx
        end = idx + len(t)
        cursor = end
        chunks.append(TextChunk(start_index=start, end_index=end, document=document))
    return chunks


def split_recursive(
    document: Document,
    *,
    chunk_size: int = 1000,
    chunk_overlap: int = 0,
) -> list[TextChunk]:
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except Exception:
        it = ChunkIterator(document, max_char_buffer=chunk_size, chunk_overlap=chunk_overlap)
        return list(iter(it))

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    texts = splitter.split_text(document.text)
    chunks: list[TextChunk] = []
    cursor = 0
    for t in texts:
        idx = document.text.find(t, cursor)
        if idx == -1:
            idx = document.text.find(t)
        if idx == -1:
            continue
        start = idx
        end = idx + len(t)
        cursor = end
        chunks.append(TextChunk(start_index=start, end_index=end, document=document))
    return chunks


def split_markdown(
    document: Document, *, chunk_size: int = 1000, chunk_overlap: int = 0
) -> list[TextChunk]:
    try:
        from langchain_text_splitters import MarkdownHeaderTextSplitter
    except Exception:
        it = ChunkIterator(document, max_char_buffer=chunk_size, chunk_overlap=chunk_overlap)
        return list(iter(it))

    # Basic header splitter: split by headers; then enforce chunk_size via recursive splitter
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3")]
    )
    try:
        md_docs = splitter.split_text(document.text)
        # md_docs are LC Document objects; concatenate their page_content with a separator
        text_segments = [getattr(d, "page_content", str(d)) for d in md_docs]
        text = "\n\n".join(text_segments)
    except Exception:
        text = document.text

    # Apply recursive size enforcement
    rec = split_recursive(
        Document(text=text, additional_context=document.additional_context),
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return rec


def split_html(
    document: Document, *, chunk_size: int = 1000, chunk_overlap: int = 0
) -> list[TextChunk]:
    try:
        from langchain_text_splitters import HTMLHeaderTextSplitter
    except Exception:
        it = ChunkIterator(document, max_char_buffer=chunk_size, chunk_overlap=chunk_overlap)
        return list(iter(it))

    splitter = HTMLHeaderTextSplitter(headers_to_split_on=[("h1", "h1"), ("h2", "h2"), ("h3", "h3")])
    try:
        html_docs = splitter.split_text(document.text)
        text_segments = [getattr(d, "page_content", str(d)) for d in html_docs]
        text = "\n\n".join(text_segments)
    except Exception:
        text = document.text
    rec = split_recursive(
        Document(text=text, additional_context=document.additional_context),
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return rec


def split_code(
    document: Document, *, chunk_size: int = 1000, chunk_overlap: int = 0, language: str | None = None
) -> list[TextChunk]:
    try:
        # Try language-specific splitters when available; fallback to recursive
        from langchain_text_splitters import (
            PythonCodeTextSplitter,
            RecursiveCharacterTextSplitter,
        )
    except Exception:
        it = ChunkIterator(document, max_char_buffer=chunk_size, chunk_overlap=chunk_overlap)
        return list(iter(it))

    if (language or "").lower() == "python":
        try:
            splitter = PythonCodeTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            texts = splitter.split_text(document.text)
            chunks: list[TextChunk] = []
            cursor = 0
            for t in texts:
                idx = document.text.find(t, cursor)
                if idx == -1:
                    idx = document.text.find(t)
                if idx == -1:
                    continue
                start = idx
                end = idx + len(t)
                cursor = end
                chunks.append(TextChunk(start_index=start, end_index=end, document=document))
            return chunks
        except Exception:
            pass

    # generic fallback
    return split_recursive(document, chunk_size=chunk_size, chunk_overlap=chunk_overlap)


def select_chunks(document: Document, policy: ChunkingPolicy) -> list[TextChunk]:
    """Factory to pick chunker by policy.strategy."""
    strat = (policy.strategy or "char").lower()
    size = policy.max_chars
    overlap = policy.chunk_overlap
    if strat == "char":
        return list(ChunkIterator(document, max_char_buffer=size, chunk_overlap=overlap))
    if strat == "token":
        return split_by_characters(
            document, chunk_size=size, chunk_overlap=overlap, encoding_name=policy.encoding_name
        )
    if strat == "recursive":
        return split_recursive(document, chunk_size=size, chunk_overlap=overlap)
    if strat == "markdown":
        return split_markdown(document, chunk_size=size, chunk_overlap=overlap)
    if strat == "html":
        return split_html(document, chunk_size=size, chunk_overlap=overlap)
    if strat == "code":
        return split_code(document, chunk_size=size, chunk_overlap=overlap)
    # semantic: placeholder -> recursive
    return split_recursive(document, chunk_size=size, chunk_overlap=overlap)


