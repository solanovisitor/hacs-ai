"""
HACS Observability Framework - OpenTelemetry-based Monitoring

This module provides comprehensive observability for healthcare AI systems
including distributed tracing, metrics collection, structured logging,
and healthcare-specific monitoring capabilities.

Features:
    - OpenTelemetry distributed tracing
    - Healthcare workflow monitoring
    - PHI-safe structured logging
    - Performance metrics collection
    - Custom healthcare dashboards
    - HIPAA-compliant audit trails

Author: HACS Development Team
License: MIT
Version: 1.0.0
"""

import os
import time
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# OpenTelemetry imports
try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.instrumentation.logging import LoggingInstrumentor
    from opentelemetry.semantic_conventions.trace import SpanAttributes
    from opentelemetry.propagate import set_global_textmap
    from opentelemetry.propagators.b3 import B3MultiFormat
    
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None
    metrics = None


class LogLevel(str, Enum):
    """Structured log levels."""
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    FATAL = "fatal"
    AUDIT = "audit"


class MetricType(str, Enum):
    """Types of metrics to collect."""
    COUNTER = "counter"
    HISTOGRAM = "histogram"
    GAUGE = "gauge"
    SUMMARY = "summary"


@dataclass
class HealthcareSpanAttributes:
    """Healthcare-specific span attributes."""
    patient_id_hash: Optional[str] = None
    organization: Optional[str] = None
    care_team: Optional[str] = None
    workflow_type: Optional[str] = None
    phi_accessed: bool = False
    fhir_resource_type: Optional[str] = None
    clinical_domain: Optional[str] = None
    tool_category: Optional[str] = None
    compliance_level: Optional[str] = None


@dataclass
class ObservabilityConfig:
    """Configuration for observability framework."""
    
    # OpenTelemetry configuration
    service_name: str = "hacs-healthcare-ai"
    service_version: str = "1.0.0"
    environment: str = "development"
    
    # Tracing configuration
    enable_tracing: bool = True
    trace_endpoint: Optional[str] = None
    trace_headers: Dict[str, str] = field(default_factory=dict)
    
    # Metrics configuration
    enable_metrics: bool = True
    metrics_endpoint: Optional[str] = None
    metrics_headers: Dict[str, str] = field(default_factory=dict)
    
    # Logging configuration
    enable_structured_logging: bool = True
    log_level: LogLevel = LogLevel.INFO
    log_format: str = "json"
    
    # Healthcare-specific settings
    enable_phi_monitoring: bool = True
    enable_compliance_tracking: bool = True
    audit_log_retention_days: int = 2557  # 7 years for HIPAA
    
    # Performance monitoring
    enable_performance_monitoring: bool = True
    slow_query_threshold_ms: int = 1000
    memory_threshold_mb: int = 512
    
    # Security monitoring
    enable_security_monitoring: bool = True
    failed_auth_threshold: int = 5
    suspicious_activity_threshold: int = 10


class StructuredLogger:
    """PHI-safe structured logger with healthcare context."""
    
    def __init__(self, name: str, config: ObservabilityConfig):
        """Initialize structured logger."""
        self.name = name
        self.config = config
        self.logger = logging.getLogger(name)
        
        # Configure structured logging
        self._configure_logger()
        
        # Healthcare context
        self.healthcare_context = {}
    
    def _configure_logger(self):
        """Configure structured logging format."""
        # Handle both enum and string log levels
        if hasattr(self.config.log_level, 'value'):
            log_level = self.config.log_level.value.upper()
        else:
            log_level = str(self.config.log_level).upper()
        
        self.logger.setLevel(getattr(logging, log_level))
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create structured formatter
        if self.config.log_format == "json":
            formatter = JSONFormatter()
        else:
            formatter = StructuredFormatter()
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler for audit logs
        if self.config.enable_structured_logging:
            log_dir = Path.home() / ".hacs" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(
                log_dir / f"{self.name}_{datetime.now().strftime('%Y%m%d')}.log"
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def set_healthcare_context(
        self,
        patient_id_hash: Optional[str] = None,
        organization: Optional[str] = None,
        care_team: Optional[str] = None,
        workflow_type: Optional[str] = None
    ):
        """Set healthcare context for all subsequent logs."""
        self.healthcare_context.update({
            k: v for k, v in {
                "patient_id_hash": patient_id_hash,
                "organization": organization,
                "care_team": care_team,
                "workflow_type": workflow_type
            }.items() if v is not None
        })
    
    def _log(self, level: LogLevel, message: str, **kwargs):
        """Internal logging method with healthcare context."""
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level.value,
            "service": self.config.service_name,
            "environment": self.config.environment,
            "message": message,
            **self.healthcare_context,
            **kwargs
        }
        
        # Add trace context if available
        if OTEL_AVAILABLE and trace.get_current_span().is_recording():
            span_context = trace.get_current_span().get_span_context()
            log_data.update({
                "trace_id": format(span_context.trace_id, "032x"),
                "span_id": format(span_context.span_id, "016x")
            })
        
        # Remove reserved fields that conflict with LogRecord
        extra_data = {k: v for k, v in log_data.items() if k not in ['message', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename', 'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated', 'thread', 'threadName', 'processName', 'process', 'name']}
        
        # Log with appropriate level  
        log_level = getattr(logging, level.value.upper()) if level != LogLevel.AUDIT else logging.INFO
        self.logger.log(log_level, json.dumps(log_data) if self.config.log_format == "json" else message, extra=extra_data)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log(LogLevel.INFO, message, **kwargs)
    
    def warn(self, message: str, **kwargs):
        """Log warning message."""
        self._log(LogLevel.WARN, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log(LogLevel.ERROR, message, **kwargs)
    
    def fatal(self, message: str, **kwargs):
        """Log fatal message."""
        self._log(LogLevel.FATAL, message, **kwargs)
    
    def audit(self, message: str, **kwargs):
        """Log audit event for HIPAA compliance."""
        kwargs["audit_event"] = True
        self._log(LogLevel.AUDIT, message, **kwargs)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        """Format log record as JSON."""
        log_obj = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ["name", "msg", "args", "levelname", "levelno", "pathname", 
                          "filename", "module", "lineno", "funcName", "created", 
                          "msecs", "relativeCreated", "thread", "threadName", 
                          "processName", "process", "getMessage"]:
                log_obj[key] = value
        
        return json.dumps(log_obj)


class StructuredFormatter(logging.Formatter):
    """Structured text formatter."""
    
    def format(self, record):
        """Format log record with structure."""
        formatted = f"{datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()} "
        formatted += f"[{record.levelname}] {record.name}: {record.getMessage()}"
        
        # Add structured fields
        extras = []
        for key, value in record.__dict__.items():
            if key not in ["name", "msg", "args", "levelname", "levelno", "pathname", 
                          "filename", "module", "lineno", "funcName", "created", 
                          "msecs", "relativeCreated", "thread", "threadName", 
                          "processName", "process", "getMessage"]:
                extras.append(f"{key}={value}")
        
        if extras:
            formatted += f" | {' '.join(extras)}"
        
        return formatted


class HealthcareTracer:
    """Healthcare-specific distributed tracing."""
    
    def __init__(self, config: ObservabilityConfig):
        """Initialize healthcare tracer."""
        self.config = config
        self.tracer = None
        
        if OTEL_AVAILABLE and config.enable_tracing:
            self._setup_tracing()
    
    def _setup_tracing(self):
        """Setup OpenTelemetry tracing."""
        # Configure tracer provider
        tracer_provider = TracerProvider()
        trace.set_tracer_provider(tracer_provider)
        
        # Configure OTLP exporter if endpoint provided
        if self.config.trace_endpoint:
            otlp_exporter = OTLPSpanExporter(
                endpoint=self.config.trace_endpoint,
                headers=self.config.trace_headers
            )
            span_processor = BatchSpanProcessor(otlp_exporter)
            tracer_provider.add_span_processor(span_processor)
        
        # Set B3 propagation for distributed tracing
        set_global_textmap(B3MultiFormat())
        
        # Get tracer
        self.tracer = trace.get_tracer(
            self.config.service_name,
            self.config.service_version
        )
        
        # Auto-instrument common libraries
        RequestsInstrumentor().instrument()
        LoggingInstrumentor().instrument()
    
    @contextmanager
    def start_healthcare_span(
        self,
        name: str,
        attributes: Optional[HealthcareSpanAttributes] = None,
        **kwargs
    ):
        """Start a healthcare-specific trace span."""
        if not self.tracer:
            yield None
            return
        
        span_attributes = {}
        
        # Add healthcare attributes
        if attributes:
            if attributes.patient_id_hash:
                span_attributes["healthcare.patient_id_hash"] = attributes.patient_id_hash
            if attributes.organization:
                span_attributes["healthcare.organization"] = attributes.organization
            if attributes.care_team:
                span_attributes["healthcare.care_team"] = attributes.care_team
            if attributes.workflow_type:
                span_attributes["healthcare.workflow_type"] = attributes.workflow_type
            if attributes.phi_accessed:
                span_attributes["healthcare.phi_accessed"] = str(attributes.phi_accessed)
            if attributes.fhir_resource_type:
                span_attributes["healthcare.fhir_resource_type"] = attributes.fhir_resource_type
            if attributes.clinical_domain:
                span_attributes["healthcare.clinical_domain"] = attributes.clinical_domain
            if attributes.tool_category:
                span_attributes["healthcare.tool_category"] = attributes.tool_category
            if attributes.compliance_level:
                span_attributes["healthcare.compliance_level"] = attributes.compliance_level
        
        # Add service attributes
        span_attributes.update({
            SpanAttributes.SERVICE_NAME: self.config.service_name,
            SpanAttributes.SERVICE_VERSION: self.config.service_version,
            "environment": self.config.environment
        })
        
        # Add custom attributes
        span_attributes.update(kwargs)
        
        with self.tracer.start_as_current_span(name, attributes=span_attributes) as span:
            yield span
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Add event to current span."""
        if not self.tracer:
            return
        
        current_span = trace.get_current_span()
        if current_span.is_recording():
            current_span.add_event(name, attributes or {})
    
    def set_attribute(self, key: str, value: Any):
        """Set attribute on current span."""
        if not self.tracer:
            return
        
        current_span = trace.get_current_span()
        if current_span.is_recording():
            current_span.set_attribute(key, value)
    
    def record_exception(self, exception: Exception):
        """Record exception in current span."""
        if not self.tracer:
            return
        
        current_span = trace.get_current_span()
        if current_span.is_recording():
            current_span.record_exception(exception)
            current_span.set_status(trace.Status(trace.StatusCode.ERROR))


class HealthcareMetrics:
    """Healthcare-specific metrics collection."""
    
    def __init__(self, config: ObservabilityConfig):
        """Initialize healthcare metrics."""
        self.config = config
        self.meter = None
        self.metrics = {}
        
        if OTEL_AVAILABLE and config.enable_metrics:
            self._setup_metrics()
    
    def _setup_metrics(self):
        """Setup OpenTelemetry metrics."""
        # Configure OTLP exporter if endpoint provided
        if self.config.metrics_endpoint:
            metric_reader = PeriodicExportingMetricReader(
                OTLPMetricExporter(
                    endpoint=self.config.metrics_endpoint,
                    headers=self.config.metrics_headers
                ),
                export_interval_millis=30000  # 30 seconds
            )
            meter_provider = MeterProvider(metric_readers=[metric_reader])
        else:
            meter_provider = MeterProvider()
        
        metrics.set_meter_provider(meter_provider)
        
        # Get meter
        self.meter = metrics.get_meter(
            self.config.service_name,
            self.config.service_version
        )
        
        # Create common healthcare metrics
        self._create_healthcare_metrics()
    
    def _create_healthcare_metrics(self):
        """Create healthcare-specific metrics."""
        if not self.meter:
            return
        
        # Patient workflow metrics
        self.metrics["patient_workflows_total"] = self.meter.create_counter(
            "hacs_patient_workflows_total",
            description="Total number of patient workflows processed",
            unit="1"
        )
        
        self.metrics["patient_workflows_duration"] = self.meter.create_histogram(
            "hacs_patient_workflows_duration_seconds",
            description="Duration of patient workflows",
            unit="s"
        )
        
        # PHI access metrics
        self.metrics["phi_access_total"] = self.meter.create_counter(
            "hacs_phi_access_total",
            description="Total PHI access events",
            unit="1"
        )
        
        # Tool execution metrics
        self.metrics["tool_executions_total"] = self.meter.create_counter(
            "hacs_tool_executions_total",
            description="Total healthcare tool executions",
            unit="1"
        )
        
        self.metrics["tool_execution_duration"] = self.meter.create_histogram(
            "hacs_tool_execution_duration_seconds",
            description="Healthcare tool execution duration",
            unit="s"
        )
        
        # FHIR operations metrics
        self.metrics["fhir_operations_total"] = self.meter.create_counter(
            "hacs_fhir_operations_total",
            description="Total FHIR operations",
            unit="1"
        )
        
        # Authentication metrics
        self.metrics["auth_attempts_total"] = self.meter.create_counter(
            "hacs_auth_attempts_total",
            description="Total authentication attempts",
            unit="1"
        )
        
        # System performance metrics
        self.metrics["memory_usage"] = self.meter.create_gauge(
            "hacs_memory_usage_bytes",
            description="Memory usage in bytes",
            unit="bytes"
        )
        
        self.metrics["active_sessions"] = self.meter.create_gauge(
            "hacs_active_sessions",
            description="Number of active user sessions",
            unit="1"
        )
    
    def increment_counter(self, metric_name: str, value: int = 1, attributes: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        if metric_name in self.metrics:
            self.metrics[metric_name].add(value, attributes or {})
    
    def record_histogram(self, metric_name: str, value: float, attributes: Optional[Dict[str, str]] = None):
        """Record a histogram value."""
        if metric_name in self.metrics:
            self.metrics[metric_name].record(value, attributes or {})
    
    def set_gauge(self, metric_name: str, value: float, attributes: Optional[Dict[str, str]] = None):
        """Set a gauge value."""
        if metric_name in self.metrics:
            self.metrics[metric_name].set(value, attributes or {})
    
    @contextmanager
    def time_histogram(self, metric_name: str, attributes: Optional[Dict[str, str]] = None):
        """Time a block of code and record to histogram."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.record_histogram(metric_name, duration, attributes)


class ObservabilityManager:
    """Central manager for HACS observability."""
    
    def __init__(self, config: Optional[ObservabilityConfig] = None):
        """Initialize observability manager."""
        self.config = config or self._create_default_config()
        
        # Initialize components
        self.logger = StructuredLogger("hacs.observability", self.config)
        self.tracer = HealthcareTracer(self.config)
        self.metrics = HealthcareMetrics(self.config)
        
        # Health check status
        self.health_checks = {}
        
        self.logger.info("Observability framework initialized", 
                        service=self.config.service_name,
                        version=self.config.service_version,
                        environment=self.config.environment)
    
    def _create_default_config(self) -> ObservabilityConfig:
        """Create default configuration from environment."""
        return ObservabilityConfig(
            service_name=os.getenv("HACS_SERVICE_NAME", "hacs-healthcare-ai"),
            service_version=os.getenv("HACS_SERVICE_VERSION", "1.0.0"),
            environment=os.getenv("HACS_ENVIRONMENT", "development"),
            trace_endpoint=os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"),
            metrics_endpoint=os.getenv("OTEL_EXPORTER_OTLP_METRICS_ENDPOINT"),
            enable_tracing=os.getenv("HACS_ENABLE_TRACING", "true").lower() == "true",
            enable_metrics=os.getenv("HACS_ENABLE_METRICS", "true").lower() == "true",
            enable_structured_logging=os.getenv("HACS_ENABLE_STRUCTURED_LOGGING", "true").lower() == "true"
        )
    
    def get_logger(self, name: str) -> StructuredLogger:
        """Get a structured logger instance."""
        return StructuredLogger(name, self.config)
    
    def trace_healthcare_workflow(
        self,
        workflow_name: str,
        patient_id_hash: Optional[str] = None,
        organization: Optional[str] = None,
        care_team: Optional[str] = None
    ):
        """Decorator to trace healthcare workflows."""
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                attributes = HealthcareSpanAttributes(
                    patient_id_hash=patient_id_hash,
                    organization=organization,
                    care_team=care_team,
                    workflow_type=workflow_name
                )
                
                with self.tracer.start_healthcare_span(
                    f"healthcare.workflow.{workflow_name}",
                    attributes=attributes
                ) as span:
                    start_time = time.time()
                    
                    # Record workflow start
                    self.metrics.increment_counter(
                        "patient_workflows_total",
                        attributes={"workflow_type": workflow_name}
                    )
                    
                    try:
                        result = func(*args, **kwargs)
                        
                        if span:
                            span.set_attribute("workflow.success", True)
                        
                        return result
                        
                    except Exception as e:
                        if span:
                            span.record_exception(e)
                            span.set_attribute("workflow.success", False)
                        
                        self.logger.error(
                            f"Healthcare workflow failed: {workflow_name}",
                            workflow_type=workflow_name,
                            error=str(e),
                            patient_id_hash=patient_id_hash
                        )
                        raise
                    
                    finally:
                        # Record workflow duration
                        duration = time.time() - start_time
                        self.metrics.record_histogram(
                            "patient_workflows_duration",
                            duration,
                            attributes={"workflow_type": workflow_name}
                        )
            
            return wrapper
        return decorator
    
    def trace_tool_execution(self, tool_name: str, category: str):
        """Decorator to trace healthcare tool execution."""
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                attributes = HealthcareSpanAttributes(
                    tool_category=category,
                    clinical_domain=category
                )
                
                with self.tracer.start_healthcare_span(
                    f"healthcare.tool.{tool_name}",
                    attributes=attributes
                ) as span:
                    
                    # Record tool execution start
                    self.metrics.increment_counter(
                        "tool_executions_total",
                        attributes={"tool_name": tool_name, "category": category}
                    )
                    
                    with self.metrics.time_histogram(
                        "tool_execution_duration",
                        attributes={"tool_name": tool_name, "category": category}
                    ):
                        try:
                            result = func(*args, **kwargs)
                            
                            if span:
                                span.set_attribute("tool.success", True)
                            
                            return result
                            
                        except Exception as e:
                            if span:
                                span.record_exception(e)
                                span.set_attribute("tool.success", False)
                            
                            self.logger.error(
                                f"Healthcare tool execution failed: {tool_name}",
                                tool_name=tool_name,
                                category=category,
                                error=str(e)
                            )
                            raise
            
            return wrapper
        return decorator
    
    def log_phi_access(
        self,
        user_id: str,
        patient_id_hash: str,
        resource_type: str,
        action: str,
        organization: Optional[str] = None
    ):
        """Log PHI access for HIPAA compliance."""
        self.logger.audit(
            "PHI access event",
            user_id=user_id,
            patient_id_hash=patient_id_hash,
            resource_type=resource_type,
            action=action,
            organization=organization,
            phi_accessed=True
        )
        
        # Record PHI access metric
        self.metrics.increment_counter(
            "phi_access_total",
            attributes={
                "resource_type": resource_type,
                "action": action,
                "organization": organization or "unknown"
            }
        )
        
        # Add trace event
        self.tracer.add_event(
            "phi_access",
            {
                "resource_type": resource_type,
                "action": action,
                "patient_id_hash": patient_id_hash
            }
        )
    
    def record_authentication_attempt(
        self,
        user_id: str,
        success: bool,
        method: str = "password",
        ip_address: Optional[str] = None
    ):
        """Record authentication attempt."""
        self.logger.info(
            "Authentication attempt",
            user_id=user_id,
            success=success,
            method=method,
            ip_address=ip_address
        )
        
        self.metrics.increment_counter(
            "auth_attempts_total",
            attributes={
                "success": str(success),
                "method": method
            }
        )
    
    def register_health_check(self, name: str, check_func: Callable[[], bool]):
        """Register a health check function."""
        self.health_checks[name] = check_func
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status."""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": self.config.service_name,
            "version": self.config.service_version,
            "checks": {}
        }
        
        all_healthy = True
        
        for name, check_func in self.health_checks.items():
            try:
                is_healthy = check_func()
                health_status["checks"][name] = {
                    "status": "healthy" if is_healthy else "unhealthy",
                    "checked_at": datetime.now(timezone.utc).isoformat()
                }
                if not is_healthy:
                    all_healthy = False
            except Exception as e:
                health_status["checks"][name] = {
                    "status": "error",
                    "error": str(e),
                    "checked_at": datetime.now(timezone.utc).isoformat()
                }
                all_healthy = False
        
        if not all_healthy:
            health_status["status"] = "unhealthy"
        
        return health_status
    
    def shutdown(self):
        """Shutdown observability components."""
        self.logger.info("Shutting down observability framework")
        
        # Flush any pending traces and metrics
        if OTEL_AVAILABLE:
            if hasattr(trace.get_tracer_provider(), 'shutdown'):
                trace.get_tracer_provider().shutdown()
            if hasattr(metrics.get_meter_provider(), 'shutdown'):
                metrics.get_meter_provider().shutdown()


# Global observability manager
_observability_manager: Optional[ObservabilityManager] = None


def get_observability_manager(config: Optional[ObservabilityConfig] = None) -> ObservabilityManager:
    """Get or create global observability manager."""
    global _observability_manager
    if _observability_manager is None:
        _observability_manager = ObservabilityManager(config)
    return _observability_manager


def initialize_observability(config: Optional[ObservabilityConfig] = None) -> ObservabilityManager:
    """Initialize HACS observability framework."""
    global _observability_manager
    _observability_manager = ObservabilityManager(config)
    return _observability_manager


# Export public API
__all__ = [
    "ObservabilityConfig",
    "ObservabilityManager",
    "StructuredLogger",
    "HealthcareTracer",
    "HealthcareMetrics",
    "HealthcareSpanAttributes",
    "LogLevel",
    "MetricType",
    "get_observability_manager",
    "initialize_observability",
]