"""
Clinical Reasoning protocols for HACS.

Based on FHIR R5 Clinical Reasoning module specifications for knowledge services,
clinical decision support, and measure processing.
"""

from abc import ABC, abstractmethod
from typing import Any, Protocol

from .actor import Actor
from .base_resource import BaseResource


class KnowledgeRepository(Protocol):
    """
    Protocol for a FHIR Clinical Reasoning Knowledge Repository service.

    Defines minimum capabilities for a knowledge repository as specified in FHIR CR module.
    Supports sharing and distribution of knowledge artifacts.
    """

    @abstractmethod
    def search_plan_definitions(
        self,
        actor: Actor,
        identifier: str | None = None,
        name: str | None = None,
        title: str | None = None,
        status: str | None = None,
        type: str | None = None,
        topic: str | None = None,
        context: str | None = None,
        **kwargs: Any,
    ) -> list[BaseResource]:
        """Search for plan definitions."""
        pass

    @abstractmethod
    def search_activity_definitions(
        self,
        actor: Actor,
        identifier: str | None = None,
        name: str | None = None,
        title: str | None = None,
        status: str | None = None,
        kind: str | None = None,
        topic: str | None = None,
        **kwargs: Any,
    ) -> list[BaseResource]:
        """Search for activity definitions."""
        pass

    @abstractmethod
    def search_libraries(
        self,
        actor: Actor,
        identifier: str | None = None,
        name: str | None = None,
        title: str | None = None,
        status: str | None = None,
        type: str | None = None,
        **kwargs: Any,
    ) -> list[BaseResource]:
        """Search for libraries."""
        pass

    @abstractmethod
    def get_plan_definition(self, actor: Actor, id: str) -> BaseResource | None:
        """Retrieve a specific plan definition."""
        pass

    @abstractmethod
    def get_activity_definition(self, actor: Actor, id: str) -> BaseResource | None:
        """Retrieve a specific activity definition."""
        pass

    @abstractmethod
    def get_library(self, actor: Actor, id: str) -> BaseResource | None:
        """Retrieve a specific library."""
        pass

    @abstractmethod
    def store_knowledge_artifact(self, actor: Actor, artifact: BaseResource) -> str:
        """Store a knowledge artifact and return its ID."""
        pass

    @abstractmethod
    def update_knowledge_artifact(
        self, actor: Actor, id: str, artifact: BaseResource
    ) -> bool:
        """Update an existing knowledge artifact."""
        pass

    @abstractmethod
    def delete_knowledge_artifact(self, actor: Actor, id: str) -> bool:
        """Delete a knowledge artifact."""
        pass


class ClinicalDecisionSupportService(Protocol):
    """
    Protocol for a Clinical Decision Support (CDS) service.

    Based on FHIR Clinical Reasoning CDS service specifications.
    Provides clinical decision support guidance and recommendations.
    """

    @abstractmethod
    def evaluate_plan_definition(
        self,
        actor: Actor,
        plan_definition_id: str,
        subject: str | None = None,
        encounter: str | None = None,
        practitioner: str | None = None,
        organization: str | None = None,
        user_type: str | None = None,
        user_language: str | None = None,
        user_task_context: str | None = None,
        setting: str | None = None,
        setting_context: str | None = None,
        **parameters: Any,
    ) -> BaseResource:
        """
        Evaluate a plan definition and return guidance response.

        Implements the $evaluate operation for PlanDefinition.
        """
        pass

    @abstractmethod
    def apply_plan_definition(
        self,
        actor: Actor,
        plan_definition_id: str,
        subject: str,
        encounter: str | None = None,
        practitioner: str | None = None,
        organization: str | None = None,
        user_type: str | None = None,
        user_language: str | None = None,
        user_task_context: str | None = None,
        setting: str | None = None,
        setting_context: str | None = None,
        **parameters: Any,
    ) -> BaseResource:
        """
        Apply a plan definition to a specific subject and return request orchestration.

        Implements the $apply operation for PlanDefinition.
        """
        pass

    @abstractmethod
    def apply_activity_definition(
        self,
        actor: Actor,
        activity_definition_id: str,
        subject: str,
        encounter: str | None = None,
        practitioner: str | None = None,
        organization: str | None = None,
        **parameters: Any,
    ) -> BaseResource:
        """
        Apply an activity definition to create a specific resource.

        Implements the $apply operation for ActivityDefinition.
        """
        pass

    @abstractmethod
    def get_data_requirements(
        self,
        actor: Actor,
        plan_definition_id: str | None = None,
        activity_definition_id: str | None = None,
        library_id: str | None = None,
    ) -> list[BaseResource]:
        """
        Get data requirements for a knowledge artifact.

        Implements the $data-requirements operation.
        """
        pass

    @abstractmethod
    def validate_guidance_request(
        self, actor: Actor, request: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate a guidance request."""
        pass

    @abstractmethod
    def get_supported_hooks(self, actor: Actor) -> list[dict[str, Any]]:
        """Get supported CDS Hooks if implementing CDS Hooks."""
        pass


class MeasureProcessor(Protocol):
    """
    Protocol for a Measure Processor service.

    Based on FHIR Clinical Reasoning Measure Processor specifications.
    Provides clinical quality measure evaluation capabilities.
    """

    @abstractmethod
    def evaluate_measure(
        self,
        actor: Actor,
        measure_id: str,
        period_start: str,
        period_end: str,
        subject: str | None = None,
        practitioner: str | None = None,
        last_received_on: str | None = None,
        **parameters: Any,
    ) -> BaseResource:
        """
        Evaluate a measure and return measure report.

        Implements the $evaluate-measure operation for Measure.
        """
        pass

    @abstractmethod
    def collect_data(
        self,
        actor: Actor,
        measure_id: str,
        period_start: str,
        period_end: str,
        subject: str | None = None,
        practitioner: str | None = None,
        last_received_on: str | None = None,
        **parameters: Any,
    ) -> BaseResource:
        """
        Collect data requirements for a measure.

        Implements the $collect-data operation for Measure.
        """
        pass

    @abstractmethod
    def submit_data(self, actor: Actor, measure_report: BaseResource) -> dict[str, Any]:
        """
        Submit measure report data.

        Implements the $submit-data operation.
        """
        pass

    @abstractmethod
    def get_care_gaps(
        self,
        actor: Actor,
        period_start: str,
        period_end: str,
        topic: str | None = None,
        subject: str | None = None,
        **parameters: Any,
    ) -> list[BaseResource]:
        """
        Identify care gaps.

        Implements the $care-gaps operation.
        """
        pass

    @abstractmethod
    def get_measure_data_requirements(
        self, actor: Actor, measure_id: str
    ) -> list[BaseResource]:
        """Get data requirements for a measure."""
        pass


class ExpressionEngine(Protocol):
    """
    Protocol for expression evaluation engines.

    Supports FHIRPath, CQL, and other expression languages for clinical reasoning.
    """

    @abstractmethod
    def evaluate_expression(
        self,
        actor: Actor,
        expression: str,
        language: str,
        context: dict[str, Any],
        parameters: dict[str, Any] | None = None,
    ) -> Any:
        """Evaluate an expression in the given context."""
        pass

    @abstractmethod
    def validate_expression(
        self, actor: Actor, expression: str, language: str
    ) -> dict[str, Any]:
        """Validate an expression syntax."""
        pass

    @abstractmethod
    def get_supported_languages(self, actor: Actor) -> list[str]:
        """Get supported expression languages."""
        pass

    @abstractmethod
    def parse_data_requirements(
        self, actor: Actor, expression: str, language: str
    ) -> list[BaseResource]:
        """Parse data requirements from an expression."""
        pass


class ClinicalReasoningEngine(ABC):
    """
    Abstract base class for clinical reasoning engines.

    Integrates knowledge repository, CDS service, measure processor, and expression engine
    to provide comprehensive clinical reasoning capabilities.
    """

    def __init__(
        self,
        knowledge_repository: KnowledgeRepository,
        cds_service: ClinicalDecisionSupportService,
        measure_processor: MeasureProcessor,
        expression_engine: ExpressionEngine,
    ):
        """Initialize the clinical reasoning engine."""
        self.knowledge_repository = knowledge_repository
        self.cds_service = cds_service
        self.measure_processor = measure_processor
        self.expression_engine = expression_engine

    @abstractmethod
    def evaluate_clinical_scenario(
        self, actor: Actor, scenario: dict[str, Any]
    ) -> dict[str, Any]:
        """Evaluate a complete clinical scenario and provide recommendations."""
        pass

    @abstractmethod
    def process_clinical_workflow(
        self, actor: Actor, workflow_id: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Process a clinical workflow end-to-end."""
        pass

    @abstractmethod
    def assess_quality_measures(
        self,
        actor: Actor,
        patient_id: str,
        measure_ids: list[str],
        period_start: str,
        period_end: str,
    ) -> dict[str, Any]:
        """Assess quality measures for a patient."""
        pass

    @abstractmethod
    def get_clinical_guidance(
        self,
        actor: Actor,
        patient_context: dict[str, Any],
        guidance_request: dict[str, Any],
    ) -> dict[str, Any]:
        """Get clinical guidance for a specific patient context."""
        pass


class ClinicalReasoningOperations:
    """
    HACS implementation of FHIR Clinical Reasoning operations.

    Provides concrete implementations of the standard FHIR CR operations
    with HACS-specific enhancements for healthcare agents.
    """

    def __init__(self, reasoning_engine: ClinicalReasoningEngine):
        """Initialize with a clinical reasoning engine."""
        self.reasoning_engine = reasoning_engine

    def plan_definition_evaluate(
        self, actor: Actor, plan_definition_id: str, **parameters: Any
    ) -> BaseResource:
        """$evaluate operation for PlanDefinition."""
        return self.reasoning_engine.cds_service.evaluate_plan_definition(
            actor, plan_definition_id, **parameters
        )

    def plan_definition_apply(
        self, actor: Actor, plan_definition_id: str, subject: str, **parameters: Any
    ) -> BaseResource:
        """$apply operation for PlanDefinition."""
        return self.reasoning_engine.cds_service.apply_plan_definition(
            actor, plan_definition_id, subject, **parameters
        )

    def activity_definition_apply(
        self, actor: Actor, activity_definition_id: str, subject: str, **parameters: Any
    ) -> BaseResource:
        """$apply operation for ActivityDefinition."""
        return self.reasoning_engine.cds_service.apply_activity_definition(
            actor, activity_definition_id, subject, **parameters
        )

    def measure_evaluate(
        self,
        actor: Actor,
        measure_id: str,
        period_start: str,
        period_end: str,
        **parameters: Any,
    ) -> BaseResource:
        """$evaluate-measure operation for Measure."""
        return self.reasoning_engine.measure_processor.evaluate_measure(
            actor, measure_id, period_start, period_end, **parameters
        )

    def library_evaluate(
        self, actor: Actor, library_id: str, context: dict[str, Any], **parameters: Any
    ) -> dict[str, Any]:
        """$evaluate operation for Library."""
        # Get the library
        library = self.reasoning_engine.knowledge_repository.get_library(
            actor, library_id
        )
        if not library:
            raise ValueError(f"Library {library_id} not found")

        # Evaluate expressions in the library
        results = {}
        # Implementation would depend on the specific library content
        # This is a simplified version
        return results

    def get_data_requirements(
        self, actor: Actor, artifact_id: str, artifact_type: str = "PlanDefinition"
    ) -> list[BaseResource]:
        """$data-requirements operation for knowledge artifacts."""
        if artifact_type == "PlanDefinition":
            return self.reasoning_engine.cds_service.get_data_requirements(
                actor, plan_definition_id=artifact_id
            )
        elif artifact_type == "ActivityDefinition":
            return self.reasoning_engine.cds_service.get_data_requirements(
                actor, activity_definition_id=artifact_id
            )
        elif artifact_type == "Library":
            return self.reasoning_engine.cds_service.get_data_requirements(
                actor, library_id=artifact_id
            )
        else:
            raise ValueError(f"Unsupported artifact type: {artifact_type}")


# HACS-specific enhancements for clinical reasoning


class HACSClinicalReasoningExtensions:
    """
    HACS-specific extensions to FHIR Clinical Reasoning.

    Provides agent-centric enhancements for healthcare agent communication.
    """

    @staticmethod
    def enhance_guidance_with_agent_context(
        guidance_response: BaseResource, agent_context: dict[str, Any]
    ) -> BaseResource:
        """Enhance guidance response with agent-specific context."""
        # Add agent context to the guidance response
        if hasattr(guidance_response, "agent_context"):
            guidance_response.agent_context.update(agent_context)
        return guidance_response

    @staticmethod
    def create_agent_friendly_recommendation(
        guidance_response: BaseResource, llm_friendly: bool = True
    ) -> dict[str, Any]:
        """Create LLM-friendly recommendation format."""
        recommendation = {
            "status": getattr(guidance_response, "status", "unknown"),
            "confidence": getattr(guidance_response, "confidence_score", None),
            "recommendations": getattr(guidance_response, "recommendations", []),
            "alerts": getattr(guidance_response, "alerts", []),
            "next_actions": [],
            "reasoning": getattr(guidance_response, "evaluation_message", []),
        }

        if llm_friendly:
            # Simplify for LLM consumption
            recommendation["summary"] = (
                f"Clinical guidance with {len(recommendation['recommendations'])} recommendations"
            )
            if recommendation["confidence"]:
                recommendation["summary"] += (
                    f" (confidence: {recommendation['confidence']:.2f})"
                )

        return recommendation

    @staticmethod
    def validate_agent_permissions(
        actor: Actor, operation: str, resource_type: str
    ) -> bool:
        """Validate that an agent has permissions for clinical reasoning operations."""
        # Implementation would check actor permissions
        # This is a simplified version
        return True
