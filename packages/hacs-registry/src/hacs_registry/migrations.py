"""
Registry migration utilities: discover, register, and persist Tools & Resources.

This module discovers plugin packages (via entry points or env), imports them to
trigger decorators, then consumes pending registrations and persists them via the
registry persistence integration.
"""

from __future__ import annotations

import importlib
import logging
import os
from typing import Iterable

from .persistence_integration import get_registry_integration
from .resource_registry import (
    consume_pending_resource_registrations,
)
from .tool_registry import get_global_registry as get_tool_registry

logger = logging.getLogger(__name__)


def _iter_plugin_modules() -> Iterable[str]:
    """Yield plugin module paths from entry points or env var.

    - Env var HACS_PLUGIN_PACKAGES: comma-separated module paths.
    - Future: pkg_resources/importlib.metadata entry points (hacs.plugins)
    """
    env = os.getenv("HACS_PLUGIN_PACKAGES", "").strip()
    if env:
        for mod in env.split(","):
            mod = mod.strip()
            if mod:
                yield mod

    # TODO: add importlib.metadata entry_points lookup if needed


def discover_and_import_plugins() -> int:
    """Import plugin modules to trigger decorators.

    Returns the count of successfully imported modules.
    """
    count = 0
    for mod in _iter_plugin_modules():
        try:
            importlib.import_module(mod)
            logger.info(f"Imported plugin module: {mod}")
            count += 1
        except Exception as e:
            logger.warning(f"Failed to import plugin module {mod}: {e}")
    return count


async def register_catalog(persist: bool = True) -> dict:
    """Consume pending resource registrations and persist tool/resource catalogs.

    - Imports plugin packages (if configured)
    - Registers pending resources into the in-memory registry
    - Optionally persists via configured persistence provider
    """
    discover_and_import_plugins()

    # Register resources from pending decorator queue
    registered_resources = consume_pending_resource_registrations(clear=True)
    logger.info(f"Registered {len(registered_resources)} resources from decorators")

    # Tools are already registered at import time via @register_tool
    tool_registry = get_tool_registry()
    tools = tool_registry.get_all_tools()
    logger.info(f"Discovered {len(tools)} tools")

    report = {
        "resources": len(registered_resources),
        "tools": len(tools),
        "persisted": False,
    }

    if not persist:
        return report

    # Persist via integration service (best-effort)
    integration = get_registry_integration()
    svc = integration.persistence_service
    if svc is None:
        logger.warning("No persistence provider configured; skipping persistence")
        return report

    try:
        async with svc.transaction():
            for res in registered_resources:
                await svc.save_registered_resource(res)
            for tool in tools:
                await svc.save_tool_definition(tool)
        report["persisted"] = True
    except Exception as e:
        logger.error(f"Failed to persist registry catalog: {e}")

    return report
