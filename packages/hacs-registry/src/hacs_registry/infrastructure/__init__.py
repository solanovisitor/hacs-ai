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
    💾 Persistence - Repository implementations and data adapters
    🔌 Integration - External service adapters
    📊 Monitoring - Audit, metrics, and compliance tracking

Hexagonal Architecture:
    🔌 Ports (Interfaces) - Defined in core layer
    🔧 Adapters (Implementations) - Implemented in infrastructure layer
    🏗️ Configuration - Dependency injection and setup
"""

from .persistence import (
    # Repository implementations
    InMemoryResourceRepository,
    InMemoryAgentRepository,
    InMemoryIAMRepository,
    InMemoryToolRepository,
    
    # Persistence adapters
    MemoryAdapter,
    FileAdapter,
    DatabaseAdapter,
    
    # Factory and management
    PersistenceFactory,
    PersistenceManager,
    
    # Unit of Work
    InMemoryUnitOfWork,
    UnitOfWorkManager,
)

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
    # Persistence
    "InMemoryResourceRepository",
    "InMemoryAgentRepository", 
    "InMemoryIAMRepository",
    "InMemoryToolRepository",
    "MemoryAdapter",
    "FileAdapter",
    "DatabaseAdapter",
    "RepositoryFactory",
    
    # Integration
    "LangChainAdapter",
    "MCPAdapter",
    "VectorStoreAdapter",
    "IntegrationFactory",
    
    # Monitoring
    "AuditLogger",
    "MetricsCollector",
    "ComplianceMonitor",
    "MonitoringFactory",
]