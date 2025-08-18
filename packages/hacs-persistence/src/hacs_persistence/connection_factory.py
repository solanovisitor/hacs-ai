"""
HACS Persistence Connection Factory

This module provides a centralized factory for creating database connections,
managing connection pooling, and handling database initialization.
"""

import logging
import asyncio
import os
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from .adapter import PostgreSQLAdapter, create_postgres_adapter
from .schema import HACSSchemaManager
from .migrations import HACSDatabaseMigration, run_migration, get_migration_status

logger = logging.getLogger(__name__)


class HACSConnectionFactory:
    """
    Factory for creating and managing HACS database connections.
    
    Provides centralized connection management, automatic migration,
    and connection pooling for HACS persistence operations.
    """
    
    _instance: Optional['HACSConnectionFactory'] = None
    _adapters: Dict[str, PostgreSQLAdapter] = {}
    
    def __new__(cls) -> 'HACSConnectionFactory':
        """Singleton pattern for connection factory."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_adapter(
        cls,
        database_url: Optional[str] = None,
        schema_name: str = "public",
        auto_migrate: bool = True,
        pool_size: int = 10
    ) -> PostgreSQLAdapter:
        """
        Get or create a database adapter with connection pooling.
        
        Args:
            database_url: PostgreSQL connection URL (defaults to env var)
            schema_name: Database schema name
            auto_migrate: Whether to automatically run migrations
            pool_size: Connection pool size
            
        Returns:
            Configured PostgreSQL adapter
            
        Raises:
            ValueError: If database URL is not provided or invalid
            ConnectionError: If database connection fails
        """
        # Get database URL from environment if not provided
        if not database_url:
            database_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
            if not database_url:
                raise ValueError(
                    "Database URL not provided. Set DATABASE_URL environment variable "
                    "or pass database_url parameter."
                )
        
        # Create cache key for adapter reuse
        adapter_key = f"{database_url}:{schema_name}"
        
        # Return existing adapter if available
        if adapter_key in cls._adapters:
            return cls._adapters[adapter_key]
        
        try:
            # Create new adapter - direct instantiation since create_postgres_adapter is async
            adapter = PostgreSQLAdapter(
                database_url=database_url,
                schema_name=schema_name,
                pool_size=pool_size
            )
            
            # Run migration if requested
            if auto_migrate:
                cls._ensure_database_migrated(database_url)
            
            # Cache and return adapter
            cls._adapters[adapter_key] = adapter
            logger.info(f"Created database adapter for schema '{schema_name}'")
            return adapter
            
        except Exception as e:
            logger.error(f"Failed to create database adapter: {e}")
            raise ConnectionError(f"Database connection failed: {e}") from e
    
    @classmethod
    def _ensure_database_migrated(cls, database_url: str) -> bool:
        """
        Ensure database is properly migrated with HACS schemas.
        
        Args:
            database_url: PostgreSQL connection URL
            
        Returns:
            True if migration successful or already completed
            
        Raises:
            RuntimeError: If migration fails
        """
        try:
            # Helper to run async functions from sync context (handles running loop)
            def _run(coro):
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                if loop and loop.is_running():
                    from threading import Thread
                    result = {}
                    err = {}
                    def _runner():
                        try:
                            result['value'] = asyncio.run(coro)
                        except Exception as ex:  # pragma: no cover
                            err['error'] = ex
                    t = Thread(target=_runner, daemon=True)
                    t.start()
                    t.join(timeout=30)
                    if 'error' in err:
                        raise err['error']
                    return result.get('value')
                return asyncio.run(coro)

            # Check migration status
            status = _run(get_migration_status(database_url)) or {}

            if status.get("migration_complete") or status.get("schemas_exist"):
                logger.info("HACS database schemas already exist")
                return True

            # Run migration
            logger.info("Running HACS database migration...")
            success = _run(run_migration(database_url))

            if success:
                logger.info("HACS database migration completed successfully")
                return True
            else:
                raise RuntimeError("Database migration failed")

        except Exception as e:
            logger.error(f"Database migration error: {e}")
            raise RuntimeError(f"Failed to migrate database: {e}") from e
    
    @classmethod
    def create_test_adapter(cls, test_db_url: Optional[str] = None) -> PostgreSQLAdapter:
        """
        Create a database adapter for testing with isolated schema.
        
        Args:
            test_db_url: Test database URL (defaults to test env var)
            
        Returns:
            Test database adapter
        """
        if not test_db_url:
            test_db_url = os.getenv("TEST_DATABASE_URL", "postgresql://test:test@localhost/hacs_test")
        
        return cls.get_adapter(
            database_url=test_db_url,
            schema_name="test_hacs",
            auto_migrate=True,
            pool_size=5
        )
    
    @classmethod
    async def health_check(cls, adapter: PostgreSQLAdapter) -> Dict[str, Any]:
        """
        Perform health check on database adapter.
        
        Args:
            adapter: Database adapter to check
            
        Returns:
            Health check results
        """
        try:
            # Test connection
            await adapter.connect()
            
            # Test basic query
            test_result = await adapter.execute_query(
                "SELECT version() as version, now() as timestamp"
            )
            
            return {
                "status": "healthy",
                "database_version": test_result[0]["version"] if test_result else "unknown",
                "timestamp": test_result[0]["timestamp"] if test_result else None,
                "adapter_name": adapter.name,
                "adapter_version": adapter.version,
                "connection_pool_active": True
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "adapter_name": adapter.name,
                "connection_pool_active": False
            }
    
    @classmethod
    def close_all_connections(cls) -> None:
        """Close all cached database connections."""
        for adapter_key, adapter in cls._adapters.items():
            try:
                if hasattr(adapter, 'close'):
                    adapter.close()
                logger.info(f"Closed database adapter: {adapter_key}")
            except Exception as e:
                logger.warning(f"Error closing adapter {adapter_key}: {e}")
        
        cls._adapters.clear()
    
    @classmethod
    @asynccontextmanager
    async def get_connection(cls, database_url: Optional[str] = None):
        """
        Async context manager for database connections.
        
        Example:
            async with HACSConnectionFactory.get_connection() as adapter:
                result = await adapter.save_record(resource)
        """
        adapter = cls.get_adapter(database_url)
        try:
            await adapter.connect()
            yield adapter
        finally:
            # Connection pooling handles cleanup automatically
            pass


# Convenience functions for common operations

def get_default_adapter() -> PostgreSQLAdapter:
    """Get default database adapter from environment configuration."""
    return HACSConnectionFactory.get_adapter()


def get_test_adapter() -> PostgreSQLAdapter:
    """Get test database adapter."""
    return HACSConnectionFactory.create_test_adapter()


async def ensure_database_ready(database_url: Optional[str] = None) -> bool:
    """
    Ensure database is ready for HACS operations.
    
    Args:
        database_url: Database URL (optional, uses environment if not provided)
        
    Returns:
        True if database is ready
        
    Raises:
        RuntimeError: If database setup fails
    """
    try:
        adapter = HACSConnectionFactory.get_adapter(database_url, auto_migrate=True)
        health = await HACSConnectionFactory.health_check(adapter)
        
        if health["status"] != "healthy":
            raise RuntimeError(f"Database not healthy: {health.get('error', 'Unknown error')}")
        
        logger.info("HACS database is ready for operations")
        return True
        
    except Exception as e:
        logger.error(f"Database readiness check failed: {e}")
        raise RuntimeError(f"Database not ready: {e}") from e
