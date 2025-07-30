"""
Anthropic Integration for HACS

Provides Claude AI model integration for healthcare applications.
"""

try:
    import anthropic
    _has_anthropic = True
except ImportError:
    _has_anthropic = False


class AnthropicClient:
    """Anthropic Claude client for healthcare AI applications."""

    def __init__(self, api_key: str | None = None):
        """Initialize Anthropic client."""
        if not _has_anthropic:
            raise ImportError(
                "Anthropic package not found. Install with: pip install anthropic"
            )

        self.client = anthropic.Anthropic(api_key=api_key)

    def chat(self, messages: list[dict], model: str = "claude-3-sonnet-20240229", **kwargs):
        """Send chat completion request to Claude."""
        response = self.client.messages.create(
            model=model,
            messages=messages,
            **kwargs
        )
        return response


def create_anthropic_client(api_key: str | None = None) -> AnthropicClient:
    """Create an Anthropic client instance."""
    return AnthropicClient(api_key=api_key)


__all__ = [
    "AnthropicClient",
    "create_anthropic_client",
]