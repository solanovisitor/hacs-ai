"""
HACS Deep Agent

A LangGraph-based deep agent that can iterate on HACS tool calls and use
HACS resources for healthcare-specific state management and clinical workflows.

This example demonstrates how to create healthcare AI agents that can:
- Use all 37 HACS healthcare tools
- Represent state using HACS resources (Patient, Observation, etc.)
- Iterate on clinical workflows and decision making
- Manage healthcare-specific subagents

Author: HACS Development Team
License: MIT
Version: 0.3.0
"""

from .agent import create_hacs_deep_agent, HACSDeepAgent
from .state import HACSAgentState
from .subagents import CLINICAL_SUBAGENTS

__all__ = [
    "create_hacs_deep_agent",
    "HACSDeepAgent", 
    "HACSAgentState",
    "CLINICAL_SUBAGENTS"
] 