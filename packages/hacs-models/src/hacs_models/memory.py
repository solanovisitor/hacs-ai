"""
Memory models for AI agent cognition and recall.

This module provides memory-related models that enable AI agents to store,
organize, and recall different types of information in healthcare workflows.

Based on cognitive science models, supports multiple memory types:
- Episodic: Specific events and experiences  
- Semantic: General knowledge and facts
- Working: Temporary information processing
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import Field, field_validator

from .base_resource import BaseResource


class MemoryBlock(BaseResource):
    """
    Base memory block for AI agent cognition.
    
    Represents a unit of memory that can be stored, retrieved, and processed
    by AI agents in healthcare workflows. Supports multiple memory types
    based on cognitive science models.
    
    Features:
        - Typed memory categorization
        - Importance and confidence scoring
        - Context metadata for healthcare workflows
        - Memory relationship tracking
        - Tag-based organization
    """
    
    resource_type: Literal["MemoryBlock"] = Field(
        default="MemoryBlock",
        description="Resource type identifier"
    )
    
    memory_type: Literal["episodic", "semantic", "working"] = Field(
        description="Type of memory this block represents",
        examples=["episodic", "semantic", "working"]
    )
    
    content: str = Field(
        description="The actual memory content or information",
        examples=[
            "Patient John Doe expressed concern about chest pain during consultation",
            "Normal systolic blood pressure range is 90-120 mmHg",
            "Current analysis: reviewing patient vital signs"
        ],
        min_length=1,
        max_length=10000
    )
    
    summary: str | None = Field(
        default=None,
        description="Compressed summary of the memory content",
        examples=["Patient chest pain concern", "BP normal range", "Reviewing vitals"],
        max_length=500
    )
    
    # Scoring and metadata
    importance_score: float = Field(
        default=0.5,
        description="Importance score from 0.0 to 1.0 for memory prioritization",
        ge=0.0,
        le=1.0
    )
    
    confidence_score: float = Field(
        default=0.8,
        description="Confidence in memory accuracy from 0.0 to 1.0",
        ge=0.0,
        le=1.0
    )
    
    # Context and relationships
    context_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured context metadata (patient_id, encounter_id, etc.)",
        examples=[{"patient_id": "patient-123", "encounter_id": "encounter-456"}]
    )
    
    related_memories: list[str] = Field(
        default_factory=list,
        description="IDs of related memory blocks",
        max_length=20
    )
    
    tags: list[str] = Field(
        default_factory=list,
        description="Tags for categorizing and searching memories",
        examples=[["patient_interaction", "vital_signs", "diagnosis"]],
        max_length=10
    )
    
    # Access patterns
    access_count: int = Field(
        default=0,
        description="Number of times this memory has been accessed",
        ge=0
    )
    
    last_accessed_at: datetime | None = Field(
        default=None,
        description="When this memory was last accessed"
    )
    
    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Validate and clean tags."""
        if not v:
            return []
        
        cleaned = []
        for tag in v:
            if not isinstance(tag, str):
                raise ValueError("Tags must be strings")
            
            clean_tag = tag.strip().lower()
            if clean_tag and len(clean_tag) <= 50:
                cleaned.append(clean_tag)
        
        return list(set(cleaned))  # Remove duplicates
    
    def access_memory(self) -> None:
        """Record access to this memory."""
        self.access_count += 1
        self.last_accessed_at = datetime.now()
        self.update_timestamp()
    
    def add_related_memory(self, memory_id: str) -> None:
        """Add a related memory reference."""
        if memory_id not in self.related_memories:
            self.related_memories.append(memory_id)
            self.update_timestamp()
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to this memory."""
        clean_tag = tag.strip().lower()
        if clean_tag and clean_tag not in self.tags:
            self.tags.append(clean_tag)
            self.update_timestamp()
    
    def update_importance(self, new_score: float) -> None:
        """Update importance score."""
        if 0.0 <= new_score <= 1.0:
            self.importance_score = new_score
            self.update_timestamp()
    
    def __str__(self) -> str:
        """Human-readable representation."""
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"MemoryBlock({self.memory_type}: {content_preview})"


class EpisodicMemory(MemoryBlock):
    """
    Episodic memory for specific events and experiences.
    
    Stores memories of specific events, interactions, and experiences
    that occurred at particular times and places.
    """
    
    memory_type: Literal["episodic"] = Field(
        default="episodic",
        description="Episodic memory type"
    )
    
    event_time: datetime | None = Field(
        default=None,
        description="When the remembered event occurred"
    )
    
    location: str | None = Field(
        default=None,
        description="Where the remembered event occurred",
        examples=["Emergency Room", "Patient Room 302", "Clinic A"],
        max_length=100
    )
    
    participants: list[str] = Field(
        default_factory=list,
        description="Who was involved in the remembered event",
        examples=[["Patient/patient-123", "Practitioner/dr-smith"]],
        max_length=10
    )


class SemanticMemory(MemoryBlock):
    """
    Semantic memory for general knowledge and facts.
    
    Stores factual information, general knowledge, and learned concepts
    that are not tied to specific experiences.
    """
    
    memory_type: Literal["semantic"] = Field(
        default="semantic",
        description="Semantic memory type"
    )
    
    knowledge_domain: str | None = Field(
        default=None,
        description="Domain or field this knowledge belongs to",
        examples=["cardiology", "pharmacology", "nursing_procedures"],
        max_length=50
    )
    
    source: str | None = Field(
        default=None,
        description="Source of this knowledge",
        examples=["Medical textbook", "Clinical guidelines", "Training data"],
        max_length=200
    )
    
    evidence_level: str | None = Field(
        default=None,
        description="Level of evidence supporting this knowledge",
        examples=["high", "medium", "low", "expert_opinion"],
        max_length=20
    )


class WorkingMemory(MemoryBlock):
    """
    Working memory for temporary information processing.
    
    Stores information that is actively being processed or manipulated
    in current tasks and workflows.
    """
    
    memory_type: Literal["working"] = Field(
        default="working",
        description="Working memory type"
    )
    
    task_context: str | None = Field(
        default=None,
        description="Current task context for this working memory",
        examples=["patient_assessment", "medication_review", "diagnostic_reasoning"],
        max_length=100
    )
    
    processing_stage: str | None = Field(
        default=None,
        description="Current processing stage",
        examples=["input", "processing", "output", "complete"],
        max_length=20
    )
    
    ttl_seconds: int | None = Field(
        default=None,
        description="Time-to-live in seconds for this working memory",
        examples=[300, 900, 3600],  # 5 min, 15 min, 1 hour
        gt=0
    )
    
    def is_expired(self) -> bool:
        """Check if this working memory has expired."""
        if not self.ttl_seconds or not self.created_at:
            return False
        
        age_seconds = (datetime.now() - self.created_at).total_seconds()
        return age_seconds > self.ttl_seconds