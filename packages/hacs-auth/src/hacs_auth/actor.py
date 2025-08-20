"""Actor models for authentication, authorization, and audit trails.

This module provides actor-related models that enable secure agent interactions
with proper permission management, authentication context, and audit logging.
Optimized for LLM generation with flexible validation and smart defaults.

Note: This module re-exports core Actor models from hacs_models to avoid duplication
while maintaining compatibility for auth-specific imports.
"""

# Re-export core models from hacs_models to maintain compatibility
from hacs_models.actor import (
    Actor,
    ActorRole,
    PermissionLevel,
    SessionStatus,
)


# Re-export all for import compatibility
__all__ = [
    "Actor",
    "ActorRole",
    "PermissionLevel",
    "SessionStatus",
]
