from __future__ import annotations

import warnings
from typing import Any

from pydantic import BaseModel, Field

from .utils import set_nested_field

warnings.warn(
    "StackTemplate/LayerSpec are deprecated. Use Composition + ResourceBundle and MappingSpec/SourceBinding instead.",
    DeprecationWarning,
    stacklevel=2,
)


class LayerSpec(BaseModel):
    """[DEPRECATED] Stack layer description.

    Prefer Composition + ResourceBundle and MappingSpec/SourceBinding.
    """

    resource_type: str = Field(..., description="HACS resource type (model name)")
    layer_name: str = Field(..., description="Layer/display name")
    bindings: dict[str, str] = Field(
        default_factory=dict, description="field_path -> variable_name"
    )
    constant_fields: dict[str, Any] = Field(default_factory=dict, description="Static fields")


class StackTemplate(BaseModel):
    """[DEPRECATED] Reusable template for composing resources.

    Use Composition + ResourceBundle and MappingSpec/SourceBinding instead.
    """

    name: str
    version: str = "1.0.0"
    description: str | None = None
    variables: dict[str, Any] = Field(
        default_factory=dict, description="Input variable schema or hints"
    )
    layers: list[LayerSpec] = Field(default_factory=list)


def _set_nested_field(obj: Any, path: str, value: Any) -> None:
    # Deprecated internal copy. Use utils.set_nested_field going forward.
    set_nested_field(obj, path, value)


def instantiate_stack_template(
    template: StackTemplate,
    variables: dict[str, Any],
    model_registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """[DEPRECATED] Instantiate a deprecated StackTemplate into instances.

    Returns a mapping of layer_name -> resource_instance. Prefer building a Composition
    and turning it into a ResourceBundle via Composition.to_resource_bundle().
    """
    warnings.warn(
        "instantiate_stack_template is deprecated; migrate to Composition/ResourceBundle.",
        DeprecationWarning,
        stacklevel=2,
    )
    from . import get_model_registry  # late import to avoid cycles

    registry = model_registry or get_model_registry()
    outputs: dict[str, Any] = {}
    bundle_instance = None
    for layer in template.layers:
        model_cls = registry.get(layer.resource_type)
        if model_cls is None:
            raise ValueError(f"Unknown resource_type: {layer.resource_type}")

        # Create minimal instance via registry compatibility (centralized)
        default_kwargs: dict[str, Any] = {}
        try:
            from . import validate_model_compatibility  # noqa: F401

            # Prefer instantiation with resource_type defaulting inside models
            instance = model_cls(**default_kwargs)
        except Exception:
            # Fallback: try minimal known fields
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

    # Link and bundle in ResourceBundle utilities if a bundle is present
    if bundle_instance is not None:
        try:
            from .resource_bundle import ResourceBundle

            if isinstance(bundle_instance, ResourceBundle):
                # Create a new bundle from instances to normalize entries
                new_bundle = ResourceBundle(
                    title=getattr(template, "name", None),
                    bundle_type=getattr(bundle_instance, "bundle_type", None),
                    version=getattr(template, "version", "1.0.0"),
                )
                for lname, res in outputs.items():
                    if res is bundle_instance:
                        continue
                    new_bundle.add_entry(res, title=lname)
                outputs = {k: v for k, v in outputs.items() if v is not bundle_instance}
                outputs["ResourceBundle"] = new_bundle
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
                        res.encounter = encounter_ref
                    except Exception:
                        pass
                if practitioner_ref:
                    try:
                        performers = list(getattr(res, "performer", []) or [])
                        if practitioner_ref not in performers:
                            performers.append(practitioner_ref)
                        res.performer = performers
                    except Exception:
                        pass
                if patient_ref:
                    try:
                        res.subject = patient_ref
                    except Exception:
                        pass
            elif rtype == "DiagnosticReport":
                if encounter_ref:
                    try:
                        res.encounter = encounter_ref
                    except Exception:
                        pass
                if organization_ref:
                    try:
                        performers = list(getattr(res, "performer", []) or [])
                        if organization_ref not in performers:
                            performers.append(organization_ref)
                        res.performer = performers
                    except Exception:
                        pass
                if patient_ref:
                    try:
                        res.subject = patient_ref
                    except Exception:
                        pass
            elif rtype == "MedicationRequest":
                # Ensure subject is linked to Patient if present
                if patient_ref:
                    try:
                        if not getattr(res, "subject", None):
                            res.subject = patient_ref
                    except Exception:
                        pass
            elif rtype == "Procedure":
                if patient_ref:
                    try:
                        if not getattr(res, "subject", None):
                            res.subject = patient_ref
                    except Exception:
                        pass
            elif rtype == "DocumentReference":
                if practitioner_ref:
                    try:
                        authors = list(getattr(res, "author_ref", []) or [])
                        if practitioner_ref not in authors:
                            authors.append(practitioner_ref)
                        res.author_ref = authors
                    except Exception:
                        pass
                if organization_ref:
                    try:
                        res.custodian_ref = organization_ref
                    except Exception:
                        pass
                if patient_ref:
                    try:
                        res.subject_ref = patient_ref
                    except Exception:
                        pass
    except Exception:
        pass

    return outputs
