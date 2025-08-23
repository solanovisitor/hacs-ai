from __future__ import annotations

from typing import Optional

from hacs_models.observation import Observation, CodeableConcept, Quantity
from hacs_models.types import ObservationStatus
from hacs_utils.terminology.helpers import loinc_for


def set_quantity(observation: Observation, value: float, unit: str, system: Optional[str] = None) -> Observation:
    observation.value_quantity = Quantity(value=value, unit=unit, system=system or "http://unitsofmeasure.org")
    observation.update_timestamp()
    return observation


def add_category(observation: Observation, text: str) -> Observation:
    observation.add_category(category_code=text, category_display=text)
    return observation


def ensure_code_text(observation: Observation, text: str) -> Observation:
    if not observation.code or not observation.code.text:
        observation.code = CodeableConcept(text=text)
    return observation


def create_vital_observation(
    metric_key: str,
    value: float,
    unit: str,
    *,
    subject_ref: Optional[str] = None,
) -> Observation:
    """Create a basic vital-sign Observation with LOINC code and quantity value."""
    obs = Observation(status=ObservationStatus.FINAL, code=CodeableConcept(text=metric_key))
    code_cc = loinc_for(metric_key)
    if code_cc:
        obs.code = code_cc
    if subject_ref:
        obs.subject = subject_ref
    set_quantity(obs, value, unit)
    add_category(obs, "vital-signs")
    return obs


def get_observation_value_summary(observation_data: dict) -> str:
    if "value_quantity" in observation_data:
        qty = observation_data["value_quantity"]
        value = qty.get("value")
        unit = qty.get("unit", "")
        if value is not None:
            return f"{value} {unit}".strip()
    if "value_string" in observation_data:
        return str(observation_data["value_string"])
    if "value_boolean" in observation_data:
        return "Yes" if observation_data["value_boolean"] else "No"
    if "value_codeable_concept" in observation_data:
        concept = observation_data["value_codeable_concept"]
        if isinstance(concept, dict) and "text" in concept:
            return concept["text"]
    return "No value recorded"


def compute_bmi_and_derived(
    weight_obs: Observation | dict | None,
    height_obs: Observation | dict | None,
    *,
    subject_ref: str | None = None,
) -> tuple[Observation | None, list[str]]:
    """
    Compute BMI when weight (kg) and height (cm or m) are available.
    - Accepts Observation models or dicts with value_quantity.
    - Returns (bmi_observation, derived_from_refs)
    """

    def _extract_value_qty(o: Observation | dict | None) -> tuple[float | None, str | None]:
        if o is None:
            return None, None
        if isinstance(o, Observation):
            if o.value_quantity and o.value_quantity.value is not None:
                return float(o.value_quantity.value), (o.value_quantity.unit or None)
            return None, None
        # dict
        vq = o.get("value_quantity") or {}
        val = vq.get("value")
        unit = vq.get("unit")
        return (float(val) if val is not None else None), unit

    weight_val, weight_unit = _extract_value_qty(weight_obs)
    height_val, height_unit = _extract_value_qty(height_obs)

    if weight_val is None or height_val is None:
        return None, []

    # Normalize units
    # weight: expect kg; if g provided, convert
    if weight_unit and weight_unit.lower() in {"g", "gram", "grams"}:
        weight_val = weight_val / 1000.0
        weight_unit = "kg"
    if not weight_unit or weight_unit.lower() not in {"kg", "kilogram", "kilograms"}:
        # Unknown unit; bail out to avoid wrong BMI
        return None, []

    # height: allow cm or m
    meters: float
    if height_unit and height_unit.lower() in {"cm", "centimeter", "centimeters"}:
        meters = height_val / 100.0
    elif height_unit and height_unit.lower() in {"m", "meter", "meters"}:
        meters = height_val
    else:
        return None, []

    if meters <= 0:
        return None, []

    bmi = round(weight_val / (meters * meters), 2)

    bmi_obs = Observation(
        status=ObservationStatus.FINAL,
        code=CodeableConcept(text="Body mass index"),
        category=[CodeableConcept(text="vital-signs")],
        subject=subject_ref,
    )
    bmi_obs.set_quantity_value(bmi, unit="kg/m2")

    derived_refs: list[str] = []
    def _ref_for(o: Observation | dict | None) -> str | None:
        if o is None:
            return None
        if isinstance(o, Observation) and hasattr(o, "to_reference"):
            return o.to_reference()
        # dict forms may already contain 'id' and 'resource_type'
        if isinstance(o, dict) and o.get("resource_type") == "Observation" and o.get("id"):
            return f"Observation/{o['id']}"
        return None

    wref = _ref_for(weight_obs)
    href = _ref_for(height_obs)
    for r in (wref, href):
        if r:
            derived_refs.append(r)
    bmi_obs.derived_from = derived_refs

    return bmi_obs, derived_refs


