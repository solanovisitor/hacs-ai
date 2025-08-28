#!/usr/bin/env python3
"""
Diagnostic script to understand why specific facades are failing.

This script performs deep analysis of facade extraction failures to identify
root causes and implement targeted fixes.
"""

import os
import asyncio
import json
from typing import Any, Dict, List, Type

# Set up environment
import dotenv
dotenv.load_dotenv()

from hacs_models.practitioner import Practitioner
from hacs_models.patient import Patient
from hacs_models.encounter import Encounter
from hacs_models.care_plan import CarePlan
from hacs_models.immunization import Immunization

from hacs_utils.integrations.openai.client import OpenAIClient
from hacs_utils.extraction.api import extract_model_facade

async def diagnose_facade_failure(
    resource_class: Type[Any], 
    facade_key: str, 
    sample_text: str
) -> Dict[str, Any]:
    """Deep diagnosis of a single facade extraction failure."""
    print(f"\n🔍 DIAGNOSING: {resource_class.__name__}.{facade_key}")
    
    # Check facade specification
    facade_spec = resource_class.get_facade_spec(facade_key)
    if facade_spec is None:
        return {"error": "No facade specification found", "facade_spec": None}
    
    print(f"  📋 Facade fields: {facade_spec.fields}")
    print(f"  🔑 Required fields: {facade_spec.required_fields}")
    
    # Check canonical defaults
    canonical_defaults = resource_class.get_canonical_defaults()
    print(f"  🏠 Canonical defaults: {canonical_defaults}")
    
    # Check required vs defaults coverage
    required_fields = facade_spec.required_fields or []
    missing_required = [f for f in required_fields if f not in canonical_defaults]
    if missing_required:
        print(f"  ⚠️  Missing required in defaults: {missing_required}")
    
    # Check extractable fields
    extractable_fields = resource_class.get_extractable_fields()
    print(f"  📤 Extractable fields: {extractable_fields}")
    
    # Attempt extraction with detailed error capture
    client = OpenAIClient(model="gpt-4o-mini")
    
    try:
        extracted = await extract_model_facade(
            client,
            resource_class,
            facade_key,
            source_text=sample_text,
            validation_rounds=1
        )
        
        if extracted is None:
            print(f"  ❌ RESULT: None returned from extraction")
            return {"error": "None result", "extracted": None}
        
        if hasattr(extracted, 'model_dump'):
            try:
                dumped = extracted.model_dump()
                print(f"  ✅ SUCCESS: Extracted {len(dumped)} fields")
                populated = {k: v for k, v in dumped.items() if v is not None and v != "" and v != []}
                print(f"  📊 Populated fields: {list(populated.keys())}")
                return {"status": "success", "extracted": dumped, "populated_fields": len(populated)}
            except Exception as e:
                print(f"  💥 SERIALIZATION ERROR: {e}")
                return {"error": "serialization_failed", "exception": str(e)}
        else:
            print(f"  ⚠️  NON-SERIALIZABLE: {type(extracted)}")
            return {"error": "not_serializable", "type": str(type(extracted))}
            
    except Exception as e:
        print(f"  💥 EXTRACTION ERROR: {e}")
        return {"error": "extraction_failed", "exception": str(e)}

async def diagnose_resource_comprehensively(resource_class: Type[Any], test_text: str):
    """Comprehensive diagnosis of all facades for a resource."""
    print(f"\n{'='*80}")
    print(f"🏥 COMPREHENSIVE DIAGNOSIS: {resource_class.__name__}")
    print(f"{'='*80}")
    
    # Get available facades
    available_facades = resource_class.list_facade_keys()
    print(f"Available facades: {available_facades}")
    
    # Check if resource has explicit facades defined
    explicit_facades = resource_class.get_facades()
    print(f"Explicit facades: {list(explicit_facades.keys()) if explicit_facades else 'None'}")
    
    # Test each facade
    results = []
    for facade_key in available_facades:
        result = await diagnose_facade_failure(resource_class, facade_key, test_text)
        results.append({
            "facade": facade_key,
            "result": result
        })
    
    return results

async def main():
    """Run comprehensive facade diagnostics."""
    print("🔧 FACADE EXTRACTION DIAGNOSTICS")
    print("=" * 80)
    
    # Focus on the most problematic resources
    problem_resources = [
        (Practitioner, "Dr. João Silva, masculino, CRM-SP 123456, ativo no sistema"),
        (Patient, "Maria Silva, 45 anos, feminino, nascida em 12/03/1979"),
        (Encounter, "Consulta ambulatorial finalizada em 15/01/2024, motivo: dor torácica"),
        (CarePlan, "Plano de cuidados para hipertensão arterial, objetivos controle pressórico"),
        (Immunization, "Vacina contra influenza aplicada em 15/03/2024, lote ABC123")
    ]
    
    all_results = {}
    
    for resource_class, test_text in problem_resources:
        results = await diagnose_resource_comprehensively(resource_class, test_text)
        all_results[resource_class.__name__] = results
    
    # Summary analysis
    print(f"\n{'='*80}")
    print("📊 DIAGNOSTIC SUMMARY")
    print(f"{'='*80}")
    
    for resource_name, results in all_results.items():
        successful = len([r for r in results if r["result"].get("status") == "success"])
        total = len(results)
        print(f"{resource_name}: {successful}/{total} facades working")
        
        # Show specific issues
        for result in results:
            if result["result"].get("error"):
                facade = result["facade"]
                error = result["result"]["error"]
                print(f"  ❌ {facade}: {error}")

if __name__ == "__main__":
    asyncio.run(main())
