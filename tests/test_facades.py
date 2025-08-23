from __future__ import annotations

from hacs_models.patient import Patient
from hacs_models.organization import Organization
from hacs_models.observation import Observation, CodeableConcept, Quantity
from hacs_models.immunization import Immunization
from hacs_models.diagnostic_report import DiagnosticReport
from hacs_models.procedure import Procedure


def test_facades_exist_and_minimal_acceptance():
    # Patient minimal: name via full_name and age
    p = Patient(resource_type="Patient", full_name="Helena", age=5)
    extractable_p = p.to_facade("extractable")
    assert extractable_p["resource_type"] == "Patient"
    assert extractable_p.get("full_name") == "Helena"
    assert extractable_p.get("age") == 5

    # Organization minimal: name-only
    o = Organization(resource_type="Organization", name="posto de saúde")
    extractable_o = o.to_facade("extractable")
    assert extractable_o["resource_type"] == "Organization"
    assert extractable_o.get("name") == "posto de saúde"

    # Observation minimal: code + value_string
    obs = Observation(
        resource_type="Observation",
        status="final",
        code=CodeableConcept(text="BP"),
        value_string="90/60",
    )
    extractable_obs = obs.to_facade("extractable")
    assert extractable_obs["resource_type"] == "Observation"
    assert (extractable_obs.get("value_string") or extractable_obs.get("value_quantity")) is not None

    # Immunization minimal: vaccine_code.text
    imm = Immunization(resource_type="Immunization", vaccine_code=CodeableConcept(text="pneumo 13"))
    extractable_imm = imm.to_facade("extractable")
    assert extractable_imm["resource_type"] == "Immunization"
    assert (extractable_imm.get("vaccine_code") or {}).get("text") == "pneumo 13"

    # DiagnosticReport minimal: code.text and optional conclusion
    dr = DiagnosticReport(resource_type="DiagnosticReport", status="final", code=CodeableConcept(text="teste do pezinho"))
    extractable_dr = dr.to_facade("extractable")
    assert extractable_dr["resource_type"] == "DiagnosticReport"
    assert (extractable_dr.get("code") or {}).get("text") == "teste do pezinho"

    # Procedure minimal: code.text and optional performed_date_time
    proc = Procedure(
        resource_type="Procedure",
        status="completed",
        code=CodeableConcept(text="aspiração"),
        subject="Patient/UNKNOWN",
    )
    extractable_proc = proc.to_facade("extractable")
    assert extractable_proc["resource_type"] == "Procedure"
    assert (extractable_proc.get("code") or {}).get("text") == "aspiração"


