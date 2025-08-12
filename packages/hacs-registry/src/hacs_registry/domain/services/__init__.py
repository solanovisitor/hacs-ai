"""
Domain Services for HACS Registry Following SOLID Principles

This module provides domain services that implement business logic
that doesn't naturally fit within a single aggregate.

SOLID Compliance:
- S: Single Responsibility - Each service handles one business capability
- O: Open/Closed - Extensible through service composition
- L: Liskov Substitution - All services implement consistent contracts
- I: Interface Segregation - Focused service interfaces
- D: Dependency Inversion - Services depend on abstractions

Domain Services:
    📋 Resource Management - Resource lifecycle and validation
    🤖 Agent Configuration - Agent setup and coordination
    🔐 IAM Operations - Identity and access management
    🔧 Tool Registry - Tool discovery and integration
    📊 Validation Services - Cross-aggregate validation
    📈 Analytics Services - Usage and performance analytics
"""

from .resource_service import (
    ResourceService,
    ResourceValidationService,
    ResourceLifecycleService,
)

__all__ = [
    # Resource services (implemented)
    'ResourceService',
    'ResourceValidationService', 
    'ResourceLifecycleService',
]