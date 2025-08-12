"""
HACS Configuration System

This module provides centralized configuration management for HACS,
supporting environment-based configuration and validation.
"""

from enum import Enum
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogLevel(str, Enum):
    """Logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class HACSSettings(BaseSettings):
    """Centralized HACS configuration settings.

    All settings can be configured via environment variables with the HACS_ prefix.
    Supports secure secret loading via *_FILE environment variables.
    """

    # Environment and deployment settings
    environment: str = Field(
        default="development",
        description="Deployment environment (development, staging, production)",
        env="HACS_ENVIRONMENT"
    )

    dev_mode: bool = Field(
        default=False,
        description="Enable development mode with relaxed security",
        env="HACS_DEV_MODE"
    )

    # Core settings
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )

    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Logging level"
    )

    # MCP Server Configuration
    mcp_server_url: str | None = Field(
        default=None,
        description="Complete MCP server URL (overrides host/port if provided)",
        env="HACS_MCP_SERVER_URL"
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

    # Security Configuration
    api_keys: list[str] = Field(
        default_factory=list,
        description="List of valid API keys for MCP server access",
        env="HACS_API_KEY"
    )

    api_keys_file: str | None = Field(
        default=None,
        description="Path to file containing API keys (one per line)",
        env="HACS_API_KEY_FILE"
    )

    allowed_origins: list[str] = Field(
        default_factory=list,
        description="Allowed CORS origins",
        env="HACS_ALLOWED_ORIGINS"
    )

    allowed_hosts: list[str] = Field(
        default_factory=list,
        description="Allowed host headers",
        env="HACS_ALLOWED_HOSTS"
    )

    rate_limit_per_minute: int = Field(
        default=60,
        description="Rate limit per minute per IP",
        env="HACS_RATE_LIMIT_PER_MINUTE"
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
    def computed_mcp_server_url(self) -> str:
        """Get the complete MCP server URL."""
        if self.mcp_server_url:
            return self.mcp_server_url
        return f"http://{self.mcp_server_host}:{self.mcp_server_port}"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"

    def _load_secret_from_file(self, file_path: str | None) -> str | None:
        """Load secret from file if it exists."""
        if not file_path:
            return None
        try:
            import os
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read().strip()
        except Exception:
            pass
        return None

    def _load_api_keys_from_file(self, file_path: str | None) -> list[str]:
        """Load API keys from file (one per line)."""
        if not file_path:
            return []
        try:
            import os
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return [line.strip() for line in f if line.strip()]
        except Exception:
            pass
        return []

    def get_effective_api_keys(self) -> list[str]:
        """Get effective API keys with precedence order."""
        # 1. Explicit env var
        if self.api_keys:
            return self.api_keys
        
        # 2. File-based
        file_keys = self._load_api_keys_from_file(self.api_keys_file)
        if file_keys:
            return file_keys
        
        # 3. Backward-compatible single key via HACS_API_KEY (singular)
        try:
            import os as _os
            single_key = _os.getenv("HACS_API_KEY")
            if single_key and single_key.strip():
                return [single_key.strip()]
        except Exception:
            pass

        # 4. Development fallback
        if self.dev_mode and self.is_development:
            import secrets
            return [f"dev-{secrets.token_urlsafe(16)}"]
        
        return []

    def get_effective_openai_api_key(self) -> str | None:
        """Get OpenAI API key with file fallback."""
        import os
        
        # 1. Explicit env var
        if self.openai_api_key:
            return self.openai_api_key
        
        # 2. File-based
        return self._load_secret_from_file(os.getenv("OPENAI_API_KEY_FILE"))

    def get_effective_anthropic_api_key(self) -> str | None:
        """Get Anthropic API key with file fallback."""
        import os
        
        # 1. Explicit env var
        if self.anthropic_api_key:
            return self.anthropic_api_key
        
        # 2. File-based
        return self._load_secret_from_file(os.getenv("ANTHROPIC_API_KEY_FILE"))

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

    # Pydantic v2 BaseSettings configuration
    model_config = SettingsConfigDict(
        env_prefix="HACS_",
        case_sensitive=False,
    )

    @field_validator("log_level", mode="before")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        if isinstance(v, str):
            return LogLevel(v.upper())
        return v

    @field_validator("api_keys", mode="before")
    @classmethod
    def validate_api_keys(cls, v):
        """Parse comma-separated API keys."""
        if isinstance(v, str):
            return [key.strip() for key in v.split(",") if key.strip()]
        return v or []

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def validate_allowed_origins(cls, v):
        """Parse comma-separated allowed origins."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v or []

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def validate_allowed_hosts(cls, v):
        """Parse comma-separated allowed hosts."""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",") if host.strip()]
        return v or []

    @field_validator("environment", mode="before")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment value."""
        if isinstance(v, str):
            env = v.lower()
            if env not in ["development", "staging", "production"]:
                raise ValueError("Environment must be one of: development, staging, production")
            return env
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
