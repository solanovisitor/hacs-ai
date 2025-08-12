# HACS + Hugging Face Ingestion (voa-alpaca)

Loads `voa-health/voa-alpaca` and for the first 10 rows:
- Parses [TEMPLATE] from `instruction` and [TRANSCRIÇÃO] from `input`
- Optionally uses an LLM to generate structured output according to the template
- Instantiates a HACS stack (Patient + Observation + Memory) and persists to the DB

Requirements:
- `.env` with `HF_TOKEN` and `DATABASE_URL`
- LLM keys optional: `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`

Run:
```bash
uv run python examples/hf_ingestion/ingest_voa_alpaca.py
```
