"""
HACS MCP Tools - Clean Wrapper for HACS Tools

This module provides a clean, simple wrapper around the HACS tools
for use with the Model Context Protocol (MCP) server.

Follows Single Responsibility Principle - only handles MCP tool execution.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from .messages import CallToolResult

logger = logging.getLogger(__name__)

# Simplified tool name mapping for MCP server (only where names differ)
TOOL_NAME_MAPPING = {
    "create_resource": "create_hacs_record",
    "get_resource": "get_hacs_record",
    "update_resource": "update_hacs_record",
    "delete_resource": "delete_hacs_record",
    "search_resources": "search_hacs_records",
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
            from hacs_utils.integrations.common import get_all_hacs_tools_sync
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
            if hasattr(tool, '__name__'):
                self._tools[tool.__name__] = tool
            elif hasattr(tool, 'name'):
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
                content=[{"type": "text", "text": f"Tool '{tool_name}' not found"}],
                isError=True
            )

        # Execute the tool
        result = tool_func(**arguments)

        # Format the result
        return _format_result(result, tool_name)

    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"Error executing {tool_name}: {str(e)}"}],
            isError=True
        )


def _format_result(result: Any, tool_name: str) -> CallToolResult:
    """Format tool execution result for MCP."""
    try:
        # Handle different result types
        if hasattr(result, 'success') and hasattr(result, 'data'):
            # HACS Result object
            content = {
                "success": result.success,
                "data": result.data,
                "message": getattr(result, 'message', ''),
                "tool": tool_name,
                "timestamp": datetime.now().isoformat()
            }
            return CallToolResult(
                content=[{"type": "text", "text": str(content)}],
                isError=not result.success
            )
        else:
            # Simple result
            content = {
                "result": result,
                "tool": tool_name,
                "timestamp": datetime.now().isoformat()
            }
            return CallToolResult(
                content=[{"type": "text", "text": str(content)}],
                isError=False
            )
    except Exception as e:
        logger.error(f"Error formatting result for {tool_name}: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"Error formatting result: {str(e)}"}],
            isError=True
        )


__all__ = [
    'execute_tool',
    'get_all_hacs_tools',
    'HACSToolsLoader',
    'get_tools_loader'
]