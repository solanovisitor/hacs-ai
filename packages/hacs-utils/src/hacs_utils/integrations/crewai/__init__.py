"""
HACS CrewAI Integration

This module provides CrewAI integration for HACS (Healthcare Agent
Communication Standard). It enables seamless integration between HACS clinical
data models and CrewAI multi-agent workflows.
"""

from .adapter import (
    CrewAIAdapter,
    CrewAIAgentBinding,
    CrewAIAgentRole,
    CrewAITask,
    CrewAITaskType,
    create_agent_binding,
    task_to_crew_format,
)

__version__ = "0.2.0"
__all__ = [
    "CrewAIAdapter",
    "CrewAIAgentRole",
    "CrewAITaskType",
    "CrewAITask",
    "CrewAIAgentBinding",
    "create_agent_binding",
    "task_to_crew_format",
]