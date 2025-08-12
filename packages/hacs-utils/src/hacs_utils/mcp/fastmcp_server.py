"""
HACS FastMCP Server (Streamable HTTP)

Purpose: Expose HACS tools as an MCP server using FastMCP so that LangChain
MCP adapters can connect via streamable HTTP (or stdio if desired) without
requiring changes to the LangGraph agent model providers.

Usage:
  uv run --with mcp --with langchain-mcp-adapters python -m hacs_utils.mcp.fastmcp_server \
      --host 0.0.0.0 --port 8010

Environment variables:
  - HACS_FASTMCP_HOST (default: 0.0.0.0)
  - HACS_FASTMCP_PORT (default: 8010)

Notes:
  - This server does not enforce Authorization headers by default. For
    production, consider adding middleware or deploying behind an authenticating
    proxy.
"""

from __future__ import annotations

import argparse
import logging
import os
from typing import List


def _get_hacs_langchain_tools() -> List:
    """Load HACS tools as LangChain tools via the LangGraph integration layer."""
    try:
        from hacs_utils.integrations.langgraph import get_hacs_agent_tools
        tools = get_hacs_agent_tools()
        return tools
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"Failed to load HACS tools: {exc}") from exc


def _convert_to_fastmcp(tools: List):
    """Convert LangChain tools into FastMCP tools using langchain-mcp-adapters."""
    try:
        from langchain_mcp_adapters.tools import to_fastmcp
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "langchain-mcp-adapters is required. Install with: uv add langchain-mcp-adapters"
        ) from exc

    fastmcp_tools = []
    for t in tools:
        try:
            fastmcp_tools.append(to_fastmcp(t))
        except Exception:
            # Skip tools that cannot be converted; continue gracefully
            continue
    return fastmcp_tools


def main() -> None:
    parser = argparse.ArgumentParser(description="HACS FastMCP Server")
    parser.add_argument("--host", default=os.getenv("HACS_FASTMCP_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.getenv("HACS_FASTMCP_PORT", "8010")))
    parser.add_argument(
        "--transport",
        default="streamable_http",
        choices=["streamable_http", "stdio"],
        help="MCP transport to use (default: streamable_http)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    logger = logging.getLogger("hacs.fastmcp")

    # Load HACS tools as LangChain tools
    lc_tools = _get_hacs_langchain_tools()
    logger.info("Loaded %d LangChain tools from HACS", len(lc_tools))

    # Convert to FastMCP tools
    fastmcp_tools = _convert_to_fastmcp(lc_tools)
    logger.info("Converted %d tools to FastMCP", len(fastmcp_tools))

    # Initialize FastMCP server
    try:
        from mcp.server.fastmcp import FastMCP
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("mcp package is required. Install with: uv add mcp") from exc

    mcp = FastMCP("HACS", tools=fastmcp_tools)

    if args.transport == "stdio":
        logger.info("Starting FastMCP (stdio) server for HACS")
        mcp.run(transport="stdio")
    else:
        logger.info(
            "Starting FastMCP (streamable-http) server for HACS on /mcp/ (bind env vars control host/port)")
        # Some FastMCP versions read host/port from environment variables
        os.environ.setdefault("FASTMCP_HOST", str(args.host))
        os.environ.setdefault("FASTMCP_PORT", str(args.port))
        mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()


