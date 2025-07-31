"""
HACS Agent State

Healthcare-specific state management using HACS resources for comprehensive
clinical context and structured healthcare data representation.

This module provides state schemas that leverage HACS healthcare resources
for maintaining clinical context, patient data, and healthcare workflows.
"""

from typing import Dict, List, Any, Optional, Annotated
from datetime import datetime
from pydantic import BaseModel, Field

from typing_extensions import TypedDict

from hacs_core.models import Patient, Observation, Encounter, Condition
from hacs_core.actor import Actor
from hacs_core.memory import MemoryBlock
from hacs_core.results import HACSResult


class HACSAgentState(TypedDict):
    """
    Healthcare Agent State using HACS resources for clinical context.
    
    This state schema leverages HACS healthcare resources to maintain
    comprehensive clinical context, patient information, and healthcare
    workflow state throughout agent interactions.
    """
    
    # Core LangGraph state (required fields)
    messages: List[Dict[str, Any]]
    remaining_steps: int  # Required by LangGraph
    
    # Healthcare Context using HACS Resources
    current_actor: Optional[Dict[str, Any]]  # Actor performing healthcare actions
    active_patients: Dict[str, Dict[str, Any]]  # Patient resources by ID
    clinical_observations: Dict[str, List[Dict[str, Any]]]  # Observations by patient ID
    active_encounters: Dict[str, Dict[str, Any]]  # Current healthcare encounters
    clinical_conditions: Dict[str, List[Dict[str, Any]]]  # Conditions by patient ID
    
    # Healthcare Memory and Context
    clinical_memories: List[Dict[str, Any]]  # Healthcare-specific memories
    clinical_context: Dict[str, Any]  # Current clinical workflow context
    admin_context: Dict[str, Any]  # Admin workflow context
    
    # Healthcare Workflow State
    active_workflows: List[Dict[str, Any]]  # Running clinical workflows
    pending_clinical_tasks: List[Dict[str, Any]]  # Clinical tasks to complete
    completed_clinical_tasks: List[Dict[str, Any]]  # Completed clinical actions
    pending_admin_tasks: List[Dict[str, Any]]  # Admin tasks to complete
    completed_admin_tasks: List[Dict[str, Any]]  # Completed admin actions
    active_systems: Dict[str, Dict[str, Any]]  # Active systems for admin context
    
    # Healthcare Quality and Analytics
    quality_metrics: Dict[str, Any]  # Clinical quality measures
    risk_assessments: Dict[str, Any]  # Patient risk stratifications
    
    # FHIR and Integration State
    fhir_resources: Dict[str, Any]  # FHIR-compliant resource cache
    external_integrations: Dict[str, Any]  # External healthcare system state
    
    # AI/ML Healthcare State
    deployed_models: Dict[str, Any]  # Healthcare AI models in use
    inference_results: Dict[str, List[Any]]  # AI inference results by patient
    
    # Healthcare Audit and Compliance
    audit_trail: List[Dict[str, Any]]  # Healthcare action audit log
    compliance_status: Dict[str, Any]  # Regulatory compliance tracking


class HealthcareWorkflowContext(BaseModel):
    """
    Structured healthcare workflow context using HACS resources.
    
    Provides typed access to healthcare workflow state with proper
    validation and clinical context preservation.
    """
    
    workflow_id: str = Field(description="Unique healthcare workflow identifier")
    workflow_type: str = Field(description="Type of clinical workflow")
    primary_actor: Actor = Field(description="Primary healthcare actor")
    
    # Patient Context
    primary_patient: Optional[Patient] = Field(default=None, description="Primary patient")
    related_patients: List[Patient] = Field(default_factory=list, description="Related patients")
    
    # Clinical Context
    active_observations: List[Observation] = Field(default_factory=list, description="Current observations")
    active_conditions: List[Condition] = Field(default_factory=list, description="Active conditions")
    current_encounter: Optional[Encounter] = Field(default=None, description="Current healthcare encounter")
    
    # Workflow State
    workflow_steps: List[Dict[str, Any]] = Field(default_factory=list, description="Workflow execution steps")
    current_step: str = Field(description="Current workflow step")
    next_actions: List[str] = Field(default_factory=list, description="Pending clinical actions")
    
    # Clinical Decision Support
    clinical_recommendations: List[Dict[str, Any]] = Field(default_factory=list, description="AI recommendations")
    risk_alerts: List[Dict[str, Any]] = Field(default_factory=list, description="Clinical risk alerts")
    quality_indicators: Dict[str, Any] = Field(default_factory=dict, description="Quality metrics")
    
    # Timestamps
    workflow_started: datetime = Field(default_factory=datetime.now, description="Workflow start time")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last update time")
    
    def add_clinical_observation(self, observation: Observation) -> None:
        """Add a new clinical observation to the workflow context."""
        self.active_observations.append(observation)
        self.last_updated = datetime.now()
    
    def add_clinical_recommendation(self, recommendation: Dict[str, Any]) -> None:
        """Add a clinical AI recommendation to the workflow."""
        self.clinical_recommendations.append({
            **recommendation,
            "timestamp": datetime.now().isoformat(),
            "workflow_id": self.workflow_id
        })
        self.last_updated = datetime.now()
    
    def update_workflow_step(self, step: str, actions: List[str] = None) -> None:
        """Update the current workflow step and next actions."""
        self.workflow_steps.append({
            "step": self.current_step,
            "completed_at": datetime.now().isoformat(),
            "duration_seconds": (datetime.now() - self.last_updated).total_seconds()
        })
        self.current_step = step
        self.next_actions = actions or []
        self.last_updated = datetime.now()


class HACSToolResult(BaseModel):
    """
    Structured representation of HACS tool execution results.
    
    Provides typed access to healthcare tool results with clinical
    context preservation and structured healthcare data.
    """
    
    tool_name: str = Field(description="Name of executed HACS tool")
    execution_timestamp: datetime = Field(default_factory=datetime.now)
    actor_name: str = Field(description="Healthcare actor who executed the tool")
    
    # Tool Results
    success: bool = Field(description="Whether tool execution succeeded")
    result_data: Dict[str, Any] = Field(description="Tool execution result data")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    
    # Healthcare Context
    affected_patients: List[str] = Field(default_factory=list, description="Patient IDs affected")
    clinical_significance: str = Field(default="routine", description="Clinical significance level")
    requires_follow_up: bool = Field(default=False, description="Whether follow-up is needed")
    
    # Integration with HACS Resources
    created_resources: List[Dict[str, Any]] = Field(default_factory=list, description="HACS resources created")
    modified_resources: List[Dict[str, Any]] = Field(default_factory=list, description="HACS resources modified")
    
    # Clinical Metrics
    quality_impact: Optional[Dict[str, Any]] = Field(default=None, description="Quality measure impact")
    compliance_notes: List[str] = Field(default_factory=list, description="Compliance observations")
    
    def to_hacs_result(self) -> HACSResult:
        """Convert to HACS standard result format."""
        return HACSResult(
            success=self.success,
            message=f"Tool {self.tool_name} executed by {self.actor_name}",
            data=self.result_data,
            error=self.error_message,
            actor_id=self.actor_name,
            timestamp=self.execution_timestamp
        )


def create_initial_hacs_state(
    actor_name: str = "HACS Admin Agent",
    actor_role: str = "system"
) -> HACSAgentState:
    """
    Create initial HACS agent state with healthcare-specific initialization.
    
    Args:
        actor_name: Name of the primary healthcare actor
        actor_role: Role of the primary healthcare actor
        
    Returns:
        Initialized HACSAgentState with healthcare context
    """
    
    primary_actor = Actor(name=actor_name, role=actor_role)
    
    return HACSAgentState(
        messages=[],
        remaining_steps=10,  # Default remaining steps for LangGraph
        current_actor=primary_actor.model_dump(),
        active_patients={},
        clinical_observations={},
        active_encounters={},
        clinical_conditions={},
        clinical_memories=[],
        clinical_context={
            "session_id": f"hacs_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "primary_actor": primary_actor.model_dump(),
            "session_started": datetime.now().isoformat(),
            "healthcare_context": "general_clinical"
        },
        admin_context={
            "session_id": f"admin_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "primary_actor": primary_actor.model_dump(),
            "session_started": datetime.now().isoformat(),
            "admin_context": "general_admin"
        },
        active_workflows=[],
        pending_clinical_tasks=[],
        completed_clinical_tasks=[],
        pending_admin_tasks=[],
        completed_admin_tasks=[],
        active_systems={},
        quality_metrics={},
        risk_assessments={},
        fhir_resources={},
        external_integrations={},
        deployed_models={},
        inference_results={},
        audit_trail=[{
            "action": "session_started",
            "actor": actor_name,
            "timestamp": datetime.now().isoformat(),
            "details": "HACS Deep Agent session initialized"
        }],
        compliance_status={
            "hipaa_compliant": True,
            "fhir_compliant": True,
            "audit_enabled": True
        }
    ) 