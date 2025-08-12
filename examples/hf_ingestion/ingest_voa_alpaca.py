import os
from typing import Any, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

from datasets import load_dataset

from hacs_models import StackTemplate, LayerSpec, instantiate_stack_template
from hacs_models import Patient, Observation, MemoryBlock, CodeableConcept, Coding
from hacs_utils.structured import generate_extractions
from hacs_utils.integrations.openai.client import OpenAIClient
from hacs_utils.integrations.anthropic.__init__ import create_anthropic_client  # may exist
from hacs_persistence import Adapter

HF_TOKEN = os.getenv("HF_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://hacs:hacs_dev@localhost:5432/hacs")

if not HF_TOKEN:
    raise RuntimeError("HF_TOKEN not set in environment")

adapter = Adapter(database_url=DATABASE_URL)

stack_template = StackTemplate(
    name="voa_alpaca_stack",
    version="1.0.0",
    description="Patient + Observation (input) + Memory (output)",
    variables={
        "patient_name": {"type": "string"},
        "instruction": {"type": "string"},
        "input_text": {"type": "string"},
        "output_text": {"type": "string"},
    },
    layers=[
        LayerSpec(
            resource_type="Patient",
            layer_name="patient",
            bindings={
                "full_name": "patient_name",
            },
            constant_fields={
                "gender": "unknown",
            },
        ),
        LayerSpec(
            resource_type="Observation",
            layer_name="input_observation",
            bindings={
                "value_string": "input_text",
            },
            constant_fields={
                "status": "final",
                # Minimal codeable concept for summarizing dataset input
                # We'll set text via bindings/constant
                "code.text": "DatasetInput",
            },
        ),
        LayerSpec(
            resource_type="MemoryBlock",
            layer_name="output_memory",
            bindings={
                "content": "output_text",
            },
            constant_fields={
                "memory_type": "semantic",
                "importance_score": 0.6,
            },
        ),
    ],
)


def _extract_between(text: str, start_tag: str, end_tag: str) -> str:
    if not text:
        return ""
    try:
        start = text.index(start_tag) + len(start_tag)
        end = text.index(end_tag, start)
        return text[start:end].strip()
    except ValueError:
        return ""


def build_stack_from_row(row: Dict[str, Any]) -> Dict[str, Any]:
    # 1) Build prompt template from instruction column (markdown template inside [TEMPLATE]...[/TEMPLATE])
    template_md = _extract_between(row.get("instruction", ""), "[TEMPLATE]", "[/TEMPLATE]") or row.get("instruction", "")

    # Define a minimal prompt expecting structured extractions with fields needed for the stack
    # The model should return JSON like: {"extractions": [{"extraction_class":"patient_name","extraction_text":"...","char_interval":{"start_pos":0,"end_pos":10}}, ...]}
    prompt = f"""
Use the following TEMPLATE and TRANSCRIÇÃO to extract the variables patient_name, input_text, output_text.

TEMPLATE:
{template_md}

TRANSCRIÇÃO:
{row.get('input','')}

Return JSON with key 'extractions' and items containing extraction_class and extraction_text for each variable.
"""

    # 2) Generate extractions with provider client auto-detection (OpenAI/Anthropic/generic)
    # Here we assume user provides a configured client outside; for demo we just simulate with None and fallback
    client = None
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if openai_key:
        try:
            client = OpenAIClient(api_key=openai_key)
        except Exception:
            client = None
    elif anthropic_key:
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=anthropic_key)
        except Exception:
            client = None

    if client is not None:
        try:
            extractions = generate_extractions(client, prompt=prompt)
        except Exception:
            extractions = []

    if not client or not extractions:
        # Fallback: build extractions trivially from fields
        from hacs_models import Extraction
        extractions = [
            Extraction(extraction_class="patient_name", extraction_text=row.get("input", "Anonymous Patient")),
            Extraction(extraction_class="input_text", extraction_text=row.get("input", "")),
            Extraction(extraction_class="output_text", extraction_text=row.get("output", "")),
        ]

    # 3) Map extractions to template variables
    by_class = {e.extraction_class: e.extraction_text for e in extractions}
    variables = {
        "patient_name": by_class.get("patient_name", row.get("input", "Anonymous Patient")),
        "instruction": template_md,
        "input_text": by_class.get("input_text", row.get("input", "")),
        "output_text": by_class.get("output_text", row.get("output", "")),
    }

    stack = instantiate_stack_template(stack_template, variables)

    # Ensure Observation has a minimal codeable concept if not set by template helper
    obs = stack["input_observation"]
    if isinstance(obs, Observation) and obs.code is None:
        obs.code = CodeableConcept(coding=[Coding(code="dataset_input", display="DatasetInput")], text="DatasetInput")

    # Set subject linkage
    patient = stack["patient"]
    if isinstance(obs, Observation):
        obs.subject = f"Patient/{patient.id}"

    return stack


def save_stack(stack: Dict[str, Any]) -> Dict[str, Any]:
    patient = stack["patient"]
    obs = stack["input_observation"]
    mem = stack["output_memory"]

    saved_patient = adapter.save_resource(patient)
    saved_obs = adapter.save_resource(obs)
    try:
        saved_mem = adapter.save_resource(mem)
    except Exception:
        saved_mem = {"id": getattr(mem, "id", None)}

    return {
        "patient_id": getattr(saved_patient, "id", None),
        "observation_id": getattr(saved_obs, "id", None),
        "memory_id": getattr(saved_mem, "id", None),
    }


def main():
    ds = load_dataset("voa-health/voa-alpaca", split="train", token=HF_TOKEN)
    ds = ds.select(range(10))

    stacks = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = [ex.submit(build_stack_from_row, ds[i]) for i in range(len(ds))]
        for fut in as_completed(futures):
            stacks.append(fut.result())

    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = [ex.submit(save_stack, s) for s in stacks]
        for fut in as_completed(futures):
            results.append(fut.result())

    print({"inserted": len(results), "sample_ids": results[:3]})

if __name__ == "__main__":
    main()
