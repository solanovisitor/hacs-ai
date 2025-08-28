"""
HACS Model Configuration

Model setup for HACS agents following the DeepAgents pattern.
"""

import os

from langchain_core.language_models import LanguageModelLike


def get_default_model() -> LanguageModelLike:
    """Get default language model for HACS agents."""

    # Try Anthropic first (if available)
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            from langchain_anthropic import ChatAnthropic

            return ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0, max_tokens=4000)
        except ImportError:
            pass

    # Fallback to OpenAI
    if os.getenv("OPENAI_API_KEY"):
        try:
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(model="gpt-4", temperature=0, max_tokens=4000)
        except ImportError:
            pass

    # Last resort: raise error
    raise ValueError(
        "No AI provider available. Please set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable."
    )
