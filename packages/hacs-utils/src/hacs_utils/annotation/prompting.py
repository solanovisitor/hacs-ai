from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from .data import FormatType


@dataclass
class PromptTemplateStructured:
    template_text: str
    variables: List[str]
    format_type: FormatType = FormatType.JSON
    fenced_output: bool = True


class QAPromptGenerator:
    def __init__(
        self,
        template: PromptTemplateStructured,
        *,
        format_type: FormatType = FormatType.JSON,
        attribute_suffix: str = "_attributes",
        fenced_output: bool = True,
    ) -> None:
        self.template = template
        self.format_type = format_type
        self.attribute_suffix = attribute_suffix
        self.fenced_output = fenced_output

    def render(self, **variables: Any) -> str:
        # naive format; developers can override at registry level
        text = self.template.template_text.format(**variables)
        if self.fenced_output:
            fence = "json" if self.format_type == FormatType.JSON else "yaml"
            return f"Return strictly {fence} within fenced code block.\n```{fence}\n" + text + "\n```"
        return text


