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

    🏥 FHIR Integration (4 tools)
        - FHIR conversion and validation
        - Bundle processing and terminology lookup
        - Healthcare standards compliance

    📈 Healthcare Analytics (4 tools)
        - Quality measures and population health
        - Clinical dashboards and risk stratification
        - Performance monitoring and insights

    🤖 AI/ML Integration (3 tools)
        - Healthcare AI model deployment
        - Clinical inference and predictions
        - Medical data preprocessing

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
from .domains.resource_management import (
    create_hacs_record,
    get_hacs_record,
    update_hacs_record,
    delete_hacs_record,
    search_hacs_records,
)
from .domains.clinical_workflows import (
    execute_clinical_workflow,
    get_clinical_guidance,
    query_with_datarequirement,
    validate_clinical_protocol,
)
from .domains.memory_operations import (
    create_hacs_memory,
    search_hacs_memories,
    consolidate_memories,
    retrieve_context,
    analyze_memory_patterns,
)
from .domains.vector_search import (
    store_embedding,
    vector_similarity_search,
    vector_hybrid_search,
    get_vector_collection_stats,
    optimize_vector_collection,
)
from .domains.schema_discovery import (
    discover_hacs_resources,
    get_hacs_resource_schema,
    analyze_resource_fields,
    compare_resource_schemas,
)
from .domains.development_tools import (
    create_resource_stack,
    create_clinical_template,
    optimize_resource_for_llm,
)
from .domains.fhir_integration import (
    convert_to_fhir,
    validate_fhir_compliance,
    process_fhir_bundle,
    lookup_fhir_terminology,
)
from .domains.healthcare_analytics import (
    calculate_quality_measures,
    analyze_population_health,
    generate_clinical_dashboard,
    perform_risk_stratification,
)
from .domains.ai_integrations import (
    deploy_healthcare_ai_model,
    run_clinical_inference,
    preprocess_medical_data,
)
from .domains.admin_operations import (
    run_database_migration,
    check_migration_status,
    describe_database_schema,
    get_table_structure,
    test_database_connection,
)

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
    
    # FHIR Integration Tools
    convert_to_fhir,
    validate_fhir_compliance,
    process_fhir_bundle,
    lookup_fhir_terminology,
    
    # Healthcare Analytics Tools
    calculate_quality_measures,
    analyze_population_health,
    generate_clinical_dashboard,
    perform_risk_stratification,
    
    # AI/ML Integration Tools
    deploy_healthcare_ai_model,
    run_clinical_inference,
    preprocess_medical_data,
    
    # Admin Operations Tools
    run_database_migration,
    check_migration_status,
    describe_database_schema,
    get_table_structure,
    test_database_connection,
]
