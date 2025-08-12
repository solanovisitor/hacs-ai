"""
Memory models for agent cognition and recall.

This module provides memory-related models that enable agents to store,
organize, and recall different types of information.
"""

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import Field, field_validator

from .base_resource import BaseResource


class MemoryBlock(BaseResource):
    """
    Represents a block of agent memory.

    Memory blocks are categorized into three types based on cognitive science:
    - Episodic: Specific events and experiences
    - Procedural: Skills, habits, and how-to knowledge
    - Executive: High-level goals, plans, and decision-making context
    - Semantic: General knowledge and facts

    New implementations should use structured fields:
    - tags: for categorization
    - confidence_score: for accuracy rating  
    - context_metadata: for structured context data
    - importance_score: for memory prioritization
    
    The deprecated 'metadata' field is maintained for backward compatibility
    but will be removed in a future version.
    """

    resource_type: Literal["MemoryBlock"] = Field(
        default="MemoryBlock", description="Resource type identifier"
    )

    memory_type: Literal["episodic", "procedural", "executive", "semantic"] = Field(
        description="Type of memory this block represents",
        examples=["episodic", "procedural", "executive", "semantic"],
    )

    content: str = Field(
        description="The actual memory content or information",
        examples=[
            "Patient John Doe expressed concern about chest pain during consultation",
            "To calculate BMI: divide weight in kg by height in meters squared",
            "Current goal: Complete patient triage within 15 minutes",
        ],
    )

    summary: str | None = Field(
        default=None,
        description="A compressed or summarized version of the memory content",
        examples=["Patient concerned about chest pain.", "BMI calculation formula."],
    )

    # Context metadata - use structured fields for new implementations
    context_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured context metadata for this memory (patient_id, encounter_id, etc.)",
        examples=[
            {
                "patient_id": "pat-001",
                "encounter_id": "enc-001",
                "session_id": "sess-123",
            }
        ],
    )

    related_memories: list[str] = Field(
        default_factory=list,
        description="IDs of other memory blocks related to this one",
        examples=[["mem-001", "mem-002"]],
    )

    importance_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Importance score from 0.0 to 1.0 for memory prioritization",
        examples=[0.8, 0.3, 0.95],
    )

    confidence_score: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Confidence in the accuracy of the memory, from 0.0 to 1.0",
        examples=[0.9, 0.75],
    )

    tags: list[str] = Field(
        default_factory=list,
        description="Tags for categorizing and searching memories",
        examples=[["patient_interaction", "diagnosis_note"]],
    )

    access_count: int = Field(
        default=0,
        ge=0,
        description="Number of times this memory has been accessed",
        examples=[0, 5, 23],
    )

    # Additional compatibility fields
    vector_id: str | None = Field(
        default=None,
        description="Vector embedding ID for semantic search",
        examples=["vec_abc123", None],
    )

    last_accessed: datetime | None = Field(
        default=None,
        description="Timestamp of last access",
        examples=["2024-01-15T10:30:00Z", None],
    )

    last_summarized: datetime | None = Field(
        default=None,
        description="Timestamp of when the summary was last updated",
        examples=["2024-01-16T11:00:00Z", None],
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Ensure content is not empty."""
        if not v.strip():
            raise ValueError("Memory content cannot be empty")
        return v.strip()

    @field_validator("context_metadata")
    @classmethod
    def validate_context_metadata(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Ensure context_metadata is a valid dictionary."""
        if not isinstance(v, dict):
            raise ValueError("Context metadata must be a dictionary")
        return v

    @property
    def metadata(self) -> dict[str, Any]:
        """
        DEPRECATED: Backward compatibility property for metadata field.
        Use context_metadata, tags, confidence_score, and other structured fields instead.
        """
        import warnings
        warnings.warn(
            "MemoryBlock.metadata is deprecated. Use context_metadata, tags, "
            "confidence_score, and other structured fields instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.context_metadata.copy()

    @metadata.setter
    def metadata(self, value: dict[str, Any]) -> None:
        """
        DEPRECATED: Backward compatibility setter for metadata field.
        """
        import warnings
        warnings.warn(
            "MemoryBlock.metadata is deprecated. Use context_metadata, tags, "
            "confidence_score, and other structured fields instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.context_metadata = value

    @classmethod
    def migrate_from_metadata(cls, memory_data: dict[str, Any]) -> dict[str, Any]:
        """
        Migrate memory data from old metadata format to new structured format.
        
        Args:
            memory_data: Memory data with old metadata field
            
        Returns:
            Migrated memory data with structured fields
        """
        if "metadata" not in memory_data:
            return memory_data
        
        migrated = memory_data.copy()
        old_metadata = migrated.pop("metadata", {})
        
        # Migrate confidence from old metadata
        if "confidence" in old_metadata and "confidence_score" not in migrated:
            migrated["confidence_score"] = old_metadata.pop("confidence")
        
        # Migrate tags from old metadata  
        if "tags" in old_metadata and "tags" not in migrated:
            migrated["tags"] = old_metadata.pop("tags")
        
        # Move remaining metadata to context_metadata
        if old_metadata:
            migrated["context_metadata"] = old_metadata
            
        return migrated

    @property
    def linked_memories(self) -> list[str]:
        """Alias for related_memories for backward compatibility."""
        return self.related_memories

    @linked_memories.setter
    def linked_memories(self, value: list[str]) -> None:
        """Setter for linked_memories."""
        self.related_memories = value

    def add_related_memory(self, memory_id: str) -> None:
        """
        Add a related memory ID if not already present.

        Args:
            memory_id: ID of the related memory block
        """
        if memory_id not in self.related_memories:
            self.related_memories.append(memory_id)
            self.update_timestamp()

    def remove_related_memory(self, memory_id: str) -> bool:
        """
        Remove a related memory ID.

        Args:
            memory_id: ID of the memory block to remove

        Returns:
            True if the memory was removed, False if it wasn't found
        """
        if memory_id in self.related_memories:
            self.related_memories.remove(memory_id)
            self.update_timestamp()
            return True
        return False

    def increment_access(self) -> None:
        """Increment the access count and update timestamp."""
        self.access_count += 1
        self.last_accessed = datetime.now(timezone.utc)
        self.update_timestamp()

    def set_importance(self, score: float) -> None:
        """
        Set the importance score.

        Args:
            score: Importance score between 0.0 and 1.0
        """
        if not 0.0 <= score <= 1.0:
            raise ValueError("Importance score must be between 0.0 and 1.0")
        self.importance_score = score
        self.update_timestamp()

    def set_confidence(self, score: float) -> None:
        """
        Set the confidence score.

        Args:
            score: Confidence score between 0.0 and 1.0
        """
        if not 0.0 <= score <= 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        self.confidence_score = score
        self.update_timestamp()

    def update_summary(self, summary_text: str) -> None:
        """
        Update the summary and the last_summarized timestamp.

        Args:
            summary_text: The new summary content.
        """
        self.summary = summary_text.strip()
        self.last_summarized = datetime.now(timezone.utc)
        self.update_timestamp()

    def add_tag(self, tag: str) -> None:
        """
        Add a tag if not already present.

        Args:
            tag: The tag to add.
        """
        tag = tag.strip().lower()
        if tag and tag not in self.tags:
            self.tags.append(tag)
            self.update_timestamp()

    def remove_tag(self, tag: str) -> bool:
        """
        Remove a tag.

        Args:
            tag: The tag to remove.

        Returns:
            True if the tag was removed, False otherwise.
        """
        tag = tag.strip().lower()
        if tag in self.tags:
            self.tags.remove(tag)
            self.update_timestamp()
            return True
        return False

    def add_metadata(self, key: str, value: Any) -> None:
        """
        Add or update a metadata field.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
        self.update_timestamp()

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get a metadata value.

        Args:
            key: Metadata key
            default: Default value if key not found

        Returns:
            Metadata value or default
        """
        return self.metadata.get(key, default)

    def __repr__(self) -> str:
        """Enhanced representation including memory type."""
        return f"MemoryBlock(id='{self.id}', type='{self.memory_type}', importance={self.importance_score})"
