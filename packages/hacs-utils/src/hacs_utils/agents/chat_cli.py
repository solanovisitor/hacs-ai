"""CLI chat interface for HACS agent."""

import asyncio
import json
import os
from typing import Any, Dict

import aiohttp


class HACSAgentCLI:
    """CLI interface for chatting with the HACS developer agent."""

    def __init__(self, agent_url: str = "http://localhost:8001"):
        self.agent_url = agent_url

    async def send_message(self, message: str) -> Dict[str, Any]:
        """Send a message to the HACS agent."""
        payload = {
            "developer_request": message,
            "hacs_guidance_schema": {
                "type": "object",
                "properties": {
                    "guidance_type": {
                        "type": "string",
                        "description": "Type of HACS guidance provided"
                    },
                    "models_suggested": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "HACS models recommended for this use case"
                    },
                    "implementation_steps": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Step-by-step implementation guidance"
                    },
                    "sample_code": {
                        "type": "string",
                        "description": "Sample code or templates"
                    },
                    "best_practices": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Best practices and recommendations"
                    },
                    "next_steps": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Suggested next steps for the developer"
                    }
                }
            }
        }

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=120)
            ) as session:
                async with session.post(
                    f"{self.agent_url}/invoke",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result
                    else:
                        error_text = await response.text()
                        return {
                            "error": f"HTTP {response.status}: {error_text}"
                        }
        except asyncio.TimeoutError:
            return {"error": "Request timed out after 120 seconds"}
        except Exception as e:
            return {"error": f"Connection error: {str(e)}"}

    async def health_check(self) -> bool:
        """Check if the agent is healthy."""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            ) as session:
                async with session.get(f"{self.agent_url}/health") as response:
                    return response.status == 200
        except Exception:
            return False

    def format_response(self, response: Dict[str, Any]) -> str:
        """Format the agent response for display."""
        if "error" in response:
            return f"❌ Error: {response['error']}"

        if "messages" in response:
            # Extract the last assistant message
            messages = response["messages"]
            for msg in reversed(messages):
                if msg.get("type") == "ai":
                    return msg.get("content", "No response content")

        # Handle recursion limit messages
        if "recursion_limit" in str(response).lower():
            return "⚠️ The agent reached its processing limit. This indicates the conversation needs to be simplified or broken into smaller parts."

        # Try to parse as structured response
        if isinstance(response, dict):
            formatted_parts = []
            for key, value in response.items():
                if key != "messages":
                    formatted_parts.append(f"**{key.replace('_', ' ').title()}:**")
                    if isinstance(value, list):
                        for item in value:
                            formatted_parts.append(f"  • {item}")
                    else:
                        formatted_parts.append(f"  {value}")

            if formatted_parts:
                return "\n".join(formatted_parts)

        return json.dumps(response, indent=2)

    async def run_chat(self):
        """Run the interactive chat interface."""
        print("🏥 HACS Developer Agent Chat")
        print("=" * 40)
        print("Type your questions about HACS development.")
        print("Commands: 'health' (check status), 'quit' (exit)")
        print("=" * 40)

        # Check agent health
        if not await self.health_check():
            print("⚠️  Warning: Agent health check failed. Continuing anyway...")
        else:
            print("✅ Agent is healthy and ready!")

        print()

        while True:
            try:
                user_input = input("\n💬 You: ").strip()

                if user_input.lower() in ["quit", "exit", "q"]:
                    print("👋 Goodbye!")
                    break

                if user_input.lower() == "health":
                    is_healthy = await self.health_check()
                    status = "✅ Healthy" if is_healthy else "❌ Unhealthy"
                    print(f"🔍 Agent Status: {status}")
                    continue

                if not user_input:
                    continue

                print("🤖 Agent: ", end="", flush=True)

                response = await self.send_message(user_input)
                formatted_response = self.format_response(response)
                print(formatted_response)

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {str(e)}")


async def main():
    """Main CLI entry point."""
    agent_url = os.getenv("HACS_AGENT_URL", "http://localhost:8001")
    cli = HACSAgentCLI(agent_url)
    await cli.run_chat()


if __name__ == "__main__":
    asyncio.run(main())