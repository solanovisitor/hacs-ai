"""
Anthropic Client Implementation for HACS

Enhanced Anthropic client with structured outputs, tool use, and MCP support.
"""

import json
from typing import Any, Dict, List, Optional, Type, Union
from pydantic import BaseModel
from dotenv import load_dotenv, dotenv_values

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

        load_dotenv()
        resolved_key = api_key or dotenv_values().get("ANTHROPIC_API_KEY")
        self.client = Anthropic(
            api_key=resolved_key,
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
        # Create a tool schema from the Pydantic model (simplified for Claude tools)
        raw_schema = response_model.model_json_schema()
        schema = self._simplify_schema_for_tool(raw_schema)

        tool_schema = {
            "name": "extract_data",
            "description": f"Extract data according to the {response_model.__name__} schema",
            "input_schema": schema,
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
            if hasattr(content, "type") and content.type == "tool_use":
                if content.name == "extract_data":
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
            if hasattr(content, "type") and content.type == "tool_use":
                tool_calls.append(
                    {
                        "id": content.id,
                        "name": content.name,
                        "input": content.input,
                    }
                )

        return tool_calls

    def create_tool_result_message(self, tool_use_id: str, result: str) -> Dict[str, Any]:
        """Create a properly formatted tool result message."""
        return {
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": tool_use_id, "content": result}],
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
            if hasattr(content, "type") and content.type == "text":
                text_content.append(content.text)

        return "\n".join(text_content)

    async def ainvoke(self, prompt: Union[str, List[Dict[str, Any]]], **kwargs) -> str:
        """Async invoke method (delegates to sync for now)."""
        return self.invoke(prompt, **kwargs)

    # ---- Utilities ----
    def to_langchain(self):
        """Return a LangChain ChatAnthropic instance configured like this client.

        Skips if langchain-anthropic is not installed.
        """
        try:
            from langchain_anthropic import ChatAnthropic  # type: ignore
        except Exception as e:  # pragma: no cover - optional dep
            raise ImportError(f"langchain-anthropic not available: {e}")

        load_dotenv()
        kv = dotenv_values()
        api_key = kv.get("ANTHROPIC_API_KEY")
        return ChatAnthropic(
            model=self.model,
            max_retries=self.max_retries,
            timeout=self.timeout,
            api_key=api_key,
        )

    # ---- Utilities ----
    @staticmethod
    def _simplify_schema_for_tool(schema: Dict[str, Any]) -> Dict[str, Any]:
        """Best-effort simplification of Pydantic JSON schema for Anthropic tool input.

        - Flattens anyOf/oneOf by taking the first branch
        - Removes unsupported keys ($ref, definitions)
        - Preserves enum, type, properties, required, description
        """

        def simplify(node: Any) -> Any:
            if isinstance(node, dict):
                # Prefer first anyOf/oneOf branch
                if "anyOf" in node and isinstance(node["anyOf"], list) and node["anyOf"]:
                    return simplify(node["anyOf"][0])
                if "oneOf" in node and isinstance(node["oneOf"], list) and node["oneOf"]:
                    return simplify(node["oneOf"][0])

                allowed_keys = {
                    "type",
                    "properties",
                    "required",
                    "enum",
                    "items",
                    "description",
                    "title",
                }
                cleaned: Dict[str, Any] = {}
                for k, v in node.items():
                    if k in {"$ref", "$defs", "definitions"}:
                        continue
                    if k in allowed_keys:
                        cleaned[k] = simplify(v)
                # Ensure object with properties has required list
                if (
                    cleaned.get("type") == "object"
                    and "properties" in cleaned
                    and "required" not in cleaned
                ):
                    cleaned["required"] = [k for k in cleaned["properties"].keys()][
                        :0
                    ]  # default empty
                return cleaned
            if isinstance(node, list):
                return [simplify(it) for it in node]
            return node

        simplified = simplify(schema)
        # If model root is not an object, wrap in an object with a single field "value"
        if not isinstance(simplified, dict) or simplified.get("type") != "object":
            simplified = {
                "type": "object",
                "properties": {"value": simplified},
                "required": ["value"],
            }
        return simplified

    def run_tool_cycle(
        self,
        *,
        user_prompt: str,
        tools: List[Dict[str, Any]],
        exec_map: Dict[str, Any],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        """Single-cycle tool-use loop.

        - Sends user prompt with tools
        - Extracts the first tool call and executes mapped function
        - Sends tool_result and returns assistant text
        """
        initial = self.tool_use(
            messages=[{"role": "user", "content": user_prompt}],
            tools=tools,
            model=model,
            max_tokens=max_tokens,
            **kwargs,
        )
        calls = self.extract_tool_calls(initial)
        if not calls:
            # return any text content directly
            text_parts = [c.text for c in initial.content if getattr(c, "type", "") == "text"]
            return "\n".join(text_parts)

        call = calls[0]
        fn = exec_map.get(call["name"])  # type: ignore[index]
        result_text = ""
        if callable(fn):
            try:
                result = fn(**call["input"])  # type: ignore[misc]
                result_text = json.dumps(result) if not isinstance(result, str) else result
            except Exception as e:
                result_text = f"ERROR: {e}"

        followup = self.tool_use(
            messages=[
                {"role": "user", "content": user_prompt},
                {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "tool_use",
                            "id": call["id"],
                            "name": call["name"],
                            "input": call["input"],
                        }
                    ],
                },
                self.create_tool_result_message(call["id"], result_text),
            ],
            tools=tools,
            model=model,
            max_tokens=max_tokens,
            **kwargs,
        )
        text_parts = [c.text for c in followup.content if getattr(c, "type", "") == "text"]
        return "\n".join(text_parts)


def create_anthropic_client(
    model: str = "claude-sonnet-4-20250514", api_key: Optional[str] = None, **kwargs
) -> AnthropicClient:
    """Factory function to create an Anthropic client."""
    return AnthropicClient(model=model, api_key=api_key, **kwargs)


# Convenience function for structured extraction
def anthropic_structured_extract(
    prompt: str,
    response_model: Type[BaseModel],
    api_key: Optional[str] = None,
    model: str = "claude-sonnet-4-20250514",
    **kwargs,
) -> BaseModel:
    """One-shot structured extraction using Claude."""
    client = create_anthropic_client(model=model, api_key=api_key)
    return client.structured_output(prompt, response_model, **kwargs)
