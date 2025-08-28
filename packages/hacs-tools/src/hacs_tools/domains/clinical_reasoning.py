"""
HACS Tools: Clinical Reasoning wrappers

Thin LLM-callable tools delegating to a configured ClinicalReasoningEngine
via hacs_utils.reasoning.engine_factory. These tools do no heavy lifting;
they resolve actor/engine, perform minimal permission checks, and return
typed hacs_models resources inside HACSResult.
"""

from __future__ import annotations

from typing import Optional, Any

from hacs_registry.tool_registry import register_tool, VersionStatus
from hacs_tools.common import HACSCommonInput, HACSResult

try:
    from hacs_utils.reasoning.engine_factory import get_reasoning_engine
    from hacs_core import HACSClinicalReasoningExtensions
    from hacs_core.config import get_settings
except Exception:  # pragma: no cover
    def get_reasoning_engine():  # type: ignore
        return None
    class HACSClinicalReasoningExtensions:  # type: ignore
        @staticmethod
        def validate_agent_permissions(*args, **kwargs) -> bool:
            return True
    def get_settings():  # type: ignore
        class _S:
            current_actor = None
        return _S()


def _resolve_actor():
    settings = get_settings()
    return getattr(settings, "current_actor", None)


def _ensure_engine() -> Any:
    engine = get_reasoning_engine()
    if engine is None:
        plan = {
            "issues": [
                {"type": "configuration", "description": "No ClinicalReasoningEngine configured"}
            ],
            "suggestions": [
                "Call configure_reasoning_engine(engine) at app startup",
                "Provide a concrete engine or use MockReasoningEngine for development",
            ],
            "next_steps": [
                "See hacs_utils.reasoning.engine_factory",
            ],
        }
        raise RuntimeError(HACSResult(success=False, message="Reasoning engine missing", data={"plan": plan}))
    return engine


@register_tool(
    name="evaluate_plan_definition",
    domain="clinical_reasoning",
    tags=["clinical_reasoning"],
    status=VersionStatus.ACTIVE,
)
def evaluate_plan_definition(
    plan_definition_id: str,
    subject: Optional[str] = None,
    encounter: Optional[str] = None,
    practitioner: Optional[str] = None,
    organization: Optional[str] = None,
    **parameters: Any,
) -> HACSResult:
    actor = _resolve_actor()
    engine = _ensure_engine()
    if not HACSClinicalReasoningExtensions.validate_agent_permissions(actor, "evaluate", "PlanDefinition"):
        return HACSResult(success=False, message="Permission denied")
    try:
        guidance = engine.cds_service.evaluate_plan_definition(
            actor, plan_definition_id,
            subject=subject,
            encounter=encounter,
            practitioner=practitioner,
            organization=organization,
            **parameters,
        )
        return HACSResult(success=True, message="Evaluated plan definition", data={"resource": guidance.model_dump() if hasattr(guidance, "model_dump") else guidance})
    except RuntimeError as e:
        # Engine missing wrapper raises RuntimeError with HACSResult
        if isinstance(e.args[0], HACSResult):
            return e.args[0]
        raise


@register_tool(
    name="apply_plan_definition",
    domain="clinical_reasoning",
    tags=["clinical_reasoning"],
    status=VersionStatus.ACTIVE,
)
def apply_plan_definition(
    plan_definition_id: str,
    subject: str,
    **parameters: Any,
) -> HACSResult:
    actor = _resolve_actor()
    engine = _ensure_engine()
    if not HACSClinicalReasoningExtensions.validate_agent_permissions(actor, "apply", "PlanDefinition"):
        return HACSResult(success=False, message="Permission denied")
    try:
        result = engine.cds_service.apply_plan_definition(actor, plan_definition_id, subject, **parameters)
        return HACSResult(success=True, message="Applied plan definition", data={"resource": result.model_dump() if hasattr(result, "model_dump") else result})
    except RuntimeError as e:
        if isinstance(e.args[0], HACSResult):
            return e.args[0]
        raise


@register_tool(
    name="apply_activity_definition",
    domain="clinical_reasoning",
    tags=["clinical_reasoning"],
    status=VersionStatus.ACTIVE,
)
def apply_activity_definition(
    activity_definition_id: str,
    subject: str,
    **parameters: Any,
) -> HACSResult:
    actor = _resolve_actor()
    engine = _ensure_engine()
    if not HACSClinicalReasoningExtensions.validate_agent_permissions(actor, "apply", "ActivityDefinition"):
        return HACSResult(success=False, message="Permission denied")
    try:
        res = engine.cds_service.apply_activity_definition(actor, activity_definition_id, subject, **parameters)
        return HACSResult(success=True, message="Applied activity definition", data={"resource": res.model_dump() if hasattr(res, "model_dump") else res})
    except RuntimeError as e:
        if isinstance(e.args[0], HACSResult):
            return e.args[0]
        raise


@register_tool(
    name="evaluate_measure",
    domain="clinical_reasoning",
    tags=["clinical_reasoning"],
    status=VersionStatus.ACTIVE,
)
def evaluate_measure(
    measure_id: str,
    period_start: str,
    period_end: str,
    subject: Optional[str] = None,
    practitioner: Optional[str] = None,
    last_received_on: Optional[str] = None,
    **parameters: Any,
) -> HACSResult:
    actor = _resolve_actor()
    engine = _ensure_engine()
    if not HACSClinicalReasoningExtensions.validate_agent_permissions(actor, "evaluate", "Measure"):
        return HACSResult(success=False, message="Permission denied")
    try:
        report = engine.measure_processor.evaluate_measure(
            actor,
            measure_id,
            period_start,
            period_end,
            subject=subject,
            practitioner=practitioner,
            last_received_on=last_received_on,
            **parameters,
        )
        return HACSResult(success=True, message="Evaluated measure", data={"resource": report.model_dump() if hasattr(report, "model_dump") else report})
    except RuntimeError as e:
        if isinstance(e.args[0], HACSResult):
            return e.args[0]
        raise


@register_tool(
    name="get_data_requirements",
    domain="clinical_reasoning",
    tags=["clinical_reasoning"],
    status=VersionStatus.ACTIVE,
)
def get_data_requirements(
    artifact_type: str,
    artifact_id: str,
) -> HACSResult:
    actor = _resolve_actor()
    engine = _ensure_engine()
    if artifact_type not in {"PlanDefinition", "ActivityDefinition", "Library"}:
        return HACSResult(success=False, message="Invalid artifact_type", data={"allowed": ["PlanDefinition", "ActivityDefinition", "Library"]})
    if not HACSClinicalReasoningExtensions.validate_agent_permissions(actor, "data-requirements", artifact_type):
        return HACSResult(success=False, message="Permission denied")
    try:
        reqs = engine.cds_service.get_data_requirements(
            actor,
            plan_definition_id=artifact_id if artifact_type == "PlanDefinition" else None,
            activity_definition_id=artifact_id if artifact_type == "ActivityDefinition" else None,
            library_id=artifact_id if artifact_type == "Library" else None,
        )
        payload = [r.model_dump() if hasattr(r, "model_dump") else r for r in (reqs or [])]
        return HACSResult(success=True, message="Fetched data requirements", data={"requirements": payload})
    except RuntimeError as e:
        if isinstance(e.args[0], HACSResult):
            return e.args[0]
        raise


