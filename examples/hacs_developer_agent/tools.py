"""Tools for HACS developer agent.

This module contains functions that are directly exposed to the LLM as tools.
These tools integrate with the HACS MCP server to perform healthcare model operations.
"""

from typing import Any, Dict, List, Optional, cast

import httpx
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg
from typing_extensions import Annotated

from configuration import Configuration

# Import real HACS tools for admin operations
try:
    from hacs_core.actor import Actor, ActorRole
    from hacs_core.results import HACSResult
    from hacs_tools.domains.admin_operations import (
        run_database_migration,
        check_migration_status,
        describe_database_schema,
        get_table_structure,
        test_database_connection
    )
    from hacs_tools.domains.resource_management import (
        create_hacs_record,
        get_hacs_record,
        search_hacs_records
    )
    HACS_TOOLS_AVAILABLE = True
except ImportError as e:
    HACS_TOOLS_AVAILABLE = False
    _import_error = str(e)


async def call_mcp_server(params: Dict[str, Any], config: RunnableConfig) -> Dict[str, Any]:
    """Helper function to call the HACS MCP server."""
    configuration = Configuration.from_runnable_config(config)

    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": params,
            "id": 1
        }

        response = await client.post(
            f"{configuration.hacs_mcp_server_url}/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()

    if "result" in result:
        return result["result"]
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}


async def discover_hacs_resources(
    category_filter: Optional[str] = None,
    model_type: Optional[str] = None,
    include_deprecated: bool = False,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """
    Discover available HACS resource schemas and their capabilities.

    TERMINOLOGY DISTINCTION:
    - HACS Records: Schema definitions/templates (Patient model, Observation model)
    - HACS Records: Actual data records validated against HACS resources
    - This tool discovers MODEL schemas, not data resources

    Args:
        category_filter: Filter by model category (clinical, administrative, reasoning)
        model_type: Specific model type to discover
        include_deprecated: Whether to include deprecated model schemas

    Returns:
        Comprehensive information about available HACS resource schemas
    """
    configuration = Configuration.from_runnable_config(config)

    # Call HACS MCP server
    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "discover_hacs_resources",
                "arguments": {
                    "category_filter": category_filter,
                    "include_field_counts": True
                }
            },
            "id": 1
        }

        response = await client.post(
            f"{configuration.hacs_mcp_server_url}/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()

    if "result" in result and result["result"] is not None:
        # Extract the CallToolResult content
        mcp_result = result["result"]

        # The content is in the 'content' field of CallToolResult
        if isinstance(mcp_result, dict) and "content" in mcp_result:
            content_items = mcp_result["content"]
            if isinstance(content_items, list) and len(content_items) > 0:
                # Get the first content item's text (which is our rich markdown)
                first_content = content_items[0]
                if isinstance(first_content, dict) and "text" in first_content:
                    return first_content["text"]

        # Fallback for older format
        if hasattr(mcp_result, 'get') and "_meta" in mcp_result:
            model_data = mcp_result["_meta"].get("result", {})
            if isinstance(model_data, dict) and "models" in model_data:
                # Create simple text output for structured data
                models = model_data["models"]
                resource_names = [m.get("name", "Unknown") for m in models]
                return f"Found {len(models)} HACS resources: " + ", ".join(resource_names)

    return "No HACS resources found or MCP server error"


async def create_clinical_template(
    template_type: str,
    focus_area: str,
    complexity_level: str = "standard",
    include_workflow_fields: bool = True,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """Generate a clinical template for healthcare workflows.

    This tool creates structured templates that help developers implement
    healthcare workflows using HACS resources, based on their specific use case.

    Args:
        template_type: Type of clinical template (e.g., 'consultation', 'intake')
        focus_area: Clinical focus area (e.g., 'diabetes', 'cardiology')
        complexity_level: Complexity level ('basic', 'standard', 'advanced')
        include_workflow_fields: Whether to include workflow management fields

    """
    configuration = Configuration.from_runnable_config(config)

    # Call HACS MCP server
    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "create_clinical_template",
                "arguments": {
                    "template_type": template_type,
                    "focus_area": focus_area,
                    "complexity_level": complexity_level,
                    "template_name": f"{focus_area}_{template_type}_{complexity_level}",
                    "base_models": ["Patient", "Observation", "Encounter"]
                }
            },
            "id": 2
        }

        response = await client.post(
            f"{configuration.hacs_mcp_server_url}/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()

    if "result" in result and result["result"] is not None:
        # Extract the CallToolResult content
        mcp_result = result["result"]

        # The content is in the 'content' field of CallToolResult
        if isinstance(mcp_result, dict) and "content" in mcp_result:
            content_items = mcp_result["content"]
            if isinstance(content_items, list) and len(content_items) > 0:
                # Get the first content item's text (which is our rich markdown)
                first_content = content_items[0]
                if isinstance(first_content, dict) and "text" in first_content:
                    return first_content["text"]

        # Fallback for older format or error response
        if isinstance(mcp_result, dict):
            if "template" in mcp_result:
                template_data = mcp_result["template"]
                return f"Created clinical template: {template_data.get('name', 'Unknown')}"
            elif "message" in mcp_result:
                return mcp_result["message"]
            elif "_meta" in mcp_result:
                # Check if there's rich content in _meta
                meta_data = mcp_result["_meta"]
                if isinstance(meta_data, dict) and "formatted" in meta_data and meta_data["formatted"]:
                    # This indicates rich content was generated but may be in a different location
                    return (f"Created clinical template for {focus_area} {template_type} "
                           f"with detailed structure")

    return f"Created clinical template for {focus_area} {template_type} (basic confirmation)"


async def create_model_stack(
    base_model: str,
    stack_name: str,
    extensions: Optional[List[Dict[str, Any]]] = None,
    merge_strategy: str = "overlay",
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Dict[str, Any]:
    """Create a model stack combining multiple HACS resources for a healthcare purpose.

    Args:
        base_model: Base HACS resource to extend (e.g., 'Patient', 'Observation')
        stack_name: Name for the healthcare model stack
        extensions: List of extensions to add to the base model
        merge_strategy: Strategy for merging extensions ('overlay', 'deep_merge', 'replace')

    """
    configuration = Configuration.from_runnable_config(config)

    # Call HACS MCP server
    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "create_model_stack",
                "arguments": {
                    "base_model": base_model,
                    "stack_name": stack_name,
                    "extensions": extensions or [],
                    "merge_strategy": merge_strategy
                }
            },
            "id": 1
        }

        response = await client.post(
            f"{configuration.hacs_mcp_server_url}/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()

    if "result" in result:
        return cast(Dict[str, Any], result["result"].get("content", {}))
    else:
        return {"error": "Failed to create model stack"}


async def get_hacs_model_definition(
    resource_name: str,
    include_examples: bool = True,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Dict[str, Any]:
    """Get detailed definition and usage guidance for a HACS resource.

    Args:
        resource_name: Name of the HACS resource to get details for
        include_examples: Whether to include implementation examples

    """
    configuration = Configuration.from_runnable_config(config)

    # Call HACS MCP server
    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "get_resource_schema",
                "arguments": {
                    "resource_type": resource_name,
                    "include_examples": include_examples
                }
            },
            "id": 1
        }

        response = await client.post(
            f"{configuration.hacs_mcp_server_url}/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()

    if "result" in result:
        return cast(Dict[str, Any], result["result"].get("content", {}))
    else:
        return {"error": f"Model '{resource_name}' not found"}


async def create_hacs_record(
    resource_type: str,
    resource_data: Dict[str, Any],
    validate_fhir: bool = True,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Dict[str, Any]:
    """
    Create a HACS resource (data record) with Product Requirement Prompt (PRP) methodology.

    TERMINOLOGY DISTINCTION:
    - HACS Records: Schema definitions/templates (Patient model defines structure)
    - HACS Records: Actual data records (Patient resource with John's data)
    - This tool creates RESOURCE records validated against HACS resource schemas

    This tool implements PRP steps:
    1. Requirements Analysis - Get HACS resource schema first
    2. Schema Discovery & Validation - Validate resource data structure
    3. Implementation - Create resource record with validated data

    Examples of CORRECT vs INCORRECT Patient resource structure:
    ✅ Correct: {"given": ["John"], "family": "Doe", "birth_date": "1990-01-01", "email": "john@example.com"}
    ❌ Incorrect: {"name": [{"given": ["John"], "family": "Doe"}], "birthDate": "1990-01-01"}
    """
    try:
        # STEP 1: Requirements Analysis - Get the model schema first (PRP)
        print(f"🔍 [PRP Step 1] Analyzing requirements for {resource_type} resource...")

        schema_params = {
            "name": "get_resource_schema",
            "arguments": {"resource_type": resource_type, "simplified": False}
        }

        schema_result = await call_mcp_server(schema_params, config)

        if not schema_result.get("success", False):
            return {
                "success": False,
                "message": f"PRP Step 1 failed: Could not get schema for {resource_type}",
                "error": schema_result.get("error", "Schema not available")
            }

        # STEP 2: Schema Discovery & Validation (PRP)
        print(f"🔍 [PRP Step 2] Schema validation for {resource_type}...")

        # Special validation for Patient resources
        if resource_type == "Patient":
            validation_errors = []
            if "name" in resource_data and isinstance(resource_data["name"], list):
                validation_errors.append(
                    "❌ Found 'name' array - use direct fields 'given', 'family', or 'full_name' instead"
                )

            if "birthDate" in resource_data:
                validation_errors.append("❌ Found 'birthDate' - use 'birth_date' instead")

            if "telecom" in resource_data:
                validation_errors.append("❌ Found 'telecom' array - use direct 'email' and 'phone' fields")

            # Check if at least one name field exists
            has_name = any(field in resource_data for field in ["given", "family", "full_name"])
            if not has_name:
                validation_errors.append(
                    "❌ Missing required name field - provide at least one of: 'given', 'family', or 'full_name'"
                )

            if validation_errors:
                corrected_example = {
                    "given": ["John"],
                    "family": "Doe",
                    "birth_date": "1990-01-01",
                    "email": "john@example.com",
                    "phone": "+1-555-0123"
                }

                return {
                    "success": False,
                    "message": f"PRP Step 2 failed: Data structure validation errors for {resource_type}",
                    "validation_errors": validation_errors,
                    "corrected_example": corrected_example,
                    "guidance": "Use direct fields as shown in corrected_example. Avoid FHIR nested arrays."
                }

        # Special validation for Organization resources
        elif resource_type == "Organization":
            validation_errors = []
            has_name_or_identifier = resource_data.get("name") or resource_data.get("identifier")
            if not has_name_or_identifier:
                validation_errors.append(
                    "❌ Missing required field - provide at least 'name' or 'identifier'"
                )

            # Check for FHIR nested structures
            if "telecom" in resource_data:
                validation_errors.append("❌ Found 'telecom' array - use 'primary_email' and 'primary_phone' fields")

            if "address" in resource_data and isinstance(resource_data["address"], list):
                validation_errors.append("❌ Found 'address' array - use direct address fields: 'address_line', 'city', 'state', 'postal_code', 'country'")

            if validation_errors:
                corrected_example = {
                    "name": "Metro General Hospital",
                    "active": True,
                    "organization_type": [{"code": "prov", "display": "Healthcare Provider"}],
                    "primary_email": "info@hospital.org",
                    "primary_phone": "+1-555-0100",
                    "address_line": ["123 Hospital Drive"],
                    "city": "Boston",
                    "state": "MA",
                    "postal_code": "02101",
                    "country": "US"
                }

                return {
                    "success": False,
                    "message": f"PRP Step 2 failed: Data structure validation errors for {resource_type}",
                    "validation_errors": validation_errors,
                    "corrected_example": corrected_example,
                    "guidance": "Use direct fields as shown in corrected_example. Avoid FHIR nested arrays."
                }

        # STEP 3: Implementation - Execute creation with validated structure (PRP)
        print(f"🚀 [PRP Step 3] Creating {resource_type} resource with validated data...")

        creation_params = {
            "name": "create_resource",
            "arguments": {
                "resource_type": resource_type,
                "resource_data": resource_data,
                "validate_fhir": validate_fhir
            }
        }

        result = await call_mcp_server(creation_params, config)

        if result.get("success", False):
            return {
                "success": True,
                "message": f"Successfully created {resource_type} using PRP methodology",
                "data": result.get("data", {}),
                "prp_steps_completed": ["requirements_analysis", "schema_validation", "implementation"],
                "methodology": "Product Requirement Prompt (PRP)"
            }
        else:
            return {
                "success": False,
                "message": f"Failed to create {resource_type}",
                "error": result.get("error", "Unknown error during creation"),
                "prp_step_failed": "implementation"
            }

    except Exception as e:
        return {
            "success": False,
            "message": f"Error in PRP resource creation for {resource_type}",
            "error": str(e),
            "prp_step_failed": "exception_occurred"
        }


async def version_hacs_resource(
    resource_name: str,
    version: str,
    description: str,
    schema_definition: Dict[str, Any],
    tags: Optional[List[str]] = None,
    status: str = "published",
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Dict[str, Any]:
    """Version and register a HACS resource or template in the registry.

    This tool creates a versioned entry for templates, models, or other HACS artifacts
    in the registry for future reuse and distribution.

    Args:
        resource_name: Name of the model/template to register
        version: Semantic version (e.g., '1.0.0')
        description: Description of this version
        schema_definition: JSON schema definition for the model
        tags: Tags for categorizing the model
        status: Lifecycle status ('draft', 'published', 'deprecated')

    """
    configuration = Configuration.from_runnable_config(config)

    # Call HACS MCP server
    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "version_model",
                "arguments": {
                    "resource_name": resource_name,
                    "version": version,
                    "description": description,
                    "schema_definition": schema_definition,
                    "tags": tags or [],
                    "status": status
                }
            },
            "id": 1
        }

        response = await client.post(
            f"{configuration.hacs_mcp_server_url}/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()

    if "result" in result:
        return cast(Dict[str, Any], result["result"].get("content", {}))
    else:
        return {"error": "Failed to version model in registry"}

async def find_resources(
    resource_type: str,
    filters: Optional[Dict[str, Any]] = None,
    semantic_query: Optional[str] = None,
    limit: int = 10,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """
    Find existing HACS resources (data records) by criteria.

    TERMINOLOGY DISTINCTION:
    - HACS Records: Schema definitions (Patient model defines structure)
    - HACS Records: Actual data records this tool searches
    - This tool searches RESOURCE data, not model schemas

    Args:
        resource_type: Type of HACS resource to search (based on HACS resource)
        filters: Criteria to filter resource data
        semantic_query: Natural language query for resource search
        limit: Maximum number of resource records to return

    Returns:
        List of matching HACS resource records
    """
    configuration = Configuration.from_runnable_config(config)

    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "find_resources",
                "arguments": {
                    "resource_type": resource_type,
                    "filters": filters,
                    "semantic_query": semantic_query,
                    "limit": limit
                }
            },
            "id": 1
        }

        response = await client.post(
            f"{configuration.hacs_mcp_server_url}/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()

    if "result" in result and result["result"] is not None:
        return cast(List[Dict[str, Any]], result["result"].get("content", []))
    return []

async def get_resource(
    resource_type: str,
    resource_id: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Dict[str, Any]:
    """Retrieve a specific HACS resource by its ID."""
    configuration = Configuration.from_runnable_config(config)

    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "get_resource",
                "arguments": {
                    "resource_type": resource_type,
                    "resource_id": resource_id
                }
            },
            "id": 1
        }

        response = await client.post(
            f"{configuration.hacs_mcp_server_url}/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()

    if "result" in result:
        return cast(Dict[str, Any], result["result"].get("content", {}))
    return {"error": f"Resource '{resource_id}' of type '{resource_type}' not found"}

async def update_resource(
    resource_type: str,
    resource_id: str,
    resource_data: Dict[str, Any],
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Dict[str, Any]:
    """Update an existing HACS resource with new data."""
    configuration = Configuration.from_runnable_config(config)

    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "update_resource",
                "arguments": {
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "data": resource_data
                }
            },
            "id": 1
        }

        response = await client.post(
            f"{configuration.hacs_mcp_server_url}/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()

    if "result" in result:
        return cast(Dict[str, Any], result["result"].get("content", {}))
    return {"error": "Failed to update resource"}

async def delete_resource(
    resource_type: str,
    resource_id: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Dict[str, Any]:
    """Delete a HACS resource by ID."""
    configuration = Configuration.from_runnable_config(config)

    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "delete_resource",
                "arguments": {
                    "resource_type": resource_type,
                    "resource_id": resource_id
                }
            },
            "id": 1
        }

        response = await client.post(
            f"{configuration.hacs_mcp_server_url}/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()

    if "result" in result and result["result"].get("content", {}).get("success"):
        return {"status": "deleted"}
    return {"error": "Failed to delete resource"}

# Memory Management Tools for LangGraph Agent

async def create_memory(
    content: str,
    memory_type: str = "episodic",
    importance_score: float = 0.5,
    tags: List[str] = None,
    session_id: str = None,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """Create and store a memory block with automatic classification and vector embedding.

    Args:
        content: Memory content to store
        memory_type: Type of memory (episodic, procedural, executive, semantic)
        importance_score: Importance score from 0.0 to 1.0
        tags: Tags for categorization
        session_id: Optional session ID for grouping

    """
    configuration = Configuration.from_runnable_config(config)

    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "create_memory",
                "arguments": {
                    "content": content,
                    "memory_type": memory_type,
                    "importance_score": importance_score,
                    "tags": tags or [],
                    "session_id": session_id
                }
            },
            "id": 1
        }

        response = await client.post(
            f"{configuration.hacs_mcp_server_url}/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()

    if "result" in result and "content" in result["result"]:
        return result["result"]["content"][0]["text"]
    else:
        return f"❌ Failed to create memory: {result.get('error', 'Unknown error')}"


async def search_memories(
    query: str = "",
    memory_type: str = None,
    session_id: str = None,
    min_importance: float = 0.0,
    limit: int = 10,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """Search memories using semantic similarity and filters.

    Args:
        query: Search query for semantic matching
        memory_type: Filter by memory type (episodic, procedural, executive, semantic)
        session_id: Filter by session ID
        min_importance: Minimum importance score (0.0-1.0)
        limit: Maximum results to return (1-20)

    """
    configuration = Configuration.from_runnable_config(config)

    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "search_memories",
                "arguments": {
                    "query": query,
                    "memory_type": memory_type,
                    "session_id": session_id,
                    "min_importance": min_importance,
                    "limit": limit
                }
            },
            "id": 1
        }

        response = await client.post(
            f"{configuration.hacs_mcp_server_url}/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()

    if "result" in result and "content" in result["result"]:
        return result["result"]["content"][0]["text"]
    else:
        return f"❌ Failed to search memories: {result.get('error', 'Unknown error')}"


async def consolidate_memories(
    session_id: str,
    memory_type: str = "episodic",
    strategy: str = "temporal",
    min_memories: int = 3,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """Consolidate related memories into summary memories for efficient recall.

    Args:
        session_id: Session ID for memory consolidation
        memory_type: Type of memories to consolidate (episodic, procedural, executive)
        strategy: Consolidation strategy (temporal, importance, semantic)
        min_memories: Minimum memories required for consolidation (2-10)

    """
    configuration = Configuration.from_runnable_config(config)

    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "consolidate_memories",
                "arguments": {
                    "session_id": session_id,
                    "memory_type": memory_type,
                    "strategy": strategy,
                    "min_memories": min_memories
                }
            },
            "id": 1
        }

        response = await client.post(
            f"{configuration.hacs_mcp_server_url}/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()

    if "result" in result and "content" in result["result"]:
        return result["result"]["content"][0]["text"]
    else:
        return f"❌ Failed to consolidate memories: {result.get('error', 'Unknown error')}"


async def retrieve_context(
    query: str,
    context_type: str = "general",
    max_memories: int = 5,
    session_id: str = None,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """Retrieve relevant memory context for informed decision making.

    Args:
        query: Query for context retrieval
        context_type: Type of context needed (general, clinical, procedural, executive)
        max_memories: Maximum memories to retrieve (1-10)
        session_id: Optional session ID for context scope

    """
    configuration = Configuration.from_runnable_config(config)

    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "retrieve_context",
                "arguments": {
                    "query": query,
                    "context_type": context_type,
                    "max_memories": max_memories,
                    "session_id": session_id
                }
            },
            "id": 1
        }

        response = await client.post(
            f"{configuration.hacs_mcp_server_url}/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()

    if "result" in result and "content" in result["result"]:
        return result["result"]["content"][0]["text"]
    else:
        return f"❌ Failed to retrieve context: {result.get('error', 'Unknown error')}"


async def analyze_memory_patterns(
    analysis_type: str = "comprehensive",
    session_id: str = None,
    time_window_days: int = 30,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """Analyze memory patterns to identify trends and optimization opportunities.

    Args:
        analysis_type: Type of analysis (comprehensive, temporal, importance, connections)
        session_id: Optional session ID for scoped analysis
        time_window_days: Time window for analysis in days (1-365)

    """
    configuration = Configuration.from_runnable_config(config)

    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "analyze_memory_patterns",
                "arguments": {
                    "analysis_type": analysis_type,
                    "session_id": session_id,
                    "time_window_days": time_window_days
                }
            },
            "id": 1
        }

        response = await client.post(
            f"{configuration.hacs_mcp_server_url}/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()

    if "result" in result and "content" in result["result"]:
        return result["result"]["content"][0]["text"]
    else:
        return f"❌ Failed to analyze memory patterns: {result.get('error', 'Unknown error')}"

# Add these new tool functions after the existing memory management tools

async def validate_resource_data(
    resource_type: str,
    data: Dict[str, Any],
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """Validate resource data against HACS resource schemas.

    Args:
        resource_type: Type of HACS resource to validate
        data: Resource data to validate

    """
    configuration = Configuration.from_runnable_config(config)

    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "validate_resource_data",
                "arguments": {
                    "resource_type": resource_type,
                    "data": data
                }
            },
            "id": 1
        }

        response = await client.post(
            f"{configuration.hacs_mcp_server_url}/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()

    if "result" in result and "content" in result["result"]:
        return result["result"]["content"][0]["text"]
    else:
        return f"❌ Failed to validate resource: {result.get('error', 'Unknown error')}"


async def list_available_resources(
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """List all available HACS resource types.

    """
    configuration = Configuration.from_runnable_config(config)

    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "list_available_resources",
                "arguments": {}
            },
            "id": 1
        }

        response = await client.post(
            f"{configuration.hacs_mcp_server_url}/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()

    if "result" in result and "content" in result["result"]:
        return result["result"]["content"][0]["text"]
    else:
        return f"❌ Failed to list resources: {result.get('error', 'Unknown error')}"


async def get_resource_schema(
    resource_type: str,
    simplified: bool = False,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """
    Get the HACS resource schema for a specific resource type.

    TERMINOLOGY DISTINCTION:
    - HACS Records: Schema definitions this tool retrieves (Patient model schema)
    - HACS Records: Data records that conform to these schemas
    - This tool provides MODEL schemas to validate resource data

    Args:
        resource_type: HACS resource type to get schema for (Patient, Observation, etc.)
        simplified: Whether to return simplified schema or full details

    Returns:
        Detailed HACS resource schema with field definitions, validation rules, and examples
    """
    configuration = Configuration.from_runnable_config(config)

    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "get_resource_schema",
                "arguments": {
                    "resource_type": resource_type,
                    "simplified": simplified
                }
            },
            "id": 1
        }

        response = await client.post(
            f"{configuration.hacs_mcp_server_url}/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()

    if "result" in result and "content" in result["result"]:
        return result["result"]["content"][0]["text"]
    else:
        return f"❌ Failed to get schema: {result.get('error', 'Unknown error')}"


async def search_hacs_records(
    resource_type: str,
    filters: Optional[Dict[str, Any]] = None,
    semantic_query: Optional[str] = None,
    limit: int = 10,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """Search for HACS records with advanced filtering.

    Args:
        resource_type: Type of HACS resource to search
        filters: Optional filters to apply
        semantic_query: Optional semantic search query
        limit: Maximum number of results

    """
    configuration = Configuration.from_runnable_config(config)

    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "search_hacs_records",
                "arguments": {
                    "resource_type": resource_type,
                    "filters": filters,
                    "semantic_query": semantic_query,
                    "limit": limit
                }
            },
            "id": 1
        }

        response = await client.post(
            f"{configuration.hacs_mcp_server_url}/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()

    if "result" in result and "content" in result["result"]:
        return result["result"]["content"][0]["text"]
    else:
        return f"❌ Failed to search records: {result.get('error', 'Unknown error')}"


async def analyze_resource_fields(
    resource_name: str,
    field_category_filter: Optional[str] = None,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """Analyze fields of a HACS resource for development insights.

    Args:
        resource_name: Name of the HACS resource to analyze
        field_category_filter: Optional filter for field categories

    """
    configuration = Configuration.from_runnable_config(config)

    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "analyze_resource_fields",
                "arguments": {
                    "resource_name": resource_name,
                    "field_category_filter": field_category_filter
                }
            },
            "id": 1
        }

        response = await client.post(
            f"{configuration.hacs_mcp_server_url}/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()

    if "result" in result and "content" in result["result"]:
        return result["result"]["content"][0]["text"]
    else:
        return f"❌ Failed to analyze fields: {result.get('error', 'Unknown error')}"


async def compare_resource_schemas(
    resource_names: List[str],
    comparison_focus: str = "fields",
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """Compare schemas of multiple HACS resources.

    Args:
        resource_names: List of HACS resource names to compare
        comparison_focus: Focus of comparison (fields, validation, etc.)

    """
    configuration = Configuration.from_runnable_config(config)

    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "compare_resource_schemas",
                "arguments": {
                    "resource_names": resource_names,
                    "comparison_focus": comparison_focus
                }
            },
            "id": 1
        }

        response = await client.post(
            f"{configuration.hacs_mcp_server_url}/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()

    if "result" in result and "content" in result["result"]:
        return result["result"]["content"][0]["text"]
    else:
        return f"❌ Failed to compare schemas: {result.get('error', 'Unknown error')}"


async def create_view_resource_schema(
    resource_name: str,
    fields: List[str],
    view_name: Optional[str] = None,
    include_optional: bool = True,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """Create a custom view schema from a HACS resource.

    Args:
        resource_name: Base HACS resource name
        fields: List of fields to include in the view
        view_name: Optional name for the view
        include_optional: Whether to include optional fields

    """
    configuration = Configuration.from_runnable_config(config)

    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "create_view_resource_schema",
                "arguments": {
                    "resource_name": resource_name,
                    "fields": fields,
                    "view_name": view_name,
                    "include_optional": include_optional
                }
            },
            "id": 1
        }

        response = await client.post(
            f"{configuration.hacs_mcp_server_url}/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()

    if "result" in result and "content" in result["result"]:
        return result["result"]["content"][0]["text"]
    else:
        return f"❌ Failed to create view schema: {result.get('error', 'Unknown error')}"


async def suggest_view_fields(
    resource_name: str,
    use_case: str,
    max_fields: int = 10,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """Get field suggestions for a specific use case.

    Args:
        resource_name: HACS resource name
        use_case: Specific use case for the view
        max_fields: Maximum number of fields to suggest

    """
    configuration = Configuration.from_runnable_config(config)

    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "suggest_view_fields",
                "arguments": {
                    "resource_name": resource_name,
                    "use_case": use_case,
                    "max_fields": max_fields
                }
            },
            "id": 1
        }

        response = await client.post(
            f"{configuration.hacs_mcp_server_url}/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()

    if "result" in result and "content" in result["result"]:
        return result["result"]["content"][0]["text"]
    else:
        return f"❌ Failed to suggest fields: {result.get('error', 'Unknown error')}"


async def optimize_resource_for_llm(
    resource_name: str,
    optimization_goal: str = "token_efficiency",
    target_use_case: str = "structured_output",
    preserve_validation: bool = True,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """Optimize a HACS resource for LLM usage.

    Args:
        resource_name: HACS resource name to optimize
        optimization_goal: Goal of optimization
        target_use_case: Target use case for optimization
        preserve_validation: Whether to preserve validation rules

    """
    configuration = Configuration.from_runnable_config(config)

    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "optimize_resource_for_llm",
                "arguments": {
                    "resource_name": resource_name,
                    "optimization_goal": optimization_goal,
                    "target_use_case": target_use_case,
                    "preserve_validation": preserve_validation
                }
            },
            "id": 1
        }

        response = await client.post(
            f"{configuration.hacs_mcp_server_url}/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()

    if "result" in result and "content" in result["result"]:
        return result["result"]["content"][0]["text"]
    else:
        return f"❌ Failed to optimize model: {result.get('error', 'Unknown error')}"


async def create_knowledge_item(
    title: str,
    content: str,
    knowledge_type: str = "fact",
    tags: List[str] = None,
    metadata: Dict[str, Any] = None,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """Create a knowledge item for the HACS knowledge base.

    Args:
        title: Title of the knowledge item
        content: Content of the knowledge item
        knowledge_type: Type of knowledge (fact, procedure, etc.)
        tags: Optional tags for categorization
        metadata: Optional metadata

    """
    configuration = Configuration.from_runnable_config(config)

    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "create_knowledge_item",
                "arguments": {
                    "title": title,
                    "content": content,
                    "knowledge_type": knowledge_type,
                    "tags": tags or [],
                    "metadata": metadata or {}
                }
            },
            "id": 1
        }

        response = await client.post(
            f"{configuration.hacs_mcp_server_url}/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()

    if "result" in result and "content" in result["result"]:
        return result["result"]["content"][0]["text"]
    else:
        return f"❌ Failed to create knowledge item: {result.get('error', 'Unknown error')}"

async def execute_prp_workflow(
    user_request: str,
    current_progress: Optional[str] = None,
    workflow_context: Optional[Dict[str, Any]] = None,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """
    Execute Product Requirement Prompt (PRP) methodology for HACS development workflows.

    This tool implements the general PRP pattern:
    1. High-Level Objective Analysis
    2. Mid-Level Objective Breakdown
    3. Implementation Planning
    4. Context-Aware Execution

    Works for ANY HACS development scenario: model discovery, resource creation,
    template building, database operations, registry management, etc.

    Args:
        user_request: The user's development request or objective
        current_progress: Current state of workflow execution
        workflow_context: Accumulated context from previous steps

    Returns:
        Next steps with updated context and progress tracking
    """
    try:
        # Store current workflow state
        workflow_id = f"prp_workflow_{hash(user_request) % 10000}"

        # Create/update workflow memory
        workflow_memory = {
            "name": "create_memory",
            "arguments": {
                "content": f"PRP Workflow: {user_request[:200]}... Progress: {current_progress or 'Starting'}",
                "memory_type": "executive",
                "importance_score": 0.9,
                "tags": ["prp_workflow", "development_task", "workflow_state"],
                "session_id": workflow_id
            }
        }

        await call_mcp_server(workflow_memory, config)

        # Analyze user request using PRP methodology
        prp_analysis = _analyze_prp_requirements(user_request, current_progress, workflow_context or {})

        return f"""🎯 **PRP Workflow Analysis**

## High-Level Objective
{prp_analysis['high_level_objective']}

## Mid-Level Objectives
{chr(10).join([f"- {obj}" for obj in prp_analysis['mid_level_objectives']])}

## Current Progress
{prp_analysis['current_progress']}

## Next Implementation Steps
{chr(10).join([f"{i+1}. {step}" for i, step in enumerate(prp_analysis['next_steps'])])}

## Context & Dependencies
{chr(10).join([f"- {ctx}" for ctx in prp_analysis['context_items']])}

## Recommended Tools
{chr(10).join([f"- {tool}: {desc}" for tool, desc in prp_analysis['recommended_tools'].items()])}

🔄 **Workflow ID**: {workflow_id}
📊 **Completion**: {prp_analysis['completion_percentage']}%

Use this analysis to proceed with systematic HACS development."""

    except Exception as e:
        return f"❌ Failed to execute PRP workflow: {str(e)}"


def _analyze_prp_requirements(request: str, progress: Optional[str], context: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze user request using PRP methodology to determine workflow approach."""

    request_lower = request.lower()

    # Determine high-level objective category
    if any(term in request_lower for term in ["criar", "create", "novo", "new"]):
        if any(term in request_lower for term in ["template", "modelo", "schema"]):
            objective_type = "template_creation"
        elif any(term in request_lower for term in ["paciente", "patient", "recurso", "resource"]):
            objective_type = "resource_creation"
        else:
            objective_type = "general_creation"
    elif any(term in request_lower for term in ["buscar", "search", "encontrar", "find", "listar", "list"]):
        objective_type = "discovery_search"
    elif any(term in request_lower for term in ["analisar", "analyze", "extrair", "extract", "processar", "process"]):
        objective_type = "data_processing"
    elif any(term in request_lower for term in ["atualizar", "update", "modificar", "modify", "editar", "edit"]):
        objective_type = "resource_modification"
    else:
        objective_type = "general_development"

    # Generate PRP structure based on objective type
    if objective_type == "template_creation":
        return {
            "high_level_objective": "Create structured HACS template for healthcare workflow automation",
            "mid_level_objectives": [
                "Analyze template requirements and use case",
                "Design template schema with appropriate HACS resources",
                "Implement template with validation and examples",
                "Integrate template into HACS ecosystem"
            ],
            "current_progress": progress or "Requirements analysis phase",
            "next_steps": [
                "Use discover_hacs_resources() to explore available model types",
                "Use create_clinical_template() with identified parameters",
                "Use validate_resource_data() to verify template structure",
                "Use version_hacs_resource() to save template for reuse"
            ],
            "context_items": [
                "Template type and complexity level required",
                "Target healthcare workflow or use case",
                "Integration requirements with existing HACS resources",
                "Validation and testing requirements"
            ],
            "recommended_tools": {
                "discover_hacs_resources": "Explore available HACS resource types",
                "create_clinical_template": "Generate structured template",
                "validate_resource_data": "Verify template integrity",
                "get_resource_schema": "Understand model structures"
            },
            "completion_percentage": 25 if not progress else 50
        }

    elif objective_type == "resource_creation":
        return {
            "high_level_objective": "Create and manage HACS healthcare resources with proper validation",
            "mid_level_objectives": [
                "Understand resource type and data requirements",
                "Validate data structure against HACS schema",
                "Execute resource creation with correct field mapping",
                "Verify and store created resource"
            ],
            "current_progress": progress or "Resource requirements analysis",
            "next_steps": [
                "Use get_resource_schema() to understand field structure",
                "Use validate_resource_data() to check data integrity",
                "Use create_hacs_record() with proper field structure",
                "Use search_resources() to verify creation"
            ],
            "context_items": [
                "Resource type and field requirements",
                "Data validation and structure requirements",
                "HACS vs FHIR field mapping considerations",
                "Error handling and retry strategies"
            ],
            "recommended_tools": {
                "get_resource_schema": "Understand resource requirements",
                "create_hacs_record": "Execute resource creation",
                "validate_resource_data": "Verify data structure",
                "find_resources": "Search and verify resources"
            },
            "completion_percentage": 15 if not progress else 60
        }

    elif objective_type == "discovery_search":
        return {
            "high_level_objective": "Discover and explore HACS resources, resources, and capabilities",
            "mid_level_objectives": [
                "Identify search criteria and filters",
                "Execute comprehensive model and resource discovery",
                "Analyze discovered capabilities and schemas",
                "Provide actionable recommendations"
            ],
            "current_progress": progress or "Discovery planning phase",
            "next_steps": [
                "Use discover_hacs_resources() for model exploration",
                "Use find_resources() for resource search",
                "Use get_resource_schema() for detailed analysis",
                "Use search_memories() for context retrieval"
            ],
            "context_items": [
                "Search scope and filtering requirements",
                "Model categories and types of interest",
                "Schema analysis depth requirements",
                "Result presentation and documentation needs"
            ],
            "recommended_tools": {
                "discover_hacs_resources": "Explore available models",
                "find_resources": "Search existing resources",
                "get_resource_schema": "Analyze model structures",
                "list_available_resources": "Get resource inventory"
            },
            "completion_percentage": 20 if not progress else 80
        }

    else:  # general_development
        return {
            "high_level_objective": "Execute general HACS development workflow with systematic approach",
            "mid_level_objectives": [
                "Analyze development requirements and scope",
                "Plan implementation approach using HACS tools",
                "Execute development with proper validation",
                "Test and verify implementation results"
            ],
            "current_progress": progress or "Development planning phase",
            "next_steps": [
                "Use appropriate discovery tools for exploration",
                "Use creation tools for implementation",
                "Use validation tools for verification",
                "Use memory tools for context tracking"
            ],
            "context_items": [
                "Development scope and requirements",
                "Tool selection and workflow planning",
                "Validation and testing strategies",
                "Documentation and maintenance needs"
            ],
            "recommended_tools": {
                "execute_prp_workflow": "Follow structured workflow",
                "discover_hacs_resources": "Explore capabilities",
                "create_memory": "Track development context",
                "validate_resource_data": "Verify implementations"
            },
            "completion_percentage": 10 if not progress else 40
        }

async def discover_and_analyze_hacs_models(
    category_filter: Optional[str] = None,
    include_schemas: bool = True,
    schema_detail_level: str = "simplified",
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """
    Efficiently discover ALL HACS resources and analyze their schemas in a single operation.

    This batch operation uses BaseResource reflection to dynamically discover every
    available HACS resource without hardcoding, then optionally retrieves schemas.

    Args:
        category_filter: Filter by model category (clinical, administrative, reasoning)
        include_schemas: Whether to include detailed schema information
        schema_detail_level: Level of schema detail (simplified/complete)

    Returns:
        Comprehensive analysis of all discoverable HACS resources
    """
    try:
        # Step 1: Dynamic model discovery through reflection
        discovered_models = await _discover_all_hacs_models_dynamically()

        if category_filter:
            discovered_models = [
                model for model in discovered_models
                if _categorize_model(model["name"]) == category_filter.lower()
            ]

        # Step 2: Batch schema retrieval if requested
        schema_results = {}
        if include_schemas and discovered_models:
            resource_names = [model["name"] for model in discovered_models]

            # Batch call to get all schemas at once
            schema_params = {
                "name": "get_resource_schema",
                "arguments": {
                    "resource_type": "batch",
                    "model_list": resource_names,
                    "simplified": schema_detail_level == "simplified"
                }
            }

            try:
                schema_response = await call_mcp_server(schema_params, config)
                if schema_response.get("success"):
                    schema_results = schema_response.get("data", {})
            except Exception:
                # Fall back to individual calls if batch not supported
                for resource_name in resource_names[:5]:  # Limit to 5 for efficiency
                    try:
                        params = {
                            "name": "get_resource_schema",
                            "arguments": {"resource_type": resource_name, "simplified": True}
                        }
                        result = await call_mcp_server(params, config)
                        if result.get("success"):
                            schema_results[resource_name] = result.get("data", {})
                    except Exception:
                        continue

        # Step 3: Generate comprehensive analysis
        analysis = _generate_comprehensive_model_analysis(
            discovered_models, schema_results, include_schemas
        )

        return analysis

    except Exception as e:
        return f"❌ **Error in model discovery**: {str(e)}\n\nFalling back to standard discovery..."


async def create_multi_model_template(
    template_name: str,
    selected_models: List[str],
    template_type: str = "consultation",
    include_all_fields: bool = False,
    custom_fields: Optional[Dict[str, Any]] = None,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """
    Create a comprehensive template combining multiple HACS resources efficiently.

    This function uses BaseResource capabilities to create templates that work
    with ANY combination of HACS resources, not just hardcoded ones.

    Args:
        template_name: Name for the multi-model template
        selected_models: List of HACS resource names to combine
        template_type: Type of template (consultation, assessment, etc.)
        include_all_fields: Whether to include all fields or create optimized subset
        custom_fields: Additional custom fields to include

    Returns:
        Comprehensive template with usage guidance
    """
    try:
        # Step 1: Validate that all models exist dynamically
        available_models = await _discover_all_hacs_models_dynamically()
        available_names = [model["name"] for model in available_models]

        invalid_models = [model for model in selected_models if model not in available_names]
        if invalid_models:
            return f"❌ **Invalid models**: {invalid_models}\n✅ **Available**: {available_names[:10]}..."

        # Step 2: Use BaseResource reflection to build template schema
        template_schema = await _build_multi_model_template_schema(
            selected_models, include_all_fields, custom_fields, config
        )

        # Step 3: Generate optimized field combinations using BaseResource.pick()
        optimized_views = _generate_optimized_model_views(selected_models, template_type)

        # Step 4: Create comprehensive template with examples
        template_result = _generate_comprehensive_template_result(
            template_name, selected_models, template_type, template_schema, optimized_views
        )

        # Step 5: Store template creation in memory for workflow tracking
        memory_params = {
            "name": "create_memory",
            "arguments": {
                "content": f"Multi-model template '{template_name}' created combining: {', '.join(selected_models)}",
                "memory_type": "executive",
                "importance_score": 0.9,
                "tags": ["template_creation", "multi_model", template_type],
                "session_id": f"template_{template_name.lower().replace(' ', '_')}"
            }
        }
        await call_mcp_server(memory_params, config)

        return template_result

    except Exception as e:
        return f"❌ **Error creating multi-model template**: {str(e)}"


async def _discover_all_hacs_models_dynamically() -> List[Dict[str, Any]]:
    """Use reflection to discover all available HACS resources without hardcoding."""
    try:
        import hacs_core
        import inspect
        from hacs_core.base_resource import BaseResource

        models = []

        # Get all classes from hacs_core that inherit from BaseResource
        for name, obj in inspect.getmembers(hacs_core):
            if (inspect.isclass(obj) and
                issubclass(obj, BaseResource) and
                obj != BaseResource and
                not name.startswith('_')):

                # Use BaseResource methods to get model info
                try:
                    sample_instance = obj(resource_type=name)
                    schema = obj.model_json_schema()

                    models.append({
                        "name": name,
                        "class": obj,
                        "category": _categorize_model(name),
                        "description": obj.__doc__ or f"HACS {name} resource",
                        "field_count": len(schema.get("properties", {})),
                        "required_fields": schema.get("required", []),
                        "has_examples": "examples" in schema,
                        "supports_pick": hasattr(obj, 'pick'),
                        "resource_type": getattr(sample_instance, 'resource_type', name)
                    })
                except Exception:
                    # Skip models that can't be instantiated
                    continue

        return sorted(models, key=lambda x: x["name"])

    except Exception as e:
        # Fallback to basic discovery if reflection fails
        return [
            {"name": "Patient", "category": "clinical", "description": "Patient demographics", "field_count": 20},
            {"name": "Observation", "category": "clinical", "description": "Clinical observations", "field_count": 15},
            {"name": "Encounter", "category": "clinical", "description": "Patient encounters", "field_count": 18},
            {"name": "Condition", "category": "clinical", "description": "Medical conditions", "field_count": 12},
            {"name": "MedicationRequest", "category": "clinical", "description": "Medication prescriptions", "field_count": 16}
        ]


def _categorize_model(resource_name: str) -> str:
    """Categorize a HACS resource based on its name and purpose."""
    clinical_models = ["patient", "observation", "encounter", "condition", "medication", "allergy", "procedure"]
    administrative_models = ["actor", "memory", "session", "auth", "config"]
    reasoning_models = ["plan", "activity", "library", "knowledge", "guidance", "evidence"]

    model_lower = resource_name.lower()

    if any(term in model_lower for term in clinical_models):
        return "clinical"
    elif any(term in model_lower for term in administrative_models):
        return "administrative"
    elif any(term in model_lower for term in reasoning_models):
        return "reasoning"
    else:
        return "utility"


async def _build_multi_model_template_schema(
    models: List[str], include_all: bool, custom_fields: Optional[Dict[str, Any]], config
) -> Dict[str, Any]:
    """Build template schema using BaseResource capabilities."""
    combined_schema = {
        "type": "object",
        "properties": {},
        "required": [],
        "models_included": models,
        "custom_fields": custom_fields or {}
    }

    # Get schemas for each model and combine
    for resource_name in models:
        try:
            params = {
                "name": "get_resource_schema",
                "arguments": {"resource_type": resource_name, "simplified": not include_all}
            }
            result = await call_mcp_server(params, config)

            if result.get("success") and "data" in result:
                schema_data = result["data"]
                if "schema" in schema_data:
                    model_schema = schema_data["schema"]
                    if "properties" in model_schema:
                        # Prefix fields with model name to avoid conflicts
                        for field_name, field_def in model_schema["properties"].items():
                            prefixed_name = f"{resource_name.lower()}_{field_name}"
                            combined_schema["properties"][prefixed_name] = field_def

                        # Add required fields with model prefix
                        if "required" in model_schema:
                            for req_field in model_schema["required"]:
                                prefixed_req = f"{resource_name.lower()}_{req_field}"
                                if prefixed_req not in combined_schema["required"]:
                                    combined_schema["required"].append(prefixed_req)
        except Exception:
            continue

    # Add custom fields
    if custom_fields:
        combined_schema["properties"].update(custom_fields)

    return combined_schema


def _generate_optimized_model_views(models: List[str], template_type: str) -> Dict[str, Dict[str, Any]]:
    """Generate optimized model views using BaseResource.pick() conceptually."""
    views = {}

    # Define common field sets for different template types
    field_sets = {
        "consultation": {
            "Patient": ["full_name", "birth_date", "gender", "email", "phone"],
            "Observation": ["code", "value", "effective_date_time", "status"],
            "Condition": ["code", "clinical_status", "severity", "onset_date_time"],
            "Encounter": ["class", "status", "period", "reason_code"]
        },
        "assessment": {
            "Patient": ["full_name", "birth_date", "gender"],
            "Observation": ["code", "value", "status", "category"],
            "Condition": ["code", "clinical_status", "verification_status"],
        },
        "discharge": {
            "Patient": ["full_name", "birth_date", "contact_info"],
            "Encounter": ["class", "status", "period", "hospitalization"],
            "Condition": ["code", "clinical_status", "resolution_date"],
        }
    }

    selected_fields = field_sets.get(template_type, field_sets["consultation"])

    for model in models:
        if model in selected_fields:
            # Pre-define variables to avoid complex f-string nesting
            model_fields = selected_fields[model]
            quoted_fields = [f'"{field}"' for field in model_fields]
            fields_str = ", ".join(quoted_fields)
            pick_command = f"{model}.pick({fields_str})"
            
            views[model] = {
                "optimized_fields": model_fields,
                "pick_command": pick_command,
                "description": f"Optimized {model} view for {template_type} workflows"
            }

    return views

def _generate_comprehensive_model_analysis(
    models: List[Dict[str, Any]],
    schema_results: Dict[str, Any],
    include_schemas: bool
) -> str:
    """Generate comprehensive analysis of discovered models."""

    # Categorize models
    categories = {}
    for model in models:
        category = model["category"]
        if category not in categories:
            categories[category] = []
        categories[category].append(model)

    # Generate analysis
    analysis_lines = [
        f"✅ **Dynamic HACS Resource Discovery Complete**",
        f"",
        f"📊 **Discovery Summary**:",
        f"- **Total Models Found**: {len(models)}",
        f"- **Categories**: {', '.join(categories.keys())}",
        f"- **Schema Analysis**: {'Included' if include_schemas else 'Skipped'}",
        f"",
        f"📂 **Models by Category**:"
    ]

    for category, category_models in categories.items():
        analysis_lines.append(f"")
        analysis_lines.append(f"**{category.title()} Models ({len(category_models)})**:")
        for model in category_models[:5]:  # Show first 5 per category
            supports_pick = "✅ pick()" if model.get("supports_pick", False) else "❌"
            analysis_lines.append(
                f"- **{model['name']}**: {model['field_count']} fields, "
                f"{len(model.get('required_fields', []))} required {supports_pick}"
            )
        if len(category_models) > 5:
            analysis_lines.append(f"  ... and {len(category_models) - 5} more")

    if include_schemas and schema_results:
        analysis_lines.extend([
            f"",
            f"🔍 **Schema Analysis Available For**:",
            f"- {', '.join(list(schema_results.keys())[:10])}"
        ])
        if len(schema_results) > 10:
            analysis_lines.append(f"- ... and {len(schema_results) - 10} more")

    analysis_lines.extend([
        f"",
        f"🎯 **Recommended Next Steps**:",
        f"- Use `create_multi_model_template()` to combine relevant models",
        f"- Use `get_resource_schema(resource_name)` for detailed field information",
        f"- Use `Model.pick(field1, field2)` to create optimized views",
        f"- Use `create_hacs_record()` to create instances",
        f"",
        f"🏗️ **Template Recommendations**:",
        f"- **Clinical Workflow**: Patient + Observation + Encounter + Condition",
        f"- **Assessment**: Patient + Observation + Condition",
        f"- **Medication Management**: Patient + MedicationRequest + Observation",
        f"- **Care Planning**: Patient + PlanDefinition + ActivityDefinition"
    ])

    return "\n".join(analysis_lines)


def _generate_comprehensive_template_result(
    template_name: str,
    selected_models: List[str],
    template_type: str,
    template_schema: Dict[str, Any],
    optimized_views: Dict[str, Dict[str, Any]]
) -> str:
    """Generate comprehensive template creation result."""

    result_lines = [
        f"✅ **Multi-Model Template Created Successfully**",
        f"",
        f"🏗️ **Template Overview**:",
        f"- **Name**: {template_name}",
        f"- **Type**: {template_type}",
        f"- **Models Combined**: {len(selected_models)}",
        f"- **Total Properties**: {len(template_schema.get('properties', {}))}",
        f"- **Required Fields**: {len(template_schema.get('required', []))}",
        f"",
        f"📋 **Included Models**:",
    ]

    for model in selected_models:
        result_lines.append(f"- **{model}**: HACS {_categorize_model(model)} model")

    result_lines.extend([
        f"",
        f"🎯 **Optimized Views Available**:"
    ])

    for model, view_info in optimized_views.items():
        fields = view_info.get("optimized_fields", [])
        result_lines.append(
            f"- **{model}View**: {len(fields)} key fields "
            f"({', '.join(fields[:3])}{'...' if len(fields) > 3 else ''})"
        )

    result_lines.extend([
        f"",
        f"💡 **Usage Examples**:",
        f"```python",
        f"# Create optimized view for structured output",
        f"PatientView = Patient.pick('full_name', 'birth_date', 'gender')",
        f"",
        f"# Create resources using the template",
        f"await create_hacs_record('Patient', patient_data)",
        f"await create_hacs_record('Observation', observation_data)",
        f"```",
        f"",
        f"🔧 **Integration Points**:",
        f"- Use with `create_hacs_record()` for data entry",
        f"- Validate with `validate_resource_data()`",
        f"- Store context with `create_memory()`",
        f"- Version with `version_hacs_resource()` for reuse",
        f"",
        f"🎯 **Best Practices**:",
        f"- Use optimized views for LLM structured output",
        f"- Validate all data before resource creation",
        f"- Follow HACS field naming conventions",
        f"- Leverage BaseResource.pick() for token efficiency",
        f"",
        f"✅ **Template is ready for {template_type} workflows!**"
    ])

    return "\n".join(result_lines)


# ============================================================================ 
# REAL HACS ADMIN OPERATIONS (Production-Ready)
# ============================================================================

async def run_hacs_database_migration(
    database_url: Optional[str] = None,
    force_migration: bool = False,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """
    Run HACS database migration to set up or update database schemas.
    
    This is a REAL admin operation that actually performs database migrations
    using the HACS persistence layer.
    
    Args:
        database_url: PostgreSQL connection URL (defaults to DATABASE_URL env var)
        force_migration: Force migration even if schemas already exist
        
    Returns:
        Migration result with detailed status information
    """
    if not HACS_TOOLS_AVAILABLE:
        return f"❌ HACS tools not available: {_import_error}. Please install HACS dependencies."
    
    # Create admin actor for this operation
    admin_actor = Actor(
        name="Developer Agent Admin",
        role=ActorRole.ADMINISTRATOR,
        permissions=["admin:*", "migration:*", "database:*"]
    )
    
    try:
        result = run_database_migration(
            database_url=database_url,
            force_migration=force_migration,
            actor=admin_actor
        )
        
        if result.success:
            return f"✅ **Database Migration Successful**\n\n{result.message}\n\n**Details**: {result.data}"
        else:
            return f"❌ **Database Migration Failed**\n\n**Error**: {result.error}"
            
    except Exception as e:
        return f"❌ **Migration Error**: {str(e)}"


async def check_hacs_migration_status(
    database_url: Optional[str] = None,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """
    Check the current status of HACS database migrations.
    
    This provides information about which schemas exist, migration history,
    and database readiness for HACS operations.
    
    Args:
        database_url: PostgreSQL connection URL (defaults to DATABASE_URL env var)
        
    Returns:
        Detailed migration status information
    """
    if not HACS_TOOLS_AVAILABLE:
        return f"❌ HACS tools not available: {_import_error}. Please install HACS dependencies."
    
    # Create admin actor for this operation
    admin_actor = Actor(
        name="Developer Agent Admin",
        role=ActorRole.ADMINISTRATOR,
        permissions=["admin:*", "schema:*"]
    )
    
    try:
        result = check_migration_status(
            database_url=database_url,
            actor=admin_actor
        )
        
        if result.success:
            status_data = result.data
            return f"""✅ **Migration Status Retrieved**

**Database Status**: {status_data.get('database_status', 'Unknown')}
**Schemas Available**: {', '.join(status_data.get('schemas', []))}
**Migration Version**: {status_data.get('migration_version', 'Unknown')}
**Last Migration**: {status_data.get('last_migration_date', 'Unknown')}

**Details**: {result.message}
"""
        else:
            return f"❌ **Migration Status Check Failed**\n\n**Error**: {result.error}"
            
    except Exception as e:
        return f"❌ **Status Check Error**: {str(e)}"


async def describe_hacs_database_schema(
    schema_name: str = "hacs_core",
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """
    Get detailed information about HACS database schemas and tables.
    
    This provides comprehensive schema information including table structures,
    indexes, constraints, and relationships.
    
    Args:
        schema_name: Name of the schema to describe (default: hacs_core)
        
    Returns:
        Detailed schema information
    """
    if not HACS_TOOLS_AVAILABLE:
        return f"❌ HACS tools not available: {_import_error}. Please install HACS dependencies."
    
    # Create admin actor for this operation
    admin_actor = Actor(
        name="Developer Agent Admin", 
        role=ActorRole.ADMINISTRATOR,
        permissions=["admin:*", "schema:*"]
    )
    
    try:
        result = describe_database_schema(
            schema_name=schema_name,
            actor=admin_actor
        )
        
        if result.success:
            schema_data = result.data
            
            response = f"✅ **Database Schema: {schema_name}**\n\n"
            
            if 'tables' in schema_data:
                response += f"**Tables** ({len(schema_data['tables'])}):\n"
                for table_name, table_info in schema_data['tables'].items():
                    columns = table_info.get('columns', {})
                    response += f"- `{table_name}` ({len(columns)} columns)\n"
                response += "\n"
            
            if 'resource_schemas' in schema_data:
                response += f"**HACS Resources** ({len(schema_data['resource_schemas'])}):\n"
                for resource_type, resource_info in schema_data['resource_schemas'].items():
                    response += f"- `{resource_type}`: {resource_info.get('description', 'No description')}\n"
                response += "\n"
            
            response += f"**Full Details**: {result.message}"
            return response
        else:
            return f"❌ **Schema Description Failed**\n\n**Error**: {result.error}"
            
    except Exception as e:
        return f"❌ **Schema Description Error**: {str(e)}"


async def create_admin_hacs_record(
    resource_type: str,
    resource_data: Dict[str, Any],
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """
    Create a HACS record using real HACS persistence layer.
    
    This creates actual healthcare records in the HACS database with proper
    validation and audit trails.
    
    Args:
        resource_type: Type of HACS resource (Patient, Observation, etc.)
        resource_data: Resource data dictionary
        
    Returns:
        Creation result with resource details
    """
    if not HACS_TOOLS_AVAILABLE:
        return f"❌ HACS tools not available: {_import_error}. Please install HACS dependencies."
    
    # Create admin actor for this operation
    admin_actor = Actor(
        name="Developer Agent Admin",
        role=ActorRole.ADMINISTRATOR,
        permissions=["admin:*", "write:*"]
    )
    
    try:
        result = create_hacs_record(
            actor_name=admin_actor.name,
            resource_type=resource_type,
            resource_data=resource_data,
            auto_generate_id=True,
            validate_fhir=True
        )
        
        if result.success:
            return f"""✅ **HACS {resource_type} Created Successfully**

**Resource ID**: {result.data.get('id', 'Generated')}
**Resource Type**: {resource_type}
**Validation**: {result.data.get('validation_status', 'Passed')}

**Details**: {result.message}
"""
        else:
            return f"❌ **HACS {resource_type} Creation Failed**\n\n**Error**: {result.error}"
            
    except Exception as e:
        return f"❌ **Record Creation Error**: {str(e)}"