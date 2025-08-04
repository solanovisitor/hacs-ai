"""
HACS Tool Registry - Centralized tool discovery and management

This module provides comprehensive tool registry functionality for HACS,
supporting automatic discovery, categorization, search, and framework-agnostic
tool management for AI agents.

Key Features:
    🔍 Automatic tool discovery from HACS domains
    📊 Tool categorization and metadata management
    🔎 Advanced search and filtering capabilities
    🛠️ Framework-agnostic tool definitions
    📋 Tool compatibility and dependency tracking
    🏥 Healthcare-specific tool organization

Author: HACS Development Team
License: MIT
Version: 0.3.0
"""

import asyncio
import importlib
import inspect
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Callable, Union
from pathlib import Path

from .resource_registry import ResourceStatus as DefinitionStatus, get_global_registry
from .plugin_discovery import discover_hacs_plugins, plugin_registry, PluginRegistry
from hacs_core import BaseResource
from pydantic import Field

logger = logging.getLogger(__name__)


class ToolDefinition(BaseResource):
    """Tool definition for the registry - simplified version that works with new architecture."""
    
    resource_type: str = Field(default="ToolDefinition", description="Resource type")
    name: str = Field(description="Tool name")
    version: str = Field(description="Tool version")
    description: str = Field(description="Tool description")
    function: Optional[Callable] = Field(default=None, description="Tool function")
    
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
    
    class Config:
        arbitrary_types_allowed = True


class HACSToolRegistry:
    """
    Centralized registry for HACS tools with discovery, categorization, and search capabilities.
    
    This registry provides framework-agnostic tool management, supporting both
    LangChain and MCP integrations while maintaining comprehensive metadata
    about each tool's capabilities and requirements.
    """
    
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._categories: Dict[str, Set[str]] = {}
        self._domains: Dict[str, Set[str]] = {}
        self._tags: Dict[str, Set[str]] = {}
        self._initialized = False
        
        # Pre-defined category mappings for tool discovery
        self._category_patterns = {
            "resource_management": [
                "create_hacs_record", "get_hacs_record", "update_hacs_record",
                "delete_hacs_record", "search_hacs_records", "validate_resource_data",
                "list_available_resources", "find_resources"
            ],
            "clinical_workflows": [
                "execute_clinical_workflow", "get_clinical_guidance",
                "query_with_datarequirement", "validate_clinical_protocol"
            ],
            "schema_discovery": [
                "discover_hacs_resources", "get_hacs_resource_schema",
                "analyze_resource_fields", "compare_resource_schemas",
                "get_resource_schema", "create_view_resource_schema",
                "suggest_view_fields"
            ],
            "development_tools": [
                "create_resource_stack", "create_clinical_template",
                "optimize_resource_for_llm", "create_model_stack",
                "version_hacs_resource"
            ],
            "memory_operations": [
                "create_hacs_memory", "search_hacs_memories", "create_memory",
                "search_memories", "consolidate_memories", "retrieve_context",
                "analyze_memory_patterns"
            ],
            "vector_search": [
                "store_embedding", "vector_similarity_search",
                "vector_hybrid_search", "get_vector_collection_stats",
                "optimize_vector_collection"
            ],
            "fhir_integration": [
                "convert_to_fhir", "validate_fhir_compliance",
                "process_fhir_bundle", "lookup_fhir_terminology"
            ],
            "healthcare_analytics": [
                "calculate_quality_measures", "analyze_population_health",
                "generate_clinical_dashboard", "perform_risk_stratification"
            ],
            "ai_integrations": [
                "deploy_healthcare_ai_model", "run_clinical_inference",
                "preprocess_medical_data"
            ],
            "admin_operations": [
                "run_database_migration", "check_migration_status",
                "describe_database_schema", "get_table_structure",
                "test_database_connection"
            ],
            "knowledge_management": [
                "create_knowledge_item"
            ]
        }
    
    def _determine_category(self, tool_name: str) -> str:
        """Determine the category of a tool based on its name."""
        for category, tool_names in self._category_patterns.items():
            if tool_name in tool_names:
                return category
        
        # Fallback pattern matching
        name_lower = tool_name.lower()
        if any(term in name_lower for term in ["create", "get", "update", "delete", "resource"]):
            return "resource_management"
        elif any(term in name_lower for term in ["workflow", "clinical", "guidance"]):
            return "clinical_workflows"
        elif any(term in name_lower for term in ["memory", "consolidate", "retrieve"]):
            return "memory_operations"
        elif any(term in name_lower for term in ["vector", "embedding", "search"]):
            return "vector_search"
        elif any(term in name_lower for term in ["schema", "discover", "analyze"]):
            return "schema_discovery"
        elif any(term in name_lower for term in ["template", "stack", "optimize"]):
            return "development_tools"
        elif any(term in name_lower for term in ["fhir", "convert", "validate"]):
            return "fhir_integration"
        elif any(term in name_lower for term in ["analytics", "quality", "population"]):
            return "healthcare_analytics"
        elif any(term in name_lower for term in ["ai", "model", "inference"]):
            return "ai_integrations"
        elif any(term in name_lower for term in ["admin", "database", "migration"]):
            return "admin_operations"
        
        return "unknown"
    
    def _extract_tool_metadata(self, func: Callable, module_path: str, domain: str) -> Dict[str, Any]:
        """Extract comprehensive metadata from a tool function."""
        # Handle LangChain StructuredTool objects
        if hasattr(func, 'func') and hasattr(func, 'name'):
            # This is a LangChain StructuredTool
            actual_func = func.func
            tool_name = func.name
            tool_description = getattr(func, 'description', f"HACS tool: {tool_name}")
        else:
            # This is a regular function
            actual_func = func
            tool_name = getattr(func, '__name__', 'unknown_tool')
            tool_description = func.__doc__ or f"HACS tool: {tool_name}"
        
        try:
            sig = inspect.signature(actual_func)
        except (ValueError, TypeError):
            # Fallback for tools where signature inspection fails
            sig = None
            
        # Analyze parameters if signature is available
        if sig:
            requires_actor = "actor_name" in sig.parameters
            requires_db = any(param in sig.parameters for param in ["db_adapter", "database"])
            requires_vector_store = "vector_store" in sig.parameters
            is_async = asyncio.iscoroutinefunction(actual_func)
        else:
            # Fallback analysis
            requires_actor = "actor" in tool_name.lower()
            requires_db = "db" in tool_name.lower() or "database" in tool_name.lower()
            requires_vector_store = "vector" in tool_name.lower()
            is_async = False
        
        # Clean up description
        if tool_description:
            tool_description = tool_description.strip().split('\n')[0]  # First line only
        
        # Extract tags from docstring and function name
        tags = []
        name_parts = tool_name.split('_')
        tags.extend(name_parts)
        
        if "clinical" in tool_description.lower() or "healthcare" in tool_description.lower():
            tags.append("clinical")
        if "fhir" in tool_description.lower():
            tags.append("fhir")
        if "workflow" in tool_description.lower():
            tags.append("workflow")
        
        return {
            "requires_actor": requires_actor,
            "requires_db": requires_db,
            "requires_vector_store": requires_vector_store,
            "is_async": is_async,
            "description": tool_description,
            "tags": list(set(tags)),  # Remove duplicates
            "signature": sig,
            "tool_name": tool_name  # Add tool name to metadata
        }
    
    def discover_tools_from_module(self, module_name: str) -> int:
        """
        Discover and register tools from a specific module.
        
        Args:
            module_name: Full module name (e.g., 'hacs_tools.domains.resource_management')
            
        Returns:
            Number of tools discovered and registered
        """
        try:
            module = importlib.import_module(module_name)
            discovered_count = 0
            
            domain = module_name.split('.')[-1] if '.' in module_name else module_name
            
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                
                # Check if it's a tool function
                if (callable(attr) and 
                    not attr_name.startswith('_') and 
                    hasattr(attr, '__doc__') and
                    not inspect.isclass(attr)):
                    
                    # Additional checks for tool detection
                    if (hasattr(attr, '_is_tool') or  # LangChain tool marker
                        'actor_name' in getattr(attr, '__annotations__', {}) or  # HACS tool pattern
                        any(term in attr_name for term in ['create', 'get', 'update', 'delete', 'search', 'analyze'])):
                        
                        try:
                            metadata = self._extract_tool_metadata(attr, module_name, domain)
                            tool_name = metadata["tool_name"]
                            category = self._determine_category(tool_name)
                            
                            tool_def = ToolDefinition(
                                name=tool_name,
                                version="1.0.0",  # Default version for discovered tools
                                description=metadata["description"],
                                function=attr,
                                module_path=module_name,
                                function_name=tool_name,
                                category=category,
                                domain=domain,
                                tags=metadata["tags"],
                                requires_actor=metadata["requires_actor"],
                                requires_db=metadata["requires_db"],
                                requires_vector_store=metadata["requires_vector_store"],
                                is_async=metadata["is_async"],
                                status=DefinitionStatus.PUBLISHED
                            )
                            
                            self.register_tool(tool_def)
                            discovered_count += 1
                            
                        except Exception as e:
                            logger.warning(f"Failed to register tool {attr_name} from {module_name}: {e}")
            
            logger.info(f"Discovered {discovered_count} tools from {module_name}")
            return discovered_count
            
        except ImportError as e:
            logger.warning(f"Could not import module {module_name}: {e}")
            return 0
    
    def auto_discover_hacs_tools(self, base_packages: List[str] = None) -> int:
        """
        Automatically discover all HACS tools using the plugin system.
        
        Args:
            base_packages: Base packages to search (defaults to ["hacs_tools"])
        
        Returns:
            Total number of tools discovered and registered
        """
        if self._initialized:
            logger.info("Registry already initialized, skipping auto-discovery")
            return len(self._tools)
        
        # Use plugin discovery system
        if base_packages is None:
            base_packages = ["hacs_tools"]
        
        # Discover plugins
        registry = discover_hacs_plugins(base_packages)
        plugins = registry.get_all_plugins()
        
        total_discovered = 0
        
        # Register discovered plugins as tools
        for plugin_name, plugin in plugins.items():
            try:
                tool_def = ToolDefinition(
                    name=plugin.metadata.name,
                    version=plugin.metadata.version,
                    description=plugin.metadata.description,
                    function=plugin.function,
                    module_path=plugin.module_path,
                    function_name=plugin.metadata.name,
                    category=self._determine_category(plugin.metadata.name),
                    domain=plugin.metadata.domain,
                    tags=plugin.metadata.tags,
                    requires_actor=self._check_requires_actor(plugin.function),
                    requires_db=self._check_requires_db(plugin.function),
                    requires_vector_store=self._check_requires_vector_store(plugin.function),
                    is_async=asyncio.iscoroutinefunction(plugin.function),
                    status=DefinitionStatus.PUBLISHED
                )
                
                self.register_tool(tool_def)
                total_discovered += 1
                
            except Exception as e:
                logger.warning(f"Failed to register plugin {plugin_name}: {e}")
        
        self._initialized = True
        logger.info(f"Plugin-based auto-discovery complete: {total_discovered} total tools registered")
        
        # Print discovery statistics
        stats = registry.get_statistics()
        logger.info(f"Discovery stats: {stats['total_plugins']} plugins across {stats['total_domains']} domains")
        for domain, count in stats['domain_counts'].items():
            logger.info(f"  {domain}: {count} tools")
        
        return total_discovered
    
    def _check_requires_actor(self, func: Callable) -> bool:
        """Check if function requires actor parameter."""
        try:
            # Handle LangChain StructuredTool objects
            if hasattr(func, 'func'):
                actual_func = func.func
            else:
                actual_func = func
                
            sig = inspect.signature(actual_func)
            return "actor_name" in sig.parameters
        except (ValueError, TypeError):
            return False
    
    def _check_requires_db(self, func: Callable) -> bool:
        """Check if function requires database parameter."""
        try:
            # Handle LangChain StructuredTool objects
            if hasattr(func, 'func'):
                actual_func = func.func
            else:
                actual_func = func
                
            sig = inspect.signature(actual_func)
            return any(param in sig.parameters for param in ["db_adapter", "database"])
        except (ValueError, TypeError):
            return False
    
    def _check_requires_vector_store(self, func: Callable) -> bool:
        """Check if function requires vector store parameter."""
        try:
            # Handle LangChain StructuredTool objects
            if hasattr(func, 'func'):
                actual_func = func.func
            else:
                actual_func = func
                
            sig = inspect.signature(actual_func)
            return "vector_store" in sig.parameters
        except (ValueError, TypeError):
            return False
    
    def register_tool(self, tool: ToolDefinition) -> None:
        """Register a tool in the registry."""
        self._tools[tool.name] = tool
        
        # Update category index
        if tool.category not in self._categories:
            self._categories[tool.category] = set()
        self._categories[tool.category].add(tool.name)
        
        # Update domain index
        if tool.domain not in self._domains:
            self._domains[tool.domain] = set()
        self._domains[tool.domain].add(tool.name)
        
        # Update tag index
        for tag in tool.tags:
            if tag not in self._tags:
                self._tags[tag] = set()
            self._tags[tag].add(tool.name)
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def get_tool_function(self, name: str) -> Optional[Callable]:
        """Get the actual function for a tool by name."""
        tool = self.get_tool(name)
        return tool.function if tool else None
    
    def get_tools_by_category(self, category: str) -> List[ToolDefinition]:
        """Get all tools in a specific category."""
        tool_names = self._categories.get(category, set())
        return [self._tools[name] for name in tool_names if name in self._tools]
    
    def get_tools_by_domain(self, domain: str) -> List[ToolDefinition]:
        """Get all tools from a specific domain."""
        tool_names = self._domains.get(domain, set())
        return [self._tools[name] for name in tool_names if name in self._tools]
    
    def get_tools_by_tag(self, tag: str) -> List[ToolDefinition]:
        """Get all tools with a specific tag."""
        tool_names = self._tags.get(tag, set())
        return [self._tools[name] for name in tool_names if name in self._tools]
    
    def get_all_tools(self) -> List[ToolDefinition]:
        """Get all registered tools."""
        return list(self._tools.values())
    
    def get_available_categories(self) -> List[str]:
        """Get all available tool categories."""
        return list(self._categories.keys())
    
    def get_available_domains(self) -> List[str]:
        """Get all available tool domains."""
        return list(self._domains.keys())
    
    def get_available_tags(self) -> List[str]:
        """Get all available tool tags."""
        return list(self._tags.keys())
    
    def search_tools(
        self, 
        query: str = None,
        category: str = None,
        domain: str = None,
        tags: List[str] = None,
        requires_actor: bool = None,
        requires_db: bool = None,
        requires_vector_store: bool = None,
        is_async: bool = None,
        framework: str = None
    ) -> List[ToolDefinition]:
        """
        Advanced tool search with multiple filter criteria.
        
        Args:
            query: Text search in name and description
            category: Filter by category
            domain: Filter by domain
            tags: Filter by tags (tools must have ALL specified tags)
            requires_actor: Filter by actor requirement
            requires_db: Filter by database requirement
            requires_vector_store: Filter by vector store requirement
            is_async: Filter by async capability
            framework: Filter by framework compatibility
            
        Returns:
            List of matching tools
        """
        results = list(self._tools.values())
        
        # Text search
        if query:
            query_lower = query.lower()
            results = [
                tool for tool in results
                if (query_lower in tool.name.lower() or 
                    query_lower in tool.description.lower() or
                    any(query_lower in tag.lower() for tag in tool.tags))
            ]
        
        # Category filter
        if category:
            results = [tool for tool in results if tool.category == category]
        
        # Domain filter
        if domain:
            results = [tool for tool in results if tool.domain == domain]
        
        # Tags filter (AND operation - tool must have ALL specified tags)
        if tags:
            results = [
                tool for tool in results 
                if all(tag in tool.tags for tag in tags)
            ]
        
        # Capability filters
        if requires_actor is not None:
            results = [tool for tool in results if tool.requires_actor == requires_actor]
        
        if requires_db is not None:
            results = [tool for tool in results if tool.requires_db == requires_db]
        
        if requires_vector_store is not None:
            results = [tool for tool in results if tool.requires_vector_store == requires_vector_store]
        
        if is_async is not None:
            results = [tool for tool in results if tool.is_async == is_async]
        
        # Framework compatibility
        if framework:
            results = [tool for tool in results if tool.is_compatible_with(framework)]
        
        return results
    
    def get_tool_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about registered tools."""
        stats = {
            "total_tools": len(self._tools),
            "categories": {
                category: len(tools)
                for category, tools in self._categories.items()
            },
            "domains": {
                domain: len(tools)
                for domain, tools in self._domains.items()
            },
            "capabilities": {
                "requires_actor": len([t for t in self._tools.values() if t.requires_actor]),
                "requires_db": len([t for t in self._tools.values() if t.requires_db]),
                "requires_vector_store": len([t for t in self._tools.values() if t.requires_vector_store]),
                "is_async": len([t for t in self._tools.values() if t.is_async]),
            },
            "framework_support": {
                "langchain": len([t for t in self._tools.values() if t.supports_langchain]),
                "mcp": len([t for t in self._tools.values() if t.supports_mcp]),
            },
            "status": {
                status.value: len([t for t in self._tools.values() if t.status == status])
                for status in DefinitionStatus
            }
        }
        return stats
    
    def export_tool_catalog(self) -> Dict[str, Any]:
        """Export a comprehensive tool catalog for external use."""
        catalog = {
            "metadata": {
                "total_tools": len(self._tools),
                "categories": list(self._categories.keys()),
                "domains": list(self._domains.keys()),
                "generated_at": str(datetime.now())
            },
            "tools": []
        }
        
        for tool in self._tools.values():
            tool_info = {
                "name": tool.name,
                "description": tool.description,
                "category": tool.category,
                "domain": tool.domain,
                "tags": tool.tags,
                "version": tool.version,
                "module_path": tool.module_path,
                "function_name": tool.function_name,
                "capabilities": {
                    "requires_actor": tool.requires_actor,
                    "requires_db": tool.requires_db,
                    "requires_vector_store": tool.requires_vector_store,
                    "is_async": tool.is_async,
                },
                "framework_support": {
                    "langchain": tool.supports_langchain,
                    "mcp": tool.supports_mcp,
                },
                "status": tool.status.value
            }
            
            if tool.function:
                tool_info["parameters"] = tool.get_parameters()
            
            catalog["tools"].append(tool_info)
        
        return catalog


# Global registry instance
_global_registry: Optional[HACSToolRegistry] = None


def get_global_registry() -> HACSToolRegistry:
    """Get the global tool registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = HACSToolRegistry()
        _global_registry.auto_discover_hacs_tools()
    return _global_registry


def discover_hacs_tools() -> HACSToolRegistry:
    """Convenience function to get a fresh registry with auto-discovery."""
    registry = HACSToolRegistry()
    registry.auto_discover_hacs_tools()
    return registry