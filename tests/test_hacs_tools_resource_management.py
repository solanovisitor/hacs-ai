import os


def test_resource_management_create_minimals():
    os.environ.setdefault("PYTHONPATH", ".")

    from hacs_tools.domains import resource_management  # type: ignore

    # Patient
    r1 = resource_management.create_hacs_record(
        actor_name="Tester",
        resource_type="Patient",
        resource_data={"full_name": "Alice Validation", "gender": "female"},
    )
    assert r1.success, r1.message

    # Observation
    r2 = resource_management.create_hacs_record(
        actor_name="Tester",
        resource_type="Observation",
        resource_data={
            "status": "final",
            "code": {"text": "Blood Pressure"},
            "value_quantity": {"value": 120, "unit": "mmHg"},
        },
    )
    assert r2.success, r2.message

    # MedicationRequest
    r3 = resource_management.create_hacs_record(
        actor_name="Tester",
        resource_type="MedicationRequest",
        resource_data={
            "status": "active",
            "intent": "order",
            "subject": "Patient/test",
            "medication_codeable_concept": {"text": "Amoxicillin"},
        },
    )
    assert r3.success, r3.message

    # Procedure
    r4 = resource_management.create_hacs_record(
        actor_name="Tester",
        resource_type="Procedure",
        resource_data={
            "status": "completed",
            "code": {"text": "Appendectomy"},
            "subject": "Patient/test",
        },
    )
    assert r4.success, r4.message

    # ServiceRequest
    r5 = resource_management.create_hacs_record(
        actor_name="Tester",
        resource_type="ServiceRequest",
        resource_data={
            "status": "active",
            "intent": "order",
            "subject": "Patient/test",
            "code": {"text": "CBC"},
        },
    )
    assert r5.success, r5.message


