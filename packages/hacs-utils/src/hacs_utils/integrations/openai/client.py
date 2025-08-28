"""
OpenAI Client Implementation for HACS
"""

import json
from collections.abc import Callable
from typing import Any
from dotenv import load_dotenv, dotenv_values

try:
    import openai
    from openai import OpenAI
except ImportError:
    openai = None
    OpenAI = None

try:
    import instructor
except ImportError:
    instructor = None

from pydantic import BaseModel


class OpenAIClient:
    """Enhanced OpenAI client with HACS integration."""

    def __init__(
        self,
        model: str = "gpt-4.1",
        api_key: str | None = None,
        base_url: str | None = None,
        organization: str | None = None,
        timeout: float | None = None,
        max_retries: int = 3,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
    ):
        """Initialize OpenAI client with configurable parameters."""
        if not openai:
            raise ImportError("openai not available. Install with: pip install openai")

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty

        load_dotenv()
        resolved_key = api_key or dotenv_values().get("OPENAI_API_KEY")
        self.client = OpenAI(
            api_key=resolved_key,
            base_url=base_url,
            organization=organization,
            timeout=timeout,
            max_retries=max_retries,
        )

    # ---- Adapters ----
    def to_langchain(self):
        """Return a LangChain ChatOpenAI instance configured like this client.

        Skips if langchain_openai is not installed.
        """
        try:
            from langchain_openai import ChatOpenAI  # type: ignore
        except Exception as e:  # pragma: no cover - optional dep
            raise ImportError(f"langchain-openai not available: {e}")

        load_dotenv()
        kv = dotenv_values()
        api_key = kv.get("OPENAI_API_KEY")
        # Map basic params
        return ChatOpenAI(
            model=self.model,
            temperature=self.temperature,
            max_retries=self.client.max_retries if hasattr(self.client, "max_retries") else 1,
            timeout=self.client.timeout if hasattr(self.client, "timeout") else 30,
            api_key=api_key,
        )

        # Setup instructor if available
        self.instructor_client = None
        if instructor:
            self.instructor_client = instructor.from_openai(self.client)

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | None = None,
        **kwargs,
    ) -> "openai.types.chat.ChatCompletion":
        """Standard chat completion with graceful param fallbacks for newer models."""
        params: dict[str, Any] = {
            "model": model or self.model,
            "messages": messages,
            "max_completion_tokens": max_tokens or self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
        }
        if tools is not None:
            params["tools"] = tools
        if tool_choice is not None:
            params["tool_choice"] = tool_choice
        # Try with temperature; some models reject non-default temperature
        if temperature is not None:
            params["temperature"] = temperature
        elif self.temperature is not None:
            params["temperature"] = self.temperature
        try:
            return self.client.chat.completions.create(**params)
        except Exception as e:
            # Retry without temperature if model rejects it
            msg = str(e)
            if "temperature" in msg and ("unsupported" in msg or "does not support" in msg):
                params.pop("temperature", None)
                return self.client.chat.completions.create(**params)
            raise

    def structured_output(
        self,
        messages: list[dict[str, str]],
        response_model: type[BaseModel],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> BaseModel:
        """Generate structured output using instructor."""
        if not self.instructor_client:
            raise ImportError("instructor not available. Install with: pip install instructor")

        return self.instructor_client.chat.completions.create(
            model=model or self.model,
            response_model=response_model,
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
            **kwargs,
        )

    def native_structured_output(
        self,
        messages: list[dict[str, str]],
        response_schema: dict[str, Any],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Generate structured output using OpenAI's native structured outputs."""
        response = self.client.chat.completions.create(
            model=model or self.model,
            messages=messages,
            temperature=temperature or self.temperature,
            max_completion_tokens=max_tokens or self.max_tokens,
            top_p=self.top_p,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "response", "schema": response_schema},
            },
            **kwargs,
        )

        return json.loads(response.choices[0].message.content)

    def responses_parse(
        self,
        input_messages: list[dict[str, str]],
        response_model: type[BaseModel],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        **kwargs,
    ) -> BaseModel:
        """Use OpenAI Responses API structured outputs parser with a Pydantic model.

        Falls back to instructor-based structured_output if Responses.parse is unavailable.
        """
        # Prefer native Responses.parse when available
        try:
            responses = getattr(self.client, "responses", None)
            if responses and hasattr(responses, "parse"):
                resp = responses.parse(
                    model=model or self.model,
                    input=input_messages,
                    text_format=response_model,
                    temperature=temperature or self.temperature,
                    max_output_tokens=max_output_tokens or self.max_tokens,
                    **kwargs,
                )
                return getattr(resp, "output_parsed")
        except Exception:
            pass

        # Fallback to instructor (chat.completions with response_model)
        return self.structured_output(
            messages=input_messages,  # instructor uses chat.completions under the hood
            response_model=response_model,
            model=model or self.model,
            temperature=temperature or self.temperature,
            max_tokens=max_output_tokens or self.max_tokens,
            **kwargs,
        )

    def function_call(
        self,
        messages: list[dict[str, str]],
        functions: list[dict[str, Any]],
        function_call: str | dict[str, str] | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> "openai.types.chat.ChatCompletion":
        """Function calling (legacy format)."""
        return self.client.chat.completions.create(
            model=model or self.model,
            messages=messages,
            functions=functions,
            function_call=function_call,
            temperature=temperature or self.temperature,
            max_completion_tokens=max_tokens or self.max_tokens,
            **kwargs,
        )

    def tool_call(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
        tool_choice: str | dict[str, Any] | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> "openai.types.chat.ChatCompletion":
        """Tool calling (new format)."""
        return self.client.chat.completions.create(
            model=model or self.model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            temperature=temperature or self.temperature,
            max_completion_tokens=max_tokens or self.max_tokens,
            **kwargs,
        )

    # Generic interface for hacs_utils.structured fallback path
    def invoke(self, prompt: str) -> str:
        """Synchronous invoke: send a single user prompt and return content string."""
        resp = self.chat(messages=[{"role": "user", "content": prompt}], model=self.model)
        try:
            return resp.choices[0].message.content or ""
        except Exception:
            # Best effort stringify
            return (
                json.dumps(resp.model_dump(mode="json"))
                if hasattr(resp, "model_dump")
                else str(resp)
            )


"""Deprecated: OpenAIStructuredGenerator removed. Use hacs_utils.structured instead."""


class OpenAIToolRegistry:
    """Registry for OpenAI tools and functions."""

    def __init__(self):
        self.tools = {}
        self.functions = {}

    def register_tool(
        self, name: str, function: Callable, description: str, parameters: dict[str, Any]
    ):
        """Register a tool for OpenAI tool calling."""
        self.tools[name] = {
            "type": "function",
            "function": {"name": name, "description": description, "parameters": parameters},
        }
        self.functions[name] = function

    def register_function(
        self, name: str, function: Callable, description: str, parameters: dict[str, Any]
    ):
        """[DEPRECATED] Register a function for legacy OpenAI function calling.

        Use register_tool() or framework adapters instead. This will be removed.
        """
        import warnings as _warnings
        _warnings.warn(
            "OpenAIToolRegistry.register_function is deprecated; use register_tool instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.functions[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "function": function,
        }

    def get_tools(self) -> list[dict[str, Any]]:
        """Get all registered tools."""
        return list(self.tools.values())

    def get_functions(self) -> list[dict[str, Any]]:
        """Get all registered functions."""
        return [
            {
                "name": func["name"],
                "description": func["description"],
                "parameters": func["parameters"],
            }
            for func in self.functions.values()
        ]

    def execute_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Execute a registered tool/function."""
        if name in self.functions:
            return self.functions[name](**arguments)

        raise ValueError(f"Tool/function '{name}' not found")
