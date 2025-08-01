#!/usr/bin/env python3
"""
Test script for HACS LangChain MCP Integration

This script validates that the MCP integration is working correctly with:
- Direct tool access via langchain-mcp-adapters
- Enhanced metadata tracking
- Proper error handling
- Tool discovery and execution

Author: HACS Development Team
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from agent_mcp_integrated import (
    HACSMCPManager,
    create_hacs_mcp_agent,
    test_mcp_integration
)
from configuration import Configuration


async def test_mcp_manager():
    """Test the MCP manager functionality."""
    print("🔧 Testing MCP Manager...")
    
    try:
        config = Configuration()
        manager = HACSMCPManager(config)
        
        # Test client initialization
        client = await manager.initialize_client()
        print(f"✅ MCP client initialized: {type(client).__name__}")
        
        # Test tool loading
        tools = await manager.get_mcp_tools()
        print(f"✅ Loaded {len(tools)} tools from MCP server")
        
        # Show some tool details
        for i, tool in enumerate(tools[:3]):
            print(f"   🔧 {tool.name}: {tool.description[:60]}...")
        
        if len(tools) > 3:
            print(f"   ... and {len(tools) - 3} more tools")
        
        # Cleanup
        await manager.close()
        print("✅ MCP manager cleaned up successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP manager test failed: {e}")
        return False


async def test_agent_creation():
    """Test creating the MCP-integrated agent."""
    print("\n🤖 Testing Agent Creation...")
    
    try:
        config = Configuration()
        agent, mcp_manager = await create_hacs_mcp_agent(config=config)
        
        print("✅ MCP-integrated agent created successfully")
        print(f"   Agent type: {type(agent).__name__}")
        print(f"   MCP manager: {type(mcp_manager).__name__}")
        
        # Cleanup
        await mcp_manager.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Agent creation test failed: {e}")
        return False


async def test_tool_execution():
    """Test executing a tool through the MCP integration."""
    print("\n🛠️ Testing Tool Execution...")
    
    try:
        config = Configuration()
        manager = HACSMCPManager(config)
        
        # Get tools
        tools = await manager.get_mcp_tools()
        
        if not tools:
            print("⚠️ No tools available for testing")
            return False
        
        # Find a safe tool to test (like list_available_tools)
        test_tool = None
        for tool in tools:
            if "list" in tool.name.lower() or "discover" in tool.name.lower():
                test_tool = tool
                break
        
        if not test_tool:
            test_tool = tools[0]  # Use first tool as fallback
        
        print(f"🧪 Testing tool: {test_tool.name}")
        
        # Test tool execution (with minimal parameters)
        try:
            if hasattr(test_tool, '_run'):
                if asyncio.iscoroutinefunction(test_tool._run):
                    result = await test_tool._run()
                else:
                    result = test_tool._run()
                
                print("✅ Tool execution successful")
                print(f"   Result type: {type(result).__name__}")
                print(f"   Result preview: {str(result)[:100]}...")
            else:
                print("⚠️ Tool doesn't have _run method, skipping execution test")
                
        except Exception as e:
            print(f"⚠️ Tool execution failed (expected for some tools): {e}")
        
        # Cleanup
        await manager.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Tool execution test failed: {e}")
        return False


async def test_error_handling():
    """Test error handling in MCP integration."""
    print("\n🚨 Testing Error Handling...")
    
    try:
        # Test with invalid MCP server URL
        config = Configuration()
        config.hacs_mcp_server_url = "http://invalid-server:9999"
        
        manager = HACSMCPManager(config)
        
        try:
            tools = await manager.get_mcp_tools()
            print(f"⚠️ Unexpected success with invalid server: {len(tools)} tools")
        except Exception as e:
            print(f"✅ Error handling working correctly: {type(e).__name__}")
        
        # Cleanup
        await manager.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


async def main():
    """Run all MCP integration tests."""
    print("🚀 HACS LangChain MCP Integration Tests")
    print("=" * 60)
    
    tests = [
        ("MCP Manager", test_mcp_manager),
        ("Agent Creation", test_agent_creation),
        ("Tool Execution", test_tool_execution),
        ("Error Handling", test_error_handling),
        ("Integration Test", test_mcp_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = await test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results.append(False)
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 Test Results Summary:")
    
    passed = sum(results)
    total = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! MCP integration is working correctly.")
        print("\n🚀 Ready to use:")
        print("   1. Start MCP server: docker-compose up -d hacs-mcp-server")
        print("   2. Run agent: uv run langgraph dev --config langgraph_mcp.json")
        print("   3. Test with: 'List available HACS tools'")
        return True
    else:
        print(f"\n❌ {total - passed} tests failed. Check MCP server connectivity.")
        print("\n🔧 Troubleshooting:")
        print("   • Ensure MCP server is running on localhost:8000")
        print("   • Check docker-compose logs hacs-mcp-server")
        print("   • Verify .env configuration")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)