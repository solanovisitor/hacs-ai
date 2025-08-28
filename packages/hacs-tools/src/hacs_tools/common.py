"""
Common schemas and utilities for HACS tools.

This module provides shared types and base classes used across all tool domains.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

from hacs_core.config import HACSSettings, HACSState
from hacs_models import get_model_registry  # type: ignore
try:
    from hacs_models import MessageDefinition
except Exception:  # pragma: no cover
    MessageDefinition = Any  # type: ignore


class HACSCommonInput(BaseModel):
    """Base class for tool inputs that support config and state injection.
    
    These fields are automatically injected by the tool loader and hidden
    from the LLM schema to provide runtime context without exposing internals.
    
    Examples:
        Basic usage in a tool input schema:
        
        ```python
        class MyToolInput(HACSCommonInput):
            text: str
            options: dict = Field(default_factory=dict)
        ```
        
        The config and state fields will be automatically available
        but hidden from the LLM's function call schema.
    """
    config: Optional[HACSSettings] = Field(
        default=None, 
        description="HACS configuration settings (injected at runtime)"
    )
    state: Optional[HACSState] = Field(
        default=None, 
        description="Session/request state (injected at runtime)"
    )


def build_error_plan(
    resource_type: Optional[str],
    payload: Optional[Dict[str, Any]] = None,
    err: Optional[Exception | str] = None,
    *,
    extra_suggestions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Return a standardized error plan with issues, suggestions, and next steps.

    Safe to call from any tool; never raises.
    """
    issues: List[Dict[str, Any]] = []
    suggestions: List[str] = []
    next_steps: List[Dict[str, Any]] = []

    # Parse Pydantic-style validation errors when available
    try:  # pragma: no cover
        if err is not None and hasattr(err, "errors"):
            for e in err.errors():  # type: ignore[attr-defined]
                loc = ".".join(str(x) for x in e.get("loc", [])) or "<root>"
                etype = e.get("type", "validation_error")
                msg = e.get("msg", str(err))
                issues.append({"field": loc, "type": etype, "message": msg})
                if etype.endswith("missing"):
                    suggestions.append(f"Provide required field '{loc}'.")
                if "extra_forbidden" in etype:
                    suggestions.append(f"Remove unsupported field '{loc}'.")
        elif err is not None:
            issues.append({"field": "<unknown>", "type": "error", "message": str(err)})
    except Exception:
        if err is not None:
            issues.append({"field": "<unknown>", "type": "error", "message": str(err)})

    # Model-aware guidance
    rt = resource_type or (payload or {}).get("resource_type")
    if rt:
        try:
            model_cls = get_model_registry().get(rt)
            if model_cls is None:
                suggestions.append(f"Unknown resource type '{rt}'. Check name or call list_models.")
                next_steps.append({"tool": "list_models", "args": {}})
            else:
                # Required fields hint
                try:
                    required = list((model_cls.get_descriptive_schema() or {}).get("required", []) or [])
                    if required:
                        suggestions.append(f"Required fields for {rt}: {', '.join(required)}")
                except Exception:
                    pass
                # Facade hint
                try:
                    facade_keys = list(model_cls.list_facade_keys())  # type: ignore[attr-defined]
                    if facade_keys:
                        suggestions.append(
                            f"Consider using a facade subset: {', '.join(facade_keys)} (describe_model_subset or extract_facade)."
                        )
                except Exception:
                    pass
        except Exception:
            pass
    else:
        suggestions.append("Include 'resource_type' in payload.")
        next_steps.append({"tool": "list_models", "args": {}})

    # Resource-specific nudge
    if rt == "Patient":
        suggestions.append("If no name, set anonymous=true or provide full_name.")

    # Tooling next steps for schema discovery
    if rt:
        next_steps.append({"tool": "describe_resource", "args": {"resource_type": rt}})
        next_steps.append({"tool": "list_model_facades", "args": {"resource_type": rt}})
        if payload:
            fields = [k for k in payload.keys() if k != "resource_type"]
            next_steps.append({
                "tool": "describe_model_subset",
                "args": {"resource_type": rt, "fields": fields},
            })

    if extra_suggestions:
        suggestions.extend(extra_suggestions)

    return {"issues": issues, "suggestions": suggestions, "next_steps": next_steps}


def get_messages_from_state(
    config: Optional[HACSSettings],
    state: Optional[HACSState],
    overrides: Optional[Union[list[dict[str, Any]], list[MessageDefinition]]] = None,
) -> List[MessageDefinition]:
    """Resolve conversational messages for LLM tools from state/config.

    Priority:
    1) Explicit overrides if provided
    2) state.messages if available
    3) Empty list
    """
    if overrides is not None:
        return _coerce_messages(overrides)
    try:
        msgs = getattr(state, "messages", None)
        if isinstance(msgs, list):
            return _coerce_messages(msgs)
    except Exception:
        pass
    return []


def _coerce_messages(messages: Union[List[MessageDefinition], List[Dict[str, Any]]]) -> List[MessageDefinition]:
    # If already MessageDefinition instances
    try:
        if messages and isinstance(messages[0], MessageDefinition):  # type: ignore[arg-type]
            return messages  # type: ignore[return-value]
    except Exception:
        pass
    # Coerce dicts to MessageDefinition
    coerced: List[MessageDefinition] = []
    for m in messages or []:
        try:
            if isinstance(m, MessageDefinition):  # type: ignore[arg-type]
                coerced.append(m)
            elif isinstance(m, dict):
                coerced.append(MessageDefinition(**m))  # type: ignore[call-arg]
        except Exception:
            # Fallback minimal construction
            try:
                coerced.append(MessageDefinition(content=str(m)))  # type: ignore[call-arg]
            except Exception:  # pragma: no cover
                pass
    return coerced


class AgentContext(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)
    messages: List[MessageDefinition] = Field(default_factory=list)


def runnable_context(
    *,
    config: Optional[HACSSettings] = None,
    state: Optional[HACSState] = None,
    model_override: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
    messages: Optional[Union[List[Dict[str, Any]], List[MessageDefinition]]] = None,
) -> AgentContext:
    """Create a consistent LLM context (provider, model, params, messages).

    - Resolves model/provider from config if available; model_override takes precedence.
    - Params merged over config defaults.
    - Messages resolved from explicit value or state.messages.
    """
    resolved_model: Optional[str] = model_override
    resolved_provider: Optional[str] = None
    resolved_params: Dict[str, Any] = {}

    try:
        # Common config shapes (best-effort; tolerate missing fields)
        models_cfg = getattr(config, "models", None) if config else None
        if resolved_model is None:
            for key in ("default_model", "model", "completion_model"):
                val = getattr(models_cfg, key, None) if models_cfg else None
                if isinstance(val, str) and val:
                    resolved_model = val
                    break
        for prov_key in ("provider", "llm_provider", "default_provider"):
            val = getattr(models_cfg, prov_key, None) if models_cfg else None
            if isinstance(val, str) and val:
                resolved_provider = val
                break
        # Params: use nested dict if present
        for params_key in ("default_params", "params", "generation_params"):
            maybe = getattr(models_cfg, params_key, None) if models_cfg else None
            if isinstance(maybe, dict):
                resolved_params.update(maybe)
                break
    except Exception:
        pass

    if params:
        try:
            resolved_params.update(params)
        except Exception:
            pass

    resolved_messages = get_messages_from_state(config, state, overrides=messages)

    return AgentContext(
        provider=resolved_provider,
        model=resolved_model,
        params=resolved_params,
        messages=resolved_messages,
    )
