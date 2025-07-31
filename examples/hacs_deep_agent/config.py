"""
HACS Admin Agent Configuration

Centralized configuration for the HACS Admin Agent, replacing state-based
configuration with a cleaner config-driven approach.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from hacs_core.actor import Actor


@dataclass
class AdminAgentConfig:
    """Configuration for HACS Admin Agent."""
    
    # Core agent settings
    primary_actor: str = "HACS Admin Agent"
    instructions: str = "You are a HACS system administrator focused on database management, configuration, and operations."
    
    # Model configuration
    model_provider: str = "anthropic"  # "anthropic" or "openai"
    model_name: str = "claude-3-sonnet-20240229"
    
    # Admin permissions and security
    admin_permissions: List[str] = None
    require_authentication: bool = True
    
    # Database configuration
    database_url: Optional[str] = None
    auto_migrate: bool = False
    
    # Subagent configuration
    enabled_subagents: List[str] = None
    max_delegation_depth: int = 2
    
    # Tool configuration
    additional_tools: List[str] = None
    disabled_tools: List[str] = None
    
    # Operational settings
    max_iterations: int = 10
    timeout_seconds: int = 300
    
    # Logging and monitoring
    audit_enabled: bool = True
    log_level: str = "INFO"
    
    def __post_init__(self):
        """Initialize default values."""
        if self.admin_permissions is None:
            self.admin_permissions = [
                "admin:*",
                "migration:run", 
                "schema:read",
                "database:admin",
                "config:write"
            ]
        
        if self.enabled_subagents is None:
            self.enabled_subagents = [
                "database_admin_specialist",
                "system_config_specialist", 
                "data_management_specialist",
                "vector_store_specialist",
                "devops_specialist"
            ]
        
        if self.additional_tools is None:
            self.additional_tools = []
            
        if self.disabled_tools is None:
            self.disabled_tools = []


# Default configuration instance
DEFAULT_ADMIN_CONFIG = AdminAgentConfig()


# Available admin subagent configurations
ADMIN_SUBAGENT_CONFIGS = {
    "database_admin_specialist": {
        "name": "Database Admin Specialist",
        "description": "Specializes in database migrations, schema management, and database health monitoring",
        "tools": [
            "run_database_migration",
            "check_migration_status", 
            "describe_database_schema",
            "get_table_structure",
            "test_database_connection"
        ],
        "max_iterations": 5
    },
    
    "system_config_specialist": {
        "name": "System Config Specialist", 
        "description": "Specializes in HACS resource configuration and service optimization",
        "tools": [
            "discover_hacs_resources",
            "get_hacs_resource_schema",
            "compare_resource_schemas",
            "create_resource_stack",
            "optimize_resource_for_llm"
        ],
        "max_iterations": 5
    },
    
    "data_management_specialist": {
        "name": "Data Management Specialist",
        "description": "Specializes in data operations, record management, and data quality",
        "tools": [
            "create_hacs_record",
            "get_hacs_record", 
            "update_hacs_record",
            "delete_hacs_record",
            "search_hacs_records"
        ],
        "max_iterations": 5
    },
    
    "vector_store_specialist": {
        "name": "Vector Store Specialist",
        "description": "Specializes in vector operations, semantic search, and embedding management", 
        "tools": [
            "store_embedding",
            "vector_similarity_search",
            "vector_hybrid_search",
            "get_vector_collection_stats",
            "optimize_vector_collection"
        ],
        "max_iterations": 5
    },
    
    "devops_specialist": {
        "name": "DevOps Specialist",
        "description": "Specializes in deployment automation, environment setup, and infrastructure",
        "tools": [
            "run_database_migration",
            "test_database_connection",
            "create_resource_stack",
            "discover_hacs_resources"
        ],
        "max_iterations": 5
    }
}


def get_admin_config(
    primary_actor: str = None,
    model_provider: str = None,
    enabled_subagents: List[str] = None,
    **kwargs
) -> AdminAgentConfig:
    """
    Get admin agent configuration with optional overrides.
    
    Args:
        primary_actor: Name of the primary admin actor
        model_provider: AI model provider ("anthropic" or "openai")
        enabled_subagents: List of subagent names to enable
        **kwargs: Additional configuration overrides
        
    Returns:
        AdminAgentConfig instance
    """
    config = AdminAgentConfig()
    
    if primary_actor:
        config.primary_actor = primary_actor
        
    if model_provider:
        config.model_provider = model_provider
        if model_provider == "openai":
            config.model_name = "gpt-4"
            
    if enabled_subagents:
        config.enabled_subagents = enabled_subagents
        
    # Apply any additional overrides
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
            
    return config


def create_admin_actor(config: AdminAgentConfig) -> Actor:
    """
    Create admin Actor with proper permissions.
    
    Args:
        config: Admin agent configuration
        
    Returns:
        Actor instance with admin permissions
    """
    actor = Actor(
        name=config.primary_actor,
        role="admin"
    )
    
    # Add admin permissions (this would need to be implemented in Actor model)
    # actor.add_permissions(config.admin_permissions)
    
    return actor


# Base prompt for admin agent
ADMIN_BASE_PROMPT = """You are a HACS Admin Agent specialized in system administration and database management.

## Core Responsibilities

- **Database Administration**: Run migrations, manage schemas, monitor database health
- **System Configuration**: Configure HACS resources, optimize performance
- **Data Management**: Perform CRUD operations, ensure data quality
- **Vector Operations**: Manage embeddings, optimize semantic search
- **DevOps**: Automate deployments, manage infrastructure

## Available Tools

You have access to specialized admin tools for database operations, resource management, 
schema discovery, vector operations, and system configuration.

## Task Delegation

Use the `delegate_admin_task` tool to route complex tasks to specialized subagents:
- Database operations → database_admin_specialist
- System configuration → system_config_specialist  
- Data operations → data_management_specialist
- Vector operations → vector_store_specialist
- Infrastructure → devops_specialist

## Best Practices

1. **Safety First**: Always validate operations before execution
2. **Permission Checks**: Verify actor permissions for admin operations
3. **Audit Trail**: Log all administrative actions
4. **Documentation**: Provide clear explanations of changes
5. **Validation**: Test changes in development before production

Focus on maintaining system reliability, data integrity, and operational efficiency.""" 