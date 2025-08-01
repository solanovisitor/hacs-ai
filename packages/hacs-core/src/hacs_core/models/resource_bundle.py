"""
Resource Bundle Models - HACS Resource Collections with Registry and Workflow Support.

This module provides the ResourceBundle class and related types for packaging
collections of HACS resources with additional metadata for registry purposes,
workflow bindings, and administrative information.

Inspired by FHIR Bundle but adapted for HACS needs.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, validator, model_validator

from ..base_resource import BaseResource


class BundleType(str, Enum):
    """
    Types of resource bundles indicating their purpose and usage patterns.
    """
    # Core bundle types
    COLLECTION = "collection"  # General collection of resources
    DOCUMENT = "document"  # Clinical document with structured resources
    SEARCHSET = "searchset"  # Results from a search operation
    STACK = "stack"  # Curated resource stack for specific use cases
    
    # Workflow types
    WORKFLOW_INPUT = "workflow-input"  # Input resources for workflow processing
    WORKFLOW_OUTPUT = "workflow-output"  # Output from workflow processing
    VALIDATION_SET = "validation-set"  # Resources for validation purposes
    
    # Registry types
    TEMPLATE = "template"  # Template resources for reuse
    REGISTRY_ENTRY = "registry-entry"  # Official registry entry
    VERSION_SNAPSHOT = "version-snapshot"  # Versioned snapshot of resources


class BundleStatus(str, Enum):
    """
    Status of the resource bundle in its lifecycle.
    """
    DRAFT = "draft"  # Under development
    ACTIVE = "active"  # Ready for use
    INACTIVE = "inactive"  # Temporarily disabled
    DEPRECATED = "deprecated"  # Superseded by newer version
    EXPERIMENTAL = "experimental"  # For testing/evaluation only


class WorkflowBindingType(str, Enum):
    """
    Types of workflow bindings that can be associated with bundles.
    """
    INPUT_FILTER = "input-filter"  # Bundle acts as input filter for workflow
    OUTPUT_TEMPLATE = "output-template"  # Bundle serves as output template
    VALIDATION_RULE = "validation-rule"  # Bundle defines validation rules
    SEARCH_FILTER = "search-filter"  # Bundle provides search filters
    TRANSFORMATION = "transformation"  # Bundle defines transformation rules


class LinkRelation(str, Enum):
    """
    Types of links that can be associated with bundles.
    """
    SELF = "self"  # Link to this bundle
    NEXT = "next"  # Next page of results
    PREVIOUS = "previous"  # Previous page of results
    FIRST = "first"  # First page of results
    LAST = "last"  # Last page of results
    RELATED = "related"  # Related bundle
    DERIVED_FROM = "derived-from"  # Source bundle this was derived from
    SUPERSEDES = "supersedes"  # Bundle this supersedes
    SUPERSEDED_BY = "superseded-by"  # Bundle that supersedes this
    ALTERNATE = "alternate"  # Alternative representation


class BundleLink(BaseModel):
    """
    Link associated with a bundle providing navigation or relationship information.
    """
    relation: LinkRelation = Field(..., description="Type of link relationship")
    url: str = Field(..., description="URL for the link")
    title: Optional[str] = Field(None, description="Human-readable description of the link")


class WorkflowBinding(BaseModel):
    """
    Binding between a resource bundle and workflow operations.
    """
    workflow_id: str = Field(..., description="Identifier of the workflow")
    workflow_name: Optional[str] = Field(None, description="Human-readable name of the workflow")
    binding_type: WorkflowBindingType = Field(..., description="Type of workflow binding")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Workflow-specific parameters")
    priority: Optional[int] = Field(None, ge=1, le=10, description="Priority (1=highest, 10=lowest)")
    active: bool = Field(True, description="Whether this binding is currently active")
    description: Optional[str] = Field(None, description="Description of the workflow binding")


class BundleSearchInfo(BaseModel):
    """
    Search-related information for bundle entries (when bundle type is searchset).
    """
    mode: Optional[str] = Field(None, description="Search mode: 'match' or 'include'")
    score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Search relevance score (0-1)")
    rank: Optional[int] = Field(None, ge=1, description="Search result ranking")


class BundleEntry(BaseModel):
    """
    Individual entry within a resource bundle containing a resource and metadata.
    """
    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        extra="allow"
    )
    
    # Core entry identification
    full_url: Optional[str] = Field(None, description="Absolute URL for this resource")
    resource: BaseResource = Field(..., description="The HACS resource in this entry")
    
    # Entry metadata
    title: Optional[str] = Field(None, description="Human-readable title for this entry")
    tags: List[str] = Field(default_factory=list, description="Tags for categorizing this entry")
    priority: Optional[int] = Field(None, ge=1, le=10, description="Priority within bundle (1=highest)")
    
    # Search-related information
    search: Optional[BundleSearchInfo] = Field(None, description="Search metadata (for searchset bundles)")
    
    # Entry-specific links
    links: List[BundleLink] = Field(default_factory=list, description="Links related to this entry")
    
    # Custom metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional entry-specific metadata")


class UseCase(BaseModel):
    """
    Documented use case for a resource bundle.
    """
    name: str = Field(..., description="Name of the use case")
    description: str = Field(..., description="Detailed description of the use case")
    examples: List[str] = Field(default_factory=list, description="Example scenarios")
    prerequisites: List[str] = Field(default_factory=list, description="Required conditions")
    outcomes: List[str] = Field(default_factory=list, description="Expected outcomes")
    tags: List[str] = Field(default_factory=list, description="Categorization tags")


class Misuse(BaseModel):
    """
    Documented misuse or anti-pattern for a resource bundle.
    """
    scenario: str = Field(..., description="Description of the misuse scenario")
    reason: str = Field(..., description="Why this is problematic")
    alternatives: List[str] = Field(default_factory=list, description="Better alternatives")
    severity: str = Field("medium", description="Severity: low, medium, high, critical")


class BundleUpdate(BaseModel):
    """
    Record of updates made to a resource bundle.
    """
    version: str = Field(..., description="Version identifier for this update")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    author: Optional[str] = Field(None, description="Author of the update")
    summary: str = Field(..., description="Brief summary of changes")
    details: Optional[str] = Field(None, description="Detailed change description")
    breaking_changes: bool = Field(False, description="Whether this includes breaking changes")
    migration_notes: Optional[str] = Field(None, description="Notes for migrating from previous version")


class ResourceBundle(BaseResource):
    """
    A container for a collection of HACS resources with registry and workflow capabilities.
    
    Provides comprehensive bundling functionality including:
    - Resource collection and organization
    - Registry metadata (versions, use cases, updates)
    - Workflow bindings for processing pipelines
    - Search and navigation capabilities
    - Administrative and lifecycle management
    
    Based on FHIR Bundle concepts but adapted for HACS ecosystem needs.
    """
    
    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        extra="allow",
        json_schema_extra={
            "examples": [
                {
                    "id": "bundle-001",
                    "resource_type": "ResourceBundle",
                    "identifier": "hacs.example.psychiatric-assessment-v1",
                    "title": "Psychiatric Assessment Resource Stack",
                    "bundle_type": "stack",
                    "status": "active",
                    "version": "1.2.0",
                    "description": "Comprehensive resource stack for psychiatric assessments",
                    "entries": [
                        {
                            "resource": {
                                "id": "patient-001",
                                "resource_type": "Patient"
                            }
                        }
                    ]
                }
            ]
        }
    )
    
    # Override resource_type
    resource_type: str = Field(default="ResourceBundle", frozen=True)
    
    # Core Bundle Information
    identifier: Optional[str] = Field(None, description="Persistent identifier for the bundle (e.g., registry ID)")
    title: Optional[str] = Field(None, description="Human-readable title for the bundle")
    bundle_type: BundleType = Field(..., description="Type of bundle indicating its purpose")
    status: BundleStatus = Field(BundleStatus.DRAFT, description="Current status of the bundle")
    
    # Versioning and Registry
    version: str = Field(..., description="Version of this bundle (semantic versioning recommended)")
    publisher: Optional[str] = Field(None, description="Organization or individual who published this bundle")
    contact: Optional[str] = Field(None, description="Contact information for bundle maintainer")
    copyright: Optional[str] = Field(None, description="Copyright notice")
    
    # Content Description
    description: Optional[str] = Field(None, description="Detailed description of bundle purpose and contents")
    purpose: Optional[str] = Field(None, description="Explanation of why this bundle exists")
    keywords: List[str] = Field(default_factory=list, description="Keywords for discovery and search")
    categories: List[str] = Field(default_factory=list, description="Broad categories this bundle belongs to")
    
    # Bundle Contents
    entries: List[BundleEntry] = Field(default_factory=list, description="Resources contained in this bundle")
    total: Optional[int] = Field(None, description="Total number of matching resources (for searchsets)")
    
    # Registry Information
    use_cases: List[UseCase] = Field(default_factory=list, description="Documented use cases for this bundle")
    misuses: List[Misuse] = Field(default_factory=list, description="Known misuses or anti-patterns")
    updates: List[BundleUpdate] = Field(default_factory=list, description="Version history and updates")
    
    # Workflow Integration
    workflow_bindings: List[WorkflowBinding] = Field(
        default_factory=list, 
        description="Bindings to workflows that can process this bundle"
    )
    
    # Navigation and Relationships
    links: List[BundleLink] = Field(default_factory=list, description="Links related to this bundle")
    
    # Quality and Validation
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="Bundle-specific validation rules")
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Quality assessment score")
    maturity_level: Optional[str] = Field(None, description="Maturity level: experimental, beta, stable, mature")
    
    # Administrative
    license: Optional[str] = Field(None, description="License under which this bundle is distributed")
    experimental: bool = Field(False, description="Whether this bundle is experimental")
    
    # Custom Extensions
    extensions: Dict[str, Any] = Field(default_factory=dict, description="Custom extensions and metadata")
    
    @validator('total')
    def validate_total(cls, v, values):
        """Validate that total is only used for searchset bundles."""
        if v is not None and values.get('bundle_type') not in [BundleType.SEARCHSET]:
            raise ValueError("total field is only valid for searchset bundles")
        return v
    
    @validator('entries')
    def validate_entries_not_empty_for_certain_types(cls, v, values):
        """Validate that certain bundle types have entries."""
        bundle_type = values.get('bundle_type')
        if bundle_type in [BundleType.DOCUMENT, BundleType.STACK] and not v:
            raise ValueError(f"{bundle_type} bundles must contain at least one entry")
        return v
    
    @model_validator(mode='after')
    def validate_workflow_bindings(self):
        """Validate workflow bindings consistency."""
        bindings = self.workflow_bindings
        workflow_ids = [b.workflow_id for b in bindings]
        if len(workflow_ids) != len(set(workflow_ids)):
            raise ValueError("Workflow bindings must have unique workflow_ids")
        return self
    
    def add_resource(
        self, 
        resource: BaseResource, 
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        priority: Optional[int] = None,
        full_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "ResourceBundle":
        """
        Add a resource to the bundle.
        
        Args:
            resource: The HACS resource to add
            title: Optional title for the entry
            tags: Optional tags for the entry
            priority: Optional priority (1=highest, 10=lowest)
            full_url: Optional absolute URL for the resource
            metadata: Optional additional metadata
            
        Returns:
            Self for method chaining
        """
        entry = BundleEntry(
            resource=resource,
            title=title,
            tags=tags or [],
            priority=priority,
            full_url=full_url,
            metadata=metadata or {}
        )
        self.entries.append(entry)
        return self
    
    def add_workflow_binding(
        self,
        workflow_id: str,
        binding_type: WorkflowBindingType,
        workflow_name: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        priority: Optional[int] = None,
        description: Optional[str] = None
    ) -> "ResourceBundle":
        """
        Add a workflow binding to the bundle.
        
        Args:
            workflow_id: Identifier of the workflow
            binding_type: Type of workflow binding
            workflow_name: Optional human-readable name
            parameters: Optional workflow parameters
            priority: Optional priority (1=highest, 10=lowest)
            description: Optional description
            
        Returns:
            Self for method chaining
        """
        binding = WorkflowBinding(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            binding_type=binding_type,
            parameters=parameters or {},
            priority=priority,
            description=description
        )
        self.workflow_bindings.append(binding)
        return self
    
    def add_use_case(
        self,
        name: str,
        description: str,
        examples: Optional[List[str]] = None,
        prerequisites: Optional[List[str]] = None,
        outcomes: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> "ResourceBundle":
        """
        Add a documented use case to the bundle.
        
        Args:
            name: Name of the use case
            description: Detailed description
            examples: Example scenarios
            prerequisites: Required conditions
            outcomes: Expected outcomes
            tags: Categorization tags
            
        Returns:
            Self for method chaining
        """
        use_case = UseCase(
            name=name,
            description=description,
            examples=examples or [],
            prerequisites=prerequisites or [],
            outcomes=outcomes or [],
            tags=tags or []
        )
        self.use_cases.append(use_case)
        return self
    
    def add_update_record(
        self,
        version: str,
        summary: str,
        author: Optional[str] = None,
        details: Optional[str] = None,
        breaking_changes: bool = False,
        migration_notes: Optional[str] = None
    ) -> "ResourceBundle":
        """
        Add an update record to track changes.
        
        Args:
            version: Version identifier
            summary: Brief summary of changes
            author: Author of the update
            details: Detailed change description
            breaking_changes: Whether this includes breaking changes
            migration_notes: Migration guidance
            
        Returns:
            Self for method chaining
        """
        update = BundleUpdate(
            version=version,
            author=author,
            summary=summary,
            details=details,
            breaking_changes=breaking_changes,
            migration_notes=migration_notes
        )
        self.updates.append(update)
        return self
    
    def get_resources_by_type(self, resource_type: str) -> List[BaseResource]:
        """
        Get all resources of a specific type from the bundle.
        
        Args:
            resource_type: The resource type to filter by
            
        Returns:
            List of resources matching the type
        """
        return [
            entry.resource 
            for entry in self.entries 
            if entry.resource.resource_type == resource_type
        ]
    
    def get_resources_by_tag(self, tag: str) -> List[BaseResource]:
        """
        Get all resources with a specific tag.
        
        Args:
            tag: The tag to filter by
            
        Returns:
            List of resources with the specified tag
        """
        return [
            entry.resource 
            for entry in self.entries 
            if tag in entry.tags
        ]
    
    def get_workflow_bindings_by_type(self, binding_type: WorkflowBindingType) -> List[WorkflowBinding]:
        """
        Get workflow bindings of a specific type.
        
        Args:
            binding_type: The binding type to filter by
            
        Returns:
            List of workflow bindings matching the type
        """
        return [
            binding 
            for binding in self.workflow_bindings 
            if binding.binding_type == binding_type and binding.active
        ]
    
    def validate_bundle_integrity(self) -> Dict[str, Any]:
        """
        Validate the integrity and consistency of the bundle.
        
        Returns:
            Dictionary with validation results
        """
        issues = []
        warnings = []
        
        # Check for duplicate resource IDs
        resource_ids = [entry.resource.id for entry in self.entries if entry.resource.id]
        if len(resource_ids) != len(set(resource_ids)):
            issues.append("Duplicate resource IDs found in bundle")
        
        # Check workflow binding consistency
        for binding in self.workflow_bindings:
            if not binding.workflow_id:
                issues.append("Workflow binding missing workflow_id")
        
        # Check use case completeness
        if not self.use_cases and self.status == BundleStatus.ACTIVE:
            warnings.append("Active bundle should have documented use cases")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "entry_count": len(self.entries),
            "workflow_binding_count": len(self.workflow_bindings),
            "use_case_count": len(self.use_cases)
        }


# Factory functions for common bundle types

def create_resource_stack(
    stack_name: str,
    version: str,
    description: str,
    resources: List[BaseResource],
    publisher: Optional[str] = None
) -> ResourceBundle:
    """
    Create a resource stack bundle for curated resource collections.
    
    Args:
        stack_name: Name of the resource stack
        version: Version of the stack
        description: Description of the stack's purpose
        resources: List of resources to include
        publisher: Optional publisher information
        
    Returns:
        Configured ResourceBundle of type STACK
    """
    bundle = ResourceBundle(
        title=stack_name,
        bundle_type=BundleType.STACK,
        version=version,
        description=description,
        publisher=publisher,
        status=BundleStatus.ACTIVE
    )
    
    for resource in resources:
        bundle.add_resource(resource)
    
    return bundle


def create_search_results_bundle(
    resources: List[BaseResource],
    total: Optional[int] = None,
    search_url: Optional[str] = None
) -> ResourceBundle:
    """
    Create a search results bundle.
    
    Args:
        resources: List of resources from search
        total: Total number of matching resources
        search_url: URL of the search that generated these results
        
    Returns:
        Configured ResourceBundle of type SEARCHSET
    """
    bundle = ResourceBundle(
        bundle_type=BundleType.SEARCHSET,
        version="1.0.0",
        total=total or len(resources)
    )
    
    for i, resource in enumerate(resources):
        bundle.add_resource(
            resource=resource,
            metadata={"search": {"mode": "match", "rank": i + 1}}
        )
    
    if search_url:
        bundle.links.append(BundleLink(
            relation=LinkRelation.SELF,
            url=search_url,
            title="Search query that generated these results"
        ))
    
    return bundle


def create_workflow_template_bundle(
    template_name: str,
    version: str,
    workflow_id: str,
    template_resources: List[BaseResource],
    description: Optional[str] = None
) -> ResourceBundle:
    """
    Create a workflow template bundle.
    
    Args:
        template_name: Name of the template
        version: Version of the template
        workflow_id: Associated workflow identifier
        template_resources: Template resources
        description: Optional description
        
    Returns:
        Configured ResourceBundle with workflow bindings
    """
    bundle = ResourceBundle(
        title=template_name,
        bundle_type=BundleType.TEMPLATE,
        version=version,
        description=description or f"Template bundle for {template_name}",
        status=BundleStatus.ACTIVE
    )
    
    for resource in template_resources:
        bundle.add_resource(resource)
    
    bundle.add_workflow_binding(
        workflow_id=workflow_id,
        binding_type=WorkflowBindingType.OUTPUT_TEMPLATE,
        description=f"Output template for {workflow_id} workflow"
    )
    
    return bundle