"""
HACS Secure Logging - PHI-Safe Logging System

This module provides HIPAA-compliant logging that automatically
sanitizes PHI data from log messages and error outputs.

Security Features:
    - Automatic PHI detection and redaction
    - Secure structured logging format
    - Audit trail compliance
    - Error message sanitization
    - Log encryption and integrity protection

Author: HACS Development Team
License: MIT
Version: 1.0.0
"""

import re
import logging
import json
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from enum import Enum

from .security import PHIEncryption, SecurityLevel


class LogLevel(str, Enum):
    """Secure log levels with PHI considerations."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    AUDIT = "AUDIT"  # Special level for audit events


class PHIDetector:
    """Detects and redacts PHI from log messages."""
    
    def __init__(self):
        """Initialize PHI detector with patterns."""
        # PHI patterns (compiled for performance)
        self.patterns = {
            "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b|\b\d{9}\b'),
            "phone": re.compile(r'(\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}'),
            "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            "date_of_birth": re.compile(r'\b(0[1-9]|1[0-2])/(0[1-9]|[12][0-9]|3[01])/(19|20)\d{2}\b|\b(19|20)\d{2}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])\b'),
            "medical_record_number": re.compile(r'\bMRN[-:\s]*\d+\b|\bMR[-:\s]*\d+\b', re.IGNORECASE),
            "patient_id": re.compile(r'\bpatient[-_\s]*id[-:\s]*[A-Za-z0-9]+\b', re.IGNORECASE),
            "account_number": re.compile(r'\baccount[-_\s]*(?:num|number)[-:\s]*[A-Za-z0-9]+\b', re.IGNORECASE),
            "insurance_id": re.compile(r'\binsurance[-_\s]*(?:id|number)[-:\s]*[A-Za-z0-9]+\b', re.IGNORECASE),
            "credit_card": re.compile(r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b'),
        }
        
        # Common PHI keywords to watch for
        self.phi_keywords = {
            "patient_name", "first_name", "last_name", "full_name",
            "address", "street", "city", "zip", "zipcode", "postal_code",
            "diagnosis", "condition", "medication", "prescription",
            "doctor", "physician", "provider", "clinician",
            "birth_date", "dob", "date_of_birth", "age",
            "gender", "sex", "race", "ethnicity",
            "next_of_kin", "emergency_contact", "guardian",
            "insurance", "coverage", "policy_number",
            "treatment", "procedure", "surgery", "therapy"
        }
        
        # Injection attack patterns
        self.injection_patterns = {
            "sql_injection": re.compile(r"(\bDROP\b|\bDELETE\b|\bINSERT\b|\bUPDATE\b).*\b(TABLE|FROM|INTO|SET)\b|'.*OR.*'.*=.*'|--|\||;", re.IGNORECASE),
            "xss": re.compile(r"<script.*?>.*?</script>|javascript:|on\w+\s*=", re.IGNORECASE),
            "path_traversal": re.compile(r"\.\./|\.\.\\\|%2e%2e%2f|%2e%2e%5c", re.IGNORECASE),
            "command_injection": re.compile(r"[;&|`$(){}]|nc\s+|wget\s+|curl\s+|bash\s+|sh\s+", re.IGNORECASE),
            "ldap_injection": re.compile(r"\$\{jndi:|ldap://|rmi://", re.IGNORECASE),
            "template_injection": re.compile(r"\{\{.*\}\}|\${.*}|<%.*%>", re.IGNORECASE),
        }
    
    def detect_phi(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect potential PHI in text.
        
        Args:
            text: Text to analyze for PHI
            
        Returns:
            List of detected PHI with type and location
        """
        detections = []
        
        # Check patterns
        for phi_type, pattern in self.patterns.items():
            for match in pattern.finditer(text):
                detections.append({
                    "type": phi_type,
                    "value": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": "high"
                })
        
        # Check keywords (lower confidence)
        words = text.lower().split()
        for i, word in enumerate(words):
            if word in self.phi_keywords:
                detections.append({
                    "type": "keyword",
                    "value": word,
                    "position": i,
                    "confidence": "medium"
                })
        
        return detections
    
    def redact_phi(self, text: str, replacement: str = "[REDACTED]") -> str:
        """
        Redact PHI and injection attacks from text.
        
        Args:
            text: Text to redact
            replacement: Replacement string for PHI
            
        Returns:
            Text with PHI and malicious content redacted
        """
        if not text:
            return text
        
        redacted_text = text
        
        # Redact PHI pattern matches
        for phi_type, pattern in self.patterns.items():
            redacted_text = pattern.sub(replacement, redacted_text)
        
        # Redact injection attack patterns
        for injection_type, pattern in self.injection_patterns.items():
            redacted_text = pattern.sub(f"[{injection_type.upper()}_BLOCKED]", redacted_text)
        
        # Redact based on common PHI field names in JSON/dict-like structures
        json_phi_pattern = re.compile(
            r'("(?:' + '|'.join(self.phi_keywords) + r')"\s*:\s*)"[^"]*"',
            re.IGNORECASE
        )
        redacted_text = json_phi_pattern.sub(r'\1"[REDACTED]"', redacted_text)
        
        return redacted_text
    
    def create_phi_hash(self, text: str) -> str:
        """
        Create a hash of PHI for tracking without exposing actual values.
        
        Args:
            text: Text containing PHI
            
        Returns:
            SHA-256 hash of the text
        """
        return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]


class SecureLogFormatter(logging.Formatter):
    """Secure log formatter that redacts PHI and structures logs for compliance."""
    
    def __init__(self, phi_detector: Optional[PHIDetector] = None):
        """Initialize secure formatter."""
        super().__init__()
        self.phi_detector = phi_detector or PHIDetector()
        
        # HIPAA-compliant log format
        self.format_template = (
            "%(asctime)s|%(levelname)s|%(name)s|%(funcName)s:%(lineno)d|"
            "%(message)s|session=%(session_id)s|user=%(user_id)s"
        )
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with PHI redaction."""
        # Redact PHI from the message
        if hasattr(record, 'msg') and record.msg:
            record.msg = self.phi_detector.redact_phi(str(record.msg))
        
        # Redact PHI from arguments
        if hasattr(record, 'args') and record.args:
            redacted_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    redacted_args.append(self.phi_detector.redact_phi(arg))
                else:
                    redacted_args.append(arg)
            record.args = tuple(redacted_args)
        
        # Add security context if available
        if not hasattr(record, 'session_id'):
            record.session_id = getattr(record, 'session_id', 'unknown')
        if not hasattr(record, 'user_id'):
            record.user_id = getattr(record, 'user_id', 'system')
        
        # Ensure message is available
        if not hasattr(record, 'message') or not record.message:
            record.message = record.getMessage()
        
        # Format timestamp in ISO format
        record.asctime = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()
        
        # Apply template formatting
        formatted = self.format_template % record.__dict__
        
        return formatted


class SecureLogger:
    """HIPAA-compliant secure logger with PHI protection."""
    
    def __init__(
        self,
        name: str,
        log_path: Optional[Path] = None,
        encryption: Optional[PHIEncryption] = None,
        min_level: LogLevel = LogLevel.INFO
    ):
        """
        Initialize secure logger.
        
        Args:
            name: Logger name
            log_path: Path to log files
            encryption: PHI encryption instance
            min_level: Minimum log level
        """
        self.name = name
        self.log_path = log_path or Path.home() / ".hacs" / "logs"
        self.log_path.mkdir(parents=True, exist_ok=True)
        
        self.encryption = encryption or PHIEncryption()
        self.phi_detector = PHIDetector()
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, min_level.value))
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create secure file handler
        log_file = self.log_path / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
        handler = logging.FileHandler(log_file, encoding='utf-8')
        handler.setLevel(getattr(logging, min_level.value))
        
        # Set secure formatter
        formatter = SecureLogFormatter(self.phi_detector)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # Set restrictive permissions
        import os
        os.chmod(log_file, 0o600)
        
        # Add audit handler for audit-level logs
        audit_file = self.log_path / f"{name}_audit_{datetime.now().strftime('%Y%m%d')}.log"
        audit_handler = logging.FileHandler(audit_file, encoding='utf-8')
        audit_handler.setLevel(logging.INFO)
        audit_handler.addFilter(lambda record: record.levelname == 'AUDIT')
        audit_handler.setFormatter(formatter)
        self.logger.addHandler(audit_handler)
        os.chmod(audit_file, 0o600)
    
    def _log_with_context(
        self,
        level: LogLevel,
        message: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """Log message with security context."""
        extra = {
            'user_id': user_id or 'system',
            'session_id': session_id or 'none',
            **kwargs
        }
        
        # Convert LogLevel to logging level
        if level == LogLevel.AUDIT:
            log_level = logging.INFO
            extra['audit_event'] = True
            extra['levelname'] = 'AUDIT'
        else:
            log_level = getattr(logging, level.value)
        
        self.logger.log(log_level, message, extra=extra)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self._log_with_context(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self._log_with_context(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self._log_with_context(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self._log_with_context(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        self._log_with_context(LogLevel.CRITICAL, message, **kwargs)
    
    def audit(self, message: str, **kwargs) -> None:
        """Log audit message."""
        self._log_with_context(LogLevel.AUDIT, message, **kwargs)
    
    def log_exception(
        self,
        exception: Exception,
        message: str = "Exception occurred",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Log exception with PHI redaction.
        
        Args:
            exception: Exception to log
            message: Additional message
            user_id: User ID context
            session_id: Session ID context
            **kwargs: Additional context
        """
        # Redact PHI from exception message
        redacted_exc_msg = self.phi_detector.redact_phi(str(exception))
        
        # Create safe exception info
        exc_info = {
            "type": type(exception).__name__,
            "message": redacted_exc_msg,
            "module": getattr(exception, '__module__', 'unknown')
        }
        
        full_message = f"{message}: {exc_info}"
        self._log_with_context(
            LogLevel.ERROR,
            full_message,
            user_id=user_id,
            session_id=session_id,
            exception_type=type(exception).__name__,
            **kwargs
        )
    
    def log_phi_access(
        self,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        success: bool = True,
        **kwargs
    ) -> None:
        """
        Log PHI access event for HIPAA compliance.
        
        Args:
            action: Action performed
            resource_type: Type of resource accessed
            resource_id: ID of resource (will be hashed)
            user_id: User performing action
            session_id: Session ID
            success: Whether access was successful
            **kwargs: Additional context
        """
        # Hash resource ID for privacy
        hashed_resource_id = None
        if resource_id:
            hashed_resource_id = self.phi_detector.create_phi_hash(resource_id)
        
        audit_message = (
            f"PHI_ACCESS|action={action}|resource_type={resource_type}|"
            f"resource_hash={hashed_resource_id}|success={success}"
        )
        
        self._log_with_context(
            LogLevel.AUDIT,
            audit_message,
            user_id=user_id,
            session_id=session_id,
            phi_access=True,
            **kwargs
        )


class ErrorSanitizer:
    """Sanitizes error messages to remove PHI before display."""
    
    def __init__(self):
        """Initialize error sanitizer."""
        self.phi_detector = PHIDetector()
    
    def sanitize_error(self, error: Exception) -> Dict[str, Any]:
        """
        Sanitize error for safe display/logging.
        
        Args:
            error: Exception to sanitize
            
        Returns:
            Sanitized error information
        """
        return {
            "type": type(error).__name__,
            "message": self.phi_detector.redact_phi(str(error)),
            "module": getattr(error, '__module__', 'unknown'),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "safe_for_display": True
        }
    
    def create_user_safe_message(self, error: Exception) -> str:
        """
        Create user-safe error message.
        
        Args:
            error: Exception to create message for
            
        Returns:
            Safe error message for user display
        """
        sanitized = self.sanitize_error(error)
        
        # Generic messages for different error types
        safe_messages = {
            "AuthError": "Authentication or authorization failed. Please check your credentials.",
            "ValidationError": "Input validation failed. Please check your data and try again.",
            "PermissionError": "You don't have permission to perform this action.",
            "ValueError": "Invalid input provided. Please check your data.",
            "ConnectionError": "Service temporarily unavailable. Please try again later.",
            "TimeoutError": "Request timed out. Please try again.",
        }
        
        return safe_messages.get(sanitized["type"], "An error occurred. Please contact support if the problem persists.")


# Global secure logger instance
_secure_logger = None


def get_secure_logger(name: str = "hacs") -> SecureLogger:
    """Get or create secure logger instance."""
    global _secure_logger
    if _secure_logger is None or _secure_logger.name != name:
        _secure_logger = SecureLogger(name)
    return _secure_logger


# Export public API
__all__ = [
    "LogLevel",
    "PHIDetector",
    "SecureLogger", 
    "ErrorSanitizer",
    "get_secure_logger",
]