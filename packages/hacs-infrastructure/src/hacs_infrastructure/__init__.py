"""
HACS Infrastructure - Core Infrastructure Components

This package provides the foundational infrastructure for healthcare AI systems,
including dependency injection, configuration management, service discovery,
and lifecycle management.

Design Philosophy:
    - Dependency injection over global state
    - Type-safe configuration management
    - Healthcare-compliant service architecture
    - Production-ready infrastructure patterns
    - AI agent-optimized service discovery

Key Features:
    - Comprehensive dependency injection container
    - Environment-based configuration with validation
    - Service registry and discovery
    - Health checking and monitoring
    - Lifecycle management for services
    - Event-driven architecture support

Author: HACS Development Team
License: MIT
Version: 0.1.0
"""

# Core infrastructure components
from .container import (
    Container, 
    Injectable, 
    Singleton, 
    Scoped,
    ServiceError,
    DependencyError,
    get_container,
    reset_container
)
from .config import (
    HACSConfig,
    ConfigurationError,
    get_config,
    reset_config,
    configure_hacs
)
from .service_registry import (
    ServiceRegistry,
    ServiceInfo,
    ServiceStatus,
    HealthCheck,
    ServiceDiscovery
)
from .lifecycle import (
    ServiceLifecycle,
    LifecycleState,
    StartupManager,
    ShutdownManager,
    GracefulShutdown
)
from .protocols import (
    Configurable,
    HealthCheckable,
    Startable,
    Stoppable,
    Injectable as InjectableProtocol
)

# Event system
from .events import (
    EventBus,
    Event,
    EventHandler,
    EventSubscription,
    EventError
)

# Monitoring and observability
from .monitoring import (
    HealthMonitor,
    MetricsCollector,
    ServiceMetrics,
    PerformanceMonitor
)

# Version info
__version__ = "0.1.0"
__author__ = "HACS Development Team"
__license__ = "MIT"

# Public API
__all__ = [
    # Core container
    "Container",
    "Injectable", 
    "Singleton",
    "Scoped",
    "ServiceError",
    "DependencyError",
    "get_container",
    "reset_container",
    
    # Configuration
    "HACSConfig",
    "ConfigurationError",
    "get_config",
    "reset_config", 
    "configure_hacs",
    
    # Service registry
    "ServiceRegistry",
    "ServiceInfo",
    "ServiceStatus",
    "HealthCheck",
    "ServiceDiscovery",
    
    # Lifecycle management
    "ServiceLifecycle",
    "LifecycleState",
    "StartupManager",
    "ShutdownManager",
    "GracefulShutdown",
    
    # Protocols
    "Configurable",
    "HealthCheckable", 
    "Startable",
    "Stoppable",
    "InjectableProtocol",
    
    # Event system
    "EventBus",
    "Event",
    "EventHandler",
    "EventSubscription", 
    "EventError",
    
    # Monitoring
    "HealthMonitor",
    "MetricsCollector",
    "ServiceMetrics", 
    "PerformanceMonitor",
]

# Package metadata
PACKAGE_INFO = {
    "name": "hacs-infrastructure",
    "version": __version__,
    "description": "Infrastructure components for healthcare AI systems",
    "author": __author__,
    "license": __license__,
    "python_requires": ">=3.11",
    "dependencies": ["pydantic>=2.11.7", "pydantic-settings>=2.7.0", "hacs-models>=0.1.0", "hacs-auth>=0.1.0"],
    "optional_dependencies": {
        "redis": ["redis>=5.2.0"],
        "async": ["asyncio-mqtt>=0.14.0", "aiofiles>=24.1.0"],
        "monitoring": ["prometheus-client>=0.21.0", "structlog>=24.4.0"]
    },
    "homepage": "https://github.com/your-org/hacs",
    "documentation": "https://hacs.readthedocs.io/",
    "repository": "https://github.com/your-org/hacs",
}


def get_infrastructure_components() -> dict[str, type]:
    """
    Get registry of all available infrastructure components.
    
    Returns:
        Dictionary mapping component names to component classes
        
    Example:
        >>> components = get_infrastructure_components()
        >>> container = components["Container"]()
    """
    return {
        "Container": Container,
        "ServiceRegistry": ServiceRegistry,
        "ServiceLifecycle": ServiceLifecycle,
        "EventBus": EventBus,
        "HealthMonitor": HealthMonitor,
        "MetricsCollector": MetricsCollector,
    }


def validate_infrastructure_setup() -> bool:
    """
    Validate that infrastructure components are properly configured.
    
    Returns:
        True if all components pass validation checks
        
    Raises:
        ValueError: If configuration issues are found
    """
    try:
        # Test configuration loading
        config = get_config()
        if not hasattr(config, 'debug'):
            raise ValueError("Configuration not properly loaded")
        
        # Test container creation
        container = Container()
        
        # Test service registry
        service_registry = ServiceRegistry()
        
        # Test basic dependency injection
        @Injectable
        class TestService:
            def __init__(self):
                self.name = "test"
        
        container.register(TestService)
        test_service = container.get(TestService)
        
        if test_service.name != "test":
            raise ValueError("Dependency injection not working")
        
        return True
        
    except Exception as e:
        raise ValueError(f"Infrastructure setup validation failed: {e}") from e


def get_feature_info() -> dict[str, str]:
    """
    Get information about infrastructure features and capabilities.
    
    Returns:
        Dictionary with feature information
    """
    return {
        "dependency_injection": "✅ Type-safe dependency injection container",
        "configuration": "✅ Environment-based configuration with validation",
        "service_registry": "✅ Service discovery and health monitoring",
        "lifecycle_management": "✅ Graceful startup and shutdown orchestration",
        "event_system": "✅ Event-driven architecture with pub/sub",
        "monitoring": "✅ Health checks and performance metrics",
        "async_support": "✅ Asyncio and async context management",
        "healthcare_optimized": "✅ Healthcare AI system integration patterns",
        "production_ready": "✅ Enterprise infrastructure standards",
    }