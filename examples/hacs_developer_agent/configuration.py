"""Define the configurable parameters for the HACS admin agent."""

from __future__ import annotations

import os
from dataclasses import dataclass, field, fields
from typing import Annotated, Optional

from langchain_core.runnables import RunnableConfig, ensure_config


@dataclass(kw_only=True)
class Configuration:
    """The configuration for the HACS admin agent."""

    model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="openai/gpt-4.1-mini",
        metadata={
            "description": "The name of the language model to use for the agent. "
            "Should be in the form: provider/model-name."
        },
    )

    # Database Configuration for Admin Operations (loaded from secrets)
    database_url: Optional[str] = field(
        default=None,
        metadata={
            "description": "PostgreSQL database URL for HACS admin operations. "
            "Loaded from runtime config secrets as __database_url."
        },
    )

    # HACS MCP Server Configuration (loaded from secrets)
    hacs_mcp_server_url: Optional[str] = field(
        default=None,
        metadata={
            "description": "URL for the HACS MCP server running in Docker container. "
            "Loaded from runtime config secrets as __hacs_mcp_server_url."
        },
    )

    # API Keys (loaded from secrets)
    anthropic_api_key: Optional[str] = field(
        default=None,
        metadata={
            "description": "Anthropic API key for Claude models. "
            "Loaded from runtime config secrets as __anthropic_api_key."
        },
    )

    openai_api_key: Optional[str] = field(
        default=None,
        metadata={
            "description": "OpenAI API key for GPT models. "
            "Loaded from runtime config secrets as __openai_api_key."
        },
    )

    # Admin Operation Limits
    max_admin_operations: int = field(
        default=3,
        metadata={
            "description": "The maximum number of admin operations allowed in a single session."
        },
    )

    max_loops: int = field(
        default=3,
        metadata={
            "description": "The maximum number of agent loops before termination (simplified for admin)."
        },
    )

    # Admin Security Settings
    require_confirmation: bool = field(
        default=True,
        metadata={
            "description": "Whether to require confirmation for destructive admin operations."
        },
    )

    enable_audit_logging: bool = field(
        default=True,
        metadata={
            "description": "Whether to enable detailed audit logging for admin operations."
        },
    )

    # Migration and Schema Settings
    enable_migration_validation: bool = field(
        default=True,
        metadata={
            "description": "Whether to enable validation before running database migrations."
        },
    )

    migration_timeout: int = field(
        default=300,
        metadata={
            "description": "Timeout in seconds for database migration operations."
        },
    )

    max_schema_results: int = field(
        default=20,
        metadata={
            "description": "The maximum number of schema elements to return in inspection operations."
        },
    )

    # Resource Management Settings  
    enable_fhir_validation: bool = field(
        default=True,
        metadata={
            "description": "Whether to enable FHIR validation for created HACS resources."
        },
    )

    max_resource_results: int = field(
        default=50,
        metadata={
            "description": "The maximum number of HACS resources to return in "
            "admin operations."
        },
    )

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> Configuration:
        """Load configuration with defaults for the given invocation.

        Runtime secrets are passed with __ prefix in configurable to prevent
        tracing. Example: {"configurable": {"__database_url": "postgresql://...",
        "model": "openai/gpt-4"}}
        """
        config = ensure_config(config)
        configurable = config.get("configurable") or {}
        _fields = {f.name for f in fields(cls) if f.init}

        # Build configuration values from both regular and secret fields
        config_values = {}

        # Add regular configuration fields (no __ prefix)
        for k, v in configurable.items():
            if k in _fields and not k.startswith("__"):
                config_values[k] = v

        # Add secret fields (with __ prefix, map to field without prefix)
        secret_mappings = {
            "__database_url": "database_url",
            "__hacs_mcp_server_url": "hacs_mcp_server_url",
            "__anthropic_api_key": "anthropic_api_key",
            "__openai_api_key": "openai_api_key",
        }

        for secret_key, field_name in secret_mappings.items():
            if secret_key in configurable and field_name in _fields:
                config_values[field_name] = configurable[secret_key]

        # Fallback to environment variables for missing secrets
        env_fallbacks = {
            "database_url": os.getenv("DATABASE_URL"),
            "hacs_mcp_server_url": os.getenv(
                "HACS_MCP_SERVER_URL", "http://localhost:8000"
            ),
            "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
        }

        for field_name, env_value in env_fallbacks.items():
            if (field_name not in config_values and env_value and 
                field_name in _fields):
                config_values[field_name] = env_value

        return cls(**config_values)


# Private configuration data that was previously in state
class PrivateConfig:
    """Private configuration and constants for the admin agent."""
    
    # Default admin permissions
    DEFAULT_ADMIN_PERMISSIONS = [
        "admin:*",
        "database:*", 
        "migration:*",
        "schema:*",
        "resource:*",
        "audit:*"
    ]
    
    # Operation types and their confirmation requirements
    OPERATION_CONFIRMATIONS = {
        "database_migration": True,
        "schema_modification": True,
        "bulk_delete": True,
        "system_reset": True,
        "migration_status": False,
        "schema_inspection": False,
        "discover_resources": False,
        "create_resource": False
    }
    
    # Operation retry limits
    RETRY_LIMITS = {
        "database_migration": 1,  # Database ops shouldn't be retried automatically
        "schema_inspection": 3,
        "resource_creation": 2,
        "resource_discovery": 3,
        "migration_status": 2
    }
    
    # Dangerous operations that require extra validation
    DANGEROUS_OPERATIONS = [
        "database_migration",
        "schema_modification", 
        "bulk_delete",
        "system_reset"
    ]
    
    # Available admin operations
    AVAILABLE_OPERATIONS = [
        "database_migration",
        "migration_status", 
        "schema_inspection",
        "discover_resources",
        "create_resource",
        "general_help"
    ]