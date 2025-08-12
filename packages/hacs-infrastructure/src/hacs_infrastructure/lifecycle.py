"""
Service Lifecycle Management for HACS Infrastructure

This module provides comprehensive lifecycle management for services
with graceful startup, shutdown, and dependency orchestration.
"""

import asyncio
import logging
import signal
import sys
import threading
import time
from contextlib import asynccontextmanager
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from pydantic import BaseModel, Field

from .protocols import Startable, Stoppable


logger = logging.getLogger(__name__)


class LifecycleState(str, Enum):
    """Service lifecycle states."""
    
    CREATED = "created"
    STARTING = "starting"
    STARTED = "started"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    FAILED = "failed"


class ServiceLifecycle:
    """
    Manages the lifecycle of a single service with state tracking
    and dependency management.
    """
    
    def __init__(
        self,
        name: str,
        service: Any,
        dependencies: Optional[List[str]] = None,
        startup_timeout: float = 30.0,
        shutdown_timeout: float = 30.0
    ):
        """
        Initialize service lifecycle manager.
        
        Args:
            name: Service name
            service: Service instance
            dependencies: List of dependency service names
            startup_timeout: Startup timeout in seconds
            shutdown_timeout: Shutdown timeout in seconds
        """
        self.name = name
        self.service = service
        self.dependencies = dependencies or []
        self.startup_timeout = startup_timeout
        self.shutdown_timeout = shutdown_timeout
        
        self._state = LifecycleState.CREATED
        self._error: Optional[Exception] = None
        self._started_at: Optional[float] = None
        self._stopped_at: Optional[float] = None
        self._lock = threading.RLock()
        
        # Lifecycle callbacks
        self._startup_callbacks: List[Callable[[], None]] = []
        self._shutdown_callbacks: List[Callable[[], None]] = []
        
    @property
    def state(self) -> LifecycleState:
        """Get current lifecycle state."""
        with self._lock:
            return self._state
    
    @property
    def is_running(self) -> bool:
        """Check if service is running."""
        return self.state == LifecycleState.RUNNING
    
    @property
    def uptime(self) -> Optional[float]:
        """Get service uptime in seconds."""
        if self._started_at is None:
            return None
        return time.time() - self._started_at
    
    def add_startup_callback(self, callback: Callable[[], None]) -> None:
        """Add startup callback."""
        self._startup_callbacks.append(callback)
    
    def add_shutdown_callback(self, callback: Callable[[], None]) -> None:
        """Add shutdown callback."""
        self._shutdown_callbacks.append(callback)
    
    async def start(self) -> None:
        """Start the service."""
        with self._lock:
            if self._state not in [LifecycleState.CREATED, LifecycleState.STOPPED]:
                raise RuntimeError(f"Cannot start service in state {self._state}")
            
            self._state = LifecycleState.STARTING
            self._error = None
        
        try:
            logger.info(f"Starting service: {self.name}")
            
            # Execute startup callbacks
            for callback in self._startup_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.warning(f"Startup callback failed for {self.name}: {e}")
            
            # Start the service
            if hasattr(self.service, 'start') and callable(self.service.start):
                await asyncio.wait_for(
                    self.service.start(),
                    timeout=self.startup_timeout
                )
            
            with self._lock:
                self._state = LifecycleState.STARTED
                self._started_at = time.time()
            
            # Wait a moment then mark as running if no errors
            await asyncio.sleep(0.1)
            
            with self._lock:
                if self._state == LifecycleState.STARTED:
                    self._state = LifecycleState.RUNNING
            
            logger.info(f"Service started successfully: {self.name}")
            
        except Exception as e:
            logger.error(f"Failed to start service {self.name}: {e}")
            with self._lock:
                self._state = LifecycleState.FAILED
                self._error = e
            raise
    
    async def stop(self) -> None:
        """Stop the service."""
        with self._lock:
            if self._state in [LifecycleState.STOPPED, LifecycleState.STOPPING]:
                return
            
            if self._state == LifecycleState.CREATED:
                self._state = LifecycleState.STOPPED
                return
            
            self._state = LifecycleState.STOPPING
        
        try:
            logger.info(f"Stopping service: {self.name}")
            
            # Stop the service
            if hasattr(self.service, 'stop') and callable(self.service.stop):
                await asyncio.wait_for(
                    self.service.stop(),
                    timeout=self.shutdown_timeout
                )
            elif hasattr(self.service, 'graceful_shutdown') and callable(self.service.graceful_shutdown):
                await asyncio.wait_for(
                    self.service.graceful_shutdown(self.shutdown_timeout),
                    timeout=self.shutdown_timeout + 5.0
                )
            
            # Execute shutdown callbacks
            for callback in reversed(self._shutdown_callbacks):
                try:
                    callback()
                except Exception as e:
                    logger.warning(f"Shutdown callback failed for {self.name}: {e}")
            
            with self._lock:
                self._state = LifecycleState.STOPPED
                self._stopped_at = time.time()
            
            logger.info(f"Service stopped successfully: {self.name}")
            
        except Exception as e:
            logger.error(f"Failed to stop service {self.name}: {e}")
            with self._lock:
                self._state = LifecycleState.ERROR
                self._error = e
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status information."""
        with self._lock:
            status = {
                "name": self.name,
                "state": self._state,
                "dependencies": self.dependencies,
                "uptime": self.uptime,
            }
            
            if self._error:
                status["error"] = str(self._error)
            
            if self._started_at:
                status["started_at"] = self._started_at
            
            if self._stopped_at:
                status["stopped_at"] = self._stopped_at
            
            return status


class StartupManager:
    """
    Manages startup of multiple services with dependency resolution
    and parallel execution where possible.
    """
    
    def __init__(self):
        """Initialize startup manager."""
        self._services: Dict[str, ServiceLifecycle] = {}
        self._startup_order: List[str] = []
        self._lock = threading.RLock()
    
    def add_service(self, service_lifecycle: ServiceLifecycle) -> None:
        """
        Add service to startup manager.
        
        Args:
            service_lifecycle: Service lifecycle manager
        """
        with self._lock:
            self._services[service_lifecycle.name] = service_lifecycle
            self._startup_order = self._calculate_startup_order()
    
    def remove_service(self, service_name: str) -> None:
        """
        Remove service from startup manager.
        
        Args:
            service_name: Name of service to remove
        """
        with self._lock:
            if service_name in self._services:
                del self._services[service_name]
                self._startup_order = self._calculate_startup_order()
    
    def _calculate_startup_order(self) -> List[str]:
        """Calculate service startup order based on dependencies."""
        # Topological sort for dependency resolution
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(service_name: str):
            if service_name in temp_visited:
                raise RuntimeError(f"Circular dependency detected involving {service_name}")
            
            if service_name not in visited:
                temp_visited.add(service_name)
                
                service = self._services.get(service_name)
                if service:
                    for dependency in service.dependencies:
                        if dependency in self._services:
                            visit(dependency)
                
                temp_visited.remove(service_name)
                visited.add(service_name)
                order.append(service_name)
        
        # Visit all services
        for service_name in self._services:
            if service_name not in visited:
                visit(service_name)
        
        return order
    
    async def start_all(self, parallel: bool = True) -> None:
        """
        Start all services in dependency order.
        
        Args:
            parallel: Whether to start independent services in parallel
        """
        logger.info("Starting all services...")
        
        with self._lock:
            startup_order = self._startup_order.copy()
            services = self._services.copy()
        
        if not parallel:
            # Sequential startup
            for service_name in startup_order:
                service = services.get(service_name)
                if service:
                    await service.start()
        else:
            # Parallel startup with dependency respect
            started = set()
            remaining = set(startup_order)
            
            while remaining:
                # Find services that can be started (dependencies satisfied)
                ready_to_start = []
                for service_name in remaining:
                    service = services[service_name]
                    dependencies_satisfied = all(
                        dep in started or dep not in services
                        for dep in service.dependencies
                    )
                    if dependencies_satisfied:
                        ready_to_start.append(service_name)
                
                if not ready_to_start:
                    raise RuntimeError("Cannot resolve service dependencies")
                
                # Start ready services in parallel
                tasks = []
                for service_name in ready_to_start:
                    service = services[service_name]
                    tasks.append(service.start())
                
                await asyncio.gather(*tasks)
                
                # Update state
                for service_name in ready_to_start:
                    started.add(service_name)
                    remaining.remove(service_name)
        
        logger.info("All services started successfully")
    
    def get_startup_status(self) -> Dict[str, Any]:
        """Get startup status of all services."""
        with self._lock:
            return {
                "services": {
                    name: service.get_status()
                    for name, service in self._services.items()
                },
                "startup_order": self._startup_order
            }


class ShutdownManager:
    """
    Manages graceful shutdown of services with proper ordering
    and timeout handling.
    """
    
    def __init__(self, startup_manager: StartupManager):
        """
        Initialize shutdown manager.
        
        Args:
            startup_manager: Startup manager to get service information
        """
        self._startup_manager = startup_manager
        self._shutdown_timeout = 60.0
        
    async def shutdown_all(self, timeout: Optional[float] = None) -> None:
        """
        Shutdown all services in reverse dependency order.
        
        Args:
            timeout: Total shutdown timeout
        """
        shutdown_timeout = timeout or self._shutdown_timeout
        logger.info(f"Shutting down all services (timeout: {shutdown_timeout}s)")
        
        with self._startup_manager._lock:
            # Reverse startup order for shutdown
            shutdown_order = list(reversed(self._startup_manager._startup_order))
            services = self._startup_manager._services.copy()
        
        start_time = time.time()
        
        for service_name in shutdown_order:
            service = services.get(service_name)
            if service and service.is_running:
                try:
                    remaining_time = shutdown_timeout - (time.time() - start_time)
                    if remaining_time <= 0:
                        logger.warning(f"Shutdown timeout exceeded, forcing stop of {service_name}")
                        break
                    
                    # Use the minimum of remaining time and service shutdown timeout
                    service_timeout = min(remaining_time, service.shutdown_timeout)
                    await asyncio.wait_for(service.stop(), timeout=service_timeout)
                    
                except asyncio.TimeoutError:
                    logger.error(f"Service {service_name} shutdown timed out")
                except Exception as e:
                    logger.error(f"Error shutting down service {service_name}: {e}")
        
        logger.info("Service shutdown completed")


class GracefulShutdown:
    """
    Handles graceful shutdown signals and orchestrates cleanup.
    """
    
    def __init__(self, shutdown_manager: ShutdownManager):
        """
        Initialize graceful shutdown handler.
        
        Args:
            shutdown_manager: Shutdown manager for service cleanup
        """
        self._shutdown_manager = shutdown_manager
        self._shutdown_event = asyncio.Event()
        self._cleanup_callbacks: List[Callable[[], None]] = []
        
    def add_cleanup_callback(self, callback: Callable[[], None]) -> None:
        """Add cleanup callback to be called during shutdown."""
        self._cleanup_callbacks.append(callback)
    
    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown")
            asyncio.create_task(self.shutdown())
        
        # Handle common shutdown signals
        if sys.platform != "win32":
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)
    
    async def shutdown(self) -> None:
        """Perform graceful shutdown."""
        if self._shutdown_event.is_set():
            return  # Already shutting down
        
        self._shutdown_event.set()
        logger.info("Starting graceful shutdown...")
        
        try:
            # Execute cleanup callbacks
            for callback in self._cleanup_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Cleanup callback failed: {e}")
            
            # Shutdown all services
            await self._shutdown_manager.shutdown_all()
            
        except Exception as e:
            logger.error(f"Error during graceful shutdown: {e}")
        
        logger.info("Graceful shutdown completed")
    
    async def wait_for_shutdown(self) -> None:
        """Wait for shutdown signal."""
        await self._shutdown_event.wait()
    
    @asynccontextmanager
    async def lifecycle_context(self):
        """Context manager for service lifecycle."""
        try:
            yield
        finally:
            await self.shutdown()