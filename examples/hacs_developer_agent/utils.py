"""Utility functions used in the HACS developer agent graph."""

from typing import Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AnyMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI

from configuration import Configuration


def get_message_text(msg: AnyMessage) -> str:
    """Get the text content of a message."""
    content = msg.content
    if isinstance(content, str):
        return content
    elif isinstance(content, dict):
        return content.get("text", "")
    else:
        txts = [c if isinstance(c, str) else (c.get("text") or "") for c in content]
        return "".join(txts).strip()


def init_model(config: Optional[RunnableConfig] = None) -> BaseChatModel:
    """Initialize the configured chat model."""
    try:
        configuration = Configuration.from_runnable_config(config)
        fully_specified_name = configuration.model
    except:
        # Fallback for testing when no config is available
        fully_specified_name = "gpt-4"

    if "/" in fully_specified_name:
        provider, model = fully_specified_name.split("/", maxsplit=1)
    else:
        provider = "openai"  # Default provider
        model = fully_specified_name

    if provider == "anthropic":
        return ChatAnthropic(model=model, temperature=0.1)
    elif provider == "openai":
        # For testing, allow creating model without API key validation
        import os
        api_key = os.getenv("OPENAI_API_KEY", "test-key-for-import-testing")
        return ChatOpenAI(model=model, temperature=0.1, api_key=api_key)
    else:
        # Default to OpenAI if provider is unknown
        import os
        api_key = os.getenv("OPENAI_API_KEY", "test-key-for-import-testing")
        return ChatOpenAI(model=model, temperature=0.1, api_key=api_key)


def format_hacs_guidance(
    operation_type: str,
    result_data: dict,
    developer_context: str = ""
) -> str:
    """Format HACS development guidance for display to developers."""

    if operation_type == "model_discovery":
        models = result_data.get("models", [])
        if models:
            response = (
                f"🔍 **Found {len(models)} HACS models for your healthcare development:**\n\n"
            )
            for model in models[:5]:  # Show first 5
                name = model.get("name", "Unknown")
                desc = model.get("description", "No description")
                usage = model.get("usage_guidance", "See documentation for usage")
                response += f"### {name}\n{desc}\n💡 **Usage**: {usage}\n\n"
            if len(models) > 5:
                response += f"... and {len(models) - 5} more models available\n"
        else:
            response = "No HACS models found matching your criteria."

    elif operation_type == "template_generation":
        template = result_data.get("template")
        if template:
            response = "🛠️ **Generated Clinical Template:**\n\n"
            response += f"**Name**: {template.get('name', 'Untitled')}\n"
            response += f"**Use Case**: {template.get('use_case', 'General healthcare')}\n"
            response += f"**Description**: {template.get('description', 'No description')}\n\n"

            if template.get("required_models"):
                models_list = ', '.join(template['required_models'])
                response += f"**Required HACS Models**: {models_list}\n\n"

            if template.get("implementation_guidance"):
                guidance = template['implementation_guidance']
                response += f"**Implementation Guidance**:\n{guidance}\n\n"

        else:
            response = "❌ Failed to generate clinical template."

    elif operation_type == "model_stack":
        stack = result_data.get("model_stack")
        if stack:
            response = "🏗️ **Created Healthcare Model Stack:**\n\n"
            response += f"**Stack Name**: {stack.get('name', 'Unknown')}\n"
            response += f"**Models**: {', '.join(stack.get('models', []))}\n"
            response += f"**Purpose**: {stack.get('purpose', 'Healthcare workflow')}\n\n"

            if stack.get("integration_guidance"):
                response += f"**Integration Guide**:\n{stack['integration_guidance']}\n"
        else:
            response = "❌ Failed to create model stack."

    elif operation_type == "resource_creation":
        resource = result_data.get("resource")
        if resource:
            response = "✅ **Created Healthcare Resource:**\n\n"
            response += f"**Type**: {resource.get('resourceType', 'Unknown')}\n"
            response += f"**ID**: {resource.get('id', 'Generated')}\n"

            if resource.get("validation_results"):
                validation = resource["validation_results"]
                status = "✅ Valid" if validation.get("is_valid") else "⚠️ Issues found"
                response += f"**FHIR Validation**: {status}\n"
        else:
            response = "❌ Failed to create resource."

    else:
        response = "✅ HACS operation completed successfully."

    if developer_context:
        response += f"\n💡 **Context**: {developer_context}"

    return response


def determine_hacs_operation(developer_request: str) -> str:
    """Determine the type of HACS operation based on the developer's request."""
    request_lower = developer_request.lower()

    if any(word in request_lower for word in ["discover", "find", "search", "available", "models"]):
        return "model_discovery"
    elif any(word in request_lower for word in ["template", "workflow", "clinical", "use case"]):
        return "template_generation"
    elif any(word in request_lower for word in ["stack", "combine", "integrate", "compose"]):
        return "model_stack"
    elif any(word in request_lower for word in ["create", "build", "resource", "example"]):
        return "resource_creation"
    elif any(word in request_lower for word in ["definition", "schema", "details", "explain"]):
        return "model_definition"
    else:
        return "general_guidance"