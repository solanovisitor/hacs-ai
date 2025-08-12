"""
HACS Agent Tools for LangGraph Integration

This module provides LangGraph-specific tool integration for HACS (Healthcare Agent Communication Standard),
designed for healthcare AI agents with proper permission control and domain organization.

Features:
- LangGraph agent tool management with HACS registry integration
- Rule-based permission control via HACS Actor system
- Healthcare-compliant access control (RBAC)
- Audit trails and compliance monitoring
- 10 healthcare domain categories with 32+ specialized tools
- Centralized tool loading via common utilities

Tool Categories:
🏥 Resource Management - CRUD operations for healthcare resources
🧠 Clinical Workflows - Clinical protocols and decision support
💭 Memory Operations - AI agent memory management
🔍 Vector Search - Semantic search and embedding operations
📊 Schema Discovery - Resource schema analysis and discovery
🛠️ Development Tools - Advanced resource composition and templates
🏥 FHIR Integration - Healthcare standards compliance
📈 Healthcare Analytics - Quality measures and population health
🤖 AI/ML Integration - Healthcare AI model deployment
⚙️ Admin Operations - Database and system management
"""

import logging
from typing import List, Any, Optional
from functools import wraps

# Import centralized tool loading
from ..common.tool_loader import get_all_hacs_tools_sync, get_availability

# Import LangGraph-specific custom tools
from .custom_tools import CUSTOM_LANGGRAPH_TOOLS

# LangGraph framework imports
try:
    from langchain_core.tools import tool, BaseTool
    from langchain_core.messages import ToolMessage
    from langgraph.types import Command
    from langgraph.prebuilt import InjectedState
    from typing import Annotated
    _has_langchain = True
except ImportError:
    # Fallback for environments without LangChain/LangGraph
    _has_langchain = False
    def tool(description=""):
        def decorator(func):
            func.description = description
            func.name = func.__name__
            return func
        return decorator

    class BaseTool:
        pass

    class ToolMessage:
        def __init__(self, content, tool_call_id=None):
            self.content = content
            self.tool_call_id = tool_call_id

    class Command:
        def __init__(self, update=None):
            self.update = update or {}

    def InjectedState(cls):
        return cls

    from typing import Annotated

# Configure logging
logger = logging.getLogger(__name__)

# === ACTOR AND PERMISSION MANAGEMENT ===

class HACSActor:
    """Mock Actor class when HACS Core is not available."""
    def __init__(self, actor_id: str = "hacs_agent", role: str = "ai_agent"):
        self.actor_id = actor_id
        self.role = role
        self.permissions = ["read", "write", "admin"]  # Mock permissions

    def check_permission(self, resource: str, action: str) -> bool:
        """Mock permission check - always returns True in development."""
        return True

def get_hacs_actor():
    """Get HACS Actor with fallback to mock."""
    availability = get_availability()

    if availability['hacs_core']:
        try:
            from hacs_models import Actor
            from hacs_core.config import get_hacs_config
            config = get_hacs_config()
            return Actor(
                actor_id="hacs_agent",
                role="ai_agent",
                permissions=["healthcare_admin", "database_admin", "clinical_read"]
            )
        except Exception as e:
            logger.warning(f"Failed to create HACS Actor: {e}")

    return HACSActor()

def permission_required(resource: str, access_level: str = "read"):
    """Decorator for permission-controlled tool access."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            actor = get_hacs_actor()
            availability = get_availability()

            if availability['hacs_registry']:
                try:
                    from hacs_registry import get_global_iam_registry, AccessLevel
                    iam = get_global_iam_registry()
                    required_access = AccessLevel.WRITE if access_level == "write" else AccessLevel.READ
                    if access_level == "admin":
                        required_access = AccessLevel.ADMIN

                    if not iam.check_access(actor.actor_id, resource, required_access):
                        return f"❌ Permission denied: Actor {actor.actor_id} lacks {access_level} access to {resource}"
                except Exception as e:
                    logger.warning(f"IAM check failed: {e}")
            else:
                # Fallback permission check
                if not actor.check_permission(resource, access_level):
                    return f"❌ Permission denied: {access_level} access to {resource} not allowed"

            return func(*args, **kwargs)
        return wrapper
    return decorator

# === HACS AGENT TOOLS INTEGRATION ===

def get_hacs_agent_tools() -> List[Any]:
    """
    Main function to get all HACS tools for LangGraph agents with permission control.

    Combines centralized HACS tools with LangGraph-specific custom tools.

    Returns:
        List of HACS tools organized by healthcare domains,
        with proper permission control and audit trails,
        plus LangGraph-specific custom tools for agent operations.
    """
    # Get centralized HACS tools
    hacs_tools = get_all_hacs_tools_sync(framework="langgraph")

    # Add LangGraph-specific custom tools
    all_tools = hacs_tools + CUSTOM_LANGGRAPH_TOOLS

    logger.info(f"✅ Loaded {len(hacs_tools)} HACS tools + {len(CUSTOM_LANGGRAPH_TOOLS)} custom LangGraph tools")

    return all_tools

# Export the main function and classes
__all__ = ["get_hacs_agent_tools", "HACSActor", "get_hacs_actor", "permission_required"]