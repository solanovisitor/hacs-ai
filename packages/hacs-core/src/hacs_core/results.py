"""
HACS Results - Standard result types for healthcare AI operations

This module provides comprehensive result models for all HACS operations,
ensuring consistent response formats across all tools and services.
All result types follow healthcare-specific patterns and include
proper audit trails, timestamps, and error handling.

Key Features:
    🏥 Healthcare-focused result types
    📊 Consistent structure across all operations
    🔍 Detailed metadata and provenance tracking
    ⚡ Optimized for AI agent consumption
    🛡️ Built-in error handling and validation
    📋 Audit-ready with timestamps and actor tracking

Author: HACS Development Team
License: MIT
Version: 0.3.0
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# === BASE RESULT TYPES ===

class HACSResult(BaseModel):
    """
    Standard result format for basic HACS tool operations.
    
    This is the foundational result type that provides consistent
    structure for all HACS operations with healthcare-specific context.
    """
    
    success: bool = Field(description="Whether the operation succeeded")
    message: str = Field(description="Human-readable result message with clinical context")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Operation specific data payload")
    error: Optional[str] = Field(default=None, description="Detailed error message if operation failed")
    timestamp: datetime = Field(default_factory=datetime.now, description="Operation execution timestamp")
    actor_id: Optional[str] = Field(default=None, description="ID of the actor who performed the operation")
    audit_trail: Optional[Dict[str, Any]] = Field(default=None, description="Audit information for compliance")


# === RESOURCE MANAGEMENT RESULTS ===

class ResourceSchemaResult(BaseModel):
    """
    Result for healthcare resource schema operations.
    
    Provides comprehensive schema information for HACS resources
    including FHIR compliance details and validation rules.
    """
    
    success: bool = Field(description="Whether schema operation succeeded")
    resource_type: str = Field(description="Type of healthcare resource (Patient, Observation, etc.)")
    schema: Dict[str, Any] = Field(description="JSON schema definition for the resource")
    fhir_compliance: bool = Field(description="Whether the schema is FHIR R4/R5 compliant")
    required_fields: List[str] = Field(description="List of required fields for validation")
    optional_fields: List[str] = Field(description="List of optional fields available")
    field_count: int = Field(description="Total number of fields in the resource")
    validation_rules: List[str] = Field(default_factory=list, description="Healthcare-specific validation rules")
    clinical_context: Optional[str] = Field(default=None, description="Clinical usage context for this resource")
    message: str = Field(description="Human-readable result message")


class ResourceDiscoveryResult(BaseModel):
    """
    Result for healthcare resource discovery operations.
    
    Enables AI agents to understand available HACS resources
    and their clinical applications.
    """
    
    success: bool = Field(description="Whether discovery operation succeeded")
    resources: List[Dict[str, Any]] = Field(description="List of available resources with metadata")
    total_count: int = Field(description="Total number of resources discovered")
    categories: List[str] = Field(description="Clinical categories available (clinical, administrative, workflow)")
    fhir_resources: List[str] = Field(default_factory=list, description="FHIR-compliant resource types")
    clinical_resources: List[str] = Field(default_factory=list, description="Clinical workflow resource types")
    administrative_resources: List[str] = Field(default_factory=list, description="Administrative resource types")
    message: str = Field(description="Human-readable discovery summary")


class FieldAnalysisResult(BaseModel):
    """
    Result for healthcare resource field analysis operations.
    
    Provides detailed analysis of resource fields for clinical
    data modeling and AI agent optimization.
    """
    
    success: bool = Field(description="Whether field analysis succeeded")
    resource_type: str = Field(description="Analyzed healthcare resource type")
    field_analysis: Dict[str, Any] = Field(description="Detailed field-by-field analysis")
    clinical_fields: List[str] = Field(description="Fields with clinical significance")
    required_for_fhir: List[str] = Field(description="Fields required for FHIR compliance")
    ai_optimized_fields: List[str] = Field(description="Fields optimized for AI agent usage")
    validation_summary: Dict[str, Any] = Field(description="Field validation requirements summary")
    recommendations: List[str] = Field(description="Field usage recommendations for healthcare workflows")
    message: str = Field(description="Human-readable analysis summary")


# === CLINICAL WORKFLOW RESULTS ===

class DataQueryResult(BaseModel):
    """
    Result for structured healthcare data queries using DataRequirement.
    
    Supports FHIR-compliant data requirements and clinical decision support.
    """
    
    success: bool = Field(description="Whether the healthcare data query succeeded")
    message: str = Field(description="Human-readable result message with clinical context")
    data_requirement_id: Optional[str] = Field(default=None, description="ID of the DataRequirement used")
    query_type: str = Field(description="Type of clinical query performed")
    results_count: int = Field(default=0, description="Number of healthcare records found")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Found healthcare resources")
    aggregated_data: Optional[Dict[str, Any]] = Field(default=None, description="Clinical aggregations if requested")
    clinical_insights: Optional[List[str]] = Field(default=None, description="Generated clinical insights")
    fhir_compliant: bool = Field(description="Whether results are FHIR compliant")
    execution_time_ms: Optional[float] = Field(default=None, description="Query execution time in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.now, description="Query execution timestamp")


class WorkflowResult(BaseModel):
    """
    Result for clinical workflow execution using PlanDefinition.
    
    Tracks execution of healthcare workflows and clinical protocols.
    """
    
    success: bool = Field(description="Whether the clinical workflow execution succeeded")
    message: str = Field(description="Human-readable workflow result message")
    workflow_id: str = Field(description="ID of the executed clinical workflow")
    plan_definition_id: str = Field(description="ID of the PlanDefinition used")
    patient_id: Optional[str] = Field(default=None, description="Patient ID if workflow is patient-specific")
    execution_summary: List[Dict[str, Any]] = Field(description="Summary of workflow step executions")
    clinical_outcomes: List[Dict[str, Any]] = Field(default_factory=list, description="Clinical outcomes achieved")
    recommendations: List[str] = Field(default_factory=list, description="Clinical recommendations generated")
    next_steps: List[str] = Field(default_factory=list, description="Recommended next clinical steps")
    compliance_notes: Optional[List[str]] = Field(default=None, description="Healthcare compliance notes")
    executed_actions: int = Field(description="Number of workflow actions executed")
    failed_actions: int = Field(default=0, description="Number of workflow actions that failed")
    execution_duration_ms: Optional[float] = Field(default=None, description="Total workflow execution time")
    timestamp: datetime = Field(default_factory=datetime.now, description="Workflow execution timestamp")


class GuidanceResult(BaseModel):
    """
    Result for clinical decision support using GuidanceResponse.
    
    Provides AI-generated clinical guidance based on evidence and protocols.
    """
    
    success: bool = Field(description="Whether the clinical decision support succeeded")
    message: str = Field(description="Human-readable guidance summary")
    guidance_response_id: str = Field(description="ID of the generated GuidanceResponse")
    guidance_type: str = Field(description="Type of clinical guidance provided")
    clinical_question: str = Field(description="Original clinical question addressed")
    recommendations: List[Dict[str, Any]] = Field(default_factory=list, description="Clinical recommendations with evidence")
    confidence_score: float = Field(description="Confidence in guidance (0.0-1.0) based on evidence quality")
    evidence_sources: List[str] = Field(default_factory=list, description="Clinical evidence sources used")
    contraindications: List[str] = Field(default_factory=list, description="Clinical contraindications identified")
    alternatives: List[str] = Field(default_factory=list, description="Alternative clinical approaches")
    follow_up_required: bool = Field(description="Whether clinical follow-up is recommended")
    urgency_level: str = Field(description="Clinical urgency level (low, moderate, high, urgent)")
    timestamp: datetime = Field(default_factory=datetime.now, description="Guidance generation timestamp")


# === MEMORY AND KNOWLEDGE RESULTS ===

class MemoryResult(BaseModel):
    """
    Result for healthcare AI agent memory operations.
    
    Supports episodic, procedural, and executive memory for clinical AI agents.
    """
    
    success: bool = Field(description="Whether the memory operation succeeded")
    message: str = Field(description="Human-readable memory operation result")
    memory_type: str = Field(description="Type of memory (episodic, procedural, executive)")
    operation_type: str = Field(description="Memory operation performed (store, retrieve, consolidate)")
    memory_count: int = Field(description="Number of memories affected")
    clinical_context: Optional[str] = Field(default=None, description="Clinical context of the memories")
    consolidation_summary: Optional[Dict[str, Any]] = Field(default=None, description="Memory consolidation results")
    retrieval_matches: Optional[List[Dict[str, Any]]] = Field(default=None, description="Retrieved memory matches")
    confidence_scores: Optional[List[float]] = Field(default=None, description="Confidence scores for retrievals")
    timestamp: datetime = Field(default_factory=datetime.now, description="Memory operation timestamp")


class VersionResult(BaseModel):
    """
    Result for healthcare resource versioning operations.
    
    Tracks version changes for clinical data and resource schemas.
    """
    
    success: bool = Field(description="Whether the versioning operation succeeded")
    message: str = Field(description="Human-readable versioning result")
    resource_type: str = Field(description="Type of healthcare resource versioned")
    resource_id: str = Field(description="ID of the versioned resource")
    previous_version: Optional[str] = Field(default=None, description="Previous version identifier")
    current_version: str = Field(description="Current version identifier")
    version_changes: List[str] = Field(description="Summary of changes made in this version")
    clinical_impact: Optional[str] = Field(default=None, description="Clinical impact assessment of changes")
    backwards_compatible: bool = Field(description="Whether version is backwards compatible")
    migration_required: bool = Field(description="Whether data migration is required")
    timestamp: datetime = Field(default_factory=datetime.now, description="Versioning operation timestamp")


# === ADVANCED TOOL RESULTS ===

class ResourceStackResult(BaseModel):
    """
    Result for healthcare resource stacking operations.
    
    Enables composition of complex clinical data structures from multiple resources.
    """
    
    success: bool = Field(description="Whether the resource stacking succeeded")
    stack_name: str = Field(description="Name of the created resource stack")
    layers: List[Dict[str, Any]] = Field(description="Information about each resource layer")
    base_resource_type: str = Field(description="Base healthcare resource type")
    total_fields: int = Field(description="Total fields in the complete stack")
    clinical_fields: int = Field(description="Number of clinically significant fields")
    dependencies: List[str] = Field(description="Resource dependencies in stacking order")
    validation_rules: List[str] = Field(description="Combined validation rules for the stack")
    fhir_compliance: bool = Field(description="Whether the stack maintains FHIR compliance")
    clinical_use_cases: List[str] = Field(description="Recommended clinical use cases for this stack")
    message: str = Field(description="Human-readable stacking result message")


class ResourceTemplateResult(BaseModel):
    """
    Result for clinical resource template operations.
    
    Provides pre-configured templates for common healthcare scenarios.
    """
    
    success: bool = Field(description="Whether template creation succeeded")
    template_name: str = Field(description="Name of the created clinical template")
    template_type: str = Field(description="Type of clinical template (assessment, intake, discharge, etc.)")
    focus_area: str = Field(description="Clinical focus area (cardiology, general, emergency, etc.)")
    template_schema: Dict[str, Any] = Field(description="JSON schema for the clinical template")
    clinical_workflows: List[str] = Field(description="Compatible clinical workflows")
    use_cases: List[str] = Field(description="Recommended healthcare use cases")
    field_mappings: Dict[str, str] = Field(description="Field to source resource mappings")
    customizable_fields: List[str] = Field(description="Fields that can be customized for specific needs")
    required_fields: List[str] = Field(description="Fields required for clinical validity")
    fhir_compliance: bool = Field(description="Whether template is FHIR compliant")
    validation_requirements: List[str] = Field(description="Clinical validation requirements")
    message: str = Field(description="Human-readable template creation result")


# === VECTOR AND SEARCH RESULTS ===

class VectorStoreResult(BaseModel):
    """
    Result for vector store operations in healthcare contexts.
    
    Supports semantic search and embedding operations for clinical data.
    """
    
    success: bool = Field(description="Whether vector operation succeeded")
    operation_type: str = Field(description="Vector operation performed (store, search, hybrid)")
    collection_name: str = Field(description="Vector collection used")
    results_count: int = Field(description="Number of vector results")
    search_results: Optional[List[Dict[str, Any]]] = Field(default=None, description="Vector search results with scores")
    similarity_scores: Optional[List[float]] = Field(default=None, description="Similarity scores for results")
    clinical_relevance: Optional[List[str]] = Field(default=None, description="Clinical relevance assessments")
    embedding_dimensions: Optional[int] = Field(default=None, description="Embedding vector dimensions")
    search_time_ms: Optional[float] = Field(default=None, description="Search execution time")
    message: str = Field(description="Human-readable vector operation result")


__all__ = [
    # Base result types
    "HACSResult",
    
    # Resource management results
    "ResourceSchemaResult", 
    "ResourceDiscoveryResult",
    "FieldAnalysisResult",
    
    # Clinical workflow results
    "DataQueryResult",
    "WorkflowResult", 
    "GuidanceResult",
    
    # Memory and knowledge results
    "MemoryResult",
    "VersionResult",
    
    # Advanced tool results
    "ResourceStackResult",
    "ResourceTemplateResult",
    
    # Vector and search results
    "VectorStoreResult",
] 