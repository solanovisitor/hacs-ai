"""
HACS IAM Registry - Identity and Access Management

This module provides comprehensive identity and access management for HACS operations,
with healthcare-specific compliance rules, role-based access control, and audit trails.

Healthcare IAM Requirements:
    🏥 HIPAA compliance - minimum necessary access
    🔐 Role-based access control (RBAC)
    📋 Audit trails for all resource access
    🚫 Break-glass emergency access
    ⏰ Time-based access controls
    🔄 Delegation and supervision patterns
"""

import logging
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union, Callable
from dataclasses import dataclass, field
from contextlib import contextmanager

from pydantic import Field, BaseModel
from hacs_core import BaseResource, HealthcareDomain, AgentRole
from hacs_core.models import Patient, Organization

from .resource_registry import get_global_registry, RegisteredResource, ResourceCategory

logger = logging.getLogger(__name__)


class AccessLevel(str, Enum):
    """Levels of access to resources."""
    NONE = "none"           # No access
    READ = "read"           # View only
    WRITE = "write"         # Create/Update  
    DELETE = "delete"       # Delete operations
    ADMIN = "admin"         # Full administrative access
    EMERGENCY = "emergency" # Break-glass emergency access


class PermissionScope(str, Enum):
    """Scope of permissions."""
    GLOBAL = "global"           # System-wide access
    ORGANIZATION = "organization" # Organization-specific
    DEPARTMENT = "department"    # Department-specific
    PATIENT = "patient"         # Patient-specific
    RESOURCE_TYPE = "resource_type" # Specific resource types
    INSTANCE = "instance"       # Specific resource instances


class ComplianceRule(str, Enum):
    """Healthcare compliance rules."""
    HIPAA_MINIMUM_NECESSARY = "hipaa_minimum_necessary"
    RBAC_SEPARATION_OF_DUTIES = "rbac_separation_of_duties"
    AUDIT_ALL_ACCESS = "audit_all_access"
    EMERGENCY_ACCESS_APPROVAL = "emergency_access_approval"
    TIME_LIMITED_ACCESS = "time_limited_access"
    PHYSICIAN_SUPERVISION = "physician_supervision"
    PATIENT_CONSENT_REQUIRED = "patient_consent_required"


class AuditEventType(str, Enum):
    """Types of events to audit."""
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PERMISSION_MODIFIED = "permission_modified"
    EMERGENCY_ACCESS = "emergency_access"
    DELEGATION_GRANTED = "delegation_granted"
    COMPLIANCE_VIOLATION = "compliance_violation"
    RESOURCE_ACCESSED = "resource_accessed"
    BULK_OPERATION = "bulk_operation"


@dataclass
class ActorIdentity:
    """Identity information for an actor in the system."""
    actor_id: str
    actor_type: str  # "human", "agent", "system", "organization"
    name: str
    email: Optional[str] = None
    organization_id: Optional[str] = None
    department: Optional[str] = None
    license_number: Optional[str] = None  # For healthcare professionals
    credentials: List[str] = field(default_factory=list)
    active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_active: Optional[datetime] = None


@dataclass
class Permission:
    """A specific permission grant."""
    permission_id: str
    actor_id: str
    resource_pattern: str  # Resource identifier pattern (can use wildcards)
    access_level: AccessLevel
    scope: PermissionScope
    scope_value: Optional[str] = None  # Specific org/department/patient ID
    
    # Time constraints
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    
    # Conditions
    conditions: Dict[str, Any] = field(default_factory=dict)
    requires_supervision: bool = False
    supervisor_id: Optional[str] = None
    
    # Compliance
    compliance_rules: List[ComplianceRule] = field(default_factory=list)
    justification: Optional[str] = None
    
    # Metadata
    granted_by: str = ""
    granted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_used: Optional[datetime] = None
    use_count: int = 0


@dataclass
class AuditEntry:
    """Audit trail entry."""
    audit_id: str
    timestamp: datetime
    event_type: AuditEventType
    actor_id: str
    resource_id: Optional[str] = None
    access_level: Optional[AccessLevel] = None
    success: bool = True
    details: Dict[str, Any] = field(default_factory=dict)
    compliance_flags: List[str] = field(default_factory=list)
    session_id: Optional[str] = None
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None


class PermissionMatrix(BaseResource):
    """
    Role-based permission matrix for healthcare operations.
    
    Defines standard permissions for healthcare roles with
    HIPAA compliance and clinical workflow considerations.
    """
    
    resource_type: str = Field(default="PermissionMatrix", description="Resource type")
    
    # Matrix metadata
    matrix_id: str = Field(description="Unique matrix identifier")
    name: str = Field(description="Matrix name")
    version: str = Field(description="Matrix version")
    domain: HealthcareDomain = Field(description="Healthcare domain")
    
    # Role-based permissions
    role_permissions: Dict[str, Dict[str, AccessLevel]] = Field(
        default_factory=dict,
        description="Mapping of roles to resource permissions"
    )
    
    # Resource categories and their default access patterns
    resource_access_patterns: Dict[ResourceCategory, Dict[str, AccessLevel]] = Field(
        default_factory=dict,
        description="Default access patterns by resource category"
    )
    
    # Compliance requirements
    required_compliance: List[ComplianceRule] = Field(
        default_factory=list,
        description="Required compliance rules for this matrix"
    )
    
    # Emergency access rules
    emergency_access_roles: List[str] = Field(
        default_factory=list,
        description="Roles that can request emergency access"
    )
    
    # Supervision requirements
    supervision_matrix: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Which roles require supervision from which other roles"
    )


class HACSIAMRegistry:
    """
    Identity and Access Management Registry for HACS.
    
    Provides healthcare-compliant access control with:
    - Role-based access control (RBAC)
    - HIPAA minimum necessary principle
    - Audit trails and compliance monitoring
    - Emergency access procedures
    - Time-based access controls
    """
    
    def __init__(self):
        self._actors: Dict[str, ActorIdentity] = {}
        self._permissions: Dict[str, Permission] = {}
        self._permission_matrices: Dict[str, PermissionMatrix] = {}
        self._audit_log: List[AuditEntry] = []
        self._active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Initialize default healthcare permission matrix
        self._initialize_healthcare_matrix()
    
    def _initialize_healthcare_matrix(self):
        """Initialize standard healthcare permission matrix."""
        # Standard clinical roles and their permissions
        clinical_matrix = PermissionMatrix(
            matrix_id="clinical-standard-v1",
            name="Standard Clinical Permissions",
            version="1.0.0",
            domain=HealthcareDomain.GENERAL,
            role_permissions={
                "physician": {
                    "patient": AccessLevel.ADMIN,
                    "observation": AccessLevel.ADMIN,
                    "medication": AccessLevel.ADMIN,
                    "diagnosis": AccessLevel.ADMIN,
                    "workflow": AccessLevel.WRITE
                },
                "nurse": {
                    "patient": AccessLevel.READ,
                    "observation": AccessLevel.WRITE,
                    "medication": AccessLevel.READ,
                    "vitals": AccessLevel.WRITE,
                    "workflow": AccessLevel.READ
                },
                "clinical_assistant": {
                    "patient": AccessLevel.READ,
                    "observation": AccessLevel.READ,
                    "appointment": AccessLevel.WRITE,
                    "workflow": AccessLevel.READ
                },
                "administrator": {
                    "organization": AccessLevel.ADMIN,
                    "user_management": AccessLevel.ADMIN,
                    "audit": AccessLevel.READ,
                    "compliance": AccessLevel.ADMIN
                },
                "ai_agent": {
                    "patient": AccessLevel.READ,
                    "observation": AccessLevel.READ,
                    "clinical_guidance": AccessLevel.READ,
                    "analysis": AccessLevel.WRITE
                }
            },
            resource_access_patterns={
                ResourceCategory.CLINICAL: {
                    "physician": AccessLevel.ADMIN,
                    "nurse": AccessLevel.WRITE,
                    "clinical_assistant": AccessLevel.READ,
                    "ai_agent": AccessLevel.READ
                },
                ResourceCategory.ADMINISTRATIVE: {
                    "administrator": AccessLevel.ADMIN,
                    "physician": AccessLevel.READ,
                    "nurse": AccessLevel.READ
                },
                ResourceCategory.WORKFLOW: {
                    "physician": AccessLevel.WRITE,
                    "nurse": AccessLevel.READ,
                    "clinical_assistant": AccessLevel.READ,
                    "ai_agent": AccessLevel.READ
                }
            },
            required_compliance=[
                ComplianceRule.HIPAA_MINIMUM_NECESSARY,
                ComplianceRule.AUDIT_ALL_ACCESS,
                ComplianceRule.RBAC_SEPARATION_OF_DUTIES
            ],
            emergency_access_roles=["physician", "emergency_physician"],
            supervision_matrix={
                "resident": ["attending_physician"],
                "medical_student": ["resident", "attending_physician"],
                "nurse_practitioner": ["physician"]
            }
        )
        
        self._permission_matrices["clinical-standard-v1"] = clinical_matrix
    
    def register_actor(self, actor: ActorIdentity) -> str:
        """Register an actor in the IAM system."""
        self._actors[actor.actor_id] = actor
        
        # Audit the registration
        self._audit(
            AuditEventType.ACCESS_GRANTED,
            actor.actor_id,
            details={"action": "actor_registration", "actor_type": actor.actor_type}
        )
        
        logger.info(f"Registered actor: {actor.actor_id} ({actor.actor_type})")
        return actor.actor_id
    
    def grant_permission(
        self,
        actor_id: str,
        resource_pattern: str,
        access_level: AccessLevel,
        scope: PermissionScope = PermissionScope.GLOBAL,
        granted_by: str = "system",
        **kwargs
    ) -> Permission:
        """Grant a permission to an actor."""
        permission_id = f"perm-{actor_id}-{len(self._permissions)}"
        
        permission = Permission(
            permission_id=permission_id,
            actor_id=actor_id,
            resource_pattern=resource_pattern,
            access_level=access_level,
            scope=scope,
            granted_by=granted_by,
            **kwargs
        )
        
        self._permissions[permission_id] = permission
        
        # Audit the permission grant
        self._audit(
            AuditEventType.PERMISSION_MODIFIED,
            actor_id,
            details={
                "action": "permission_granted",
                "permission_id": permission_id,
                "resource_pattern": resource_pattern,
                "access_level": access_level.value,
                "granted_by": granted_by
            }
        )
        
        logger.info(f"Granted permission {permission_id} to {actor_id}")
        return permission
    
    def check_access(
        self,
        actor_id: str,
        resource_id: str,
        access_level: AccessLevel,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if an actor has access to a resource.
        
        Implements HIPAA minimum necessary principle and RBAC.
        """
        context = context or {}
        
        # Get actor
        actor = self._actors.get(actor_id)
        if not actor or not actor.active:
            self._audit(
                AuditEventType.ACCESS_DENIED,
                actor_id,
                resource_id=resource_id,
                access_level=access_level,
                success=False,
                details={"reason": "actor_not_found_or_inactive"}
            )
            return False
        
        # Check direct permissions
        for permission in self._permissions.values():
            if permission.actor_id == actor_id and self._matches_pattern(resource_id, permission.resource_pattern):
                if self._check_permission_validity(permission, context):
                    if self._access_level_sufficient(permission.access_level, access_level):
                        # Update usage tracking
                        permission.last_used = datetime.now(timezone.utc)
                        permission.use_count += 1
                        
                        self._audit(
                            AuditEventType.ACCESS_GRANTED,
                            actor_id,
                            resource_id=resource_id,
                            access_level=access_level,
                            details={
                                "permission_id": permission.permission_id,
                                "access_pattern": "direct_permission"
                            }
                        )
                        return True
        
        # Check role-based permissions through matrices
        for matrix in self._permission_matrices.values():
            if self._check_matrix_access(actor, resource_id, access_level, matrix, context):
                self._audit(
                    AuditEventType.ACCESS_GRANTED,
                    actor_id,
                    resource_id=resource_id,
                    access_level=access_level,
                    details={
                        "matrix_id": matrix.matrix_id,
                        "access_pattern": "role_based"
                    }
                )
                return True
        
        # Access denied
        self._audit(
            AuditEventType.ACCESS_DENIED,
            actor_id,
            resource_id=resource_id,
            access_level=access_level,
            success=False,
            details={"reason": "insufficient_permissions"}
        )
        return False
    
    def request_emergency_access(
        self,
        actor_id: str,
        resource_id: str,
        justification: str,
        emergency_type: str = "clinical"
    ) -> bool:
        """Request emergency break-glass access."""
        actor = self._actors.get(actor_id)
        if not actor:
            return False
        
        # Check if actor can request emergency access
        can_emergency = False
        for matrix in self._permission_matrices.values():
            if any(role in matrix.emergency_access_roles 
                   for role in actor.credentials):
                can_emergency = True
                break
        
        if not can_emergency:
            self._audit(
                AuditEventType.ACCESS_DENIED,
                actor_id,
                resource_id=resource_id,
                success=False,
                details={
                    "reason": "emergency_access_not_authorized",
                    "emergency_type": emergency_type
                }
            )
            return False
        
        # Grant temporary emergency permission
        emergency_permission = self.grant_permission(
            actor_id=actor_id,
            resource_pattern=resource_id,
            access_level=AccessLevel.EMERGENCY,
            scope=PermissionScope.INSTANCE,
            granted_by="emergency_system",
            justification=justification,
            valid_until=datetime.now(timezone.utc) + timedelta(hours=1),  # 1-hour emergency access
            compliance_rules=[
                ComplianceRule.EMERGENCY_ACCESS_APPROVAL,
                ComplianceRule.AUDIT_ALL_ACCESS
            ]
        )
        
        self._audit(
            AuditEventType.EMERGENCY_ACCESS,
            actor_id,
            resource_id=resource_id,
            access_level=AccessLevel.EMERGENCY,
            details={
                "justification": justification,
                "emergency_type": emergency_type,
                "permission_id": emergency_permission.permission_id,
                "valid_until": emergency_permission.valid_until.isoformat() if emergency_permission.valid_until else None
            },
            compliance_flags=["EMERGENCY_ACCESS", "REQUIRES_REVIEW"]
        )
        
        logger.warning(f"Emergency access granted to {actor_id} for {resource_id}: {justification}")
        return True
    
    def delegate_permission(
        self,
        delegator_id: str,
        delegatee_id: str,
        permission_id: str,
        duration: timedelta,
        reason: str
    ) -> Optional[Permission]:
        """Delegate a permission from one actor to another."""
        original_permission = self._permissions.get(permission_id)
        if not original_permission or original_permission.actor_id != delegator_id:
            return None
        
        # Create delegated permission
        delegated_permission = Permission(
            permission_id=f"delegated-{permission_id}-{len(self._permissions)}",
            actor_id=delegatee_id,
            resource_pattern=original_permission.resource_pattern,
            access_level=original_permission.access_level,
            scope=original_permission.scope,
            scope_value=original_permission.scope_value,
            valid_from=datetime.now(timezone.utc),
            valid_until=datetime.now(timezone.utc) + duration,
            requires_supervision=True,
            supervisor_id=delegator_id,
            compliance_rules=original_permission.compliance_rules + [ComplianceRule.PHYSICIAN_SUPERVISION],
            justification=reason,
            granted_by=delegator_id
        )
        
        self._permissions[delegated_permission.permission_id] = delegated_permission
        
        self._audit(
            AuditEventType.DELEGATION_GRANTED,
            delegator_id,
            details={
                "delegatee_id": delegatee_id,
                "original_permission_id": permission_id,
                "delegated_permission_id": delegated_permission.permission_id,
                "duration_hours": duration.total_seconds() / 3600,
                "reason": reason
            }
        )
        
        logger.info(f"Permission {permission_id} delegated from {delegator_id} to {delegatee_id}")
        return delegated_permission
    
    def get_audit_trail(
        self,
        actor_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_types: Optional[List[AuditEventType]] = None
    ) -> List[AuditEntry]:
        """Get filtered audit trail."""
        filtered_entries = []
        
        for entry in self._audit_log:
            # Apply filters
            if actor_id and entry.actor_id != actor_id:
                continue
            if resource_id and entry.resource_id != resource_id:
                continue
            if start_time and entry.timestamp < start_time:
                continue
            if end_time and entry.timestamp > end_time:
                continue
            if event_types and entry.event_type not in event_types:
                continue
            
            filtered_entries.append(entry)
        
        return sorted(filtered_entries, key=lambda x: x.timestamp, reverse=True)
    
    def check_compliance(self, actor_id: str) -> Dict[str, Any]:
        """Check compliance status for an actor."""
        actor = self._actors.get(actor_id)
        if not actor:
            return {"error": "Actor not found"}
        
        compliance_report = {
            "actor_id": actor_id,
            "compliance_status": "compliant",
            "violations": [],
            "recommendations": [],
            "last_check": datetime.now(timezone.utc).isoformat()
        }
        
        # Check for compliance violations
        recent_entries = self.get_audit_trail(
            actor_id=actor_id,
            start_time=datetime.now(timezone.utc) - timedelta(days=30)
        )
        
        # Look for patterns that might indicate violations
        emergency_accesses = [e for e in recent_entries if e.event_type == AuditEventType.EMERGENCY_ACCESS]
        if len(emergency_accesses) > 5:  # Too many emergency accesses
            compliance_report["violations"].append({
                "rule": "excessive_emergency_access",
                "description": f"Excessive emergency access requests: {len(emergency_accesses)} in 30 days",
                "severity": "medium"
            })
            compliance_report["compliance_status"] = "warning"
        
        failed_accesses = [e for e in recent_entries if not e.success]
        if len(failed_accesses) > 20:  # Many failed access attempts
            compliance_report["violations"].append({
                "rule": "excessive_failed_access",
                "description": f"High number of failed access attempts: {len(failed_accesses)}",
                "severity": "high"
            })
            compliance_report["compliance_status"] = "violation"
        
        return compliance_report
    
    def _matches_pattern(self, resource_id: str, pattern: str) -> bool:
        """Check if resource ID matches permission pattern."""
        if pattern == "*":
            return True
        if pattern == resource_id:
            return True
        # Simple wildcard matching - could be enhanced with regex
        if pattern.endswith("*") and resource_id.startswith(pattern[:-1]):
            return True
        return False
    
    def _check_permission_validity(self, permission: Permission, context: Dict[str, Any]) -> bool:
        """Check if permission is currently valid."""
        now = datetime.now(timezone.utc)
        
        # Check time constraints
        if permission.valid_from and now < permission.valid_from:
            return False
        if permission.valid_until and now > permission.valid_until:
            return False
        
        # Check supervision requirements
        if permission.requires_supervision and not context.get("supervisor_approved"):
            return False
        
        # Check conditions
        for condition, required_value in permission.conditions.items():
            if context.get(condition) != required_value:
                return False
        
        return True
    
    def _access_level_sufficient(self, granted: AccessLevel, required: AccessLevel) -> bool:
        """Check if granted access level is sufficient for required level."""
        access_hierarchy = {
            AccessLevel.NONE: 0,
            AccessLevel.READ: 1,
            AccessLevel.WRITE: 2,
            AccessLevel.DELETE: 3,
            AccessLevel.ADMIN: 4,
            AccessLevel.EMERGENCY: 5
        }
        
        return access_hierarchy.get(granted, 0) >= access_hierarchy.get(required, 0)
    
    def _check_matrix_access(
        self,
        actor: ActorIdentity,
        resource_id: str,
        access_level: AccessLevel,
        matrix: PermissionMatrix,
        context: Dict[str, Any]
    ) -> bool:
        """Check access through permission matrix."""
        # This is a simplified implementation - would need more sophisticated
        # resource type detection and role matching in a full implementation
        for role in actor.credentials:
            if role in matrix.role_permissions:
                role_perms = matrix.role_permissions[role]
                # Check if any permission pattern matches
                for resource_pattern, granted_level in role_perms.items():
                    if self._matches_pattern(resource_id, resource_pattern):
                        if self._access_level_sufficient(granted_level, access_level):
                            return True
        
        return False
    
    def _audit(
        self,
        event_type: AuditEventType,
        actor_id: str,
        resource_id: Optional[str] = None,
        access_level: Optional[AccessLevel] = None,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
        compliance_flags: Optional[List[str]] = None
    ):
        """Add entry to audit log."""
        audit_entry = AuditEntry(
            audit_id=f"audit-{len(self._audit_log)}",
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            actor_id=actor_id,
            resource_id=resource_id,
            access_level=access_level,
            success=success,
            details=details or {},
            compliance_flags=compliance_flags or []
        )
        
        self._audit_log.append(audit_entry)
        
        # Log high-priority events
        if event_type in [AuditEventType.EMERGENCY_ACCESS, AuditEventType.COMPLIANCE_VIOLATION]:
            logger.warning(f"Critical IAM event: {event_type.value} for {actor_id}")


# Global IAM registry instance
_global_iam_registry: Optional[HACSIAMRegistry] = None


def get_global_iam_registry() -> HACSIAMRegistry:
    """Get the global IAM registry instance."""
    global _global_iam_registry
    if _global_iam_registry is None:
        _global_iam_registry = HACSIAMRegistry()
    return _global_iam_registry


@contextmanager
def iam_context(actor_id: str, session_context: Optional[Dict[str, Any]] = None):
    """Context manager for IAM-controlled operations."""
    iam = get_global_iam_registry()
    session_id = f"session-{actor_id}-{datetime.now().timestamp()}"
    
    try:
        # Start session
        iam._active_sessions[session_id] = {
            "actor_id": actor_id,
            "start_time": datetime.now(timezone.utc),
            "context": session_context or {}
        }
        
        yield iam
        
    finally:
        # End session
        if session_id in iam._active_sessions:
            session_data = iam._active_sessions[session_id]
            session_data["end_time"] = datetime.now(timezone.utc)
            session_data["duration"] = (session_data["end_time"] - session_data["start_time"]).total_seconds()
            
            # Audit session end
            iam._audit(
                AuditEventType.ACCESS_GRANTED,
                actor_id,
                details={
                    "action": "session_ended",
                    "session_id": session_id,
                    "duration_seconds": session_data["duration"]
                }
            )
            
            del iam._active_sessions[session_id]


def require_permission(resource_pattern: str, access_level: AccessLevel):
    """Decorator to require specific permissions for function access."""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            # Extract actor_id from kwargs or context
            actor_id = kwargs.get("actor_id") or kwargs.get("context", {}).get("actor_id")
            if not actor_id:
                raise PermissionError("Actor ID required for permission check")
            
            # Extract resource_id from args or kwargs
            resource_id = kwargs.get("resource_id", resource_pattern)
            
            iam = get_global_iam_registry()
            if not iam.check_access(actor_id, resource_id, access_level):
                raise PermissionError(f"Access denied: {actor_id} -> {resource_id} ({access_level.value})")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


__all__ = [
    'AccessLevel',
    'PermissionScope',
    'ComplianceRule',
    'AuditEventType',
    'ActorIdentity',
    'Permission',
    'AuditEntry',
    'PermissionMatrix',
    'HACSIAMRegistry',
    'get_global_iam_registry',
    'iam_context',
    'require_permission',
]