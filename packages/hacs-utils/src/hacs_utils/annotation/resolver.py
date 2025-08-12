from __future__ import annotations

import json
from typing import Any, Dict, List

import yaml

from .data import FormatType, Extraction


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


