# Create a simple agent with LangGraph

```python
# Prereq: uv pip install -U hacs-utils[langchain,langgraph]
from hacs_utils.integrations.langchain.tools import langchain_tools

# Provision tools
tools = langchain_tools()
print("Tools ready:", len(tools), "tools")

# Optional: Create agent (requires langgraph and API keys)
# from langgraph.prebuilt import create_react_agent
# agent = create_react_agent(model="anthropic:claude-3-7-sonnet-latest", tools=tools,
#                            prompt="You are a healthcare assistant using HACS tools.")
# print("Agent ready with", len(tools), "tools")
```

**Output:**
```
Tools ready: 41 tools
```
