"""
HACS Authentication Module

Provides OAuth2 and JWT token management for secure API access.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from pydantic import BaseModel, Field


class AuthConfig(BaseModel):
    """Authentication configuration."""

    jwt_secret: str = Field(..., description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    token_expire_minutes: int = Field(default=30, description="Token expiration in minutes")
    oauth2_client_id: Optional[str] = Field(None, description="OAuth2 client ID")
    oauth2_client_secret: Optional[str] = Field(None, description="OAuth2 client secret")
    oauth2_redirect_uri: Optional[str] = Field(None, description="OAuth2 redirect URI")


class TokenData(BaseModel):
    """Token data structure."""

    user_id: str
    role: str
    permissions: list[str]
    issued_at: datetime
    expires_at: datetime


class AuthError(Exception):
    """Authentication error."""
    pass


class AuthManager:
    """Manages authentication and authorization."""

    def __init__(self, config: Optional[AuthConfig] = None):
        """Initialize auth manager."""
        if config is None:
            config = AuthConfig(
                jwt_secret=os.getenv("HACS_JWT_SECRET", "dev-secret-change-in-production"),
                jwt_algorithm=os.getenv("HACS_JWT_ALGORITHM", "HS256"),
                token_expire_minutes=int(os.getenv("HACS_TOKEN_EXPIRE_MINUTES", "30")),
                oauth2_client_id=os.getenv("HACS_OAUTH2_CLIENT_ID"),
                oauth2_client_secret=os.getenv("HACS_OAUTH2_CLIENT_SECRET"),
                oauth2_redirect_uri=os.getenv("HACS_OAUTH2_REDIRECT_URI"),
            )
        self.config = config

    def create_access_token(self, user_id: str, role: str, permissions: list[str]) -> str:
        """Create a JWT access token."""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self.config.token_expire_minutes)

        payload = {
            "sub": user_id,
            "role": role,
            "permissions": permissions,
            "iat": now.timestamp(),
            "exp": expire.timestamp(),
        }

        return jwt.encode(payload, self.config.jwt_secret, algorithm=self.config.jwt_algorithm)

    def verify_token(self, token: str) -> TokenData:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(
                token, self.config.jwt_secret, algorithms=[self.config.jwt_algorithm]
            )

            user_id = payload.get("sub")
            role = payload.get("role")
            permissions = payload.get("permissions", [])
            iat = payload.get("iat")
            exp = payload.get("exp")

            if not user_id:
                raise AuthError("Invalid token: missing user ID")

            return TokenData(
                user_id=user_id,
                role=role,
                permissions=permissions,
                issued_at=datetime.fromtimestamp(iat, tz=timezone.utc),
                expires_at=datetime.fromtimestamp(exp, tz=timezone.utc),
            )
        except jwt.ExpiredSignatureError as e:
            raise AuthError("Token has expired") from e
        except jwt.InvalidTokenError as e:
            raise AuthError("Invalid token") from e

    def has_permission(self, token_data: TokenData, required_permission: str) -> bool:
        """Check if token has required permission."""
        return required_permission in token_data.permissions

    def require_permission(self, token_data: TokenData, required_permission: str) -> None:
        """Require specific permission or raise error."""
        if not self.has_permission(token_data, required_permission):
            raise AuthError(f"Permission denied: {required_permission} required")


def require_auth(permission: Optional[str] = None):
    """Decorator to require authentication and optional permission."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract token from kwargs or context
            auth_header = kwargs.get("authorization") or kwargs.get("auth_header")
            if not auth_header:
                raise AuthError("Authorization header required")

            if not auth_header.startswith("Bearer "):
                raise AuthError("Invalid authorization header format")

            token = auth_header[7:]  # Remove "Bearer " prefix

            # Get auth manager (could be passed in context)
            auth_manager = kwargs.get("auth_manager")
            if not auth_manager:
                auth_manager = AuthManager()

            # Verify token
            token_data = auth_manager.verify_token(token)

            # Check permission if required
            if permission:
                auth_manager.require_permission(token_data, permission)

            # Add token data to kwargs
            kwargs["token_data"] = token_data

            return func(*args, **kwargs)
        return wrapper
    return decorator


# Global auth manager instance
_auth_manager: Optional[AuthManager] = None


def init_auth(config: Optional[AuthConfig] = None) -> AuthManager:
    """Initialize global auth manager."""
    global _auth_manager
    _auth_manager = AuthManager(config)
    return _auth_manager


def get_auth_manager() -> AuthManager:
    """Get global auth manager."""
    if _auth_manager is None:
        return init_auth()
    return _auth_manager