#!/usr/bin/env python3
"""
HACS + Hugging Face Ingestion (voa-alpaca) - DIRECT HACS TOOLS VERSION

Eliminates MCP dependency and uses HACS tools directly for improved reliability.

Key improvements:
- No MCP server dependency
- Direct HACS tool integration  
- Enhanced error handling
- Comprehensive logging
- Fallback mechanisms

Loads `voa-engines/voa-alpaca` and for each record:
- Parses [TEMPLATE] from `instruction` and [TRANSCRIÇÃO] from `input`
- Uses HACS tools directly for template generation and stack instantiation
- Persists HACS resources to PostgreSQL database
"""

import os
import sys
import time
import asyncio
import logging
from typing import Any, Dict, List
from datetime import datetime

# Import workflow visualizer for enhanced output
from workflow_visualizer import WorkflowVisualizer, console

# Setup comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hf_ingestion_direct_hacs.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Add paths for imports
sys.path.append(os.path.dirname(__file__))

# Standard imports
from datasets import load_dataset, Dataset
from datasets.exceptions import DatasetNotFoundError
from huggingface_hub import login as hf_login, HfApi

# HACS imports
from hacs_models import StackTemplate, LayerSpec
from hacs_persistence.adapter import PostgreSQLAdapter
from hacs_core import Actor

# Direct HACS workflows (no MCP dependency)
from workflows_direct_hacs import (
    register_template_from_instruction,
    instantiate_and_persist_stack,
    validate_hacs_tools_availability
)

# Configuration from environment
HF_TOKEN = os.getenv("HF_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://hacs:hacs_dev@localhost:5432/hacs")
HF_DATASET_ID = os.getenv("HF_DATASET_ID", "voa-engines/voa-alpaca")
HF_REVISION = os.getenv("HF_REVISION")
HF_SPLIT = os.getenv("HF_SPLIT", "train")
HF_SAMPLE_SIZE = int(os.getenv("HF_SAMPLE_SIZE", "10"))
HF_SHUFFLE_SEED = os.getenv("HF_SHUFFLE_SEED")
HF_SHARD_NUM = int(os.getenv("HF_SHARD_NUM", "0"))
HF_SHARD_INDEX = int(os.getenv("HF_SHARD_INDEX", "0"))
USE_LLM_EXTRACTIONS = os.getenv("HACS_USE_LLM_EXTRACTIONS", "0").lower() not in ("0", "false", "no", "")

# Validate required configuration
if not HF_TOKEN:
    logger.warning("HF_TOKEN not set - will use fallback synthetic dataset")

# Global actor for ingestion operations
INGESTION_ACTOR = Actor(id="hf-ingestion-direct", name="HF Ingestion Direct HACS", role="system")


def create_fallback_dataset(sample_size: int = 10) -> Dataset:
    """Create a fallback synthetic dataset for testing when HF dataset is unavailable."""
    logger.info(f"Creating fallback synthetic dataset with {sample_size} samples")
    
    samples = []
    templates = [
        {
            "template": """## Identificação do Paciente
- Nome: 
- Idade: 
- Gênero: 

## Queixa Principal


## História da Doença Atual


## Exame Físico


## Diagnóstico


## Plano de Tratamento""",
            "input_patterns": [
                "Paciente {name}, {age} anos, sexo {gender}, apresenta {complaint}.",
                "Sr(a) {name}, {age} anos, {gender}, refere {complaint} há {duration}.",
                "{name}, {age} anos, {gender}, comparece com queixa de {complaint}."
            ]
        },
        {
            "template": """## Dados do Paciente
- Nome:
- Idade:
- Sexo:

## Medicamentos em Uso


## Exames Complementares


## Diagnóstico""",
            "input_patterns": [
                "Paciente {name}, {age} anos, {gender}, em uso de {medication}.",
                "{name}, {age} anos, {gender}, hipertenso há {duration}.",
                "Sr(a) {name}, {age} anos, realiza acompanhamento de {condition}."
            ]
        }
    ]
    
    names = ["Maria Silva", "João Santos", "Ana Costa", "Pedro Oliveira", "Carla Souza"]
    ages = ["25", "45", "35", "55", "30"]
    genders = ["feminino", "masculino", "feminino", "masculino", "feminino"]
    complaints = ["dor de cabeça", "dor abdominal", "tosse seca", "dor lombar", "fadiga"]
    
    for i in range(sample_size):
        template_choice = templates[i % len(templates)]
        
        # Create instruction with template
        instruction = f"""Aja como um médico. Use [TRANSCRIÇÃO] para preencher o [TEMPLATE].

[TEMPLATE]
{template_choice["template"]}
[/TEMPLATE]"""
        
        # Create input with transcription
        pattern = template_choice["input_patterns"][i % len(template_choice["input_patterns"])]
        input_text = f"""[TRANSCRIÇÃO]
{pattern.format(
    name=names[i % len(names)],
    age=ages[i % len(ages)],
    gender=genders[i % len(genders)],
    complaint=complaints[i % len(complaints)],
    duration="3 dias",
    medication="losartana 50mg",
    condition="hipertensão arterial"
)}
[/TRANSCRIÇÃO]"""
        
        # Create expected output
        output = f"Registro médico processado para paciente {i+1} com sucesso."
        
        samples.append({
            "instruction": instruction,
            "input": input_text,
            "output": output
        })
    
    return Dataset.from_list(samples)


async def load_hf_dataset() -> Dataset:
    """Load dataset from Hugging Face Hub with fallback to synthetic data."""
    logger.info("Starting dataset loading process")
    
    if not HF_TOKEN:
        logger.warning("No HF_TOKEN provided, using fallback dataset")
        return create_fallback_dataset(HF_SAMPLE_SIZE)
    
    try:
        # Authenticate with Hugging Face
        logger.info("Authenticating with Hugging Face Hub")
        hf_login(token=HF_TOKEN, add_to_git_credential=False, new_session=False)
        
        # Verify dataset access
        logger.info(f"Verifying access to dataset: {HF_DATASET_ID}")
        HfApi().dataset_info(repo_id=HF_DATASET_ID, token=HF_TOKEN, revision=HF_REVISION)
        
        # Load dataset
        logger.info(f"Loading dataset: {HF_DATASET_ID}")
        kwargs = {"token": HF_TOKEN}
        if HF_REVISION:
            kwargs["revision"] = HF_REVISION
            
        ds = load_dataset(HF_DATASET_ID, split=HF_SPLIT, **kwargs)
        
        # Apply transformations
        if HF_SHUFFLE_SEED:
            logger.info(f"Shuffling dataset with seed: {HF_SHUFFLE_SEED}")
            ds = ds.shuffle(seed=int(HF_SHUFFLE_SEED))
            
        if HF_SHARD_NUM and HF_SHARD_NUM > 0:
            logger.info(f"Sharding dataset: {HF_SHARD_INDEX}/{HF_SHARD_NUM}")
            ds = ds.shard(num_shards=HF_SHARD_NUM, index=HF_SHARD_INDEX)
            
        # Sample dataset
        original_size = len(ds)
        ds = ds.select(range(min(HF_SAMPLE_SIZE, len(ds))))
        
        logger.info(f"Successfully loaded dataset: {len(ds)}/{original_size} records")
        return ds
        
    except (DatasetNotFoundError, Exception) as e:
        logger.warning(f"Failed to load HF dataset: {e}")
        logger.info("Falling back to synthetic dataset")
        return create_fallback_dataset(HF_SAMPLE_SIZE)


async def analyze_dataset_structure(dataset: Dataset) -> Dict[str, Any]:
    """Analyze the structure and content of the loaded dataset."""
    logger.info("Analyzing dataset structure")
    
    if len(dataset) == 0:
        return {"error": "Empty dataset"}
    
    # Basic statistics
    analysis = {
        "total_records": len(dataset),
        "columns": list(dataset.features.keys()),
        "sample_record": dataset[0],
        "content_analysis": {}
    }
    
    # Content analysis
    for column in analysis["columns"]:
        values = [str(row.get(column, "")) for row in dataset]
        analysis["content_analysis"][column] = {
            "avg_length": sum(len(v) for v in values) / len(values),
            "max_length": max(len(v) for v in values),
            "min_length": min(len(v) for v in values),
            "empty_count": sum(1 for v in values if not v.strip())
        }
    
    logger.info(f"Dataset analysis completed: {analysis['total_records']} records, {len(analysis['columns'])} columns")
    return analysis


async def process_records_batch_with_progress(dataset: Dataset, progress, task, batch_size: int = 5) -> List[Dict[str, Any]]:
    """Process dataset records in batches with live progress updates."""
    results = await process_records_batch(dataset, batch_size)
    
    # Update progress for each processed record
    for i in range(len(dataset)):
        progress.update(task, advance=1)
        if i % 5 == 0:  # Update every 5 records
            await asyncio.sleep(0.01)  # Allow UI update
    
    return results


async def process_records_batch(dataset: Dataset, batch_size: int = 5) -> List[Dict[str, Any]]:
    """Process dataset records in batches using direct HACS tools."""
    logger.info(f"Starting batch processing of {len(dataset)} records (batch size: {batch_size})")
    
    # Validate HACS tools availability first
    tools_status = validate_hacs_tools_availability()
    logger.info(f"HACS tools status: {tools_status}")
    
    if not all(tools_status.values()):
        logger.error("Some HACS tools are not available")
        failed_tools = [tool for tool, status in tools_status.items() if not status]
        raise RuntimeError(f"Required HACS tools unavailable: {failed_tools}")
    
    # Step 1: Register a dedicated template per row to maximize resource coverage
    logger.info("Preparing per-row template registration")
    # Robust row access (datasets can sometimes return dict or tuple-like)
    def _get(row: Any, key: str, default: str = "") -> str:
        try:
            if isinstance(row, dict):
                return str(row.get(key, default) or default)
            # datasets may return a list-like struct with features order; fallback to default
            return default
        except Exception:
            return default

    # Register an initial generic template for fallback
    first_instruction = _get(dataset[0], "instruction") if len(dataset) > 0 else ""
    fallback_template_name = "hf_direct_template_generic"
    _ = await register_template_from_instruction.ainvoke(
        {
            "instruction_md": first_instruction,
            "template_name": fallback_template_name,
            "session_id": f"direct-hacs-{int(time.time())}"
        },
        {"configurable": {"thread_id": f"reg-{int(time.time())}"}}
    )
    
    # Step 2: Process records in batches
    results = []
    total_batches = (len(dataset) + batch_size - 1) // batch_size
    
    for batch_idx in range(total_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, len(dataset))
        batch_records = dataset[start_idx:end_idx]
        
        logger.info(f"Processing batch {batch_idx + 1}/{total_batches} (records {start_idx}-{end_idx-1})")
        
        batch_results = []
        for record_idx, record in enumerate(batch_records):
            absolute_idx = start_idx + record_idx
            logger.info(f"Processing record {absolute_idx + 1}/{len(dataset)}")

            try:
                context_text = _get(record, "input")
                row_instruction = _get(record, "instruction")
                row_template_name = f"hf_row_template_{absolute_idx}"

                # Register template tailored to this row's instruction
                reg_res = await register_template_from_instruction.ainvoke(
                    {
                        "instruction_md": row_instruction or first_instruction,
                        "template_name": row_template_name,
                        "session_id": f"direct-hacs-reg-{absolute_idx}"
                    },
                    {"configurable": {"thread_id": f"reg-row-{absolute_idx}-{int(time.time())}"}}
                )
                tpl_name = reg_res.get("template_name") or row_template_name or fallback_template_name

                # Instantiate and persist stack with 5 passes to reinforce filling
                inst_result = None
                last_error = None
                for pass_idx in range(5):
                    try:
                        inst_result = await instantiate_and_persist_stack.ainvoke(
                            {
                                "template_name": tpl_name,
                                "context_text": context_text,
                                "database_url": DATABASE_URL,
                                # Force LLM usage for extraction/classification
                                "use_llm": True,
                                "session_id": f"direct-hacs-{absolute_idx}-p{pass_idx+1}"
                            },
                            {"configurable": {"thread_id": f"inst-{absolute_idx}-p{pass_idx+1}-{int(time.time())}"}}
                        )
                        # Ensure dict
                        if isinstance(inst_result, str):
                            inst_result = {"error": inst_result, "success": False}
                        # If succeeded and persisted, break
                        if inst_result.get("success"):
                            break
                        last_error = inst_result.get("error")
                    except Exception as _e:
                        last_error = str(_e)
                        continue

                # Analyze result
                hacs_result = (inst_result or {}).get("hacs_result", {})
                bundle_entries = hacs_result.get("data", {}).get("bundle_entries", 0) if isinstance(hacs_result.get("data"), dict) else 0
                grounded_extractions_count = len(hacs_result.get("data", {}).get("grounded_extractions", [])) if isinstance(hacs_result.get("data"), dict) else 0
                bundle_validation = hacs_result.get("data", {}).get("bundle_validation", {}) if isinstance(hacs_result.get("data"), dict) else {}
                
                record_result = {
                    "record_index": absolute_idx,
                    "success": bool(inst_result and inst_result.get("success", False)),
                    "persisted": (inst_result or {}).get("persisted", {}),
                    "stack_preview": (inst_result or {}).get("stack_preview", {}),
                    "extracted_variables": hacs_result.get("data", {}).get("variables") if isinstance(hacs_result.get("data"), dict) else None,
                    "bundle_entries": bundle_entries,
                    "grounded_extractions_count": grounded_extractions_count,
                    "bundle_validation": bundle_validation,
                    "error": (inst_result or {}).get("error", last_error),
                    "message": (inst_result or {}).get("message", ""),
                    "processing_timestamp": datetime.now().isoformat()
                }

                if record_result["success"]:
                    persisted_count = len([p for p in record_result["persisted"].values() if p.get("status") == "saved"])
                    bundle_count = record_result.get("bundle_entries", 0)
                    extractions_count = record_result.get("grounded_extractions_count", 0)
                    bundle_validation = record_result.get("bundle_validation", {})
                    bundle_status = bundle_validation.get("status", "unknown")
                    valid_entries = bundle_validation.get("details", {}).get("valid_entries", 0)
                    logger.info(f"Record {absolute_idx + 1} processed successfully: {persisted_count} resources persisted, bundle {bundle_status} with {valid_entries}/{bundle_count} valid entries, {extractions_count} grounded extractions")
                else:
                    logger.warning(f"Record {absolute_idx + 1} failed: {record_result['error']}")

                batch_results.append(record_result)

            except Exception as e:
                logger.error(f"Exception processing record {absolute_idx + 1}: {e}")
                batch_results.append({
                    "record_index": absolute_idx,
                    "success": False,
                    "error": str(e),
                    "processing_timestamp": datetime.now().isoformat()
                })
        
        results.extend(batch_results)
        
        # Log batch completion
        batch_success_count = sum(1 for r in batch_results if r["success"])
        logger.info(f"Batch {batch_idx + 1} completed: {batch_success_count}/{len(batch_results)} records successful")
    
    return results


async def generate_processing_report(results: List[Dict[str, Any]], dataset_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a comprehensive processing report."""
    logger.info("Generating processing report")
    
    total_records = len(results)
    successful_records = sum(1 for r in results if r["success"])
    failed_records = total_records - successful_records
    
    # Analyze persisted resources
    resource_counts = {}
    error_patterns = {}
    
    for result in results:
        if result["success"]:
            persisted = result.get("persisted", {})
            for layer_name, layer_data in persisted.items():
                if isinstance(layer_data, dict) and layer_data.get("status") == "saved":
                    resource_type = layer_data.get("resource_type", "unknown")
                    resource_counts[resource_type] = resource_counts.get(resource_type, 0) + 1
        else:
            error = result.get("error", "unknown")
            error_key = error[:100]  # Truncate for grouping
            error_patterns[error_key] = error_patterns.get(error_key, 0) + 1
    
    report = {
        "summary": {
            "total_records": total_records,
            "successful_records": successful_records,
            "failed_records": failed_records,
            "success_rate": successful_records / total_records if total_records > 0 else 0
        },
        "resource_analysis": {
            "types_created": list(resource_counts.keys()),
            "resource_counts": resource_counts,
            "total_resources": sum(resource_counts.values())
        },
        "error_analysis": {
            "unique_error_patterns": len(error_patterns),
            "error_frequency": error_patterns
        },
        "dataset_info": dataset_analysis,
        "processing_timestamp": datetime.now().isoformat()
    }
    
    logger.info(f"Report generated: {successful_records}/{total_records} records successful, {sum(resource_counts.values())} resources created")
    return report


async def main():
    """Main ingestion workflow using direct HACS tools with enhanced visualization."""
    start_time = time.time()
    
    # Initialize workflow visualizer for enhanced output
    visualizer = WorkflowVisualizer()
    
    # Enhanced startup banner
    console.print("\n" + "="*80)
    console.print("🚀 [bold blue]HF INGESTION WITH DIRECT HACS TOOLS[/bold blue]")
    console.print("="*80)
    console.print(visualizer.create_workflow_dag())
    console.print("="*80)
    
    try:
                # Step 1: Load and analyze dataset
        stage_id = visualizer.log_stage_start("📊 Dataset Loading & Analysis")
        dataset = await load_hf_dataset()
        dataset_analysis = await analyze_dataset_structure(dataset)
        
        if len(dataset) == 0:
            visualizer.log_stage_end("📊 Dataset Loading & Analysis", stage_id, False, errors=["No data to process"])
            console.print("[bold red]❌ No data to process - terminating workflow[/bold red]")
            return 1
            
        visualizer.log_stage_end("📊 Dataset Loading & Analysis", stage_id, True, resources_processed=len(dataset))

        # Step 2: Process records with live progress
        stage_id = visualizer.log_stage_start("🏥 HACS Tools Processing")
        
        # Create live progress monitor
        with visualizer.create_live_progress_monitor(len(dataset)) as progress:
            task = progress.add_task("Processing records...", total=len(dataset))
            
            # Process records with progress updates
            results = await process_records_batch_with_progress(dataset, progress, task, batch_size=3)
            
        successful_count = sum(1 for r in results if r.get("success", False))
        created_count = sum(len(r.get("persisted", {})) for r in results if r.get("success", False))
        errors = [r.get("error", "") for r in results if not r.get("success", False)]
        
        visualizer.log_stage_end("🏥 HACS Tools Processing", stage_id, True, 
                                resources_processed=len(dataset), 
                                resources_created=created_count,
                                errors=errors)

        # Step 3: Generate enhanced report
        stage_id = visualizer.log_stage_start("📋 Report Generation & Analysis")
        report = await generate_processing_report(results, dataset_analysis)
        visualizer.log_stage_end("📋 Report Generation & Analysis", stage_id, True)
        
        # Step 4: Save results
        output_file = f"hf_ingestion_direct_hacs_results_{int(time.time())}.json"
        import json
        with open(output_file, 'w') as f:
            json.dump({
                "report": report,
                "detailed_results": results
            }, f, indent=2, default=str)
        
        # Step 4: Generate comprehensive visual report
        stage_id = visualizer.log_stage_start("📊 Visual Report Generation")
        
        # Generate enhanced visual report
        report_path = visualizer.generate_workflow_report({"report": report})
        metrics_path = visualizer.export_metrics_json()
        
        visualizer.log_stage_end("📊 Visual Report Generation", stage_id, True)
        
        # Final summary with enhanced visuals
        total_time = time.time() - start_time
        success_rate = report["summary"]["success_rate"] * 100
        total_resources = report["resource_analysis"]["total_resources"]
        
        # Enhanced completion summary
        console.print("\n" + "="*80)
        console.print("🎉 [bold green]WORKFLOW COMPLETED SUCCESSFULLY![/bold green]")
        console.print("="*80)
        
        # Create final summary table
        from rich.table import Table
        summary_table = Table(title="🎯 Final Execution Summary", show_header=True, header_style="bold blue")
        summary_table.add_column("Metric", style="cyan", width=20)
        summary_table.add_column("Value", style="yellow", width=15)
        summary_table.add_column("Status", justify="center", width=10)
        
        summary_table.add_row("Total Time", f"{total_time:.2f}s", "⏱️")
        summary_table.add_row("Success Rate", f"{success_rate:.1f}%", "📈")
        summary_table.add_row("Resources Created", str(total_resources), "🏗️")
        summary_table.add_row("Records Processed", str(report["summary"]["total_records"]), "📊")
        summary_table.add_row("Successful Records", str(report["summary"]["successful_records"]), "✅")
        summary_table.add_row("Failed Records", str(report["summary"]["failed_records"]), "❌")
        
        console.print(summary_table)
        
        # Output file locations
        console.print(f"\n📁 [bold blue]Output Files:[/bold blue]")
        console.print(f"   📄 JSON Results: [cyan]{output_file}[/cyan]")
        console.print(f"   📊 Visual Report: [cyan]{report_path}[/cyan]")
        console.print(f"   📈 Metrics Data: [cyan]{metrics_path}[/cyan]")
        
        console.print("\n" + "="*80)
        
        # Sleep for log analysis as per user preference
        sleep_time = float(os.getenv("INGESTION_SLEEP", "3.0"))
        console.print(f"⏱️  [yellow]Sleeping for {sleep_time}s to allow log analysis...[/yellow]")
        time.sleep(sleep_time)
        console.print("⏰ [green]Sleep completed - workflow analysis ready![/green]")
        
        return 0
        
    except Exception as e:
        total_time = time.time() - start_time
        logger.error("="*80)
        logger.error("❌ HF INGESTION FAILED")
        logger.error(f"💥 Error: {e}")
        logger.error(f"⏱️  Total Time: {total_time:.2f}s")
        logger.error("="*80)
        
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
