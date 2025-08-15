"""
LangGraph Functional API workflows for HACS HF ingestion - DIRECT HACS TOOLS VERSION.

Eliminates MCP dependency and uses HACS tools directly for improved reliability.

Provides two entrypoints:
- register_template_from_instruction: discovers models via HACS tools, generates and registers a StackTemplate from markdown.
- instantiate_and_persist_stack: fills a registered template with context, instantiates resources, and persists them.
"""

from __future__ import annotations

import os
import asyncio
import logging
from typing import Any, Dict, List, Optional

from langgraph.func import entrypoint, task
from langgraph.checkpoint.memory import InMemorySaver

from hacs_models import StackTemplate, LayerSpec
from hacs_registry import instantiate_registered_stack, get_global_registry, register_stack_template
from hacs_persistence.adapter import PostgreSQLAdapter
from hacs_core import Actor

# Direct HACS tool imports - no MCP dependency
from hacs_tools.domains.schema_discovery import (
    discover_hacs_resources,
    get_hacs_resource_schema
)
from hacs_tools.domains.development_tools import (
    register_stack_template_tool,
    instantiate_stack_template_tool,
)
from hacs_utils.annotation.chunking import ChunkIterator, make_batches_of_textchunk
from hacs_utils.annotation.data import (
    CharInterval as HCharInterval,
    AlignmentStatus as HAlignmentStatus,
    Document as HDocument,
)
from hacs_utils.structured import generate_extractions
from hacs_utils.integrations.common.tool_loader import get_all_hacs_tools_sync

logger = logging.getLogger(__name__)


def _generate_comprehensive_template_examples(type_hints: dict) -> str:
    """Generate comprehensive template examples with resource previews and required fields."""
    
    # Core template examples with detailed explanations
    core_examples = [
        {
            "name": "comprehensive_encounter_template",
            "description": "Multi-resource clinical encounter with observations, conditions, and procedures",
            "use_case": "Clinical consultations, emergency visits, routine check-ups",
            "template": {
                "name": "comprehensive_encounter_template",
                "version": "1.0.0",
                "variables": {
                    "patient_name": {"type": "string", "description": "Full patient name"},
                    "encounter_reason": {"type": "string", "description": "Chief complaint or visit reason"},
                    "vital_signs": {"type": "string", "description": "Blood pressure, temperature, etc."},
                    "diagnosis_text": {"type": "string", "description": "Primary diagnosis"},
                    "treatment_plan": {"type": "string", "description": "Care plan and instructions"}
                },
                "layers": [
                    {"resource_type": "ResourceBundle", "layer_name": "document_bundle", "bindings": {}, "constant_fields": {"bundle_type": "document", "title": "Clinical Encounter"}},
                    {"resource_type": "Patient", "layer_name": "patient", "bindings": {"full_name": "{{ patient_name }}"}, "constant_fields": {}},
                    {"resource_type": "Encounter", "layer_name": "encounter", "bindings": {"reason_code_text": "{{ encounter_reason }}", "subject": "patient"}, "constant_fields": {"status": "finished", "class_": {"code": "AMB"}}},
                    {"resource_type": "Observation", "layer_name": "vitals", "bindings": {"value_string": "{{ vital_signs }}", "subject": "patient", "encounter": "encounter"}, "constant_fields": {"status": "final", "code": {"text": "Vital Signs"}}},
                    {"resource_type": "Condition", "layer_name": "diagnosis", "bindings": {"code_text": "{{ diagnosis_text }}", "subject": "patient", "encounter": "encounter"}, "constant_fields": {"clinical_status": "active"}},
                    {"resource_type": "Procedure", "layer_name": "treatment", "bindings": {"code_text": "{{ treatment_plan }}", "subject": "patient", "encounter": "encounter"}, "constant_fields": {"status": "completed"}}
                ]
            }
        },
        {
            "name": "medication_management_template", 
            "description": "Medication prescription with monitoring observations",
            "use_case": "Prescriptions, medication reviews, drug therapy monitoring",
            "template": {
                "name": "medication_management_template",
                "version": "1.0.0",
                "variables": {
                    "patient_name": {"type": "string"},
                    "medication_name": {"type": "string"},
                    "dosage_instruction": {"type": "string"},
                    "monitoring_parameter": {"type": "string"}
                },
                "layers": [
                    {"resource_type": "ResourceBundle", "layer_name": "document_bundle", "bindings": {}, "constant_fields": {"bundle_type": "document", "title": "Medication Management"}},
                    {"resource_type": "Patient", "layer_name": "patient", "bindings": {"full_name": "{{ patient_name }}"}, "constant_fields": {}},
                    {"resource_type": "MedicationRequest", "layer_name": "prescription", "bindings": {"medication_codeable_concept_text": "{{ medication_name }}", "subject": "patient"}, "constant_fields": {"status": "active", "intent": "order"}},
                    {"resource_type": "Observation", "layer_name": "monitoring", "bindings": {"value_string": "{{ monitoring_parameter }}", "subject": "patient"}, "constant_fields": {"status": "final", "code": {"text": "Medication Monitoring"}}}
                ]
            }
        },
        {
            "name": "diagnostic_report_template",
            "description": "Laboratory or imaging results with multiple observations",
            "use_case": "Lab reports, imaging studies, diagnostic workups",
            "template": {
                "name": "diagnostic_report_template",
                "version": "1.0.0", 
                "variables": {
                    "patient_name": {"type": "string"},
                    "report_title": {"type": "string"},
                    "test_results": {"type": "string"},
                    "conclusion": {"type": "string"}
                },
                "layers": [
                    {"resource_type": "ResourceBundle", "layer_name": "document_bundle", "bindings": {}, "constant_fields": {"bundle_type": "document", "title": "Diagnostic Report"}},
                    {"resource_type": "Patient", "layer_name": "patient", "bindings": {"full_name": "{{ patient_name }}"}, "constant_fields": {}},
                    {"resource_type": "DiagnosticReport", "layer_name": "report", "bindings": {"code_text": "{{ report_title }}", "subject": "patient", "conclusion": "{{ conclusion }}"}, "constant_fields": {"status": "final"}},
                    {"resource_type": "Observation", "layer_name": "results", "bindings": {"value_string": "{{ test_results }}", "subject": "patient"}, "constant_fields": {"status": "final", "code": {"text": "Test Result"}}}
                ]
            }
        }
    ]
    
    # Generate resource previews with required fields
    resource_previews = _generate_resource_previews(type_hints)
    
    # Build comprehensive examples section
    examples_text = "COMPREHENSIVE TEMPLATE EXAMPLES AND RESOURCE REFERENCE:\n\n"
    
    # Add core template examples
    examples_text += "=== TEMPLATE EXAMPLES ===\n"
    for i, example in enumerate(core_examples, 1):
        examples_text += f"{i}) {example['name'].upper()}:\n"
        examples_text += f"   Description: {example['description']}\n"
        examples_text += f"   Use Cases: {example['use_case']}\n"
        examples_text += f"   Template JSON:\n"
        import json as _json
        examples_text += f"   {_json.dumps(example['template'], ensure_ascii=False, indent=2)}\n\n"
    
    # Add resource previews
    examples_text += resource_previews
    
    return examples_text


def _generate_detailed_resource_catalog(available_types: list[str]) -> str:
    """Generate a detailed catalog of available HACS resources with clinical context and relationships."""
    if not available_types:
        return "No HACS resources available."
    
    # Detailed resource definitions with clinical context, FHIR alignment, and use cases
    resource_definitions = {
        "Patient": {
            "description": "Core demographic and identification information for individuals receiving healthcare",
            "fhir_alignment": "FHIR Patient resource - foundational resource for all clinical documentation",
            "clinical_context": "Demographics, identifiers, contact information, emergency contacts",
            "common_fields": ["full_name", "birth_date", "gender", "phone", "address", "emergency_contact"],
            "relationships": "Referenced by: Observation, Encounter, Condition, MedicationRequest, Procedure",
            "use_cases": ["Patient registration", "Demographics capture", "Identity management"]
        },
        "Encounter": {
            "description": "Healthcare service interactions between patient and healthcare provider",
            "fhir_alignment": "FHIR Encounter resource - context for clinical activities",
            "clinical_context": "Visits, admissions, consultations, emergency encounters",
            "common_fields": ["status", "class_", "subject", "period", "reason_code", "diagnosis"],
            "relationships": "References: Patient, Organization, Practitioner; Referenced by: Observation, Procedure",
            "use_cases": ["Visit documentation", "Episode tracking", "Care context establishment"]
        },
        "Observation": {
            "description": "Clinical measurements, assessments, and findings about a patient",
            "fhir_alignment": "FHIR Observation resource - central to clinical documentation",
            "clinical_context": "Vital signs, lab results, assessments, clinical notes",
            "common_fields": ["code", "value_string", "value_quantity", "status", "subject", "encounter"],
            "relationships": "References: Patient, Encounter; May reference: Procedure, Condition",
            "use_cases": ["Vital signs", "Lab results", "Clinical assessments", "Progress notes"]
        },
        "Condition": {
            "description": "Patient health conditions, diagnoses, and clinical problems",
            "fhir_alignment": "FHIR Condition resource - patient health status documentation",
            "clinical_context": "Diagnoses, problems, health concerns, chronic conditions",
            "common_fields": ["code", "clinical_status", "subject", "encounter", "onset_date_time", "severity"],
            "relationships": "References: Patient, Encounter; Referenced by: MedicationRequest, Procedure",
            "use_cases": ["Diagnosis documentation", "Problem lists", "Clinical decision support"]
        },
        "MedicationRequest": {
            "description": "Prescription and medication ordering information",
            "fhir_alignment": "FHIR MedicationRequest resource - medication orders and prescriptions",
            "clinical_context": "Prescriptions, medication orders, therapy planning",
            "common_fields": ["medication_codeable_concept", "status", "intent", "subject", "dosage_instruction"],
            "relationships": "References: Patient, Encounter, Condition, Medication",
            "use_cases": ["E-prescribing", "Medication management", "Pharmacy integration"]
        },
        "Procedure": {
            "description": "Healthcare procedures, treatments, and interventions performed",
            "fhir_alignment": "FHIR Procedure resource - clinical procedures documentation",
            "clinical_context": "Surgeries, treatments, interventions, therapeutic procedures",
            "common_fields": ["code", "status", "subject", "encounter", "performed_date_time", "outcome"],
            "relationships": "References: Patient, Encounter, Condition; May create: Observation",
            "use_cases": ["Surgery documentation", "Treatment tracking", "Procedure billing"]
        },
        "DiagnosticReport": {
            "description": "Results and interpretations of diagnostic testing and investigations",
            "fhir_alignment": "FHIR DiagnosticReport resource - diagnostic test results",
            "clinical_context": "Lab reports, imaging studies, pathology results",
            "common_fields": ["code", "status", "subject", "conclusion", "result", "issued"],
            "relationships": "References: Patient, Encounter; Contains: Observation results",
            "use_cases": ["Lab reporting", "Imaging results", "Diagnostic interpretation"]
        },
        "ServiceRequest": {
            "description": "Orders and requests for healthcare services and procedures",
            "fhir_alignment": "FHIR ServiceRequest resource - service ordering and requisitions",
            "clinical_context": "Lab orders, imaging requests, referrals, consultations",
            "common_fields": ["code", "status", "intent", "subject", "encounter", "reason_code"],
            "relationships": "References: Patient, Encounter, Condition; Creates: DiagnosticReport",
            "use_cases": ["Lab ordering", "Imaging requests", "Referral management"]
        },
        "Goal": {
            "description": "Patient care goals, objectives, and targeted outcomes",
            "fhir_alignment": "FHIR Goal resource - care planning and outcome tracking",
            "clinical_context": "Treatment goals, health objectives, care planning",
            "common_fields": ["description_text", "lifecycle_status", "subject", "target", "start_date"],
            "relationships": "References: Patient, Condition; Part of: CarePlan",
            "use_cases": ["Care planning", "Treatment monitoring", "Outcome tracking"]
        },
        "DocumentReference": {
            "description": "References to clinical documents, reports, and external content",
            "fhir_alignment": "FHIR DocumentReference resource - document management",
            "clinical_context": "Clinical documents, reports, images, external references",
            "common_fields": ["status", "type", "subject", "content", "description"],
            "relationships": "References: Patient, Encounter; May contain: Attachment data",
            "use_cases": ["Document management", "Report linking", "External content reference"]
        },
        "Organization": {
            "description": "Healthcare organizations, facilities, and institutions",
            "fhir_alignment": "FHIR Organization resource - organizational entities",
            "clinical_context": "Hospitals, clinics, departments, healthcare systems",
            "common_fields": ["name", "type", "address", "contact", "identifier"],
            "relationships": "Referenced by: Encounter, Practitioner, Patient",
            "use_cases": ["Facility management", "Provider networks", "Organizational hierarchy"]
        },
        "Practitioner": {
            "description": "Healthcare providers, clinicians, and care team members",
            "fhir_alignment": "FHIR Practitioner resource - healthcare personnel",
            "clinical_context": "Doctors, nurses, therapists, care team members",
            "common_fields": ["name", "qualification", "specialty", "contact", "identifier"],
            "relationships": "Referenced by: Encounter, Procedure, MedicationRequest",
            "use_cases": ["Provider directories", "Care team management", "Professional credentials"]
        },
        "Medication": {
            "description": "Medication and pharmaceutical product definitions",
            "fhir_alignment": "FHIR Medication resource - pharmaceutical products",
            "clinical_context": "Drug definitions, formulations, pharmaceutical products",
            "common_fields": ["code", "form", "ingredient", "manufacturer", "amount"],
            "relationships": "Referenced by: MedicationRequest, MedicationStatement",
            "use_cases": ["Drug catalogs", "Pharmaceutical management", "Medication reconciliation"]
        },
        "AllergyIntolerance": {
            "description": "Patient allergies, intolerances, and adverse reactions",
            "fhir_alignment": "FHIR AllergyIntolerance resource - allergy documentation",
            "clinical_context": "Drug allergies, food allergies, environmental sensitivities",
            "common_fields": ["code", "patient", "category", "reaction", "severity"],
            "relationships": "References: Patient; Impacts: MedicationRequest decisions",
            "use_cases": ["Allergy alerts", "Medication safety", "Clinical decision support"]
        },
        "Immunization": {
            "description": "Vaccination records and immunization history",
            "fhir_alignment": "FHIR Immunization resource - vaccination documentation",
            "clinical_context": "Vaccines, immunizations, vaccination schedules",
            "common_fields": ["vaccine_code", "patient", "occurrence_date_time", "status"],
            "relationships": "References: Patient, Encounter, Organization",
            "use_cases": ["Vaccination tracking", "Immunization records", "Public health reporting"]
        },
        "ResourceBundle": {
            "description": "Container for grouping related HACS resources together",
            "fhir_alignment": "FHIR Bundle resource - resource collection container",
            "clinical_context": "Document bundles, transaction groups, resource collections",
            "common_fields": ["bundle_type", "title", "entries"],
            "relationships": "Contains: Any HACS resources as bundle entries",
            "use_cases": ["Document assembly", "Transaction grouping", "Resource packaging"]
        }
    }
    
    catalog_text = "=== DETAILED HACS RESOURCE CATALOG ===\n\n"
    
    # Group resources by clinical category for better organization
    categories = {
        "🏥 Foundational": ["Patient", "Encounter", "Organization", "Practitioner"],
        "📊 Clinical Data": ["Observation", "Condition", "Procedure", "DiagnosticReport"],
        "💊 Medication": ["MedicationRequest", "Medication", "AllergyIntolerance"],
        "📋 Care Planning": ["Goal", "ServiceRequest", "CarePlan"],
        "📄 Documentation": ["DocumentReference", "ResourceBundle"],
        "🛡️ Prevention": ["Immunization", "FamilyMemberHistory"]
    }
    
    for category_name, category_resources in categories.items():
        available_in_category = [r for r in category_resources if r in available_types]
        if not available_in_category:
            continue
            
        catalog_text += f"{category_name} RESOURCES:\n"
        catalog_text += "-" * 50 + "\n"
        
        for resource_type in available_in_category:
            if resource_type in resource_definitions:
                res_def = resource_definitions[resource_type]
                catalog_text += f"\n📌 {resource_type}:\n"
                catalog_text += f"   Description: {res_def['description']}\n"
                catalog_text += f"   FHIR Alignment: {res_def['fhir_alignment']}\n"
                catalog_text += f"   Clinical Context: {res_def['clinical_context']}\n"
                catalog_text += f"   Key Fields: {', '.join(res_def['common_fields'])}\n"
                catalog_text += f"   Relationships: {res_def['relationships']}\n"
                catalog_text += f"   Use Cases: {', '.join(res_def['use_cases'])}\n"
        
        catalog_text += "\n"
    
    # Add resources not in predefined categories
    uncategorized = [r for r in available_types if not any(r in cat_resources for cat_resources in categories.values())]
    if uncategorized:
        catalog_text += "🔧 OTHER AVAILABLE RESOURCES:\n"
        catalog_text += "-" * 50 + "\n"
        for resource_type in uncategorized:
            catalog_text += f"   • {resource_type}\n"
        catalog_text += "\n"
    
    catalog_text += "=== RESOURCE SELECTION GUIDELINES ===\n"
    catalog_text += "1. Always include Patient for individual-specific data\n"
    catalog_text += "2. Include Encounter for visit/episode context\n"
    catalog_text += "3. Use Observation for measurements and clinical findings\n"
    catalog_text += "4. Use Condition for diagnoses and health problems\n"
    catalog_text += "5. Use MedicationRequest for prescriptions and medications\n"
    catalog_text += "6. Use Procedure for treatments and interventions\n"
    catalog_text += "7. Consider DocumentReference for external content\n"
    catalog_text += "8. Use ResourceBundle as the container for all resources\n\n"
    
    return catalog_text


def _generate_resource_previews(type_hints: dict) -> str:
    """Generate previews of all available resources with their required fields."""
    
    if not type_hints:
        return "=== RESOURCE PREVIEWS ===\nNo resource information available.\n\n"
    
    previews_text = "=== AVAILABLE HACS RESOURCES WITH REQUIRED FIELDS ===\n"
    previews_text += "Use this reference to understand what fields are required for each resource type.\n\n"
    
    # Group resources by category
    resource_categories = {
        "Core Clinical": ["Patient", "Encounter", "Observation", "Condition", "Procedure"],
        "Medication": ["MedicationRequest", "Medication", "MedicationStatement"],
        "Diagnostics": ["DiagnosticReport", "ServiceRequest"],
        "Documentation": ["DocumentReference", "ResourceBundle"],
        "Care Planning": ["Goal", "CarePlan", "CareTeam", "PlanDefinition"],
        "Administrative": ["Organization", "Practitioner", "Appointment"],
        "Specialty": ["AllergyIntolerance", "Immunization", "FamilyMemberHistory", "NutritionOrder"]
    }
    
    for category, resources in resource_categories.items():
        category_resources = [r for r in resources if r in type_hints]
        if not category_resources:
            continue
            
        previews_text += f"--- {category.upper()} RESOURCES ---\n"
        
        for resource_type in category_resources:
            resource_info = type_hints[resource_type]
            required_fields = resource_info.get("required", [])
            view_fields = resource_info.get("view_fields", [])
            
            previews_text += f"\n{resource_type}:\n"
            previews_text += f"  Required Fields: {', '.join(required_fields) if required_fields else 'None'}\n"
            previews_text += f"  Key Fields: {', '.join(view_fields[:8]) if view_fields else 'None'}\n"  # Show first 8 fields
            
            # Add field descriptions from schema
            view_schema = resource_info.get("view_schema", {})
            if view_schema and required_fields:
                previews_text += f"  Field Details:\n"
                for field in required_fields[:3]:  # Show details for first 3 required fields
                    field_info = view_schema.get(field, {})
                    field_type = field_info.get("type", "unknown")
                    field_desc = field_info.get("description", "No description")
                    previews_text += f"    - {field} ({field_type}): {field_desc}\n"
        
        previews_text += "\n"
    
    # Add binding guidance
    previews_text += "=== BINDING GUIDANCE ===\n"
    previews_text += "- Use {{ variable_name }} syntax for variable bindings\n"
    previews_text += "- Provide constant_fields for required fields not bound to variables\n"
    previews_text += "- Use layer references like 'patient' or 'encounter' for resource linking\n"
    previews_text += "- Ensure all variables defined are used in at least one binding\n\n"
    
    return previews_text


def _get_template_extraction_context(template_name: str, template_vars: dict, remaining_vars: set) -> str:
    """Generate context information about the template to guide LLM extraction."""
    context = f"Template: {template_name}\n"
    context += f"Total Variables: {len(template_vars)}\n"
    context += f"Remaining to Extract: {len(remaining_vars)}\n\n"
    
    context += "VARIABLE GUIDANCE:\n"
    
    # Provide extraction guidance based on variable names
    guidance_map = {
        "patient_name": "Extract full patient name (first and last name)",
        "patient_full_name": "Extract complete patient name as written",
        "subject_full_name": "Extract patient's full legal name",
        "encounter_reason": "Extract chief complaint or reason for visit",
        "diagnosis_text": "Extract primary diagnosis or clinical impression",
        "vital_signs": "Extract vital sign measurements (BP, HR, temp, etc.)",
        "medication_name": "Extract specific medication name or brand",
        "medication_text": "Extract medication information including name and strength",
        "dosage_instruction": "Extract dosing information and administration instructions",
        "treatment_plan": "Extract treatment recommendations and care plan",
        "clinical_note": "Extract relevant clinical observations or notes",
        "condition_text": "Extract health condition or problem description",
        "procedure_name": "Extract procedure or intervention performed",
        "test_results": "Extract laboratory or diagnostic test results",
        "report_title": "Extract report or document title/type",
        "conclusion": "Extract clinical conclusion or summary",
        "assessment": "Extract clinical assessment or evaluation"
    }
    
    for var in sorted(remaining_vars):
        var_lower = var.lower()
        found_guidance = False
        
        for pattern, guidance in guidance_map.items():
            if pattern in var_lower:
                context += f"- {var}: {guidance}\n"
                found_guidance = True
                break
        
        if not found_guidance:
            # Generic guidance based on common patterns
            if "date" in var_lower or "time" in var_lower:
                context += f"- {var}: Extract date/time information in appropriate format\n"
            elif "name" in var_lower:
                context += f"- {var}: Extract name or identifier information\n"
            elif "code" in var_lower:
                context += f"- {var}: Extract medical code or classification\n"
            elif "status" in var_lower:
                context += f"- {var}: Extract status or state information\n"
            else:
                context += f"- {var}: Extract relevant clinical information for this field\n"
    
    context += "\nFOCUS ON:\n"
    context += "- Exact text as it appears in the clinical context\n"
    context += "- Medical terminology and standard abbreviations\n"
    context += "- Quantitative values with appropriate units\n"
    context += "- Structured clinical data when available\n"
    
    return context


def _validate_bundle_creation(bundle) -> Dict[str, Any]:
    """Validate that a ResourceBundle is properly created with resources."""
    if bundle is None:
        return {"status": "failed", "message": "Bundle is None", "details": {}}
    
    resource_type = getattr(bundle, "resource_type", None)
    if resource_type != "ResourceBundle":
        return {"status": "failed", "message": f"Object is not a ResourceBundle (type: {resource_type})", "details": {}}
    
    entry_count = len(bundle.entries) if hasattr(bundle, "entries") and bundle.entries else 0
    
    # Check entries have actual resources
    valid_entries = 0
    entry_details = []
    
    for i, entry in enumerate(bundle.entries):
        has_resource = hasattr(entry, "resource") and entry.resource is not None
        if has_resource:
            valid_entries += 1
            resource_type = getattr(entry.resource, "resource_type", "Unknown")
            resource_id = getattr(entry.resource, "id", "No ID")
            entry_details.append({"index": i, "type": resource_type, "id": resource_id, "title": getattr(entry, "title", "")})
    
    details = {
        "total_entries": entry_count,
        "valid_entries": valid_entries,
        "bundle_id": getattr(bundle, "id", "No ID"),
        "bundle_title": getattr(bundle, "title", "No Title"),
        "entries": entry_details
    }
    
    if entry_count == 0:
        return {"status": "warning", "message": "Bundle has no entries", "details": details}
    elif valid_entries == 0:
        return {"status": "failed", "message": "Bundle has entries but no valid resources", "details": details}
    elif valid_entries < entry_count:
        return {"status": "warning", "message": f"Bundle has {valid_entries}/{entry_count} valid entries", "details": details}
    else:
        return {"status": "success", "message": f"Bundle properly created with {valid_entries} valid entries", "details": details}


def _as_dict(result: Any) -> Dict[str, Any]:
    """Convert various result types to dictionary format."""
    if isinstance(result, dict):
        return result
    
    # Handle HACS result objects
    if hasattr(result, 'model_dump'):
        return result.model_dump()
    elif hasattr(result, '__dict__'):
        return {k: v for k, v in result.__dict__.items() if not k.startswith('_')}
    else:
        return {"result": str(result)}


# ===== HACS Tools via Integration =====

_TOOL_CACHE: list[Any] | None = None

def _get_hacs_tool_by_name(name: str):
    global _TOOL_CACHE
    if _TOOL_CACHE is None:
        try:
            _TOOL_CACHE = get_all_hacs_tools_sync(framework="langgraph")
        except Exception:
            _TOOL_CACHE = []
    for t in _TOOL_CACHE or []:
        tname = getattr(t, "name", None) or getattr(t, "__name__", None)
        if tname == name:
            return t
    return None

def _call_hacs_tool(name: str, **kwargs) -> Dict[str, Any]:
    tool = _get_hacs_tool_by_name(name)
    if tool is None:
        return {"success": False, "message": f"Tool '{name}' not found"}
    try:
        if hasattr(tool, "invoke"):
            return tool.invoke(kwargs)  # LangChain style
        if hasattr(tool, "run"):
            return tool.run(kwargs)
        func = getattr(tool, "function", None) or getattr(tool, "__call__", None) or tool
        return func(**kwargs)
    except Exception as e:
        return {"success": False, "message": str(e)}

# ===== Direct HACS Tool Tasks =====

@task
async def hacs_discover_resources() -> Dict[str, Any]:
    """Discover HACS resources using direct tool calls instead of MCP."""
    try:
        logger.info("Discovering HACS resources using direct tools")
        result = discover_hacs_resources(
            category_filter="clinical"
        )
        
        response = _as_dict(result)
        logger.info(f"Discovered {len(response.get('resources', []))} resources")
        return response
        
    except Exception as e:
        logger.error(f"Resource discovery failed: {e}")
        return {"success": False, "error": str(e), "resources": []}


@task
async def hacs_get_schema(resource_type: str) -> Dict[str, Any]:
    """Get resource schema using direct HACS tools."""
    try:
        logger.info(f"Getting schema for resource type: {resource_type}")
        result = get_hacs_resource_schema(
            resource_type=resource_type,
            include_examples=True,
            include_validation_rules=True
        )

        response = _as_dict(result)
        logger.info(f"Retrieved schema for {resource_type} with {response.get('field_count', 0)} fields")
        return response
        
    except Exception as e:
        logger.error(f"Schema retrieval failed for {resource_type}: {e}")
        return {"success": False, "error": str(e)}


@task
async def _build_and_register_template_via_llm(instruction_md: str, template_name: Optional[str]) -> Dict[str, Any]:
    """LLM-first template synthesis inside workflow (no dev-tool prompts)."""
    try:
        from hacs_utils.integrations.openai.client import OpenAIClient as _OpenAIClient
        from hacs_models import get_model_registry

        key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        if not key:
            return {"success": False, "message": "OPENAI_API_KEY not set for template synthesis"}

        client = _OpenAIClient(api_key=key, model=model)

        # Available HACS types
        try:
            reg = get_model_registry()
            available_types = sorted([name for name in reg.keys() if isinstance(name, str)])
        except Exception:
            available_types = []

        # LLM Call 1: select resource types with detailed HACS resource information
        resource_catalog = _generate_detailed_resource_catalog(available_types)
        
        sys1 = (
            "You are a clinical informatics assistant specializing in FHIR/HACS resource modeling. "
            "From the provided instruction TEMPLATE and the detailed catalog of available HACS resources, "
            "select the best set of resource types (max 12) to comprehensively model the clinical content. "
            "Consider the clinical context, relationships between resources, and FHIR best practices. "
            "Return strict JSON with detailed reasoning: "
            "{\n  \"resources\": [\n    {\"type\": \"Patient\", \"reason\": \"Contains patient demographics mentioned in template\", \"priority\": \"high\"}, ...\n  ]\n}"
        )
        user1 = (
            f"INSTRUCTION TEMPLATE (markdown):\n{instruction_md}\n\n"
            f"AVAILABLE HACS RESOURCES CATALOG:\n{resource_catalog}\n\n"
            f"SELECTION CRITERIA:\n"
            f"- Prioritize resources that directly map to template content\n"
            f"- Include foundational resources (Patient, Encounter) when appropriate\n"
            f"- Consider clinical workflows and resource relationships\n"
            f"- Ensure comprehensive coverage of all clinical domains mentioned\n"
            f"- Balance breadth with relevance to avoid over-engineering"
        )
        import re as _re, json as _json
        selected_types: list[str] = []
        try:
            r1 = client.chat([{"role": "system", "content": sys1}, {"role": "user", "content": user1}])
            raw = str(getattr(r1, "content", r1) or "").strip()
            logger.info(f"🤖 LLM Resource Selection Raw Response ({len(raw)} chars):\n{raw}")
            
            mj = _re.search(r"\{[\s\S]*\}$", raw)
            extracted_json = mj.group(0) if mj else raw
            logger.info(f"📊 Extracted JSON for parsing:\n{extracted_json}")
            
            data = _json.loads(extracted_json)
            logger.info(f"🎯 Parsed LLM Selection Data: {_json.dumps(data, indent=2)}")
            
            items = data.get("resources") if isinstance(data, dict) else None
            if isinstance(items, list):
                for it in items:
                    t = it.get("type") if isinstance(it, dict) else None
                    reason = it.get("reason", "No reason provided") if isinstance(it, dict) else "No reason provided"
                    if isinstance(t, str) and (not available_types or t in available_types):
                        selected_types.append(t)
                        logger.info(f"✅ Selected Resource: {t} - Reason: {reason}")
                    elif isinstance(t, str):
                        logger.warning(f"⚠️ Rejected Resource: {t} (not in available types) - Reason: {reason}")
        except Exception:
            pass
        if not selected_types:
            # Conservative defaults
            selected_types = ["ResourceBundle", "Patient", "Observation", "Condition", "Procedure", "MedicationRequest"]

        # Schema hints (optional) - include ALL HACS resources with pick() views
        # Use required fields + prioritized common fields to generate compact view schemas
        type_hints: dict[str, dict] = {}
        try:
            reg2 = get_model_registry()
            # Build hints for every available resource, not only selected
            all_types_for_hints = [name for name in reg2.keys() if isinstance(name, str)]
            prioritized = [
                "id", "status", "intent", "subject", "code", "code.text", "value", "value_string",
                "value_quantity", "description", "note", "effective_date_time", "issued", "category",
                "encounter", "performer", "reason_code", "medication_codeable_concept.text",
            ]
            MAX_FIELDS = 12
            for t in all_types_for_hints:
                cls = reg2.get(t)
                if not cls:
                    continue
                try:
                    sch = cls.model_json_schema()
                except Exception:
                    sch = {}
                props = list((sch.get("properties", {}) or {}).keys())
                req = list(sch.get("required", []) or [])
                # choose pick fields: required + prioritized available + fill up to MAX_FIELDS
                pick_fields: list[str] = []
                for f in req:
                    if f in props and f not in pick_fields:
                        pick_fields.append(f)
                for f in prioritized:
                    # handle nested fields hint by taking last segment if dot in name
                    base_f = f.split(".")[0]
                    if base_f in props and base_f not in pick_fields:
                        pick_fields.append(base_f)
                    if len(pick_fields) >= MAX_FIELDS:
                        break
                if len(pick_fields) < MAX_FIELDS:
                    for f in props:
                        if f not in pick_fields:
                            pick_fields.append(f)
                            if len(pick_fields) >= MAX_FIELDS:
                                break
                # Build view schema using pick() when available
                view_schema = {}
                try:
                    # Some classes may not implement pick; guard it
                    view_cls = getattr(cls, "pick", None)
                    if callable(view_cls) and pick_fields:
                        view_model = cls.pick(*pick_fields)
                        view_schema = view_model.model_json_schema().get("properties", {})
                    else:
                        # fallback to full schema properties (truncated)
                        view_schema = {k: (sch.get("properties", {}) or {}).get(k, {}) for k in pick_fields}
                except Exception:
                    view_schema = {k: (sch.get("properties", {}) or {}).get(k, {}) for k in pick_fields}

                type_hints[t] = {
                    "required": req[:MAX_FIELDS],
                    "view_fields": pick_fields,
                    "view_schema": view_schema,
                }
        except Exception:
            pass

        # LLM Call 2: produce StackTemplate JSON
        tpl_name = (template_name or "auto_template").strip() or "auto_template"
        sys2 = (
            "Produce a strict JSON HACS StackTemplate for the instruction TEMPLATE using the SELECTED_RESOURCES. "
            "The JSON MUST be:\n{\n  \"name\": \"...\",\n  \"version\": \"1.0.0\",\n  \"variables\": { varName: {type: \"string\"|... } },\n  \"layers\": [\n    {\"resource_type\": \"ResourceBundle\", \"layer_name\": \"document_bundle\", \"bindings\": {}, \"constant_fields\": {\"bundle_type\": \"document\", \"title\": \"...\"}},\n    {\"resource_type\": \"Patient\", \"layer_name\": \"patient\", \"bindings\": {...}, \"constant_fields\": {}},\n    ... more layers ...\n  ]\n}\n"
            "Rules: (1) Prefer Encounter as the parent when appropriate; alternatively choose another suitable parent such as MedicationRequest, Procedure or ServiceRequest. "
            "(2) Include at least 4 clinical layers when content permits (e.g., Encounter, Condition, Observation, Procedure, MedicationRequest, ServiceRequest, DiagnosticReport, DocumentReference). Avoid returning only ResourceBundle and Patient. "
            "(3) Include a Patient layer only if patient-identifying data appear in TEMPLATE; otherwise omit Patient. "
            "(4) Define variables covering all included layers; every variable must be used in at least one binding. Do not define unused variables. "
            "(5) Only include fields that are suggested by TEMPLATE; do not fabricate. "
            "(6) Ensure required fields for strict resources are supplied via bindings or constant_fields. "
            "(7) Keep ResourceBundle minimal (bundle_type/title only)."
        )
        examples = _generate_comprehensive_template_examples(type_hints)
        logger.info(f"Generated examples for template synthesis ({len(examples)} characters)")
        
        user2 = (
            f"TEMPLATE (markdown):\n{instruction_md}\n\n"
            f"SELECTED_RESOURCES:\n{', '.join(selected_types)}\n\n"
            f"SCHEMA_HINTS (per resource; include ALL HACS resources with compact pick() views):\n{_json.dumps(type_hints, ensure_ascii=False)}\n\n"
            f"{examples}"
        )
        variables: dict[str, Any] = {}
        layers: list[dict[str, Any]] = []
        try:
            logger.info(f"🤖 Sending Template Synthesis Request to LLM...")
            logger.info(f"📝 System Prompt ({len(sys2)} chars): {sys2[:200]}...")
            logger.info(f"📝 User Prompt ({len(user2)} chars): {user2[:500]}...")
            
            r2 = client.chat([{"role": "system", "content": sys2}, {"role": "user", "content": user2}])
            raw2 = str(getattr(r2, "content", r2) or "").strip()
            logger.info(f"🤖 LLM Template Synthesis Raw Response ({len(raw2)} chars):\n{raw2}")
            
            m2 = _re.search(r"\{[\s\S]*\}$", raw2)
            extracted_template_json = m2.group(0) if m2 else raw2
            logger.info(f"📊 Extracted Template JSON for parsing:\n{extracted_template_json}")
            
            data2 = _json.loads(extracted_template_json)
            logger.info(f"🎯 Parsed Template Structure: {_json.dumps(data2, indent=2)}")
            
            tpl_name = str(data2.get("name") or tpl_name)
            version = str(data2.get("version") or "1.0.0")
            variables = data2.get("variables") or {}
            layers = data2.get("layers") or []
            
            logger.info(f"📋 Template Analysis:")
            logger.info(f"  Name: {tpl_name}")
            logger.info(f"  Version: {version}")
            logger.info(f"  Variables Count: {len(variables)}")
            logger.info(f"  Variables: {list(variables.keys())}")
            logger.info(f"  Layers Count: {len(layers)}")
            
            try:
                layer_types = [l.get("resource_type") for l in layers if isinstance(l, dict)]
                logger.info(f"  Layer Types: {layer_types}")
                for i, layer in enumerate(layers):
                    if isinstance(layer, dict):
                        layer_name = layer.get("layer_name", f"layer_{i}")
                        resource_type = layer.get("resource_type", "Unknown")
                        bindings = layer.get("bindings", {})
                        constants = layer.get("constant_fields", {})
                        logger.info(f"    Layer {i+1}: {resource_type} ({layer_name}) - {len(bindings)} bindings, {len(constants)} constants")
            except Exception as e:
                logger.warning(f"Failed to analyze layers: {e}")
            # Retry once if too few clinical layers (excluding ResourceBundle)
            non_bundle = [l for l in layers if isinstance(l, dict) and l.get("resource_type") != "ResourceBundle"]
            if len(non_bundle) < 2:
                sys2_retry = sys2 + " You MUST include at least 4 clinical layers (excluding ResourceBundle) when content permits; avoid minimal outputs."
                r2b = client.chat([{"role": "system", "content": sys2_retry}, {"role": "user", "content": user2}])
                raw2b = str(getattr(r2b, "content", r2b) or "").strip()
                m2b = _re.search(r"\{[\s\S]*\}$", raw2b)
                data2b = _json.loads(m2b.group(0) if m2b else raw2b)
                layers_b = data2b.get("layers") or []
                non_bundle_b = [l for l in layers_b if isinstance(l, dict) and l.get("resource_type") != "ResourceBundle"]
                if len(non_bundle_b) > len(non_bundle):
                    variables = data2b.get("variables") or variables
                    layers = layers_b
        except Exception as e:
            logger.warning(f"LLM template synthesis failed, using fallback: {e}")
            version = "1.0.0"
            variables = {
                "patient_name": {"type": "string"},
                "clinical_note": {"type": "string"}
            }
            layers = [
                {"resource_type": "ResourceBundle", "layer_name": "document_bundle", "bindings": {}, "constant_fields": {"bundle_type": "document", "title": tpl_name[:200]}},
                {"resource_type": "Patient", "layer_name": "patient", "bindings": {"full_name": "{{ patient_name }}"}, "constant_fields": {}},
                {"resource_type": "Observation", "layer_name": "clinical_note", "bindings": {"value_string": "{{ clinical_note }}"}, "constant_fields": {"status": "final", "code": {"text": "Clinical Note"}}}
            ]

        # Register template via tool dispatcher (prefer explicit tool names)
        template_payload = {
            "name": tpl_name,
            "version": version,
            "variables": variables,
            "layers": layers,
            "description": "LLM-generated template from instruction markdown",
        }
        
        logger.info(f"🔧 Template Registration Payload:")
        logger.info(f"📋 Final Template Structure: {_json.dumps(template_payload, indent=2)}")
        
        # Try known tool names in order of preference
        reg_try_order = [
            "generate_stack_template_from_markdown",
            "register_stack_template_tool",
            "register_stack_template",
        ]
        resp = {"success": False}
        for tool_name in reg_try_order:
            logger.info(f"🔧 Attempting template registration with tool: {tool_name}")
            reg_res = _call_hacs_tool(tool_name, template=template_payload)
            resp = _as_dict(reg_res)
            logger.info(f"🔧 Tool '{tool_name}' response: {resp}")
            if resp.get("success", False):
                logger.info(f"✅ Template successfully registered with tool: {tool_name}")
                break
            else:
                logger.warning(f"⚠️ Tool '{tool_name}' failed: {resp.get('message', 'Unknown error')}")
        # Final fallback: direct import if dispatcher did not find a tool
        if not resp.get("success", False):
            try:
                from hacs_tools.domains.development_tools import generate_stack_template_from_markdown_tool as _gen_tpl
                dr = _gen_tpl(template=template_payload)
                resp = _as_dict(dr)
            except Exception:
                try:
                    from hacs_tools.domains.development_tools import register_stack_template_tool as _reg_tpl
                    dr = _reg_tpl(template=template_payload)
                    resp = _as_dict(dr)
                except Exception as _e:
                    resp = {"success": False, "message": str(_e)}
        if not resp.get("success", False):
            return {"success": False, "message": resp.get("message", "registration failed")}
        return {
            "success": True,
            "template_name": tpl_name,
            "data": {"variables": variables, "layers": layers},
            "message": f"Template '{tpl_name}' registered"
        }
    except Exception as e:
        logger.error(f"Template synthesis failed: {e}")
        return {"success": False, "error": str(e)}


@task
async def _extract_variables_and_instantiate(template_name: str, context_text: str, use_llm: bool = False) -> Dict[str, Any]:
    """LLM-first variable extraction and instantiation inside workflow."""
    try:
        from hacs_registry import get_global_registry, instantiate_registered_stack
        variables: dict[str, Any] = {}

        # Resolve template variables schema
        registry = get_global_registry()
        candidates = [r for r in registry._resources.values() if getattr(r, 'metadata', None) and r.metadata.name == template_name]
        if not candidates:
            return {"success": False, "message": f"Template not found: {template_name}"}
        tpl_res = sorted(candidates, key=lambda r: r.metadata.version, reverse=True)[0]
        tpl = getattr(tpl_res, 'resource_instance', None) or {}
        tpl_vars = (tpl.get('variables', {}) if isinstance(tpl, dict) else getattr(tpl, 'variables', {}) or {})
        variable_names = list(tpl_vars.keys())
        variables = {k: context_text for k in variable_names}

        # Optional LLM extraction via generic Extraction interface with chunking + grounding
        grounded_extractions: list[dict] = []
        if use_llm and variable_names:
            try:
                from hacs_utils.integrations.openai.client import OpenAIClient as _OpenAIClient
                key = os.getenv("OPENAI_API_KEY")
                model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                if key:
                    client = _OpenAIClient(api_key=key, model=model)

                    max_char_buffer = int(os.getenv("HACS_EXTRACT_MAX_CHARS", "4000"))
                    chunk_overlap = int(os.getenv("HACS_EXTRACT_CHUNK_OVERLAP", "0"))
                    batch_length = int(os.getenv("HACS_EXTRACT_BATCH", "4"))

                    doc = HDocument(text=context_text)
                    chunks = ChunkIterator(doc, max_char_buffer=max_char_buffer, chunk_overlap=chunk_overlap)
                    batches = make_batches_of_textchunk(iter(chunks), batch_length)

                    remaining = set(variable_names)
                    for batch in batches:
                        if not remaining:
                            break
                        for ch in batch:
                            if not remaining:
                                break
                            # Get template context for more informed extraction
                            template_context = _get_template_extraction_context(template_name, tpl_vars, remaining)
                            
                            system_msg = (
                                "You are a clinical extraction assistant specializing in FHIR/HACS resource data extraction. "
                                "Extract precise clinical values needed to populate the template's variables. "
                                "Focus on clinical accuracy, data precision, and appropriate medical terminology. "
                                "Return a JSON array of {extraction_class, extraction_text} objects. "
                                "extraction_class MUST exactly match one of the provided variable names."
                            )
                            variable_list = "\n".join([f"- {var}: Extract relevant clinical data for this field" for var in sorted(remaining)])
                            user_msg = (
                                f"TEMPLATE CONTEXT:\n{template_context}\n\n"
                                f"VARIABLES TO EXTRACT:\n{variable_list}\n\n"
                                f"CLINICAL CONTEXT TO ANALYZE:\n{ch.chunk_text}\n\n"
                                f"EXTRACTION REQUIREMENTS:\n"
                                f"- Extract only factual information present in the context\n"
                                f"- Maintain clinical terminology and precision\n"
                                f"- Use appropriate medical units and formats\n"
                                f"- Do not infer or fabricate information not explicitly stated\n\n"
                                f'Respond with JSON array: [{{"extraction_class": "variable_name", "extraction_text": "extracted_value"}}]'
                            )
                            logger.info(f"🤖 Sending Variable Extraction Request for chunk {ch.start_index}-{ch.end_index}...")
                            logger.info(f"📝 System Message: {system_msg[:200]}...")
                            logger.info(f"📝 User Message ({len(user_msg)} chars): {user_msg[:300]}...")
                            
                            extrs = generate_extractions(
                                client,
                                messages=[
                                    {"role": "system", "content": system_msg},
                                    {"role": "user", "content": user_msg},
                                ],
                                provider="openai",
                                max_tokens=1500,
                            )
                            
                            logger.info(f"🎯 Extraction Results for chunk: {len(extrs)} extractions found")
                            for i, ex in enumerate(extrs):
                                logger.info(f"  Extraction {i+1}: class='{ex.extraction_class}', text='{ex.extraction_text[:100]}{'...' if len(str(ex.extraction_text)) > 100 else ''}'")
                            
                            hay_low = ch.chunk_text.lower()
                            for ex in extrs:
                                cls = (ex.extraction_class or "").strip()
                                txt = ex.extraction_text if isinstance(ex.extraction_text, str) else ""
                                if cls in remaining and txt:
                                    variables[cls] = txt
                                    remaining.discard(cls)
                                start_local = hay_low.find((txt or "").lower()) if txt else -1
                                if start_local >= 0:
                                    ci = HCharInterval(start_pos=ch.start_index + start_local, end_pos=ch.start_index + start_local + len(txt))
                                    status = HAlignmentStatus.MATCH_EXACT
                                else:
                                    ci = None
                                    status = HAlignmentStatus.MATCH_FUZZY
                                grounded_extractions.append({
                                    "extraction_class": cls,
                                    "extraction_text": txt,
                                    "char_interval": {"start_pos": getattr(ci, "start_pos", None), "end_pos": getattr(ci, "end_pos", None)} if ci else None,
                                    "alignment_status": getattr(status, "value", None),
                                })
            except Exception:
                grounded_extractions = []

        # Instantiate resources and build detailed ResourceBundle
        logger.info(f"🏗️ Instantiating stack template: {template_name}")
        import json as _json2
        logger.info(f"📋 Variables for instantiation: {_json2.dumps(variables, indent=2)}")
        
        # Use tools path for instantiation
        tool_res = _call_hacs_tool("instantiate_stack_from_context", template_name=template_name, variables=variables)
        logger.info(f"🔧 Tool instantiation response: {tool_res}")
        
        if tool_res.get("success") and isinstance(tool_res.get("data"), dict):
            logger.info("✅ Tool instantiation successful, using registry fallback for persistence")
            # Fallback to registry objects for persistence below
            resources = instantiate_registered_stack(template_name, variables)
        else:
            logger.info("⚠️ Tool instantiation failed, using direct registry instantiation")
            resources = instantiate_registered_stack(template_name, variables)
            
        logger.info(f"🏗️ Instantiated Resources ({len(resources)} total):")
        for layer_name, resource in resources.items():
            resource_type = getattr(resource, "resource_type", "Unknown")
            resource_id = getattr(resource, "id", "No ID")
            logger.info(f"  {layer_name}: {resource_type} (ID: {resource_id})")
        
        # Create detailed ResourceBundle with all layers as entries
        bundle = None
        individual_resources = {}
        
        logger.info(f"Processing {len(resources)} instantiated resources: {list(resources.keys())}")
        
        for layer_name, resource in resources.items():
            resource_type = getattr(resource, "resource_type", None)
            logger.info(f"Layer '{layer_name}': {resource_type}")
            
            if resource_type == "ResourceBundle":
                # Use the first ResourceBundle as our main bundle
                if bundle is None:
                    bundle = resource
                    logger.info(f"Using existing ResourceBundle from layer '{layer_name}'")
            else:
                # Store individual resources to add as entries
                individual_resources[layer_name] = resource
        
        logger.info(f"Found {len(individual_resources)} individual resources to add to bundle: {list(individual_resources.keys())}")
        
        # If no ResourceBundle was created, create one
        if bundle is None:
            from hacs_models import ResourceBundle
            bundle = ResourceBundle(
                title=f"Generated Bundle from {template_name}",
                bundle_type="document"
            )
        
        # Add all individual resources as entries using .add_entry()
        logger.info(f"📦 Building ResourceBundle with {len(individual_resources)} entries:")
        for layer_name, resource in individual_resources.items():
            resource_type = getattr(resource, "resource_type", "Unknown")
            resource_id = getattr(resource, "id", "No ID")
            logger.info(f"  Adding: {resource_type} ({resource_id}) from layer '{layer_name}'")
            
            # Show some field details for verification
            if hasattr(resource, 'model_dump'):
                resource_data = resource.model_dump()
                non_empty_fields = {k: v for k, v in resource_data.items() if v is not None and v != "" and v != []}
                logger.info(f"    Non-empty fields ({len(non_empty_fields)}): {list(non_empty_fields.keys())}")
            
            bundle.add_entry(
                resource=resource,
                title=f"{resource_type} - {layer_name}",
                tags=[resource_type.lower(), layer_name],
                priority=1 if resource_type == "Patient" else 0  # Prioritize Patient entries
            )
            logger.info(f"    ✅ Entry added. Bundle now has {len(bundle.entries)} entries")
        
        # Update resources dict to include the detailed bundle
        resources["document_bundle"] = bundle
        
        # Validate bundle is properly created
        bundle_validation = _validate_bundle_creation(bundle)
        logger.info(f"Bundle validation: {bundle_validation['status']} - {bundle_validation['message']}")
        
        return {
            "success": True,
            "variables": variables,
            "stack": {k: getattr(v, "resource_type", None) for k, v in resources.items()},
            "bundle_entries": len(bundle.entries) if bundle else 0,
            "bundle_validation": bundle_validation,
            "grounded_extractions": grounded_extractions if use_llm and variable_names else [],
        }
    except Exception as e:
        logger.error(f"Variable extraction/instantiation failed: {e}")
        return {"success": False, "error": str(e)}


# ===== LLM-assisted resource selection =====

def _get_openai_client():
    try:
        from hacs_utils.integrations.openai.client import OpenAIClient as _OpenAIClient
    except Exception:
        return None
    key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    if not key:
        return None
    try:
        return _OpenAIClient(api_key=key, model=model)
    except Exception:
        return None


def _llm_rank_resources(instruction_md: str, candidates: list[str], top_k: int = 8) -> list[str]:
    """Use an LLM to rank/select the best HACS resource types for a given instruction template."""
    client = _get_openai_client()
    if client is None:
        # Reasonable default ordering emphasizing common clinical types
        preferred = [
            "Patient", "Encounter", "Observation", "Condition", "ServiceRequest",
            "Procedure", "MedicationRequest", "Goal", "DiagnosticReport", "Organization", "Practitioner"
        ]
        ranked = [r for r in preferred if r in candidates] + [r for r in candidates if r not in preferred]
        return ranked[:top_k]

    # Generate detailed resource information for better LLM decision making
    candidate_details = _generate_detailed_resource_catalog(candidates)
    
    system = (
        "You are a clinical informatics assistant specializing in FHIR/HACS resource modeling. "
        "Given a markdown instruction template and detailed information about available HACS resources, "
        "rank the most appropriate resource types to comprehensively model the clinical content. "
        "Consider clinical workflows, resource relationships, and FHIR best practices. "
        "Return a JSON with a 'resources' array in priority order with reasoning."
    )
    user = (
        f"INSTRUCTION TEMPLATE:\n{instruction_md}\n\n"
        f"DETAILED RESOURCE CATALOG:\n{candidate_details}\n\n"
        f"RANKING CRITERIA:\n"
        f"- Relevance to template content and clinical context\n"
        f"- FHIR compliance and healthcare standards alignment\n"
        f"- Resource relationships and dependencies\n"
        f"- Clinical workflow completeness\n"
        f"- Data modeling best practices\n\n"
        f"Respond with JSON: {{\"resources\": [\"ResourceType1\", \"ResourceType2\", ...], \"reasoning\": \"Brief explanation\"}}"
    )
    try:
        logger.info(f"🤖 Sending Resource Ranking Request to LLM...")
        logger.info(f"📝 System prompt: {system[:200]}...")
        logger.info(f"📝 User prompt: {user[:300]}...")
        
        resp = client.chat([
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ])
        
        raw_response = getattr(resp, "content", "{}")
        logger.info(f"🤖 LLM Resource Ranking Raw Response: {raw_response}")
        
        import json as _json
        parsed = _json.loads(raw_response)
        logger.info(f"🎯 Parsed Ranking Data: {_json.dumps(parsed, indent=2)}")
        
        resources = parsed.get("resources")
        reasoning = parsed.get("reasoning", "")
        
        if reasoning:
            logger.info(f"💭 LLM resource ranking reasoning: {reasoning}")
        
        if isinstance(resources, list) and all(isinstance(r, str) for r in resources):
            # Filter to candidates and cap
            filtered = [r for r in resources if r in candidates]
            if filtered:
                logger.info(f"✅ LLM ranked resources: {filtered[:top_k]}")
                return filtered[:top_k]
            else:
                logger.warning(f"⚠️ No valid resources found in LLM response")
    except Exception:
        pass
    return candidates[:top_k]


# ===== Persistence Task =====

@task
async def _persist_stack(database_url: str, stack: Dict[str, Any]) -> Dict[str, Any]:
    """Persist stack resources to database."""
    persisted = {}
    
    try:
        adapter = PostgreSQLAdapter(database_url)
        actor = Actor(id="hf-ingestion", name="HF Ingestion Workflow", role="system")
        
        logger.info(f"Persisting stack with {len(stack)} resources to database")
        await adapter.connect()
        logger.info(f"💾 Starting persistence of {len(stack)} resources to database...")
        
        for layer_name, resource in stack.items():
            try:
                resource_type = getattr(resource, "resource_type", type(resource).__name__)
                resource_id = getattr(resource, "id", "No ID")
                logger.info(f"💾 Saving {resource_type} ({resource_id}) from layer '{layer_name}'...")
                
                # Show resource summary before saving
                if hasattr(resource, 'model_dump'):
                    resource_data = resource.model_dump()
                    non_empty_fields = {k: v for k, v in resource_data.items() if v is not None and v != "" and v != []}
                    logger.info(f"    Resource fields ({len(non_empty_fields)}): {list(non_empty_fields.keys())}")
                
                saved_resource = await adapter.save(resource, actor)
                persisted[layer_name] = {
                    "id": saved_resource.id,
                    "resource_type": getattr(saved_resource, "resource_type", type(saved_resource).__name__),
                    "status": "saved"
                }
                logger.info(f"    ✅ Saved successfully with ID: {saved_resource.id}")
                
            except Exception as e:
                persisted[layer_name] = {
                    "status": "error",
                    "error": str(e)
                }
                logger.error(f"    ❌ Failed to save {layer_name}: {e}")
                import traceback
                logger.error(f"    Stack trace: {traceback.format_exc()}")
        try:
            await adapter.disconnect()
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Database persistence setup failed: {e}")
        return {"error": str(e), "persisted": persisted}
    
    successful_saves = sum(1 for p in persisted.values() if p.get("status") == "saved")
    logger.info(f"Persistence completed: {successful_saves}/{len(stack)} resources saved")
    
    return persisted


# ===== Main Workflows =====

@entrypoint(checkpointer=InMemorySaver())
async def register_template_from_instruction(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Register a template from instruction using direct HACS tools.
    
    Inputs: { instruction_md: str, template_name?: str, fetch_schemas_for?: list[str] }
    Returns: { template_name, template_schema, discovered_resources, schemas_by_type }
    """
    instruction_md: str = inputs.get("instruction_md", "")
    template_name: Optional[str] = inputs.get("template_name")
    # Default discovery is now dynamic via schema discovery; keep a broad preferred list as a hint
    default_types: List[str] = [
        "Patient", "Encounter", "Observation", "Condition", "Procedure",
        "MedicationRequest", "Medication", "MedicationStatement", "AllergyIntolerance",
        "DiagnosticReport", "DocumentReference", "Immunization", "ServiceRequest",
        "Goal", "FamilyMemberHistory", "Organization", "Practitioner",
        "Appointment", "CarePlan", "CareTeam", "NutritionOrder", "PlanDefinition",
    ]
    types_to_fetch: List[str] = inputs.get("fetch_schemas_for", default_types)
    
    logger.info(f"Starting template registration for: {template_name}")
    
    # Step 1: Discover available resources
    discovered = await hacs_discover_resources()

    # Optional: LLM-assisted resource selection to prioritize schemas and guide downstream steps
    use_llm_selection: bool = bool(inputs.get("use_llm_selection", True))
    if instruction_md and discovered.get("resources") and use_llm_selection:
        candidate_types = [r.get("resource_type") or r.get("name") for r in discovered["resources"]]
        candidate_types = [c for c in candidate_types if isinstance(c, str)]
        ranked = _llm_rank_resources(instruction_md, candidate_types, top_k=10)
        # Keep original order fallback but prefer ranked
        types_to_fetch = [r for r in ranked if r in types_to_fetch] + [r for r in types_to_fetch if r not in ranked]

    # Step 2: Generate template from markdown (drive LLM to include any discovered resource via free-text anchors)
    gen_res = await _build_and_register_template_via_llm(instruction_md, template_name)
    
    # Step 3: Fetch schemas for requested resource types (use discovered names to widen coverage)
    schemas_by_type: Dict[str, Any] = {}
    # Merge discovered resource types if available
    discovered_types = [r.get("resource_type") or r.get("name") for r in discovered.get("resources", [])]
    discovered_types = [t for t in discovered_types if isinstance(t, str)]
    all_types = list(dict.fromkeys(types_to_fetch + discovered_types))[:50]
    for resource_type in all_types:
        try:
            schema_result = await hacs_get_schema(resource_type)
            if schema_result.get("success", False):
                schemas_by_type[resource_type] = schema_result
            else:
                logger.warning(f"Failed to get schema for {resource_type}: {schema_result.get('message')}")
        except Exception as e:
            logger.error(f"Exception getting schema for {resource_type}: {e}")
    
    # Compile final result
    result = {
        "template_name": gen_res.get("template_name"),
        "template_schema": gen_res.get("data", {}),
        "discovered_resources": discovered.get("resources", []),
        "schemas_by_type": schemas_by_type,
        "success": gen_res.get("success", False),
        "message": gen_res.get("message", "Template registration completed")
    }
    
    if result["success"]:
        logger.info(f"Successfully registered template: {result['template_name']}")
    else:
        logger.error(f"Template registration failed: {result['message']}")
    
    return result


@entrypoint(checkpointer=InMemorySaver())
async def instantiate_and_persist_stack(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Instantiate and persist stack using direct HACS tools.
    
    Inputs: { template_name: str, context_text: str, database_url?: str, use_llm?: bool }
    Returns: { persisted: dict, layers: list, stack_preview: dict }
    """
    template_name: str = inputs["template_name"]
    context_text: str = inputs.get("context_text", "")
    database_url: str = inputs.get(
        "database_url", os.getenv("DATABASE_URL", "postgresql://hacs:hacs_dev@localhost:5432/hacs")
    )
    use_llm: bool = bool(inputs.get("use_llm", False))
    
    logger.info(f"Starting stack instantiation for template: {template_name}")
    
    # Step 1: Instantiate stack from context using HACS tools
    hacs_result = await _extract_variables_and_instantiate(template_name, context_text, use_llm)
    
    # Step 2: Get actual resource objects from registry for persistence
    registry = get_global_registry()
    candidates = [r for r in registry._resources.values() if r.metadata.name == template_name]
    
    if not candidates:
        error_msg = f"Template not found in registry: {template_name}"
        logger.error(error_msg)
        return {
            "error": error_msg,
            "hacs_result": hacs_result,
            "persisted": {},
            "layers": [],
            "stack_preview": {}
        }
    
    # Get the latest version of the template
    tpl_res = sorted(candidates, key=lambda r: r.metadata.version, reverse=True)[0]
    instance = getattr(tpl_res, "resource_instance", {}) or {}
    variables_keys = list(instance.get("variables", {}).keys())
    
    # Fill variables with context (simplified approach)
    variables = {k: context_text for k in variables_keys}
    
    try:
        # Step 3: Instantiate the registered stack template
        stack = instantiate_registered_stack(template_name, variables)
        logger.info(f"Successfully instantiated stack with {len(stack)} resources")
        
        # Step 4: Persist to database
        persisted = await _persist_stack(database_url, stack)
        
        # Compile result
        result = {
            "persisted": persisted,
            "layers": hacs_result.get("layers", []),
            "stack_preview": {k: getattr(v, "resource_type", None) for k, v in stack.items()},
            "hacs_result": hacs_result,
            "success": True,
            "message": f"Stack instantiated and persisted successfully"
        }
        
        logger.info(f"Workflow completed successfully for template: {template_name}")
        return result
        
    except Exception as e:
        error_msg = f"Stack instantiation failed: {e}"
        logger.error(error_msg)
        return {
            "error": error_msg,
            "hacs_result": hacs_result,
            "persisted": {},
            "layers": [],
            "stack_preview": {},
            "success": False,
            "message": error_msg
        }


# ===== Utility Functions =====

def validate_hacs_tools_availability() -> Dict[str, bool]:
    """Validate that all required HACS tools are available."""
    tools_status = {}
    
    try:
        # Test resource discovery directly
        from hacs_tools.domains.schema_discovery import discover_hacs_resources as direct_discover
        result = direct_discover(category_filter="clinical")
        tools_status["discover_resources"] = getattr(result, "success", False)
    except Exception as e:
        logger.error(f"discover_resources test failed: {e}")
        tools_status["discover_resources"] = False
    
    try:
        # Test schema retrieval directly
        from hacs_tools.domains.schema_discovery import get_hacs_resource_schema as direct_schema
        result = direct_schema("Patient")
        tools_status["get_schema"] = getattr(result, "success", False)
    except Exception as e:
        logger.error(f"get_schema test failed: {e}")
        tools_status["get_schema"] = False
    
    try:
        # Test template generation directly
        from hacs_tools.domains.development_tools import generate_stack_template_from_markdown_tool as direct_generate
        payload = {
            "name": "devtools_validation_template",
            "version": "1.0.0",
            "variables": {},
            "layers": [
                {"resource_type": "ResourceBundle", "layer_name": "document_bundle", "bindings": {}, "constant_fields": {"bundle_type": "document", "title": "validation"}},
                {"resource_type": "Patient", "layer_name": "patient", "bindings": {}, "constant_fields": {}},
            ],
            "description": "Validation template",
        }
        result = direct_generate(template=payload)
        tools_status["generate_template"] = bool(getattr(result, "success", False))
    except Exception as e:
        logger.error(f"generate_template test failed: {e}")
        tools_status["generate_template"] = False
    
    return tools_status


# Export main entrypoints
__all__ = [
    "register_template_from_instruction",
    "instantiate_and_persist_stack", 
    "validate_hacs_tools_availability",
    "universal_extract",
]


# ===== Universal Extraction Entry =====

def _normalize_sources_to_text(sources: list[Any]) -> str:
    parts: list[str] = []
    for item in sources or []:
        try:
            if item is None:
                continue
            if isinstance(item, str):
                parts.append(item)
            elif hasattr(item, "model_dump_json"):
                parts.append(item.model_dump_json())  # pydantic models
            elif hasattr(item, "model_dump"):
                import json as _json
                parts.append(_json.dumps(item.model_dump(), ensure_ascii=False))
            elif isinstance(item, dict):
                import json as _json
                parts.append(_json.dumps(item, ensure_ascii=False))
            else:
                parts.append(str(item))
        except Exception:
            try:
                parts.append(str(item))
            except Exception:
                continue
    return "\n\n".join(parts)


@entrypoint(checkpointer=InMemorySaver())
async def universal_extract(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Universal extraction: build a template and/or instantiate stacks from mixed sources.

    Inputs:
      - sources: list[str|dict|pydantic] arbitrary inputs (markdown, HACS records, JSON)
      - mode: "template" | "instantiate" | "both" (default: "both")
      - template_name?: desired template name
      - database_url?: optional persistence target
      - persist?: bool (default False)
      - use_llm?: bool (default True)

    Returns a dict with keys present depending on mode: { template_name, template_schema, variables, stack, persisted }
    """
    sources: list[Any] = inputs.get("sources", [])
    mode: str = str(inputs.get("mode", "both")).lower()
    template_name: Optional[str] = inputs.get("template_name")
    database_url: Optional[str] = inputs.get("database_url")
    persist: bool = bool(inputs.get("persist", False))
    use_llm: bool = bool(inputs.get("use_llm", True))

    combined_text = _normalize_sources_to_text(sources)

    result: Dict[str, Any] = {"success": True}

    # Build/register template if requested
    if mode in ("template", "both"):
        tpl_res = await _build_and_register_template_via_llm(combined_text, template_name)
        result["template_result"] = tpl_res
        template_name = tpl_res.get("template_name") or template_name

    # Instantiate if requested and a template is known
    if mode in ("instantiate", "both") and template_name:
        inst = await _extract_variables_and_instantiate(template_name, combined_text, use_llm)
        result["instantiation_result"] = inst

        if persist and database_url and inst.get("success"):
            # Persist using existing persistence task
            try:
                from hacs_registry import get_global_registry, instantiate_registered_stack
                registry = get_global_registry()
                candidates = [r for r in registry._resources.values() if getattr(r, 'metadata', None) and r.metadata.name == template_name]
                if candidates:
                    tpl_res = sorted(candidates, key=lambda r: r.metadata.version, reverse=True)[0]
                    instance_vars = inst.get("variables", {})
                    stack_objs = instantiate_registered_stack(template_name, instance_vars)
                    persisted = await _persist_stack(database_url, stack_objs)
                    result["persisted"] = persisted
            except Exception as e:
                result["persist_error"] = str(e)

    return result
