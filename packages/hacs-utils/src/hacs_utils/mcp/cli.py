"""
HACS MCP CLI

Command-line interface for running the HACS MCP server.
"""

import argparse
import asyncio
import logging
import os
import sys

from .server import create_mcp_server
from .transport import HTTPTransport

logger = logging.getLogger(__name__)


async def run_server_async(
    host: str | None = None, port: int | None = None, log_level: str = "INFO"
) -> None:
    """Run the HACS MCP server asynchronously with enhanced persistence and security."""
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()), format="%(levelname)s:%(name)s:%(message)s"
    )

    # Get settings for configuration
    from hacs_core import get_settings

    settings = get_settings()

    # Parse MCP server URL if provided, otherwise use host/port
    if settings.mcp_server_url and not host and not port:
        from urllib.parse import urlparse

        parsed = urlparse(settings.mcp_server_url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 8000
    else:
        host = host or "127.0.0.1"
        port = port or 8000

    logger.info(f"Starting HACS MCP Server on {host}:{port}")
    logger.info(f"Environment: {settings.environment} | Dev Mode: {settings.dev_mode}")

    # Security validation for production
    if settings.is_production:
        api_keys = settings.get_effective_api_keys()
        if not api_keys:
            logger.error(
                "❌ Production mode requires API keys. Set HACS_API_KEY or HACS_API_KEY_FILE"
            )
            sys.exit(1)
        logger.info("✅ API authentication configured for production")

    # Create server with enhanced persistence
    server = create_mcp_server()

    # Log persistence status on startup
    status = server.get_persistence_status()
    logger.info("🏥 HACS MCP Server starting with enhanced persistence")
    logger.info(
        f"   📊 Database: {'✅ Connected' if status['database']['connected'] else '❌ Disconnected'}"
    )
    logger.info(
        f"   🔍 Vector Store: {'✅ Connected' if status['vector_store']['connected'] else '❌ Disconnected'}"
    )
    logger.info("   🛡️ Security: ✅ Enabled")
    logger.info(
        f"   📋 CRUD Operations: {'✅ Available' if status['capabilities']['crud_operations'] else '❌ Unavailable'}"
    )

    # Start secure HTTP transport
    transport = HTTPTransport(server, host=host, port=port)
    await transport.start()


def main() -> None:
    """Main CLI entry point."""
    # Get settings first to provide defaults
    from hacs_core import get_settings

    settings = get_settings()

    parser = argparse.ArgumentParser(description="HACS Model Context Protocol Server")
    parser.add_argument(
        "--host",
        default=os.getenv("MCP_HOST"),  # Allow override via MCP_HOST
        help="Host to bind to (overrides HACS_MCP_SERVER_URL host)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("MCP_PORT", "0")) if os.getenv("MCP_PORT") else None,
        help="Port to bind to (overrides HACS_MCP_SERVER_URL port)",
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level (default: INFO)",
    )
    parser.add_argument(
        "--migrate", action="store_true", help="Run database migration before starting server"
    )
    parser.add_argument(
        "--generate-api-key", action="store_true", help="Generate a secure API key and exit"
    )

    args = parser.parse_args()

    # Handle API key generation
    if args.generate_api_key:
        import secrets

        api_key = secrets.token_urlsafe(32)
        print(f"Generated API key: {api_key}")
        print(f"Add to your environment: export HACS_API_KEY='{api_key}'")
        print(
            f"Or save to file: echo '{api_key}' > /path/to/api_keys.txt && export HACS_API_KEY_FILE='/path/to/api_keys.txt'"
        )
        return

    try:
        # Run migration if requested
        if args.migrate:
            from hacs_persistence import initialize_hacs_database

            database_url = os.getenv("DATABASE_URL")
            if database_url:
                print("Running HACS database migration...")
                success = initialize_hacs_database(database_url, force_migration=True)
                if success:
                    print("✅ Migration completed successfully")
                else:
                    print("❌ Migration failed")
                    sys.exit(1)
            else:
                print("❌ DATABASE_URL not set, cannot run migration")
                sys.exit(1)

        # Start server
        asyncio.run(run_server_async(args.host, args.port, args.log_level))

    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
