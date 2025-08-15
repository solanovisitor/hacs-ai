import os
from typing import Any, Dict

from datasets import load_dataset
from datasets.exceptions import DatasetNotFoundError
from huggingface_hub import login as hf_login, HfApi

import sys
import uuid
sys.path.append(os.path.dirname(__file__))
from workflows_direct_hacs import register_template_from_instruction, instantiate_and_persist_stack

HF_TOKEN = os.getenv("HF_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://hacs:hacs_dev@localhost:5432/hacs")
HF_DATASET_ID = os.getenv("HF_DATASET_ID", "voa-engines/voa-alpaca")
HF_REVISION = os.getenv("HF_REVISION")
HF_SPLIT = os.getenv("HF_SPLIT", "train")
HF_SAMPLE_SIZE = int(os.getenv("HF_SAMPLE_SIZE", "10"))
HF_SHUFFLE_SEED = os.getenv("HF_SHUFFLE_SEED")
HF_SHARD_NUM = int(os.getenv("HF_SHARD_NUM", "0"))
HF_SHARD_INDEX = int(os.getenv("HF_SHARD_INDEX", "0"))
HF_NUM_PROC = int(os.getenv("HF_NUM_PROC", "4"))
USE_LLM_EXTRACTIONS = os.getenv("HACS_USE_LLM_EXTRACTIONS", "0").lower() not in ("0", "false", "no", "")

if not HF_TOKEN:
    raise RuntimeError("HF_TOKEN not set in environment")

def _extract_tag_sections(text: str, tags: list[str]) -> dict[str, list[str]]:
    # Minimal helper retained for dataset analysis logging only
    results: dict[str, list[str]] = {t: [] for t in tags}
    return results


import asyncio


async def main():
    # Authenticate to Hugging Face Hub non-interactively using token from .env
    try:
        hf_login(token=HF_TOKEN, add_to_git_credential=False, new_session=False)
    except Exception:
        # Continue; datasets.load_dataset will still attempt with provided token
        pass

    dataset_id = HF_DATASET_ID
    try:
        # Preflight: verify dataset access via Hub API for clearer errors
        try:
            HfApi().dataset_info(repo_id=dataset_id, token=HF_TOKEN, revision=HF_REVISION)
        except Exception:
            pass

        # Try with modern 'token' parameter
        try:
            kwargs = {"token": HF_TOKEN}
            if HF_REVISION:
                kwargs["revision"] = HF_REVISION
            ds = load_dataset(dataset_id, split=HF_SPLIT, **kwargs)
        except TypeError:
            # Fallback for older datasets lib
            kw2 = {"use_auth_token": HF_TOKEN}
            if HF_REVISION:
                kw2["revision"] = HF_REVISION
            ds = load_dataset(dataset_id, split=HF_SPLIT, **kw2)
        # Shuffle / shard / sample controls
        if HF_SHUFFLE_SEED:
            ds = ds.shuffle(seed=int(HF_SHUFFLE_SEED))
        if HF_SHARD_NUM and HF_SHARD_NUM > 0:
            ds = ds.shard(num_shards=HF_SHARD_NUM, index=HF_SHARD_INDEX)
        ds = ds.select(range(min(HF_SAMPLE_SIZE, len(ds))))
    except (DatasetNotFoundError, Exception):
        # Fallback: build a small local dataset to exercise the pipeline end-to-end
        from datasets import Dataset
        samples = []
        tmpl = (
            "## Queixa Principal: Texto\n"
            "## História da Doença Atual: Texto\n"
            "## História Médica e Psiquiátrica: Texto\n"
            "## Tratamento: lista\n"
        )
        for i in range(10):
            samples.append(
                {
                    "instruction": (
                        "Aja como um médico. Use [TRANSCRIÇÃO] para preencher o [TEMPLATE].\n"
                        f"[TEMPLATE]\n{tmpl}\n[/TEMPLATE]"
                    ),
                    "input": f"Paciente {i} apresenta queixa de dor de cabeça há 3 dias.",
                    "output": "Registro clínico sintetizado.",
                }
            )
        ds = Dataset.from_list(samples)

    # Enhanced logging: sample unique instruction/input prefixes to inspect parsing
    def log_samples(dataset, prefix_len: int = 100, sample_k: int = 5) -> None:
        try:
            instr_prefixes = {}
            input_prefixes = {}
            for i in range(min(len(dataset), HF_SAMPLE_SIZE)):
                ex = dataset[i]
                instr = (ex.get("instruction") or ex.get("template_md") or "")[:prefix_len]
                inp = (ex.get("input") or ex.get("input_text_var") or "")[:prefix_len]
                if instr:
                    instr_prefixes[instr] = instr_prefixes.get(instr, 0) + 1
                if inp:
                    input_prefixes[inp] = input_prefixes.get(inp, 0) + 1
            def top_k(d, k):
                items = sorted(d.items(), key=lambda x: (-x[1], x[0]))[:k]
                return [{"prefix": k, "count": v} for k, v in items]
            print({
                "log": "instruction_input_prefixes",
                "instruction_samples": top_k(instr_prefixes, sample_k),
                "input_samples": top_k(input_prefixes, sample_k),
            })
        except Exception as e:
            print({"log": "prefix_log_error", "error": str(e)})

    log_samples(ds, prefix_len=100, sample_k=5)

    # Use Functional API workflows: register template once, then instantiate+persist per row
    first_instruction = ds[0].get("instruction", "") if len(ds) > 0 else ""
    reg_out = await register_template_from_instruction.ainvoke(
        {
            "instruction_md": first_instruction,
            "template_name": "voa_template_auto",
        },
        {"configurable": {"thread_id": f"hf-reg-{uuid.uuid4()}"}},
    )
    template_name = reg_out.get("template_name") or "voa_template_auto"

    results = []
    for i in range(len(ds)):
        row = ds[i]
        context_text = row.get("input", "")
        inst_out = await instantiate_and_persist_stack.ainvoke(
            {
                "template_name": template_name,
                "context_text": context_text,
                "database_url": DATABASE_URL,
                "use_llm": os.getenv("HACS_USE_LLM_EXTRACTIONS", "0") not in ("0", "false", "no", ""),
            },
            {"configurable": {"thread_id": f"hf-inst-{i}-{uuid.uuid4()}"}},
        )
        results.append(inst_out)

    print({"inserted": len(results), "sample": results[:1], "template": template_name})

if __name__ == "__main__":
    asyncio.run(main())
