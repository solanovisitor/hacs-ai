"""
MCP Transport Implementations

Provides STDIO and HTTP transport for the Model Context Protocol server.
"""

import asyncio
import json
import logging
import sys
from abc import ABC, abstractmethod

from .messages import MCPRequest, MCPResponse
from .server import HacsMCPServer

logger = logging.getLogger(__name__)


class MCPTransport(ABC):
    """Abstract base class for MCP transport implementations."""

    def __init__(self, server: HacsMCPServer):
        """Initialize transport with server instance."""
        self.server = server

    @abstractmethod
    async def start(self) -> None:
        """Start the transport."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the transport."""
        pass


class StdioTransport(MCPTransport):
    """STDIO transport for MCP server."""

    def __init__(self, server: HacsMCPServer):
        """Initialize STDIO transport."""
        super().__init__(server)
        self.running = False

    async def start(self) -> None:
        """Start the STDIO transport."""
        logger.info("Starting HACS MCP Server on STDIO")
        self.running = True

        try:
            while self.running:
                # Read line from stdin
                line = await self._read_line()
                if not line:
                    break

                try:
                    # Parse JSON-RPC message
                    message_data = json.loads(line)
                    request = MCPRequest(**message_data)

                    # Handle request
                    response = await self.server.handle_request(request)

                    # Send response
                    await self._write_response(response)

                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received: {line}")
                    continue
                except Exception as e:
                    logger.exception("Error processing request")
                    # Send error response if we have an ID
                    if "id" in message_data:
                        error_response = MCPResponse(
                            id=message_data["id"],
                            error={
                                "code": -32603,
                                "message": f"Internal error: {str(e)}"
                            }
                        )
                        await self._write_response(error_response)

        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            await self.stop()

    async def stop(self) -> None:
        """Stop the STDIO transport."""
        logger.info("Stopping HACS MCP Server")
        self.running = False

    async def _read_line(self) -> str:
        """Read a line from stdin asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sys.stdin.readline)

    async def _write_response(self, response: MCPResponse) -> None:
        """Write response to stdout."""
        response_json = json.dumps(response.model_dump())
        print(response_json, flush=True)


class HTTPTransport(MCPTransport):
    """HTTP transport for MCP server (placeholder for future implementation)."""

    def __init__(self, server: HacsMCPServer, host: str = "127.0.0.1", port: int = 8000):
        """Initialize HTTP transport."""
        super().__init__(server)
        self.host = host
        self.port = port

    async def start(self) -> None:
        """Start the HTTP transport using FastAPI + Uvicorn.

        The server exposes a single POST endpoint (``/``) that expects a JSON-RPC
        request body.  The request is forwarded to :py:meth:`HacsMCPServer.handle_request`
        and the JSON representation of the response is returned.

        This method blocks until the Uvicorn server shuts down.
        """
        try:
            from fastapi import FastAPI, Request
            import uvicorn
        except ModuleNotFoundError as exc:  # pragma: no cover – runtime guard
            raise RuntimeError(
                "HTTP transport requires `fastapi` and `uvicorn`. Install with:"
                " pip install fastapi uvicorn[standard]"
            ) from exc

        app = FastAPI(
            title="HACS MCP Server",
            version=getattr(self.server, 'version', '1.0.0'),
            description="Healthcare Agent Communication Standard Model Context Protocol Server"
        )

        @app.post("/")
        async def mcp_endpoint(request: Request):  # type: ignore[valid-type]
            """Receive an MCP JSON-RPC request and return the server response."""
            payload = await request.json()
            try:
                mcp_request = MCPRequest(**payload)
            except Exception as exc:
                # Invalid request – respond with generic error following JSON-RPC format
                logger.warning("Received invalid MCP request: %s", exc)
                return {
                    "id": payload.get("id"),
                    "error": {
                        "code": -32600,
                        "message": f"Invalid Request: {exc}",
                    },
                }

            mcp_response = await self.server.handle_request(mcp_request)
            return mcp_response.model_dump()

        config = uvicorn.Config(app, host=self.host, port=self.port, log_level="info")
        self._uvicorn_server = uvicorn.Server(config)  # type: ignore[attr-defined]

        logger.info("Starting HTTP MCP server on http://%s:%d", self.host, self.port)
        await self._uvicorn_server.serve()

    async def stop(self) -> None:
        """Stop the HTTP transport."""
        if hasattr(self, "_uvicorn_server") and self._uvicorn_server is not None:  # type: ignore[attr-defined]
            logger.info("Shutting down HTTP MCP server")
            # Uvicorn exposes *should_exit* flag to trigger graceful shutdown
            self._uvicorn_server.should_exit = True  # type: ignore[attr-defined]
            await asyncio.sleep(0)