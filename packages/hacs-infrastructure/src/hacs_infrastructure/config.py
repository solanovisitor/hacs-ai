"""
Configuration Management for HACS Infrastructure

This module provides comprehensive configuration management with environment
variable support, validation, and healthcare-specific settings.
"""

import os
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

# Fallback for environments without pydantic-settings
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    # Create a simple BaseSettings fallback
    class BaseSettings(BaseModel):
        class Config:
            env_prefix = ""
            case_sensitive = False
    
    def SettingsConfigDict(**kwargs):
        return kwargs


class LogLevel(str, Enum):
    """Logging levels."""
    
    DEBUG = "DEBUG"
    INFO = "INFO" 
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Environment(str, Enum):
    """Deployment environments."""
    
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class SecurityLevel(str, Enum):
    """Security levels for healthcare compliance."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DatabaseConfig(BaseModel):
    """Database configuration settings."""
    
    url: Optional[str] = Field(None, description="Database connection URL")
    host: str = Field("localhost", description="Database host")
    port: int = Field(5432, description="Database port")
    name: str = Field("hacs", description="Database name")
    user: Optional[str] = Field(None, description="Database user")
    password: Optional[str] = Field(None, description="Database password")
    schema: str = Field("public", description="Database schema")
    pool_size: int = Field(10, description="Connection pool size")
    max_overflow: int = Field(20, description="Maximum pool overflow")
    pool_timeout: int = Field(30, description="Pool connection timeout")
    
    @property
    def connection_url(self) -> str:
        """Get complete database connection URL."""
        if self.url:
            return self.url
        
        auth = ""
        if self.user:
            auth = self.user
            if self.password:
                auth += f":{self.password}"
            auth += "@"
        
        return f"postgresql://{auth}{self.host}:{self.port}/{self.name}"


class CacheConfig(BaseModel):
    """Cache configuration settings."""
    
    enabled: bool = Field(True, description="Enable caching")
    backend: str = Field("memory", description="Cache backend (memory, redis)")
    ttl: int = Field(3600, description="Default TTL in seconds")
    max_size: int = Field(1000, description="Maximum cache size")
    
    # Redis-specific settings
    redis_url: Optional[str] = Field(None, description="Redis connection URL")
    redis_host: str = Field("localhost", description="Redis host")
    redis_port: int = Field(6379, description="Redis port")
    redis_db: int = Field(0, description="Redis database number")
    redis_password: Optional[str] = Field(None, description="Redis password")


class LLMConfig(BaseModel):
    """LLM provider configuration."""
    
    provider: str = Field("openai", description="LLM provider (openai, anthropic)")
    model: str = Field("gpt-4", description="Default model")
    api_key: Optional[str] = Field(None, description="API key")
    base_url: Optional[str] = Field(None, description="Base URL")
    timeout: float = Field(30.0, description="Request timeout")
    max_retries: int = Field(3, description="Maximum retries")
    temperature: float = Field(0.7, description="Default temperature")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens")


class VectorStoreConfig(BaseModel):
    """Vector store configuration."""
    
    provider: str = Field("qdrant", description="Vector store provider")
    host: str = Field("localhost", description="Vector store host")
    port: int = Field(6333, description="Vector store port")
    api_key: Optional[str] = Field(None, description="API key")
    collection_name: str = Field("hacs_vectors", description="Collection name")
    dimension: int = Field(1536, description="Vector dimension")
    distance_metric: str = Field("cosine", description="Distance metric")


class HealthCheckConfig(BaseModel):
    """Health check configuration."""
    
    enabled: bool = Field(True, description="Enable health checks")
    interval: int = Field(30, description="Health check interval in seconds")
    timeout: float = Field(5.0, description="Health check timeout")
    failure_threshold: int = Field(3, description="Failure threshold")
    success_threshold: int = Field(1, description="Success threshold")


class ObservabilityConfig(BaseModel):
    """Observability and monitoring configuration."""
    
    metrics_enabled: bool = Field(True, description="Enable metrics collection")
    tracing_enabled: bool = Field(False, description="Enable distributed tracing")
    logging_level: LogLevel = Field(LogLevel.INFO, description="Logging level")
    
    # Prometheus metrics
    prometheus_enabled: bool = Field(False, description="Enable Prometheus metrics")
    prometheus_port: int = Field(9090, description="Prometheus metrics port")
    
    # OpenTelemetry
    otel_endpoint: Optional[str] = Field(None, description="OpenTelemetry endpoint")
    otel_service_name: str = Field("hacs", description="Service name for tracing")


class SecurityConfig(BaseModel):
    """Security configuration settings."""
    
    level: SecurityLevel = Field(SecurityLevel.MEDIUM, description="Security level")
    
    # JWT settings
    jwt_secret: str = Field(..., description="JWT secret key")
    jwt_algorithm: str = Field("HS256", description="JWT algorithm")
    jwt_expiration: int = Field(3600, description="JWT expiration in seconds")
    
    # Session settings
    session_timeout: int = Field(28800, description="Session timeout in seconds (8 hours)")
    max_sessions_per_user: int = Field(5, description="Maximum sessions per user")
    
    # Rate limiting
    rate_limit_enabled: bool = Field(True, description="Enable rate limiting")
    rate_limit_requests: int = Field(100, description="Requests per minute")
    
    # CORS settings
    cors_enabled: bool = Field(True, description="Enable CORS")
    cors_origins: List[str] = Field(default_factory=list, description="Allowed CORS origins")
    
    # HIPAA compliance
    hipaa_compliant: bool = Field(True, description="Enable HIPAA compliance features")
    audit_all_access: bool = Field(True, description="Audit all data access")
    encrypt_at_rest: bool = Field(True, description="Encrypt data at rest")


class HACSConfig(BaseSettings):
    """
    Comprehensive HACS configuration with healthcare-specific settings.
    
    All settings can be configured via environment variables with the HACS_ prefix.
    """
    
    model_config = SettingsConfigDict(
        env_prefix="HACS_",
        case_sensitive=False,
        validate_assignment=True,
        extra="forbid"
    )
    
    # Core settings
    environment: Environment = Field(Environment.DEVELOPMENT, description="Deployment environment")
    debug: bool = Field(False, description="Enable debug mode")
    version: str = Field("0.1.0", description="Application version")
    
    # Service settings
    host: str = Field("localhost", description="Service host")
    port: int = Field(8000, description="Service port")
    workers: int = Field(1, description="Number of worker processes")
    
    # Component configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig, description="Database configuration")
    cache: CacheConfig = Field(default_factory=CacheConfig, description="Cache configuration")
    llm: LLMConfig = Field(default_factory=LLMConfig, description="LLM configuration")
    vector_store: VectorStoreConfig = Field(default_factory=VectorStoreConfig, description="Vector store configuration")
    health_check: HealthCheckConfig = Field(default_factory=HealthCheckConfig, description="Health check configuration")
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig, description="Observability configuration")
    security: SecurityConfig = Field(default_factory=lambda: SecurityConfig(jwt_secret=os.urandom(32).hex()), description="Security configuration")
    
    # Healthcare-specific settings
    fhir_version: str = Field("R4", description="FHIR version")
    organization_name: str = Field("HACS Healthcare", description="Organization name")
    organization_id: Optional[str] = Field(None, description="Organization identifier")
    
    # Default permissions
    default_actor_permissions: List[str] = Field(
        default_factory=lambda: [
            "read:patient", "read:observation", "read:encounter",
            "write:memory", "read:workflow", "execute:workflow"
        ],
        description="Default permissions for new actors"
    )
    
    # Integration settings
    mcp_server_enabled: bool = Field(True, description="Enable MCP server")
    mcp_server_url: str = Field("http://localhost:8000", description="MCP server URL")
    
    langgraph_enabled: bool = Field(False, description="Enable LangGraph integration")
    langgraph_url: str = Field("http://localhost:8001", description="LangGraph server URL")
    
    @field_validator("environment", mode="before")
    @classmethod
    def validate_environment(cls, v: Any) -> Environment:
        """Validate environment setting."""
        if isinstance(v, str):
            return Environment(v.lower())
        return v
    
    @field_validator("security")
    @classmethod
    def validate_security_config(cls, v: Any) -> SecurityConfig:
        """Validate security configuration."""
        if isinstance(v, dict):
            # Ensure JWT secret is provided
            if "jwt_secret" not in v:
                v["jwt_secret"] = os.urandom(32).hex()
            return SecurityConfig(**v)
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == Environment.PRODUCTION
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == Environment.DEVELOPMENT
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment == Environment.TESTING
    
    @property 
    def service_url(self) -> str:
        """Get complete service URL."""
        protocol = "https" if self.is_production else "http"
        return f"{protocol}://{self.host}:{self.port}"
    
    def get_database_url(self) -> str:
        """Get database connection URL."""
        return self.database.connection_url
    
    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache configuration as dictionary."""
        return self.cache.model_dump()
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration as dictionary."""
        return self.security.model_dump()
    
    def validate_production_settings(self) -> List[str]:
        """
        Validate settings for production deployment.
        
        Returns:
            List of validation errors
        """
        errors = []
        
        if self.is_production:
            # Check critical production settings
            if self.debug:
                errors.append("Debug mode should be disabled in production")
            
            if self.security.jwt_secret == "dev-secret":
                errors.append("JWT secret must be changed from default in production")
            
            if not self.security.hipaa_compliant:
                errors.append("HIPAA compliance should be enabled in production")
            
            if not self.database.url and not all([self.database.host, self.database.user, self.database.password]):
                errors.append("Database connection must be properly configured in production")
            
            if self.security.level == SecurityLevel.LOW:
                errors.append("Security level should be MEDIUM or higher in production")
        
        return errors


class ConfigurationError(Exception):
    """Configuration-related errors."""
    pass


# Global configuration instance
_global_config: Optional[HACSConfig] = None


def get_config() -> HACSConfig:
    """
    Get the global configuration instance.
    
    Returns:
        Global configuration instance
    """
    global _global_config
    if _global_config is None:
        try:
            _global_config = HACSConfig()
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}") from e
    return _global_config


def set_config(config: HACSConfig) -> None:
    """
    Set the global configuration instance.
    
    Args:
        config: Configuration instance to set as global
    """
    global _global_config
    _global_config = config


def reset_config() -> None:
    """Reset the global configuration instance."""
    global _global_config
    _global_config = None


def configure_hacs(**kwargs: Any) -> HACSConfig:
    """
    Configure HACS with explicit settings.
    
    Args:
        **kwargs: Configuration values to override
        
    Returns:
        The configured settings instance
    """
    global _global_config
    try:
        _global_config = HACSConfig(**kwargs)
    except Exception as e:
        raise ConfigurationError(f"Failed to configure HACS: {e}") from e
    return _global_config


def load_config_from_file(file_path: str) -> HACSConfig:
    """
    Load configuration from file.
    
    Args:
        file_path: Path to configuration file (JSON, YAML, or TOML)
        
    Returns:
        Loaded configuration instance
    """
    import json
    from pathlib import Path
    
    config_file = Path(file_path)
    if not config_file.exists():
        raise ConfigurationError(f"Configuration file not found: {file_path}")
    
    try:
        if config_file.suffix.lower() == '.json':
            with open(config_file, 'r') as f:
                data = json.load(f)
        elif config_file.suffix.lower() in ['.yml', '.yaml']:
            import yaml
            with open(config_file, 'r') as f:
                data = yaml.safe_load(f)
        elif config_file.suffix.lower() == '.toml':
            import tomllib
            with open(config_file, 'rb') as f:
                data = tomllib.load(f)
        else:
            raise ConfigurationError(f"Unsupported configuration file format: {config_file.suffix}")
        
        global _global_config
        _global_config = HACSConfig(**data)
        return _global_config
        
    except Exception as e:
        raise ConfigurationError(f"Failed to load configuration from {file_path}: {e}") from e


def validate_config() -> None:
    """
    Validate current configuration.
    
    Raises:
        ConfigurationError: If configuration is invalid
    """
    config = get_config()
    
    # Validate production settings if in production
    if config.is_production:
        errors = config.validate_production_settings()
        if errors:
            raise ConfigurationError(f"Production configuration errors: {'; '.join(errors)}")
    
    # Additional validation logic can be added here
    pass