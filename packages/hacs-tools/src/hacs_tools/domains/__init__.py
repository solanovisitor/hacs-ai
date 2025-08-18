"""
HACS Tools Domains - 4-Domain Tool Organization

This package organizes HACS tools into 4 core domains for healthcare AI agents:

Domain Organization:
    🔧 modeling - Resource instantiation, validation, composition, diffing
    🔍 extraction - Structured extraction, mapping specs, context summarization  
    💾 database - Typed/generic CRUD, registry ops, vector search, migrations
    🤖 agents - Scratchpad, todos, memory, preferences, tool loadout, state management
    🧬 terminology (optional) - UMLS-based code search/match helpers (kept separate from modeling)

All domains use standardized result types from hacs_core.HACSResult
and follow healthcare compliance standards.

Author: HACS Development Team
License: MIT
Version: 0.4.0
"""

# Import from new 4-domain structure
from .modeling import (
    pin_resource,
    compose_bundle,
    validate_resource,
    diff_resources,
    validate_bundle,
)

# Optional: Terminology domain (kept separate from modeling)
try:
    from .terminology import (
        normalize_code,
        search_umls,
        suggest_resource_codings,
        summarize_codable_concepts,
        map_terminology,
    )
except Exception:
    # Terminology tools are optional, import failures are ignored
    normalize_code = None
    search_umls = None
    suggest_resource_codings = None
    summarize_codable_concepts = None
    map_terminology = None

from .extraction import (
    synthesize_mapping_spec,
    extract_variables,
    apply_mapping_spec,
    summarize_context,
)

from .database import (
    save_resource,
    read_resource,
    update_resource,
    delete_resource,
    register_model_version,
    search_knowledge_items,
    search_memories,
    run_migrations,
    get_db_status,
)

from .agents import (
    write_scratchpad,
    read_scratchpad,
    create_todo,
    list_todos,
    complete_todo,
    store_memory,
    retrieve_memories,
    inject_preferences,
    select_tools_for_task,
    summarize_state,
    prune_state,
)

# Legacy imports removed - all functionality consolidated into 4 core domains
# For backward compatibility, legacy tool names are mapped in the __all__ export below

# Export all tools for external access - new 4-domain structure
__all__ = [
    # Modeling Domain - Resource definition, composition, validation
    "pin_resource",
    "compose_bundle", 
    "validate_resource",
    "diff_resources",
    "validate_bundle",
    
    # Extraction Domain - Structured data extraction and mapping
    "synthesize_mapping_spec",
    "extract_variables",
    "apply_mapping_spec",
    "summarize_context",
    
    # Database Domain - CRUD operations, registry, vector search
    "save_resource",
    "read_resource",
    "update_resource", 
    "delete_resource",
    "register_model_version",
    "search_knowledge_items",
    "search_memories",
    "run_migrations",
    "get_db_status",
    
    # Agents Domain - Context engineering for AI agents
    "write_scratchpad",
    "read_scratchpad",
    "create_todo",
    "list_todos",
    "complete_todo",
    "store_memory",
    "retrieve_memories",
    "inject_preferences",
    "select_tools_for_task",
    "summarize_state",
    "prune_state",

    # Terminology (optional)
    "normalize_code",
    "search_umls",
    "suggest_resource_codings",
    "summarize_codable_concepts",
    "map_terminology",
    
    
    # Note: Legacy tool names have been consolidated into the 4 core domains above.
    # Users should migrate to the new domain-specific tool names for better clarity.
]