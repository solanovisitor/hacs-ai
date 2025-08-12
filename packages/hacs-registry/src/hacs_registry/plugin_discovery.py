"""
Plugin Discovery System for HACS Tools

This module provides a dynamic plugin discovery system that can automatically
find and register HACS tools without hardcoded module paths. It supports:

- Automatic discovery of tool modules
- Plugin registration decorators
- Extensible domain detection
- Version management
- Dependency tracking
"""

import importlib
import inspect
import logging
import pkgutil
from pathlib import Path
from typing import Any, Dict, List, Set, Callable, Optional, Type
from dataclasses import dataclass, field
from datetime import datetime

from .versioning import version_manager, check_tool_version, VersionStatus

logger = logging.getLogger(__name__)


@dataclass
class PluginMetadata:
    """Metadata for a discovered plugin."""
    name: str
    version: str = "1.0.0"
    description: str = ""
    domain: str = "general"
    author: str = ""
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    discovered_at: datetime = field(default_factory=datetime.now)


@dataclass
class ToolPlugin:
    """Represents a discovered tool plugin."""
    function: Callable
    metadata: PluginMetadata
    module_path: str
    is_registered: bool = False


class PluginRegistry:
    """Registry for managing tool plugins."""
    
    def __init__(self):
        self._plugins: Dict[str, ToolPlugin] = {}
        self._domains: Set[str] = set()
        self._search_paths: List[str] = []
    
    def register_tool(self, 
                     name: str = None, 
                     version: str = "1.0.0",
                     description: str = "",
                     domain: str = "general",
                     author: str = "",
                     dependencies: List[str] = None,
                     tags: List[str] = None,
                     status: VersionStatus = VersionStatus.ACTIVE,
                     migration_notes: str = "",
                     breaking_changes: List[str] = None):
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
            
            metadata = PluginMetadata(
                name=tool_name,
                version=version,
                description=description or func.__doc__ or f"HACS tool: {tool_name}",
                domain=domain,
                author=author,
                dependencies=dependencies or [],
                tags=tags or []
            )
            
            plugin = ToolPlugin(
                function=func,
                metadata=metadata,
                module_path=func.__module__
            )
            
            self._plugins[tool_name] = plugin
            self._domains.add(domain)
            
            # Register version information
            try:
                from .versioning import register_tool_version
                register_tool_version(
                    tool_name=tool_name,
                    version=version,
                    status=status,
                    migration_notes=migration_notes,
                    breaking_changes=breaking_changes or []
                )
            except Exception as e:
                logger.warning(f"Failed to register version info for {tool_name}: {e}")
            
            # Mark the function as a registered plugin
            func._hacs_plugin = plugin
            func._hacs_registered = True
            
            logger.debug(f"Registered plugin: {tool_name} v{version} (domain: {domain})")
            return func
            
        return decorator
    
    def add_search_path(self, path: str):
        """Add a search path for plugin discovery."""
        if path not in self._search_paths:
            self._search_paths.append(path)
    
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
        if hasattr(package, '__path__'):
            package_path = package.__path__
        else:
            logger.warning(f"Package {package_name} has no __path__ attribute")
            return 0
        
        # Walk through all modules in package
        for importer, modname, ispkg in pkgutil.walk_packages(
            package_path, 
            package_name + "."
        ):
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
            if attr_name.startswith('_'):
                continue
                
            attr = getattr(module, attr_name)
            
            # Check if it's already a registered plugin
            if hasattr(attr, '_hacs_registered'):
                discovered_count += 1
                continue
            
            # Check if it's a potential tool (not just functions now!)
            if self._is_potential_tool(attr, attr_name):
                
                # Auto-register discovered tools
                domain = self._infer_domain_from_module(module_name)
                metadata = self._extract_metadata_from_function(
                    attr, attr_name, domain, module_name
                )
                
                plugin = ToolPlugin(
                    function=attr,
                    metadata=metadata,
                    module_path=module_name
                )
                
                self._plugins[attr_name] = plugin
                self._domains.add(domain)
                
                # Register version information for auto-discovered tools
                try:
                    from .versioning import register_tool_version
                    register_tool_version(
                        tool_name=attr_name,
                        version=metadata.version,
                        status=VersionStatus.ACTIVE,
                        migration_notes="Auto-discovered tool"
                    )
                except Exception as e:
                    logger.debug(f"Could not register version for {attr_name}: {e}")
                
                # Mark as registered
                try:
                    attr._hacs_plugin = plugin  
                    attr._hacs_registered = True
                except AttributeError:
                    # Some objects might not allow attribute assignment
                    pass
                
                discovered_count += 1
                logger.debug(f"Auto-discovered tool: {attr_name} v{metadata.version} in {module_name}")
        
        return discovered_count
    
    def _is_potential_tool(self, func: Callable, name: str) -> bool:
        """Check if a function is potentially a HACS tool."""
        # Skip non-callable objects (strings, modules, classes, etc.)
        if not callable(func) and not hasattr(func, 'func'):
            return False
        
        # Skip constants and description strings
        if isinstance(func, str) or name.endswith('_DESCRIPTION'):
            return False
        
        # Skip modules and classes
        if inspect.ismodule(func) or inspect.isclass(func):
            return False
        
        # Check for LangChain tool markers
        if hasattr(func, '_is_tool'):  # LangChain tool marker
            return True
        
        # Check if it's a LangChain StructuredTool object
        if hasattr(func, 'name') and hasattr(func, 'func'):
            return True
        
        # Check if it has langchain tool attributes
        if hasattr(func, 'description') and hasattr(func, 'args_schema'):
            return True
        
        # Check function signature for HACS patterns
        try:
            # Handle both regular functions and LangChain tools
            actual_func = getattr(func, 'func', func)
            if callable(actual_func):
                sig = inspect.signature(actual_func)
                if "actor_name" in sig.parameters:
                    return True
        except (ValueError, TypeError):
            pass
        
        # Check function name patterns for actual callable functions
        if callable(func):
            tool_keywords = [
                'create', 'get', 'update', 'delete', 'search', 'analyze',
                'execute', 'validate', 'convert', 'process', 'generate',
                'discover', 'extract', 'transform', 'deploy', 'run'
            ]
            
            return any(keyword in name.lower() for keyword in tool_keywords)
        
        return False
    
    def _infer_domain_from_module(self, module_name: str) -> str:
        """Infer domain from module name."""
        module_parts = module_name.split('.')
        
        # Look for domain indicators in module path
        domain_mappings = {
            'resource_management': 'resource_management',
            'clinical_workflow': 'clinical_workflows',
            'clinical_workflows': 'clinical_workflows',
            'schema_discovery': 'schema_discovery',
            'memory_operation': 'memory_operations',
            'memory_operations': 'memory_operations',
            'vector_search': 'vector_search',
            'development_tool': 'development_tools',
            'development_tools': 'development_tools',
            'fhir_integration': 'fhir_integration',
            'healthcare_analytic': 'healthcare_analytics',
            'healthcare_analytics': 'healthcare_analytics',
            'ai_integration': 'ai_integrations',
            'ai_integrations': 'ai_integrations',
            'admin_operation': 'admin_operations',
            'admin_operations': 'admin_operations'
        }
        
        for part in module_parts:
            for pattern, domain in domain_mappings.items():
                if pattern in part:
                    return domain
        
        return "general"
    
    def _extract_metadata_from_function(self, func: Callable, name: str, 
                                      domain: str, module_path: str) -> PluginMetadata:
        """Extract metadata from a function."""
        # Handle LangChain StructuredTool objects
        if hasattr(func, 'name') and hasattr(func, 'description'):
            # This is a LangChain tool
            tool_name = func.name
            tool_description = func.description
        elif hasattr(func, 'func'):
            # This is a LangChain tool with underlying function
            tool_name = name
            tool_description = func.func.__doc__ or f"HACS tool: {name}"
        else:
            # Regular function
            tool_name = name
            tool_description = func.__doc__ or f"HACS tool: {name}"
        
        if tool_description:
            tool_description = tool_description.strip().split('\n')[0]  # First line only
        
        # Extract tags from function name and domain
        tags = []
        name_parts = tool_name.split('_')
        tags.extend(name_parts)
        tags.append(domain)
        
        return PluginMetadata(
            name=tool_name,
            description=tool_description,
            domain=domain,
            tags=list(set(tags))  # Remove duplicates
        )
    
    def get_plugin(self, name: str) -> Optional[ToolPlugin]:
        """Get a plugin by name."""
        return self._plugins.get(name)
    
    def get_plugins_by_domain(self, domain: str) -> List[ToolPlugin]:
        """Get all plugins for a specific domain."""
        return [plugin for plugin in self._plugins.values() 
                if plugin.metadata.domain == domain]
    
    def get_all_plugins(self) -> Dict[str, ToolPlugin]:
        """Get all registered plugins."""
        return self._plugins.copy()
    
    def get_domains(self) -> Set[str]:
        """Get all discovered domains."""
        return self._domains.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get discovery statistics."""
        domain_counts = {}
        for domain in self._domains:
            domain_counts[domain] = len(self.get_plugins_by_domain(domain))
        
        return {
            "total_plugins": len(self._plugins),
            "total_domains": len(self._domains),
            "domain_counts": domain_counts,
            "search_paths": self._search_paths.copy()
        }


# Global plugin registry instance
plugin_registry = PluginRegistry()

# Convenience decorator using global registry
def register_tool(name: str = None, 
                 version: str = "1.0.0",
                 description: str = "",
                 domain: str = "general", 
                 author: str = "",
                 dependencies: List[str] = None,
                 tags: List[str] = None,
                 status: VersionStatus = VersionStatus.ACTIVE,
                 migration_notes: str = "",
                 breaking_changes: List[str] = None):
    """
    Global tool registration decorator with versioning support.
    
    Usage:
        @register_tool(name="my_tool", domain="healthcare", version="1.1.0", 
                      status=VersionStatus.ACTIVE)
        def my_healthcare_tool(actor_name: str, data: dict) -> HACSResult:
            # Tool implementation
            pass
            
        @register_tool(name="my_old_tool", version="1.0.0", 
                      status=VersionStatus.DEPRECATED,
                      migration_notes="Please use my_tool v1.1.0 instead")
        def my_old_tool(actor_name: str, data: dict) -> HACSResult:
            # Deprecated implementation
            pass
    """
    return plugin_registry.register_tool(
        name=name,
        version=version,
        description=description,
        domain=domain,
        author=author,
        dependencies=dependencies,
        tags=tags,
        status=status,
        migration_notes=migration_notes,
        breaking_changes=breaking_changes
    )


def discover_hacs_plugins(base_packages: List[str] = None) -> PluginRegistry:
    """
    Discover and return all HACS plugins.
    
    Args:
        base_packages: Base packages to search (defaults to ["hacs_tools"])
        
    Returns:
        PluginRegistry with discovered plugins
    """
    if base_packages is None:
        base_packages = ["hacs_tools"]
    
    plugin_registry.discover_plugins(base_packages)
    return plugin_registry