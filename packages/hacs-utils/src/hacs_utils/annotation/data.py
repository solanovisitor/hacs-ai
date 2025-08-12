from __future__ import annotations

import dataclasses
import enum
import uuid
from typing import Any, Dict, List, Optional


class AlignmentStatus(enum.Enum):
    MATCH_EXACT = "match_exact"
    MATCH_GREATER = "match_greater"
    MATCH_LESSER = "match_lesser"
    MATCH_FUZZY = "match_fuzzy"


@dataclasses.dataclass
class CharInterval:
    start_pos: int | None = None
    end_pos: int | None = None


@dataclasses.dataclass(init=False)
class Extraction:
    extraction_class: str
    extraction_text: str
    char_interval: CharInterval | None = None
    alignment_status: AlignmentStatus | None = None
    extraction_index: int | None = None
    group_index: int | None = None
    description: str | None = None
    attributes: dict[str, str | list[str]] | None = None

    def __init__(
        self,
        extraction_class: str,
        extraction_text: str,
        *,
        char_interval: CharInterval | None = None,
        alignment_status: AlignmentStatus | None = None,
        extraction_index: int | None = None,
        group_index: int | None = None,
        description: str | None = None,
        attributes: dict[str, str | list[str]] | None = None,
    ):
        self.extraction_class = extraction_class
        self.extraction_text = extraction_text
        self.char_interval = char_interval
        self.alignment_status = alignment_status
        self.extraction_index = extraction_index
        self.group_index = group_index
        self.description = description
        self.attributes = attributes


@dataclasses.dataclass
class Document:
    text: str
    additional_context: str | None = None
    _document_id: str | None = dataclasses.field(default=None, init=False, repr=False, compare=False)

    def __init__(self, text: str, *, document_id: str | None = None, additional_context: str | None = None):
        self.text = text
        self.additional_context = additional_context
        self._document_id = document_id

    @property
    def document_id(self) -> str:
        if self._document_id is None:
            self._document_id = f"doc_{uuid.uuid4().hex[:8]}"
        return self._document_id

    @document_id.setter
    def document_id(self, value: str | None) -> None:
        self._document_id = value


@dataclasses.dataclass
class AnnotatedDocument:
    extractions: list[Extraction] | None = None
    text: str | None = None
    _document_id: str | None = dataclasses.field(default=None, init=False, repr=False, compare=False)

    def __init__(self, *, document_id: str | None = None, extractions: list[Extraction] | None = None, text: str | None = None):
        self.extractions = extractions
        self.text = text
        self._document_id = document_id

    @property
    def document_id(self) -> str:
        if self._document_id is None:
            self._document_id = f"doc_{uuid.uuid4().hex[:8]}"
        return self._document_id

    @document_id.setter
    def document_id(self, value: str | None) -> None:
        self._document_id = value


class FormatType(enum.Enum):
    YAML = "yaml"
    JSON = "json"


