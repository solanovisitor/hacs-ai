"""
Anthropic Client Implementation for HACS

Enhanced Anthropic client with structured outputs, tool use, and MCP support.
"""

import json
import os
from typing import Any, Dict, List, Optional, Type, Union
from pydantic import BaseModel

try:
    import anthropic
    from anthropic import Anthropic
except ImportError:
    anthropic = None
    Anthropic = None


class AnthropicClient:
    """Enhanced Anthropic client with HACS integration."""

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        max_tokens: int = 1024,
    ):
        """Initialize Anthropic client with configurable parameters."""
        if not anthropic:
            raise ImportError("anthropic not available. Install with: pip install anthropic")

        self.model = model
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries

        self.client = Anthropic(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
            timeout=timeout,
            max_retries=max_retries,
        )

    def chat(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        **kwargs,
    ) -> "anthropic.types.Message":
        """Send chat messages to Claude."""
        return self.client.messages.create(
            model=model or self.model,
            max_tokens=max_tokens or self.max_tokens,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            **kwargs,
        )

    def structured_output(
        self,
        prompt: str,
        response_model: Type[BaseModel],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> BaseModel:
        """Generate structured output using tool-based JSON mode.
        
        Uses Claude's tool use capability to enforce JSON schema compliance.
        """
        # Create a tool schema from the Pydantic model
        schema = response_model.model_json_schema()
        
        tool_schema = {
            "name": "extract_data",
            "description": f"Extract data according to the {response_model.__name__} schema",
            "input_schema": schema
        }

        response = self.client.messages.create(
            model=model or self.model,
            max_tokens=max_tokens or self.max_tokens,
            tools=[tool_schema],
            tool_choice={"type": "tool", "name": "extract_data"},
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )

        # Extract tool use input as the structured data
        for content in response.content:
            if hasattr(content, 'type') and content.type == 'tool_use':
                if content.name == 'extract_data':
                    return response_model.model_validate(content.input)
        
        raise ValueError("No structured tool use found in Claude's response")

    def tool_use(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        **kwargs,
    ) -> "anthropic.types.Message":
        """Execute tool use with Claude."""
        return self.client.messages.create(
            model=model or self.model,
            max_tokens=max_tokens or self.max_tokens,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            **kwargs,
        )

    def extract_tool_calls(self, response: "anthropic.types.Message") -> List[Dict[str, Any]]:
        """Extract tool calls from Claude's response."""
        tool_calls = []
        
        for content in response.content:
            if hasattr(content, 'type') and content.type == 'tool_use':
                tool_calls.append({
                    "id": content.id,
                    "name": content.name,
                    "input": content.input,
                })
        
        return tool_calls

    def create_tool_result_message(
        self, 
        tool_use_id: str, 
        result: str
    ) -> Dict[str, Any]:
        """Create a properly formatted tool result message."""
        return {
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": result
            }]
        }

    def invoke(self, prompt: Union[str, List[Dict[str, Any]]], **kwargs) -> str:
        """Generic invoke method for compatibility with other providers."""
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        else:
            messages = prompt

        response = self.chat(messages, **kwargs)
        
        # Extract text content from response
        text_content = []
        for content in response.content:
            if hasattr(content, 'type') and content.type == 'text':
                text_content.append(content.text)
        
        return "\n".join(text_content)

    async def ainvoke(self, prompt: Union[str, List[Dict[str, Any]]], **kwargs) -> str:
        """Async invoke method (delegates to sync for now)."""
        return self.invoke(prompt, **kwargs)


def create_anthropic_client(
    model: str = "claude-sonnet-4-20250514",
    api_key: Optional[str] = None,
    **kwargs
) -> AnthropicClient:
    """Factory function to create an Anthropic client."""
    return AnthropicClient(
        model=model,
        api_key=api_key,
        **kwargs
    )


# Convenience function for structured extraction
def anthropic_structured_extract(
    prompt: str,
    response_model: Type[BaseModel],
    api_key: Optional[str] = None,
    model: str = "claude-sonnet-4-20250514",
    **kwargs
) -> BaseModel:
    """One-shot structured extraction using Claude."""
    client = create_anthropic_client(model=model, api_key=api_key)
    return client.structured_output(prompt, response_model, **kwargs)
