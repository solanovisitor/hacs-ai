"""
Anthropic Integration for HACS

Provides Claude AI model integration for healthcare applications.

Adds optional support for Anthropic's MCP connector so HACS can connect to a
remote MCP server directly via the Messages API without a separate MCP client.

Environment variables used when MCP connector is enabled:
  - HACS_MCP_CONNECTOR_ENABLED=true|false (default: false)
  - HACS_MCP_SERVER_URL (e.g., https://your-hacs.example.com/sse or https://your-hacs.example.com)
  - HACS_MCP_SERVER_NAME (default: hacs-mcp)
  - HACS_API_KEY (authorization token for the MCP server)
  - HACS_MCP_ALLOWED_TOOLS (comma-separated tool whitelist; optional)

Notes:
  - The Anthropic MCP connector requires the beta header: "anthropic-beta": "mcp-client-2025-04-04".
  - Per Anthropic docs, the URL should be HTTPS and can point to an SSE endpoint or a streamable HTTP endpoint.
"""

import os

try:
    import anthropic
    _has_anthropic = True
except ImportError:
    _has_anthropic = False


class AnthropicClient:
    """Anthropic Claude client for healthcare AI applications."""

    def __init__(self, api_key: str | None = None):
        """Initialize Anthropic client."""
        if not _has_anthropic:
            raise ImportError(
                "Anthropic package not found. Install with: pip install anthropic"
            )

        self.client = anthropic.Anthropic(api_key=api_key)

    def _build_mcp_servers_from_env(self) -> list[dict] | None:
        """Build Anthropic MCP connector config from environment variables.

        Returns None if connector is not enabled.
        """
        enabled = os.getenv("HACS_MCP_CONNECTOR_ENABLED", "false").strip().lower() == "true"
        if not enabled:
            return None

        url = os.getenv("HACS_MCP_SERVER_URL")
        if not url or not isinstance(url, str):
            # Connector enabled but no URL – return None to avoid invalid requests
            return None

        # Anthropic docs recommend HTTPS; allow HTTP in development with a warning
        if url.startswith("http://") and os.getenv("HACS_ENVIRONMENT", "development") != "development":
            # In non-development environments, enforce HTTPS
            raise ValueError("HACS_MCP_SERVER_URL must use HTTPS in non-development environments")

        name = os.getenv("HACS_MCP_SERVER_NAME", "hacs-mcp")
        auth_token = os.getenv("HACS_API_KEY")
        allowed_tools_env = os.getenv("HACS_MCP_ALLOWED_TOOLS", "").strip()
        allowed_tools = [t.strip() for t in allowed_tools_env.split(",") if t.strip()] if allowed_tools_env else None

        mcp_entry: dict = {
            "type": "url",
            "url": url,
            "name": name,
        }
        if auth_token:
            mcp_entry["authorization_token"] = auth_token
        if allowed_tools is not None:
            mcp_entry["tool_configuration"] = {
                "enabled": True,
                "allowed_tools": allowed_tools,
            }

        return [mcp_entry]

    def chat(
        self,
        messages: list[dict],
        model: str = "claude-3-sonnet-20240229",
        use_mcp: bool = False,
        mcp_servers: list[dict] | None = None,
        betas: list[str] | None = None,
        **kwargs,
    ):
        """Send chat completion request to Claude.

        If `use_mcp` is True, configures Anthropic's MCP connector based on either explicit
        `mcp_servers` argument or environment variables (see module docstring).
        Automatically enables the required beta header/version.
        """
        final_mcp_servers = None
        if use_mcp:
            final_mcp_servers = mcp_servers or self._build_mcp_servers_from_env()

        # Set required beta if MCP is used
        final_betas = betas or (["mcp-client-2025-04-04"] if use_mcp else None)

        # Prefer the official beta API surface if available in the SDK
        try:
            if use_mcp:
                if hasattr(self.client, "beta") and hasattr(self.client.beta, "messages"):
                    return self.client.beta.messages.create(
                        model=model,
                        messages=messages,
                        mcp_servers=final_mcp_servers,
                        betas=final_betas,
                        **kwargs,
                    )
                # Fallback: attempt to pass beta header via extra headers
                kwargs.setdefault("extra_headers", {})
                kwargs["extra_headers"].update({"anthropic-beta": "mcp-client-2025-04-04"})
                return self.client.messages.create(
                    model=model,
                    messages=messages,
                    mcp_servers=final_mcp_servers,
                    **kwargs,
                )
            # No MCP: standard call
            return self.client.messages.create(
                model=model,
                messages=messages,
                **kwargs,
            )
        except Exception:
            # Re-raise after giving a clearer message if MCP was requested
            if use_mcp and (final_mcp_servers is None):
                raise RuntimeError(
                    "Anthropic MCP connector requested but not configured. Set HACS_MCP_CONNECTOR_ENABLED=true and HACS_MCP_SERVER_URL."
                )
            raise


def create_anthropic_client(api_key: str | None = None) -> AnthropicClient:
    """Create an Anthropic client instance."""
    return AnthropicClient(api_key=api_key)


__all__ = [
    "AnthropicClient",
    "create_anthropic_client",
]