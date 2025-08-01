"""
HACS Tool Integration Examples

This module demonstrates best practices for using the HACS tool integration framework
across different scenarios and frameworks. It showcases elegant design patterns and
proper error handling.

Author: HACS Development Team
License: MIT
Version: 0.3.0
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional

# Import the integration framework
from hacs_registry import (
    get_integration_manager,
    FrameworkType,
    ExecutionContext,
    ToolExecutionResult,
    get_langchain_tools,
    get_mcp_tools,
    execute_hacs_tool
)

logger = logging.getLogger(__name__)


class HACSIntegrationExamples:
    """Examples demonstrating HACS tool integration patterns."""
    
    def __init__(self):
        self.integration_manager = get_integration_manager()
    
    async def example_1_basic_tool_execution(self):
        """Example 1: Basic tool execution with context."""
        print("🔧 Example 1: Basic Tool Execution")
        print("=" * 50)
        
        # Execute a tool with context
        result = await execute_hacs_tool(
            tool_name="discover_hacs_resources",
            params={"category_filter": "clinical"},
            actor_name="example_clinician",
            metadata={"example": "basic_execution"}
        )
        
        if result.success:
            print(f"✅ Tool executed successfully in {result.execution_time_ms:.1f}ms")
            print(f"📊 Result: {result.data}")
        else:
            print(f"❌ Tool execution failed: {result.error}")
        
        print()
    
    async def example_2_framework_specific_adaptation(self):
        """Example 2: Framework-specific tool adaptation."""
        print("🔧 Example 2: Framework-Specific Tool Adaptation")
        print("=" * 60)
        
        # Get tools adapted for different frameworks
        try:
            # LangChain tools
            langchain_tools = get_langchain_tools(category="resource_management")
            print(f"🦜 LangChain tools: {len(langchain_tools)} available")
            for tool in langchain_tools[:3]:  # Show first 3
                print(f"   - {tool.name}: {tool.description[:60]}...")
            
            # MCP tools
            mcp_tools = get_mcp_tools(category="schema_discovery")
            print(f"🔌 MCP tools: {len(mcp_tools)} available")
            for tool in mcp_tools[:3]:  # Show first 3
                print(f"   - {tool['name']}: {tool['description'][:60]}...")
            
        except Exception as e:
            print(f"❌ Framework adaptation failed: {e}")
        
        print()
    
    async def example_3_batch_tool_execution(self):
        """Example 3: Batch tool execution with error handling."""
        print("🔧 Example 3: Batch Tool Execution")
        print("=" * 40)
        
        # Define multiple tool executions
        tool_executions = [
            {
                "name": "discover_hacs_resources", 
                "params": {"category_filter": "clinical"}
            },
            {
                "name": "get_hacs_resource_schema",
                "params": {"resource_type": "Patient"}
            },
            {
                "name": "create_clinical_template",
                "params": {
                    "template_type": "assessment",
                    "focus_area": "cardiology"
                }
            }
        ]
        
        # Execute tools in batch
        results = []
        for execution in tool_executions:
            result = await execute_hacs_tool(
                tool_name=execution["name"],
                params=execution["params"],
                actor_name="batch_executor"
            )
            results.append({
                "tool": execution["name"],
                "success": result.success,
                "execution_time": result.execution_time_ms,
                "error": result.error if not result.success else None
            })
        
        # Report results
        successful = sum(1 for r in results if r["success"])
        total_time = sum(r["execution_time"] for r in results)
        
        print(f"📊 Batch execution completed:")
        print(f"   ✅ Successful: {successful}/{len(results)}")
        print(f"   ⏱️ Total time: {total_time:.1f}ms")
        
        for result in results:
            status = "✅" if result["success"] else "❌"
            print(f"   {status} {result['tool']}: {result['execution_time']:.1f}ms")
            if result["error"]:
                print(f"      Error: {result['error']}")
        
        print()
    
    async def example_4_advanced_context_management(self):
        """Example 4: Advanced context management with dependency injection."""
        print("🔧 Example 4: Advanced Context Management")
        print("=" * 50)
        
        # Simulate database and vector store adapters
        class MockDatabaseAdapter:
            def __init__(self):
                self.name = "PostgreSQL Mock Adapter"
        
        class MockVectorStore:
            def __init__(self):
                self.name = "Qdrant Mock Store"
        
        # Create context with dependencies
        context = ExecutionContext(
            actor_name="advanced_user",
            db_adapter=MockDatabaseAdapter(),
            vector_store=MockVectorStore(),
            session_id="session_123",
            framework=FrameworkType.NATIVE,
            metadata={
                "department": "cardiology",
                "priority": "high",
                "use_case": "clinical_research"
            }
        )
        
        # Execute tool with rich context
        result = await self.integration_manager.execute_tool(
            tool_name="search_hacs_records",
            params={
                "resource_type": "Patient",
                "search_criteria": {"department": "cardiology"},
                "limit": 10
            },
            context=context
        )
        
        if result.success:
            print(f"✅ Context-aware execution successful")
            print(f"📋 Context metadata: {result.metadata.get('context', {})}")
            print(f"⏱️ Execution time: {result.execution_time_ms:.1f}ms")
        else:
            print(f"❌ Context-aware execution failed: {result.error}")
        
        print()
    
    def example_5_registry_introspection(self):
        """Example 5: Registry introspection and tool discovery."""
        print("🔧 Example 5: Registry Introspection")
        print("=" * 40)
        
        # Get comprehensive statistics
        stats = self.integration_manager.get_integration_stats()
        
        print("📊 Integration Framework Statistics:")
        print(f"   🛠️ Total tools: {stats['registry_stats']['total_tools']}")
        print(f"   📂 Categories: {len(stats['registry_stats']['categories'])}")
        print(f"   🏗️ Domains: {len(stats['registry_stats']['domains'])}")
        print(f"   🔌 Supported frameworks: {', '.join(stats['supported_frameworks'])}")
        print(f"   ⚡ Adaptable tools: {stats['total_adaptable_tools']}")
        
        # Show tools by category
        print("\n📋 Tools by Category:")
        for category, count in stats['registry_stats']['categories'].items():
            print(f"   {category.replace('_', ' ').title()}: {count} tools")
        
        # Show capabilities distribution
        capabilities = stats['registry_stats']['capabilities']
        print(f"\n🎯 Tool Capabilities:")
        print(f"   👤 Require actor: {capabilities['requires_actor']}")
        print(f"   🗄️ Require database: {capabilities['requires_db']}")
        print(f"   🔍 Require vector store: {capabilities['requires_vector_store']}")
        print(f"   ⚡ Async tools: {capabilities['is_async']}")
        
        print()
    
    async def example_6_tool_search_and_filtering(self):
        """Example 6: Advanced tool search and filtering."""
        print("🔧 Example 6: Tool Search and Filtering")
        print("=" * 45)
        
        # Search by query
        search_results = self.integration_manager.registry.search_tools(
            query="clinical",
            requires_actor=True,
            framework="langchain"
        )
        
        print(f"🔍 Search results for 'clinical' tools:")
        print(f"   Found {len(search_results)} matching tools")
        
        for tool in search_results[:5]:  # Show first 5
            print(f"   - {tool.name} ({tool.category})")
            print(f"     {tool.description[:80]}...")
        
        # Filter by specific criteria
        memory_tools = self.integration_manager.registry.get_tools_by_category("memory_operations")
        async_memory_tools = [t for t in memory_tools if t.is_async]
        
        print(f"\n🧠 Memory operations tools: {len(memory_tools)} total")
        print(f"   ⚡ Async memory tools: {len(async_memory_tools)}")
        
        # Show tools by domain
        domains = self.integration_manager.registry.get_available_domains()
        print(f"\n🏗️ Available domains: {', '.join(domains)}")
        
        print()
    
    async def example_7_error_handling_patterns(self):
        """Example 7: Error handling and recovery patterns."""
        print("🔧 Example 7: Error Handling Patterns")
        print("=" * 45)
        
        # Example with invalid tool name
        result = await execute_hacs_tool(
            tool_name="nonexistent_tool",
            params={"test": "data"}
        )
        
        print(f"❌ Invalid tool test: {result.error}")
        
        # Example with invalid parameters
        result = await execute_hacs_tool(
            tool_name="discover_hacs_resources",
            params={"invalid_param": "value"}
        )
        
        if result.success:
            print("✅ Tool handled invalid parameters gracefully")
        else:
            print(f"⚠️ Parameter validation: {result.error}")
        
        # Example with timeout simulation
        try:
            # This would normally include timeout handling
            result = await execute_hacs_tool(
                tool_name="discover_hacs_resources",
                params={"category_filter": "clinical"},
                metadata={"timeout": 30}
            )
            print(f"✅ Timeout handling test completed: {result.success}")
        except Exception as e:
            print(f"⚠️ Timeout handling error: {e}")
        
        print()


async def run_all_examples():
    """Run all integration examples."""
    print("🚀 HACS Tool Integration Framework Examples")
    print("=" * 70)
    print()
    
    examples = HACSIntegrationExamples()
    
    try:
        await examples.example_1_basic_tool_execution()
        await examples.example_2_framework_specific_adaptation()
        await examples.example_3_batch_tool_execution()
        await examples.example_4_advanced_context_management()
        examples.example_5_registry_introspection()
        await examples.example_6_tool_search_and_filtering()
        await examples.example_7_error_handling_patterns()
        
        print("🎉 All examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Example execution failed: {e}")
        logger.error(f"Example execution error: {e}", exc_info=True)


def demonstrate_integration_patterns():
    """Demonstrate key integration patterns."""
    print("📚 Key Integration Patterns")
    print("=" * 35)
    
    # Pattern 1: Factory Pattern for Adapters
    print("🏭 Factory Pattern: Framework Adapters")
    print("   - LangChainAdapter: Converts to StructuredTool")
    print("   - MCPAdapter: Converts to MCP tool definition")
    print("   - NativeAdapter: Returns tool as-is")
    print()
    
    # Pattern 2: Strategy Pattern for Execution
    print("🎯 Strategy Pattern: Execution Strategies")
    print("   - AsyncExecutionStrategy: Async tool execution")
    print("   - SyncExecutionStrategy: Sync tool execution")
    print("   - BatchExecutionStrategy: Batch processing")
    print()
    
    # Pattern 3: Dependency Injection
    print("💉 Dependency Injection: Context Management")
    print("   - Database adapters injected automatically")
    print("   - Vector stores injected based on tool requirements")
    print("   - Actor context propagated through execution")
    print()
    
    # Pattern 4: Observer Pattern for Events
    print("👁️ Observer Pattern: Tool Lifecycle Events")
    print("   - Tool execution started/completed events")
    print("   - Error notification and logging")
    print("   - Performance monitoring")
    print()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run examples
    demonstrate_integration_patterns()
    asyncio.run(run_all_examples())