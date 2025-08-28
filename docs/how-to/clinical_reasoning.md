# Clinical Reasoning (Protocols)

HACS exposes FHIR Clinical Reasoning–aligned protocols (no implementations) in `hacs_core`.
This guide shows how to wire an engine and call it via HACS tools.

## Concepts

- Knowledge artifacts: `PlanDefinition`, `ActivityDefinition`, `Library`
- Execution artifacts: `RequestGroup`, `GuidanceResponse`, `CarePlan`
- Measures: `Measure`, `MeasureReport`, `DataRequirement`
- Protocols (contracts only): `KnowledgeRepository`, `ClinicalDecisionSupportService`, `MeasureProcessor`, `ExpressionEngine`, `ClinicalReasoningEngine`

## Configure an Engine

```python
from hacs_utils.reasoning.engine_factory import configure_reasoning_engine, MockReasoningEngine
from hacs_core.config import get_settings
from hacs_models import Actor

# Configure your actor (auth)
settings = get_settings()
settings.current_actor = Actor(name="cds-agent", role="agent")

# Register a reasoning engine (mock for local dev)
configure_reasoning_engine(MockReasoningEngine())
```

## Call Tools

```python
from hacs_tools.domains.clinical_reasoning import (
    evaluate_plan_definition,
    apply_plan_definition,
    apply_activity_definition,
    evaluate_measure,
    get_data_requirements,
)

# Evaluate PlanDefinition (guidance)
res = evaluate_plan_definition(plan_definition_id="pd-1", subject="Patient/123")
assert res.success
print(res.data["resource"])  # GuidanceResponse (typed dict)

# Apply PlanDefinition (orchestration)
res = apply_plan_definition(plan_definition_id="pd-1", subject="Patient/123")
assert res.success
print(res.data["resource"])  # RequestGroup

# Apply ActivityDefinition (specific resource)
res = apply_activity_definition(activity_definition_id="ad-1", subject="Patient/123")
assert res.success
print(res.data["resource"])  # e.g., ServiceRequest

# Evaluate a measure
res = evaluate_measure(measure_id="m-1", period_start="2024-01-01", period_end="2024-12-31")
assert res.success
print(res.data["resource"])  # MeasureReport

# Data requirements
res = get_data_requirements(artifact_type="PlanDefinition", artifact_id="pd-1")
assert res.success
print(len(res.data["requirements"]))
```

## Compose with Modeling & Persistence

Use existing tools to validate and save:

```python
from hacs_tools.domains.modeling import validate_resource
from hacs_tools.domains.database import save_resource

req_group = apply_plan_definition("pd-1", subject="Patient/123").data["resource"]
val = validate_resource(req_group)
assert val.success
sav = save_resource(resource=val.data["resource"])  # async in real usage
```

## Notes

- If no engine is configured, tools return an actionable plan explaining how to configure one.
- In production, replace the mock with your concrete engine adapter (CDS Hooks, internal rules, etc.).
