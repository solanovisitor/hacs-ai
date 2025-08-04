"""HACS Tools Package

This package provides a comprehensive suite of tools for healthcare AI agents.
All tools are now organized into domain-specific modules for better architecture.
"""

# Import all tools from the main tools module (which imports from domains)
from .tools import *

# Import specific domain modules for direct access if needed
from . import domains

# For backwards compatibility, import result types from hacs_core
from hacs_core.results import (
    HACSResult,
    ResourceSchemaResult,
    ResourceDiscoveryResult,
    FieldAnalysisResult,
    DataQueryResult,
    WorkflowResult,
    GuidanceResult,
    MemoryResult,
    VersionResult,
    ResourceStackResult,
    ResourceTemplateResult,
    VectorStoreResult,
)

# Import backwards compatibility aliases from model_dev
from .model_dev import create_model_stack, optimize_model_for_llm

__version__ = "0.3.0"

__all__ = [
    # Result Models (from hacs_core.results)
    "HACSResult",
    "ResourceSchemaResult",
    "ResourceDiscoveryResult",
    "FieldAnalysisResult",
    "DataQueryResult",
    "WorkflowResult",
    "GuidanceResult", 
    "MemoryResult",
    "VersionResult",
    "ResourceStackResult",
    "ResourceTemplateResult",
    "VectorStoreResult",
    
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
    
    # Backwards compatibility aliases
    "create_model_stack",
    "optimize_model_for_llm",
    
    # Domain modules
    "domains",
    
    # All tools list
    "ALL_HACS_TOOLS"
]
