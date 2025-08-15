#!/usr/bin/env python3
"""
Deep Evaluation Framework for HF Ingestion Workflow
Comprehensive logging, monitoring, and data validation at each stage.
"""

import os
import sys
import time
import json
import asyncio
import logging
import traceback
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid
import hashlib

# Setup comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hf_ingestion_evaluation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Add packages to path
sys.path.insert(0, os.path.join(os.getcwd(), "examples", "hf_ingestion"))
sys.path.insert(0, os.path.join(os.getcwd(), "packages", "hacs-models", "src"))
sys.path.insert(0, os.path.join(os.getcwd(), "packages", "hacs-core", "src"))
sys.path.insert(0, os.path.join(os.getcwd(), "packages", "hacs-tools", "src"))
sys.path.insert(0, os.path.join(os.getcwd(), "packages", "hacs-utils", "src"))
sys.path.insert(0, os.path.join(os.getcwd(), "packages", "hacs-persistence", "src"))
sys.path.insert(0, os.path.join(os.getcwd(), "packages", "hacs-registry", "src"))

@dataclass
class WorkflowStage:
    """Represents a stage in the workflow with comprehensive logging."""
    stage_name: str
    start_time: float
    end_time: Optional[float] = None
    success: bool = False
    data_in: Optional[Dict[str, Any]] = None
    data_out: Optional[Dict[str, Any]] = None
    errors: List[str] = None
    warnings: List[str] = None
    metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.metrics is None:
            self.metrics = {}
    
    @property
    def duration(self) -> Optional[float]:
        if self.end_time is not None:
            return self.end_time - self.start_time
        return None
    
    def complete(self, success: bool = True, data_out: Dict[str, Any] = None):
        """Mark stage as complete with results."""
        self.end_time = time.time()
        self.success = success
        if data_out is not None:
            self.data_out = data_out
    
    def add_error(self, error: str):
        """Add an error to this stage."""
        self.errors.append(error)
        logger.error(f"[{self.stage_name}] ERROR: {error}")
    
    def add_warning(self, warning: str):
        """Add a warning to this stage."""
        self.warnings.append(warning)
        logger.warning(f"[{self.stage_name}] WARNING: {warning}")
    
    def add_metric(self, key: str, value: Any):
        """Add a metric to this stage."""
        self.metrics[key] = value
        logger.info(f"[{self.stage_name}] METRIC: {key} = {value}")
    
    def log_progress(self, message: str):
        """Log progress message for this stage."""
        logger.info(f"[{self.stage_name}] {message}")


@dataclass 
class WorkflowEvaluation:
    """Complete evaluation results for a workflow execution."""
    workflow_id: str
    start_time: float
    end_time: Optional[float] = None
    total_records: int = 0
    processed_records: int = 0
    successful_records: int = 0
    failed_records: int = 0
    stages: List[WorkflowStage] = None
    database_metrics: Dict[str, Any] = None
    resource_metrics: Dict[str, Any] = None
    performance_metrics: Dict[str, Any] = None
    data_quality_metrics: Dict[str, Any] = None
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.stages is None:
            self.stages = []
        if self.database_metrics is None:
            self.database_metrics = {}
        if self.resource_metrics is None:
            self.resource_metrics = {}
        if self.performance_metrics is None:
            self.performance_metrics = {}
        if self.data_quality_metrics is None:
            self.data_quality_metrics = {}
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
    
    @property
    def total_duration(self) -> Optional[float]:
        if self.end_time is not None:
            return self.end_time - self.start_time
        return None
    
    @property
    def success_rate(self) -> float:
        if self.processed_records == 0:
            return 0.0
        return self.successful_records / self.processed_records
    
    def add_stage(self, stage: WorkflowStage):
        """Add a stage to the evaluation."""
        self.stages.append(stage)
    
    def get_stage(self, stage_name: str) -> Optional[WorkflowStage]:
        """Get a stage by name."""
        for stage in self.stages:
            if stage.stage_name == stage_name:
                return stage
        return None
    
    def complete(self):
        """Mark the workflow evaluation as complete."""
        self.end_time = time.time()
        
        # Calculate aggregate metrics
        self.performance_metrics = {
            "total_duration": self.total_duration,
            "avg_record_processing_time": self.total_duration / max(1, self.processed_records) if self.total_duration else 0,
            "throughput_records_per_second": self.processed_records / max(0.001, self.total_duration) if self.total_duration else 0,
            "stage_durations": {stage.stage_name: stage.duration for stage in self.stages if stage.duration}
        }
        
        self.data_quality_metrics = {
            "success_rate": self.success_rate,
            "error_rate": self.failed_records / max(1, self.processed_records),
            "total_errors": sum(len(stage.errors) for stage in self.stages),
            "total_warnings": sum(len(stage.warnings) for stage in self.stages)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "workflow_id": self.workflow_id,
            "timestamp": datetime.fromtimestamp(self.start_time).isoformat(),
            "total_duration": self.total_duration,
            "total_records": self.total_records,
            "processed_records": self.processed_records,
            "successful_records": self.successful_records,
            "failed_records": self.failed_records,
            "success_rate": self.success_rate,
            "stages": [asdict(stage) for stage in self.stages],
            "database_metrics": self.database_metrics,
            "resource_metrics": self.resource_metrics,
            "performance_metrics": self.performance_metrics,
            "data_quality_metrics": self.data_quality_metrics,
            "errors": self.errors,
            "warnings": self.warnings
        }


class HFIngestionEvaluator:
    """Comprehensive evaluator for HF ingestion workflow."""
    
    def __init__(self, evaluation_id: Optional[str] = None):
        self.evaluation_id = evaluation_id or f"eval_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        self.evaluation = WorkflowEvaluation(
            workflow_id=self.evaluation_id,
            start_time=time.time()
        )
        self.logger = logging.getLogger(f"HFIngestionEvaluator.{self.evaluation_id}")
        
        # Setup environment
        os.environ.setdefault("PYTHONPATH", ".")
        
        self.logger.info(f"Initialized HF Ingestion Evaluator: {self.evaluation_id}")
    
    def create_stage(self, stage_name: str, data_in: Dict[str, Any] = None) -> WorkflowStage:
        """Create and start a new workflow stage."""
        stage = WorkflowStage(
            stage_name=stage_name,
            start_time=time.time(),
            data_in=data_in
        )
        self.evaluation.add_stage(stage)
        stage.log_progress("Started")
        return stage
    
    async def evaluate_dataset_loading(self) -> WorkflowStage:
        """Evaluate the dataset loading stage."""
        stage = self.create_stage("dataset_loading")
        
        try:
            from datasets import load_dataset, Dataset
            from datasets.exceptions import DatasetNotFoundError
            from huggingface_hub import login as hf_login, HfApi
            
            # Configuration
            HF_TOKEN = os.getenv("HF_TOKEN")
            HF_DATASET_ID = os.getenv("HF_DATASET_ID", "voa-engines/voa-alpaca")
            HF_SPLIT = os.getenv("HF_SPLIT", "train")
            HF_SAMPLE_SIZE = int(os.getenv("HF_SAMPLE_SIZE", "5"))  # Smaller for evaluation
            
            stage.add_metric("hf_token_available", bool(HF_TOKEN))
            stage.add_metric("dataset_id", HF_DATASET_ID)
            stage.add_metric("sample_size", HF_SAMPLE_SIZE)
            
            if not HF_TOKEN:
                stage.add_warning("HF_TOKEN not available, will use fallback dataset")
            
            ds = None
            try:
                if HF_TOKEN:
                    stage.log_progress("Authenticating with Hugging Face Hub")
                    hf_login(token=HF_TOKEN, add_to_git_credential=False, new_session=False)
                    
                    stage.log_progress(f"Loading dataset: {HF_DATASET_ID}")
                    ds = load_dataset(HF_DATASET_ID, split=HF_SPLIT, token=HF_TOKEN)
                    
                    if len(ds) > HF_SAMPLE_SIZE:
                        ds = ds.select(range(HF_SAMPLE_SIZE))
                    
                    stage.add_metric("dataset_source", "huggingface_hub")
                    stage.add_metric("original_dataset_size", len(ds))
            
            except Exception as e:
                stage.add_warning(f"Failed to load HF dataset: {e}")
                ds = None
            
            # Fallback to synthetic dataset
            if ds is None:
                stage.log_progress("Creating fallback synthetic dataset")
                samples = []
                for i in range(HF_SAMPLE_SIZE):
                    samples.append({
                        "instruction": f"[TEMPLATE]\n## Identificação do Paciente\n- Nome: \n- Idade: \n- Gênero: \n\n## Queixa Principal\n\n## História Atual\n[/TEMPLATE]",
                        "input": f"[TRANSCRIÇÃO]\nPaciente {i+1} relata dor de cabeça há 3 dias. Idade 35 anos, sexo feminino.\n[/TRANSCRIÇÃO]",
                        "output": f"Registro médico processado para paciente {i+1}"
                    })
                ds = Dataset.from_list(samples)
                stage.add_metric("dataset_source", "synthetic_fallback")
            
            # Analyze dataset structure
            if ds and len(ds) > 0:
                first_row = ds[0]
                stage.add_metric("dataset_columns", list(first_row.keys()))
                stage.add_metric("final_dataset_size", len(ds))
                
                # Analyze content patterns
                instruction_lengths = [len(str(row.get("instruction", ""))) for row in ds]
                input_lengths = [len(str(row.get("input", ""))) for row in ds]
                
                stage.add_metric("avg_instruction_length", sum(instruction_lengths) / len(instruction_lengths))
                stage.add_metric("avg_input_length", sum(input_lengths) / len(input_lengths))
                stage.add_metric("max_instruction_length", max(instruction_lengths))
                stage.add_metric("max_input_length", max(input_lengths))
            
            stage.complete(True, {"dataset": ds, "dataset_size": len(ds) if ds else 0})
            
        except Exception as e:
            stage.add_error(f"Dataset loading failed: {e}")
            stage.complete(False)
        
        return stage
    
    async def evaluate_template_registration(self, dataset) -> WorkflowStage:
        """Evaluate template registration from instruction."""
        stage = self.create_stage("template_registration")
        
        try:
            from workflows import register_template_from_instruction
            
            if not dataset or len(dataset) == 0:
                stage.add_error("No dataset available for template registration")
                stage.complete(False)
                return stage
            
            first_instruction = dataset[0].get("instruction", "")
            stage.add_metric("instruction_length", len(first_instruction))
            
            # Check for template markers
            has_template_tags = "[TEMPLATE]" in first_instruction and "[/TEMPLATE]" in first_instruction
            stage.add_metric("has_template_tags", has_template_tags)
            
            if not has_template_tags:
                stage.add_warning("No [TEMPLATE] tags found in instruction")
            
            stage.log_progress("Registering template from instruction")
            
            # Register template using LangGraph workflow
            reg_result = await register_template_from_instruction.ainvoke(
                {
                    "instruction_md": first_instruction,
                    "template_name": f"eval_template_{self.evaluation_id}",
                    "session_id": f"eval_{self.evaluation_id}"
                },
                {"configurable": {"thread_id": f"eval-reg-{uuid.uuid4()}"}}
            )
            
            stage.add_metric("template_name", reg_result.get("template_name"))
            stage.add_metric("discovered_resources", len(reg_result.get("discovered_resources", [])))
            stage.add_metric("schemas_count", len(reg_result.get("schemas_by_type", {})))
            
            # Analyze template structure
            template_schema = reg_result.get("template_schema", {})
            if template_schema:
                variables = template_schema.get("variables", {})
                layers = template_schema.get("layers", [])
                
                stage.add_metric("template_variables_count", len(variables))
                stage.add_metric("template_layers_count", len(layers))
                stage.add_metric("variable_types", list(variables.keys()) if variables else [])
                stage.add_metric("layer_resource_types", [layer.get("resource_type") for layer in layers])
            
            success = reg_result.get("template_name") is not None
            stage.complete(success, reg_result)
            
        except Exception as e:
            stage.add_error(f"Template registration failed: {e}")
            stage.add_error(f"Traceback: {traceback.format_exc()}")
            stage.complete(False)
        
        return stage
    
    async def evaluate_data_processing(self, dataset, template_name: str) -> WorkflowStage:
        """Evaluate data processing for each record."""
        stage = self.create_stage("data_processing")
        
        try:
            from workflows import instantiate_and_persist_stack
            
            if not template_name:
                stage.add_error("No template name available for processing")
                stage.complete(False)
                return stage
            
            stage.add_metric("template_name", template_name)
            stage.add_metric("records_to_process", len(dataset))
            
            processed_records = []
            successful_records = 0
            failed_records = 0
            processing_times = []
            
            for i, row in enumerate(dataset):
                record_start = time.time()
                stage.log_progress(f"Processing record {i+1}/{len(dataset)}")
                
                try:
                    context_text = row.get("input", "")
                    
                    # Analyze input structure
                    has_transcription = "[TRANSCRIÇÃO]" in context_text or "[TRANSCRICAO]" in context_text
                    
                    inst_result = await instantiate_and_persist_stack.ainvoke(
                        {
                            "template_name": template_name,
                            "context_text": context_text,
                            "database_url": os.getenv("DATABASE_URL", "postgresql://hacs:hacs_dev@localhost:5432/hacs"),
                            "use_llm": False,  # Disable LLM for consistent evaluation
                            "session_id": f"eval_{self.evaluation_id}_{i}"
                        },
                        {"configurable": {"thread_id": f"eval-inst-{i}-{uuid.uuid4()}"}}
                    )
                    
                    record_duration = time.time() - record_start
                    processing_times.append(record_duration)
                    
                    # Analyze results
                    persisted = inst_result.get("persisted", {})
                    layers = inst_result.get("layers", [])
                    stack_preview = inst_result.get("stack_preview", {})
                    
                    record_success = not inst_result.get("error") and persisted
                    
                    record_data = {
                        "record_index": i,
                        "success": record_success,
                        "processing_time": record_duration,
                        "persisted_count": len(persisted) if persisted else 0,
                        "layers_count": len(layers),
                        "stack_resources": list(stack_preview.keys()) if stack_preview else [],
                        "has_transcription_tags": has_transcription,
                        "context_length": len(context_text),
                        "error": inst_result.get("error")
                    }
                    
                    processed_records.append(record_data)
                    
                    if record_success:
                        successful_records += 1
                    else:
                        failed_records += 1
                        stage.add_warning(f"Record {i} failed: {inst_result.get('error', 'Unknown error')}")
                
                except Exception as e:
                    record_duration = time.time() - record_start
                    processing_times.append(record_duration)
                    failed_records += 1
                    
                    error_msg = f"Record {i} processing error: {e}"
                    stage.add_error(error_msg)
                    
                    processed_records.append({
                        "record_index": i,
                        "success": False,
                        "processing_time": record_duration,
                        "error": str(e)
                    })
            
            # Calculate aggregate metrics
            stage.add_metric("total_processed", len(processed_records))
            stage.add_metric("successful_records", successful_records)
            stage.add_metric("failed_records", failed_records)
            stage.add_metric("success_rate", successful_records / len(processed_records) if processed_records else 0)
            
            if processing_times:
                stage.add_metric("avg_processing_time", sum(processing_times) / len(processing_times))
                stage.add_metric("min_processing_time", min(processing_times))
                stage.add_metric("max_processing_time", max(processing_times))
                stage.add_metric("total_processing_time", sum(processing_times))
            
            # Update evaluation totals
            self.evaluation.total_records = len(dataset)
            self.evaluation.processed_records = len(processed_records)
            self.evaluation.successful_records = successful_records
            self.evaluation.failed_records = failed_records
            
            stage.complete(
                successful_records > 0,
                {"processed_records": processed_records, "processing_times": processing_times}
            )
            
        except Exception as e:
            stage.add_error(f"Data processing evaluation failed: {e}")
            stage.add_error(f"Traceback: {traceback.format_exc()}")
            stage.complete(False)
        
        return stage
    
    async def evaluate_database_state(self) -> WorkflowStage:
        """Evaluate database state and persistence."""
        stage = self.create_stage("database_evaluation")
        
        try:
            from hacs_persistence.adapter import PostgreSQLAdapter
            from hacs_core import Actor
            
            database_url = os.getenv("DATABASE_URL", "postgresql://hacs:hacs_dev@localhost:5432/hacs")
            stage.add_metric("database_url", database_url.split("@")[-1] if "@" in database_url else "mock")
            
            try:
                # Test database connection
                adapter = PostgreSQLAdapter(database_url)
                actor = Actor(id="evaluator", name="Database Evaluator", role="system")
                
                stage.log_progress("Testing database connectivity")
                
                # Test basic operations
                from hacs_models import Patient
                test_patient = Patient(
                    full_name="DB Test Patient",
                    gender="other",
                    agent_context={"evaluation_id": self.evaluation_id, "test": "connectivity"}
                )
                
                # Try to save a test record
                conn_start = time.time()
                saved_patient = await adapter.save(test_patient, actor)
                conn_duration = time.time() - conn_start
                
                stage.add_metric("database_connected", True)
                stage.add_metric("test_save_duration", conn_duration)
                stage.add_metric("test_record_id", saved_patient.id if saved_patient else None)
                
                # Query evaluation records (if any exist)
                # Note: This would require implementing query functionality in the adapter
                stage.add_metric("database_type", "postgresql")
                
            except Exception as e:
                stage.add_warning(f"Database connection failed, using mock: {e}")
                stage.add_metric("database_connected", False)
                stage.add_metric("database_type", "mock")
            
            stage.complete(True)
            
        except Exception as e:
            stage.add_error(f"Database evaluation failed: {e}")
            stage.complete(False)
        
        return stage
    
    async def evaluate_resource_validation(self, processed_data: List[Dict[str, Any]]) -> WorkflowStage:
        """Evaluate the quality and validity of generated resources."""
        stage = self.create_stage("resource_validation")
        
        try:
            if not processed_data:
                stage.add_warning("No processed data available for resource validation")
                stage.complete(True)
                return stage
            
            validation_results = {
                "total_records": len(processed_data),
                "records_with_resources": 0,
                "resource_type_counts": {},
                "validation_errors": [],
                "data_quality_issues": []
            }
            
            for record in processed_data:
                if record.get("success") and record.get("stack_resources"):
                    validation_results["records_with_resources"] += 1
                    
                    for resource_type in record["stack_resources"]:
                        validation_results["resource_type_counts"][resource_type] = (
                            validation_results["resource_type_counts"].get(resource_type, 0) + 1
                        )
                
                # Check for quality issues
                if record.get("context_length", 0) == 0:
                    validation_results["data_quality_issues"].append(f"Record {record.get('record_index')}: Empty context")
                
                if record.get("processing_time", 0) > 10:  # Long processing time
                    validation_results["data_quality_issues"].append(f"Record {record.get('record_index')}: Long processing time ({record.get('processing_time'):.2f}s)")
            
            # Calculate resource distribution
            total_resources = sum(validation_results["resource_type_counts"].values())
            resource_distribution = {
                rt: count / total_resources if total_resources > 0 else 0
                for rt, count in validation_results["resource_type_counts"].items()
            }
            
            stage.add_metric("records_with_resources", validation_results["records_with_resources"])
            stage.add_metric("resource_type_counts", validation_results["resource_type_counts"])
            stage.add_metric("resource_distribution", resource_distribution)
            stage.add_metric("data_quality_issues_count", len(validation_results["data_quality_issues"]))
            
            # Log quality issues
            for issue in validation_results["data_quality_issues"][:10]:  # Limit to first 10
                stage.add_warning(issue)
            
            self.evaluation.resource_metrics = validation_results
            
            stage.complete(True, validation_results)
            
        except Exception as e:
            stage.add_error(f"Resource validation failed: {e}")
            stage.complete(False)
        
        return stage
    
    async def run_full_evaluation(self) -> WorkflowEvaluation:
        """Run the complete evaluation workflow."""
        self.logger.info(f"Starting full HF ingestion evaluation: {self.evaluation_id}")
        
        try:
            # Stage 1: Dataset Loading
            dataset_stage = await self.evaluate_dataset_loading()
            dataset = dataset_stage.data_out.get("dataset") if dataset_stage.data_out else None
            
            if not dataset:
                self.evaluation.errors.append("Failed to load dataset - cannot continue evaluation")
                self.evaluation.complete()
                return self.evaluation
            
            # Stage 2: Template Registration  
            template_stage = await self.evaluate_template_registration(dataset)
            template_name = template_stage.data_out.get("template_name") if template_stage.data_out else None
            
            if not template_name:
                self.evaluation.errors.append("Failed to register template - cannot continue evaluation")
                self.evaluation.complete()
                return self.evaluation
            
            # Stage 3: Data Processing
            processing_stage = await self.evaluate_data_processing(dataset, template_name)
            processed_data = processing_stage.data_out.get("processed_records", []) if processing_stage.data_out else []
            
            # Stage 4: Database State
            await self.evaluate_database_state()
            
            # Stage 5: Resource Validation
            await self.evaluate_resource_validation(processed_data)
            
            self.evaluation.complete()
            self.logger.info(f"Evaluation completed: {self.evaluation_id}")
            
        except Exception as e:
            self.evaluation.errors.append(f"Evaluation failed: {e}")
            self.evaluation.errors.append(f"Traceback: {traceback.format_exc()}")
            self.evaluation.complete()
            self.logger.error(f"Evaluation failed: {e}")
        
        return self.evaluation


async def main():
    """Main evaluation runner."""
    print("🔍 HF Ingestion Workflow Deep Evaluation")
    print("="*60)
    
    # Create evaluator
    evaluator = HFIngestionEvaluator()
    
    try:
        # Run evaluation
        results = await evaluator.run_full_evaluation()
        
        # Print summary
        print(f"\n📊 EVALUATION SUMMARY - {results.workflow_id}")
        print("="*60)
        print(f"Total Duration: {results.total_duration:.2f}s")
        print(f"Records Processed: {results.processed_records}/{results.total_records}")
        print(f"Success Rate: {results.success_rate:.1%}")
        print(f"Stages Completed: {len([s for s in results.stages if s.success])}/{len(results.stages)}")
        
        if results.performance_metrics:
            print(f"\n⚡ PERFORMANCE METRICS:")
            for key, value in results.performance_metrics.items():
                if isinstance(value, dict):
                    print(f"  {key}:")
                    for k, v in value.items():
                        print(f"    {k}: {v}")
                else:
                    print(f"  {key}: {value}")
        
        if results.data_quality_metrics:
            print(f"\n📈 DATA QUALITY METRICS:")
            for key, value in results.data_quality_metrics.items():
                print(f"  {key}: {value}")
        
        # Stage-by-stage analysis
        print(f"\n🔄 STAGE ANALYSIS:")
        for stage in results.stages:
            status = "✅ PASSED" if stage.success else "❌ FAILED"
            duration = f"{stage.duration:.2f}s" if stage.duration else "N/A"
            print(f"  {stage.stage_name}: {status} ({duration})")
            
            if stage.errors:
                for error in stage.errors[:3]:  # Show first 3 errors
                    print(f"    ERROR: {error}")
            
            if stage.warnings:
                for warning in stage.warnings[:3]:  # Show first 3 warnings
                    print(f"    WARNING: {warning}")
        
        # Resource analysis
        if results.resource_metrics:
            print(f"\n🏥 RESOURCE ANALYSIS:")
            resource_counts = results.resource_metrics.get("resource_type_counts", {})
            for resource_type, count in resource_counts.items():
                print(f"  {resource_type}: {count} instances")
        
        # Save detailed results
        output_file = f"hf_ingestion_evaluation_{results.workflow_id}.json"
        with open(output_file, 'w') as f:
            json.dump(results.to_dict(), f, indent=2)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        
        # Sleep for log analysis as requested
        sleep_time = float(os.getenv("EVALUATION_SLEEP", "3.0"))
        print(f"\n⏱️  Sleeping for {sleep_time}s to allow log analysis...")
        time.sleep(sleep_time)
        print("⏰ Sleep completed")
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
