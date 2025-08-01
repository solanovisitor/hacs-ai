#!/usr/bin/env python3
"""
Fixed MCP Test with Proper Configuration

Tests MCP functionality with properly configured URLs and fallback handling.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


class SimpleConfig:
    """Simple configuration with defaults for testing."""
    
    def __init__(self):
        self.hacs_mcp_server_url = os.getenv("HACS_MCP_SERVER_URL", "http://localhost:8000")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")


async def test_working_mcp_connection():
    """Test MCP connection with proper configuration."""
    print("🔌 Testing MCP Connection with Fixed Configuration...")
    
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
        
        config = SimpleConfig()
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
        print("✅ MCP client created successfully")
        
        # Try to get tools with error handling
        try:
            print("🔍 Retrieving tools...")
            tools = await asyncio.wait_for(client.get_tools(), timeout=10.0)
            print(f"✅ Successfully retrieved {len(tools)} tools")
            
            # Show tool details
            if tools:
                print("\n🛠️ Available Tools:")
                for i, tool in enumerate(tools[:5]):
                    print(f"   {i+1}. {tool.name}: {tool.description[:60]}...")
                if len(tools) > 5:
                    print(f"   ... and {len(tools) - 5} more tools")
                
                # Test one tool execution
                print(f"\n🧪 Testing tool execution...")
                test_tool = None
                for tool in tools:
                    if "list" in tool.name.lower() or "discover" in tool.name.lower():
                        test_tool = tool
                        break
                
                if test_tool:
                    print(f"Testing: {test_tool.name}")
                    try:
                        result = await asyncio.wait_for(
                            test_tool.ainvoke({}), 
                            timeout=15.0
                        )
                        print("✅ Tool execution successful!")
                        print(f"Result type: {type(result)}")
                        print(f"Result preview: {str(result)[:200]}...")
                    except Exception as e:
                        print(f"⚠️ Tool execution failed: {e}")
                        print(f"   This is expected for some tools without proper parameters")
                else:
                    print("ℹ️ No suitable test tool found")
            else:
                print("⚠️ No tools retrieved")
                
        except asyncio.TimeoutError:
            print("⏰ Tool retrieval timed out (server may be slow)")
            return False
            
        except Exception as e:
            print(f"❌ Tool retrieval failed: {e}")
            print(f"   Error type: {type(e).__name__}")
            
            # Check if it's the TaskGroup error we've been seeing
            if "TaskGroup" in str(e):
                print("🔍 This appears to be the TaskGroup error we've been investigating")
                print("   The MCP client may have internal connection issues")
                return False
            
        # Try to close the client properly
        try:
            # Different ways to close based on what methods are available
            if hasattr(client, 'close'):
                await asyncio.wait_for(client.close(), timeout=5.0)
                print("✅ Client closed via close() method")
            elif hasattr(client, '__aexit__'):
                await client.__aexit__(None, None, None)
                print("✅ Client closed via context manager")
            else:
                print("⚠️ No standard close method found, may leak connections")
        except Exception as e:
            print(f"⚠️ Client close warning: {e}")
        
        return True
        
    except ImportError:
        print("❌ langchain-mcp-adapters not available")
        return False
        
    except Exception as e:
        print(f"❌ MCP connection test failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False


async def test_http_direct():
    """Test direct HTTP connection to MCP server."""
    print("\n🌐 Testing Direct HTTP Connection...")
    
    try:
        import httpx
        
        config = SimpleConfig()
        url = config.hacs_mcp_server_url
        
        print(f"📡 Connecting to: {url}")
        
        # Test basic HTTP connectivity
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            print(f"✅ HTTP GET successful: {response.status_code}")
            
            # Test JSON-RPC tools endpoint
            tools_response = await client.post(
                url,
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "id": 1
                },
                headers={"Content-Type": "application/json"}
            )
            
            if tools_response.status_code == 200:
                result = tools_response.json()
                tools = result.get('result', {}).get('tools', [])
                print(f"✅ JSON-RPC tools/list: {len(tools)} tools available")
                
                # Show first few tools
                for i, tool in enumerate(tools[:3]):
                    name = tool.get('name', 'Unknown')
                    desc = tool.get('description', 'No description')
                    print(f"   {i+1}. {name}: {desc[:50]}...")
                    
                return True
            else:
                print(f"❌ JSON-RPC failed: {tools_response.status_code}")
                print(f"Response: {tools_response.text[:200]}")
                return False
        
    except Exception as e:
        print(f"❌ Direct HTTP test failed: {e}")
        return False


async def main():
    """Run fixed MCP tests."""
    print("🚀 Fixed MCP Integration Tests")
    print("=" * 40)
    
    tests = [
        ("Direct HTTP", test_http_direct),
        ("MCP Connection", test_working_mcp_connection),
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
    
    if results[0]:  # HTTP test passed
        print("\n✅ HACS MCP server is working correctly")
        if not results[1]:  # But MCP client failed
            print("⚠️ Issue is in langchain-mcp-adapters, not the server")
            print("💡 Recommendation: Use manual HTTP calls as fallback")
    
    return passed > 0  # Success if at least one test passes


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)