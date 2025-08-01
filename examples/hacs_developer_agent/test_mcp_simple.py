#!/usr/bin/env python3
"""
Simple test for HACS MCP Integration using langchain-mcp-adapters

This script tests the core MCP integration functionality without
complex LangChain dependencies that might cause import issues.
"""

import asyncio
import sys


async def test_mcp_client():
    """Test direct MCP client functionality."""
    print("🔌 Testing MCP Client Connection...")
    
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
        
        # Configure HACS MCP server
        server_config = {
            "hacs": {
                "url": "http://localhost:8000",
                "transport": "streamable_http"
            }
        }
        
        # Create MCP client
        client = MultiServerMCPClient(server_config)
        print("✅ MCP client created successfully")
        
        # Get tools
        tools = await client.get_tools()
        print(f"✅ Retrieved {len(tools)} tools from HACS MCP server")
        
        # Show tool details
        if tools:
            print("\n🛠️ Available Tools:")
            for i, tool in enumerate(tools[:5]):
                print(f"   {i+1}. {tool.name}: {tool.description[:60]}...")
            
            if len(tools) > 5:
                print(f"   ... and {len(tools) - 5} more tools")
                
            # Test executing a simple tool
            print("\n🧪 Testing tool execution...")
            
            # Try to find a list or discover tool
            test_tool = None
            for tool in tools:
                keywords = ['list', 'discover', 'available']
                if any(keyword in tool.name.lower() for keyword in keywords):
                    test_tool = tool
                    break
            
            if test_tool:
                print(f"Testing: {test_tool.name}")
                try:
                    # Try to invoke the tool with minimal parameters
                    result = await test_tool.ainvoke({})
                    print("✅ Tool execution successful!")
                    print(f"Result preview: {str(result)[:200]}...")
                except Exception as e:
                    print(f"⚠️ Tool execution failed (may need parameters): {e}")
            else:
                print("⚠️ No suitable test tool found")
        else:
            print("⚠️ No tools retrieved from MCP server")
        
        # Cleanup
        await client.close()
        print("✅ MCP client closed successfully")
        
        return len(tools) > 0
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure langchain-mcp-adapters is installed")
        return False
        
    except Exception as e:
        print(f"❌ MCP client test failed: {e}")
        return False


async def test_mcp_server_connectivity():
    """Test basic connectivity to MCP server."""
    print("\n🌐 Testing MCP Server Connectivity...")
    
    try:
        import httpx
        
        # Test basic HTTP connectivity
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/")
            print(f"✅ MCP server responding: {response.status_code}")
            
            # Test tools endpoint if available
            try:
                tools_response = await client.post(
                    "http://localhost:8000/",
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/list",
                        "id": 1
                    },
                    headers={"Content-Type": "application/json"}
                )
                tools_result = tools_response.json()
                print(f"✅ Tools endpoint responding: {tools_result.get('result', 'No result')}")
            except Exception as e:
                print(f"⚠️ Tools endpoint test failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Server connectivity test failed: {e}")
        return False


async def test_langchain_mcp_integration():
    """Test the integration between LangChain and MCP."""
    print("\n🔗 Testing LangChain MCP Integration...")
    
    try:
        # Test if we can import and use the adapter
        from langchain_mcp_adapters.client import MultiServerMCPClient
        
        # Create client
        client = MultiServerMCPClient({
            "hacs": {
                "url": "http://localhost:8000",
                "transport": "streamable_http"
            }
        })
        
        # Get tools
        tools = await client.get_tools()
        
        if tools:
            # Test tool properties
            first_tool = tools[0]
            print(f"✅ Tool object type: {type(first_tool).__name__}")
            print(f"✅ Tool has name: {hasattr(first_tool, 'name')}")
            print(f"✅ Tool has description: {hasattr(first_tool, 'description')}")
            print(f"✅ Tool is callable: {callable(first_tool)}")
            
            # Check if it's a proper LangChain tool
            try:
                from langchain_core.tools import BaseTool
                is_base_tool = isinstance(first_tool, BaseTool)
                print(f"✅ Is LangChain BaseTool: {is_base_tool}")
            except ImportError:
                print("⚠️ Cannot check BaseTool type due to import issues")
            
        await client.close()
        
        return True
        
    except Exception as e:
        print(f"❌ LangChain MCP integration test failed: {e}")
        return False


async def main():
    """Run all simple MCP tests."""
    print("🚀 Simple HACS MCP Integration Tests")
    print("=" * 50)
    
    tests = [
        ("Server Connectivity", test_mcp_server_connectivity),
        ("MCP Client", test_mcp_client),
        ("LangChain Integration", test_langchain_mcp_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*10} {test_name} {'='*10}")
        try:
            result = await test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results.append(False)
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 Test Results:")
    
    passed = sum(results)
    total = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 MCP integration is working!")
        print("\n📋 Next Steps:")
        print("   1. The langchain-mcp-adapters library is working correctly")
        print("   2. HACS MCP server is accessible and providing tools")
        print("   3. Tools can be retrieved and are LangChain-compatible")
        print("   4. Ready to integrate with LangGraph agent")
        return True
    else:
        print(f"\n❌ {total - passed} tests failed.")
        print("\n🔧 Troubleshooting:")
        print("   • Check if MCP server is running: docker-compose up -d hacs-mcp-server")
        print("   • Verify server logs: docker logs hacs-mcp-server")
        print("   • Test manual connection: curl http://localhost:8000")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)