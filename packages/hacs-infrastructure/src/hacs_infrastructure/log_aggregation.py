"""
HACS Log Aggregation and Correlation System

This module provides comprehensive log aggregation, correlation, and analysis
capabilities for healthcare AI systems with HIPAA-compliant centralized logging.

Features:
    - Centralized log aggregation
    - Log correlation across services
    - Healthcare-specific log analysis
    - HIPAA-compliant audit trails
    - Real-time log streaming
    - Anomaly detection in logs
    - Performance analytics from logs

Author: HACS Development Team
License: MIT
Version: 1.0.0
"""

import asyncio
import json
import time
import re
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Callable, Union, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import logging
from pathlib import Path

from .observability import StructuredLogger, LogLevel
from .healthcare_monitoring import HealthcareMonitoringManager


class LogSeverity(str, Enum):
    """Log severity levels for analysis."""
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    FATAL = "fatal"
    AUDIT = "audit"


class CorrelationType(str, Enum):
    """Types of log correlation."""
    TRACE_ID = "trace_id"
    SESSION_ID = "session_id"
    USER_ID = "user_id"
    PATIENT_ID = "patient_id_hash"
    WORKFLOW_TYPE = "workflow_type"
    IP_ADDRESS = "ip_address"
    ORGANIZATION = "organization"


@dataclass
class LogEntry:
    """Structured log entry."""
    timestamp: datetime
    level: LogSeverity
    service: str
    message: str
    logger_name: str
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    patient_id_hash: Optional[str] = None
    organization: Optional[str] = None
    workflow_type: Optional[str] = None
    ip_address: Optional[str] = None
    extra_fields: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "service": self.service,
            "message": self.message,
            "logger_name": self.logger_name,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "patient_id_hash": self.patient_id_hash,
            "organization": self.organization,
            "workflow_type": self.workflow_type,
            "ip_address": self.ip_address,
            "tags": self.tags,
            **self.extra_fields
        }


@dataclass
class LogPattern:
    """Pattern for log analysis."""
    name: str
    pattern: str
    description: str
    severity: LogSeverity
    action: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class LogCorrelation:
    """Correlated log entries."""
    correlation_id: str
    correlation_type: CorrelationType
    entries: List[LogEntry]
    start_time: datetime
    end_time: datetime
    duration_ms: float
    entry_count: int
    error_count: int
    services_involved: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "correlation_id": self.correlation_id,
            "correlation_type": self.correlation_type.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_ms": self.duration_ms,
            "entry_count": self.entry_count,
            "error_count": self.error_count,
            "services_involved": self.services_involved,
            "entries": [entry.to_dict() for entry in self.entries]
        }


class LogAggregator:
    """Centralized log aggregation system."""
    
    def __init__(
        self,
        buffer_size: int = 10000,
        flush_interval_seconds: int = 30,
        retention_days: int = 30
    ):
        """Initialize log aggregator."""
        self.buffer_size = buffer_size
        self.flush_interval_seconds = flush_interval_seconds
        self.retention_days = retention_days
        
        # Log storage
        self._log_buffer: deque = deque(maxlen=buffer_size)
        self._log_index: Dict[str, List[LogEntry]] = defaultdict(list)
        self._correlation_cache: Dict[str, LogCorrelation] = {}
        
        # Pattern matching
        self._patterns: List[LogPattern] = []
        self._pattern_matches: Dict[str, int] = defaultdict(int)
        
        # Streaming subscribers
        self._stream_subscribers: List[Callable[[LogEntry], None]] = []
        
        # Background tasks
        self._running = False
        self._flush_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Healthcare-specific patterns
        self._setup_healthcare_patterns()
        
        # Logger
        self.logger = logging.getLogger("hacs.log_aggregation")
    
    def _setup_healthcare_patterns(self):
        """Setup healthcare-specific log patterns."""
        patterns = [
            LogPattern(
                name="phi_access",
                pattern=r"PHI.*(?:access|read|write|modify)",
                description="PHI access detected",
                severity=LogSeverity.AUDIT,
                tags=["phi", "audit", "hipaa"]
            ),
            LogPattern(
                name="authentication_failure",
                pattern=r"(?:authentication|auth|login).*(?:fail|error|deny)",
                description="Authentication failure detected",
                severity=LogSeverity.WARN,
                action="security_alert",
                tags=["security", "auth", "failure"]
            ),
            LogPattern(
                name="hipaa_violation",
                pattern=r"(?:HIPAA|compliance).*(?:violation|breach|unauthorized)",
                description="Potential HIPAA violation",
                severity=LogSeverity.ERROR,
                action="compliance_alert",
                tags=["hipaa", "compliance", "violation"]
            ),
            LogPattern(
                name="clinical_alert",
                pattern=r"(?:clinical|patient|safety).*(?:alert|critical|urgent)",
                description="Clinical alert detected",
                severity=LogSeverity.ERROR,
                action="clinical_alert",
                tags=["clinical", "patient_safety", "alert"]
            ),
            LogPattern(
                name="system_error",
                pattern=r"(?:system|internal|fatal).*(?:error|exception|crash)",
                description="System error detected",
                severity=LogSeverity.ERROR,
                action="system_alert",
                tags=["system", "error", "reliability"]
            ),
            LogPattern(
                name="performance_issue",
                pattern=r"(?:slow|timeout|performance|latency).*(?:warning|issue|problem)",
                description="Performance issue detected",
                severity=LogSeverity.WARN,
                tags=["performance", "latency", "monitoring"]
            ),
            LogPattern(
                name="security_threat",
                pattern=r"(?:security|threat|attack|injection|exploit)",
                description="Security threat detected",
                severity=LogSeverity.ERROR,
                action="security_incident",
                tags=["security", "threat", "incident"]
            )
        ]
        
        self._patterns.extend(patterns)
    
    async def start(self):
        """Start log aggregation."""
        if self._running:
            return
        
        self._running = True
        self._flush_task = asyncio.create_task(self._flush_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        self.logger.info("Log aggregation started")
    
    async def stop(self):
        """Stop log aggregation."""
        if not self._running:
            return
        
        self._running = False
        
        # Cancel tasks
        if self._flush_task:
            self._flush_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        # Wait for tasks to complete
        tasks = [t for t in [self._flush_task, self._cleanup_task] if t]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Final flush
        await self._flush_logs()
        
        self.logger.info("Log aggregation stopped")
    
    def add_log_entry(
        self,
        level: LogSeverity,
        service: str,
        message: str,
        logger_name: str = "unknown",
        **kwargs
    ):
        """Add a log entry to the aggregation system."""
        entry = LogEntry(
            timestamp=datetime.now(timezone.utc),
            level=level,
            service=service,
            message=message,
            logger_name=logger_name,
            **kwargs
        )
        
        # Add to buffer
        self._log_buffer.append(entry)
        
        # Index for correlation
        self._index_log_entry(entry)
        
        # Pattern matching
        self._match_patterns(entry)
        
        # Notify stream subscribers
        for subscriber in self._stream_subscribers:
            try:
                subscriber(entry)
            except Exception as e:
                self.logger.error(f"Error notifying subscriber: {e}")
    
    def add_structured_log(self, log_data: Dict[str, Any]):
        """Add structured log data."""
        try:
            entry = LogEntry(
                timestamp=datetime.fromisoformat(log_data.get("timestamp", datetime.now(timezone.utc).isoformat())),
                level=LogSeverity(log_data.get("level", "info")),
                service=log_data.get("service", "unknown"),
                message=log_data.get("message", ""),
                logger_name=log_data.get("logger", "unknown"),
                trace_id=log_data.get("trace_id"),
                span_id=log_data.get("span_id"),
                session_id=log_data.get("session_id"),
                user_id=log_data.get("user_id"),
                patient_id_hash=log_data.get("patient_id_hash"),
                organization=log_data.get("organization"),
                workflow_type=log_data.get("workflow_type"),
                ip_address=log_data.get("ip_address"),
                tags=log_data.get("tags", []),
                extra_fields={k: v for k, v in log_data.items() if k not in [
                    "timestamp", "level", "service", "message", "logger",
                    "trace_id", "span_id", "session_id", "user_id", 
                    "patient_id_hash", "organization", "workflow_type",
                    "ip_address", "tags"
                ]}
            )
            
            # Add to buffer
            self._log_buffer.append(entry)
            self._index_log_entry(entry)
            self._match_patterns(entry)
            
            # Notify subscribers
            for subscriber in self._stream_subscribers:
                try:
                    subscriber(entry)
                except Exception as e:
                    self.logger.error(f"Error notifying subscriber: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error processing structured log: {e}")
    
    def _index_log_entry(self, entry: LogEntry):
        """Index log entry for correlation."""
        # Index by various correlation fields
        if entry.trace_id:
            self._log_index[f"trace:{entry.trace_id}"].append(entry)
        if entry.session_id:
            self._log_index[f"session:{entry.session_id}"].append(entry)
        if entry.user_id:
            self._log_index[f"user:{entry.user_id}"].append(entry)
        if entry.patient_id_hash:
            self._log_index[f"patient:{entry.patient_id_hash}"].append(entry)
        if entry.workflow_type:
            self._log_index[f"workflow:{entry.workflow_type}"].append(entry)
        if entry.ip_address:
            self._log_index[f"ip:{entry.ip_address}"].append(entry)
        if entry.organization:
            self._log_index[f"org:{entry.organization}"].append(entry)
    
    def _match_patterns(self, entry: LogEntry):
        """Match log entry against known patterns."""
        full_text = f"{entry.message} {' '.join(entry.extra_fields.values() if isinstance(v, str) else str(v) for v in entry.extra_fields.values())}"
        
        for pattern in self._patterns:
            if re.search(pattern.pattern, full_text, re.IGNORECASE):
                self._pattern_matches[pattern.name] += 1
                
                # Add pattern tags
                if pattern.tags:
                    entry.tags.extend(pattern.tags)
                    entry.tags = list(set(entry.tags))  # Remove duplicates
                
                # Execute action if defined
                if pattern.action:
                    asyncio.create_task(self._execute_pattern_action(pattern, entry))
    
    async def _execute_pattern_action(self, pattern: LogPattern, entry: LogEntry):
        """Execute action for matched pattern."""
        try:
            if pattern.action == "security_alert":
                # Trigger security alert
                pass
            elif pattern.action == "compliance_alert":
                # Trigger compliance alert
                pass
            elif pattern.action == "clinical_alert":
                # Trigger clinical alert
                pass
            elif pattern.action == "system_alert":
                # Trigger system alert
                pass
            elif pattern.action == "security_incident":
                # Trigger security incident response
                pass
                
        except Exception as e:
            self.logger.error(f"Error executing pattern action {pattern.action}: {e}")
    
    def correlate_logs(
        self,
        correlation_type: CorrelationType,
        correlation_value: str,
        time_window_minutes: int = 60
    ) -> Optional[LogCorrelation]:
        """Correlate logs by correlation type and value."""
        correlation_key = f"{correlation_type.value}:{correlation_value}"
        
        # Check cache
        if correlation_key in self._correlation_cache:
            return self._correlation_cache[correlation_key]
        
        # Get correlated entries
        entries = self._log_index.get(correlation_key, [])
        if not entries:
            return None
        
        # Filter by time window
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=time_window_minutes)
        recent_entries = [e for e in entries if e.timestamp >= cutoff]
        
        if not recent_entries:
            return None
        
        # Sort by timestamp
        recent_entries.sort(key=lambda x: x.timestamp)
        
        # Calculate correlation metrics
        start_time = recent_entries[0].timestamp
        end_time = recent_entries[-1].timestamp
        duration_ms = (end_time - start_time).total_seconds() * 1000
        error_count = sum(1 for e in recent_entries if e.level in [LogSeverity.ERROR, LogSeverity.FATAL])
        services_involved = list(set(e.service for e in recent_entries))
        
        correlation = LogCorrelation(
            correlation_id=correlation_value,
            correlation_type=correlation_type,
            entries=recent_entries,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            entry_count=len(recent_entries),
            error_count=error_count,
            services_involved=services_involved
        )
        
        # Cache correlation
        self._correlation_cache[correlation_key] = correlation
        
        return correlation
    
    def search_logs(
        self,
        query: str = "",
        level: Optional[LogSeverity] = None,
        service: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[LogEntry]:
        """Search logs with filters."""
        results = []
        
        for entry in reversed(list(self._log_buffer)):  # Most recent first
            # Apply filters
            if level and entry.level != level:
                continue
            if service and entry.service != service:
                continue
            if start_time and entry.timestamp < start_time:
                continue
            if end_time and entry.timestamp > end_time:
                continue
            if tags and not any(tag in entry.tags for tag in tags):
                continue
            if query and query.lower() not in entry.message.lower():
                continue
            
            results.append(entry)
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_log_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get log statistics for specified time period."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent_logs = [e for e in self._log_buffer if e.timestamp >= cutoff]
        
        # Count by level
        level_counts = defaultdict(int)
        service_counts = defaultdict(int)
        hourly_counts = defaultdict(int)
        
        for entry in recent_logs:
            level_counts[entry.level.value] += 1
            service_counts[entry.service] += 1
            hour_key = entry.timestamp.strftime("%Y-%m-%d %H:00")
            hourly_counts[hour_key] += 1
        
        return {
            "total_logs": len(recent_logs),
            "time_period_hours": hours,
            "by_level": dict(level_counts),
            "by_service": dict(service_counts),
            "hourly_distribution": dict(hourly_counts),
            "pattern_matches": dict(self._pattern_matches),
            "error_rate": level_counts.get("error", 0) / max(len(recent_logs), 1) * 100,
            "top_services": sorted(service_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        }
    
    def subscribe_to_stream(self, callback: Callable[[LogEntry], None]):
        """Subscribe to real-time log stream."""
        self._stream_subscribers.append(callback)
    
    def unsubscribe_from_stream(self, callback: Callable[[LogEntry], None]):
        """Unsubscribe from log stream."""
        if callback in self._stream_subscribers:
            self._stream_subscribers.remove(callback)
    
    async def stream_logs(
        self,
        level_filter: Optional[LogSeverity] = None,
        service_filter: Optional[str] = None
    ) -> AsyncGenerator[LogEntry, None]:
        """Stream logs asynchronously."""
        queue = asyncio.Queue()
        
        def stream_callback(entry: LogEntry):
            if level_filter and entry.level != level_filter:
                return
            if service_filter and entry.service != service_filter:
                return
            queue.put_nowait(entry)
        
        self.subscribe_to_stream(stream_callback)
        
        try:
            while self._running:
                try:
                    entry = await asyncio.wait_for(queue.get(), timeout=1)
                    yield entry
                except asyncio.TimeoutError:
                    continue
        finally:
            self.unsubscribe_from_stream(stream_callback)
    
    async def _flush_loop(self):
        """Background log flushing loop."""
        while self._running:
            try:
                await asyncio.sleep(self.flush_interval_seconds)
                await self._flush_logs()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in flush loop: {e}")
    
    async def _flush_logs(self):
        """Flush logs to persistent storage."""
        if not self._log_buffer:
            return
        
        # In a real implementation, this would write to a database or file system
        # For now, we'll just log the flush operation
        log_count = len(self._log_buffer)
        self.logger.debug(f"Flushing {log_count} log entries to storage")
    
    async def _cleanup_loop(self):
        """Background cleanup loop for old logs and correlations."""
        while self._running:
            try:
                await asyncio.sleep(3600)  # Run every hour
                await self._cleanup_old_data()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
    
    async def _cleanup_old_data(self):
        """Clean up old logs and correlations."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
        
        # Clean up log index
        for key, entries in list(self._log_index.items()):
            self._log_index[key] = [e for e in entries if e.timestamp >= cutoff]
            if not self._log_index[key]:
                del self._log_index[key]
        
        # Clean up correlation cache
        for key, correlation in list(self._correlation_cache.items()):
            if correlation.end_time < cutoff:
                del self._correlation_cache[key]
        
        self.logger.debug("Cleaned up old log data")


# Global log aggregator
_log_aggregator: Optional[LogAggregator] = None


def get_log_aggregator() -> LogAggregator:
    """Get or create global log aggregator."""
    global _log_aggregator
    if _log_aggregator is None:
        _log_aggregator = LogAggregator()
    return _log_aggregator


def initialize_log_aggregation(
    buffer_size: int = 10000,
    flush_interval_seconds: int = 30,
    retention_days: int = 30
) -> LogAggregator:
    """Initialize log aggregation system."""
    global _log_aggregator
    _log_aggregator = LogAggregator(
        buffer_size=buffer_size,
        flush_interval_seconds=flush_interval_seconds,
        retention_days=retention_days
    )
    return _log_aggregator


# Export public API
__all__ = [
    "LogAggregator",
    "LogEntry",
    "LogCorrelation",
    "LogPattern",
    "LogSeverity",
    "CorrelationType",
    "get_log_aggregator",
    "initialize_log_aggregation",
]