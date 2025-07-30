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

# Import all domain-specific tools
from .resource_management import *
from .clinical_workflows import *
from .memory_operations import *
from .vector_search import *
from .schema_discovery import *
from .development_tools import *

__all__ = [
    # Resource Management Tools (CRUD operations)
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
] 