from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LayerSpec(BaseModel):
    """Defines one resource layer in a stack template.

    - resource_type: the HACS model name, e.g., "Patient", "Observation"
    - layer_name: human-friendly name used for grouping or bundle titles
    - bindings: mapping of target field paths to variable names, e.g.
      {"full_name": "patient_name", "agent_context.instruction": "instruction"}
    - constant_fields: static fields set directly on the resource, e.g.
      {"status": "final"}
    """

    resource_type: str = Field(..., description="HACS resource type (model name)")
    layer_name: str = Field(..., description="Layer/display name")
    bindings: Dict[str, str] = Field(default_factory=dict, description="field_path -> variable_name")
    constant_fields: Dict[str, Any] = Field(default_factory=dict, description="Static fields")


class StackTemplate(BaseModel):
    """A reusable, versioned template for composing HACS resources into a stack.

    Variables provide a schema for inputs; "layers" describes how to bind variables
    to resource fields across different HACS resource types.
    """

    name: str
    version: str = "1.0.0"
    description: Optional[str] = None
    variables: Dict[str, Any] = Field(default_factory=dict, description="Input variable schema or hints")
    layers: List[LayerSpec] = Field(default_factory=list)


def _set_nested_field(obj: Any, path: str, value: Any) -> None:
    parts = path.split(".")
    cur = obj
    for i, part in enumerate(parts):
        is_last = i == len(parts) - 1
        if is_last:
            try:
                setattr(cur, part, value)
            except Exception:
                # Fallback for dict-like structures
                if isinstance(cur, dict):
                    cur[part] = value
                else:
                    raise
        else:
            try:
                nxt = getattr(cur, part, None)
            except Exception:
                nxt = None
            if nxt is None:
                # create intermediate dict
                nxt = {}
                try:
                    setattr(cur, part, nxt)
                except Exception:
                    if isinstance(cur, dict):
                        cur[part] = nxt
                    else:
                        raise
            cur = nxt


def instantiate_stack_template(
    template: StackTemplate,
    variables: Dict[str, Any],
    model_registry: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Instantiate a template into concrete HACS resource instances.

    Returns a mapping of layer_name -> resource_instance.
    """
    from . import get_model_registry  # late import to avoid cycles

    registry = model_registry or get_model_registry()
    outputs: Dict[str, Any] = {}

    for layer in template.layers:
        model_cls = registry.get(layer.resource_type)
        if model_cls is None:
            raise ValueError(f"Unknown resource_type: {layer.resource_type}")

        # Create minimal instance (resource_type set via constructor or default)
        instance = model_cls()

        # Apply constant fields
        for field_name, field_val in layer.constant_fields.items():
            _set_nested_field(instance, field_name, field_val)

        # Apply variable bindings
        for field_path, var_name in layer.bindings.items():
            if var_name in variables:
                _set_nested_field(instance, field_path, variables[var_name])

        outputs[layer.layer_name] = instance

    return outputs


