"""
HACS Schema Discovery Tools

This module provides comprehensive schema analysis and discovery tools
for healthcare resources. Enables AI agents to understand resource
structures, field relationships, and FHIR compliance requirements.

Key Features:
    🔍 Resource schema discovery and analysis
    📊 Field-level analysis with clinical context
    🏥 FHIR compliance assessment
    📋 Resource comparison and mapping
    ⚡ AI-optimized schema recommendations
    🛠️ Custom view generation

All tools use ResourceSchemaResult and ResourceDiscoveryResult from
hacs_core.results for consistent response formatting.

Author: HACS Development Team
License: MIT
Version: 0.3.0
"""

import logging
from typing import Any, Dict, List, Optional

from hacs_core.results import (
    ResourceSchemaResult, 
    ResourceDiscoveryResult,
    FieldAnalysisResult,
    HACSResult
)
from hacs_core.tool_protocols import healthcare_tool, ToolCategory

logger = logging.getLogger(__name__)

# Import tool descriptions
from .descriptions import (
    DISCOVER_HACS_RESOURCES_DESCRIPTION,
    GET_HACS_RESOURCE_SCHEMA_DESCRIPTION,
    ANALYZE_RESOURCE_FIELDS_DESCRIPTION,
    COMPARE_RESOURCE_SCHEMAS_DESCRIPTION,
)

@healthcare_tool(
    name="discover_hacs_resources",
    description="Discover all available HACS healthcare resources with comprehensive metadata",
    category=ToolCategory.SCHEMA_DISCOVERY,
    healthcare_domains=['resource_management'],
    fhir_resources=['Patient', 'Observation', 'Encounter', 'Condition', 'MedicationRequest', 'Medication', 'Procedure', 'Goal']
)
def discover_hacs_resources(
    category_filter: Optional[str] = None,
    include_field_counts: bool = True,
    include_fhir_status: bool = True
) -> ResourceDiscoveryResult:
    """
    Discover all available HACS healthcare resources with comprehensive metadata.

    This tool helps AI agents understand what healthcare resources are available
    for manipulation, their clinical purposes, FHIR compliance status, and
    basic statistics about their structure.

    Args:
        category_filter: Optional filter by resource category (clinical, administrative, workflow)
        include_field_counts: Whether to include detailed field count information
        include_fhir_status: Whether to include FHIR compliance assessment

    Returns:
        ResourceDiscoveryResult with comprehensive resource catalog and metadata

    Examples:
        discover_hacs_resources() -> Lists all Patient, Observation, Goal, etc. resources
        discover_hacs_resources("clinical") -> Only clinical resources like Patient, Observation
        discover_hacs_resources("administrative", include_fhir_status=True) -> Admin resources with FHIR status
    """
    try:
        import inspect
        import hacs_core
        from hacs_core import BaseResource

        resources = []
        categories = set()
        fhir_resources = []
        clinical_resources = []
        administrative_resources = []

        for name in dir(hacs_core):
            obj = getattr(hacs_core, name)
            if inspect.isclass(obj) and issubclass(obj, BaseResource) and obj is not BaseResource:
                # Determine clinical category
                category = "administrative"
                if any(term in name.lower() for term in ["patient", "observation", "condition", "procedure", "medication", "allergy"]):
                    category = "clinical"
                    clinical_resources.append(name)
                elif any(term in name.lower() for term in ["appointment", "task", "service"]):
                    category = "workflow"
                elif any(term in name.lower() for term in ["goal", "risk", "family"]):
                    category = "assessment"
                    clinical_resources.append(name)
                else:
                    administrative_resources.append(name)

                categories.add(category)

                # Basic resource information
                resource_info = {
                    "name": name,
                    "category": category,
                    "description": obj.__doc__.split('\n')[0] if obj.__doc__ else f"{name} healthcare resource",
                    "resource_type": getattr(obj, 'resource_type', name),
                }

                # Add field count information if requested
                if include_field_counts:
                    field_count = len(obj.model_fields)
                    required_count = len([f for f, info in obj.model_fields.items()
                                        if info.default is ... and info.default_factory is None])
                    resource_info.update({
                        "total_fields": field_count,
                        "required_fields": required_count,
                        "optional_fields": field_count - required_count
                    })

                # Add FHIR compliance status if requested
                if include_fhir_status:
                    # Check for FHIR-specific attributes
                    is_fhir_compliant = hasattr(obj, 'fhir_resource_type') or name in [
                        "Patient", "Observation", "Encounter", "Condition", 
                        "MedicationRequest", "Medication", "AllergyIntolerance",
                        "Procedure", "Goal", "ServiceRequest", "Organization"
                    ]
                    resource_info["fhir_compliant"] = is_fhir_compliant
                    if is_fhir_compliant:
                        fhir_resources.append(name)

                # Apply category filter
                if not category_filter or category == category_filter:
                    resources.append(resource_info)

        return ResourceDiscoveryResult(
            success=True,
            resources=resources,
            total_count=len(resources),
            categories=list(categories),
            fhir_resources=fhir_resources,
            clinical_resources=clinical_resources,
            administrative_resources=administrative_resources,
            message=f"Discovered {len(resources)} healthcare resources" + 
                   (f" in category '{category_filter}'" if category_filter else "")
        )

    except Exception as e:
        return ResourceDiscoveryResult(
            success=False,
            resources=[],
            total_count=0,
            categories=[],
            fhir_resources=[],
            clinical_resources=[],
            administrative_resources=[],
            message=f"Failed to discover healthcare resources: {str(e)}"
        )

@healthcare_tool(
    name="get_hacs_resource_schema",
    description="Get comprehensive schema information for a healthcare resource type",
    category=ToolCategory.SCHEMA_DISCOVERY,
    healthcare_domains=['resource_management'],
    fhir_resources=['Patient', 'Observation', 'Encounter', 'Condition', 'MedicationRequest', 'Medication', 'Procedure', 'Goal']
)
def get_hacs_resource_schema(
    resource_type: str,
    include_examples: bool = True,
    include_validation_rules: bool = True
) -> ResourceSchemaResult:
    """
    Get comprehensive schema information for a healthcare resource type.

    Provides detailed JSON schema definition including field types, validation
    rules, clinical context, and FHIR compliance information.

    Args:
        resource_type: Name of the healthcare resource type (Patient, Observation, etc.)
        include_examples: Whether to include field examples in the schema
        include_validation_rules: Whether to include validation rule details

    Returns:
        ResourceSchemaResult with complete schema information and clinical context

    Examples:
        get_hacs_resource_schema("Patient") -> Complete Patient resource schema
        get_hacs_resource_schema("Observation", include_examples=False) -> Observation schema without examples
    """
    try:
        # Get resource class
        resource_class = _get_resource_class(resource_type)
        if not resource_class:
            return ResourceSchemaResult(
                success=False,
                resource_type=resource_type,
                schema={},
                fhir_compliance=False,
                required_fields=[],
                optional_fields=[],
                field_count=0,
                message=f"Healthcare resource type '{resource_type}' not found"
            )

        # Generate JSON schema
        schema = resource_class.model_json_schema()
        
        # Extract field information
        properties = schema.get("properties", {})
        required_fields = schema.get("required", [])
        optional_fields = [field for field in properties.keys() if field not in required_fields]
        
        # Determine FHIR compliance
        fhir_compliance = resource_type in [
            "Patient", "Observation", "Encounter", "Condition",
            "MedicationRequest", "Medication", "AllergyIntolerance",
            "Procedure", "Goal", "ServiceRequest", "Organization"
        ]

        # Collect validation rules if requested
        validation_rules = []
        if include_validation_rules:
            for field_name, field_info in resource_class.model_fields.items():
                if field_info.constraints:
                    validation_rules.append(f"{field_name}: {field_info.constraints}")

        # Add clinical context
        clinical_context = _get_clinical_context(resource_type)

        return ResourceSchemaResult(
            success=True,
            resource_type=resource_type,
            schema=schema,
            fhir_compliance=fhir_compliance,
            required_fields=required_fields,
            optional_fields=optional_fields,
            field_count=len(properties),
            validation_rules=validation_rules,
            clinical_context=clinical_context,
            message=f"Healthcare resource schema retrieved for {resource_type}"
        )

    except Exception as e:
        return ResourceSchemaResult(
            success=False,
            resource_type=resource_type,
            schema={},
            fhir_compliance=False,
            required_fields=[],
            optional_fields=[],
            field_count=0,
            message=f"Failed to get schema for {resource_type}: {str(e)}"
        )

@healthcare_tool(
    name="analyze_resource_fields",
    description="Perform detailed analysis of healthcare resource fields for clinical usage",
    category=ToolCategory.SCHEMA_DISCOVERY,
    healthcare_domains=['resource_management'],
    fhir_resources=['Patient', 'Observation', 'Encounter', 'Condition', 'MedicationRequest', 'Medication', 'Procedure', 'Goal']
)
def analyze_resource_fields(
    resource_type: str,
    focus_area: str = "all",
    include_ai_recommendations: bool = True
) -> FieldAnalysisResult:
    """
    Perform detailed analysis of healthcare resource fields for clinical usage.

    Analyzes individual fields within a healthcare resource, providing insights
    about clinical significance, FHIR requirements, and AI optimization recommendations.

    Args:
        resource_type: Name of the healthcare resource type to analyze
        focus_area: Analysis focus (all, clinical, fhir, ai_optimization)  
        include_ai_recommendations: Whether to include AI agent usage recommendations

    Returns:
        FieldAnalysisResult with detailed field-by-field analysis and recommendations

    Examples:
        analyze_resource_fields("Patient", "clinical") -> Clinical field analysis for Patient
        analyze_resource_fields("Observation", "ai_optimization") -> AI-optimized field recommendations
    """
    try:
        # Get resource class
        resource_class = _get_resource_class(resource_type)
        if not resource_class:
            return FieldAnalysisResult(
                success=False,
                resource_type=resource_type,
                field_analysis={},
                clinical_fields=[],
                required_for_fhir=[],
                ai_optimized_fields=[],
                validation_summary={},
                recommendations=[],
                message=f"Healthcare resource type '{resource_type}' not found"
            )

        # Analyze each field
        field_analysis = {}
        clinical_fields = []
        required_for_fhir = []
        ai_optimized_fields = []

        for field_name, field_info in resource_class.model_fields.items():
            # Basic field analysis
            field_data = {
                "name": field_name,
                "type": str(field_info.annotation),
                "required": field_info.default is ... and field_info.default_factory is None,
                "description": field_info.description or "No description available"
            }

            # Clinical significance analysis
            if _is_clinical_field(field_name, resource_type):
                clinical_fields.append(field_name)
                field_data["clinical_significance"] = "high"
            
            # FHIR requirement analysis
            if _is_fhir_required(field_name, resource_type):
                required_for_fhir.append(field_name)
                field_data["fhir_required"] = True

            # AI optimization analysis
            if _is_ai_optimized(field_name, field_info):
                ai_optimized_fields.append(field_name)
                field_data["ai_friendly"] = True

            field_analysis[field_name] = field_data

        # Generate recommendations
        recommendations = []
        if include_ai_recommendations:
            recommendations = _generate_field_recommendations(resource_type, field_analysis, focus_area)

        # Create validation summary
        validation_summary = {
            "total_fields": len(field_analysis),
            "required_fields": len([f for f in field_analysis.values() if f["required"]]),
            "clinical_fields": len(clinical_fields),
            "fhir_required_fields": len(required_for_fhir),
            "ai_optimized_fields": len(ai_optimized_fields)
        }

        return FieldAnalysisResult(
            success=True,
            resource_type=resource_type,
            field_analysis=field_analysis,
            clinical_fields=clinical_fields,
            required_for_fhir=required_for_fhir,
            ai_optimized_fields=ai_optimized_fields,
            validation_summary=validation_summary,
            recommendations=recommendations,
            message=f"Field analysis completed for {resource_type} healthcare resource"
        )

    except Exception as e:
        return FieldAnalysisResult(
            success=False,
            resource_type=resource_type,
            field_analysis={},
            clinical_fields=[],
            required_for_fhir=[],
            ai_optimized_fields=[],
            validation_summary={},
            recommendations=[],
            message=f"Failed to analyze fields for {resource_type}: {str(e)}"
        )

@healthcare_tool(
    name="compare_resource_schemas",
    description="Compare schemas between two healthcare resource types for integration analysis",
    category=ToolCategory.SCHEMA_DISCOVERY,
    healthcare_domains=['resource_management'],
    fhir_resources=['Patient', 'Observation', 'Encounter', 'Condition', 'MedicationRequest', 'Medication', 'Procedure', 'Goal']
)
def compare_resource_schemas(
    resource_type_1: str,
    resource_type_2: str,
    comparison_focus: str = "structure"
) -> HACSResult:
    """
    Compare schemas between two healthcare resource types for integration analysis.

    Performs detailed comparison between healthcare resource schemas to identify
    common fields, differences, and integration opportunities.

    Args:
        resource_type_1: First healthcare resource type to compare
        resource_type_2: Second healthcare resource type to compare
        comparison_focus: Focus of comparison (structure, clinical, fhir)

    Returns:
        HACSResult with detailed schema comparison and integration recommendations

    Examples:
        compare_resource_schemas("Patient", "Observation") -> Compare Patient and Observation schemas
        compare_resource_schemas("Condition", "Procedure", "clinical") -> Clinical-focused comparison
    """
    try:
        # Get both resource classes
        class_1 = _get_resource_class(resource_type_1)
        class_2 = _get_resource_class(resource_type_2)

        if not class_1 or not class_2:
            missing = []
            if not class_1: missing.append(resource_type_1)
            if not class_2: missing.append(resource_type_2)
            return HACSResult(
                success=False,
                message=f"Healthcare resource type(s) not found: {', '.join(missing)}",
                error=f"Could not locate resource classes for comparison"
            )

        # Extract field information
        fields_1 = set(class_1.model_fields.keys())
        fields_2 = set(class_2.model_fields.keys())

        # Perform comparison analysis
        common_fields = fields_1.intersection(fields_2)
        unique_to_1 = fields_1 - fields_2
        unique_to_2 = fields_2 - fields_1

        # Detailed comparison data
        comparison_data = {
            "resource_1": {
                "type": resource_type_1,
                "total_fields": len(fields_1),
                "unique_fields": list(unique_to_1)
            },
            "resource_2": {
                "type": resource_type_2,
                "total_fields": len(fields_2),
                "unique_fields": list(unique_to_2)
            },
            "comparison": {
                "common_fields": list(common_fields),
                "common_field_count": len(common_fields),
                "similarity_percentage": (len(common_fields) / max(len(fields_1), len(fields_2))) * 100,
                "integration_potential": "high" if len(common_fields) > 5 else "moderate" if len(common_fields) > 2 else "low"
            }
        }

        return HACSResult(
            success=True,
            message=f"Schema comparison completed between {resource_type_1} and {resource_type_2}",
            data=comparison_data
        )

    except Exception as e:
        return HACSResult(
            success=False,
            message=f"Failed to compare schemas between {resource_type_1} and {resource_type_2}",
            error=str(e)
        )

# === UTILITY FUNCTIONS ===

def _get_resource_class(resource_type: str):
    """Get the resource class for a given resource type."""
    try:
        from hacs_core.models import (
            Patient, Observation, Encounter, Condition, MedicationRequest,
            Medication, AllergyIntolerance, Procedure, Goal, ServiceRequest,
            Organization, OrganizationContact, OrganizationQualification
        )

        resource_map = {
            "Patient": Patient,
            "Observation": Observation,
            "Encounter": Encounter,
            "Condition": Condition,
            "MedicationRequest": MedicationRequest,
            "Medication": Medication,
            "AllergyIntolerance": AllergyIntolerance,
            "Procedure": Procedure,
            "Goal": Goal,
            "ServiceRequest": ServiceRequest,
            "Organization": Organization,
            "OrganizationContact": OrganizationContact,
            "OrganizationQualification": OrganizationQualification,
        }

        return resource_map.get(resource_type)
    except ImportError:
        return None

def _get_clinical_context(resource_type: str) -> str:
    """Get clinical context description for a resource type."""
    clinical_contexts = {
        "Patient": "Core demographic and contact information for healthcare individuals",
        "Observation": "Clinical observations, vital signs, lab results, and assessments",
        "Encounter": "Healthcare visits, appointments, and clinical interactions",
        "Condition": "Medical conditions, diagnoses, and health problems",
        "MedicationRequest": "Prescription orders and medication requests",
        "Medication": "Drug and medication definitions with dosage information",
        "AllergyIntolerance": "Allergic reactions and substance intolerances",
        "Procedure": "Medical procedures, interventions, and treatments",
        "Goal": "Healthcare goals and care plan objectives",
        "ServiceRequest": "Orders for healthcare services and referrals",
        "Organization": "Healthcare organizations, facilities, and departments",
    }
    return clinical_contexts.get(resource_type, f"Healthcare resource for {resource_type} operations")

def _is_clinical_field(field_name: str, resource_type: str) -> bool:
    """Determine if a field has clinical significance."""
    clinical_patterns = [
        "diagnosis", "condition", "symptom", "vital", "lab", "result",
        "medication", "allergy", "procedure", "treatment", "clinical",
        "medical", "health", "care", "therapy", "assessment"
    ]
    return any(pattern in field_name.lower() for pattern in clinical_patterns)

def _is_fhir_required(field_name: str, resource_type: str) -> bool:
    """Determine if a field is required for FHIR compliance."""
    fhir_required_fields = {
        "Patient": ["id", "resource_type"],
        "Observation": ["id", "resource_type", "status", "code"],
        "Encounter": ["id", "resource_type", "status", "class"],
        "Condition": ["id", "resource_type", "code"],
    }
    return field_name in fhir_required_fields.get(resource_type, [])

def _is_ai_optimized(field_name: str, field_info) -> bool:
    """Determine if a field is optimized for AI agent usage."""
    ai_friendly_types = ["str", "bool", "int", "float"]
    field_type_str = str(field_info.annotation).lower()
    return any(ai_type in field_type_str for ai_type in ai_friendly_types)

def _generate_field_recommendations(resource_type: str, field_analysis: Dict, focus_area: str) -> List[str]:
    """Generate field usage recommendations based on analysis."""
    recommendations = []
    
    if focus_area in ["all", "clinical"]:
        clinical_count = len([f for f in field_analysis.values() if f.get("clinical_significance") == "high"])
        if clinical_count > 0:
            recommendations.append(f"Focus on {clinical_count} clinically significant fields for healthcare workflows")
    
    if focus_area in ["all", "ai_optimization"]:
        ai_count = len([f for f in field_analysis.values() if f.get("ai_friendly")])
        if ai_count > 0:
            recommendations.append(f"Prioritize {ai_count} AI-friendly fields for agent interactions")
    
    if focus_area in ["all", "fhir"]:
        fhir_count = len([f for f in field_analysis.values() if f.get("fhir_required")])
        if fhir_count > 0:
            recommendations.append(f"Ensure {fhir_count} FHIR-required fields are populated for compliance")

    return recommendations

__all__ = [
    "discover_hacs_resources",
    "get_hacs_resource_schema",
    "analyze_resource_fields",
    "compare_resource_schemas",
] 