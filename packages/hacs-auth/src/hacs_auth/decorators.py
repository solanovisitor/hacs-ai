"""
Authentication and authorization decorators for healthcare systems.

This module provides decorators to secure functions and methods with
authentication and authorization requirements, optimized for healthcare
AI agent systems.
"""

import functools
from typing import Any, Callable, Optional, TypeVar, cast

from .auth_manager import AuthManager, AuthError, TokenData
from .actor import Actor, ActorRole

# Type variable for decorated function
F = TypeVar("F", bound=Callable[..., Any])


def require_auth(
    permission: Optional[str] = None,
    role: Optional[str] = None, 
    security_level: Optional[str] = None,
    auth_manager: Optional[AuthManager] = None,
) -> Callable[[F], F]:
    """
    Decorator to require authentication and optional authorization.
    
    Args:
        permission: Required permission (format: "action:resource")
        role: Required actor role
        security_level: Required security level (low/medium/high/critical)
        auth_manager: AuthManager instance (creates default if None)
        
    Returns:
        Decorated function that enforces authentication
        
    Example:
        @require_auth(permission="read:patient", role="physician")
        def get_patient_data(patient_id: str, **kwargs):
            token_data = kwargs["token_data"]  # Added by decorator
            return {"patient_id": patient_id, "user": token_data.user_id}
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract auth manager
            manager = auth_manager or kwargs.get("auth_manager") or AuthManager()
            
            # Extract token from kwargs or context
            auth_header = kwargs.get("authorization") or kwargs.get("auth_header")
            token = kwargs.get("token") or kwargs.get("access_token")
            
            # Try to extract from Authorization header
            if not token and auth_header:
                if not auth_header.startswith("Bearer "):
                    raise AuthError(
                        "Invalid authorization header format",
                        "INVALID_AUTH_HEADER"
                    )
                token = auth_header[7:]  # Remove "Bearer " prefix
            
            if not token:
                raise AuthError(
                    "Authentication required",
                    "AUTH_REQUIRED",
                    {"required_permission": permission, "required_role": role}
                )

            # Verify token
            try:
                token_data = manager.verify_token(token)
            except AuthError:
                raise
            except Exception as e:
                raise AuthError(f"Token verification failed: {e}", "VERIFICATION_FAILED") from e

            # Check if token is expired
            if manager.is_token_expired(token_data):
                raise AuthError("Token has expired", "TOKEN_EXPIRED")

            # Check role requirement
            if role and token_data.role != role:
                raise AuthError(
                    f"Role '{role}' required, but user has role '{token_data.role}'",
                    "ROLE_REQUIRED",
                    {"required_role": role, "user_role": token_data.role}
                )

            # Check permission requirement
            if permission:
                try:
                    manager.require_permission(token_data, permission)
                except AuthError:
                    raise

            # Check security level requirement
            if security_level and not manager.validate_security_level(token_data, security_level):
                raise AuthError(
                    f"Security level '{security_level}' required",
                    "SECURITY_LEVEL_REQUIRED",
                    {
                        "required_level": security_level,
                        "user_level": token_data.security_level
                    }
                )

            # Add token data to kwargs for use in the decorated function
            kwargs["token_data"] = token_data
            kwargs["auth_manager"] = manager

            return func(*args, **kwargs)
        
        return cast(F, wrapper)
    return decorator


def require_permission(permission: str, auth_manager: Optional[AuthManager] = None) -> Callable[[F], F]:
    """
    Decorator to require specific permission.
    
    Args:
        permission: Required permission (format: "action:resource")
        auth_manager: AuthManager instance (creates default if None)
        
    Returns:
        Decorated function that enforces permission
        
    Example:
        @require_permission("write:patient")
        def update_patient(patient_id: str, data: dict, **kwargs):
            token_data = kwargs["token_data"]
            return f"Updated patient {patient_id} by {token_data.user_id}"
    """
    return require_auth(permission=permission, auth_manager=auth_manager)


def require_role(role: str, auth_manager: Optional[AuthManager] = None) -> Callable[[F], F]:
    """
    Decorator to require specific actor role.
    
    Args:
        role: Required actor role
        auth_manager: AuthManager instance (creates default if None)
        
    Returns:
        Decorated function that enforces role
        
    Example:
        @require_role("physician")
        def prescribe_medication(patient_id: str, medication: str, **kwargs):
            token_data = kwargs["token_data"]
            return f"Prescribed {medication} for patient {patient_id}"
    """
    return require_auth(role=role, auth_manager=auth_manager)


def require_security_level(
    level: str, 
    auth_manager: Optional[AuthManager] = None
) -> Callable[[F], F]:
    """
    Decorator to require minimum security level.
    
    Args:
        level: Required security level (low/medium/high/critical)
        auth_manager: AuthManager instance (creates default if None)
        
    Returns:
        Decorated function that enforces security level
        
    Example:
        @require_security_level("high")
        def access_sensitive_data(data_id: str, **kwargs):
            token_data = kwargs["token_data"]
            return f"Accessed sensitive data {data_id}"
    """
    return require_auth(security_level=level, auth_manager=auth_manager)


def require_actor_permission(permission: str) -> Callable[[F], F]:
    """
    Decorator that works with Actor instances instead of tokens.
    
    Expects the decorated function to receive an 'actor' parameter
    with an Actor instance that has the required permission.
    
    Args:
        permission: Required permission (format: "action:resource")
        
    Returns:
        Decorated function that checks actor permissions
        
    Example:
        @require_actor_permission("read:patient")
        def get_patient_info(patient_id: str, actor: Actor):
            return f"Patient {patient_id} accessed by {actor.name}"
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract actor from arguments
            actor = kwargs.get("actor")
            
            # Try to find actor in positional arguments
            if not actor:
                for arg in args:
                    if isinstance(arg, Actor):
                        actor = arg
                        break
            
            if not actor:
                raise AuthError(
                    "Actor instance required",
                    "ACTOR_REQUIRED",
                    {"required_permission": permission}
                )
            
            if not isinstance(actor, Actor):
                raise AuthError(
                    "Invalid actor instance",
                    "INVALID_ACTOR",
                    {"actor_type": type(actor).__name__}
                )
            
            # Check if actor has permission
            if not actor.has_permission(permission):
                raise AuthError(
                    f"Actor '{actor.name}' does not have permission '{permission}'",
                    "PERMISSION_DENIED",
                    {
                        "actor_id": actor.id,
                        "actor_name": actor.name,
                        "required_permission": permission,
                        "actor_permissions": actor.permissions
                    }
                )
            
            return func(*args, **kwargs)
        
        return cast(F, wrapper)
    return decorator


def require_actor_role(role: ActorRole) -> Callable[[F], F]:
    """
    Decorator that requires actor to have specific role.
    
    Args:
        role: Required actor role
        
    Returns:
        Decorated function that checks actor role
        
    Example:
        @require_actor_role(ActorRole.PHYSICIAN)
        def diagnose_patient(patient_id: str, diagnosis: str, actor: Actor):
            return f"Diagnosis by Dr. {actor.name}: {diagnosis}"
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract actor from arguments
            actor = kwargs.get("actor")
            
            # Try to find actor in positional arguments
            if not actor:
                for arg in args:
                    if isinstance(arg, Actor):
                        actor = arg
                        break
            
            if not actor:
                raise AuthError(
                    "Actor instance required",
                    "ACTOR_REQUIRED",
                    {"required_role": role}
                )
            
            if actor.role != role:
                raise AuthError(
                    f"Actor role '{role}' required, but actor has role '{actor.role}'",
                    "ROLE_REQUIRED",
                    {
                        "actor_id": actor.id,
                        "actor_name": actor.name,
                        "required_role": role,
                        "actor_role": actor.role
                    }
                )
            
            return func(*args, **kwargs)
        
        return cast(F, wrapper)
    return decorator


def audit_access(
    action: str,
    resource_type: Optional[str] = None,
    include_args: bool = False,
    include_result: bool = False,
) -> Callable[[F], F]:
    """
    Decorator to audit function access with authentication context.
    
    Args:
        action: Action being performed (e.g., "read", "write", "delete")
        resource_type: Type of resource being accessed
        include_args: Whether to include function arguments in audit log
        include_result: Whether to include function result in audit log
        
    Returns:
        Decorated function that logs access
        
    Example:
        @require_auth(permission="read:patient")
        @audit_access("read", "patient", include_args=True)
        def get_patient(patient_id: str, **kwargs):
            return {"patient_id": patient_id, "name": "John Doe"}
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract token data (should be added by auth decorator)
            token_data = kwargs.get("token_data")
            
            audit_info = {
                "function": func.__name__,
                "action": action,
                "timestamp": None,  # Will be set by audit system
                "user_id": token_data.user_id if token_data else "unknown",
                "role": token_data.role if token_data else "unknown",
            }
            
            if resource_type:
                audit_info["resource_type"] = resource_type
                
            if include_args:
                # Exclude sensitive kwargs
                safe_kwargs = {k: v for k, v in kwargs.items() 
                             if k not in ["token_data", "auth_manager", "authorization", "token"]}
                audit_info["arguments"] = {
                    "args": args,
                    "kwargs": safe_kwargs
                }
            
            try:
                result = func(*args, **kwargs)
                audit_info["status"] = "success"
                
                if include_result:
                    # Be careful not to include sensitive data
                    if isinstance(result, dict):
                        # Exclude potential sensitive keys
                        safe_result = {k: v for k, v in result.items() 
                                     if k not in ["password", "token", "secret", "key"]}
                        audit_info["result"] = safe_result
                    else:
                        audit_info["result"] = str(result)[:500]  # Limit size
                
                # In a real implementation, this would send to audit service
                # For now, we'll add it to the actor's audit trail if available
                if token_data and hasattr(token_data, "audit_trail"):
                    token_data.audit_trail.append(audit_info)
                
                return result
                
            except Exception as e:
                audit_info["status"] = "error"
                audit_info["error"] = str(e)
                
                # Log error access attempt
                if token_data and hasattr(token_data, "audit_trail"):
                    token_data.audit_trail.append(audit_info)
                
                raise
        
        return cast(F, wrapper)
    return decorator