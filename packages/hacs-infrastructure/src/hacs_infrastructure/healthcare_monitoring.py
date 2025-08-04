"""
HACS Healthcare-Specific Monitoring Framework

This module extends the base monitoring capabilities with healthcare-specific
monitoring, alerting, and compliance tracking for HIPAA environments.

Features:
    - PHI access monitoring
    - HIPAA compliance tracking
    - Healthcare workflow monitoring
    - Clinical tool performance tracking
    - Patient safety alerting
    - Audit trail monitoring

Author: HACS Development Team
License: MIT
Version: 1.0.0
"""

import asyncio
import time
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import json

from .monitoring import MetricsCollector, HealthMonitor, PerformanceMonitor
from .events import EventBus, Event, EventPriority


class ClinicalSeverity(str, Enum):
    """Clinical severity levels for healthcare alerts."""
    INFORMATIONAL = "informational"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"
    LIFE_THREATENING = "life_threatening"


class ComplianceStatus(str, Enum):
    """HIPAA compliance status."""
    COMPLIANT = "compliant"
    WARNING = "warning"
    VIOLATION = "violation"
    CRITICAL_VIOLATION = "critical_violation"


@dataclass
class PHIAccessEvent:
    """PHI access event for audit tracking."""
    timestamp: datetime
    user_id: str
    patient_id_hash: str
    resource_type: str
    action: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    organization: Optional[str] = None
    session_id: Optional[str] = None
    success: bool = True
    access_reason: Optional[str] = None
    data_elements_accessed: List[str] = field(default_factory=list)


@dataclass 
class ClinicalAlert:
    """Clinical alert for patient safety."""
    alert_id: str
    timestamp: datetime
    severity: ClinicalSeverity
    patient_id_hash: str
    alert_type: str
    message: str
    clinical_context: Dict[str, Any] = field(default_factory=dict)
    recommended_actions: List[str] = field(default_factory=list)
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class ComplianceEvent:
    """HIPAA compliance monitoring event."""
    timestamp: datetime
    event_type: str
    status: ComplianceStatus
    description: str
    affected_resources: List[str] = field(default_factory=list)
    remediation_required: bool = False
    remediation_steps: List[str] = field(default_factory=list)
    risk_level: str = "medium"


class HealthcareMetricsCollector(MetricsCollector):
    """Extended metrics collector with healthcare-specific metrics."""
    
    def __init__(self, retention_period: int = 7 * 24 * 3600):  # 7 days for HIPAA
        """Initialize with longer retention for healthcare compliance."""
        super().__init__(retention_period)
        
        # Healthcare-specific metric tracking
        self._phi_access_events: List[PHIAccessEvent] = []
        self._clinical_alerts: List[ClinicalAlert] = []
        self._compliance_events: List[ComplianceEvent] = []
        
        # Alert thresholds
        self._phi_access_rate_threshold = 100  # per hour
        self._failed_auth_threshold = 5  # per 15 minutes
        self._workflow_error_threshold = 0.05  # 5% error rate
    
    def record_phi_access(
        self,
        user_id: str,
        patient_id_hash: str,
        resource_type: str,
        action: str,
        **kwargs
    ) -> None:
        """Record PHI access event for HIPAA audit."""
        event = PHIAccessEvent(
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            patient_id_hash=patient_id_hash,
            resource_type=resource_type,
            action=action,
            **kwargs
        )
        
        self._phi_access_events.append(event)
        
        # Record metrics
        self.increment_counter(
            "healthcare.phi_access.total",
            tags={
                "resource_type": resource_type,
                "action": action,
                "user_type": self._classify_user_type(user_id)
            }
        )
        
        # Check for excessive access patterns
        self._check_phi_access_patterns(user_id)
    
    def record_clinical_workflow(
        self,
        workflow_type: str,
        duration_ms: float,
        patient_id_hash: Optional[str] = None,
        success: bool = True,
        error_type: Optional[str] = None,
        **kwargs
    ) -> None:
        """Record clinical workflow execution."""
        tags = {
            "workflow_type": workflow_type,
            "status": "success" if success else "error"
        }
        
        if error_type:
            tags["error_type"] = error_type
        
        # Record timing and count
        self.record_timing("healthcare.workflow", duration_ms, tags)
        
        # Record patient-specific metrics if applicable
        if patient_id_hash:
            self.increment_counter(
                "healthcare.patient_workflows.total",
                tags={"workflow_type": workflow_type}
            )
        
        # Check workflow error rates
        if not success:
            self._check_workflow_error_rates(workflow_type)
    
    def record_clinical_tool_execution(
        self,
        tool_name: str,
        category: str,
        duration_ms: float,
        success: bool = True,
        patient_impact: bool = False,
        **kwargs
    ) -> None:
        """Record clinical tool execution metrics."""
        tags = {
            "tool_name": tool_name,
            "category": category,
            "status": "success" if success else "error",
            "patient_impact": str(patient_impact).lower()
        }
        
        self.record_timing("healthcare.tool_execution", duration_ms, tags)
        
        # Track patient-impacting tools separately
        if patient_impact:
            self.increment_counter("healthcare.patient_impacting_tools.total", tags=tags)
    
    def record_authentication_event(
        self,
        user_id: str,
        method: str,
        success: bool,
        ip_address: Optional[str] = None,
        **kwargs
    ) -> None:
        """Record authentication event with security monitoring."""
        tags = {
            "method": method,
            "status": "success" if success else "failure",
            "user_type": self._classify_user_type(user_id)
        }
        
        self.increment_counter("healthcare.authentication.total", tags=tags)
        
        # Track failed attempts for security monitoring
        if not success:
            self._check_failed_authentication_patterns(user_id, ip_address)
    
    def create_clinical_alert(
        self,
        alert_type: str,
        severity: ClinicalSeverity,
        patient_id_hash: str,
        message: str,
        clinical_context: Optional[Dict[str, Any]] = None,
        recommended_actions: Optional[List[str]] = None
    ) -> ClinicalAlert:
        """Create and track clinical alert."""
        alert = ClinicalAlert(
            alert_id=f"alert_{int(time.time() * 1000)}_{patient_id_hash[:8]}",
            timestamp=datetime.now(timezone.utc),
            severity=severity,
            patient_id_hash=patient_id_hash,
            alert_type=alert_type,
            message=message,
            clinical_context=clinical_context or {},
            recommended_actions=recommended_actions or []
        )
        
        self._clinical_alerts.append(alert)
        
        # Record alert metrics
        self.increment_counter(
            "healthcare.clinical_alerts.total",
            tags={
                "alert_type": alert_type,
                "severity": severity.value
            }
        )
        
        return alert
    
    def record_compliance_event(
        self,
        event_type: str,
        status: ComplianceStatus,
        description: str,
        affected_resources: Optional[List[str]] = None,
        **kwargs
    ) -> ComplianceEvent:
        """Record HIPAA compliance event."""
        event = ComplianceEvent(
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            status=status,
            description=description,
            affected_resources=affected_resources or [],
            **kwargs
        )
        
        self._compliance_events.append(event)
        
        # Record compliance metrics
        self.increment_counter(
            "healthcare.compliance.events.total",
            tags={
                "event_type": event_type,
                "status": status.value,
                "risk_level": event.risk_level
            }
        )
        
        # Alert on violations
        if status in [ComplianceStatus.VIOLATION, ComplianceStatus.CRITICAL_VIOLATION]:
            self._handle_compliance_violation(event)
        
        return event
    
    def get_phi_access_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get PHI access summary for specified hours."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent_events = [e for e in self._phi_access_events if e.timestamp >= cutoff]
        
        # Group by resource type and action
        by_resource = {}
        by_action = {}
        by_user = {}
        
        for event in recent_events:
            by_resource[event.resource_type] = by_resource.get(event.resource_type, 0) + 1
            by_action[event.action] = by_action.get(event.action, 0) + 1
            by_user[event.user_id] = by_user.get(event.user_id, 0) + 1
        
        return {
            "total_accesses": len(recent_events),
            "time_period_hours": hours,
            "by_resource_type": by_resource,
            "by_action": by_action,
            "by_user": by_user,
            "unique_patients": len(set(e.patient_id_hash for e in recent_events)),
            "unique_users": len(set(e.user_id for e in recent_events))
        }
    
    def get_clinical_alerts_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get clinical alerts summary."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent_alerts = [a for a in self._clinical_alerts if a.timestamp >= cutoff]
        
        # Group by severity
        by_severity = {}
        for alert in recent_alerts:
            by_severity[alert.severity.value] = by_severity.get(alert.severity.value, 0) + 1
        
        return {
            "total_alerts": len(recent_alerts),
            "active_alerts": len([a for a in recent_alerts if not a.resolved]),
            "acknowledged_alerts": len([a for a in recent_alerts if a.acknowledged]),
            "by_severity": by_severity,
            "critical_unresolved": len([
                a for a in recent_alerts 
                if a.severity in [ClinicalSeverity.CRITICAL, ClinicalSeverity.LIFE_THREATENING] 
                and not a.resolved
            ])
        }
    
    def get_compliance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get HIPAA compliance summary."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent_events = [e for e in self._compliance_events if e.timestamp >= cutoff]
        
        # Group by status
        by_status = {}
        for event in recent_events:
            by_status[event.status.value] = by_status.get(event.status.value, 0) + 1
        
        return {
            "total_events": len(recent_events),
            "compliance_score": self._calculate_compliance_score(recent_events),
            "by_status": by_status,
            "violations": len([e for e in recent_events if e.status in [
                ComplianceStatus.VIOLATION, ComplianceStatus.CRITICAL_VIOLATION
            ]]),
            "remediation_required": len([e for e in recent_events if e.remediation_required])
        }
    
    def _classify_user_type(self, user_id: str) -> str:
        """Classify user type based on user ID patterns."""
        user_id_lower = user_id.lower()
        
        if "admin" in user_id_lower:
            return "administrator"
        elif "dr_" in user_id_lower or "doctor" in user_id_lower:
            return "physician"
        elif "nurse" in user_id_lower or "rn_" in user_id_lower:
            return "nurse"
        elif "tech" in user_id_lower or "technician" in user_id_lower:
            return "technician"
        elif "agent" in user_id_lower or "ai_" in user_id_lower:
            return "ai_agent"
        else:
            return "user"
    
    def _check_phi_access_patterns(self, user_id: str) -> None:
        """Check for suspicious PHI access patterns."""
        # Check access rate in last hour
        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        recent_accesses = [
            e for e in self._phi_access_events 
            if e.user_id == user_id and e.timestamp >= cutoff
        ]
        
        if len(recent_accesses) > self._phi_access_rate_threshold:
            self.record_compliance_event(
                "excessive_phi_access",
                ComplianceStatus.WARNING,
                f"User {user_id} accessed PHI {len(recent_accesses)} times in the last hour",
                risk_level="high"
            )
    
    def _check_workflow_error_rates(self, workflow_type: str) -> None:
        """Check workflow error rates for patient safety."""
        # Get recent workflow executions
        error_count = self.get_counter(
            "healthcare.workflow.count",
            tags={"workflow_type": workflow_type, "status": "error"}
        )
        total_count = self.get_counter(
            "healthcare.workflow.count",
            tags={"workflow_type": workflow_type}
        )
        
        if total_count > 10:  # Only check if we have enough data
            error_rate = error_count / total_count
            if error_rate > self._workflow_error_threshold:
                # Create clinical alert for high error rate
                self.create_clinical_alert(
                    "workflow_error_rate",
                    ClinicalSeverity.HIGH,
                    "system",  # System-level alert
                    f"High error rate detected in {workflow_type} workflow: {error_rate:.2%}",
                    clinical_context={"workflow_type": workflow_type, "error_rate": error_rate},
                    recommended_actions=[
                        "Review workflow configuration",
                        "Check system dependencies",
                        "Review recent changes"
                    ]
                )
    
    def _check_failed_authentication_patterns(self, user_id: str, ip_address: Optional[str]) -> None:
        """Check for suspicious authentication patterns."""
        # Check failed attempts in last 15 minutes
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=15)
        
        # Count recent failures by user
        user_failures = self.get_counter(
            "healthcare.authentication.total",
            tags={"status": "failure"}
        )
        
        if user_failures > self._failed_auth_threshold:
            self.record_compliance_event(
                "suspicious_authentication",
                ComplianceStatus.WARNING,
                f"Multiple failed authentication attempts detected",
                risk_level="high"
            )
    
    def _handle_compliance_violation(self, event: ComplianceEvent) -> None:
        """Handle HIPAA compliance violations."""
        # Log violation
        logger = logging.getLogger("hacs.compliance")
        logger.error(f"HIPAA compliance violation: {event.description}", extra={
            "event_type": event.event_type,
            "status": event.status.value,
            "affected_resources": event.affected_resources
        })
        
        # Create clinical alert if critical
        if event.status == ComplianceStatus.CRITICAL_VIOLATION:
            self.create_clinical_alert(
                "compliance_violation",
                ClinicalSeverity.CRITICAL,
                "system",
                f"Critical HIPAA violation: {event.description}",
                clinical_context={"compliance_event": event.event_type},
                recommended_actions=event.remediation_steps
            )
    
    def _calculate_compliance_score(self, events: List[ComplianceEvent]) -> float:
        """Calculate compliance score based on recent events."""
        if not events:
            return 100.0
        
        total_score = 100.0
        
        for event in events:
            if event.status == ComplianceStatus.CRITICAL_VIOLATION:
                total_score -= 20.0
            elif event.status == ComplianceStatus.VIOLATION:
                total_score -= 10.0
            elif event.status == ComplianceStatus.WARNING:
                total_score -= 2.0
        
        return max(0.0, total_score)


class HealthcareMonitoringManager:
    """Central healthcare monitoring manager."""
    
    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        enable_phi_monitoring: bool = True,
        enable_compliance_tracking: bool = True
    ):
        """Initialize healthcare monitoring manager."""
        self.event_bus = event_bus or EventBus()
        self.enable_phi_monitoring = enable_phi_monitoring
        self.enable_compliance_tracking = enable_compliance_tracking
        
        # Initialize components
        self.metrics = HealthcareMetricsCollector()
        self.health_monitor = HealthMonitor(self.event_bus)
        self.performance_monitor = PerformanceMonitor(self.metrics)
        
        # Healthcare-specific monitoring
        self._monitoring_tasks: List[asyncio.Task] = []
        self._running = False
        
        # Alert callbacks
        self._alert_callbacks: List[Callable[[ClinicalAlert], None]] = []
        self._compliance_callbacks: List[Callable[[ComplianceEvent], None]] = []
    
    async def start(self) -> None:
        """Start healthcare monitoring."""
        if self._running:
            return
        
        self._running = True
        
        # Start base monitoring components
        await self.metrics.start()
        await self.health_monitor.start()
        await self.performance_monitor.start()
        
        # Start healthcare-specific monitoring tasks
        if self.enable_phi_monitoring:
            task = asyncio.create_task(self._phi_monitoring_loop())
            self._monitoring_tasks.append(task)
        
        if self.enable_compliance_tracking:
            task = asyncio.create_task(self._compliance_monitoring_loop())
            self._monitoring_tasks.append(task)
        
        # Start alert processing
        task = asyncio.create_task(self._alert_processing_loop())
        self._monitoring_tasks.append(task)
    
    async def stop(self) -> None:
        """Stop healthcare monitoring."""
        if not self._running:
            return
        
        self._running = False
        
        # Stop base monitoring components
        await self.metrics.stop()
        await self.health_monitor.stop()
        await self.performance_monitor.stop()
        
        # Cancel healthcare-specific tasks
        for task in self._monitoring_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._monitoring_tasks:
            await asyncio.gather(*self._monitoring_tasks, return_exceptions=True)
        
        self._monitoring_tasks.clear()
    
    def register_alert_callback(self, callback: Callable[[ClinicalAlert], None]) -> None:
        """Register callback for clinical alerts."""
        self._alert_callbacks.append(callback)
    
    def register_compliance_callback(self, callback: Callable[[ComplianceEvent], None]) -> None:
        """Register callback for compliance events."""
        self._compliance_callbacks.append(callback)
    
    def get_healthcare_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive healthcare monitoring dashboard data."""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "phi_access": self.metrics.get_phi_access_summary(),
            "clinical_alerts": self.metrics.get_clinical_alerts_summary(),
            "compliance": self.metrics.get_compliance_summary(),
            "health_summary": self.health_monitor.get_health_summary(),
            "system_metrics": {
                "cpu_usage": self.metrics.get_gauge("system.cpu.usage_percent"),
                "memory_usage": self.metrics.get_gauge("system.memory.usage_percent"),
                "active_workflows": self.metrics.get_counter("healthcare.workflow.count"),
                "total_phi_accesses": self.metrics.get_counter("healthcare.phi_access.total")
            }
        }
    
    async def _phi_monitoring_loop(self) -> None:
        """Monitor PHI access patterns."""
        while self._running:
            try:
                # Check for unusual PHI access patterns
                # This would integrate with actual access logs
                await asyncio.sleep(300)  # Check every 5 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger = logging.getLogger("hacs.monitoring")
                logger.error(f"Error in PHI monitoring: {e}")
                await asyncio.sleep(60)
    
    async def _compliance_monitoring_loop(self) -> None:
        """Monitor HIPAA compliance."""
        while self._running:
            try:
                # Perform compliance checks
                await self._check_audit_trail_integrity()
                await self._check_encryption_compliance()
                await self._check_access_controls()
                
                await asyncio.sleep(600)  # Check every 10 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger = logging.getLogger("hacs.monitoring")
                logger.error(f"Error in compliance monitoring: {e}")
                await asyncio.sleep(60)
    
    async def _alert_processing_loop(self) -> None:
        """Process and distribute alerts."""
        while self._running:
            try:
                # Process pending clinical alerts
                for alert in self.metrics._clinical_alerts:
                    if not alert.acknowledged and alert.severity in [
                        ClinicalSeverity.CRITICAL, ClinicalSeverity.LIFE_THREATENING
                    ]:
                        # Notify alert callbacks
                        for callback in self._alert_callbacks:
                            try:
                                callback(alert)
                            except Exception as e:
                                logger = logging.getLogger("hacs.monitoring")
                                logger.error(f"Error in alert callback: {e}")
                
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger = logging.getLogger("hacs.monitoring")
                logger.error(f"Error in alert processing: {e}")
                await asyncio.sleep(30)
    
    async def _check_audit_trail_integrity(self) -> None:
        """Check audit trail integrity for HIPAA compliance."""
        # Placeholder for audit trail integrity checks
        pass
    
    async def _check_encryption_compliance(self) -> None:
        """Check encryption compliance."""
        # Placeholder for encryption compliance checks
        pass
    
    async def _check_access_controls(self) -> None:
        """Check access control compliance."""
        # Placeholder for access control checks
        pass


# Global healthcare monitoring manager
_healthcare_monitoring: Optional[HealthcareMonitoringManager] = None


def get_healthcare_monitoring() -> HealthcareMonitoringManager:
    """Get or create global healthcare monitoring manager."""
    global _healthcare_monitoring
    if _healthcare_monitoring is None:
        _healthcare_monitoring = HealthcareMonitoringManager()
    return _healthcare_monitoring


def initialize_healthcare_monitoring(
    event_bus: Optional[EventBus] = None,
    enable_phi_monitoring: bool = True,
    enable_compliance_tracking: bool = True
) -> HealthcareMonitoringManager:
    """Initialize healthcare monitoring framework."""
    global _healthcare_monitoring
    _healthcare_monitoring = HealthcareMonitoringManager(
        event_bus=event_bus,
        enable_phi_monitoring=enable_phi_monitoring,
        enable_compliance_tracking=enable_compliance_tracking
    )
    return _healthcare_monitoring


# Export public API
__all__ = [
    "HealthcareMonitoringManager",
    "HealthcareMetricsCollector",
    "PHIAccessEvent",
    "ClinicalAlert",
    "ComplianceEvent",
    "ClinicalSeverity",
    "ComplianceStatus",
    "get_healthcare_monitoring",
    "initialize_healthcare_monitoring",
]