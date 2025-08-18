"""
LangChain Tools Integration for HACS

Clean, unified tool provisioning for LangChain (consumed by LangGraph as well).

Boundaries:
- Tool discovery/provisioning is centralized in hacs_utils.integrations.common.tool_loader
- This module exposes LangChain BaseTool instances via langchain_tools()
- LangGraph should consume the same LangChain BaseTool set (no separate provisioning)

Notes:
- Older, heavy wrappers and bespoke schemas are deprecated in favor of the centralized loader
- Keep the public API small and SOLID: provisioning, lookup, and light validation helpers
"""

import logging
from typing import Any, Dict, List, Optional

try:
    from pydantic import BaseModel, Field, ValidationError
    _has_pydantic = True
except ImportError:
    _has_pydantic = False
    # Graceful fallback for environments without Pydantic
    class BaseModel:
        pass

    class Field:
        def __init__(self, *args, **kwargs):
            pass

    class ValidationError(Exception):
        pass

def _lazy_import_langchain():
    """Lazy import of LangChain components with proper error handling."""
    try:
        from langchain_core.tools.convert import tool
        from langchain_core.tools.base import BaseTool, ArgsSchema, ToolException
        from langchain_core.tools.structured import StructuredTool
        return {
            'tool': tool,
            'BaseTool': BaseTool,
            'StructuredTool': StructuredTool,
            'ToolException': ToolException,
            'ArgsSchema': ArgsSchema,
            'available': True
        }
    except ImportError as e:
        logger.error(f"LangChain is required for this integration but not available: {e}")
        raise ImportError(
            "LangChain is required for HACS-LangChain integration. "
            "Please install: pip install langchain-core langchain-community"
        ) from e

# Lazy loading - only import when needed
_langchain = None

def _lazy_import_hacs_tools():
    """Lazy import of HACS tools with proper error handling."""
    try:
        # Import HACS tools directly - they should work without LangChain mocking
        from hacs_tools.tools import ALL_HACS_TOOLS
        from hacs_tools import (
            create_record,
            get_record,
            update_record,
            delete_record,
            search_records,
            discover_hacs_resources,
            get_hacs_resource_schema,
            analyze_resource_fields,
            compare_resource_schemas,
            create_resource_stack,
            register_prompt_template_tool,
            register_extraction_schema_tool,
            register_stack_template_tool,
            generate_stack_template_from_markdown_tool,
            instantiate_stack_from_context_tool,
            instantiate_stack_template_tool,
        )

        return {
            'create_record': create_record,
            'get_record': get_record,
            'update_record': update_record,
            'delete_record': delete_record,
            'search_records': search_records,
            'discover_hacs_resources': discover_hacs_resources,
            'get_hacs_resource_schema': get_hacs_resource_schema,
            'analyze_resource_fields': analyze_resource_fields,
            'compare_resource_schemas': compare_resource_schemas,
            'create_resource_stack': create_resource_stack,
            'register_prompt_template': register_prompt_template_tool,
            'register_extraction_schema': register_extraction_schema_tool,
            'register_stack_template': register_stack_template_tool,
            'generate_stack_template_from_markdown': generate_stack_template_from_markdown_tool,
            'instantiate_stack_from_context': instantiate_stack_from_context_tool,
            'instantiate_stack_template': instantiate_stack_template_tool,
            'all_tools': ALL_HACS_TOOLS,
            'available': True
        }

    except ImportError as e:
        logger.warning(f"HACS tools not available: {e}")
        return {'available': False}

# Lazy loading - only import when needed
_hacs_tools = None

logger = logging.getLogger(__name__)


# ===== Pydantic Schemas for Tool Inputs =====

class CreateRecordInput(BaseModel):
    """Input schema for creating HACS records."""
    actor_name: str = Field(description="Name of the healthcare actor creating the record")
    resource_type: str = Field(description="Type of healthcare resource (Patient, Observation, etc.)")
    resource_data: Dict[str, Any] = Field(description="Resource data conforming to HACS/FHIR schema")
    auto_generate_id: bool = Field(default=True, description="Whether to auto-generate ID if not provided")
    validate_fhir: bool = Field(default=True, description="Whether to perform FHIR compliance validation")


class GetRecordInput(BaseModel):
    """Input schema for retrieving HACS records."""
    actor_name: str = Field(description="Name of the healthcare actor requesting the resource")
    resource_type: str = Field(description="Type of healthcare resource to retrieve")
    resource_id: str = Field(description="Unique identifier of the healthcare resource")
    include_audit_trail: bool = Field(default=False, description="Whether to include audit trail in response")


class UpdateRecordInput(BaseModel):
    """Input schema for updating HACS records."""
    actor_name: str = Field(description="Name of the healthcare actor updating the record")
    resource_type: str = Field(description="Type of healthcare resource to update")
    resource_id: str = Field(description="Unique identifier of the healthcare resource")
    update_data: Dict[str, Any] = Field(description="Updated resource data")
    validate_fhir: bool = Field(default=True, description="Whether to perform FHIR compliance validation")


class DeleteRecordInput(BaseModel):
    """Input schema for deleting HACS records."""
    actor_name: str = Field(description="Name of the healthcare actor deleting the record")
    resource_type: str = Field(description="Type of healthcare resource to delete")
    resource_id: str = Field(description="Unique identifier of the healthcare resource")
    soft_delete: bool = Field(default=True, description="Whether to perform soft delete (mark as inactive)")


class SearchRecordsInput(BaseModel):
    """Input schema for searching HACS records."""
    actor_name: str = Field(description="Name of the healthcare actor performing the search")
    resource_type: str = Field(description="Type of healthcare resource to search")
    search_criteria: Dict[str, Any] = Field(description="Search criteria (filters, conditions)")
    limit: int = Field(default=10, description="Maximum number of results to return")
    include_metadata: bool = Field(default=True, description="Whether to include metadata in results")


class ExecuteWorkflowInput(BaseModel):
    """Input schema for executing clinical workflows."""
    actor_name: str = Field(description="Name of the healthcare actor executing the workflow")
    plan_definition_id: str = Field(description="ID of the PlanDefinition resource to execute")
    patient_id: Optional[str] = Field(default=None, description="Optional patient ID if workflow is patient-specific")
    input_parameters: Optional[Dict[str, Any]] = Field(default=None, description="Input parameters for workflow execution")
    execution_context: str = Field(default="routine", description="Context of execution (routine, urgent, emergency, research)")


class GetGuidanceInput(BaseModel):
    """Input schema for getting clinical guidance."""
    actor_name: str = Field(description="Name of the healthcare actor requesting guidance")
    patient_context: Dict[str, Any] = Field(description="Patient clinical context and data")
    clinical_question: str = Field(description="Specific clinical question or scenario")
    evidence_requirements: Optional[List[str]] = Field(default=None, description="Required types of evidence")
    urgency_level: str = Field(default="routine", description="Urgency level (routine, urgent, emergency)")


class DiscoverResourcesInput(BaseModel):
    """Input schema for discovering HACS resources."""
    category_filter: Optional[str] = Field(default=None, description="Filter by resource category")
    fhir_compliant_only: bool = Field(default=False, description="Return only FHIR-compliant resources")
    include_field_details: bool = Field(default=True, description="Include detailed field information")
    search_term: Optional[str] = Field(default=None, description="Search term for resource discovery")


class CreateTemplateInput(BaseModel):
    """Input schema for creating clinical templates."""
    template_type: str = Field(default="assessment", description="Type of clinical template")
    focus_area: str = Field(default="general", description="Clinical focus area")
    complexity_level: str = Field(default="standard", description="Template complexity level")
    include_workflow_fields: bool = Field(default=True, description="Include workflow-related fields")


# ===== LangChain Tool Wrappers =====

def create_langchain_tool_wrapper(func, name: str, description: str, args_schema: BaseModel):
    """Create a LangChain tool wrapper with proper error handling."""
    global _langchain
    if _langchain is None:
        _langchain = _lazy_import_langchain()

    if not _langchain['available']:
        raise ImportError("LangChain is required for tool creation")

    def handle_tool_error(error) -> str:
        """Handle tool errors gracefully."""
        logger.error(f"Tool error in {name}: {error}")
        return f"Tool execution failed: {str(error)}"

    try:
        # Create StructuredTool with proper configuration
        return _langchain['StructuredTool'].from_function(
            func=func,
            name=name,
            description=description,
            args_schema=args_schema,
            handle_tool_error=handle_tool_error,
            response_format="content",  # Can be changed to "content_and_artifact" if needed
            return_direct=False,
        )
    except Exception as e:
        logger.error(f"Failed to create tool wrapper for {name}: {e}")
        raise


def langchain_tools() -> List:
    """Get all HACS tools as LangChain BaseTool instances using centralized loader."""
    from ..common.tool_loader import get_all_hacs_tools_sync
    return get_all_hacs_tools_sync(framework="langchain")


def get_tool_by_name(tool_name: str):
    """Get a specific HACS tool by name."""
    tools = langchain_tools()
    for tool in tools:
        if hasattr(tool, 'name') and tool.name == tool_name:
            return tool
    return None


def validate_tool_inputs(tool_name: str, inputs: Dict[str, Any]) -> bool:
    """Validate inputs for a specific tool."""
    tool = get_tool_by_name(tool_name)
    if not tool:
        return False

    try:
        # Use the tool's args_schema to validate inputs
        if hasattr(tool, 'args_schema') and tool.args_schema:
            tool.args_schema(**inputs)
        return True
    except ValidationError as e:
        logger.error(f"Validation error for {tool_name}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error validating {tool_name}: {e}")
        return False


# ===== Tool Registry and Management =====

# HACS Registry is required - no fallback
from hacs_registry import get_global_registry, HACSToolRegistry as CoreToolRegistry


class HACSToolRegistry:
    """LangChain-specific wrapper for the centralized HACS tool registry."""

    def __init__(self):
        self._tools: Dict[str, Any] = {}
        self._core_registry = get_global_registry()
        self._initialize_tools()

    def _initialize_tools(self):
        """Initialize all tools in the registry."""
        try:
            tools = langchain_tools()
            for tool in tools:
                if hasattr(tool, 'name'):
                    self._tools[tool.name] = tool
            logger.info(f"Initialized {len(self._tools)} LangChain tools in registry")
        except Exception as e:
            logger.error(f"Failed to initialize tools: {e}")

    def get_tool(self, name: str):
        """Get a tool by name."""
        return self._tools.get(name)

    def get_tools_by_category(self, category: str) -> List:
        """Get all tools in a specific category."""
        # Use the centralized registry for categorization
        tool_defs = self._core_registry.get_tools_by_category(category)
        langchain_tools = []
        for tool_def in tool_defs:
            if tool_def.name in self._tools:
                langchain_tools.append(self._tools[tool_def.name])
        return langchain_tools

    def get_all_tools(self) -> List:
        """Get all registered tools."""
        return list(self._tools.values())

    def get_available_categories(self) -> List[str]:
        """Get all available tool categories."""
        if self._core_registry:
            return self._core_registry.get_available_categories()
        else:
            # Fallback categories
            return ["resource_management", "clinical_workflows", "schema_discovery",
                   "development_tools", "memory_operations", "vector_search",
                   "fhir_integration", "healthcare_analytics", "ai_integrations",
                   "admin_operations"]

    def search_tools(self, query: str) -> List:
        """Search tools by name or description."""
        if self._core_registry:
            # Use centralized search capabilities
            tool_defs = self._core_registry.search_tools(query=query, framework="langchain")
            langchain_tools = []
            for tool_def in tool_defs:
                if tool_def.name in self._tools:
                    langchain_tools.append(self._tools[tool_def.name])
            return langchain_tools
        else:
            # Fallback search
            results = []
            query_lower = query.lower()

            for tool in self._tools.values():
                if hasattr(tool, 'name') and hasattr(tool, 'description'):
                    if (query_lower in tool.name.lower() or
                        query_lower in tool.description.lower()):
                        results.append(tool)

            return results

    def get_tool_stats(self) -> Dict[str, Any]:
        """Get statistics about registered tools."""
        if self._core_registry:
            core_stats = self._core_registry.get_tool_stats()
            return {
                "langchain_tools": len(self._tools),
                "core_registry_stats": core_stats
            }
        else:
            return {"langchain_tools": len(self._tools)}


# Global registry instance
_registry = HACSToolRegistry()

# Export convenience functions
def get_hacs_tools() -> List:
    """Get all HACS tools as LangChain BaseTool instances."""
    return _registry.get_all_tools()


def get_hacs_tool(name: str):
    """Get a specific HACS tool by name."""
    return _registry.get_tool(name)


def get_hacs_tools_by_category(category: str) -> List:
    """Get HACS tools by category."""
    return _registry.get_tools_by_category(category)


# ===== Export all important classes and functions =====
__all__ = [
    # Provisioning
    "langchain_tools",
    # Lookups and simple helpers
    "get_tool_by_name",
    "validate_tool_inputs",
    # Optional registry convenience
    "HACSToolRegistry",
    "get_hacs_tools",
    "get_hacs_tool",
    "get_hacs_tools_by_category",
]