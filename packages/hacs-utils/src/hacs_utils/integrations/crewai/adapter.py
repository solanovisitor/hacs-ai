"""
CrewAI Adapter

This module provides adapters for integrating HACS with CrewAI agents
including agent binding helpers and task format conversion.
"""

import uuid
from enum import Enum
from typing import Any

from hacs_core import Actor, Evidence, MemoryBlock

try:
    from hacs_models import Observation, Patient
except ImportError:
    # Fallback to hacs_core.models if hacs_models is not available
    try:
        from hacs_core.models import Observation, Patient
    except ImportError:
        # Create placeholder classes if neither is available
        class _PlaceholderModel:
            pass
        Observation = _PlaceholderModel
        Patient = _PlaceholderModel
from pydantic import BaseModel, Field


class CrewAIAgentRole(str, Enum):
    """CrewAI agent roles for healthcare workflows."""

    CLINICAL_ASSESSOR = "clinical_assessor"
    TREATMENT_PLANNER = "treatment_planner"
    EVIDENCE_REVIEWER = "evidence_reviewer"
    MEMORY_MANAGER = "memory_manager"
    DATA_ANALYST = "data_analyst"
    PATIENT_ADVOCATE = "patient_advocate"
    QUALITY_ASSURANCE = "quality_assurance"
    DECISION_SUPPORT = "decision_support"


class CrewAITaskType(str, Enum):
    """CrewAI task types for different operations."""

    PATIENT_ASSESSMENT = "patient_assessment"
    OBSERVATION_ANALYSIS = "observation_analysis"
    TREATMENT_PLANNING = "treatment_planning"
    EVIDENCE_SYNTHESIS = "evidence_synthesis"
    MEMORY_CONSOLIDATION = "memory_consolidation"
    QUALITY_REVIEW = "quality_review"
    DECISION_MAKING = "decision_making"
    REPORT_GENERATION = "report_generation"


class CrewAITask(BaseModel):
    """CrewAI Task format for agent workflows."""

    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_type: CrewAITaskType = Field(description="Type of CrewAI task")
    description: str = Field(description="Task description")
    expected_output: str = Field(description="Expected output description")
    agent_role: CrewAIAgentRole = Field(description="Assigned agent role")
    context: dict[str, Any] = Field(default_factory=dict, description="Task context")
    tools: list[str] = Field(default_factory=list, description="Available tools")
    resources: dict[str, Any] = Field(
        default_factory=dict, description="HACS resources"
    )
    dependencies: list[str] = Field(
        default_factory=list, description="Task dependencies"
    )
    priority: int = Field(default=5, ge=1, le=10, description="Task priority")
    timeout_minutes: int = Field(default=30, description="Task timeout in minutes")
    actor_context: dict[str, Any] = Field(
        default_factory=dict, description="Actor context"
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class CrewAIAgentBinding(BaseModel):
    """CrewAI Agent binding with HACS integration."""

    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: CrewAIAgentRole = Field(description="Agent role")
    goal: str = Field(description="Agent goal")
    backstory: str = Field(description="Agent backstory")
    capabilities: list[str] = Field(
        default_factory=list, description="Agent capabilities"
    )
    tools: list[str] = Field(default_factory=list, description="Available tools")
    hacs_permissions: list[str] = Field(
        default_factory=list, description="HACS permissions"
    )
    memory_access: bool = Field(default=True, description="Memory access enabled")
    evidence_access: bool = Field(default=True, description="Evidence access enabled")
    actor_binding: str | None = Field(default=None, description="Bound HACS Actor ID")
    specializations: list[str] = Field(
        default_factory=list, description="Clinical specializations"
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class CrewAIAdapter:
    """Adapter for integrating HACS with CrewAI workflows."""

    def __init__(self):
        """Initialize CrewAI adapter."""
        self.task_registry: dict[str, CrewAITask] = {}
        self.agent_registry: dict[str, CrewAIAgentBinding] = {}
        self.crew_registry: dict[str, dict[str, Any]] = {}

    def create_agent_binding(
        self,
        role: CrewAIAgentRole,
        actor: Actor | None = None,
        specializations: list[str] | None = None,
        **kwargs,
    ) -> CrewAIAgentBinding:
        """Create CrewAI agent binding with HACS integration.

        Args:
            role: CrewAI agent role
            actor: Optional HACS Actor to bind
            specializations: Optional clinical specializations
            **kwargs: Additional agent parameters

        Returns:
            CrewAIAgentBinding instance
        """
        # Define role-specific configurations
        role_configs = {
            CrewAIAgentRole.CLINICAL_ASSESSOR: {
                "goal": "Assess patient conditions and analyze clinical data to provide accurate diagnoses and recommendations",
                "backstory": "You are an experienced clinical assessor with expertise in patient evaluation, diagnostic reasoning, and evidence-based medicine. You excel at synthesizing complex clinical information.",
                "capabilities": [
                    "patient_assessment",
                    "diagnostic_reasoning",
                    "clinical_analysis",
                    "risk_stratification",
                ],
                "tools": [
                    "observation_analyzer",
                    "patient_profiler",
                    "risk_calculator",
                    "guideline_checker",
                ],
            },
            CrewAIAgentRole.TREATMENT_PLANNER: {
                "goal": "Develop comprehensive treatment plans based on patient assessments and clinical evidence",
                "backstory": "You are a treatment planning specialist who creates personalized, evidence-based treatment strategies. You consider patient preferences, clinical guidelines, and resource constraints.",
                "capabilities": [
                    "treatment_planning",
                    "medication_management",
                    "care_coordination",
                    "outcome_prediction",
                ],
                "tools": [
                    "treatment_optimizer",
                    "drug_interaction_checker",
                    "care_plan_generator",
                    "outcome_predictor",
                ],
            },
            CrewAIAgentRole.EVIDENCE_REVIEWER: {
                "goal": "Review and synthesize clinical evidence to support decision-making and quality improvement",
                "backstory": "You are a clinical research expert who evaluates evidence quality, synthesizes findings, and provides evidence-based recommendations for clinical practice.",
                "capabilities": [
                    "evidence_synthesis",
                    "quality_assessment",
                    "literature_review",
                    "guideline_development",
                ],
                "tools": [
                    "evidence_grader",
                    "meta_analyzer",
                    "guideline_mapper",
                    "quality_scorer",
                ],
            },
            CrewAIAgentRole.MEMORY_MANAGER: {
                "goal": "Manage and consolidate clinical memories to support learning and decision-making",
                "backstory": "You are a knowledge management specialist who organizes, consolidates, and retrieves clinical memories to enhance care continuity and learning.",
                "capabilities": [
                    "memory_consolidation",
                    "knowledge_extraction",
                    "pattern_recognition",
                    "learning_facilitation",
                ],
                "tools": [
                    "memory_consolidator",
                    "pattern_detector",
                    "knowledge_extractor",
                    "learning_tracker",
                ],
            },
        }

        config = role_configs.get(
            role,
            {
                "goal": f"Perform {role.value} tasks effectively",
                "backstory": f"You are a specialized {role.value} agent",
                "capabilities": [role.value],
                "tools": ["general_tool"],
            },
        )

        # Create agent binding
        binding = CrewAIAgentBinding(
            role=role,
            goal=kwargs.get("goal", config["goal"]),
            backstory=kwargs.get("backstory", config["backstory"]),
            capabilities=kwargs.get("capabilities", config["capabilities"]),
            tools=kwargs.get("tools", config["tools"]),
            specializations=specializations or [],
            **kwargs,
        )

        # Bind HACS Actor if provided
        if actor:
            binding.actor_binding = actor.id
            binding.hacs_permissions = actor.permissions
            binding.metadata["actor_name"] = actor.name
            binding.metadata["actor_role"] = (
                actor.role.value if hasattr(actor.role, "value") else str(actor.role)
            )
            binding.metadata["organization"] = getattr(actor, "organization", None)

        # Register agent
        self.agent_registry[binding.agent_id] = binding

        return binding

    def create_task(
        self,
        task_type: CrewAITaskType,
        description: str,
        expected_output: str,
        agent_role: CrewAIAgentRole,
        resources: dict[str, Any] | None = None,
        actor: Actor | None = None,
        **kwargs,
    ) -> CrewAITask:
        """Create CrewAI task with HACS integration.

        Args:
            task_type: Type of CrewAI task
            description: Task description
            expected_output: Expected output description
            agent_role: Assigned agent role
            resources: Optional HACS resources
            actor: Optional actor context
            **kwargs: Additional task parameters

        Returns:
            CrewAITask instance
        """
        # Create actor context
        actor_context = {}
        if actor:
            actor_context = {
                "actor_id": actor.id,
                "actor_name": actor.name,
                "actor_role": actor.role.value
                if hasattr(actor.role, "value")
                else str(actor.role),
                "permissions": actor.permissions,
            }

        # Create task
        task = CrewAITask(
            task_type=task_type,
            description=description,
            expected_output=expected_output,
            agent_role=agent_role,
            context=kwargs.get("context", {}),
            tools=kwargs.get("tools", []),
            resources=resources or {},
            dependencies=kwargs.get("dependencies", []),
            priority=kwargs.get("priority", 5),
            timeout_minutes=kwargs.get("timeout_minutes", 30),
            actor_context=actor_context,
            metadata=kwargs.get("metadata", {}),
        )

        # Register task
        self.task_registry[task.task_id] = task

        return task

    def create_patient_assessment_task(
        self, patient: Patient, observations: list[Observation], actor: Actor, **kwargs
    ) -> CrewAITask:
        """Create patient assessment task.

        Args:
            patient: Patient resource
            observations: List of observations
            actor: Actor requesting assessment
            **kwargs: Additional parameters

        Returns:
            CrewAITask for patient assessment
        """
        description = f"""
        Assess patient {patient.display_name} (ID: {patient.id}) based on available clinical data.

        Patient Details:
        - Age: {patient.age_years} years
        - Gender: {patient.gender.value if patient.gender else "Unknown"}
        - Active Status: {patient.active}

        Available Observations: {len(observations)}

        Provide a comprehensive clinical assessment including:
        1. Current clinical status
        2. Risk factors and concerns
        3. Recommended follow-up actions
        4. Care plan considerations
        """

        expected_output = """
        A structured clinical assessment report containing:
        - Patient summary and key demographics
        - Clinical findings and observations analysis
        - Risk stratification and concerns
        - Recommended interventions and follow-up
        - Care plan recommendations
        """

        resources = {
            "patient": patient.model_dump(),
            "observations": [obs.model_dump() for obs in observations],
            "observation_count": len(observations),
        }

        context = {
            "assessment_type": "comprehensive",
            "patient_id": patient.id,
            "patient_name": patient.display_name,
            "observation_count": len(observations),
            "requested_by": actor.name,
        }

        return self.create_task(
            CrewAITaskType.PATIENT_ASSESSMENT,
            description,
            expected_output,
            CrewAIAgentRole.CLINICAL_ASSESSOR,
            resources=resources,
            actor=actor,
            context=context,
            tools=["observation_analyzer", "patient_profiler", "risk_calculator"],
            **kwargs,
        )

    def create_evidence_synthesis_task(
        self, evidence_list: list[Evidence], query: str, actor: Actor, **kwargs
    ) -> CrewAITask:
        """Create evidence synthesis task.

        Args:
            evidence_list: List of evidence resources
            query: Research query or question
            actor: Actor requesting synthesis
            **kwargs: Additional parameters

        Returns:
            CrewAITask for evidence synthesis
        """
        description = f"""
        Synthesize clinical evidence to answer the query: "{query}"

        Available Evidence Sources: {len(evidence_list)}
        Evidence Types: {list({e.evidence_type.value for e in evidence_list})}

        Analyze the evidence quality, synthesize findings, and provide evidence-based recommendations.
        Consider confidence scores, quality ratings, and evidence levels in your analysis.
        """

        expected_output = """
        An evidence synthesis report containing:
        - Executive summary of findings
        - Evidence quality assessment
        - Synthesized recommendations
        - Strength of evidence ratings
        - Clinical implications and applications
        - Limitations and gaps identified
        """

        resources = {
            "evidence": [e.model_dump() for e in evidence_list],
            "evidence_count": len(evidence_list),
            "query": query,
        }

        # Calculate average confidence and quality
        avg_confidence = (
            sum(e.confidence_score for e in evidence_list) / len(evidence_list)
            if evidence_list
            else 0
        )
        avg_quality = (
            sum(e.quality_score for e in evidence_list) / len(evidence_list)
            if evidence_list
            else 0
        )

        context = {
            "synthesis_type": "comprehensive",
            "evidence_count": len(evidence_list),
            "query": query,
            "average_confidence": avg_confidence,
            "average_quality": avg_quality,
            "requested_by": actor.name,
        }

        return self.create_task(
            CrewAITaskType.EVIDENCE_SYNTHESIS,
            description,
            expected_output,
            CrewAIAgentRole.EVIDENCE_REVIEWER,
            resources=resources,
            actor=actor,
            context=context,
            tools=["evidence_grader", "meta_analyzer", "quality_scorer"],
            **kwargs,
        )

    def create_memory_consolidation_task(
        self,
        memories: list[MemoryBlock],
        consolidation_type: str,
        actor: Actor,
        **kwargs,
    ) -> CrewAITask:
        """Create memory consolidation task.

        Args:
            memories: List of memory blocks
            consolidation_type: Type of consolidation
            actor: Actor requesting consolidation
            **kwargs: Additional parameters

        Returns:
            CrewAITask for memory consolidation
        """
        description = f"""
        Consolidate {len(memories)} memory blocks using {consolidation_type} consolidation approach.

        Memory Types: {list({m.memory_type for m in memories})}
        Importance Range: {min(m.importance_score for m in memories):.2f} - {max(m.importance_score for m in memories):.2f}

        Identify patterns, extract key insights, and create consolidated knowledge representations.
        Maintain important details while reducing redundancy and improving accessibility.
        """

        expected_output = """
        A memory consolidation report containing:
        - Consolidated memory summary
        - Key patterns and insights identified
        - Importance-weighted knowledge extraction
        - Memory relationship mapping
        - Recommendations for future memory organization
        """

        resources = {
            "memories": [m.model_dump() for m in memories],
            "memory_count": len(memories),
            "consolidation_type": consolidation_type,
        }

        # Analyze memory distribution
        memory_types = {}
        for memory in memories:
            if memory.memory_type not in memory_types:
                memory_types[memory.memory_type] = 0
            memory_types[memory.memory_type] += 1

        context = {
            "consolidation_type": consolidation_type,
            "memory_count": len(memories),
            "memory_types": memory_types,
            "avg_importance": sum(m.importance_score for m in memories) / len(memories),
            "requested_by": actor.name,
        }

        return self.create_task(
            CrewAITaskType.MEMORY_CONSOLIDATION,
            description,
            expected_output,
            CrewAIAgentRole.MEMORY_MANAGER,
            resources=resources,
            actor=actor,
            context=context,
            tools=["memory_consolidator", "pattern_detector", "knowledge_extractor"],
            **kwargs,
        )

    def task_to_crew_format(self, task: CrewAITask) -> dict[str, Any]:
        """Convert HACS task to CrewAI crew format.

        Args:
            task: CrewAI task instance

        Returns:
            Dict containing crew-formatted task
        """
        return {
            "description": task.description,
            "expected_output": task.expected_output,
            "agent": task.agent_role.value,
            "tools": task.tools,
            "context": task.context,
            "dependencies": task.dependencies,
            "priority": task.priority,
            "timeout": f"{task.timeout_minutes}m",
            "metadata": {
                "task_id": task.task_id,
                "task_type": task.task_type.value,
                "resources": task.resources,
                "actor_context": task.actor_context,
                "hacs_metadata": task.metadata,
            },
        }

    def get_task(self, task_id: str) -> CrewAITask | None:
        """Get task by ID.

        Args:
            task_id: Task ID

        Returns:
            CrewAITask or None if not found
        """
        return self.task_registry.get(task_id)

    def get_agent(self, agent_id: str) -> CrewAIAgentBinding | None:
        """Get agent binding by ID.

        Args:
            agent_id: Agent ID

        Returns:
            CrewAIAgentBinding or None if not found
        """
        return self.agent_registry.get(agent_id)


# Convenience functions for direct usage
def create_agent_binding(
    role: str,
    actor: Actor | None = None,
    specializations: list[str] | None = None,
    **kwargs,
) -> CrewAIAgentBinding:
    """Create CrewAI agent binding with HACS integration.

    Args:
        role: CrewAI agent role
        actor: Optional HACS Actor to bind
        specializations: Optional clinical specializations
        **kwargs: Additional parameters

    Returns:
        CrewAIAgentBinding instance
    """
    adapter = CrewAIAdapter()
    return adapter.create_agent_binding(
        CrewAIAgentRole(role.lower()),
        actor=actor,
        specializations=specializations,
        **kwargs,
    )


def task_to_crew_format(task: CrewAITask) -> dict[str, Any]:
    """Convert HACS task to CrewAI format.

    Args:
        task: CrewAI task instance

    Returns:
        Dict containing crew-formatted task
    """
    adapter = CrewAIAdapter()
    return adapter.task_to_crew_format(task)
