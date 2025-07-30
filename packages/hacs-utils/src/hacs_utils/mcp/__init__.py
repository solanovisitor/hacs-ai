"""
HACS Model Context Protocol (MCP) Integration

This package provides a complete MCP server implementation for HACS with
enhanced persistence, security, and LangGraph Cloud integration.
"""

from .server import HacsMCPServer, create_mcp_server
from .messages import MCPRequest, MCPResponse, CallToolParams, CallToolResult
from .tools import execute_tool, get_all_hacs_tools

__all__ = [
    "HacsMCPServer",
    "create_mcp_server",
    "MCPRequest",
    "MCPResponse",
    "CallToolParams",
    "CallToolResult",
    "execute_tool",
    "get_all_hacs_tools"
]

# For backward compatibility
create_hacs_mcp_server = create_mcp_server