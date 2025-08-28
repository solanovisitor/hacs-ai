"""
Reasoning engine factory and DI glue for HACS Clinical Reasoning.

This module wires concrete clinical reasoning engines (or a mock) into
the HACS environment so tools can delegate operations without coupling
to any specific backend.
"""

from __future__ import annotations

from typing import Optional, Any, List

try:
    # Protocols and DI utilities from hacs-core
    from hacs_core import (
        ClinicalReasoningEngine,
        KnowledgeRepository,
        ClinicalDecisionSupportService,
        MeasureProcessor,
        ExpressionEngine,
    )
    from hacs_core import register_provider, get_provider  # type: ignore
    from hacs_core.config import get_settings  # type: ignore
except Exception:  # pragma: no cover
    ClinicalReasoningEngine = object  # type: ignore
    KnowledgeRepository = object  # type: ignore
    ClinicalDecisionSupportService = object  # type: ignore
    MeasureProcessor = object  # type: ignore
    ExpressionEngine = object  # type: ignore
    def register_provider(*args, **kwargs):  # type: ignore
        return None
    def get_provider(*args, **kwargs):  # type: ignore
        raise LookupError("No provider registry available")
    def get_settings():  # type: ignore
        class _S:  # minimal fallback
            pass
        return _S()

try:
    from hacs_models import Actor, BaseResource
except Exception:  # pragma: no cover
    Actor = object  # type: ignore
    BaseResource = object  # type: ignore


def configure_reasoning_engine(engine: ClinicalReasoningEngine) -> None:
    """Register the reasoning engine in DI and settings (if available)."""
    try:
        register_provider(ClinicalReasoningEngine, engine)
    except Exception:
        pass
    try:
        settings = get_settings()
        setattr(settings, "reasoning_engine", engine)
    except Exception:
        pass


def get_reasoning_engine() -> Optional[ClinicalReasoningEngine]:
    """Resolve a reasoning engine from DI or settings.

    Returns None if no engine is configured.
    """
    # Try DI registry first
    try:
        return get_provider(ClinicalReasoningEngine)  # type: ignore[return-value]
    except Exception:
        pass
    # Fallback to settings
    try:
        settings = get_settings()
        engine = getattr(settings, "reasoning_engine", None)
        if engine is not None:
            return engine  # type: ignore[return-value]
    except Exception:
        pass
    return None


# -----------------------------
# Mock implementation for local dev
# -----------------------------

class _MockKnowledgeRepository:
    def search_plan_definitions(self, actor: Actor, **kwargs: Any) -> List[BaseResource]:  # type: ignore[override]
        return []

    def search_activity_definitions(self, actor: Actor, **kwargs: Any) -> List[BaseResource]:  # type: ignore[override]
        return []

    def search_libraries(self, actor: Actor, **kwargs: Any) -> List[BaseResource]:  # type: ignore[override]
        return []

    def get_plan_definition(self, actor: Actor, id: str) -> Optional[BaseResource]:  # type: ignore[override]
        return None

    def get_activity_definition(self, actor: Actor, id: str) -> Optional[BaseResource]:  # type: ignore[override]
        return None

    def get_library(self, actor: Actor, id: str) -> Optional[BaseResource]:  # type: ignore[override]
        return None

    def store_knowledge_artifact(self, actor: Actor, artifact: BaseResource) -> str:  # type: ignore[override]
        return "artifact-unknown"

    def update_knowledge_artifact(self, actor: Actor, id: str, artifact: BaseResource) -> bool:  # type: ignore[override]
        return True

    def delete_knowledge_artifact(self, actor: Actor, id: str) -> bool:  # type: ignore[override]
        return True


class _MockCDSService:
    def evaluate_plan_definition(self, actor: Actor, plan_definition_id: str, **parameters: Any) -> BaseResource:  # type: ignore[override]
        # Minimal typed BaseResource fallback
        return BaseResource(resource_type="GuidanceResponse")  # type: ignore[call-arg]

    def apply_plan_definition(self, actor: Actor, plan_definition_id: str, subject: str, **parameters: Any) -> BaseResource:  # type: ignore[override]
        return BaseResource(resource_type="RequestGroup")  # type: ignore[call-arg]

    def apply_activity_definition(self, actor: Actor, activity_definition_id: str, subject: str, **parameters: Any) -> BaseResource:  # type: ignore[override]
        return BaseResource(resource_type="ServiceRequest")  # type: ignore[call-arg]

    def get_data_requirements(self, actor: Actor, plan_definition_id: Optional[str] = None, activity_definition_id: Optional[str] = None, library_id: Optional[str] = None) -> List[BaseResource]:  # type: ignore[override]
        return []

    def validate_guidance_request(self, actor: Actor, request: dict[str, Any]) -> dict[str, Any]:  # type: ignore[override]
        return {"valid": True}

    def get_supported_hooks(self, actor: Actor) -> list[dict[str, Any]]:  # type: ignore[override]
        return []


class _MockMeasureProcessor:
    def evaluate_measure(self, actor: Actor, measure_id: str, period_start: str, period_end: str, **parameters: Any) -> BaseResource:  # type: ignore[override]
        return BaseResource(resource_type="MeasureReport")  # type: ignore[call-arg]

    def collect_data(self, actor: Actor, measure_id: str, period_start: str, period_end: str, **parameters: Any) -> BaseResource:  # type: ignore[override]
        return BaseResource(resource_type="Parameters")  # type: ignore[call-arg]

    def submit_data(self, actor: Actor, measure_report: BaseResource) -> dict[str, Any]:  # type: ignore[override]
        return {"submitted": True}

    def get_care_gaps(self, actor: Actor, period_start: str, period_end: str, **parameters: Any) -> List[BaseResource]:  # type: ignore[override]
        return []

    def get_measure_data_requirements(self, actor: Actor, measure_id: str) -> List[BaseResource]:  # type: ignore[override]
        return []


class _MockExpressionEngine:
    def evaluate_expression(self, actor: Actor, expression: str, language: str, context: dict[str, Any], parameters: Optional[dict[str, Any]] = None) -> Any:  # type: ignore[override]
        return True

    def validate_expression(self, actor: Actor, expression: str, language: str) -> dict[str, Any]:  # type: ignore[override]
        return {"valid": True}

    def get_supported_languages(self, actor: Actor) -> list[str]:  # type: ignore[override]
        return ["text/fhirpath", "text/cql"]

    def parse_data_requirements(self, actor: Actor, expression: str, language: str) -> List[BaseResource]:  # type: ignore[override]
        return []


class MockReasoningEngine(ClinicalReasoningEngine):  # type: ignore[misc]
    """Minimal engine wiring mock components for local development."""

    def __init__(self) -> None:
        super().__init__(
            knowledge_repository=_MockKnowledgeRepository(),
            cds_service=_MockCDSService(),
            measure_processor=_MockMeasureProcessor(),
            expression_engine=_MockExpressionEngine(),
        )

    # Abstract methods (unused in tool wrappers) implemented minimally
    def evaluate_clinical_scenario(self, actor: Actor, scenario: dict[str, Any]) -> dict[str, Any]:  # type: ignore[override]
        return {"status": "ok"}

    def process_clinical_workflow(self, actor: Actor, workflow_id: str, context: dict[str, Any]) -> dict[str, Any]:  # type: ignore[override]
        return {"status": "ok"}

    def assess_quality_measures(self, actor: Actor, patient_id: str, measure_ids: list[str], period_start: str, period_end: str) -> dict[str, Any]:  # type: ignore[override]
        return {"status": "ok"}

    def get_clinical_guidance(self, actor: Actor, patient_context: dict[str, Any], guidance_request: dict[str, Any]) -> dict[str, Any]:  # type: ignore[override]
        return {"status": "ok"}


