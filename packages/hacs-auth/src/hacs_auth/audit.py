"""
Audit logging system for HACS authentication.

This module provides comprehensive audit logging for healthcare systems
with compliance features for HIPAA, SOX, and other regulatory requirements.
"""

import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AuditLevel(str, Enum):
    """Audit event severity levels."""
    
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditCategory(str, Enum):
    """Categories of audit events."""
    
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    CONFIGURATION = "configuration"
    SYSTEM = "system"
    COMPLIANCE = "compliance"
    SECURITY = "security"


class AuditEvent(BaseModel):
    """
    Represents a single audit event with healthcare compliance features.
    """
    
    event_id: str = Field(
        default_factory=lambda: f"audit_{uuid.uuid4().hex[:16]}",
        description="Unique event identifier"
    )
    
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Event timestamp in UTC"
    )
    
    level: AuditLevel = Field(..., description="Event severity level")
    category: AuditCategory = Field(..., description="Event category")
    action: str = Field(..., description="Action that was performed")
    
    # Actor information
    user_id: Optional[str] = Field(None, description="User who performed the action")
    actor_id: Optional[str] = Field(None, description="Actor ID if different from user")
    session_id: Optional[str] = Field(None, description="Session identifier")
    
    # Context information
    resource_type: Optional[str] = Field(None, description="Type of resource accessed")
    resource_id: Optional[str] = Field(None, description="Specific resource identifier")
    organization: Optional[str] = Field(None, description="Healthcare organization")
    department: Optional[str] = Field(None, description="Department context")
    
    # Technical details
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    request_id: Optional[str] = Field(None, description="Request identifier")
    
    # Event details
    message: str = Field(..., description="Human-readable event description")
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional event details"
    )
    
    # Compliance fields
    patient_id: Optional[str] = Field(None, description="Patient ID if PHI was accessed") 
    phi_accessed: bool = Field(default=False, description="Whether PHI was accessed")
    consent_verified: Optional[bool] = Field(None, description="Whether patient consent was verified")
    
    # Security fields
    success: bool = Field(default=True, description="Whether the action succeeded")
    error_code: Optional[str] = Field(None, description="Error code if action failed")
    risk_score: Optional[float] = Field(None, description="Risk score (0.0-1.0)")
    
    def to_log_format(self) -> str:
        """Convert to structured log format."""
        log_data = {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "category": self.category,
            "action": self.action,
            "message": self.message,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "success": self.success,
        }
        
        # Add non-null optional fields
        for field in ["actor_id", "resource_type", "resource_id", "organization", 
                     "department", "ip_address", "user_agent", "request_id",
                     "patient_id", "error_code", "risk_score"]:
            value = getattr(self, field)
            if value is not None:
                log_data[field] = value
        
        # Add boolean flags
        if self.phi_accessed:
            log_data["phi_accessed"] = True
        if self.consent_verified is not None:
            log_data["consent_verified"] = self.consent_verified
        
        # Add details if present
        if self.details:
            log_data["details"] = self.details
        
        return json.dumps(log_data, default=str, separators=(',', ':'))
    
    def is_security_event(self) -> bool:
        """Check if this is a security-related event."""
        return (
            self.category == AuditCategory.SECURITY or
            self.level in [AuditLevel.WARNING, AuditLevel.ERROR, AuditLevel.CRITICAL] or
            not self.success or
            (self.risk_score is not None and self.risk_score > 0.7)
        )
    
    def is_compliance_event(self) -> bool:
        """Check if this is a compliance-related event."""
        return (
            self.category == AuditCategory.COMPLIANCE or
            self.phi_accessed or
            self.patient_id is not None
        )


class AuditLogger:
    """
    Comprehensive audit logger for healthcare systems with compliance features.
    """
    
    def __init__(self, organization: Optional[str] = None, department: Optional[str] = None):
        """
        Initialize audit logger.
        
        Args:
            organization: Default organization for events
            department: Default department for events
        """
        self.default_organization = organization
        self.default_department = department
        self._events: List[AuditEvent] = []
    
    def log_event(
        self,
        level: AuditLevel,
        category: AuditCategory,
        action: str,
        message: str,
        user_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        session_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        organization: Optional[str] = None,
        department: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        phi_accessed: bool = False,
        consent_verified: Optional[bool] = None,
        success: bool = True,
        error_code: Optional[str] = None,
        risk_score: Optional[float] = None,
        **details: Any
    ) -> AuditEvent:
        """
        Log an audit event.
        
        Args:
            level: Event severity level
            category: Event category
            action: Action performed
            message: Human-readable description
            user_id: User identifier
            actor_id: Actor identifier
            session_id: Session identifier
            resource_type: Resource type accessed
            resource_id: Specific resource ID
            organization: Healthcare organization
            department: Department context
            ip_address: Client IP address
            user_agent: Client user agent
            request_id: Request identifier
            patient_id: Patient ID if PHI accessed
            phi_accessed: Whether PHI was accessed
            consent_verified: Whether consent was verified
            success: Whether action succeeded
            error_code: Error code if failed
            risk_score: Risk assessment score
            **details: Additional event details
            
        Returns:
            Created audit event
        """
        event = AuditEvent(
            level=level,
            category=category,
            action=action,
            message=message,
            user_id=user_id,
            actor_id=actor_id,
            session_id=session_id,
            resource_type=resource_type,
            resource_id=resource_id,
            organization=organization or self.default_organization,
            department=department or self.default_department,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            patient_id=patient_id,
            phi_accessed=phi_accessed,
            consent_verified=consent_verified,
            success=success,
            error_code=error_code,
            risk_score=risk_score,
            details=details
        )
        
        self._events.append(event)
        
        # In a real implementation, this would send to logging system
        print(event.to_log_format())
        
        return event
    
    # Convenience methods for common audit events
    
    def log_authentication(
        self,
        action: str,
        user_id: str,
        success: bool = True,
        ip_address: Optional[str] = None,
        error_code: Optional[str] = None,
        **details: Any
    ) -> AuditEvent:
        """Log authentication event."""
        level = AuditLevel.INFO if success else AuditLevel.WARNING
        message = f"User {user_id} {action}"
        if not success:
            message += f" failed"
            if error_code:
                message += f" ({error_code})"
        
        return self.log_event(
            level=level,
            category=AuditCategory.AUTHENTICATION,
            action=action,
            message=message,
            user_id=user_id,
            ip_address=ip_address,
            success=success,
            error_code=error_code,
            **details
        )
    
    def log_authorization(
        self,
        action: str,
        user_id: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        permission: Optional[str] = None,
        success: bool = True,
        **details: Any
    ) -> AuditEvent:
        """Log authorization event."""
        level = AuditLevel.INFO if success else AuditLevel.WARNING
        message = f"User {user_id} {action} access to {resource_type}"
        if resource_id:
            message += f" {resource_id}"
        if not success:
            message += " denied"
        
        audit_details = details.copy()
        if permission:
            audit_details["permission"] = permission
        
        return self.log_event(
            level=level,
            category=AuditCategory.AUTHORIZATION,
            action=action,
            message=message,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            success=success,
            **audit_details
        )
    
    def log_data_access(
        self,
        action: str,
        user_id: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        phi_accessed: bool = False,
        consent_verified: Optional[bool] = None,
        **details: Any
    ) -> AuditEvent:
        """Log data access event."""
        message = f"User {user_id} {action} {resource_type}"
        if resource_id:
            message += f" {resource_id}"
        if phi_accessed:
            message += " (PHI accessed)"
        
        return self.log_event(
            level=AuditLevel.INFO,
            category=AuditCategory.DATA_ACCESS,
            action=action,
            message=message,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            patient_id=patient_id,
            phi_accessed=phi_accessed,
            consent_verified=consent_verified,
            **details
        )
    
    def log_security_event(
        self,
        action: str,
        message: str,
        user_id: Optional[str] = None,
        level: AuditLevel = AuditLevel.WARNING,
        risk_score: Optional[float] = None,
        **details: Any
    ) -> AuditEvent:
        """Log security event."""
        return self.log_event(
            level=level,
            category=AuditCategory.SECURITY,
            action=action,
            message=message,
            user_id=user_id,
            risk_score=risk_score,
            success=level != AuditLevel.ERROR,
            **details
        )
    
    def log_system_event(
        self,
        action: str,
        message: str,
        level: AuditLevel = AuditLevel.INFO,
        **details: Any
    ) -> AuditEvent:
        """Log system event."""
        return self.log_event(
            level=level,
            category=AuditCategory.SYSTEM,
            action=action,
            message=message,
            **details
        )
    
    def log_configuration_change(
        self,
        action: str,
        user_id: str,
        resource_type: str,
        old_value: Any = None,
        new_value: Any = None,
        **details: Any
    ) -> AuditEvent:
        """Log configuration change."""
        message = f"User {user_id} {action} {resource_type} configuration"
        
        audit_details = details.copy()
        if old_value is not None:
            audit_details["old_value"] = old_value
        if new_value is not None:
            audit_details["new_value"] = new_value
        
        return self.log_event(
            level=AuditLevel.INFO,
            category=AuditCategory.CONFIGURATION,
            action=action,
            message=message,
            user_id=user_id,
            resource_type=resource_type,
            **audit_details
        )
    
    # Query and analysis methods
    
    def get_events(
        self,
        level: Optional[AuditLevel] = None,
        category: Optional[AuditCategory] = None,
        user_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[AuditEvent]:
        """
        Query audit events with filters.
        
        Args:
            level: Filter by severity level
            category: Filter by category
            user_id: Filter by user ID
            patient_id: Filter by patient ID
            start_time: Filter events after this time
            end_time: Filter events before this time
            limit: Maximum number of events to return
            
        Returns:
            List of matching audit events
        """
        events = self._events
        
        # Apply filters
        if level:
            events = [e for e in events if e.level == level]
        if category:
            events = [e for e in events if e.category == category]
        if user_id:
            events = [e for e in events if e.user_id == user_id]
        if patient_id:
            events = [e for e in events if e.patient_id == patient_id]
        if start_time:
            events = [e for e in events if e.timestamp >= start_time]
        if end_time:
            events = [e for e in events if e.timestamp <= end_time]
        
        # Sort by timestamp (most recent first)
        events.sort(key=lambda x: x.timestamp, reverse=True)
        
        return events[:limit]
    
    def get_security_events(self, limit: int = 100) -> List[AuditEvent]:
        """Get recent security events."""
        return [e for e in self._events if e.is_security_event()][:limit]
    
    def get_compliance_events(self, limit: int = 100) -> List[AuditEvent]:
        """Get recent compliance events."""
        return [e for e in self._events if e.is_compliance_event()][:limit]
    
    def get_user_activity(self, user_id: str, limit: int = 100) -> List[AuditEvent]:
        """Get activity for specific user."""
        return self.get_events(user_id=user_id, limit=limit)
    
    def get_patient_access(self, patient_id: str, limit: int = 100) -> List[AuditEvent]:
        """Get all access events for a patient."""
        return self.get_events(patient_id=patient_id, limit=limit)
    
    def export_events(
        self,
        events: Optional[List[AuditEvent]] = None,
        format: str = "json"
    ) -> str:
        """
        Export events in specified format.
        
        Args:
            events: Events to export (all if None)
            format: Export format ("json" or "csv")
            
        Returns:
            Exported data as string
        """
        if events is None:
            events = self._events
        
        if format == "json":
            return json.dumps([e.dict() for e in events], default=str, indent=2)
        elif format == "csv":
            if not events:
                return ""
            
            # Create CSV header
            fields = ["event_id", "timestamp", "level", "category", "action", "message", 
                     "user_id", "success", "resource_type", "patient_id", "phi_accessed"]
            csv_lines = [",".join(fields)]
            
            # Add event rows
            for event in events:
                row = [
                    event.event_id,
                    event.timestamp.isoformat(),
                    event.level,
                    event.category,
                    event.action,
                    f'"{event.message}"',  # Quote message for CSV
                    event.user_id or "",
                    str(event.success),
                    event.resource_type or "",
                    event.patient_id or "",
                    str(event.phi_accessed)
                ]
                csv_lines.append(",".join(row))
            
            return "\n".join(csv_lines)
        else:
            raise ValueError(f"Unsupported export format: {format}")