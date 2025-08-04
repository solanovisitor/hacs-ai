"""
HACS Authentication Manager

Provides OAuth2 and JWT token management for secure API access with
healthcare-specific claims and security requirements.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt
from pydantic import BaseModel, Field


class AuthConfig(BaseModel):
    """Authentication configuration with healthcare security standards."""

    jwt_secret: str = Field(..., description="JWT secret key for token signing")
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    token_expire_minutes: int = Field(default=30, description="Token expiration in minutes")
    refresh_token_expire_days: int = Field(default=7, description="Refresh token expiration in days")
    
    # OAuth2 configuration
    oauth2_client_id: Optional[str] = Field(None, description="OAuth2 client ID")
    oauth2_client_secret: Optional[str] = Field(None, description="OAuth2 client secret")
    oauth2_redirect_uri: Optional[str] = Field(None, description="OAuth2 redirect URI")
    oauth2_scope: list[str] = Field(
        default_factory=lambda: ["openid", "profile", "email"],
        description="OAuth2 requested scopes"
    )
    
    # Healthcare-specific settings
    require_mfa: bool = Field(default=False, description="Require multi-factor authentication")
    max_session_duration_hours: int = Field(default=8, description="Maximum session duration")
    audit_all_access: bool = Field(default=True, description="Audit all authentication events")
    
    # Security settings
    allowed_algorithms: list[str] = Field(
        default_factory=lambda: ["HS256", "RS256"],
        description="Allowed JWT algorithms"
    )
    require_https: bool = Field(default=True, description="Require HTTPS for token operations")
    token_leeway_seconds: int = Field(default=10, description="Clock skew tolerance in seconds")


class TokenData(BaseModel):
    """JWT token data structure with healthcare claims."""

    user_id: str = Field(..., description="Unique user identifier")
    role: str = Field(..., description="User role in healthcare system")
    permissions: list[str] = Field(..., description="List of granted permissions")
    
    # Standard JWT claims
    issued_at: datetime = Field(..., description="Token issuance timestamp")
    expires_at: datetime = Field(..., description="Token expiration timestamp")
    not_before: Optional[datetime] = Field(None, description="Token not valid before")
    
    # Healthcare-specific claims
    organization: Optional[str] = Field(None, description="Healthcare organization")
    department: Optional[str] = Field(None, description="Department within organization")
    security_level: str = Field(default="medium", description="Security clearance level")
    session_id: Optional[str] = Field(None, description="Associated session identifier")
    
    # Audit and compliance
    issuer: str = Field(default="hacs-auth", description="Token issuer")
    audience: list[str] = Field(default_factory=list, description="Intended token audience")
    subject: Optional[str] = Field(None, description="Token subject (usually user_id)")


class AuthError(Exception):
    """Authentication and authorization errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[dict[str, Any]] = None):
        """
        Initialize authentication error.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error context
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "AUTH_ERROR"
        self.details = details or {}


class AuthManager:
    """
    Manages authentication and authorization for healthcare systems.
    
    Provides comprehensive JWT token management with healthcare-specific
    claims, OAuth2 integration, and security features required for
    healthcare AI agent systems.
    """

    def __init__(self, config: Optional[AuthConfig] = None):
        """
        Initialize authentication manager.
        
        Args:
            config: Authentication configuration, uses environment defaults if None
        """
        if config is None:
            config = self._create_default_config()
        self.config = config
        self._validate_config()

    def _create_default_config(self) -> AuthConfig:
        """Create default configuration from environment variables."""
        # SECURITY FIX: Generate secure JWT secret if not provided
        jwt_secret = os.getenv("HACS_JWT_SECRET")
        if not jwt_secret:
            from .security import SecureSecretsManager
            secrets_manager = SecureSecretsManager()
            
            # Check if we have a stored secret
            if secrets_manager.secret_exists("jwt_secret"):
                jwt_secret = secrets_manager.get_secret("jwt_secret")
            else:
                # Generate and store new secure secret
                jwt_secret = secrets_manager.generate_jwt_secret()
                secrets_manager.store_secret("jwt_secret", jwt_secret)
                print("🔒 Generated new secure JWT secret and stored safely")
        
        return AuthConfig(
            jwt_secret=jwt_secret,
            jwt_algorithm=os.getenv("HACS_JWT_ALGORITHM", "HS256"),
            token_expire_minutes=int(os.getenv("HACS_TOKEN_EXPIRE_MINUTES", "15")),  # Reduced from 30 to 15 minutes
            refresh_token_expire_days=int(os.getenv("HACS_REFRESH_TOKEN_EXPIRE_DAYS", "7")),
            oauth2_client_id=os.getenv("HACS_OAUTH2_CLIENT_ID"),
            oauth2_client_secret=os.getenv("HACS_OAUTH2_CLIENT_SECRET"),
            oauth2_redirect_uri=os.getenv("HACS_OAUTH2_REDIRECT_URI"),
            require_mfa=os.getenv("HACS_REQUIRE_MFA", "true").lower() == "true",  # Changed default to true
            max_session_duration_hours=int(os.getenv("HACS_MAX_SESSION_HOURS", "4")),  # Reduced from 8 to 4 hours
            require_https=os.getenv("HACS_REQUIRE_HTTPS", "true").lower() == "true",
        )

    def _validate_config(self) -> None:
        """Validate authentication configuration with enhanced security checks."""
        # SECURITY: Validate JWT secret strength
        if not self.config.jwt_secret:
            raise AuthError("JWT secret is required for authentication")
        
        if len(self.config.jwt_secret) < 32:
            raise AuthError("JWT secret must be at least 32 characters for security")
        
        # SECURITY: Reject known weak secrets
        weak_secrets = [
            "dev-secret-change-in-production",
            "secret",
            "password",
            "change-me",
            "development-key"
        ]
        if self.config.jwt_secret in weak_secrets:
            raise AuthError("Weak or default JWT secret detected - use secure generated secret")
        
        # SECURITY: Validate algorithm
        if self.config.jwt_algorithm not in self.config.allowed_algorithms:
            raise AuthError(f"JWT algorithm {self.config.jwt_algorithm} not in allowed list")
        
        # SECURITY: Validate token expiration times
        if self.config.token_expire_minutes > 60:
            raise AuthError("Token expiration too long - maximum 60 minutes for security")
        
        if self.config.token_expire_minutes < 5:
            raise AuthError("Token expiration too short - minimum 5 minutes for usability")
        
        # SECURITY: Validate session duration
        if self.config.max_session_duration_hours > 24:
            raise AuthError("Session duration too long - maximum 24 hours")
        
        # SECURITY: Production environment checks
        if os.getenv("HACS_ENV") == "production":
            if not self.config.require_https:
                raise AuthError("HTTPS is required in production environment")
            
            if not self.config.require_mfa:
                raise AuthError("Multi-factor authentication is required in production")
            
            if self.config.token_expire_minutes > 30:
                raise AuthError("Token expiration must be ≤30 minutes in production")

    def create_access_token(
        self,
        user_id: str,
        role: str,
        permissions: list[str],
        organization: Optional[str] = None,
        department: Optional[str] = None,
        security_level: str = "medium",
        session_id: Optional[str] = None,
        audience: Optional[list[str]] = None,
    ) -> str:
        """
        Create a JWT access token with healthcare claims.
        
        Args:
            user_id: Unique user identifier
            role: User role in healthcare system
            permissions: List of granted permissions
            organization: Healthcare organization
            department: Department within organization  
            security_level: Security clearance level
            session_id: Associated session identifier
            audience: Intended token audience
            
        Returns:
            Encoded JWT token string
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self.config.token_expire_minutes)
        
        # Standard JWT claims
        payload = {
            "iss": "hacs-auth",  # Issuer
            "sub": user_id,      # Subject (user ID)
            "aud": audience or ["hacs-api"],  # Audience
            "iat": now.timestamp(),           # Issued at
            "exp": expire.timestamp(),        # Expires at
            "nbf": now.timestamp(),           # Not before
            "jti": f"jwt_{user_id}_{int(now.timestamp())}",  # JWT ID
        }
        
        # Healthcare-specific claims
        payload.update({
            "role": role,
            "permissions": permissions,
            "security_level": security_level,
        })
        
        # Optional claims
        if organization:
            payload["organization"] = organization
        if department:
            payload["department"] = department
        if session_id:
            payload["session_id"] = session_id

        # SECURITY: Enhanced JWT encoding with strict validation
        return jwt.encode(
            payload,
            self.config.jwt_secret,
            algorithm=self.config.jwt_algorithm,
            headers={"typ": "JWT", "alg": self.config.jwt_algorithm}
        )

    def verify_token(self, token: str) -> TokenData:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string to verify
            
        Returns:
            Decoded token data with healthcare claims
            
        Raises:
            AuthError: If token is invalid, expired, or malformed
        """
        try:
            # SECURITY: Enhanced JWT verification with strict validation
            payload = jwt.decode(
                token,
                self.config.jwt_secret,
                algorithms=self.config.allowed_algorithms,
                leeway=timedelta(seconds=self.config.token_leeway_seconds),
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                    "verify_aud": False,  # Application-specific audience validation
                    "require": ["exp", "iat", "sub", "jti"]  # Required claims
                }
            )

            # Extract standard claims
            user_id = payload.get("sub")
            role = payload.get("role")
            permissions = payload.get("permissions", [])
            iat = payload.get("iat")
            exp = payload.get("exp")
            nbf = payload.get("nbf")

            if not user_id:
                raise AuthError("Invalid token: missing user ID", "MISSING_USER_ID")
            if not role:
                raise AuthError("Invalid token: missing role", "MISSING_ROLE")

            # Convert timestamps to datetime objects
            issued_at = datetime.fromtimestamp(iat, tz=timezone.utc) if iat else datetime.now(timezone.utc)
            expires_at = datetime.fromtimestamp(exp, tz=timezone.utc) if exp else datetime.now(timezone.utc)
            not_before = datetime.fromtimestamp(nbf, tz=timezone.utc) if nbf else None

            return TokenData(
                user_id=user_id,
                role=role,
                permissions=permissions,
                issued_at=issued_at,
                expires_at=expires_at,
                not_before=not_before,
                organization=payload.get("organization"),
                department=payload.get("department"),
                security_level=payload.get("security_level", "medium"),
                session_id=payload.get("session_id"),
                issuer=payload.get("iss", "unknown"),
                audience=payload.get("aud", []),
                subject=payload.get("sub"),
            )

        except jwt.ExpiredSignatureError as e:
            raise AuthError("Token has expired", "TOKEN_EXPIRED") from e
        except jwt.InvalidTokenError as e:
            raise AuthError("Invalid token", "INVALID_TOKEN") from e
        except Exception as e:
            raise AuthError(f"Token verification failed: {e}", "VERIFICATION_FAILED") from e

    def create_refresh_token(self, user_id: str, session_id: Optional[str] = None) -> str:
        """
        Create a refresh token for token renewal.
        
        Args:
            user_id: User identifier
            session_id: Associated session identifier
            
        Returns:
            Refresh token string
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=self.config.refresh_token_expire_days)
        
        payload = {
            "iss": "hacs-auth",
            "sub": user_id,
            "aud": ["hacs-refresh"],
            "iat": now.timestamp(),
            "exp": expire.timestamp(),
            "token_type": "refresh",
            "jti": f"refresh_{user_id}_{int(now.timestamp())}",
        }
        
        if session_id:
            payload["session_id"] = session_id
            
        # SECURITY: Enhanced refresh token encoding
        return jwt.encode(
            payload,
            self.config.jwt_secret,
            algorithm=self.config.jwt_algorithm,
            headers={"typ": "JWT", "alg": self.config.jwt_algorithm}
        )

    def verify_refresh_token(self, refresh_token: str) -> str:
        """
        Verify refresh token and extract user ID.
        
        Args:
            refresh_token: Refresh token to verify
            
        Returns:
            User ID from refresh token
            
        Raises:
            AuthError: If refresh token is invalid
        """
        try:
            payload = jwt.decode(
                refresh_token,
                self.config.jwt_secret,
                algorithms=self.config.allowed_algorithms,
                audience=["hacs-refresh"]
            )
            
            if payload.get("token_type") != "refresh":
                raise AuthError("Invalid refresh token type", "INVALID_REFRESH_TYPE")
                
            user_id = payload.get("sub")
            if not user_id:
                raise AuthError("Invalid refresh token: missing user ID", "MISSING_USER_ID")
                
            return user_id
            
        except jwt.ExpiredSignatureError as e:
            raise AuthError("Refresh token has expired", "REFRESH_EXPIRED") from e
        except jwt.InvalidTokenError as e:
            raise AuthError("Invalid refresh token", "INVALID_REFRESH_TOKEN") from e

    def has_permission(self, token_data: TokenData, required_permission: str) -> bool:
        """
        Check if token has required permission.
        
        Args:
            token_data: Decoded token data
            required_permission: Permission to check (format: "action:resource")
            
        Returns:
            True if token has the permission
        """
        if not token_data.permissions:
            return False
            
        required_permission = required_permission.lower().strip()
        
        # Check exact permission
        if required_permission in token_data.permissions:
            return True
        
        # Check for wildcard permissions
        if ":" in required_permission:
            action, resource = required_permission.split(":", 1)
            
            # Check for action:* (all resources for this action)
            if f"{action}:*" in token_data.permissions:
                return True
                
            # Check for admin permissions
            if "admin:*" in token_data.permissions:
                return True
        
        return False

    def require_permission(self, token_data: TokenData, required_permission: str) -> None:
        """
        Require specific permission or raise error.
        
        Args:
            token_data: Decoded token data
            required_permission: Permission that is required
            
        Raises:
            AuthError: If permission is not granted
        """
        if not self.has_permission(token_data, required_permission):
            raise AuthError(
                f"Permission denied: {required_permission} required",
                "PERMISSION_DENIED",
                {"required_permission": required_permission, "user_permissions": token_data.permissions}
            )

    def is_token_expired(self, token_data: TokenData) -> bool:
        """
        Check if token is expired.
        
        Args:  
            token_data: Token data to check
            
        Returns:
            True if token is expired
        """
        return datetime.now(timezone.utc) >= token_data.expires_at

    def get_token_ttl(self, token_data: TokenData) -> int:
        """
        Get time-to-live for token in seconds.
        
        Args:
            token_data: Token data to check
            
        Returns:
            Seconds until token expires (0 if expired)
        """
        now = datetime.now(timezone.utc)
        if now >= token_data.expires_at:
            return 0
        return int((token_data.expires_at - now).total_seconds())

    def validate_security_level(self, token_data: TokenData, required_level: str) -> bool:
        """
        Validate token security level meets requirement.
        
        Args:
            token_data: Token data to check
            required_level: Required security level (low/medium/high/critical)
            
        Returns:
            True if security level is sufficient
        """
        level_hierarchy = {
            "low": 1,
            "medium": 2, 
            "high": 3,
            "critical": 4
        }
        
        token_level = level_hierarchy.get(token_data.security_level, 0)
        required_level_num = level_hierarchy.get(required_level, 0)
        
        return token_level >= required_level_num