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


async def run_server_async(host: str, port: int, log_level: str = "INFO") -> None:
    """Run the HACS MCP server asynchronously with enhanced persistence."""
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(levelname)s:%(name)s:%(message)s"
    )

    logger.info(f"Starting HACS MCP Server on {host}:{port}")

    # Create server with enhanced persistence
    server = create_mcp_server()

    # Log persistence status on startup
    status = server.get_persistence_status()
    logger.info("🏥 HACS MCP Server starting with enhanced persistence")
    logger.info(f"   📊 Database: {'✅ Connected' if status['database']['connected'] else '❌ Disconnected'}")
    logger.info(f"   🔍 Vector Store: {'✅ Connected' if status['vector_store']['connected'] else '❌ Disconnected'}")
    logger.info("   🛡️ Security: ✅ Enabled")
    logger.info(f"   📋 CRUD Operations: {'✅ Available' if status['capabilities']['crud_operations'] else '❌ Unavailable'}")

    # Start HTTP transport
    transport = HTTPTransport(server, host=host, port=port)
    await transport.start()


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="HACS Model Context Protocol Server")
    parser.add_argument(
        "--host",
        default=os.getenv("MCP_HOST", "0.0.0.0"),
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("MCP_PORT", "8090")),
        help="Port to bind to (default: 8090)"
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level (default: INFO)"
    )
    parser.add_argument(
        "--migrate",
        action="store_true",
        help="Run database migration before starting server"
    )

    args = parser.parse_args()

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