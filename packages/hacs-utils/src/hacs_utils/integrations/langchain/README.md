# HACS LangChain Integration

This package provides comprehensive LangChain integration for HACS (Healthcare Agent Communication Standard), enabling AI agents to work seamlessly with healthcare resources and workflows.

## 🚀 Quick Start

### Installation

The HACS LangChain integration is included in the hacs-utils package:

```bash
# Install HACS with UV
uv add hacs-utils

# Or install in development mode from source
cd packages/hacs-utils
uv sync --all-extras --dev
```

### Basic Usage

```python
from hacs_utils.integrations.langchain import get_hacs_tools

# Get all available HACS tools for LangChain agents
tools = get_hacs_tools()

# Use with any LangChain agent
from langchain.agents import create_openai_functions_agent
agent = create_openai_functions_agent(llm=llm, tools=tools, prompt=prompt)
```

### Category-Specific Tools

```python
from hacs_utils.integrations.langchain import get_hacs_tools_by_category

# Get tools by healthcare domain
resource_tools = get_hacs_tools_by_category("resource_management")
clinical_tools = get_hacs_tools_by_category("clinical_workflows")
memory_tools = get_hacs_tools_by_category("memory_operations")
```

## 🏥 Available Tool Categories

1. **Resource Management** - CRUD operations for healthcare resources (Patient, Observation, etc.)
2. **Clinical Workflows** - Clinical decision support and protocol execution
3. **Memory Operations** - AI agent memory management and retrieval
4. **Vector Search** - Semantic search capabilities for medical knowledge
5. **Schema Discovery** - Healthcare resource type discovery and analysis
6. **Development Tools** - Template generation and optimization
7. **FHIR Integration** - Healthcare standards compliance and interoperability
8. **Healthcare Analytics** - Population health and quality measures
9. **AI/ML Integration** - Healthcare model deployment and inference
10. **Admin Operations** - Database and system management

## 📁 Package Structure

```
langchain/
├── __init__.py           # Main exports and document processing
├── tools.py              # LangChain tool wrappers and registry
├── README.md             # This file
├── examples/             # Examples and demonstrations
│   ├── README.md         # Examples documentation
│   ├── demo_hacs_langchain_tools.py    # Working demo
│   └── test_hacs_langchain_tools.py    # Validation tests
├── COMPLETION_SUMMARY.md              # Implementation summary
└── HACS_LANGCHAIN_INTEGRATION_REPORT.md  # Detailed technical report
```

## 🔧 API Reference

### Core Functions

#### `get_hacs_tools()`
Returns all available HACS tools as LangChain-compatible tools.

```python
tools = get_hacs_tools()
# Returns: List[BaseTool]
```

#### `get_hacs_tool(name: str)`
Returns a specific HACS tool by name.

```python
discovery_tool = get_hacs_tool("discover_hacs_resources")
```

#### `get_hacs_tools_by_category(category: str)`
Returns tools filtered by healthcare domain category.

```python
clinical_tools = get_hacs_tools_by_category("clinical_workflows")
```

#### `validate_tool_inputs(tool_name: str, inputs: Dict)`
Validates inputs for a specific tool.

```python
is_valid = validate_tool_inputs("create_hacs_record", {
    "resource_type": "Patient",
    "resource_data": patient_data
})
```

### Document Processing

#### `LangChainDocumentAdapter`
Adapter for processing healthcare documents with LangChain.

```python
from hacs_utils.integrations.langchain import LangChainDocumentAdapter

adapter = LangChainDocumentAdapter(chunk_size=1000, chunk_overlap=200)
documents = adapter.process_text(clinical_text, metadata={"source": "ehr"})
```

## 🧪 Examples and Testing

See the `examples/` directory for:

- **Demo Script**: Working demonstration of all tool categories
- **Test Suite**: Comprehensive validation of the integration
- **Examples Documentation**: Detailed usage examples

```bash
# Run the demo
cd packages/hacs-utils/src/hacs_utils/integrations/langchain/examples
python demo_hacs_langchain_tools.py

# Run validation tests
python test_hacs_langchain_tools.py
```

## 🏗️ Architecture

### Tool Wrapper System

HACS tools are wrapped using LangChain's `StructuredTool` with:

- **Pydantic Schemas**: Comprehensive input validation
- **Error Handling**: Robust error handling following LangChain patterns
- **Async Support**: Full async/await compatibility
- **Metadata**: Rich tool metadata for agent decision-making

### Registry Management

The `HACSToolRegistry` provides:

- **Lazy Loading**: Tools loaded on-demand to avoid import issues
- **Categorization**: Tools organized by healthcare domain
- **Discovery**: Search and filtering capabilities
- **Validation**: Input schema validation and type checking

## 🔗 Integration with Agent Frameworks

### LangGraph

```python
from langgraph.graph import StateGraph
from hacs_utils.integrations.langchain import get_hacs_tools

# Create workflow with HACS tools
tools = get_hacs_tools()
workflow = StateGraph(state_schema)
workflow.add_node("agent", create_agent_executor(tools))
```

### CrewAI

```python
from crewai import Agent, Task, Crew
from hacs_utils.integrations.langchain import get_hacs_tools_by_category

# Create healthcare specialist agents
clinical_agent = Agent(
    role="Clinical Specialist",
    tools=get_hacs_tools_by_category("clinical_workflows")
)
```

### LangChain Agents

```python
from langchain.agents import create_openai_functions_agent
from hacs_utils.integrations.langchain import get_hacs_tools

agent = create_openai_functions_agent(
    llm=llm,
    tools=get_hacs_tools(),
    prompt=healthcare_prompt
)
```

## 🐛 Known Issues & Workarounds

### LangChain Import Issues
Some environments may experience import issues with `langchain_core.runnables.base`. The integration uses lazy loading to mitigate this.

**Workaround**: Use the demo scripts which include mock implementations showing the expected interface.

## 📊 Performance Considerations

- **Lazy Loading**: Tools are loaded on-demand to minimize startup time
- **Caching**: Tool registry implements caching for repeated access
- **Async Support**: All tools support async execution for better performance
- **Validation**: Input validation is performed efficiently using Pydantic

## 🔮 Future Enhancements

1. **Enhanced Async Support** - Full async/await for all operations
2. **Tool Composition** - Ability to compose multiple tools into workflows
3. **Smart Caching** - Intelligent caching of tool results
4. **Performance Monitoring** - Built-in performance metrics and monitoring
5. **Advanced Validation** - Context-aware input validation

## 📞 Support

For questions about the HACS LangChain integration:

- **Documentation**: See the `examples/` directory for detailed examples
- **Issues**: Report issues in the main HACS repository
- **Community**: Join the HACS developer community

---

*Part of the HACS (Healthcare Agent Communication Standard) project*