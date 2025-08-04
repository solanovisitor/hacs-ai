"""
Monitoring and Observability for HACS Infrastructure

This module provides comprehensive monitoring capabilities including
health checks, metrics collection, and performance monitoring.
"""

import asyncio
import threading

# Optional psutil dependency
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field

from pydantic import BaseModel, Field

from .protocols import HealthCheckable
from .events import EventBus, Event, EventPriority


@dataclass
class MetricPoint:
    """Single metric data point."""
    
    timestamp: float
    value: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    
    service_name: str
    is_healthy: bool
    response_time: float
    error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class ServiceMetrics(BaseModel):
    """Metrics for a service."""
    
    service_name: str = Field(..., description="Service name")
    
    # Request metrics
    request_count: int = Field(0, description="Total requests")
    request_rate: float = Field(0.0, description="Requests per second")
    error_count: int = Field(0, description="Total errors")
    error_rate: float = Field(0.0, description="Error rate percentage")
    
    # Response time metrics
    avg_response_time: float = Field(0.0, description="Average response time in ms")
    p50_response_time: float = Field(0.0, description="50th percentile response time")
    p95_response_time: float = Field(0.0, description="95th percentile response time")
    p99_response_time: float = Field(0.0, description="99th percentile response time")
    
    # Resource metrics
    cpu_usage: float = Field(0.0, description="CPU usage percentage")
    memory_usage: float = Field(0.0, description="Memory usage in MB")
    memory_usage_percent: float = Field(0.0, description="Memory usage percentage")
    
    # Health metrics
    health_status: str = Field("unknown", description="Health status")
    uptime: float = Field(0.0, description="Uptime in seconds")
    last_health_check: Optional[datetime] = Field(None, description="Last health check time")


class MetricsCollector:
    """
    Collects and aggregates metrics for services and system resources.
    """
    
    def __init__(self, retention_period: int = 3600):
        """
        Initialize metrics collector.
        
        Args:
            retention_period: How long to keep metrics in seconds
        """
        self._retention_period = retention_period
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.RLock()
        
        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self) -> None:
        """Start metrics collection."""
        if self._running:
            return
        
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop(self) -> None:
        """Stop metrics collection."""
        if not self._running:
            return
        
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        key = self._build_metric_key(name, tags)
        with self._lock:
            self._counters[key] += value
            self._record_metric_point(name, self._counters[key], tags)
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric value."""
        key = self._build_metric_key(name, tags)
        with self._lock:
            self._gauges[key] = value
            self._record_metric_point(name, value, tags)
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a value in a histogram."""
        key = self._build_metric_key(name, tags)
        with self._lock:
            self._histograms[key].append(value)
            # Keep only recent values for performance
            if len(self._histograms[key]) > 1000:
                self._histograms[key] = self._histograms[key][-1000:]
            self._record_metric_point(name, value, tags)
    
    def record_timing(self, name: str, duration_ms: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record timing information."""
        self.record_histogram(f"{name}.duration", duration_ms, tags)
        self.increment_counter(f"{name}.count", 1, tags)
    
    def get_counter(self, name: str, tags: Optional[Dict[str, str]] = None) -> int:
        """Get counter value."""
        key = self._build_metric_key(name, tags)
        with self._lock:
            return self._counters.get(key, 0)
    
    def get_gauge(self, name: str, tags: Optional[Dict[str, str]] = None) -> float:
        """Get gauge value."""
        key = self._build_metric_key(name, tags)
        with self._lock:
            return self._gauges.get(key, 0.0)
    
    def get_histogram_stats(self, name: str, tags: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """Get histogram statistics."""
        key = self._build_metric_key(name, tags)
        with self._lock:
            values = self._histograms.get(key, [])
            if not values:
                return {"count": 0, "min": 0, "max": 0, "avg": 0, "p50": 0, "p95": 0, "p99": 0}
            
            values_sorted = sorted(values)
            count = len(values_sorted)
            
            return {
                "count": count,
                "min": values_sorted[0],
                "max": values_sorted[-1],
                "avg": sum(values_sorted) / count,
                "p50": self._percentile(values_sorted, 50),
                "p95": self._percentile(values_sorted, 95),
                "p99": self._percentile(values_sorted, 99),
            }
    
    def get_metric_history(
        self,
        name: str,
        tags: Optional[Dict[str, str]] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> List[MetricPoint]:
        """Get metric history within time range."""
        with self._lock:
            points = list(self._metrics[name])
        
        # Filter by tags if specified
        if tags:
            points = [p for p in points if all(p.tags.get(k) == v for k, v in tags.items())]
        
        # Filter by time range
        if start_time:
            points = [p for p in points if p.timestamp >= start_time]
        if end_time:
            points = [p for p in points if p.timestamp <= end_time]
        
        return points
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metric values."""
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {k: self.get_histogram_stats(k.split("|")[0], self._parse_tags(k)) 
                              for k in self._histograms.keys()}
            }
    
    def _build_metric_key(self, name: str, tags: Optional[Dict[str, str]]) -> str:
        """Build metric key with tags."""
        if not tags:
            return name
        
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}|{tag_str}"
    
    def _parse_tags(self, key: str) -> Optional[Dict[str, str]]:
        """Parse tags from metric key."""
        if "|" not in key:
            return None
        
        _, tag_str = key.split("|", 1)
        tags = {}
        for tag_pair in tag_str.split(","):
            if "=" in tag_pair:
                k, v = tag_pair.split("=", 1)
                tags[k] = v
        return tags
    
    def _record_metric_point(self, name: str, value: float, tags: Optional[Dict[str, str]]) -> None:
        """Record a metric point."""
        point = MetricPoint(
            timestamp=time.time(),
            value=value,
            tags=tags or {}
        )
        self._metrics[name].append(point)
    
    def _percentile(self, sorted_values: List[float], percentile: float) -> float:
        """Calculate percentile from sorted values."""
        if not sorted_values:
            return 0.0
        
        index = (percentile / 100.0) * (len(sorted_values) - 1)
        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower_index = int(index)
            upper_index = lower_index + 1
            weight = index - lower_index
            return sorted_values[lower_index] * (1 - weight) + sorted_values[upper_index] * weight
    
    async def _cleanup_loop(self) -> None:
        """Background cleanup of old metrics."""
        while self._running:
            try:
                await asyncio.sleep(300)  # Clean up every 5 minutes
                await self._cleanup_old_metrics()
            except asyncio.CancelledError:
                break
            except Exception:
                # Continue cleanup even if error occurs
                pass
    
    async def _cleanup_old_metrics(self) -> None:
        """Remove old metric points."""
        cutoff_time = time.time() - self._retention_period
        
        with self._lock:
            for name, points in self._metrics.items():
                # Remove old points
                while points and points[0].timestamp < cutoff_time:
                    points.popleft()


class HealthMonitor:
    """
    Monitors health of services and system resources.
    """
    
    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        check_interval: int = 30,
        failure_threshold: int = 3
    ):
        """
        Initialize health monitor.
        
        Args:
            event_bus: Event bus for publishing health events
            check_interval: Health check interval in seconds
            failure_threshold: Number of failures before marking unhealthy
        """
        self._event_bus = event_bus
        self._check_interval = check_interval
        self._failure_threshold = failure_threshold
        
        self._services: Dict[str, HealthCheckable] = {}
        self._custom_checks: Dict[str, Callable[[], bool]] = {}
        self._health_results: Dict[str, HealthCheckResult] = {}
        self._failure_counts: Dict[str, int] = defaultdict(int)
        
        self._monitor_task: Optional[asyncio.Task] = None
        self._running = False
        self._lock = threading.RLock()
    
    def register_service(self, name: str, service: HealthCheckable) -> None:
        """Register service for health monitoring."""
        with self._lock:
            self._services[name] = service
    
    def register_custom_check(self, name: str, check_func: Callable[[], bool]) -> None:
        """Register custom health check function."""
        with self._lock:
            self._custom_checks[name] = check_func
    
    def unregister_service(self, name: str) -> None:
        """Unregister service from health monitoring."""
        with self._lock:
            self._services.pop(name, None)
            self._custom_checks.pop(name, None)
            self._health_results.pop(name, None)
            self._failure_counts.pop(name, None)
    
    async def start(self) -> None:
        """Start health monitoring."""
        if self._running:
            return
        
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
    
    async def stop(self) -> None:
        """Stop health monitoring."""
        if not self._running:
            return
        
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
    
    async def check_service_health(self, service_name: str) -> HealthCheckResult:
        """Check health of a specific service."""
        start_time = time.time()
        
        try:
            with self._lock:
                service = self._services.get(service_name)
                custom_check = self._custom_checks.get(service_name)
            
            is_healthy = False
            details = {}
            error = None
            
            if service:
                try:
                    is_healthy = service.health_check()
                    if hasattr(service, 'get_health_details'):
                        details = service.get_health_details()
                except Exception as e:
                    error = str(e)
                    is_healthy = False
            elif custom_check:
                try:
                    is_healthy = custom_check()
                except Exception as e:
                    error = str(e)
                    is_healthy = False
            else:
                error = "No health check method available"
                is_healthy = False
            
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            result = HealthCheckResult(
                service_name=service_name,
                is_healthy=is_healthy,
                response_time=response_time,
                error=error,
                details=details
            )
            
            # Update failure count
            with self._lock:
                if is_healthy:
                    self._failure_counts[service_name] = 0
                else:
                    self._failure_counts[service_name] += 1
                
                self._health_results[service_name] = result
            
            # Publish health event
            if self._event_bus:
                from .events import create_health_event
                event = create_health_event(service_name, is_healthy, details)
                self._event_bus.publish(event)
            
            return result
            
        except Exception as e:
            result = HealthCheckResult(
                service_name=service_name,
                is_healthy=False,
                response_time=(time.time() - start_time) * 1000,
                error=str(e)
            )
            
            with self._lock:
                self._failure_counts[service_name] += 1
                self._health_results[service_name] = result
            
            return result
    
    def get_service_health(self, service_name: str) -> Optional[HealthCheckResult]:
        """Get last health check result for service."""
        with self._lock:
            return self._health_results.get(service_name)
    
    def get_all_health_results(self) -> Dict[str, HealthCheckResult]:
        """Get all health check results."""
        with self._lock:
            return self._health_results.copy()
    
    def is_service_healthy(self, service_name: str) -> bool:
        """Check if service is currently healthy."""
        with self._lock:
            failure_count = self._failure_counts.get(service_name, 0)
            return failure_count < self._failure_threshold
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary."""
        with self._lock:
            total_services = len(self._services) + len(self._custom_checks)
            healthy_services = sum(
                1 for name in set(list(self._services.keys()) + list(self._custom_checks.keys()))
                if self.is_service_healthy(name)
            )
            
            return {
                "total_services": total_services,
                "healthy_services": healthy_services,
                "unhealthy_services": total_services - healthy_services,
                "overall_healthy": healthy_services == total_services,
                "check_interval": self._check_interval,
                "failure_threshold": self._failure_threshold
            }
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                await self._check_all_services()
                await asyncio.sleep(self._check_interval)
            except asyncio.CancelledError:
                break
            except Exception:
                # Continue monitoring even if error occurs
                await asyncio.sleep(self._check_interval)
    
    async def _check_all_services(self) -> None:
        """Check health of all registered services."""
        services_to_check = []
        
        with self._lock:
            services_to_check = list(set(list(self._services.keys()) + list(self._custom_checks.keys())))
        
        # Check services concurrently
        tasks = [
            self.check_service_health(service_name)
            for service_name in services_to_check
        ]
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


class PerformanceMonitor:
    """
    Monitors system performance metrics.
    """
    
    def __init__(self, metrics_collector: MetricsCollector):
        """
        Initialize performance monitor.
        
        Args:
            metrics_collector: Metrics collector for recording metrics
        """
        self._metrics = metrics_collector
        self._monitor_task: Optional[asyncio.Task] = None
        self._running = False
        self._collection_interval = 10  # seconds
    
    async def start(self) -> None:
        """Start performance monitoring."""
        if self._running:
            return
        
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
    
    async def stop(self) -> None:
        """Stop performance monitoring."""
        if not self._running:
            return
        
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
    
    async def _monitoring_loop(self) -> None:
        """Main performance monitoring loop."""
        while self._running:
            try:
                self._collect_system_metrics()
                await asyncio.sleep(self._collection_interval)
            except asyncio.CancelledError:
                break
            except Exception:
                # Continue monitoring even if error occurs
                await asyncio.sleep(self._collection_interval)
    
    def _collect_system_metrics(self) -> None:
        """Collect system performance metrics."""
        if not HAS_PSUTIL:
            # Mock metrics if psutil not available
            self._metrics.set_gauge("system.cpu.usage_percent", 25.0)
            self._metrics.set_gauge("system.memory.usage_percent", 50.0)
            return
        
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self._metrics.set_gauge("system.cpu.usage_percent", cpu_percent)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self._metrics.set_gauge("system.memory.total_bytes", memory.total)
            self._metrics.set_gauge("system.memory.available_bytes", memory.available)
            self._metrics.set_gauge("system.memory.used_bytes", memory.used)
            self._metrics.set_gauge("system.memory.usage_percent", memory.percent)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            self._metrics.set_gauge("system.disk.total_bytes", disk.total)
            self._metrics.set_gauge("system.disk.free_bytes", disk.free)
            self._metrics.set_gauge("system.disk.used_bytes", disk.used)
            self._metrics.set_gauge("system.disk.usage_percent", (disk.used / disk.total) * 100)
            
            # Network metrics
            network = psutil.net_io_counters()
            self._metrics.set_gauge("system.network.bytes_sent", network.bytes_sent)
            self._metrics.set_gauge("system.network.bytes_recv", network.bytes_recv)
            self._metrics.set_gauge("system.network.packets_sent", network.packets_sent)
            self._metrics.set_gauge("system.network.packets_recv", network.packets_recv)
            
        except Exception:
            # Ignore errors in system metric collection
            pass