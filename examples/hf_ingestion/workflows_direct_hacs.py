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

# Composition + ResourceBundle + MappingSpec path (StackTemplate deprecated)
from hacs_registry import get_global_registry
from hacs_models import (
    MappingSpec,
    OutputSpec,
    SourceBinding,
    AnnotationWorkflowResource,
    Document as HACSDocument,
    ResourceBundle as HACSResourceBundle,
    get_model_registry,
)
from hacs_models.utils import set_nested_field
from hacs_registry import (
    register_prompt_template,
    register_extraction_schema,
    register_annotation_workflow,
)
from hacs_persistence.adapter import PostgreSQLAdapter
from hacs_core import Actor

"""
Direct HACS tool imports - no MCP dependency. Use schema discovery for model descriptions
and thin modeling/bundle/persistence tools for resource operations.
"""
from hacs_tools.domains.schema_discovery import (
    discover_hacs_resources,
    get_hacs_resource_schema,
)
from hacs_tools.domains.modeling_tools import (
    instantiate_hacs_resource,
    validate_hacs_resource,
)
from hacs_tools.domains.bundle_tools import (
    create_resource_bundle,
    add_bundle_entry,
    validate_resource_bundle,
)
from hacs_tools.domains.persistence_tools import (
    persist_hacs_resource,
)
from hacs_utils.annotation.chunking import ChunkIterator, make_batches_of_textchunk
from hacs_utils.annotation.data import (
    CharInterval as HCharInterval,
    AlignmentStatus as HAlignmentStatus,
    Document as HDocument,
)
from hacs_utils.structured import generate_extractions
from hacs_registry import (
    register_prompt_template,
    register_extraction_schema,
    register_annotation_workflow,
)
# Optional: tool loader (used by _get_hacs_tool_by_name fallback)
# removed: tool loader helpers (unused)

logger = logging.getLogger(__name__)


def _build_type_hints_from_registry_schemas(available_types: list[str]) -> dict:
    """Build compact type hints using schema discovery (registry-backed)."""
    hints: dict[str, dict] = {}
    # Limit to a reasonable number to keep prompts short
    for t in available_types[:20]:
        try:
            sch = asyncio.run(hacs_get_schema.ainvoke({"resource_type": t})) if hasattr(hacs_get_schema, "ainvoke") else None
        except Exception:
            sch = None
        if isinstance(sch, dict) and sch.get("success"):
            hints[t] = {
                "clinical_context": sch.get("clinical_context", ""),
                "required": sch.get("required_fields", []),
            }
    return hints


def _build_default_mapping_spec() -> MappingSpec:
    """Return a conservative MappingSpec using Composition Document + Patient.

    Variables expected: document_title, patient_name, clinical_note
    """
    return MappingSpec(
        outputs=[
            OutputSpec(
                resource="Document",
                operation="create",
                fields={
                    "title": SourceBinding(var="document_title"),
                    "subject_name": SourceBinding(var="patient_name"),
                },
            ),
            OutputSpec(
                resource="Patient",
                operation="create",
                fields={
                    "full_name": SourceBinding(var="patient_name"),
                },
            ),
        ]
    )


def _register_annotation_workflow(
    name: str,
    mapping_spec: MappingSpec,
    instruction_md: str,
) -> dict:
    """Create and register prompt/extraction schema + annotation workflow.

    Returns registry result dict including template_name and mapping summary.
    """
    # Build minimal, real prompt and response schema based on mapping variables
    variable_names: list[str] = []
    for out in mapping_spec.outputs:
        for b in out.fields.values():
            if isinstance(b, SourceBinding) and b.var and b.var not in variable_names:
                variable_names.append(b.var)

    prompt_text = (
        "You will extract strictly the following variables from the given clinical context.\n"
        "Return a JSON object with only these keys.\n\n"
        f"Variables: {', '.join(variable_names)}\n\n"
        "Context:\n{context}\n"
    )
    prompt_res = register_prompt_template(
        name=f"{name}-prompt",
        template_text=prompt_text,
        version="1.0.0",
        variables=["context"],
        format="json",
        fenced_output=True,
    )

    # Build JSON Schema with variables as string properties
    schema_props = {vn: {"type": "string"} for vn in variable_names}
    response_schema = {"type": "object", "properties": schema_props, "required": variable_names}
    schema_res = register_extraction_schema(
        name=f"{name}-schema",
        response_schema=response_schema,
        version="1.0.0",
    )

    workflow = AnnotationWorkflowResource(
        name=name,
        version="1.0.0",
        prompt_template_ref=f"{prompt_res.metadata.name}:{prompt_res.metadata.version}",
        extraction_schema_ref=f"{schema_res.metadata.name}:{schema_res.metadata.version}",
        mapping_spec=mapping_spec,
    )
    reg_res = register_annotation_workflow(workflow)
    return {
        "success": True,
        "template_name": name,
        "data": {
            "mapping_spec": workflow.mapping_spec.model_dump(),
            "variables": variable_names,
        },
        "message": f"AnnotationWorkflow '{name}' registered",
        "registry_id": getattr(reg_res, "registry_id", None),
    }


def _instantiate_from_mapping(mapping: MappingSpec, variables: dict[str, Any]) -> dict[str, Any]:
    """Instantiate resources defined by MappingSpec using provided variables.

    Returns dict of layer_name -> resource objects, plus a 'document_bundle' ResourceBundle.
    """
    resources: dict[str, Any] = {}
    model_registry = get_model_registry()

    # Create resources per output spec
    for idx, out in enumerate(mapping.outputs):
        resource_name = out.resource
        if not isinstance(resource_name, str):
            continue
        model_cls = model_registry.get(resource_name)
        if model_cls is None:
            continue
        data: dict[str, Any] = {}
        for path, binding in (out.fields or {}).items():
            if isinstance(binding, SourceBinding):
                if binding.var is not None and binding.var in variables:
                    value = variables[binding.var]
                elif binding.from_ is not None:
                    # Not implemented: JSONPath-like extraction; skip for now
                    continue
                else:
                    continue
                # Assign nested value into data
                set_nested_field(data, path, value)
        try:
            instance = model_cls(**data)
        except Exception:
            # Skip invalid instance
            continue
        layer_key = f"{resource_name.lower()}_{idx}"
        resources[layer_key] = instance

    # Build ResourceBundle and add entries for created resources
    bundle = HACSResourceBundle(title=f"Generated Bundle", bundle_type="document")
    for layer_name, resource in resources.items():
        try:
            bundle.add_entry(
                resource=resource,
                title=f"{getattr(resource, 'resource_type', type(resource).__name__)} - {layer_name}",
                tags=[getattr(resource, 'resource_type', type(resource).__name__).lower(), layer_name],
                priority=1 if getattr(resource, 'resource_type', None) == 'Patient' else 0,
            )
        except Exception:
            continue
    resources["document_bundle"] = bundle
    return resources


def _resource_type_hints_markdown(available_types: list[str]) -> str:
    """Produce a compact markdown of resource types with clinical context from registry-backed schemas."""
    if not available_types:
        return "No HACS resources available."
    lines = ["=== HACS RESOURCES (from registry) ===\n"]
    # Try to fetch clinical_context via schema discovery
    for t in available_types[:20]:
        try:
            sch = asyncio.run(hacs_get_schema.ainvoke({"resource_type": t})) if hasattr(hacs_get_schema, "ainvoke") else None
        except Exception:
            sch = None
        ctx = ""
        req = []
        if isinstance(sch, dict) and sch.get("success"):
            ctx = sch.get("clinical_context", "")
            req = sch.get("required_fields", [])
        req_str = f" (required: {', '.join(req)})" if req else ""
        lines.append(f"- {t}: {ctx}{req_str}")
    return "\n".join(lines)


# removed: _generate_resource_previews (no longer needed)


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

# removed: tool loader helpers (unused)


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
        # Build type hints and short descriptions from schema discovery
        type_hints = _build_type_hints_from_registry_schemas(available_types)
        
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
            f"AVAILABLE HACS RESOURCES (from registry schemas):\n{type_hints}\n\n"
            f"SELECTION CRITERIA:\n"
            f"- Prioritize resources that directly map to template content\n"
            f"- Include foundational resources (Patient, Encounter) when appropriate\n"
            f"- Consider clinical workflows and resource relationships\n"
            f"- Balance breadth with relevance; avoid over-engineering"
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

        # Build MappingSpec instead of StackTemplate and register AnnotationWorkflowResource
        tpl_name = (template_name or "auto_workflow").strip() or "auto_workflow"
        mapping_spec = _build_default_mapping_spec()
        try:
            reg_out = _register_annotation_workflow(tpl_name, mapping_spec, instruction_md)
            return reg_out
        except Exception as _e:
            return {"success": False, "message": str(_e)}
    except Exception as e:
        logger.error(f"Template synthesis failed: {e}")
        return {"success": False, "error": str(e)}


@task
async def _extract_variables_and_instantiate(template_name: str, context_text: str, use_llm: bool = False) -> Dict[str, Any]:
    """LLM-first variable extraction and instantiation inside workflow."""
    try:
        from hacs_registry import get_global_registry
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
        
        # Retrieve registered workflow mapping
        reg = get_global_registry()
        candidates = [r for r in reg._resources.values() if getattr(r, 'metadata', None) and r.metadata.name == template_name]
        workflow_res = None
        for r in candidates:
            if getattr(r, 'resource_class', None) == 'AnnotationWorkflowResource':
                workflow_res = r
                break
        mapping = _build_default_mapping_spec()
        if workflow_res is not None:
            wf_instance = getattr(workflow_res, 'resource_instance', {}) or {}
            mapping_dict = (wf_instance.get('mapping_spec') if isinstance(wf_instance, dict) else None) or {}
            try:
                mapping = MappingSpec(**mapping_dict)
            except Exception:
                mapping = _build_default_mapping_spec()
        # Instantiate via mapping spec
        resources = _instantiate_from_mapping(mapping, variables)
            
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
    # Build concise registry-backed descriptions
    candidate_details = _resource_type_hints_markdown(candidates)
    
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
    # Build comprehensive set of HACS model types suitable for this workflow
    # Start with a broad preferred list, then union with model registry entries
    default_types: List[str] = [
        "Patient", "Encounter", "Observation", "Condition", "Procedure",
        "MedicationRequest", "Medication", "MedicationStatement", "AllergyIntolerance",
        "DiagnosticReport", "DocumentReference", "Immunization", "ServiceRequest",
        "Goal", "FamilyMemberHistory", "Organization", "Practitioner",
        "Appointment", "CarePlan", "CareTeam", "NutritionOrder", "PlanDefinition",
        "ResourceBundle", "MemoryBlock", "Document",
    ]
    try:
        registry_types = [name for name in get_model_registry().keys() if isinstance(name, str)]
    except Exception:
        registry_types = []
    all_types = list(dict.fromkeys(default_types + registry_types))
    types_to_fetch: List[str] = inputs.get("fetch_schemas_for", all_types)
    
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
    
    # Determine variables from MappingSpec in registered workflow
    tpl_res = sorted(candidates, key=lambda r: r.metadata.version, reverse=True)[0]
    wf_instance = getattr(tpl_res, "resource_instance", {}) or {}
    mapping_dict = (wf_instance.get("mapping_spec") if isinstance(wf_instance, dict) else None) or {}
    try:
        mapping = MappingSpec(**mapping_dict)
    except Exception:
        mapping = _build_default_mapping_spec()
    needed_vars: list[str] = []
    for out in mapping.outputs:
        for b in out.fields.values():
            if isinstance(b, dict):
                var_name = b.get("var")
                if isinstance(var_name, str) and var_name not in needed_vars:
                    needed_vars.append(var_name)
            elif isinstance(b, SourceBinding) and b.var and b.var not in needed_vars:
                needed_vars.append(b.var)
    variables = {k: context_text for k in needed_vars}
    
    try:
        # Step 3: Instantiate resources via mapping
        stack = _instantiate_from_mapping(mapping, variables)
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
    # Keep a minimal availability check used by README/invocations
    status: Dict[str, bool] = {"discover_resources": False, "get_schema": False, "modeling_bundling": False}
    try:
        status["discover_resources"] = bool(getattr(discover_hacs_resources(category_filter="clinical"), "success", False))
    except Exception:
        pass
    try:
        status["get_schema"] = bool(getattr(get_hacs_resource_schema("Patient"), "success", False))
    except Exception:
        pass
    try:
        _ = validate_hacs_resource(actor_name="validator", model_name="Patient", data={"full_name": "Test"})
        bundle = create_resource_bundle(actor_name="validator", bundle_type="document", title="validation")
        status["modeling_bundling"] = bool(getattr(bundle, "success", False))
    except Exception:
        pass
    return status


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
                from hacs_registry import get_global_registry
                registry = get_global_registry()
                candidates = [r for r in registry._resources.values() if getattr(r, 'metadata', None) and r.metadata.name == template_name]
                mapping = _build_default_mapping_spec()
                if candidates:
                    wf_res = sorted(candidates, key=lambda r: r.metadata.version, reverse=True)[0]
                    wf_instance = getattr(wf_res, 'resource_instance', {}) or {}
                    mapping_dict = (wf_instance.get('mapping_spec') if isinstance(wf_instance, dict) else None) or {}
                    try:
                        mapping = MappingSpec(**mapping_dict)
                    except Exception:
                        mapping = _build_default_mapping_spec()
                instance_vars = inst.get("variables", {})
                stack_objs = _instantiate_from_mapping(mapping, instance_vars)
                persisted = await _persist_stack(database_url, stack_objs)
                result["persisted"] = persisted
            except Exception as e:
                result["persist_error"] = str(e)

    return result
