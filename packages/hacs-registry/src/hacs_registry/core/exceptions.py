"""
Exception Hierarchy Following SOLID Principles

This module defines a comprehensive exception hierarchy that follows SOLID principles:

S - Single Responsibility: Each exception represents one specific error condition
O - Open/Closed: Easy to add new exception types without modification
L - Liskov Substitution: All exceptions are substitutable for their base types
I - Interface Segregation: Focused exception interfaces for different concerns
D - Dependency Inversion: Higher-level modules catch base exceptions

Exception Categories:
    🏗️ Registry Exceptions - Core registry operations
    🏥 Domain Exceptions - Business logic violations
    🔧 Infrastructure Exceptions - External system failures
    ✅ Validation Exceptions - Data validation errors
    🔐 Permission Exceptions - Access control violations
"""

from abc import ABC
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone


class RegistryException(Exception):
    """
    Base exception for all HACS Registry errors.
    
    SOLID Compliance:
    - S: Single responsibility - represents registry errors
    - O: Open/closed - extensible for specific error types
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        inner_exception: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.inner_exception = inner_exception
        self.timestamp = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization."""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "inner_exception": str(self.inner_exception) if self.inner_exception else None
        }
    
    def __str__(self) -> str:
        return f"{self.error_code}: {self.message}"


# Domain Layer Exceptions (Business Logic Violations)

class DomainException(RegistryException):
    """Base class for domain layer exceptions."""
    
    def __init__(self, message: str, domain_object: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.domain_object = domain_object


class ResourceException(DomainException):
    """Base class for resource-related exceptions."""
    
    def __init__(self, message: str, resource_id: Optional[str] = None, resource_type: Optional[str] = None, **kwargs):
        super().__init__(message, domain_object="Resource", **kwargs)
        self.resource_id = resource_id
        self.resource_type = resource_type


class ResourceNotFoundError(ResourceException):
    """Resource not found in registry."""
    
    def __init__(self, resource_id: str, resource_type: Optional[str] = None):
        message = f"Resource '{resource_id}' not found"
        if resource_type:
            message += f" (type: {resource_type})"
        super().__init__(message, resource_id=resource_id, resource_type=resource_type)


class ResourceAlreadyExistsError(ResourceException):
    """Resource already exists in registry."""
    
    def __init__(self, resource_id: str, resource_type: Optional[str] = None):
        message = f"Resource '{resource_id}' already exists"
        if resource_type:
            message += f" (type: {resource_type})"
        super().__init__(message, resource_id=resource_id, resource_type=resource_type)


class ResourceVersionConflictError(ResourceException):
    """Resource version conflict during update."""
    
    def __init__(self, resource_id: str, expected_version: str, actual_version: str):
        message = f"Version conflict for resource '{resource_id}': expected {expected_version}, got {actual_version}"
        super().__init__(
            message, 
            resource_id=resource_id,
            details={
                "expected_version": expected_version,
                "actual_version": actual_version
            }
        )


class ResourceLifecycleError(ResourceException):
    """Invalid resource lifecycle transition."""
    
    def __init__(self, resource_id: str, current_state: str, attempted_action: str):
        message = f"Cannot {attempted_action} resource '{resource_id}' in state '{current_state}'"
        super().__init__(
            message,
            resource_id=resource_id,
            details={
                "current_state": current_state,
                "attempted_action": attempted_action
            }
        )


class AgentException(DomainException):
    """Base class for agent-related exceptions."""
    
    def __init__(self, message: str, agent_id: Optional[str] = None, agent_type: Optional[str] = None, **kwargs):
        super().__init__(message, domain_object="Agent", **kwargs)
        self.agent_id = agent_id
        self.agent_type = agent_type


class AgentNotFoundError(AgentException):
    """Agent not found in registry."""
    
    def __init__(self, agent_id: str, agent_type: Optional[str] = None):
        message = f"Agent '{agent_id}' not found"
        if agent_type:
            message += f" (type: {agent_type})"
        super().__init__(message, agent_id=agent_id, agent_type=agent_type)


class AgentConfigurationError(AgentException):
    """Agent configuration is invalid."""
    
    def __init__(self, agent_id: str, config_errors: List[str]):
        message = f"Agent '{agent_id}' has invalid configuration: {'; '.join(config_errors)}"
        super().__init__(
            message,
            agent_id=agent_id,
            details={"config_errors": config_errors}
        )


class AgentDeploymentError(AgentException):
    """Agent deployment failed."""
    
    def __init__(self, agent_id: str, environment: str, reason: str):
        message = f"Failed to deploy agent '{agent_id}' to {environment}: {reason}"
        super().__init__(
            message,
            agent_id=agent_id,
            details={
                "environment": environment,
                "reason": reason
            }
        )


class ToolException(DomainException):
    """Base class for tool-related exceptions."""
    
    def __init__(self, message: str, tool_name: Optional[str] = None, **kwargs):
        super().__init__(message, domain_object="Tool", **kwargs)
        self.tool_name = tool_name


class ToolNotFoundError(ToolException):
    """Tool not found in registry."""
    
    def __init__(self, tool_name: str):
        message = f"Tool '{tool_name}' not found"
        super().__init__(message, tool_name=tool_name)


class ToolExecutionError(ToolException):
    """Tool execution failed."""
    
    def __init__(self, tool_name: str, execution_error: str, **kwargs):
        message = f"Tool '{tool_name}' execution failed: {execution_error}"
        super().__init__(
            message,
            tool_name=tool_name,
            details={"execution_error": execution_error},
            **kwargs
        )


# Infrastructure Layer Exceptions (External System Failures)

class InfrastructureException(RegistryException):
    """Base class for infrastructure layer exceptions."""
    
    def __init__(self, message: str, component: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.component = component


class PersistenceException(InfrastructureException):
    """Database or storage operation failed."""
    
    def __init__(self, message: str, operation: Optional[str] = None, **kwargs):
        super().__init__(message, component="Persistence", **kwargs)
        self.operation = operation


class DatabaseConnectionError(PersistenceException):
    """Database connection failed."""
    
    def __init__(self, database_url: Optional[str] = None, inner_exception: Optional[Exception] = None):
        message = "Failed to connect to database"
        if database_url:
            message += f" at {database_url}"
        super().__init__(
            message,
            operation="connect",
            inner_exception=inner_exception,
            details={"database_url": database_url}
        )


class DatabaseTimeoutError(PersistenceException):
    """Database operation timed out."""
    
    def __init__(self, operation: str, timeout_seconds: float):
        message = f"Database {operation} timed out after {timeout_seconds} seconds"
        super().__init__(
            message,
            operation=operation,
            details={"timeout_seconds": timeout_seconds}
        )


class IntegrationException(InfrastructureException):
    """External integration failed."""
    
    def __init__(self, message: str, service_name: Optional[str] = None, **kwargs):
        super().__init__(message, component="Integration", **kwargs)
        self.service_name = service_name


class LangChainIntegrationError(IntegrationException):
    """LangChain integration failed."""
    
    def __init__(self, operation: str, error_details: str):
        message = f"LangChain {operation} failed: {error_details}"
        super().__init__(
            message,
            service_name="LangChain",
            details={"operation": operation, "error_details": error_details}
        )


class MCPIntegrationError(IntegrationException):
    """MCP integration failed."""
    
    def __init__(self, operation: str, error_details: str):
        message = f"MCP {operation} failed: {error_details}"
        super().__init__(
            message,
            service_name="MCP",
            details={"operation": operation, "error_details": error_details}
        )


class EventPublishingError(InfrastructureException):
    """Event publishing failed."""
    
    def __init__(self, event_type: str, error_details: str):
        message = f"Failed to publish event '{event_type}': {error_details}"
        super().__init__(
            message,
            component="EventBus",
            details={"event_type": event_type, "error_details": error_details}
        )


# Validation Layer Exceptions (Data Validation Errors)

class ValidationException(RegistryException):
    """Base class for validation exceptions."""
    
    def __init__(self, message: str, validation_errors: Optional[List[str]] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.validation_errors = validation_errors or []


class SchemaValidationError(ValidationException):
    """Schema validation failed."""
    
    def __init__(self, schema_name: str, validation_errors: List[str]):
        message = f"Schema validation failed for '{schema_name}'"
        super().__init__(
            message,
            validation_errors=validation_errors,
            details={"schema_name": schema_name}
        )


class BusinessRuleViolationError(ValidationException):
    """Business rule validation failed."""
    
    def __init__(self, rule_name: str, rule_description: str, entity_id: Optional[str] = None):
        message = f"Business rule violation: {rule_description}"
        if entity_id:
            message += f" (entity: {entity_id})"
        super().__init__(
            message,
            details={
                "rule_name": rule_name,
                "rule_description": rule_description,
                "entity_id": entity_id
            }
        )


class ComplianceViolationError(ValidationException):
    """Healthcare compliance rule violated."""
    
    def __init__(self, compliance_rule: str, violation_details: str, severity: str = "error"):
        message = f"Compliance violation ({compliance_rule}): {violation_details}"
        super().__init__(
            message,
            details={
                "compliance_rule": compliance_rule,
                "violation_details": violation_details,
                "severity": severity
            }
        )


class TypeSafetyError(ValidationException):
    """Type safety validation failed."""
    
    def __init__(self, expected_type: str, actual_type: str, field_name: Optional[str] = None):
        message = f"Type safety violation: expected {expected_type}, got {actual_type}"
        if field_name:
            message += f" for field '{field_name}'"
        super().__init__(
            message,
            details={
                "expected_type": expected_type,
                "actual_type": actual_type,
                "field_name": field_name
            }
        )


# Permission Layer Exceptions (Access Control Violations)

class PermissionException(RegistryException):
    """Base class for permission-related exceptions."""
    
    def __init__(self, message: str, actor_id: Optional[str] = None, resource_id: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.actor_id = actor_id
        self.resource_id = resource_id


class AccessDeniedError(PermissionException):
    """Access denied to resource."""
    
    def __init__(self, actor_id: str, resource_id: str, required_permission: str):
        message = f"Access denied: {actor_id} lacks '{required_permission}' for {resource_id}"
        super().__init__(
            message,
            actor_id=actor_id,
            resource_id=resource_id,
            details={"required_permission": required_permission}
        )


class InsufficientPermissionsError(PermissionException):
    """Actor has insufficient permissions."""
    
    def __init__(self, actor_id: str, required_permissions: List[str], actual_permissions: List[str]):
        missing_permissions = set(required_permissions) - set(actual_permissions)
        message = f"Actor {actor_id} missing permissions: {', '.join(missing_permissions)}"
        super().__init__(
            message,
            actor_id=actor_id,
            details={
                "required_permissions": required_permissions,
                "actual_permissions": actual_permissions,
                "missing_permissions": list(missing_permissions)
            }
        )


class PermissionExpiredError(PermissionException):
    """Permission has expired."""
    
    def __init__(self, actor_id: str, permission_id: str, expired_at: datetime):
        message = f"Permission '{permission_id}' for {actor_id} expired at {expired_at}"
        super().__init__(
            message,
            actor_id=actor_id,
            details={
                "permission_id": permission_id,
                "expired_at": expired_at.isoformat()
            }
        )


class EmergencyAccessRequiredError(PermissionException):
    """Emergency access is required for this operation."""
    
    def __init__(self, actor_id: str, resource_id: str, reason: str):
        message = f"Emergency access required for {actor_id} to access {resource_id}: {reason}"
        super().__init__(
            message,
            actor_id=actor_id,
            resource_id=resource_id,
            details={"reason": reason}
        )


class SupervisionRequiredError(PermissionException):
    """Supervision is required for this operation."""
    
    def __init__(self, actor_id: str, required_supervisor_role: str):
        message = f"Actor {actor_id} requires supervision from {required_supervisor_role}"
        super().__init__(
            message,
            actor_id=actor_id,
            details={"required_supervisor_role": required_supervisor_role}
        )


# Audit and Compliance Exceptions

class AuditException(InfrastructureException):
    """Audit-related operation failed."""
    
    def __init__(self, message: str, audit_operation: Optional[str] = None, **kwargs):
        super().__init__(message, component="Audit", **kwargs)
        self.audit_operation = audit_operation


class AuditTrailCorruptedError(AuditException):
    """Audit trail integrity check failed."""
    
    def __init__(self, entity_id: str, corruption_details: str):
        message = f"Audit trail corrupted for {entity_id}: {corruption_details}"
        super().__init__(
            message,
            audit_operation="integrity_check",
            details={
                "entity_id": entity_id,
                "corruption_details": corruption_details
            }
        )


class ComplianceReportError(AuditException):
    """Compliance report generation failed."""
    
    def __init__(self, report_type: str, error_details: str):
        message = f"Failed to generate {report_type} compliance report: {error_details}"
        super().__init__(
            message,
            audit_operation="compliance_report",
            details={
                "report_type": report_type,
                "error_details": error_details
            }
        )


# Configuration and Initialization Exceptions

class ConfigurationError(RegistryException):
    """Configuration error."""
    
    def __init__(self, config_key: str, error_details: str):
        message = f"Configuration error for '{config_key}': {error_details}"
        super().__init__(
            message,
            details={
                "config_key": config_key,
                "error_details": error_details
            }
        )


class InitializationError(RegistryException):
    """Component initialization failed."""
    
    def __init__(self, component_name: str, error_details: str, **kwargs):
        message = f"Failed to initialize {component_name}: {error_details}"
        super().__init__(
            message,
            details={
                "component_name": component_name,
                "error_details": error_details
            },
            **kwargs
        )


# Exception Utilities

class ExceptionHandler:
    """
    Utility class for handling exceptions consistently.
    
    SOLID Compliance:
    - S: Single responsibility - exception handling utilities
    - O: Open/closed - extensible for new exception handling patterns
    """
    
    @staticmethod
    def is_retryable(exception: Exception) -> bool:
        """Check if an exception represents a retryable error."""
        retryable_types = (
            DatabaseTimeoutError,
            DatabaseConnectionError,
            IntegrationException,
            EventPublishingError
        )
        return isinstance(exception, retryable_types)
    
    @staticmethod
    def is_security_related(exception: Exception) -> bool:
        """Check if an exception is security-related."""
        security_types = (
            PermissionException,
            AccessDeniedError,
            InsufficientPermissionsError,
            EmergencyAccessRequiredError,
            SupervisionRequiredError
        )
        return isinstance(exception, security_types)
    
    @staticmethod
    def get_error_severity(exception: Exception) -> str:
        """Get the severity level of an exception."""
        if isinstance(exception, (
            EmergencyAccessRequiredError,
            ComplianceViolationError,
            AuditTrailCorruptedError
        )):
            return "critical"
        elif isinstance(exception, (
            PermissionException,
            ResourceLifecycleError,
            AgentDeploymentError
        )):
            return "high"
        elif isinstance(exception, (
            ValidationException,
            ConfigurationError
        )):
            return "medium"
        else:
            return "low"
    
    @staticmethod
    def should_audit(exception: Exception) -> bool:
        """Check if an exception should be audited."""
        audit_types = (
            PermissionException,
            ComplianceViolationError,
            AuditException,
            EmergencyAccessRequiredError
        )
        return isinstance(exception, audit_types)


# Exception Context Manager for Consistent Error Handling

class ExceptionContext:
    """
    Context manager for consistent exception handling.
    
    SOLID Compliance:
    - S: Single responsibility - provides exception context
    """
    
    def __init__(self, operation: str, component: str, logger=None):
        self.operation = operation
        self.component = component
        self.logger = logger
    
    def __enter__(self):
        if self.logger:
            self.logger.debug(f"Starting {self.operation} in {self.component}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            if self.logger:
                severity = ExceptionHandler.get_error_severity(exc_val)
                self.logger.error(f"{self.operation} failed in {self.component}: {exc_val} (severity: {severity})")
            
            # Re-raise with additional context if it's not already a RegistryException
            if not isinstance(exc_val, RegistryException):
                raise InfrastructureException(
                    f"{self.operation} failed in {self.component}",
                    component=self.component,
                    inner_exception=exc_val
                ) from exc_val
        
        return False  # Don't suppress the exception