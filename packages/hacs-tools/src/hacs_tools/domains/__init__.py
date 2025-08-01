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
from .clinical_workflows import (
    execute_clinical_workflow,
    get_clinical_guidance,
    query_with_datarequirement,
    validate_clinical_protocol,
)
from .memory_operations import (
    create_hacs_memory,
    search_hacs_memories,
    consolidate_memories,
    retrieve_context,
    analyze_memory_patterns,
)
from .vector_search import (
    store_embedding,
    vector_similarity_search,
    vector_hybrid_search,
    get_vector_collection_stats,
    optimize_vector_collection,
)
from .schema_discovery import (
    discover_hacs_resources,
    get_hacs_resource_schema,
    analyze_resource_fields,
    compare_resource_schemas,
)
from .development_tools import (
    create_resource_stack,
    create_clinical_template,
    optimize_resource_for_llm,
)
from .fhir_integration import (
    convert_to_fhir,
    validate_fhir_compliance,
    process_fhir_bundle,
    lookup_fhir_terminology,
)
from .healthcare_analytics import (
    calculate_quality_measures,
    analyze_population_health,
    generate_clinical_dashboard,
    perform_risk_stratification,
)
from .ai_integrations import (
    deploy_healthcare_ai_model,
    run_clinical_inference,
    preprocess_medical_data,
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
    
    # Clinical Workflow Tools
    "execute_clinical_workflow",
    "get_clinical_guidance",
    "query_with_datarequirement",
    "validate_clinical_protocol",
    
    # Memory Operations Tools
    "create_hacs_memory",
    "search_hacs_memories",
    "consolidate_memories",
    "retrieve_context",
    "analyze_memory_patterns",
    
    # Vector Search Tools
    "store_embedding",
    "vector_similarity_search",
    "vector_hybrid_search",
    "get_vector_collection_stats",
    "optimize_vector_collection",
    
    # Schema Discovery Tools
    "discover_hacs_resources",
    "get_hacs_resource_schema",
    "analyze_resource_fields",
    "compare_resource_schemas",
    
    # Development Tools
    "create_resource_stack",
    "create_clinical_template",
    "optimize_resource_for_llm",
    
    # FHIR Integration Tools
    "convert_to_fhir",
    "validate_fhir_compliance",
    "process_fhir_bundle",
    "lookup_fhir_terminology",
    
    # Healthcare Analytics Tools
    "calculate_quality_measures",
    "analyze_population_health",
    "generate_clinical_dashboard",
    "perform_risk_stratification",
    
    # AI/ML Integration Tools
    "deploy_healthcare_ai_model",
    "run_clinical_inference",
    "preprocess_medical_data",
    
    # Admin Operations Tools
    "run_database_migration",
    "check_migration_status",
    "describe_database_schema",
    "get_table_structure",
    "test_database_connection",
] 