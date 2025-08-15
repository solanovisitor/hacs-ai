from __future__ import annotations

import json
from typing import Any, Dict, List

import yaml

from .data import FormatType, Extraction, CharInterval, AlignmentStatus


def extract_fenced_or_raw(output: str) -> str:
    """Extract fenced code block content if present, else return raw output."""
    output = output.strip()
    if output.startswith("```"):
        # simple fence extraction
        parts = output.split("\n", 1)
        if len(parts) == 2:
            body = parts[1]
            if "```" in body:
                return body.rsplit("```", 1)[0].strip()
    return output


class AbstractResolver:
    def __init__(self, format_type: FormatType = FormatType.JSON) -> None:
        self.format_type = format_type

    def parse(self, output: str) -> Any:
        raw = extract_fenced_or_raw(output)
        if self.format_type == FormatType.JSON:
            return json.loads(raw)
        return yaml.safe_load(raw)

    def resolve(self, parsed_output: Any) -> List[Extraction]:
        """Convert parsed output into Extraction objects.

        Default: if an array of {extraction_class, extraction_text} is present, map directly.
        Apps are expected to provide a richer resolver per schema.
        """
        extractions: list[Extraction] = []
        if isinstance(parsed_output, list):
            for item in parsed_output:
                if isinstance(item, dict) and "extraction_class" in item and "extraction_text" in item:
                    extractions.append(
                        Extraction(
                            extraction_class=str(item["extraction_class"]),
                            extraction_text=str(item["extraction_text"]),
                        )
                    )
        return extractions


class Resolver(AbstractResolver):
    """Concrete resolver with basic alignment to source text.

    - resolve: same default behavior, mapping list of dicts to Extraction
    - align: assigns char intervals by locating extraction_text in chunk_text
    """

    def resolve(self, parsed_output: Any) -> List[Extraction]:
        return super().resolve(parsed_output)

    def align(
        self,
        extractions: List[Extraction],
        chunk_text: str,
        *,
        char_offset: int = 0,
        case_insensitive: bool = True,
    ) -> List[Extraction]:
        aligned: List[Extraction] = []
        haystack_ci = chunk_text.lower() if case_insensitive else chunk_text
        for ex in extractions:
            text = ex.extraction_text or ""
            if not text:
                aligned.append(ex)
                continue
            needle = text.lower() if case_insensitive else text
            start_local = haystack_ci.find(needle)
            if start_local >= 0:
                end_local = start_local + len(text)
                ex.char_interval = CharInterval(
                    start_pos=char_offset + start_local,
                    end_pos=char_offset + end_local,
                )
                ex.alignment_status = AlignmentStatus.MATCH_EXACT
            else:
                ex.alignment_status = AlignmentStatus.MATCH_FUZZY
            aligned.append(ex)
        return aligned

