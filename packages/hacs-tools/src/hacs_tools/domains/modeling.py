"""
HACS Modeling Tools - Resource Definition, Composition, and Validation

This domain provides tools for creating, composing, validating, and versioning HACS resources.
These are the foundational modeling primitives that enable any HACS resource creation,
versioning, and validation, making resources ready for registry and use within a scope.

Domain Focus:
- Resource instantiation from JSON/specs
- Resource composition into bundles and documents
- Resource validation and integrity checks
- Resource diffing and versioning
"""

import logging
import inspect
from typing import Dict, List, Any, Optional, Set

from hacs_models import HACSResult, BaseResource, DomainResource, Reference
from hacs_registry.tool_registry import register_tool, VersionStatus, get_global_registry as get_tool_registry

try:
    from pydantic import BaseModel, Field
except Exception:  # pragma: no cover

    class BaseModel:  # type: ignore
        pass

    def Field(*args, **kwargs):  # type: ignore
        return None

# Import common input schema
from hacs_tools.common import HACSCommonInput, build_error_plan


from hacs_models import get_model_registry, ResourceBundle, BundleEntry, Document
from hacs_models.utils import set_nested_field
# from hacs_utils.structured import extract  # Temporarily disabled
# Tool domain: modeling - Resource instantiation, validation, composition, diffing

logger = logging.getLogger(__name__)


class PinResourceInput(HACSCommonInput):
    resource_type: str = Field(description="HACS resource type (e.g., Patient)")
    resource_data: Dict[str, Any] = Field(description="Resource payload")


@register_tool(
    name="pin_resource", domain="modeling", tags=["domain:modeling"], status=VersionStatus.ACTIVE
)
def pin_resource(resource_type: str, resource_data: Dict[str, Any]) -> HACSResult:
    """
    Instantiate a HACS resource from a resource type string and data dictionary.

    Args:
        resource_type: The HACS resource type (e.g., "Patient", "Condition", "Document")
        resource_data: Dictionary containing the resource data fields

    Returns:
        HACSResult with the instantiated resource or error details
    """
    try:
        # Get the model class from registry
        model_registry = get_model_registry()
        resource_class = model_registry.get(resource_type)

        if not resource_class:
            return HACSResult(
                success=False,
                message=f"Unknown resource type: {resource_type}",
                error=f"Resource type '{resource_type}' not found in model registry. Available types: {list(model_registry.keys())}",
            )

        # Instantiate the resource
        resource = resource_class(**resource_data)

        return HACSResult(
            success=True,
            message=f"Successfully instantiated {resource_type}",
            data={"resource": resource.model_dump(), "resource_type": resource_type},
        )

    except Exception as e:
        return HACSResult(
            success=False, message=f"Failed to instantiate {resource_type}", error=str(e)
        )


# Attach explicit args model for integrations
pin_resource._tool_args = PinResourceInput  # type: ignore[attr-defined]


def pin_resources(items: List[Dict[str, Any]]) -> HACSResult:
    """
    Instantiate multiple HACS resources.

    Each item should be {"resource_type": str, "resource_data": dict}.
    """
    results: List[Dict[str, Any]] = []
    for item in items or []:
        rtype = item.get("resource_type")
        rdata = item.get("resource_data", {})
        single = pin_resource(rtype, rdata)
        results.append(
            {
                "success": single.success,
                "message": single.message,
                "resource_type": rtype,
                "resource": (single.data or {}).get("resource") if single.success else None,
                "error": single.error,
            }
        )
    return HACSResult(
        success=all(r["success"] for r in results),
        message=f"Instantiated {len(results)} resources",
        data={"results": results},
    )


class ComposeBundleInput(HACSCommonInput):
    entries: List[Dict[str, Any]]
    bundle_type: str = Field(default="document")
    title: Optional[str] = None
    description: Optional[str] = None


@register_tool(
    name="compose_bundle", domain="modeling", tags=["domain:modeling"], status=VersionStatus.ACTIVE
)
def compose_bundle(
    entries: List[Dict[str, Any]],
    bundle_type: str = "document",
    title: Optional[str] = None,
    description: Optional[str] = None,
) -> HACSResult:
    """
    Compose a ResourceBundle from a list of resource entries.

    Args:
        entries: List of entries, each with resource_data, title, tags, priority
        bundle_type: Type of bundle ("document", "stack", "template")
        title: Optional bundle title
        description: Optional bundle description

    Returns:
        HACSResult with the composed ResourceBundle
    """
    try:
        # Convert entries to BundleEntry objects
        bundle_entries = []

        for entry_data in entries:
            # Extract components
            resource_data = entry_data.get("resource_data", {})
            entry_title = entry_data.get("title", "")
            tags = entry_data.get("tags", [])
            priority = entry_data.get("priority", 5)

            # Get resource type and instantiate if needed
            resource_type = resource_data.get("resource_type")
            if not resource_type:
                continue

            # Create resource instance
            result = pin_resource(resource_type, resource_data)
            if not result.success:
                return result

            resource = result.data["resource"]

            # Create bundle entry
            bundle_entry = BundleEntry(
                resource=resource, title=entry_title, tags=tags, priority=priority
            )
            bundle_entries.append(bundle_entry)

        # Create the bundle
        # Accept common inputs (case-insensitive) but persist lower-case enum values
        normalized_type = (bundle_type or "document").lower()
        bundle_data = {"bundle_type": normalized_type, "entries": bundle_entries}

        if title:
            bundle_data["title"] = title
        if description:
            bundle_data["description"] = description

        bundle = ResourceBundle(**bundle_data)

        return HACSResult(
            success=True,
            message=f"Successfully composed {bundle_type} bundle with {len(bundle_entries)} entries",
            data={"bundle": bundle.model_dump()},
        )

    except Exception as e:
        return HACSResult(success=False, message="Failed to compose bundle", error=str(e))


compose_bundle._tool_args = ComposeBundleInput  # type: ignore[attr-defined]


class ValidateResourceInput(HACSCommonInput):
    resource: Dict[str, Any]


@register_tool(
    name="validate_resource",
    domain="modeling",
    tags=["domain:modeling"],
    status=VersionStatus.ACTIVE,
)
def validate_resource(resource: Dict[str, Any]) -> HACSResult:
    """
    Validate a HACS resource for correctness and integrity.

    Args:
        resource: Dictionary representation of the resource to validate

    Returns:
        HACSResult with validation status and any issues found
    """
    try:
        resource_type = resource.get("resource_type")
        if not resource_type:
            return HACSResult(
                success=False,
                message="Validation failed",
                error="Resource missing 'resource_type' field",
            )

        # Attempt to instantiate the resource (validates structure)
        result = pin_resource(resource_type, resource)

        if not result.success:
            return HACSResult(
                success=False,
                message="Resource validation failed",
                error=result.error,
                data={"valid": False, "issues": [result.error]},
            )

        # Additional validation checks
        issues = []

        # Check for required fields based on resource type
        instantiated_resource = result.data["resource"]

        # Check ID format if present
        if "id" in instantiated_resource and instantiated_resource["id"]:
            resource_id = instantiated_resource["id"]
            if not isinstance(resource_id, str) or len(resource_id.strip()) == 0:
                issues.append("Resource ID must be a non-empty string")

        # Check for circular references in nested objects
        try:
            import json

            json.dumps(instantiated_resource, default=str)
        except (TypeError, ValueError) as e:
            issues.append(f"Resource contains non-serializable data: {str(e)}")

        valid = len(issues) == 0

        return HACSResult(
            success=True,
            message="Resource validation completed",
            data={"valid": valid, "issues": issues, "resource_type": resource_type},
        )

    except Exception as e:
        return HACSResult(
            success=False,
            message="Validation error",
            error=str(e),
            data={"valid": False, "issues": [str(e)]},
        )


validate_resource._tool_args = ValidateResourceInput  # type: ignore[attr-defined]


def validate_resources(resources: List[Dict[str, Any]]) -> HACSResult:
    """Validate multiple resources at once."""
    results: List[Dict[str, Any]] = []
    for res in resources or []:
        single = validate_resource(res)
        results.append(
            {
                "resource_type": res.get("resource_type"),
                "valid": (single.data or {}).get("valid") if single.success else False,
                "issues": (single.data or {}).get("issues")
                if single.success
                else [single.error or single.message],
                "success": single.success,
            }
        )
    return HACSResult(
        success=all(r.get("success") for r in results),
        message=f"Validated {len(results)} resources",
        data={"results": results},
    )


class DiffResourcesInput(HACSCommonInput):
    before: Dict[str, Any]
    after: Dict[str, Any]


@register_tool(
    name="diff_resources", domain="modeling", tags=["domain:modeling"], status=VersionStatus.ACTIVE
)
def diff_resources(before: Dict[str, Any], after: Dict[str, Any]) -> HACSResult:
    """
    Compare two resources and identify the differences between them.

    Args:
        before: The original resource state
        after: The modified resource state

    Returns:
        HACSResult with detailed change information
    """
    try:
        changes = []

        def compare_dicts(dict1, dict2, path=""):
            """Recursively compare two dictionaries."""
            all_keys = set(dict1.keys()) | set(dict2.keys())

            for key in all_keys:
                current_path = f"{path}.{key}" if path else key

                if key not in dict1:
                    changes.append({"type": "added", "path": current_path, "value": dict2[key]})
                elif key not in dict2:
                    changes.append({"type": "removed", "path": current_path, "value": dict1[key]})
                elif dict1[key] != dict2[key]:
                    if isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                        compare_dicts(dict1[key], dict2[key], current_path)
                    else:
                        changes.append(
                            {
                                "type": "modified",
                                "path": current_path,
                                "before": dict1[key],
                                "after": dict2[key],
                            }
                        )

        compare_dicts(before, after)

        return HACSResult(
            success=True,
            message=f"Resource comparison completed with {len(changes)} changes",
            data={"changes": changes, "has_changes": len(changes) > 0},
        )

    except Exception as e:
        return HACSResult(success=False, message="Failed to compare resources", error=str(e))


diff_resources._tool_args = DiffResourcesInput  # type: ignore[attr-defined]


def diff_pairs(pairs: List[Dict[str, Any]]) -> HACSResult:
    """
    Compute diffs for multiple before/after pairs.

    Each pair is {"before": dict, "after": dict}.
    """
    diffs: List[Dict[str, Any]] = []
    for pair in pairs or []:
        single = diff_resources(pair.get("before", {}), pair.get("after", {}))
        diffs.append(single.data or {})
    return HACSResult(success=True, message=f"Computed {len(diffs)} diffs", data={"results": diffs})


class ValidateBundleInput(HACSCommonInput):
    bundle: Dict[str, Any]


@register_tool(
    name="validate_bundle", domain="modeling", tags=["domain:modeling"], status=VersionStatus.ACTIVE
)
def validate_bundle(bundle: Dict[str, Any]) -> HACSResult:
    """
    Validate a ResourceBundle for integrity and consistency.

    Args:
        bundle: Dictionary representation of the ResourceBundle

    Returns:
        HACSResult with validation status and details
    """
    try:
        # Instantiate the bundle to perform basic validation
        bundle_obj = ResourceBundle(**bundle)

        # Perform integrity validation
        integrity_result = bundle_obj.validate_bundle_integrity()

        if not integrity_result.success:
            return HACSResult(
                success=False,
                message="Bundle validation failed",
                error=integrity_result.message,
                data={"valid": False, "details": integrity_result.data},
            )

        # Additional validations
        issues = []

        # Check that all resources in entries are valid
        for i, entry in enumerate(bundle_obj.entries):
            if hasattr(entry, "resource") and entry.resource:
                resource_result = validate_resource(entry.resource)
                if not resource_result.success or not resource_result.data.get("valid", False):
                    issues.extend(
                        [f"Entry {i}: {issue}" for issue in resource_result.data.get("issues", [])]
                    )

        # Check for duplicate entry titles
        titles = [
            entry.title for entry in bundle_obj.entries if hasattr(entry, "title") and entry.title
        ]
        if len(titles) != len(set(titles)):
            issues.append("Bundle contains duplicate entry titles")

        valid = len(issues) == 0

        return HACSResult(
            success=True,
            message="Bundle validation completed",
            data={
                "valid": valid,
                "issues": issues,
                "entry_count": len(bundle_obj.entries),
                "bundle_type": bundle_obj.bundle_type,
            },
        )

    except Exception as e:
        return HACSResult(
            success=False,
            message="Bundle validation error",
            error=str(e),
            data={"valid": False, "issues": [str(e)]},
        )


validate_bundle._tool_args = ValidateBundleInput  # type: ignore[attr-defined]


# ----------------------------------------------------------------------------
# Document/Composition mutations: add_entries
# ----------------------------------------------------------------------------


class AddEntriesInput(BaseModel):
    document: Dict[str, Any] = Field(description="Document/Composition dictionary")
    entries: List[Dict[str, Any]] = Field(
        description=
        "List of resources to add. Each item must contain 'resource_type' and the fields of the resource."
    )
    strategy: str = Field(
        default="append",
        description="append|upsert (best-effort upsert by resource_type + simple keys like code.text)",
    )


def _ensure_document(doc_data: Dict[str, Any]) -> Document:
    """Instantiate a Document safely even if status=final and no sections yet."""
    try:
        return Document(**doc_data)
    except Exception:
        tmp = dict(doc_data)
        tmp["status"] = "preliminary"
        return Document(**tmp)


def _get_or_create_section(doc: Document, title: str):
    sec = doc.get_section_by_title(title)
    if not sec:
        doc.add_section(title, "")
        sec = doc.get_section_by_title(title)
    return sec


def _summarize_resource_line(rtype: str, res: Dict[str, Any]) -> str:
    rtype_lower = (rtype or "").lower()
    if rtype_lower == "observation":
        code = (((res.get("code") or {}).get("text")) if isinstance(res.get("code"), dict) else res.get("code")) or "Observação"
        vq = res.get("value_quantity") or {}
        val = vq.get("value")
        unit = vq.get("unit")
        return f"{code}: {val} {unit}".strip()
    if rtype_lower == "medicationstatement":
        m = res.get("medication_codeable_concept") or {}
        name = m.get("text") or "Medicamento"
        ds = res.get("dosage") or []
        dtext = ds[0].get("text") if ds and isinstance(ds[0], dict) else None
        return f"{name}{' - ' + dtext if dtext else ''}"
    if rtype_lower == "condition":
        code = (((res.get("code") or {}).get("text")) if isinstance(res.get("code"), dict) else res.get("code")) or "Condição"
        return f"{code}"
    if rtype_lower == "immunization":
        v = res.get("vaccine_code") or {}
        vtext = v.get("text") or "Imunização"
        when = res.get("occurrence_date_time") or ""
        return f"{vtext}{' - ' + when if when else ''}"
    if rtype_lower == "familymemberhistory":
        rel = res.get("relationship")
        note = res.get("note")
        rel_text = rel.get("text") if isinstance(rel, dict) else rel
        note_text = note.get("text") if isinstance(note, dict) else note
        return " - ".join([x for x in [rel_text, note_text] if x]) or "História familiar"
    if rtype_lower == "servicerequest":
        code = (((res.get("code") or {}).get("text")) if isinstance(res.get("code"), dict) else res.get("code")) or "Solicitação"
        return f"{code}"
    # Fallback
    return rtype


def _target_section_for_resource(rtype: str, res: Dict[str, Any]) -> str:
    rl = (rtype or "").lower()
    if rl == "observation":
        code = (((res.get("code") or {}).get("text")) if isinstance(res.get("code"), dict) else res.get("code")) or ""
        return "Sinais Vitais" if any(k in (code or "").lower() for k in ["pa", "fc", "fr", "temp", "sp"]) else "Dados Antropométricos"
    if rl == "medicationstatement":
        return "Medicações em uso"
    if rl == "condition":
        return "Hipóteses Diagnósticas"
    if rl == "immunization":
        return "História Vacinal"
    if rl == "familymemberhistory":
        return "História Familiar"
    if rl == "servicerequest":
        return "Exames Complementares"
    return "Outros"


@register_tool(name="add_entries", domain="modeling", tags=["domain:modeling"], status=VersionStatus.ACTIVE)
def add_entries(document: Dict[str, Any], entries: List[Dict[str, Any]], strategy: str = "append") -> HACSResult:
    """
    Add HACS resources into a Document/Composition, mapping each resource to the appropriate section and
    appending a concise, clinical summary line. If strategy='upsert', best-effort replace lines by
    resource_type + a simple key (e.g., Observation.code.text).

    Returns the updated document.
    """
    try:
        doc_obj = _ensure_document(document)
        added = 0
        for res in entries or []:
            rtype = res.get("resource_type")
            if not rtype:
                continue
            target = _target_section_for_resource(rtype, res)
            line = _summarize_resource_line(rtype, res)
            sec = _get_or_create_section(doc_obj, target)
            current_text = getattr(sec, "text", "") or ""
            # naive upsert: replace line containing the code text if present
            if strategy == "upsert":
                key = None
                if rtype.lower() == "observation":
                    code = res.get("code") or {}
                    key = (code.get("text") if isinstance(code, dict) else None)
                if key and current_text:
                    lines = [ln for ln in current_text.split("\n") if ln.strip()]
                    replaced = False
                    for i, ln in enumerate(lines):
                        if key and key.lower() in ln.lower():
                            lines[i] = line
                            replaced = True
                            break
                    if replaced:
                        sec.text = "\n".join(lines)
                    else:
                        sec.text = (current_text + ("\n" if current_text and not current_text.endswith("\n") else "") + line)
                else:
                    sec.text = (current_text + ("\n" if current_text and not current_text.endswith("\n") else "") + line)
            else:
                sec.text = (current_text + ("\n" if current_text and not current_text.endswith("\n") else "") + line)
            added += 1

        updated = doc_obj.model_dump()
        return HACSResult(success=True, message=f"Added {added} entries", data={"document": updated, "added": added})
    except Exception as e:
        return HACSResult(success=False, message="Failed to add entries", error=str(e))


add_entries._tool_args = AddEntriesInput  # type: ignore[attr-defined]


def validate_bundles(bundles: List[Dict[str, Any]]) -> HACSResult:
    """Validate multiple bundles."""
    results: List[Dict[str, Any]] = []
    for b in bundles or []:
        single = validate_bundle(b)
        results.append(single.data or {"valid": False})
    return HACSResult(
        success=all(r.get("valid") for r in results),
        message=f"Validated {len(results)} bundles",
        data={"results": results},
    )


# Export canonical tool names (without _tool suffix)
__all__ = [
    "pin_resource",
    "compose_bundle",
    "validate_resource",
    "diff_resources",
    "validate_bundle",
]


# --------------------------------------------
# Granular Modeling Tools (introspection + pick)
# --------------------------------------------


@register_tool(
    name="list_models", domain="modeling", tags=["domain:modeling"], status=VersionStatus.ACTIVE
)
def list_models() -> HACSResult:
    """
    List all available HACS model types.

    Returns:
        HACSResult with a list of model names
    """
    try:
        registry = get_model_registry()
        return HACSResult(
            success=True,
            message=f"Found {len(registry)} models",
            data={"models": sorted(list(registry.keys()))},
        )
    except Exception as e:
        return HACSResult(success=False, message="Failed to list models", error=str(e))


class DescribeResourceInput(BaseModel):
    resource_type: str


class DescribeModelsInput(BaseModel):
    resource_types: List[str]


@register_tool(
    name="describe_resources", domain="modeling", tags=["domain:modeling"], status=VersionStatus.ACTIVE
)
def describe_resources(resource_types: List[str]) -> HACSResult:
    """Describe multiple models at once."""
    items: List[Dict[str, Any]] = []
    for rt in resource_types or []:
        single = describe_resource(rt)
        items.append(
            {
                "resource_type": rt,
                "definition": (single.data or {}),
                "success": single.success,
            }
        )
    return HACSResult(
        success=all(i.get("success") for i in items),
        message=f"Described {len(items)} resources",
        data={"results": items},
    )


class ListModelFieldsInput(BaseModel):
    resource_type: str


@register_tool(
    name="list_model_fields",
    domain="modeling",
    tags=["domain:modeling"],
    status=VersionStatus.ACTIVE,
)
def list_model_fields(resource_type: str) -> HACSResult:
    """
    List fields for a given model with basic type info and descriptions.
    """
    try:
        registry = get_model_registry()
        resource_class = registry.get(resource_type)
        if not resource_class:
            return HACSResult(success=False, message=f"Unknown resource type: {resource_type}")
        fields: List[Dict[str, Any]] = []
        for name, field in getattr(resource_class, "model_fields", {}).items():
            fields.append(
                {
                    "name": name,
                    "type": str(getattr(field, "annotation", "")),
                    "description": getattr(field, "description", None),
                    "required": getattr(field, "is_required", False),
                }
            )
        return HACSResult(
            success=True, message=f"Listed {len(fields)} fields", data={"fields": fields}
        )
    except Exception as e:
        plan = build_error_plan(resource_type, None, e)
        return HACSResult(success=False, message="Failed to list fields", error=str(e), data={"plan": plan})


class ListModelFacadesInput(BaseModel):
    resource_type: str


@register_tool(
    name="list_model_facades",
    domain="modeling",
    tags=["domain:modeling"],
    status=VersionStatus.ACTIVE,
)
def list_model_facades(resource_type: str) -> HACSResult:
    """List available facades for a model with brief summaries."""
    try:
        registry = get_model_registry()
        resource_class = registry.get(resource_type)
        if not resource_class:
            return HACSResult(success=False, message=f"Unknown resource type: {resource_type}")

        facades = {}
        if hasattr(resource_class, "get_facades"):
            for key, spec in (resource_class.get_facades() or {}).items():
                facades[key] = {
                    "description": getattr(spec, "description", ""),
                    "fields": list(getattr(spec, "fields", [])),
                    "required": list(getattr(spec, "required_fields", []) or []),
                    "many": bool(getattr(spec, "many", False)),
                    "max_items": int(getattr(spec, "max_items", 0)),
                    "field_hints": getattr(spec, "field_hints", {}) or {},
                    "field_examples": getattr(spec, "field_examples", {}) or {},
                    "field_types": getattr(spec, "field_types", {}) or {},
                    "llm_guidance": getattr(spec, "llm_guidance", ""),
                    "conversational_prompts": getattr(spec, "conversational_prompts", []) or [],
                }

        return HACSResult(
            success=True,
            message=f"Found {len(facades)} facades for {resource_type}",
            data={"resource_type": resource_type, "facades": facades},
        )
    except Exception as e:
        plan = build_error_plan(resource_type, None, e)
        return HACSResult(success=False, message="Failed to list facades", error=str(e), data={"plan": plan})
list_model_facades._tool_args = ListModelFacadesInput  # type: ignore[attr-defined]


class DescribeModelEnrichedInput(BaseModel):
    resource_type: str


@register_tool(
    name="describe_resource",
    domain="modeling",
    tags=["domain:modeling"],
    status=VersionStatus.ACTIVE,
)
def describe_resource(resource_type: str) -> HACSResult:
    """Describe a model including scope, facades, and resource-specific tools."""
    try:
        registry = get_model_registry()
        resource_class = registry.get(resource_type)
        if not resource_class:
            return HACSResult(success=False, message=f"Unknown resource type: {resource_type}")

        # Base specifications
        if hasattr(resource_class, "get_specifications"):
            base = resource_class.get_specifications()
        else:
            base = {"title": resource_type}

        # Facades
        facades = (resource_class.get_facades() or {}) if hasattr(resource_class, "get_facades") else {}
        facade_map: Dict[str, Any] = {}
        for key, spec in facades.items():
            facade_map[key] = {
                "description": getattr(spec, "description", ""),
                "fields": list(getattr(spec, "fields", [])),
                "required": list(getattr(spec, "required_fields", []) or []),
                "many": bool(getattr(spec, "many", False)),
                "max_items": int(getattr(spec, "max_items", 0)),
                "hints": getattr(spec, "field_hints", {}) or {},
            }

        # Resource-specific tools (by tag resource:<lower>)
        tools_section: List[Dict[str, Any]] = []
        try:
            tool_reg = get_tool_registry()
            tag_key = f"resource:{resource_type.lower()}"
            resource_tools = tool_reg.get_tools_by_tag(tag_key)
            for t in resource_tools:
                tools_section.append({
                    "name": t.name,
                    "description": t.description,
                    "domain": t.domain,
                    "tags": t.tags,
                })
        except Exception:
            pass

        pack = {
            "resource": base,
            "facades": facade_map,
            "tools": tools_section,
        }
        return HACSResult(success=True, message="Resource description", data=pack)
    except Exception as e:
        plan = build_error_plan(resource_type, None, e)
        return HACSResult(success=False, message="Failed to describe resource", error=str(e), data={"plan": plan})
describe_resource._tool_args = DescribeModelEnrichedInput  # type: ignore[attr-defined]


class DescribeModelSubsetInput(BaseModel):
    resource_type: str
    fields: Optional[List[str]] = None
    facade: Optional[str] = None


@register_tool(
    name="describe_model_subset",
    domain="modeling",
    tags=["domain:modeling"],
    status=VersionStatus.ACTIVE,
)
def describe_model_subset(resource_type: str, fields: Optional[List[str]] = None, facade: Optional[str] = None) -> HACSResult:
    """Describe a subset schema (manual fields or facade). Useful with pick()."""
    try:
        registry = get_model_registry()
        resource_class = registry.get(resource_type)
        if not resource_class:
            return HACSResult(success=False, message=f"Unknown resource type: {resource_type}")

        selected: List[str]
        hints: Dict[str, str] = {}
        required: List[str] = []
        field_examples: Dict[str, Any] = {}
        field_types: Dict[str, str] = {}
        llm_guidance: str = ""
        conversational_prompts: List[str] = []

        if facade:
            spec = resource_class.get_facade_spec(facade) if hasattr(resource_class, "get_facade_spec") else None
            if not spec:
                return HACSResult(success=False, message=f"Unknown facade '{facade}' for {resource_type}")
            selected = list(spec.fields)
            hints = spec.field_hints or {}
            required = list(spec.required_fields or [])
            field_examples = spec.field_examples or {}
            field_types = spec.field_types or {}
            llm_guidance = spec.llm_guidance or ""
            conversational_prompts = spec.conversational_prompts or []
        else:
            selected = list(fields or [])

        # Field detail map
        field_defs: Dict[str, Any] = {}
        mf = getattr(resource_class, "model_fields", {}) or {}
        for name in selected:
            if name in mf:
                f = mf[name]
                field_defs[name] = {
                    "type": field_types.get(name, str(getattr(f, "annotation", ""))),
                    "description": getattr(f, "description", None),
                    "required": getattr(f, "is_required", False) or (name in required),
                    "hint": hints.get(name),
                    "example": field_examples.get(name),
                }

        # Provide a compact example via pick_facade or pick
        try:
            if facade:
                subset_cls = resource_class.pick_facade(facade)  # type: ignore[attr-defined]
            else:
                subset_cls = resource_class.pick(*selected)
            example = subset_cls.model_json_schema().get("examples") or []  # type: ignore[attr-defined]
        except Exception:
            example = []

        data = {
            "resource_type": resource_type,
            "fields": field_defs,
            "facade": facade,
            "required": required,
            "hints": hints,
            "field_examples": field_examples,
            "field_types": field_types,
            "llm_guidance": llm_guidance,
            "conversational_prompts": conversational_prompts,
            "example": example,
        }
        return HACSResult(success=True, message="Subset description", data=data)
    except Exception as e:
        plan = build_error_plan(resource_type, {"fields": fields or [], "facade": facade, "resource_type": resource_type}, e)
        return HACSResult(success=False, message="Failed to describe subset", error=str(e), data={"plan": plan})
describe_model_subset._tool_args = DescribeModelSubsetInput  # type: ignore[attr-defined]


class ListFieldsInput(BaseModel):
    resource_types: List[str]


@register_tool(
    name="list_fields", domain="modeling", tags=["domain:modeling"], status=VersionStatus.ACTIVE
)
def list_fields(resource_types: List[str]) -> HACSResult:
    """List fields for multiple models."""
    results: List[Dict[str, Any]] = []
    for rt in resource_types or []:
        single = list_model_fields(rt)
        results.append({"resource_type": rt, "fields": (single.data or {}).get("fields", [])})
    return HACSResult(
        success=True, message=f"Listed fields for {len(results)} models", data={"results": results}
    )


class PickResourceFieldsInput(BaseModel):
    resource_type: str
    fields: List[str]


@register_tool(
    name="pick_resource_fields",
    domain="modeling",
    tags=["domain:modeling"],
    status=VersionStatus.ACTIVE,
)
def pick_resource_fields(resource_type: str, fields: List[str]) -> HACSResult:
    """
    Create a subset schema for the specified resource fields (plus essentials).

    Returns the JSON schema of the subset model so agents can plan extractions.
    """
    try:
        registry = get_model_registry()
        resource_class = registry.get(resource_type)
        if not resource_class:
            return HACSResult(success=False, message=f"Unknown resource type: {resource_type}")

        if not hasattr(resource_class, "pick"):
            return HACSResult(
                success=False, message=f"Model {resource_type} does not support 'pick' operation"
            )

        subset_cls = resource_class.pick(*fields)
        try:
            subset_schema = subset_cls.model_json_schema()
        except Exception:
            subset_schema = getattr(subset_cls, "schema", lambda: {})()

        return HACSResult(
            success=True,
            message=f"Created subset schema for {resource_type}",
            data={
                "subset_resource_name": subset_cls.__name__,
                "json_schema": subset_schema,
                "fields": fields,
            },
        )
    except Exception as e:
        return HACSResult(success=False, message="Failed to create subset schema", error=str(e))


class ProjectResourceFieldsInput(BaseModel):
    resource: Dict[str, Any]
    fields: List[str]


@register_tool(
    name="project_resource_fields",
    domain="modeling",
    tags=["domain:modeling"],
    status=VersionStatus.ACTIVE,
)
def project_resource_fields(resource: Dict[str, Any], fields: List[str]) -> HACSResult:
    """
    Project a resource dictionary to only selected fields (plus essentials).
    """
    try:
        resource_type = resource.get("resource_type")
        if not resource_type:
            plan = build_error_plan(None, resource, "Missing resource_type")
            return HACSResult(success=False, message="Resource missing 'resource_type'", data={"plan": plan})

        registry = get_model_registry()
        resource_class = registry.get(resource_type)
        if not resource_class:
            return HACSResult(success=False, message=f"Unknown resource type: {resource_type}")

        instance = resource_class(**resource)
        essential_fields: Set[str] = {"id", "resource_type", "created_at", "updated_at"}
        include_fields = set(fields) | essential_fields
        projected = instance.model_dump(include=include_fields)

        return HACSResult(success=True, message="Projected resource", data={"resource": projected})
    except Exception as e:
        return HACSResult(success=False, message="Failed to project resource", error=str(e))


class ToReferenceInput(BaseModel):
    resource: Dict[str, Any]


@register_tool(
    name="to_reference", domain="modeling", tags=["domain:modeling"], status=VersionStatus.ACTIVE
)
def to_reference(resource: Dict[str, Any]) -> HACSResult:
    """
    Return a FHIR-style reference string "ResourceType/id" for a resource.
    """
    try:
        resource_type = resource.get("resource_type")
        if not resource_type:
            return HACSResult(success=False, message="Resource missing 'resource_type'")

        registry = get_model_registry()
        resource_class = registry.get(resource_type)
        if not resource_class:
            return HACSResult(success=False, message=f"Unknown resource type: {resource_type}")

        instance = resource_class(**resource)
        ref = (
            instance.to_reference()
            if hasattr(instance, "to_reference")
            else f"{resource_type}/{resource.get('id', '')}"
        )
        return HACSResult(success=True, message="Reference created", data={"reference": ref})
    except Exception as e:
        return HACSResult(success=False, message="Failed to create reference", error=str(e))


class AddExtensionInput(BaseModel):
    resource: Dict[str, Any]
    url: str
    value: Any


@register_tool(
    name="add_extension_to_resource",
    domain="modeling",
    tags=["domain:modeling"],
    status=VersionStatus.ACTIVE,
)
def add_extension_to_resource(resource: Dict[str, Any], url: str, value: Any) -> HACSResult:
    """
    Add an extension to a DomainResource-compatible resource.
    """
    try:
        resource_type = resource.get("resource_type")
        if not resource_type:
            return HACSResult(success=False, message="Resource missing 'resource_type'")

        registry = get_model_registry()
        resource_class = registry.get(resource_type)
        if not resource_class:
            return HACSResult(success=False, message=f"Unknown resource type: {resource_type}")

        instance = resource_class(**resource)
        if not isinstance(instance, DomainResource):
            return HACSResult(
                success=False, message=f"Resource {resource_type} does not support extensions"
            )

        instance.add_extension(url, value)
        return HACSResult(
            success=True, message="Extension added", data={"resource": instance.model_dump()}
        )
    except Exception as e:
        return HACSResult(success=False, message="Failed to add extension", error=str(e))


class ListModelMethodsInput(BaseModel):
    resource_type: str


@register_tool(
    name="list_model_methods",
    domain="modeling",
    tags=["domain:modeling"],
    status=VersionStatus.ACTIVE,
)
def list_model_methods(resource_type: str) -> HACSResult:
    """
    List safe, instance-level methods for a model that agents can call.
    Returns method names and first-line docstrings.
    """
    try:
        registry = get_model_registry()
        resource_class = registry.get(resource_type)
        if not resource_class:
            return HACSResult(success=False, message=f"Unknown resource type: {resource_type}")

        # Candidate methods: public instance methods, excluding BaseModel internals
        candidates: List[Dict[str, Any]] = []
        blacklist = {"model_dump", "model_json_schema", "model_validate", "copy"}
        for name, member in inspect.getmembers(resource_class, predicate=inspect.isfunction):
            if name.startswith("_"):
                continue
            if name in blacklist:
                continue
            try:
                sig = inspect.signature(member)
                if "self" not in sig.parameters:
                    continue
            except (ValueError, TypeError):
                continue
            doc = (inspect.getdoc(member) or "").strip().split("\n")[0]
            candidates.append({"name": name, "doc": doc})

        return HACSResult(
            success=True, message=f"Found {len(candidates)} methods", data={"methods": candidates}
        )
    except Exception as e:
        return HACSResult(success=False, message="Failed to list methods", error=str(e))


class InvokeModelMethodInput(BaseModel):
    resource: Dict[str, Any]
    method_name: str
    arguments: Optional[Dict[str, Any]] = None


@register_tool(
    name="invoke_model_method",
    domain="modeling",
    tags=["domain:modeling"],
    status=VersionStatus.ACTIVE,
)
def invoke_model_method(
    resource: Dict[str, Any], method_name: str, arguments: Optional[Dict[str, Any]] = None
) -> HACSResult:
    """
    Safely invoke a whitelisted instance method on a resource model.

    Only allows safe domain-specific methods such as:
      - Document: add_section, add_author, add_attester, get_word_count, get_full_text, summary
      - ResourceBundle: validate_bundle_integrity, add_workflow_binding
      - Generic: summary, add_extension (via add_extension_to_resource)
    """
    try:
        arguments = arguments or {}
        resource_type = resource.get("resource_type")
        if not resource_type:
            return HACSResult(success=False, message="Resource missing 'resource_type'")

        registry = get_model_registry()
        resource_class = registry.get(resource_type)
        if not resource_class:
            return HACSResult(success=False, message=f"Unknown resource type: {resource_type}")

        instance = resource_class(**resource)

        allowed: Dict[str, Set[str]] = {
            "Document": {
                "add_section",
                "add_author",
                "add_attester",
                "get_word_count",
                "get_full_text",
                "summary",
            },
            "ResourceBundle": {"validate_bundle_integrity", "add_workflow_binding"},
        }
        generic_allowed: Set[str] = {"summary"}

        allowed_methods = allowed.get(resource_type, generic_allowed)
        if method_name not in allowed_methods:
            return HACSResult(
                success=False, message=f"Method '{method_name}' not allowed for {resource_type}"
            )

        method = getattr(instance, method_name, None)
        if not callable(method):
            return HACSResult(
                success=False, message=f"Method '{method_name}' not found on {resource_type}"
            )

        # Align provided arguments with signature
        try:
            sig = inspect.signature(method)
            call_kwargs = {}
            for pname, param in sig.parameters.items():
                if pname == "self":
                    continue
                if pname in arguments:
                    call_kwargs[pname] = arguments[pname]
                elif param.default is inspect._empty:
                    return HACSResult(success=False, message=f"Missing required argument: {pname}")
        except (ValueError, TypeError):
            call_kwargs = arguments

        result = method(**call_kwargs)

        # If method returns a result model, serialize; otherwise return updated resource
        if isinstance(result, BaseResource):
            return HACSResult(
                success=True, message="Method invoked", data={"result": result.model_dump()}
            )

        # Re-serialize instance in case it was mutated
        return HACSResult(
            success=True,
            message="Method invoked",
            data={"resource": instance.model_dump(), "result": result},
        )
    except Exception as e:
        return HACSResult(success=False, message="Failed to invoke method", error=str(e))


class AddBundleEntriesInput(BaseModel):
    bundle: Dict[str, Any]
    entries: List[Dict[str, Any]]


@register_tool(
    name="add_bundle_entries",
    domain="modeling",
    tags=["domain:modeling"],
    status=VersionStatus.ACTIVE,
)
def add_bundle_entries(bundle: Dict[str, Any], entries: List[Dict[str, Any]]) -> HACSResult:
    """
    Add multiple entries to a ResourceBundle in a single operation.

    Args:
        bundle: Existing ResourceBundle as dict
        entries: List of dicts each with at least {"resource": {...}} and optional title/tags/priority
    """
    try:
        bundle_obj = ResourceBundle(**bundle)
        new_entries: List[BundleEntry] = []
        for entry in entries:
            if "resource" not in entry:
                return HACSResult(success=False, message="Entry missing 'resource'")
            new_entries.append(
                BundleEntry(
                    resource=entry["resource"],
                    title=entry.get("title"),
                    tags=entry.get("tags", []),
                    priority=entry.get("priority", 5),
                )
            )
        updated_entries = list(bundle_obj.entries or []) + new_entries
        updated_bundle = bundle_obj.model_copy(update={"entries": updated_entries})
        return HACSResult(
            success=True,
            message=f"Added {len(new_entries)} entries",
            data={"bundle": updated_bundle.model_dump()},
        )
    except Exception as e:
        return HACSResult(success=False, message="Failed to add bundle entries", error=str(e))


class ListBundleEntriesInput(BaseModel):
    bundle: Dict[str, Any]


@register_tool(
    name="list_bundle_entries",
    domain="modeling",
    tags=["domain:modeling"],
    status=VersionStatus.ACTIVE,
)
def list_bundle_entries(bundle: Dict[str, Any]) -> HACSResult:
    """
    List entries of a ResourceBundle with minimal details.
    """
    try:
        bundle_obj = ResourceBundle(**bundle)
        entries: List[Dict[str, Any]] = []
        for idx, be in enumerate(bundle_obj.entries or []):
            entries.append(
                {
                    "index": idx,
                    "title": getattr(be, "title", None),
                    "tags": getattr(be, "tags", []),
                    "priority": getattr(be, "priority", 5),
                    "resource_type": be.resource.get("resource_type")
                    if isinstance(be.resource, dict)
                    else getattr(be.resource, "resource_type", None),
                }
            )
        return HACSResult(
            success=True, message=f"Found {len(entries)} entries", data={"entries": entries}
        )
    except Exception as e:
        return HACSResult(success=False, message="Failed to list bundle entries", error=str(e))


# Extend exports with granular tools
__all__.extend(
    [
        "list_models",
        "describe_model",
        "describe_models",
        "list_model_fields",
        "list_fields",
        "pick_resource_fields",
        "project_resource_fields",
        "to_reference",
        "add_extension_to_resource",
        "list_model_methods",
        "invoke_model_method",
        "add_bundle_entries",
        "list_bundle_entries",
    ]
)


# --------------------------------------------
# Higher-level planning helpers (schema planning)
# --------------------------------------------


def compute_required_fields(resource_type: str) -> HACSResult:
    """Return required fields for a model based on Pydantic field metadata."""
    try:
        registry = get_model_registry()
        resource_class = registry.get(resource_type)
        if not resource_class:
            return HACSResult(success=False, message=f"Unknown resource type: {resource_type}")
        required = []
        for name, field in getattr(resource_class, "model_fields", {}).items():
            if getattr(field, "is_required", False):
                required.append(name)
        # Ensure essentials are included even if not marked required
        for essential in ("id", "resource_type", "created_at", "updated_at"):
            if essential not in required and essential in resource_class.model_fields:
                required.append(essential)
        return HACSResult(
            success=True, message=f"{len(required)} required fields", data={"fields": required}
        )
    except Exception as e:
        return HACSResult(success=False, message="Failed to compute required fields", error=str(e))


def build_subset_schemas(resource_fields_map: Dict[str, List[str]]) -> HACSResult:
    """
    Given {resource_type: [fields...]}, build subset JSON schemas for each.
    """
    try:
        registry = get_model_registry()
        subset_schemas: Dict[str, Any] = {}
        for rtype, fields in resource_fields_map.items():
            resource_class = registry.get(rtype)
            if not resource_class:
                return HACSResult(success=False, message=f"Unknown resource type: {rtype}")
            if not hasattr(resource_class, "pick"):
                return HACSResult(success=False, message=f"Model {rtype} does not support 'pick'")
            subset_cls = resource_class.pick(*fields)
            try:
                subset_schema = subset_cls.model_json_schema()
            except Exception:
                subset_schema = getattr(subset_cls, "schema", lambda: {})()
            subset_schemas[rtype] = {
                "subset_resource_name": subset_cls.__name__,
                "json_schema": subset_schema,
                "fields": list(fields),
            }
        return HACSResult(
            success=True, message="Built subset schemas", data={"schemas": subset_schemas}
        )
    except Exception as e:
        return HACSResult(success=False, message="Failed to build subset schemas", error=str(e))


def plan_bundle_schema(resource_types: List[str], use_case: Optional[str] = None) -> HACSResult:
    """
    Suggest a minimal bundle schema across multiple resources.
    Returns a plan with required fields per resource and an initial bundle template.
    """
    try:
        plan: List[Dict[str, Any]] = []
        for rtype in resource_types:
            req = compute_required_fields(rtype)
            if not req.success:
                return req
            plan.append({"resource_type": rtype, "required_fields": req.data.get("fields", [])})
        # Compose a basic bundle template with empty entries
        entries: List[Dict[str, Any]] = []
        for item in plan:
            entries.append(
                {
                    "title": item["resource_type"],
                    "tags": [item["resource_type"].lower()],
                    "priority": 5,
                    "resource_data": {"resource_type": item["resource_type"]},
                }
            )
        bundle_result = compose_bundle(
            entries=entries, bundle_type="document", title="Planned Bundle"
        )
        if not bundle_result.success:
            return bundle_result
        return HACSResult(
            success=True,
            message="Planned bundle schema",
            data={
                "resources": plan,
                "bundle_template": bundle_result.data.get("bundle"),
                "use_case": use_case,
            },
        )
    except Exception as e:
        return HACSResult(success=False, message="Failed to plan bundle schema", error=str(e))


# --------------------------------------------
# Composition/Document helpers (explicit wrappers)
# --------------------------------------------


def create_document(
    title: Optional[str] = None, status: Optional[str] = None, confidentiality: Optional[str] = None
) -> HACSResult:
    """Create a minimal Document resource."""
    try:
        data: Dict[str, Any] = {"resource_type": "Document"}
        if title:
            data["title"] = title
        if status:
            data["status"] = status
        if confidentiality:
            data["confidentiality"] = confidentiality
        doc = Document(**data)
        return HACSResult(
            success=True, message="Document created", data={"resource": doc.model_dump()}
        )
    except Exception as e:
        return HACSResult(success=False, message="Failed to create document", error=str(e))


def add_document_section(
    document: Dict[str, Any], title: str, content: Optional[str] = None
) -> HACSResult:
    """Add a section to a Document and return the updated resource."""
    try:
        doc = Document(**document)
        if not hasattr(doc, "add_section"):
            return HACSResult(success=False, message="Document does not support add_section")
        section = doc.add_section(title=title, text=content or "")
        return HACSResult(
            success=True,
            message="Section added",
            data={"resource": doc.model_dump(), "section": getattr(section, "title", title)},
        )
    except Exception as e:
        return HACSResult(success=False, message="Failed to add document section", error=str(e))


def list_document_sections(document: Dict[str, Any]) -> HACSResult:
    """List section titles of a Document."""
    try:
        doc = Document(**document)
        sections = []
        for s in getattr(doc, "sections", []) or []:
            sections.append(getattr(s, "title", None))
        return HACSResult(
            success=True, message=f"{len(sections)} sections", data={"sections": sections}
        )
    except Exception as e:
        return HACSResult(success=False, message="Failed to list document sections", error=str(e))


def document_summary(document: Dict[str, Any]) -> HACSResult:
    """Return summary and word count for a Document."""
    try:
        doc = Document(**document)
        summary = doc.summary() if hasattr(doc, "summary") else None
        words = doc.get_word_count() if hasattr(doc, "get_word_count") else None
        return HACSResult(
            success=True, message="Summary computed", data={"summary": summary, "word_count": words}
        )
    except Exception as e:
        return HACSResult(success=False, message="Failed to compute document summary", error=str(e))


# Export new planning and composition helpers
__all__.extend(
    [
        "compute_required_fields",
        "build_subset_schemas",
        "plan_bundle_schema",
        "create_document",
        "add_document_section",
        "list_document_sections",
        "document_summary",
    ]
)


# --------------------------------------------
# Deep field inspection and validation helpers
# --------------------------------------------


def list_nested_fields(
    resource_type: str, prefix: Optional[str] = None, max_depth: int = 2
) -> HACSResult:
    """
    Recursively list nested fields for a model up to max_depth. Returns dot-paths.
    """
    try:
        registry = get_model_registry()
        resource_class = registry.get(resource_type)
        if not resource_class:
            return HACSResult(success=False, message=f"Unknown resource type: {resource_type}")

        paths: List[Dict[str, Any]] = []

        def _collect(cls, base: str, depth: int):
            if depth > max_depth:
                return
            fields = getattr(cls, "model_fields", {})
            for name, field in fields.items():
                path = f"{base}.{name}" if base else name
                type_str = str(getattr(field, "annotation", ""))
                desc = getattr(field, "description", None)
                paths.append({"path": path, "type": type_str, "description": desc})
                # Recurse into nested Pydantic models when possible
                nested_cls = getattr(field, "annotation", None)
                nested_model_fields = getattr(nested_cls, "model_fields", None)
                if nested_model_fields:
                    _collect(nested_cls, path, depth + 1)

        start_prefix = prefix or ""
        _collect(resource_class, start_prefix, 0)
        return HACSResult(
            success=True, message=f"Found {len(paths)} fields", data={"fields": paths}
        )
    except Exception as e:
        return HACSResult(success=False, message="Failed to list nested fields", error=str(e))


def inspect_field(resource_type: str, field_path: str) -> HACSResult:
    """
    Inspect a field by dot-path, returning type and description if available.
    """
    try:
        registry = get_model_registry()
        resource_class = registry.get(resource_type)
        if not resource_class:
            return HACSResult(success=False, message=f"Unknown resource type: {resource_type}")

        parts = [p for p in field_path.split(".") if p]
        cls = resource_class
        field_info = None
        full_path_accum = []
        for part in parts:
            full_path_accum.append(part)
            mf = getattr(cls, "model_fields", {})
            if part not in mf:
                return HACSResult(
                    success=False, message=f"Field not found: {'.'.join(full_path_accum)}"
                )
            f = mf[part]
            field_info = {
                "name": part,
                "type": str(getattr(f, "annotation", "")),
                "description": getattr(f, "description", None),
                "required": getattr(f, "is_required", False),
            }
            # Descend into nested model if possible
            nested_cls = getattr(f, "annotation", None)
            if getattr(nested_cls, "model_fields", None):
                cls = nested_cls
            else:
                cls = None
        return HACSResult(success=True, message="Field inspected", data={"field": field_info})
    except Exception as e:
        return HACSResult(success=False, message="Failed to inspect field", error=str(e))


def validate_subset(resource_type: str, data: Dict[str, Any], fields: List[str]) -> HACSResult:
    """
    Validate a data payload against a subset model defined by fields.
    """
    try:
        registry = get_model_registry()
        resource_class = registry.get(resource_type)
        if not resource_class:
            return HACSResult(success=False, message=f"Unknown resource type: {resource_type}")
        if not hasattr(resource_class, "pick"):
            return HACSResult(
                success=False, message=f"Model {resource_type} does not support 'pick'"
            )
        subset_cls = resource_class.pick(*fields)
        try:
            subset_instance = subset_cls(**data)
            return HACSResult(
                success=True,
                message="Subset is valid",
                data={"resource": subset_instance.model_dump()},
            )
        except Exception as e:
            return HACSResult(success=False, message="Subset validation failed", error=str(e))
    except Exception as e:
        return HACSResult(success=False, message="Failed to validate subset", error=str(e))


__all__.extend(
    [
        "list_nested_fields",
        "inspect_field",
        "validate_subset",
    ]
)


# --------------------------------------------
# LLM-assisted schema suggestion for bundles
# --------------------------------------------


def suggest_bundle_schema(
    use_case: str, candidate_resources: Optional[List[str]] = None, max_resources: int = 4
) -> HACSResult:
    """
    Use an LLM to suggest a multi-resource bundle schema for a given use case.
    Returns resource types and selected fields per resource, plus a bundle template.
    """
    try:
        registry = get_model_registry()
        available = sorted(list(registry.keys()))
        if candidate_resources:
            candidates = [r for r in candidate_resources if r in registry]
        else:
            # Heuristic shortlist of commonly useful resources
            preferred = ["Document", "Patient", "Encounter", "Observation", "Condition"]
            candidates = [r for r in preferred if r in registry] or available[:8]

        # Build a compact field map for the prompt
        field_map: Dict[str, List[str]] = {}
        for rtype in candidates:
            fields = list(getattr(registry[rtype], "model_fields", {}).keys())
            # Keep a small subset for readability
            field_map[rtype] = fields[:20]


        # Response schema (loosely typed) for robust parsing

        # LLM generation temporarily disabled - fallback to deterministic plan
        llm_result = HACSResult(success=False, message="LLM not available")

        if llm_result.success and llm_result.data:
            plan_items = []
            for item in llm_result.data.get("resources", [])[:max_resources]:
                rtype = item.get("resource_type")
                fields = [
                    f
                    for f in item.get("fields", [])
                    if f in getattr(registry[rtype], "model_fields", {})
                ]
                if rtype in registry and fields:
                    plan_items.append({"resource_type": rtype, "required_fields": fields})
            if not plan_items:
                # Fall back to non-LLM plan if no usable response
                return plan_bundle_schema(resource_types=candidates[:max_resources])

            # Build template bundle
            entries: List[Dict[str, Any]] = []
            for item in plan_items:
                entries.append(
                    {
                        "title": item["resource_type"],
                        "tags": [item["resource_type"].lower()],
                        "priority": 5,
                        "resource_data": {"resource_type": item["resource_type"]},
                    }
                )
            bundle_result = compose_bundle(
                entries=entries, bundle_type="document", title="Suggested Bundle"
            )
            if not bundle_result.success:
                return bundle_result

            return HACSResult(
                success=True,
                message="Suggested bundle schema (LLM)",
                data={
                    "resources": plan_items,
                    "bundle_template": bundle_result.data.get("bundle"),
                    "use_case": use_case,
                    "source": "llm",
                },
            )

        # Fallback if LLM not available
        return plan_bundle_schema(resource_types=candidates[:max_resources])
    except Exception as e:
        # Final fallback to deterministic plan
        try:
            return plan_bundle_schema(resource_types=candidates[:max_resources])
        except Exception:
            return HACSResult(
                success=False, message="Failed to suggest bundle schema", error=str(e)
            )


__all__.extend(
    [
        "suggest_bundle_schema",
    ]
)


# --------------------------------------------
# Binding helpers (records -> composition/bundle; evidence -> document)
# --------------------------------------------


def build_composition(
    resources: List[Dict[str, Any]],
    *,
    patient_id: Optional[str] = None,
    title: Optional[str] = None,
) -> HACSResult:
    """
    Create a Document (Composition) from existing resource records and attribute to a patient.
    """
    try:
        doc = Document(title=title or "Clinical Composition")
        if patient_id:
            doc.subject_id = patient_id
        # Add simple sections summarizing each resource
        for res in resources:
            rtype = res.get("resource_type", "Resource")
            rid = res.get("id", "")
            doc.add_section(title=f"{rtype}", text=f"Linked resource: {rtype}/{rid}")
        bundle = doc.to_resource_bundle()
        return HACSResult(
            success=True,
            message="Composition built",
            data={"document": doc.model_dump(), "bundle": bundle.model_dump()},
        )
    except Exception as e:
        return HACSResult(success=False, message="Failed to build composition", error=str(e))


def reference_evidence(*args, **kwargs) -> HACSResult:
    return HACSResult(
        success=False,
        message="reference_evidence removed; use set_reference/make_reference in agents.",
    )


__all__.extend(
    [
        # Binding
        "build_composition",
    ]
)


# --------------------------------------------
# Generic referencing helpers (FHIR-style Reference)
# --------------------------------------------


def make_reference(
    resource: Optional[Dict[str, Any]] = None,
    *,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    display: Optional[str] = None,
) -> HACSResult:
    """
    Create a generic reference object and string ("ResourceType/id").
    Accepts either a full resource dict or explicit type/id.
    """
    try:
        if resource:
            rtype = resource.get("resource_type")
            rid = resource.get("id")
            disp = display or resource.get("title") or resource.get("name") or None
        else:
            rtype = resource_type
            rid = resource_id
            disp = display
        if not rtype or not rid:
            return HACSResult(success=False, message="Missing resource_type or id for reference")
        ref_str = f"{rtype}/{rid}"
        ref_obj = Reference(reference=ref_str, type=rtype, display=disp)
        return HACSResult(
            success=True,
            message="Reference created",
            data={"reference": ref_str, "object": ref_obj.model_dump()},
        )
    except Exception as e:
        return HACSResult(success=False, message="Failed to create reference", error=str(e))


def set_reference(
    resource: Dict[str, Any],
    field: str,
    *,
    reference: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    display: Optional[str] = None,
) -> HACSResult:
    """
    Set a FHIR-style reference string into a resource at the given dot-path "field".
    If reference not provided, builds from resource_type/id.
    """
    try:
        if not reference:
            mref = make_reference(
                resource_type=resource_type, resource_id=resource_id, display=display
            )
            if not mref.success:
                return mref
            reference = mref.data.get("reference")
        target = dict(resource)
        set_nested_field(target, field, reference)
        return HACSResult(
            success=True,
            message="Reference set",
            data={"resource": target, "field": field, "reference": reference},
        )
    except Exception as e:
        return HACSResult(success=False, message="Failed to set reference", error=str(e))


def list_relations(resource: Dict[str, Any]) -> HACSResult:
    """Return agent_context.relations list (if any)."""
    try:
        rels = ((resource or {}).get("agent_context") or {}).get("relations") or []
        return HACSResult(
            success=True, message=f"Found {len(rels)} relations", data={"relations": rels}
        )
    except Exception as e:
        return HACSResult(success=False, message="Failed to list relations", error=str(e))


__all__.extend(
    [
        "make_reference",
        "set_reference",
    ]
)


# --------------------------------------------
# Graph traversal using GraphDefinition-like dict
# --------------------------------------------


def follow_graph(
    start: Dict[str, Any],
    graph_definition: Dict[str, Any],
    *,
    records: Optional[List[Dict[str, Any]]] = None,
    max_depth: int = 2,
) -> HACSResult:
    try:
        if not isinstance(start, dict) or "resource_type" not in start:
            return HACSResult(success=False, message="Invalid start resource")

        gd = graph_definition or {}
        links: List[Dict[str, Any]] = gd.get("link", []) or []
        start_ref = f"{start.get('resource_type')}/{start.get('id', '')}"

        # Build lookup for local resolution
        lookup: Dict[str, Dict[str, Any]] = {}
        for r in records or []:
            rtype = r.get("resource_type")
            rid = r.get("id")
            if rtype and rid:
                lookup[f"{rtype}/{rid}"] = r

        from collections import deque

        visited: Set[str] = set()
        edges: List[Dict[str, Any]] = []
        unresolved: List[str] = []
        q = deque()
        q.append((start, 0, start_ref))
        visited.add(start_ref)

        def extract_refs(resource: Dict[str, Any], path: str) -> List[str]:
            try:
                node: Any = resource
                for part in [p for p in path.split(".") if p]:
                    node = node.get(part) if isinstance(node, dict) else None
                    if node is None:
                        return []
                if isinstance(node, str):
                    return [node]
                if isinstance(node, list):
                    refs = []
                    for item in node:
                        if isinstance(item, str):
                            refs.append(item)
                        elif isinstance(item, dict) and "reference" in item:
                            refs.append(item["reference"])
                    return refs
                if isinstance(node, dict) and "reference" in node:
                    return [node["reference"]]
                return []
            except Exception:
                return []

        while q:
            current, depth, from_ref = q.popleft()
            depth_limited = depth >= max_depth
            for link in links:
                path = link.get("path")
                if not path:
                    continue
                targets = [t.get("type") for t in (link.get("target") or []) if isinstance(t, dict)]
                refs = extract_refs(current, path)
                for ref in refs:
                    if targets:
                        rtype = ref.split("/")[0] if "/" in ref else None
                        if rtype and rtype not in targets:
                            continue
                    edges.append({"from": from_ref, "to": ref, "path": path})
                    if not depth_limited and ref not in visited and ref in lookup:
                        visited.add(ref)
                        q.append((lookup[ref], depth + 1, ref))
                    elif not depth_limited and ref not in lookup:
                        unresolved.append(ref)

        return HACSResult(
            success=True,
            message="Graph traversal complete",
            data={"start": start_ref, "edges": edges, "unresolved": unresolved},
        )
    except Exception as e:
        return HACSResult(success=False, message="Failed to follow graph", error=str(e))


__all__.extend(["follow_graph"])
