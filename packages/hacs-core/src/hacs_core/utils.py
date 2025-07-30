"""
HACS Core Utilities

Common utilities and patterns used across HACS packages to eliminate
code duplication and ensure consistency.
"""

import logging
import os
from functools import wraps
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ImportError(Exception):
    """Enhanced import error with helpful messages."""

    def __init__(self, package: str, install_command: str, description: str = ""):
        self.package = package
        self.install_command = install_command
        self.description = description

        message = f"{package} not available."
        if description:
            message += f" {description}"
        message += f" Install with: {install_command}"

        super().__init__(message)


def safe_import(package_name: str, install_command: str, description: str = "") -> Any:
    """
    Safely import a package with helpful error messages.

    Args:
        package_name: Name of the package to import
        install_command: Command to install the package
        description: Optional description of what the package is used for

    Returns:
        The imported package or None if import fails

    Raises:
        ImportError: If package is required but not available
    """
    try:
        return __import__(package_name)
    except ImportError as original_error:
        raise ImportError(package_name, install_command, description) from original_error


def optional_import(package_name: str, fallback_value: Any = None) -> Any:
    """
    Import a package optionally, returning fallback value if not available.

    Args:
        package_name: Name of the package to import
        fallback_value: Value to return if import fails

    Returns:
        The imported package or fallback value
    """
    try:
        return __import__(package_name)
    except ImportError:
        logger.warning(f"Optional package '{package_name}' not available")
        return fallback_value


def get_api_key(key_name: str, env_var: str, required: bool = True) -> str | None:
    """
    Get API key from environment with consistent error handling.

    Args:
        key_name: Human-readable name of the API key
        env_var: Environment variable name
        required: Whether the key is required

    Returns:
        API key value or None if not required and not found

    Raises:
        ValueError: If required key is not found
    """
    api_key = os.getenv(env_var)

    if not api_key and required:
        raise ValueError(
            f"{key_name} is required. Set the {env_var} environment variable."
        )

    return api_key


class ClientConfig:
    """Base configuration for LLM client initialization."""

    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        max_retries: int = 3,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.extra_params = kwargs

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        config = {
            "model": self.model,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
        }

        if self.api_key:
            config["api_key"] = self.api_key
        if self.base_url:
            config["base_url"] = self.base_url

        config.update(self.extra_params)
        return {k: v for k, v in config.items() if v is not None}


def validate_response_model(response_model: type[T]) -> type[T]:
    """
    Validate that a response model is a proper Pydantic model.

    Args:
        response_model: The model class to validate

    Returns:
        The validated model class

    Raises:
        TypeError: If the model is not a valid Pydantic model
    """
    try:
        from pydantic import BaseModel

        if not issubclass(response_model, BaseModel):
            raise TypeError(f"{response_model} must be a Pydantic BaseModel")

        return response_model
    except ImportError as original_error:
        raise ImportError(
            "pydantic", "pip install pydantic", "for response model validation"
        ) from original_error


def log_llm_request(func):
    """Decorator to log LLM requests for debugging."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"LLM request: {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"LLM response: {func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"LLM error: {func.__name__} failed with {e}")
            raise

    return wrapper


def standardize_messages(messages: str | list[dict[str, str]]) -> list[dict[str, str]]:
    """
    Standardize message format across different LLM providers.

    Args:
        messages: Either a string or list of message dictionaries

    Returns:
        Standardized list of message dictionaries
    """
    if isinstance(messages, str):
        return [{"role": "user", "content": messages}]

    if isinstance(messages, list):
        standardized = []
        for msg in messages:
            if isinstance(msg, dict):
                # Ensure required fields
                if "content" not in msg:
                    raise ValueError("Message must have 'content' field")
                if "role" not in msg:
                    msg["role"] = "user"  # Default role
                standardized.append(msg)
            else:
                raise TypeError("Messages must be dictionaries")
        return standardized

    raise TypeError("Messages must be string or list of dictionaries")


class RetryMixin:
    """Mixin for adding retry logic to client operations."""

    def _retry_operation(self, operation, max_retries: int = 3, **kwargs):
        """Retry an operation with exponential backoff."""
        import time

        for attempt in range(max_retries):
            try:
                return operation(**kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e

                wait_time = 2**attempt  # Exponential backoff
                logger.warning(
                    f"Operation failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}"
                )
                time.sleep(wait_time)


# Version management utilities
class VersionManager:
    """Utility for managing consistent versioning across packages."""

    # Define version categories for different package types
    CORE_VERSION = "0.3.0"  # Core packages (hacs-core, hacs-models)
    INTEGRATION_VERSION = "0.2.0"  # Integration packages (hacs-openai, hacs-anthropic)
    TOOL_VERSION = "1.3.0"  # Tool packages (hacs-tools)
    UTILITY_VERSION = "0.1.0"  # Utility packages (hacs-cli, hacs-api)

    @classmethod
    def get_version_for_package(cls, package_name: str) -> str:
        """Get the appropriate version for a package based on its type."""
        if package_name in ["hacs-core", "hacs-models"]:
            return cls.CORE_VERSION
        elif package_name in [
            "hacs-openai",
            "hacs-anthropic",
            "hacs-langgraph",
            "hacs-crewai",
        ]:
            return cls.INTEGRATION_VERSION
        elif package_name == "hacs-tools":
            return cls.TOOL_VERSION
        else:
            return cls.UTILITY_VERSION


def _get_model_class(resource_type: str):
    """Get the model class for a resource type."""
    try:
        from hacs_core import (
            Patient, Observation, Encounter, AgentMessage,
            AllergyIntolerance, Condition, Medication, MedicationRequest,
            PlanDefinition, ActivityDefinition, Library,
            GuidanceResponse, RequestOrchestration,
            DataRequirement, EvidenceVariable, ArtifactAssessment,
            Memory, KnowledgeItem
        )

        model_map = {
            "Patient": Patient, "Observation": Observation, "Encounter": Encounter,
            "AgentMessage": AgentMessage, "AllergyIntolerance": AllergyIntolerance,
            "Condition": Condition, "Medication": Medication, "MedicationRequest": MedicationRequest,
            "PlanDefinition": PlanDefinition, "ActivityDefinition": ActivityDefinition,
            "Library": Library, "GuidanceResponse": GuidanceResponse,
            "RequestOrchestration": RequestOrchestration, "DataRequirement": DataRequirement,
            "EvidenceVariable": EvidenceVariable, "ArtifactAssessment": ArtifactAssessment,
            "Memory": Memory, "KnowledgeItem": KnowledgeItem
        }

        return model_map.get(resource_type)
    except ImportError:
        return None
