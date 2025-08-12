"""
HACS Resource Registry

This module provides registration, versioning, and lifecycle management 
for hacs-core healthcare resources. It acts as a wrapper/facade around
hacs-core resources rather than redefining them.

Architecture:
    🏗️ hacs-core: Defines healthcare resources (Patient, Observation, etc.)
    📋 hacs-registry: Registers, versions, and manages those resources
    🔄 Pure wrapper pattern - no resource redefinition
"""

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union, get_type_hints
from dataclasses import dataclass, field

from pydantic import Field, BaseModel
from hacs_core import BaseResource

# Import all hacs-core resources that can be registered
from hacs_core.models import (
    # Clinical Resources
    Patient, Observation, Condition, Procedure, Medication, MedicationRequest,
    AllergyIntolerance, FamilyMemberHistory, Goal, RiskAssessment,
    
    # Workflow Resources  
    ActivityDefinition, PlanDefinition, Task, Appointment,
    
    # Communication Resources
    AgentMessage, Document, Library,
    
    # Administrative Resources
    Organization, Encounter,
    
    # Evidence and Guidance
    EvidenceVariable, GuidanceResponse,
    
    # Context and Memory
    ContextSummary, Memory, ResourceBundle
)

# Import workflow definitions from hacs-core (compatibility layer)
from hacs_core.models import (
    WorkflowDefinition, WorkflowRequest, WorkflowEvent, WorkflowExecution
)

logger = logging.getLogger(__name__)


class ResourceStatus(str, Enum):
    """Lifecycle status of a registered resource."""
    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class ResourceCategory(str, Enum):
    """Categories for organizing registered resources."""
    CLINICAL = "clinical"
    WORKFLOW = "workflow"
    ADMINISTRATIVE = "administrative"
    COMMUNICATION = "communication"
    EVIDENCE = "evidence"
    MEMORY = "memory"
    CUSTOM = "custom"


@dataclass
class ResourceMetadata:
    """Metadata for a registered resource."""
    name: str
    version: str
    description: str
    category: ResourceCategory
    status: ResourceStatus = ResourceStatus.DRAFT
    author: Optional[str] = None
    organization: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    use_cases: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    published_at: Optional[datetime] = None
    deprecated_at: Optional[datetime] = None


class RegisteredResource(BaseResource):
    """
    A wrapper around hacs-core resources that adds registry functionality.
    
    This doesn't redefine resources - it wraps them with versioning,
    lifecycle management, and metadata.
    """
    
    resource_type: str = Field(default="RegisteredResource", description="Registry wrapper type")
    
    # Registry metadata
    registry_id: str = Field(description="Unique registry identifier")
    metadata: ResourceMetadata = Field(description="Resource metadata")
    
    # Reference to the actual hacs-core resource
    resource_class: str = Field(description="Name of the hacs-core resource class")
    resource_instance: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Serialized instance of the hacs-core resource"
    )
    
    # Validation and schema information
    schema_version: str = Field(description="Schema version compatibility")
    validation_rules: List[str] = Field(
        default_factory=list,
        description="Additional validation rules"
    )
    
    # Lifecycle management
    lifecycle_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="History of status changes"
    )
    
    def update_status(self, new_status: ResourceStatus, reason: str = ""):
        """Update the resource status with history tracking."""
        old_status = self.metadata.status
        self.metadata.status = new_status
        self.metadata.updated_at = datetime.now(timezone.utc)
        
        if new_status == ResourceStatus.PUBLISHED:
            self.metadata.published_at = datetime.now(timezone.utc)
        elif new_status == ResourceStatus.DEPRECATED:
            self.metadata.deprecated_at = datetime.now(timezone.utc)
        
        # Record history
        self.lifecycle_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "from_status": old_status,
            "to_status": new_status,
            "reason": reason
        })
    
    def get_resource_class(self) -> Optional[Type[BaseResource]]:
        """Get the actual hacs-core resource class."""
        # Map resource class names to actual classes
        resource_map = {
            "Patient": Patient,
            "Observation": Observation,
            "Condition": Condition,
            "Procedure": Procedure,
            "Medication": Medication,
            "MedicationRequest": MedicationRequest,
            "AllergyIntolerance": AllergyIntolerance,
            "FamilyMemberHistory": FamilyMemberHistory,
            "Goal": Goal,
            "RiskAssessment": RiskAssessment,
            "ActivityDefinition": ActivityDefinition,
            "PlanDefinition": PlanDefinition,
            "Task": Task,
            "Appointment": Appointment,
            "AgentMessage": AgentMessage,
            "Document": Document,
            "Library": Library,
            "Organization": Organization,
            "Encounter": Encounter,
            "EvidenceVariable": EvidenceVariable,
            "GuidanceResponse": GuidanceResponse,
            "ContextSummary": ContextSummary,
            "Memory": Memory,
            "ResourceBundle": ResourceBundle,
            "WorkflowDefinition": WorkflowDefinition,
            "WorkflowRequest": WorkflowRequest,
            "WorkflowEvent": WorkflowEvent,
            "WorkflowExecution": WorkflowExecution,
        }
        
        return resource_map.get(self.resource_class)
    
    def instantiate_resource(self, **kwargs) -> Optional[BaseResource]:
        """Create an instance of the wrapped hacs-core resource."""
        resource_cls = self.get_resource_class()
        if resource_cls:
            # Merge stored instance data with provided kwargs
            instance_data = self.resource_instance or {}
            instance_data.update(kwargs)
            return resource_cls(**instance_data)
        return None


class HACSResourceRegistry:
    """
    Central registry for managing hacs-core resources.
    
    Provides registration, versioning, discovery, and lifecycle management
    without redefining any hacs-core resources.
    """
    
    def __init__(self):
        self._resources: Dict[str, RegisteredResource] = {}
        self._by_category: Dict[ResourceCategory, List[str]] = {
            category: [] for category in ResourceCategory
        }
        self._by_class: Dict[str, List[str]] = {}
    
    def register_resource(
        self,
        resource_class: Type[BaseResource],
        metadata: ResourceMetadata,
        instance_data: Optional[Dict[str, Any]] = None,
        actor_id: Optional[str] = None
    ) -> RegisteredResource:
        """
        Register a hacs-core resource with the registry.
        
        Args:
            resource_class: The hacs-core resource class to register
            metadata: Registry metadata for the resource
            instance_data: Optional default instance data
            actor_id: ID of actor registering the resource (for IAM)
            
        Returns:
            RegisteredResource wrapper
        """
        # IAM check for resource registration
        if actor_id:
            try:
                from .iam_registry import get_global_iam_registry, AccessLevel
                iam = get_global_iam_registry()
                if not iam.check_access(actor_id, f"resource_registry:{resource_class.__name__}", AccessLevel.WRITE):
                    raise PermissionError(f"Actor {actor_id} not authorized to register {resource_class.__name__}")
            except ImportError:
                # IAM not available, proceed without check
                pass
        registry_id = f"{resource_class.__name__.lower()}-{metadata.name.lower()}-{metadata.version}"
        
        registered = RegisteredResource(
            registry_id=registry_id,
            metadata=metadata,
            resource_class=resource_class.__name__,
            resource_instance=instance_data,
            schema_version="1.0.0"  # Could be derived from resource class
        )
        
        # Store in registry
        self._resources[registry_id] = registered
        
        # Index by category
        if registry_id not in self._by_category[metadata.category]:
            self._by_category[metadata.category].append(registry_id)
        
        # Index by resource class
        class_name = resource_class.__name__
        if class_name not in self._by_class:
            self._by_class[class_name] = []
        if registry_id not in self._by_class[class_name]:
            self._by_class[class_name].append(registry_id)
        
        logger.info(f"Registered resource: {registry_id}")
        return registered
    
    def get_resource(self, registry_id: str) -> Optional[RegisteredResource]:
        """Get a registered resource by ID."""
        return self._resources.get(registry_id)
    
    def list_resources(
        self,
        category: Optional[ResourceCategory] = None,
        resource_class: Optional[str] = None,
        status: Optional[ResourceStatus] = None
    ) -> List[RegisteredResource]:
        """List registered resources with optional filtering."""
        resources = []
        
        if category:
            resource_ids = self._by_category.get(category, [])
        elif resource_class:
            resource_ids = self._by_class.get(resource_class, [])
        else:
            resource_ids = list(self._resources.keys())
        
        for resource_id in resource_ids:
            resource = self._resources[resource_id]
            if status is None or resource.metadata.status == status:
                resources.append(resource)
        
        return resources
    
    def find_resources(
        self,
        name_pattern: Optional[str] = None,
        tags: Optional[List[str]] = None,
        use_case: Optional[str] = None
    ) -> List[RegisteredResource]:
        """Find resources by name, tags, or use case."""
        results = []
        
        for resource in self._resources.values():
            match = True
            
            if name_pattern and name_pattern.lower() not in resource.metadata.name.lower():
                match = False
            
            if tags and not any(tag in resource.metadata.tags for tag in tags):
                match = False
            
            if use_case and use_case not in resource.metadata.use_cases:
                match = False
            
            if match:
                results.append(resource)
        
        return results
    
    def update_resource_status(
        self,
        registry_id: str,
        new_status: ResourceStatus,
        reason: str = ""
    ) -> bool:
        """Update the status of a registered resource."""
        resource = self._resources.get(registry_id)
        if resource:
            resource.update_status(new_status, reason)
            return True
        return False
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get statistics about the registry."""
        stats = {
            "total_resources": len(self._resources),
            "by_category": {
                cat.value: len(ids) for cat, ids in self._by_category.items()
            },
            "by_status": {},
            "by_class": {
                cls: len(ids) for cls, ids in self._by_class.items()
            }
        }
        
        # Count by status
        for resource in self._resources.values():
            status = resource.metadata.status.value
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
        
        return stats


# Global registry instance
_global_registry: Optional[HACSResourceRegistry] = None


def get_global_registry() -> HACSResourceRegistry:
    """Get the global resource registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = HACSResourceRegistry()
    return _global_registry


def register_hacs_resource(
    resource_class: Type[BaseResource],
    name: str,
    version: str,
    description: str,
    category: ResourceCategory,
    actor_id: Optional[str] = None,
    **metadata_kwargs
) -> RegisteredResource:
    """
    Convenience function to register a hacs-core resource.
    
    Args:
        resource_class: The hacs-core resource class
        name: Human-readable name
        version: Semantic version
        description: Resource description
        category: Resource category
        actor_id: ID of actor registering the resource (for IAM)
        **metadata_kwargs: Additional metadata fields
        
    Returns:
        RegisteredResource wrapper
    """
    metadata = ResourceMetadata(
        name=name,
        version=version,
        description=description,
        category=category,
        **metadata_kwargs
    )
    
    registry = get_global_registry()
    return registry.register_resource(resource_class, metadata, instance_data=None, actor_id=actor_id)


# Pre-register common hacs-core resources
def _register_core_resources():
    """Register common hacs-core resources with the global registry."""
    registry = get_global_registry()
    
    # Clinical resources
    registry.register_resource(
        Patient,
        ResourceMetadata(
            name="Patient",
            version="1.0.0",
            description="FHIR-compatible patient resource",
            category=ResourceCategory.CLINICAL,
            tags=["fhir", "patient", "demographics"]
        )
    )
    
    registry.register_resource(
        Observation,
        ResourceMetadata(
            name="Observation",
            version="1.0.0", 
            description="Clinical observations and measurements",
            category=ResourceCategory.CLINICAL,
            tags=["fhir", "observation", "measurement"]
        )
    )
    
    # Workflow resources
    registry.register_resource(
        WorkflowDefinition,
        ResourceMetadata(
            name="WorkflowDefinition",
            version="1.0.0",
            description="Clinical workflow definition",
            category=ResourceCategory.WORKFLOW,
            tags=["workflow", "clinical", "process"]
        )
    )
    
    registry.register_resource(
        ActivityDefinition,
        ResourceMetadata(
            name="ActivityDefinition", 
            version="1.0.0",
            description="Definition of activities in workflows",
            category=ResourceCategory.WORKFLOW,
            tags=["workflow", "activity", "process"]
        )
    )
    
    # Communication resources
    registry.register_resource(
        AgentMessage,
        ResourceMetadata(
            name="AgentMessage",
            version="1.0.0",
            description="Messages for agent communication",
            category=ResourceCategory.COMMUNICATION,
            tags=["agent", "message", "communication"]
        )
    )
    
    registry.register_resource(
        Document,
        ResourceMetadata(
            name="Document",
            version="1.0.0",
            description="Clinical documents with LangChain integration",
            category=ResourceCategory.COMMUNICATION,
            tags=["document", "clinical", "langchain"]
        )
    )


# Initialize core resources on import
_register_core_resources()


__all__ = [
    'ResourceStatus',
    'ResourceCategory', 
    'ResourceMetadata',
    'RegisteredResource',
    'HACSResourceRegistry',
    'get_global_registry',
    'register_hacs_resource',
]