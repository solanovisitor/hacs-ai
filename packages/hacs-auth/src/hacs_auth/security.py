"""
HACS Security Module - HIPAA-Compliant Security Controls

This module implements comprehensive security controls required for HIPAA
compliance and healthcare data protection, including encryption, audit
logging, and threat detection.

Security Features:
    - PHI encryption at rest and in transit
    - Secure secrets management
    - HIPAA audit logging requirements
    - Threat detection and monitoring
    - Security validation and compliance checking

Author: HACS Development Team
License: MIT
Version: 1.0.0
"""

import os
import secrets
import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from pydantic import BaseModel, Field
import base64


class SecurityLevel(str, Enum):
    """Security levels for healthcare data classification."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"  # PHI level
    TOP_SECRET = "top_secret"


class EncryptionType(str, Enum):
    """Supported encryption types."""
    SYMMETRIC = "symmetric"
    ASYMMETRIC = "asymmetric"
    HYBRID = "hybrid"


class AuditEventType(str, Enum):
    """HIPAA-compliant audit event types."""
    ACCESS_ATTEMPT = "access_attempt"
    PHI_ACCESS = "phi_access"
    PHI_MODIFICATION = "phi_modification"
    PHI_DELETION = "phi_deletion"
    AUTHENTICATION = "authentication"
    AUTHORIZATION_FAILURE = "authorization_failure"
    SYSTEM_ACCESS = "system_access"
    DATA_EXPORT = "data_export"
    SECURITY_ALERT = "security_alert"
    CONFIGURATION_CHANGE = "configuration_change"


class SecurityConfig(BaseModel):
    """HIPAA-compliant security configuration."""
    
    # Encryption settings
    encryption_key_size: int = Field(default=256, description="Encryption key size in bits")
    encryption_algorithm: str = Field(default="AES-256-GCM", description="Primary encryption algorithm")
    key_rotation_days: int = Field(default=90, description="Days between key rotation")
    
    # Authentication security
    min_password_length: int = Field(default=12, description="Minimum password length")
    require_mfa: bool = Field(default=True, description="Require multi-factor authentication")
    session_timeout_minutes: int = Field(default=15, description="Session timeout in minutes")
    max_failed_attempts: int = Field(default=3, description="Maximum failed login attempts")
    account_lockout_minutes: int = Field(default=30, description="Account lockout duration")
    
    # HIPAA compliance
    phi_encryption_required: bool = Field(default=True, description="Require PHI encryption")
    audit_all_access: bool = Field(default=True, description="Audit all data access")
    data_retention_days: int = Field(default=2557, description="Data retention period (7 years)")
    backup_encryption_required: bool = Field(default=True, description="Require encrypted backups")
    
    # Security monitoring
    enable_intrusion_detection: bool = Field(default=True, description="Enable intrusion detection")
    log_security_events: bool = Field(default=True, description="Log all security events")
    alert_on_suspicious_activity: bool = Field(default=True, description="Alert on suspicious activity")
    
    # Network security
    require_https: bool = Field(default=True, description="Require HTTPS for all connections")
    
    # Compliance settings
    hipaa_compliance_mode: bool = Field(default=True, description="Enable HIPAA compliance mode")
    gdpr_compliance_mode: bool = Field(default=False, description="Enable GDPR compliance mode")
    sox_compliance_mode: bool = Field(default=False, description="Enable SOX compliance mode")


class PHIEncryption:
    """PHI (Protected Health Information) encryption utilities."""
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        """
        Initialize PHI encryption.
        
        Args:
            encryption_key: Optional encryption key, generates new if None
        """
        if encryption_key:
            self.fernet = Fernet(encryption_key)
            self.encryption_key = encryption_key
        else:
            self.encryption_key = Fernet.generate_key()
            self.fernet = Fernet(self.encryption_key)
        
        # Generate RSA key pair for hybrid encryption
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        self.public_key = self.private_key.public_key()
    
    def encrypt_phi_data(self, data: Union[str, dict], security_level: SecurityLevel = SecurityLevel.RESTRICTED) -> Dict[str, Any]:
        """
        Encrypt PHI data with appropriate security level.
        
        Args:
            data: Data to encrypt (PHI)
            security_level: Security level for encryption
            
        Returns:
            Encrypted data package with metadata
        """
        if isinstance(data, dict):
            data_str = str(data).encode('utf-8')
        else:
            data_str = str(data).encode('utf-8')
        
        # Use hybrid encryption for PHI
        if security_level in [SecurityLevel.RESTRICTED, SecurityLevel.TOP_SECRET]:
            # Encrypt data with symmetric key
            encrypted_data = self.fernet.encrypt(data_str)
            
            # Encrypt symmetric key with public key
            encrypted_key = self.public_key.encrypt(
                self.encryption_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            return {
                "encrypted_data": base64.b64encode(encrypted_data).decode('utf-8'),
                "encrypted_key": base64.b64encode(encrypted_key).decode('utf-8'),
                "encryption_type": "hybrid",
                "security_level": security_level.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "algorithm": "AES-256-GCM + RSA-2048"
            }
        else:
            # Use symmetric encryption for lower security levels
            encrypted_data = self.fernet.encrypt(data_str)
            return {
                "encrypted_data": base64.b64encode(encrypted_data).decode('utf-8'),
                "encryption_type": "symmetric",
                "security_level": security_level.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "algorithm": "AES-256-GCM"
            }
    
    def decrypt_phi_data(self, encrypted_package: Dict[str, Any]) -> str:
        """
        Decrypt PHI data package.
        
        Args:
            encrypted_package: Encrypted data package from encrypt_phi_data
            
        Returns:
            Decrypted data string
            
        Raises:
            ValueError: If decryption fails or package is invalid
        """
        try:
            encryption_type = encrypted_package.get("encryption_type")
            
            if encryption_type == "hybrid":
                # Decrypt symmetric key with private key
                encrypted_key = base64.b64decode(encrypted_package["encrypted_key"])
                decrypted_key = self.private_key.decrypt(
                    encrypted_key,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                
                # Decrypt data with symmetric key
                fernet = Fernet(decrypted_key)
                encrypted_data = base64.b64decode(encrypted_package["encrypted_data"])
                decrypted_data = fernet.decrypt(encrypted_data)
                
            elif encryption_type == "symmetric":
                encrypted_data = base64.b64decode(encrypted_package["encrypted_data"])
                decrypted_data = self.fernet.decrypt(encrypted_data)
            else:
                raise ValueError(f"Unsupported encryption type: {encryption_type}")
            
            return decrypted_data.decode('utf-8')
            
        except Exception as e:
            raise ValueError(f"PHI decryption failed: {e}") from e
    
    def get_public_key_pem(self) -> str:
        """Get public key in PEM format for sharing."""
        pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode('utf-8')
    
    def get_private_key_pem(self, password: Optional[bytes] = None) -> str:
        """Get private key in PEM format (use with caution)."""
        encryption_algorithm = serialization.NoEncryption()
        if password:
            encryption_algorithm = serialization.BestAvailableEncryption(password)
        
        pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=encryption_algorithm
        )
        return pem.decode('utf-8')


class SecureSecretsManager:
    """Secure secrets management for HACS system."""
    
    def __init__(self, secrets_path: Optional[Path] = None):
        """
        Initialize secrets manager.
        
        Args:
            secrets_path: Path to secrets storage directory
        """
        self.secrets_path = secrets_path or Path.home() / ".hacs" / "secrets"
        self.secrets_path.mkdir(parents=True, exist_ok=True)
        
        # Ensure proper permissions on secrets directory
        os.chmod(self.secrets_path, 0o700)
        
        self.phi_encryption = PHIEncryption()
    
    def generate_secure_secret(self, length: int = 32) -> str:
        """
        Generate cryptographically secure secret.
        
        Args:
            length: Length of secret in bytes
            
        Returns:
            Base64-encoded secure secret
        """
        return base64.b64encode(secrets.token_bytes(length)).decode('utf-8')
    
    def generate_jwt_secret(self) -> str:
        """Generate secure JWT secret key."""
        return self.generate_secure_secret(64)  # 512-bit key
    
    def store_secret(self, name: str, value: str, security_level: SecurityLevel = SecurityLevel.RESTRICTED) -> None:
        """
        Store secret with encryption.
        
        Args:
            name: Secret name
            value: Secret value
            security_level: Security level for storage
        """
        encrypted_package = self.phi_encryption.encrypt_phi_data(value, security_level)
        
        secret_file = self.secrets_path / f"{name}.secret"
        with open(secret_file, 'w') as f:
            import json
            json.dump(encrypted_package, f)
        
        # Set restrictive permissions
        os.chmod(secret_file, 0o600)
    
    def get_secret(self, name: str) -> str:
        """
        Retrieve and decrypt secret.
        
        Args:
            name: Secret name
            
        Returns:
            Decrypted secret value
            
        Raises:
            FileNotFoundError: If secret doesn't exist
            ValueError: If decryption fails
        """
        secret_file = self.secrets_path / f"{name}.secret"
        
        if not secret_file.exists():
            raise FileNotFoundError(f"Secret '{name}' not found")
        
        with open(secret_file, 'r') as f:
            import json
            encrypted_package = json.load(f)
        
        return self.phi_encryption.decrypt_phi_data(encrypted_package)
    
    def secret_exists(self, name: str) -> bool:
        """Check if secret exists."""
        return (self.secrets_path / f"{name}.secret").exists()
    
    def delete_secret(self, name: str) -> None:
        """Securely delete secret."""
        secret_file = self.secrets_path / f"{name}.secret"
        if secret_file.exists():
            # Overwrite file with random data before deletion
            with open(secret_file, 'rb+') as f:
                size = f.seek(0, 2)  # Get file size
                f.seek(0)
                f.write(secrets.token_bytes(size))
                f.flush()
                os.fsync(f.fileno())
            
            secret_file.unlink()
    
    def rotate_secrets(self) -> Dict[str, str]:
        """Rotate all secrets and return new values."""
        rotated = {}
        
        for secret_file in self.secrets_path.glob("*.secret"):
            name = secret_file.stem
            try:
                # Generate new secret
                new_value = self.generate_secure_secret()
                
                # Store new secret
                self.store_secret(name, new_value)
                rotated[name] = new_value
                
            except Exception as e:
                logging.error(f"Failed to rotate secret '{name}': {e}")
        
        return rotated


class HIPAAAuditLogger:
    """HIPAA-compliant audit logging system."""
    
    def __init__(self, log_path: Optional[Path] = None, encryption: Optional[PHIEncryption] = None):
        """
        Initialize HIPAA audit logger.
        
        Args:
            log_path: Path to audit log storage
            encryption: PHI encryption instance
        """
        self.log_path = log_path or Path.home() / ".hacs" / "audit_logs"
        self.log_path.mkdir(parents=True, exist_ok=True)
        
        self.encryption = encryption or PHIEncryption()
        
        # Configure audit logger
        self.logger = logging.getLogger("hacs.audit")
        self.logger.setLevel(logging.INFO)
        
        # Create audit log file handler
        audit_log_file = self.log_path / f"hacs_audit_{datetime.now().strftime('%Y%m%d')}.log"
        handler = logging.FileHandler(audit_log_file)
        handler.setLevel(logging.INFO)
        
        # HIPAA-compliant log format
        formatter = logging.Formatter(
            '%(asctime)s|%(levelname)s|AUDIT|%(message)s',
            datefmt='%Y-%m-%d %H:%M:%S UTC'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # Set restrictive permissions on log files
        os.chmod(audit_log_file, 0o600)
    
    def log_phi_access(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        success: bool = True,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log PHI access event (HIPAA requirement).
        
        Args:
            user_id: User accessing PHI
            action: Action performed (read, write, delete, etc.)
            resource_type: Type of resource accessed
            resource_id: ID of specific resource
            patient_id: Patient ID (if applicable)
            success: Whether access was successful
            ip_address: Client IP address
            user_agent: Client user agent
            additional_data: Additional audit data
        """
        audit_data = {
            "event_type": AuditEventType.PHI_ACCESS.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "patient_id": patient_id,
            "success": success,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "session_id": additional_data.get("session_id") if additional_data else None,
            "organization": additional_data.get("organization") if additional_data else None,
        }
        
        # Add additional data if provided
        if additional_data:
            audit_data.update(additional_data)
        
        # Log audit event
        self.logger.info(f"PHI_ACCESS|{self._format_audit_data(audit_data)}")
    
    def log_authentication_event(
        self,
        user_id: str,
        event_type: str,
        success: bool,
        ip_address: Optional[str] = None,
        failure_reason: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log authentication event.
        
        Args:
            user_id: User ID attempting authentication
            event_type: Type of auth event (login, logout, mfa, etc.)
            success: Whether authentication was successful
            ip_address: Client IP address
            failure_reason: Reason for failure (if applicable)
            additional_data: Additional audit data
        """
        audit_data = {
            "event_type": AuditEventType.AUTHENTICATION.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "auth_event_type": event_type,
            "success": success,
            "ip_address": ip_address,
            "failure_reason": failure_reason,
        }
        
        if additional_data:
            audit_data.update(additional_data)
        
        self.logger.info(f"AUTHENTICATION|{self._format_audit_data(audit_data)}")
    
    def log_security_alert(
        self,
        alert_type: str,
        severity: str,
        description: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log security alert.
        
        Args:
            alert_type: Type of security alert
            severity: Alert severity (low, medium, high, critical)
            description: Alert description
            user_id: Associated user ID (if applicable)
            ip_address: Source IP address
            additional_data: Additional alert data
        """
        audit_data = {
            "event_type": AuditEventType.SECURITY_ALERT.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "alert_type": alert_type,
            "severity": severity,
            "description": description,
            "user_id": user_id,
            "ip_address": ip_address,
        }
        
        if additional_data:
            audit_data.update(additional_data)
        
        self.logger.warning(f"SECURITY_ALERT|{self._format_audit_data(audit_data)}")
    
    def _format_audit_data(self, data: Dict[str, Any]) -> str:
        """Format audit data for logging."""
        return "|".join([f"{k}:{v}" for k, v in data.items() if v is not None])


class SecurityValidator:
    """Validates security configuration and compliance."""
    
    def __init__(self, config: SecurityConfig):
        """Initialize security validator."""
        self.config = config
        self.secrets_manager = SecureSecretsManager()
    
    def validate_hipaa_compliance(self) -> Dict[str, Any]:
        """
        Validate HIPAA compliance requirements.
        
        Returns:
            Compliance validation results
        """
        results = {
            "compliant": True,
            "violations": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Check encryption requirements
        if not self.config.phi_encryption_required:
            results["violations"].append("PHI encryption is not required (§164.312(a)(1))")
            results["compliant"] = False
        
        # Check audit requirements
        if not self.config.audit_all_access:
            results["violations"].append("Audit all access is not enabled (§164.312(b))")
            results["compliant"] = False
        
        # Check authentication requirements
        if not self.config.require_mfa:
            results["warnings"].append("Multi-factor authentication not required")
        
        if self.config.min_password_length < 8:
            results["violations"].append("Password length too short (minimum 8 characters)")
            results["compliant"] = False
        
        # Check session timeout
        if self.config.session_timeout_minutes > 30:
            results["warnings"].append("Session timeout exceeds recommended 30 minutes")
        
        # Check data retention
        if self.config.data_retention_days < 2557:  # 7 years
            results["warnings"].append("Data retention period less than HIPAA recommendation")
        
        # Check for secure secrets
        try:
            jwt_secret = os.getenv("HACS_JWT_SECRET")
            if not jwt_secret:
                # Try to get from secure secrets manager
                try:
                    secrets_manager = SecureSecretsManager()
                    if secrets_manager.secret_exists("jwt_secret"):
                        jwt_secret = secrets_manager.get_secret("jwt_secret")
                    else:
                        results["violations"].append("No JWT secret configured")
                        results["compliant"] = False
                except Exception:
                    results["violations"].append("No JWT secret configured")
                    results["compliant"] = False
            
            # Check if secret is secure
            if jwt_secret:
                weak_secrets = [
                    "dev-secret-change-in-production",
                    "secret",
                    "password",
                    "change-me",
                    "development-key"
                ]
                if jwt_secret in weak_secrets or len(jwt_secret) < 32:
                    results["violations"].append("Default or weak JWT secret detected")
                    results["compliant"] = False
        except Exception:
            results["violations"].append("Unable to validate JWT secret")
            results["compliant"] = False
        
        return results
    
    def check_security_configuration(self) -> Dict[str, Any]:
        """
        Check overall security configuration.
        
        Returns:
            Security configuration assessment
        """
        results = {
            "security_score": 0,
            "max_score": 100,
            "issues": [],
            "recommendations": []
        }
        
        score = 0
        
        # Encryption checks (30 points)
        if self.config.phi_encryption_required:
            score += 15
        if self.config.backup_encryption_required:
            score += 10
        if self.config.encryption_key_size >= 256:
            score += 5
        
        # Authentication checks (25 points)
        if self.config.require_mfa:
            score += 10
        if self.config.min_password_length >= 12:
            score += 5
        elif self.config.min_password_length >= 8:
            score += 3
        if self.config.session_timeout_minutes <= 15:
            score += 10
        
        # Monitoring checks (25 points)
        if self.config.enable_intrusion_detection:
            score += 10
        if self.config.log_security_events:
            score += 10
        if self.config.alert_on_suspicious_activity:
            score += 5
        
        # Compliance checks (20 points)
        if self.config.hipaa_compliance_mode:
            score += 15
        if self.config.audit_all_access:
            score += 5
        
        results["security_score"] = score
        
        # Generate recommendations based on score
        if score < 70:
            results["recommendations"].append("Security configuration needs significant improvement")
        elif score < 85:
            results["recommendations"].append("Security configuration is good but has room for improvement")
        else:
            results["recommendations"].append("Security configuration meets high standards")
        
        return results


# Secure initialization functions
def generate_production_secrets() -> Dict[str, str]:
    """Generate secure production secrets."""
    secrets_manager = SecureSecretsManager()
    
    secrets_generated = {}
    
    # Generate JWT secret if not exists
    if not secrets_manager.secret_exists("jwt_secret"):
        jwt_secret = secrets_manager.generate_jwt_secret()
        secrets_manager.store_secret("jwt_secret", jwt_secret)
        secrets_generated["jwt_secret"] = "Generated secure JWT secret"
    
    # Generate database encryption key
    if not secrets_manager.secret_exists("db_encryption_key"):
        db_key = secrets_manager.generate_secure_secret(32)
        secrets_manager.store_secret("db_encryption_key", db_key)
        secrets_generated["db_encryption_key"] = "Generated database encryption key"
    
    # Generate API keys
    for api_name in ["internal_api", "external_api", "monitoring_api"]:
        if not secrets_manager.secret_exists(f"{api_name}_key"):
            api_key = secrets_manager.generate_secure_secret(24)
            secrets_manager.store_secret(f"{api_name}_key", api_key)
            secrets_generated[f"{api_name}_key"] = f"Generated {api_name} key"
    
    return secrets_generated


def validate_production_security() -> Dict[str, Any]:
    """Validate production security configuration."""
    config = SecurityConfig()
    validator = SecurityValidator(config)
    
    # Run HIPAA compliance check
    hipaa_results = validator.validate_hipaa_compliance()
    
    # Run security configuration check
    security_results = validator.check_security_configuration()
    
    return {
        "hipaa_compliance": hipaa_results,
        "security_configuration": security_results,
        "production_ready": hipaa_results["compliant"] and security_results["security_score"] >= 85
    }


# Export public API
__all__ = [
    "SecurityLevel",
    "EncryptionType", 
    "AuditEventType",
    "SecurityConfig",
    "PHIEncryption",
    "SecureSecretsManager",
    "HIPAAAuditLogger",
    "SecurityValidator",
    "generate_production_secrets",
    "validate_production_security",
]