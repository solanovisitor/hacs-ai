#!/usr/bin/env python3
"""
Comprehensive verification of the ResourceBundle workflow creation process.
Tests the entire pipeline from template generation to bundle validation.
"""

import sys
import os
import asyncio
import json
import logging
from typing import Dict, Any
from datetime import datetime

# Add HACS paths
hacs_paths = [
    "/Users/solanotodeschini/Code/hacs-ai/packages/hacs-models/src",
    "/Users/solanotodeschini/Code/hacs-ai/packages/hacs-core/src",
    "/Users/solanotodeschini/Code/hacs-ai/packages/hacs-tools/src",
    "/Users/solanotodeschini/Code/hacs-ai/packages/hacs-utils/src",
    "/Users/solanotodeschini/Code/hacs-ai/packages/hacs-persistence/src",
    "/Users/solanotodeschini/Code/hacs-ai/packages/hacs-registry/src",
]
for path in hacs_paths:
    if path not in sys.path:
        sys.path.insert(0, path)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import workflow functions
from workflows_direct_hacs import (
    register_template_from_instruction,
    instantiate_and_persist_stack,
    validate_hacs_tools_availability
)

# Import HACS models for validation
from hacs_models import ResourceBundle, Patient, Observation, Condition, Encounter


def validate_bundle_structure(bundle: ResourceBundle) -> Dict[str, Any]:
    """Validate the structure and content of a ResourceBundle."""
    validation_result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "summary": {},
        "details": {}
    }
    
    try:
        # Basic structure validation
        if not isinstance(bundle, ResourceBundle):
            validation_result["valid"] = False
            validation_result["errors"].append("Object is not a ResourceBundle instance")
            return validation_result
        
        # Check bundle metadata
        validation_result["details"]["bundle_id"] = bundle.id
        validation_result["details"]["bundle_title"] = bundle.title
        validation_result["details"]["bundle_type"] = bundle.bundle_type
        validation_result["details"]["entry_count"] = len(bundle.entries)
        
        # Validate entries
        if not bundle.entries:
            validation_result["warnings"].append("Bundle contains no entries")
        
        entry_details = []
        resource_types = []
        
        for i, entry in enumerate(bundle.entries):
            entry_detail = {
                "index": i,
                "title": entry.title,
                "tags": entry.tags,
                "priority": entry.priority,
                "has_resource": entry.resource is not None,
                "resource_type": None,
                "resource_id": None
            }
            
            # Validate entry has actual resource
            if entry.resource is None:
                validation_result["errors"].append(f"Entry {i} has no resource object")
                validation_result["valid"] = False
            else:
                entry_detail["resource_type"] = getattr(entry.resource, "resource_type", "Unknown")
                entry_detail["resource_id"] = getattr(entry.resource, "id", "No ID")
                resource_types.append(entry_detail["resource_type"])
                
                # Validate resource structure
                try:
                    if hasattr(entry.resource, "model_validate"):
                        entry.resource.model_validate(entry.resource.model_dump())
                except Exception as e:
                    validation_result["errors"].append(f"Entry {i} resource validation failed: {e}")
                    validation_result["valid"] = False
            
            entry_details.append(entry_detail)
        
        validation_result["details"]["entries"] = entry_details
        validation_result["details"]["resource_types"] = list(set(resource_types))
        
        # Summary statistics
        validation_result["summary"] = {
            "total_entries": len(bundle.entries),
            "entries_with_resources": sum(1 for e in bundle.entries if e.resource is not None),
            "unique_resource_types": len(set(resource_types)),
            "resource_type_distribution": {rt: resource_types.count(rt) for rt in set(resource_types)}
        }
        
        # Validate JSON serialization
        try:
            bundle_json = bundle.model_dump()
            validation_result["details"]["json_serializable"] = True
            validation_result["details"]["json_size"] = len(json.dumps(bundle_json))
        except Exception as e:
            validation_result["errors"].append(f"JSON serialization failed: {e}")
            validation_result["valid"] = False
            validation_result["details"]["json_serializable"] = False
        
    except Exception as e:
        validation_result["valid"] = False
        validation_result["errors"].append(f"Validation exception: {e}")
    
    return validation_result


async def test_template_registration(instruction: str) -> Dict[str, Any]:
    """Test template registration from instruction."""
    logger.info("🔧 Testing template registration...")
    
    template_name = f"test_template_{int(datetime.now().timestamp())}"
    
    try:
        result = await register_template_from_instruction.ainvoke(
            {
                "instruction_md": instruction,
                "template_name": template_name,
                "session_id": f"test-{template_name}"
            },
            {"configurable": {"thread_id": f"reg-{template_name}"}}
        )
        
        logger.info(f"Template registration result: {result.get('success', False)}")
        if result.get("success"):
            logger.info(f"Registered template: {result.get('template_name')}")
            template_schema = result.get("template_schema", {})
            logger.info(f"Template has {len(template_schema.get('variables', {}))} variables")
            logger.info(f"Template has {len(template_schema.get('layers', []))} layers")
        else:
            logger.error(f"Template registration failed: {result.get('message')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Template registration exception: {e}")
        return {"success": False, "error": str(e)}


async def test_stack_instantiation(template_name: str, context: str) -> Dict[str, Any]:
    """Test stack instantiation and bundle creation."""
    logger.info("🏗️ Testing stack instantiation and bundle creation...")
    
    try:
        result = await instantiate_and_persist_stack.ainvoke(
            {
                "template_name": template_name,
                "context_text": context,
                "database_url": "postgresql://test:test@localhost:5432/test",  # Mock URL for testing
                "use_llm": True,
                "session_id": f"test-inst-{template_name}"
            },
            {"configurable": {"thread_id": f"inst-{template_name}"}}
        )
        
        logger.info(f"Stack instantiation result: {result.get('success', False)}")
        if result.get("success"):
            hacs_result = result.get("hacs_result", {})
            bundle_entries = hacs_result.get("data", {}).get("bundle_entries", 0)
            grounded_extractions = hacs_result.get("data", {}).get("grounded_extractions", [])
            logger.info(f"Bundle created with {bundle_entries} entries")
            logger.info(f"Generated {len(grounded_extractions)} grounded extractions")
        else:
            logger.error(f"Stack instantiation failed: {result.get('message')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Stack instantiation exception: {e}")
        return {"success": False, "error": str(e)}


async def test_full_workflow() -> Dict[str, Any]:
    """Test the complete workflow end-to-end."""
    logger.info("🚀 Startingbundle workflow verification...")
    
    # Test data
    test_instruction = """Aja como um médico. Use [TRANSCRIÇÃO] para preencher o [TEMPLATE].

[TEMPLATE]
## Identificação do Paciente
- Nome: 
- Idade: 
- Gênero: 

## Queixa Principal


## Exame Físico
- Pressão Arterial:
- Frequência Cardíaca:
- Temperatura:

## Diagnóstico


## Plano de Tratamento
- Medicamentos:
- Orientações:
[/TEMPLATE]"""

    test_context = """[TRANSCRIÇÃO]
Paciente Maria Silva, 45 anos, sexo feminino, apresenta dor de cabeça há 3 dias.
Pressão arterial: 140/90 mmHg
Frequência cardíaca: 80 bpm
Temperatura: 36.5°C
Diagnóstico: Hipertensão arterial
Prescrição: Losartana 50mg, 1 comprimido ao dia
[/TRANSCRIÇÃO]"""

    workflow_result = {
        "success": False,
        "steps": {},
        "bundle_validation": {},
        "summary": {}
    }
    
    try:
        # Step 1: Validate tools availability
        logger.info("Step 1: Validating HACS tools availability")
        tools_status = validate_hacs_tools_availability()
        workflow_result["steps"]["tools_validation"] = tools_status
        
        if not all(tools_status.values()):
            failed_tools = [tool for tool, status in tools_status.items() if not status]
            logger.error(f"Failed tools: {failed_tools}")
            workflow_result["summary"]["error"] = f"Required tools unavailable: {failed_tools}"
            return workflow_result
        
        logger.info("✅ All required tools are available")
        
        # Step 2: Test template registration
        logger.info("Step 2: Testing template registration")
        template_result = await test_template_registration(test_instruction)
        workflow_result["steps"]["template_registration"] = template_result
        
        if not template_result.get("success"):
            logger.error("Template registration failed")
            workflow_result["summary"]["error"] = "Template registration failed"
            return workflow_result
        
        template_name = template_result.get("template_name")
        logger.info(f"✅ Template '{template_name}' registered successfully")
        
        # Step 3: Test stack instantiation and bundle creation
        logger.info("Step 3: Testing stack instantiation and bundle creation")
        instantiation_result = await test_stack_instantiation(template_name, test_context)
        workflow_result["steps"]["stack_instantiation"] = instantiation_result
        
        if not instantiation_result.get("success"):
            logger.error("Stack instantiation failed")
            workflow_result["summary"]["error"] = "Stack instantiation failed"
            return workflow_result
        
        logger.info("✅ Stack instantiation completed")
        
        # Step 4: Extract and validate the bundle
        logger.info("Step 4: Extracting and validating ResourceBundle")
        
        # We need to access the actual bundle object from the registry for validation
        # Since we can't access persistence in this test, we'll simulate bundle extraction
        from hacs_registry import get_global_registry, instantiate_registered_stack
        
        # Get template variables from the result
        hacs_result = instantiation_result.get("hacs_result", {})
        variables = hacs_result.get("data", {}).get("variables", {})
        
        # Re-instantiate to get the actual objects
        resources = instantiate_registered_stack(template_name, variables)
        logger.info(f"Re-instantiated {len(resources)} resources for validation")
        
        # Find the ResourceBundle
        bundle = None
        for layer_name, resource in resources.items():
            if getattr(resource, "resource_type", None) == "ResourceBundle":
                bundle = resource
                break
        
        if bundle is None:
            logger.error("No ResourceBundle found in instantiated resources")
            workflow_result["summary"]["error"] = "No ResourceBundle created"
            return workflow_result
        
        # Validate the bundle
        bundle_validation = validate_bundle_structure(bundle)
        workflow_result["bundle_validation"] = bundle_validation
        
        if bundle_validation["valid"]:
            logger.info("✅ ResourceBundle validation passed")
            summary = bundle_validation["summary"]
            logger.info(f"Bundle summary: {summary['total_entries']} entries, {summary['unique_resource_types']} resource types")
            for resource_type, count in summary["resource_type_distribution"].items():
                logger.info(f"  - {resource_type}: {count}")
        else:
            logger.error("❌ ResourceBundle validation failed")
            for error in bundle_validation["errors"]:
                logger.error(f"  Error: {error}")
            for warning in bundle_validation["warnings"]:
                logger.warning(f"  Warning: {warning}")
        
        # Final summary
        workflow_result["success"] = bundle_validation["valid"]
        workflow_result["summary"] = {
            "template_name": template_name,
            "bundle_valid": bundle_validation["valid"],
            "bundle_entries": bundle_validation["summary"].get("total_entries", 0),
            "resource_types": bundle_validation["details"].get("resource_types", []),
            "json_serializable": bundle_validation["details"].get("json_serializable", False)
        }
        
        logger.info("🎉 Workflow verification completed")
        return workflow_result
        
    except Exception as e:
        logger.error(f"Workflow verification failed with exception: {e}")
        workflow_result["summary"]["error"] = str(e)
        return workflow_result


def print_verification_report(result: Dict[str, Any]):
    """Print averification report."""
    print("\n" + "="*80)
    print("📋 RESOURCEBUNDLE WORKFLOW VERIFICATION REPORT")
    print("="*80)
    
    success = result.get("success", False)
    status = "✅ PASSED" if success else "❌ FAILED"
    print(f"Overall Status: {status}")
    
    summary = result.get("summary", {})
    if "error" in summary:
        print(f"Error: {summary['error']}")
    
    print(f"\n📊 Summary:")
    if "template_name" in summary:
        print(f"  Template: {summary['template_name']}")
    if "bundle_entries" in summary:
        print(f"  Bundle Entries: {summary['bundle_entries']}")
    if "resource_types" in summary:
        print(f"  Resource Types: {', '.join(summary['resource_types'])}")
    if "json_serializable" in summary:
        print(f"  JSON Serializable: {'Yes' if summary['json_serializable'] else 'No'}")
    
    # Step details
    steps = result.get("steps", {})
    print(f"\n🔧 Step Results:")
    for step_name, step_result in steps.items():
        step_success = step_result.get("success", False)
        step_status = "✅" if step_success else "❌"
        print(f"  {step_status} {step_name.replace('_', ' ').title()}")
    
    # Bundle validation details
    bundle_validation = result.get("bundle_validation", {})
    if bundle_validation:
        print(f"\n📦 Bundle Validation:")
        print(f"  Valid: {'Yes' if bundle_validation.get('valid') else 'No'}")
        
        if bundle_validation.get("errors"):
            print(f"  Errors:")
            for error in bundle_validation["errors"]:
                print(f"    - {error}")
        
        if bundle_validation.get("warnings"):
            print(f"  Warnings:")
            for warning in bundle_validation["warnings"]:
                print(f"    - {warning}")
        
        details = bundle_validation.get("details", {})
        if details:
            print(f"  Bundle ID: {details.get('bundle_id', 'N/A')}")
            print(f"  Bundle Title: {details.get('bundle_title', 'N/A')}")
            print(f"  Entry Count: {details.get('entry_count', 0)}")
            
            entries = details.get("entries", [])
            if entries:
                print(f"  Entries:")
                for entry in entries:
                    resource_status = "✅" if entry["has_resource"] else "❌"
                    print(f"    {resource_status} {entry['title']} ({entry['resource_type']})")
    
    print("="*80)


async def main():
    """Main verification function."""
    print("🔍 Starting ResourceBundle workflow verification...")
    
    try:
        result = await test_full_workflow()
        print_verification_report(result)
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = f"bundle_verification_result_{timestamp}.json"
        
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: {result_file}")
        
        return 0 if result.get("success", False) else 1
        
    except Exception as e:
        print(f"❌ Verification failed with exception: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
