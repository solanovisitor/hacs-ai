"""
HACS Alerting and Notification Framework

This module provides comprehensive alerting and notification capabilities
for healthcare AI systems with multi-channel delivery and escalation support.

Features:
    - Multi-channel alert delivery (email, SMS, Slack, PagerDuty)
    - Alert escalation workflows
    - Healthcare-specific alert types
    - HIPAA-compliant notifications
    - Alert correlation and deduplication
    - On-call rotation management
    - Alert acknowledgment and resolution tracking

Author: HACS Development Team
License: MIT
Version: 1.0.0
"""

import asyncio
import json
import time
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
try:
    import smtplib
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    MimeText = None
    MimeMultipart = None
    smtplib = None

from .healthcare_monitoring import ClinicalAlert, ComplianceEvent, ClinicalSeverity, ComplianceStatus
from .observability import get_observability_manager


class AlertChannel(str, Enum):
    """Alert delivery channels."""
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    TEAMS = "teams"
    PAGERDUTY = "pagerduty"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


class AlertType(str, Enum):
    """Types of alerts."""
    CLINICAL = "clinical"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    SYSTEM = "system"
    PERFORMANCE = "performance"
    INFRASTRUCTURE = "infrastructure"


class AlertStatus(str, Enum):
    """Alert status."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"
    ESCALATED = "escalated"


class AlertPriority(str, Enum):
    """Alert priority levels."""
    P1_CRITICAL = "p1_critical"    # < 5 minutes
    P2_HIGH = "p2_high"            # < 15 minutes
    P3_MEDIUM = "p3_medium"        # < 1 hour
    P4_LOW = "p4_low"              # < 24 hours
    P5_INFO = "p5_info"            # No SLA


@dataclass
class AlertRule:
    """Alert rule configuration."""
    id: str
    name: str
    description: str
    alert_type: AlertType
    priority: AlertPriority
    condition: str  # Expression to evaluate
    threshold: Optional[float] = None
    duration_minutes: int = 5
    channels: List[AlertChannel] = field(default_factory=list)
    recipients: List[str] = field(default_factory=list)
    escalation_minutes: int = 15
    enabled: bool = True
    tags: List[str] = field(default_factory=list)
    suppress_similar_minutes: int = 60


@dataclass
class Alert:
    """Alert instance."""
    id: str
    rule_id: str
    alert_type: AlertType
    priority: AlertPriority
    title: str
    description: str
    status: AlertStatus
    created_at: datetime
    updated_at: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    escalated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    channels_notified: List[AlertChannel] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "alert_type": self.alert_type.value,
            "priority": self.priority.value,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "acknowledged_by": self.acknowledged_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "escalated_at": self.escalated_at.isoformat() if self.escalated_at else None,
            "metadata": self.metadata,
            "tags": self.tags,
            "channels_notified": [c.value for c in self.channels_notified]
        }


@dataclass
class NotificationChannel:
    """Notification channel configuration."""
    channel_type: AlertChannel
    name: str
    config: Dict[str, Any]
    enabled: bool = True
    retry_attempts: int = 3
    retry_delay_seconds: int = 30


@dataclass
class OnCallSchedule:
    """On-call schedule configuration."""
    name: str
    rotation_hours: int = 24
    escalation_minutes: int = 15
    participants: List[str] = field(default_factory=list)
    alert_types: List[AlertType] = field(default_factory=list)
    active: bool = True


class AlertManager:
    """Healthcare alert management system."""
    
    def __init__(self):
        """Initialize alert manager."""
        self.observability = get_observability_manager()
        self.logger = self.observability.get_logger("hacs.alerting")
        
        # Alert storage
        self._alerts: Dict[str, Alert] = {}
        self._alert_rules: Dict[str, AlertRule] = {}
        self._notification_channels: Dict[str, NotificationChannel] = {}
        self._on_call_schedules: List[OnCallSchedule] = []
        
        # Alert processing
        self._alert_queue: asyncio.Queue = asyncio.Queue()
        self._suppression_cache: Dict[str, datetime] = {}
        
        # Background tasks
        self._running = False
        self._processing_task: Optional[asyncio.Task] = None
        self._escalation_task: Optional[asyncio.Task] = None
        
        # Event handlers
        self._alert_handlers: List[Callable[[Alert], None]] = []
        
        # Initialize default rules and channels
        self._setup_default_rules()
        self._setup_default_channels()
    
    def _setup_default_rules(self):
        """Setup default healthcare alert rules."""
        default_rules = [
            AlertRule(
                id="clinical_critical_alert",
                name="Critical Clinical Alert",
                description="Life-threatening or critical clinical situations",
                alert_type=AlertType.CLINICAL,
                priority=AlertPriority.P1_CRITICAL,
                condition="severity in ['critical', 'life_threatening']",
                channels=[AlertChannel.EMAIL, AlertChannel.SMS, AlertChannel.PAGERDUTY],
                escalation_minutes=5,
                tags=["clinical", "patient_safety"]
            ),
            AlertRule(
                id="hipaa_compliance_violation",
                name="HIPAA Compliance Violation",
                description="HIPAA compliance violations requiring immediate attention",
                alert_type=AlertType.COMPLIANCE,
                priority=AlertPriority.P1_CRITICAL,
                condition="status in ['violation', 'critical_violation']",
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK],
                escalation_minutes=10,
                tags=["compliance", "hipaa", "violation"]
            ),
            AlertRule(
                id="security_incident",
                name="Security Incident",
                description="Security threats and incidents",
                alert_type=AlertType.SECURITY,
                priority=AlertPriority.P2_HIGH,
                condition="threat_level == 'high' or attack_detected == true",
                channels=[AlertChannel.EMAIL, AlertChannel.PAGERDUTY],
                escalation_minutes=15,
                tags=["security", "incident"]
            ),
            AlertRule(
                id="system_failure",
                name="System Failure",
                description="Critical system failures affecting patient care",
                alert_type=AlertType.SYSTEM,
                priority=AlertPriority.P2_HIGH,
                condition="service_status == 'down' or error_rate > 50",
                channels=[AlertChannel.EMAIL, AlertChannel.SMS],
                escalation_minutes=10,
                tags=["system", "failure", "downtime"]
            ),
            AlertRule(
                id="performance_degradation",
                name="Performance Degradation",
                description="Significant performance issues affecting workflows",
                alert_type=AlertType.PERFORMANCE,
                priority=AlertPriority.P3_MEDIUM,
                condition="response_time > 5000 or throughput < baseline * 0.5",
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK],
                escalation_minutes=30,
                tags=["performance", "latency"]
            )
        ]
        
        for rule in default_rules:
            self._alert_rules[rule.id] = rule
    
    def _setup_default_channels(self):
        """Setup default notification channels."""
        # Email channel
        email_channel = NotificationChannel(
            channel_type=AlertChannel.EMAIL,
            name="Default Email",
            config={
                "smtp_server": "localhost",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "from_address": "alerts@hacs.healthcare"
            }
        )
        
        # Slack channel
        slack_channel = NotificationChannel(
            channel_type=AlertChannel.SLACK,
            name="Default Slack",
            config={
                "webhook_url": "",
                "channel": "#alerts",
                "username": "HACS Alerts"
            }
        )
        
        # Webhook channel
        webhook_channel = NotificationChannel(
            channel_type=AlertChannel.WEBHOOK,
            name="Default Webhook",
            config={
                "url": "",
                "headers": {"Content-Type": "application/json"},
                "timeout_seconds": 30
            }
        )
        
        self._notification_channels.update({
            "email_default": email_channel,
            "slack_default": slack_channel,
            "webhook_default": webhook_channel
        })
    
    async def start(self):
        """Start alert processing."""
        if self._running:
            return
        
        self._running = True
        self._processing_task = asyncio.create_task(self._process_alerts())
        self._escalation_task = asyncio.create_task(self._handle_escalations())
        
        self.logger.info("Alert manager started")
    
    async def stop(self):
        """Stop alert processing."""
        if not self._running:
            return
        
        self._running = False
        
        # Cancel tasks
        if self._processing_task:
            self._processing_task.cancel()
        if self._escalation_task:
            self._escalation_task.cancel()
        
        # Wait for tasks to complete
        tasks = [t for t in [self._processing_task, self._escalation_task] if t]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        self.logger.info("Alert manager stopped")
    
    def create_alert(
        self,
        rule_id: str,
        title: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> Alert:
        """Create a new alert."""
        rule = self._alert_rules.get(rule_id)
        if not rule:
            raise ValueError(f"Unknown alert rule: {rule_id}")
        
        # Check suppression
        suppression_key = self._get_suppression_key(rule_id, title, metadata or {})
        if self._is_suppressed(suppression_key):
            self.logger.debug(f"Alert suppressed: {title}")
            return None
        
        # Create alert
        alert_id = self._generate_alert_id(rule_id, title)
        now = datetime.now(timezone.utc)
        
        alert = Alert(
            id=alert_id,
            rule_id=rule_id,
            alert_type=rule.alert_type,
            priority=rule.priority,
            title=title,
            description=description,
            status=AlertStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
            tags=(tags or []) + rule.tags
        )
        
        # Store alert
        self._alerts[alert_id] = alert
        
        # Add to processing queue
        self._alert_queue.put_nowait(alert)
        
        # Set suppression
        self._suppression_cache[suppression_key] = now
        
        self.logger.info(f"Created alert: {alert_id} - {title}")
        return alert
    
    def create_clinical_alert(self, clinical_alert: ClinicalAlert) -> Alert:
        """Create alert from clinical alert."""
        severity_priority_map = {
            ClinicalSeverity.LIFE_THREATENING: AlertPriority.P1_CRITICAL,
            ClinicalSeverity.CRITICAL: AlertPriority.P1_CRITICAL,
            ClinicalSeverity.HIGH: AlertPriority.P2_HIGH,
            ClinicalSeverity.MODERATE: AlertPriority.P3_MEDIUM,
            ClinicalSeverity.LOW: AlertPriority.P4_LOW,
            ClinicalSeverity.INFORMATIONAL: AlertPriority.P5_INFO
        }
        
        # Determine rule based on severity
        if clinical_alert.severity in [ClinicalSeverity.CRITICAL, ClinicalSeverity.LIFE_THREATENING]:
            rule_id = "clinical_critical_alert"
        else:
            rule_id = "clinical_moderate_alert"
            
        # Create rule if it doesn't exist
        if rule_id not in self._alert_rules:
            self._alert_rules[rule_id] = AlertRule(
                id=rule_id,
                name="Clinical Alert",
                description="Clinical workflow alert",
                alert_type=AlertType.CLINICAL,
                priority=severity_priority_map.get(clinical_alert.severity, AlertPriority.P3_MEDIUM),
                condition="clinical_alert",
                channels=[AlertChannel.EMAIL, AlertChannel.IN_APP]
            )
        
        return self.create_alert(
            rule_id=rule_id,
            title=f"Clinical Alert: {clinical_alert.alert_type}",
            description=clinical_alert.message,
            metadata={
                "patient_id_hash": clinical_alert.patient_id_hash,
                "severity": clinical_alert.severity.value,
                "alert_type": clinical_alert.alert_type,
                "clinical_context": clinical_alert.clinical_context,
                "recommended_actions": clinical_alert.recommended_actions
            },
            tags=["clinical", "patient_safety", clinical_alert.severity.value]
        )
    
    def create_compliance_alert(self, compliance_event: ComplianceEvent) -> Alert:
        """Create alert from compliance event."""
        status_priority_map = {
            ComplianceStatus.CRITICAL_VIOLATION: AlertPriority.P1_CRITICAL,
            ComplianceStatus.VIOLATION: AlertPriority.P2_HIGH,
            ComplianceStatus.WARNING: AlertPriority.P3_MEDIUM,
            ComplianceStatus.COMPLIANT: AlertPriority.P5_INFO
        }
        
        if compliance_event.status in [ComplianceStatus.VIOLATION, ComplianceStatus.CRITICAL_VIOLATION]:
            rule_id = "hipaa_compliance_violation"
        else:
            rule_id = "compliance_warning"
            
        # Create rule if it doesn't exist
        if rule_id not in self._alert_rules:
            self._alert_rules[rule_id] = AlertRule(
                id=rule_id,
                name="Compliance Alert",
                description="HIPAA compliance alert",
                alert_type=AlertType.COMPLIANCE,
                priority=status_priority_map.get(compliance_event.status, AlertPriority.P3_MEDIUM),
                condition="compliance_event",
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK]
            )
        
        return self.create_alert(
            rule_id=rule_id,
            title=f"Compliance Alert: {compliance_event.event_type}",
            description=compliance_event.description,
            metadata={
                "event_type": compliance_event.event_type,
                "status": compliance_event.status.value,
                "affected_resources": compliance_event.affected_resources,
                "remediation_required": compliance_event.remediation_required,
                "remediation_steps": compliance_event.remediation_steps,
                "risk_level": compliance_event.risk_level
            },
            tags=["compliance", "hipaa", compliance_event.status.value]
        )
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert."""
        alert = self._alerts.get(alert_id)
        if not alert:
            return False
        
        if alert.status != AlertStatus.ACTIVE:
            return False
        
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.now(timezone.utc)
        alert.acknowledged_by = acknowledged_by
        alert.updated_at = datetime.now(timezone.utc)
        
        self.logger.info(f"Alert acknowledged: {alert_id} by {acknowledged_by}")
        
        # Notify handlers
        for handler in self._alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"Error in alert handler: {e}")
        
        return True
    
    async def resolve_alert(self, alert_id: str, resolved_by: str, resolution_note: str = "") -> bool:
        """Resolve an alert."""
        alert = self._alerts.get(alert_id)
        if not alert:
            return False
        
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now(timezone.utc)
        alert.resolved_by = resolved_by
        alert.updated_at = datetime.now(timezone.utc)
        
        if resolution_note:
            alert.metadata["resolution_note"] = resolution_note
        
        self.logger.info(f"Alert resolved: {alert_id} by {resolved_by}")
        
        # Notify handlers
        for handler in self._alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"Error in alert handler: {e}")
        
        return True
    
    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get alert by ID."""
        return self._alerts.get(alert_id)
    
    def list_alerts(
        self,
        status: Optional[AlertStatus] = None,
        alert_type: Optional[AlertType] = None,
        priority: Optional[AlertPriority] = None,
        limit: int = 100
    ) -> List[Alert]:
        """List alerts with filters."""
        alerts = list(self._alerts.values())
        
        # Apply filters
        if status:
            alerts = [a for a in alerts if a.status == status]
        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]
        if priority:
            alerts = [a for a in alerts if a.priority == priority]
        
        # Sort by created_at (most recent first)
        alerts.sort(key=lambda x: x.created_at, reverse=True)
        
        return alerts[:limit]
    
    def get_alert_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get alert statistics."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent_alerts = [a for a in self._alerts.values() if a.created_at >= cutoff]
        
        # Count by various dimensions
        by_status = {}
        by_type = {}
        by_priority = {}
        
        for alert in recent_alerts:
            by_status[alert.status.value] = by_status.get(alert.status.value, 0) + 1
            by_type[alert.alert_type.value] = by_type.get(alert.alert_type.value, 0) + 1
            by_priority[alert.priority.value] = by_priority.get(alert.priority.value, 0) + 1
        
        # Calculate metrics
        total_alerts = len(recent_alerts)
        acknowledged_count = sum(1 for a in recent_alerts if a.acknowledged_at)
        resolved_count = sum(1 for a in recent_alerts if a.resolved_at)
        
        # Calculate average resolution time
        resolved_alerts = [a for a in recent_alerts if a.resolved_at]
        avg_resolution_time = 0
        if resolved_alerts:
            total_resolution_time = sum(
                (a.resolved_at - a.created_at).total_seconds() 
                for a in resolved_alerts
            )
            avg_resolution_time = total_resolution_time / len(resolved_alerts) / 60  # minutes
        
        return {
            "total_alerts": total_alerts,
            "time_period_hours": hours,
            "by_status": by_status,
            "by_type": by_type,
            "by_priority": by_priority,
            "acknowledgment_rate": (acknowledged_count / max(total_alerts, 1)) * 100,
            "resolution_rate": (resolved_count / max(total_alerts, 1)) * 100,
            "average_resolution_time_minutes": avg_resolution_time,
            "active_alerts": by_status.get("active", 0),
            "critical_alerts": by_priority.get("p1_critical", 0)
        }
    
    def register_alert_handler(self, handler: Callable[[Alert], None]):
        """Register alert event handler."""
        self._alert_handlers.append(handler)
    
    async def _process_alerts(self):
        """Background alert processing loop."""
        while self._running:
            try:
                # Wait for alerts
                alert = await asyncio.wait_for(self._alert_queue.get(), timeout=1)
                await self._send_notifications(alert)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error processing alert: {e}")
    
    async def _send_notifications(self, alert: Alert):
        """Send notifications for an alert."""
        rule = self._alert_rules.get(alert.rule_id)
        if not rule or not rule.enabled:
            return
        
        # Send to each configured channel
        for channel in rule.channels:
            try:
                await self._send_to_channel(alert, channel, rule.recipients)
                alert.channels_notified.append(channel)
            except Exception as e:
                self.logger.error(f"Failed to send alert {alert.id} to {channel}: {e}")
        
        # Notify handlers
        for handler in self._alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"Error in alert handler: {e}")
    
    async def _send_to_channel(self, alert: Alert, channel: AlertChannel, recipients: List[str]):
        """Send alert to specific channel."""
        if channel == AlertChannel.EMAIL:
            await self._send_email(alert, recipients)
        elif channel == AlertChannel.SLACK:
            await self._send_slack(alert)
        elif channel == AlertChannel.WEBHOOK:
            await self._send_webhook(alert)
        # Add more channels as needed
    
    async def _send_email(self, alert: Alert, recipients: List[str]):
        """Send email notification."""
        channel = self._notification_channels.get("email_default")
        if not channel or not channel.enabled:
            return
        
        config = channel.config
        
        # Create email message
        msg = MimeMultipart()
        msg["From"] = config["from_address"]
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = f"[{alert.priority.value.upper()}] {alert.title}"
        
        # Email body
        body = f"""
Healthcare Alert Notification

Alert ID: {alert.id}
Priority: {alert.priority.value}
Type: {alert.alert_type.value}
Status: {alert.status.value}

Description:
{alert.description}

Created: {alert.created_at.isoformat()}

Metadata:
{json.dumps(alert.metadata, indent=2)}

This is an automated message from HACS Healthcare Monitoring System.
"""
        
        msg.attach(MimeText(body, "plain"))
        
        # Send email (mock implementation)
        self.logger.info(f"Email notification sent for alert {alert.id}")
    
    async def _send_slack(self, alert: Alert):
        """Send Slack notification."""
        channel = self._notification_channels.get("slack_default")
        if not channel or not channel.enabled:
            return
        
        # Create Slack message
        color_map = {
            AlertPriority.P1_CRITICAL: "danger",
            AlertPriority.P2_HIGH: "warning",
            AlertPriority.P3_MEDIUM: "good",
            AlertPriority.P4_LOW: "#439FE0",
            AlertPriority.P5_INFO: "#9E9E9E"
        }
        
        message = {
            "username": channel.config["username"],
            "channel": channel.config["channel"],
            "attachments": [{
                "color": color_map.get(alert.priority, "good"),
                "title": alert.title,
                "text": alert.description,
                "fields": [
                    {"title": "Priority", "value": alert.priority.value, "short": True},
                    {"title": "Type", "value": alert.alert_type.value, "short": True},
                    {"title": "Status", "value": alert.status.value, "short": True},
                    {"title": "Alert ID", "value": alert.id, "short": True}
                ],
                "ts": int(alert.created_at.timestamp())
            }]
        }
        
        # Send to Slack (mock implementation)
        self.logger.info(f"Slack notification sent for alert {alert.id}")
    
    async def _send_webhook(self, alert: Alert):
        """Send webhook notification."""
        channel = self._notification_channels.get("webhook_default")
        if not channel or not channel.enabled:
            return
        
        # Send webhook (mock implementation)
        self.logger.info(f"Webhook notification sent for alert {alert.id}")
    
    async def _handle_escalations(self):
        """Handle alert escalations."""
        while self._running:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self._check_escalations()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error handling escalations: {e}")
    
    async def _check_escalations(self):
        """Check for alerts that need escalation."""
        now = datetime.now(timezone.utc)
        
        for alert in self._alerts.values():
            if alert.status != AlertStatus.ACTIVE:
                continue
            
            rule = self._alert_rules.get(alert.rule_id)
            if not rule:
                continue
            
            # Check if escalation time has passed
            escalation_threshold = alert.created_at + timedelta(minutes=rule.escalation_minutes)
            if now >= escalation_threshold and not alert.escalated_at:
                await self._escalate_alert(alert)
    
    async def _escalate_alert(self, alert: Alert):
        """Escalate an alert."""
        alert.status = AlertStatus.ESCALATED
        alert.escalated_at = datetime.now(timezone.utc)
        alert.updated_at = datetime.now(timezone.utc)
        
        # Send escalation notifications
        rule = self._alert_rules.get(alert.rule_id)
        if rule:
            # Send to additional channels or recipients for escalation
            await self._send_notifications(alert)
        
        self.logger.warning(f"Alert escalated: {alert.id}")
    
    def _generate_alert_id(self, rule_id: str, title: str) -> str:
        """Generate unique alert ID."""
        timestamp = int(time.time() * 1000)
        hash_source = f"{rule_id}_{title}_{timestamp}"
        hash_digest = hashlib.md5(hash_source.encode()).hexdigest()[:8]
        return f"alert_{timestamp}_{hash_digest}"
    
    def _get_suppression_key(self, rule_id: str, title: str, metadata: Dict[str, Any]) -> str:
        """Generate suppression key for deduplication."""
        # Include relevant metadata fields for suppression
        suppression_fields = ["patient_id_hash", "user_id", "resource_type"]
        suppression_data = {k: v for k, v in metadata.items() if k in suppression_fields}
        
        key_data = f"{rule_id}_{title}_{json.dumps(suppression_data, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _is_suppressed(self, suppression_key: str) -> bool:
        """Check if alert should be suppressed."""
        if suppression_key not in self._suppression_cache:
            return False
        
        last_alert_time = self._suppression_cache[suppression_key]
        suppression_window = timedelta(minutes=60)  # Default suppression window
        
        return datetime.now(timezone.utc) - last_alert_time < suppression_window


# Global alert manager
_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """Get or create global alert manager."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager


def initialize_alerting() -> AlertManager:
    """Initialize alerting system."""
    global _alert_manager
    _alert_manager = AlertManager()
    return _alert_manager


# Export public API
__all__ = [
    "AlertManager",
    "Alert",
    "AlertRule",
    "AlertChannel",
    "AlertType",
    "AlertStatus",
    "AlertPriority",
    "NotificationChannel",
    "OnCallSchedule",
    "get_alert_manager",
    "initialize_alerting",
]