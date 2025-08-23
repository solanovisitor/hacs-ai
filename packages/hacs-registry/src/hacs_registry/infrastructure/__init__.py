"""
HACS Registry Infrastructure Layer

This module implements the infrastructure layer following SOLID principles
and the Hexagonal Architecture pattern (Ports and Adapters).

SOLID Compliance:
- S: Single Responsibility - Each infrastructure component has one purpose
- O: Open/Closed - Extensible through adapters and implementations
- L: Liskov Substitution - All implementations are substitutable
- I: Interface Segregation - Focused infrastructure interfaces
- D: Dependency Inversion - Implementations depend on abstractions

Infrastructure Components:
    🔌 Integration - External service adapters
    📊 Monitoring - Audit, metrics, and compliance tracking

Note: Persistence layer has been moved to hacs-persistence package.
Registry now uses hacs-persistence via dependency injection for data storage.

Hexagonal Architecture:
    🔌 Ports (Interfaces) - Defined in hacs-core
    🔧 Adapters (Implementations) - Implemented in infrastructure layer
    🏗️ Configuration - Dependency injection and setup
"""

from .integration import (
    # Integration adapters
    LangChainAdapter,
    MCPAdapter,
    FrameworkAdapter,
)

from .monitoring import (
    # Monitoring components
    AuditLogger,
    MetricsCollector,
    ComplianceMonitor,
)

__all__ = [
    # Integration
    "LangChainAdapter",
    "MCPAdapter",
    "FrameworkAdapter",
    # Monitoring
    "AuditLogger",
    "MetricsCollector",
    "ComplianceMonitor",
]
