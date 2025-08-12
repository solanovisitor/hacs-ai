"""
HACS Configuration System

This module provides centralized configuration management for HACS,
supporting environment-based configuration and validation.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class LogLevel(str, Enum):
    """Logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class HACSSettings(BaseModel):
    """Centralized HACS configuration settings.

    All settings can be configured via environment variables with the HACS_ prefix.
    """

    # Core settings
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )

    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Logging level"
    )

    # Service URLs - Configurable for deployment flexibility
    mcp_server_host: str = Field(
        default="localhost",
        description="MCP server host address"
    )

    mcp_server_port: int = Field(
        default=8000,
        description="MCP server port"
    )

    langgraph_agent_host: str = Field(
        default="localhost",
        description="LangGraph agent host address"
    )

    langgraph_agent_port: int = Field(
        default=8001,
        description="LangGraph agent port"
    )

    database_host: str = Field(
        default="localhost",
        description="Database host address"
    )

    database_port: int = Field(
        default=5432,
        description="Database port"
    )

    # Vector store configuration
    vector_store_host: str = Field(
        default="localhost",
        description="Vector store host address (for Qdrant)"
    )

    vector_store_port: int = Field(
        default=6333,
        description="Vector store port (for Qdrant)"
    )

    # Computed service URLs
    @property
    def mcp_server_url(self) -> str:
        """Get the complete MCP server URL."""
        return f"http://{self.mcp_server_host}:{self.mcp_server_port}"

    @property
    def langgraph_agent_url(self) -> str:
        """Get the complete LangGraph agent URL."""
        return f"http://{self.langgraph_agent_host}:{self.langgraph_agent_port}"

    @property
    def database_url_host(self) -> str:
        """Get the database host:port combination."""
        return f"{self.database_host}:{self.database_port}"

    @property
    def vector_store_url(self) -> str:
        """Get the complete vector store URL."""
        return f"http://{self.vector_store_host}:{self.vector_store_port}"

    # LLM Provider Settings - OpenAI
    openai_api_key: str | None = Field(
        default=None,
        description="OpenAI API key"
    )

    openai_model: str = Field(
        default="gpt-4.1-mini", description="Default OpenAI model", env="HACS_OPENAI_MODEL"
    )

    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Default OpenAI embedding model",
        env="HACS_OPENAI_EMBEDDING_MODEL",
    )

    openai_base_url: str | None = Field(
        default=None, description="OpenAI base URL", env="HACS_OPENAI_BASE_URL"
    )

    openai_organization: str | None = Field(
        default=None,
        description="OpenAI organization ID",
        env="HACS_OPENAI_ORGANIZATION",
    )

    # LLM Provider Settings - Anthropic
    anthropic_api_key: str | None = Field(
        default=None, description="Anthropic API key", env="ANTHROPIC_API_KEY"
    )

    anthropic_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Default Anthropic model",
        env="HACS_ANTHROPIC_MODEL",
    )

    anthropic_base_url: str | None = Field(
        default=None, description="Anthropic base URL", env="HACS_ANTHROPIC_BASE_URL"
    )

    # Vector Store Settings - Pinecone
    pinecone_api_key: str | None = Field(
        default=None, description="Pinecone API key", env="PINECONE_API_KEY"
    )

    pinecone_environment: str | None = Field(
        default=None, description="Pinecone environment", env="PINECONE_ENVIRONMENT"
    )

    pinecone_index_name: str = Field(
        default="hacs-default",
        description="Default Pinecone index name",
        env="HACS_PINECONE_INDEX_NAME",
    )

    # Vector Store Settings - Qdrant
    qdrant_url: str = Field(
        default="http://localhost:6333",
        description="Qdrant server URL",
        env="HACS_QDRANT_URL",
    )

    qdrant_api_key: str | None = Field(
        default=None, description="Qdrant API key", env="QDRANT_API_KEY"
    )

    qdrant_collection_name: str = Field(
        default="hacs_default",
        description="Default Qdrant collection name",
        env="HACS_QDRANT_COLLECTION_NAME",
    )

    # Persistence Settings - PostgreSQL
    postgres_url: str | None = Field(
        default=None, description="PostgreSQL connection URL.", env="HACS_POSTGRES_URL"
    )

    postgres_schema: str = Field(
        default="public",
        description="The database schema to use.",
        env="HACS_POSTGRES_SCHEMA",
    )

    # Main database URL (standard PostgreSQL format)
    database_url: str | None = Field(
        default=None, description="Database connection URL", env="HACS_DATABASE_URL"
    )

    # Agent Framework Settings
    langgraph_memory_store: str = Field(
        default="memory",
        description="LangGraph memory store type",
        env="HACS_LANGGRAPH_MEMORY_STORE",
    )

    # Performance Settings
    request_timeout: float = Field(
        default=30.0,
        description="Default request timeout in seconds",
        env="HACS_REQUEST_TIMEOUT",
    )

    max_retries: int = Field(
        default=3,
        description="Maximum number of retries for failed requests",
        env="HACS_MAX_RETRIES",
    )

    # Default Actor Settings
    default_actor_permissions: list[str] = Field(
        default=["llm:generate", "memory:read", "memory:write", "evidence:read"],
        description="Default permissions for new actors",
    )

    class Config:
        """Pydantic configuration."""

        env_prefix = "HACS_"
        case_sensitive = False
        validate_assignment = True

    @field_validator("log_level", mode="before")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        if isinstance(v, str):
            return LogLevel(v.upper())
        return v

    @property
    def openai_enabled(self) -> bool:
        """Check if OpenAI is configured."""
        return self.openai_api_key is not None

    @property
    def anthropic_enabled(self) -> bool:
        """Check if Anthropic is configured."""
        return self.anthropic_api_key is not None

    @property
    def pinecone_enabled(self) -> bool:
        """Check if Pinecone is configured."""
        return self.pinecone_api_key is not None

    @property
    def qdrant_enabled(self) -> bool:
        """Check if Qdrant is configured."""
        return True  # Qdrant can work without API key for local instances

    @property
    def postgres_enabled(self) -> bool:
        """Check if PostgreSQL is configured."""
        return (self.database_url is not None and self.database_url.strip() != "") or (
            self.postgres_url is not None and self.postgres_url.strip() != ""
        )

    @property
    def supabase_enabled(self) -> bool:
        """Check if Supabase is configured."""
        return self.supabase_url is not None and self.supabase_anon_key is not None

    def get_openai_config(self) -> dict[str, Any]:
        """Get OpenAI configuration."""
        return {
            "api_key": self.openai_api_key,
            "model": self.openai_model,
            "embedding_model": self.openai_embedding_model,
            "base_url": self.openai_base_url,
            "organization": self.openai_organization,
            "timeout": self.request_timeout,
            "max_retries": self.max_retries,
        }

    def get_anthropic_config(self) -> dict[str, Any]:
        """Get Anthropic configuration."""
        return {
            "api_key": self.anthropic_api_key,
            "model": self.anthropic_model,
            "base_url": self.anthropic_base_url,
            "timeout": self.request_timeout,
            "max_retries": self.max_retries,
        }

    def get_pinecone_config(self) -> dict[str, Any]:
        """Get Pinecone configuration."""
        return {
            "api_key": self.pinecone_api_key,
            "environment": self.pinecone_environment,
            "index_name": self.pinecone_index_name,
        }

    def get_qdrant_config(self) -> dict[str, Any]:
        """Get Qdrant configuration."""
        return {
            "url": self.qdrant_url,
            "api_key": self.qdrant_api_key,
            "collection_name": self.qdrant_collection_name,
        }

    def get_postgres_config(self) -> dict[str, Any]:
        """Get PostgreSQL configuration."""
        return {
            "url": self.postgres_url,
            "database_url": self.database_url,
            "schema_name": self.postgres_schema,
        }

    def extract_postgres_params(self) -> dict[str, str]:
        """Extract individual PostgreSQL connection parameters from DATABASE_URL."""
        from urllib.parse import urlparse

        db_url = self.database_url or self.postgres_url
        if not db_url:
            return {}

        parsed = urlparse(db_url)
        return {
            "user": parsed.username,
            "password": parsed.password,
            "host": parsed.hostname,
            "port": str(parsed.port or 5432),
            "dbname": parsed.path.lstrip("/"),
        }


# Global settings instance
_settings: HACSSettings | None = None


def get_settings() -> HACSSettings:
    """Get the global HACS settings instance.

    Returns:
        The global settings instance, creating it if necessary
    """
    global _settings
    if _settings is None:
        _settings = HACSSettings()
    return _settings


def reset_settings() -> None:
    """Reset the global settings instance.

    Useful for testing or when configuration changes.
    """
    global _settings
    _settings = None


def configure_hacs(**kwargs: Any) -> HACSSettings:
    """Configure HACS with explicit settings.

    Args:
        **kwargs: Configuration values to override

    Returns:
        The configured settings instance
    """
    global _settings
    _settings = HACSSettings(**kwargs)
    return _settings


__all__ = [
    "HACSSettings",
    "LogLevel",
    "get_settings",
    "reset_settings",
    "configure_hacs",
]
