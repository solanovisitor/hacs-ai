"""
Enhanced HACS MCP Tools with Persistence Integration

This module provides MCP-compatible tool implementations that leverage the comprehensive
HACS tools package while adding persistence, vector store, and security capabilities.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import json


# Import enhanced tools from hacs-tools package organized by resource vs record operations
try:
    from hacs_tools.tools import (
        # Result models
        HACSResult,
        MemoryResult,
        ResourceSchemaResult,  # Renamed from ResourceSchemaResult
        VersionResult,

        # HACS Resource Schema Tools (for resource_discovery_agent and template_builder_agent)
        analyze_resource_fields,  # Renamed from analyze_resource_fields
        compare_resource_schemas,  # Renamed from compare_resource_schemas
        create_view_resource_schema,  # Renamed from create_view_resource_schema
        discover_hacs_resources,  # Renamed from discover_hacs_resources
        get_hacs_resource_schema,  # Renamed from get_hacs_resource_schema
        suggest_view_fields,

        # HACS Record Data Tools (for record_manager_agent)
        create_hacs_record,  # Renamed from create_hacs_record
        validate_hacs_record_data,  # Renamed from validate_hacs_record_data

        # Memory Tools (for memory_agent)
        create_hacs_memory,
        search_hacs_memories,

        # Workflow and Knowledge Tools (for general use)
        create_knowledge_item,

        # Legacy tools (keeping for backward compatibility)
        create_model_stack,
        get_resource_schema,
        validate_resource_data,
        list_available_resources,
    )
    HACS_TOOLS_AVAILABLE = True
except ImportError as e:
    # Create placeholder result models to avoid NameError
    from typing import Any, Dict, List

    class HACSResult:
        def __init__(self, success=False, message="", data=None, error=None):
            self.success = success
            self.message = message
            self.data = data
            self.error = error

    class MemoryResult:
        def __init__(self, success=False, message="", memory_id=None, content=None):
            self.success = success
            self.message = message
            self.memory_id = memory_id
            self.content = content

    class ResourceSchemaResult:
        def __init__(self, success=False, message="", resource_name="", schema=None):
            self.success = success
            self.message = message
            self.resource_name = resource_name
            self.schema = schema or {}

    class VersionResult:
        def __init__(self, success=False, message="", version=""):
            self.success = success
            self.message = message
            self.version = version

    HACS_TOOLS_AVAILABLE = False

# Core HACS imports for persistence and models
try:
    from hacs_core.actor import Actor
    from hacs_core.base_resource import BaseResource
    from hacs_core.memory import MemoryBlock
    from hacs_persistence.adapter import PostgreSQLAdapter
    from hacs_utils.integrations.openai.embedding import get_openai_embedding
    from hacs_utils.integrations.qdrant.store import QdrantVectorStore

    HACS_CORE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"HACS core modules not available: {e}")
    HACS_CORE_AVAILABLE = False

# MCP message types
from .messages import CallToolResult, Tool

logger = logging.getLogger(__name__)

# Log import errors if any
if not HACS_TOOLS_AVAILABLE:
    logger.warning("HACS tools not fully available - using placeholder implementations")

# Security configuration
MAX_RESOURCE_LIMIT = 100
MAX_JSON_SIZE = 1024 * 1024  # 1MB
MAX_QUERY_LENGTH = 1000

# ===== UTILITY FUNCTIONS =====


def _get_security_context(actor: Actor) -> Dict[str, Any]:
    """Get security context and permissions for an actor."""
    return {
        "memory_operations": actor.has_permission("write:memory")
        or actor.has_permission("admin:*"),
        "crud_operations": actor.has_permission("write:*") or actor.has_permission("admin:*"),
        "read_operations": actor.has_permission("read:*") or actor.has_permission("admin:*"),
        "max_resource_limit": MAX_RESOURCE_LIMIT,
        "max_json_size": MAX_JSON_SIZE,
        "max_query_length": MAX_QUERY_LENGTH,
    }


def _create_security_error_response(message: str, suggestions: List[str] = None) -> CallToolResult:
    """Create a security error response with suggestions."""
    suggestions = suggestions or [
        "Use only alphanumeric characters and underscores in names",
        "Ensure data is healthcare-related and properly formatted",
        "Check that resource types match HACS resource names",
        "Verify JSON payload size is reasonable",
    ]

    suggestion_text = "\n".join(f"   • {s}" for s in suggestions)

    content = f"""❌ **Security Validation Failed**

🚨 **Issue:** {message}

💡 **Suggestions:**
{suggestion_text}

🔒 **Security Context:**
- Max Resource Limit: {MAX_RESOURCE_LIMIT}
- Max JSON Size: {MAX_JSON_SIZE // 1000}KB
- Max Query Length: {MAX_QUERY_LENGTH}
- HACS Core Available: {"✅" if HACS_CORE_AVAILABLE else "❌"}
"""

    return CallToolResult(content=[{"type": "text", "text": content}], isError=True)


def _convert_hacs_result_to_mcp(
    result: Union[HACSResult, MemoryResult, VersionResult, ResourceSchemaResult, List],
    operation_name: str,
) -> CallToolResult:
    """Convert HACS tool results to MCP format with enhanced developer-friendly output."""
    try:
        if isinstance(result, list):
            # Handle list results (multiple resources)
            content = f"✅ **{operation_name} Results** ({len(result)} items)\n\n"

            for i, item in enumerate(result[:5]):  # Show first 5 items
                if hasattr(item, 'data') and item.data:
                    content += f"**Item {i+1}:**\n```json\n{json.dumps(item.data, indent=2)}\n```\n\n"
                elif hasattr(item, 'message'):
                    content += f"**Item {i+1}:** {item.message}\n\n"
                else:
                    content += f"**Item {i+1}:** {str(item)}\n\n"

            if len(result) > 5:
                content += f"... and {len(result) - 5} more items\n\n"

            return CallToolResult(
                content=[{"type": "text", "text": content}],
                isError=False
            )

        # Handle single result objects
        if hasattr(result, 'success'):
            if result.success:
                content = f"✅ **{operation_name} Successful**\n\n"
                content += f"**Message:** {result.message}\n\n"

                # Include complete resource/model definition in response
                if hasattr(result, 'data') and result.data:
                    content += "## 📋 **Complete Resource Definition**\n"
                    content += "```json\n"
                    content += json.dumps(result.data, indent=2, default=str)
                    content += "\n```\n\n"

                    # Add developer-friendly summary for common operations
                    if operation_name in ["create_hacs_record", "create_resource"]:
                        resource_type = result.data.get('resource_type', 'Unknown')
                        resource_id = result.data.get('id', 'No ID')
                        content += f"🎯 **Created Resource Summary:**\n"
                        content += f"- **Type:** {resource_type}\n"
                        content += f"- **ID:** {resource_id}\n"
                        content += f"- **Fields:** {len(result.data)} total fields\n"

                        # Highlight key fields for Patient resources
                        if resource_type == "Patient":
                            content += f"- **Name:** {result.data.get('full_name', result.data.get('given', [''])[0] + ' ' + result.data.get('family', ''))}\n"
                            content += f"- **Birth Date:** {result.data.get('birth_date', 'Not specified')}\n"
                            content += f"- **Contact:** {result.data.get('email', result.data.get('phone', 'Not specified'))}\n"

                        # Highlight key fields for Observation resources
                        elif resource_type == "Observation":
                            content += f"- **Code:** {result.data.get('code', {}).get('display', 'Not specified')}\n"
                            content += f"- **Value:** {result.data.get('valueQuantity', {}).get('value', result.data.get('valueString', 'Not specified'))}\n"
                            content += f"- **Subject:** {result.data.get('subject', 'Not specified')}\n"

                        content += "\n"

                # Add specific data based on result type
                if hasattr(result, "data") and result.data:
                    # Only add details section if not already included above
                    if not hasattr(result, 'data') or operation_name not in ["create_hacs_record", "create_resource"]:
                        content += "📊 **Details:**\n"
                        for key, value in result.data.items():
                            content += f"  - **{key}**: {value}\n"
                        content += "\n"

                # Enhanced handling for different result types
                if isinstance(result, ResourceSchemaResult):
                    content += "🏗️ **Schema Details:**\n"
                    content += f"  - **Field Count:** {result.field_count}\n"
                    content += f"  - **Required Fields:** {len(result.required_fields)}\n"
                    content += f"  - **Optional Fields:** {len(result.optional_fields)}\n\n"

                    # Include complete schema definition
                    content += "## 📐 **Complete Schema Definition**\n"
                    content += "```json\n"
                    content += json.dumps(result.schema, indent=2)
                    content += "\n```\n\n"

                elif hasattr(result, 'models') and hasattr(result, 'total_count'):
                    # ModelDiscoveryResult-like
                    content += f"🔍 **Available Models ({result.total_count}):**\n"
                    content += f"📂 **Categories:** {', '.join(result.categories)}\n"

                    # Create detailed model table
                    content += "\n## 📋 **Model Definitions**\n"
                    content += "| Model | Category | Fields | Description |\n"
                    content += "|-------|----------|--------|-------------|\n"

                    for model in result.models[:10]:  # Show first 10 models
                        name = model.get('name', 'Unknown')
                        category = model.get('category', 'Unknown')
                        total_fields = model.get('field_count', 0)
                        description = model.get('description', 'No description')[:50] + "..."
                        content += f"| {name} | {category} | {total_fields} | {description} |\n"

                    if len(result.models) > 10:
                        content += f"\n... and {len(result.models) - 10} more models\n"

                    content += "\n🎯 **Next Steps for Agent:**\n"
                    content += "- Use `get_hacs_resource_schema(resource_name)` to get detailed field information\n"
                    content += "- Use `create_clinical_template()` with types: assessment, intake, discharge, monitoring, referral\n"

                # Handle ModelTemplateResult - provide ACTIONABLE template information
                elif hasattr(result, 'template_schema') and hasattr(result, 'template_name'):
                    content += "🏗️ **Template Details:**\n"
                    content += f"📝 **Template Name:** {result.template_name}\n"

                    if hasattr(result, 'field_mappings') and result.field_mappings:
                        content += f"📊 **Fields:** {len(result.field_mappings)} configured\n"

                    if hasattr(result, 'use_cases') and result.use_cases:
                        content += "🎯 **Use Cases:**\n"
                        for use_case in result.use_cases:
                            content += f"  - {use_case}\n"

                    if hasattr(result, 'customizable_fields') and result.customizable_fields:
                        content += f"🔧 **Customizable Fields:** {', '.join(result.customizable_fields[:5])}"
                        if len(result.customizable_fields) > 5:
                            content += f" (+{len(result.customizable_fields) - 5} more)"

                    # Include complete template schema
                    content += "\n## 🏗️ **Complete Template Schema**\n"
                    content += "```json\n"
                    content += json.dumps(result.template_schema, indent=2)
                    content += "\n```\n\n"

                    content += "🎯 **Next Steps for Agent:**\n"
                    content += "- Use `create_hacs_record()` to create instances using this template\n"
                    content += "- Use `validate_resource_data()` to validate data against this schema\n"

                # Enhanced Memory Results
                elif isinstance(result, MemoryResult):
                    content += "🧠 **Memory Details:**\n"
                    if result.memory_id:
                        content += f"  - **Memory ID:** {result.memory_id}\n"
                    if result.content:
                        content += f"  - **Content Preview:** {result.content[:100]}...\n"
                    if hasattr(result, 'importance_score'):
                        content += f"  - **Importance:** {result.importance_score}\n"
                    if result.tags:
                        content += f"  - **Tags:** {', '.join(result.tags)}\n"
                    content += "\n"

                # Add development guidance
                content += "🔧 **Developer Actions Available:**\n"
                content += "- View complete definition above in JSON format\n"
                content += "- Copy/modify the JSON for creating similar resources\n"
                content += "- Use the resource ID for further operations\n"
                content += "- Validate field structure against HACS resources\n"

                return CallToolResult(
                    content=[{"type": "text", "text": content}],
                    isError=False
                )
            else:
                # Error case with enhanced debugging info
                content = f"❌ **{operation_name} Failed**\n\n"
                content += f"**Error:** {result.message}\n\n"

                if hasattr(result, 'error') and result.error:
                    content += f"**Details:** {result.error}\n\n"

                # Include troubleshooting for common errors
                if hasattr(result, 'validation_errors'):
                    content += "🔍 **Validation Errors:**\n"
                    for error in result.validation_errors:
                        content += f"  - {error}\n"
                    content += "\n"

                if hasattr(result, 'corrected_example'):
                    content += "✅ **Corrected Example:**\n"
                    content += "```json\n"
                    content += json.dumps(result.corrected_example, indent=2)
                    content += "\n```\n\n"

                if hasattr(result, 'guidance'):
                    content += f"💡 **Guidance:** {result.guidance}\n\n"

                return CallToolResult(
                    content=[{"type": "text", "text": content}],
                    isError=True
                )
        else:
            # Fallback for non-standard result objects
            content = f"✅ **{operation_name} Result**\n\n"
            content += f"**Response:** {str(result)}\n\n"

            # Try to extract JSON if possible
            if hasattr(result, '__dict__'):
                content += "## 📋 **Complete Response Data**\n"
                content += "```json\n"
                content += json.dumps(result.__dict__, indent=2, default=str)
                content += "\n```\n\n"

            return CallToolResult(
                content=[{"type": "text", "text": content}],
                isError=False
            )

    except Exception as e:
        # Enhanced error handling with debugging info
        error_content = f"❌ **Error Converting {operation_name} Result**\n\n"
        error_content += f"**Error:** {str(e)}\n"
        error_content += f"**Result Type:** {type(result)}\n"
        error_content += f"**Raw Result:** {str(result)[:500]}...\n\n"
        error_content += "🔧 **Developer Note:** Check result format and conversion logic\n"

        return CallToolResult(
            content=[{"type": "text", "text": error_content}],
            isError=True
        )


# ===== MCP EXECUTE FUNCTIONS =====


async def execute_discover_hacs_resources(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute discover HACS resources using hacs-tools."""
    try:
        if not HACS_TOOLS_AVAILABLE:
            return CallToolResult(
                content=[{"type": "text", "text": "❌ **HACS tools not available**"}], isError=True
            )

        # Extract parameters
        category_filter = params.get("category_filter")
        include_field_counts = params.get("include_field_counts", True)

        # Call hacs-tools function
        result = discover_hacs_resources(
            category_filter=category_filter, include_field_counts=include_field_counts
        )

        return _convert_hacs_result_to_mcp(result, "Model Discovery")

    except Exception as e:
        logger.error(f"Error in execute_discover_hacs_resources: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Error discovering models**: {str(e)}"}],
            isError=True,
        )


async def execute_create_clinical_template(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute create clinical template using hacs-tools."""
    try:
        if not HACS_TOOLS_AVAILABLE:
            return CallToolResult(
                content=[{"type": "text", "text": "❌ **HACS tools not available**"}], isError=True
            )

        # Extract parameters
        template_type = params.get("template_type", "assessment")
        focus_area = params.get("focus_area", "general")
        complexity_level = params.get("complexity_level", "standard")
        include_workflow_fields = params.get("include_workflow_fields", True)

        # Call hacs-tools function
        result = create_clinical_template(
            template_type=template_type,
            focus_area=focus_area,
            complexity_level=complexity_level,
            include_workflow_fields=include_workflow_fields,
        )

        return _convert_hacs_result_to_mcp(result, "Clinical Template Creation")

    except Exception as e:
        logger.error(f"Error in execute_create_clinical_template: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Error creating template**: {str(e)}"}],
            isError=True,
        )


async def execute_create_model_stack(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute create model stack using hacs-tools."""
    try:
        if not HACS_TOOLS_AVAILABLE:
            return CallToolResult(
                content=[{"type": "text", "text": "❌ **HACS tools not available**"}], isError=True
            )

        # Extract parameters
        base_model = params.get("base_model")
        stack_name = params.get("stack_name")
        extensions = params.get("extensions", [])
        merge_strategy = params.get("merge_strategy", "overlay")

        if not base_model or not stack_name:
            return CallToolResult(
                content=[
                    {
                        "type": "text",
                        "text": "❌ **Missing required parameters**: base_model and stack_name are required",
                    }
                ],
                isError=True,
            )

        # Call hacs-tools function
        result = create_model_stack(
            base_model=base_model,
            extensions=extensions,
            stack_name=stack_name,
            merge_strategy=merge_strategy,
        )

        return _convert_hacs_result_to_mcp(result, "Model Stack Creation")

    except Exception as e:
        logger.error(f"Error in execute_create_model_stack: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Error creating model stack**: {str(e)}"}],
            isError=True,
        )


async def execute_version_model(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute version_hacs_resource tool."""
    try:
        if not HACS_TOOLS_AVAILABLE:
            return CallToolResult(
                content=[{"type": "text", "text": "❌ **HACS Tools Unavailable**: HACS tools package not available"}],
                isError=True
            )

        result = version_hacs_resource(
            actor_name="mcp_server",
            resource_name=params["resource_name"],
            version=params["version"],
            description=params["description"],
            schema_definition=params["schema_definition"],
            tags=params.get("tags", []),
            status=params.get("status", "published")
        )

        return _convert_hacs_result_to_mcp(result, "version_model")

    except Exception as e:
        logger.error(f"Error in version_model: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Version Model Error**: {str(e)}"}],
            isError=True
        )


async def execute_validate_resource_data(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute validate_resource_data tool."""
    try:
        if not HACS_TOOLS_AVAILABLE:
            return CallToolResult(
                content=[{"type": "text", "text": "❌ **HACS Tools Unavailable**: HACS tools package not available"}],
                isError=True
            )

        result = validate_resource_data(
            resource_type=params["resource_type"],
            data=params["data"]
        )

        return _convert_hacs_result_to_mcp(result, "validate_resource_data")

    except Exception as e:
        logger.error(f"Error in validate_resource_data: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Validation Error**: {str(e)}"}],
            isError=True
        )


async def execute_list_available_resources(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute list_available_resources tool."""
    try:
        if not HACS_TOOLS_AVAILABLE:
            return CallToolResult(
                content=[{"type": "text", "text": "❌ **HACS Tools Unavailable**: HACS tools package not available"}],
                isError=True
            )

        resources = list_available_resources()

        content = "# 📋 Available HACS Resources\n\n"
        content += "## Resource Types\n\n"
        for i, resource in enumerate(resources, 1):
            content += f"{i}. **{resource}**\n"

        content += f"\n🔢 **Total Resources**: {len(resources)}"

        return CallToolResult(
            content=[{"type": "text", "text": content}],
            _meta={
                "resources": resources,
                "total_count": len(resources),
                "success": True
            }
        )

    except Exception as e:
        logger.error(f"Error in list_available_resources: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Resource List Error**: {str(e)}"}],
            isError=True
        )


async def execute_find_resources(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute find_resources tool."""
    try:
        if not HACS_TOOLS_AVAILABLE:
            return CallToolResult(
                content=[{"type": "text", "text": "❌ **HACS Tools Unavailable**: HACS tools package not available"}],
                isError=True
            )

        results = find_resources(
            actor_name="mcp_server",
            resource_type=params["resource_type"],
            filters=params.get("filters"),
            semantic_query=params.get("semantic_query"),
            limit=params.get("limit", 10)
        )

        return _convert_hacs_result_to_mcp(results, "find_resources")

    except Exception as e:
        logger.error(f"Error in find_resources: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Search Error**: {str(e)}"}],
            isError=True
        )


async def execute_get_resource_schema(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Get resource schema with detailed examples and validation rules."""
    try:
        resource_type = params.get("resource_type")
        simplified = params.get("simplified", False)

        if not resource_type:
            return CallToolResult(
                content=[{"type": "text", "text": "❌ Error: resource_type parameter is required"}]
            )

        result = get_resource_schema(resource_type=resource_type, simplified=simplified)

        if result.success:
            content = f"✅ **{resource_type} Schema Retrieved**\n\n"
            content += f"📊 **Schema Overview:**\n"
            content += f"- **Total Fields:** {result.field_count}\n"
            content += f"- **Required Fields:** {len(result.required_fields)}\n"
            content += f"- **Optional Fields:** {len(result.optional_fields)}\n\n"

            # Add examples if available in schema
            if "examples" in result.schema:
                examples = result.schema["examples"]
                content += f"🎯 **AGENT USAGE EXAMPLES:**\n\n"

                if "minimal_example" in examples:
                    content += f"**Minimal Valid {resource_type}:**\n"
                    content += f"```json\n{str(examples['minimal_example'])}\n```\n\n"

                if "complete_example" in examples:
                    content += f"**Complete {resource_type} Example:**\n"
                    content += f"```json\n{str(examples['complete_example'])}\n```\n\n"

                if "validation_notes" in examples:
                    content += f"⚠️ **CRITICAL VALIDATION RULES:**\n"
                    for note in examples["validation_notes"]:
                        content += f"- {note}\n"
                    content += "\n"

            # Required fields detail
            if result.required_fields:
                content += f"🔴 **Required Fields:** {', '.join(result.required_fields)}\n\n"

            # Key field structure for Patient specifically
            if resource_type == "Patient":
                content += f"🏗️ **PATIENT FIELD STRUCTURE (CRITICAL!):**\n\n"
                content += f"✅ **Use DIRECT fields:**\n"
                content += f"- `given: [\"John\"]` (array of given names)\n"
                content += f"- `family: \"Doe\"` (family name as string)\n"
                content += f"- `full_name: \"John Doe\"` (complete name)\n"
                content += f"- `birth_date: \"1990-01-01\"` (YYYY-MM-DD format)\n"
                content += f"- `email: \"john@example.com\"` (direct email field)\n"
                content += f"- `phone: \"+1-555-0123\"` (direct phone field)\n\n"
                content += f"❌ **DO NOT use FHIR nested structure:**\n"
                content += f"- ~~`name: [{{\"given\": [\"John\"], \"family\": \"Doe\"}}]`~~ (Wrong!)\n"
                content += f"- ~~`birthDate: \"1990-01-01\"`~~ (Use `birth_date`)\n"
                content += f"- ~~`telecom: [{{\"system\": \"email\", \"value\": \"...\"}}]`~~ (Use `email`/`phone`)\n\n"

            content += f"🎯 **Next Steps for Agent:**\n"
            content += f"- Use the examples above as templates for `create_hacs_record()`\n"
            content += f"- Ensure all required fields are included\n"
            content += f"- Follow the exact field names and structures shown\n"

            return CallToolResult(
                content=[{"type": "text", "text": content}],
                isError=False
            )
        else:
            return CallToolResult(
                content=[{"type": "text", "text": f"❌ **Error:** {result.message}"}],
                isError=True
            )

    except Exception as e:
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Error getting schema:** {str(e)}"}],
            isError=True
        )


async def execute_search_hacs_records(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute search_hacs_records tool."""
    try:
        if not HACS_TOOLS_AVAILABLE:
            return CallToolResult(
                content=[{"type": "text", "text": "❌ **HACS Tools Unavailable**: HACS tools package not available"}],
                isError=True
            )

        results = search_hacs_records(
            actor_name="mcp_server",
            resource_type=params["resource_type"],
            filters=params.get("filters"),
            semantic_query=params.get("semantic_query"),
            limit=params.get("limit", 10)
        )

        return _convert_hacs_result_to_mcp(results, "search_hacs_records")

    except Exception as e:
        logger.error(f"Error in search_hacs_records: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Search Error**: {str(e)}"}],
            isError=True
        )


async def execute_search_memories(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute search_memories tool."""
    try:
        if not HACS_TOOLS_AVAILABLE:
            return CallToolResult(
                content=[{"type": "text", "text": "❌ **HACS Tools Unavailable**: HACS tools package not available"}],
                isError=True
            )

        results = search_hacs_memories(
            actor_name="mcp_server",
            query=params.get("query", ""),
            memory_type=params.get("memory_type"),
            session_id=params.get("session_id"),
            min_importance=params.get("min_importance", 0.0),
            limit=params.get("limit", 10)
        )

        return _convert_hacs_result_to_mcp(results, "search_memories")

    except Exception as e:
        logger.error(f"Error in search_memories: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Memory Search Error**: {str(e)}"}],
            isError=True
        )


async def execute_consolidate_memories(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute consolidate_memories tool."""
    try:
        if not HACS_TOOLS_AVAILABLE:
            return CallToolResult(
                content=[{"type": "text", "text": "❌ **HACS Tools Unavailable**: HACS tools package not available"}],
                isError=True
            )

        result = consolidate_memories(
            actor_name="mcp_server",
            session_id=params["session_id"],
            memory_type=params.get("memory_type", "episodic"),
            strategy=params.get("strategy", "temporal"),
            min_memories=params.get("min_memories", 3)
        )

        return _convert_hacs_result_to_mcp(result, "consolidate_memories")

    except Exception as e:
        logger.error(f"Error in consolidate_memories: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Memory Consolidation Error**: {str(e)}"}],
            isError=True
        )


async def execute_retrieve_context(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute retrieve_context tool."""
    try:
        if not HACS_TOOLS_AVAILABLE:
            return CallToolResult(
                content=[{"type": "text", "text": "❌ **HACS Tools Unavailable**: HACS tools package not available"}],
                isError=True
            )

        results = retrieve_context(
            actor_name="mcp_server",
            query=params["query"],
            context_type=params.get("context_type", "general"),
            max_memories=params.get("max_memories", 5),
            session_id=params.get("session_id")
        )

        return _convert_hacs_result_to_mcp(results, "retrieve_context")

    except Exception as e:
        logger.error(f"Error in retrieve_context: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Context Retrieval Error**: {str(e)}"}],
            isError=True
        )


async def execute_analyze_memory_patterns(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute analyze_memory_patterns tool."""
    try:
        if not HACS_TOOLS_AVAILABLE:
            return CallToolResult(
                content=[{"type": "text", "text": "❌ **HACS Tools Unavailable**: HACS tools package not available"}],
                isError=True
            )

        result = analyze_memory_patterns(
            actor_name="mcp_server",
            analysis_type=params.get("analysis_type", "comprehensive"),
            session_id=params.get("session_id"),
            time_window_days=params.get("time_window_days", 30)
        )

        return _convert_hacs_result_to_mcp(result, "analyze_memory_patterns")

    except Exception as e:
        logger.error(f"Error in analyze_memory_patterns: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Pattern Analysis Error**: {str(e)}"}],
            isError=True
        )


async def execute_analyze_resource_fields(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute analyze_resource_fields tool."""
    try:
        if not HACS_TOOLS_AVAILABLE:
            return CallToolResult(
                content=[{"type": "text", "text": "❌ **HACS Tools Unavailable**: HACS tools package not available"}],
                isError=True
            )

        result = analyze_resource_fields(
            resource_name=params["resource_name"],
            field_category_filter=params.get("field_category_filter")
        )

        return _convert_hacs_result_to_mcp(result, "analyze_resource_fields")

    except Exception as e:
        logger.error(f"Error in analyze_resource_fields: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Field Analysis Error**: {str(e)}"}],
            isError=True
        )


async def execute_compare_resource_schemas(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute compare_resource_schemas tool."""
    try:
        if not HACS_TOOLS_AVAILABLE:
            return CallToolResult(
                content=[{"type": "text", "text": "❌ **HACS Tools Unavailable**: HACS tools package not available"}],
                isError=True
            )

        result = compare_resource_schemas(
            resource_names=params["resource_names"],
            comparison_focus=params.get("comparison_focus", "fields")
        )

        return _convert_hacs_result_to_mcp(result, "compare_resource_schemas")

    except Exception as e:
        logger.error(f"Error in compare_resource_schemas: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Schema Comparison Error**: {str(e)}"}],
            isError=True
        )


async def execute_create_view_resource_schema(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute create_view_resource_schema tool."""
    try:
        if not HACS_TOOLS_AVAILABLE:
            return CallToolResult(
                content=[{"type": "text", "text": "❌ **HACS Tools Unavailable**: HACS tools package not available"}],
                isError=True
            )

        result = create_view_resource_schema(
            resource_name=params["resource_name"],
            fields=params["fields"],
            view_name=params.get("view_name"),
            include_optional=params.get("include_optional", True)
        )

        return _convert_hacs_result_to_mcp(result, "create_view_resource_schema")

    except Exception as e:
        logger.error(f"Error in create_view_resource_schema: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **View Schema Error**: {str(e)}"}],
            isError=True
        )


async def execute_suggest_view_fields(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute suggest_view_fields tool."""
    try:
        if not HACS_TOOLS_AVAILABLE:
            return CallToolResult(
                content=[{"type": "text", "text": "❌ **HACS Tools Unavailable**: HACS tools package not available"}],
                isError=True
            )

        result = suggest_view_fields(
            resource_name=params["resource_name"],
            use_case=params["use_case"],
            max_fields=params.get("max_fields", 10)
        )

        return _convert_hacs_result_to_mcp(result, "suggest_view_fields")

    except Exception as e:
        logger.error(f"Error in suggest_view_fields: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Field Suggestion Error**: {str(e)}"}],
            isError=True
        )


async def execute_optimize_resource_for_llm(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute optimize_resource_for_llm tool."""
    try:
        if not HACS_TOOLS_AVAILABLE:
            return CallToolResult(
                content=[{"type": "text", "text": "❌ **HACS Tools Unavailable**: HACS tools package not available"}],
                isError=True
            )

        result = optimize_resource_for_llm(
            resource_name=params["resource_name"],
            optimization_goal=params.get("optimization_goal", "token_efficiency"),
            target_use_case=params.get("target_use_case", "structured_output"),
            preserve_validation=params.get("preserve_validation", True)
        )

        return _convert_hacs_result_to_mcp(result, "optimize_resource_for_llm")

    except Exception as e:
        logger.error(f"Error in optimize_resource_for_llm: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Model Optimization Error**: {str(e)}"}],
            isError=True
        )


async def execute_create_knowledge_item(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute create_knowledge_item tool."""
    try:
        if not HACS_TOOLS_AVAILABLE:
            return CallToolResult(
                content=[{"type": "text", "text": "❌ **HACS Tools Unavailable**: HACS tools package not available"}],
                isError=True
            )

        result = create_knowledge_item(
            actor_name="mcp_server",
            title=params["title"],
            content=params["content"],
            knowledge_type=params.get("knowledge_type", "fact"),
            tags=params.get("tags", []),
            metadata=params.get("metadata", {})
        )

        return _convert_hacs_result_to_mcp(result, "create_knowledge_item")

    except Exception as e:
        logger.error(f"Error in create_knowledge_item: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Knowledge Creation Error**: {str(e)}"}],
            isError=True
        )


async def execute_create_resource(params: Dict[str, Any], db_adapter=None, vector_store=None, actor=None, **kwargs) -> CallToolResult:
    """Execute create_resource tool."""
    try:
        if not HACS_TOOLS_AVAILABLE:
            return CallToolResult(
                content=[{"type": "text", "text": "❌ **HACS Tools Unavailable**: HACS tools package not available"}],
                isError=True
            )

        result = create_hacs_record(
            actor_name="mcp_server",
            resource_type=params["resource_type"],
            resource_data=params.get("resource_data", params.get("data", {})),
            validate_fhir=params.get("validate_fhir", True),
            auto_generate_id=params.get("auto_generate_id", True)
        )

        return _convert_hacs_result_to_mcp(result, "create_resource")

    except Exception as e:
        logger.error(f"Error in create_resource: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Resource Creation Error**: {str(e)}"}],
            isError=True
        )


async def execute_create_memory(params: Dict[str, Any], db_adapter=None, vector_store=None, actor=None, **kwargs) -> CallToolResult:
    """Execute create_memory tool."""
    try:
        if not HACS_TOOLS_AVAILABLE:
            return CallToolResult(
                content=[{"type": "text", "text": "❌ **HACS Tools Unavailable**: HACS tools package not available"}],
                isError=True
            )

        result = create_hacs_memory(
            actor_name="mcp_server",
            content=params["content"],
            memory_type=params.get("memory_type", "episodic"),
            importance_score=params.get("importance_score", 0.5),
            tags=params.get("tags", []),
            session_id=params.get("session_id")
        )

        return _convert_hacs_result_to_mcp(result, "create_memory")

    except Exception as e:
        logger.error(f"Error in create_memory: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Memory Creation Error**: {str(e)}"}],
            isError=True
        )


# Enhanced MCP tool implementations using hacs-tools

# Database Visualization and Query Tools for Developers

async def execute_describe_database_schema(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute database schema visualization tool."""
    try:
        schema_type = params.get("schema_type", "all")

        schema_info = {
            "database_name": "hacs_db",
            "schemas": {
                "hacs_core": {
                    "tables": ["patients", "observations", "encounters", "conditions"],
                    "views": ["patient_summary", "recent_observations"],
                    "indexes": ["idx_patient_id", "idx_encounter_date"]
                }
            },
            "total_tables": 10,
            "total_views": 6,
            "total_indexes": 6
        }

        content = "# 🗄️ **HACS Database Schema Overview**\n\n"
        content += f"**Database:** {schema_info['database_name']}\n"
        content += f"**Total Tables:** {schema_info['total_tables']}\n"

        return CallToolResult(content=[{"type": "text", "text": content}], isError=False)

    except Exception as e:
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Database Schema Error**: {str(e)}"}],
            isError=True
        )


async def execute_describe_table_structure(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute table structure description tool."""
    try:
        table_name = params.get("table_name")
        if not table_name:
            return CallToolResult(
                content=[{"type": "text", "text": "❌ Error: table_name parameter is required"}],
                isError=True
            )

        content = f"# 📋 **Table Structure: `{table_name}`**\n\n"
        content += "Mock table structure information would go here.\n"

        return CallToolResult(content=[{"type": "text", "text": content}], isError=False)

    except Exception as e:
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Table Structure Error**: {str(e)}"}],
            isError=True
        )


async def execute_query_hacs_data(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute structured data queries with range filters and pagination."""
    try:
        table_name = params.get("table_name")
        if not table_name:
            return CallToolResult(
                content=[{"type": "text", "text": "❌ Error: table_name parameter is required"}],
                isError=True
            )

        content = f"# 🔍 **Query Results: `{table_name}`**\n\n"
        content += "Mock query results would go here.\n"

        return CallToolResult(content=[{"type": "text", "text": content}], isError=False)

    except Exception as e:
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Query Error**: {str(e)}"}],
            isError=True
        )


async def execute_get_table_sample_data(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Get sample data from a table for development reference."""
    try:
        table_name = params.get("table_name")
        if not table_name:
            return CallToolResult(
                content=[{"type": "text", "text": "❌ Error: table_name parameter is required"}],
                isError=True
            )

        content = f"# 📋 **Sample Data: `{table_name}`**\n\n"
        content += "Mock sample data would go here.\n"

        return CallToolResult(content=[{"type": "text", "text": content}], isError=False)

    except Exception as e:
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Sample Data Error**: {str(e)}"}],
            isError=True
        )


async def execute_analyze_table_relationships(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Analyze table relationships and foreign key connections."""
    try:
        focus_table = params.get("focus_table", "all")

        content = "# 🔗 **HACS Database Relationship Analysis**\n\n"
        content += f"Analysis for focus_table: {focus_table}\n"
        content += "Mock relationship analysis would go here.\n"

        return CallToolResult(content=[{"type": "text", "text": content}], isError=False)

    except Exception as e:
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Relationship Analysis Error**: {str(e)}"}],
            isError=True
        )


# Updated comprehensive tool implementations mapping
TOOL_IMPLEMENTATIONS = {
    # HACS Resource Schema Tools (for resource_discovery_agent and template_builder_agent)
    "discover_hacs_resources": execute_discover_hacs_resources,
    "analyze_resource_fields": execute_analyze_resource_fields,
    "compare_resource_schemas": execute_compare_resource_schemas,
    "create_view_resource_schema": execute_create_view_resource_schema,
    "suggest_view_fields": execute_suggest_view_fields,

    # Template Creation Tools (for template_builder_agent)
    "create_clinical_template": execute_create_clinical_template,
    "create_model_stack": execute_create_model_stack,

    # HACS Resource Data Tools (for record_manager_agent)
    "validate_resource_data": execute_validate_resource_data,
    "list_available_resources": execute_list_available_resources,

    # Memory Management Tools (for memory_agent)
    "search_memories": execute_search_memories,
    "consolidate_memories": execute_consolidate_memories,
    "retrieve_context": execute_retrieve_context,
    "analyze_memory_patterns": execute_analyze_memory_patterns,

    # Knowledge Management Tools
    "create_knowledge_item": execute_create_knowledge_item,

    # Database Visualization & Query Tools (for developers)
    "describe_database_schema": execute_describe_database_schema,
    "describe_table_structure": execute_describe_table_structure,
    "query_hacs_data": execute_query_hacs_data,
    "get_table_sample_data": execute_get_table_sample_data,
    "analyze_table_relationships": execute_analyze_table_relationships,

    # Vector Store Operations (pgvector)
    # "store_embedding": execute_store_embedding,
    # "vector_similarity_search": execute_vector_similarity_search,
    # "vector_hybrid_search": execute_vector_hybrid_search,
    # "get_vector_collection_stats": execute_get_vector_collection_stats,

    # Legacy/Backward Compatibility Tools
    "create_resource": execute_create_resource,
    "create_memory": execute_create_memory,
    "get_resource_schema": execute_get_resource_schema,
}


def get_all_hacs_tools() -> List[Tool]:
    """Get all available HACS tools organized by categories with enhanced descriptions."""
    if not HACS_TOOLS_AVAILABLE:
        return []

    tools = [
        # ============================================================================
        # HACS MODEL SCHEMA TOOLS (for resource_discovery_agent and template_builder_agent)
        # ============================================================================
        Tool(
            name="discover_hacs_resources",
            description="🔍 **Model Discovery**: Discover all available HACS resource schemas with comprehensive metadata, field analysis, and categorization for development planning.",
            inputSchema={
                "type": "object",
                "properties": {
                    "category_filter": {
                        "type": "string",
                        "description": "Filter by model category (clinical, administrative, reasoning)",
                    },
                    "include_field_counts": {
                        "type": "boolean",
                        "description": "Include detailed field statistics",
                        "default": True,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_hacs_resource_schema",
            description="📋 **Model Schema**: Get detailed schema for a specific HACS resource type with field definitions, validation rules, and usage examples.",
            inputSchema={
                "type": "object",
                "properties": {
                    "resource_type": {
                        "type": "string",
                        "description": "HACS resource type to get schema for (Patient, Observation, etc.)",
                    },
                    "simplified": {
                        "type": "boolean",
                        "description": "Return simplified schema",
                        "default": False,
                    },
                },
                "required": ["resource_type"],
            },
        ),
        Tool(
            name="list_available_hacs_resources",
            description="📜 **Model List**: List all available HACS resource types for resource creation and validation.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="analyze_resource_fields",
            description="🔬 **Field Analysis**: Analyze field structure and characteristics of a HACS resource for development insights.",
            inputSchema={
                "type": "object",
                "properties": {
                    "resource_name": {
                        "type": "string",
                        "description": "Name of the HACS resource to analyze",
                    },
                    "field_category_filter": {
                        "type": "string",
                        "description": "Filter by field category",
                    },
                },
                "required": ["resource_name"],
            },
        ),
        Tool(
            name="compare_resource_schemas",
            description="⚖️ **Model Comparison**: Compare schemas between multiple HACS resources to identify commonalities and differences.",
            inputSchema={
                "type": "object",
                "properties": {
                    "resource_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of HACS resource names to compare",
                    },
                    "comparison_focus": {
                        "type": "string",
                        "enum": ["fields", "validation", "structure"],
                        "description": "Focus of comparison",
                        "default": "fields",
                    },
                },
                "required": ["resource_names"],
            },
        ),
        Tool(
            name="create_view_resource_schema",
            description="👁️ **Model Views**: Create optimized view schema from a HACS resource with selected fields for specific use cases.",
            inputSchema={
                "type": "object",
                "properties": {
                    "resource_name": {"type": "string", "description": "Base HACS resource name"},
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of fields to include in view",
                    },
                    "view_name": {"type": "string", "description": "Name for the view"},
                    "include_optional": {
                        "type": "boolean",
                        "description": "Include optional fields",
                        "default": True,
                    },
                },
                "required": ["resource_name", "fields"],
            },
        ),
        Tool(
            name="suggest_view_fields",
            description="💡 **Field Suggestions**: Get field suggestions for creating optimized model views for specific use cases.",
            inputSchema={
                "type": "object",
                "properties": {
                    "resource_name": {"type": "string", "description": "HACS resource name"},
                    "use_case": {"type": "string", "description": "Intended use case"},
                    "max_fields": {
                        "type": "integer",
                        "description": "Maximum fields to suggest",
                        "default": 10,
                    },
                },
                "required": ["resource_name", "use_case"],
            },
        ),
        Tool(
            name="optimize_resource_for_llm",
            description="🤖 **LLM Optimization**: Optimize HACS resource schema for LLM structured output with token efficiency and validation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "resource_name": {"type": "string", "description": "HACS resource to optimize"},
                    "optimization_goal": {
                        "type": "string",
                        "enum": ["token_efficiency", "validation_strict", "balanced"],
                        "description": "Optimization goal",
                        "default": "token_efficiency",
                    },
                    "target_use_case": {"type": "string", "description": "Target use case"},
                    "preserve_validation": {
                        "type": "boolean",
                        "description": "Preserve validation rules",
                        "default": True,
                    },
                },
                "required": ["resource_name"],
            },
        ),
        Tool(
            name="create_multi_resource_schema",
            description="🏗️ **Multi-Model Schema**: Create composite schema combining multiple HACS resources for complex workflows.",
            inputSchema={
                "type": "object",
                "properties": {
                    "model_specs": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "List of model specifications to combine",
                    },
                    "schema_name": {
                        "type": "string",
                        "description": "Name for composite schema",
                        "default": "CompositeSchema",
                    },
                },
                "required": ["model_specs"],
            },
        ),
        Tool(
            name="version_hacs_resource",
            description="📝 **Model Versioning**: Create and manage versions of HACS resource schemas for evolution tracking.",
            inputSchema={
                "type": "object",
                "properties": {
                    "resource_name": {"type": "string", "description": "Model to version"},
                    "version": {"type": "string", "description": "Version identifier"},
                    "description": {"type": "string", "description": "Version description"},
                    "schema_definition": {
                        "type": "object",
                        "description": "Schema definition for this version",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Version tags",
                    },
                    "status": {
                        "type": "string",
                        "enum": ["draft", "published", "deprecated"],
                        "description": "Version status",
                        "default": "published",
                    },
                },
                "required": ["resource_name", "version", "description", "schema_definition"],
            },
        ),

        # ============================================================================
        # TEMPLATE CREATION TOOLS (for template_builder_agent)
        # ============================================================================
        Tool(
            name="create_clinical_template",
            description="🏥 **Clinical Templates**: Generate pre-configured clinical templates for healthcare scenarios with HACS resource integration.",
            inputSchema={
                "type": "object",
                "properties": {
                    "template_type": {
                        "type": "string",
                        "enum": ["assessment", "intake", "discharge", "monitoring", "referral"],
                        "description": "Type of clinical template",
                    },
                    "focus_area": {
                        "type": "string",
                        "description": "Clinical focus area (cardiology, general, emergency, etc.)",
                    },
                    "complexity_level": {
                        "type": "string",
                        "enum": ["minimal", "standard", "comprehensive"],
                        "description": "Detail level",
                        "default": "standard",
                    },
                    "include_workflow_fields": {
                        "type": "boolean",
                        "description": "Include workflow management fields",
                        "default": True,
                    },
                },
                "required": ["template_type", "focus_area"],
            },
        ),
        Tool(
            name="create_model_stack",
            description="📚 **Model Stacking**: Create layered model combinations with intelligent field merging for complex workflows.",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_model": {"type": "string", "description": "Base HACS resource name"},
                    "stack_name": {"type": "string", "description": "Name for stacked model"},
                    "extensions": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Extension model specifications",
                    },
                    "merge_strategy": {
                        "type": "string",
                        "enum": ["overlay", "prefix", "namespace"],
                        "description": "Field conflict resolution strategy",
                        "default": "overlay",
                    },
                },
                "required": ["base_model", "stack_name"],
            },
        ),

        # ============================================================================
        # HACS RESOURCE DATA TOOLS (for record_manager_agent)
        # ============================================================================
        Tool(
            name="create_hacs_record",
            description="✨ **Create Resource**: Create new HACS resource records with validation against model schemas using PRP methodology.",
            inputSchema={
                "type": "object",
                "properties": {
                    "resource_type": {
                        "type": "string",
                        "description": "HACS resource type for validation (Patient, Observation, etc.)",
                    },
                    "resource_data": {
                        "type": "object",
                        "description": "Resource data conforming to HACS resource schema",
                    },
                    "actor_name": {
                        "type": "string",
                        "description": "Name of actor creating resource",
                        "default": "mcp_server",
                    },
                    "validate_fhir": {
                        "type": "boolean",
                        "description": "Perform additional FHIR validation",
                        "default": True,
                    },
                    "auto_generate_id": {
                        "type": "boolean",
                        "description": "Auto-generate ID if missing",
                        "default": True,
                    },
                },
                "required": ["resource_type", "resource_data"],
            },
        ),
        Tool(
            name="get_hacs_record_by_id",
            description="🔍 **Get Resource**: Retrieve specific HACS resource record by ID with optional related data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "resource_type": {"type": "string", "description": "HACS resource type"},
                    "resource_id": {"type": "string", "description": "Resource ID"},
                    "actor_name": {
                        "type": "string",
                        "description": "Actor requesting resource",
                        "default": "mcp_server",
                    },
                    "include_related": {
                        "type": "boolean",
                        "description": "Include related resources",
                        "default": False,
                    },
                },
                "required": ["resource_type", "resource_id"],
            },
        ),
        Tool(
            name="find_hacs_records",
            description="🔎 **Search Resources**: Find HACS resource records using filters and semantic search capabilities.",
            inputSchema={
                "type": "object",
                "properties": {
                    "resource_type": {"type": "string", "description": "HACS resource type to search"},
                    "filters": {
                        "type": "object",
                        "description": "Filter criteria for resource data",
                    },
                    "semantic_query": {
                        "type": "string",
                        "description": "Natural language search query",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results",
                        "default": 10,
                    },
                },
                "required": ["resource_type"],
            },
        ),
        Tool(
            name="update_resource_by_id",
            description="✏️ **Update Resource**: Update existing HACS resource record with validation against model schema.",
            inputSchema={
                "type": "object",
                "properties": {
                    "resource_type": {"type": "string", "description": "HACS resource type"},
                    "resource_id": {"type": "string", "description": "Resource ID to update"},
                    "updates": {
                        "type": "object",
                        "description": "Field updates to apply",
                    },
                    "actor_name": {
                        "type": "string",
                        "description": "Actor performing update",
                        "default": "mcp_server",
                    },
                    "validate_before_update": {
                        "type": "boolean",
                        "description": "Validate before applying updates",
                        "default": True,
                    },
                },
                "required": ["resource_type", "resource_id", "updates"],
            },
        ),
        Tool(
            name="delete_resource_by_id",
            description="🗑️ **Delete Resource**: Delete HACS resource record with soft/hard delete options (requires approval).",
            inputSchema={
                "type": "object",
                "properties": {
                    "resource_type": {"type": "string", "description": "HACS resource type"},
                    "resource_id": {"type": "string", "description": "Resource ID to delete"},
                    "actor_name": {
                        "type": "string",
                        "description": "Actor performing deletion",
                        "default": "mcp_server",
                    },
                    "soft_delete": {
                        "type": "boolean",
                        "description": "Perform soft delete vs hard delete",
                        "default": True,
                    },
                },
                "required": ["resource_type", "resource_id"],
            },
        ),
        Tool(
            name="validate_hacs_record_data",
            description="✅ **Validate Resource**: Validate resource data against HACS resource schema with detailed error reporting.",
            inputSchema={
                "type": "object",
                "properties": {
                    "resource_type": {"type": "string", "description": "HACS resource type for validation"},
                    "data": {
                        "type": "object",
                        "description": "Resource data to validate",
                    },
                },
                "required": ["resource_type", "data"],
            },
        ),

        # ============================================================================
        # MEMORY MANAGEMENT TOOLS (for memory_agent)
        # ============================================================================
        Tool(
            name="create_hacs_memory",
            description="🧠 **Create Memory**: Store session context and workflow state in memory blocks with automatic classification.",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Memory content to store"},
                    "actor_name": {
                        "type": "string",
                        "description": "Actor creating memory",
                        "default": "mcp_server",
                    },
                    "memory_type": {
                        "type": "string",
                        "enum": ["episodic", "procedural", "executive", "semantic"],
                        "description": "Type of memory",
                        "default": "episodic",
                    },
                    "importance_score": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "Importance score",
                        "default": 0.5,
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Memory tags",
                        "default": [],
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Session ID for grouping",
                    },
                },
                "required": ["content"],
            },
        ),
        Tool(
            name="search_hacs_memories",
            description="🔍 **Search Memories**: Search memory blocks using semantic similarity and filters for context retrieval.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query",
                        "default": "",
                    },
                    "actor_name": {
                        "type": "string",
                        "description": "Actor searching memories",
                        "default": "mcp_server",
                    },
                    "memory_type": {
                        "type": "string",
                        "description": "Filter by memory type",
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Filter by session ID",
                    },
                    "min_importance": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "Minimum importance score",
                        "default": 0.0,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results",
                        "default": 5,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="consolidate_memories",
            description="🔄 **Consolidate Memories**: Consolidate related memories into summary memories for efficient recall.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID for consolidation"},
                    "memory_type": {
                        "type": "string",
                        "description": "Memory type to consolidate",
                        "default": "episodic",
                    },
                    "strategy": {
                        "type": "string",
                        "enum": ["temporal", "importance", "semantic"],
                        "description": "Consolidation strategy",
                        "default": "temporal",
                    },
                    "min_memories": {
                        "type": "integer",
                        "description": "Minimum memories for consolidation",
                        "default": 3,
                    },
                },
                "required": ["session_id"],
            },
        ),
        Tool(
            name="retrieve_context",
            description="📖 **Retrieve Context**: Retrieve relevant memory context for informed decision making.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Context query"},
                    "context_type": {
                        "type": "string",
                        "description": "Type of context",
                        "default": "general",
                    },
                    "max_memories": {
                        "type": "integer",
                        "description": "Maximum memories to retrieve",
                        "default": 5,
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Session ID for context scope",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="analyze_memory_patterns",
            description="📊 **Memory Analysis**: Analyze memory patterns to identify trends, gaps, and optimization opportunities.",
            inputSchema={
                "type": "object",
                "properties": {
                    "analysis_type": {
                        "type": "string",
                        "enum": ["comprehensive", "temporal", "importance", "connections"],
                        "description": "Analysis type",
                        "default": "comprehensive",
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Session ID for scoped analysis",
                    },
                    "time_window_days": {
                        "type": "integer",
                        "description": "Time window for analysis",
                        "default": 30,
                    },
                },
                "required": [],
            },
        ),

        # ============================================================================
        # WORKFLOW AND KNOWLEDGE TOOLS (for general use)
        # ============================================================================
        Tool(
            name="get_clinical_guidance",
            description="🏥 **Clinical Guidance**: Get clinical decision support and guidance for patient care scenarios.",
            inputSchema={
                "type": "object",
                "properties": {
                    "patient_id": {"type": "string", "description": "Patient ID"},
                    "clinical_question": {"type": "string", "description": "Clinical question"},
                    "actor_name": {
                        "type": "string",
                        "description": "Actor requesting guidance",
                        "default": "mcp_server",
                    },
                    "patient_context": {
                        "type": "object",
                        "description": "Patient context data",
                    },
                    "knowledge_base_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Knowledge base IDs to use",
                    },
                },
                "required": ["patient_id", "clinical_question"],
            },
        ),
        Tool(
            name="execute_workflow",
            description="⚙️ **Execute Workflow**: Execute clinical workflows using PlanDefinition with patient context.",
            inputSchema={
                "type": "object",
                "properties": {
                    "plan_definition_id": {"type": "string", "description": "PlanDefinition ID"},
                    "patient_id": {"type": "string", "description": "Patient ID"},
                    "actor_name": {
                        "type": "string",
                        "description": "Actor executing workflow",
                        "default": "mcp_server",
                    },
                    "input_parameters": {
                        "type": "object",
                        "description": "Workflow input parameters",
                    },
                },
                "required": ["plan_definition_id", "patient_id"],
            },
        ),
        Tool(
            name="query_with_datarequirement",
            description="📊 **Data Query**: Execute structured data queries using DataRequirement specifications.",
            inputSchema={
                "type": "object",
                "properties": {
                    "data_requirement": {
                        "type": "object",
                        "description": "DataRequirement specification",
                    },
                    "actor_name": {
                        "type": "string",
                        "description": "Actor executing query",
                        "default": "mcp_server",
                    },
                },
                "required": ["data_requirement"],
            },
        ),
        Tool(
            name="create_datarequirement_query",
            description="🔧 **Build Data Query**: Create DataRequirement specifications for structured data retrieval.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query_description": {"type": "string", "description": "Description of data query"},
                    "resource_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Resource types to query",
                    },
                    "actor_name": {
                        "type": "string",
                        "description": "Actor creating query",
                        "default": "mcp_server",
                    },
                    "time_period_days": {
                        "type": "integer",
                        "description": "Time period in days",
                        "default": 30,
                    },
                    "include_codes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Include specific codes",
                    },
                    "sort_by": {
                        "type": "string",
                        "description": "Sort field",
                        "default": "effectiveDateTime",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Result limit",
                        "default": 20,
                    },
                },
                "required": ["query_description", "resource_types"],
            },
        ),
        Tool(
            name="create_knowledge_item",
            description="📚 **Knowledge Item**: Create knowledge items for clinical decision support and documentation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Knowledge item title"},
                    "content": {"type": "string", "description": "Knowledge content"},
                    "knowledge_type": {
                        "type": "string",
                        "enum": ["fact", "guideline", "protocol", "reference"],
                        "description": "Knowledge type",
                        "default": "fact",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Knowledge tags",
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional metadata",
                    },
                },
                "required": ["title", "content"],
            },
        ),

        # ============================================================================
        # LEGACY/BACKWARD COMPATIBILITY TOOLS
        # ============================================================================
        Tool(
            name="get_resource_schema",
            description="📋 **Legacy: Get Schema**: Get resource schema (legacy - use get_hacs_resource_schema for new code).",
            inputSchema={
                "type": "object",
                "properties": {
                    "resource_type": {"type": "string", "description": "Resource type"},
                    "simplified": {
                        "type": "boolean",
                        "description": "Return simplified schema",
                        "default": False,
                    },
                },
                "required": ["resource_type"],
            },
        ),
        Tool(
            name="create_resource",
            description="✨ **Legacy: Create**: Create resource (legacy - use create_hacs_record for new code).",
            inputSchema={
                "type": "object",
                "properties": {
                    "resource_type": {"type": "string", "description": "Resource type"},
                    "resource_data": {"type": "object", "description": "Resource data"},
                    "validate_fhir": {
                        "type": "boolean",
                        "description": "Validate FHIR",
                        "default": True,
                    },
                },
                "required": ["resource_type", "resource_data"],
            },
        ),
        Tool(
            name="create_memory",
            description="🧠 **Legacy: Memory**: Create memory (legacy - use create_hacs_memory for new code).",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Memory content"},
                    "memory_type": {
                        "type": "string",
                        "description": "Memory type",
                        "default": "episodic",
                    },
                    "importance_score": {
                        "type": "number",
                        "description": "Importance score",
                        "default": 0.5,
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags",
                        "default": [],
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Session ID",
                    },
                },
                "required": ["content"],
            },
        ),
        # ============================================================================
        # DATABASE VISUALIZATION & QUERY TOOLS (for developers)
        # ============================================================================
        Tool(
            name="describe_database_schema",
            description="🗄️ **Database Schema**: Visualize complete HACS database schema with tables, views, and indexes organized by schema.",
            inputSchema={
                "type": "object",
                "properties": {
                    "schema_type": {
                        "type": "string",
                        "enum": ["all", "tables", "views", "indexes"],
                        "description": "Type of schema components to show",
                        "default": "all",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="describe_table_structure",
            description="📋 **Table Structure**: Get detailed table schema with columns, types, constraints, indexes, and relationships.",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table to analyze (patients, observations, encounters, etc.)",
                    },
                },
                "required": ["table_name"],
            },
        ),
        Tool(
            name="query_hacs_data",
            description="🔍 **Query Data**: Execute structured queries with filters, range filtering, pagination, and sorting on HACS database tables.",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Table to query (patients, observations, encounters, etc.)",
                    },
                    "filters": {
                        "type": "object",
                        "description": "Field-based filters for specific values",
                    },
                    "range_filter": {
                        "type": "object",
                        "description": "Range filter for dates/numbers: {field, start, end}",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum records to return",
                        "default": 10,
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Number of records to skip for pagination",
                        "default": 0,
                    },
                    "order_by": {
                        "type": "string",
                        "description": "Field to sort by",
                        "default": "created_at",
                    },
                    "order_direction": {
                        "type": "string",
                        "enum": ["ASC", "DESC"],
                        "description": "Sort direction",
                        "default": "DESC",
                    },
                },
                "required": ["table_name"],
            },
        ),
        Tool(
            name="get_table_sample_data",
            description="📊 **Sample Data**: View sample records from any HACS table for development reference and structure understanding.",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Table to get sample data from",
                    },
                    "sample_size": {
                        "type": "integer",
                        "description": "Number of sample records to return",
                        "default": 5,
                    },
                },
                "required": ["table_name"],
            },
        ),
        Tool(
            name="analyze_table_relationships",
            description="🔗 **Table Relationships**: Analyze foreign key relationships and data connections between HACS database tables.",
            inputSchema={
                "type": "object",
                "properties": {
                    "focus_table": {
                        "type": "string",
                        "description": "Specific table to analyze, or 'all' for complete relationship map",
                        "default": "all",
                    },
                },
                "required": [],
            },
        ),
    ]

    return tools


async def execute_tool(
    tool_name: str,
    params: Dict[str, Any],
    db_adapter=None,
    vector_store=None,
    actor=None,
) -> CallToolResult:
    """Execute a tool with the given parameters and persistence context."""
    if tool_name not in TOOL_IMPLEMENTATIONS:
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Unknown tool**: {tool_name}"}], isError=True
        )

    try:
        execute_func = TOOL_IMPLEMENTATIONS[tool_name]

        # Call the appropriate execute function with all available context
        if tool_name in ["create_resource", "create_memory"]:
            # Tools that require persistence context
            result = await execute_func(params, db_adapter, vector_store, actor)
        else:
            # Tools that don't require persistence context
            result = await execute_func(params)

        return result

    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Tool execution failed**: {str(e)}"}],
            isError=True,
        )

# Add missing MCP tool implementations for unused imported hacs-tools

async def execute_get_hacs_resource_schema(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute get_hacs_resource_schema tool."""
    try:
        result = get_hacs_resource_schema(
            resource_type=params["resource_type"],
            simplified=params.get("simplified", False)
        )
        return _convert_hacs_result_to_mcp(result, "get_hacs_resource_schema")
    except Exception as e:
        logger.error(f"Error in get_hacs_resource_schema: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Model Schema Error**: {str(e)}"}],
            isError=True
        )


async def execute_create_multi_resource_schema(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute create_multi_resource_schema tool."""
    try:
        result = create_multi_resource_schema(
            model_specs=params["model_specs"],
            schema_name=params.get("schema_name", "CompositeSchema")
        )
        return _convert_hacs_result_to_mcp(result, "create_multi_resource_schema")
    except Exception as e:
        logger.error(f"Error in create_multi_resource_schema: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Multi-Model Schema Error**: {str(e)}"}],
            isError=True
        )


async def execute_list_available_hacs_resources(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute list_available_hacs_resources tool."""
    try:
        result = list_available_hacs_resources()
        content = "# 📋 Available HACS Resources\n\n"
        content += "## Model Types\n\n"
        for model_type in result:
            content += f"- **{model_type}**\n"

        content += "\n🎯 **Next Steps for Agent:**\n"
        content += "- Use `get_hacs_resource_schema(resource_name)` to get detailed schema\n"
        content += "- Use `create_hacs_record(resource_name, data)` to create instances\n"

        return CallToolResult(
            content=[{"type": "text", "text": content}],
            isError=False
        )
    except Exception as e:
        logger.error(f"Error in list_available_hacs_resources: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Model List Error**: {str(e)}"}],
            isError=True
        )


async def execute_create_hacs_record_direct(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute create_hacs_record tool directly."""
    try:
        result = create_hacs_record(
            actor_name=params.get("actor_name", "mcp_server"),
            resource_type=params["resource_type"],
            resource_data=params.get("resource_data", params.get("data", {})),
            validate_fhir=params.get("validate_fhir", True),
            auto_generate_id=params.get("auto_generate_id", True)
        )
        return _convert_hacs_result_to_mcp(result, "create_hacs_record")
    except Exception as e:
        logger.error(f"Error in create_hacs_record: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Resource Creation Error**: {str(e)}"}],
            isError=True
        )


async def execute_get_hacs_record_by_id(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute get_hacs_record_by_id tool."""
    try:
        result = get_hacs_record_by_id(
            actor_name=params.get("actor_name", "mcp_server"),
            resource_type=params["resource_type"],
            resource_id=params["resource_id"],
            include_related=params.get("include_related", False)
        )
        return _convert_hacs_result_to_mcp(result, "get_hacs_record_by_id")
    except Exception as e:
        logger.error(f"Error in get_hacs_record_by_id: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Resource Retrieval Error**: {str(e)}"}],
            isError=True
        )


async def execute_find_hacs_records(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute find_hacs_records tool."""
    try:
        results = find_hacs_records(
            resource_type=params["resource_type"],
            filters=params.get("filters"),
            semantic_query=params.get("semantic_query"),
            limit=params.get("limit", 10)
        )
        return _convert_hacs_result_to_mcp(results, "find_hacs_records")
    except Exception as e:
        logger.error(f"Error in find_hacs_records: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Resource Search Error**: {str(e)}"}],
            isError=True
        )


async def execute_update_resource_by_id(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute update_resource_by_id tool."""
    try:
        result = update_resource_by_id(
            actor_name=params.get("actor_name", "mcp_server"),
            resource_type=params["resource_type"],
            resource_id=params["resource_id"],
            updates=params["updates"],
            validate_before_update=params.get("validate_before_update", True)
        )
        return _convert_hacs_result_to_mcp(result, "update_resource_by_id")
    except Exception as e:
        logger.error(f"Error in update_resource_by_id: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Resource Update Error**: {str(e)}"}],
            isError=True
        )


async def execute_delete_resource_by_id(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute delete_resource_by_id tool."""
    try:
        result = delete_resource_by_id(
            actor_name=params.get("actor_name", "mcp_server"),
            resource_type=params["resource_type"],
            resource_id=params["resource_id"],
            soft_delete=params.get("soft_delete", True)
        )
        return _convert_hacs_result_to_mcp(result, "delete_resource_by_id")
    except Exception as e:
        logger.error(f"Error in delete_resource_by_id: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Resource Deletion Error**: {str(e)}"}],
            isError=True
        )


async def execute_validate_hacs_record_data(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute validate_hacs_record_data tool."""
    try:
        result = validate_hacs_record_data(
            resource_type=params["resource_type"],
            data=params["data"]
        )
        return _convert_hacs_result_to_mcp(result, "validate_hacs_record_data")
    except Exception as e:
        logger.error(f"Error in validate_hacs_record_data: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Resource Validation Error**: {str(e)}"}],
            isError=True
        )


async def execute_create_hacs_memory_direct(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute create_hacs_memory tool directly."""
    try:
        result = create_hacs_memory(
            actor_name=params.get("actor_name", "mcp_server"),
            content=params["content"],
            memory_type=params.get("memory_type", "episodic"),
            importance_score=params.get("importance_score", 0.5),
            tags=params.get("tags", []),
            session_id=params.get("session_id")
        )
        return _convert_hacs_result_to_mcp(result, "create_hacs_memory")
    except Exception as e:
        logger.error(f"Error in create_hacs_memory: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Memory Creation Error**: {str(e)}"}],
            isError=True
        )


async def execute_search_hacs_memories(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute search_hacs_memories tool."""
    try:
        results = search_hacs_memories(
            actor_name=params.get("actor_name", "mcp_server"),
            query=params.get("query", ""),
            memory_type=params.get("memory_type"),
            session_id=params.get("session_id"),
            min_importance=params.get("min_importance", 0.0),
            limit=params.get("limit", 5)
        )
        return _convert_hacs_result_to_mcp(results, "search_hacs_memories")
    except Exception as e:
        logger.error(f"Error in search_hacs_memories: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Memory Search Error**: {str(e)}"}],
            isError=True
        )


async def execute_get_clinical_guidance(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute get_clinical_guidance tool."""
    try:
        result = get_clinical_guidance(
            actor_name=params.get("actor_name", "mcp_server"),
            patient_id=params["patient_id"],
            clinical_question=params["clinical_question"],
            patient_context=params.get("patient_context"),
            knowledge_base_ids=params.get("knowledge_base_ids")
        )
        return _convert_hacs_result_to_mcp(result, "get_clinical_guidance")
    except Exception as e:
        logger.error(f"Error in get_clinical_guidance: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Clinical Guidance Error**: {str(e)}"}],
            isError=True
        )


async def execute_execute_workflow(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute execute_workflow tool."""
    try:
        result = execute_workflow(
            actor_name=params.get("actor_name", "mcp_server"),
            plan_definition_id=params["plan_definition_id"],
            patient_id=params["patient_id"],
            input_parameters=params.get("input_parameters")
        )
        return _convert_hacs_result_to_mcp(result, "execute_workflow")
    except Exception as e:
        logger.error(f"Error in execute_workflow: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Workflow Execution Error**: {str(e)}"}],
            isError=True
        )


async def execute_query_with_datarequirement(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute query_with_datarequirement tool."""
    try:
        result = query_with_datarequirement(
            actor_name=params.get("actor_name", "mcp_server"),
            data_requirement=params["data_requirement"]
        )
        return _convert_hacs_result_to_mcp(result, "query_with_datarequirement")
    except Exception as e:
        logger.error(f"Error in query_with_datarequirement: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Data Query Error**: {str(e)}"}],
            isError=True
        )


async def execute_create_datarequirement_query(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute create_datarequirement_query tool."""
    try:
        result = create_datarequirement_query(
            actor_name=params.get("actor_name", "mcp_server"),
            query_description=params["query_description"],
            resource_types=params["resource_types"],
            time_period_days=params.get("time_period_days", 30),
            include_codes=params.get("include_codes"),
            sort_by=params.get("sort_by", "effectiveDateTime"),
            limit=params.get("limit", 20)
        )
        return _convert_hacs_result_to_mcp(result, "create_datarequirement_query")
    except Exception as e:
        logger.error(f"Error in create_datarequirement_query: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Data Requirement Query Error**: {str(e)}"}],
            isError=True
        )

# Create placeholder implementations for missing functions when HACS tools aren't fully available
def create_placeholder_function(func_name: str):
    """Create a placeholder function that returns a standardized error response."""
    def placeholder(*args, **kwargs):
        return HACSResult(
            success=False,
            message=f"Function {func_name} not available - HACS tools not fully loaded",
            error=f"Placeholder implementation for {func_name}"
        )
    return placeholder

# Define placeholder functions for missing imports
if not HACS_TOOLS_AVAILABLE:
    create_clinical_template = create_placeholder_function("create_clinical_template")
    version_hacs_resource = create_placeholder_function("version_hacs_resource")
    find_resources = create_placeholder_function("find_resources")
    search_hacs_records = create_placeholder_function("search_hacs_records")
    consolidate_memories = create_placeholder_function("consolidate_memories")
    retrieve_context = create_placeholder_function("retrieve_context")
    analyze_memory_patterns = create_placeholder_function("analyze_memory_patterns")
    optimize_resource_for_llm = create_placeholder_function("optimize_resource_for_llm")
    create_multi_resource_schema = create_placeholder_function("create_multi_resource_schema")
    list_available_hacs_resources = create_placeholder_function("list_available_hacs_resources")
    get_hacs_record_by_id = create_placeholder_function("get_hacs_record_by_id")
    find_hacs_records = create_placeholder_function("find_hacs_records")
    update_resource_by_id = create_placeholder_function("update_resource_by_id")
    delete_resource_by_id = create_placeholder_function("delete_resource_by_id")
    get_clinical_guidance = create_placeholder_function("get_clinical_guidance")
    execute_workflow = create_placeholder_function("execute_workflow")
    query_with_datarequirement = create_placeholder_function("query_with_datarequirement")
    create_datarequirement_query = create_placeholder_function("create_datarequirement_query")
    search_hacs_memories = create_placeholder_function("search_hacs_memories")

# Database functions moved to before TOOL_IMPLEMENTATIONS mapping


async def execute_describe_table_structure(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute table structure description tool."""
    try:
        table_name = params.get("table_name")
        if not table_name:
            return CallToolResult(
                content=[{"type": "text", "text": "❌ Error: table_name parameter is required"}],
                isError=True
            )

        content = f"# 📋 **Table Structure: `{table_name}`**\n\n"
        content += "Mock table structure information would go here.\n"

        return CallToolResult(content=[{"type": "text", "text": content}], isError=False)

    except Exception as e:
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Table Structure Error**: {str(e)}"}],
            isError=True
        )


async def execute_query_hacs_data(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute structured data queries with range filters and pagination."""
    try:
        table_name = params.get("table_name")
        if not table_name:
            return CallToolResult(
                content=[{"type": "text", "text": "❌ Error: table_name parameter is required"}],
                isError=True
            )

        content = f"# 🔍 **Query Results: `{table_name}`**\n\n"
        content += "Mock query results would go here.\n"

        return CallToolResult(content=[{"type": "text", "text": content}], isError=False)

    except Exception as e:
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Query Error**: {str(e)}"}],
            isError=True
        )


async def execute_get_table_sample_data(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Get sample data from a table for development reference."""
    try:
        table_name = params.get("table_name")
        if not table_name:
            return CallToolResult(
                content=[{"type": "text", "text": "❌ Error: table_name parameter is required"}],
                isError=True
            )

        content = f"# 📋 **Sample Data: `{table_name}`**\n\n"
        content += "Mock sample data would go here.\n"

        return CallToolResult(content=[{"type": "text", "text": content}], isError=False)

    except Exception as e:
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Sample Data Error**: {str(e)}"}],
            isError=True
        )


async def execute_analyze_table_relationships(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Analyze table relationships and foreign key connections."""
    try:
        focus_table = params.get("focus_table", "all")

        content = "# 🔗 **HACS Database Relationship Analysis**\n\n"
        content += f"Analysis for focus_table: {focus_table}\n"
        content += "Mock relationship analysis would go here.\n"

        return CallToolResult(content=[{"type": "text", "text": content}], isError=False)

    except Exception as e:
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Relationship Analysis Error**: {str(e)}"}],
            isError=True
        )


# Updated comprehensive tool implementations mapping

# Database Visualization and Query Tools for Developers

async def execute_describe_database_schema(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute database schema visualization tool."""
    try:
        schema_type = params.get("schema_type", "all")

        schema_info = {
            "database_name": "hacs_db",
            "schemas": {
                "hacs_core": {
                    "tables": ["patients", "observations", "encounters", "conditions"],
                    "views": ["patient_summary", "recent_observations"],
                    "indexes": ["idx_patient_id", "idx_encounter_date"]
                }
            },
            "total_tables": 10,
            "total_views": 6,
            "total_indexes": 6
        }

        content = "# 🗄️ **HACS Database Schema Overview**\n\n"
        content += f"**Database:** {schema_info['database_name']}\n"
        content += f"**Total Tables:** {schema_info['total_tables']}\n"

        return CallToolResult(content=[{"type": "text", "text": content}], isError=False)

    except Exception as e:
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Database Schema Error**: {str(e)}"}],
            isError=True
        )


async def execute_describe_table_structure(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute table structure description tool."""
    try:
        table_name = params.get("table_name")
        if not table_name:
            return CallToolResult(
                content=[{"type": "text", "text": "❌ Error: table_name parameter is required"}],
                isError=True
            )

        content = f"# 📋 **Table Structure: `{table_name}`**\n\n"
        content += "Mock table structure information would go here.\n"

        return CallToolResult(content=[{"type": "text", "text": content}], isError=False)

    except Exception as e:
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Table Structure Error**: {str(e)}"}],
            isError=True
        )


async def execute_query_hacs_data(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Execute structured data queries with range filters and pagination."""
    try:
        table_name = params.get("table_name")
        if not table_name:
            return CallToolResult(
                content=[{"type": "text", "text": "❌ Error: table_name parameter is required"}],
                isError=True
            )

        content = f"# 🔍 **Query Results: `{table_name}`**\n\n"
        content += "Mock query results would go here.\n"

        return CallToolResult(content=[{"type": "text", "text": content}], isError=False)

    except Exception as e:
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Query Error**: {str(e)}"}],
            isError=True
        )


async def execute_get_table_sample_data(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Get sample data from a table for development reference."""
    try:
        table_name = params.get("table_name")
        if not table_name:
            return CallToolResult(
                content=[{"type": "text", "text": "❌ Error: table_name parameter is required"}],
                isError=True
            )

        content = f"# 📋 **Sample Data: `{table_name}`**\n\n"
        content += "Mock sample data would go here.\n"

        return CallToolResult(content=[{"type": "text", "text": content}], isError=False)

    except Exception as e:
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Sample Data Error**: {str(e)}"}],
            isError=True
        )


async def execute_analyze_table_relationships(params: Dict[str, Any], **kwargs) -> CallToolResult:
    """Analyze table relationships and foreign key connections."""
    try:
        focus_table = params.get("focus_table", "all")

        content = "# 🔗 **HACS Database Relationship Analysis**\n\n"
        content += f"Analysis for focus_table: {focus_table}\n"
        content += "Mock relationship analysis would go here.\n"

        return CallToolResult(content=[{"type": "text", "text": content}], isError=False)

    except Exception as e:
        return CallToolResult(
            content=[{"type": "text", "text": f"❌ **Relationship Analysis Error**: {str(e)}"}],
            isError=True
        )


# Updated comprehensive tool implementations mapping

# Vector Store Operations
async def execute_store_embedding(arguments: Dict[str, Any]) -> str:
    """Execute store_embedding tool."""
    try:
        result = await store_embedding(**arguments)
        return _convert_hacs_result_to_mcp(result, "Vector Embedding Storage")
    except Exception as e:
        return f"❌ **Vector Store Error**: {str(e)}"

async def execute_vector_similarity_search(arguments: Dict[str, Any]) -> str:
    """Execute vector_similarity_search tool."""
    try:
        result = await vector_similarity_search(**arguments)
        return _convert_hacs_result_to_mcp(result, "Vector Similarity Search")
    except Exception as e:
        return f"❌ **Vector Search Error**: {str(e)}"

async def execute_vector_hybrid_search(arguments: Dict[str, Any]) -> str:
    """Execute vector_hybrid_search tool."""
    try:
        result = await vector_hybrid_search(**arguments)
        return _convert_hacs_result_to_mcp(result, "Vector Hybrid Search")
    except Exception as e:
        return f"❌ **Vector Hybrid Search Error**: {str(e)}"

async def execute_get_vector_collection_stats(arguments: Dict[str, Any]) -> str:
    """Execute get_vector_collection_stats tool."""
    try:
        result = await get_vector_collection_stats(**arguments)
        return _convert_hacs_result_to_mcp(result, "Vector Collection Statistics")
    except Exception as e:
        return f"❌ **Vector Stats Error**: {str(e)}"
