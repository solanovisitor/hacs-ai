#!/usr/bin/env python
"""
Generate a machine-readable inventory of HACS tools and a capability map.

Outputs:
- docs/tools/tool_inventory.json
- docs/tools/capability_map.json

Strategy:
1) Import hacs_tools domain modules and enumerate exported tool functions
2) Introspect signatures and docstrings for LLM-friendly metadata
3) Cross-reference hacs_models registry documentation to map resource-specific tools

This script is read-only for code; it writes JSON artifacts for docs/automation.
"""

from __future__ import annotations

import importlib
import inspect
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


DOMAIN_MODULES: List[Tuple[str, str]] = [
    ("modeling", "hacs_tools.domains.modeling"),
    ("extraction", "hacs_tools.domains.extraction"),
    ("database", "hacs_tools.domains.database"),
    ("agents", "hacs_tools.domains.agents"),
    ("resource", "hacs_tools.domains.resource_tools"),
]


@dataclass
class ToolInfo:
    name: str
    domain: str
    module: str
    signature: str
    doc: str
    resources: List[str]
    is_async: bool


def _collect_module_functions(module_name: str) -> Tuple[str, List[Tuple[str, Any]]]:
    module = importlib.import_module(module_name)
    exported = getattr(module, "__all__", None)
    names: List[str]
    if exported and isinstance(exported, (list, tuple)):
        names = list(exported)
    else:
        # Fallback: collect functions defined in this module
        names = [
            n
            for n, obj in inspect.getmembers(module, inspect.isfunction)
            if getattr(obj, "__module__", "") == module.__name__
        ]
    functions: List[Tuple[str, Any]] = []
    for n in names:
        fn = getattr(module, n, None)
        if callable(fn):
            functions.append((n, fn))
    return module.__name__, functions


def _build_tool_inventory() -> List[ToolInfo]:
    # Map tool_name -> [resource_types] from hacs_models seeded docs
    # Import lazily to avoid heavy imports earlier
    from hacs_models import get_model_registry

    registry = get_model_registry()
    tool_to_resources: Dict[str, List[str]] = {}
    for resource_name, cls in registry.items():
        try:
            specs = cls.get_specifications()  # type: ignore[attr-defined]
            docs = (specs or {}).get("documentation", {}) or {}
            tools = docs.get("tools", []) or []
            for t in tools:
                tool_to_resources.setdefault(t, []).append(resource_name)
        except Exception:
            continue

    inventory: List[ToolInfo] = []
    for domain, module_name in DOMAIN_MODULES:
        try:
            mod_name, functions = _collect_module_functions(module_name)
        except Exception:
            continue

        for fname, fn in functions:
            try:
                sig = str(inspect.signature(fn))
            except Exception:
                sig = "(…)"
            doc = inspect.getdoc(fn) or ""
            is_async = inspect.iscoroutinefunction(fn)
            resources = sorted(tool_to_resources.get(fname, []))
            inventory.append(
                ToolInfo(
                    name=fname,
                    domain=domain,
                    module=mod_name,
                    signature=sig,
                    doc=doc,
                    resources=resources,
                    is_async=is_async,
                )
            )

    return inventory


def _write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def main() -> None:
    inventory = _build_tool_inventory()

    # Tool inventory
    inventory_json = [asdict(t) for t in inventory]
    # Attach args_schema if tool exposes a Pydantic model via _tool_args
    try:
        enriched: list[dict] = []
        for item in inventory_json:
            try:
                mod = importlib.import_module(item["module"])  # type: ignore[index]
                fn = getattr(mod, item["name"], None)
                args = getattr(fn, "_tool_args", None)
                if args is not None and hasattr(args, "model_json_schema"):
                    item["args_schema"] = args.model_json_schema()  # type: ignore[attr-defined]
            except Exception:
                pass
            enriched.append(item)
        inventory_json = enriched
    except Exception:
        pass

    _write_json("docs/tools/tool_inventory.json", inventory_json)

    # Capability map
    resource_to_tools: Dict[str, List[str]] = {}
    domain_to_tools: Dict[str, List[str]] = {}
    generic_tools: List[str] = []
    for t in inventory:
        if t.resources:
            for r in t.resources:
                resource_to_tools.setdefault(r, []).append(t.name)
        else:
            generic_tools.append(t.name)
        domain_to_tools.setdefault(t.domain, []).append(t.name)

    # Sort for deterministic output
    for lst in resource_to_tools.values():
        lst.sort()
    for lst in domain_to_tools.values():
        lst.sort()
    generic_tools = sorted(set(generic_tools))

    capability_map = {
        "resource_to_tools": resource_to_tools,
        "domain_to_tools": domain_to_tools,
        "generic_tools": generic_tools,
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
    _write_json("docs/tools/capability_map.json", capability_map)

    print("WROTE docs/tools/tool_inventory.json and docs/tools/capability_map.json")


if __name__ == "__main__":
    main()


