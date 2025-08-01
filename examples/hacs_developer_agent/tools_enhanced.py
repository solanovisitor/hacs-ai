"""Enhanced Tools for HACS developer agent.

This module contains functions that are directly exposed to the LLM as tools.
These tools integrate with the HACS MCP server and the new integration framework
to perform healthcare model operations with enhanced metadata and result parsing.
"""

import json
from typing import Any, Dict, List, Optional, cast
from datetime import datetime

import httpx
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg
from typing_extensions import Annotated

from configuration import Configuration

# HACS tools are now accessed via HTTP calls to MCP server with enhanced metadata
HACS_TOOLS_AVAILABLE = True  # Always available via HTTP


async def call_mcp_server(params: Dict[str, Any], config: RunnableConfig) -> Dict[str, Any]:
    """Enhanced helper function to call the HACS MCP server with metadata tracking."""
    configuration = Configuration.from_runnable_config(config)
    start_time = datetime.now()

    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": params,
            "id": 1
        }

        response = await client.post(
            f"{configuration.hacs_mcp_server_url}/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()

    execution_time = (datetime.now() - start_time).total_seconds() * 1000

    if "result" in result:
        mcp_result = result["result"]
        
        # Check if the result indicates HACS tools are not available
        if (isinstance(mcp_result, dict) and 
            mcp_result.get("isError") and 
            isinstance(mcp_result.get("content"), list) and
            len(mcp_result["content"]) > 0 and
            "HACS tools not available" in str(mcp_result["content"][0])):
            return {
                "success": False, 
                "error": "HACS packages not installed in MCP server Docker container",
                "detailed_error": mcp_result["content"][0].get("text", "Unknown HACS error"),
                "_metadata": {
                    "tool_name": params.get("name", "unknown"),
                    "execution_time_ms": execution_time,
                    "mcp_server_url": configuration.hacs_mcp_server_url,
                    "timestamp": start_time.isoformat()
                }
            }
        
        # Enhance result with metadata
        if isinstance(mcp_result, dict):
            mcp_result["_metadata"] = {
                "tool_name": params.get("name", "unknown"),
                "execution_time_ms": execution_time,
                "mcp_server_url": configuration.hacs_mcp_server_url,
                "timestamp": start_time.isoformat(),
                "success": not mcp_result.get("isError", False)
            }
        
        return mcp_result
    else:
        return {
            "success": False, 
            "error": result.get("error", "Unknown error"),
            "_metadata": {
                "tool_name": params.get("name", "unknown"),
                "execution_time_ms": execution_time,
                "mcp_server_url": configuration.hacs_mcp_server_url,
                "timestamp": start_time.isoformat(),
                "success": False
            }
        }


def parse_tool_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhanced parser for MCP tool results with better metadata extraction.
    
    This function extracts structured information from MCP tool results,
    making them more useful for agent reflection and decision-making.
    """
    parsed = {
        "success": False,
        "content": "",
        "structured_data": {},
        "metadata": {},
        "reflection_notes": []
    }
    
    # Extract metadata
    if "_metadata" in result:
        parsed["metadata"] = result["_metadata"]
        parsed["success"] = result["_metadata"].get("success", False)
    
    # Handle MCP CallToolResult format
    if isinstance(result, dict):
        # Check for error status
        if result.get("isError", False):
            parsed["success"] = False
            if "content" in result and isinstance(result["content"], list):
                error_content = result["content"][0] if result["content"] else {}
                parsed["content"] = error_content.get("text", "Unknown error")
                parsed["reflection_notes"].append(f"Tool execution failed: {parsed['content']}")
        else:
            parsed["success"] = True
            
        # Extract content
        if "content" in result and isinstance(result["content"], list):
            content_items = result["content"]
            if content_items:
                first_content = content_items[0]
                if isinstance(first_content, dict) and "text" in first_content:
                    parsed["content"] = first_content["text"]
                    
                    # Try to extract structured data from markdown/text content
                    try:
                        # Look for JSON blocks in markdown
                        if "```json" in parsed["content"]:
                            json_start = parsed["content"].find("```json") + 7
                            json_end = parsed["content"].find("```", json_start)
                            if json_end > json_start:
                                json_str = parsed["content"][json_start:json_end].strip()
                                parsed["structured_data"] = json.loads(json_str)
                        
                        # Look for key-value patterns
                        lines = parsed["content"].split('\n')
                        for line in lines:
                            if ':' in line and not line.startswith('#'):
                                parts = line.split(':', 1)
                                if len(parts) == 2:
                                    key = parts[0].strip('- ').strip()
                                    value = parts[1].strip()
                                    if key and value:
                                        parsed["structured_data"][key] = value
                    except Exception:
                        pass  # Continue if parsing fails
    
    # Add reflection notes based on content analysis
    if parsed["success"]:
        content_lower = parsed["content"].lower()
        if "created successfully" in content_lower:
            parsed["reflection_notes"].append("Resource creation was successful")
        elif "found" in content_lower and any(x in content_lower for x in ["tool", "resource", "model"]):
            parsed["reflection_notes"].append("Discovery operation returned results")
        elif "error" in content_lower or "failed" in content_lower:
            parsed["reflection_notes"].append("Operation may have encountered issues despite success status")
    
    return parsed


async def discover_hacs_resources(
    category_filter: Optional[str] = None,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """
    Discover available HACS resource schemas and their capabilities with enhanced metadata.

    TERMINOLOGY DISTINCTION:
    - HACS Resources: Schema definitions/templates (Patient model, Observation model)
    - HACS Records: Actual data records validated against HACS resources
    - This tool discovers MODEL schemas, not data records

    Args:
        category_filter: Filter by model category (clinical, administrative, reasoning)

    Returns:
        Comprehensive information about available HACS resource schemas with metadata
    """
    # Use enhanced MCP server call
    result = await call_mcp_server(
        params={
            "name": "discover_hacs_resources",
            "arguments": {
                "category_filter": category_filter,
                "include_field_counts": True
            }
        },
        config=config
    )
    
    # Parse result with enhanced metadata extraction
    parsed = parse_tool_result(result)
    
    # Format comprehensive response with metadata
    if parsed["success"]:
        response_parts = [
            "🔍 **HACS Resource Discovery Results**",
            "",
            parsed["content"],
            "",
            "📊 **Execution Metadata:**"
        ]
        
        if parsed["metadata"]:
            metadata = parsed["metadata"]
            response_parts.extend([
                f"- Tool: {metadata.get('tool_name', 'unknown')}",
                f"- Execution time: {metadata.get('execution_time_ms', 0):.1f}ms",
                f"- Timestamp: {metadata.get('timestamp', 'unknown')}",
                f"- Server: {metadata.get('mcp_server_url', 'unknown')}"
            ])
        
        if parsed["structured_data"]:
            response_parts.extend([
                "",
                "🏗️ **Structured Data Extracted:**",
                json.dumps(parsed["structured_data"], indent=2)
            ])
        
        if parsed["reflection_notes"]:
            response_parts.extend([
                "",
                "💭 **Reflection Notes:**"
            ])
            response_parts.extend([f"- {note}" for note in parsed["reflection_notes"]])
        
        return "\n".join(response_parts)
    else:
        error_response = [
            "❌ **HACS Resource Discovery Failed**",
            "",
            f"Error: {parsed['content']}"
        ]
        
        if parsed["metadata"]:
            error_response.extend([
                "",
                f"Execution time: {parsed['metadata'].get('execution_time_ms', 0):.1f}ms"
            ])
        
        return "\n".join(error_response)


async def create_clinical_template(
    template_type: str,
    focus_area: str,
    complexity_level: str = "standard",
    include_workflow_fields: bool = True,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """Generate a clinical template for healthcare workflows with enhanced metadata.

    This tool creates structured templates that help developers implement
    healthcare workflows using HACS resources, based on their specific use case.

    Args:
        template_type: Type of clinical template (e.g., 'consultation', 'intake')
        focus_area: Clinical focus area (e.g., 'diabetes', 'cardiology')
        complexity_level: Complexity level ('basic', 'standard', 'advanced')
        include_workflow_fields: Whether to include workflow management fields

    Returns:
        Clinical template with metadata and reflection notes for agent use
    """
    # Use enhanced MCP server call
    result = await call_mcp_server(
        params={
            "name": "create_clinical_template",
            "arguments": {
                "template_type": template_type,
                "focus_area": focus_area,
                "complexity_level": complexity_level,
                "include_workflow_fields": include_workflow_fields
            }
        },
        config=config
    )
    
    # Parse result with enhanced metadata extraction
    parsed = parse_tool_result(result)
    
    # Format comprehensive response with metadata
    if parsed["success"]:
        response_parts = [
            f"🏥 **Clinical Template Created: {template_type.title()} for {focus_area.title()}**",
            "",
            parsed["content"],
            "",
            "📊 **Template Generation Metadata:**"
        ]
        
        if parsed["metadata"]:
            metadata = parsed["metadata"]
            response_parts.extend([
                f"- Template type: {template_type}",
                f"- Focus area: {focus_area}",
                f"- Complexity: {complexity_level}",
                f"- Workflow fields: {include_workflow_fields}",
                f"- Generation time: {metadata.get('execution_time_ms', 0):.1f}ms",
                f"- Timestamp: {metadata.get('timestamp', 'unknown')}"
            ])
        
        if parsed["structured_data"]:
            response_parts.extend([
                "",
                "🏗️ **Template Structure:**",
                json.dumps(parsed["structured_data"], indent=2)
            ])
        
        if parsed["reflection_notes"]:
            response_parts.extend([
                "",
                "💭 **Template Notes:**"
            ])
            response_parts.extend([f"- {note}" for note in parsed["reflection_notes"]])
            
        # Add usage guidance
        response_parts.extend([
            "",
            "📝 **Usage Guidance:**",
            f"- This {template_type} template is optimized for {focus_area}",
            f"- Complexity level '{complexity_level}' provides appropriate detail",
            f"- Workflow fields {'included' if include_workflow_fields else 'excluded'} based on requirements",
            "- Template can be customized further based on specific clinical needs"
        ])
        
        return "\n".join(response_parts)
    else:
        error_response = [
            f"❌ **Clinical Template Creation Failed**",
            f"Template: {template_type} for {focus_area}",
            "",
            f"Error: {parsed['content']}"
        ]
        
        if parsed["metadata"]:
            error_response.extend([
                "",
                f"Attempted generation time: {parsed['metadata'].get('execution_time_ms', 0):.1f}ms"
            ])
        
        return "\n".join(error_response)


async def list_available_tools(
    category_filter: Optional[str] = None,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """
    List all available HACS tools with their metadata and capabilities.
    
    This tool provides comprehensive information about available MCP tools,
    including their categories, descriptions, and execution capabilities.
    
    Args:
        category_filter: Filter tools by category (e.g., 'clinical_workflows', 'resource_management')
    
    Returns:
        Detailed list of available tools with metadata for agent reflection
    """
    # Use enhanced MCP server call
    result = await call_mcp_server(
        params={
            "name": "list_available_tools",
            "arguments": {
                "category_filter": category_filter
            }
        },
        config=config
    )
    
    # Parse result with enhanced metadata extraction
    parsed = parse_tool_result(result)
    
    # Format comprehensive response with metadata
    if parsed["success"]:
        response_parts = [
            "🛠️ **Available HACS Tools**",
            ""
        ]
        
        if category_filter:
            response_parts.insert(1, f"Category: {category_filter}")
            response_parts.insert(2, "")
        
        response_parts.extend([
            parsed["content"],
            "",
            "📊 **Tool Discovery Metadata:**"
        ])
        
        if parsed["metadata"]:
            metadata = parsed["metadata"]
            response_parts.extend([
                f"- Discovery time: {metadata.get('execution_time_ms', 0):.1f}ms",
                f"- Server: {metadata.get('mcp_server_url', 'unknown')}",
                f"- Timestamp: {metadata.get('timestamp', 'unknown')}"
            ])
        
        if parsed["structured_data"]:
            response_parts.extend([
                "",
                "🔧 **Tool Capabilities Summary:**"
            ])
            # Extract tool count information from structured data
            for key, value in parsed["structured_data"].items():
                if isinstance(value, (int, str)):
                    response_parts.append(f"- {key}: {value}")
        
        if parsed["reflection_notes"]:
            response_parts.extend([
                "",
                "💭 **Tool Analysis Notes:**"
            ])
            response_parts.extend([f"- {note}" for note in parsed["reflection_notes"]])
        
        # Add guidance for tool usage
        response_parts.extend([
            "",
            "📝 **Tool Usage Guidance:**",
            "- Use specific tool names when calling MCP server",
            "- Check tool descriptions for parameter requirements",
            "- Consider tool categories for workflow organization",
            "- Monitor execution times for performance optimization"
        ])
        
        return "\n".join(response_parts)
    else:
        error_response = [
            "❌ **Tool Discovery Failed**",
            "",
            f"Error: {parsed['content']}"
        ]
        
        if parsed["metadata"]:
            error_response.extend([
                "",
                f"Discovery attempt time: {parsed['metadata'].get('execution_time_ms', 0):.1f}ms"
            ])
        
        return "\n".join(error_response)


async def get_tool_metadata(
    tool_name: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """
    Get detailed metadata for a specific HACS tool.
    
    This tool provides comprehensive information about a specific tool's
    capabilities, parameters, and usage patterns for better agent decision-making.
    
    Args:
        tool_name: Name of the tool to get metadata for
    
    Returns:
        Detailed tool metadata with reflection notes for agent use
    """
    configuration = Configuration.from_runnable_config(config)
    start_time = datetime.now()
    
    # First get the tool list to find our tool
    list_result = await call_mcp_server(
        params={
            "name": "list_available_tools",
            "arguments": {}
        },
        config=config
    )
    
    execution_time = (datetime.now() - start_time).total_seconds() * 1000
    
    # Parse and analyze the tool list
    parsed = parse_tool_result(list_result)
    
    if parsed["success"]:
        content = parsed["content"]
        
        # Look for the specific tool in the content
        tool_found = False
        tool_info = []
        
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if tool_name in line and ('**' in line or '-' in line):
                tool_found = True
                tool_info.append(line)
                
                # Get the next few lines for description
                for j in range(1, 5):
                    if i + j < len(lines) and lines[i + j].strip():
                        tool_info.append(lines[i + j])
                    else:
                        break
                break
        
        if tool_found:
            response_parts = [
                f"🔧 **Tool Metadata: {tool_name}**",
                "",
                "📋 **Tool Information:**"
            ] + tool_info + [
                "",
                "📊 **Metadata Discovery:**",
                f"- Query time: {execution_time:.1f}ms",
                f"- Tool found in registry: Yes",
                f"- Discovery timestamp: {start_time.isoformat()}"
            ]
            
            # Add analysis based on tool name patterns
            analysis_notes = []
            if "create" in tool_name.lower():
                analysis_notes.append("This is a creation tool - likely modifies system state")
            elif "get" in tool_name.lower() or "discover" in tool_name.lower() or "list" in tool_name.lower():
                analysis_notes.append("This is a discovery/query tool - safe for exploration")
            elif "update" in tool_name.lower() or "modify" in tool_name.lower():
                analysis_notes.append("This is a modification tool - use with caution")
            elif "delete" in tool_name.lower() or "remove" in tool_name.lower():
                analysis_notes.append("This is a deletion tool - requires careful consideration")
            
            if "clinical" in tool_name.lower():
                analysis_notes.append("Clinical domain tool - healthcare-specific functionality")
            elif "admin" in tool_name.lower():
                analysis_notes.append("Administrative tool - system management functionality")
            
            if analysis_notes:
                response_parts.extend([
                    "",
                    "🔍 **Tool Analysis:**"
                ] + [f"- {note}" for note in analysis_notes])
            
            return "\n".join(response_parts)
        else:
            return f"❌ **Tool Not Found: {tool_name}**\n\nThe tool '{tool_name}' was not found in the available tools list.\nUse `list_available_tools()` to see available tools."
    else:
        return f"❌ **Tool Metadata Discovery Failed**\n\nError retrieving tool list: {parsed['content']}"


# Export the enhanced tools for use by the agent
def get_enhanced_hacs_tools():
    """Get all enhanced HACS tools with metadata support."""
    return [
        discover_hacs_resources,
        create_clinical_template,
        list_available_tools,
        get_tool_metadata
    ]