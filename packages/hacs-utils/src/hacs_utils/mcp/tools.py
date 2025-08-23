"""
HACS MCP Tools - Model and Field Discovery for Workflows

Expose tools over MCP to discover HACS models and their fields, enabling
workflows to programmatically select appropriate resources and validated
fields when generating stacks.
"""

import inspect
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .messages import CallToolResult


def _get_models_info() -> List[Dict[str, Any]]:
    try:
        import hacs_models as hm
    except Exception:
        import hacs_core as hm
    models = []
    for name in dir(hm):
        cls = getattr(hm, name)
        if hasattr(cls, "model_fields") and hasattr(cls, "model_json_schema"):
            schema = {}
            try:
                schema = cls.model_json_schema()
            except Exception:
                pass
            description = ""
            try:
                # Prefer BaseResource.get_descriptive_schema if available
                if hasattr(cls, "get_descriptive_schema"):
                    ds = cls.get_descriptive_schema()  # type: ignore[attr-defined]
                    description = ds.get("description", "")
                else:
                    description = inspect.getdoc(cls) or ""
            except Exception:
                description = ""
            models.append(
                {
                    "name": name,
                    "fields": list(getattr(cls, "model_fields").keys()),
                    "schema": schema,
                    "description": description,
                }
            )
    return models


def mcp_list_models() -> Dict[str, Any]:
    return {"success": True, "models": _get_models_info()}


def mcp_get_model_schema(resource_name: str) -> Dict[str, Any]:
    try:
        import hacs_models as hm
    except Exception:
        import hacs_core as hm
    cls = getattr(hm, resource_name, None)
    if not cls or not hasattr(cls, "model_json_schema"):
        return {"success": False, "error": f"Model not found: {resource_name}"}
    try:
        ds = {}
        if hasattr(cls, "get_descriptive_schema"):
            ds = cls.get_descriptive_schema()  # type: ignore[attr-defined]
        return {"success": True, "schema": cls.model_json_schema(), "descriptive": ds}
    except Exception as e:
        return {"success": False, "error": str(e)}


logger = logging.getLogger(__name__)

# Simplified tool name mapping for MCP server (only where names differ)
TOOL_NAME_MAPPING = {
    "create_resource": "create_record",
    "get_resource": "get_record",
    "update_resource": "update_record",
    "delete_resource": "delete_record",
    "search_resources": "search_records",
    "create_memory": "create_hacs_memory",
    "search_memories": "search_hacs_memories",
}


class HACSToolsLoader:
    """
    Tool loader that follows Dependency Inversion Principle.

    Abstracts tool loading to support different sources (registry, direct, fallback).
    """

    def __init__(self):
        self._tools: Dict[str, Any] = {}
        self._loaded = False

    def get_all_tools(self) -> List[Any]:
        """Get all available HACS tools."""
        if not self._loaded:
            self._load_tools()
        return list(self._tools.values())

    def get_tool_by_name(self, name: str) -> Optional[Any]:
        """Get a specific tool by name."""
        if not self._loaded:
            self._load_tools()
        return self._tools.get(name)

    def _load_tools(self) -> None:
        """Load tools using priority-based strategy."""
        try:
            # Priority 1: Use centralized loader from hacs-utils
            from hacs_utils.integrations.common.tool_loader import get_all_hacs_tools_sync

            tools = get_all_hacs_tools_sync(framework="mcp")
            self._register_tools(tools)
            logger.info(f"✅ Loaded {len(tools)} tools via centralized loader")
        except ImportError:
            try:
                # Priority 2: Direct hacs-tools import
                from hacs_tools import get_all_tools

                tools = get_all_tools()
                self._register_tools(tools)
                logger.info(f"✅ Loaded {len(tools)} tools via HACS Tools registry")
            except ImportError:
                logger.error("❌ No HACS tools available")

        self._loaded = True

    def _register_tools(self, tools: List[Any]) -> None:
        """Register tools in the internal dictionary."""
        for tool in tools:
            if hasattr(tool, "__name__"):
                self._tools[tool.__name__] = tool
            elif hasattr(tool, "name"):
                self._tools[tool.name] = tool


# Global tool loader instance
_tools_loader: Optional[HACSToolsLoader] = None


def get_tools_loader() -> HACSToolsLoader:
    """Get the global tools loader instance."""
    global _tools_loader
    if _tools_loader is None:
        _tools_loader = HACSToolsLoader()
    return _tools_loader


def get_all_hacs_tools() -> List[Any]:
    """Get all HACS tools."""
    return get_tools_loader().get_all_tools()


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """
    Execute a HACS tool with the given arguments.

    Args:
        tool_name: Name of the tool to execute (may be mapped)
        arguments: Tool arguments

    Returns:
        CallToolResult with execution result
    """
    try:
        # Map tool name if needed
        actual_tool_name = TOOL_NAME_MAPPING.get(tool_name, tool_name)

        # Get the tool function
        loader = get_tools_loader()
        tool_func = loader.get_tool_by_name(actual_tool_name)

        if tool_func is None:
            return CallToolResult(
                content=[{"type": "text", "text": f"Tool '{tool_name}' not found"}], isError=True
            )

        # Execute the tool
        result = tool_func(**arguments)

        # Format the result
        return _format_result(result, tool_name)

    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"Error executing {tool_name}: {str(e)}"}],
            isError=True,
        )


def _format_result(result: Any, tool_name: str) -> CallToolResult:
    """Format tool execution result for MCP."""
    try:
        # Handle different result types
        if hasattr(result, "success") and hasattr(result, "data"):
            # HACS Result object
            content = {
                "success": result.success,
                "data": result.data,
                "message": getattr(result, "message", ""),
                "tool": tool_name,
                "timestamp": datetime.now().isoformat(),
            }
            return CallToolResult(
                content=[{"type": "text", "text": str(content)}], isError=not result.success
            )
        else:
            # Simple result
            content = {"result": result, "tool": tool_name, "timestamp": datetime.now().isoformat()}
            return CallToolResult(content=[{"type": "text", "text": str(content)}], isError=False)
    except Exception as e:
        logger.error(f"Error formatting result for {tool_name}: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"Error formatting result: {str(e)}"}], isError=True
        )


__all__ = ["execute_tool", "get_all_hacs_tools", "HACSToolsLoader", "get_tools_loader"]
