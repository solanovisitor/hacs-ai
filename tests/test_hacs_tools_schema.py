import os


def test_schema_discovery_core_models():
    # Ensure imports resolve using repo layout
    os.environ.setdefault("PYTHONPATH", ".")

    from hacs_tools.domains import schema_discovery  # type: ignore

    core = [
        "Patient",
        "Observation",
        "Encounter",
        "Condition",
        "Medication",
        "MedicationRequest",
        "Procedure",
        "Goal",
        "ServiceRequest",
        "DiagnosticReport",
    ]

    failures: list[str] = []
    for rt in core:
        res = schema_discovery.get_hacs_resource_schema(
            rt, include_examples=False, include_validation_rules=True
        )
        if not res.success or res.field_count <= 0:
            failures.append(f"{rt}: success={res.success}, fields={res.field_count}")

    assert not failures, f"Schema discovery failed: {failures}"


