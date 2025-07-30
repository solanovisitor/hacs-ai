"""
HACS Model Development Utilities

Advanced tools for model composition, stacking, and development workflows.
These utilities enable sophisticated model manipulation and creation patterns.
"""

from typing import Any, Dict, List
from pydantic import BaseModel, Field

try:
    from langchain_core.tools import tool
    _has_langchain = True
except ImportError:
    _has_langchain = False
    def tool(func):
        func._is_tool = True
        return func


class ModelStackResult(BaseModel):
    """Result for model stacking operations."""

    success: bool = Field(description="Whether the stacking succeeded")
    stack_name: str = Field(description="Name of the created model stack")
    layers: List[Dict[str, Any]] = Field(description="Information about each layer")
    total_fields: int = Field(description="Total fields in the complete stack")
    dependencies: List[str] = Field(description="Model dependencies in order")
    validation_rules: List[str] = Field(description="Combined validation rules")
    message: str = Field(description="Human-readable result message")


class ModelTemplateResult(BaseModel):
    """Result for model template operations."""

    success: bool = Field(description="Whether template creation succeeded")
    template_name: str = Field(description="Name of the created template")
    template_schema: Dict[str, Any] = Field(description="JSON schema for the template")
    use_cases: List[str] = Field(description="Recommended use cases")
    field_mappings: Dict[str, str] = Field(description="Field to source model mappings")
    customizable_fields: List[str] = Field(description="Fields that can be customized")
    message: str = Field(description="Human-readable result message")


@tool
def create_model_stack(
    base_model: str,
    extensions: List[Dict[str, Any]],
    stack_name: str,
    merge_strategy: str = "overlay"
) -> ModelStackResult:
    """
    Create a stacked model by layering multiple models or views.

    This advanced tool enables building complex data structures by stacking
    models on top of each other, useful for comprehensive clinical workflows.

    Args:
        base_model: Name of the base HACS model (foundation layer)
        extensions: List of extension specs: [{"model": "ModelName", "fields": [...], "layer_name": "..."}]
        stack_name: Name for the stacked model
        merge_strategy: How to handle conflicts ("overlay", "prefix", "namespace")

    Returns:
        ModelStackResult with stacked model information

    Examples:
        create_model_stack("Patient", [
            {"model": "Observation", "fields": ["code", "value_quantity"], "layer_name": "vitals"},
            {"model": "Condition", "fields": ["code", "severity"], "layer_name": "conditions"}
        ], "ComprehensivePatientView")
    """
    try:
        import hacs_core

        # Validate base model
        if not hasattr(hacs_core, base_model):
            return ModelStackResult(
                success=False,
                stack_name=stack_name,
                layers=[],
                total_fields=0,
                dependencies=[],
                validation_rules=[],
                message=f"Base model '{base_model}' not found"
            )

        base_class = getattr(hacs_core, base_model)
        layers = []
        dependencies = [base_model]
        total_fields = 0
        all_validation_rules = []

        # Process base layer
        base_schema = base_class.model_json_schema()
        base_layer = {
            "layer_name": "base",
            "model": base_model,
            "fields": list(base_schema.get("properties", {}).keys()),
            "field_count": len(base_schema.get("properties", {})),
            "is_base": True
        }
        layers.append(base_layer)
        total_fields += base_layer["field_count"]

        # Process extension layers
        stacked_fields = set(base_schema.get("properties", {}).keys())
        field_conflicts = {}

        for ext in extensions:
            ext_model = ext.get("model")
            ext_fields = ext.get("fields", [])
            layer_name = ext.get("layer_name", ext_model.lower())

            if not hasattr(hacs_core, ext_model):
                return ModelStackResult(
                    success=False,
                    stack_name=stack_name,
                    layers=layers,
                    total_fields=total_fields,
                    dependencies=dependencies,
                    validation_rules=[],
                    message=f"Extension model '{ext_model}' not found"
                )

            ext_class = getattr(hacs_core, ext_model)
            dependencies.append(ext_model)

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
                        field_conflicts[field] = field_conflicts.get(field, []) + [f"{base_model}", f"{ext_model}"]
                else:
                    resolved_field = field

                resolved_fields.append(resolved_field)
                stacked_fields.add(resolved_field)

            layer_info = {
                "layer_name": layer_name,
                "model": ext_model,
                "fields": resolved_fields,
                "field_count": len(resolved_fields),
                "conflicts": list(conflicts),
                "is_base": False
            }
            layers.append(layer_info)
            total_fields += len(resolved_fields)

        # Collect validation rules
        for model_name in dependencies:
            model_class = getattr(hacs_core, model_name)
            if hasattr(model_class, 'model_config'):
                config = model_class.model_config
                if hasattr(config, 'extra'):
                    all_validation_rules.append(f"{model_name}: extra={config.get('extra')}")

        return ModelStackResult(
            success=True,
            stack_name=stack_name,
            layers=layers,
            total_fields=total_fields,
            dependencies=dependencies,
            validation_rules=all_validation_rules,
            message=f"Created model stack '{stack_name}' with {len(layers)} layers and {total_fields} total fields"
        )

    except Exception as e:
        return ModelStackResult(
            success=False,
            stack_name=stack_name,
            layers=[],
            total_fields=0,
            dependencies=[],
            validation_rules=[],
            message=f"Failed to create model stack: {str(e)}"
        )


@tool
def create_clinical_template(
    template_type: str,
    focus_area: str,
    complexity_level: str = "standard",
    include_workflow_fields: bool = True
) -> ModelTemplateResult:
    """
    Generate pre-configured clinical templates for common healthcare scenarios.

    This tool creates ready-to-use model compositions for typical clinical
    workflows, eliminating the need to manually select fields for common cases.

    Args:
        template_type: Type of template ("assessment", "intake", "discharge", "monitoring", "referral")
        focus_area: Clinical focus ("cardiology", "general", "emergency", "mental_health", "pediatric")
        complexity_level: Detail level ("minimal", "standard", "comprehensive")
        include_workflow_fields: Whether to include workflow management fields

    Returns:
        ModelTemplateResult with the generated template schema and metadata

    Examples:
        create_clinical_template("assessment", "cardiology") -> Cardiac assessment template
        create_clinical_template("intake", "general", "comprehensive") -> Comprehensive intake form
    """
    try:
        # Define template configurations - Enhanced with consultation type
        template_configs = {
            "assessment": {
                "base_models": ["Patient", "Observation", "Condition"],
                "core_fields": {
                    "Patient": ["full_name", "birth_date", "gender"],
                    "Observation": ["code", "value_quantity", "status", "effective_date_time"],
                    "Condition": ["code", "clinical_status", "severity"]
                }
            },
            "intake": {
                "base_models": ["Patient", "FamilyMemberHistory", "Allergy"],
                "core_fields": {
                    "Patient": ["full_name", "birth_date", "gender", "phone", "address"],
                    "FamilyMemberHistory": ["relationship", "condition"],
                    "Allergy": ["code", "category", "reaction"]
                }
            },
            "consultation": {
                "base_models": ["Patient", "Observation", "Condition", "Procedure"],
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
                }
            },
            "discharge": {
                "base_models": ["Patient", "Condition", "Procedure", "ServiceRequest"],
                "core_fields": {
                    "Patient": ["full_name", "birth_date"],
                    "Condition": ["code", "clinical_status"],
                    "Procedure": ["code", "status", "performed_date_time"],
                    "ServiceRequest": ["code", "intent", "priority"]
                }
            },
            "monitoring": {
                "base_models": ["Patient", "Observation", "Goal"],
                "core_fields": {
                    "Patient": ["full_name", "birth_date"],
                    "Observation": ["code", "value_quantity", "status", "effective_date_time"],
                    "Goal": ["description_text", "lifecycle_status", "target"]
                }
            },
            "referral": {
                "base_models": ["Patient", "ServiceRequest", "Condition"],
                "core_fields": {
                    "Patient": ["full_name", "birth_date", "gender", "phone"],
                    "ServiceRequest": ["code", "intent", "priority", "reason_reference"],
                    "Condition": ["code", "clinical_status"]
                }
            }
        }

        # Focus area modifications
        focus_modifications = {
            "cardiology": {
                "Observation": ["code", "value_quantity", "status", "body_site"],
                "additional_concepts": ["heart_rate", "blood_pressure", "ecg"]
            },
            "emergency": {
                "Patient": ["full_name", "birth_date", "emergency_contact"],
                "priority_fields": ["priority", "urgency", "triage"]
            },
            "mental_health": {
                "additional_models": ["RiskAssessment"],
                "RiskAssessment": ["code", "status", "prediction"]
            },
            "pediatric": {
                "Patient": ["full_name", "birth_date", "guardian_contact"],
                "additional_concepts": ["growth_charts", "immunizations"]
            }
        }

        # Complexity level adjustments
        complexity_adjustments = {
            "minimal": {"field_limit": 5, "models_limit": 2},
            "standard": {"field_limit": 10, "models_limit": 3},
            "comprehensive": {"field_limit": 20, "models_limit": 5}
        }

        if template_type not in template_configs:
            return ModelTemplateResult(
                success=False,
                template_name="",
                template_schema={},
                use_cases=[],
                field_mappings={},
                customizable_fields=[],
                message=f"Unknown template type: {template_type}"
            )

        config = template_configs[template_type]
        template_name = f"{template_type.title()}{focus_area.title()}Template"

        # Build template schema
        template_schema = {
            "type": "object",
            "title": template_name,
            "description": f"{template_type.title()} template for {focus_area} focused on {complexity_level} complexity",
            "properties": {},
            "required": []
        }

        field_mappings = {}
        customizable_fields = []
        use_cases = [
            f"{focus_area} {template_type}",
            f"Clinical {template_type} workflow",
            f"{complexity_level.title()} healthcare documentation"
        ]

        # Apply complexity limits
        complexity = complexity_adjustments.get(complexity_level, complexity_adjustments["standard"])
        field_count = 0
        max_fields = complexity["field_limit"]

        # For consultation templates, prioritize SOAP sections
        soap_fields_reserved = 0
        if template_type == "consultation" and "soap_sections" in config:
            # Reserve fields for SOAP sections (4 sections * 3 fields each)
            soap_fields_reserved = 12
            max_fields_for_base_models = max(3, max_fields - soap_fields_reserved)
        else:
            max_fields_for_base_models = max_fields

        # Process each model in the template (with limited fields for consultation)
        for model_name in config["base_models"]:
            if field_count >= max_fields_for_base_models:
                break

            try:
                import hacs_core
                if not hasattr(hacs_core, model_name):
                    continue

                model_class = getattr(hacs_core, model_name)
                model_fields = config["core_fields"].get(model_name, [])

                # Apply focus area modifications
                if focus_area in focus_modifications:
                    focus_mod = focus_modifications[focus_area]
                    if model_name in focus_mod:
                        model_fields = focus_mod[model_name]

                # Limit fields based on remaining slots for base models
                remaining_slots = max_fields_for_base_models - field_count
                model_fields = model_fields[:remaining_slots]

                # Create view and extract schema
                if model_fields:
                    view_class = model_class.pick(*model_fields)
                    view_schema = view_class.model_json_schema()

                    for field_name, field_schema in view_schema.get("properties", {}).items():
                        if field_name == "resource_type":
                            continue

                        prefixed_name = f"{model_name.lower()}_{field_name}"
                        template_schema["properties"][prefixed_name] = field_schema
                        field_mappings[prefixed_name] = f"{model_name}.{field_name}"
                        customizable_fields.append(prefixed_name)
                        field_count += 1

                        # Add to required based on original model
                        if field_name in view_schema.get("required", []):
                            template_schema["required"].append(prefixed_name)

            except Exception:
                continue  # Skip problematic models

        # Add SOAP sections for consultation templates - PRIORITY for consultation
        if template_type == "consultation" and "soap_sections" in config:
            soap_sections = config["soap_sections"]

            for section_name, section_fields in soap_sections.items():
                # Create section container
                section_schema = {
                    "type": "object",
                    "title": f"{section_name.upper()} Section",
                    "description": f"SOAP {section_name} section for clinical documentation",
                    "properties": {},
                    "required": []
                }

                # Add fields to section (limited to 3 key fields per section)
                for i, field_name in enumerate(section_fields[:3]):  # Limit to 3 fields per section
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
                    if section_name in ["subjective", "assessment"]:  # Required sections in SOAP
                        section_schema["required"].append(field_name)

                    field_count += 1

                # Add section to main schema
                template_schema["properties"][f"soap_{section_name}"] = section_schema
                field_mappings[f"soap_{section_name}"] = f"soap.{section_name}"
                customizable_fields.append(f"soap_{section_name}")

                # Update use cases to reflect SOAP structure
                if "SOAP" not in str(use_cases):
                    use_cases.insert(0, f"SOAP {section_name.upper()} documentation")

        # Add workflow fields if requested (and space permits)
        if include_workflow_fields and field_count < max_fields:
            workflow_fields = {
                "workflow_status": {"type": "string", "enum": ["draft", "active", "completed", "cancelled"]},
                "created_by": {"type": "string", "description": "User who created this record"},
                "last_updated": {"type": "string", "format": "date-time"}
            }

            for wf_field, wf_schema in workflow_fields.items():
                if field_count >= max_fields:
                    break
                template_schema["properties"][wf_field] = wf_schema
                field_mappings[wf_field] = "workflow.system"
                customizable_fields.append(wf_field)
                field_count += 1

        return ModelTemplateResult(
            success=True,
            template_name=template_name,
            template_schema=template_schema,
            use_cases=use_cases,
            field_mappings=field_mappings,
            customizable_fields=customizable_fields,
            message=f"Created {template_name} with {field_count} fields for {focus_area} {template_type}"
        )

    except Exception as e:
        return ModelTemplateResult(
            success=False,
            template_name="",
            template_schema={},
            use_cases=[],
            field_mappings={},
            customizable_fields=[],
            message=f"Failed to create clinical template: {str(e)}"
        )


@tool
def optimize_resource_for_llm(
    model_name: str,
    optimization_goal: str = "token_efficiency",
    target_use_case: str = "structured_output",
    preserve_validation: bool = True
) -> ModelTemplateResult:
    """
    Optimize a HACS resource for LLM interactions by intelligent field selection.

    This tool automatically selects the most LLM-friendly fields from a model
    based on optimization goals and use case requirements.

    Args:
        model_name: Name of the HACS model to optimize
        optimization_goal: Goal ("token_efficiency", "accuracy", "completeness", "simplicity")
        target_use_case: Target use case ("structured_output", "classification", "extraction", "validation")
        preserve_validation: Whether to keep validation-critical fields

    Returns:
        ModelTemplateResult with optimized model schema

    Examples:
        optimize_model_for_llm("Patient", "token_efficiency") -> Minimal essential Patient fields
        optimize_model_for_llm("Observation", "accuracy", "structured_output") -> LLM-optimized Observation
    """
    try:
        import hacs_core

        if not hasattr(hacs_core, model_name):
            return ModelTemplateResult(
                success=False,
                template_name="",
                template_schema={},
                use_cases=[],
                field_mappings={},
                customizable_fields=[],
                message=f"Model '{model_name}' not found"
            )

        model_class = getattr(hacs_core, model_name)
        all_fields = list(model_class.model_fields.keys())

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
            field_info = model_class.model_fields[field_name]
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
        optimized_name = f"{model_name}Optimized{optimization_goal.title()}"
        view_class = model_class.pick(*selected_fields, name=optimized_name)
        schema = view_class.model_json_schema()

        # Build field mappings and metadata
        field_mappings = {field: f"{model_name}.{field}" for field in selected_fields}
        use_cases = [
            f"LLM {target_use_case}",
            f"{optimization_goal} optimized",
            f"Efficient {model_name} processing"
        ]

        return ModelTemplateResult(
            success=True,
            template_name=optimized_name,
            template_schema=schema,
            use_cases=use_cases,
            field_mappings=field_mappings,
            customizable_fields=selected_fields,
            message=f"Optimized {model_name} for {optimization_goal} with {len(selected_fields)} fields"
        )

    except Exception as e:
        return ModelTemplateResult(
            success=False,
            template_name="",
            template_schema={},
            use_cases=[],
            field_mappings={},
            customizable_fields=[],
            message=f"Failed to optimize model: {str(e)}"
        )


__all__ = [
    "ModelStackResult",
    "ModelTemplateResult",
    "create_model_stack",
    "create_clinical_template",
    "optimize_resource_for_llm",
]