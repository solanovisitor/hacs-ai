"""
HACS Modeling Tools

Thin, SOLID-compliant adapters that expose hacs-models resource constructors and
validators as tools. These tools avoid business logic and only orchestrate
model creation/validation and schema access.

Organization:
- Resource instantiation
- Resource validation

Note: Prefer existing discovery tools in schema_discovery for schema queries.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import ValidationError

from hacs_models import HACSResult
from hacs_core.tool_protocols import hacs_tool, ToolCategory


def _get_model_class(model_name: str):
    try:
        from hacs_models import get_model_registry
        registry = get_model_registry()
        return registry.get(model_name)
    except Exception:
        return None


@hacs_tool(
    name="instantiate_hacs_resource",
    description="Instantiate a HACS model by name with provided data (pure adapter)",
    category=ToolCategory.RESOURCE_MANAGEMENT,
    healthcare_domains=["resource_modeling"]
)
def instantiate_hacs_resource(
    actor_name: str,
    model_name: str,
    data: Dict[str, Any],
) -> HACSResult:
    try:
        model_class = _get_model_class(model_name)
        if model_class is None:
            return HACSResult(success=False, message=f"Unknown model '{model_name}'", error="model_not_found", actor_id=actor_name)
        # Ensure resource_type default if missing
        if "resource_type" not in data:
            data["resource_type"] = model_name
        instance = model_class(**data)  # type: ignore[call-arg]
        return HACSResult(success=True, message=f"Instantiated {model_name}", data=instance.model_dump(), actor_id=actor_name)
    except ValidationError as ve:  # pydantic validation
        return HACSResult(success=False, message=f"Validation failed for {model_name}", error=str(ve), actor_id=actor_name)
    except Exception as e:
        return HACSResult(success=False, message=f"Failed to instantiate {model_name}", error=str(e), actor_id=actor_name)


@hacs_tool(
    name="validate_hacs_resource",
    description="Validate a HACS model instance from raw data and return issues (pure adapter)",
    category=ToolCategory.RESOURCE_MANAGEMENT,
    healthcare_domains=["resource_modeling"]
)
def validate_hacs_resource(
    actor_name: str,
    model_name: str,
    data: Dict[str, Any],
) -> HACSResult:
    try:
        model_class = _get_model_class(model_name)
        if model_class is None:
            return HACSResult(success=False, message=f"Unknown model '{model_name}'", error="model_not_found", actor_id=actor_name)
        if "resource_type" not in data:
            data["resource_type"] = model_name
        # Create instance for validation
        instance = model_class(**data)  # type: ignore[call-arg]
        issues = instance.validate() if hasattr(instance, "validate") else []
        return HACSResult(success=len(issues) == 0, message="Validation completed", data={"issues": issues}, actor_id=actor_name)
    except ValidationError as ve:
        return HACSResult(success=False, message="Validation error", error=str(ve), data={"issues": [str(ve)]}, actor_id=actor_name)
    except Exception as e:
        return HACSResult(success=False, message="Failed to validate resource", error=str(e), actor_id=actor_name)


__all__ = [
    "instantiate_hacs_resource",
    "validate_hacs_resource",
]


