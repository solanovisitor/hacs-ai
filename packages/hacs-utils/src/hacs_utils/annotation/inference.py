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


class AnthropicLanguageModel(BaseLanguageModel):
    def __init__(self, **kwargs) -> None:
        # Defer import to keep optional
        import os
        from anthropic import Anthropic

        fmt = kwargs.pop("format_type", FormatType.JSON)
        super().__init__(format_type=fmt)
        api_key = kwargs.pop("api_key", os.getenv("ANTHROPIC_API_KEY"))
        self._client = Anthropic(api_key=api_key)
        self._model = kwargs.pop("model", "claude-3-7-sonnet-latest")
        self._max_tokens = kwargs.pop("max_tokens", 1024)

    def infer(self, batch_prompts: Sequence[str], **kwargs) -> Iterator[Sequence[ScoredOutput]]:
        # Basic non-streaming implementation; can add streaming later
        for prompt in batch_prompts:
            msg = self._client.messages.create(
                model=self._model,
                max_tokens=kwargs.get("max_tokens", self._max_tokens),
                messages=[{"role": "user", "content": prompt}],
            )
            # msg.content is a list of content blocks; concatenate text blocks
            parts = []
            for block in getattr(msg, "content", []) or []:
                if getattr(block, "type", None) == "text":
                    parts.append(getattr(block, "text", ""))
            content = "".join(parts)
            yield [ScoredOutput(score=None, output=content)]


