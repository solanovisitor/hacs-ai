"""
Service Registry and Discovery for HACS Infrastructure

This module provides comprehensive service registry and discovery capabilities
with health monitoring, load balancing, and automatic failover.
"""

import asyncio
import threading
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from .protocols import HealthCheckable, ServiceProvider


class ServiceStatus(str, Enum):
    """Service status enumeration."""
    
    UNKNOWN = "unknown"
    STARTING = "starting"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    STOPPING = "stopping"
    STOPPED = "stopped"


class ServiceInfo(BaseModel):
    """Information about a registered service."""
    
    id: str = Field(..., description="Unique service identifier")
    name: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    host: str = Field(..., description="Service host")
    port: int = Field(..., description="Service port")
    protocol: str = Field("http", description="Service protocol")
    
    # Service metadata
    tags: Set[str] = Field(default_factory=set, description="Service tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Health and status
    status: ServiceStatus = Field(ServiceStatus.UNKNOWN, description="Current service status")
    last_health_check: Optional[datetime] = Field(None, description="Last health check timestamp")
    health_check_url: Optional[str] = Field(None, description="Health check endpoint")
    
    # Registration details
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Registration timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp")
    
    # Load balancing
    weight: int = Field(100, description="Load balancing weight")
    connections: int = Field(0, description="Current active connections")
    
    @property
    def url(self) -> str:
        """Get service URL."""
        return f"{self.protocol}://{self.host}:{self.port}"
    
    @property
    def is_healthy(self) -> bool:
        """Check if service is healthy."""
        return self.status == ServiceStatus.HEALTHY
    
    def update_status(self, status: ServiceStatus) -> None:
        """Update service status."""
        self.status = status
        self.updated_at = datetime.now(timezone.utc)


class HealthCheck(BaseModel):
    """Health check configuration."""
    
    enabled: bool = Field(True, description="Enable health checking")
    interval: int = Field(30, description="Health check interval in seconds")
    timeout: float = Field(5.0, description="Health check timeout")
    failure_threshold: int = Field(3, description="Consecutive failures before marking unhealthy")
    success_threshold: int = Field(1, description="Consecutive successes before marking healthy")
    
    # Custom health check function
    custom_check: Optional[Callable[[ServiceInfo], bool]] = Field(None, description="Custom health check function")
    
    class Config:
        arbitrary_types_allowed = True


class ServiceRegistry:
    """
    Service registry with health monitoring and discovery capabilities.
    
    Provides comprehensive service management including:
    - Service registration and deregistration
    - Health monitoring with configurable checks
    - Service discovery with filtering
    - Load balancing support
    - Automatic cleanup of stale services
    """
    
    def __init__(self, health_check_config: Optional[HealthCheck] = None):
        """
        Initialize service registry.
        
        Args:
            health_check_config: Health check configuration
        """
        self._services: Dict[str, ServiceInfo] = {}
        self._services_by_name: Dict[str, List[str]] = {}
        self._health_config = health_check_config or HealthCheck()
        self._health_failures: Dict[str, int] = {}
        self._health_successes: Dict[str, int] = {}
        self._lock = threading.RLock()
        self._health_check_task: Optional[asyncio.Task] = None
        self._running = False
        
    def register_service(
        self,
        name: str,
        host: str,
        port: int,
        version: str = "1.0.0",
        protocol: str = "http",
        tags: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        health_check_url: Optional[str] = None,
        weight: int = 100
    ) -> str:
        """
        Register a service.
        
        Args:
            name: Service name
            host: Service host
            port: Service port
            version: Service version
            protocol: Service protocol
            tags: Service tags
            metadata: Additional metadata
            health_check_url: Health check endpoint
            weight: Load balancing weight
            
        Returns:
            Service ID
        """
        service_id = f"{name}-{host}:{port}"
        
        with self._lock:
            service_info = ServiceInfo(
                id=service_id,
                name=name,
                version=version,
                host=host,
                port=port,
                protocol=protocol,
                tags=tags or set(),
                metadata=metadata or {},
                health_check_url=health_check_url,
                weight=weight
            )
            
            self._services[service_id] = service_info
            
            # Update name index
            if name not in self._services_by_name:
                self._services_by_name[name] = []
            if service_id not in self._services_by_name[name]:
                self._services_by_name[name].append(service_id)
            
            # Initialize health tracking
            self._health_failures[service_id] = 0
            self._health_successes[service_id] = 0
        
        return service_id
    
    def deregister_service(self, service_id: str) -> bool:
        """
        Deregister a service.
        
        Args:
            service_id: Service identifier
            
        Returns:
            True if service was deregistered
        """
        with self._lock:
            if service_id not in self._services:
                return False
            
            service = self._services[service_id]
            
            # Remove from services
            del self._services[service_id]
            
            # Remove from name index
            if service.name in self._services_by_name:
                self._services_by_name[service.name] = [
                    sid for sid in self._services_by_name[service.name] 
                    if sid != service_id
                ]
                if not self._services_by_name[service.name]:
                    del self._services_by_name[service.name]
            
            # Clean up health tracking
            self._health_failures.pop(service_id, None)
            self._health_successes.pop(service_id, None)
        
        return True
    
    def get_service(self, service_id: str) -> Optional[ServiceInfo]:
        """
        Get service by ID.
        
        Args:
            service_id: Service identifier
            
        Returns:
            Service info if found
        """
        with self._lock:
            return self._services.get(service_id)
    
    def get_services_by_name(
        self,
        name: str,
        healthy_only: bool = True,
        tags: Optional[Set[str]] = None
    ) -> List[ServiceInfo]:
        """
        Get services by name with optional filtering.
        
        Args:
            name: Service name
            healthy_only: Return only healthy services
            tags: Required tags filter
            
        Returns:
            List of matching services
        """
        with self._lock:
            if name not in self._services_by_name:
                return []
            
            services = []
            for service_id in self._services_by_name[name]:
                service = self._services.get(service_id)
                if not service:
                    continue
                
                # Filter by health status
                if healthy_only and not service.is_healthy:
                    continue
                
                # Filter by tags
                if tags and not tags.issubset(service.tags):
                    continue
                
                services.append(service)
            
            return services
    
    def get_all_services(self) -> List[ServiceInfo]:
        """Get all registered services."""
        with self._lock:
            return list(self._services.values())
    
    def get_service_names(self) -> List[str]:
        """Get all registered service names."""
        with self._lock:
            return list(self._services_by_name.keys())
    
    def update_service_status(self, service_id: str, status: ServiceStatus) -> bool:
        """
        Update service status.
        
        Args:
            service_id: Service identifier
            status: New status
            
        Returns:
            True if status was updated
        """
        with self._lock:
            service = self._services.get(service_id)
            if not service:
                return False
            
            service.update_status(status)
            return True
    
    def update_service_connections(self, service_id: str, connections: int) -> bool:
        """
        Update service connection count.
        
        Args:
            service_id: Service identifier
            connections: Number of active connections
            
        Returns:
            True if count was updated
        """
        with self._lock:
            service = self._services.get(service_id)
            if not service:
                return False
            
            service.connections = connections
            service.updated_at = datetime.now(timezone.utc)
            return True
    
    async def start_health_monitoring(self) -> None:
        """Start health monitoring background task."""
        if not self._health_config.enabled or self._running:
            return
        
        self._running = True
        self._health_check_task = asyncio.create_task(self._health_check_loop())
    
    async def stop_health_monitoring(self) -> None:
        """Stop health monitoring background task."""
        self._running = False
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            self._health_check_task = None
    
    async def _health_check_loop(self) -> None:
        """Health check background loop."""
        while self._running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self._health_config.interval)
            except asyncio.CancelledError:
                break
            except Exception:
                # Log error but continue monitoring
                await asyncio.sleep(self._health_config.interval)
    
    async def _perform_health_checks(self) -> None:
        """Perform health checks on all registered services."""
        services_to_check = []
        
        with self._lock:
            services_to_check = list(self._services.values())
        
        # Check services concurrently
        tasks = [
            self._check_service_health(service)
            for service in services_to_check
        ]
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _check_service_health(self, service: ServiceInfo) -> None:
        """Check health of a single service."""
        try:
            is_healthy = False
            
            # Use custom health check if provided
            if self._health_config.custom_check:
                is_healthy = self._health_config.custom_check(service)
            elif service.health_check_url:
                is_healthy = await self._http_health_check(service)
            elif hasattr(service, 'health_check'):
                is_healthy = service.health_check()
            else:
                # Default: assume healthy if service is reachable
                is_healthy = await self._connectivity_check(service)
            
            await self._update_health_status(service.id, is_healthy)
            
        except Exception:
            # Health check failed
            await self._update_health_status(service.id, False)
    
    async def _http_health_check(self, service: ServiceInfo) -> bool:
        """Perform HTTP health check."""
        import aiohttp
        
        try:
            timeout = aiohttp.ClientTimeout(total=self._health_config.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = service.health_check_url or f"{service.url}/health"
                async with session.get(url) as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def _connectivity_check(self, service: ServiceInfo) -> bool:
        """Perform basic connectivity check."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(service.host, service.port),
                timeout=self._health_config.timeout
            )
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False
    
    async def _update_health_status(self, service_id: str, is_healthy: bool) -> None:
        """Update service health status based on check result."""
        with self._lock:
            service = self._services.get(service_id)
            if not service:
                return
            
            service.last_health_check = datetime.now(timezone.utc)
            
            if is_healthy:
                self._health_successes[service_id] = self._health_successes.get(service_id, 0) + 1
                self._health_failures[service_id] = 0
                
                # Mark healthy if enough consecutive successes
                if self._health_successes[service_id] >= self._health_config.success_threshold:
                    if service.status != ServiceStatus.HEALTHY:
                        service.update_status(ServiceStatus.HEALTHY)
            else:
                self._health_failures[service_id] = self._health_failures.get(service_id, 0) + 1
                self._health_successes[service_id] = 0
                
                # Mark unhealthy if enough consecutive failures
                if self._health_failures[service_id] >= self._health_config.failure_threshold:
                    if service.status != ServiceStatus.UNHEALTHY:
                        service.update_status(ServiceStatus.UNHEALTHY)
    
    def get_health_summary(self) -> Dict[str, Any]:
        """
        Get health summary of all services.
        
        Returns:
            Dictionary with health statistics
        """
        with self._lock:
            total = len(self._services)
            healthy = sum(1 for s in self._services.values() if s.status == ServiceStatus.HEALTHY)
            unhealthy = sum(1 for s in self._services.values() if s.status == ServiceStatus.UNHEALTHY)
            unknown = total - healthy - unhealthy
            
            return {
                "total_services": total,
                "healthy_services": healthy,
                "unhealthy_services": unhealthy,
                "unknown_services": unknown,
                "health_check_enabled": self._health_config.enabled,
                "monitoring_active": self._running
            }


class ServiceDiscovery:
    """
    Service discovery client with load balancing and failover.
    """
    
    def __init__(self, registry: ServiceRegistry):
        """
        Initialize service discovery.
        
        Args:
            registry: Service registry instance
        """
        self._registry = registry
        self._round_robin_counters: Dict[str, int] = {}
        self._lock = threading.Lock()
    
    def discover_service(
        self,
        name: str,
        tags: Optional[Set[str]] = None,
        load_balance: str = "round_robin"
    ) -> Optional[ServiceInfo]:
        """
        Discover a service instance.
        
        Args:
            name: Service name
            tags: Required tags
            load_balance: Load balancing strategy ("round_robin", "weighted", "least_connections")
            
        Returns:
            Selected service instance
        """
        services = self._registry.get_services_by_name(name, healthy_only=True, tags=tags)
        if not services:
            return None
        
        if len(services) == 1:
            return services[0]
        
        # Apply load balancing strategy
        if load_balance == "round_robin":
            return self._round_robin_select(name, services)
        elif load_balance == "weighted":
            return self._weighted_select(services)
        elif load_balance == "least_connections":
            return self._least_connections_select(services)
        else:
            # Default to first service
            return services[0]
    
    def _round_robin_select(self, service_name: str, services: List[ServiceInfo]) -> ServiceInfo:
        """Round-robin load balancing."""
        with self._lock:
            counter = self._round_robin_counters.get(service_name, 0)
            selected = services[counter % len(services)]
            self._round_robin_counters[service_name] = counter + 1
            return selected
    
    def _weighted_select(self, services: List[ServiceInfo]) -> ServiceInfo:
        """Weighted load balancing."""
        import random
        
        total_weight = sum(service.weight for service in services)
        if total_weight == 0:
            return random.choice(services)
        
        rand_weight = random.randint(1, total_weight)
        current_weight = 0
        
        for service in services:
            current_weight += service.weight
            if rand_weight <= current_weight:
                return service
        
        return services[-1]  # Fallback
    
    def _least_connections_select(self, services: List[ServiceInfo]) -> ServiceInfo:
        """Least connections load balancing."""
        return min(services, key=lambda s: s.connections)
    
    def get_service_url(
        self,
        name: str,
        tags: Optional[Set[str]] = None,
        load_balance: str = "round_robin"
    ) -> Optional[str]:
        """
        Get service URL with load balancing.
        
        Args:
            name: Service name
            tags: Required tags
            load_balance: Load balancing strategy
            
        Returns:
            Service URL if available
        """
        service = self.discover_service(name, tags, load_balance)
        return service.url if service else None
    
    def get_all_service_urls(
        self,
        name: str,
        tags: Optional[Set[str]] = None,
        healthy_only: bool = True
    ) -> List[str]:
        """
        Get all URLs for a service.
        
        Args:
            name: Service name
            tags: Required tags
            healthy_only: Return only healthy services
            
        Returns:
            List of service URLs
        """
        services = self._registry.get_services_by_name(name, healthy_only, tags)
        return [service.url for service in services]