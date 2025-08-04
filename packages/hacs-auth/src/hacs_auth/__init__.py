"""
HACS Authentication - Secure Authentication and Authorization

This package provides comprehensive authentication and authorization components
for healthcare AI agent systems, including JWT token management, OAuth2 support,
role-based access control, and audit logging.

Design Philosophy:
    - Zero-trust security model
    - Healthcare-compliant authentication
    - AI agent-optimized authorization
    - Comprehensive audit trails
    - Production-ready security

Key Features:
    - JWT token management with healthcare claims
    - OAuth2 integration for enterprise systems
    - Role-based permission system
    - Session management with expiration
    - Comprehensive audit logging
    - Healthcare-specific security levels

Author: HACS Development Team
License: MIT
Version: 0.1.0
"""

# Core authentication components
from .auth_manager import AuthManager, AuthConfig, TokenData, AuthError
from .actor import Actor, ActorRole, PermissionLevel, SessionStatus
from .permissions import PermissionManager, PermissionSchema, Permission
from .session import SessionManager, Session, SessionConfig
from .decorators import require_auth, require_permission, require_role
from .audit import AuditLogger, AuditEvent, AuditLevel

# OAuth2 support (optional)
try:
    from .oauth2 import OAuth2Config, OAuth2Manager, OAuth2Error
    _HAS_OAUTH2 = True
except ImportError:
    _HAS_OAUTH2 = False
    OAuth2Config = None
    OAuth2Manager = None  
    OAuth2Error = None

# Version info
__version__ = "0.1.0"
__author__ = "HACS Development Team"
__license__ = "MIT"

# Public API
__all__ = [
    # Core authentication
    "AuthManager",
    "AuthConfig", 
    "TokenData",
    "AuthError",
    
    # Actor and roles
    "Actor",
    "ActorRole",
    "PermissionLevel",
    "SessionStatus",
    
    # Permission management
    "PermissionManager",
    "PermissionSchema",
    "Permission",
    
    # Session management
    "SessionManager",
    "Session",
    "SessionConfig",
    
    # Decorators
    "require_auth",
    "require_permission", 
    "require_role",
    
    # Audit logging
    "AuditLogger",
    "AuditEvent",
    "AuditLevel",
    
    # OAuth2 (if available)
    "OAuth2Config",
    "OAuth2Manager",
    "OAuth2Error",
]

# Package metadata
PACKAGE_INFO = {
    "name": "hacs-auth",
    "version": __version__,
    "description": "Authentication and authorization for healthcare AI systems",
    "author": __author__,
    "license": __license__,
    "python_requires": ">=3.11",
    "dependencies": ["pydantic>=2.11.7", "pyjwt>=2.10.1", "hacs-models>=0.1.0"],
    "optional_dependencies": {
        "oauth2": ["authlib>=1.3.0", "httpx>=0.28.0"]
    },
    "homepage": "https://github.com/your-org/hacs",
    "documentation": "https://hacs.readthedocs.io/",
    "repository": "https://github.com/your-org/hacs",
}


def get_auth_components() -> dict[str, type]:
    """
    Get registry of all available authentication components.
    
    Returns:
        Dictionary mapping component names to component classes
        
    Example:
        >>> components = get_auth_components()
        >>> auth_manager = components["AuthManager"]()
    """
    components = {
        "AuthManager": AuthManager,
        "Actor": Actor,
        "PermissionManager": PermissionManager,
        "SessionManager": SessionManager,
        "AuditLogger": AuditLogger,
    }
    
    if _HAS_OAUTH2 and OAuth2Manager:
        components["OAuth2Manager"] = OAuth2Manager
        
    return components


def validate_auth_setup() -> bool:
    """
    Validate that authentication components are properly configured.
    
    Returns:
        True if all components pass validation checks
        
    Raises:
        ValueError: If configuration issues are found
    """
    try:
        # Test core components instantiation
        auth_config = AuthConfig(jwt_secret="test-secret")
        auth_manager = AuthManager(auth_config)
        
        # Test token creation and verification
        test_token = auth_manager.create_access_token(
            user_id="test-user",
            role="agent", 
            permissions=["read:patient"]
        )
        token_data = auth_manager.verify_token(test_token)
        
        if token_data.user_id != "test-user":
            raise ValueError("Token verification failed")
            
        # Test actor creation
        actor = Actor(
            name="Test Actor",
            role=ActorRole.AGENT,
            permissions=["read:patient"]
        )
        
        # Start session to enable authentication for permission checking
        actor.start_session("test-session")
        
        if not actor.has_permission("read:patient"):
            raise ValueError("Actor permission check failed")
            
        return True
        
    except Exception as e:
        raise ValueError(f"Authentication setup validation failed: {e}") from e


def get_security_info() -> dict[str, str]:
    """
    Get information about security features and compliance.
    
    Returns:
        Dictionary with security feature information
    """
    return {
        "jwt_support": "✅ JWT token management with healthcare claims",
        "oauth2_support": "✅ OAuth2 integration" if _HAS_OAUTH2 else "❌ OAuth2 not available",
        "role_based_access": "✅ Healthcare role-based permissions",
        "audit_logging": "✅ Comprehensive audit trails", 
        "session_management": "✅ Secure session handling with expiration",
        "healthcare_compliance": "✅ HIPAA-compatible security patterns",
        "ai_agent_optimized": "✅ AI agent authentication patterns",
        "production_ready": "✅ Enterprise security standards",
    }