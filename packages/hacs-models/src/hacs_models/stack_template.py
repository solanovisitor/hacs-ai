from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LayerSpec(BaseModel):
    """Defines one resource layer in a stack template.

    - resource_type: the HACS model name, e.g., "Patient", "Observation"
    - layer_name: human-friendly name used for grouping or bundle titles
    - bindings: mapping of target field paths to variable names, e.g.
      {"full_name": "patient_name", "agent_context.instruction": "instruction"}
    - constant_fields: static fields set directly on the resource, e.g.
      {"status": "final"}
    """

    resource_type: str = Field(..., description="HACS resource type (model name)")
    layer_name: str = Field(..., description="Layer/display name")
    bindings: Dict[str, str] = Field(default_factory=dict, description="field_path -> variable_name")
    constant_fields: Dict[str, Any] = Field(default_factory=dict, description="Static fields")


class StackTemplate(BaseModel):
    """A reusable, versioned template for composing HACS resources into a stack.

    Variables provide a schema for inputs; "layers" describes how to bind variables
    to resource fields across different HACS resource types.
    """

    name: str
    version: str = "1.0.0"
    description: Optional[str] = None
    variables: Dict[str, Any] = Field(default_factory=dict, description="Input variable schema or hints")
    layers: List[LayerSpec] = Field(default_factory=list)


def _set_nested_field(obj: Any, path: str, value: Any) -> None:
    parts = path.split(".")
    cur = obj
    for i, part in enumerate(parts):
        is_last = i == len(parts) - 1
        if is_last:
            try:
                setattr(cur, part, value)
            except Exception:
                # Fallback for dict-like structures
                if isinstance(cur, dict):
                    cur[part] = value
                else:
                    # Last resort: stash into agent_context or note when available
                    try:
                        if hasattr(cur, "agent_context") and isinstance(value, (str, int, float, bool, dict, list)):
                            ctx = getattr(cur, "agent_context") or {}
                            ctx[path] = value
                            setattr(cur, "agent_context", ctx)
                        elif hasattr(cur, "note") and isinstance(value, str):
                            notes = list(getattr(cur, "note") or [])
                            notes.append(value)
                            setattr(cur, "note", notes)
                        else:
                            raise
                    except Exception:
                        raise
        else:
            try:
                nxt = getattr(cur, part, None)
            except Exception:
                nxt = None
            if nxt is None:
                # create intermediate dict
                nxt = {}
                try:
                    setattr(cur, part, nxt)
                except Exception:
                    if isinstance(cur, dict):
                        cur[part] = nxt
                    else:
                        raise
            cur = nxt


def instantiate_stack_template(
    template: StackTemplate,
    variables: Dict[str, Any],
    model_registry: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Instantiate a template into concrete HACS resource instances.

    Returns a mapping of layer_name -> resource_instance.
    """
    from . import get_model_registry  # late import to avoid cycles

    registry = model_registry or get_model_registry()
    outputs: Dict[str, Any] = {}

    bundle_instance = None
    for layer in template.layers:
        model_cls = registry.get(layer.resource_type)
        if model_cls is None:
            raise ValueError(f"Unknown resource_type: {layer.resource_type}")

        # Create minimal instance with safe defaults for required fields
        # Provide safe defaults for common required fields
        default_kwargs: Dict[str, Any] = {}
        if layer.resource_type == "Patient":
            default_kwargs.setdefault("full_name", "Anonymous Patient")
        if layer.resource_type == "Observation":
            # minimal required fields per model definition
            from .types import ObservationStatus
            from .observation import CodeableConcept as ObsCodeableConcept, Coding as ObsCoding
            default_kwargs.setdefault("status", ObservationStatus.FINAL)
            default_kwargs.setdefault(
                "code",
                ObsCodeableConcept(coding=[ObsCoding(code="dataset_input", display="DatasetInput")], text="DatasetInput"),
            )
        if layer.resource_type == "Encounter":
            # Provide safe defaults required by Encounter
            from .types import EncounterStatus
            default_kwargs.setdefault("status", EncounterStatus.IN_PROGRESS)
            # Use alias field name for class
            default_kwargs.setdefault("class", "outpatient")
        if layer.resource_type == "MedicationRequest":
            # Provide safe defaults for required fields to reduce validation failures
            default_kwargs.setdefault("status", "active")
            # Use plain string to avoid enum serialization issues
            default_kwargs.setdefault("intent", "order")
            # Provide a temporary subject; will be replaced with actual Patient link if present
            default_kwargs.setdefault("subject", "Patient/unknown")
        if layer.resource_type == "Procedure":
            # Reasonable default status per FHIR and temporary subject
            default_kwargs.setdefault("status", "completed")
            try:
                from .observation import CodeableConcept as _CodeableConcept, Coding as _Coding
                default_kwargs.setdefault(
                    "code",
                    _CodeableConcept(coding=[_Coding(code="unspecified", display="Unspecified")], text="Unspecified"),
                )
            except Exception:
                pass
            default_kwargs.setdefault("subject", "Patient/unknown")
        if layer.resource_type == "MemoryBlock":
            # basic defaults to satisfy required fields
            default_kwargs.setdefault("memory_type", "semantic")
            default_kwargs.setdefault("content", "Auto-generated memory content")
        instance = model_cls(**default_kwargs)

        # Apply constant fields
        for field_name, field_val in layer.constant_fields.items():
            _set_nested_field(instance, field_name, field_val)

        # Apply variable bindings
        for field_path, var_name in layer.bindings.items():
            if var_name in variables:
                _set_nested_field(instance, field_path, variables[var_name])

        outputs[layer.layer_name] = instance
        # Capture top-level bundle for later linkage
        if layer.resource_type == "ResourceBundle":
            bundle_instance = instance

    # Link all non-bundle resources into the bundle as entries
    if bundle_instance is not None:
        try:
            from .resource_bundle import ResourceBundle, BundleEntry
            if isinstance(bundle_instance, ResourceBundle):
                for lname, res in outputs.items():
                    if res is bundle_instance:
                        continue
                    try:
                        bundle_instance.add_entry(res, title=lname)
                    except Exception:
                        # Fallback: append minimal entry dict
                        entries = getattr(bundle_instance, "entries", []) or []
                        entries.append({"title": lname, "contained_resource_id": getattr(res, "id", None)})
                        setattr(bundle_instance, "entries", entries)
        except Exception:
            pass

    # Establish simple references between key resources if present
    try:
        # Identify common instances
        encounter_ref = None
        practitioner_ref = None
        organization_ref = None
        patient_ref = None

        for name, res in outputs.items():
            rtype = getattr(res, "resource_type", "")
            if rtype == "Encounter" and encounter_ref is None:
                encounter_ref = f"Encounter/{getattr(res, 'id', '')}"
            elif rtype == "Practitioner" and practitioner_ref is None:
                practitioner_ref = f"Practitioner/{getattr(res, 'id', '')}"
            elif rtype == "Organization" and organization_ref is None:
                organization_ref = f"Organization/{getattr(res, 'id', '')}"
            elif rtype == "Patient" and patient_ref is None:
                patient_ref = f"Patient/{getattr(res, 'id', '')}"

        # Apply references where model fields exist
        for _, res in outputs.items():
            rtype = getattr(res, "resource_type", "")
            if rtype == "Observation":
                if encounter_ref:
                    try:
                        setattr(res, "encounter", encounter_ref)
                    except Exception:
                        pass
                if practitioner_ref:
                    try:
                        performers = list(getattr(res, "performer", []) or [])
                        if practitioner_ref not in performers:
                            performers.append(practitioner_ref)
                        setattr(res, "performer", performers)
                    except Exception:
                        pass
                if patient_ref:
                    try:
                        setattr(res, "subject", patient_ref)
                    except Exception:
                        pass
            elif rtype == "DiagnosticReport":
                if encounter_ref:
                    try:
                        setattr(res, "encounter", encounter_ref)
                    except Exception:
                        pass
                if organization_ref:
                    try:
                        performers = list(getattr(res, "performer", []) or [])
                        if organization_ref not in performers:
                            performers.append(organization_ref)
                        setattr(res, "performer", performers)
                    except Exception:
                        pass
                if patient_ref:
                    try:
                        setattr(res, "subject", patient_ref)
                    except Exception:
                        pass
            elif rtype == "MedicationRequest":
                # Ensure subject is linked to Patient if present
                if patient_ref:
                    try:
                        if not getattr(res, "subject", None):
                            setattr(res, "subject", patient_ref)
                    except Exception:
                        pass
            elif rtype == "Procedure":
                if patient_ref:
                    try:
                        if not getattr(res, "subject", None):
                            setattr(res, "subject", patient_ref)
                    except Exception:
                        pass
            elif rtype == "DocumentReference":
                if practitioner_ref:
                    try:
                        authors = list(getattr(res, "author_ref", []) or [])
                        if practitioner_ref not in authors:
                            authors.append(practitioner_ref)
                        setattr(res, "author_ref", authors)
                    except Exception:
                        pass
                if organization_ref:
                    try:
                        setattr(res, "custodian_ref", organization_ref)
                    except Exception:
                        pass
                if patient_ref:
                    try:
                        setattr(res, "subject_ref", patient_ref)
                    except Exception:
                        pass
    except Exception:
        pass

    return outputs


