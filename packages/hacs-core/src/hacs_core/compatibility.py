"""
Backward Compatibility Layer for HACS SOLID Migration

This module provides backward compatibility support during the migration
from direct LangChain dependencies to the new framework-agnostic architecture.

Features:
- Legacy import support with deprecation warnings
- Automatic framework detection and configuration
- Gradual migration support
- Performance monitoring
"""

import warnings
import logging
from typing import Any, Callable, Dict, List, Optional, TypeVar
from functools import wraps

logger = logging.getLogger(__name__)
F = TypeVar('F', bound=Callable[..., Any])


class DeprecationHelper:
    """Helper class for managing deprecation warnings and migration guidance."""
    
    def __init__(self):
        self._warned_items: set[str] = set()
        self._migration_stats = {
            'legacy_imports': 0,
            'legacy_decorators': 0,
            'framework_detections': 0
        }
    
    def warn_once(self, item_id: str, message: str, category: type = DeprecationWarning) -> None:
        """Issue a deprecation warning only once per item."""
        if item_id not in self._warned_items:
            warnings.warn(message, category, stacklevel=3)
            self._warned_items.add(item_id)
            logger.debug(f"Deprecation warning issued for: {item_id}")
    
    def track_usage(self, category: str) -> None:
        """Track legacy usage for migration metrics."""
        if category in self._migration_stats:
            self._migration_stats[category] += 1
    
    def get_migration_stats(self) -> Dict[str, Any]:
        """Get migration statistics."""
        return {
            'warnings_issued': len(self._warned_items),
            'usage_stats': self._migration_stats.copy(),
            'warned_items': list(self._warned_items)
        }


# Global deprecation helper
_deprecation_helper = DeprecationHelper()


def get_migration_stats() -> Dict[str, Any]:
    """Get current migration statistics."""
    return _deprecation_helper.get_migration_stats()


def legacy_tool_decorator(func: F) -> F:
    """
    Legacy tool decorator that provides backward compatibility.
    
    This decorator:
    1. Issues deprecation warnings
    2. Automatically configures framework adapter if needed
    3. Applies the new healthcare_tool decorator
    4. Tracks usage for migration metrics
    """
    
    # Issue deprecation warning
    _deprecation_helper.warn_once(
        f"legacy_tool_{func.__name__}",
        f"Direct @tool decorator usage is deprecated. "
        f"Use @healthcare_tool from hacs_core.tool_protocols instead. "
        f"See HACS_SOLID_MIGRATION_GUIDE.md for details.",
        DeprecationWarning
    )
    
    # Track usage
    _deprecation_helper.track_usage('legacy_decorators')
    
    # Try to apply new decorator pattern
    try:
        from hacs_core.tool_protocols import healthcare_tool, ToolCategory
        
        # Auto-detect appropriate category based on function name/module
        category = _detect_tool_category(func)
        
        # Extract description from docstring
        description = _extract_description(func)
        
        # Apply new decorator with sensible defaults
        new_decorator = healthcare_tool(
            name=func.__name__,
            description=description,
            category=category,
            healthcare_domains=["general_healthcare"],
            fhir_resources=["Patient", "Observation"]  # Common defaults
        )
        
        decorated_func = new_decorator(func)
        
        # Ensure framework is configured
        _ensure_framework_configured()
        
        logger.debug(f"Auto-migrated legacy tool: {func.__name__}")
        return decorated_func
        
    except ImportError as e:
        logger.warning(f"Could not auto-migrate tool {func.__name__}: {e}")
        # Return original function with legacy marker
        func._legacy_tool = True
        return func


def _detect_tool_category(func: Callable) -> 'ToolCategory':
    """Auto-detect tool category based on function context."""
    try:
        from hacs_core.tool_protocols import ToolCategory
        
        # Check module path for hints
        module = getattr(func, '__module__', '')
        name = func.__name__.lower()
        
        if 'resource_management' in module or any(word in name for word in ['create', 'get', 'update', 'delete', 'resource']):
            return ToolCategory.RESOURCE_MANAGEMENT
        elif 'clinical_workflows' in module or any(word in name for word in ['clinical', 'workflow', 'protocol']):
            return ToolCategory.CLINICAL_WORKFLOWS
        elif 'memory' in module or 'memory' in name:
            return ToolCategory.MEMORY_OPERATIONS
        elif 'vector' in module or 'search' in name:
            return ToolCategory.VECTOR_SEARCH
        elif 'analytics' in module or 'analyt' in name:
            return ToolCategory.HEALTHCARE_ANALYTICS
        elif 'admin' in module or 'admin' in name:
            return ToolCategory.ADMIN_OPERATIONS
        else:
            return ToolCategory.RESOURCE_MANAGEMENT  # Safe default
            
    except ImportError:
        # If ToolCategory not available, return string
        return "resource_management"


def _extract_description(func: Callable) -> str:
    """Extract description from function docstring."""
    docstring = func.__doc__
    if not docstring:
        return f"Healthcare tool: {func.__name__}"
    
    # Get first line of docstring
    first_line = docstring.strip().split('\n')[0].strip()
    return first_line or f"Healthcare tool: {func.__name__}"


def _ensure_framework_configured() -> None:
    """Ensure framework adapter is configured, with auto-detection if needed."""
    try:
        from hacs_core.tool_protocols import get_global_framework_adapter
        
        # Check if already configured
        adapter = get_global_framework_adapter()
        if adapter.framework_name != "none":
            return  # Already configured
        
        # Auto-configure framework
        _deprecation_helper.track_usage('framework_detections')
        
        try:
            from hacs_utils.integrations.framework_adapter import FrameworkDetector
            available = FrameworkDetector.detect_available_frameworks()
            
            if available:
                from hacs_infrastructure.container import get_container
                container = get_container()
                container.configure_framework_adapter(available[0])
                
                logger.info(f"Auto-configured framework adapter: {available[0]}")
            else:
                logger.warning("No AI frameworks detected for auto-configuration")
                
        except ImportError:
            logger.debug("Framework auto-detection not available")
            
    except ImportError:
        logger.debug("Framework adapter system not available")


class LegacyToolModule:
    """
    Compatibility module that provides legacy tool decorator import.
    
    This allows existing code using:
        from langchain_core.tools import tool
    
    To continue working with deprecation warnings.
    """
    
    def __init__(self):
        self._tool_decorator = legacy_tool_decorator
    
    @property
    def tool(self) -> Callable[[F], F]:
        """Legacy tool decorator with deprecation warning."""
        _deprecation_helper.warn_once(
            "langchain_import",
            "Importing 'tool' from langchain_core.tools is deprecated. "
            "Use 'healthcare_tool' from hacs_core.tool_protocols instead.",
            DeprecationWarning
        )
        _deprecation_helper.track_usage('legacy_imports')
        
        return self._tool_decorator


def create_legacy_import_hook():
    """
    Create import hook for legacy langchain_core.tools imports.
    
    This allows existing code to continue working during migration.
    """
    import sys
    
    class LegacyImportFinder:
        """Custom import finder for legacy langchain imports."""
        
        def find_spec(self, fullname, path, target=None):
            if fullname == 'langchain_core.tools':
                # Return our compatibility module
                import importlib.util
                spec = importlib.util.spec_from_loader(
                    fullname,
                    LegacyImportLoader(),
                    origin="hacs_compatibility"
                )
                return spec
            return None
    
    class LegacyImportLoader:
        """Custom loader for legacy imports."""
        
        def create_module(self, spec):
            return LegacyToolModule()
        
        def exec_module(self, module):
            pass
    
    # Install the import hook
    if not any(isinstance(finder, LegacyImportFinder) for finder in sys.meta_path):
        sys.meta_path.insert(0, LegacyImportFinder())
        logger.debug("Installed legacy import compatibility hook")


def configure_backward_compatibility(
    enable_import_hooks: bool = True,
    warning_level: str = "default"
) -> None:
    """
    Configure backward compatibility settings.
    
    Args:
        enable_import_hooks: Whether to enable legacy import compatibility
        warning_level: Deprecation warning level ('ignore', 'default', 'error')
    """
    
    # Configure warning levels
    if warning_level == "ignore":
        warnings.filterwarnings("ignore", category=DeprecationWarning, module="hacs_core.compatibility")
    elif warning_level == "error":
        warnings.filterwarnings("error", category=DeprecationWarning, module="hacs_core.compatibility")
    
    # Enable import hooks if requested
    if enable_import_hooks:
        create_legacy_import_hook()
    
    logger.info(f"Configured backward compatibility: import_hooks={enable_import_hooks}, warnings={warning_level}")


def validate_migration_progress() -> Dict[str, Any]:
    """
    Validate migration progress and provide recommendations.
    
    Returns:
        Migration progress report with recommendations
    """
    stats = get_migration_stats()
    
    # Analyze usage patterns
    total_legacy_usage = sum(stats['usage_stats'].values())
    
    if total_legacy_usage == 0:
        migration_status = "complete"
        recommendations = ["Migration completed successfully!"]
    elif stats['usage_stats']['legacy_imports'] > 0:
        migration_status = "in_progress"
        recommendations = [
            "Update imports to use hacs_core.tool_protocols",
            "Replace @tool with @healthcare_tool decorators",
            "See HACS_SOLID_MIGRATION_GUIDE.md for detailed instructions"
        ]
    else:
        migration_status = "minimal"
        recommendations = [
            "Continue gradual migration to new patterns",
            "Consider updating remaining legacy tool decorators"
        ]
    
    # Check framework configuration
    framework_status = "unknown"
    try:
        from hacs_core.tool_protocols import get_global_framework_adapter
        adapter = get_global_framework_adapter()
        framework_status = adapter.framework_name
        
        if framework_status == "none":
            recommendations.append("Configure framework adapter for optimal performance")
    except ImportError:
        recommendations.append("Install hacs-utils for framework adapter support")
    
    return {
        "migration_status": migration_status,
        "framework_status": framework_status,
        "legacy_usage": total_legacy_usage,
        "statistics": stats,
        "recommendations": recommendations,
        "next_steps": [
            "Review HACS_SOLID_MIGRATION_GUIDE.md",
            "Run migration validation script",
            "Update code to use new patterns",
            "Test thoroughly before removing compatibility layer"
        ]
    }


# Auto-configure on import
try:
    configure_backward_compatibility()
except Exception as e:
    logger.debug(f"Auto-configuration of backward compatibility failed: {e}")


__all__ = [
    'legacy_tool_decorator',
    'configure_backward_compatibility', 
    'validate_migration_progress',
    'get_migration_stats',
    'LegacyToolModule'
]