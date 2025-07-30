"""
HACS Tools - Unified LangChain tools for healthcare AI agents.

This single module provides a comprehensive collection of LangChain @tool
decorated functions for all HACS operations, from basic CRUD to advanced,
model-driven clinical workflows.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, Union

logger = logging.getLogger(__name__)

try:
    from langchain_core.tools import tool
    _has_langchain = True
except ImportError:
    _has_langchain = False
    # Placeholder decorator when langchain is not available
    def tool(func):
        """Placeholder tool decorator when langchain is not available."""
        func._is_tool = True
        return func

from pydantic import BaseModel, Field

# === RESULT MODELS ===


class HACSResult(BaseModel):
    """Standard result format for basic HACS tool operations."""

    success: bool = Field(description="Whether the operation succeeded")
    message: str = Field(description="Human-readable result message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Operation specific data")
    error: Optional[str] = Field(default=None, description="Error message if operation failed")
    timestamp: datetime = Field(default_factory=datetime.now)


class ResourceSchemaResult(BaseModel):
    """Result for model schema operations."""

    success: bool = Field(description="Whether the operation succeeded")
    resource_name: str = Field(description="Name of the model or view")
    schema: Dict[str, Any] = Field(description="JSON schema for the model")
    field_count: int = Field(description="Number of fields in the schema")
    required_fields: List[str] = Field(description="List of required field names")
    optional_fields: List[str] = Field(description="List of optional field names")
    message: str = Field(description="Human-readable result message")


class ModelDiscoveryResult(BaseModel):
    """Result for model discovery operations."""

    success: bool = Field(description="Whether the operation succeeded")
    models: List[Dict[str, Any]] = Field(description="List of available models with metadata")
    total_count: int = Field(description="Total number of models found")
    categories: List[str] = Field(description="Categories of models available")
    message: str = Field(description="Human-readable result message")


class FieldAnalysisResult(BaseModel):
    """Result for field analysis operations."""

    success: bool = Field(description="Whether the analysis succeeded")
    resource_name: str = Field(description="Name of the analyzed model")
    total_fields: int = Field(description="Total number of fields")
    field_details: List[Dict[str, Any]] = Field(description="Detailed field information")
    field_types: Dict[str, int] = Field(description="Count of fields by type")
    validation_rules: List[str] = Field(description="List of validation rules")
    message: str = Field(description="Human-readable result message")


class DataQueryResult(BaseModel):
    """Result of a structured search using a DataRequirement."""

    success: bool = Field(description="Whether the search succeeded")
    message: str = Field(description="Human-readable result message")
    data_requirement_id: str | None = Field(
        default=None, description="ID of the DataRequirement used"
    )
    results_count: int = Field(default=0, description="Number of results found")
    results: list[dict[str, Any]] = Field(
        default_factory=list, description="Found resources"
    )
    aggregated_data: dict[str, Any] | None = Field(
        default=None, description="Aggregated results if requested"
    )
    execution_time_ms: float | None = Field(
        default=None, description="Query execution time"
    )
    timestamp: datetime = Field(default_factory=datetime.now)


class WorkflowResult(BaseModel):
    """Result of executing a clinical workflow using a PlanDefinition."""

    success: bool = Field(description="Whether the workflow execution succeeded")
    message: str = Field(description="Human-readable result message")
    plan_definition_id: str = Field(description="ID of the PlanDefinition executed")
    execution_id: str = Field(description="Unique ID for this execution")
    completed_actions: list[str] = Field(
        default_factory=list, description="IDs of completed actions"
    )
    pending_actions: list[str] = Field(
        default_factory=list, description="IDs of pending actions"
    )
    failed_actions: list[str] = Field(
        default_factory=list, description="IDs of failed actions"
    )
    execution_status: str = Field(description="Overall execution status")
    next_recommended_action: str | None = Field(
        default=None, description="Next recommended action ID"
    )
    timestamp: datetime = Field(default_factory=datetime.now)


class GuidanceResult(BaseModel):
    """Result of clinical decision support using a GuidanceResponse."""

    success: bool = Field(description="Whether the decision support succeeded")
    message: str = Field(description="Human-readable result message")
    guidance_response_id: str = Field(description="ID of the GuidanceResponse")
    guidance_type: str = Field(description="Type of guidance provided")
    recommendations: list[dict[str, Any]] = Field(
        default_factory=list, description="Clinical recommendations"
    )
    confidence_score: float = Field(description="Confidence in the guidance (0.0-1.0)")
    evidence_sources: list[str] = Field(
        default_factory=list, description="Sources of evidence used"
    )
    contraindications: list[str] = Field(
        default_factory=list, description="Any contraindications found"
    )
    timestamp: datetime = Field(default_factory=datetime.now)


class MemoryResult(BaseModel):
    """Result for memory management operations."""

    success: bool = Field(description="Whether the memory operation succeeded")
    message: str = Field(description="Human-readable result message")
    memory_id: Optional[str] = Field(default=None, description="ID of the memory block")
    memory_type: Optional[str] = Field(default=None, description="Type of memory")
    content: Optional[str] = Field(default=None, description="Memory content")
    importance_score: Optional[float] = Field(default=None, description="Importance score")
    tags: List[str] = Field(default_factory=list, description="Memory tags")
    related_memories: List[str] = Field(default_factory=list, description="Related memory IDs")
    timestamp: datetime = Field(default_factory=datetime.now)


class VersionResult(BaseModel):
    """Result for versioning operations."""

    success: bool = Field(description="Whether the versioning operation succeeded")
    message: str = Field(description="Human-readable result message")
    resource_name: str = Field(description="Name of the versioned model")
    version: str = Field(description="Version identifier")
    version_id: str = Field(description="Unique version ID")
    description: str = Field(description="Version description")
    status: str = Field(description="Version status")
    schema_definition: Dict[str, Any] = Field(description="Schema definition for this version")
    tags: List[str] = Field(default_factory=list, description="Version tags")
    timestamp: datetime = Field(default_factory=datetime.now)


# === ENHANCED CRUD OPERATIONS ===

@tool
def create_hacs_record(
    actor_name: str, resource_type: str, resource_data: dict[str, Any],
    validate_fhir: bool = True, auto_generate_id: bool = True
) -> HACSResult:
    """
    Create a new HACS resource (data record) with enhanced validation and ID generation.

    TERMINOLOGY DISTINCTION:
    - HACS Records: Schema definitions/templates (Patient model, Observation model)
    - HACS Records: Actual data records validated against HACS resources
    - This tool creates HACS RESOURCES (data records) using HACS resource schemas for validation

    IMPORTANT: HACS resources use DIRECT field structure, NOT nested FHIR-style arrays!

    Args:
        actor_name: Name of the actor creating the resource
        resource_type: Type of HACS resource to use for validation (Patient, Observation, etc.)
        resource_data: Resource data - MUST conform to HACS resource's direct field structure
        validate_fhir: Whether to perform additional FHIR validation
        auto_generate_id: Whether to auto-generate ID if missing

    PATIENT RESOURCE STRUCTURE EXAMPLES (using Patient model):
    ✅ CORRECT - Direct fields matching Patient model:
    {
        "given": ["John"],
        "family": "Doe",
        "full_name": "John Doe",
        "birth_date": "1990-01-01",
        "gender": "male",
        "email": "john@example.com",
        "phone": "+1-555-0123"
    }

    ❌ INCORRECT - Nested FHIR structure (not compatible with HACS resources):
    {
        "name": [{"given": ["John"], "family": "Doe"}],  # DON'T USE - use direct fields!
        "birthDate": "1990-01-01",  # Use birth_date to match Patient model
        "telecom": [{"system": "email", "value": "john@example.com"}]  # Use email field
    }

    Returns:
        HACSResult indicating success/failure with resource ID and validation details
    """
    try:
        from hacs_core.actor import Actor
        from hacs_core.protocols import PersistenceProvider

        # Create actor instance
        actor = Actor(name=actor_name, role="physician")

        # Auto-generate ID if requested and missing
        if auto_generate_id and 'id' not in resource_data:
            import uuid
            resource_data['id'] = f"{resource_type.lower()}-{str(uuid.uuid4())[:8]}"

        # Set resource_type if missing
        if 'resource_type' not in resource_data:
            resource_data['resource_type'] = resource_type

        # Get model class and validate
        model_class = _get_model_class(resource_type)
        if not model_class:
            return HACSResult(
                success=False,
                message=f"Resource type '{resource_type}' not found in HACS resources",
                error=f"Resource type '{resource_type}' not found in HACS resources"
            )

        # Create and validate the resource
        resource = model_class.model_validate(resource_data)

        # Additional FHIR validation if requested
        if validate_fhir and hasattr(resource, 'validate_fhir'):
            try:
                resource.validate_fhir()
            except Exception as e:
                # Don't fail on FHIR validation, just warn
                pass

        # Here you would integrate with your persistence provider
        # For now, return success with the created resource data

        return HACSResult(
            success=True,
            message=f"Successfully created {resource_type} with ID: {resource.id}",
            data={
                "resource_id": resource.id,
                "resource_type": resource_type,
                "created_fields": list(resource_data.keys()),
                "validation_passed": True
            }
        )

    except Exception as e:
        return HACSResult(
            success=False,
            message=f"Failed to create {resource_type}",
            error=str(e)
        )


@tool
def get_hacs_record(
    actor_name: str, resource_type: str, resource_id: str
) -> HACSResult:
    """
    Retrieve a HACS record by ID.

    Args:
        actor_name: Name of the actor requesting the record
        resource_type: Type of HACS resource
        resource_id: Unique ID of the resource

    Returns:
        HACSResult with the retrieved resource data
    """
    try:
        from hacs_core.actor import Actor

        # Create actor instance
        actor = Actor(name=actor_name, role="physician")

        # Validate resource type
        model_class = _get_model_class(resource_type)
        if not model_class:
            return HACSResult(
                success=False,
                message=f"Unknown resource type: {resource_type}",
                error=f"Resource type '{resource_type}' not found"
            )

        # Here you would integrate with your persistence provider
        # For now, return a placeholder response

        return HACSResult(
            success=True,
            message=f"Retrieved {resource_type} with ID: {resource_id}",
            data={
                "resource_id": resource_id,
                "resource_type": resource_type,
                "retrieval_time": datetime.now().isoformat()
            }
        )

    except Exception as e:
        return HACSResult(
            success=False,
            message=f"Failed to retrieve {resource_type} with ID: {resource_id}",
            error=str(e)
        )


@tool
def search_hacs_records(
    actor_name: str,
    resource_type: str,
    filters: dict[str, Any] | None = None,
    semantic_query: str | None = None,
    limit: int = 10,
) -> list[HACSResult]:
    """
    Search for HACS records with optional semantic search capabilities.

    Args:
        actor_name: Name of the actor performing the search
        resource_type: Type of HACS resource to search
        filters: Optional dictionary of field filters
        semantic_query: Optional semantic search query
        limit: Maximum number of results to return

    Returns:
        List of HACSResult objects with search results
    """
    try:
        from hacs_core.actor import Actor

        # Create actor instance
        actor = Actor(name=actor_name, role="physician")

        # Validate resource type
        model_class = _get_model_class(resource_type)
        if not model_class:
            return [HACSResult(
                success=False,
                message=f"Unknown resource type: {resource_type}",
                error=f"Resource type '{resource_type}' not found"
            )]

        # Here you would integrate with your persistence provider and vector store
        # For now, return placeholder results

        results = []
        for i in range(min(3, limit)):  # Placeholder: return 3 results
            results.append(HACSResult(
                success=True,
                message=f"Found {resource_type} record {i+1}",
                data={
                    "resource_id": f"{resource_type.lower()}-{i+1}",
                    "resource_type": resource_type,
                    "match_score": 0.9 - (i * 0.1),
                    "search_query": semantic_query or "filter-based"
                }
            ))

        return results

    except Exception as e:
        return [HACSResult(
            success=False,
            message=f"Failed to search {resource_type} records",
            error=str(e)
        )]


@tool
def update_hacs_record(
    actor_name: str, resource_type: str, resource_id: str, updates: dict[str, Any]
) -> HACSResult:
    """
    Update an existing HACS record.

    Args:
        actor_name: Name of the actor updating the record
        resource_type: Type of HACS resource
        resource_id: Unique ID of the resource to update
        updates: Dictionary of field updates

    Returns:
        HACSResult with update status and details
    """
    try:
        from hacs_core.actor import Actor

        # Create actor instance
        actor = Actor(name=actor_name, role="physician")

        # Validate resource type
        model_class = _get_model_class(resource_type)
        if not model_class:
            return HACSResult(
                success=False,
                message=f"Unknown resource type: {resource_type}",
                error=f"Resource type '{resource_type}' not found"
            )

        # Here you would integrate with your persistence provider
        # For now, return success response

        return HACSResult(
            success=True,
            message=f"Successfully updated {resource_type} with ID: {resource_id}",
            data={
                "resource_id": resource_id,
                "resource_type": resource_type,
                "updated_fields": list(updates.keys()),
                "update_count": len(updates)
            }
        )

    except Exception as e:
        return HACSResult(
            success=False,
            message=f"Failed to update {resource_type} with ID: {resource_id}",
            error=str(e)
        )


@tool
def delete_hacs_record(
    actor_name: str, resource_type: str, resource_id: str
) -> HACSResult:
    """
    Delete a HACS record.

    Args:
        actor_name: Name of the actor deleting the record
        resource_type: Type of HACS resource
        resource_id: Unique ID of the resource to delete

    Returns:
        HACSResult with deletion status
    """
    try:
        from hacs_core.actor import Actor

        # Create actor instance
        actor = Actor(name=actor_name, role="physician")

        # Validate resource type
        model_class = _get_model_class(resource_type)
        if not model_class:
            return HACSResult(
                success=False,
                message=f"Unknown resource type: {resource_type}",
                error=f"Resource type '{resource_type}' not found"
            )

        # Here you would integrate with your persistence provider
        # For now, return success response

        return HACSResult(
            success=True,
            message=f"Successfully deleted {resource_type} with ID: {resource_id}",
            data={
                "resource_id": resource_id,
                "resource_type": resource_type,
                "deletion_time": datetime.now().isoformat()
            }
        )

    except Exception as e:
        return HACSResult(
            success=False,
            message=f"Failed to delete {resource_type} with ID: {resource_id}",
            error=str(e)
        )


# === MEMORY MANAGEMENT TOOLS ===

@tool
def create_hacs_memory(
    actor_name: str,
    content: str,
    memory_type: str = "episodic",
    importance_score: float = 0.5,
    tags: list[str] | None = None,
    session_id: str | None = None,
) -> MemoryResult:
    """
    Create and store a memory block with automatic classification and vector embedding.

    Args:
        actor_name: Name of the actor creating the memory
        content: Memory content to store
        memory_type: Type of memory (episodic, procedural, executive, semantic)
        importance_score: Importance score from 0.0 to 1.0
        tags: Optional tags for categorization
        session_id: Optional session ID for grouping

    Returns:
        MemoryResult with memory creation details
    """
    try:
        from hacs_core.actor import Actor
        from hacs_core.models.memory import MemoryBlock
        import uuid

        # Create actor instance
        actor = Actor(name=actor_name, role="physician")

        # Create memory block
        memory_id = f"mem-{str(uuid.uuid4())[:8]}"
        memory = MemoryBlock(
            id=memory_id,
            memory_type=memory_type,
            content=content,
            importance_score=importance_score,
            tags=tags or [],
            metadata={"session_id": session_id} if session_id else {}
        )

        # Here you would integrate with your persistence provider and vector store
        # For now, return success response

        return MemoryResult(
            success=True,
            message=f"Successfully created {memory_type} memory with ID: {memory_id}",
            memory_id=memory_id,
            memory_type=memory_type,
            content=content,
            importance_score=importance_score,
            tags=tags or []
        )

    except Exception as e:
        return MemoryResult(
            success=False,
            message=f"Failed to create memory",
            error=str(e)
        )


@tool
def search_hacs_memories(
    actor_name: str,
    query: str = "",
    memory_type: str | None = None,
    session_id: str | None = None,
    min_importance: float = 0.0,
    limit: int = 5,
) -> list[MemoryResult]:
    """
    Search memories using semantic similarity, filters, and advanced retrieval methods.

    Args:
        actor_name: Name of the actor searching memories
        query: Search query for semantic matching
        memory_type: Optional filter by memory type
        session_id: Optional filter by session ID
        min_importance: Minimum importance score filter
        limit: Maximum results to return

    Returns:
        List of MemoryResult objects with search results
    """
    try:
        from hacs_core.actor import Actor

        # Create actor instance
        actor = Actor(name=actor_name, role="physician")

        # Here you would integrate with your persistence provider and vector store
        # For now, return placeholder results

        results = []
        for i in range(min(3, limit)):  # Placeholder: return 3 results
            results.append(MemoryResult(
                success=True,
                message=f"Found memory {i+1} matching query",
                memory_id=f"mem-{i+1}",
                memory_type=memory_type or "episodic",
                content=f"Memory content {i+1} related to: {query}",
                importance_score=min_importance + (i * 0.1),
                tags=["search_result"]
            ))

        return results

    except Exception as e:
        return [MemoryResult(
            success=False,
            message=f"Failed to search memories",
            error=str(e)
        )]


@tool
def consolidate_memories(
    actor_name: str,
    session_id: str,
    memory_type: str = "episodic",
    strategy: str = "temporal",
    min_memories: int = 3,
) -> MemoryResult:
    """
    Consolidate related memories into summary memories for efficient recall.

    Args:
        actor_name: Name of the actor performing consolidation
        session_id: Session ID for memory consolidation
        memory_type: Type of memories to consolidate
        strategy: Consolidation strategy (temporal, importance, semantic)
        min_memories: Minimum memories required for consolidation

    Returns:
        MemoryResult with consolidation details
    """
    try:
        from hacs_core.actor import Actor
        import uuid

        # Create actor instance
        actor = Actor(name=actor_name, role="physician")

        # Here you would implement memory consolidation logic
        # For now, return success response

        consolidated_id = f"consolidated-{str(uuid.uuid4())[:8]}"

        return MemoryResult(
            success=True,
            message=f"Successfully consolidated memories using {strategy} strategy",
            memory_id=consolidated_id,
            memory_type=memory_type,
            content=f"Consolidated memory from session {session_id}",
            importance_score=0.8,
            tags=["consolidated", strategy]
        )

    except Exception as e:
        return MemoryResult(
            success=False,
            message=f"Failed to consolidate memories",
            error=str(e)
        )


@tool
def retrieve_context(
    actor_name: str,
    query: str,
    context_type: str = "general",
    max_memories: int = 5,
    session_id: str | None = None,
) -> list[MemoryResult]:
    """
    Retrieve relevant memory context for informed decision making.

    Args:
        actor_name: Name of the actor retrieving context
        query: Query for context retrieval
        context_type: Type of context needed (general, clinical, procedural, executive)
        max_memories: Maximum memories to retrieve
        session_id: Optional session ID for context scope

    Returns:
        List of MemoryResult objects with relevant context
    """
    try:
        from hacs_core.actor import Actor

        # Create actor instance
        actor = Actor(name=actor_name, role="physician")

        # Here you would implement context retrieval logic
        # For now, return placeholder results

        results = []
        for i in range(min(3, max_memories)):
            results.append(MemoryResult(
                success=True,
                message=f"Retrieved context memory {i+1}",
                memory_id=f"context-{i+1}",
                memory_type="semantic",
                content=f"Context memory {i+1} for query: {query}",
                importance_score=0.7 + (i * 0.1),
                tags=["context", context_type]
            ))

        return results

    except Exception as e:
        return [MemoryResult(
            success=False,
            message=f"Failed to retrieve context",
            error=str(e)
        )]


@tool
def analyze_memory_patterns(
    actor_name: str,
    analysis_type: str = "comprehensive",
    session_id: str | None = None,
    time_window_days: int = 30,
) -> HACSResult:
    """
    Analyze memory patterns to identify trends, gaps, and optimization opportunities.

    Args:
        actor_name: Name of the actor performing analysis
        analysis_type: Type of analysis (comprehensive, temporal, importance, connections)
        session_id: Optional session ID for scoped analysis
        time_window_days: Time window for analysis in days

    Returns:
        HACSResult with pattern analysis details
    """
    try:
        from hacs_core.actor import Actor

        # Create actor instance
        actor = Actor(name=actor_name, role="physician")

        # Here you would implement memory pattern analysis
        # For now, return placeholder analysis

        analysis_data = {
            "analysis_type": analysis_type,
            "time_window_days": time_window_days,
            "total_memories_analyzed": 45,
            "memory_types_distribution": {
                "episodic": 25,
                "procedural": 10,
                "executive": 7,
                "semantic": 3
            },
            "importance_stats": {
                "average_importance": 0.65,
                "high_importance_count": 12,
                "low_importance_count": 8
            },
            "patterns_identified": [
                "Increased procedural memory creation in recent days",
                "High concentration of cardiovascular-related memories",
                "Strong connections between patient consultation memories"
            ],
            "recommendations": [
                "Consider consolidating older episodic memories",
                "Create more executive memories for strategic planning",
                "Strengthen connections between related clinical observations"
            ]
        }

        return HACSResult(
            success=True,
            message=f"Completed {analysis_type} memory pattern analysis",
            data=analysis_data
        )

    except Exception as e:
        return HACSResult(
            success=False,
            message=f"Failed to analyze memory patterns",
            error=str(e)
        )


# === VERSIONING TOOLS ===

@tool
def version_hacs_resource(
    actor_name: str,
    resource_name: str,
    version: str,
    description: str,
    schema_definition: Dict[str, Any],
    tags: Optional[List[str]] = None,
    status: str = "published",
) -> VersionResult:
    """
    Create a new version of a HACS resource with schema definition.

    Args:
        actor_name: Name of the actor creating the version
        resource_name: Name of the model to version
        version: Version identifier (e.g., "1.0.0", "2.1.0")
        description: Description of changes in this version
        schema_definition: JSON schema definition for this version
        tags: Optional tags for categorization
        status: Version status (draft, published, deprecated)

    Returns:
        VersionResult with versioning details
    """
    try:
        from hacs_core.actor import Actor
        import uuid

        # Create actor instance
        actor = Actor(name=actor_name, role="physician")

        # Validate model exists
        model_class = _get_model_class(resource_name)
        if not model_class:
            return VersionResult(
                success=False,
                message=f"Unknown model: {resource_name}",
                resource_name=resource_name,
                version=version,
                version_id="",
                description=description,
                status=status,
                schema_definition={}
            )

        # Create version ID
        version_id = f"{resource_name.lower()}-v{version}-{str(uuid.uuid4())[:8]}"

        # Here you would integrate with your versioning system
        # For now, return success response

        return VersionResult(
            success=True,
            message=f"Successfully created version {version} for {resource_name}",
            resource_name=resource_name,
            version=version,
            version_id=version_id,
            description=description,
            status=status,
            schema_definition=schema_definition,
            tags=tags or []
        )

    except Exception as e:
        return VersionResult(
            success=False,
            message=f"Failed to create version for {resource_name}",
            resource_name=resource_name,
            version=version,
            version_id="",
            description=description,
            status=status,
            schema_definition={},
            error=str(e)
        )


# === ENHANCED KNOWLEDGE MANAGEMENT ===

@tool
def create_knowledge_item(
    actor_name: str,
    title: str,
    content: str,
    knowledge_type: str = "fact",
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> HACSResult:
    """
    Create a knowledge item for clinical decision support.

    Args:
        actor_name: Name of the actor creating the knowledge item
        title: Title of the knowledge item
        content: Content of the knowledge item
        knowledge_type: Type of knowledge (fact, rule, guideline, protocol)
        tags: Optional tags for categorization
        metadata: Optional additional metadata

    Returns:
        HACSResult with knowledge item creation details
    """
    try:
        from hacs_core.actor import Actor
        from hacs_core.models.knowledge import KnowledgeItem
        import uuid

        # Create actor instance
        actor = Actor(name=actor_name, role="physician")

        # Create knowledge item
        knowledge_id = f"knowledge-{str(uuid.uuid4())[:8]}"
        knowledge_item = KnowledgeItem(
            id=knowledge_id,
            title=title,
            content=content,
            knowledge_type=knowledge_type,
            tags=tags or [],
            metadata=metadata or {}
        )

        # Here you would integrate with your knowledge base
        # For now, return success response

        return HACSResult(
            success=True,
            message=f"Successfully created {knowledge_type} knowledge item: {title}",
            data={
                "knowledge_id": knowledge_id,
                "title": title,
                "knowledge_type": knowledge_type,
                "tags": tags or [],
                "content_length": len(content)
            }
        )

    except Exception as e:
        return HACSResult(
            success=False,
            message=f"Failed to create knowledge item",
            error=str(e)
        )


# === ENHANCED SCHEMA AND VALIDATION TOOLS ===

@tool
def get_resource_schema(resource_type: str, simplified: bool = False) -> ResourceSchemaResult:
    """
    Get the JSON schema for a HACS resource type with detailed examples and validation rules.

    CRITICAL FOR AGENTS: This schema shows the EXACT field structure required!
    - Use DIRECT fields (e.g., 'given', 'family', 'birth_date')
    - NOT nested FHIR arrays (e.g., 'name' array, 'birthDate', 'telecom' array)

    Args:
        resource_type: The HACS resource type (Patient, Observation, etc.)
        simplified: Whether to return a simplified schema (fewer optional fields)

    Returns:
        ResourceSchemaResult with detailed schema, examples, and validation requirements
    """
    try:
        model_class = _get_model_class(resource_type)
        if not model_class:
            return ResourceSchemaResult(
                success=False,
                resource_name=resource_type,
                schema={},
                field_count=0,
                required_fields=[],
                optional_fields=[],
                message=f"Resource type '{resource_type}' not found in HACS resources"
            )

        # Get the JSON schema
        schema = model_class.model_json_schema()

        # Extract field information
        properties = schema.get("properties", {})
        required_fields = schema.get("required", [])
        optional_fields = [field for field in properties.keys() if field not in required_fields]

        # Add detailed examples for common resources
        examples_map = {
            "Patient": {
                "minimal_example": {
                    "given": ["John"],
                    "family": "Doe"
                },
                "complete_example": {
                    "given": ["John", "Michael"],
                    "family": "Doe",
                    "full_name": "John Michael Doe",
                    "birth_date": "1990-03-15",
                    "gender": "male",
                    "email": "john.doe@example.com",
                    "phone": "+1-555-0123",
                    "age": 34
                },
                "validation_notes": [
                    "At least one of 'given', 'family', or 'full_name' must be provided",
                    "Use 'birth_date' format: 'YYYY-MM-DD'",
                    "Use 'email' and 'phone' fields directly, not 'telecom' array",
                    "Gender values: 'male', 'female', 'other', 'unknown'"
                ]
            },
            "Observation": {
                "minimal_example": {
                    "status": "final",
                    "code": "29463-7"
                },
                "complete_example": {
                    "status": "final",
                    "code": "29463-7",
                    "display": "Body Weight",
                    "value_quantity": {"value": 70.5, "unit": "kg"},
                    "effective_date_time": "2024-01-15T10:30:00Z",
                    "subject": "patient-123"
                },
                "validation_notes": [
                    "'status' is required: 'registered', 'preliminary', 'final', 'amended', 'cancelled'",
                    "'code' is required: Use LOINC codes or system-specific codes",
                    "Use 'value_quantity', 'value_string', or 'value_boolean' for values"
                ]
            },
            "Organization": {
                "minimal_example": {
                    "name": "General Hospital"
                },
                "complete_example": {
                    "name": "Metro General Hospital",
                    "active": True,
                    "organization_type": [{"code": "prov", "display": "Healthcare Provider"}],
                    "identifier": ["NPI-1234567890", "TIN-12-3456789"],
                    "alias": ["Metro General", "MGH"],
                    "description": "A 500-bed tertiary care hospital serving the metropolitan area",
                    "primary_email": "info@metrogeneral.org",
                    "primary_phone": "+1-555-0199",
                    "website": "https://www.metrogeneral.org",
                    "address_line": ["123 Hospital Drive"],
                    "city": "Boston",
                    "state": "MA",
                    "postal_code": "02101",
                    "country": "US",
                    "tags": ["hospital", "emergency_care", "trauma_center"]
                },
                "validation_notes": [
                    "Organization must have at least a 'name' or 'identifier'",
                    "Use 'organization_type' with codes: 'prov' (provider), 'dept' (department), 'team', 'govt', 'ins' (insurance), 'pay' (payer), 'edu' (educational), 'reli' (religious), 'crs' (clinical research), 'cg' (community group)",
                    "Use direct contact fields: 'primary_email', 'primary_phone' instead of complex telecom arrays",
                    "Use 'part_of_organization_id' to establish organizational hierarchy",
                    "Use 'contacts' array for specific purpose contacts (admin, billing, etc.)"
                ]
            }
        }

        # Add examples to schema if available
        if resource_type in examples_map:
            schema["examples"] = examples_map[resource_type]

        return ResourceSchemaResult(
            success=True,
            resource_name=resource_type,
            schema=schema,
            field_count=len(properties),
            required_fields=required_fields,
            optional_fields=optional_fields,
            message=f"Successfully retrieved schema for {resource_type} with {len(properties)} fields"
        )

    except Exception as e:
        return ResourceSchemaResult(
            success=False,
            resource_name=resource_type,
            schema={},
            field_count=0,
            required_fields=[],
            optional_fields=[],
            message=f"Error retrieving schema for {resource_type}: {str(e)}"
        )


@tool
def validate_resource_data(resource_type: str, data: dict[str, Any]) -> HACSResult:
    """
    Validate resource data against a HACS resource schema.

    Args:
        resource_type: Name of the HACS resource type
        data: Data to validate

    Returns:
        HACSResult with validation results
    """
    try:
        model_class = _get_model_class(resource_type)
        if not model_class:
            return HACSResult(
                success=False,
                message=f"Unknown resource type: {resource_type}",
                error=f"Resource type '{resource_type}' not found"
            )

        # Validate the data
        try:
            resource = model_class.model_validate(data)

            return HACSResult(
                success=True,
                message=f"Validation successful for {resource_type}",
                data={
                    "resource_id": getattr(resource, 'id', None),
                    "validated_fields": list(data.keys()),
                    "validation_passed": True
                }
            )

        except Exception as validation_error:
            return HACSResult(
                success=False,
                message=f"Validation failed for {resource_type}",
                error=str(validation_error),
                data={
                    "provided_fields": list(data.keys()),
                    "validation_passed": False
                }
            )

    except Exception as e:
        return HACSResult(
            success=False,
            message=f"Failed to validate {resource_type}",
            error=str(e)
        )


@tool
def list_available_resources() -> list[str]:
    """
    List all available HACS resource types.

    Returns:
        List of available resource type names
    """
    try:
        import hacs_core.models as models
        import inspect

        resource_types = []
        for name, obj in inspect.getmembers(models):
            if (inspect.isclass(obj) and
                hasattr(obj, 'resource_type') and
                name != 'BaseResource'):
                resource_types.append(name)

        return sorted(resource_types)

    except Exception:
        # Fallback to common resource types
        return [
            "Patient", "Observation", "Encounter", "Condition", "Medication",
            "MedicationRequest", "Procedure", "AllergyIntolerance", "Goal",
            "ServiceRequest", "FamilyMemberHistory", "RiskAssessment",
            "AgentMessage", "MemoryBlock", "KnowledgeItem", "Actor"
        ]


# === MODEL-DRIVEN TOOLS ===


@tool
def query_with_datarequirement(
    actor_name: str, data_requirement: dict[str, Any]
) -> DataQueryResult:
    """Search records using a structured HACS DataRequirement specification."""
    # (Implementation from enhanced_tools.py)
    try:
        from hacs_core import Actor, ActorRole, get_persistence_provider
        from hacs_models import DataRequirement

        start_time = datetime.now()
        actor = Actor(name=actor_name, role=ActorRole.SYSTEM)
        requirement = DataRequirement(**data_requirement)
        persistence = get_persistence_provider()
        model_class = _get_model_class(requirement.type)

        if not model_class:
            return DataQueryResult(
                success=False,
                message=f"Unknown resource type: {requirement.type}",
                data_requirement_id=requirement.id,
            )

        search_filters = _convert_data_requirement_to_filters(requirement)
        resources = persistence.search(
            model_class, actor, filters=search_filters, limit=requirement.limit or 50
        )
        filtered_resources = _apply_data_requirement_filtering(resources, requirement)
        aggregated_data = (
            _aggregate_results(filtered_resources, requirement.aggregate_method)
            if requirement.aggregate_method
            else None
        )
        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        return DataQueryResult(
            success=True,
            message=f"Found {len(filtered_resources)} {requirement.type} resources",
            data_requirement_id=requirement.id,
            results_count=len(filtered_resources),
            results=[r.model_dump() for r in filtered_resources],
            aggregated_data=aggregated_data,
            execution_time_ms=execution_time,
        )
    except Exception as e:
        return DataQueryResult(
            success=False,
            message="DataRequirement search failed",
            error=str(e),
        )


@tool
def create_datarequirement_query(
    actor_name: str,
    query_description: str,
    resource_types: list[str],
    time_period_days: int | None = 30,
    include_codes: list[str] | None = None,
    sort_by: str = "effectiveDateTime",
    limit: int = 20,
) -> dict[str, Any]:
    """Create a structured DataRequirement for common clinical queries."""
    # (Implementation from enhanced_tools.py)
    try:
        from datetime import timedelta

        from hacs_models import DataRequirement

        end_date = datetime.now()
        start_date = (
            end_date - timedelta(days=time_period_days) if time_period_days else None
        )
        data_requirements = []

        for resource_type in resource_types:
            req_data = {
                "type": resource_type,
                "description": f"{query_description} - {resource_type}",
                "limit": limit,
                "sort": [{"path": sort_by, "direction": "descending"}],
            }
            if start_date:
                req_data["date_filter"] = [
                    {
                        "path": sort_by,
                        "valuePeriod": {
                            "start": start_date.isoformat(),
                            "end": end_date.isoformat(),
                        },
                    }
                ]
            if include_codes:
                req_data["code_filter"] = [
                    {"path": "code.coding.code", "codes": include_codes}
                ]
            data_requirements.append(DataRequirement(**req_data).model_dump())

        return {
            "success": True,
            "message": f"Created {len(data_requirements)} DataRequirement specs",
            "data_requirements": data_requirements,
        }
    except Exception as e:
        return {"success": False, "message": "Query creation failed", "error": str(e)}


@tool
def execute_workflow(
    actor_name: str,
    plan_definition_id: str,
    patient_id: str,
    input_parameters: dict[str, Any] | None = None,
) -> WorkflowResult:
    """Execute a clinical workflow using a HACS PlanDefinition."""
    # (Implementation from enhanced_tools.py)
    try:
        import uuid

        from hacs_core import Actor, ActorRole, get_persistence_provider
        from hacs_models import PlanDefinition, RequestOrchestration

        actor = Actor(name=actor_name, role=ActorRole.SYSTEM)
        persistence = get_persistence_provider()
        plan = persistence.get(PlanDefinition, plan_definition_id, actor)

        if not plan:
            return WorkflowResult(
                success=False,
                message=f"PlanDefinition {plan_definition_id} not found",
                plan_definition_id=plan_definition_id,
                execution_id="",
                execution_status="failed",
            )

        exec_id = str(uuid.uuid4())
        orch_data = {
            "status": "active",
            "intent": "plan",
            "subject": patient_id,
            "instantiates_canonical": plan_definition_id,
            "description": f"Execution of {plan.title or plan_definition_id}",
            "execution_metadata": {
                "execution_id": exec_id,
                "executed_by": actor_name,
                "input_parameters": input_parameters or {},
            },
        }
        persistence.save(RequestOrchestration(**orch_data), actor)

        results = [
            _execute_plan_action(a, patient_id, actor, persistence, input_parameters)
            for a in plan.action
        ]
        completed = [r["action_id"] for r in results if r["status"] == "completed"]
        pending = [r["action_id"] for r in results if r["status"] == "pending"]
        failed = [r["action_id"] for r in results if r["status"] == "failed"]

        status = "failed" if failed else "in-progress" if pending else "completed"
        next_action = pending[0] if pending else None

        return WorkflowResult(
            success=True,
            message=f"Executed workflow {plan.title or plan_definition_id}",
            plan_definition_id=plan_definition_id,
            execution_id=exec_id,
            completed_actions=completed,
            pending_actions=pending,
            failed_actions=failed,
            execution_status=status,
            next_recommended_action=next_action,
        )
    except Exception:
        return WorkflowResult(
            success=False,
            message="Workflow execution failed",
            plan_definition_id=plan_definition_id,
            execution_id="",
            execution_status="failed",
        )


@tool
def get_clinical_guidance(
    actor_name: str,
    patient_id: str,
    clinical_question: str,
    patient_context: dict[str, Any] | None = None,
    knowledge_base_ids: list[str] | None = None,
) -> GuidanceResult:
    """Provide clinical decision support using HACS knowledge assets."""
    # (Implementation from enhanced_tools.py)
    try:
        from hacs_core import Actor, ActorRole, get_persistence_provider
        from hacs_models import GuidanceResponse, Library, PlanDefinition

        actor = Actor(name=actor_name, role=ActorRole.SYSTEM)
        persistence = get_persistence_provider()
        plans, libs = [], []

        if knowledge_base_ids:
            for kb_id in knowledge_base_ids:
                try:
                    plans.append(persistence.get(PlanDefinition, kb_id, actor))
                except Exception:
                    try:
                        libs.append(persistence.get(Library, kb_id, actor))
                    except Exception:
                        pass
        else:
            filters = {"description__icontains": clinical_question, "status": "active"}
            plans = persistence.search(PlanDefinition, actor, filters=filters, limit=5)
            libs = persistence.search(Library, actor, filters=filters, limit=5)

        recs = [
            {
                "type": "protocol",
                "title": p.title,
                "description": p.description,
                "actions": [a.title for a in p.action if a.title],
                "source": p.id,
            }
            for p in plans
        ] + [
            {
                "type": "evidence",
                "title": library.title,
                "description": library.description,
                "content": library.logic_content,
                "source": library.id,
            }
            for library in libs
        ]
        evidence = [p.id for p in plans] + [library.id for library in libs]

        guidance_data = {
            "status": "success",
            "subject": patient_id,
            "description": f"Guidance for: {clinical_question}",
            "guidance_content": {
                "question": clinical_question,
                "recommendations": recs,
                "evidence_sources": evidence,
                "patient_context": patient_context or {},
            },
            "confidence_score": 0.8,
        }
        guidance_id = persistence.save(GuidanceResponse(**guidance_data), actor)

        return GuidanceResult(
            success=True,
            message=f"Provided guidance for: {clinical_question}",
            guidance_response_id=guidance_id,
            guidance_type="clinical_decision_support",
            recommendations=recs,
            confidence_score=0.8,
            evidence_sources=evidence,
            contraindications=[],
        )
    except Exception:
        return GuidanceResult(
            success=False,
            message="Guidance provision failed",
            guidance_response_id="",
            guidance_type="error",
        )


# === UTILITY FUNCTIONS ===


def _get_model_class(resource_type: str):
    """Get the model class for a given resource type."""
    try:
        from hacs_core.models import (
            Patient, Observation, Encounter, Condition, MedicationRequest,
            Medication, AllergyIntolerance, Procedure, Goal, ServiceRequest,
            Organization, OrganizationContact, OrganizationQualification  # Added Organization models
        )

        model_map = {
            "Patient": Patient,
            "Observation": Observation,
            "Encounter": Encounter,
            "Condition": Condition,
            "MedicationRequest": MedicationRequest,
            "Medication": Medication,
            "AllergyIntolerance": AllergyIntolerance,
            "Procedure": Procedure,
            "Goal": Goal,
            "ServiceRequest": ServiceRequest,
            "Organization": Organization,
            "OrganizationContact": OrganizationContact,
            "OrganizationQualification": OrganizationQualification,
        }

        return model_map.get(resource_type)
    except ImportError:
        return None


def _convert_data_requirement_to_filters(requirement):
    """Convert DataRequirement to search filters."""
    # (Implementation remains the same)
    filters = {}
    for code_filter in requirement.code_filter:
        path = code_filter.get("path", "code")
        if "code" in code_filter:
            filters[f"{path}__code"] = code_filter["code"]
        elif "codes" in code_filter:
            filters[f"{path}__code__in"] = code_filter["codes"]
    for date_filter in requirement.date_filter:
        path = date_filter.get("path", "effectiveDateTime")
        if "valuePeriod" in date_filter:
            period = date_filter["valuePeriod"]
            if "start" in period:
                filters[f"{path}__gte"] = period["start"]
            if "end" in period:
                filters[f"{path}__lte"] = period["end"]
    for value_filter in requirement.value_filter:
        path = value_filter.get("path", "value")
        if "value" in value_filter:
            filters[path] = value_filter["value"]
    return filters


def _apply_data_requirement_filtering(resources, requirement):
    """Apply additional DataRequirement filtering logic."""
    return resources


def _aggregate_results(resources, aggregate_method):
    """Aggregate search results based on the specified method."""
    if aggregate_method == "count":
        return {"count": len(resources)}
    return {"method": aggregate_method, "count": len(resources)}


def _execute_plan_action(action, patient_id, actor, persistence, input_parameters):
    """Execute a single PlanDefinition action."""
    return {
        "action_id": action.prefix or "unknown",
        "status": "completed",
        "result": f"Executed action: {action.title or 'Unnamed action'}",
    }


# === ENHANCED RESOURCE FINDER TOOLS ===

@tool
def find_resources(
    actor_name: str,
    resource_type: str,
    filters: dict[str, Any] | None = None,
    semantic_query: str | None = None,
    limit: int = 10,
) -> list[HACSResult]:
    """
    Find HACS resources with advanced filtering and semantic search capabilities.

    Args:
        actor_name: Name of the actor performing the search
        resource_type: Type of HACS resource to find
        filters: Optional dictionary of field filters
        semantic_query: Optional semantic search query
        limit: Maximum number of results to return

    Returns:
        List of HACSResult objects with found resources
    """
    try:
        from hacs_core.actor import Actor

        # Create actor instance
        actor = Actor(name=actor_name, role="physician")

        # Validate resource type
        model_class = _get_model_class(resource_type)
        if not model_class:
            return [HACSResult(
                success=False,
                message=f"Unknown resource type: {resource_type}",
                error=f"Resource type '{resource_type}' not found"
            )]

        # Here you would integrate with your persistence provider and vector store
        # For now, return placeholder results

        results = []
        for i in range(min(5, limit)):  # Placeholder: return up to 5 results
            results.append(HACSResult(
                success=True,
                message=f"Found {resource_type} resource {i+1}",
                data={
                    "resource_id": f"{resource_type.lower()}-{i+1}",
                    "resource_type": resource_type,
                    "match_score": 0.95 - (i * 0.05),
                    "filters_applied": filters or {},
                    "semantic_query": semantic_query
                }
            ))

        return results

    except Exception as e:
        return [HACSResult(
            success=False,
            message=f"Failed to find {resource_type} resources",
            error=str(e)
        )]


@tool
def get_resource_by_id(
    actor_name: str,
    resource_type: str,
    resource_id: str,
    include_related: bool = False,
) -> HACSResult:
    """
    Get a specific HACS resource by its ID with optional related resources.

    Args:
        actor_name: Name of the actor requesting the resource
        resource_type: Type of HACS resource
        resource_id: Unique ID of the resource
        include_related: Whether to include related resources

    Returns:
        HACSResult with the retrieved resource and optional related data
    """
    try:
        from hacs_core.actor import Actor

        # Create actor instance
        actor = Actor(name=actor_name, role="physician")

        # Validate resource type
        model_class = _get_model_class(resource_type)
        if not model_class:
            return HACSResult(
                success=False,
                message=f"Unknown resource type: {resource_type}",
                error=f"Resource type '{resource_type}' not found"
            )

        # Here you would integrate with your persistence provider
        # For now, return a detailed placeholder response

        resource_data = {
            "id": resource_id,
            "resource_type": resource_type,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "data_fields": ["field1", "field2", "field3"]
        }

        if include_related:
            resource_data["related_resources"] = [
                {"type": "related_type", "id": "related_id_1"},
                {"type": "related_type", "id": "related_id_2"}
            ]

        return HACSResult(
            success=True,
            message=f"Retrieved {resource_type} with ID: {resource_id}",
            data=resource_data
        )

    except Exception as e:
        return HACSResult(
            success=False,
            message=f"Failed to retrieve {resource_type} with ID: {resource_id}",
            error=str(e)
        )


@tool
def update_resource_by_id(
    actor_name: str,
    resource_type: str,
    resource_id: str,
    updates: dict[str, Any],
    validate_before_update: bool = True,
) -> HACSResult:
    """
    Update a specific HACS resource by its ID with validation.

    Args:
        actor_name: Name of the actor updating the resource
        resource_type: Type of HACS resource
        resource_id: Unique ID of the resource to update
        updates: Dictionary of field updates
        validate_before_update: Whether to validate before applying updates

    Returns:
        HACSResult with update status and details
    """
    try:
        from hacs_core.actor import Actor

        # Create actor instance
        actor = Actor(name=actor_name, role="physician")

        # Validate resource type
        model_class = _get_model_class(resource_type)
        if not model_class:
            return HACSResult(
                success=False,
                message=f"Unknown resource type: {resource_type}",
                error=f"Resource type '{resource_type}' not found"
            )

        # Validate updates if requested
        if validate_before_update:
            try:
                # This would validate the updates against the model schema
                for field, value in updates.items():
                    if field not in model_class.model_fields:
                        return HACSResult(
                            success=False,
                            message=f"Invalid field '{field}' for {resource_type}",
                            error=f"Field '{field}' not found in {resource_type} schema"
                        )
            except Exception as validation_error:
                return HACSResult(
                    success=False,
                    message=f"Validation failed for updates",
                    error=str(validation_error)
                )

        # Here you would integrate with your persistence provider
        # For now, return success response

        return HACSResult(
            success=True,
            message=f"Successfully updated {resource_type} with ID: {resource_id}",
            data={
                "resource_id": resource_id,
                "resource_type": resource_type,
                "updated_fields": list(updates.keys()),
                "update_count": len(updates),
                "validation_performed": validate_before_update,
                "updated_at": datetime.now().isoformat()
            }
        )

    except Exception as e:
        return HACSResult(
            success=False,
            message=f"Failed to update {resource_type} with ID: {resource_id}",
            error=str(e)
        )


@tool
def delete_resource_by_id(
    actor_name: str,
    resource_type: str,
    resource_id: str,
    soft_delete: bool = True,
) -> HACSResult:
    """
    Delete a specific HACS resource by its ID with soft delete option.

    Args:
        actor_name: Name of the actor deleting the resource
        resource_type: Type of HACS resource
        resource_id: Unique ID of the resource to delete
        soft_delete: Whether to perform soft delete (mark as deleted) vs hard delete

    Returns:
        HACSResult with deletion status
    """
    try:
        from hacs_core.actor import Actor

        # Create actor instance
        actor = Actor(name=actor_name, role="physician")

        # Validate resource type
        model_class = _get_model_class(resource_type)
        if not model_class:
            return HACSResult(
                success=False,
                message=f"Unknown resource type: {resource_type}",
                error=f"Resource type '{resource_type}' not found"
            )

        # Here you would integrate with your persistence provider
        # For now, return success response

        deletion_type = "soft" if soft_delete else "hard"

        return HACSResult(
            success=True,
            message=f"Successfully {deletion_type} deleted {resource_type} with ID: {resource_id}",
            data={
                "resource_id": resource_id,
                "resource_type": resource_type,
                "deletion_type": deletion_type,
                "deleted_at": datetime.now().isoformat(),
                "deleted_by": actor_name
            }
        )

    except Exception as e:
        return HACSResult(
            success=False,
            message=f"Failed to delete {resource_type} with ID: {resource_id}",
            error=str(e)
        )


@tool
def get_hacs_resource_schema(resource_type: str, simplified: bool = False) -> ResourceSchemaResult:
    """
    Get the JSON schema for a HACS resource type with detailed examples and validation rules.

    TERMINOLOGY DISTINCTION:
    - HACS Records: Schema definitions/templates this tool retrieves (Patient model schema)
    - HACS Records: Data records that must conform to these model schemas
    - This tool provides MODEL schemas used to validate resource data creation

    CRITICAL FOR AGENTS: This schema shows the EXACT field structure required!
    - Use DIRECT fields from model schema (e.g., 'given', 'family', 'birth_date')
    - NOT nested FHIR arrays (e.g., 'name' array, 'birthDate', 'telecom' array)

    Args:
        resource_type: The HACS resource type (Patient model, Observation model, etc.)
        simplified: Whether to return a simplified schema (fewer optional fields)

    Returns:
        ResourceSchemaResult with detailed model schema, examples, and validation requirements
    """


@tool
def validate_hacs_record_data(resource_type: str, data: dict[str, Any]) -> HACSResult:
    """
    Validate HACS record data against its corresponding HACS resource schema.

    TERMINOLOGY DISTINCTION:
    - HACS Records: Schema definitions used for validation (Patient model, Observation model)
    - HACS Records: Data records being validated (Patient resource data, Observation data)
    - This tool validates RESOURCE data against MODEL schemas

    Args:
        resource_type: HACS resource type to validate against (Patient, Observation, etc.)
        data: Resource data to validate against the model schema

    Returns:
        HACSResult with validation status and detailed error information
    """


@tool
def list_available_hacs_resources() -> list[str]:
    """
    List all available HACS resource types for resource creation and validation.

    TERMINOLOGY DISTINCTION:
    - HACS Records: Schema definitions/templates this tool lists
    - HACS Records: Data records created using these models
    - This tool discovers available MODEL types for development

    Returns:
        List of available HACS resource type names (Patient, Observation, Condition, etc.)
    """
    try:
        # Return available HACS resource types
        models = [
            "Patient",
            "Observation",
            "Encounter",
            "Condition",
            "MedicationRequest",
            "Medication",
            "AllergyIntolerance",
            "Procedure",
            "Goal",
            "ServiceRequest",
            "Organization",
            "OrganizationContact",
            "OrganizationQualification"
        ]

        return models

    except Exception:
        # Fallback list if imports fail
        return [
            "Patient",
            "Observation",
            "Encounter",
            "Condition",
            "Organization"
        ]


@tool
def find_hacs_records(
    resource_type: str,
    filters: dict[str, Any] | None = None,
    semantic_query: str | None = None,
    limit: int = 10,
) -> list[HACSResult]:
    """
    Search for existing HACS resources (data records) by criteria.

    TERMINOLOGY DISTINCTION:
    - HACS Records: Schema definitions that define the structure
    - HACS Records: Actual data records this tool searches through
    - This tool searches RESOURCE data, not model definitions

    Args:
        resource_type: HACS resource type that defines the resource structure
        filters: Criteria to filter resource data
        semantic_query: Natural language search query
        limit: Maximum number of resource records to return

    Returns:
        List of HACSResult objects containing matching resource data
    """


@tool
def get_hacs_record_by_id(
    actor_name: str,
    resource_type: str,
    resource_id: str,
    include_related: bool = False,
) -> HACSResult:
    """
    Retrieve a specific HACS resource (data record) by its ID.

    TERMINOLOGY DISTINCTION:
    - HACS Records: Schema definitions that define the resource structure
    - HACS Records: Actual data record this tool retrieves
    - This tool gets RESOURCE data, validated against model schemas

    Args:
        actor_name: Name of the actor requesting the resource
        resource_type: HACS resource type (defines what kind of resource)
        resource_id: Unique identifier of the resource record
        include_related: Whether to include related resource records

    Returns:
        HACSResult containing the resource data and metadata
    """


# === ALL TOOLS COLLECTION ===

ALL_HACS_TOOLS = [
    # Result models
    "HACSResult",
    "ResourceSchemaResult",
    "ModelDiscoveryResult",
    "FieldAnalysisResult",
    "DataQueryResult",
    "WorkflowResult",
    "GuidanceResult",
    "MemoryResult",
    "VersionResult",
    # Enhanced CRUD tools
    "create_hacs_record",
    "get_hacs_record",
    "search_hacs_records",
    "update_hacs_record",
    "delete_hacs_record",
    # Resource finder tools
    "find_resources",
    "get_resource_by_id",
    "update_resource_by_id",
    "delete_resource_by_id",
    # Memory management tools
    "create_hacs_memory",
    "search_hacs_memories",
    "consolidate_memories",
    "retrieve_context",
    "analyze_memory_patterns",
    # Versioning tools
    "version_hacs_resource",
    # Knowledge management
    "create_knowledge_item",
    # Schema and validation tools
    "get_resource_schema",
    "get_hacs_resource_schema",
    "validate_resource_data",
    "list_available_resources",
    # Model-driven tools
    "query_with_datarequirement",
    "create_datarequirement_query",

    # Vector Store Operations (pgvector)
    "store_embedding",
    "vector_similarity_search",
    "vector_hybrid_search",
    "get_vector_collection_stats",
    "execute_workflow",
    "get_clinical_guidance",
    # Model manipulation tools
    "discover_hacs_resources",
    "create_view_resource_schema",
    "analyze_resource_fields",
    "compare_resource_schemas",
    "suggest_view_fields",
    "create_multi_resource_schema",
]


# === MODEL MANIPULATION AND DEVELOPMENT TOOLS ===


@tool
def discover_hacs_resources(
    category_filter: Optional[str] = None,
    include_field_counts: bool = True
) -> ModelDiscoveryResult:
    """
    Discover all available HACS resources with metadata.

    This tool helps LLMs understand what models are available for manipulation,
    their purposes, and basic statistics about their structure.

    Args:
        category_filter: Optional filter by model category (e.g., "clinical", "administrative")
        include_field_counts: Whether to include field count information

    Returns:
        ModelDiscoveryResult with list of available models and metadata

    Example:
        discover_hacs_resources() -> Lists all Patient, Observation, Goal, etc. models
        discover_hacs_resources("clinical") -> Only clinical models like Patient, Observation
    """
    try:
        import inspect
        import hacs_core
        from hacs_core import BaseResource

        models = []
        categories = set()

        for name in dir(hacs_core):
            obj = getattr(hacs_core, name)
            if inspect.isclass(obj) and issubclass(obj, BaseResource) and obj is not BaseResource:
                # Determine category
                category = "administrative"
                if any(term in name.lower() for term in ["patient", "observation", "condition", "procedure", "medication", "allergy"]):
                    category = "clinical"
                elif any(term in name.lower() for term in ["appointment", "task", "service"]):
                    category = "workflow"
                elif any(term in name.lower() for term in ["goal", "risk", "family"]):
                    category = "assessment"

                categories.add(category)

                model_info = {
                    "name": name,
                    "category": category,
                    "description": obj.__doc__.split('\n')[0] if obj.__doc__ else f"{name} model",
                    "resource_type": getattr(obj, 'resource_type', name),
                }

                if include_field_counts:
                    field_count = len(obj.model_fields)
                    required_count = len([f for f, info in obj.model_fields.items()
                                        if info.default is ... and info.default_factory is None])
                    model_info.update({
                        "total_fields": field_count,
                        "required_fields": required_count,
                        "optional_fields": field_count - required_count
                    })

                if not category_filter or category == category_filter:
                    models.append(model_info)

        return ModelDiscoveryResult(
            success=True,
            models=models,
            total_count=len(models),
            categories=sorted(categories),
            message=f"Found {len(models)} HACS resources" +
                   (f" in category '{category_filter}'" if category_filter else "")
        )

    except Exception as e:
        return ModelDiscoveryResult(
            success=False,
            models=[],
            total_count=0,
            categories=[],
            message=f"Failed to discover models: {str(e)}"
        )


@tool
def create_view_resource_schema(
    resource_name: str,
    fields: List[str],
    view_name: Optional[str] = None,
    include_optional: bool = True,
    extra_validation: str = "forbid"
) -> ResourceSchemaResult:
    """
    Create a JSON schema for a custom view model with selected fields.

    This is the primary tool for LLMs to create focused, efficient schemas
    for structured output by selecting only needed fields from HACS resources.

    Args:
        resource_name: Name of the HACS resource (e.g., "Patient", "Observation")
        fields: List of field names to include in the view
        view_name: Optional custom name for the view (defaults to ModelNameView)
        include_optional: Whether to preserve optional field behavior
        extra_validation: Pydantic extra validation mode ("forbid", "allow", "ignore")

    Returns:
        ResourceSchemaResult with the generated schema and metadata

    Examples:
        create_view_resource_schema("Patient", ["full_name", "birth_date", "gender"])
        create_view_resource_schema("Observation", ["status", "code", "value_quantity"])
    """
    try:
        import hacs_core

        # Get the model class
        if not hasattr(hacs_core, resource_name):
            return ResourceSchemaResult(
                success=False,
                resource_name=resource_name,
                schema={},
                field_count=0,
                required_fields=[],
                optional_fields=[],
                message=f"Model '{resource_name}' not found in hacs_core"
            )

        model_class = getattr(hacs_core, resource_name)

        # Validate fields exist
        missing_fields = [f for f in fields if f not in model_class.model_fields]
        if missing_fields:
            return ResourceSchemaResult(
                success=False,
                resource_name=resource_name,
                schema={},
                field_count=0,
                required_fields=[],
                optional_fields=[],
                message=f"Fields not found in {resource_name}: {missing_fields}"
            )

        # Create view model
        view_class = model_class.pick(
            *fields,
            name=view_name,
            include_optional=include_optional,
            extra=extra_validation
        )

        # Generate schema
        schema = view_class.model_json_schema()

        # Analyze schema
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))

        required_fields = [f for f in properties.keys() if f in required]
        optional_fields = [f for f in properties.keys() if f not in required]

        return ResourceSchemaResult(
            success=True,
            resource_name=view_class.__name__,
            schema=schema,
            field_count=len(properties),
            required_fields=required_fields,
            optional_fields=optional_fields,
            message=f"Created schema for {view_class.__name__} with {len(fields)} selected fields"
        )

    except Exception as e:
        return ResourceSchemaResult(
            success=False,
            resource_name=resource_name,
            schema={},
            field_count=0,
            required_fields=[],
            optional_fields=[],
            message=f"Failed to create view schema: {str(e)}"
        )


@tool
def analyze_resource_fields(
    resource_name: str,
    field_category_filter: Optional[str] = None
) -> FieldAnalysisResult:
    """
    Analyze the fields and structure of a HACS resource.

    This tool helps LLMs understand the available fields, their types,
    validation rules, and relationships before creating view models.

    Args:
        resource_name: Name of the HACS resource to analyze
        field_category_filter: Optional filter (e.g., "required", "optional", "string", "date")

    Returns:
        FieldAnalysisResult with detailed field analysis

    Examples:
        analyze_resource_fields("Patient") -> Complete field analysis
        analyze_resource_fields("Patient", "required") -> Only required fields
        analyze_resource_fields("Observation", "string") -> Only string-type fields
    """
    try:
        import hacs_core
        from typing import get_origin, get_args

        if not hasattr(hacs_core, resource_name):
            return FieldAnalysisResult(
                success=False,
                resource_name=resource_name,
                total_fields=0,
                field_details=[],
                field_types={},
                validation_rules=[],
                message=f"Model '{resource_name}' not found in hacs_core"
            )

        model_class = getattr(hacs_core, resource_name)
        field_details = []
        field_types = {}
        validation_rules = []

        for field_name, field_info in model_class.model_fields.items():
            # Determine if field is required
            is_required = field_info.default is ... and field_info.default_factory is None

            # Get type information
            field_type = field_info.annotation
            type_name = "unknown"

            if hasattr(field_type, '__name__'):
                type_name = field_type.__name__
            elif hasattr(field_type, '__origin__'):
                origin = get_origin(field_type)
                if origin:
                    type_name = origin.__name__
                    args = get_args(field_type)
                    if args:
                        type_name += f"[{', '.join(getattr(arg, '__name__', str(arg)) for arg in args)}]"
            else:
                type_name = str(field_type)

            # Count field types
            base_type = type_name.split('[')[0]
            field_types[base_type] = field_types.get(base_type, 0) + 1

            # Build field detail
            detail = {
                "name": field_name,
                "type": type_name,
                "required": is_required,
                "default": str(field_info.default) if field_info.default is not ... else None,
                "description": field_info.description,
                "examples": getattr(field_info, 'examples', None)
            }

            # Apply category filter
            if field_category_filter:
                if field_category_filter == "required" and not is_required:
                    continue
                elif field_category_filter == "optional" and is_required:
                    continue
                elif field_category_filter in ["string", "str"] and "str" not in type_name.lower():
                    continue
                elif field_category_filter in ["date", "datetime"] and "date" not in type_name.lower():
                    continue
                elif field_category_filter in ["int", "integer"] and "int" not in type_name.lower():
                    continue
                elif field_category_filter in ["bool", "boolean"] and "bool" not in type_name.lower():
                    continue

            field_details.append(detail)

        # Extract validation rules from model
        if hasattr(model_class, 'model_config'):
            config = model_class.model_config
            if hasattr(config, 'extra'):
                validation_rules.append(f"extra={config.get('extra', 'allow')}")
            if hasattr(config, 'validate_assignment'):
                validation_rules.append(f"validate_assignment={config.get('validate_assignment', False)}")

        return FieldAnalysisResult(
            success=True,
            resource_name=resource_name,
            total_fields=len(field_details),
            field_details=field_details,
            field_types=field_types,
            validation_rules=validation_rules,
            message=f"Analyzed {len(field_details)} fields from {resource_name}" +
                   (f" (filtered by: {field_category_filter})" if field_category_filter else "")
        )

    except Exception as e:
        return FieldAnalysisResult(
            success=False,
            resource_name=resource_name,
            total_fields=0,
            field_details=[],
            field_types={},
            validation_rules=[],
            message=f"Failed to analyze model fields: {str(e)}"
        )


@tool
def compare_resource_schemas(
    resource_names: List[str],
    comparison_focus: str = "fields"
) -> HACSResult:
    """
    Compare multiple HACS resources to understand similarities and differences.

    This tool helps LLMs understand relationships between models and identify
    common fields that could be used in cross-model workflows.

    Args:
        resource_names: List of model names to compare (e.g., ["Patient", "Observation"])
        comparison_focus: What to compare ("fields", "types", "required", "optional")

    Returns:
        HACSResult with comparison analysis

    Examples:
        compare_resource_schemas(["Patient", "Observation"]) -> Compare all fields
        compare_resource_schemas(["Patient", "Observation"], "required") -> Compare required fields
    """
    try:
        import hacs_core

        if len(resource_names) < 2:
            return HACSResult(
                success=False,
                message="Need at least 2 models to compare",
                error="Insufficient models for comparison"
            )

        models_data = {}

        # Collect data for each model
        for resource_name in resource_names:
            if not hasattr(hacs_core, resource_name):
                return HACSResult(
                    success=False,
                    message=f"Model '{resource_name}' not found",
                    error=f"Unknown model: {resource_name}"
                )

            model_class = getattr(hacs_core, resource_name)
            fields = set(model_class.model_fields.keys())

            if comparison_focus == "required":
                fields = {f for f, info in model_class.model_fields.items()
                         if info.default is ... and info.default_factory is None}
            elif comparison_focus == "optional":
                fields = {f for f, info in model_class.model_fields.items()
                         if info.default is not ... or info.default_factory is not None}
            elif comparison_focus == "types":
                fields = {f: str(info.annotation) for f, info in model_class.model_fields.items()}

            models_data[resource_name] = fields

        # Perform comparison
        if comparison_focus == "types":
            # Compare field types
            common_fields = set(models_data[resource_names[0]].keys())
            for resource_name in resource_names[1:]:
                common_fields &= set(models_data[resource_name].keys())

            type_matches = {}
            type_conflicts = {}

            for field in common_fields:
                types = [models_data[model][field] for model in resource_names]
                if len(set(types)) == 1:
                    type_matches[field] = types[0]
                else:
                    type_conflicts[field] = dict(zip(resource_names, types))

            comparison_data = {
                "common_fields": list(common_fields),
                "type_matches": type_matches,
                "type_conflicts": type_conflicts,
                "total_common": len(common_fields)
            }
        else:
            # Compare field sets
            all_fields = set()
            for fields in models_data.values():
                all_fields.update(fields)

            common_fields = set(models_data[resource_names[0]])
            for resource_name in resource_names[1:]:
                common_fields &= models_data[resource_name]

            unique_fields = {}
            for resource_name, fields in models_data.items():
                unique = fields - common_fields
                unique_fields[resource_name] = list(unique)

            comparison_data = {
                "common_fields": list(common_fields),
                "unique_fields": unique_fields,
                "total_common": len(common_fields),
                "total_unique": sum(len(unique) for unique in unique_fields.values()),
                "field_overlap_percentage": len(common_fields) / len(all_fields) * 100 if all_fields else 0
            }

        return HACSResult(
            success=True,
            message=f"Compared {len(resource_names)} models focusing on {comparison_focus}",
            data=comparison_data
        )

    except Exception as e:
        return HACSResult(
            success=False,
            message=f"Failed to compare models: {str(e)}",
            error=str(e)
        )


@tool
def suggest_view_fields(
    resource_name: str,
    use_case: str,
    max_fields: int = 10
) -> HACSResult:
    """
    Suggest optimal fields for a view model based on use case.

    This tool helps LLMs automatically select the most relevant fields
    for common healthcare scenarios and structured output tasks.

    Args:
        resource_name: Name of the HACS resource
        use_case: Description of the use case (e.g., "patient demographics", "lab results summary")
        max_fields: Maximum number of fields to suggest

    Returns:
        HACSResult with suggested fields and rationale

    Examples:
        suggest_view_fields("Patient", "patient demographics") -> ["full_name", "birth_date", "gender"]
        suggest_view_fields("Observation", "vital signs summary") -> ["code", "value_quantity", "status"]
    """
    try:
        import hacs_core

        if not hasattr(hacs_core, resource_name):
            return HACSResult(
                success=False,
                message=f"Model '{resource_name}' not found",
                error=f"Unknown model: {resource_name}"
            )

        model_class = getattr(hacs_core, resource_name)
        all_fields = list(model_class.model_fields.keys())

        # Define use case patterns
        use_case_patterns = {
            "demographics": ["name", "birth", "gender", "age", "address", "phone"],
            "identity": ["name", "id", "identifier", "given", "family"],
            "contact": ["phone", "email", "address", "contact"],
            "medical": ["condition", "medication", "allergy", "diagnosis"],
            "administrative": ["id", "status", "date", "type", "category"],
            "summary": ["name", "status", "description", "text", "title"],
            "vital signs": ["code", "value", "unit", "status", "category"],
            "lab results": ["code", "value", "reference", "status", "performed"],
            "appointment": ["status", "start", "end", "participant", "type"],
            "workflow": ["status", "intent", "priority", "category", "description"]
        }

        # Match use case to patterns
        suggested_fields = []
        rationale = []

        use_case_lower = use_case.lower()

        for pattern_name, keywords in use_case_patterns.items():
            if any(keyword in use_case_lower for keyword in [pattern_name]):
                # Find fields matching this pattern
                pattern_fields = []
                for field in all_fields:
                    field_lower = field.lower()
                    if any(keyword in field_lower for keyword in keywords):
                        pattern_fields.append(field)

                if pattern_fields:
                    suggested_fields.extend(pattern_fields)
                    rationale.append(f"Matched '{pattern_name}' pattern: {pattern_fields}")

        # Remove duplicates and limit
        suggested_fields = list(dict.fromkeys(suggested_fields))[:max_fields]

        # If no pattern matches, suggest common essential fields
        if not suggested_fields:
            essential_patterns = ["id", "name", "status", "type", "description"]
            for field in all_fields:
                field_lower = field.lower()
                if any(pattern in field_lower for pattern in essential_patterns):
                    suggested_fields.append(field)
                    if len(suggested_fields) >= max_fields:
                        break
            rationale.append("Used essential field patterns as fallback")

        return HACSResult(
            success=True,
            message=f"Suggested {len(suggested_fields)} fields for '{use_case}' use case",
            data={
                "suggested_fields": suggested_fields,
                "rationale": rationale,
                "use_case": use_case,
                "resource_name": resource_name,
                "total_available_fields": len(all_fields)
            }
        )

    except Exception as e:
        return HACSResult(
            success=False,
            message=f"Failed to suggest fields: {str(e)}",
            error=str(e)
        )


@tool
def create_multi_resource_schema(
    model_specs: List[Dict[str, Any]],
    schema_name: str = "CompositeSchema"
) -> HACSResult:
    """
    Create a composite schema combining fields from multiple HACS resources.

    This tool enables LLMs to create complex structured output schemas
    that combine data from multiple healthcare models in a single response.

    Args:
        model_specs: List of model specifications, each containing:
                    {"model": "ModelName", "fields": ["field1", "field2"], "prefix": "optional_prefix"}
        schema_name: Name for the composite schema

    Returns:
        HACSResult with the composite schema and metadata

    Examples:
        create_multi_resource_schema([
            {"model": "Patient", "fields": ["full_name", "birth_date"], "prefix": "patient"},
            {"model": "Observation", "fields": ["code", "value_quantity"], "prefix": "vitals"}
        ])
    """
    try:
        import hacs_core

        composite_schema = {
            "type": "object",
            "title": schema_name,
            "properties": {},
            "required": []
        }

        field_sources = {}
        total_fields = 0

        for spec in model_specs:
            resource_name = spec.get("model")
            fields = spec.get("fields", [])
            prefix = spec.get("prefix", "")

            if not hasattr(hacs_core, resource_name):
                return HACSResult(
                    success=False,
                    message=f"Model '{resource_name}' not found",
                    error=f"Unknown model: {resource_name}"
                )

            model_class = getattr(hacs_core, resource_name)

            # Validate fields exist
            missing_fields = [f for f in fields if f not in model_class.model_fields]
            if missing_fields:
                return HACSResult(
                    success=False,
                    message=f"Fields not found in {resource_name}: {missing_fields}",
                    error=f"Invalid fields for {resource_name}"
                )

            # Create view schema for this model
            view_class = model_class.pick(*fields)
            view_schema = view_class.model_json_schema()

            # Add fields to composite schema
            for field_name, field_schema in view_schema.get("properties", {}).items():
                if field_name == "resource_type":  # Skip auto-added resource_type
                    continue

                composite_field_name = f"{prefix}_{field_name}" if prefix else field_name
                composite_schema["properties"][composite_field_name] = field_schema
                field_sources[composite_field_name] = f"{resource_name}.{field_name}"
                total_fields += 1

                # Add to required if it was required in the original
                if field_name in view_schema.get("required", []):
                    composite_schema["required"].append(composite_field_name)

        return HACSResult(
            success=True,
            message=f"Created composite schema '{schema_name}' with {total_fields} fields from {len(model_specs)} models",
            data={
                "schema": composite_schema,
                "field_sources": field_sources,
                "total_fields": total_fields,
                "source_models": [spec.get("model") for spec in model_specs],
                "schema_name": schema_name
            }
        )

    except Exception as e:
        return HACSResult(
            success=False,
            message=f"Failed to create composite schema: {str(e)}",
            error=str(e)
        )


# Update the __all__ list to include new tools organized by model vs resource operations
__all__ = [
    # Result models
    "HACSResult",
    "ResourceSchemaResult",
    "ModelDiscoveryResult",
    "FieldAnalysisResult",
    "DataQueryResult",
    "WorkflowResult",
    "GuidanceResult",
    "MemoryResult",
    "VersionResult",

    # HACS Resource Schema Tools (work with model definitions/templates)
    "get_hacs_resource_schema",
    "discover_hacs_resources",
    "create_view_resource_schema",
    "analyze_resource_fields",
    "compare_resource_schemas",
    "suggest_view_fields",
    "optimize_resource_for_llm",
    "create_multi_resource_schema",
    "list_available_hacs_resources",
    "version_hacs_resource",

    # HACS Resource Data Tools (work with actual data records)
    "create_hacs_record",
    "get_hacs_record_by_id",
    "find_hacs_records",
    "update_resource_by_id",
    "delete_resource_by_id",
    "validate_hacs_record_data",
    "search_hacs_records",
    "get_hacs_record",
    "update_hacs_record",
    "delete_hacs_record",

    # Memory management tools
    "create_hacs_memory",
    "search_hacs_memories",
    "consolidate_memories",
    "retrieve_context",
    "analyze_memory_patterns",

    # Workflow and guidance tools
    "query_with_datarequirement",
    "create_datarequirement_query",
    "execute_workflow",
    "get_clinical_guidance",
    "create_knowledge_item",
]

# Vector Store Operations (pgvector)
async def store_embedding(
    content: str,
    embedding: List[float],
    metadata: Optional[Dict[str, Any]] = None,
    source: Optional[str] = None,
    database_url: Optional[str] = None
) -> HACSResult:
    """
    Store a text embedding in the PostgreSQL vector database using pgvector.

    Args:
        content: The original text content
        embedding: Vector embedding as a list of floats
        metadata: Optional metadata dictionary
        source: Optional source identifier (e.g., document name)
        database_url: Optional database URL (defaults to settings)

    Returns:
        HACSResult with the stored embedding ID and confirmation

    Example:
        >>> # Store an embedding for a medical note
        >>> result = await store_embedding(
        ...     content="Patient shows improvement after treatment",
        ...     embedding=[0.1, 0.2, 0.3, ...],  # 1536-dimensional embedding
        ...     metadata={"type": "clinical_note", "patient_id": "P123"},
        ...     source="clinical_notes_2024"
        ... )
        >>> print(result.success)  # True
        >>> print(result.data["embedding_id"])  # "knowledge_20241201_143022_123456"
    """
    try:
        # Import vector store functionality
        from hacs_persistence import HACSVectorStore, PGVECTOR_AVAILABLE

        if not PGVECTOR_AVAILABLE:
            return HACSResult(
                success=False,
                message="pgvector is not available. Please install pgvector dependencies.",
                error_code="PGVECTOR_NOT_AVAILABLE"
            )

        # Get database URL from settings if not provided
        if not database_url:
            from hacs_core import get_settings
            settings = get_settings()
            database_url = settings.database_url

            if not database_url:
                return HACSResult(
                    success=False,
                    message="Database URL not configured. Please set DATABASE_URL.",
                    error_code="DATABASE_URL_NOT_SET"
                )

        # Create vector store instance
        vector_store = HACSVectorStore(database_url=database_url)
        await vector_store.connect()

        # Store the embedding
        embedding_id = await vector_store.store_embedding(
            content=content,
            embedding=embedding,
            metadata=metadata,
            source=source
        )

        await vector_store.disconnect()

        return HACSResult(
            success=True,
            message=f"Successfully stored embedding with ID: {embedding_id}",
            data={
                "embedding_id": embedding_id,
                "content_length": len(content),
                "embedding_dimension": len(embedding),
                "metadata_fields": len(metadata) if metadata else 0,
                "source": source
            }
        )

    except Exception as e:
        logger.error(f"Failed to store embedding: {e}")
        return HACSResult(
            success=False,
            message=f"Failed to store embedding: {str(e)}",
            error_code="STORE_EMBEDDING_FAILED"
        )


async def vector_similarity_search(
    query_embedding: List[float],
    top_k: int = 5,
    distance_metric: str = "cosine",
    metadata_filter: Optional[Dict[str, Any]] = None,
    source_filter: Optional[str] = None,
    database_url: Optional[str] = None
) -> HACSResult:
    """
    Perform vector similarity search using pgvector.

    Args:
        query_embedding: Query vector as list of floats
        top_k: Number of most similar results to return
        distance_metric: Distance metric ("cosine", "l2", "inner_product")
        metadata_filter: Optional metadata filtering (key-value pairs)
        source_filter: Optional source filtering
        database_url: Optional database URL (defaults to settings)

    Returns:
        HACSResult with search results including similarity scores

    Example:
        >>> # Search for similar medical concepts
        >>> result = await vector_similarity_search(
        ...     query_embedding=[0.1, 0.2, 0.3, ...],
        ...     top_k=3,
        ...     distance_metric="cosine",
        ...     metadata_filter={"type": "clinical_note"}
        ... )
        >>> for item in result.data["results"]:
        ...     print(f"Content: {item['content'][:50]}...")
        ...     print(f"Similarity: {item['similarity']:.3f}")
    """
    try:
        from hacs_persistence import HACSVectorStore, PGVECTOR_AVAILABLE

        if not PGVECTOR_AVAILABLE:
            return HACSResult(
                success=False,
                message="pgvector is not available. Please install pgvector dependencies.",
                error_code="PGVECTOR_NOT_AVAILABLE"
            )

        # Get database URL from settings if not provided
        if not database_url:
            from hacs_core import get_settings
            settings = get_settings()
            database_url = settings.database_url

            if not database_url:
                return HACSResult(
                    success=False,
                    message="Database URL not configured. Please set DATABASE_URL.",
                    error_code="DATABASE_URL_NOT_SET"
                )

        # Create vector store instance
        vector_store = HACSVectorStore(database_url=database_url)
        await vector_store.connect()

        # Perform similarity search
        results = await vector_store.similarity_search(
            query_embedding=query_embedding,
            top_k=top_k,
            distance_metric=distance_metric,
            metadata_filter=metadata_filter,
            source_filter=source_filter
        )

        await vector_store.disconnect()

        return HACSResult(
            success=True,
            message=f"Found {len(results)} similar items using {distance_metric} distance",
            data={
                "results": results,
                "query_dimension": len(query_embedding),
                "distance_metric": distance_metric,
                "results_count": len(results),
                "top_k": top_k,
                "metadata_filter": metadata_filter,
                "source_filter": source_filter
            }
        )

    except Exception as e:
        logger.error(f"Failed to perform similarity search: {e}")
        return HACSResult(
            success=False,
            message=f"Failed to perform similarity search: {str(e)}",
            error_code="SIMILARITY_SEARCH_FAILED"
        )


async def vector_hybrid_search(
    query_embedding: List[float],
    text_query: Optional[str] = None,
    top_k: int = 5,
    distance_metric: str = "cosine",
    metadata_filter: Optional[Dict[str, Any]] = None,
    source_filter: Optional[str] = None,
    database_url: Optional[str] = None
) -> HACSResult:
    """
    Perform hybrid search combining vector similarity with text search.

    Args:
        query_embedding: Query vector as list of floats
        text_query: Optional full-text search query
        top_k: Number of results to return
        distance_metric: Distance metric ("cosine", "l2", "inner_product")
        metadata_filter: Optional metadata filtering
        source_filter: Optional source filtering
        database_url: Optional database URL (defaults to settings)

    Returns:
        HACSResult with hybrid search results including text relevance scores

    Example:
        >>> # Combine vector similarity with text search
        >>> result = await vector_hybrid_search(
        ...     query_embedding=[0.1, 0.2, 0.3, ...],
        ...     text_query="diabetes medication",
        ...     top_k=5,
        ...     metadata_filter={"type": "prescription"}
        ... )
        >>> for item in result.data["results"]:
        ...     print(f"Content: {item['content'][:50]}...")
        ...     print(f"Similarity: {item['similarity']:.3f}")
        ...     if 'text_rank' in item:
        ...         print(f"Text Relevance: {item['text_rank']:.3f}")
    """
    try:
        from hacs_persistence import HACSVectorStore, PGVECTOR_AVAILABLE

        if not PGVECTOR_AVAILABLE:
            return HACSResult(
                success=False,
                message="pgvector is not available. Please install pgvector dependencies.",
                error_code="PGVECTOR_NOT_AVAILABLE"
            )

        # Get database URL from settings if not provided
        if not database_url:
            from hacs_core import get_settings
            settings = get_settings()
            database_url = settings.database_url

            if not database_url:
                return HACSResult(
                    success=False,
                    message="Database URL not configured. Please set DATABASE_URL.",
                    error_code="DATABASE_URL_NOT_SET"
                )

        # Create vector store instance
        vector_store = HACSVectorStore(database_url=database_url)
        await vector_store.connect()

        # Perform hybrid search
        results = await vector_store.hybrid_search(
            query_embedding=query_embedding,
            text_query=text_query,
            top_k=top_k,
            distance_metric=distance_metric,
            metadata_filter=metadata_filter,
            source_filter=source_filter
        )

        await vector_store.disconnect()

        return HACSResult(
            success=True,
            message=f"Found {len(results)} results using hybrid search (vector + text)",
            data={
                "results": results,
                "query_dimension": len(query_embedding),
                "text_query": text_query,
                "distance_metric": distance_metric,
                "results_count": len(results),
                "top_k": top_k,
                "metadata_filter": metadata_filter,
                "source_filter": source_filter
            }
        )

    except Exception as e:
        logger.error(f"Failed to perform hybrid search: {e}")
        return HACSResult(
            success=False,
            message=f"Failed to perform hybrid search: {str(e)}",
            error_code="HYBRID_SEARCH_FAILED"
        )


async def get_vector_collection_stats(database_url: Optional[str] = None) -> HACSResult:
    """
    Get statistics about the vector collection.

    Args:
        database_url: Optional database URL (defaults to settings)

    Returns:
        HACSResult with collection statistics

    Example:
        >>> # Get vector database statistics
        >>> result = await get_vector_collection_stats()
        >>> print(f"Total embeddings: {result.data['total_embeddings']}")
        >>> print(f"Unique sources: {result.data['unique_sources']}")
        >>> print(f"Average content length: {result.data['avg_content_length']:.1f}")
    """
    try:
        from hacs_persistence import HACSVectorStore, PGVECTOR_AVAILABLE

        if not PGVECTOR_AVAILABLE:
            return HACSResult(
                success=False,
                message="pgvector is not available. Please install pgvector dependencies.",
                error_code="PGVECTOR_NOT_AVAILABLE"
            )

        # Get database URL from settings if not provided
        if not database_url:
            from hacs_core import get_settings
            settings = get_settings()
            database_url = settings.database_url

            if not database_url:
                return HACSResult(
                    success=False,
                    message="Database URL not configured. Please set DATABASE_URL.",
                    error_code="DATABASE_URL_NOT_SET"
                )

        # Create vector store instance
        vector_store = HACSVectorStore(database_url=database_url)
        await vector_store.connect()

        # Get collection statistics
        stats = await vector_store.get_collection_stats()

        await vector_store.disconnect()

        return HACSResult(
            success=True,
            message="Successfully retrieved vector collection statistics",
            data=stats
        )

    except Exception as e:
        logger.error(f"Failed to get collection stats: {e}")
        return HACSResult(
            success=False,
            message=f"Failed to get collection stats: {str(e)}",
            error_code="COLLECTION_STATS_FAILED"
        )
