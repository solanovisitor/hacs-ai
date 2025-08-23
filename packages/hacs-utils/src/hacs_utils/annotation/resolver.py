from __future__ import annotations

import json
from typing import Any, List

import yaml

from .data import FormatType, ExtractionResults, CharInterval, AlignmentStatus


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

    def resolve(self, parsed_output: Any) -> List[ExtractionResults]:
        """Convert parsed output into Extraction objects.

        Default: if an array of {extraction_class, extraction_text} is present, map directly.
        Apps are expected to provide a richer resolver per schema.
        """
        extractions: list[ExtractionResults] = []
        if isinstance(parsed_output, list):
            for item in parsed_output:
                if (
                    isinstance(item, dict)
                    and "extraction_class" in item
                    and "extraction_text" in item
                ):
                    extractions.append(
                        ExtractionResults(
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

    def resolve(self, parsed_output: Any) -> List[ExtractionResults]:
        return super().resolve(parsed_output)

    def align(
        self,
        extractions: List[ExtractionResults],
        text: str,
        *,
        char_offset: int = 0,
        case_insensitive: bool = True,
    ) -> List[ExtractionResults]:
        aligned: List[ExtractionResults] = []
        for e in extractions or []:
            if not e or not getattr(e, "extraction_text", None):
                aligned.append(e)
                continue
            needle = e.extraction_text
            haystack = text
            index = -1
            if case_insensitive:
                index = haystack.lower().find(needle.lower())
            else:
                index = haystack.find(needle)
            if index >= 0:
                start = char_offset + index
                end = start + len(needle)
                ci = CharInterval(start_pos=start, end_pos=end) if CharInterval else None
                try:
                    from hacs_models import ExtractionResults as ExtractionDC  # type: ignore
                except Exception:
                    ExtractionDC = None  # type: ignore
                if ExtractionDC:
                    aligned.append(
                        ExtractionDC(
                            extraction_class=e.extraction_class,
                            extraction_text=e.extraction_text,
                            char_interval=ci,
                            alignment_status=AlignmentStatus.MATCH_EXACT if AlignmentStatus else None,
                            extraction_index=e.extraction_index,
                            group_index=e.group_index,
                            description=e.description,
                            attributes=e.attributes,
                        )
                    )
                else:
                    aligned.append(e)
            else:
                aligned.append(e)
        return aligned
