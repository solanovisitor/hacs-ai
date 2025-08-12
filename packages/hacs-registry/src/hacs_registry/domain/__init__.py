"""
HACS Registry Domain Layer

This module implements the domain layer following Domain-Driven Design (DDD) 
principles and SOLID design patterns.

Domain Layer Structure:
    📋 Models - Domain entities, value objects, and aggregates
    🏥 Services - Domain services for complex business logic
    📏 Specifications - Business rules and domain constraints

SOLID Compliance:
- S: Single Responsibility - Each model represents one domain concept
- O: Open/Closed - Extensible through inheritance and composition
- L: Liskov Substitution - All domain objects follow contracts
- I: Interface Segregation - Focused domain interfaces
- D: Dependency Inversion - Domain depends on abstractions

Domain Concepts:
    🏥 Resource Domain - Healthcare resource management
    🤖 Agent Domain - AI agent lifecycle and configuration
    🔐 IAM Domain - Identity and access management
    🔧 Tool Domain - Tool registration and execution
"""

from .models import (
    # Resource domain (implemented)
    ResourceAggregate,
    ResourceMetadata,
    ResourceVersion,
    ResourceTag,
    ResourceCategory,
    ResourceStatus,
)

from .services import (
    # Resource services (implemented)
    ResourceService,
    ResourceValidationService,
    ResourceLifecycleService,
)

__all__ = [
    # Resource Models
    "ResourceAggregate",
    "ResourceMetadata", 
    "ResourceVersion",
    "ResourceTag",
    "ResourceCategory",
    "ResourceStatus",
    
    # Resource Services
    "ResourceService",
    "ResourceValidationService",
    "ResourceLifecycleService",
]