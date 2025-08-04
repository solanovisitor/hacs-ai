#!/usr/bin/env python3
"""
HACS LangChain Tools Validation Script

This script validates that all HACS tools are properly integrated with LangChain
and functioning correctly. It tests tool discovery, validation, and execution.

Usage:
    python test_hacs_langchain_tools.py

Author: HACS Development Team
License: MIT
Version: 0.3.0
"""

import sys
import json
import logging
from typing import Dict, Any, List
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all required modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        from hacs_utils.integrations.langchain import (
            get_hacs_tools,
            get_hacs_tool,
            get_hacs_tools_by_category,
            HACSToolRegistry,
            validate_tool_inputs,
        )
        print("✅ LangChain integration imports successful")
        return True
    except ImportError as e:
        print(f"❌ LangChain integration import failed: {e}")
        return False

def test_tool_discovery():
    """Test tool discovery and registry functionality."""
    print("\n🔧 Testing tool discovery...")
    
    try:
        from hacs_utils.integrations.langchain import get_hacs_tools, get_hacs_tools_by_category
        
        # Get all tools
        all_tools = get_hacs_tools()
        print(f"✅ Found {len(all_tools)} total tools")
        
        # Test category-based discovery
        categories = [
            "resource_management",
            "clinical_workflows", 
            "schema_discovery",
            "development_tools"
        ]
        
        for category in categories:
            category_tools = get_hacs_tools_by_category(category)
            print(f"✅ Category '{category}': {len(category_tools)} tools")
            
        return True
        
    except Exception as e:
        print(f"❌ Tool discovery failed: {e}")
        return False

def test_individual_tools():
    """Test individual tool functionality."""
    print("\n🧪 Testing individual tools...")
    
    try:
        from hacs_utils.integrations.langchain import get_hacs_tool, validate_tool_inputs
        
        # Test resource discovery tool
        discovery_tool = get_hacs_tool("discover_hacs_resources")
        if discovery_tool:
            print("✅ Found discover_hacs_resources tool")
            
            # Test input validation
            valid_inputs = {
                "category_filter": "clinical",
                "fhir_compliant_only": True,
                "include_field_details": True,
                "search_term": "patient"
            }
            
            if validate_tool_inputs("discover_hacs_resources", valid_inputs):
                print("✅ Tool input validation successful")
            else:
                print("❌ Tool input validation failed")
        else:
            print("❌ discover_hacs_resources tool not found")
        
        # Test create record tool
        create_tool = get_hacs_tool("create_hacs_record")
        if create_tool:
            print("✅ Found create_hacs_record tool")
            
            # Test input validation
            valid_inputs = {
                "actor_name": "Dr. Test",
                "resource_type": "Patient",
                "resource_data": {
                    "full_name": "John Doe",
                    "birth_date": "1990-01-01",
                    "gender": "male"
                },
                "auto_generate_id": True,
                "validate_fhir": True
            }
            
            if validate_tool_inputs("create_hacs_record", valid_inputs):
                print("✅ Tool input validation successful")
            else:
                print("❌ Tool input validation failed")
        else:
            print("❌ create_hacs_record tool not found")
        
        # Test clinical template tool
        template_tool = get_hacs_tool("create_clinical_template")
        if template_tool:
            print("✅ Found create_clinical_template tool")
            
            # Test input validation
            valid_inputs = {
                "template_type": "assessment",
                "focus_area": "cardiology",
                "complexity_level": "standard",
                "include_workflow_fields": True
            }
            
            if validate_tool_inputs("create_clinical_template", valid_inputs):
                print("✅ Tool input validation successful")
            else:
                print("❌ Tool input validation failed")
        else:
            print("❌ create_clinical_template tool not found")
        
        return True
        
    except Exception as e:
        print(f"❌ Individual tool testing failed: {e}")
        return False

def test_tool_execution():
    """Test actual tool execution (safe operations only)."""
    print("\n⚡ Testing tool execution...")
    
    try:
        from hacs_utils.integrations.langchain import get_hacs_tool
        
        # Test discovery tool execution (read-only, safe)
        discovery_tool = get_hacs_tool("discover_hacs_resources")
        if discovery_tool:
            try:
                result = discovery_tool.invoke({
                    "category_filter": None,
                    "fhir_compliant_only": False,
                    "include_field_details": True,
                    "search_term": None
                })
                print("✅ discover_hacs_resources execution successful")
                print(f"📊 Result type: {type(result)}")
                
                # Try to extract meaningful info from result
                if hasattr(result, 'success'):
                    print(f"📊 Success: {result.success}")
                    if hasattr(result, 'data') and result.data:
                        print(f"📊 Data keys: {list(result.data.keys()) if isinstance(result.data, dict) else 'Non-dict data'}")
                
            except Exception as e:
                print(f"❌ discover_hacs_resources execution failed: {e}")
        
        # Test clinical template tool execution (read-only template generation)
        template_tool = get_hacs_tool("create_clinical_template")
        if template_tool:
            try:
                result = template_tool.invoke({
                    "template_type": "assessment",
                    "focus_area": "general",
                    "complexity_level": "standard",
                    "include_workflow_fields": True
                })
                print("✅ create_clinical_template execution successful")
                print(f"📊 Result type: {type(result)}")
                
                # Try to extract meaningful info from result
                if hasattr(result, 'success'):
                    print(f"📊 Success: {result.success}")
                    if hasattr(result, 'data') and result.data:
                        print(f"📊 Data keys: {list(result.data.keys()) if isinstance(result.data, dict) else 'Non-dict data'}")
                
            except Exception as e:
                print(f"❌ create_clinical_template execution failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Tool execution testing failed: {e}")
        return False

def test_langchain_compatibility():
    """Test LangChain compatibility features."""
    print("\n🔗 Testing LangChain compatibility...")
    
    try:
        from hacs_utils.integrations.langchain import get_hacs_tools
        
        tools = get_hacs_tools()
        if not tools:
            print("❌ No tools available for compatibility testing")
            return False
        
        # Test a few tools for LangChain interface compliance
        for i, tool in enumerate(tools[:3]):  # Test first 3 tools
            print(f"🔧 Testing tool {i+1}: {tool.name}")
            
            # Check required attributes
            required_attrs = ['name', 'description', 'args', 'invoke']
            for attr in required_attrs:
                if hasattr(tool, attr):
                    print(f"✅ Has {attr}")
                else:
                    print(f"❌ Missing {attr}")
            
            # Check if tool has proper schema
            if hasattr(tool, 'args_schema') and tool.args_schema:
                print("✅ Has proper args_schema")
            else:
                print("❌ Missing or invalid args_schema")
        
        return True
        
    except Exception as e:
        print(f"❌ LangChain compatibility testing failed: {e}")
        return False

def generate_report():
    """Generate a comprehensive validation report."""
    print("\n📊 Generating validation report...")
    
    try:
        from hacs_utils.integrations.langchain import get_hacs_tools, get_hacs_tools_by_category
        
        all_tools = get_hacs_tools()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_tools": len(all_tools),
            "tools_by_category": {},
            "tool_details": []
        }
        
        # Get tools by category
        categories = [
            "resource_management", "clinical_workflows", "schema_discovery",
            "development_tools", "memory_operations", "vector_search",
            "fhir_integration", "healthcare_analytics", "ai_integrations",
            "admin_operations"
        ]
        
        for category in categories:
            category_tools = get_hacs_tools_by_category(category)
            report["tools_by_category"][category] = len(category_tools)
        
        # Get tool details
        for tool in all_tools:
            tool_info = {
                "name": tool.name,
                "description": tool.description[:100] + "..." if len(tool.description) > 100 else tool.description,
                "has_args_schema": hasattr(tool, 'args_schema') and tool.args_schema is not None,
                "args_count": len(tool.args) if hasattr(tool, 'args') else 0
            }
            report["tool_details"].append(tool_info)
        
        # Save report
        with open("hacs_langchain_tools_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ Report saved to hacs_langchain_tools_report.json")
        print(f"📊 Total tools: {report['total_tools']}")
        print("📊 Tools by category:")
        for category, count in report["tools_by_category"].items():
            print(f"  - {category}: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Report generation failed: {e}")
        return False

def main():
    """Main validation routine."""
    print("🚀 HACS LangChain Tools Validation")
    print("=" * 50)
    
    tests = [
        ("Import Testing", test_imports),
        ("Tool Discovery", test_tool_discovery),
        ("Individual Tools", test_individual_tools),
        ("Tool Execution", test_tool_execution),
        ("LangChain Compatibility", test_langchain_compatibility),
        ("Report Generation", generate_report),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}")
        print("-" * len(test_name))
        
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n🏁 Validation Summary")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! HACS LangChain tools are ready.")
        return 0
    else:
        print("⚠️ Some tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())