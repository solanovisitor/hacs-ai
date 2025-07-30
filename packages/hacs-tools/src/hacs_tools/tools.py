"""
HACS Tools - Healthcare Agent Communication Standard Tools Module

This module provides a comprehensive suite of 25+ specialized healthcare tools
designed for AI agents working with clinical data, FHIR resources, and healthcare
workflows. All tools are compatible with LangChain and the Model Context Protocol (MCP)
providing structured responses for seamless integration.

Tool Categories:
    🏥 Resource Management (5 tools)
        - CRUD operations for healthcare resources  
        - Advanced search and filtering

    🧠 Clinical Workflows (4 tools)
        - Clinical decision support and workflow execution
        - Evidence-based recommendations and guidance

    💭 Memory Operations (5 tools)
        - Episodic, procedural, and executive memory storage
        - Semantic search and consolidation
        - Context-aware retrieval

    🔍 Vector Search (5 tools)
        - Semantic search and embedding operations
        - Hybrid search and collection management

    📊 Schema Discovery (4 tools)
        - Resource schema exploration
        - Field analysis and comparison

    🛠️ Development Tools (3 tools)
        - Resource stacking and composition
        - Clinical template generation
        - LLM optimization

Healthcare Standards Compliance:
    - FHIR R4/R5 compatibility
    - Actor-based permissions
    - Audit trail support
    - Clinical error handling
    - HIPAA-aware data processing

Author: HACS Development Team
License: MIT
Version: 0.3.0
Repository: https://github.com/solanovisitor/hacs-ai
"""

# Import all tools from organized domain modules
from .domains import *

# Re-export all tools for backwards compatibility
ALL_HACS_TOOLS = [
    # Resource Management Tools (CRUD operations)
    create_hacs_record,
    get_hacs_record, 
    update_hacs_record,
    delete_hacs_record,
    search_hacs_records,
    
    # Clinical Workflow Tools
    execute_clinical_workflow,
    get_clinical_guidance,
    query_with_datarequirement,
    validate_clinical_protocol,
    
    # Memory Operations Tools
    create_hacs_memory,
    search_hacs_memories,
    consolidate_memories,
    retrieve_context,
    analyze_memory_patterns,
    
    # Vector Search Tools
    store_embedding,
    vector_similarity_search, 
    vector_hybrid_search,
    get_vector_collection_stats,
    optimize_vector_collection,
    
    # Schema Discovery Tools
    discover_hacs_resources,
    get_hacs_resource_schema,
    analyze_resource_fields,
    compare_resource_schemas,
    
    # Development Tools
    create_resource_stack,
    create_clinical_template,
    optimize_resource_for_llm,
]
