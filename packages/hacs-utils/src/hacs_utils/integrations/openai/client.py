"""
OpenAI Client Implementation for HACS
"""

import json
import os
from collections.abc import Callable
from typing import Any

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
        model: str = "gpt-4.1-mini",
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

        self.client = OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            base_url=base_url,
            organization=organization,
            timeout=timeout,
            max_retries=max_retries,
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
        """Standard chat completion."""
        return self.client.chat.completions.create(
            model=model or self.model,
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
            top_p=self.top_p,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
            tools=tools,
            tool_choice=tool_choice,
            **kwargs,
        )

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
            max_tokens=max_tokens or self.max_tokens,
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
            max_tokens=max_tokens or self.max_tokens,
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
            max_tokens=max_tokens or self.max_tokens,
            **kwargs,
        )


class OpenAIStructuredGenerator:
    """Specialized class for generating HACS models with OpenAI."""

    def __init__(
        self,
        client: OpenAIClient | None = None,
        model: str = "gpt-4.1-mini",
        temperature: float = 0.3,  # Lower temperature for structured output
        system_prompt: str | None = None,
    ):
        """Initialize structured generator."""
        self.client = client or OpenAIClient(model=model, temperature=temperature)
        self.system_prompt = system_prompt or self._default_system_prompt()

    def _default_system_prompt(self) -> str:
        """Default system prompt for healthcare AI."""
        return """You are a healthcare AI assistant that generates structured,
        FHIR-compliant healthcare data. Always use proper medical terminology
        and follow healthcare data standards. Ensure all generated data is
        realistic and clinically appropriate."""

    def generate_hacs_resource(
        self,
        resource_type: type[BaseModel],
        user_prompt: str,
        system_prompt: str | None = None,
        **kwargs,
    ) -> BaseModel:
        """Generate a HACS resource from natural language."""
        messages = [
            {"role": "system", "content": system_prompt or self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        return self.client.structured_output(
            messages=messages, response_model=resource_type, **kwargs
        )

    def generate_batch_resources(
        self,
        resource_type: type[BaseModel],
        prompts: list[str],
        system_prompt: str | None = None,
        **kwargs,
    ) -> list[BaseModel]:
        """Generate multiple HACS resources."""
        results = []
        for prompt in prompts:
            try:
                resource = self.generate_hacs_resource(
                    resource_type=resource_type,
                    user_prompt=prompt,
                    system_prompt=system_prompt,
                    **kwargs,
                )
                results.append(resource)
            except Exception as e:
                print(f"Error generating resource for prompt '{prompt}': {e}")
                results.append(None)

        return results


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
        """Register a function for OpenAI function calling (legacy)."""
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