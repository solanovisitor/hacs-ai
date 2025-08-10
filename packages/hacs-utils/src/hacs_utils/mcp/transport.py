"""
MCP Transport Implementations

Provides STDIO and HTTP transport for the Model Context Protocol server.
"""

import asyncio
import json
import logging
import sys
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Dict, Set
from urllib.parse import urlparse

from .messages import MCPRequest, MCPResponse
from .server import HacsMCPServer

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, limit_per_minute: int = 60):
        self.limit_per_minute = limit_per_minute
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, client_ip: str) -> bool:
        """Check if request is allowed for given IP."""
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip] 
            if req_time > minute_ago
        ]
        
        # Check limit
        if len(self.requests[client_ip]) >= self.limit_per_minute:
            return False
            
        # Add current request
        self.requests[client_ip].append(now)
        return True


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
    """Secure HTTP transport for MCP server with authentication, CORS, and rate limiting."""

    def __init__(self, server: HacsMCPServer, host: str = "127.0.0.1", port: int = 8000):
        """Initialize HTTP transport."""
        super().__init__(server)
        self.host = host
        self.port = port
        
        # Get settings for security configuration
        from hacs_core import get_settings
        self.settings = get_settings()
        
        # Initialize rate limiter
        if not self.settings.dev_mode:
            self.rate_limiter = RateLimiter(self.settings.rate_limit_per_minute)
        else:
            self.rate_limiter = None

    def _get_client_ip(self, request) -> str:
        """Extract client IP from request."""
        # Check X-Forwarded-For header first (proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
            
        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"

    def _validate_api_key(self, request) -> bool:
        """Validate API key from request headers."""
        # Development mode bypass when no explicit API keys are configured
        if self.settings.dev_mode and self.settings.is_development:
            # Check if API keys were explicitly configured (not auto-generated)
            if not self.settings.api_keys and not self.settings.api_keys_file:
                return True
            
        # Get valid API keys (excluding auto-generated dev keys for validation)
        if self.settings.api_keys:
            valid_keys = self.settings.api_keys
        elif self.settings.api_keys_file:
            valid_keys = self.settings._load_api_keys_from_file(self.settings.api_keys_file)
        else:
            # No explicit keys configured
            if self.settings.dev_mode and self.settings.is_development:
                return True  # Allow in dev mode without keys
            return False  # Deny in production without keys
        
        if not valid_keys:
            return self.settings.dev_mode and self.settings.is_development
        
        # Check Authorization header (Bearer token)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            if token in valid_keys:
                return True
        
        # Check X-HACS-API-Key header
        api_key_header = request.headers.get("X-HACS-API-Key")
        if api_key_header and api_key_header in valid_keys:
            return True
            
        return False

    def _validate_host(self, request) -> bool:
        """Validate host header against allowed hosts."""
        if self.settings.is_development:
            return True  # Allow all in development
            
        allowed_hosts = self.settings.allowed_hosts
        if not allowed_hosts:
            return True  # No restriction if not configured
            
        host_header = request.headers.get("Host", "")
        return any(host in host_header for host in allowed_hosts)

    def _validate_origin(self, origin: str) -> bool:
        """Validate origin against allowed origins."""
        if self.settings.is_development:
            return True  # Allow all in development
            
        allowed_origins = self.settings.allowed_origins
        if not allowed_origins:
            return False  # Deny all if not configured in production
            
        return origin in allowed_origins

    async def start(self) -> None:
        """Start the secure HTTP transport using FastAPI + Uvicorn."""
        try:
            from fastapi import FastAPI, Request, HTTPException
            from fastapi.middleware.cors import CORSMiddleware
            from fastapi.responses import JSONResponse
            import uvicorn
        except ModuleNotFoundError as exc:  # pragma: no cover – runtime guard
            raise RuntimeError(
                "HTTP transport requires `fastapi` and `uvicorn`. Install with:"
                " pip install fastapi uvicorn[standard]"
            ) from exc

        app = FastAPI(
            title="HACS MCP Server",
            version=getattr(self.server, 'version', '1.0.0'),
            description="Healthcare Agent Communication Standard Model Context Protocol Server",
            docs_url=None if self.settings.is_production else "/docs",
            redoc_url=None if self.settings.is_production else "/redoc"
        )

        # Add CORS middleware
        if self.settings.is_development or self.settings.allowed_origins:
            app.add_middleware(
                CORSMiddleware,
                allow_origins=self.settings.allowed_origins if not self.settings.is_development else ["*"],
                allow_credentials=True,
                allow_methods=["POST", "GET", "OPTIONS"],
                allow_headers=["*"],
            )

        @app.middleware("http")
        async def security_middleware(request: Request, call_next):
            """Security middleware for authentication, rate limiting, and host validation."""
            # Skip security for health endpoints
            if request.url.path in ["/health", "/ready"]:
                return await call_next(request)
            
            # Host validation
            if not self._validate_host(request):
                logger.warning(f"Invalid host header: {request.headers.get('Host')}")
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid host header"}
                )
            
            # Rate limiting
            if self.rate_limiter:
                client_ip = self._get_client_ip(request)
                if not self.rate_limiter.is_allowed(client_ip):
                    logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                    return JSONResponse(
                        status_code=429,
                        content={
                            "jsonrpc": "2.0",
                            "error": {
                                "code": -32000,
                                "message": "Rate limit exceeded"
                            }
                        }
                    )
            
            # API key validation for POST requests
            if request.method == "POST":
                if not self._validate_api_key(request):
                    logger.warning(f"Unauthorized access attempt from {self._get_client_ip(request)}")
                    return JSONResponse(
                        status_code=401,
                        content={
                            "jsonrpc": "2.0",
                            "error": {
                                "code": -32001,
                                "message": "Unauthorized: Valid API key required"
                            }
                        }
                    )
            
            return await call_next(request)

        @app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "timestamp": time.time()}

        @app.get("/ready")
        async def readiness_check():
            """Readiness check endpoint."""
            status = self.server.get_persistence_status()
            ready = (
                status["vector_store"]["connected"] or 
                status["database"]["connected"] or
                self.settings.is_development
            )
            
            return {
                "status": "ready" if ready else "not_ready",
                "timestamp": time.time(),
                "database_connected": status["database"]["connected"],
                "vector_store_connected": status["vector_store"]["connected"],
                "environment": self.settings.environment
            }

        @app.post("/")
        async def mcp_endpoint(request: Request):  # type: ignore[valid-type]
            """Secure MCP JSON-RPC endpoint with authentication."""
            try:
                payload = await request.json()
            except Exception as exc:
                logger.warning("Invalid JSON payload: %s", exc)
                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32700,
                        "message": "Parse error: Invalid JSON"
                    }
                }
            
            try:
                mcp_request = MCPRequest(**payload)
            except Exception as exc:
                logger.warning("Invalid MCP request: %s", exc)
                return {
                    "jsonrpc": "2.0",
                    "id": payload.get("id"),
                    "error": {
                        "code": -32600,
                        "message": f"Invalid Request: {exc}",
                    },
                }

            # Add request metadata for auditing
            client_ip = self._get_client_ip(request)
            logger.info(f"MCP request from {client_ip}: {mcp_request.method}")

            mcp_response = await self.server.handle_request(mcp_request)
            return mcp_response.model_dump()

        # Parse URL to get host and port
        if self.settings.mcp_server_url:
            parsed = urlparse(self.settings.mcp_server_url)
            self.host = parsed.hostname or self.host
            self.port = parsed.port or self.port

        config = uvicorn.Config(
            app, 
            host=self.host, 
            port=self.port, 
            log_level="info",
            access_log=not self.settings.is_production  # Disable access logs in production
        )
        self._uvicorn_server = uvicorn.Server(config)  # type: ignore[attr-defined]

        logger.info("Starting secure HTTP MCP server on http://%s:%d", self.host, self.port)
        logger.info("Environment: %s | Dev Mode: %s", self.settings.environment, self.settings.dev_mode)
        
        if not self.settings.dev_mode:
            api_keys = self.settings.get_effective_api_keys()
            logger.info("API authentication: %s", "ENABLED" if api_keys else "DISABLED")
            logger.info("Rate limiting: %s req/min", self.settings.rate_limit_per_minute)
        
        await self._uvicorn_server.serve()

    async def stop(self) -> None:
        """Stop the HTTP transport."""
        if hasattr(self, "_uvicorn_server") and self._uvicorn_server is not None:  # type: ignore[attr-defined]
            logger.info("Shutting down HTTP MCP server")
            self._uvicorn_server.should_exit = True  # type: ignore[attr-defined]
            await asyncio.sleep(0)