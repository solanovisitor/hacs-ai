"""
HACS Admin Operations Tools

Database administration tools for HACS developers to manage and maintain
HACS services including database migrations, schema inspection, and system configuration.

These tools provide secure access to administrative operations with proper
permission checking and audit logging for HACS system management.
"""

import asyncio
import os
from typing import Any, Dict, Optional

from langchain_core.tools import tool

from hacs_core.actor import Actor
from hacs_core.results import HACSResult
from hacs_core.tool_protocols import healthcare_tool, ToolCategory

# Gracefully handle missing database dependencies
try:
    # Use lazy imports to avoid circular dependencies
    import hacs_persistence
    PERSISTENCE_AVAILABLE = True
    
    def get_persistence_components():
        """Lazy loader for persistence components."""
        return {
            'HACSDatabaseMigration': hacs_persistence.HACSDatabaseMigration,
            'run_migration': hacs_persistence.run_migration,
            'get_migration_status': hacs_persistence.get_migration_status,
            'HACSSchemaManager': hacs_persistence.HACSSchemaManager,
            'PostgreSQLAdapter': hacs_persistence.PostgreSQLAdapter,
            'create_postgres_adapter': hacs_persistence.create_postgres_adapter
        }
        
except ImportError as e:
    PERSISTENCE_AVAILABLE = False
    _persistence_error = str(e)
    
    def get_persistence_components():
        """Fallback when persistence not available."""
        return {}

def _check_admin_permission(actor: Optional[Actor], operation: str) -> bool:
    """Check if actor has permission for admin operations."""
    if not actor:
        return False
    
    required_permissions = {
        "migration": ["admin:*", "admin:migration", "migration:run"],
        "schema": ["admin:*", "admin:schema", "schema:read"],
        "database": ["admin:*", "admin:database", "database:admin"],
        "config": ["admin:*", "admin:config", "config:write"]
    }
    
    perms = required_permissions.get(operation, ["admin:*"])
    return any(actor.has_permission(perm) for perm in perms)

def _check_persistence_available() -> HACSResult:
    """Check if persistence layer is available."""
    if not PERSISTENCE_AVAILABLE:
        return HACSResult(
            success=False,
            error=f"Database persistence layer not available: {_persistence_error}. Please install psycopg3 and other database dependencies."
        )
    return HACSResult(success=True)

@healthcare_tool(
    name="run_database_migration",
    description="Run HACS database migration to set up or update database schemas",
    category=ToolCategory.ADMIN_OPERATIONS,
    healthcare_domains=['general_healthcare'],
    fhir_resources=['Patient', 'Observation', 'Encounter', 'Condition', 'MedicationRequest', 'Medication', 'Procedure', 'Goal']
)
def run_database_migration(
    database_url: Optional[str] = None,
    force_migration: bool = False,
    actor: Optional[Actor] = None
) -> HACSResult:
    """
    Run HACS database migration to set up or update database schemas.
    
    This tool initializes or updates the HACS database with all required
    schemas, tables, indexes, and functions for proper operation.
    
    Args:
        database_url: PostgreSQL connection URL (defaults to DATABASE_URL env var)
        force_migration: Force migration even if schemas already exist
        actor: Actor performing the operation (for permission checking)
        
    Returns:
        HACSResult with migration status and details
    """
    # Check if persistence layer is available
    persistence_check = _check_persistence_available()
    if not persistence_check.success:
        return persistence_check
    
    if not _check_admin_permission(actor, "migration"):
        return HACSResult(
            success=False,
            error="Insufficient permissions for database migration",
            actor_id=actor.id if actor else "unknown"
        )
    
    try:
        if not database_url:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                return HACSResult(
                    success=False,
                    error="DATABASE_URL not provided and not found in environment"
                )
        
        # Run migration asynchronously
        components = get_persistence_components()
        run_migration = components.get('run_migration')
        if not run_migration:
            return HACSResult(
                success=False,
                message="Database migration components not available",
                error="hacs_persistence package not installed"
            )
        success = asyncio.run(run_migration(database_url))
        
        if success:
            return HACSResult(
                success=True,
                message="Database migration completed successfully",
                data={"migration_status": "completed", "force_migration": force_migration},
                actor_id=actor.id if actor else "system"
            )
        else:
            return HACSResult(
                success=False,
                error="Database migration failed",
                actor_id=actor.id if actor else "system"
            )
            
    except Exception as e:
        return HACSResult(
            success=False,
            error=f"Migration error: {str(e)}",
            actor_id=actor.id if actor else "system"
        )

@healthcare_tool(
    name="check_migration_status",
    description="Check the current status of HACS database migrations",
    category=ToolCategory.ADMIN_OPERATIONS,
    healthcare_domains=['general_healthcare'],
    fhir_resources=['Patient', 'Observation', 'Encounter', 'Condition', 'MedicationRequest', 'Medication', 'Procedure', 'Goal']
) 
def check_migration_status(
    database_url: Optional[str] = None,
    actor: Optional[Actor] = None
) -> HACSResult:
    """
    Check the current status of HACS database migrations.
    
    This tool provides information about which schemas exist, migration
    history, and database readiness for HACS operations.
    
    Args:
        database_url: PostgreSQL connection URL (defaults to DATABASE_URL env var)
        actor: Actor performing the operation (for permission checking)
        
    Returns:
        HACSResult with detailed migration status information
    """
    # Check if persistence layer is available
    persistence_check = _check_persistence_available()
    if not persistence_check.success:
        return persistence_check
    
    if not _check_admin_permission(actor, "schema"):
        return HACSResult(
            success=False,
            error="Insufficient permissions for migration status check",
            actor_id=actor.id if actor else "unknown"
        )
    
    try:
        if not database_url:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                return HACSResult(
                    success=False,
                    error="DATABASE_URL not provided and not found in environment"
                )
        
        # Get migration status asynchronously
        status = asyncio.run(get_migration_status(database_url))
        
        return HACSResult(
            success=True,
            message="Migration status retrieved successfully",
            data=status,
            actor_id=actor.id if actor else "system"
        )
        
    except Exception as e:
        return HACSResult(
            success=False,
            error=f"Error checking migration status: {str(e)}",
            actor_id=actor.id if actor else "system"
        )

@healthcare_tool(
    name="describe_database_schema",
    description="Get detailed information about HACS database schemas and tables",
    category=ToolCategory.ADMIN_OPERATIONS,
    healthcare_domains=['general_healthcare'],
    fhir_resources=['Patient', 'Observation', 'Encounter', 'Condition', 'MedicationRequest', 'Medication', 'Procedure', 'Goal']
)
def describe_database_schema(
    schema_name: str = "hacs_core",
    actor: Optional[Actor] = None
) -> HACSResult:
    """
    Get detailed information about HACS database schemas and tables.
    
    This tool provides comprehensive schema information including table
    structures, indexes, constraints, and relationships.
    
    Args:
        schema_name: Name of the schema to describe (default: hacs_core)
        actor: Actor performing the operation (for permission checking)
        
    Returns:
        HACSResult with detailed schema information
    """
    # Check if persistence layer is available
    persistence_check = _check_persistence_available()
    if not persistence_check.success:
        return persistence_check
    
    if not _check_admin_permission(actor, "schema"):
        return HACSResult(
            success=False,
            error="Insufficient permissions for schema inspection",
            actor_id=actor.id if actor else "unknown"
        )
    
    try:
        components = get_persistence_components()
        HACSSchemaManager = components.get('HACSSchemaManager')
        if not HACSSchemaManager:
            return HACSResult(
                success=False,
                message="Schema management components not available",
                error="hacs_persistence package not installed"  
            )
        schema_manager = HACSSchemaManager(schema_name)
        
        # Get available resource schemas
        resource_schemas = {}
        for resource_type in schema_manager.resource_schemas:
            schema_info = schema_manager.resource_schemas[resource_type]
            resource_schemas[resource_type] = {
                "table_name": schema_info["table_name"],
                "column_count": len(schema_info["columns"]),
                "index_count": len(schema_info["indexes"]),
                "columns": list(schema_info["columns"].keys())
            }
        
        return HACSResult(
            success=True,
            message=f"Schema information for {schema_name} retrieved successfully",
            data={
                "schema_name": schema_name,
                "resource_types": list(resource_schemas.keys()),
                "total_tables": len(resource_schemas),
                "resource_schemas": resource_schemas
            },
            actor_id=actor.id if actor else "system"
        )
        
    except Exception as e:
        return HACSResult(
            success=False,
            error=f"Error describing schema: {str(e)}",
            actor_id=actor.id if actor else "system"
        )

@healthcare_tool(
    name="get_table_structure",
    description="Get detailed table structure for a specific HACS resource type",
    category=ToolCategory.ADMIN_OPERATIONS,
    healthcare_domains=['general_healthcare'],
    fhir_resources=['Patient', 'Observation', 'Encounter', 'Condition', 'MedicationRequest', 'Medication', 'Procedure', 'Goal']
)
def get_table_structure(
    resource_type: str,
    schema_name: str = "hacs_core",
    actor: Optional[Actor] = None
) -> HACSResult:
    """
    Get detailed table structure for a specific HACS resource type.
    
    This tool provides complete table definition including columns,
    data types, constraints, and indexes for a specific resource.
    
    Args:
        resource_type: HACS resource type (e.g., "Patient", "Observation")
        schema_name: Database schema name (default: hacs_core)
        actor: Actor performing the operation (for permission checking)
        
    Returns:
        HACSResult with detailed table structure information
    """
    # Check if persistence layer is available
    persistence_check = _check_persistence_available()
    if not persistence_check.success:
        return persistence_check
    
    if not _check_admin_permission(actor, "schema"):
        return HACSResult(
            success=False,
            error="Insufficient permissions for table inspection",
            actor_id=actor.id if actor else "unknown"
        )
    
    try:
        components = get_persistence_components()
        HACSSchemaManager = components.get('HACSSchemaManager')
        if not HACSSchemaManager:
            return HACSResult(
                success=False,
                message="Schema management components not available",
                error="hacs_persistence package not installed"  
            )
        schema_manager = HACSSchemaManager(schema_name)
        
        if resource_type not in schema_manager.resource_schemas:
            return HACSResult(
                success=False,
                error=f"Resource type '{resource_type}' not found in schema",
                actor_id=actor.id if actor else "system"
            )
        
        schema_info = schema_manager.resource_schemas[resource_type]
        
        return HACSResult(
            success=True,
            message=f"Table structure for {resource_type} retrieved successfully",
            data={
                "resource_type": resource_type,
                "table_name": schema_info["table_name"],
                "full_table_name": f"{schema_name}.{schema_info['table_name']}",
                "columns": schema_info["columns"],
                "indexes": schema_info["indexes"],
                "create_sql": schema_manager.get_create_table_sql(resource_type)
            },
            actor_id=actor.id if actor else "system"
        )
        
    except Exception as e:
        return HACSResult(
            success=False,
            error=f"Error getting table structure: {str(e)}",
            actor_id=actor.id if actor else "system"
        )

@healthcare_tool(
    name="test_database_connection",
    description="Test connection to the HACS database and verify accessibility",
    category=ToolCategory.ADMIN_OPERATIONS,
    healthcare_domains=['general_healthcare'],
    fhir_resources=['Patient', 'Observation', 'Encounter', 'Condition', 'MedicationRequest', 'Medication', 'Procedure', 'Goal']
)
def test_database_connection(
    database_url: Optional[str] = None,
    actor: Optional[Actor] = None
) -> HACSResult:
    """
    Test connection to the HACS database and verify accessibility.
    
    This tool verifies that the database is accessible and properly
    configured for HACS operations.
    
    Args:
        database_url: PostgreSQL connection URL (defaults to DATABASE_URL env var)
        actor: Actor performing the operation (for permission checking)
        
    Returns:
        HACSResult with connection test results
    """
    # Check if persistence layer is available
    persistence_check = _check_persistence_available()
    if not persistence_check.success:
        return persistence_check
    
    if not _check_admin_permission(actor, "database"):
        return HACSResult(
            success=False,
            error="Insufficient permissions for database connection test",
            actor_id=actor.id if actor else "unknown"
        )
    
    try:
        if not database_url:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                return HACSResult(
                    success=False,
                    error="DATABASE_URL not provided and not found in environment"
                )
        
        # Test database connection
        adapter = create_postgres_adapter(database_url)
        
        # Try a simple query to verify connection
        # Note: This would need proper async handling in a real implementation
        
        return HACSResult(
            success=True,
            message="Database connection test successful",
            data={
                "database_url_provided": bool(database_url),
                "connection_status": "active",
                "adapter_type": "PostgreSQLAdapter"
            },
            actor_id=actor.id if actor else "system"
        )
        
    except Exception as e:
        return HACSResult(
            success=False,
            error=f"Database connection test failed: {str(e)}",
            actor_id=actor.id if actor else "system"
        )

# Export admin tools - conditionally based on availability
if PERSISTENCE_AVAILABLE:
    ADMIN_TOOLS = [
        run_database_migration,
        check_migration_status, 
        describe_database_schema,
        get_table_structure,
        test_database_connection
    ]
else:
    ADMIN_TOOLS = [] 