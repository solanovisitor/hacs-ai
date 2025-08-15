import os
from typing import Any, Dict
import re

from datasets import load_dataset
from datasets.exceptions import DatasetNotFoundError
from huggingface_hub import login as hf_login, HfApi

from hacs_models import StackTemplate, LayerSpec, instantiate_stack_template
from hacs_models import Observation, Patient, CodeableConcept, Coding
from hacs_utils.structured import (
    generate_extractions,
    generate_structured_output_openai,
    generate_structured_output_anthropic,
)
from hacs_utils.integrations.openai.client import OpenAIClient
from hacs_registry import register_stack_template, instantiate_registered_stack
from hacs_tools.domains.development_tools import (
    generate_stack_template_from_markdown_tool,
)
import sys
import uuid
sys.path.append(os.path.dirname(__file__))
from workflows import register_template_from_instruction, instantiate_and_persist_stack
from hacs_persistence.adapter import PostgreSQLAdapter
from hacs_core import Actor

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
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
USE_LLM_EXTRACTIONS = os.getenv("HACS_USE_LLM_EXTRACTIONS", "0").lower() not in ("0", "false", "no", "")

if not HF_TOKEN:
    raise RuntimeError("HF_TOKEN not set in environment")

INGESTION_ACTOR = Actor(id="hf-ingestion", name="HF Ingestion", role="system")

# In-memory cache of generated templates to avoid re-registering
TEMPLATE_CACHE: dict[str, StackTemplate] = {}

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


def _extract_tag_sections(text: str, tags: list[str]) -> dict[str, list[str]]:
    """Extract all occurrences of sections delimited by [TAG]...[/TAG] for given tags.

    - Matching is case-insensitive
    - Accented and non-accented variants can be provided in tags
    - Returns a mapping tag -> list of contents (stripped)
    """
    results: dict[str, list[str]] = {t: [] for t in tags}
    if not text:
        return results
    for tag in tags:
        pattern = re.compile(r"\[" + re.escape(tag) + r"\](.*?)\[/" + re.escape(tag) + r"\]", re.IGNORECASE | re.DOTALL)
        matches = pattern.findall(text)
        if matches:
            results[tag].extend([m.strip() for m in matches if m and m.strip()])
    return results


def _slugify(value: str) -> str:
    value = value.strip().lower()
    # replace accented characters (quick transliteration)
    value = (
        value.replace("ç", "c").replace("ã", "a").replace("õ", "o").replace("á", "a").replace("à", "a")
        .replace("â", "a").replace("é", "e").replace("ê", "e").replace("í", "i").replace("ó", "o")
        .replace("ô", "o").replace("ú", "u").replace("ü", "u")
    )
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "section"


def _parse_sections_from_template_md(template_md: str) -> list[dict[str, Any]]:
    """Parse markdown template into sections.

    Returns list of {title, content, variables (list[str])}.
    Variables are inferred from bullet lines like "- Nome:".
    """
    sections: list[dict[str, Any]] = []
    if not template_md:
        return sections
    # Split by headings starting with ##
    parts = re.split(r"(?m)^##\s+", template_md)
    for part in parts:
        if not part.strip():
            continue
        # title until end of line
        lines = part.splitlines()
        title = lines[0].strip().rstrip(":")
        body = "\n".join(lines[1:]).strip()
        # infer variables from bullet lines "- Label:"
        vars_found: list[str] = []
        for m in re.finditer(r"(?m)^-\s*([^:\n\r]+):", body):
            label = m.group(1).strip()
            if label:
                vars_found.append(label)
        sections.append({"title": title, "content": body, "variables": vars_found})
    return sections


def generate_stack_template_from_markdown(template_md: str) -> StackTemplate:
    """Generate a StackTemplate from markdown.

    Heuristics:
    - Always include Observations for each section with value_string bound to a variable per section
    - If a section title indicates patient identification and contains bullets Nome/Idade/Gênero etc., add a Patient layer with appropriate bindings
    - Variables map includes one per section and detailed patient variables when present
    """
    key = f"tpl_{hash(template_md)}"
    if key in TEMPLATE_CACHE:
        return TEMPLATE_CACHE[key]

    sections = _parse_sections_from_template_md(template_md)
    variables: dict[str, Any] = {}
    layers: list[LayerSpec] = []

    # Patient identification mapping
    patient_layer_added = False
    patient_bindings: dict[str, str] = {}
    patient_extra_bindings: dict[str, str] = {}

    for sec in sections:
        title = sec["title"]
        var_name = _slugify(title)
        # For general sections, create an Observation layer per section
        variables[var_name] = {"type": "string"}
        layers.append(
            LayerSpec(
                resource_type="Observation",
                layer_name=var_name,
                bindings={"value_string": var_name},
                constant_fields={"status": "final", "code.text": title},
            )
        )

        # Handle patient identification specially
        if not patient_layer_added and re.search(r"identifica[çc][aã]o\s+do\s+paciente", title, re.IGNORECASE):
            # Scan variables inside section
            for lb in sec.get("variables", []):
                lb_lower = lb.strip().lower()
                if "nome" in lb_lower:
                    vn = "patient_full_name"
                    variables[vn] = {"type": "string"}
                    patient_bindings["full_name"] = vn
                elif "idade" in lb_lower:
                    vn = "patient_age"
                    variables[vn] = {"type": "integer"}
                    patient_bindings["age"] = vn
                elif "gênero" in lb_lower or "genero" in lb_lower or "sexo" in lb_lower:
                    vn = "patient_gender"
                    variables[vn] = {"type": "string"}
                    patient_bindings["gender"] = vn
                else:
                    # store extra identification fields under agent_context
                    vn = _slugify(f"patient_{lb}")
                    variables[vn] = {"type": "string"}
                    patient_extra_bindings[f"agent_context.{_slugify(lb)}"] = vn
            if patient_bindings or patient_extra_bindings:
                layers.insert(0, LayerSpec(resource_type="Patient", layer_name="patient", bindings={**patient_bindings, **patient_extra_bindings}, constant_fields={}))
                patient_layer_added = True

    tpl = StackTemplate(
        name=_slugify(sections[0]["title"]) if sections else "auto_template",
        version="1.0.0",
        description="Auto-generated from markdown template",
        variables=variables,
        layers=layers,
    )
    try:
        register_stack_template(tpl)
    except Exception:
        pass

    TEMPLATE_CACHE[key] = tpl
    return tpl


def _extract_variables_from_row(row: Dict[str, Any]) -> Dict[str, Any]:
    # 1) Build prompt template from instruction column (markdown template inside [TEMPLATE]...[/TEMPLATE])
    instruction_text = row.get("instruction", "") or ""
    tpl_sections = _extract_tag_sections(instruction_text, ["TEMPLATE"])  # extract only inside [TEMPLATE]
    template_md = "\n\n".join(tpl_sections.get("TEMPLATE", [])) or _extract_between(instruction_text, "[TEMPLATE]", "[/TEMPLATE]") or instruction_text

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
    client = None
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if USE_LLM_EXTRACTIONS and openai_key:
        try:
            client = OpenAIClient(api_key=openai_key, model=OPENAI_MODEL)
        except Exception as e:
            print({"log": "llm_client_error", "provider": "openai", "error": str(e)})
            client = None
    elif USE_LLM_EXTRACTIONS and anthropic_key:
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=anthropic_key)
        except Exception as e:
            print({"log": "llm_client_error", "provider": "anthropic", "error": str(e)})
            client = None
    else:
        if not USE_LLM_EXTRACTIONS:
            print({"log": "llm_extractions_disabled"})

    if client is not None:
        try:
            extractions = generate_extractions(client, prompt=prompt, model=OPENAI_MODEL)
        except Exception as e:
            print({"log": "llm_extraction_error", "error": str(e)})
            extractions = []

    if not client or not extractions:
        # Fallback: build extractions trivially from fields
        from hacs_models import Extraction
        extractions = [
            Extraction(extraction_class="patient_name", extraction_text="Anonymous Patient"),
            Extraction(extraction_class="input_text", extraction_text=row.get("input", "")),
            Extraction(extraction_class="output_text", extraction_text=row.get("output", "")),
        ]

    # 3) Map extractions to template variables
    by_class = {e.extraction_class: e.extraction_text for e in extractions}
    # Build variables and sanitize patient name for model constraints
    raw_name = by_class.get("patient_name")
    name = raw_name.strip() if isinstance(raw_name, str) else None
    if not name:
        name = "Anonymous Patient"
    if len(name) > 200:
        name = name[:200]

    # Extract inputs only from whitelisted tags: TRANSCRIÇÃO/TRANSCRICAO, CONTEXTO, ANOTAÇÕES/ANOTACOES
    raw_input_source = row.get("input", "") or ""
    input_tags = ["TRANSCRIÇÃO", "TRANSCRICAO", "CONTEXTO", "ANOTAÇÕES", "ANOTACOES"]
    input_sections = _extract_tag_sections(raw_input_source, input_tags)
    ordered_join = []
    for tag in input_tags:
        parts = input_sections.get(tag, [])
        if parts:
            ordered_join.extend(parts)
    # If LLM provided an input_text extraction, prefer it; else use tag-only content; else fallback to raw
    raw_input = by_class.get("input_text")
    if isinstance(raw_input, str) and raw_input.strip():
        input_text = raw_input
    elif ordered_join:
        input_text = "\n\n".join(ordered_join)
    else:
        input_text = raw_input_source

    variables = {
        "patient_name": name,
        "instruction": template_md,
        "input_text": input_text,
        "output_text": by_class.get("output_text", row.get("output", "")),
    }
    return variables


def build_stack_from_row(row: Dict[str, Any]) -> Dict[str, Any]:
    # Extract instruction and input sections
    instruction_text = row.get("instruction", "") or ""
    tpl_sections = _extract_tag_sections(instruction_text, ["TEMPLATE"])
    template_md = "\n\n".join(tpl_sections.get("TEMPLATE", [])) or _extract_between(instruction_text, "[TEMPLATE]", "[/TEMPLATE]") or instruction_text

    # Generate or reuse a stack template derived from instruction using hacs-tools
    gen_res = generate_stack_template_from_markdown_tool(template_md)
    if not getattr(gen_res, "success", False):
        print({"log": "template_generation_failed", "message": gen_res.message})
        # Fallback to local heuristic generator
        effective_template = generate_stack_template_from_markdown(template_md)
        tpl_name = effective_template.name
    else:
        tpl_name = gen_res.template_name
        # Reconstruct template locally from tool payload to preserve resource types
        try:
            vars_payload = (gen_res.data or {}).get("variables", {})
            layers_payload = (gen_res.data or {}).get("layers", [])
            variables = vars_payload if isinstance(vars_payload, dict) else {}
            layers = []
            for lp in layers_payload:
                try:
                    layers.append(LayerSpec(**lp))
                except Exception:
                    continue
            effective_template = StackTemplate(
                name=tpl_name,
                version="1.0.0",
                description="Generated via tool",
                variables=variables,
                layers=layers,
            )
        except Exception as e:
            print({"log": "reconstruct_template_error", "error": str(e)})
            effective_template = generate_stack_template_from_markdown(template_md)

    # Extract input-only context from allowed tags
    raw_input_source = row.get("input", "") or ""
    input_tags = ["TRANSCRIÇÃO", "TRANSCRICAO", "CONTEXTO", "ANOTAÇÕES", "ANOTACOES"]
    input_sections = _extract_tag_sections(raw_input_source, input_tags)
    context_text = "\n\n".join([s for tag in input_tags for s in input_sections.get(tag, [])]) or raw_input_source

    # Fill variables: by default, assign section variables to context text; for Patient vars, attempt simple regex; optionally LLM per-section
    filled_vars: dict[str, Any] = {k: "" for k in effective_template.variables.keys()}

    # Patient heuristics
    if "patient_full_name" in filled_vars:
        # very simple heuristic: look for "Nome:" lines
        m = re.search(r"(?im)^\s*-?\s*nome\s*:\s*(.+)$", instruction_text)
        if m:
            filled_vars["patient_full_name"] = m.group(1).strip()
    if "patient_age" in filled_vars:
        m = re.search(r"(?i)\b(\d{1,3})\s*anos?\b", context_text)
        if m:
            filled_vars["patient_age"] = int(m.group(1))
    if "patient_gender" in filled_vars:
        if re.search(r"(?i)\b(feminino|female)\b", context_text):
            filled_vars["patient_gender"] = "female"
        elif re.search(r"(?i)\b(masculino|male)\b", context_text):
            filled_vars["patient_gender"] = "male"

    # Section variables: set to context_text by default; if LLM enabled, try to extract per section
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    llm_client = None
    if USE_LLM_EXTRACTIONS and openai_key:
        try:
            llm_client = OpenAIClient(api_key=openai_key, model=OPENAI_MODEL)
        except Exception:
            llm_client = None
    elif USE_LLM_EXTRACTIONS and anthropic_key:
        try:
            from anthropic import Anthropic
            llm_client = Anthropic(api_key=anthropic_key)
        except Exception:
            llm_client = None

    for var_name in effective_template.variables.keys():
        if var_name in ("patient_full_name", "patient_age", "patient_gender"):
            continue
        value = context_text
        if llm_client is not None:
            try:
                sec_title = var_name.replace("_", " ")
                messages = [
                    {"role": "system", "content": "Você extrai conteúdo de seções do contexto fornecido. Retorne apenas o texto da seção, sem explicações."},
                    {"role": "user", "content": f"Seção: {sec_title}\n\nContexto:\n\n{context_text}"},
                ]
                resp = llm_client.chat(messages, model=OPENAI_MODEL, temperature=0)
                value = str(getattr(resp, "content", resp))
            except Exception as e:
                print({"log": "section_llm_error", "var": var_name, "error": str(e)})
                value = context_text
        filled_vars[var_name] = value

    # Instantiate stack using registered template so resource types are preserved
    try:
        stack = instantiate_registered_stack(tpl_name, filled_vars)
    except Exception as e:
        print({"log": "instantiate_registered_stack_error", "error": str(e)})
        stack = instantiate_stack_template(effective_template, filled_vars)

    # Ensure Observation has a minimal codeable concept if not set by template helper
    obs_resource = None
    patient_resource = None
    for _layer_name, resource in stack.items():
        if obs_resource is None and isinstance(resource, Observation):
            obs_resource = resource
        if patient_resource is None and (isinstance(resource, Patient) or getattr(resource, "resource_type", "") == "Patient"):
            patient_resource = resource

    if isinstance(obs_resource, Observation) and getattr(obs_resource, "code", None) is None:
        obs_resource.code = CodeableConcept(
            coding=[Coding(code="dataset_input", display="DatasetInput")], text="DatasetInput"
        )

    # Set subject linkage if both exist
    if isinstance(obs_resource, Observation) and patient_resource is not None:
        try:
            obs_resource.subject = f"Patient/{patient_resource.id}"
        except Exception:
            pass

    return stack


async def save_stack(adapter: PostgreSQLAdapter, stack: Dict[str, Any]) -> Dict[str, Any]:
    persisted: Dict[str, Any] = {}
    for layer_name, resource in stack.items():
        try:
            saved = await adapter.save(resource, INGESTION_ACTOR)
            persisted[layer_name] = getattr(saved, "id", None)
        except Exception as e:
            persisted[layer_name] = f"error: {e}"
    return persisted


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
