"""
HACS Tools Domains - Domain-specific tool organization

This package organizes HACS tools into logical domains for better
architecture and maintainability. Each domain focuses on a specific
aspect of healthcare AI agent operations.

Domain Organization:
    🏥 resource_management - CRUD operations for healthcare resources
    🧠 clinical_workflows - Clinical protocols and decision support
    💭 memory_operations - AI agent memory management
    🔍 vector_search - Semantic search and embedding operations
    📊 schema_discovery - Resource schema analysis and discovery
    🛠️ development_tools - Advanced resource composition and templates

All domains use standardized result types from hacs_core.results
and follow healthcare compliance standards.

Author: HACS Development Team
License: MIT
Version: 0.3.0
"""

# Import from all domain modules to make tools available
from .resource_management import (
    create_hacs_record,
    get_hacs_record,
    update_hacs_record,
    delete_hacs_record,
    search_hacs_records,
)
from .workflow_tools import (
    create_activity_definition,
    create_plan_definition,
    create_task_from_activity,
    complete_task,
    fail_task,
)
from .memory_operations import (
    create_hacs_memory,
    search_hacs_memories,
    consolidate_memories,
    retrieve_context,
    analyze_memory_patterns,
)
from .evidence_tools import (
    index_evidence,
    check_evidence,
)
from .schema_discovery import (
    discover_hacs_resources,
    get_hacs_resource_schema,
    analyze_resource_fields,
    compare_resource_schemas,
)
from .modeling_tools import (
    instantiate_hacs_resource,
    validate_hacs_resource,
)
from .bundle_tools import (
    create_resource_bundle,
    add_bundle_entry,
    validate_resource_bundle,
)
from .persistence_tools import (
    persist_hacs_resource,
    read_hacs_resource,
)
from .preferences_tools import (
    set_actor_preference,
    list_actor_preferences,
)
from .admin_operations import (
    run_database_migration,
    check_migration_status,
    describe_database_schema,
    get_table_structure,
    test_database_connection,
)

# Export all tools for external access
__all__ = [
    # Resource Management Tools
    "create_hacs_record",
    "get_hacs_record",
    "update_hacs_record",
    "delete_hacs_record",
    "search_hacs_records",

    # Clinical Workflow Tools (low-level only)
    "create_activity_definition",
    "create_plan_definition",
    "create_task_from_activity",
    "complete_task",
    "fail_task",
    "create_activity_definition",
    "create_plan_definition",
    "create_task_from_activity",
    "complete_task",
    "fail_task",

    # Memory Operations Tools
    "create_hacs_memory",
    "search_hacs_memories",
    "consolidate_memories",
    "retrieve_context",
    "analyze_memory_patterns",

    # Evidence Tools (context-specific vector usage)
    "index_evidence",
    "check_evidence",

    # Schema Discovery Tools
    "discover_hacs_resources",
    "get_hacs_resource_schema",
    "analyze_resource_fields",
    "compare_resource_schemas",

    # Modeling Tools
    "instantiate_hacs_resource",
    "validate_hacs_resource",

    # Development/Template tools removed

    # Bundle Tools
    "create_resource_bundle",
    "add_bundle_entry",
    "validate_resource_bundle",

    # Persistence Tools
    "persist_hacs_resource",
    "read_hacs_resource",

    # Preferences Tools
    "set_actor_preference",
    "list_actor_preferences",

    # Generic FHIR/Analytics domains removed


    # Admin Operations Tools
    "run_database_migration",
    "check_migration_status",
    "describe_database_schema",
    "get_table_structure",
    "test_database_connection",
]