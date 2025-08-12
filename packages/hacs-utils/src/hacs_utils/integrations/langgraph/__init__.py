"""
LangGraph Integration for HACS

Provides LangGraph workflow orchestration for healthcare AI applications.
"""

try:
    from langgraph.graph import StateGraph as LangGraphStateGraph
    _has_langgraph = True
except ImportError:
    _has_langgraph = False
    LangGraphStateGraph = None


# Placeholder class for when LangGraph is not available
class StateGraph:
    def __init__(self):
        self.nodes = {}
        self.edges = []

    def add_node(self, name: str, func):
        self.nodes[name] = func

    def add_edge(self, from_node: str, to_node: str):
        self.edges.append((from_node, to_node))

    def compile(self):
        return LangGraphWorkflow(self.nodes, self.edges)


class LangGraphWorkflow:
    """LangGraph workflow for healthcare processes."""

    def __init__(self, nodes: dict = None, edges: list = None):
        """Initialize workflow."""
        self.nodes = nodes or {}
        self.edges = edges or []

    def invoke(self, input_data: dict) -> dict:
        """Execute the workflow."""
        # Simple placeholder execution
        result = input_data.copy()
        result["processed"] = True
        return result


class HealthcareWorkflowBuilder:
    """Builder for healthcare-specific LangGraph workflows."""

    def __init__(self):
        """Initialize builder."""
        if _has_langgraph and LangGraphStateGraph:
            self.graph = LangGraphStateGraph()
        else:
            self.graph = StateGraph()

    def add_patient_assessment_node(self, func):
        """Add patient assessment node."""
        self.graph.add_node("patient_assessment", func)
        return self

    def add_diagnosis_node(self, func):
        """Add diagnosis node."""
        self.graph.add_node("diagnosis", func)
        return self

    def add_treatment_planning_node(self, func):
        """Add treatment planning node."""
        self.graph.add_node("treatment_planning", func)
        return self

    def build(self) -> LangGraphWorkflow:
        """Build the workflow."""
        return self.graph.compile()


def create_langgraph_workflow() -> LangGraphWorkflow:
    """Create a LangGraph workflow."""
    builder = HealthcareWorkflowBuilder()
    return builder.build()


def create_healthcare_workflow() -> HealthcareWorkflowBuilder:
    """Create a healthcare workflow builder."""
    return HealthcareWorkflowBuilder()


# Import HACS agent tools integration
try:
    from .hacs_agent_tools import (
        get_hacs_agent_tools,
        HACSActor,
        get_hacs_actor,
        permission_required,
    )
    _has_agent_tools = True
except ImportError:
    _has_agent_tools = False
    get_hacs_agent_tools = None
    HACSActor = None
    get_hacs_actor = None
    permission_required = None

# Import custom LangGraph tools
try:
    from .custom_tools import (
        CUSTOM_LANGGRAPH_TOOLS,
        create_scratchpad_todo,
        write_file,
        read_file,
        edit_file,
        validate_hacs_integration,
        discover_available_tools,
        delegate_to_subagent,
    )
    _has_custom_tools = True
except ImportError:
    _has_custom_tools = False
    CUSTOM_LANGGRAPH_TOOLS = []

__all__ = [
    "LangGraphWorkflow",
    "HealthcareWorkflowBuilder",
    "create_langgraph_workflow",
    "create_healthcare_workflow",
    "StateGraph",
]

# Add agent tools exports if available
if _has_agent_tools:
    __all__.extend([
        "get_hacs_agent_tools",
        "HACSActor",
        "get_hacs_actor",
        "permission_required",
    ])

# Add custom tools exports if available
if _has_custom_tools:
    __all__.extend([
        "CUSTOM_LANGGRAPH_TOOLS",
        "create_scratchpad_todo",
        "write_file",
        "read_file",
        "edit_file",
        "validate_hacs_integration",
        "discover_available_tools",
        "delegate_to_subagent",
    ])