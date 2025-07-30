"""
MCP Messages Module

Implements JSON-RPC 2.0 message types according to the Model Context Protocol specification.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class MCPRequest(BaseModel):
    """MCP request message following JSON-RPC 2.0 specification."""

    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    id: str | int = Field(..., description="Request ID (must not be null)")
    method: str = Field(..., description="Method name")
    params: dict[str, Any] | None = Field(None, description="Method parameters")

    class Config:
        extra = "forbid"


class MCPResponse(BaseModel):
    """MCP response message following JSON-RPC 2.0 specification."""

    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    id: str | int = Field(..., description="Request ID this response corresponds to")
    result: dict[str, Any] | None = Field(None, description="Result data")
    error: Optional["MCPError"] = Field(None, description="Error information")

    class Config:
        extra = "forbid"

    def model_post_init(self, __context: Any) -> None:
        """Validate that either result or error is set, but not both."""
        if self.result is not None and self.error is not None:
            raise ValueError("Response must not set both result and error")
        if self.result is None and self.error is None:
            raise ValueError("Response must set either result or error")


class MCPNotification(BaseModel):
    """MCP notification message following JSON-RPC 2.0 specification."""

    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    method: str = Field(..., description="Method name")
    params: dict[str, Any] | None = Field(None, description="Method parameters")

    class Config:
        extra = "forbid"


class MCPError(BaseModel):
    """MCP error information following JSON-RPC 2.0 specification."""

    code: int = Field(..., description="Error code (must be integer)")
    message: str = Field(..., description="Error message")
    data: Any | None = Field(None, description="Additional error data")

    class Config:
        extra = "forbid"


# Standard JSON-RPC error codes
class ErrorCodes:
    """Standard JSON-RPC 2.0 error codes."""

    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    # MCP-specific error codes (application-defined range)
    UNAUTHORIZED = -32000
    FORBIDDEN = -32001
    RESOURCE_NOT_FOUND = -32002
    VALIDATION_ERROR = -32003
    BACKEND_ERROR = -32004


# MCP Server Capability Messages
class ServerCapabilities(BaseModel):
    """Server capabilities for MCP initialization."""

    tools: bool | None = Field(None, description="Whether server supports tools")
    resources: bool | None = Field(None, description="Whether server supports resources")
    prompts: bool | None = Field(None, description="Whether server supports prompts")


class ClientCapabilities(BaseModel):
    """Client capabilities for MCP initialization."""

    sampling: bool | None = Field(None, description="Whether client supports sampling")


class InitializeRequest(BaseModel):
    """MCP initialize request."""

    jsonrpc: str = Field(default="2.0")
    id: str | int = Field(...)
    method: str = Field(default="initialize")
    params: dict[str, Any] = Field(...)

    class Config:
        extra = "forbid"


class InitializeParams(BaseModel):
    """Parameters for MCP initialize request."""

    protocolVersion: str = Field(..., description="MCP protocol version")
    capabilities: ClientCapabilities = Field(..., description="Client capabilities")
    clientInfo: dict[str, Any] = Field(..., description="Client information")


class InitializeResult(BaseModel):
    """Result of MCP initialize request."""

    protocolVersion: str = Field(..., description="MCP protocol version")
    capabilities: ServerCapabilities = Field(..., description="Server capabilities")
    serverInfo: dict[str, Any] = Field(..., description="Server information")


# Tool-related messages
class Tool(BaseModel):
    """MCP tool definition."""

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    inputSchema: dict[str, Any] = Field(..., description="JSON schema for tool input")


class ListToolsResult(BaseModel):
    """Result of tools/list request."""

    tools: list[Tool] = Field(..., description="Available tools")


class CallToolParams(BaseModel):
    """Parameters for tools/call request."""

    name: str = Field(..., description="Tool name to call")
    arguments: dict[str, Any] = Field(..., description="Tool arguments")


class CallToolResult(BaseModel):
    """Result of tools/call request."""

    content: list[dict[str, Any]] = Field(..., description="Tool result content")
    isError: bool | None = Field(None, description="Whether result represents an error")


# Resource-related messages
class Resource(BaseModel):
    """MCP resource definition."""

    uri: str = Field(..., description="Resource URI")
    name: str = Field(..., description="Resource name")
    description: str | None = Field(None, description="Resource description")
    mimeType: str | None = Field(None, description="Resource MIME type")


class ListResourcesResult(BaseModel):
    """Result of resources/list request."""

    resources: list[Resource] = Field(..., description="Available resources")


class ReadResourceParams(BaseModel):
    """Parameters for resources/read request."""

    uri: str = Field(..., description="Resource URI to read")


class ResourceContent(BaseModel):
    """Resource content."""

    uri: str = Field(..., description="Resource URI")
    mimeType: str | None = Field(None, description="Content MIME type")
    text: str | None = Field(None, description="Text content")
    blob: str | None = Field(None, description="Base64-encoded binary content")


class ReadResourceResult(BaseModel):
    """Result of resources/read request."""

    contents: list[ResourceContent] = Field(..., description="Resource contents")


# Update model references
MCPResponse.model_rebuild()