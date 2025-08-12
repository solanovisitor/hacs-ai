"""
Domain Models Following SOLID Principles

This module contains all domain models (entities, value objects, aggregates)
that represent the core business concepts in the HACS Registry.

SOLID Compliance:
- S: Single Responsibility - Each model represents one business concept
- O: Open/Closed - Models are extensible through inheritance
- L: Liskov Substitution - All models follow their base contracts
- I: Interface Segregation - Focused model interfaces
- D: Dependency Inversion - Models depend on abstractions

Model Categories:
    🏥 Resource Models - Healthcare resource management
    🤖 Agent Models - AI agent lifecycle and configuration  
    🔐 IAM Models - Identity and access management
    🔧 Tool Models - Tool registration and execution
"""

from .resource import (
    ResourceAggregate,
    ResourceMetadata,
    ResourceVersion,
    ResourceTag,
    ResourceCategory,
    ResourceStatus,
)

# Note: Additional domain models (agent, iam, tool) would be implemented
# following the same SOLID patterns as ResourceAggregate

__all__ = [
    # Resource models
    "ResourceAggregate",
    "ResourceMetadata",
    "ResourceVersion",
    "ResourceTag",
    "ResourceCategory",
    "ResourceStatus",
]