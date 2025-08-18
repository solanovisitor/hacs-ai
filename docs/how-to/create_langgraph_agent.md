# Create a simple agent with LangGraph

```python
# Prereq: uv pip install -U hacs-utils[langchain,langgraph]
from langgraph.prebuilt import create_react_agent
from hacs_utils.integrations.langchain.tools import langchain_tools

# Provision tools
tools = langchain_tools()

# Minimal agent
agent = create_react_agent(model="anthropic:claude-3-7-sonnet-latest", tools=tools,
                           prompt="You are a healthcare assistant using HACS tools.")
print("Agent ready with", len(tools), "tools")
```
