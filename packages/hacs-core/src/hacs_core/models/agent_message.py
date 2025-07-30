"""
Agent message model for healthcare agent communication.

This module provides the AgentMessage model for structured communication
between healthcare agents with memory references, provenance tracking,
and confidence scoring.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from hacs_core.base_resource import BaseResource
from pydantic import Field, computed_field, field_validator


class MessageRole(str, Enum):
    """Standard message roles in healthcare agent communication."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"
    AGENT = "agent"
    PHYSICIAN = "physician"
    NURSE = "nurse"
    PATIENT = "patient"
    CAREGIVER = "caregiver"


class MessageType(str, Enum):
    """Types of agent messages."""

    CLINICAL_NOTE = "clinical_note"
    ASSESSMENT = "assessment"
    PLAN = "plan"
    INSTRUCTION = "instruction"
    QUESTION = "question"
    RESPONSE = "response"
    ALERT = "alert"
    REMINDER = "reminder"
    RECOMMENDATION = "recommendation"
    SUMMARY = "summary"
    HANDOFF = "handoff"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"


class MessagePriority(str, Enum):
    """Message priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class AgentMessage(BaseResource):
    """
    Represents a message in healthcare agent communication.

    This model includes structured content, memory references, provenance tracking,
    and agent-specific metadata for comprehensive healthcare communication.
    """

    resource_type: Literal["AgentMessage"] = Field(
        default="AgentMessage", description="Resource type identifier"
    )

    # Core message fields
    role: MessageRole = Field(
        description="Role of the message sender",
        examples=["assistant", "physician", "agent", "patient"],
    )

    content: str = Field(
        description="Message content",
        examples=[
            "Patient presents with chest pain and shortness of breath.",
            "Recommend cardiology consultation within 24 hours.",
            "Blood pressure reading: 140/90 mmHg, elevated from baseline.",
        ],
    )

    message_type: MessageType = Field(
        default=MessageType.RESPONSE,
        description="Type of message",
        examples=["clinical_note", "assessment", "recommendation"],
    )

    priority: MessagePriority = Field(
        default=MessagePriority.NORMAL,
        description="Message priority level",
        examples=["normal", "high", "urgent"],
    )

    # Relationships and references
    related_to: list[str] = Field(
        default_factory=list,
        description="IDs of related resources (Patient, Encounter, etc.)",
        examples=[["patient-001", "encounter-123", "observation-456"]],
    )

    parent_message_id: str | None = Field(
        default=None,
        description="ID of the parent message in a thread or workflow",
        examples=["message-parent-001", None],
    )

    in_reply_to: str | None = Field(
        default=None,
        description="ID of message this is replying to",
        examples=["message-001", None],
    )

    thread_id: str | None = Field(
        default=None,
        description="Conversation thread identifier",
        examples=["thread-abc123", None],
    )

    summary: str | None = Field(
        default=None,
        description="A compressed summary of the message content for long-term storage",
        examples=["Patient reports chest pain, recommends cardiology consult."],
    )

    # Agent-centric fields
    memory_handles: list[str] = Field(
        default_factory=list,
        description="References to memory blocks used in generating this message",
        examples=[["memory-001", "memory-002", "memory-episodic-123"]],
    )

    evidence_references: list[str] = Field(
        default_factory=list,
        description="References to evidence used in this message",
        examples=[["evidence-001", "evidence-guideline-002"]],
        alias="evidence_links",
    )

    confidence_score: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Confidence score for this message (0.0 to 1.0)",
        examples=[0.95, 0.7, 0.85],
    )

    # Provenance and metadata
    provenance: dict[str, Any] = Field(
        default_factory=dict,
        description="Provenance information about message generation",
        examples=[
            {
                "agent_model": "gpt-4-healthcare",
                "agent_version": "1.2.0",
                "generation_method": "reasoning_chain",
                "input_tokens": 1500,
                "output_tokens": 250,
                "processing_time_ms": 2340,
                "temperature": 0.7,
            }
        ],
    )

    # Tool and reasoning metadata
    tool_calls: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Tool calls made during message generation",
        examples=[
            [
                {
                    "tool_name": "search_guidelines",
                    "parameters": {"condition": "hypertension", "age_group": "adult"},
                    "result_summary": "Found 3 relevant guidelines",
                    "execution_time_ms": 450,
                    "version": "1.1",
                }
            ]
        ],
    )

    reasoning_trace: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Reasoning steps taken to generate this message",
        examples=[
            [
                {
                    "step": 1,
                    "type": "information_gathering",
                    "description": "Retrieved patient history and current symptoms",
                    "confidence": 0.9,
                    "version": "1.0",
                },
                {
                    "step": 2,
                    "type": "differential_diagnosis",
                    "description": "Considered cardiac vs. pulmonary causes",
                    "confidence": 0.8,
                    "version": "1.0",
                },
            ]
        ],
    )

    action_items: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Actionable items or tasks derived from the message",
        examples=[
            [
                {
                    "item": "Schedule cardiology consult",
                    "priority": "high",
                    "due_date": "2024-08-01T17:00:00Z",
                    "assigned_to": "scheduling-agent",
                }
            ]
        ],
    )

    # Clinical context
    clinical_context: dict[str, Any] = Field(
        default_factory=dict,
        description="Clinical context and metadata",
        examples=[
            {
                "encounter_type": "emergency",
                "department": "cardiology",
                "urgency_level": "high",
                "patient_acuity": "stable",
                "clinical_decision_support": True,
            }
        ],
    )

    # Communication metadata
    sender_id: str | None = Field(
        default=None,
        description="ID of the sender (Actor, Agent, etc.)",
        examples=["actor-001", "agent-cardiology", None],
    )

    recipient_ids: list[str] = Field(
        default_factory=list,
        description="IDs of intended recipients",
        examples=[["actor-002", "agent-primary-care"]],
    )

    tags: list[str] = Field(
        default_factory=list,
        description="Tags for categorizing and searching messages",
        examples=[["cardiology", "urgent", "chest_pain", "assessment"]],
    )

    # Status and workflow
    status: Literal["draft", "sent", "delivered", "read", "archived"] = Field(
        default="sent", description="Message status in workflow"
    )

    requires_response: bool = Field(
        default=False, description="Whether this message requires a response"
    )

    response_deadline: datetime | None = Field(
        default=None, description="Deadline for response if required"
    )

    # Additional compatibility fields
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="DEPRECATED: Use specific fields like `tags`, `provenance`, and `clinical_context` instead. "
        "Additional metadata for the message",
        examples=[{"department": "cardiology", "priority_level": "high"}],
    )

    patient_id: str | None = Field(
        default=None,
        description="ID of the patient this message relates to",
        examples=["patient-001", None],
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Ensure content is not empty."""
        if not v.strip():
            raise ValueError("Message content cannot be empty")
        return v.strip()

    @field_validator("confidence_score")
    @classmethod
    def validate_confidence_score(cls, v: float) -> float:
        """Ensure confidence score is between 0.0 and 1.0."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        return v

    @field_validator("provenance")
    @classmethod
    def validate_provenance(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Ensure provenance is a valid dictionary."""
        if not isinstance(v, dict):
            raise ValueError("Provenance must be a dictionary")
        return v

    @computed_field
    @property
    def word_count(self) -> int:
        """Computed field for message word count."""
        return len(self.content.split())

    @computed_field
    @property
    def has_clinical_content(self) -> bool:
        """Computed field indicating if message has clinical content."""
        clinical_keywords = [
            "patient",
            "diagnosis",
            "treatment",
            "medication",
            "symptom",
            "vital",
            "lab",
            "test",
            "procedure",
            "condition",
            "disease",
            "therapy",
            "assessment",
            "plan",
            "recommendation",
        ]
        content_lower = self.content.lower()
        return any(keyword in content_lower for keyword in clinical_keywords)

    @computed_field
    @property
    def urgency_score(self) -> float:
        """Computed urgency score based on priority and content."""
        priority_scores = {
            MessagePriority.LOW: 0.2,
            MessagePriority.NORMAL: 0.4,
            MessagePriority.HIGH: 0.7,
            MessagePriority.URGENT: 0.9,
            MessagePriority.CRITICAL: 1.0,
        }

        base_score = priority_scores.get(self.priority, 0.4)

        # Boost score for urgent keywords
        urgent_keywords = ["emergency", "critical", "urgent", "stat", "immediate"]
        content_lower = self.content.lower()
        urgency_boost = sum(
            0.1 for keyword in urgent_keywords if keyword in content_lower
        )

        return min(1.0, base_score + urgency_boost)

    @property
    def evidence_links(self) -> list[str]:
        """Alias for evidence_references for backward compatibility."""
        return self.evidence_references

    @evidence_links.setter
    def evidence_links(self, value: list[str]) -> None:
        """Setter for evidence_links."""
        self.evidence_references = value

    def link_to_encounter(self, encounter_id: str) -> None:
        """
        Link this message to an encounter.

        Args:
            encounter_id: ID of the encounter to link to
        """
        if encounter_id not in self.related_to:
            self.related_to.append(encounter_id)
            self.update_timestamp()

    def update_summary(self, summary_text: str) -> None:
        """
        Update the message summary.

        Args:
            summary_text: The new summary content.
        """
        self.summary = summary_text.strip()
        self.update_timestamp()

    def add_memory_reference(self, memory_id: str) -> None:
        """
        Add a memory block reference.

        Args:
            memory_id: ID of the memory block
        """
        if memory_id not in self.memory_handles:
            self.memory_handles.append(memory_id)
            self.update_timestamp()

    def remove_memory_reference(self, memory_id: str) -> bool:
        """
        Remove a memory block reference.

        Args:
            memory_id: ID of the memory block to remove

        Returns:
            True if reference was removed, False if not found
        """
        if memory_id in self.memory_handles:
            self.memory_handles.remove(memory_id)
            self.update_timestamp()
            return True
        return False

    def link_to_evidence(self, evidence_id: str) -> None:
        """
        Link this message to evidence.

        Args:
            evidence_id: ID of the evidence to link to
        """
        if evidence_id not in self.evidence_references:
            self.evidence_references.append(evidence_id)
            self.update_timestamp()

    def update_provenance(self, key: str, value: Any) -> None:
        """
        Update provenance information.

        Args:
            key: Provenance key
            value: Provenance value
        """
        self.provenance[key] = value
        self.update_timestamp()

    def add_tool_call(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        result_summary: str,
        execution_time_ms: int | None = None,
        version: str | None = None,
    ) -> None:
        """
        Add a tool call record.

        Args:
            tool_name: Name of the tool called
            parameters: Parameters passed to the tool
            result_summary: Summary of the tool result
            execution_time_ms: Execution time in milliseconds
            version: The version of the tool used
        """
        tool_call = {
            "tool_name": tool_name,
            "parameters": parameters,
            "result_summary": result_summary,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if execution_time_ms is not None:
            tool_call["execution_time_ms"] = execution_time_ms
        if version:
            tool_call["version"] = version

        self.tool_calls.append(tool_call)
        self.update_timestamp()

    def add_reasoning_step(
        self,
        step_type: str,
        description: str,
        confidence: float,
        step_number: int | None = None,
        version: str | None = None,
    ) -> None:
        """
        Add a reasoning step to the trace.

        Args:
            step_type: Type of reasoning step
            description: Description of the reasoning
            confidence: Confidence in this step (0.0 to 1.0)
            step_number: Step number (auto-generated if not provided)
            version: The version of the reasoning process used
        """
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")

        if step_number is None:
            step_number = len(self.reasoning_trace) + 1

        reasoning_step = {
            "step": step_number,
            "type": step_type,
            "description": description,
            "confidence": confidence,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if version:
            reasoning_step["version"] = version

        self.reasoning_trace.append(reasoning_step)
        self.update_timestamp()

    def add_action_item(
        self,
        item: str,
        priority: str = "normal",
        due_date: datetime | None = None,
        assigned_to: str | None = None,
    ) -> None:
        """
        Add an action item to the message.

        Args:
            item: The description of the action item.
            priority: The priority of the item (e.g., 'low', 'normal', 'high').
            due_date: The due date for the action item.
            assigned_to: The ID of the agent or actor assigned to the item.
        """
        action_item = {"item": item, "priority": priority, "status": "pending"}
        if due_date:
            action_item["due_date"] = due_date.isoformat()
        if assigned_to:
            action_item["assigned_to"] = assigned_to
        self.action_items.append(action_item)
        self.update_timestamp()

    def update_clinical_context(self, key: str, value: Any) -> None:
        """
        Update clinical context information.

        Args:
            key: Context key
            value: Context value
        """
        self.clinical_context[key] = value
        self.update_timestamp()

    def add_tag(self, tag: str) -> None:
        """
        Add a tag if not already present.

        Args:
            tag: Tag to add
        """
        tag = tag.strip().lower()
        if tag and tag not in self.tags:
            self.tags.append(tag)
            self.update_timestamp()

    def remove_tag(self, tag: str) -> bool:
        """
        Remove a tag.

        Args:
            tag: Tag to remove

        Returns:
            True if the tag was removed, False if it wasn't found
        """
        tag = tag.strip().lower()
        if tag in self.tags:
            self.tags.remove(tag)
            self.update_timestamp()
            return True
        return False

    def add_recipient(self, recipient_id: str) -> None:
        """
        Add a recipient if not already present.

        Args:
            recipient_id: ID of the recipient to add
        """
        if recipient_id not in self.recipient_ids:
            self.recipient_ids.append(recipient_id)
            self.update_timestamp()

    def set_response_deadline(self, deadline: datetime) -> None:
        """
        Set response deadline and mark as requiring response.

        Args:
            deadline: Response deadline
        """
        self.response_deadline = deadline
        self.requires_response = True
        self.update_timestamp()

    def mark_as_read(self) -> None:
        """Mark message as read."""
        self.status = "read"
        self.update_timestamp()

    def archive(self) -> None:
        """Archive the message."""
        self.status = "archived"
        self.update_timestamp()

    def is_overdue(self) -> bool:
        """
        Check if response is overdue.

        Returns:
            True if response deadline has passed
        """
        if not self.requires_response or not self.response_deadline:
            return False
        return datetime.now(timezone.utc) > self.response_deadline

    def get_average_reasoning_confidence(self) -> float:
        """
        Get average confidence across all reasoning steps.

        Returns:
            Average confidence score, or 0.0 if no reasoning steps
        """
        if not self.reasoning_trace:
            return 0.0

        confidences = [step.get("confidence", 0.0) for step in self.reasoning_trace]
        return sum(confidences) / len(confidences)

    def __repr__(self) -> str:
        """Enhanced representation including role, type, and urgency."""
        urgency_indicator = (
            "🔴"
            if self.urgency_score >= 0.8
            else "🟡"
            if self.urgency_score >= 0.6
            else "🟢"
        )
        content_preview = (
            self.content[:50] + "..." if len(self.content) > 50 else self.content
        )
        return f"AgentMessage(id='{self.id}', role='{self.role}', type='{self.message_type}', urgency={urgency_indicator}, content='{content_preview}')"
