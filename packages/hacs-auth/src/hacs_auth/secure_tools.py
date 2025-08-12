"""
HACS Secure Tool Execution - Authentication-Protected Tool Wrappers

This module provides secure wrappers for tool execution that enforce
authentication and authorization requirements for all healthcare tools.

Security Features:
    - Mandatory authentication for all tool executions
    - Role-based authorization checks
    - PHI access audit logging
    - Session validation and security level checks
    - Input validation and sanitization
    - Rate limiting and abuse detection

Author: HACS Development Team
License: MIT
Version: 1.0.0
"""

import time
import hashlib
import functools
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Union
from collections import defaultdict

from .auth_manager import AuthManager, TokenData, AuthError
from .security import HIPAAAuditLogger, SecurityLevel
from hacs_core.tool_protocols import ToolCategory


class SecurityContext:
    """Security context for tool execution."""
    
    def __init__(
        self,
        token_data: TokenData,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_data: Optional[Dict[str, Any]] = None
    ):
        """Initialize security context."""
        self.token_data = token_data
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.session_data = session_data or {}
        self.request_timestamp = datetime.now(timezone.utc)


class RateLimiter:
    """Rate limiter for preventing abuse."""
    
    def __init__(self):
        """Initialize rate limiter."""
        self.requests = defaultdict(list)  # user_id -> [timestamps]
        self.limits = {
            "per_minute": 60,
            "per_hour": 1000,
            "per_day": 10000
        }
    
    def is_allowed(self, user_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if user is within rate limits.
        
        Args:
            user_id: User identifier
            
        Returns:
            Tuple of (allowed, reason_if_denied)
        """
        now = time.time()
        user_requests = self.requests[user_id]
        
        # Clean old requests
        user_requests[:] = [req_time for req_time in user_requests if now - req_time < 86400]  # 24 hours
        
        # Check limits
        minute_requests = len([req for req in user_requests if now - req < 60])
        hour_requests = len([req for req in user_requests if now - req < 3600])
        day_requests = len(user_requests)
        
        if minute_requests >= self.limits["per_minute"]:
            return False, f"Rate limit exceeded: {minute_requests} requests per minute"
        
        if hour_requests >= self.limits["per_hour"]:
            return False, f"Rate limit exceeded: {hour_requests} requests per hour"
        
        if day_requests >= self.limits["per_day"]:
            return False, f"Rate limit exceeded: {day_requests} requests per day"
        
        # Record this request
        user_requests.append(now)
        return True, None


class SecureToolExecutor:
    """Secure executor for healthcare tools with authentication enforcement."""
    
    def __init__(
        self,
        auth_manager: Optional[AuthManager] = None,
        audit_logger: Optional[HIPAAAuditLogger] = None,
        rate_limiter: Optional[RateLimiter] = None
    ):
        """
        Initialize secure tool executor.
        
        Args:
            auth_manager: Authentication manager instance
            audit_logger: HIPAA audit logger instance
            rate_limiter: Rate limiter instance
        """
        self.auth_manager = auth_manager or AuthManager()
        self.audit_logger = audit_logger or HIPAAAuditLogger()
        self.rate_limiter = rate_limiter or RateLimiter()
        
        # Tool permission requirements
        self.permission_requirements = {
            ToolCategory.RESOURCE_MANAGEMENT: ["read:patient", "write:patient"],
            ToolCategory.CLINICAL_WORKFLOWS: ["read:clinical", "execute:workflow"],
            ToolCategory.MEMORY_OPERATIONS: ["read:memory", "write:memory"],
            ToolCategory.VECTOR_SEARCH: ["read:data", "search:vectors"],
            ToolCategory.SCHEMA_DISCOVERY: ["read:schema"],
            ToolCategory.DEVELOPMENT_TOOLS: ["dev:tools"],
            ToolCategory.FHIR_INTEGRATION: ["read:fhir", "write:fhir"],
            ToolCategory.HEALTHCARE_ANALYTICS: ["read:analytics", "execute:analytics"],
            ToolCategory.AI_INTEGRATIONS: ["ai:integration"],
            ToolCategory.ADMIN_OPERATIONS: ["admin:*"]
        }
        
        # Security level requirements for tool categories
        self.security_level_requirements = {
            ToolCategory.RESOURCE_MANAGEMENT: SecurityLevel.RESTRICTED,
            ToolCategory.CLINICAL_WORKFLOWS: SecurityLevel.RESTRICTED,
            ToolCategory.ADMIN_OPERATIONS: SecurityLevel.TOP_SECRET,
            ToolCategory.HEALTHCARE_ANALYTICS: SecurityLevel.CONFIDENTIAL,
            ToolCategory.FHIR_INTEGRATION: SecurityLevel.RESTRICTED,
        }
    
    def require_authentication(
        self,
        category: ToolCategory,
        required_permissions: Optional[List[str]] = None,
        required_security_level: Optional[SecurityLevel] = None,
        phi_access: bool = False,
        audit_resource_type: Optional[str] = None
    ):
        """
        Decorator to enforce authentication and authorization for tools.
        
        Args:
            category: Tool category
            required_permissions: Override default permissions for category
            required_security_level: Override default security level
            phi_access: Whether tool accesses PHI data
            audit_resource_type: Resource type for audit logging
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Extract security context from kwargs (injected by framework adapter)
                security_context = kwargs.pop('_security_context', None)
                if not security_context:
                    raise AuthError("Authentication required - no security context provided")
                
                # Validate security context
                self._validate_security_context(security_context, category, required_permissions, required_security_level)
                
                # Check rate limits
                allowed, reason = self.rate_limiter.is_allowed(security_context.token_data.user_id)
                if not allowed:
                    self.audit_logger.log_security_alert(
                        alert_type="rate_limit_exceeded",
                        severity="medium",
                        description=reason,
                        user_id=security_context.token_data.user_id,
                        ip_address=security_context.ip_address
                    )
                    raise AuthError(f"Rate limit exceeded: {reason}")
                
                # Log PHI access if applicable
                if phi_access:
                    self.audit_logger.log_phi_access(
                        user_id=security_context.token_data.user_id,
                        action=f"execute:{func.__name__}",
                        resource_type=audit_resource_type or "unknown",
                        success=True,  # Will be updated if execution fails
                        ip_address=security_context.ip_address,
                        user_agent=security_context.user_agent,
                        additional_data={
                            "session_id": security_context.token_data.session_id,
                            "organization": security_context.token_data.organization,
                            "function_args": self._sanitize_args_for_audit(args, kwargs)
                        }
                    )
                
                try:
                    # Execute the tool function
                    result = func(*args, **kwargs)
                    return result
                    
                except Exception as e:
                    # Log failed execution
                    if phi_access:
                        self.audit_logger.log_phi_access(
                            user_id=security_context.token_data.user_id,
                            action=f"execute:{func.__name__}",
                            resource_type=audit_resource_type or "unknown",
                            success=False,
                            ip_address=security_context.ip_address,
                            user_agent=security_context.user_agent,
                            additional_data={
                                "error": str(e),
                                "session_id": security_context.token_data.session_id
                            }
                        )
                    raise
            
            # Mark function as requiring authentication
            wrapper._requires_auth = True
            wrapper._auth_category = category
            wrapper._auth_permissions = required_permissions or self.permission_requirements.get(category, [])
            wrapper._auth_security_level = required_security_level or self.security_level_requirements.get(category, SecurityLevel.CONFIDENTIAL)
            wrapper._phi_access = phi_access
            
            return wrapper
        return decorator
    
    def _validate_security_context(
        self,
        context: SecurityContext,
        category: ToolCategory,
        required_permissions: Optional[List[str]],
        required_security_level: Optional[SecurityLevel]
    ) -> None:
        """Validate security context for tool execution."""
        token_data = context.token_data
        
        # Check token expiration
        if self.auth_manager.is_token_expired(token_data):
            raise AuthError("Token has expired - authentication required")
        
        # Check permissions
        permissions = required_permissions or self.permission_requirements.get(category, [])
        for permission in permissions:
            if not self.auth_manager.has_permission(token_data, permission):
                self.audit_logger.log_security_alert(
                    alert_type="permission_denied",
                    severity="high",
                    description=f"Permission denied for {permission}",
                    user_id=token_data.user_id,
                    ip_address=context.ip_address,
                    additional_data={"required_permission": permission, "user_permissions": token_data.permissions}
                )
                raise AuthError(f"Permission denied: {permission} required for {category.value}")
        
        # Check security level
        req_level = required_security_level or self.security_level_requirements.get(category, SecurityLevel.CONFIDENTIAL)
        if not self.auth_manager.validate_security_level(token_data, req_level.value):
            raise AuthError(f"Insufficient security level: {req_level.value} required for {category.value}")
        
        # Additional security checks for high-risk categories
        if category in [ToolCategory.ADMIN_OPERATIONS, ToolCategory.RESOURCE_MANAGEMENT]:
            # Require recent authentication (within last 30 minutes)
            token_age = (datetime.now(timezone.utc) - token_data.issued_at).total_seconds()
            if token_age > 1800:  # 30 minutes
                raise AuthError("Recent authentication required for high-security operations")
    
    def _sanitize_args_for_audit(self, args: tuple, kwargs: dict) -> dict:
        """Sanitize function arguments for audit logging (remove sensitive data)."""
        sanitized = {}
        
        # Sanitize kwargs
        sensitive_keys = {"password", "secret", "token", "key", "ssn", "dob", "birth_date"}
        for key, value in kwargs.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, (str, int, float, bool)):
                sanitized[key] = value
            else:
                sanitized[key] = str(type(value).__name__)
        
        # Add args count
        sanitized["_args_count"] = len(args)
        
        return sanitized
    
    def validate_tool_function(self, func: Callable) -> List[str]:
        """
        Validate that a tool function has proper security configuration.
        
        Args:
            func: Tool function to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check if function requires authentication
        if not hasattr(func, '_requires_auth'):
            errors.append("Tool function does not require authentication")
        
        # Check if function has defined permissions
        if not hasattr(func, '_auth_permissions') or not func._auth_permissions:
            errors.append("Tool function has no defined permissions")
        
        # Check if function has security level
        if not hasattr(func, '_auth_security_level'):
            errors.append("Tool function has no defined security level")
        
        return errors


# Decorator shortcuts for common use cases
def require_phi_access(
    category: ToolCategory,
    resource_type: str,
    permissions: Optional[List[str]] = None
):
    """Shortcut decorator for tools that access PHI."""
    executor = SecureToolExecutor()
    return executor.require_authentication(
        category=category,
        required_permissions=permissions,
        phi_access=True,
        audit_resource_type=resource_type
    )


def require_admin_access(permissions: Optional[List[str]] = None):
    """Shortcut decorator for administrative tools."""
    executor = SecureToolExecutor()
    return executor.require_authentication(
        category=ToolCategory.ADMIN_OPERATIONS,
        required_permissions=permissions or ["admin:*"],
        required_security_level=SecurityLevel.TOP_SECRET
    )


def require_clinical_access(permissions: Optional[List[str]] = None):
    """Shortcut decorator for clinical workflow tools."""
    executor = SecureToolExecutor()
    return executor.require_authentication(
        category=ToolCategory.CLINICAL_WORKFLOWS,
        required_permissions=permissions or ["read:clinical", "execute:workflow"],
        required_security_level=SecurityLevel.RESTRICTED,
        phi_access=True,
        audit_resource_type="clinical_workflow"
    )


# Export public API
__all__ = [
    "SecurityContext",
    "SecureToolExecutor", 
    "RateLimiter",
    "require_phi_access",
    "require_admin_access",
    "require_clinical_access",
]