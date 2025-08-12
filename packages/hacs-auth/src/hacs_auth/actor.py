"""
Actor models for authentication, authorization, and audit trails.

This module provides actor-related models that enable secure agent interactions
with proper permission management, authentication context, and audit logging.
Optimized for LLM generation with flexible validation and smart defaults.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import Field, computed_field, field_validator
from hacs_models import BaseResource


class ActorRole(str, Enum):
    """Standard actor roles in healthcare systems."""

    PHYSICIAN = "physician"
    NURSE = "nurse"
    PHARMACIST = "pharmacist"
    THERAPIST = "therapist"
    TECHNICIAN = "technician"
    ADMINISTRATOR = "administrator"
    ADMIN = "admin"  # Added for flexibility
    PATIENT = "patient"
    CAREGIVER = "caregiver"
    AGENT = "agent"
    SYSTEM = "system"
    RESEARCHER = "researcher"
    AUDITOR = "auditor"


class PermissionLevel(str, Enum):
    """Permission levels for resource access."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    AUDIT = "audit"


class SessionStatus(str, Enum):
    """Session status values."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    LOCKED = "locked"
    TERMINATED = "terminated"


class Actor(BaseResource):
    """
    Represents an actor (human or agent) in the healthcare system.

    Actors have roles, permissions, and authentication context for secure
    interactions with healthcare data and other agents.

    LLM-Friendly Features:
    - Simplified permission system with smart defaults
    - Flexible validation that guides rather than blocks
    - Helper methods for common use cases
    - Auto-generation of basic permissions based on role
    """

    resource_type: Literal["Actor"] = Field(
        default="Actor", description="Resource type identifier"
    )

    name: str = Field(
        description="Display name of the actor",
        examples=["Dr. Sarah Johnson", "Nursing Agent v2.1", "John Doe (Patient)"],
    )

    role: ActorRole = Field(
        description="Primary role of this actor",
        examples=["physician", "agent", "patient"],
    )

    # LLM-FRIENDLY: Simplified permissions with smart defaults
    permissions: list[str] = Field(
        default_factory=list,
        description="List of permissions granted to this actor - Auto-generated based on role if not provided",
        examples=[
            ["read:patient", "write:observation", "read:encounter"],
            ["admin:system", "audit:all"],
            ["read:own_data", "write:own_data"],
        ],
    )

    # LLM-FRIENDLY: Simple permission level alternative
    permission_level: str | None = Field(
        default=None,
        description="Simple permission level (read/write/admin) - Will generate detailed permissions",
        examples=["read", "write", "admin"],
    )

    auth_context: dict[str, Any] = Field(
        default_factory=dict,
        description="Authentication and authorization context",
        examples=[
            {
                "auth_provider": "oauth2",
                "token_type": "bearer",
                "scope": ["patient:read", "observation:write"],
                "issued_at": "2024-01-15T10:30:00Z",
                "expires_at": "2024-01-15T18:30:00Z",
            }
        ],
    )

    session_id: str | None = Field(
        default=None,
        description="Current session identifier",
        examples=["sess_abc123", "session_456def", None],
    )

    session_status: SessionStatus = Field(
        default=SessionStatus.INACTIVE, description="Current session status"
    )

    last_activity: datetime | None = Field(
        default=None, description="Timestamp of last activity"
    )

    organization: str | None = Field(
        default=None,
        description="Organization this actor belongs to",
        examples=["Mayo Clinic", "Johns Hopkins", "AI Health Systems Inc."],
    )

    department: str | None = Field(
        default=None,
        description="Department within the organization",
        examples=["Cardiology", "Emergency Medicine", "AI Operations"],
    )

    contact_info: dict[str, str] = Field(
        default_factory=dict,
        description="Contact information for this actor",
        examples=[
            {
                "email": "sarah.johnson@hospital.com",
                "phone": "+1-555-0123",
                "pager": "12345",
            }
        ],
    )

    # LLM-FRIENDLY: Simple contact alternatives
    email: str | None = Field(
        default=None,
        description="Primary email address (will be added to contact_info)",
        examples=["sarah.johnson@hospital.com", "agent@hospital.com"],
    )

    phone: str | None = Field(
        default=None,
        description="Primary phone number (will be added to contact_info)",
        examples=["+1-555-0123", "555-0123"],
    )

    audit_trail: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Audit trail of significant actions",
        examples=[
            [
                {
                    "action": "login",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "ip_address": "192.168.1.100",
                    "user_agent": "Mozilla/5.0...",
                }
            ]
        ],
    )

    is_active: bool = Field(
        default=True, description="Whether this actor is currently active"
    )

    security_level: Literal["low", "medium", "high", "critical"] = Field(
        default="medium", description="Security clearance level"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure name is not empty."""
        if not v.strip():
            raise ValueError("Actor name cannot be empty")
        return v.strip()

    @field_validator("permissions")
    @classmethod
    def validate_permissions(cls, v: list[str]) -> list[str]:
        """LLM-FRIENDLY: More flexible permission validation."""
        validated_permissions = []
        for perm in v:
            if not isinstance(perm, str) or not perm.strip():
                continue

            perm = perm.strip().lower()

            # Allow simple permission formats
            if ":" not in perm:
                # Convert simple permissions to proper format
                if perm in ["read", "write", "admin", "delete", "audit"]:
                    perm = f"{perm}:*"
                else:
                    # Assume it's a resource with read permission
                    perm = f"read:{perm}"

            validated_permissions.append(perm)
        return validated_permissions

    @field_validator("auth_context")
    @classmethod
    def validate_auth_context(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Ensure auth_context is a valid dictionary."""
        if not isinstance(v, dict):
            raise ValueError("Auth context must be a dictionary")
        return v

    def model_post_init(self, __context) -> None:
        """LLM-FRIENDLY: Post-initialization processing for smart defaults."""
        super().model_post_init(__context)

        # Generate permissions based on role if not provided
        if not self.permissions and self.role:
            self.permissions = self._generate_role_permissions(self.role)

        # Generate permissions from permission_level if provided
        if self.permission_level and not self.permissions:
            self.permissions = self._generate_level_permissions(self.permission_level)

        # Add simple contact info to structured format
        if self.email and "email" not in self.contact_info:
            self.contact_info["email"] = self.email

        if self.phone and "phone" not in self.contact_info:
            self.contact_info["phone"] = self.phone

    def _generate_role_permissions(self, role: ActorRole) -> list[str]:
        """Generate default permissions based on actor role."""
        role_permissions = {
            ActorRole.PHYSICIAN: [
                "read:patient",
                "write:patient",
                "read:observation",
                "write:observation",
                "read:encounter",
                "write:encounter",
                "read:diagnosis",
                "write:diagnosis",
                "read:medication",
                "write:medication",
                "read:procedure",
                "write:procedure",
            ],
            ActorRole.NURSE: [
                "read:patient",
                "read:observation",
                "write:observation",
                "read:encounter",
                "write:encounter",
                "read:medication",
                "write:medication",
            ],
            ActorRole.PHARMACIST: [
                "read:patient",
                "read:medication",
                "write:medication",
                "read:observation",
                "read:allergy",
            ],
            ActorRole.THERAPIST: [
                "read:patient",
                "read:observation",
                "write:observation",
                "read:encounter",
                "write:encounter",
                "read:procedure",
                "write:procedure",
            ],
            ActorRole.TECHNICIAN: [
                "read:patient",
                "read:observation",
                "write:observation",
                "read:procedure",
                "write:procedure",
            ],
            ActorRole.ADMINISTRATOR: [
                "admin:*",
                "audit:*",
                "registry:read",
                "registry:write",
            ],
            ActorRole.ADMIN: ["admin:*", "audit:*", "registry:read", "registry:write"],
            ActorRole.PATIENT: ["read:own_data", "write:own_data"],
            ActorRole.CAREGIVER: ["read:patient", "read:observation", "read:encounter"],
            ActorRole.AGENT: [
                "read:patient",
                "write:patient",
                "read:observation",
                "write:observation",
                "read:encounter",
                "write:encounter",
                "read:memory",
                "write:memory",
            ],
            ActorRole.SYSTEM: ["admin:*", "audit:*"],
            ActorRole.RESEARCHER: [
                "read:patient",
                "read:observation",
                "read:encounter",
                "audit:research",
            ],
            ActorRole.AUDITOR: ["audit:*", "read:*"],
        }

        return role_permissions.get(role, ["read:basic"])

    def _generate_level_permissions(self, level: str) -> list[str]:
        """Generate permissions based on simple permission level."""
        level_permissions = {
            "read": ["read:*"],
            "write": ["read:*", "write:*"],
            "admin": ["admin:*", "audit:*"],
            "full": ["admin:*", "audit:*", "read:*", "write:*", "delete:*"],
        }

        return level_permissions.get(level.lower(), ["read:basic"])

    @computed_field
    @property
    def is_authenticated(self) -> bool:
        """Check if actor has valid authentication."""
        if not self.auth_context:
            return False

        # Check if token is expired
        expires_at = self.auth_context.get("expires_at")
        if expires_at:
            try:
                expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                if datetime.now(timezone.utc) > expiry:
                    return False
            except (ValueError, TypeError):
                return False

        return self.session_status == SessionStatus.ACTIVE

    @computed_field
    @property
    def permission_summary(self) -> dict[str, list[str]]:
        """Group permissions by action type."""
        summary = {}
        for perm in self.permissions:
            if ":" in perm:
                action, resource = perm.split(":", 1)
                if action not in summary:
                    summary[action] = []
                summary[action].append(resource)
        return summary

    @computed_field
    @property
    def display_role(self) -> str:
        """LLM-FRIENDLY: Human-readable role name."""
        role_names = {
            "physician": "Physician",
            "nurse": "Nurse",
            "pharmacist": "Pharmacist",
            "therapist": "Therapist",
            "technician": "Technician",
            "administrator": "Administrator",
            "patient": "Patient",
            "caregiver": "Caregiver",
            "agent": "AI Agent",
            "system": "System",
            "researcher": "Researcher",
            "auditor": "Auditor",
        }
        return role_names.get(self.role, self.role.title())

    # LLM-FRIENDLY: Helper methods for common use cases
    def has_permission(self, permission: str) -> bool:
        """
        Check if actor has a specific permission.

        Args:
            permission: Permission to check (format: "action:resource")

        Returns:
            True if actor has the permission
        """
        if not self.is_active or not self.is_authenticated:
            return False

        permission = permission.lower().strip()

        # Check exact permission
        if permission in self.permissions:
            return True

        # Check for wildcard permissions
        if ":" in permission:
            action, resource = permission.split(":", 1)

            # Check for action:* (all resources for this action)
            if f"{action}:*" in self.permissions:
                return True

            # Check for admin permissions
            if "admin:*" in self.permissions or "admin:all" in self.permissions:
                return True

        return False

    def add_permission(self, permission: str) -> None:
        """
        Add a permission to this actor.

        Args:
            permission: Permission to add (format: "action:resource" or simple format)
        """
        permission = permission.lower().strip()

        # Convert simple permission to proper format if needed
        if ":" not in permission:
            if permission in ["read", "write", "admin", "delete", "audit"]:
                permission = f"{permission}:*"
            else:
                permission = f"read:{permission}"

        if permission not in self.permissions:
            self.permissions.append(permission)
            self.update_timestamp()
            self._log_audit_event("permission_added", {"permission": permission})

    def remove_permission(self, permission: str) -> bool:
        """
        Remove a permission from this actor.

        Args:
            permission: Permission to remove

        Returns:
            True if permission was removed, False if not found
        """
        permission = permission.lower().strip()

        # Handle simple permission format
        if ":" not in permission:
            if permission in ["read", "write", "admin", "delete", "audit"]:
                permission = f"{permission}:*"
            else:
                permission = f"read:{permission}"

        if permission in self.permissions:
            self.permissions.remove(permission)
            self.update_timestamp()
            self._log_audit_event("permission_removed", {"permission": permission})
            return True
        return False

    def set_permission_level(self, level: str) -> None:
        """
        LLM-FRIENDLY: Set permissions using simple level.

        Args:
            level: Permission level (read/write/admin/full)
        """
        self.permissions = self._generate_level_permissions(level)
        self.permission_level = level
        self.update_timestamp()
        self._log_audit_event("permission_level_changed", {"level": level})

    def update_auth_context(self, key: str, value: Any) -> None:
        """
        Update authentication context.

        Args:
            key: Context key
            value: Context value
        """
        self.auth_context[key] = value
        self.update_timestamp()

    def start_session(self, session_id: str, **context) -> None:
        """
        Start a new session for this actor.

        Args:
            session_id: Unique session identifier
            **context: Additional session context
        """
        self.session_id = session_id
        self.session_status = SessionStatus.ACTIVE
        self.last_activity = datetime.now(timezone.utc)

        # Update auth context with session info - ensure at least session_id is in context
        self.auth_context["session_id"] = session_id
        self.auth_context["session_started"] = datetime.now(timezone.utc).isoformat()

        for key, value in context.items():
            self.auth_context[key] = value

        self.update_timestamp()
        self._log_audit_event("session_started", {"session_id": session_id, **context})

    def end_session(self, reason: str = "user_logout") -> None:
        """
        End the current session.

        Args:
            reason: Reason for ending the session
        """
        old_session_id = self.session_id
        self.session_id = None
        self.session_status = SessionStatus.TERMINATED
        self.update_timestamp()

        self._log_audit_event(
            "session_ended", {"session_id": old_session_id, "reason": reason}
        )

    def update_activity(self) -> None:
        """Update the last activity timestamp."""
        self.last_activity = datetime.now(timezone.utc)
        self.update_timestamp()

    def deactivate(self, reason: str = "administrative") -> None:
        """
        Deactivate this actor.

        Args:
            reason: Reason for deactivation
        """
        self.is_active = False
        if self.session_id:
            self.end_session(f"deactivated: {reason}")
        self.update_timestamp()

        self._log_audit_event("actor_deactivated", {"reason": reason})

    def activate(self, reason: str = "administrative") -> None:
        """
        Activate this actor.

        Args:
            reason: Reason for activation
        """
        self.is_active = True
        self.update_timestamp()

        self._log_audit_event("actor_activated", {"reason": reason})

    def _log_audit_event(self, action: str, details: dict[str, Any]) -> None:
        """
        Log an audit event.

        Args:
            action: Action that occurred
            details: Additional details about the action
        """
        audit_entry = {
            "action": action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor_id": self.id,
            "details": details,
        }
        self.audit_trail.append(audit_entry)

    def get_audit_events(
        self, action_filter: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        Get audit events for this actor.

        Args:
            action_filter: Filter by specific action type
            limit: Maximum number of events to return

        Returns:
            List of audit events
        """
        events = self.audit_trail

        if action_filter:
            events = [e for e in events if e.get("action") == action_filter]

        # Return most recent events first
        return sorted(events, key=lambda x: x.get("timestamp", ""), reverse=True)[
            :limit
        ]

    def is_session_expired(self, timeout_minutes: int = 480) -> bool:
        """
        Check if the current session has expired.

        Args:
            timeout_minutes: Session timeout in minutes (default 8 hours)

        Returns:
            True if session is expired
        """
        if not self.last_activity or self.session_status != SessionStatus.ACTIVE:
            return True

        timeout_threshold = datetime.now(timezone.utc).timestamp() - (
            timeout_minutes * 60
        )
        last_activity_timestamp = self.last_activity.timestamp()

        return last_activity_timestamp < timeout_threshold

    def __repr__(self) -> str:
        """Enhanced representation including role and status."""
        status = "active" if self.is_active else "inactive"
        auth_status = "authenticated" if self.is_authenticated else "unauthenticated"
        return f"Actor(id='{self.id}', name='{self.name}', role='{self.display_role}', status='{status}', auth='{auth_status}')"