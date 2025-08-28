"""
Database Utilities for HACS Persistence

This module provides high-level utilities for database inspection,
health checks, and status reporting to avoid raw SQL in documentation
and applications.
"""

import logging
import os
from typing import Any
from urllib.parse import urlparse

import psycopg
from psycopg.rows import dict_row

from .migrations import get_migration_status

logger = logging.getLogger(__name__)


async def get_database_info(database_url: str | None = None) -> dict[str, Any]:
    """
    Get comprehensive database information using HACS helpers.
    
    Args:
        database_url: PostgreSQL connection URL (uses DATABASE_URL if None)
        
    Returns:
        Dictionary with database version, connection details, and status
    """
    if not database_url:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            return {"error": "DATABASE_URL not provided"}

    try:
        async with await psycopg.AsyncConnection.connect(database_url) as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                # Get database version and connection info
                await cur.execute("SELECT version(), current_database(), inet_server_addr()")
                result = await cur.fetchone()

                if result:
                    version_str = result["version"]
                    db_name = result["current_database"]
                    server_addr = result["inet_server_addr"]

                    # Parse PostgreSQL version
                    version_parts = version_str.split()
                    pg_version = f"{version_parts[0]} {version_parts[1]}" if len(version_parts) > 1 else version_str
                else:
                    pg_version = "unknown"
                    db_name = "unknown"
                    server_addr = None

                # Parse connection URL for display
                parsed_url = urlparse(database_url)

                return {
                    "status": "connected",
                    "database_name": db_name,
                    "postgresql_version": pg_version,
                    "server_address": server_addr,
                    "connection": {
                        "host": parsed_url.hostname,
                        "port": parsed_url.port,
                        "database": (parsed_url.path or "/").lstrip("/"),
                        "ssl_mode": "require" if "sslmode=require" in database_url else "unknown"
                    }
                }

    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return {"error": str(e), "status": "connection_failed"}


async def get_hacs_schema_summary(database_url: str | None = None) -> dict[str, Any]:
    """
    Get a summary of HACS schemas using migration status helper.
    
    Args:
        database_url: PostgreSQL connection URL (uses DATABASE_URL if None)
        
    Returns:
        Dictionary with schema breakdown and migration status
    """
    try:
        status = await get_migration_status(database_url)

        if "error" in status:
            return status

        # Extract relevant information
        schema_breakdown = status.get("schema_breakdown", {})

        return {
            "hacs_schemas": schema_breakdown,
            "total_tables": status.get("total_tables", 0),
            "expected_tables": status.get("expected_tables", 0),
            "migration_complete": status.get("migration_complete", False),
            "pgvector_enabled": status.get("pgvector_enabled", False),
            "schemas_count": len(schema_breakdown)
        }

    except Exception as e:
        logger.error(f"Failed to get HACS schema summary: {e}")
        return {"error": str(e)}


async def check_hacs_tables_exist(database_url: str | None = None,
                                  target_schemas: list[str] | None = None) -> dict[str, Any]:
    """
    Check if specific HACS tables exist in the database.
    
    Args:
        database_url: PostgreSQL connection URL (uses DATABASE_URL if None)
        target_schemas: List of schema names to check (defaults to main HACS schemas)
        
    Returns:
        Dictionary with table existence status per schema
    """
    if not database_url:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            return {"error": "DATABASE_URL not provided"}

    if target_schemas is None:
        target_schemas = ['hacs_core', 'hacs_clinical', 'hacs_registry', 'hacs_agents', 'hacs_admin', 'hacs_audit']

    try:
        async with await psycopg.AsyncConnection.connect(database_url) as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                # Check table existence across target schemas
                await cur.execute("""
                    SELECT table_schema, table_name, table_type
                    FROM information_schema.tables 
                    WHERE table_schema = ANY(%s)
                    ORDER BY table_schema, table_name
                """, (target_schemas,))

                tables = await cur.fetchall()

                # Group by schema
                schema_tables = {}
                for table in tables:
                    schema = table["table_schema"]
                    if schema not in schema_tables:
                        schema_tables[schema] = []
                    schema_tables[schema].append({
                        "name": table["table_name"],
                        "type": table["table_type"]
                    })

                # Check for missing schemas
                found_schemas = set(schema_tables.keys())
                missing_schemas = set(target_schemas) - found_schemas

                return {
                    "schemas_found": schema_tables,
                    "missing_schemas": list(missing_schemas),
                    "total_tables": len(tables),
                    "schemas_with_tables": len(schema_tables)
                }

    except Exception as e:
        logger.error(f"Failed to check HACS tables: {e}")
        return {"error": str(e)}


async def verify_database_environment() -> dict[str, Any]:
    """
    Comprehensive environment and database verification.
    
    Returns:
        Dictionary with environment variables, connection status, and recommendations
    """
    # Check environment variables
    env_vars = {
        "DATABASE_URL": os.getenv("DATABASE_URL"),
        "HACS_DATABASE_URL": os.getenv("HACS_DATABASE_URL"),
        "POSTGRES_URL": os.getenv("POSTGRES_URL"),
        "HACS_POSTGRES_URL": os.getenv("HACS_POSTGRES_URL")
    }

    # Find the first available database URL
    database_url = None
    for var_name, url in env_vars.items():
        if url:
            database_url = url
            break

    result = {
        "environment_variables": {
            k: "✓ Set" if v else "✗ Not set" for k, v in env_vars.items()
        },
        "database_url_source": None,
        "connection_test": None,
        "hacs_schemas": None,
        "recommendations": []
    }

    if database_url:
        # Find which env var provided the URL
        for var_name, url in env_vars.items():
            if url == database_url:
                result["database_url_source"] = var_name
                break

        # Test connection
        db_info = await get_database_info(database_url)
        result["connection_test"] = db_info

        if "error" not in db_info:
            # Test HACS schemas
            schema_info = await get_hacs_schema_summary(database_url)
            result["hacs_schemas"] = schema_info

            # Generate recommendations
            if not schema_info.get("migration_complete", False):
                result["recommendations"].append("Run HACS migrations: `from hacs_persistence.migrations import run_migration; await run_migration()`")

            if not schema_info.get("pgvector_enabled", False):
                result["recommendations"].append("Enable pgvector extension for vector operations")
        else:
            result["recommendations"].append("Fix database connection issues before proceeding")
    else:
        result["recommendations"].append("Set DATABASE_URL environment variable")

    return result


async def get_generic_table_status(database_url: str | None = None) -> dict[str, Any]:
    """
    Check status of the generic HACS resources table (public.hacs_resources).
    
    Args:
        database_url: PostgreSQL connection URL (uses DATABASE_URL if None)
        
    Returns:
        Dictionary with table status and basic statistics
    """
    if not database_url:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            return {"error": "DATABASE_URL not provided"}

    try:
        async with await psycopg.AsyncConnection.connect(database_url) as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                # Check if table exists
                await cur.execute("""
                    SELECT EXISTS(
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'hacs_resources'
                    )
                """)
                table_exists = (await cur.fetchone())["exists"]

                if not table_exists:
                    return {
                        "table_exists": False,
                        "message": "Generic HACS resources table not found"
                    }

                # Get basic statistics
                await cur.execute("""
                    SELECT 
                        COUNT(*) as total_resources,
                        COUNT(DISTINCT resource_type) as resource_types,
                        MIN(created_at) as earliest_record,
                        MAX(created_at) as latest_record
                    FROM public.hacs_resources
                """)
                stats = await cur.fetchone()

                # Get resource type breakdown
                await cur.execute("""
                    SELECT resource_type, COUNT(*) as count
                    FROM public.hacs_resources
                    GROUP BY resource_type
                    ORDER BY count DESC
                    LIMIT 10
                """)
                type_breakdown = await cur.fetchall()

                return {
                    "table_exists": True,
                    "total_resources": stats["total_resources"],
                    "resource_types_count": stats["resource_types"],
                    "earliest_record": stats["earliest_record"].isoformat() if stats["earliest_record"] else None,
                    "latest_record": stats["latest_record"].isoformat() if stats["latest_record"] else None,
                    "resource_breakdown": {
                        row["resource_type"]: row["count"] for row in type_breakdown
                    }
                }

    except Exception as e:
        logger.error(f"Failed to get generic table status: {e}")
        return {"error": str(e)}
