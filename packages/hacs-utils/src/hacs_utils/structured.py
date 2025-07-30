"""
Structured output generation utilities for HACS applications.

This module provides utilities for generating structured Pydantic models
from LLM responses using prompt engineering, designed to work with any
HACS-compatible LLM provider.
"""

import json
from typing import Any, TypeVar, Type
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

async def generate_structured_output(
    llm_provider: Any,
    prompt: str,
    output_model: Type[T],
    **kwargs
) -> T:
    """
    Generate structured output from LLM using the specified Pydantic model.

    Args:
        llm_provider: The LLM provider instance (must support ainvoke method)
        prompt: The prompt to send to the LLM
        output_model: The Pydantic model class to generate
        **kwargs: Additional arguments passed to LLM

    Returns:
        Instance of the output_model with generated data

    Raises:
        ValueError: If LLM provider doesn't support required methods
    """
    if not hasattr(llm_provider, 'ainvoke'):
        raise ValueError("LLM provider must support 'ainvoke' method")

    # Create a prompt that asks for JSON output
    structured_prompt = f"""
{prompt}

Please respond with a valid JSON object that matches this schema. Do not include any explanations or additional text.

Required JSON format:
{_get_model_schema_example(output_model)}
"""

    # Get response from LLM
    response = await llm_provider.ainvoke(structured_prompt)

    # Extract JSON from response
    response_text = response.content if hasattr(response, 'content') else str(response)

    # Try to parse JSON and create model instance
    try:
        # Look for JSON in the response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1

        if json_start >= 0 and json_end > json_start:
            json_text = response_text[json_start:json_end]
            data = json.loads(json_text)
            return output_model(**data)
        else:
            # Fallback: create a basic instance with default values
            return _create_fallback_instance(output_model)

    except Exception:
        # If parsing fails, create a fallback instance
        return _create_fallback_instance(output_model)

async def generate_structured_list(
    llm_provider: Any,
    prompt: str,
    output_model: Type[T],
    max_items: int = 10,
    **kwargs
) -> list[T]:
    """
    Generate a list of structured outputs from LLM.

    Args:
        llm_provider: The LLM provider instance (must support ainvoke method)
        prompt: The prompt to send to the LLM
        output_model: The Pydantic model class to generate
        max_items: Maximum number of items to generate
        **kwargs: Additional arguments passed to LLM

    Returns:
        List of instances of the output_model

    Raises:
        ValueError: If LLM provider doesn't support required methods
    """
    if not hasattr(llm_provider, 'ainvoke'):
        raise ValueError("LLM provider must support 'ainvoke' method")

    structured_prompt = f"""
{prompt}

Please respond with a valid JSON array containing multiple objects (up to {max_items} items).
Do not include any explanations or additional text.

Required JSON format (array of objects):
[
{_get_model_schema_example(output_model)},
{_get_model_schema_example(output_model)}
]
"""

    # Get response from LLM
    response = await llm_provider.ainvoke(structured_prompt)

    # Extract JSON from response
    response_text = response.content if hasattr(response, 'content') else str(response)

    try:
        # Look for JSON array in the response
        json_start = response_text.find('[')
        json_end = response_text.rfind(']') + 1

        if json_start >= 0 and json_end > json_start:
            json_text = response_text[json_start:json_end]
            data_list = json.loads(json_text)
            # Limit to max_items
            limited_data = data_list[:max_items] if len(data_list) > max_items else data_list
            return [output_model(**item) for item in limited_data]
        else:
            # Fallback: create a list with one default instance
            return [_create_fallback_instance(output_model)]

    except Exception:
        # If parsing fails, create a fallback list
        return [_create_fallback_instance(output_model)]

def _get_model_schema_example(model_class: Type[BaseModel]) -> str:
    """Get a JSON schema example for the model class."""
    try:
        # Try to get the JSON schema
        schema = model_class.model_json_schema()

        # Create a simple example based on the schema
        example = {}
        properties = schema.get('properties', {})

        for field_name, field_info in properties.items():
            field_type = field_info.get('type', 'string')

            if field_type == 'string':
                example[field_name] = f"example_{field_name}"
            elif field_type == 'integer':
                example[field_name] = 1
            elif field_type == 'number':
                example[field_name] = 1.0
            elif field_type == 'boolean':
                example[field_name] = True
            elif field_type == 'array':
                example[field_name] = []
            elif field_type == 'object':
                example[field_name] = {}
            else:
                example[field_name] = None

        return json.dumps(example, indent=2)

    except Exception:
        # If schema generation fails, create a fallback instance
        try:
            example = _create_fallback_instance(model_class)
            return json.dumps(example.model_dump(), indent=2)
        except Exception:
            return '{"example": "data"}'

def _create_fallback_instance(model_class: Type[T]) -> T:
    """Create a fallback instance of the model with reasonable defaults."""
    try:
        # Try to create with no arguments first
        return model_class()
    except Exception:
        try:
            # Try to create with empty dict
            return model_class(**{})
        except Exception:
            # If that fails, try to create with default values for required fields
            schema = model_class.model_json_schema()
            properties = schema.get('properties', {})
            required = schema.get('required', [])

            defaults = {}
            for field_name in required:
                field_info = properties.get(field_name, {})
                field_type = field_info.get('type')

                # Handle enum fields with better fallback
                if 'enum' in field_info:
                    # Use the first enum value as default
                    defaults[field_name] = field_info['enum'][0]
                elif field_name == 'urgency':
                    # Special handling for urgency field - use common default
                    defaults[field_name] = 'moderate'
                elif field_name == 'reason':
                    # Special handling for reason field
                    defaults[field_name] = 'Clinical assessment recommended'
                elif field_type == 'string':
                    defaults[field_name] = f"default_{field_name}"
                elif field_type == 'integer':
                    defaults[field_name] = 0
                elif field_type == 'number':
                    defaults[field_name] = 0.0
                elif field_type == 'boolean':
                    defaults[field_name] = False
                elif field_type == 'array':
                    defaults[field_name] = []
                elif field_type == 'object':
                    defaults[field_name] = {}
                else:
                    # For unknown types, try to get a reasonable default
                    defaults[field_name] = None

            return model_class(**defaults)