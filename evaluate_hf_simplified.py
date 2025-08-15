#!/usr/bin/env python3
"""
Simplified HF Ingestion Evaluation - bypasses MCP dependencies
Focuses on core data transformation and persistence logic.
"""

import os
import sys
import time
import json
import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add packages to path
packages = ["hacs-models", "hacs-core", "hacs-tools", "hacs-utils", "hacs-persistence", "hacs-registry"]
for pkg in packages:
    pkg_path = os.path.join(os.getcwd(), "packages", pkg, "src")
    if os.path.exists(pkg_path) and pkg_path not in sys.path:
        sys.path.insert(0, pkg_path)

sys.path.insert(0, os.path.join(os.getcwd(), "examples", "hf_ingestion"))


async def evaluate_core_workflow():
    """Evaluate the core HF ingestion workflow without MCP dependencies."""
    print("🔍 Simplified HF Ingestion Workflow Evaluation")
    print("="*70)
    
    evaluation_start = time.time()
    evaluation_id = f"simplified_eval_{int(time.time())}"
    
    # Stage 1: Import and Setup
    print("\n📦 Stage 1: Import and Setup")
    stage_start = time.time()
    
    try:
        # Import HF ingestion modules
        import ingest_voa_alpaca
        from datasets import Dataset
        
        print(f"✅ Successfully imported HF ingestion modules")
        print(f"   Duration: {time.time() - stage_start:.3f}s")
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return
    
    # Stage 2: Dataset Creation (Synthetic)
    print("\n📊 Stage 2: Dataset Creation")
    stage_start = time.time()
    
    try:
        # Create synthetic dataset matching voa-alpaca structure
        synthetic_data = [
            {
                "instruction": """Aja como um médico. Use [TRANSCRIÇÃO] para preencher o [TEMPLATE].

[TEMPLATE]
## Identificação do Paciente
- Nome: 
- Idade: 
- Gênero: 

## Queixa Principal


## História da Doença Atual


## Exame Físico


## Diagnóstico


## Plano de Tratamento
[/TEMPLATE]""",
                "input": """[TRANSCRIÇÃO]
Paciente Maria Silva, 35 anos, sexo feminino, comparece ao consultório com queixa de dor de cabeça há 3 dias. Refere dor pulsátil em região temporal bilateral, intensidade 7/10, sem fatores de melhora ou piora identificados. Nega febre, náuseas ou vômitos. Ao exame físico: PA 130/80 mmHg, FC 72 bpm, afebril. Exame neurológico sumário normal.
[/TRANSCRIÇÃO]""",
                "output": "Registro médico processado com diagnóstico de cefaleia tensional e prescrição de analgésicos."
            },
            {
                "instruction": """Aja como um médico. Use [TRANSCRIÇÃO] para preencher o [TEMPLATE].

[TEMPLATE]
## Identificação do Paciente
- Nome: 
- Idade: 
- Gênero: 

## Queixa Principal


## História da Doença Atual


## Medicamentos em Uso


## Diagnóstico
[/TEMPLATE]""",
                "input": """[TRANSCRIÇÃO]
João Santos, 45 anos, masculino, hipertenso há 5 anos, em uso de losartana 50mg 1x/dia. Comparece para consulta de rotina. Refere aderência ao tratamento. PA atual 125/75 mmHg. Sem queixas no momento.
[/TRANSCRIÇÃO]""",
                "output": "Controle adequado da hipertensão arterial, manter medicação atual."
            },
            {
                "instruction": """Use [CONTEXTO] para criar relatório médico.

[TEMPLATE]
## Dados do Paciente
- Nome:
- Idade:

## Anotações Clínicas


## Observações
[/TEMPLATE]""",
                "input": """[CONTEXTO]
Ana Costa, 28 anos, grávida de 32 semanas. Consulta de pré-natal. Peso 68kg, ganho de peso adequado. PA 110/70 mmHg. Feto com movimentos ativos, BCF 145 bpm. Exames laboratoriais dentro da normalidade.
[/CONTEXTO]""",
                "output": "Gestação de baixo risco, evolução adequada."
            }
        ]
        
        dataset = Dataset.from_list(synthetic_data)
        
        print(f"✅ Created synthetic dataset with {len(dataset)} records")
        print(f"   Columns: {list(dataset.features.keys())}")
        print(f"   Duration: {time.time() - stage_start:.3f}s")
        
        # Analyze dataset structure
        avg_instruction_len = sum(len(row["instruction"]) for row in dataset) / len(dataset)
        avg_input_len = sum(len(row["input"]) for row in dataset) / len(dataset)
        
        print(f"   Avg instruction length: {avg_instruction_len:.0f} chars")
        print(f"   Avg input length: {avg_input_len:.0f} chars")
        
    except Exception as e:
        print(f"❌ Dataset creation failed: {e}")
        return
    
    # Stage 3: Template Generation and Registration
    print("\n🏗️  Stage 3: Template Generation")
    stage_start = time.time()
    
    template_results = []
    
    for i, row in enumerate(dataset):
        print(f"\n   Processing record {i+1}/{len(dataset)}")
        record_start = time.time()
        
        try:
            # Use the local template generation function
            template = ingest_voa_alpaca.generate_stack_template_from_markdown(
                row["instruction"]
            )
            
            record_duration = time.time() - record_start
            
            template_info = {
                "record_index": i,
                "template_name": template.name,
                "template_version": template.version,
                "variables_count": len(template.variables),
                "layers_count": len(template.layers),
                "layer_types": [layer.resource_type for layer in template.layers],
                "generation_time": record_duration,
                "success": True
            }
            
            template_results.append(template_info)
            print(f"   ✅ Template '{template.name}' generated in {record_duration:.3f}s")
            print(f"      Variables: {len(template.variables)}, Layers: {len(template.layers)}")
            print(f"      Layer types: {', '.join(template_info['layer_types'])}")
            
        except Exception as e:
            record_duration = time.time() - record_start
            template_info = {
                "record_index": i,
                "generation_time": record_duration,
                "success": False,
                "error": str(e)
            }
            template_results.append(template_info)
            print(f"   ❌ Template generation failed in {record_duration:.3f}s: {e}")
    
    total_template_time = time.time() - stage_start
    successful_templates = sum(1 for r in template_results if r["success"])
    
    print(f"\n📊 Template Generation Summary:")
    print(f"   Total time: {total_template_time:.3f}s")
    print(f"   Success rate: {successful_templates}/{len(template_results)} ({successful_templates/len(template_results)*100:.1f}%)")
    print(f"   Avg time per template: {total_template_time/len(template_results):.3f}s")
    
    # Stage 4: Stack Building and Resource Creation
    print("\n🏥 Stage 4: Stack Building and Resource Creation")
    stage_start = time.time()
    
    stack_results = []
    
    for i, row in enumerate(dataset):
        print(f"\n   Building stack for record {i+1}/{len(dataset)}")
        record_start = time.time()
        
        try:
            # Build stack from row using the HF ingestion logic
            stack = ingest_voa_alpaca.build_stack_from_row(row)
            
            record_duration = time.time() - record_start
            
            # Analyze the created stack
            stack_info = {
                "record_index": i,
                "stack_size": len(stack),
                "resource_types": {layer: type(resource).__name__ for layer, resource in stack.items()},
                "resource_ids": {layer: getattr(resource, 'id', 'unknown') for layer, resource in stack.items()},
                "creation_time": record_duration,
                "success": True
            }
            
            # Detailed resource analysis
            for layer_name, resource in stack.items():
                print(f"     📋 {layer_name}: {type(resource).__name__}")
                print(f"        ID: {getattr(resource, 'id', 'N/A')}")
                
                # Check key fields
                if hasattr(resource, 'resource_type'):
                    print(f"        Type: {resource.resource_type}")
                
                if hasattr(resource, 'agent_context') and resource.agent_context:
                    context_keys = list(resource.agent_context.keys())[:3]  # Show first 3 keys
                    print(f"        Context keys: {context_keys}")
                
                # Check specific field content for validation
                if type(resource).__name__ == 'Patient':
                    print(f"        Name: {getattr(resource, 'full_name', 'N/A')}")
                    print(f"        Gender: {getattr(resource, 'gender', 'N/A')}")
                elif type(resource).__name__ == 'Observation':
                    print(f"        Status: {getattr(resource, 'status', 'N/A')}")
                    print(f"        Value: {getattr(resource, 'value_string', 'N/A')[:50]}...")
            
            stack_results.append(stack_info)
            print(f"   ✅ Stack built in {record_duration:.3f}s")
            
        except Exception as e:
            record_duration = time.time() - record_start
            stack_info = {
                "record_index": i,
                "creation_time": record_duration,
                "success": False,
                "error": str(e)
            }
            stack_results.append(stack_info)
            print(f"   ❌ Stack building failed in {record_duration:.3f}s: {e}")
    
    total_stack_time = time.time() - stage_start
    successful_stacks = sum(1 for r in stack_results if r["success"])
    
    print(f"\n📊 Stack Building Summary:")
    print(f"   Total time: {total_stack_time:.3f}s")
    print(f"   Success rate: {successful_stacks}/{len(stack_results)} ({successful_stacks/len(stack_results)*100:.1f}%)")
    print(f"   Avg time per stack: {total_stack_time/len(stack_results):.3f}s")
    
    # Stage 5: Data Quality Analysis
    print("\n🔍 Stage 5: Data Quality Analysis")
    stage_start = time.time()
    
    quality_metrics = {
        "empty_resources": 0,
        "missing_required_fields": 0,
        "agent_context_usage": 0,
        "resource_type_distribution": {},
        "field_completeness": {},
        "data_consistency_issues": []
    }
    
    for stack_result in stack_results:
        if not stack_result["success"]:
            continue
            
        # Analyze resource type distribution
        for resource_type in stack_result["resource_types"].values():
            quality_metrics["resource_type_distribution"][resource_type] = (
                quality_metrics["resource_type_distribution"].get(resource_type, 0) + 1
            )
    
    # Simulate database persistence analysis
    print(f"\n   🗃️  Database Persistence Simulation")
    persistence_start = time.time()
    
    try:
        from hacs_persistence.adapter import PostgreSQLAdapter
        from hacs_core import Actor
        
        database_url = os.getenv("DATABASE_URL", "postgresql://hacs:hacs_dev@localhost:5432/hacs")
        adapter = PostgreSQLAdapter(database_url)
        actor = Actor(id="evaluator", name="HF Ingestion Evaluator", role="system")
        
        print(f"   ✅ Database adapter initialized")
        
        # Test persistence with one sample resource
        from hacs_models import Patient
        test_patient = Patient(
            full_name="HF Evaluation Test Patient",
            gender="other",
            agent_context={"evaluation_id": evaluation_id, "test": "persistence"}
        )
        
        saved_patient = await adapter.save(test_patient, actor)
        persistence_duration = time.time() - persistence_start
        
        print(f"   ✅ Test persistence completed in {persistence_duration:.3f}s")
        print(f"      Saved patient ID: {saved_patient.id}")
        
        quality_metrics["database_persistence"] = {
            "connection_successful": True,
            "test_save_duration": persistence_duration,
            "test_record_id": saved_patient.id
        }
        
    except Exception as e:
        persistence_duration = time.time() - persistence_start
        print(f"   ❌ Database persistence test failed: {e}")
        quality_metrics["database_persistence"] = {
            "connection_successful": False,
            "error": str(e),
            "test_duration": persistence_duration
        }
    
    quality_analysis_time = time.time() - stage_start
    
    print(f"\n📊 Data Quality Summary:")
    print(f"   Analysis time: {quality_analysis_time:.3f}s")
    print(f"   Resource type distribution:")
    for rt, count in quality_metrics["resource_type_distribution"].items():
        print(f"     {rt}: {count} instances")
    
    # Stage 6: Overall Evaluation Summary
    print("\n🎯 Overall Evaluation Summary")
    
    total_evaluation_time = time.time() - evaluation_start
    
    summary = {
        "evaluation_id": evaluation_id,
        "timestamp": datetime.now().isoformat(),
        "total_duration": total_evaluation_time,
        "stages": {
            "template_generation": {
                "success_rate": successful_templates / len(template_results),
                "avg_time": total_template_time / len(template_results),
                "total_time": total_template_time
            },
            "stack_building": {
                "success_rate": successful_stacks / len(stack_results),
                "avg_time": total_stack_time / len(stack_results),
                "total_time": total_stack_time
            },
            "quality_analysis": {
                "duration": quality_analysis_time
            }
        },
        "data_metrics": {
            "records_processed": len(dataset),
            "templates_generated": successful_templates,
            "stacks_created": successful_stacks,
            "resource_types": quality_metrics["resource_type_distribution"]
        },
        "performance_metrics": {
            "throughput_records_per_second": len(dataset) / total_evaluation_time,
            "avg_template_time": total_template_time / len(template_results),
            "avg_stack_time": total_stack_time / len(stack_results)
        },
        "quality_metrics": quality_metrics
    }
    
    print(f"="*70)
    print(f"✅ EVALUATION COMPLETED")
    print(f"   Total Duration: {total_evaluation_time:.2f}s")
    print(f"   Records Processed: {len(dataset)}")
    print(f"   Overall Success Rate: {min(successful_templates, successful_stacks) / len(dataset) * 100:.1f}%")
    print(f"   Throughput: {len(dataset) / total_evaluation_time:.2f} records/second")
    print(f"="*70)
    
    # Export results
    output_file = f"hf_simplified_evaluation_{evaluation_id}.json"
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {output_file}")
    
    # Sleep for log analysis
    sleep_time = float(os.getenv("EVALUATION_SLEEP", "2.0"))
    print(f"\n⏱️  Sleeping for {sleep_time}s to allow log analysis...")
    time.sleep(sleep_time)
    print("⏰ Sleep completed")


if __name__ == "__main__":
    asyncio.run(evaluate_core_workflow())
