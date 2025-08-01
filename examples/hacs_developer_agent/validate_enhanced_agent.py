#!/usr/bin/env python3
"""
Validation script for Enhanced HACS Developer Agent

This script validates that the enhanced agent is properly configured with:
- Enhanced metadata tracking and parsing
- Improved tool result reflection capabilities  
- Better MCP tool integration
- Comprehensive tool discovery and analysis

Author: HACS Development Team
"""

import sys
import os
from pathlib import Path

# Add paths for HACS packages
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "packages" / "hacs-registry" / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "packages" / "hacs-core" / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "packages" / "hacs-tools" / "src"))


def validate_integration_framework():
    """Validate the HACS integration framework."""
    print("🔍 Validating HACS Integration Framework...")
    
    try:
        from hacs_registry import (
            get_integration_manager, 
            FrameworkType, 
            ExecutionContext,
            ToolExecutionResult
        )
        
        # Test integration manager
        manager = get_integration_manager()
        stats = manager.get_integration_stats()
        
        print(f"✅ Integration framework loaded successfully")
        print(f"   📊 Total tools: {stats['registry_stats']['total_tools']}")
        print(f"   🔌 Supported frameworks: {', '.join(stats['supported_frameworks'])}")
        print(f"   ⚙️ Adaptable tools: {stats['total_adaptable_tools']}")
        
        # Test framework adapters
        for framework in [FrameworkType.LANGCHAIN, FrameworkType.MCP, FrameworkType.NATIVE]:
            try:
                adapter = manager.get_adapter(framework)
                print(f"   ✅ {framework.value} adapter: {adapter.__class__.__name__}")
            except Exception as e:
                print(f"   ⚠️ {framework.value} adapter issue: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration framework validation failed: {e}")
        return False


def validate_enhanced_tools():
    """Validate the enhanced tools module."""
    print("\n🛠️ Validating Enhanced Tools...")
    
    try:
        from tools_enhanced import (
            get_enhanced_hacs_tools,
            call_mcp_server,
            parse_tool_result,
            discover_hacs_resources,
            create_clinical_template,
            list_available_tools,
            get_tool_metadata
        )
        
        # Test tool loading
        tools = get_enhanced_hacs_tools()
        print(f"✅ Enhanced tools loaded: {len(tools)} tools")
        
        # Validate each tool
        for tool in tools:
            tool_name = tool.__name__
            doc = tool.__doc__.split('.')[0] if tool.__doc__ else "No description"
            print(f"   📋 {tool_name}: {doc}")
            
            # Check if tool has required async annotation
            import asyncio
            if asyncio.iscoroutinefunction(tool):
                print(f"      ⚡ Async tool ✓")
            else:
                print(f"      ⚠️ Not async")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced tools validation failed: {e}")
        return False


def validate_agent_state():
    """Validate the enhanced agent state definition."""
    print("\n📊 Validating Enhanced Agent State...")
    
    try:
        from agent import HACSAgentState
        
        # Check that enhanced fields exist
        annotations = HACSAgentState.__annotations__
        enhanced_fields = [
            "tool_execution_history",
            "discovered_tools", 
            "reflection_notes"
        ]
        
        for field in enhanced_fields:
            if field in annotations:
                print(f"   ✅ {field}: {annotations[field]}")
            else:
                print(f"   ❌ Missing field: {field}")
                return False
        
        print("✅ Enhanced agent state validated")
        return True
        
    except Exception as e:
        print(f"❌ Agent state validation failed: {e}")
        return False


def validate_enhanced_prompts():
    """Validate the enhanced prompts."""
    print("\n💬 Validating Enhanced Prompts...")
    
    try:
        from prompts import HACS_AGENT_INSTRUCTIONS
        
        # Check for enhanced content
        enhanced_keywords = [
            "metadata",
            "reflection", 
            "Enhanced HACS",
            "METADATA UTILIZATION",
            "ANALYZE tool results",
            "execution metadata"
        ]
        
        missing_keywords = []
        for keyword in enhanced_keywords:
            if keyword.lower() in HACS_AGENT_INSTRUCTIONS.lower():
                print(f"   ✅ Found: {keyword}")
            else:
                missing_keywords.append(keyword)
        
        if missing_keywords:
            print(f"   ⚠️ Missing keywords: {', '.join(missing_keywords)}")
            return False
        
        print("✅ Enhanced prompts validated")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced prompts validation failed: {e}")
        return False


def validate_metadata_parsing():
    """Validate metadata parsing functionality."""
    print("\n🔧 Validating Metadata Parsing...")
    
    try:
        from tools_enhanced import parse_tool_result
        
        # Test successful result parsing
        test_result = {
            "isError": False,
            "content": [
                {
                    "type": "text",
                    "text": "✅ Resource created successfully\n\n```json\n{\"resource_id\": \"12345\", \"type\": \"Patient\"}\n```\n\n- Status: Active\n- Created: 2024-01-15"
                }
            ],
            "_metadata": {
                "tool_name": "create_resource",
                "execution_time_ms": 150.5,
                "success": True,
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
        
        parsed = parse_tool_result(test_result)
        
        # Validate parsing results
        assert parsed["success"] == True
        assert "created successfully" in parsed["content"]
        assert parsed["metadata"]["execution_time_ms"] == 150.5
        assert "resource_id" in parsed["structured_data"]
        assert len(parsed["reflection_notes"]) > 0
        
        print("✅ Metadata parsing functionality validated")
        print(f"   📊 Extracted metadata: {parsed['metadata']['tool_name']}")
        print(f"   📋 Structured data: {len(parsed['structured_data'])} fields")
        print(f"   💭 Reflection notes: {len(parsed['reflection_notes'])} notes")
        
        return True
        
    except Exception as e:
        print(f"❌ Metadata parsing validation failed: {e}")
        return False


def validate_mcp_integration():
    """Validate MCP integration enhancements."""
    print("\n🔌 Validating MCP Integration...")
    
    try:
        from tools_enhanced import call_mcp_server
        from configuration import Configuration
        
        # This would need a running MCP server to test fully
        # For now, just validate the function exists and has proper signature
        import inspect
        sig = inspect.signature(call_mcp_server)
        
        expected_params = ['params', 'config']
        actual_params = list(sig.parameters.keys())
        
        for param in expected_params:
            if param in actual_params:
                print(f"   ✅ Parameter: {param}")
            else:
                print(f"   ❌ Missing parameter: {param}")
                return False
        
        print("✅ MCP integration structure validated")
        print("   ⚠️ Full MCP testing requires running server")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP integration validation failed: {e}")
        return False


def main():
    """Run all validation tests."""
    print("🚀 Enhanced HACS Developer Agent Validation")
    print("=" * 60)
    
    tests = [
        validate_integration_framework,
        validate_enhanced_tools,
        validate_agent_state,
        validate_enhanced_prompts,
        validate_metadata_parsing,
        validate_mcp_integration
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
    
    print("\n" + "=" * 60)
    print("📊 Validation Summary:")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 All {total} validation tests passed!")
        print("\n✅ **Enhanced HACS Agent is ready for use with:**")
        print("   • Comprehensive metadata tracking")
        print("   • Enhanced tool result parsing")
        print("   • Improved reflection capabilities")
        print("   • Better MCP tool integration")
        print("   • Framework-agnostic tool management")
        
        print("\n🔧 **Next Steps:**")
        print("   1. Start MCP server and database")
        print("   2. Run: uv run langgraph dev")
        print("   3. Test agent with clinical template creation")
        print("   4. Observe enhanced metadata in responses")
        
        return True
    else:
        print(f"❌ {total - passed} out of {total} tests failed")
        print("\n🔧 **Issues to address:**")
        print("   • Check all enhanced modules are properly imported")
        print("   • Ensure agent state includes metadata fields")
        print("   • Verify prompts include metadata instructions")
        
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)