"""
HACS Development Tools

This module provides advanced tools for healthcare resource composition,
stacking, and template generation. Enables sophisticated resource
manipulation and creation patterns for complex clinical workflows.

Key Features:
    🏗️ Healthcare resource stacking and composition
    📋 Clinical template generation for common scenarios
    ⚡ AI-optimized resource views
    🔄 Resource field analysis and optimization
    🏥 FHIR-compliant resource development
    🛠️ Advanced development workflows

All tools use ResourceStackResult and ResourceTemplateResult from
hacs_core.results for consistent development operation formatting.

Author: HACS Development Team
License: MIT
Version: 0.3.0
"""

import logging
from typing import Any, Dict, List, Optional
import os
import re
import json

from hacs_models import ResourceStackResult, ResourceTemplateResult
from hacs_models import StackTemplate, LayerSpec
from hacs_core.tool_protocols import hacs_tool, ToolCategory
@hacs_tool(
    name="register_prompt_template",
    description="Register an annotation PromptTemplate into the registry",
    category=ToolCategory.DEVELOPMENT_TOOLS,
    healthcare_domains=["templates", "annotation"],
    fhir_resources=["WorkflowDefinition"]
)
def register_prompt_template_tool(template: dict) -> ResourceTemplateResult:
    try:
        from hacs_registry import register_prompt_template
        name = template.get("name")
        version = template.get("version", "1.0.0")
        template_text = template.get("template_text", "")
        variables = template.get("variables", [])
        format = template.get("format", "json")
        fenced_output = template.get("fenced_output", True)
        reg = register_prompt_template(name, template_text, version=version, variables=variables, format=format, fenced_output=fenced_output)
        return ResourceTemplateResult(success=True, message="Prompt template registered", template=reg.model_dump())
    except Exception as e:
        return ResourceTemplateResult(success=False, message=str(e))


@hacs_tool(
    name="register_extraction_schema",
    description="Register an ExtractionSchema for annotation",
    category=ToolCategory.DEVELOPMENT_TOOLS,
    healthcare_domains=["templates", "annotation"],
    fhir_resources=["WorkflowDefinition"]
)
def register_extraction_schema_tool(schema: dict) -> ResourceTemplateResult:
    try:
        from hacs_registry import register_extraction_schema
        name = schema.get("name")
        version = schema.get("version", "1.0.0")
        response_schema = schema.get("response_schema")
        reg = register_extraction_schema(name, response_schema, version=version)
        return ResourceTemplateResult(success=True, message="Extraction schema registered", template=reg.model_dump())
    except Exception as e:
        return ResourceTemplateResult(success=False, message=str(e))

@hacs_tool(
    name="register_stack_template",
    description="Register a reusable stack template (resources + variable bindings)",
    category=ToolCategory.DEVELOPMENT_TOOLS,
    healthcare_domains=["resource_management", "templates"],
    fhir_resources=["ResourceBundle"]
)
def register_stack_template_tool(template: dict) -> ResourceTemplateResult:
    """Register a stack template via registry.

    Args:
        template: JSON payload matching StackTemplate schema (name, version, variables, layers)
    """
    try:
        from hacs_registry import register_stack_template
        from hacs_models import StackTemplate
        tmpl = StackTemplate(**template)
        reg = register_stack_template(tmpl)
        return ResourceTemplateResult(
            success=True,
            template_name=tmpl.name,
            template_type="generic",
            focus_area=template.get("focus_area", "general"),
            template_schema=tmpl.model_json_schema(),
            clinical_workflows=["generic_workflow"],
            use_cases=["generic_registration"],
            field_mappings={},
            customizable_fields=list((tmpl.variables or {}).keys()),
            required_fields=list((tmpl.variables or {}).keys()),
            fhir_compliance=True,
            validation_requirements=["Pydantic model validation"],
            message="Template registered",
            data={"id": str(reg.id), "name": tmpl.name},
        )
    except Exception as e:
        return ResourceTemplateResult(success=False, message=f"Failed: {e}")


@hacs_tool(
    name="generate_stack_template_from_markdown",
    description="Generate and register a HACS StackTemplate from a pre-built template payload (no embedded logic)",
    category=ToolCategory.DEVELOPMENT_TOOLS,
    healthcare_domains=["templates", "resource_management"],
    fhir_resources=["ResourceBundle"]
)
def generate_stack_template_from_markdown_tool(
    *,
    template: dict,
) -> ResourceTemplateResult:
    """Register a provided StackTemplate payload. All LLM/extraction logic must reside in the workflow.

    Args:
        template: dict conforming to StackTemplate schema (name, version, variables, layers, description)
    """
    try:
        from hacs_registry import register_stack_template
        payload = dict(template)
        tmpl = StackTemplate(**payload)
        reg = register_stack_template(tmpl)
        return ResourceTemplateResult(
            success=True,
            template_name=tmpl.name,
            template_type="generic",
            focus_area=payload.get("focus_area", "general"),
            template_schema=tmpl.model_json_schema(),
            clinical_workflows=["generic_workflow"],
            use_cases=["generic_registration"],
            field_mappings={},
            customizable_fields=list((tmpl.variables or {}).keys()),
            required_fields=list((tmpl.variables or {}).keys()),
            fhir_compliance=True,
            validation_requirements=["Pydantic model validation"],
            message="Template registered",
            data={"id": str(reg.id), "name": tmpl.name},
        )
    except Exception as e:
        return ResourceTemplateResult(success=False, message=f"Failed: {e}")


@hacs_tool(
    name="instantiate_stack_from_context",
    description="Instantiate a registered stack template from provided variables (no embedded extraction)",
    category=ToolCategory.DEVELOPMENT_TOOLS,
    healthcare_domains=["resource_management", "templates"],
    fhir_resources=["ResourceBundle"]
)
def instantiate_stack_from_context_tool(
    *,
    template_name: str,
    variables: dict,
) -> ResourceStackResult:
    """Instantiate a stack using provided variables. Extraction must occur in the workflow."""
    try:
        from hacs_registry import instantiate_registered_stack
        resources = instantiate_registered_stack(template_name, variables)
        layers_info = [{"layer": name, "resource_type": getattr(res, "resource_type", None), "id": getattr(res, "id", None)} for name, res in resources.items()]
        return ResourceStackResult(
            success=True,
            stack_name=template_name,
            layers=layers_info,
            base_resource_type=layers_info[0]["resource_type"] if layers_info else "",
            total_fields=len(variables),
            clinical_fields=0,
            dependencies=[l["resource_type"] for l in layers_info if l.get("resource_type")],
            validation_rules=[],
            fhir_compliance=True,
            clinical_use_cases=["context_instantiation"],
            message=f"Instantiated stack '{template_name}' with {len(resources)} resources",
            data={"variables": variables}
        )
    except Exception as e:
        return ResourceStackResult(success=False, stack_name=template_name, layers=[], base_resource_type="", total_fields=0, clinical_fields=0, dependencies=[], validation_rules=[], fhir_compliance=False, clinical_use_cases=[], message=f"Failed: {e}")


@hacs_tool(
    name="instantiate_stack_template",
    description="Instantiate a registered stack template by name and variables",
    category=ToolCategory.DEVELOPMENT_TOOLS,
    healthcare_domains=["resource_management", "templates"],
    fhir_resources=["ResourceBundle"]
)
def instantiate_stack_template_tool(template_name: str, variables: dict) -> ResourceStackResult:
    """Instantiate a registered stack template and return resource IDs/summary."""
    try:
        from hacs_registry import instantiate_registered_stack
        resources = instantiate_registered_stack(template_name, variables)
        summary = {k: getattr(v, 'id', None) for k, v in resources.items()}
        return ResourceStackResult(success=True, message="Stack instantiated", data=summary)
    except Exception as e:
        return ResourceStackResult(success=False, message=f"Failed: {e}")

logger = logging.getLogger(__name__)

# Import tool descriptions (none required for current tools)

@hacs_tool(
    name="create_resource_stack",
    description="Create a stacked healthcare resource by layering multiple resources or views",
    category=ToolCategory.DEVELOPMENT_TOOLS,
    healthcare_domains=['resource_management'],
    fhir_resources=['Patient', 'Observation', 'Encounter', 'Condition', 'MedicationRequest', 'Medication', 'Procedure', 'Goal']
)
def create_resource_stack(
    base_resource: str,
    extensions: List[Dict[str, Any]],
    stack_name: str,
    merge_strategy: str = "overlay"
) -> ResourceStackResult:
    """
    Create a stacked healthcare resource by layering multiple resources or views.

    This advanced tool enables building complex clinical data structures by
    stacking healthcare resources on top of each other, useful for comprehensive
    clinical workflows and multi-resource patient views.

    Args:
        base_resource: Name of the base HACS resource (foundation layer)
        extensions: List of extension specs: [{"resource": "ResourceName", "fields": [...], "layer_name": "..."}]
        stack_name: Name for the stacked resource
        merge_strategy: How to handle conflicts ("overlay", "prefix", "namespace")

    Returns:
        ResourceStackResult with stacked resource information and clinical metadata

    Examples:
        create_resource_stack("Patient", [
            {"resource": "Observation", "fields": ["code", "value_quantity"], "layer_name": "vitals"},
            {"resource": "Condition", "fields": ["code", "severity"], "layer_name": "conditions"}
        ], "ComprehensivePatientView")

        create_resource_stack("Encounter", [
            {"resource": "Procedure", "fields": ["code", "status"], "layer_name": "procedures"},
            {"resource": "MedicationRequest", "fields": ["medication", "dosage"], "layer_name": "medications"}
        ], "DetailedEncounterRecord")
    """
    try:
        import hacs_core

        # Validate base resource
        if not hasattr(hacs_core, base_resource):
            return ResourceStackResult(
                success=False,
                stack_name=stack_name,
                layers=[],
                base_resource_type=base_resource,
                total_fields=0,
                clinical_fields=0,
                dependencies=[],
                validation_rules=[],
                fhir_compliance=False,
                clinical_use_cases=[],
                message=f"Base healthcare resource '{base_resource}' not found"
            )

        base_class = getattr(hacs_core, base_resource)
        layers = []
        dependencies = [base_resource]
        total_fields = 0
        clinical_fields = 0
        all_validation_rules = []

        # Process base layer
        base_schema = base_class.model_json_schema()
        base_layer = {
            "layer_name": "base",
            "resource": base_resource,
            "fields": list(base_schema.get("properties", {}).keys()),
            "field_count": len(base_schema.get("properties", {})),
            "is_base": True,
            "clinical_significance": "high" if base_resource in ["Patient", "Observation", "Condition"] else "moderate"
        }
        layers.append(base_layer)
        total_fields += base_layer["field_count"]

        # Count clinical fields in base
        clinical_fields += _count_clinical_fields(base_layer["fields"], base_resource)

        # Process extension layers
        stacked_fields = set(base_schema.get("properties", {}).keys())
        field_conflicts = {}

        for ext in extensions:
            ext_resource = ext.get("resource")
            ext_fields = ext.get("fields", [])
            layer_name = ext.get("layer_name", ext_resource.lower())

            if not hasattr(hacs_core, ext_resource):
                return ResourceStackResult(
                    success=False,
                    stack_name=stack_name,
                    layers=layers,
                    base_resource_type=base_resource,
                    total_fields=total_fields,
                    clinical_fields=clinical_fields,
                    dependencies=dependencies,
                    validation_rules=[],
                    fhir_compliance=False,
                    clinical_use_cases=[],
                    message=f"Extension healthcare resource '{ext_resource}' not found"
                )

            _ = getattr(hacs_core, ext_resource)
            dependencies.append(ext_resource)

            # Handle field conflicts based on merge strategy
            conflicts = set(ext_fields) & stacked_fields
            resolved_fields = []

            for field in ext_fields:
                if field in conflicts:
                    if merge_strategy == "prefix":
                        resolved_field = f"{layer_name}_{field}"
                    elif merge_strategy == "namespace":
                        resolved_field = f"{layer_name}.{field}"
                    else:  # overlay
                        resolved_field = field
                        field_conflicts[field] = field_conflicts.get(field, []) + [f"{base_resource}", f"{ext_resource}"]
                else:
                    resolved_field = field

                resolved_fields.append(resolved_field)
                stacked_fields.add(resolved_field)

            # Determine clinical significance of extension
            clinical_significance = "high" if ext_resource in ["Observation", "Condition", "Procedure"] else "moderate"

            layer_info = {
                "layer_name": layer_name,
                "resource": ext_resource,
                "fields": resolved_fields,
                "field_count": len(resolved_fields),
                "conflicts": list(conflicts),
                "is_base": False,
                "clinical_significance": clinical_significance
            }
            layers.append(layer_info)
            total_fields += len(resolved_fields)
            clinical_fields += _count_clinical_fields(resolved_fields, ext_resource)

        # Collect validation rules
        for resource_name in dependencies:
            resource_class = getattr(hacs_core, resource_name)
            if hasattr(resource_class, 'model_config'):
                config = resource_class.model_config
                if hasattr(config, 'extra'):
                    all_validation_rules.append(f"{resource_name}: extra={config.get('extra')}")

        # Determine FHIR compliance
        fhir_compliance = all(dep in [
            "Patient", "Observation", "Encounter", "Condition",
            "MedicationRequest", "Medication", "AllergyIntolerance",
            "Procedure", "Goal", "ServiceRequest", "Organization"
        ] for dep in dependencies)

        # Generate clinical use cases
        clinical_use_cases = _generate_clinical_use_cases(base_resource, dependencies, stack_name)

        return ResourceStackResult(
            success=True,
            stack_name=stack_name,
            layers=layers,
            base_resource_type=base_resource,
            total_fields=total_fields,
            clinical_fields=clinical_fields,
            dependencies=dependencies,
            validation_rules=all_validation_rules,
            fhir_compliance=fhir_compliance,
            clinical_use_cases=clinical_use_cases,
            message=f"Created healthcare resource stack '{stack_name}' with {len(layers)} layers and {total_fields} total fields"
        )

    except Exception as e:
        return ResourceStackResult(
            success=False,
            stack_name=stack_name,
            layers=[],
            base_resource_type=base_resource,
            total_fields=0,
            clinical_fields=0,
            dependencies=[],
            validation_rules=[],
            fhir_compliance=False,
            clinical_use_cases=[],
            message=f"Failed to create healthcare resource stack: {str(e)}"
        )

 

# === UTILITY FUNCTIONS ===

def _count_clinical_fields(fields: List[str], resource_type: str) -> int:
    """Count fields that have clinical significance."""
    clinical_patterns = [
        "diagnosis", "condition", "symptom", "vital", "lab", "result",
        "medication", "allergy", "procedure", "treatment", "clinical",
        "medical", "health", "care", "therapy", "assessment", "code", "status"
    ]
    count = 0
    for field in fields:
        if any(pattern in field.lower() for pattern in clinical_patterns):
            count += 1
    return count

def _generate_clinical_use_cases(base_resource: str, dependencies: List[str], stack_name: str) -> List[str]:
    """Generate clinical use cases for a resource stack."""
    use_cases = []

    # Base use case
    use_cases.append(f"Comprehensive {base_resource.lower()} management")

    # Add specialty use cases based on dependencies
    if "Observation" in dependencies:
        use_cases.append("Clinical monitoring and vital signs tracking")
    if "Condition" in dependencies:
        use_cases.append("Disease management and diagnosis tracking")
    if "Procedure" in dependencies:
        use_cases.append("Treatment and procedure documentation")
    if "MedicationRequest" in dependencies:
        use_cases.append("Medication management and prescribing")

    # Add stack-specific use case
    use_cases.append(f"Integrated healthcare workflow using {stack_name}")

    return use_cases

__all__ = [
    "create_resource_stack",
    "create_clinical_template",
    "optimize_resource_for_llm",
]