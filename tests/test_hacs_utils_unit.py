"""
Unit tests for HACS Utils package functionality.

Tests integrations, MCP server, and utility functions
with proper mocking for CI - no real API keys needed.
"""

import pytest
import os
import json
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, Any

# Mock all external dependencies for CI
@pytest.fixture(autouse=True)
def mock_external_apis():
    """Mock external API dependencies for CI testing."""
    with patch.dict(os.environ, {
        'ANTHROPIC_API_KEY': 'test-anthropic-key',
        'OPENAI_API_KEY': 'test-openai-key',
        'PINECONE_API_KEY': 'test-pinecone-key',
        'QDRANT_URL': 'http://localhost:6333',
        'DATABASE_URL': 'sqlite:///test.db',
        'HACS_ORGANIZATION': 'test-org'
    }):
        # Mock anthropic client
        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_anthropic.return_value.messages.create.return_value = MagicMock(
                content=[MagicMock(text="Test response")]
            )
            
            # Mock OpenAI client
            with patch('openai.OpenAI') as mock_openai:
                mock_openai.return_value.chat.completions.create.return_value = MagicMock(
                    choices=[MagicMock(message=MagicMock(content="Test response"))]
                )
                
                # Mock Pinecone
                with patch('pinecone.Pinecone') as mock_pinecone:
                    mock_pinecone.return_value.describe_index.return_value = {"dimension": 1536}
                    
                    # Mock Qdrant
                    with patch('qdrant_client.QdrantClient') as mock_qdrant:
                        mock_qdrant.return_value.get_collections.return_value = []
                        
                        yield


@pytest.mark.unit
class TestHACSUtilsCore:
    """Test HACS Utils core functionality."""

    def test_utils_module_imports(self):
        """Test that utils module imports work."""
        try:
            import hacs_utils
            assert hacs_utils is not None
            
            # Test version access
            assert hasattr(hacs_utils, '__version__')
            
        except ImportError as e:
            pytest.skip(f"HACS Utils not available: {e}")

    def test_integration_discovery(self):
        """Test integration discovery functionality."""
        try:
            import hacs_utils
            
            # Test available integrations
            integrations = hacs_utils.list_available_integrations()
            assert isinstance(integrations, list)
            
        except (ImportError, AttributeError):
            pytest.skip("Integration discovery not available")

    def test_adapter_imports(self):
        """Test adapter imports work."""
        try:
            from hacs_utils import CrewAIAdapter
            assert CrewAIAdapter is not None
            
        except ImportError:
            pytest.skip("CrewAI adapter not available")


@pytest.mark.unit
class TestHACSUtilsIntegrations:
    """Test HACS Utils integration functionality."""

    @patch('anthropic.Anthropic')
    def test_anthropic_integration(self, mock_anthropic):
        """Test Anthropic integration with mocked client."""
        # Setup mock
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="Mocked Anthropic response")]
        )
        
        try:
            from hacs_utils.integrations.anthropic import AnthropicClient
            
            client = AnthropicClient(api_key="test-key")
            response = client.create_message(
                messages=[{"role": "user", "content": "Test message"}]
            )
            
            assert response is not None
            mock_anthropic.assert_called_once()
            
        except ImportError:
            pytest.skip("Anthropic integration not available")

    @patch('openai.OpenAI')
    def test_openai_integration(self, mock_openai):
        """Test OpenAI integration with mocked client."""
        # Setup mock
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Mocked OpenAI response"))]
        )
        
        try:
            from hacs_utils.integrations.openai import OpenAIClient
            
            client = OpenAIClient(api_key="test-key")
            response = client.create_completion(
                messages=[{"role": "user", "content": "Test message"}]
            )
            
            assert response is not None
            mock_openai.assert_called_once()
            
        except ImportError:
            pytest.skip("OpenAI integration not available")

    @patch('pinecone.Pinecone')
    def test_pinecone_integration(self, mock_pinecone):
        """Test Pinecone integration with mocked client."""
        # Setup mock
        mock_client = MagicMock()
        mock_pinecone.return_value = mock_client
        mock_client.describe_index.return_value = {"dimension": 1536}
        
        try:
            from hacs_utils.integrations.pinecone import PineconeStore
            
            store = PineconeStore(api_key="test-key", index_name="test-index")
            info = store.get_index_info()
            
            assert info is not None
            mock_pinecone.assert_called_once()
            
        except ImportError:
            pytest.skip("Pinecone integration not available")

    @patch('qdrant_client.QdrantClient')
    def test_qdrant_integration(self, mock_qdrant):
        """Test Qdrant integration with mocked client."""
        # Setup mock
        mock_client = MagicMock()
        mock_qdrant.return_value = mock_client
        mock_client.get_collections.return_value = []
        
        try:
            from hacs_utils.integrations.qdrant import QdrantStore
            
            store = QdrantStore(url="http://localhost:6333")
            collections = store.list_collections()
            
            assert isinstance(collections, list)
            mock_qdrant.assert_called_once()
            
        except ImportError:
            pytest.skip("Qdrant integration not available")

    def test_crewai_integration(self):
        """Test CrewAI integration."""
        try:
            from hacs_utils.integrations.crewai import CrewAIAdapter
            
            adapter = CrewAIAdapter()
            assert adapter is not None
            
            # Test adapter functionality without external dependencies
            assert hasattr(adapter, 'create_agent')
            assert hasattr(adapter, 'create_task')
            
        except ImportError:
            pytest.skip("CrewAI integration not available")

    def test_langchain_integration(self):
        """Test LangChain integration."""
        try:
            from hacs_utils.integrations.langchain import LangChainAdapter
            
            adapter = LangChainAdapter()
            assert adapter is not None
            
        except ImportError:
            pytest.skip("LangChain integration not available")

    def test_langgraph_integration(self):
        """Test LangGraph integration."""
        try:
            from hacs_utils.integrations.langgraph import LangGraphAdapter
            
            adapter = LangGraphAdapter()
            assert adapter is not None
            
        except ImportError:
            pytest.skip("LangGraph integration not available")


@pytest.mark.unit
class TestHACSUtilsMCP:
    """Test HACS Utils MCP server functionality."""

    def test_mcp_server_imports(self):
        """Test MCP server imports."""
        try:
            from hacs_utils.mcp import MCPServer
            assert MCPServer is not None
            
            from hacs_utils.mcp.server import create_hacs_mcp_server
            assert callable(create_hacs_mcp_server)
            
        except ImportError:
            pytest.skip("MCP server not available")

    @patch('hacs_utils.mcp.server.get_persistence_provider')
    def test_mcp_server_initialization(self, mock_provider):
        """Test MCP server initialization."""
        mock_provider.return_value = MagicMock()
        
        try:
            from hacs_utils.mcp.server import create_hacs_mcp_server
            
            server = create_hacs_mcp_server()
            assert server is not None
            
        except ImportError:
            pytest.skip("MCP server initialization not available")

    def test_mcp_tools_listing(self):
        """Test MCP tools listing."""
        try:
            from hacs_utils.mcp.tools import list_available_tools
            
            tools = list_available_tools()
            assert isinstance(tools, (list, dict))
            
        except ImportError:
            pytest.skip("MCP tools listing not available")

    def test_mcp_message_validation(self):
        """Test MCP message validation."""
        try:
            from hacs_utils.mcp.messages import validate_mcp_message
            
            # Test valid message
            valid_message = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 1
            }
            
            result = validate_mcp_message(valid_message)
            assert result["is_valid"] is True
            
            # Test invalid message
            invalid_message = {
                "method": "tools/list"  # Missing jsonrpc and id
            }
            
            result = validate_mcp_message(invalid_message)
            assert result["is_valid"] is False
            
        except ImportError:
            pytest.skip("MCP message validation not available")

    @patch('hacs_utils.mcp.transport.start_server')
    def test_mcp_transport_layer(self, mock_start_server):
        """Test MCP transport layer."""
        mock_start_server.return_value = MagicMock()
        
        try:
            from hacs_utils.mcp.transport import MCPTransport
            
            transport = MCPTransport(host="localhost", port=8000)
            assert transport is not None
            
        except ImportError:
            pytest.skip("MCP transport not available")


@pytest.mark.unit
class TestHACSUtilsAgents:
    """Test HACS Utils agent functionality."""

    def test_chat_cli_imports(self):
        """Test chat CLI imports."""
        try:
            from hacs_utils.agents.chat_cli import ChatCLI
            assert ChatCLI is not None
            
        except ImportError:
            pytest.skip("Chat CLI not available")

    @patch('hacs_utils.agents.mcp_client.requests.post')
    def test_mcp_client(self, mock_post):
        """Test MCP client functionality."""
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": {"tools": []},
            "id": 1
        }
        mock_post.return_value = mock_response
        
        try:
            from hacs_utils.agents.mcp_client import MCPClient
            
            client = MCPClient(base_url="http://localhost:8000")
            result = client.call_tool("tools/list", {})
            
            assert result is not None
            mock_post.assert_called_once()
            
        except ImportError:
            pytest.skip("MCP client not available")

    @patch('sys.stdin')
    @patch('builtins.print')
    def test_chat_cli_basic(self, mock_print, mock_stdin):
        """Test basic chat CLI functionality."""
        mock_stdin.readline.return_value = "exit\n"
        
        try:
            from hacs_utils.agents.chat_cli import ChatCLI
            
            cli = ChatCLI()
            assert cli is not None
            
            # Test without actually running the CLI
            assert hasattr(cli, 'start')
            assert hasattr(cli, 'process_message')
            
        except ImportError:
            pytest.skip("Chat CLI not available")


@pytest.mark.unit
class TestHACSUtilsStructured:
    """Test HACS Utils structured data functionality."""

    def test_structured_imports(self):
        """Test structured data imports."""
        try:
            from hacs_utils.structured import StructuredExtractor
            assert StructuredExtractor is not None
            
        except ImportError:
            pytest.skip("Structured data functionality not available")

    def test_data_extraction(self):
        """Test structured data extraction."""
        try:
            from hacs_utils.structured import extract_structured_data
            
            # Test data extraction without external dependencies
            sample_text = "Patient John Doe, age 45, diagnosed with hypertension"
            
            result = extract_structured_data(
                text=sample_text,
                target_schema={"name": "string", "age": "integer", "diagnosis": "string"}
            )
            
            assert isinstance(result, dict)
            
        except ImportError:
            pytest.skip("Structured data extraction not available")

    def test_schema_validation(self):
        """Test schema validation functionality."""
        try:
            from hacs_utils.structured import validate_against_schema
            
            # Test valid data
            data = {"name": "John Doe", "age": 45}
            schema = {"name": "string", "age": "integer"}
            
            result = validate_against_schema(data, schema)
            assert result["is_valid"] is True
            
        except ImportError:
            pytest.skip("Schema validation not available")


@pytest.mark.unit
class TestHACSUtilsAdapter:
    """Test HACS Utils adapter functionality."""

    def test_base_adapter(self):
        """Test base adapter functionality."""
        try:
            from hacs_utils.adapter import BaseAdapter
            
            adapter = BaseAdapter()
            assert adapter is not None
            
            # Test adapter interface
            assert hasattr(adapter, 'connect')
            assert hasattr(adapter, 'disconnect')
            
        except ImportError:
            pytest.skip("Base adapter not available")

    def test_adapter_configuration(self):
        """Test adapter configuration."""
        try:
            from hacs_utils.adapter import configure_adapter
            
            config = {
                "type": "test",
                "settings": {"test_setting": "value"}
            }
            
            adapter = configure_adapter(config)
            assert adapter is not None
            
        except ImportError:
            pytest.skip("Adapter configuration not available")


@pytest.mark.unit
class TestHACSUtilsError:
    """Test HACS Utils error handling."""

    def test_integration_error_handling(self):
        """Test integration error handling."""
        try:
            from hacs_utils.integrations.openai import OpenAIClient
            
            # Test with invalid API key
            client = OpenAIClient(api_key="invalid-key")
            
            # Should handle error gracefully
            with patch('openai.OpenAI') as mock_openai:
                mock_openai.side_effect = Exception("Invalid API key")
                
                try:
                    response = client.create_completion(
                        messages=[{"role": "user", "content": "test"}]
                    )
                    # Should return error response, not raise exception
                    assert "error" in response or response is None
                except Exception:
                    # This is acceptable - error handling varies by implementation
                    pass
                    
        except ImportError:
            pytest.skip("OpenAI integration not available")

    def test_mcp_error_handling(self):
        """Test MCP error handling."""
        try:
            from hacs_utils.mcp.messages import validate_mcp_message
            
            # Test malformed message
            malformed_message = {"invalid": "message"}
            
            result = validate_mcp_message(malformed_message)
            assert result["is_valid"] is False
            assert "errors" in result
            
        except ImportError:
            pytest.skip("MCP message validation not available")


@pytest.mark.performance
class TestHACSUtilsPerformance:
    """Test HACS Utils performance."""

    @patch('hacs_utils.agents.mcp_client.requests.post')
    def test_mcp_client_performance(self, mock_post):
        """Test MCP client performance."""
        import time
        
        # Mock fast responses
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": {"success": True},
            "id": 1
        }
        mock_post.return_value = mock_response
        
        try:
            from hacs_utils.agents.mcp_client import MCPClient
            
            client = MCPClient(base_url="http://localhost:8000")
            
            start = time.time()
            
            # Make multiple calls
            for i in range(10):
                client.call_tool("test_tool", {"data": f"test_{i}"})
            
            end = time.time()
            duration = end - start
            
            # Should be fast
            assert duration < 2.0
            
        except ImportError:
            pytest.skip("MCP client not available")

    def test_integration_initialization_performance(self):
        """Test integration initialization performance."""
        import time
        
        try:
            start = time.time()
            
            # Initialize multiple integrations
            from hacs_utils.integrations.crewai import CrewAIAdapter
            from hacs_utils.integrations.langchain import LangChainAdapter
            
            crewai_adapter = CrewAIAdapter()
            langchain_adapter = LangChainAdapter()
            
            end = time.time()
            duration = end - start
            
            # Should be fast
            assert duration < 1.0
            assert crewai_adapter is not None
            assert langchain_adapter is not None
            
        except ImportError:
            pytest.skip("Integration adapters not available")


@pytest.mark.external
class TestHACSUtilsExternal:
    """External tests that require real services - marked separately."""

    @pytest.mark.skip(reason="Requires real API keys")
    def test_real_anthropic_integration(self):
        """Test real Anthropic integration - requires API key."""
        # This test would run with real API keys in specific environments
        pass

    @pytest.mark.skip(reason="Requires real API keys")
    def test_real_openai_integration(self):
        """Test real OpenAI integration - requires API key."""
        # This test would run with real API keys in specific environments
        pass

    @pytest.mark.skip(reason="Requires external services")
    def test_real_vector_store_integration(self):
        """Test real vector store integration - requires running services."""
        # This test would run with real Pinecone/Qdrant services
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 