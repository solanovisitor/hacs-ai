"""
Persistence Infrastructure Following SOLID Principles

This module implements the Repository pattern with pluggable persistence
adapters, following SOLID principles and dependency inversion.

SOLID Compliance:
- S: Single Responsibility - Each repository manages one aggregate type
- O: Open/Closed - New persistence mechanisms via adapter pattern
- L: Liskov Substitution - All repositories implement same interface
- I: Interface Segregation - Focused repository interfaces
- D: Dependency Inversion - Repositories depend on adapter abstractions

Repository Pattern:
    📋 Aggregate Repositories - Domain-specific data access
    🔧 Persistence Adapters - Storage mechanism implementations
    🏭 Repository Factory - Creates configured repositories
    🔄 Unit of Work - Transaction management

Supported Persistence:
    💾 Memory - In-memory storage (development/testing)
    📁 File - JSON/YAML file storage (simple persistence)
    🗄️ Database - SQL/NoSQL database storage (production)
"""

from .repositories import (
    InMemoryResourceRepository,
    InMemoryAgentRepository,
    InMemoryIAMRepository,
    InMemoryToolRepository,
)

from .adapters import (
    MemoryAdapter,
    FileAdapter,
    DatabaseAdapter,
    PersistenceAdapter,
)

from .factory import (
    PersistenceFactory,
    PersistenceManager,
    create_memory_persistence,
    create_file_persistence,
    create_database_persistence,
)

from .unit_of_work import (
    InMemoryUnitOfWork,
    UnitOfWorkManager,
)

__all__ = [
    # Repository implementations
    "InMemoryResourceRepository",
    "InMemoryAgentRepository",
    "InMemoryIAMRepository", 
    "InMemoryToolRepository",
    
    # Persistence adapters
    "MemoryAdapter",
    "FileAdapter",
    "DatabaseAdapter",
    "PersistenceAdapter",
    
    # Factory and configuration
    "RepositoryFactory",
    "RepositoryConfiguration",
    
    # Unit of Work
    "InMemoryUnitOfWork",
    "UnitOfWorkManager",
]