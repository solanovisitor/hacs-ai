"""
HACS Tools - Unified LangChain tools for healthcare AI agents.

This single module provides a comprehensive collection of LangChain @tool
decorated functions for all HACS operations, from basic CRUD to advanced,
model-driven clinical workflows.
"""

from hacs_core.utils import VersionManager

from .tools import (
    # All tools collection
    ALL_HACS_TOOLS,
    DataQueryResult,
    GuidanceResult,
    # Result models
    HACSResult,
    ResourceSchemaResult,
    ModelDiscoveryResult,
    FieldAnalysisResult,
    MemoryResult,
    VersionResult,
    WorkflowResult,
    create_datarequirement_query,
    # Enhanced CRUD operations
    create_hacs_record,
    get_hacs_record,
    search_hacs_records,
    update_hacs_record,
    delete_hacs_record,
    # Resource finder tools
    find_resources,
    get_resource_by_id,
    update_resource_by_id,
    delete_resource_by_id,
    # Memory management tools
    create_hacs_memory,
    search_hacs_memories,
    consolidate_memories,
    retrieve_context,
    analyze_memory_patterns,
    # Versioning tools
    version_hacs_resource,
    # Knowledge management
    create_knowledge_item,
    # Schema and validation tools
    get_resource_schema,
    get_hacs_resource_schema,
    validate_resource_data,
    list_available_resources,
    # Model-Driven Tools
    query_with_datarequirement,
    execute_workflow,
    get_clinical_guidance,
    # Model Manipulation Tools
    discover_hacs_resources,
    create_view_resource_schema,
    analyze_resource_fields,
    compare_resource_schemas,
    suggest_view_fields,
    create_multi_resource_schema,
    # Vector Store Operations (pgvector)
    store_embedding,
    vector_similarity_search,
    vector_hybrid_search,
    get_vector_collection_stats,
)

from .model_dev import (
    ModelStackResult,
    ModelTemplateResult,
    create_model_stack,
    create_clinical_template,
    optimize_resource_for_llm,
)

__version__ = VersionManager.TOOL_VERSION

__all__ = [
    # Result models
    "HACSResult",
    "ResourceSchemaResult",
    "ModelDiscoveryResult",
    "FieldAnalysisResult",
    "ModelStackResult",
    "ModelTemplateResult",
    "MemoryResult",
    "VersionResult",
    "DataQueryResult",
    "WorkflowResult",
    "GuidanceResult",
    # Enhanced CRUD operations
    "create_hacs_record",
    "get_hacs_record",
    "search_hacs_records",
    "update_hacs_record",
    "delete_hacs_record",
    # Resource finder tools
    "find_resources",
    "get_resource_by_id",
    "update_resource_by_id",
    "delete_resource_by_id",
    # Memory management tools
    "create_hacs_memory",
    "search_hacs_memories",
    "consolidate_memories",
    "retrieve_context",
    "analyze_memory_patterns",
    # Versioning tools
    "version_hacs_resource",
    # Knowledge management
    "create_knowledge_item",
    # Schema and validation tools
    "get_resource_schema",
    "get_hacs_resource_schema",
    "validate_resource_data",
    "list_available_resources",
    # Model-Driven Tools
    "query_with_datarequirement",
    "create_datarequirement_query",
    "execute_workflow",
    "get_clinical_guidance",
    # Model Manipulation Tools
    "discover_hacs_resources",
    "create_view_resource_schema",
    "analyze_resource_fields",
    "compare_resource_schemas",
    "suggest_view_fields",
    "create_multi_resource_schema",
    # Vector Store Operations (pgvector)
    "store_embedding",
    "vector_similarity_search",
    "vector_hybrid_search",
    "get_vector_collection_stats",
    # Model Development Tools
    "create_model_stack",
    "create_clinical_template",
    "optimize_resource_for_llm",
    # Collections
    "ALL_HACS_TOOLS",
]
