# VOA-Alpaca HACS Resource Extraction Pipeline

This example demonstrates extracting HACS resources from the Portuguese medical dataset `voa-engines/voa-alpaca` from Hugging Face.

## Overview

The pipeline processes medical transcriptions and clinical contexts in Portuguese, extracting structured HACS resources like:
- **Patient** information
- **Observations** (vital signs, symptoms)
- **Conditions** (diagnoses, problems)
- **Medications** and prescriptions
- **Procedures** and interventions

## Dataset Format

The VOA-Alpaca dataset contains entries with tagged content:

### TRANSCRIÇÃO (Transcription)
Medical consultation audio transcriptions:
```
[TRANSCRIÇÃO]
Para insônia eu não tenho um laudo, mas é uma coisa que já desde a pandemia...
[/TRANSCRIÇÃO]
```

### CONTEXTO (Context)
Structured clinical information:
```
[CONTEXTO]
Identificação:
* Nome: Joelma Gomes Henriques Queiroz
* Idade: 55 anos

Evolução Clínica:
Paciente relata alteração recente na medicação psiquiátrica...
[/CONTEXTO]
```

## Setup

1. **Install dependencies:**
   ```bash
   pip install datasets transformers
   ```

2. **Set environment variables in `.env`:**
   ```
   OPENAI_API_KEY=your_openai_key_here
   HUGGINGFACE_API_TOKEN=your_hf_token_here  # Optional for public datasets
   ```

## Usage

### Test Parsing Logic
```bash
uv run python examples/test_voa_parsing.py
```

### Run Full Extraction Pipeline
```bash
uv run python examples/huggingface_voa_extraction.py
```

## Pipeline Steps

1. **Load Dataset**: Downloads first 10 entries from `voa-engines/voa-alpaca`
2. **Parse Content**: Extracts text from `[TRANSCRIÇÃO]` and `[CONTEXTO]` tags
3. **Extract Resources**: Uses citation-guided extraction to find HACS resources
4. **Aggregate Results**: Shows statistics and detailed examples

## Expected Output

```
🚀 VOA-Alpaca HACS Resource Extraction Pipeline
============================================================

📥 Loading 10 entries from voa-engines/voa-alpaca...
✅ Loaded 10 entries successfully

📋 Dataset Preview:
   Entry 0: ['transcricao']
     transcricao: Para insônia eu não tenho um laudo, mas é uma coisa...
   Entry 1: ['contexto']
     contexto: Identificação: Nome: Joelma Gomes Henriques...

🔬 Starting Resource Extraction...
----------------------------------------
✅ Entry 0 (transcricao): 3 resources
   - Observation: 2
   - Condition: 1
✅ Entry 1 (contexto): 8 resources
   - Patient: 1
   - Observation: 4
   - MedicationStatement: 3

📊 Extraction Summary:
   📥 Entries processed: 10
   ✅ Successful extractions: 8
   🏥 Total resources extracted: 45
   📈 Average resources per entry: 5.6

🏥 Resource Type Distribution:
   Observation: 18 total
   MedicationStatement: 12 total
   Patient: 8 total
   Condition: 7 total
```

## Features

- **Multilingual**: Handles Portuguese medical text
- **Tag-aware**: Properly extracts content from structured tags
- **Citation-guided**: Uses two-stage extraction for better accuracy
- **Resource-rich**: Extracts multiple HACS resource types
- **Error handling**: Graceful handling of parsing and extraction errors
- **Detailed reporting**: Comprehensive statistics and examples

## Notes

- The pipeline uses `gpt-4o-mini` for extraction (configurable)
- Rate limiting is applied (max 2 concurrent extractions)
- First 10 entries are processed by default (configurable)
- Results include citation spans for traceability
