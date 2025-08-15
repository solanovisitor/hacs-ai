"""
HACS Bundle Tools

Thin adapters around hacs_models.ResourceBundle utilities. No embedded business logic.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import ValidationError

from hacs_models import HACSResult, ResourceBundle, BundleType, BundleStatus
from hacs_core.tool_protocols import hacs_tool, ToolCategory
from hacs_models import get_model_registry


@hacs_tool(
    name="create_resource_bundle",
    description="Create a HACS ResourceBundle (STACK, TEMPLATE, or DOCUMENT)",
    category=ToolCategory.RESOURCE_MANAGEMENT,
    domains=["bundles"]
)
def create_resource_bundle(
    actor_name: str,
    bundle_type: str,
    title: Optional[str] = None,
    status: str = "active",
    version: str = "1.0.0",
    metadata: Optional[Dict[str, Any]] = None,
) -> HACSResult:
    try:
        bt = BundleType(bundle_type.upper()) if isinstance(bundle_type, str) else bundle_type
        st = BundleStatus(status) if isinstance(status, str) else status
        bundle = ResourceBundle(bundle_type=bt, title=title, status=st, version=version)
        if metadata:
            for k, v in metadata.items():
                setattr(bundle, k, v)
        return HACSResult(success=True, message="Bundle created", data=bundle.model_dump(), actor_id=actor_name)
    except ValidationError as ve:
        return HACSResult(success=False, message="Bundle validation error", error=str(ve), actor_id=actor_name)
    except Exception as e:
        return HACSResult(success=False, message="Failed to create bundle", error=str(e), actor_id=actor_name)


@hacs_tool(
    name="add_bundle_entry",
    description="Add a resource entry to a ResourceBundle from raw resource data",
    category=ToolCategory.RESOURCE_MANAGEMENT,
    domains=["bundles"]
)
def add_bundle_entry(
    actor_name: str,
    bundle: Dict[str, Any],
    resource_type: str,
    resource_data: Dict[str, Any],
    entry_title: Optional[str] = None,
) -> HACSResult:
    try:
        rb = ResourceBundle(**bundle)
        registry = get_model_registry()
        model_cls = registry.get(resource_type)
        if model_cls is None:
            return HACSResult(success=False, message=f"Unknown resource type '{resource_type}'", error="model_not_found", actor_id=actor_name)
        if "resource_type" not in resource_data:
            resource_data["resource_type"] = resource_type
        resource = model_cls(**resource_data)
        rb.add_entry(resource, title=entry_title or getattr(resource, "resource_type", resource_type))
        return HACSResult(success=True, message="Entry added", data=rb.model_dump(), actor_id=actor_name)
    except ValidationError as ve:
        return HACSResult(success=False, message="Validation error", error=str(ve), actor_id=actor_name)
    except Exception as e:
        return HACSResult(success=False, message="Failed to add entry", error=str(e), actor_id=actor_name)


@hacs_tool(
    name="validate_resource_bundle",
    description="Validate bundle integrity rules and report issues",
    category=ToolCategory.RESOURCE_MANAGEMENT,
    domains=["bundles"]
)
def validate_resource_bundle(
    actor_name: str,
    bundle: Dict[str, Any],
) -> HACSResult:
    try:
        rb = ResourceBundle(**bundle)
        try:
            rb.validate_bundle_integrity()
            return HACSResult(success=True, message="Bundle is valid", data={"valid": True}, actor_id=actor_name)
        except Exception as e:
            return HACSResult(success=False, message="Bundle validation failed", error=str(e), data={"valid": False}, actor_id=actor_name)
    except ValidationError as ve:
        return HACSResult(success=False, message="Bundle parse error", error=str(ve), actor_id=actor_name)


__all__ = [
    "create_resource_bundle",
    "add_bundle_entry",
    "validate_resource_bundle",
]


