from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator, Sequence

from .data import FormatType


@dataclass(frozen=True)
class ScoredOutput:
    score: float | None = None
    output: str | None = None


class BaseLanguageModel:
    def __init__(self, *, format_type: FormatType = FormatType.JSON) -> None:
        self.format_type = format_type

    def infer(self, batch_prompts: Sequence[str], **kwargs) -> Iterator[Sequence[ScoredOutput]]:  # pragma: no cover
        raise NotImplementedError


class OpenAILanguageModel(BaseLanguageModel):
    def __init__(self, **kwargs) -> None:
        from hacs_utils.integrations.openai.client import OpenAIClient, OpenAIStructuredGenerator

        fmt = kwargs.pop("format_type", FormatType.JSON)
        super().__init__(format_type=fmt)
        self._client = OpenAIClient(**kwargs)
        self._generator = OpenAIStructuredGenerator(client=self._client)

    def infer(self, batch_prompts: Sequence[str], **kwargs) -> Iterator[Sequence[ScoredOutput]]:
        for prompt in batch_prompts:
            # Prefer structured generation when response_model provided
            response_model = kwargs.pop("response_model", None)
            if response_model is not None:
                obj = self._generator.generate_hacs_resource(response_model, user_prompt=prompt)
                yield [ScoredOutput(score=None, output=obj.json())]
                continue
            messages = [{"role": "user", "content": prompt}]
            resp = self._client.chat(messages, **kwargs)
            content = resp.choices[0].message.content if getattr(resp, "choices", None) else ""
            yield [ScoredOutput(score=None, output=content)]


