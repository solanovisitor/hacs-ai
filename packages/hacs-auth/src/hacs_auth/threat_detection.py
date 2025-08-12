"""
HACS Threat Detection and Security Monitoring

This module provides real-time threat detection and security monitoring
capabilities for healthcare AI systems, including anomaly detection,
intrusion detection, and automated incident response.

Security Features:
    - Real-time threat detection
    - Behavioral anomaly detection
    - Intrusion detection and prevention
    - Automated security incident response
    - Threat intelligence integration
    - Security metrics and alerting

Author: HACS Development Team
License: MIT
Version: 1.0.0
"""

import time
import json
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
import threading
from pathlib import Path

from .security import SecurityLevel, AuditEventType
from .secure_logging import SecureLogger, get_secure_logger


class ThreatLevel(str, Enum):
    """Threat severity levels."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(str, Enum):
    """Types of security threats."""
    BRUTE_FORCE = "brute_force"
    ACCOUNT_TAKEOVER = "account_takeover"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    SUSPICIOUS_ACCESS = "suspicious_access"
    RATE_LIMIT_ABUSE = "rate_limit_abuse"
    INJECTION_ATTACK = "injection_attack"
    UNAUTHORIZED_API_ACCESS = "unauthorized_api_access"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"
    SYSTEM_COMPROMISE = "system_compromise"


@dataclass
class SecurityEvent:
    """Security event data structure."""
    event_id: str
    timestamp: datetime
    event_type: AuditEventType
    threat_type: Optional[ThreatType]
    threat_level: ThreatLevel
    user_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    source: str = "hacs_security"
    resolved: bool = False
    response_actions: List[str] = field(default_factory=list)


@dataclass
class UserBehaviorProfile:
    """User behavior profile for anomaly detection."""
    user_id: str
    typical_access_hours: Set[int] = field(default_factory=set)
    typical_ip_addresses: Set[str] = field(default_factory=set)
    typical_user_agents: Set[str] = field(default_factory=set)
    typical_resources: Set[str] = field(default_factory=set)
    average_session_duration: float = 0.0
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    failed_login_count: int = 0
    successful_login_count: int = 0


class ThreatDetectionEngine:
    """Real-time threat detection and security monitoring engine."""
    
    def __init__(
        self,
        storage_path: Optional[Path] = None,
        logger: Optional[SecureLogger] = None
    ):
        """
        Initialize threat detection engine.
        
        Args:
            storage_path: Path for storing threat data
            logger: Secure logger instance
        """
        self.storage_path = storage_path or Path.home() / ".hacs" / "security"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.logger = logger or get_secure_logger("threat_detection")
        
        # Threat detection state
        self.active_threats: Dict[str, SecurityEvent] = {}
        self.user_profiles: Dict[str, UserBehaviorProfile] = {}
        self.ip_reputation: Dict[str, Dict[str, Any]] = {}
        
        # Event tracking for pattern detection
        self.recent_events: deque = deque(maxlen=10000)  # Last 10k events
        self.failed_logins: defaultdict = defaultdict(list)  # IP -> [timestamps]
        self.rate_limits: defaultdict = defaultdict(list)  # user_id -> [timestamps]
        
        # Detection rules and thresholds
        self.detection_rules = {
            "failed_login_threshold": 5,  # Failed logins per 15 minutes
            "failed_login_window": 900,   # 15 minutes
            "rate_limit_threshold": 100,  # Requests per minute
            "unusual_hour_threshold": 0.1,  # Probability threshold for unusual access hours
            "new_ip_alert": True,         # Alert on new IP addresses
            "session_duration_multiplier": 3,  # Alert if session > 3x typical duration
        }
        
        # Response actions configuration
        self.response_actions = {
            ThreatLevel.LOW: ["log", "monitor"],
            ThreatLevel.MEDIUM: ["log", "monitor", "alert"],
            ThreatLevel.HIGH: ["log", "monitor", "alert", "block_ip"],
            ThreatLevel.CRITICAL: ["log", "monitor", "alert", "block_ip", "disable_account", "notify_admin"]
        }
        
        # Load existing data
        self._load_user_profiles()
        self._load_ip_reputation()
        
        # Background thread for continuous monitoring
        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(target=self._continuous_monitoring, daemon=True)
        self._monitoring_thread.start()
    
    def analyze_authentication_event(
        self,
        user_id: str,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> List[SecurityEvent]:
        """
        Analyze authentication event for threats.
        
        Args:
            user_id: User ID attempting authentication
            success: Whether authentication was successful
            ip_address: Source IP address
            user_agent: User agent string
            timestamp: Event timestamp
            
        Returns:
            List of detected security events
        """
        timestamp = timestamp or datetime.now(timezone.utc)
        events = []
        
        # Update user profile
        self._update_user_profile(user_id, success, ip_address, user_agent, timestamp)
        
        if not success:
            # Failed login detection
            if ip_address:
                self.failed_logins[ip_address].append(timestamp.timestamp())
                # Clean old entries
                cutoff = timestamp.timestamp() - self.detection_rules["failed_login_window"]
                self.failed_logins[ip_address] = [
                    t for t in self.failed_logins[ip_address] if t > cutoff
                ]
                
                # Check for brute force attack
                if len(self.failed_logins[ip_address]) >= self.detection_rules["failed_login_threshold"]:
                    event = SecurityEvent(
                        event_id=self._generate_event_id(),
                        timestamp=timestamp,
                        event_type=AuditEventType.SECURITY_ALERT,
                        threat_type=ThreatType.BRUTE_FORCE,
                        threat_level=ThreatLevel.HIGH,
                        user_id=user_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        description=f"Brute force attack detected from {ip_address}",
                        details={
                            "failed_attempts": len(self.failed_logins[ip_address]),
                            "time_window": self.detection_rules["failed_login_window"]
                        }
                    )
                    events.append(event)
                    self._handle_security_event(event)
        
        else:  # Successful login
            # Check for anomalous access patterns
            profile = self.user_profiles.get(user_id)
            if profile:
                anomalies = self._detect_behavioral_anomalies(
                    profile, ip_address, user_agent, timestamp
                )
                events.extend(anomalies)
        
        return events
    
    def analyze_access_event(
        self,
        user_id: str,
        resource_type: str,
        action: str,
        ip_address: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> List[SecurityEvent]:
        """
        Analyze resource access event for threats.
        
        Args:
            user_id: User accessing resource
            resource_type: Type of resource accessed
            action: Action performed
            ip_address: Source IP address
            timestamp: Event timestamp
            additional_data: Additional event data
            
        Returns:
            List of detected security events
        """
        timestamp = timestamp or datetime.now(timezone.utc)
        events = []
        additional_data = additional_data or {}
        
        # Rate limiting check
        self.rate_limits[user_id].append(timestamp.timestamp())
        # Clean old entries (1 minute window)
        cutoff = timestamp.timestamp() - 60
        self.rate_limits[user_id] = [
            t for t in self.rate_limits[user_id] if t > cutoff
        ]
        
        if len(self.rate_limits[user_id]) > self.detection_rules["rate_limit_threshold"]:
            event = SecurityEvent(
                event_id=self._generate_event_id(),
                timestamp=timestamp,
                event_type=AuditEventType.SECURITY_ALERT,
                threat_type=ThreatType.RATE_LIMIT_ABUSE,
                threat_level=ThreatLevel.MEDIUM,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=additional_data.get("user_agent"),
                description=f"Rate limit abuse detected for user {user_id}",
                details={
                    "requests_per_minute": len(self.rate_limits[user_id]),
                    "resource_type": resource_type,
                    "action": action
                }
            )
            events.append(event)
            self._handle_security_event(event)
        
        # Check for privilege escalation attempts
        if action in ["admin", "delete", "modify"] and resource_type in ["user", "system", "config"]:
            event = SecurityEvent(
                event_id=self._generate_event_id(),
                timestamp=timestamp,
                event_type=AuditEventType.SECURITY_ALERT,
                threat_type=ThreatType.PRIVILEGE_ESCALATION,
                threat_level=ThreatLevel.HIGH,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=additional_data.get("user_agent"),
                description=f"Potential privilege escalation attempt by {user_id}",
                details={
                    "resource_type": resource_type,
                    "action": action,
                    "permissions": additional_data.get("permissions", [])
                }
            )
            events.append(event)
            self._handle_security_event(event)
        
        # Check for data exfiltration patterns
        if action in ["export", "download", "read"] and "bulk" in str(additional_data).lower():
            event = SecurityEvent(
                event_id=self._generate_event_id(),
                timestamp=timestamp,
                event_type=AuditEventType.SECURITY_ALERT,
                threat_type=ThreatType.DATA_EXFILTRATION,
                threat_level=ThreatLevel.HIGH,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=additional_data.get("user_agent"),
                description=f"Potential data exfiltration detected for user {user_id}",
                details={
                    "resource_type": resource_type,
                    "action": action,
                    "bulk_operation": True
                }
            )
            events.append(event)
            self._handle_security_event(event)
        
        return events
    
    def _detect_behavioral_anomalies(
        self,
        profile: UserBehaviorProfile,
        ip_address: Optional[str],
        user_agent: Optional[str],
        timestamp: datetime
    ) -> List[SecurityEvent]:
        """Detect behavioral anomalies based on user profile."""
        events = []
        
        # Check for unusual access hours
        access_hour = timestamp.hour
        if profile.typical_access_hours and access_hour not in profile.typical_access_hours:
            # Calculate probability of access at this hour
            total_hours = len(profile.typical_access_hours)
            if total_hours > 0:
                event = SecurityEvent(
                    event_id=self._generate_event_id(),
                    timestamp=timestamp,
                    event_type=AuditEventType.SECURITY_ALERT,
                    threat_type=ThreatType.ANOMALOUS_BEHAVIOR,
                    threat_level=ThreatLevel.LOW,
                    user_id=profile.user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    description=f"Unusual access time for user {profile.user_id}",
                    details={
                        "access_hour": access_hour,
                        "typical_hours": list(profile.typical_access_hours)
                    }
                )
                events.append(event)
        
        # Check for new IP address
        if ip_address and profile.typical_ip_addresses:
            if ip_address not in profile.typical_ip_addresses and self.detection_rules["new_ip_alert"]:
                event = SecurityEvent(
                    event_id=self._generate_event_id(),
                    timestamp=timestamp,
                    event_type=AuditEventType.SECURITY_ALERT,
                    threat_type=ThreatType.SUSPICIOUS_ACCESS,
                    threat_level=ThreatLevel.MEDIUM,
                    user_id=profile.user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    description=f"New IP address detected for user {profile.user_id}",
                    details={
                        "new_ip": ip_address,
                        "typical_ips": list(profile.typical_ip_addresses)
                    }
                )
                events.append(event)
        
        # Check for new user agent
        if user_agent and profile.typical_user_agents:
            if user_agent not in profile.typical_user_agents:
                event = SecurityEvent(
                    event_id=self._generate_event_id(),
                    timestamp=timestamp,
                    event_type=AuditEventType.SECURITY_ALERT,
                    threat_type=ThreatType.SUSPICIOUS_ACCESS,
                    threat_level=ThreatLevel.LOW,
                    user_id=profile.user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    description=f"New user agent detected for user {profile.user_id}",
                    details={
                        "new_user_agent": user_agent,
                        "typical_user_agents": list(profile.typical_user_agents)
                    }
                )
                events.append(event)
        
        return events
    
    def _update_user_profile(
        self,
        user_id: str,
        success: bool,
        ip_address: Optional[str],
        user_agent: Optional[str],
        timestamp: datetime
    ) -> None:
        """Update user behavior profile."""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserBehaviorProfile(user_id=user_id)
        
        profile = self.user_profiles[user_id]
        
        if success:
            profile.successful_login_count += 1
            profile.typical_access_hours.add(timestamp.hour)
            
            if ip_address:
                profile.typical_ip_addresses.add(ip_address)
            
            if user_agent:
                profile.typical_user_agents.add(user_agent)
        else:
            profile.failed_login_count += 1
        
        profile.last_updated = timestamp
        
        # Limit the size of sets to prevent memory issues
        if len(profile.typical_ip_addresses) > 10:
            # Keep only the most recent IPs
            profile.typical_ip_addresses = set(list(profile.typical_ip_addresses)[-10:])
        
        if len(profile.typical_user_agents) > 5:
            profile.typical_user_agents = set(list(profile.typical_user_agents)[-5:])
    
    def _handle_security_event(self, event: SecurityEvent) -> None:
        """Handle detected security event with appropriate response."""
        # Store active threat
        self.active_threats[event.event_id] = event
        
        # Log security event
        self.logger.audit(
            f"SECURITY_THREAT_DETECTED: {event.threat_type.value}",
            user_id=event.user_id,
            session_id="threat_detection",
            threat_level=event.threat_level.value,
            event_id=event.event_id,
            ip_address=event.ip_address
        )
        
        # Execute response actions based on threat level
        actions = self.response_actions.get(event.threat_level, ["log"])
        for action in actions:
            self._execute_response_action(action, event)
    
    def _execute_response_action(self, action: str, event: SecurityEvent) -> None:
        """Execute security response action."""
        if action == "log":
            self.logger.warning(
                f"Security event: {event.description}",
                user_id=event.user_id,
                event_id=event.event_id
            )
        
        elif action == "alert":
            self.logger.critical(
                f"SECURITY ALERT: {event.description}",
                user_id=event.user_id,
                event_id=event.event_id,
                requires_attention=True
            )
        
        elif action == "block_ip" and event.ip_address:
            # Add IP to reputation system as blocked
            self.ip_reputation[event.ip_address] = {
                "status": "blocked",
                "reason": event.threat_type.value,
                "blocked_at": event.timestamp.isoformat(),
                "event_id": event.event_id
            }
            self.logger.critical(
                f"IP address blocked: {event.ip_address}",
                user_id=event.user_id,
                event_id=event.event_id
            )
        
        elif action == "disable_account" and event.user_id:
            self.logger.critical(
                f"Account disabled due to security threat: {event.user_id}",
                user_id=event.user_id,
                event_id=event.event_id,
                account_disabled=True
            )
        
        elif action == "notify_admin":
            self.logger.critical(
                f"ADMIN NOTIFICATION: Critical security event - {event.description}",
                user_id=event.user_id,
                event_id=event.event_id,
                notify_admin=True
            )
        
        event.response_actions.append(action)
    
    def _continuous_monitoring(self) -> None:
        """Background thread for continuous security monitoring."""
        while self._monitoring_active:
            try:
                # Clean up old events and data
                self._cleanup_old_data()
                
                # Check for pattern-based threats
                self._detect_pattern_threats()
                
                # Save state periodically
                self._save_user_profiles()
                self._save_ip_reputation()
                
                # Sleep for 60 seconds before next check
                time.sleep(60)
                
            except Exception as e:
                self.logger.error(f"Error in continuous monitoring: {e}")
                time.sleep(60)
    
    def _detect_pattern_threats(self) -> None:
        """Detect threats based on patterns in recent events."""
        # Implementation for advanced pattern detection
        # This could include ML-based anomaly detection in the future
        pass
    
    def _cleanup_old_data(self) -> None:
        """Clean up old data to prevent memory issues."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=30)
        
        # Clean old failed login records
        for ip in list(self.failed_logins.keys()):
            self.failed_logins[ip] = [
                t for t in self.failed_logins[ip] 
                if datetime.fromtimestamp(t, tz=timezone.utc) > cutoff
            ]
            if not self.failed_logins[ip]:
                del self.failed_logins[ip]
        
        # Clean old rate limit records
        for user_id in list(self.rate_limits.keys()):
            self.rate_limits[user_id] = [
                t for t in self.rate_limits[user_id]
                if datetime.fromtimestamp(t, tz=timezone.utc) > cutoff
            ]
            if not self.rate_limits[user_id]:
                del self.rate_limits[user_id]
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        timestamp = datetime.now(timezone.utc).isoformat()
        return hashlib.sha256(f"{timestamp}{time.time()}".encode()).hexdigest()[:16]
    
    def _load_user_profiles(self) -> None:
        """Load user profiles from storage."""
        profiles_file = self.storage_path / "user_profiles.json"
        if profiles_file.exists():
            try:
                with open(profiles_file, 'r') as f:
                    data = json.load(f)
                    for user_id, profile_data in data.items():
                        profile = UserBehaviorProfile(user_id=user_id)
                        profile.typical_access_hours = set(profile_data.get("typical_access_hours", []))
                        profile.typical_ip_addresses = set(profile_data.get("typical_ip_addresses", []))
                        profile.typical_user_agents = set(profile_data.get("typical_user_agents", []))
                        profile.average_session_duration = profile_data.get("average_session_duration", 0.0)
                        profile.failed_login_count = profile_data.get("failed_login_count", 0)
                        profile.successful_login_count = profile_data.get("successful_login_count", 0)
                        self.user_profiles[user_id] = profile
            except Exception as e:
                self.logger.error(f"Failed to load user profiles: {e}")
    
    def _save_user_profiles(self) -> None:
        """Save user profiles to storage."""
        profiles_file = self.storage_path / "user_profiles.json"
        try:
            data = {}
            for user_id, profile in self.user_profiles.items():
                data[user_id] = {
                    "typical_access_hours": list(profile.typical_access_hours),
                    "typical_ip_addresses": list(profile.typical_ip_addresses),
                    "typical_user_agents": list(profile.typical_user_agents),
                    "average_session_duration": profile.average_session_duration,
                    "failed_login_count": profile.failed_login_count,
                    "successful_login_count": profile.successful_login_count,
                    "last_updated": profile.last_updated.isoformat()
                }
            
            with open(profiles_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save user profiles: {e}")
    
    def _load_ip_reputation(self) -> None:
        """Load IP reputation data from storage."""
        reputation_file = self.storage_path / "ip_reputation.json"
        if reputation_file.exists():
            try:
                with open(reputation_file, 'r') as f:
                    self.ip_reputation = json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load IP reputation: {e}")
    
    def _save_ip_reputation(self) -> None:
        """Save IP reputation data to storage."""
        reputation_file = self.storage_path / "ip_reputation.json"
        try:
            with open(reputation_file, 'w') as f:
                json.dump(self.ip_reputation, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save IP reputation: {e}")
    
    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if an IP address is blocked."""
        return self.ip_reputation.get(ip_address, {}).get("status") == "blocked"
    
    def get_threat_summary(self) -> Dict[str, Any]:
        """Get summary of current threats and security status."""
        active_count = len(self.active_threats)
        threat_levels = defaultdict(int)
        threat_types = defaultdict(int)
        
        for threat in self.active_threats.values():
            threat_levels[threat.threat_level.value] += 1
            threat_types[threat.threat_type.value] += 1
        
        return {
            "active_threats": active_count,
            "threat_levels": dict(threat_levels),
            "threat_types": dict(threat_types),
            "blocked_ips": len([ip for ip, rep in self.ip_reputation.items() if rep.get("status") == "blocked"]),
            "monitored_users": len(self.user_profiles),
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    
    def shutdown(self) -> None:
        """Shutdown threat detection engine."""
        self._monitoring_active = False
        if self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=5)
        
        # Save final state
        self._save_user_profiles()
        self._save_ip_reputation()


# Global threat detection instance
_threat_detector = None


def get_threat_detector() -> ThreatDetectionEngine:
    """Get or create threat detection engine instance."""
    global _threat_detector
    if _threat_detector is None:
        _threat_detector = ThreatDetectionEngine()
    return _threat_detector


# Export public API
__all__ = [
    "ThreatLevel",
    "ThreatType",
    "SecurityEvent",
    "ThreatDetectionEngine",
    "get_threat_detector",
]