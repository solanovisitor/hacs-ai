import os
from typing import Any, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

from datasets import load_dataset

from hacs_models import StackTemplate, LayerSpec, instantiate_stack_template
from hacs_models import Patient, Observation, MemoryBlock, CodeableConcept, Coding
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


def build_stack_from_row(row: Dict[str, Any]) -> Dict[str, Any]:
    variables = {
        "patient_name": row.get("input", "Anonymous Patient"),
        "instruction": row.get("instruction", ""),
        "input_text": row.get("input", ""),
        "output_text": row.get("output", ""),
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


+if __name__ == "__main__":
+    main()
