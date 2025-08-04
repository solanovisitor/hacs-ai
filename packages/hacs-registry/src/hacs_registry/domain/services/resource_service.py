"""
Resource Domain Services Following SOLID Principles

This module implements domain services for resource management,
providing business logic that spans multiple aggregates or requires
external dependencies.

SOLID Compliance:
- S: Single Responsibility - Each service handles one business area
- O: Open/Closed - Extensible through service composition
- L: Liskov Substitution - All services implement service contracts
- I: Interface Segregation - Focused service interfaces  
- D: Dependency Inversion - Services depend on repository abstractions
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from ...core.base import EntityId, Repository, DomainService
from ...core.events import EventBus, ResourceEvent
from ...core.exceptions import ResourceException, ValidationException
from ..models.resource import (
    ResourceAggregate, ResourceStatus, ResourceMetadata, ResourceVersion,
    ResourceCategory, ResourceTag
)

logger = logging.getLogger(__name__)


class IResourceService(DomainService):
    """
    Interface for resource services.
    
    SOLID Compliance:
    - I: Interface segregation - minimal service contract
    - D: Dependency inversion - abstraction for all implementations
    """
    
    @abstractmethod
    async def register_resource(
        self,
        metadata: ResourceMetadata,
        hacs_resource_class: str,
        instance_data: Optional[Dict[str, Any]] = None,
        actor_id: Optional[str] = None
    ) -> ResourceAggregate:
        """Register a new resource."""
        pass
    
    @abstractmethod
    async def update_resource(
        self,
        resource_id: EntityId,
        updates: Dict[str, Any],
        actor_id: Optional[str] = None
    ) -> ResourceAggregate:
        """Update an existing resource."""
        pass
    
    @abstractmethod
    async def validate_resource(
        self,
        resource_id: EntityId
    ) -> List[str]:
        """Validate a resource and return errors."""
        pass


class ResourceService(IResourceService):
    """
    Core resource management service.
    
    SOLID Compliance:
    - S: Single responsibility - manages resource business logic
    - O: Open/closed - extensible through service composition
    - D: Dependency inversion - depends on repository abstraction
    """
    
    def __init__(
        self,
        resource_repository: Repository,
        event_bus: Optional[EventBus] = None,
        validation_service: Optional['ResourceValidationService'] = None,
        lifecycle_service: Optional['ResourceLifecycleService'] = None
    ):
        self.resource_repository = resource_repository
        self.event_bus = event_bus
        self.validation_service = validation_service
        self.lifecycle_service = lifecycle_service
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def register_resource(
        self,
        metadata: ResourceMetadata,
        hacs_resource_class: str,
        instance_data: Optional[Dict[str, Any]] = None,
        actor_id: Optional[str] = None
    ) -> ResourceAggregate:
        """Register a new resource."""
        try:
            # Generate unique ID
            resource_id = EntityId.generate()
            
            # Create resource aggregate
            resource = ResourceAggregate(
                id=resource_id,
                metadata=metadata,
                hacs_resource_class=hacs_resource_class,
                instance_data=instance_data or {},
                status=ResourceStatus.DRAFT
            )
            
            # Validate if validation service is available
            if self.validation_service:
                validation_errors = await self.validation_service.validate_resource_creation(
                    resource, actor_id
                )
                if validation_errors:
                    raise ValidationException(f"Resource validation failed: {validation_errors}")
            
            # Save through repository
            saved_resource = await self.resource_repository.save(resource)
            
            # Publish events if event bus is available
            if self.event_bus:
                events = resource.get_domain_events()
                for event in events:
                    await self.event_bus.publish(event)
                resource.clear_domain_events()
            
            self.logger.info(f"Resource registered: {resource_id} ({hacs_resource_class})")
            return saved_resource
            
        except Exception as e:
            self.logger.error(f"Failed to register resource: {e}")
            raise ResourceException(f"Resource registration failed: {e}")
    
    async def update_resource(
        self,
        resource_id: EntityId,
        updates: Dict[str, Any],
        actor_id: Optional[str] = None
    ) -> ResourceAggregate:
        """Update an existing resource."""
        try:
            # Load existing resource
            resource = await self.resource_repository.find_by_id(resource_id)
            if not resource:
                raise ResourceException(f"Resource not found: {resource_id}")
            
            # Apply updates
            if 'metadata' in updates:
                resource.update_metadata(updates['metadata'])
            
            if 'instance_data' in updates:
                resource.update_instance_data(updates['instance_data'])
            
            if 'status' in updates:
                # Use lifecycle service if available
                if self.lifecycle_service:
                    await self.lifecycle_service.change_status(
                        resource, updates['status'], actor_id
                    )
                else:
                    resource.change_status(updates['status'])
            
            # Validate if validation service is available
            if self.validation_service:
                validation_errors = await self.validation_service.validate_resource_update(
                    resource, updates, actor_id
                )
                if validation_errors:
                    raise ValidationException(f"Resource update validation failed: {validation_errors}")
            
            # Save updated resource
            saved_resource = await self.resource_repository.save(resource)
            
            # Publish events
            if self.event_bus:
                events = resource.get_domain_events()
                for event in events:
                    await self.event_bus.publish(event)
                resource.clear_domain_events()
            
            self.logger.info(f"Resource updated: {resource_id}")
            return saved_resource
            
        except Exception as e:
            self.logger.error(f"Failed to update resource {resource_id}: {e}")
            raise ResourceException(f"Resource update failed: {e}")
    
    async def validate_resource(self, resource_id: EntityId) -> List[str]:
        """Validate a resource and return errors."""
        try:
            resource = await self.resource_repository.find_by_id(resource_id)
            if not resource:
                return [f"Resource not found: {resource_id}"]
            
            if self.validation_service:
                return await self.validation_service.validate_resource_state(resource)
            else:
                # Basic validation
                return resource.validation_errors
                
        except Exception as e:
            self.logger.error(f"Failed to validate resource {resource_id}: {e}")
            return [f"Validation error: {e}"]
    
    async def find_resources_by_category(self, category: ResourceCategory) -> List[ResourceAggregate]:
        """Find resources by category."""
        try:
            resources = await self.resource_repository.find_by_criteria(
                {"category": category.value}
            )
            return resources
        except Exception as e:
            self.logger.error(f"Failed to find resources by category {category}: {e}")
            return []
    
    async def find_resources_by_status(self, status: ResourceStatus) -> List[ResourceAggregate]:
        """Find resources by status."""
        try:
            resources = await self.resource_repository.find_by_criteria(
                {"status": status.value}
            )
            return resources
        except Exception as e:
            self.logger.error(f"Failed to find resources by status {status}: {e}")
            return []


class ResourceValidationService:
    """
    Service for comprehensive resource validation.
    
    SOLID Compliance:
    - S: Single responsibility - handles resource validation logic
    - O: Open/closed - extensible through validation rule registration
    """
    
    def __init__(self):
        self.validation_rules = {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def validate_resource_creation(
        self,
        resource: ResourceAggregate,
        actor_id: Optional[str] = None
    ) -> List[str]:
        """Validate resource creation."""
        errors = []
        
        # Basic metadata validation
        if not resource.metadata.name.strip():
            errors.append("Resource name cannot be empty")
        
        if not resource.metadata.description.strip():
            errors.append("Resource description cannot be empty")
        
        # Version validation
        if resource.metadata.version.major == 0:
            errors.append("Resource version must have major version > 0 for production")
        
        # HACS resource class validation
        if not resource.hacs_resource_class:
            errors.append("HACS resource class must be specified")
        
        # Category-specific validation
        category_errors = await self._validate_by_category(resource)
        errors.extend(category_errors)
        
        return errors
    
    async def validate_resource_update(
        self,
        resource: ResourceAggregate,
        updates: Dict[str, Any],
        actor_id: Optional[str] = None
    ) -> List[str]:
        """Validate resource updates."""
        errors = []
        
        # Status transition validation
        if 'status' in updates:
            if not resource._is_valid_status_transition(resource.status, updates['status']):
                errors.append(f"Invalid status transition from {resource.status} to {updates['status']}")
        
        # Metadata update validation
        if 'metadata' in updates:
            metadata = updates['metadata']
            if hasattr(metadata, 'name') and metadata.name != resource.metadata.name:
                errors.append("Cannot change resource name after creation")
        
        return errors
    
    async def validate_resource_state(self, resource: ResourceAggregate) -> List[str]:
        """Validate current resource state."""
        errors = []
        
        # Basic state validation
        if not resource.is_valid():
            errors.extend(resource.validation_errors)
        
        # Status-specific validation
        if resource.status == ResourceStatus.PUBLISHED:
            if resource.metadata.version.major == 0:
                errors.append("Published resources must have major version >= 1")
        
        return errors
    
    async def _validate_by_category(self, resource: ResourceAggregate) -> List[str]:
        """Validate resource based on its category."""
        errors = []
        category = resource.metadata.category
        
        if category == ResourceCategory.CLINICAL:
            # Clinical resources need specific validation
            if not any('clinical' in tag.name for tag in resource.metadata.tags):
                errors.append("Clinical resources should have clinical tags")
        
        elif category == ResourceCategory.WORKFLOW:
            # Workflow resources need specific validation
            if 'steps' not in resource.instance_data:
                errors.append("Workflow resources must define steps")
        
        return errors


class ResourceLifecycleService:
    """
    Service for managing resource lifecycle transitions.
    
    SOLID Compliance:
    - S: Single responsibility - manages resource lifecycle
    - O: Open/closed - extensible for new lifecycle rules
    """
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus
        self.lifecycle_rules = {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def change_status(
        self,
        resource: ResourceAggregate,
        new_status: ResourceStatus,
        actor_id: Optional[str] = None
    ) -> None:
        """Change resource status with business rules."""
        old_status = resource.status
        
        # Check transition rules
        if not self._is_allowed_transition(old_status, new_status, resource):
            raise ResourceException(
                f"Status transition not allowed: {old_status} -> {new_status}"
            )
        
        # Apply status change
        resource.change_status(new_status, f"Changed by {actor_id or 'system'}")
        
        # Apply lifecycle rules
        await self._apply_lifecycle_rules(resource, old_status, new_status)
        
        self.logger.info(f"Resource {resource.id} status changed: {old_status} -> {new_status}")
    
    def _is_allowed_transition(
        self,
        from_status: ResourceStatus,
        to_status: ResourceStatus,
        resource: ResourceAggregate
    ) -> bool:
        """Check if status transition is allowed."""
        # Default transitions - could be made configurable
        allowed_transitions = {
            ResourceStatus.DRAFT: [ResourceStatus.REVIEW, ResourceStatus.SUSPENDED],
            ResourceStatus.REVIEW: [ResourceStatus.APPROVED, ResourceStatus.DRAFT],
            ResourceStatus.APPROVED: [ResourceStatus.PUBLISHED, ResourceStatus.REVIEW],
            ResourceStatus.PUBLISHED: [ResourceStatus.DEPRECATED, ResourceStatus.SUSPENDED],
            ResourceStatus.DEPRECATED: [ResourceStatus.RETIRED],
            ResourceStatus.SUSPENDED: [ResourceStatus.DRAFT, ResourceStatus.REVIEW, ResourceStatus.PUBLISHED],
            ResourceStatus.RETIRED: []  # No transitions from retired
        }
        
        return to_status in allowed_transitions.get(from_status, [])
    
    async def _apply_lifecycle_rules(
        self,
        resource: ResourceAggregate,
        old_status: ResourceStatus,
        new_status: ResourceStatus
    ) -> None:
        """Apply business rules for lifecycle transitions."""
        
        # Publishing rules
        if new_status == ResourceStatus.PUBLISHED:
            # Ensure resource is ready for publication
            if not resource.can_be_published():
                raise ResourceException("Resource is not ready for publication")
        
        # Retirement rules
        if new_status == ResourceStatus.RETIRED:
            # Clear sensitive data, archive, etc.
            pass
        
        # Suspension rules
        if new_status == ResourceStatus.SUSPENDED:
            # Log suspension reason, notify stakeholders, etc.
            pass