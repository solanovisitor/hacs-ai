"""
HACS Extraction Tools - Structured Data Extraction and Resource Creation

This domain provides tools for creating and updating HACS resource records and compositions
from any data source (unstructured text, other HACS records like memories/preferences/procedures).
Focuses on robust structured generation, mapping specifications, and context management.

Domain Focus:
- Structured extraction with chunking and source grounding
- MappingSpec synthesis and application
- Variable extraction from unstructured data
- Context summarization and compression for long pipelines
"""

import logging
import os
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from hacs_models import HACSResult, BaseResource
from hacs_core import Actor
from hacs_models import (
    get_model_registry, MappingSpec, OutputSpec, SourceBinding, 
    ResourceBundle, Patient, Document
)
from hacs_models.utils import set_nested_field
from hacs_utils.structured import (
    generate_structured_output, generate_chunked_extractions,
    generate_structured_list, extract
)
# Tool domain: extraction - Structured data extraction and resource creation

logger = logging.getLogger(__name__)


def suggest_mapping(
    instruction: Optional[str] = None,
    resource_hints: Optional[List[str]] = None,
    messages: Optional[List[Dict[str, Any]]] = None,
    extraction_prompt: Optional[str] = None,
    documents: Optional[List[Dict[str, Any]]] = None,
) -> HACSResult:
    """
    Generate a MappingSpec that defines how to extract variables and map them to HACS resources.
    
    Args:
        instruction_md: Markdown instruction describing the mapping requirements
        resource_hints: Optional list of resource types to prioritize (e.g., ["Patient", "Document"])
        
    Returns:
        HACSResult with the synthesized MappingSpec
    """
    try:
        # Get available resource types
        model_registry = get_model_registry()
        available_types = list(model_registry.keys())
        
        # Use hints or default to common clinical types
        if resource_hints:
            target_types = [t for t in resource_hints if t in available_types]
        else:
            target_types = [
                "Patient", "Document", "Condition", "Observation", 
                "MedicationRequest", "Procedure", "Encounter"
            ]
            target_types = [t for t in target_types if t in available_types]
        
        # Build composite instruction context
        blocks: List[str] = []
        if instruction:
            blocks.append(str(instruction))
        if messages:
            blocks.append("\n".join([str(m.get("content", m)) for m in messages]))
        if documents:
            for d in documents:
                content = d.get("content") or d.get("text") or ""
                blocks.append(str(content))
        combined_instruction = "\n\n".join(blocks).strip()

        # Build prompt for LLM to generate mapping spec
        base_prompt = f"""
Based on the following instruction, create a MappingSpec that defines:
1. What variables need to be extracted from input text
2. How those variables map to HACS resource fields

Instruction:
{combined_instruction}

Available resource types: {target_types}
Available model registry: {list(model_registry.keys())}

Generate a MappingSpec with:
- variables: list of variable names to extract
- layers: dict mapping layer names to OutputSpec objects
- Each OutputSpec should specify resource_type and source_bindings

Respond with valid JSON for the MappingSpec.
"""
        
        # Try to use LLM if available
        try:
            result = generate_structured_output(
                prompt=extraction_prompt or base_prompt,
                response_model=MappingSpec,
                llm_provider="openai",
                format_type="json"
            )
            
            if result.success and result.data:
                return HACSResult(
                    success=True,
                    message="Successfully synthesized MappingSpec using LLM",
                    data={"mapping_spec": result.data.model_dump()}
                )
        except Exception as llm_error:
            logger.warning(f"LLM synthesis failed: {llm_error}")
        
        # Fallback: create a conservative default mapping
        default_mapping = MappingSpec(
            variables=["patient_name", "document_title", "clinical_note"],
            layers={
                "patient": OutputSpec(
                    resource_type="Patient",
                    source_bindings=[
                        SourceBinding(
                            target_field="name.0.text",
                            source_variable="patient_name"
                        )
                    ]
                ),
                "document": OutputSpec(
                    resource_type="Document", 
                    source_bindings=[
                        SourceBinding(
                            target_field="title",
                            source_variable="document_title"
                        ),
                        SourceBinding(
                            target_field="content.0.attachment.data",
                            source_variable="clinical_note"
                        )
                    ]
                )
            }
        )
        
        return HACSResult(
            success=True,
            message="Created default MappingSpec (LLM synthesis not available)",
            data={"mapping_spec": default_mapping.model_dump()}
        )
        
    except Exception as e:
        return HACSResult(
            success=False,
            message="Failed to synthesize MappingSpec",
            error=str(e)
        )


def extract_values(
    text: Optional[str] = None,
    variables: Optional[List[str]] = None,
    chunking: Optional[Dict[str, Any]] = None,
    provider: str = "openai",
    messages: Optional[List[Dict[str, Any]]] = None,
    extraction_prompt: Optional[str] = None,
    documents: Optional[List[Dict[str, Any]]] = None,
) -> HACSResult:
    """
    Extract specified variables from input text using structured generation.
    
    Args:
        text: Input text to extract variables from
        variables: List of variable names to extract
        chunking: Optional chunking config with max_chars, overlap
        provider: LLM provider to use ("openai", "anthropic")
        
    Returns:
        HACSResult with extracted variables and optional grounding information
    """
    try:
        # Normalize inputs
        variables = variables or []
        text_input = text or ""
        # Build composite context if documents or messages are provided
        contextual_blocks: List[str] = []
        if messages:
            contextual_blocks.append("\n".join([str(m.get("content", m)) for m in messages]))
        if documents:
            for d in documents:
                content = d.get("content") or d.get("text") or ""
                contextual_blocks.append(str(content))
        if contextual_blocks:
            text_input = (text_input + "\n\n" + "\n\n".join(contextual_blocks)).strip()

        # If an explicit extraction_prompt is provided, prefer using generate_extractions
        if extraction_prompt:
            try:
                schema = {"type": "object", "properties": {v: {"type": "string"} for v in variables}, "required": variables}
                result = generate_extractions(
                    prompt=extraction_prompt,
                    input_text=text_input,
                    extraction_schema=schema,
                    llm_provider=provider,
                    fenced_output=True,
                )
                if result.success:
                    return HACSResult(success=True, message="Extracted using custom prompt", data={"variables": result.data})
            except Exception as e:
                logger.warning(f"Prompted extraction failed, falling back: {e}")

        # Check for chunking requirements
        use_chunking = chunking and len(text_input) > chunking.get("max_chars", 4000)
        
        if use_chunking:
            # Use chunked extraction with grounding
            chunk_config = {
                "max_chars": chunking.get("max_chars", 4000),
                "overlap": chunking.get("overlap", 200)
            }
            
            extraction_schema = {
                "type": "object",
                "properties": {var: {"type": "string"} for var in variables},
                "required": variables
            }
            
            result = generate_chunked_extractions(
                text=text_input,
                extraction_schema=extraction_schema,
                chunk_size=chunk_config["max_chars"],
                overlap=chunk_config["overlap"],
                llm_provider=provider
            )
            
            if result.success:
                # Merge extractions from chunks
                merged_variables = {}
                grounded_extractions = result.data.get("extractions", [])
                
                for extraction in grounded_extractions:
                    for var, value in extraction.get("extracted_data", {}).items():
                        if var in variables and value:
                            merged_variables[var] = value
                
                return HACSResult(
                    success=True,
                    message=f"Extracted {len(merged_variables)} variables from {len(grounded_extractions)} chunks",
                    data={
                        "variables": merged_variables,
                        "grounded_extractions": grounded_extractions
                    }
                )
        
        else:
            # Simple single-pass extraction
            extraction_prompt_default = f"""
Extract the following variables from the given text:
Variables to extract: {variables}

Text:
{text_input}

Respond with a JSON object containing the extracted variables.
If a variable cannot be found, use an empty string or reasonable default.
"""
            
            extraction_schema = {
                "type": "object", 
                "properties": {var: {"type": "string"} for var in variables},
                "required": variables
            }
            
            result = extract(
                prompt=extraction_prompt or extraction_prompt_default,
                response_model=extraction_schema,
                llm_provider=provider,
                format_type="json"
            )
            
            if result.success:
                return HACSResult(
                    success=True,
                    message=f"Extracted {len(variables)} variables",
                    data={"variables": result.data, "grounded_extractions": []}
                )
        
        # No-LLM fallback for essential variables
        fallback_variables = {}
        text_lower = text_input.lower()
        
        for var in variables:
            if var == "patient_name":
                # Simple regex for names
                import re
                name_match = re.search(r'patient:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', text_input, re.IGNORECASE)
                fallback_variables[var] = name_match.group(1) if name_match else "Anonymous Patient"
            elif var == "document_title":
                # Use first line or extract from headers
                lines = text_input.strip().split('\n')
                fallback_variables[var] = lines[0][:100] if lines else "Clinical Document"
            elif var == "clinical_note":
                # Use the text content
                fallback_variables[var] = text_input[:1000] if text_input else ""
            else:
                fallback_variables[var] = ""
        
        return HACSResult(
            success=True,
            message=f"Used fallback extraction for {len(variables)} variables",
            data={"variables": fallback_variables, "grounded_extractions": []}
        )
        
    except Exception as e:
        return HACSResult(
            success=False,
            message="Failed to extract variables",
            error=str(e)
        )


def apply_mapping(mapping_spec: Dict[str, Any], variables: Dict[str, Any]) -> HACSResult:
    """
    Apply a MappingSpec to extracted variables to create resources and assemble a bundle.
    
    Args:
        mapping_spec: Dictionary representation of MappingSpec
        variables: Dictionary of extracted variable values
        
    Returns:
        HACSResult with created resources and ResourceBundle
    """
    try:
        # Parse mapping spec
        mapping = MappingSpec(**mapping_spec)
        
        # Create resources according to mapping
        resources = {}
        model_registry = get_model_registry()
        
        for layer_name, output_spec in mapping.layers.items():
            resource_type = output_spec.resource_type
            resource_class = model_registry.get(resource_type)
            
            if not resource_class:
                logger.warning(f"Unknown resource type: {resource_type}")
                continue
            
            # Start with base resource structure
            resource_data = {"resource_type": resource_type}
            
            # Apply source bindings
            for binding in output_spec.source_bindings:
                source_value = variables.get(binding.source_variable)
                if source_value:
                    # Use set_nested_field to handle dot notation
                    set_nested_field(resource_data, binding.target_field, source_value)
            
            # Create resource instance
            try:
                resource = resource_class(**resource_data)
                resources[layer_name] = resource
            except Exception as e:
                logger.warning(f"Failed to create {resource_type}: {e}")
                continue
        
        # Ensure we have at least one resource for bundle creation
        if not resources:
            # Create fallback Patient resource
            patient = Patient(
                name=[{"text": variables.get("patient_name", "Anonymous Patient")}]
            )
            resources["patient"] = patient
        
        # Create ResourceBundle with entries
        bundle_entries = []
        for layer_name, resource in resources.items():
            from hacs_models import BundleEntry
            entry = BundleEntry(
                resource=resource.model_dump(),
                title=f"{resource.resource_type} - {layer_name}",
                tags=[resource.resource_type.lower(), layer_name]
            )
            bundle_entries.append(entry)
        
        bundle = ResourceBundle(
            bundle_type="DOCUMENT",
            entries=bundle_entries,
            title=variables.get("document_title", "Generated Resource Bundle"),
            description=f"Bundle created from mapping spec with {len(resources)} resources"
        )
        
        return HACSResult(
            success=True,
            message=f"Successfully applied mapping spec to create {len(resources)} resources",
            data={
                "resources": {k: v.model_dump() for k, v in resources.items()},
                "bundle": bundle.model_dump()
            }
        )
        
    except Exception as e:
        return HACSResult(
            success=False,
            message="Failed to apply mapping spec",
            error=str(e)
        )


def summarize_context(
    content: Union[str, List[Dict[str, Any]]], 
    strategy: str = "recursive",
    target_tokens: int = 1000,
    provider: str = "openai"
) -> HACSResult:
    """
    Summarize context content using various strategies for token efficiency.
    
    Args:
        content: Content to summarize (string or list of messages/objects)
        strategy: Summarization strategy ("recursive", "window", "key_points")
        target_tokens: Target token count for summary
        provider: LLM provider to use
        
    Returns:
        HACSResult with summary and retained references
    """
    try:
        # Convert content to text if needed
        if isinstance(content, list):
            text_content = "\n".join([
                str(item.get("content", item)) if isinstance(item, dict) else str(item)
                for item in content
            ])
        else:
            text_content = str(content)
        
        # Estimate current token count (rough approximation)
        current_tokens = len(text_content.split()) * 1.3  # rough token estimate
        
        if current_tokens <= target_tokens:
            return HACSResult(
                success=True,
                message="Content already within target token limit",
                data={"summary": text_content, "retained_refs": []}
            )
        
        # Build summarization prompt based on strategy
        if strategy == "recursive":
            # Split into chunks and summarize progressively
            chunk_size = len(text_content) // 3
            chunks = [
                text_content[i:i+chunk_size] 
                for i in range(0, len(text_content), chunk_size)
            ]
            
            summaries = []
            for i, chunk in enumerate(chunks):
                if len(chunk.strip()) == 0:
                    continue
                    
                summary_prompt = f"""
Summarize the following content, preserving key clinical information and action items:

{chunk}

Provide a concise summary in approximately {target_tokens // len(chunks)} words.
"""
                
                try:
                    result = generate_structured_output(
                        prompt=summary_prompt,
                        response_model={"type": "string"},
                        llm_provider=provider
                    )
                    if result.success:
                        summaries.append(result.data)
                except Exception:
                    # Fallback to simple truncation
                    summaries.append(chunk[:target_tokens//len(chunks)*4])  # rough chars per token
            
            final_summary = "\n\n".join(summaries)
            
        elif strategy == "window":
            # Keep beginning and end, summarize middle
            keep_chars = target_tokens * 2  # rough char estimate
            if len(text_content) <= keep_chars * 2:
                final_summary = text_content
            else:
                beginning = text_content[:keep_chars//2]
                ending = text_content[-keep_chars//2:]
                final_summary = f"{beginning}\n\n[... content summarized ...]\n\n{ending}"
                
        else:  # key_points
            # Extract key points
            summary_prompt = f"""
Extract the key points from the following content as a concise bullet list:

{text_content}

Focus on:
- Clinical findings and observations
- Action items and decisions
- Important context for patient care
- Resource references

Target length: approximately {target_tokens} words.
"""
            
            try:
                result = generate_structured_output(
                    prompt=summary_prompt,
                    response_model={"type": "string"},
                    llm_provider=provider
                )
                final_summary = result.data if result.success else text_content[:target_tokens*4]
            except Exception:
                # Fallback: simple truncation with ellipsis
                final_summary = text_content[:target_tokens*4] + "..."
        
        # Extract retained references (IDs, names, etc.)
        retained_refs = []
        import re
        # Look for common ID patterns and resource references
        id_patterns = [
            r'\b[A-Za-z]+\-[0-9a-f\-]{8,}\b',  # Resource IDs
            r'\bpatient[_\s]*(?:id|name):\s*([^\n,]+)',  # Patient references
            r'\bresource[_\s]*(?:id|type):\s*([^\n,]+)'   # Resource references
        ]
        
        for pattern in id_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            retained_refs.extend(matches)
        
        return HACSResult(
            success=True,
            message=f"Summarized content using {strategy} strategy",
            data={
                "summary": final_summary,
                "retained_refs": list(set(retained_refs)),
                "strategy_used": strategy,
                "compression_ratio": len(final_summary) / len(text_content) if text_content else 1
            }
        )
        
    except Exception as e:
        return HACSResult(
            success=False,
            message="Failed to summarize context",
            error=str(e)
        )


# Backward-compatible wrappers (deprecated names)
def synthesize_mapping_spec(instruction_md: str, resource_hints: Optional[List[str]] = None) -> HACSResult:
    return suggest_mapping(instruction=instruction_md, resource_hints=resource_hints)


def extract_variables(**kwargs) -> HACSResult:
    return extract_values(**kwargs)


def apply_mapping_spec(mapping_spec: Dict[str, Any], variables: Dict[str, Any]) -> HACSResult:
    return apply_mapping(mapping_spec, variables)


# Export canonical tool names
__all__ = [
    "suggest_mapping",
    "extract_values",
    "apply_mapping", 
    "summarize_context",
    # Legacy aliases
    "synthesize_mapping_spec",
    "extract_variables",
    "apply_mapping_spec",
]
