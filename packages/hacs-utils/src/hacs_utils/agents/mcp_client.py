"""Direct MCP client for HACS."""

import asyncio
import json
from typing import Any, Dict, List, Optional

import aiohttp
import anthropic


class HACSMCPClient:
    """Direct client for HACS MCP server."""

    def __init__(
        self,
        mcp_server_url: str = "http://localhost:8000",
        anthropic_api_key: Optional[str] = None,
    ):
        self.mcp_server_url = mcp_server_url
        self.anthropic_client = None
        if anthropic_api_key:
            self.anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)

    async def call_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a tool on the MCP server."""
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
            "id": 1,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.mcp_server_url, json=payload
            ) as response:
                result = await response.json()
                if "error" in result:
                    raise Exception(f"MCP Error: {result['error']}")
                return result.get("result", {})

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the MCP server."""
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 1,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.mcp_server_url, json=payload
            ) as response:
                result = await response.json()
                if "error" in result:
                    raise Exception(f"MCP Error: {result['error']}")
                return result.get("result", {}).get("tools", [])

    async def chat_with_hacs_guidance(self, user_message: str) -> str:
        """Use Anthropic LLM to provide HACS guidance using MCP tools."""
        if not self.anthropic_client:
            return "No LLM configured for guidance generation."

        # Get available tools
        tools = await self.list_tools()

        # Format tools for Anthropic
        anthropic_tools = []
        for tool in tools:
            anthropic_tools.append({
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool.get("inputSchema", {}),
            })

        # Create system prompt
        system_prompt = """You are a HACS (Healthcare Agent Communication Standard) developer assistant.

Use the available HACS tools to:
- Discover relevant healthcare models for developer needs
- Create clinical templates and workflows
- Generate sample resources and model stacks
- Provide implementation guidance and best practices

When a developer asks a question, use the tools to provide comprehensive guidance."""

        # Call Anthropic with tools
        response = self.anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            tools=anthropic_tools,
        )

        result_parts = []

        # Process the response and tool calls
        for content_block in response.content:
            if content_block.type == "text":
                result_parts.append(content_block.text)
            elif content_block.type == "tool_use":
                # Execute the tool
                try:
                    tool_result = await self.call_tool(
                        content_block.name,
                        content_block.input,
                    )
                    result_parts.append(
                        f"\n🔧 Used {content_block.name}:\n"
                        f"{json.dumps(tool_result, indent=2)}"
                    )
                except Exception as e:
                    result_parts.append(f"\n❌ Tool error: {str(e)}")

        return "\n".join(result_parts)


async def main():
    """Example usage of the HACS MCP client."""
    import os

    client = HACSMCPClient(
        mcp_server_url=os.getenv("HACS_MCP_SERVER_URL", "http://localhost:8000"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    print("HACS MCP Client Ready!")
    print("Available commands:")
    print("- Type a question to get HACS guidance")
    print("- Type 'tools' to list available tools")
    print("- Type 'quit' to exit")

    while True:
        user_input = input("\n> ").strip()

        if user_input.lower() in ["quit", "exit"]:
            break
        elif user_input.lower() == "tools":
            try:
                tools = await client.list_tools()
                print("\nAvailable HACS Tools:")
                for tool in tools:
                    print(f"- {tool['name']}: {tool['description']}")
            except Exception as e:
                print(f"Error listing tools: {e}")
        else:
            try:
                response = await client.chat_with_hacs_guidance(user_input)
                print(f"\n{response}")
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())