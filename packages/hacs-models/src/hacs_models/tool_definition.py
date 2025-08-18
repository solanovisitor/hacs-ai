"""
ToolDefinition - HACS model for tool registry and metadata.

Represents a tool function with its metadata, requirements, and framework support.
Used by the HACS registry system for tool discovery, categorization, and management.
"""

from typing import Any, Dict, List, Optional, Callable, Literal
from pydantic import Field

from .base_resource import BaseResource


class ToolDefinition(BaseResource):
    """Tool definition for the HACS registry system."""

    resource_type: Literal["ToolDefinition"] = Field(default="ToolDefinition")
    
    # Core tool identity
    name: str = Field(description="Tool name")
    version: str = Field(description="Tool version")
    description: str = Field(description="Tool description")
    function: Optional[Callable] = Field(default=None, description="Tool function")
    
    # Optional args schema (Pydantic) for integrations/LLMs
    args_schema: Optional[Dict[str, Any]] = Field(default=None, description="JSON schema for tool inputs if available")

    # Tool metadata fields
    module_path: Optional[str] = Field(default=None, description="Module path where tool is defined")
    function_name: Optional[str] = Field(default=None, description="Function name")
    category: Optional[str] = Field(default="general", description="Tool category")
    domain: Optional[str] = Field(default="general", description="Tool domain")
    tags: List[str] = Field(default_factory=list, description="Tool tags")

    # Tool requirements
    requires_actor: bool = Field(default=False, description="Whether tool requires actor authentication")
    requires_db: bool = Field(default=False, description="Whether tool requires database")
    requires_vector_store: bool = Field(default=False, description="Whether tool requires vector store")
    is_async: bool = Field(default=False, description="Whether tool is async")

    # Tool status
    status: Optional[str] = Field(default="published", description="Tool status")

    # Framework support
    supports_langchain: bool = Field(default=True, description="Whether tool supports LangChain")
    supports_mcp: bool = Field(default=True, description="Whether tool supports MCP")

    model_config = {"arbitrary_types_allowed": True}

    def get_parameters(self) -> List[Dict[str, Any]]:
        """Get tool parameters from function signature or args_schema."""
        if self.args_schema and "properties" in self.args_schema:
            return [
                {
                    "name": name,
                    "type": prop.get("type", "string"),
                    "description": prop.get("description", ""),
                    "required": name in self.args_schema.get("required", [])
                }
                for name, prop in self.args_schema["properties"].items()
            ]
        
        # Fallback to function signature inspection
        if self.function:
            import inspect
            try:
                sig = inspect.signature(self.function)
                params = []
                for name, param in sig.parameters.items():
                    if name in ("self", "args", "kwargs"):
                        continue
                    params.append({
                        "name": name,
                        "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any",
                        "description": "",
                        "required": param.default == inspect.Parameter.empty
                    })
                return params
            except (ValueError, TypeError):
                pass
        
        return []

    def is_compatible_with(self, framework: str) -> bool:
        """Check if tool is compatible with a framework."""
        if framework == "langchain":
            return self.supports_langchain
        elif framework == "mcp":
            return self.supports_mcp
        return True  # Default compatibility
