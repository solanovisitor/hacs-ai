"""
HACS Model Context Protocol Server

This module implements a complete MCP server for HACS with LangGraph Cloud integration.
"""

import logging
import os
from typing import Any, Dict

from hacs_core import get_settings
from hacs_core.auth import AuthManager, get_auth_manager

from .messages import CallToolParams, MCPRequest, MCPResponse

# Enhanced persistence imports
try:
    from hacs_persistence import PostgreSQLAdapter, initialize_hacs_database, get_migration_status

    PERSISTENCE_AVAILABLE = True
except ImportError:
    PERSISTENCE_AVAILABLE = False

try:
    from hacs_utils.integrations.qdrant.store import QdrantVectorStore

    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

logger = logging.getLogger(__name__)


class HacsMCPServer:
    """Enhanced HACS MCP Server with security, persistence, andtool integration."""

    def __init__(self):
        """Initialize the enhanced HACS MCP server with security and persistence."""
        self.version = "1.0.0"
        self.server_info = {
            "name": "HACS MCP Server",
            "version": self.version,
            "description": "Healthcare Agent Communication Standard Model Context Protocol Server",
        }

        # Initialize auth and settings
        self.auth_manager = get_auth_manager()
        self.settings = get_settings()

        # Initialize enhanced persistence providers
        self.db_adapter = None
        self.vector_store = None

        # Initialize persistence layer
        self._initialize_persistence()

    def _initialize_persistence(self) -> None:
        """Initialize database and vector store with full migration."""
        # Database initialization with enhanced connection factory
        database_url = os.getenv("DATABASE_URL")
        if database_url and PERSISTENCE_AVAILABLE:
            try:
                logger.info("Initializing HACS database with connection factory...")

                # Use connection factory for robust initialization
                from hacs_persistence import HACSConnectionFactory

                # Get adapter with automatic migration and connection pooling
                self.db_adapter = HACSConnectionFactory.get_adapter(
                    database_url=database_url, auto_migrate=True, pool_size=10
                )
                logger.info("✅ PostgreSQL adapter initialized via connection factory")

            except Exception as e:
                self.db_adapter = None
                logger.warning(
                    f"Could not initialize PostgreSQL adapter: {e}. CRUD operations will be mocked."
                )
        else:
            self.db_adapter = None
            logger.info("PostgreSQL not available - CRUD operations will be mocked")

        # Vector store initialization
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        if QDRANT_AVAILABLE:
            try:
                self.vector_store = QdrantVectorStore(
                    url=qdrant_url,
                    collection_name="hacs_vectors",
                    dimension=1536,
                    create_if_not_exists=True,
                )
                logger.info(f"Qdrant vector store initialized at {qdrant_url}")
            except Exception as e:
                self.vector_store = None
                logger.warning(
                    f"Could not initialize Qdrant vector store: {e}. Vector operations will be disabled."
                )

    async def _handle_use_tool(self, request: MCPRequest) -> MCPResponse:
        """Handle tools/call request with enhanced persistence-enabled execution."""
        try:
            params = CallToolParams(**(request.params or {}))

            # Create enhanced actor context
            from hacs_models import Actor

            actor = Actor(
                id="mcp-server",
                name="HACS MCP Server",
                role="system",
                permissions=["admin:*", "audit:*"],
                session_status="active",
            )

            # Execute via integration manager (async) with context injection
            from hacs_registry import execute_hacs_tool

            tool_result = await execute_hacs_tool(
                tool_name=params.name,
                params=params.arguments,
                actor_name=actor.name,
                db_adapter=self.db_adapter,
                vector_store=self.vector_store,
            )

            return MCPResponse(id=request.id, result=tool_result.to_dict())

        except Exception as e:
            logger.error(f"Error executing tool {getattr(params, 'name', 'unknown')}: {e}")
            return MCPResponse(
                id=request.id,
                error={
                    "code": -32603,
                    "message": "Internal error",
                    "data": {"details": str(e)},
                },
            )

    async def _handle_list_tools(self, request: MCPRequest) -> MCPResponse:
        """Handle tools/list requests withHACS tool coverage organized in blocks."""
        try:
            # Import all available tools from hacs-tools
            try:
                # from hacs_tools import ALL_HACS_TOOLS  # For future tool integration
                hacs_tools_available = True
            except ImportError:
                hacs_tools_available = False

            # BLOCK 1: MODEL DISCOVERY & DEVELOPMENT TOOLS
            model_tools = [
                {
                    "name": "describe_models",
                    "description": "🔍 Describe HACS models with examples and usage",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "resource_types": {"type": "array", "items": {"type": "string"}},
                            "include_examples": {"type": "boolean", "default": True},
                        },
                    },
                },
                {
                    "name": "list_model_fields",
                    "description": "📋 List fields for a HACS model",
                    "inputSchema": {
                        "type": "object",
                        "properties": {"resource_type": {"type": "string"}},
                        "required": ["resource_type"],
                    },
                },
                {
                    "name": "plan_bundle_schema",
                    "description": "🧩 Plan a bundle schema across resource types",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "resource_types": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["resource_types"],
                    },
                },
            ]

            # BLOCK 2: REGISTRY & CRUD TOOLS
            registry_tools = [
                {
                    "name": "save_record",
                    "description": "➕ Save a HACS resource record (typed CRUD)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "resource_type": {"type": "string"},
                            "resource_data": {"type": "object"},
                        },
                        "required": ["resource_type", "resource_data"],
                    },
                },
                {
                    "name": "read_record",
                    "description": "📖 Read a HACS record by ID",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "resource_type": {"type": "string"},
                            "resource_id": {"type": "string"},
                        },
                        "required": ["resource_type", "resource_id"],
                    },
                },
                {
                    "name": "update_record",
                    "description": "✏️ Update a HACS record",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "resource_type": {"type": "string"},
                            "resource_id": {"type": "string"},
                            "patch": {"type": "object"},
                        },
                        "required": ["resource_type", "resource_id", "patch"],
                    },
                },
                {
                    "name": "delete_record",
                    "description": "🗑️ Delete a HACS record",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "resource_type": {"type": "string"},
                            "resource_id": {"type": "string"},
                        },
                        "required": ["resource_type", "resource_id"],
                    },
                },
            ]

            # BLOCK 3: SEARCH & DISCOVERY TOOLS
            search_tools = [
                {
                    "name": "search_hacs_records",
                    "description": "📊 Search HACS records with filtering",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "resource_types": {"type": "array", "items": {"type": "string"}},
                            "limit": {"type": "integer", "default": 10},
                        },
                    },
                }
            ]

            # BLOCK 4: MEMORY MANAGEMENT TOOLS
            memory_tools = [
                {
                    "name": "create_memory",
                    "description": "🧠 **Memory Creator**: Store knowledge blocks with automatic classification, importance scoring, and vector embedding for intelligent retrieval",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string", "description": "Memory content to store"},
                            "memory_type": {
                                "type": "string",
                                "enum": ["episodic", "procedural", "executive", "semantic"],
                                "description": "Memory classification",
                                "default": "episodic",
                            },
                            "importance_score": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0,
                                "description": "Importance (0.0-1.0)",
                                "default": 0.5,
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Categorization tags",
                            },
                            "session_id": {"type": "string", "description": "Session grouping ID"},
                        },
                        "required": ["content"],
                    },
                },
                {
                    "name": "search_memories",
                    "description": "🔍 **Memory Search**: Semantic memory search with similarity matching, filtering, and context-aware retrieval",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "memory_type": {
                                "type": "string",
                                "enum": ["episodic", "procedural", "executive", "semantic"],
                                "description": "Memory type filter",
                            },
                            "session_id": {"type": "string", "description": "Session filter"},
                            "min_importance": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0,
                                "default": 0.0,
                            },
                            "limit": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 50,
                                "default": 10,
                            },
                            "similarity_threshold": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0,
                                "default": 0.7,
                            },
                        },
                    },
                },
                {
                    "name": "consolidate_memories",
                    "description": "🗂️ **Memory Consolidator**: Merge related memories into summaries for efficient storage and faster recall",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "Session to consolidate",
                            },
                            "memory_type": {
                                "type": "string",
                                "enum": ["episodic", "procedural", "executive"],
                                "default": "episodic",
                            },
                            "strategy": {
                                "type": "string",
                                "enum": ["temporal", "importance", "semantic"],
                                "default": "temporal",
                            },
                            "min_memories": {
                                "type": "integer",
                                "minimum": 2,
                                "maximum": 20,
                                "default": 3,
                            },
                        },
                        "required": ["session_id"],
                    },
                },
                {
                    "name": "retrieve_context",
                    "description": "🎯 **Context Retrieval**: Get relevant memory context for informed decision-making and situational awareness",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Context query"},
                            "context_type": {
                                "type": "string",
                                "enum": ["general", "clinical", "procedural", "executive"],
                                "default": "general",
                            },
                            "max_memories": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 20,
                                "default": 5,
                            },
                            "session_id": {"type": "string", "description": "Session scope"},
                        },
                        "required": ["query"],
                    },
                },
                {
                    "name": "analyze_memory_patterns",
                    "description": "📈 **Pattern Analyzer**: Analyze memory usage patterns, identify trends, gaps, and optimization opportunities",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "analysis_type": {
                                "type": "string",
                                "enum": ["comprehensive", "temporal", "importance", "connections"],
                                "default": "comprehensive",
                            },
                            "session_id": {"type": "string", "description": "Session to analyze"},
                            "time_window_days": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 365,
                                "default": 30,
                            },
                        },
                    },
                },
            ]

            # BLOCK 5: VALIDATION & SCHEMA TOOLS
            validation_tools = [
                {
                    "name": "get_resource_schema",
                    "description": "📋 **Schema Explorer**: Get JSON schema for HACS resources with field details and validation rules",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "resource_type": {
                                "type": "string",
                                "description": "HACS resource type",
                            },
                            "simplified": {
                                "type": "boolean",
                                "description": "Return simplified schema",
                                "default": False,
                            },
                        },
                        "required": ["resource_type"],
                    },
                },
                {
                    "name": "analyze_resource_fields",
                    "description": "🔬 **Field Analyzer**: Analyze model fields with type distribution, validation rules, and usage patterns",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "resource_name": {"type": "string", "description": "Model to analyze"},
                            "field_category_filter": {
                                "type": "string",
                                "description": "Filter by field category",
                            },
                        },
                        "required": ["resource_name"],
                    },
                },
                {
                    "name": "compare_resource_schemas",
                    "description": "⚖️ **Schema Comparator**: Compare multiple model schemas to identify differences, similarities, and integration points",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "resource_names": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Models to compare",
                            },
                            "comparison_focus": {
                                "type": "string",
                                "enum": ["fields", "types", "validation"],
                                "default": "fields",
                            },
                        },
                        "required": ["resource_names"],
                    },
                },
            ]

            # BLOCK 6: ADVANCED MODEL TOOLS
            advanced_tools = [
                {
                    "name": "create_view_resource_schema",
                    "description": "🎨 **View Creator**: Create custom model views with selected fields and validation rules for specific use cases",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "resource_name": {"type": "string", "description": "Base model name"},
                            "fields": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Fields to include",
                            },
                            "view_name": {"type": "string", "description": "Custom view name"},
                            "include_optional": {"type": "boolean", "default": True},
                        },
                        "required": ["resource_name", "fields"],
                    },
                },
                {
                    "name": "suggest_view_fields",
                    "description": "💡 **Field Suggester**: Get intelligent field suggestions for model views based on use case and context",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "resource_name": {"type": "string", "description": "Base model"},
                            "use_case": {"type": "string", "description": "Intended use case"},
                            "max_fields": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 50,
                                "default": 10,
                            },
                        },
                        "required": ["resource_name", "use_case"],
                    },
                },
                {
                    "name": "optimize_resource_for_llm",
                    "description": "🚀 **LLM Optimizer**: Optimize HACS models for LLM interactions with intelligent field selection and token efficiency",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "resource_name": {"type": "string", "description": "Model to optimize"},
                            "optimization_goal": {
                                "type": "string",
                                "enum": [
                                    "token_efficiency",
                                    "accuracy",
                                    "completeness",
                                    "simplicity",
                                ],
                                "default": "token_efficiency",
                            },
                            "target_use_case": {
                                "type": "string",
                                "enum": [
                                    "structured_output",
                                    "classification",
                                    "extraction",
                                    "validation",
                                ],
                                "default": "structured_output",
                            },
                            "preserve_validation": {"type": "boolean", "default": True},
                        },
                        "required": ["resource_name"],
                    },
                },
            ]

            # BLOCK 7: KNOWLEDGE MANAGEMENT TOOLS
            knowledge_tools = [
                {
                    "name": "create_knowledge_item",
                    "description": "📚 **Knowledge Creator**: Create structured knowledge items for clinical decision support and guidelines",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Knowledge item title"},
                            "content": {"type": "string", "description": "Knowledge content"},
                            "knowledge_type": {
                                "type": "string",
                                "enum": ["fact", "rule", "guideline", "protocol"],
                                "default": "fact",
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Categorization tags",
                            },
                            "metadata": {"type": "object", "description": "Additional metadata"},
                        },
                        "required": ["title", "content"],
                    },
                },
            ]

            # Combine all tool blocks
            all_tools = []

            # Add tools with block headers for organization
            tool_blocks = [
                ("🔍 MODEL DISCOVERY & DEVELOPMENT", model_tools),
                ("📋 REGISTRY & CRUD OPERATIONS", registry_tools),
                ("🔍 SEARCH & DISCOVERY", search_tools),
                ("🧠 MEMORY MANAGEMENT", memory_tools),
                ("✅ VALIDATION & SCHEMA", validation_tools),
                ("🎨 ADVANCED MODEL TOOLS", advanced_tools),
                ("📚 KNOWLEDGE MANAGEMENT", knowledge_tools),
            ]

            for block_name, tools in tool_blocks:
                # Add a separator comment (for documentation purposes)
                all_tools.extend(tools)

            # Add system status and capabilities
            capabilities = {
                "total_tools": len(all_tools),
                "tool_blocks": len(tool_blocks),
                "hacs_tools_available": hacs_tools_available,
                "crud_operations": self.db_adapter is not None,
                "vector_search": self.vector_store is not None,
                "audit_trails": self.db_adapter is not None,
                "fhir_validation": True,
                "security_filters": True,
                "memory_management": True,
                "semantic_search": self.vector_store is not None,
                "model_versioning": True,
                "schema_validation": True,
            }

            # Add persistence status
            persistence_status = {
                "database_connected": self.db_adapter is not None,
                "vector_store_connected": self.vector_store is not None,
                "migration_status": "ready" if self.db_adapter else "unavailable",
                "security_enabled": True,
            }

            return MCPResponse(
                id=request.id,
                result={
                    "tools": all_tools,
                    "capabilities": capabilities,
                    "persistence_status": persistence_status,
                    "tool_organization": {
                        "blocks": [block_name for block_name, _ in tool_blocks],
                        "total_tools_per_block": {
                            block_name: len(tools) for block_name, tools in tool_blocks
                        },
                    },
                    "server_info": {
                        "name": "Enhanced HACS MCP Server",
                        "version": "2.0.0",
                        "description": "Comprehensive HACS tool server with memory, registry, search, and model management capabilities",
                        "features": [
                            "Complete HACS model ecosystem",
                            "Advanced memory management",
                            "Semantic search & discovery",
                            "FHIR-compliant validation",
                            "Enterprise security",
                            "Audit trails & versioning",
                        ],
                    },
                },
            )

        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            return MCPResponse(
                id=request.id,
                error={
                    "code": -32603,
                    "message": "Internal error",
                    "data": {"details": str(e)},
                },
            )

    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle incoming MCP requests with enhanced error handling and logging."""
        try:
            logger.debug(f"Handling MCP request: {request.method}")

            if request.method == "tools/list":
                return await self._handle_list_tools(request)
            elif request.method == "tools/call":
                return await self._handle_use_tool(request)
            else:
                return MCPResponse(
                    id=request.id,
                    error={
                        "code": -32601,
                        "message": "Method not found",
                        "data": {"method": request.method},
                    },
                )

        except Exception as e:
            logger.error(f"Unexpected error handling request: {e}")
            return MCPResponse(
                id=request.id,
                error={
                    "code": -32603,
                    "message": "Internal error",
                    "data": {"details": str(e)},
                },
            )

    def get_persistence_status(self) -> Dict[str, Any]:
        """Get current persistence status for monitoring and debugging."""
        status = {
            "database": {
                "connected": self.db_adapter is not None,
                "adapter_type": type(self.db_adapter).__name__ if self.db_adapter else None,
            },
            "vector_store": {
                "connected": self.vector_store is not None,
                "store_type": type(self.vector_store).__name__ if self.vector_store else None,
            },
            "capabilities": {
                "persistence_available": PERSISTENCE_AVAILABLE,
                "qdrant_available": QDRANT_AVAILABLE,
                "crud_operations": self.db_adapter is not None,
                "vector_search": self.vector_store is not None,
            },
        }

        # Add migration status if database is available
        if self.db_adapter:
            try:
                database_url = os.getenv("DATABASE_URL")
                if database_url:
                    migration_status = get_migration_status(database_url)
                    status["migration"] = migration_status
            except Exception as e:
                status["migration"] = {"error": str(e)}

        return status


def create_mcp_server(auth_manager: AuthManager | None = None) -> HacsMCPServer:
    """Create a HACS MCP server instance with enhanced persistence."""
    return HacsMCPServer()
