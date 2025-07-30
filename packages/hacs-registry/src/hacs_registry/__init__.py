"""
HACS Registry - Resource, prompt, and workflow definitions.

This package provides the domain models for defining and managing versioned
healthcare AI resources including resource schemas, prompt templates, and workflow definitions.
"""

from .definitions import ResourceDefinition, ModelDefinition, PromptDefinition, WorkflowDefinition
from .exceptions import RegistryError

__version__ = "0.1.0"

__all__ = [
    "ResourceDefinition",
    "ModelDefinition",  # Backwards compatibility
    "PromptDefinition",
    "WorkflowDefinition",
    "RegistryError",
]
