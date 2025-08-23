"""
Response parsing and validation for structured extraction.

This module handles:
- Parsing LLM responses to Pydantic models
- Extracting fenced code blocks (JSON/YAML)
- Validating citation structure
- Fallback parsing strategies
"""

from __future__ import annotations

import json
import yaml
from typing import Any, Type, TypeVar, List
from pydantic import BaseModel

from .prompt_builder import create_fallback_instance

T = TypeVar("T", bound=BaseModel)


def extract_fenced(text: str) -> str:
    """Extract content from fenced code blocks."""
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("\n", 1)
        if len(parts) == 2:
            body = parts[1]
            if "```" in body:
                return body.rsplit("```", 1)[0].strip()
    return text


def parse_to_model(response_text: str, output_model: Type[T]) -> T:
    """Parse response text to a Pydantic model instance."""
    response_text = extract_fenced(response_text)
    # Try JSON, then YAML
    try:
        data = json.loads(response_text)
        return output_model(**data)
    except Exception:
        try:
            data = yaml.safe_load(response_text)
            return output_model(**data)
        except Exception:
            return create_fallback_instance(output_model)


def parse_to_model_list(response_text: str, output_model: Type[T], *, max_items: int) -> list[T]:
    """Parse response text to a list of Pydantic model instances."""
    response_text = extract_fenced(response_text)
    try:
        data_list = json.loads(response_text)
    except Exception:
        try:
            data_list = yaml.safe_load(response_text)
        except Exception:
            return [create_fallback_instance(output_model)]
    if not isinstance(data_list, list):
        return [create_fallback_instance(output_model)]
    limited = data_list[:max_items] if len(data_list) > max_items else data_list
    result: list[T] = []
    for item in limited:
        try:
            result.append(output_model(**item))
        except Exception:
            continue
    return result or [create_fallback_instance(output_model)]


def try_parse_to_model(response_text: str, output_model: Type[T]) -> T | None:
    """Try to parse response text to a model, returning None on failure."""
    response_text = extract_fenced(response_text)
    try:
        data = json.loads(response_text)
    except Exception:
        try:
            data = yaml.safe_load(response_text)
        except Exception:
            return None
    try:
        return output_model(**data)
    except Exception:
        return None


def try_parse_to_model_list(
    response_text: str, output_model: Type[T], *, max_items: int
) -> list[T] | None:
    """Try to parse response text to a list of models, returning None on failure."""
    response_text = extract_fenced(response_text)
    try:
        data_list = json.loads(response_text)
    except Exception:
        try:
            data_list = yaml.safe_load(response_text)
        except Exception:
            return None
    if not isinstance(data_list, list):
        return None
    limited = data_list[:max_items] if len(data_list) > max_items else data_list
    result: list[T] = []
    for item in limited:
        try:
            result.append(output_model(**item))
        except Exception:
            continue
    return result or None


def validate_citations_structure(items: List[Any]) -> List[str]:
    """Validate the structure of citation extraction results.
    
    Returns a list of validation issues found.
    """
    issues: List[str] = []
    for idx, it in enumerate(items or []):
        try:
            attrs = getattr(it, "attributes", None)
            if attrs is None and isinstance(it, dict):
                attrs = it.get("attributes")
            if not isinstance(attrs, dict):
                t = type(attrs).__name__
                issues.append(f"[{idx}] attributes expected object, got {t}")
                continue
            field = attrs.get("field")
            if not isinstance(field, str) or not field.strip():
                issues.append(f"[{idx}] attributes.field must be non-empty string")
            value = attrs.get("value")
            if not (
                isinstance(value, str)
                or (isinstance(value, list) and all(isinstance(v, str) for v in value))
            ):
                issues.append(f"[{idx}] attributes.value must be string or list[str]")
            res = attrs.get("resources")
            if res is not None:
                if not isinstance(res, dict) or not all(isinstance(k, str) for k in res.keys()):
                    issues.append(f"[{idx}] attributes.resources must be object mapping str -> object")
        except Exception as e:
            issues.append(f"[{idx}] validation error: {e}")
    return issues
