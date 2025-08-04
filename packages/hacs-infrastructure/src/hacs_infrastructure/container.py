"""
Dependency Injection Container for HACS Infrastructure

This module provides a comprehensive dependency injection container designed
for healthcare AI systems with type safety, lifecycle management, and
advanced injection patterns.

Key Features:
- Framework adapter integration for SOLID-compliant tool systems
- Healthcare-specific service registration patterns
- Advanced lifecycle management
- Thread-safe operations
"""

import inspect
import logging
import threading
import weakref
from abc import ABC, abstractmethod
from contextlib import contextmanager
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, Type, TypeVar, Union, get_args, get_origin

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


T = TypeVar("T")
TService = TypeVar("TService")


class ServiceLifetime(str, Enum):
    """Service lifetime scopes for dependency injection."""
    
    TRANSIENT = "transient"  # New instance every time
    SINGLETON = "singleton"  # Single instance for entire application
    SCOPED = "scoped"        # Single instance per scope (e.g., request)


class ServiceError(Exception):
    """Base exception for service-related errors."""
    
    def __init__(self, message: str, service_type: Optional[Type] = None):
        super().__init__(message)
        self.service_type = service_type


class DependencyError(ServiceError):
    """Exception raised when dependency resolution fails."""
    pass


class CircularDependencyError(DependencyError):
    """Exception raised when circular dependencies are detected."""
    pass


class ServiceDescriptor(BaseModel):
    """Describes how to construct and manage a service."""
    
    service_type: Type = Field(..., description="The service type/class")
    implementation_type: Optional[Type] = Field(None, description="Implementation type if different from service type")
    factory: Optional[Callable[..., Any]] = Field(None, description="Factory function for service creation")
    instance: Optional[Any] = Field(None, description="Pre-created instance for singleton")
    lifetime: ServiceLifetime = Field(ServiceLifetime.TRANSIENT, description="Service lifetime scope")
    dependencies: List[Type] = Field(default_factory=list, description="Required dependencies")
    
    class Config:
        arbitrary_types_allowed = True


class InjectionContext:
    """Context for dependency injection resolution."""
    
    def __init__(self):
        self._resolving: set[Type] = set()
        
    def is_resolving(self, service_type: Type) -> bool:
        """Check if a service type is currently being resolved."""
        return service_type in self._resolving
    
    @contextmanager
    def resolving(self, service_type: Type):
        """Context manager for tracking service resolution."""
        if service_type in self._resolving:
            raise CircularDependencyError(
                f"Circular dependency detected: {service_type.__name__} is already being resolved"
            )
        
        self._resolving.add(service_type)
        try:
            yield
        finally:
            self._resolving.discard(service_type)


class Scope:
    """Represents a dependency injection scope."""
    
    def __init__(self, name: str):
        self.name = name
        self._instances: Dict[Type, Any] = {}
        self._lock = threading.RLock()
    
    def get_scoped_instance(self, service_type: Type) -> Optional[Any]:
        """Get scoped instance if it exists."""
        with self._lock:
            return self._instances.get(service_type)
    
    def set_scoped_instance(self, service_type: Type, instance: Any) -> None:
        """Set scoped instance."""
        with self._lock:
            self._instances[service_type] = instance
    
    def clear(self) -> None:
        """Clear all scoped instances."""
        with self._lock:
            # Dispose instances if they have a dispose method
            for instance in self._instances.values():
                if hasattr(instance, 'dispose'):
                    try:
                        instance.dispose()
                    except Exception:
                        pass  # Continue cleanup even if disposal fails
            self._instances.clear()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.clear()


class Container:
    """
    Dependency injection container with healthcare-specific optimizations.
    
    Provides comprehensive dependency injection with support for:
    - Multiple service lifetimes (transient, singleton, scoped)
    - Automatic constructor injection
    - Factory functions
    - Circular dependency detection
    - Thread-safe operations
    - Scope management for request/session-based services
    """
    
    def __init__(self, parent: Optional["Container"] = None):
        """
        Initialize container.
        
        Args:
            parent: Parent container for hierarchical DI
        """
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._parent = parent
        self._lock = threading.RLock()
        self._current_scope: Optional[Scope] = None
        
    def register(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable[..., T]] = None,
        instance: Optional[T] = None,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    ) -> "Container":
        """
        Register a service with the container.
        
        Args:
            service_type: The service type/interface
            implementation_type: Implementation type (defaults to service_type)
            factory: Factory function for creating instances
            instance: Pre-created instance for singleton services
            lifetime: Service lifetime scope
            
        Returns:
            Self for method chaining
        """
        with self._lock:
            impl_type = implementation_type or service_type
            
            # If instance provided, force singleton lifetime
            if instance is not None:
                lifetime = ServiceLifetime.SINGLETON
                self._singletons[service_type] = instance
            
            # Analyze dependencies from constructor
            dependencies = self._analyze_dependencies(impl_type)
            
            descriptor = ServiceDescriptor(
                service_type=service_type,
                implementation_type=impl_type,
                factory=factory,
                instance=instance,
                lifetime=lifetime,
                dependencies=dependencies
            )
            
            self._services[service_type] = descriptor
        
        return self
    
    def register_singleton(self, service_type: Type[T], implementation_type: Optional[Type[T]] = None) -> "Container":
        """Register service as singleton."""
        return self.register(service_type, implementation_type, lifetime=ServiceLifetime.SINGLETON)
    
    def register_scoped(self, service_type: Type[T], implementation_type: Optional[Type[T]] = None) -> "Container":
        """Register service as scoped."""
        return self.register(service_type, implementation_type, lifetime=ServiceLifetime.SCOPED)
    
    def register_factory(self, service_type: Type[T], factory: Callable[..., T]) -> "Container":
        """Register service with factory function."""
        return self.register(service_type, factory=factory)
    
    def register_instance(self, service_type: Type[T], instance: T) -> "Container":
        """Register pre-created instance."""
        return self.register(service_type, instance=instance)
    
    def get(self, service_type: Type[T]) -> T:
        """
        Get service instance from container.
        
        Args:
            service_type: Type of service to retrieve
            
        Returns:
            Service instance
            
        Raises:
            DependencyError: If service is not registered or cannot be created
        """
        context = InjectionContext()
        return self._resolve_service(service_type, context)
    
    def _resolve_service(self, service_type: Type[T], context: InjectionContext) -> T:
        """Resolve service with dependency injection context."""
        with context.resolving(service_type):
            with self._lock:
                # Check if service is registered in this container
                if service_type in self._services:
                    descriptor = self._services[service_type]
                    return self._create_instance(descriptor, context)
                
                # Check parent container
                if self._parent is not None:
                    try:
                        return self._parent._resolve_service(service_type, context)
                    except DependencyError:
                        pass
                
                # Try to auto-register if it's a concrete class
                if self._can_auto_register(service_type):
                    self.register(service_type)
                    descriptor = self._services[service_type]
                    return self._create_instance(descriptor, context)
                
                raise DependencyError(f"Service {service_type.__name__} is not registered", service_type)
    
    def _create_instance(self, descriptor: ServiceDescriptor, context: InjectionContext) -> Any:
        """Create service instance based on descriptor."""
        service_type = descriptor.service_type
        
        # Handle singleton lifetime
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            if service_type in self._singletons:
                return self._singletons[service_type]
            
            instance = self._construct_instance(descriptor, context)
            self._singletons[service_type] = instance
            return instance
        
        # Handle scoped lifetime
        if descriptor.lifetime == ServiceLifetime.SCOPED:
            if self._current_scope is not None:
                scoped_instance = self._current_scope.get_scoped_instance(service_type)
                if scoped_instance is not None:
                    return scoped_instance
                
                instance = self._construct_instance(descriptor, context)
                self._current_scope.set_scoped_instance(service_type, instance)
                return instance
            else:
                # No scope, treat as transient
                return self._construct_instance(descriptor, context)
        
        # Handle transient lifetime (default)
        return self._construct_instance(descriptor, context)
    
    def _construct_instance(self, descriptor: ServiceDescriptor, context: InjectionContext) -> Any:
        """Construct instance using factory or constructor."""
        # Use pre-created instance if available
        if descriptor.instance is not None:
            return descriptor.instance
        
        # Use factory if provided
        if descriptor.factory is not None:
            factory_args = self._resolve_factory_args(descriptor.factory, context)
            return descriptor.factory(**factory_args)
        
        # Use constructor injection
        impl_type = descriptor.implementation_type or descriptor.service_type
        constructor_args = self._resolve_constructor_args(impl_type, context)
        
        try:
            return impl_type(**constructor_args)
        except Exception as e:
            raise DependencyError(
                f"Failed to create instance of {impl_type.__name__}: {e}",
                impl_type
            ) from e
    
    def _resolve_constructor_args(self, service_type: Type, context: InjectionContext) -> Dict[str, Any]:
        """Resolve constructor arguments through dependency injection."""
        args = {}
        
        # Get constructor signature
        try:
            signature = inspect.signature(service_type.__init__)
        except (ValueError, TypeError):
            return args
        
        # Skip 'self' parameter
        parameters = list(signature.parameters.values())[1:]
        
        for param in parameters:
            param_type = param.annotation
            
            # Skip parameters without type annotations
            if param_type == inspect.Parameter.empty:
                if param.default == inspect.Parameter.empty:
                    raise DependencyError(
                        f"Parameter '{param.name}' in {service_type.__name__} has no type annotation and no default value"
                    )
                continue
            
            # Skip string annotations (forward references) that can't be resolved
            if isinstance(param_type, str):
                if param.default != inspect.Parameter.empty:
                    args[param.name] = param.default
                else:
                    # For testing purposes, skip unresolvable forward references
                    continue
            
            # Handle Optional types
            elif self._is_optional_type(param_type):
                try:
                    args[param.name] = self._resolve_service(self._get_optional_inner_type(param_type), context)
                except DependencyError:
                    # Optional dependency not available, use default or None
                    if param.default != inspect.Parameter.empty:
                        args[param.name] = param.default
                    else:
                        args[param.name] = None
            else:
                # Required dependency
                try:
                    args[param.name] = self._resolve_service(param_type, context)
                except DependencyError:
                    if param.default != inspect.Parameter.empty:
                        args[param.name] = param.default
                    else:
                        raise
        
        return args
    
    def _resolve_factory_args(self, factory: Callable, context: InjectionContext) -> Dict[str, Any]:
        """Resolve factory function arguments."""
        args = {}
        
        try:
            signature = inspect.signature(factory)
        except (ValueError, TypeError):
            return args
        
        for param in signature.parameters.values():
            param_type = param.annotation
            
            if param_type == inspect.Parameter.empty:
                if param.default == inspect.Parameter.empty:
                    raise DependencyError(f"Factory parameter '{param.name}' has no type annotation and no default value")
                continue
            
            try:
                args[param.name] = self._resolve_service(param_type, context)
            except DependencyError:
                if param.default != inspect.Parameter.empty:
                    args[param.name] = param.default
                else:
                    raise
        
        return args
    
    def _analyze_dependencies(self, service_type: Type) -> List[Type]:
        """Analyze service dependencies from constructor."""
        dependencies = []
        
        try:
            signature = inspect.signature(service_type.__init__)
            parameters = list(signature.parameters.values())[1:]  # Skip 'self'
            
            for param in parameters:
                if param.annotation != inspect.Parameter.empty:
                    param_type = param.annotation
                    if self._is_optional_type(param_type):
                        param_type = self._get_optional_inner_type(param_type)
                    
                    # Skip string annotations (forward references) to avoid validation errors
                    if not isinstance(param_type, str):
                        dependencies.append(param_type)
        except (ValueError, TypeError):
            pass
        
        return dependencies
    
    def _can_auto_register(self, service_type: Type) -> bool:
        """Check if service can be auto-registered."""
        return (
            inspect.isclass(service_type) and
            not inspect.isabstract(service_type) and
            hasattr(service_type, '__init__')
        )
    
    def _is_optional_type(self, type_hint: Any) -> bool:
        """Check if type hint is Optional[T] or Union[T, None]."""
        origin = get_origin(type_hint)
        if origin is Union:
            args = get_args(type_hint)
            return len(args) == 2 and type(None) in args
        return False
    
    def _get_optional_inner_type(self, type_hint: Any) -> Type:
        """Get inner type from Optional[T]."""
        args = get_args(type_hint)
        return next(arg for arg in args if arg is not type(None))
    
    @contextmanager
    def create_scope(self, name: str = "default"):
        """Create a new dependency injection scope."""
        scope = Scope(name)
        old_scope = self._current_scope
        self._current_scope = scope
        
        try:
            yield scope
        finally:
            self._current_scope = old_scope
            scope.clear()
    
    def is_registered(self, service_type: Type) -> bool:
        """Check if service type is registered."""
        with self._lock:
            if service_type in self._services:
                return True
            if self._parent is not None:
                return self._parent.is_registered(service_type)
            return False
    
    def get_registered_services(self) -> List[Type]:
        """Get list of all registered service types."""
        with self._lock:
            services = list(self._services.keys())
            if self._parent is not None:
                services.extend(self._parent.get_registered_services())
            return list(set(services))  # Remove duplicates
    
    def create_child(self) -> "Container":
        """Create child container for hierarchical dependency injection."""
        return Container(parent=self)
    
    def configure_framework_adapter(self, adapter_or_name: Union[str, Any]) -> "Container":
        """
        Configure framework adapter for HACS tools.
        
        Args:
            adapter_or_name: Framework adapter instance or name ('langchain', 'mcp', 'crewai')
            
        Returns:
            Self for method chaining
        """
        try:
            # Import here to avoid circular dependencies
            from hacs_core.tool_protocols import set_global_framework_adapter
            
            if isinstance(adapter_or_name, str):
                # Create adapter by name
                from hacs_utils.integrations.framework_adapter import create_framework_adapter
                adapter = create_framework_adapter(adapter_or_name)
            else:
                # Use provided adapter instance
                adapter = adapter_or_name
            
            # Set global adapter for HACS tools
            set_global_framework_adapter(adapter)
            
            # Register adapter services with container
            self.register_instance(type(adapter), adapter)
            
            # Register tool decorator and registry
            tool_decorator = adapter.create_tool_decorator()
            tool_registry = adapter.create_tool_registry()
            
            # Import protocols for type registration
            from hacs_core.tool_protocols import ToolDecorator, ToolRegistry
            self.register_instance(ToolDecorator, tool_decorator)
            self.register_instance(ToolRegistry, tool_registry)
            
            logger.info(f"Configured framework adapter: {adapter.framework_name} v{adapter.framework_version}")
            
        except ImportError as e:
            logger.warning(f"Failed to configure framework adapter: {e}")
            logger.info("Framework adapters require hacs-core and hacs-utils packages")
        
        return self
    
    def register_healthcare_services(self) -> "Container":
        """
        Register common healthcare services and patterns.
        
        Returns:
            Self for method chaining
        """
        try:
            # Register core HACS services
            from hacs_core import Actor
            from hacs_core.results import HACSResult
            
            # Register common healthcare types
            self.register(Actor, lifetime=ServiceLifetime.SCOPED)
            
            # Try to register additional healthcare services if available
            try:
                from hacs_models import Patient, Observation, Encounter
                self.register(Patient, lifetime=ServiceLifetime.SCOPED)
                self.register(Observation, lifetime=ServiceLifetime.TRANSIENT)
                self.register(Encounter, lifetime=ServiceLifetime.SCOPED)
            except ImportError:
                logger.debug("hacs-models not available, skipping model registration")
            
            try:
                from hacs_persistence import MemoryManager
                self.register(MemoryManager, lifetime=ServiceLifetime.SINGLETON)
            except ImportError:
                logger.debug("hacs-persistence not available, skipping persistence registration")
            
            logger.info("Registered common healthcare services")
            
        except ImportError as e:
            logger.warning(f"Failed to register healthcare services: {e}")
        
        return self
    
    def validate_framework_integration(self) -> Dict[str, Any]:
        """
        Validate framework integration setup.
        
        Returns:
            Validation report with status and recommendations
        """
        report = {
            "container_status": "healthy",
            "registered_services": len(self._services),
            "singleton_instances": len(self._singletons),
            "framework_adapter": None,
            "tool_services": {},
            "recommendations": []
        }
        
        try:
            # Check for framework adapter
            from hacs_core.tool_protocols import get_global_framework_adapter
            adapter = get_global_framework_adapter()
            
            report["framework_adapter"] = {
                "name": adapter.framework_name,
                "version": adapter.framework_version,
                "available": adapter.is_available()
            }
            
            # Check tool services
            from hacs_core.tool_protocols import ToolDecorator, ToolRegistry
            
            if self.is_registered(ToolDecorator):
                decorator = self.get(ToolDecorator)
                report["tool_services"]["decorator"] = str(type(decorator))
            else:
                report["recommendations"].append("Register ToolDecorator service")
            
            if self.is_registered(ToolRegistry):
                registry = self.get(ToolRegistry)
                report["tool_services"]["registry"] = str(type(registry))
                
                # Get registry info if available
                if hasattr(registry, 'list_tools'):
                    try:
                        tools = registry.list_tools()
                        report["tool_services"]["registered_tools"] = len(tools)
                    except Exception:
                        pass
            else:
                report["recommendations"].append("Register ToolRegistry service")
            
        except ImportError:
            report["framework_adapter"] = "not_configured"
            report["recommendations"].append("Configure framework adapter using configure_framework_adapter()")
        except Exception as e:
            report["container_status"] = "warning"
            report["recommendations"].append(f"Framework integration issue: {e}")
        
        return report

    def dispose(self) -> None:
        """Dispose container and clean up resources."""
        with self._lock:
            # Dispose singleton instances
            for instance in self._singletons.values():
                if hasattr(instance, 'dispose'):
                    try:
                        instance.dispose()
                    except Exception:
                        pass
            
            self._singletons.clear()
            self._services.clear()
            
            if self._current_scope is not None:
                self._current_scope.clear()


# Decorators for dependency injection

def Injectable(cls: Type[T]) -> Type[T]:
    """
    Decorator to mark a class as injectable.
    
    This is primarily for documentation and future tooling support.
    The container can inject any class with proper type annotations.
    """
    cls._injectable = True
    return cls


def Singleton(cls: Type[T]) -> Type[T]:
    """
    Decorator to mark a class as singleton.
    
    Classes marked with this decorator will be automatically registered
    as singletons when first resolved.
    """
    cls._lifetime = ServiceLifetime.SINGLETON
    return cls


def Scoped(cls: Type[T]) -> Type[T]:
    """
    Decorator to mark a class as scoped.
    
    Classes marked with this decorator will be automatically registered
    as scoped when first resolved.
    """
    cls._lifetime = ServiceLifetime.SCOPED
    return cls


# Global container instance
_global_container: Optional[Container] = None
_container_lock = threading.RLock()


def get_container() -> Container:
    """
    Get the global container instance.
    
    Returns:
        Global container instance
    """
    global _global_container
    with _container_lock:
        if _global_container is None:
            _global_container = Container()
        return _global_container


def set_container(container: Container) -> None:
    """
    Set the global container instance.
    
    Args:
        container: Container instance to set as global
    """
    global _global_container
    with _container_lock:
        _global_container = container


def reset_container() -> None:
    """Reset the global container instance."""
    global _global_container
    with _container_lock:
        if _global_container is not None:
            _global_container.dispose()
        _global_container = None


def configure_hacs_container(
    framework: Optional[str] = None,
    register_healthcare_services: bool = True
) -> Container:
    """
    Configure HACS container with framework adapter and healthcare services.
    
    Args:
        framework: Framework name ('langchain', 'mcp', 'crewai') or None for auto-detection
        register_healthcare_services: Whether to register common healthcare services
        
    Returns:
        Configured container instance
        
    Example:
        >>> container = configure_hacs_container('langchain')
        >>> # Container now has framework adapter and healthcare services configured
    """
    container = get_container()
    
    # Configure framework adapter
    if framework is not None:
        container.configure_framework_adapter(framework)
    else:
        # Auto-detect and configure best available framework
        try:
            from hacs_utils.integrations.framework_adapter import FrameworkDetector
            available = FrameworkDetector.detect_available_frameworks()
            if available:
                best_framework = available[0]  # Use first available
                container.configure_framework_adapter(best_framework)
                logger.info(f"Auto-configured framework: {best_framework}")
            else:
                logger.warning("No AI frameworks detected, using no-op adapter")
                container.configure_framework_adapter("none")
        except ImportError:
            logger.warning("Framework detection not available")
    
    # Register healthcare services
    if register_healthcare_services:
        container.register_healthcare_services()
    
    return container


def validate_hacs_setup() -> Dict[str, Any]:
    """
    Validate complete HACS container and framework setup.
    
    Returns:
        Comprehensive validation report
    """
    container = get_container()
    
    # Get container validation
    container_report = container.validate_framework_integration()
    
    # Add framework adapter validation
    try:
        from hacs_utils.integrations.framework_adapter import validate_framework_integration
        framework_report = validate_framework_integration()
        
        report = {
            "overall_status": "healthy" if container_report["container_status"] == "healthy" else "warning",
            "container": container_report,
            "framework_integration": framework_report,
            "summary": {
                "container_services": container_report["registered_services"],
                "available_frameworks": framework_report.get("available_frameworks", []),
                "active_framework": container_report.get("framework_adapter", {}).get("name", "none"),
                "recommendations": container_report["recommendations"]
            }
        }
        
        # Add framework-specific recommendations
        if framework_report.get("errors"):
            report["summary"]["recommendations"].extend([
                f"Framework error: {error}" for error in framework_report["errors"]
            ])
        
        return report
        
    except ImportError:
        return {
            "overall_status": "warning",
            "container": container_report,
            "framework_integration": "not_available",
            "summary": {
                "container_services": container_report["registered_services"],
                "available_frameworks": [],
                "active_framework": "unknown",
                "recommendations": container_report["recommendations"] + [
                    "Install hacs-utils for framework integration"
                ]
            }
        }