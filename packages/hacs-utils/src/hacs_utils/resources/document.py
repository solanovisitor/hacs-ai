from __future__ import annotations

from typing import Dict, Any, List


def get_document_full_text(document_data: Dict[str, Any]) -> str:
    text_parts: List[str] = []
    title = document_data.get("title", "")
    if title:
        text_parts.append(title)
    sections = document_data.get("section", [])
    for section in sections:
        section_title = section.get("title", "")
        if section_title:
            text_parts.append(section_title)
        section_text = section.get("text", "")
        if section_text:
            text_parts.append(section_text)
    return "\n\n".join(text_parts)


