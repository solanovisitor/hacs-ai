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
from .tools import execute_tool

# Enhanced persistence imports
try:
    from hacs_persistence import (
        PostgreSQLAdapter,
        initialize_hacs_database,
        get_migration_status
    )
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
    """Enhanced HACS MCP Server with security, persistence, and comprehensive tool integration."""

    def __init__(self):
        """Initialize the enhanced HACS MCP server with security and persistence."""
        self.version = "1.0.0"
        self.server_info = {
            "name": "HACS MCP Server",
            "version": self.version,
            "description": "Healthcare Agent Communication Standard Model Context Protocol Server"
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
        # Database initialization with migration
        database_url = os.getenv("DATABASE_URL")
        if database_url and PERSISTENCE_AVAILABLE:
            try:
                logger.info("Initializing HACS database with migration...")

                # Check migration status first
                status = get_migration_status(database_url)
                logger.info(f"Migration status: {status}")

                if status.get("error"):
                    logger.warning(f"⚠️ Migration status check failed: {status.get('error')}")
                elif status.get("migration_complete", False):
                    logger.info(f"✅ HACS schemas ready - found: {', '.join(status.get('schemas_found', []))}")
                else:
                    logger.info("Running HACS database migration...")
                    success = initialize_hacs_database(database_url)
                    if success:
                        logger.info("✅ HACS database migration completed successfully")
                        logger.info(f"📊 Created schemas: {', '.join(['hacs_core', 'hacs_clinical', 'hacs_registry', 'hacs_agents', 'hacs_admin', 'hacs_audit'])}")
                    else:
                        logger.warning("⚠️ Database migration failed, using fallback mode")

                # Initialize adapter
                self.db_adapter = PostgreSQLAdapter(database_url=database_url)
                logger.info("PostgreSQL persistence adapter initialized")

            except Exception as e:
                self.db_adapter = None
                logger.warning(f"Could not initialize PostgreSQL adapter: {e}. CRUD operations will be mocked.")
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
                    create_if_not_exists=True
                )
                logger.info(f"Qdrant vector store initialized at {qdrant_url}")
            except Exception as e:
                self.vector_store = None
                logger.warning(f"Could not initialize Qdrant vector store: {e}. Vector operations will be disabled.")

    async def _handle_call_tool(self, request: MCPRequest) -> MCPResponse:
        """Handle tools/call request with enhanced persistence-enabled execution."""
        try:
            params = CallToolParams(**request.params)

            # Create enhanced actor context
            from hacs_core import Actor
            actor = Actor(
                id="mcp-server",
                name="HACS MCP Server",
                role="system",
                permissions=["admin:*", "audit:*"],
                session_status="active"
            )

            # Execute tool with full persistence context
            result = await execute_tool(
                tool_name=params.name,
                params=params.arguments,
                db_adapter=self.db_adapter,
                vector_store=self.vector_store,
                actor=actor
            )

            return MCPResponse(id=request.id, result=result.model_dump())

        except Exception as e:
            logger.error(f"Error executing tool {request.params.get('name', 'unknown')}: {e}")
            return MCPResponse(
                id=request.id,
                error={
                    "code": -32603,
                    "message": "Internal error",
                    "data": {"details": str(e)},
                },
        )

    async def _handle_list_tools(self, request: MCPRequest) -> MCPResponse:
        """Handle tools/list requests with comprehensive HACS tool coverage organized in blocks."""
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
                    "name": "discover_hacs_resources",
                    "description": "🔍 **Model Discovery**: Explore all available HACS models with comprehensive metadata, field analysis, and usage patterns for development planning",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "category_filter": {"type": "string", "description": "Filter by model category (clinical, administrative, workflow)"},
                            "include_field_counts": {"type": "boolean", "description": "Include detailed field statistics", "default": True},
                            "include_examples": {"type": "boolean", "description": "Include usage examples", "default": True}
                        },
                    },
                },
                {
                    "name": "get_hacs_resource_schema",
                    "description": "📋 **Schema Inspector**: Get detailed schema information for HACS models including field types, validation rules, examples, and FHIR mappings",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "resource_type": {"type": "string", "description": "HACS resource type to inspect"},
                            "include_examples": {"type": "boolean", "description": "Include field examples", "default": True},
                            "include_validation_rules": {"type": "boolean", "description": "Include validation information", "default": True},
                        },
                        "required": ["resource_type"],
                    },
                },
                {
                    "name": "create_clinical_template",
                    "description": "🏥 **Template Generator**: Create pre-configured clinical templates for common healthcare scenarios with FHIR compliance and workflow integration",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "template_type": {"type": "string", "enum": ["assessment", "intake", "discharge", "monitoring", "referral"], "description": "Type of clinical template"},
                            "focus_area": {"type": "string", "description": "Clinical focus area (cardiology, general, emergency, mental_health, pediatric)"},
                            "complexity_level": {"type": "string", "enum": ["minimal", "standard", "comprehensive"], "description": "Detail level", "default": "standard"},
                            "include_workflow_fields": {"type": "boolean", "description": "Include workflow management fields", "default": True},
                        },
                        "required": ["template_type", "focus_area"],
                    },
                },
                {
                    "name": "create_model_stack",
                    "description": "🏗️ **Model Composer**: Build complex data structures by stacking multiple HACS models with intelligent field merging and conflict resolution",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "base_model": {"type": "string", "description": "Base HACS model name"},
                            "stack_name": {"type": "string", "description": "Name for the composed model"},
                            "extensions": {"type": "array", "items": {"type": "object"}, "description": "Extension model specifications"},
                            "merge_strategy": {"type": "string", "enum": ["overlay", "prefix", "namespace"], "description": "Field conflict resolution", "default": "overlay"},
                        },
                        "required": ["base_model", "stack_name"],
                    },
                },
                {
                    "name": "version_hacs_resource",
                    "description": "📦 **Version Manager**: Create and manage versions of HACS models with schema tracking, change logs, and deployment status",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "model_name": {"type": "string", "description": "Model to version"},
                            "version": {"type": "string", "description": "Version identifier (e.g., '1.0.0')"},
                            "description": {"type": "string", "description": "Change description"},
                            "schema_definition": {"type": "object", "description": "Schema definition"},
                            "tags": {"type": "array", "items": {"type": "string"}, "description": "Version tags"},
                            "status": {"type": "string", "enum": ["draft", "published", "deprecated"], "default": "published"},
                        },
                        "required": ["model_name", "version", "description", "schema_definition"],
                    },
                },
            ]

            # BLOCK 2: REGISTRY & CRUD TOOLS
            registry_tools = [
                {
                    "name": "create_resource",
                    "description": "➕ **Resource Creator**: Create new HACS resources with comprehensive validation, auto-ID generation, FHIR compliance, and persistent storage",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "resource_type": {"type": "string", "description": "Type of HACS resource to create"},
                            "resource_data": {"type": "object", "description": "Resource data following HACS schema"},
                            "validate_fhir": {"type": "boolean", "description": "Perform FHIR validation", "default": True},
                            "auto_generate_id": {"type": "boolean", "description": "Auto-generate unique ID", "default": True},
                        },
                        "required": ["resource_type", "resource_data"],
                    },
                },
                {
                    "name": "get_resource",
                    "description": "📖 **Resource Reader**: Retrieve HACS resources by ID with related data, audit information, and security validation",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "resource_type": {"type": "string", "description": "Type of HACS resource"},
                            "resource_id": {"type": "string", "description": "Unique resource identifier"},
                            "include_related": {"type": "boolean", "description": "Include related resources", "default": False},
                        },
                        "required": ["resource_type", "resource_id"],
                    },
                },
                {
                    "name": "update_resource",
                    "description": "✏️ **Resource Updater**: Update existing HACS resources with validation, conflict detection, and audit tracking",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "resource_type": {"type": "string", "description": "Type of HACS resource"},
                            "resource_id": {"type": "string", "description": "Resource identifier"},
                            "updates": {"type": "object", "description": "Fields to update"},
                            "validate_before_update": {"type": "boolean", "description": "Validate before applying", "default": True},
                        },
                        "required": ["resource_type", "resource_id", "updates"],
                    },
                },
                {
                    "name": "delete_resource",
                    "description": "🗑️ **Resource Deleter**: Delete HACS resources with security validation, audit logging, and soft delete options",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "resource_type": {"type": "string", "description": "Type of HACS resource"},
                            "resource_id": {"type": "string", "description": "Resource identifier"},
                            "soft_delete": {"type": "boolean", "description": "Soft delete (recoverable)", "default": True},
                        },
                        "required": ["resource_type", "resource_id"],
                    },
                },
                {
                    "name": "validate_resource_data",
                    "description": "✅ **Data Validator**: Validate resource data against HACS schemas with detailed error reporting and suggestions",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "resource_type": {"type": "string", "description": "HACS resource type"},
                            "data": {"type": "object", "description": "Data to validate"},
                        },
                        "required": ["resource_type", "data"],
                    },
                },
                {
                    "name": "list_available_resources",
                    "description": "📋 **Resource Catalog**: List all available HACS resource types with descriptions and capabilities",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                    },
                },
            ]

            # BLOCK 3: SEARCH & DISCOVERY TOOLS
            search_tools = [
                {
                    "name": "find_resources",
                    "description": "🔍 **Smart Search**: Advanced resource search with semantic similarity, filters, faceted search, and relevance scoring",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "resource_type": {"type": "string", "description": "Type of resource to search"},
                            "filters": {"type": "object", "description": "Field-based filters"},
                            "semantic_query": {"type": "string", "description": "Natural language search query"},
                            "limit": {"type": "integer", "minimum": 1, "maximum": 100, "description": "Max results", "default": 10},
                            "include_score": {"type": "boolean", "description": "Include relevance scores", "default": True},
                        },
                        "required": ["resource_type"],
                    },
                },
                {
                    "name": "search_hacs_records",
                    "description": "📊 **Record Search**: Search HACS records with advanced filtering, sorting, and aggregation capabilities",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "resource_type": {"type": "string", "description": "Resource type to search"},
                            "filters": {"type": "object", "description": "Search filters"},
                            "semantic_query": {"type": "string", "description": "Semantic search query"},
                            "limit": {"type": "integer", "default": 10},
                            "sort_by": {"type": "string", "description": "Sort field"},
                            "sort_order": {"type": "string", "enum": ["asc", "desc"], "default": "desc"},
                        },
                        "required": ["resource_type"],
                    },
                },
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
                            "memory_type": {"type": "string", "enum": ["episodic", "procedural", "executive", "semantic"], "description": "Memory classification", "default": "episodic"},
                            "importance_score": {"type": "number", "minimum": 0.0, "maximum": 1.0, "description": "Importance (0.0-1.0)", "default": 0.5},
                            "tags": {"type": "array", "items": {"type": "string"}, "description": "Categorization tags"},
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
                            "memory_type": {"type": "string", "enum": ["episodic", "procedural", "executive", "semantic"], "description": "Memory type filter"},
                            "session_id": {"type": "string", "description": "Session filter"},
                            "min_importance": {"type": "number", "minimum": 0.0, "maximum": 1.0, "default": 0.0},
                            "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
                            "similarity_threshold": {"type": "number", "minimum": 0.0, "maximum": 1.0, "default": 0.7},
                        },
                    },
                },
                {
                    "name": "consolidate_memories",
                    "description": "🗂️ **Memory Consolidator**: Merge related memories into summaries for efficient storage and faster recall",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string", "description": "Session to consolidate"},
                            "memory_type": {"type": "string", "enum": ["episodic", "procedural", "executive"], "default": "episodic"},
                            "strategy": {"type": "string", "enum": ["temporal", "importance", "semantic"], "default": "temporal"},
                            "min_memories": {"type": "integer", "minimum": 2, "maximum": 20, "default": 3},
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
                            "context_type": {"type": "string", "enum": ["general", "clinical", "procedural", "executive"], "default": "general"},
                            "max_memories": {"type": "integer", "minimum": 1, "maximum": 20, "default": 5},
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
                            "analysis_type": {"type": "string", "enum": ["comprehensive", "temporal", "importance", "connections"], "default": "comprehensive"},
                            "session_id": {"type": "string", "description": "Session to analyze"},
                            "time_window_days": {"type": "integer", "minimum": 1, "maximum": 365, "default": 30},
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
                            "resource_type": {"type": "string", "description": "HACS resource type"},
                            "simplified": {"type": "boolean", "description": "Return simplified schema", "default": False},
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
                            "model_name": {"type": "string", "description": "Model to analyze"},
                            "field_category_filter": {"type": "string", "description": "Filter by field category"},
                        },
                        "required": ["model_name"],
                    },
                },
                {
                    "name": "compare_resource_schemas",
                    "description": "⚖️ **Schema Comparator**: Compare multiple model schemas to identify differences, similarities, and integration points",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "model_names": {"type": "array", "items": {"type": "string"}, "description": "Models to compare"},
                            "comparison_focus": {"type": "string", "enum": ["fields", "types", "validation"], "default": "fields"},
                        },
                        "required": ["model_names"],
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
                            "model_name": {"type": "string", "description": "Base model name"},
                            "fields": {"type": "array", "items": {"type": "string"}, "description": "Fields to include"},
                            "view_name": {"type": "string", "description": "Custom view name"},
                            "include_optional": {"type": "boolean", "default": True},
                        },
                        "required": ["model_name", "fields"],
                    },
                },
                {
                    "name": "suggest_view_fields",
                    "description": "💡 **Field Suggester**: Get intelligent field suggestions for model views based on use case and context",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "model_name": {"type": "string", "description": "Base model"},
                            "use_case": {"type": "string", "description": "Intended use case"},
                            "max_fields": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
                        },
                        "required": ["model_name", "use_case"],
                    },
                },
                {
                    "name": "optimize_resource_for_llm",
                    "description": "🚀 **LLM Optimizer**: Optimize HACS models for LLM interactions with intelligent field selection and token efficiency",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "model_name": {"type": "string", "description": "Model to optimize"},
                            "optimization_goal": {"type": "string", "enum": ["token_efficiency", "accuracy", "completeness", "simplicity"], "default": "token_efficiency"},
                            "target_use_case": {"type": "string", "enum": ["structured_output", "classification", "extraction", "validation"], "default": "structured_output"},
                            "preserve_validation": {"type": "boolean", "default": True},
                        },
                        "required": ["model_name"],
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
                            "knowledge_type": {"type": "string", "enum": ["fact", "rule", "guideline", "protocol"], "default": "fact"},
                            "tags": {"type": "array", "items": {"type": "string"}, "description": "Categorization tags"},
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
                        "total_tools_per_block": {block_name: len(tools) for block_name, tools in tool_blocks}
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
                            "Audit trails & versioning"
                        ]
                    }
                }
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
                return await self._handle_call_tool(request)
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
            }
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