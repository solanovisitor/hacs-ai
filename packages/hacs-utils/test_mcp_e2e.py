#!/usr/bin/env python3
"""
End-to-End Test for HACS MCP Server

Tests the complete MCP implementation including:
- Message parsing and validation
- Tool listing and execution using hacs-tools
- Authentication integration
- Error handling
"""

import asyncio
import json
import logging

import pytest

from hacs_core.auth import AuthConfig, AuthManager
from hacs_utils.mcp.messages import ErrorCodes, MCPRequest
from hacs_utils.mcp.server import HacsMCPServer


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestHacsMCPServer:
    """Test suite for HACS MCP Server."""

    @pytest.fixture
    def auth_manager(self):
        """Create a test auth manager."""
        config = AuthConfig(
            jwt_secret="test-secret",
            token_expire_minutes=30
        )
        return AuthManager(config)

    @pytest.fixture
    def server(self, auth_manager):
        """Create a test MCP server."""
        return HacsMCPServer(auth_manager=auth_manager)

    async def test_initialize_request(self, server):
        """Test MCP initialization."""
        request = MCPRequest(
            id="test-1",
            method="initialize",
            params={
                "protocolVersion": "2025-03-26",
                "capabilities": {"sampling": False},
                "clientInfo": {"name": "Test Client", "version": "1.0.0"}
            }
        )

        response = await server.handle_request(request)

        assert response.id == "test-1"
        assert response.result is not None
        assert response.error is None
        assert "protocolVersion" in response.result
        assert "capabilities" in response.result
        assert "serverInfo" in response.result

    async def test_list_tools(self, server):
        """Test tools listing."""
        request = MCPRequest(
            id="test-2",
            method="tools/list",
            params={}
        )

        response = await server.handle_request(request)

        assert response.id == "test-2"
        assert response.result is not None
        assert response.error is None
        assert "tools" in response.result

        tools = response.result["tools"]
        tool_names = [tool["name"] for tool in tools]

        # Check that expected tools are available
        expected_tools = [
            "get_available_resources",
            "get_resource_schema",
            "find_resources",
            "get_resource",
            "create_resource",
            "update_resource"
        ]

        for tool_name in expected_tools:
            assert tool_name in tool_names

    async def test_get_available_resources_tool(self, server):
        """Test get_available_resources tool (should use hacs-tools)."""
        request = MCPRequest(
            id="test-3",
            method="tools/call",
            params={
                "name": "get_available_resources",
                "arguments": {}
            }
        )

        response = await server.handle_request(request)

        assert response.id == "test-3"
        assert response.result is not None
        assert response.error is None

        # Parse the result content
        content = response.result["content"][0]["text"]
        result = json.loads(content)

        # Should return either an error or a list of resource types
        if isinstance(result, dict) and "error" in result:
            assert "HACS Tools not available" in result["error"]
        else:
            # If hacs-tools is available, should return list of resource types
            assert isinstance(result, list)
            assert "Patient" in result

    async def test_get_resource_schema_tool(self, server):
        """Test get_resource_schema tool (should use hacs-tools)."""
        request = MCPRequest(
            id="test-4",
            method="tools/call",
            params={
                "name": "get_resource_schema",
                "arguments": {"resource_type": "Patient"}
            }
        )

        response = await server.handle_request(request)

        assert response.id == "test-4"
        assert response.result is not None
        assert response.error is None

        # Parse the result content
        content = response.result["content"][0]["text"]
        result = json.loads(content)

        # Should return either the schema or an error about tools not being available
        if isinstance(result, dict) and "error" in result:
            # Could be HACS Tools not available OR invalid resource type
            assert "error" in result
            assert any(phrase in result["error"] for phrase in [
                "HACS Tools not available",
                "Invalid resource type",
                "Unknown resource type"
            ])
        else:
            # If hacs-tools is available, should return a schema
            assert isinstance(result, dict)
            assert "type" in result or "properties" in result

    async def test_get_resource_tool(self, server):
        """Test get_resource tool (should use hacs-tools)."""
        request = MCPRequest(
            id="test-5",
            method="tools/call",
            params={
                "name": "get_resource",
                "arguments": {
                    "resource_type": "Patient",
                    "resource_id": "patient-123"
                }
            }
        )

        response = await server.handle_request(request)

        assert response.id == "test-5"
        assert response.result is not None
        assert response.error is None

        # Parse the result content
        content = response.result["content"][0]["text"]
        result = json.loads(content)

        # Should return an error (either tools not available or resource not found)
        assert "error" in result
        assert any(phrase in result["error"] for phrase in [
            "HACS Tools not available",
            "Invalid resource type",
            "Unknown resource type",
            "not found",
            "Failed to retrieve"
        ])

    async def test_invalid_tool_name(self, server):
        """Test calling a non-existent tool."""
        request = MCPRequest(
            id="test-6",
            method="tools/call",
            params={
                "name": "nonexistent_tool",
                "arguments": {}
            }
        )

        response = await server.handle_request(request)

        assert response.id == "test-6"
        assert response.result is None
        assert response.error is not None
        assert response.error.code == ErrorCodes.METHOD_NOT_FOUND

    async def test_invalid_method(self, server):
        """Test calling a non-existent method."""
        request = MCPRequest(
            id="test-7",
            method="invalid/method",
            params={}
        )

        response = await server.handle_request(request)

        assert response.id == "test-7"
        assert response.result is None
        assert response.error is not None
        assert response.error.code == ErrorCodes.METHOD_NOT_FOUND

    async def test_malformed_tool_call(self, server):
        """Test malformed tool call parameters."""
        request = MCPRequest(
            id="test-8",
            method="tools/call",
            params={
                # Missing required 'name' parameter
                "arguments": {}
            }
        )

        response = await server.handle_request(request)

        assert response.id == "test-8"
        assert response.result is None
        assert response.error is not None
        assert response.error.code == ErrorCodes.INTERNAL_ERROR


async def test_tool_handlers_directly():
    """Test tool handlers directly without MCP server."""
    from hacs_utils.mcp.tools import (
        get_available_resources_tool,
        get_resource_schema_tool,
        find_resources_tool,
        get_resource_tool,
    )

    # Test get_available_resources (should fail gracefully without hacs-tools)
    result = await get_available_resources_tool({})
    if isinstance(result, dict) and "error" in result:
        assert "HACS Tools not available" in result["error"]
    else:
        assert isinstance(result, list)

    # Test get_resource_schema with invalid type (should fail without hacs-tools)
    result = await get_resource_schema_tool({"resource_type": "Patient"})
    assert isinstance(result, dict)
    assert "error" in result

    # Test find_resources with missing parameters
    result = await find_resources_tool({})
    assert isinstance(result, dict)
    assert "error" in result

    # Test get_resource with missing parameters
    result = await get_resource_tool({})
    assert isinstance(result, dict)
    assert "error" in result


def test_message_validation():
    """Test MCP message validation."""
    from hacs_utils.mcp.messages import MCPRequest, MCPResponse, MCPError

    # Valid request
    request = MCPRequest(
        id="test",
        method="test_method",
        params={"key": "value"}
    )
    assert request.jsonrpc == "2.0"
    assert request.id == "test"

    # Valid response with result
    response = MCPResponse(
        id="test",
        result={"data": "value"}
    )
    assert response.error is None

    # Valid response with error
    error_response = MCPResponse(
        id="test",
        error=MCPError(code=-32603, message="Internal error")
    )
    assert error_response.result is None

    # Invalid response (both result and error)
    with pytest.raises(ValueError):
        MCPResponse(
            id="test",
            result={"data": "value"},
            error=MCPError(code=-32603, message="Internal error")
        )


async def main():
    """Run all tests."""
    logger.info("Running HACS MCP Server E2E Tests")

    # Test message validation
    test_message_validation()
    logger.info("✓ Message validation tests passed")

    # Test tool handlers directly
    await test_tool_handlers_directly()
    logger.info("✓ Tool handler tests passed")

    # Create server for integration tests
    auth_manager = AuthManager(AuthConfig(
        jwt_secret="test-secret",
        token_expire_minutes=30
    ))
    server = HacsMCPServer(auth_manager=auth_manager)

    # Run server tests
    test_suite = TestHacsMCPServer()

    await test_suite.test_initialize_request(server)
    logger.info("✓ Initialize request test passed")

    await test_suite.test_list_tools(server)
    logger.info("✓ List tools test passed")

    await test_suite.test_get_available_resources_tool(server)
    logger.info("✓ Get available resources test passed")

    await test_suite.test_get_resource_schema_tool(server)
    logger.info("✓ Get resource schema test passed")

    await test_suite.test_get_resource_tool(server)
    logger.info("✓ Get resource test passed")

    await test_suite.test_invalid_tool_name(server)
    logger.info("✓ Invalid tool name test passed")

    await test_suite.test_invalid_method(server)
    logger.info("✓ Invalid method test passed")

    await test_suite.test_malformed_tool_call(server)
    logger.info("✓ Malformed tool call test passed")

    logger.info("🎉 All HACS MCP Server tests passed!")


if __name__ == "__main__":
    asyncio.run(main())