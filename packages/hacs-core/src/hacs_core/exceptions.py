"""
Public exception types for HACS core.

This module provides the public exception hierarchy for HACS, allowing
other packages to import and handle exceptions without coupling to internal
implementation details.
"""


class HACSError(Exception):
    """Base exception for all HACS errors."""
    
    def __init__(self, message: str, code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.code = code or "HACS_ERROR"
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (Code: {self.code}, Details: {self.details})"
        return f"{self.message} (Code: {self.code})"


class AdapterError(HACSError):
    """Error in adapter operations."""
    
    def __init__(self, message: str, adapter_type: str = None, code: str = "ADAPTER_ERROR", **kwargs):
        super().__init__(message, code=code, **kwargs)
        self.adapter_type = adapter_type


class AdapterNotFoundError(AdapterError):
    """Raised when a requested adapter is not found."""
    
    def __init__(self, adapter_type: str, message: str = None):
        if message is None:
            message = f"Adapter not found: {adapter_type}"
        super().__init__(message, adapter_type=adapter_type, code="ADAPTER_NOT_FOUND")


class AuthenticationError(HACSError):
    """Authentication-related errors."""
    
    def __init__(self, message: str, actor_id: str = None, code: str = "AUTH_ERROR", **kwargs):
        super().__init__(message, code=code, **kwargs)
        self.actor_id = actor_id


class AuthorizationError(HACSError):
    """Authorization-related errors."""
    
    def __init__(self, message: str, actor_id: str = None, permission: str = None, code: str = "AUTHZ_ERROR", **kwargs):
        super().__init__(message, code=code, **kwargs)
        self.actor_id = actor_id
        self.permission = permission


class ValidationError(HACSError):
    """Validation errors."""
    
    def __init__(self, message: str, field: str = None, value = None, code: str = "VALIDATION_ERROR", **kwargs):
        super().__init__(message, code=code, **kwargs)
        self.field = field
        self.value = value


class ConfigurationError(HACSError):
    """Configuration-related errors."""
    
    def __init__(self, message: str, config_key: str = None, code: str = "CONFIG_ERROR", **kwargs):
        super().__init__(message, code=code, **kwargs)
        self.config_key = config_key


class ResourceError(HACSError):
    """Resource operation errors."""
    
    def __init__(self, message: str, resource_type: str = None, resource_id: str = None, code: str = "RESOURCE_ERROR", **kwargs):
        super().__init__(message, code=code, **kwargs)
        self.resource_type = resource_type
        self.resource_id = resource_id


class ResourceNotFoundError(ResourceError):
    """Raised when a requested resource is not found."""
    
    def __init__(self, resource_type: str, resource_id: str, message: str = None):
        if message is None:
            message = f"Resource not found: {resource_type}#{resource_id}"
        super().__init__(message, resource_type=resource_type, resource_id=resource_id, code="RESOURCE_NOT_FOUND")


class MemoryError(HACSError):
    """Memory operation errors."""
    
    def __init__(self, message: str, memory_type: str = None, code: str = "MEMORY_ERROR", **kwargs):
        super().__init__(message, code=code, **kwargs)
        self.memory_type = memory_type


class VectorStoreError(HACSError):
    """Vector store operation errors."""
    
    def __init__(self, message: str, operation: str = None, code: str = "VECTOR_STORE_ERROR", **kwargs):
        super().__init__(message, code=code, **kwargs)
        self.operation = operation