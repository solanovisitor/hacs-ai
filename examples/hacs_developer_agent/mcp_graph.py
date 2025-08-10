"""
Async LangGraph graph factory that connects to the HACS MCP Server via
langchain-mcp-adapters and exposes its tools to a LangGraph agent.

Configuration via environment variables:
  - HACS_MCP_SERVER_URL: Base URL of the HACS MCP server (e.g., http://localhost:8000)
  - HACS_API_KEY: Bearer token for the HACS MCP server (optional in dev)
  - HACS_MCP_TRANSPORT: "streamable_http" (default) or "sse"
  - HACS_MCP_SERVER_NAME: Name identifier for the server (default: hacs-mcp)

Notes:
  - The langchain-mcp-adapters prefer a streamable HTTP path such as 
    "http(s)://host:port/mcp/". If HACS_MCP_SERVER_URL does not include 
    "/mcp" or "/mcp/", we will append "/mcp/" automatically.
  - If your HACS MCP server currently exposes only a root JSON-RPC endpoint ("/"),
    you should enable a proper MCP streamable HTTP endpoint at "/mcp/" for full compatibility.
"""

import os
from typing import Dict, Any

from langgraph.prebuilt import create_react_agent

# HACS model selector (LangChain-compatible)
from hacs_model import get_default_model


def _normalize_streamable_url(base_url: str) -> str:
    """Ensure the URL ends with /mcp/ for streamable HTTP as per adapter docs."""
    url = base_url.rstrip("/")
    # If already contains /mcp at end, normalize to have trailing slash
    if url.endswith("/mcp"):
        return url + "/"
    # If already has /mcp/ anywhere, return as-is
    if url.endswith("/mcp/"):
        return url
    # Otherwise append /mcp/
    return url + "/mcp/"


async def make_graph():
    """Async factory returning a LangGraph agent wired to HACS MCP via MCP adapters."""
    # Defer imports to avoid hard dependency if not used
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "langchain-mcp-adapters is required. Install with: uv add langchain-mcp-adapters"
        ) from exc

    # Read configuration
    server_name = os.getenv("HACS_MCP_SERVER_NAME", "hacs-mcp")
    base_url = os.getenv("HACS_MCP_SERVER_URL", "http://127.0.0.1:8000")
    transport = os.getenv("HACS_MCP_TRANSPORT", "streamable_http").strip().lower()
    api_key = os.getenv("HACS_API_KEY")

    # Build server config for MultiServerMCPClient
    server_cfg: Dict[str, Any] = {
        "transport": transport,
    }

    if transport == "streamable_http":
        url = _normalize_streamable_url(base_url)
        server_cfg["url"] = url
        # Optional auth header
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        if headers:
            server_cfg["headers"] = headers
    elif transport == "sse":
        # SSE requires a concrete SSE endpoint; assume base_url already points to SSE path
        server_cfg["url"] = base_url
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        if headers:
            server_cfg["headers"] = headers
    else:
        raise ValueError(f"Unsupported HACS_MCP_TRANSPORT: {transport}")

    # Initialize MCP client and load tools
    client = MultiServerMCPClient({server_name: server_cfg})
    tools = await client.get_tools()

    # Initialize the model (LangChain-compatible)
    model = get_default_model()

    # Create agent with MCP tools
    agent = create_react_agent(model, tools)
    return agent


