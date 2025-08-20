"""HACS Tool Security Integration

This module provides security integration for HACS tools, including
permission validation, audit logging, and secure execution contexts.
"""

import logging
import os
from collections.abc import Callable
from datetime import UTC, datetime
from functools import wraps
from typing import Any

from .actor import Actor, ActorRole
from .audit import AuditEvent, AuditLevel, AuditLogger
from .permissions import PermissionManager
from .session import SessionManager


logger = logging.getLogger(__name__)


class ToolSecurityContext:
    """Security context for tool execution with permission validation and audit logging.
    """

    def __init__(
        self,
        actor: Actor,
        permission_manager: PermissionManager | None = None,
        audit_logger: AuditLogger | None = None,
        session_manager: SessionManager | None = None,
    ):
        self.actor = actor
        self.permission_manager = permission_manager or PermissionManager()
        self.audit_logger = audit_logger or AuditLogger()
        self.session_manager = session_manager or SessionManager()

        # Validate actor has active session (unless in development mode)
        dev_mode = os.getenv("HACS_DEV_MODE", "false").lower() == "true"
        if not dev_mode and not self.actor.has_active_session():
            raise ValueError(f"Actor {actor.name} must have an active session for tool execution")
        if dev_mode and not self.actor.has_active_session():
            # In dev mode, auto-start session for convenience
            logger.info(f"DEV MODE: Auto-starting session for actor {actor.name}")
            self.actor.start_session(f"dev-session-{datetime.now().timestamp()}")

    def validate_tool_permission(self, tool_name: str, required_permissions: list[str]) -> bool:
        """Validate actor has required permissions for tool execution.

        Args:
            tool_name: Name of the tool being executed
            required_permissions: List of required permission strings

        Returns:
            True if actor has all required permissions

        Raises:
            PermissionError: If actor lacks required permissions
        """
        missing_permissions = []

        for permission in required_permissions:
            if not self.actor.has_permission(permission):
                missing_permissions.append(permission)

        if missing_permissions:
            self.audit_logger.log_security_event(
                event_type="permission_denied",
                actor_id=self.actor.id,
                resource=tool_name,
                details={
                    "required_permissions": required_permissions,
                    "missing_permissions": missing_permissions,
                    "actor_permissions": self.actor.permissions,
                },
            )
            raise PermissionError(
                f"Actor {self.actor.name} missing permissions for {tool_name}: {missing_permissions}"
            )

        # Log successful permission validation
        self.audit_logger.log_access_event(
            actor_id=self.actor.id,
            resource=tool_name,
            action="tool_execution_authorized",
            success=True,
        )

        return True

    def validate_data_access_permissions(self, resource_type: str, operation: str) -> bool:
        """Validate actor has data access permissions for healthcare resources.

        Args:
            resource_type: Type of healthcare resource (Patient, Observation, etc.)
            operation: Operation type (read, write, delete)

        Returns:
            True if access is authorized

        Raises:
            PermissionError: If access is denied
        """
        required_permission = f"{operation}:{resource_type.lower()}"

        # Check specific permission first
        if self.actor.has_permission(required_permission):
            return True

        # Check wildcard permissions
        wildcard_patterns = [
            f"{operation}:*",  # Can perform operation on any resource
            f"*:{resource_type.lower()}",  # Can perform any operation on this resource
            "admin:*",  # Full admin access
        ]

        for pattern in wildcard_patterns:
            if self.actor.has_permission(pattern):
                self.audit_logger.log_access_event(
                    actor_id=self.actor.id,
                    resource=resource_type,
                    action=f"{operation}_authorized_via_{pattern}",
                    success=True,
                )
                return True

        # Access denied
        self.audit_logger.log_security_event(
            event_type="data_access_denied",
            actor_id=self.actor.id,
            resource=resource_type,
            details={
                "operation": operation,
                "required_permission": required_permission,
                "actor_permissions": self.actor.permissions,
            },
        )

        raise PermissionError(
            f"Actor {self.actor.name} not authorized for {operation} on {resource_type}"
        )

    def log_tool_execution(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        result: Any,
        execution_time_ms: float,
        success: bool = True,
        error: str | None = None,
    ) -> None:
        """Log tool execution withaudit information.

        Args:
            tool_name: Name of executed tool
            parameters: Tool execution parameters (sensitive data will be redacted)
            result: Tool execution result
            execution_time_ms: Execution time in milliseconds
            success: Whether execution was successful
            error: Error message if execution failed
        """
        # Redact sensitive parameters
        safe_parameters = self._redact_sensitive_data(parameters)

        audit_event = AuditEvent(
            timestamp=datetime.now(UTC),
            actor_id=self.actor.id,
            actor_name=self.actor.name,
            action="tool_execution",
            resource=tool_name,
            success=success,
            details={
                "tool_name": tool_name,
                "parameters": safe_parameters,
                "execution_time_ms": execution_time_ms,
                "result_summary": self._summarize_result(result),
                "session_id": self.actor.session_id,
                "actor_role": self.actor.role.value
                if hasattr(self.actor.role, "value")
                else str(self.actor.role),
                "error": error,
            },
            level=AuditLevel.INFO if success else AuditLevel.ERROR,
        )

        self.audit_logger.log_event(audit_event)

    def _redact_sensitive_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Redact sensitive information from parameters for audit logging.

        Args:
            data: Original data dictionary

        Returns:
            Data dictionary with sensitive fields redacted
        """
        sensitive_fields = {
            "password",
            "token",
            "secret",
            "key",
            "auth",
            "credential",
            "social_security_number",
            "ssn",
            "date_of_birth",
            "dob",
            "phone_number",
            "email",
            "address",
        }

        redacted_data = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                redacted_data[key] = "[REDACTED]"
            elif isinstance(value, dict):
                redacted_data[key] = self._redact_sensitive_data(value)
            elif isinstance(value, str) and len(value) > 100:
                # Truncate very long strings
                redacted_data[key] = value[:100] + "... [TRUNCATED]"
            else:
                redacted_data[key] = value

        return redacted_data

    def _summarize_result(self, result: Any) -> str:
        """Create a summary of the tool execution result for audit logging.

        Args:
            result: Tool execution result

        Returns:
            Summary string
        """
        if result is None:
            return "null"
        if isinstance(result, dict):
            if "success" in result:
                return f"success: {result['success']}, message: {result.get('message', 'N/A')}"
            return f"dict with {len(result)} keys"
        if isinstance(result, list):
            return f"list with {len(result)} items"
        if isinstance(result, str):
            return f"string: {result[:50]}..." if len(result) > 50 else f"string: {result}"
        return f"{type(result).__name__}: {str(result)[:50]}..."


def secure_tool_execution(
    required_permissions: list[str] = None,
    resource_type: str | None = None,
    operation: str | None = None,
    audit_level: AuditLevel = AuditLevel.INFO,
):
    """Decorator to secure tool execution with permission validation and audit logging.

    Args:
        required_permissions: List of required permissions for tool execution
        resource_type: Healthcare resource type for data access validation
        operation: Operation type (read, write, delete)
        audit_level: Audit logging level

    Example:
        @secure_tool_execution(
            required_permissions=["read:patient", "write:observation"],
            resource_type="Patient",
            operation="read"
        )
        def my_healthcare_tool(actor_name: str, patient_id: str, **kwargs):
            # Tool implementation
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract actor information
            actor_name = kwargs.get("actor_name") or (args[0] if args else None)
            if not actor_name:
                raise ValueError("Tool execution requires actor_name parameter")

            # Create actor instance (simplified for tool execution)
            actor = Actor(
                name=actor_name,
                role=ActorRole.AGENT,  # Default role, should be enhanced with real role lookup
                permissions=["read:*", "write:*"],  # Default permissions, should be enhanced
            )

            # Ensure actor has session
            if not actor.has_active_session():
                actor.start_session(f"tool-session-{datetime.now().timestamp()}")

            # Create security context
            security_context = ToolSecurityContext(actor)

            # Validate permissions
            if required_permissions:
                security_context.validate_tool_permission(func.__name__, required_permissions)

            if resource_type and operation:
                security_context.validate_data_access_permissions(resource_type, operation)

            # Execute tool with timing
            start_time = datetime.now()
            try:
                result = func(*args, **kwargs)
                end_time = datetime.now()
                execution_time_ms = (end_time - start_time).total_seconds() * 1000

                # Log successful execution
                security_context.log_tool_execution(
                    tool_name=func.__name__,
                    parameters=kwargs,
                    result=result,
                    execution_time_ms=execution_time_ms,
                    success=True,
                )

                return result

            except Exception as e:
                end_time = datetime.now()
                execution_time_ms = (end_time - start_time).total_seconds() * 1000

                # Log failed execution
                security_context.log_tool_execution(
                    tool_name=func.__name__,
                    parameters=kwargs,
                    result=None,
                    execution_time_ms=execution_time_ms,
                    success=False,
                    error=str(e),
                )

                raise

        return wrapper

    return decorator


def create_secure_actor(
    actor_name: str, role: ActorRole, permissions: list[str], session_duration_hours: int = 8
) -> Actor:
    """Create a secure actor with proper session management.

    Args:
        actor_name: Name of the actor
        role: Actor role
        permissions: List of permissions
        session_duration_hours: Session duration in hours

    Returns:
        Configured actor with active session
    """
    actor = Actor(name=actor_name, role=role, permissions=permissions)

    # Start secure session
    session_id = f"secure-session-{actor_name}-{datetime.now().timestamp()}"
    actor.start_session(session_id)

    logger.info(
        f"Created secure actor {actor_name} with role {role} and {len(permissions)} permissions"
    )

    return actor
