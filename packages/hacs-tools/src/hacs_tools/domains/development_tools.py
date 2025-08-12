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
from typing import Any, Dict, List

from hacs_core.results import ResourceStackResult, ResourceTemplateResult
from hacs_core.tool_protocols import healthcare_tool, ToolCategory

logger = logging.getLogger(__name__)

# Import tool descriptions
from .descriptions import (
    CREATE_RESOURCE_STACK_DESCRIPTION,
    CREATE_CLINICAL_TEMPLATE_DESCRIPTION,
    OPTIMIZE_RESOURCE_FOR_LLM_DESCRIPTION,
)

@healthcare_tool(
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

@healthcare_tool(
    name="create_clinical_template",
    description="Generate pre-configured clinical templates for common healthcare scenarios",
    category=ToolCategory.DEVELOPMENT_TOOLS,
    healthcare_domains=['clinical_data'],
    fhir_resources=['Patient', 'Observation', 'Encounter', 'Condition', 'MedicationRequest', 'Medication', 'Procedure', 'Goal']
)
def create_clinical_template(
    template_type: str,
    focus_area: str,
    complexity_level: str = "standard",
    include_workflow_fields: bool = True
) -> ResourceTemplateResult:
    """
    Generate pre-configured clinical templates for common healthcare scenarios.

    This tool creates ready-to-use resource compositions for typical clinical
    workflows, eliminating the need to manually select fields for common
    healthcare use cases and ensuring clinical best practices.

    Args:
        template_type: Type of template ("assessment", "intake", "discharge", "monitoring", "referral", "consultation")
        focus_area: Clinical focus ("cardiology", "general", "emergency", "mental_health", "pediatric")
        complexity_level: Detail level ("minimal", "standard", "comprehensive")
        include_workflow_fields: Whether to include workflow management fields

    Returns:
        ResourceTemplateResult with the generated template schema and clinical metadata

    Examples:
        create_clinical_template("assessment", "cardiology") -> Cardiac assessment template
        create_clinical_template("intake", "general", "comprehensive") -> Comprehensive intake form
        create_clinical_template("consultation", "emergency", "standard") -> Emergency consultation template
    """
    try:
        # Define template configurations with healthcare focus
        template_configs = {
            "assessment": {
                "base_resources": ["Patient", "Observation", "Condition"],
                "core_fields": {
                    "Patient": ["full_name", "birth_date", "gender"],
                    "Observation": ["code", "value_quantity", "status", "effective_date_time"],
                    "Condition": ["code", "clinical_status", "severity"]
                },
                "clinical_purpose": "Patient health assessment and clinical evaluation"
            },
            "intake": {
                "base_resources": ["Patient", "FamilyMemberHistory", "AllergyIntolerance"],
                "core_fields": {
                    "Patient": ["full_name", "birth_date", "gender", "phone", "address"],
                    "FamilyMemberHistory": ["relationship", "condition"],
                    "AllergyIntolerance": ["code", "category", "reaction"]
                },
                "clinical_purpose": "Initial patient intake and medical history collection"
            },
            "consultation": {
                "base_resources": ["Patient", "Observation", "Condition", "Procedure"],
                "core_fields": {
                    "Patient": ["full_name", "birth_date", "gender"],
                    "Observation": ["code", "value_quantity", "status", "effective_date_time", "note"],
                    "Condition": ["code", "clinical_status", "severity", "note"],
                    "Procedure": ["code", "status", "performed_date_time", "note"]
                },
                "soap_sections": {
                    "subjective": ["chief_complaint", "history_present_illness", "review_systems"],
                    "objective": ["vital_signs", "physical_exam", "diagnostic_results"],
                    "assessment": ["primary_diagnosis", "differential_diagnosis", "clinical_impression"],
                    "plan": ["treatment_plan", "medications", "follow_up", "patient_education"]
                },
                "clinical_purpose": "Structured clinical consultation using SOAP methodology"
            },
            "discharge": {
                "base_resources": ["Patient", "Condition", "Procedure", "ServiceRequest"],
                "core_fields": {
                    "Patient": ["full_name", "birth_date"],
                    "Condition": ["code", "clinical_status"],
                    "Procedure": ["code", "status", "performed_date_time"],
                    "ServiceRequest": ["code", "intent", "priority"]
                },
                "clinical_purpose": "Patient discharge planning and care coordination"
            },
            "monitoring": {
                "base_resources": ["Patient", "Observation", "Goal"],
                "core_fields": {
                    "Patient": ["full_name", "birth_date"],
                    "Observation": ["code", "value_quantity", "status", "effective_date_time"],
                    "Goal": ["description_text", "lifecycle_status", "target"]
                },
                "clinical_purpose": "Ongoing patient monitoring and care plan tracking"
            },
            "referral": {
                "base_resources": ["Patient", "ServiceRequest", "Condition"],
                "core_fields": {
                    "Patient": ["full_name", "birth_date", "gender", "phone"],
                    "ServiceRequest": ["code", "intent", "priority", "reason_reference"],
                    "Condition": ["code", "clinical_status"]
                },
                "clinical_purpose": "Patient referral and care coordination"
            }
        }

        # Clinical focus area modifications
        focus_modifications = {
            "cardiology": {
                "Observation": ["code", "value_quantity", "status", "body_site"],
                "additional_concepts": ["heart_rate", "blood_pressure", "ecg"],
                "clinical_emphasis": "Cardiovascular health assessment and monitoring"
            },
            "emergency": {
                "Patient": ["full_name", "birth_date", "emergency_contact"],
                "priority_fields": ["priority", "urgency", "triage"],
                "clinical_emphasis": "Rapid assessment and emergency care protocols"
            },
            "mental_health": {
                "additional_resources": ["RiskAssessment"],
                "RiskAssessment": ["code", "status", "prediction"],
                "clinical_emphasis": "Mental health evaluation and risk assessment"
            },
            "pediatric": {
                "Patient": ["full_name", "birth_date", "guardian_contact"],
                "additional_concepts": ["growth_charts", "immunizations"],
                "clinical_emphasis": "Pediatric care with age-appropriate assessments"
            },
            "general": {
                "clinical_emphasis": "General medical care and routine healthcare"
            }
        }

        # Complexity level adjustments
        complexity_adjustments = {
            "minimal": {"field_limit": 5, "resources_limit": 2},
            "standard": {"field_limit": 10, "resources_limit": 3},
            "comprehensive": {"field_limit": 20, "resources_limit": 5}
        }

        if template_type not in template_configs:
            return ResourceTemplateResult(
                success=False,
                template_name="",
                template_type=template_type,
                focus_area=focus_area,
                template_schema={},
                clinical_workflows=[],
                use_cases=[],
                field_mappings={},
                customizable_fields=[],
                required_fields=[],
                fhir_compliance=False,
                validation_requirements=[],
                message=f"Unknown clinical template type: {template_type}"
            )

        config = template_configs[template_type]
        template_name = f"{template_type.title()}{focus_area.title()}Template"

        # Build template schema
        template_schema = {
            "type": "object",
            "title": template_name,
            "description": f"{template_type.title()} template for {focus_area} - {config['clinical_purpose']}",
            "properties": {},
            "required": []
        }

        field_mappings = {}
        customizable_fields = []
        required_fields = []
        clinical_workflows = [f"{focus_area}_{template_type}_workflow"]
        use_cases = [
            f"{focus_area} {template_type}",
            f"Clinical {template_type} workflow", 
            f"{complexity_level.title()} healthcare documentation",
            config["clinical_purpose"]
        ]

        # Apply complexity limits
        complexity = complexity_adjustments.get(complexity_level, complexity_adjustments["standard"])
        field_count = 0
        max_fields = complexity["field_limit"]

        # Handle SOAP sections for consultation templates
        soap_fields_reserved = 0
        if template_type == "consultation" and "soap_sections" in config:
            soap_fields_reserved = 12
            max_fields_for_base_resources = max(3, max_fields - soap_fields_reserved)
        else:
            max_fields_for_base_resources = max_fields

        # Process each resource in the template
        for resource_name in config["base_resources"]:
            if field_count >= max_fields_for_base_resources:
                break

            try:
                import hacs_core
                if not hasattr(hacs_core, resource_name):
                    continue

                resource_class = getattr(hacs_core, resource_name)
                resource_fields = config["core_fields"].get(resource_name, [])

                # Apply focus area modifications
                if focus_area in focus_modifications:
                    focus_mod = focus_modifications[focus_area]
                    if resource_name in focus_mod:
                        resource_fields = focus_mod[resource_name]

                # Limit fields based on remaining slots
                remaining_slots = max_fields_for_base_resources - field_count
                resource_fields = resource_fields[:remaining_slots]

                # Create view and extract schema
                if resource_fields:
                    view_class = resource_class.pick(*resource_fields)
                    view_schema = view_class.model_json_schema()

                    for field_name, field_schema in view_schema.get("properties", {}).items():
                        if field_name == "resource_type":
                            continue

                        prefixed_name = f"{resource_name.lower()}_{field_name}"
                        template_schema["properties"][prefixed_name] = field_schema
                        field_mappings[prefixed_name] = f"{resource_name}.{field_name}"
                        customizable_fields.append(prefixed_name)
                        field_count += 1

                        # Add to required based on clinical importance
                        if field_name in view_schema.get("required", []) or field_name in ["id", "status", "code"]:
                            template_schema["required"].append(prefixed_name)
                            required_fields.append(prefixed_name)

            except Exception:
                continue  # Skip problematic resources

        # Add SOAP sections for consultation templates
        if template_type == "consultation" and "soap_sections" in config:
            soap_sections = config["soap_sections"]

            for section_name, section_fields in soap_sections.items():
                section_schema = {
                    "type": "object",
                    "title": f"{section_name.upper()} Section",
                    "description": f"SOAP {section_name} section for clinical documentation",
                    "properties": {},
                    "required": []
                }

                # Add fields to section (limited to 3 key fields per section)
                for field_name in section_fields[:3]:
                    field_schema = {
                        "type": "string",
                        "description": f"{field_name.replace('_', ' ').title()} - Part of {section_name.upper()} section"
                    }

                    # Special handling for certain field types
                    if "date" in field_name.lower():
                        field_schema["format"] = "date-time"
                    elif field_name in ["vital_signs", "diagnostic_results"]:
                        field_schema = {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": f"List of {field_name.replace('_', ' ')}"
                        }

                    section_schema["properties"][field_name] = field_schema
                    if section_name in ["subjective", "assessment"]:
                        section_schema["required"].append(field_name)

                    field_count += 1

                # Add section to main schema
                template_schema["properties"][f"soap_{section_name}"] = section_schema
                field_mappings[f"soap_{section_name}"] = f"soap.{section_name}"
                customizable_fields.append(f"soap_{section_name}")

        # Add workflow fields if requested
        if include_workflow_fields and field_count < max_fields:
            workflow_fields = {
                "workflow_status": {"type": "string", "enum": ["draft", "active", "completed", "cancelled"]},
                "created_by": {"type": "string", "description": "Healthcare actor who created this record"},
                "last_updated": {"type": "string", "format": "date-time"}
            }

            for wf_field, wf_schema in workflow_fields.items():
                if field_count >= max_fields:
                    break
                template_schema["properties"][wf_field] = wf_schema
                field_mappings[wf_field] = "workflow.system"
                customizable_fields.append(wf_field)
                field_count += 1

        # Determine FHIR compliance
        fhir_compliance = all(resource in [
            "Patient", "Observation", "Encounter", "Condition",
            "MedicationRequest", "Medication", "AllergyIntolerance", 
            "Procedure", "Goal", "ServiceRequest"
        ] for resource in config["base_resources"])

        # Generate validation requirements
        validation_requirements = [
            "Clinical data validation required",
            "Healthcare professional review recommended",
            "FHIR compliance validation if applicable"
        ]
        if focus_area in ["emergency", "mental_health"]:
            validation_requirements.append("Specialized clinical review required")

        return ResourceTemplateResult(
            success=True,
            template_name=template_name,
            template_type=template_type,
            focus_area=focus_area,
            template_schema=template_schema,
            clinical_workflows=clinical_workflows,
            use_cases=use_cases,
            field_mappings=field_mappings,
            customizable_fields=customizable_fields,
            required_fields=required_fields,
            fhir_compliance=fhir_compliance,
            validation_requirements=validation_requirements,
            message=f"Created {template_name} with {field_count} fields for {focus_area} {template_type}"
        )

    except Exception as e:
        return ResourceTemplateResult(
            success=False,
            template_name="",
            template_type=template_type,
            focus_area=focus_area,
            template_schema={},
            clinical_workflows=[],
            use_cases=[],
            field_mappings={},
            customizable_fields=[],
            required_fields=[],
            fhir_compliance=False,
            validation_requirements=[],
            message=f"Failed to create clinical template: {str(e)}"
        )

@healthcare_tool(
    name="optimize_resource_for_llm",
    description="Optimize a HACS healthcare resource for LLM interactions by intelligent field selection",
    category=ToolCategory.DEVELOPMENT_TOOLS,
    healthcare_domains=['resource_management'],
    fhir_resources=['Patient', 'Observation', 'Encounter', 'Condition', 'MedicationRequest', 'Medication', 'Procedure', 'Goal']
)
def optimize_resource_for_llm(
    resource_name: str,
    optimization_goal: str = "token_efficiency",
    target_use_case: str = "structured_output",
    preserve_validation: bool = True
) -> ResourceTemplateResult:
    """
    Optimize a HACS healthcare resource for LLM interactions by intelligent field selection.

    This tool automatically selects the most LLM-friendly fields from a healthcare
    resource based on optimization goals and clinical use case requirements.

    Args:
        resource_name: Name of the HACS resource to optimize
        optimization_goal: Goal ("token_efficiency", "accuracy", "completeness", "simplicity") 
        target_use_case: Target use case ("structured_output", "classification", "extraction", "validation")
        preserve_validation: Whether to keep validation-critical fields

    Returns:
        ResourceTemplateResult with optimized resource schema and clinical context

    Examples:
        optimize_resource_for_llm("Patient", "token_efficiency") -> Minimal essential Patient fields
        optimize_resource_for_llm("Observation", "accuracy", "structured_output") -> LLM-optimized Observation
        optimize_resource_for_llm("Condition", "completeness", "clinical_classification") -> Complete Condition view
    """
    try:
        import hacs_core

        if not hasattr(hacs_core, resource_name):
            return ResourceTemplateResult(
                success=False,
                template_name="",
                template_type="llm_optimization",
                focus_area="ai_agents",
                template_schema={},
                clinical_workflows=[],
                use_cases=[],
                field_mappings={},
                customizable_fields=[],
                required_fields=[],
                fhir_compliance=False,
                validation_requirements=[],
                message=f"Healthcare resource '{resource_name}' not found"
            )

        resource_class = getattr(hacs_core, resource_name)
        all_fields = list(resource_class.model_fields.keys())

        # Define optimization strategies
        optimization_strategies = {
            "token_efficiency": {
                "max_fields": 6,
                "prefer_types": ["str", "bool", "int"],
                "avoid_types": ["list", "dict", "complex"],
                "priority_patterns": ["name", "id", "status", "type", "code"]
            },
            "accuracy": {
                "max_fields": 8,
                "prefer_types": ["str", "bool", "enum"],
                "avoid_types": ["Any", "Union"],
                "priority_patterns": ["code", "status", "category", "type", "value"]
            },
            "completeness": {
                "max_fields": 15,
                "prefer_types": ["str", "int", "bool", "date"],
                "avoid_types": [],
                "priority_patterns": ["name", "code", "value", "status", "date", "type"]
            },
            "simplicity": {
                "max_fields": 4,
                "prefer_types": ["str", "bool"],
                "avoid_types": ["list", "dict", "Union", "Optional"],
                "priority_patterns": ["name", "status", "type"]
            }
        }

        # Use case specific requirements
        use_case_requirements = {
            "structured_output": {
                "required_patterns": ["name", "id"],
                "bonus_patterns": ["status", "code", "type"],
                "penalty_patterns": ["metadata", "extension"]
            },
            "classification": {
                "required_patterns": ["code", "category", "type"],
                "bonus_patterns": ["status", "classification"],
                "penalty_patterns": ["description", "note"]
            },
            "extraction": {
                "required_patterns": ["value", "code", "text"],
                "bonus_patterns": ["name", "description"],
                "penalty_patterns": ["metadata", "reference"]
            },
            "validation": {
                "required_patterns": ["status", "code"],
                "bonus_patterns": ["category", "type", "validation"],
                "penalty_patterns": ["display", "text"]
            }
        }

        strategy = optimization_strategies.get(optimization_goal, optimization_strategies["token_efficiency"])
        use_case_req = use_case_requirements.get(target_use_case, use_case_requirements["structured_output"])

        # Score fields based on optimization criteria
        field_scores = {}

        for field_name in all_fields:
            score = 0
            field_info = resource_class.model_fields[field_name]
            field_type = str(field_info.annotation).lower()

            # Type preferences
            for preferred_type in strategy["prefer_types"]:
                if preferred_type in field_type:
                    score += 3

            for avoided_type in strategy["avoid_types"]:
                if avoided_type in field_type:
                    score -= 2

            # Pattern matching
            field_lower = field_name.lower()

            for pattern in strategy["priority_patterns"]:
                if pattern in field_lower:
                    score += 2

            for pattern in use_case_req["required_patterns"]:
                if pattern in field_lower:
                    score += 5

            for pattern in use_case_req["bonus_patterns"]:
                if pattern in field_lower:
                    score += 1

            for pattern in use_case_req["penalty_patterns"]:
                if pattern in field_lower:
                    score -= 1

            # Validation preservation
            if preserve_validation:
                if field_info.default is ... and field_info.default_factory is None:
                    score += 1  # Required fields get bonus

            field_scores[field_name] = score

        # Select top scoring fields
        sorted_fields = sorted(field_scores.items(), key=lambda x: x[1], reverse=True)
        selected_fields = [field for field, score in sorted_fields[:strategy["max_fields"]]]

        # Create optimized view
        optimized_name = f"{resource_name}Optimized{optimization_goal.title()}"
        view_class = resource_class.pick(*selected_fields, name=optimized_name)
        schema = view_class.model_json_schema()

        # Build field mappings and metadata
        field_mappings = {field: f"{resource_name}.{field}" for field in selected_fields}
        
        # Generate clinical workflows and use cases
        clinical_workflows = [f"llm_{target_use_case}_workflow"]
        use_cases = [
            f"LLM {target_use_case}",
            f"{optimization_goal} optimized",
            f"Efficient {resource_name} processing",
            f"AI agent {resource_name} interaction"
        ]

        # Determine FHIR compliance
        fhir_compliance = resource_name in [
            "Patient", "Observation", "Encounter", "Condition",
            "MedicationRequest", "Medication", "AllergyIntolerance",
            "Procedure", "Goal", "ServiceRequest", "Organization"
        ]

        # Required fields for LLM usage
        required_fields = [field for field in selected_fields if field in ["id", "resource_type", "status"]]

        # Validation requirements
        validation_requirements = [
            "LLM output validation required",
            "Clinical context preservation required",
            "AI agent compatibility testing recommended"
        ]

        return ResourceTemplateResult(
            success=True,
            template_name=optimized_name,
            template_type="llm_optimization",
            focus_area="ai_agents", 
            template_schema=schema,
            clinical_workflows=clinical_workflows,
            use_cases=use_cases,
            field_mappings=field_mappings,
            customizable_fields=selected_fields,
            required_fields=required_fields,
            fhir_compliance=fhir_compliance,
            validation_requirements=validation_requirements,
            message=f"Optimized {resource_name} for {optimization_goal} with {len(selected_fields)} fields"
        )

    except Exception as e:
        return ResourceTemplateResult(
            success=False,
            template_name="",
            template_type="llm_optimization",
            focus_area="ai_agents",
            template_schema={},
            clinical_workflows=[],
            use_cases=[],
            field_mappings={},
            customizable_fields=[],
            required_fields=[],
            fhir_compliance=False,
            validation_requirements=[],
            message=f"Failed to optimize resource: {str(e)}"
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