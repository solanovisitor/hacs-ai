"""
HACS Unified Tool Registry - Consolidated tool discovery and management

This module consolidates plugin discovery and tool registry functionality,
eliminating duplication and providing a single source of truth for HACS tools.

Key Features:
    🔍 Automatic tool discovery from HACS domains
    📊 Tool categorization and metadata management
    🔎 Advanced search and filtering capabilities
    🛠️ Framework-agnostic tool definitions
    📋 Tool compatibility and dependency tracking
    🏥 Healthcare-specific tool organization
    ⚡ Plugin registration decorators
    📋 Version management and lifecycle tracking

Author: HACS Development Team
License: MIT
Version: 0.4.0
"""

import asyncio
import importlib
import inspect
import logging
import pkgutil
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Callable

from .versioning import VersionStatus
from hacs_models import ToolDefinition

logger = logging.getLogger(__name__)


class HACSToolRegistry:
    """
    Unified registry for HACS tools with discovery, categorization, and search capabilities.

    This registry provides framework-agnostic tool management, supporting both
    LangChain and MCP integrations while maintaining metadata about each tool's
    capabilities and requirements.
    """

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._categories: Dict[str, Set[str]] = {}
        self._domains: Dict[str, Set[str]] = {}
        self._tags: Dict[str, Set[str]] = {}
        self._initialized = False
        self._search_paths: List[str] = []
        # Canonical public tool allowlist (target ~22 tools)
        self._public_allowlist: Set[str] = set(
            [
                # Modeling
                "pin_resource",
                "compose_bundle",
                "validate_resource",
                "diff_resources",
                "validate_bundle",
                "list_models",
                "describe_model",
                "list_model_fields",
                "to_reference",
                # Database
                "save_resource",
                "read_resource",
                "update_resource",
                "delete_resource",
                "register_model_version",
                "search_memories",
                "run_migrations",
                "get_db_status",
                # Agents
                "write_scratchpad",
                "read_scratchpad",
                "summarize_state",
                "select_tools_for_task",
                "retrieve_memories",
            ]
        )
        # Toggle to include specialized resource tools
        import os

        self._include_specialized: bool = os.getenv(
            "HACS_INCLUDE_SPECIALIZED_TOOLS", "1"
        ).lower() not in {"0", "false"}

        # Pre-defined category mappings for new 4-domain structure
        self._category_patterns = {
            "modeling": [
                "pin_resource",
                "compose_bundle",
                "validate_resource",
                "diff_resources",
                "validate_bundle",
                # Legacy mappings for backward compatibility
                "instantiate_hacs_resource",
                "validate_hacs_resource",
                "create_resource_bundle",
                "add_bundle_entry",
                "validate_resource_bundle",
            ],
            "extraction": [
                "synthesize_mapping_spec",
                "extract_variables",
                "apply_mapping_spec",
                "summarize_context",
                # Legacy mappings for backward compatibility
                "register_prompt_template",
                "register_extraction_schema",
                "generate_stack_template_from_markdown",
                "instantiate_stack_template",
            ],
            "database": [
                "save_resource",
                "read_resource",
                "update_resource",
                "delete_resource",
                "register_model_version",
                "search_knowledge_items",
                "search_memories",
                "run_migrations",
                "get_db_status",
                # Legacy mappings for backward compatibility
                "persist_hacs_resource",
                "read_hacs_resource",
                "run_database_migration",
                "check_migration_status",
                "test_database_connection",
                "index_evidence",
                "check_evidence",
            ],
            "agents": [
                "write_scratchpad",
                "read_scratchpad",
                "create_todo",
                "list_todos",
                "complete_todo",
                "store_memory",
                "retrieve_memories",
                "inject_preferences",
                "select_tools_for_task",
                "summarize_state",
                "prune_state",
                # Legacy mappings for backward compatibility
                "check_memory",
                "set_actor_preference",
                "list_actor_preferences",
            ],
        }

    def register_tool(
        self,
        name: str = None,
        version: str = "1.0.0",
        description: str = "",
        domain: str = "general",
        author: str = "",
        dependencies: List[str] = None,
        tags: List[str] = None,
        status: VersionStatus = VersionStatus.ACTIVE,
        migration_notes: str = "",
        breaking_changes: List[str] = None,
        args_model: Any = None,
    ):
        """
        Decorator to register a tool as a plugin.

        Args:
            name: Tool name (defaults to function name)
            version: Tool version (semantic versioning)
            description: Tool description
            domain: Tool domain
            author: Tool author
            dependencies: List of dependencies
            tags: List of tags
            status: Version status (active, deprecated, etc.)
            migration_notes: Migration guidance for this version
            breaking_changes: List of breaking changes in this version
        """

        def decorator(func: Callable) -> Callable:
            tool_name = name or func.__name__

            # Convert to ToolDefinition directly
            plugin = ToolDefinition(
                name=tool_name,
                version=version,
                description=description or func.__doc__ or f"HACS tool: {tool_name}",
                function=func,
                module_path=func.__module__,
                function_name=tool_name,
                domain=domain,
                tags=tags or [],
                requires_actor=self._check_requires_actor(func),
                requires_db=self._check_requires_db(func),
                requires_vector_store=self._check_requires_vector_store(func),
                is_async=asyncio.iscoroutinefunction(func),
                status="published",
            )

            # Auto-detect Pydantic input model from function signature (single-model param)
            try:
                import inspect

                try:
                    from pydantic import BaseModel as _PydanticBaseModel  # type: ignore
                except Exception:
                    _PydanticBaseModel = None  # type: ignore
                if _PydanticBaseModel is not None and args_model is None:
                    sig = inspect.signature(func)
                    # Exclude typical non-user params
                    excluded = {"self", "args", "kwargs"}
                    params = [
                        p for p in sig.parameters.values() if p.name not in excluded
                    ]
                    if (
                        len(params) == 1
                        and params[0].annotation
                        and isinstance(
                            getattr(params[0].annotation, "__mro__", []), tuple
                        )
                    ):
                        if _PydanticBaseModel in getattr(
                            params[0].annotation, "__mro__", []
                        ):  # type: ignore
                            model = params[0].annotation
                            # Attach schema to plugin and function
                            try:
                                plugin.args_schema = model.model_json_schema()  # type: ignore[attr-defined]
                                setattr(func, "_tool_args", model)
                            except Exception:
                                pass
            except Exception:
                pass

            self._register_tool_definition(plugin)

            # Attach args schema if present or provided
            try:
                model = args_model or getattr(func, "_tool_args", None)
                if model is not None and hasattr(model, "model_json_schema"):
                    plugin.args_schema = model.model_json_schema()
                    try:
                        setattr(func, "_tool_args", model)
                    except Exception:
                        pass
            except Exception:
                pass

            # Register version information
            try:
                from .versioning import register_tool_version

                register_tool_version(
                    tool_name=tool_name,
                    version=version,
                    status=status,
                    migration_notes=migration_notes,
                    breaking_changes=breaking_changes or [],
                )
            except Exception as e:
                logger.warning(f"Failed to register version info for {tool_name}: {e}")

            # Mark the function as a registered plugin
            func._hacs_plugin = plugin
            func._hacs_registered = True

            logger.debug(
                f"Registered plugin: {tool_name} v{version} (domain: {domain})"
            )
            return func

        return decorator

    def discover_plugins(self, base_packages: List[str] = None) -> int:
        """
        Discover plugins from specified base packages.

        Args:
            base_packages: List of base package names to search

        Returns:
            Number of plugins discovered
        """
        if base_packages is None:
            base_packages = ["hacs_tools"]

        discovered_count = 0

        for base_package in base_packages:
            discovered_count += self._discover_from_package(base_package)

        logger.info(f"Plugin discovery complete: {discovered_count} plugins found")
        return discovered_count

    def _discover_from_package(self, package_name: str) -> int:
        """Discover plugins from a specific package."""
        try:
            package = importlib.import_module(package_name)
        except ImportError as e:
            logger.warning(f"Could not import package {package_name}: {e}")
            return 0

        discovered_count = 0

        # Get package path
        if hasattr(package, "__path__"):
            package_path = package.__path__
        else:
            logger.warning(f"Package {package_name} has no __path__ attribute")
            return 0

        # Walk through all modules in package
        # Blocklist generic domains and removed legacy domains
        blocked_substrings = {
            "hacs_tools.domains.fhir_integration",
            "hacs_tools.domains.development_tools",
            "hacs_tools.domains.healthcare_analytics",
            # Legacy domains that have been removed/consolidated into 4 core domains
            "hacs_tools.domains.admin_operations",
            "hacs_tools.domains.bundle_tools",
            "hacs_tools.domains.evidence_tools",
            "hacs_tools.domains.memory_operations",
            "hacs_tools.domains.modeling_tools",
            "hacs_tools.domains.persistence_tools",
            "hacs_tools.domains.preferences_tools",
            "hacs_tools.domains.resource_management",
            "hacs_tools.domains.schema_discovery",
            "hacs_tools.domains.vector_search",
            "hacs_tools.domains.workflow_tools",
        }

        for importer, modname, ispkg in pkgutil.walk_packages(
            package_path, package_name + "."
        ):
            # Skip blocked modules (cleanup of generic domains)
            if any(b in modname for b in blocked_substrings):
                continue
            try:
                module = importlib.import_module(modname)
                discovered_count += self._scan_module_for_tools(module, modname)
            except Exception as e:
                logger.debug(f"Could not scan module {modname}: {e}")
                continue

        return discovered_count

    def _scan_module_for_tools(self, module: Any, module_name: str) -> int:
        """Scan a module for tool functions."""
        discovered_count = 0

        for attr_name in dir(module):
            if attr_name.startswith("_"):
                continue

            attr = getattr(module, attr_name)

            # Only register functions explicitly decorated as HACS tools
            if hasattr(attr, "_hacs_registered") and hasattr(attr, "_hacs_plugin"):
                try:
                    plugin: ToolDefinition = getattr(attr, "_hacs_plugin")
                    # Decide registration based on allowlist and specialized toggle
                    if plugin:
                        is_specialized = plugin.domain == "resource" or any(
                            str(tag).startswith("resource:")
                            for tag in (plugin.tags or [])
                        )
                        # Always include specialized resource tools
                        if (
                            not is_specialized
                            and plugin.name not in self._public_allowlist
                        ):
                            continue
                    # Ensure function reference is set
                    if plugin and not plugin.function:
                        plugin.function = attr
                    self._register_tool_definition(plugin)
                    discovered_count += 1
                except Exception as e:
                    logger.debug(f"Failed to register decorated tool {attr_name}: {e}")
                continue

        return discovered_count

    def _is_potential_tool(self, func: Callable, name: str) -> bool:
        """Check if a function is potentially a HACS tool."""
        # Skip non-callable objects (strings, modules, classes, etc.)
        if not callable(func) and not hasattr(func, "func"):
            return False

        # Skip constants and description strings
        if isinstance(func, str) or name.endswith("_DESCRIPTION"):
            return False

        # Skip modules and classes
        if inspect.ismodule(func) or inspect.isclass(func):
            return False

        # Check for LangChain tool markers
        if hasattr(func, "_is_tool"):  # LangChain tool marker
            return True

        # Check if it's a LangChain StructuredTool object
        if hasattr(func, "name") and hasattr(func, "func"):
            return True

        # Check if it has langchain tool attributes
        if hasattr(func, "description") and hasattr(func, "args_schema"):
            return True

        # Check function signature for HACS patterns
        try:
            # Handle both regular functions and LangChain tools
            actual_func = getattr(func, "func", func)
            if callable(actual_func):
                sig = inspect.signature(actual_func)
                if "actor_name" in sig.parameters:
                    return True
        except (ValueError, TypeError):
            pass

        # Check function name patterns for actual callable functions
        if callable(func):
            tool_keywords = [
                "create",
                "get",
                "update",
                "delete",
                "search",
                "analyze",
                "execute",
                "validate",
                "convert",
                "process",
                "generate",
                "discover",
                "extract",
                "transform",
                "deploy",
                "run",
                "register",
                "instantiate",
                "optimize",
                "compare",
                # Additional modeling keywords for granular tools
                "list",
                "describe",
                "pick",
                "project",
                "reference",
                "add",
                "invoke",
                "plan",
                "suggest",
                "bundle",
                # High-level task tools
                "summarize",
                "annotate",
                "map",
                "enrich",
            ]

            return any(keyword in name.lower() for keyword in tool_keywords)

        return False

    def _infer_domain_from_module(self, module_name: str) -> str:
        """Infer domain from module name."""
        module_parts = module_name.split(".")

        # Look for domain indicators in module path - new 4-domain structure
        domain_mappings = {
            "modeling": "modeling",
            "extraction": "extraction",
            "database": "database",
            "agents": "agents",
            "terminology": "terminology",
            "resource_tools": "resource",
            # Legacy domain mappings for backward compatibility
            "resource_management": "modeling",
            "clinical_workflow": "modeling",
            "clinical_workflows": "modeling",
            "bundle_tools": "modeling",
            "workflow_tools": "modeling",
            "modeling_tools": "modeling",
            "schema_discovery": "extraction",
            "evidence_tools": "database",
            "persistence_tools": "database",
            "admin_operations": "database",
            "memory_operation": "agents",
            "memory_operations": "agents",
            "preferences_tools": "agents",
        }

        for part in module_parts:
            for pattern, domain in domain_mappings.items():
                if pattern in part:
                    return domain

        return "general"

    def _extract_tags_from_function(
        self, func: Callable, name: str, domain: str
    ) -> List[str]:
        """Extract tags from a function."""
        # Extract tags from function name and domain
        tags = []
        name_parts = name.split("_")
        tags.extend(name_parts)
        # High-signal domain tags for loadout
        tags.append(domain)
        if domain in ("modeling", "agents", "extraction", "database", "terminology"):
            tags.append(f"domain:{domain}")

        # Add fine-grained tags for database tools to distinguish records vs definitions
        if domain == "database":
            lower_name = name.lower()
            if any(
                k in lower_name
                for k in [
                    "save_record",
                    "read_record",
                    "update_record",
                    "delete_record",
                ]
            ):
                tags.append("records")
            if any(
                k in lower_name
                for k in [
                    "register_resource_definition",
                    "list_resource_definitions",
                    "get_resource_definition",
                    "update_resource_definition_status",
                ]
            ):
                tags.append("definitions")

        # Add resource-specific tags if tool name indicates a resource
        resource_indicators = [
            "patient",
            "observation",
            "document",
            "condition",
            "medication",
            "medicationrequest",
            "diagnosticreport",
            "servicerequest",
            "event",
            "appointment",
            "careplan",
            "careteam",
            "goal",
            "nutritionorder",
        ]
        lname = name.lower()
        for r in resource_indicators:
            if r in lname:
                tags.append(f"resource:{r}")
                break

        return list(set(tags))  # Remove duplicates

    def _check_requires_actor(self, func: Callable) -> bool:
        """Check if function requires actor parameter."""
        try:
            if hasattr(func, "func"):
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
            if hasattr(func, "func"):
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
            if hasattr(func, "func"):
                actual_func = func.func
            else:
                actual_func = func
            sig = inspect.signature(actual_func)
            return "vector_store" in sig.parameters
        except (ValueError, TypeError):
            return False

    def _determine_category(self, tool_name: str) -> str:
        """Determine the category of a tool based on its name."""
        for category, tool_names in self._category_patterns.items():
            if tool_name in tool_names:
                return category

        # Fallback pattern matching for new 4-domain structure
        name_lower = tool_name.lower()
        if any(
            term in name_lower
            for term in ["instantiate", "compose", "validate", "diff", "bundle"]
        ):
            return "modeling"
        elif any(
            term in name_lower
            for term in ["extract", "synthesize", "mapping", "summarize", "apply"]
        ):
            return "extraction"
        elif any(
            term in name_lower
            for term in [
                "save",
                "read",
                "update",
                "delete",
                "search",
                "migration",
                "database",
                "db",
            ]
        ):
            return "database"
        elif any(
            term in name_lower
            for term in [
                "scratchpad",
                "todo",
                "memory",
                "preference",
                "tool",
                "state",
                "agent",
            ]
        ):
            return "agents"
        elif any(
            term in name_lower
            for term in [
                "umls",
                "cui",
                "crosswalk",
                "concept",
                "code",
                "valueset",
                "value_set",
                "conceptmap",
                "concept_map",
                "normalize",
            ]
        ):
            return "terminology"

        # Legacy fallbacks for backward compatibility
        elif any(term in name_lower for term in ["create", "get", "resource"]):
            return "modeling"  # Map legacy resource management to modeling
        elif any(term in name_lower for term in ["workflow", "clinical", "guidance"]):
            return "modeling"  # Map workflows to modeling
        elif any(term in name_lower for term in ["template", "stack", "optimize"]):
            return "extraction"  # Map legacy templates to extraction
        elif any(term in name_lower for term in ["admin", "persist"]):
            return "database"  # Map admin operations to database

        return "modeling"  # Default to modeling domain

    def _register_tool_definition(self, tool: ToolDefinition) -> None:
        """Register a tool definition in the registry."""
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

        # Discover plugins directly
        if base_packages is None:
            base_packages = ["hacs_tools"]

        total_discovered = self.discover_plugins(base_packages)
        self._initialized = True

        logger.info(
            f"Auto-discovery complete: {total_discovered} total tools registered"
        )
        return total_discovered

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
        framework: str = None,
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
                tool
                for tool in results
                if (
                    query_lower in tool.name.lower()
                    or query_lower in tool.description.lower()
                    or any(query_lower in tag.lower() for tag in tool.tags)
                )
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
                tool for tool in results if all(tag in tool.tags for tag in tags)
            ]

        # Capability filters
        if requires_actor is not None:
            results = [
                tool for tool in results if tool.requires_actor == requires_actor
            ]

        if requires_db is not None:
            results = [tool for tool in results if tool.requires_db == requires_db]

        if requires_vector_store is not None:
            results = [
                tool
                for tool in results
                if tool.requires_vector_store == requires_vector_store
            ]

        if is_async is not None:
            results = [tool for tool in results if tool.is_async == is_async]

        # Framework compatibility
        if framework:
            results = [tool for tool in results if tool.is_compatible_with(framework)]

        return results

    def get_tool_stats(self) -> Dict[str, Any]:
        """Get statistics about registered tools."""
        stats = {
            "total_tools": len(self._tools),
            "categories": {
                category: len(tools) for category, tools in self._categories.items()
            },
            "domains": {domain: len(tools) for domain, tools in self._domains.items()},
            "capabilities": {
                "requires_actor": len(
                    [t for t in self._tools.values() if t.requires_actor]
                ),
                "requires_db": len([t for t in self._tools.values() if t.requires_db]),
                "requires_vector_store": len(
                    [t for t in self._tools.values() if t.requires_vector_store]
                ),
                "is_async": len([t for t in self._tools.values() if t.is_async]),
            },
            "framework_support": {
                "langchain": len(
                    [t for t in self._tools.values() if t.supports_langchain]
                ),
                "mcp": len([t for t in self._tools.values() if t.supports_mcp]),
            },
        }
        return stats

    def export_tool_catalog(self) -> Dict[str, Any]:
        """Export a tool catalog for external use."""
        catalog = {
            "metadata": {
                "total_tools": len(self._tools),
                "categories": list(self._categories.keys()),
                "domains": list(self._domains.keys()),
                "generated_at": str(datetime.now()),
            },
            "tools": [],
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
                "status": tool.status,
            }

            if tool.function:
                tool_info["parameters"] = tool.get_parameters()

            if tool.args_schema:
                tool_info["args_schema"] = tool.args_schema

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


# Convenience decorator using global registry
def register_tool(
    name: str = None,
    version: str = "1.0.0",
    description: str = "",
    domain: str = "general",
    author: str = "",
    dependencies: List[str] = None,
    tags: List[str] = None,
    status: VersionStatus = VersionStatus.ACTIVE,
    migration_notes: str = "",
    breaking_changes: List[str] = None,
):
    """
    Global tool registration decorator with versioning support.

    Usage:
        @register_tool(name="my_tool", domain="healthcare", version="1.1.0",
                      status=VersionStatus.ACTIVE)
        def my_hacs_tool(actor_name: str, data: dict) -> HACSResult:
            # Tool implementation
            pass
    """
    return get_global_registry().register_tool(
        name=name,
        version=version,
        description=description,
        domain=domain,
        author=author,
        dependencies=dependencies,
        tags=tags,
        status=status,
        migration_notes=migration_notes,
        breaking_changes=breaking_changes,
    )


# Export main classes and functions
__all__ = [
    "HACSToolRegistry",
    "register_tool",
    "get_global_registry",
    "discover_hacs_tools",
]
