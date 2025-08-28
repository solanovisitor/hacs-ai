"""
Tests for HACS database utilities

These tests verify the database inspection and utility functions work correctly
with both mock and real database connections.
"""

import asyncio
import os
from unittest.mock import patch

import pytest

from hacs_persistence.database_utils import (
    get_database_info,
    get_hacs_schema_summary,
    verify_database_environment,
)


class TestDatabaseUtils:
    """Test database utility functions."""

    @pytest.mark.asyncio
    async def test_get_database_info_missing_url(self):
        """Test get_database_info with missing DATABASE_URL."""
        with patch.dict(os.environ, {}, clear=True):
            result = await get_database_info()
            assert "error" in result
            assert "DATABASE_URL not provided" in result["error"]

    @pytest.mark.asyncio
    async def test_get_hacs_schema_summary_calls_migration_status(self):
        """Test that get_hacs_schema_summary uses migration status helper."""
        mock_status = {
            "schema_breakdown": {"hacs_core": 7, "hacs_clinical": 22},
            "total_tables": 29,
            "expected_tables": 23,
            "migration_complete": True,
            "pgvector_enabled": True
        }

        with patch('hacs_persistence.database_utils.get_migration_status') as mock_get_status:
            mock_get_status.return_value = mock_status

            result = await get_hacs_schema_summary()

            assert result["hacs_schemas"] == {"hacs_core": 7, "hacs_clinical": 22}
            assert result["total_tables"] == 29
            assert result["migration_complete"] is True
            assert result["pgvector_enabled"] is True
            mock_get_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_database_environment_structure(self):
        """Test that verify_database_environment returns expected structure."""
        # Mock a complete successful result
        mock_db_info = {
            "status": "connected",
            "postgresql_version": "PostgreSQL 15.0",
            "database_name": "test_db",
            "connection": {
                "host": "localhost",
                "ssl_mode": "require"
            }
        }

        mock_schema_info = {
            "hacs_schemas": {"hacs_core": 7},
            "migration_complete": True,
            "pgvector_enabled": True
        }

        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test@localhost/test"}):
            with patch('hacs_persistence.database_utils.get_database_info') as mock_db:
                with patch('hacs_persistence.database_utils.get_hacs_schema_summary') as mock_schema:
                    mock_db.return_value = mock_db_info
                    mock_schema.return_value = mock_schema_info

                    result = await verify_database_environment()

                    # Check structure
                    assert "environment_variables" in result
                    assert "database_url_source" in result
                    assert "connection_test" in result
                    assert "hacs_schemas" in result
                    assert "recommendations" in result

                    # Check specific values
                    assert result["database_url_source"] == "DATABASE_URL"
                    assert result["connection_test"] == mock_db_info
                    assert result["hacs_schemas"] == mock_schema_info

    def test_environment_variable_precedence(self):
        """Test that environment variables are checked in correct order."""
        # Test DATABASE_URL takes precedence
        with patch.dict(os.environ, {
            "DATABASE_URL": "url1",
            "HACS_DATABASE_URL": "url2",
            "POSTGRES_URL": "url3"
        }):
            # Import here to get fresh environment
            from hacs_persistence.database_utils import verify_database_environment

            # The function should find DATABASE_URL first
            result = asyncio.run(verify_database_environment())
            assert result["database_url_source"] == "DATABASE_URL"


@pytest.mark.integration
class TestDatabaseUtilsIntegration:
    """Integration tests that require a real database connection."""

    @pytest.mark.asyncio
    async def test_real_database_info(self):
        """Test get_database_info with real database (if available)."""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            pytest.skip("DATABASE_URL not available for integration test")

        result = await get_database_info(database_url)

        if "error" not in result:
            # If connection succeeds, check structure
            assert result["status"] == "connected"
            assert "postgresql_version" in result
            assert "database_name" in result
            assert "connection" in result
            assert "host" in result["connection"]

    @pytest.mark.asyncio
    async def test_real_schema_summary(self):
        """Test get_hacs_schema_summary with real database (if available)."""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            pytest.skip("DATABASE_URL not available for integration test")

        result = await get_hacs_schema_summary(database_url)

        if "error" not in result:
            # If migration status succeeds, check structure
            assert "hacs_schemas" in result
            assert "total_tables" in result
            assert "migration_complete" in result
            assert isinstance(result["hacs_schemas"], dict)

    @pytest.mark.asyncio
    async def test_real_environment_verification(self):
        """Test verify_database_environment with real setup (if available)."""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            pytest.skip("DATABASE_URL not available for integration test")

        result = await verify_database_environment()

        # Should always have these keys regardless of connection success
        assert "environment_variables" in result
        assert "recommendations" in result
        assert isinstance(result["recommendations"], list)

        # Check environment variables structure
        env_vars = result["environment_variables"]
        expected_vars = ["DATABASE_URL", "HACS_DATABASE_URL", "POSTGRES_URL", "HACS_POSTGRES_URL"]
        for var in expected_vars:
            assert var in env_vars
            assert env_vars[var] in ["✓ Set", "✗ Not set"]


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])
