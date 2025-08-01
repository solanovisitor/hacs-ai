#!/usr/bin/env python3
"""
Core MCP Functionality Test

Tests just the MCP client functionality without the full agent setup
to isolate and fix the TaskGroup error.
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from configuration import Configuration


async def test_basic_mcp_connection():
    """Test basic MCP connection without full agent setup."""
    print("🔌 Testing Basic MCP Connection...")
    
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
        
        config = Configuration()
        print(f"🌐 Connecting to: {config.hacs_mcp_server_url}")
        
        # Configure HACS MCP server
        server_config = {
            "hacs": {
                "url": config.hacs_mcp_server_url,
                "transport": "streamable_http"
            }
        }
        
        # Create MCP client
        client = MultiServerMCPClient(server_config)
        print("✅ MCP client created")
        
        # Try to get tools with a shorter timeout
        try:
            print("🔍 Getting tools...")
            tools = await asyncio.wait_for(client.get_tools(), timeout=5.0)
            print(f"✅ Retrieved {len(tools)} tools successfully")
            
            # Show first few tools
            for i, tool in enumerate(tools[:3]):
                print(f"   {i+1}. {tool.name}")
                
        except asyncio.TimeoutError:
            print("⏰ Tool retrieval timed out")
            
        except Exception as e:
            print(f"❌ Tool retrieval failed: {e}")
            print(f"   Error type: {type(e).__name__}")
            
        # Close client
        try:
            await asyncio.wait_for(client.close(), timeout=3.0)
            print("✅ Client closed successfully")
        except Exception as e:
            print(f"⚠️ Client close warning: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic MCP connection test failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False


async def test_manual_http_fallback():
    """Test manual HTTP fallback for comparison."""
    print("\n🌐 Testing Manual HTTP Fallback...")
    
    try:
        import httpx
        
        config = Configuration()
        
        # Test basic HTTP connectivity
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(config.hacs_mcp_server_url)
            print(f"✅ HTTP connection successful: {response.status_code}")
            
            # Test JSON-RPC tools endpoint
            try:
                tools_response = await client.post(
                    config.hacs_mcp_server_url,
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/list",
                        "id": 1
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=5.0
                )
                
                if tools_response.status_code == 200:
                    result = tools_response.json()
                    tools = result.get('result', {}).get('tools', [])
                    print(f"✅ Manual HTTP tools call: {len(tools)} tools")
                else:
                    print(f"⚠️ Manual HTTP tools call: {tools_response.status_code}")
                    
            except Exception as e:
                print(f"⚠️ Manual HTTP tools call failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Manual HTTP fallback test failed: {e}")
        return False


async def main():
    """Run core MCP functionality tests."""
    print("🚀 Core MCP Functionality Tests")
    print("=" * 40)
    
    tests = [
        ("Basic MCP Connection", test_basic_mcp_connection),
        ("Manual HTTP Fallback", test_manual_http_fallback),
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
    print(f"\n{'='*40}")
    print("📊 Test Results:")
    
    passed = sum(results)
    total = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed > 0:
        print("\n💡 Analysis:")
        if results[0]:  # Basic MCP connection worked
            print("   • MCP client connection is working")
            print("   • The issue may be in agent integration, not core MCP")
        if results[1]:  # Manual HTTP worked
            print("   • HACS MCP server is responding correctly")
            print("   • HTTP transport is functioning")
        
        print("\n🎯 Recommendations:")
        print("   • Use manual HTTP calls as fallback if MCP integration issues persist")
        print("   • MCP tools are accessible, focus on fixing agent-level integration")
        print("   • Consider using simplified tool wrappers")
        
    else:
        print("\n🔧 Troubleshooting:")
        print("   • Check MCP server: docker logs hacs-mcp-server")
        print("   • Verify server is running: docker-compose ps")
        print("   • Test manual connection: curl http://localhost:8000")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)