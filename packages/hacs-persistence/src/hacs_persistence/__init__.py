"""
HACS Persistence Layer

This package provides a robust persistence layer for HACS, including
database adapters, schema management, data mapping, and migrations.
"""

# from hacs_tools.vectorization import VectorMetadata, VectorStore
from .adapter import PostgreSQLAdapter, create_postgres_adapter

# Optional granular adapter – depends on hacs_models package
try:
    from .granular_adapter import GranularPostgreSQLAdapter  # noqa: F401
except ModuleNotFoundError:
    GranularPostgreSQLAdapter = None  # type: ignore
from .resource_mapper import ResourceMapper
from .schema import HACSSchemaManager

# Import migration functionality
try:
    from .migrations import HACSDatabaseMigration, run_migration
    from .migrations import get_migration_status as _get_migration_status
    MIGRATIONS_AVAILABLE = True
except ImportError:
    HACSDatabaseMigration = None
    run_migration = None
    _get_migration_status = None
    MIGRATIONS_AVAILABLE = False

# Vector store integration (conditional import to avoid circular dependencies)
QdrantVectorStore = None  # Available via dependency injection

# pgvector integration
try:
    from .vector_store import HACSVectorStore, create_vector_store
    PGVECTOR_AVAILABLE = True
except ImportError:
    HACSVectorStore = None
    create_vector_store = None
    PGVECTOR_AVAILABLE = False

__all__ = [
    "PostgreSQLAdapter",
    "create_postgres_adapter",
    "GranularPostgreSQLAdapter",
    "ResourceMapper",
    "HACSSchemaManager",
    "HACSDatabaseMigration",
    "run_migration",
    "QdrantVectorStore",
    "HACSVectorStore",
    "create_vector_store",
    "initialize_hacs_database",
    "get_migration_status"
]

def initialize_hacs_database(database_url: str, force_migration: bool = False) -> bool:
    """
    Initialize HACS database with full schema migration.

    Args:
        database_url: PostgreSQL connection URL
        force_migration: Force migration even if schemas exist

    Returns:
        True if initialization successful, False otherwise
    """
    if not MIGRATIONS_AVAILABLE:
        print("Migration functionality not available")
        return False

    try:
        # Check if migration needed
        if not force_migration:
            status = get_migration_status(database_url)
            if status.get("schemas_exist", False):
                print("HACS schemas already exist, skipping migration")
                return True

        return run_migration(database_url)

    except Exception as e:
        print(f"Database initialization failed: {e}")
        return False


def get_migration_status(database_url: str) -> dict:
    """
    Get current migration status of HACS database.

    Args:
        database_url: PostgreSQL connection URL

    Returns:
        Dictionary with migration status information
    """
    if not MIGRATIONS_AVAILABLE or not _get_migration_status:
        return {
            "schemas_exist": False,
            "schemas": [],
            "migration_table_exists": False,
            "migration_records": [],
            "status": "error",
            "error": "Migration functionality not available"
        }

    return _get_migration_status(database_url)
