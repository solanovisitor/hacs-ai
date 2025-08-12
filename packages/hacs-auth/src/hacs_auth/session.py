"""
Session management for HACS authentication system.

This module provides comprehensive session management with healthcare-specific
security requirements, including session expiration, activity tracking,
and multi-factor authentication support.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from .actor import Actor, SessionStatus


class SessionConfig(BaseModel):
    """Configuration for session management."""
    
    default_timeout_minutes: int = Field(
        default=480,  # 8 hours
        description="Default session timeout in minutes"
    )
    
    max_timeout_minutes: int = Field(
        default=1440,  # 24 hours
        description="Maximum allowed session timeout"
    )
    
    idle_timeout_minutes: int = Field(
        default=30,
        description="Idle timeout before warning"
    )
    
    require_activity_tracking: bool = Field(
        default=True,
        description="Whether to track user activity"
    )
    
    max_concurrent_sessions: int = Field(
        default=3,
        description="Maximum concurrent sessions per user"
    )
    
    enable_session_notifications: bool = Field(
        default=True,
        description="Enable session-related notifications"
    )
    
    secure_cookies: bool = Field(
        default=True,
        description="Require secure cookies for session management"
    )


class Session(BaseModel):
    """
    Represents an active user session with healthcare security features.
    """
    
    session_id: str = Field(
        default_factory=lambda: f"sess_{uuid.uuid4().hex[:16]}",
        description="Unique session identifier"
    )
    
    user_id: str = Field(..., description="User ID associated with session")
    actor_id: Optional[str] = Field(None, description="Actor ID if different from user")
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Session creation timestamp"
    )
    
    last_activity: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last activity timestamp"
    )
    
    expires_at: datetime = Field(..., description="Session expiration timestamp")
    
    status: SessionStatus = Field(
        default=SessionStatus.ACTIVE,
        description="Current session status"
    )
    
    # Authentication context
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    device_fingerprint: Optional[str] = Field(None, description="Device fingerprint")
    
    # Healthcare-specific context
    organization: Optional[str] = Field(None, description="Healthcare organization")
    department: Optional[str] = Field(None, description="Department context")
    location: Optional[str] = Field(None, description="Physical location")
    
    # Security features
    mfa_verified: bool = Field(default=False, description="Multi-factor authentication status")
    security_level: str = Field(default="medium", description="Session security level")
    requires_reauth: bool = Field(default=False, description="Whether session requires re-authentication")
    
    # Session metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional session metadata"
    )
    
    # Activity tracking
    activity_count: int = Field(default=0, description="Number of activities in session")
    last_ip_change: Optional[datetime] = Field(None, description="Last IP address change")
    
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.now(timezone.utc) >= self.expires_at
    
    def is_idle(self, idle_timeout_minutes: int = 30) -> bool:
        """Check if session is idle."""
        idle_threshold = datetime.now(timezone.utc) - timedelta(minutes=idle_timeout_minutes)
        return self.last_activity <= idle_threshold
    
    def time_until_expiry(self) -> timedelta:
        """Get time until session expires."""
        return self.expires_at - datetime.now(timezone.utc)
    
    def time_since_activity(self) -> timedelta:
        """Get time since last activity."""
        return datetime.now(timezone.utc) - self.last_activity
    
    def update_activity(self, ip_address: Optional[str] = None) -> None:
        """Update session activity timestamp."""
        now = datetime.now(timezone.utc)
        self.last_activity = now
        self.activity_count += 1
        
        # Track IP changes for security
        if ip_address and ip_address != self.ip_address:
            self.last_ip_change = now
            self.ip_address = ip_address
    
    def extend_session(self, minutes: int) -> None:
        """Extend session expiration."""
        self.expires_at = max(
            self.expires_at,
            datetime.now(timezone.utc) + timedelta(minutes=minutes)
        )
    
    def terminate(self, reason: str = "user_logout") -> None:
        """Terminate session."""
        self.status = SessionStatus.TERMINATED
        self.metadata["termination_reason"] = reason
        self.metadata["terminated_at"] = datetime.now(timezone.utc).isoformat()
    
    def lock(self, reason: str = "security_violation") -> None:
        """Lock session."""
        self.status = SessionStatus.LOCKED
        self.metadata["lock_reason"] = reason
        self.metadata["locked_at"] = datetime.now(timezone.utc).isoformat()
    
    def unlock(self, reason: str = "administrative") -> None:
        """Unlock session."""
        if self.status == SessionStatus.LOCKED:
            self.status = SessionStatus.ACTIVE
            self.metadata["unlock_reason"] = reason
            self.metadata["unlocked_at"] = datetime.now(timezone.utc).isoformat()


class SessionManager:
    """
    Manages user sessions with healthcare security requirements.
    """
    
    def __init__(self, config: Optional[SessionConfig] = None):
        """
        Initialize session manager.
        
        Args:
            config: Session configuration
        """
        self.config = config or SessionConfig()
        self._sessions: Dict[str, Session] = {}
        self._user_sessions: Dict[str, list[str]] = {}
    
    def create_session(
        self,
        user_id: str,
        actor: Optional[Actor] = None,
        timeout_minutes: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        organization: Optional[str] = None,
        department: Optional[str] = None,
        **metadata
    ) -> Session:
        """
        Create a new session.
        
        Args:
            user_id: User identifier
            actor: Actor instance if available
            timeout_minutes: Custom timeout (uses default if None)
            ip_address: Client IP address
            user_agent: Client user agent
            organization: Healthcare organization
            department: Department context
            **metadata: Additional session metadata
            
        Returns:
            New session instance
            
        Raises:
            ValueError: If user has too many concurrent sessions
        """
        # Check concurrent session limit
        user_sessions = self._user_sessions.get(user_id, [])
        active_sessions = [
            s for s in user_sessions 
            if s in self._sessions and self._sessions[s].status == SessionStatus.ACTIVE
        ]
        
        if len(active_sessions) >= self.config.max_concurrent_sessions:
            raise ValueError(f"User {user_id} has too many concurrent sessions")
        
        # Determine timeout
        timeout = timeout_minutes or self.config.default_timeout_minutes
        timeout = min(timeout, self.config.max_timeout_minutes)
        
        # Create session
        session = Session(
            user_id=user_id,
            actor_id=actor.id if actor else None,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=timeout),
            ip_address=ip_address,
            user_agent=user_agent,
            organization=organization or (actor.organization if actor else None),
            department=department or (actor.department if actor else None),
            security_level=actor.security_level if actor else "medium",
            metadata=metadata
        )
        
        # Store session
        self._sessions[session.session_id] = session
        
        # Track user sessions
        if user_id not in self._user_sessions:
            self._user_sessions[user_id] = []
        self._user_sessions[user_id].append(session.session_id)
        
        # Update actor if provided
        if actor:
            actor.start_session(
                session.session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                organization=organization,
                department=department
            )
        
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session if found, None otherwise
        """
        session = self._sessions.get(session_id)
        
        # Clean up expired sessions
        if session and session.is_expired():
            session.status = SessionStatus.EXPIRED
        
        return session
    
    def validate_session(self, session_id: str) -> bool:
        """
        Validate session is active and not expired.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session is valid
        """
        session = self.get_session(session_id)
        return (
            session is not None and
            session.status == SessionStatus.ACTIVE and
            not session.is_expired()
        )
    
    def update_session_activity(
        self,
        session_id: str,
        ip_address: Optional[str] = None,
        extend_if_near_expiry: bool = True
    ) -> bool:
        """
        Update session activity.
        
        Args:
            session_id: Session identifier
            ip_address: Current IP address
            extend_if_near_expiry: Whether to extend session if near expiry
            
        Returns:
            True if session was updated
        """
        session = self.get_session(session_id)
        if not session or session.status != SessionStatus.ACTIVE:
            return False
        
        session.update_activity(ip_address)
        
        # Auto-extend session if near expiry
        if extend_if_near_expiry:
            time_until_expiry = session.time_until_expiry()
            if time_until_expiry.total_seconds() < 300:  # Less than 5 minutes
                session.extend_session(self.config.default_timeout_minutes)
        
        return True
    
    def terminate_session(self, session_id: str, reason: str = "user_logout") -> bool:
        """
        Terminate session.
        
        Args:
            session_id: Session identifier
            reason: Termination reason
            
        Returns:
            True if session was terminated
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.terminate(reason)
        
        # Remove from active tracking
        if session.user_id in self._user_sessions:
            try:
                self._user_sessions[session.user_id].remove(session_id)
            except ValueError:
                pass
        
        return True
    
    def terminate_user_sessions(self, user_id: str, reason: str = "administrative") -> int:
        """
        Terminate all sessions for a user.
        
        Args:
            user_id: User identifier
            reason: Termination reason
            
        Returns:
            Number of sessions terminated
        """
        user_sessions = self._user_sessions.get(user_id, [])
        terminated_count = 0
        
        for session_id in user_sessions.copy():
            if self.terminate_session(session_id, reason):
                terminated_count += 1
        
        return terminated_count
    
    def lock_session(self, session_id: str, reason: str = "security_violation") -> bool:
        """
        Lock session for security reasons.
        
        Args:
            session_id: Session identifier
            reason: Lock reason
            
        Returns:
            True if session was locked
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.lock(reason)
        return True
    
    def get_user_sessions(self, user_id: str, active_only: bool = True) -> list[Session]:
        """
        Get all sessions for a user.
        
        Args:
            user_id: User identifier
            active_only: Whether to return only active sessions
            
        Returns:
            List of user sessions
        """
        session_ids = self._user_sessions.get(user_id, [])
        sessions = []
        
        for session_id in session_ids:
            session = self.get_session(session_id)
            if session:
                if not active_only or session.status == SessionStatus.ACTIVE:
                    sessions.append(session)
        
        return sessions
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired and terminated sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        cleaned_count = 0
        expired_sessions = []
        
        for session_id, session in self._sessions.items():
            if (session.is_expired() or 
                session.status in [SessionStatus.TERMINATED, SessionStatus.EXPIRED]):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            session = self._sessions.pop(session_id, None)
            if session:
                # Remove from user tracking
                if session.user_id in self._user_sessions:
                    try:
                        self._user_sessions[session.user_id].remove(session_id)
                    except ValueError:
                        pass
                cleaned_count += 1
        
        return cleaned_count
    
    def get_session_stats(self) -> Dict[str, Any]:
        """
        Get session statistics.
        
        Returns:
            Dictionary with session statistics
        """
        total_sessions = len(self._sessions)
        active_sessions = sum(
            1 for s in self._sessions.values() 
            if s.status == SessionStatus.ACTIVE and not s.is_expired()
        )
        expired_sessions = sum(
            1 for s in self._sessions.values() 
            if s.is_expired()
        )
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "expired_sessions": expired_sessions,
            "locked_sessions": sum(
                1 for s in self._sessions.values() 
                if s.status == SessionStatus.LOCKED
            ),
            "terminated_sessions": sum(
                1 for s in self._sessions.values() 
                if s.status == SessionStatus.TERMINATED
            ),
            "unique_users": len(self._user_sessions),
        }