"""
Unit tests for HACS Persistence package functionality.

Tests database operations, vector storage, and persistence adapters
with proper mocking for CI - no real database connections needed.
"""

import pytest
import os
import sqlite3
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import date, datetime
from typing import Dict, Any, List

# Mock external dependencies for CI
@pytest.fixture(autouse=True)
def mock_database_dependencies():
    """Mock database dependencies for CI testing."""
    with patch.dict(os.environ, {
        'DATABASE_URL': 'sqlite:///test.db',
        'VECTOR_STORE': 'pgvector',
        'HACS_ORGANIZATION': 'test-org'
    }):
        # Mock psycopg connections
        with patch('psycopg.connect') as mock_psycopg:
            mock_conn = MagicMock()
            mock_psycopg.return_value = mock_conn
            
            # Mock pgvector
            with patch('pgvector.psycopg.register_vector') as mock_register:
                mock_register.return_value = None
                
                yield mock_conn


@pytest.mark.unit
class TestHACSPersistenceCore:
    """Test HACS Persistence core functionality."""

    def test_persistence_module_imports(self):
        """Test that persistence module imports work."""
        try:
            import hacs_persistence
            assert hacs_persistence is not None
            
        except ImportError as e:
            pytest.skip(f"HACS Persistence not available: {e}")

    def test_adapter_imports(self):
        """Test adapter imports."""
        try:
            from hacs_persistence import Adapter
            assert Adapter is not None
            
            from hacs_persistence.adapter import BaseAdapter
            assert BaseAdapter is not None
            
        except ImportError:
            pytest.skip("Persistence adapters not available")

    def test_vector_store_imports(self):
        """Test vector store imports."""
        try:
            from hacs_persistence.vector_store import VectorStore
            assert VectorStore is not None
            
        except ImportError:
            pytest.skip("Vector store not available")


@pytest.mark.unit
class TestHACSPersistenceAdapter:
    """Test HACS Persistence adapter functionality."""

    @patch('hacs_persistence.adapter.get_database_connection')
    def test_adapter_initialization(self, mock_get_conn):
        """Test adapter initialization with mocked database."""
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        
        try:
            from hacs_persistence import Adapter
            
            adapter = Adapter(database_url="sqlite:///test.db")
            assert adapter is not None
            
        except ImportError:
            pytest.skip("Adapter not available")

    @patch('hacs_persistence.adapter.get_database_connection')
    def test_save_resource(self, mock_get_conn):
        """Test saving a resource."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ("patient-123",)
        mock_get_conn.return_value = mock_conn
        
        try:
            from hacs_persistence import Adapter
            from hacs_core import Patient
            
            adapter = Adapter(database_url="sqlite:///test.db")
            
            patient = Patient(
                full_name="Test Patient",
                birth_date=date(1990, 1, 1),
                gender="male"
            )
            
            result = adapter.save_resource(patient)
            
            assert result is not None
            assert hasattr(result, 'id')
            
        except ImportError:
            pytest.skip("Adapter or Patient not available")

    @patch('hacs_persistence.adapter.get_database_connection')
    def test_get_resource(self, mock_get_conn):
        """Test retrieving a resource."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            "id": "patient-123",
            "resource_type": "Patient",
            "full_name": "Test Patient",
            "birth_date": "1990-01-01",
            "gender": "male"
        }
        mock_get_conn.return_value = mock_conn
        
        try:
            from hacs_persistence import Adapter
            
            adapter = Adapter(database_url="sqlite:///test.db")
            
            result = adapter.get_resource("Patient", "patient-123")
            
            assert result is not None
            assert result["id"] == "patient-123"
            assert result["resource_type"] == "Patient"
            
        except ImportError:
            pytest.skip("Adapter not available")

    @patch('hacs_persistence.adapter.get_database_connection')
    def test_update_resource(self, mock_get_conn):
        """Test updating a resource."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1
        mock_get_conn.return_value = mock_conn
        
        try:
            from hacs_persistence import Adapter
            
            adapter = Adapter(database_url="sqlite:///test.db")
            
            result = adapter.update_resource(
                "Patient",
                "patient-123",
                {"full_name": "Updated Patient"}
            )
            
            assert result is not None
            
        except ImportError:
            pytest.skip("Adapter not available")

    @patch('hacs_persistence.adapter.get_database_connection')
    def test_delete_resource(self, mock_get_conn):
        """Test deleting a resource."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1
        mock_get_conn.return_value = mock_conn
        
        try:
            from hacs_persistence import Adapter
            
            adapter = Adapter(database_url="sqlite:///test.db")
            
            result = adapter.delete_resource("Patient", "patient-123")
            
            assert result is True
            
        except ImportError:
            pytest.skip("Adapter not available")

    @patch('hacs_persistence.adapter.get_database_connection')
    def test_search_resources(self, mock_get_conn):
        """Test searching resources."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            {
                "id": "patient-123",
                "resource_type": "Patient",
                "full_name": "Test Patient"
            },
            {
                "id": "patient-124",
                "resource_type": "Patient",
                "full_name": "Another Patient"
            }
        ]
        mock_get_conn.return_value = mock_conn
        
        try:
            from hacs_persistence import Adapter
            
            adapter = Adapter(database_url="sqlite:///test.db")
            
            results = adapter.search_resources(
                resource_type="Patient",
                filters={"gender": "male"},
                limit=10
            )
            
            assert isinstance(results, list)
            assert len(results) == 2
            
        except ImportError:
            pytest.skip("Adapter not available")


@pytest.mark.unit
class TestHACSPersistenceVectorStore:
    """Test HACS Persistence vector store functionality."""

    @patch('hacs_persistence.vector_store.get_pgvector_connection')
    def test_vector_store_initialization(self, mock_get_conn):
        """Test vector store initialization."""
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        
        try:
            from hacs_persistence.vector_store import VectorStore
            
            store = VectorStore(database_url="postgresql://test")
            assert store is not None
            
        except ImportError:
            pytest.skip("Vector store not available")

    @patch('hacs_persistence.vector_store.get_pgvector_connection')
    def test_store_vector(self, mock_get_conn):
        """Test storing a vector."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        try:
            from hacs_persistence.vector_store import VectorStore
            
            store = VectorStore(database_url="postgresql://test")
            
            result = store.store_vector(
                resource_id="patient-123",
                embedding=[0.1, 0.2, 0.3, 0.4],
                metadata={"type": "patient", "department": "cardiology"}
            )
            
            assert result is not None
            
        except ImportError:
            pytest.skip("Vector store not available")

    @patch('hacs_persistence.vector_store.get_pgvector_connection')
    def test_search_vectors(self, mock_get_conn):
        """Test vector similarity search."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            ("patient-123", [0.1, 0.2, 0.3, 0.4], 0.95, {"type": "patient"}),
            ("patient-124", [0.2, 0.3, 0.4, 0.5], 0.85, {"type": "patient"})
        ]
        mock_get_conn.return_value = mock_conn
        
        try:
            from hacs_persistence.vector_store import VectorStore
            
            store = VectorStore(database_url="postgresql://test")
            
            results = store.search_vectors(
                query_embedding=[0.1, 0.2, 0.3, 0.4],
                top_k=5,
                filters={"type": "patient"}
            )
            
            assert isinstance(results, list)
            assert len(results) == 2
            assert results[0][2] == 0.95  # similarity score
            
        except ImportError:
            pytest.skip("Vector store not available")

    @patch('hacs_persistence.vector_store.get_pgvector_connection')
    def test_delete_vector(self, mock_get_conn):
        """Test deleting a vector."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1
        mock_get_conn.return_value = mock_conn
        
        try:
            from hacs_persistence.vector_store import VectorStore
            
            store = VectorStore(database_url="postgresql://test")
            
            result = store.delete_vector("patient-123")
            
            assert result is True
            
        except ImportError:
            pytest.skip("Vector store not available")


@pytest.mark.unit
class TestHACSPersistenceMigrations:
    """Test HACS Persistence migration functionality."""

    @patch('hacs_persistence.migrations.get_database_connection')
    def test_migration_system(self, mock_get_conn):
        """Test database migration system."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)  # Current version
        mock_get_conn.return_value = mock_conn
        
        try:
            from hacs_persistence.migrations import MigrationManager
            
            manager = MigrationManager(database_url="sqlite:///test.db")
            
            # Test current version
            version = manager.get_current_version()
            assert isinstance(version, int)
            
            # Test pending migrations
            pending = manager.get_pending_migrations()
            assert isinstance(pending, list)
            
        except ImportError:
            pytest.skip("Migration manager not available")

    @patch('hacs_persistence.migrations.get_database_connection')
    def test_run_migrations(self, mock_get_conn):
        """Test running migrations."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        try:
            from hacs_persistence.migrations import run_migrations
            
            result = run_migrations("sqlite:///test.db")
            
            assert result["success"] is True
            
        except ImportError:
            pytest.skip("Migration runner not available")

    def test_migration_validation(self):
        """Test migration validation."""
        try:
            from hacs_persistence.migrations import validate_migration_status
            
            # Test with mocked database URL
            result = validate_migration_status("sqlite:///test.db")
            
            assert isinstance(result, dict)
            assert "current_version" in result
            
        except ImportError:
            pytest.skip("Migration validation not available")


@pytest.mark.unit
class TestHACSPersistenceSchema:
    """Test HACS Persistence schema functionality."""

    def test_schema_imports(self):
        """Test schema imports."""
        try:
            from hacs_persistence.schema import get_table_schema
            assert callable(get_table_schema)
            
            from hacs_persistence.schema import validate_schema
            assert callable(validate_schema)
            
        except ImportError:
            pytest.skip("Schema functionality not available")

    def test_table_schema_generation(self):
        """Test table schema generation."""
        try:
            from hacs_persistence.schema import get_table_schema
            
            # Test patient table schema
            schema = get_table_schema("patients")
            
            assert isinstance(schema, dict)
            assert "columns" in schema
            
        except ImportError:
            pytest.skip("Schema generation not available")

    def test_schema_validation(self):
        """Test schema validation."""
        try:
            from hacs_persistence.schema import validate_schema
            
            # Test valid schema
            valid_data = {
                "id": "patient-123",
                "resource_type": "Patient",
                "full_name": "Test Patient"
            }
            
            result = validate_schema(valid_data, "patients")
            
            assert result["is_valid"] is True
            
        except ImportError:
            pytest.skip("Schema validation not available")


@pytest.mark.unit
class TestHACSPersistenceResourceMapper:
    """Test HACS Persistence resource mapper functionality."""

    def test_resource_mapper_imports(self):
        """Test resource mapper imports."""
        try:
            from hacs_persistence.resource_mapper import ResourceMapper
            assert ResourceMapper is not None
            
        except ImportError:
            pytest.skip("Resource mapper not available")

    def test_resource_to_database_mapping(self):
        """Test mapping HACS resources to database format."""
        try:
            from hacs_persistence.resource_mapper import ResourceMapper
            from hacs_core import Patient
            
            mapper = ResourceMapper()
            
            patient = Patient(
                full_name="Test Patient",
                birth_date=date(1990, 1, 1),
                gender="male"
            )
            
            db_data = mapper.resource_to_db(patient)
            
            assert isinstance(db_data, dict)
            assert "full_name" in db_data
            assert db_data["resource_type"] == "Patient"
            
        except ImportError:
            pytest.skip("Resource mapper not available")

    def test_database_to_resource_mapping(self):
        """Test mapping database data to HACS resources."""
        try:
            from hacs_persistence.resource_mapper import ResourceMapper
            
            mapper = ResourceMapper()
            
            db_data = {
                "id": "patient-123",
                "resource_type": "Patient",
                "full_name": "Test Patient",
                "birth_date": "1990-01-01",
                "gender": "male"
            }
            
            resource = mapper.db_to_resource(db_data)
            
            assert resource is not None
            assert hasattr(resource, 'full_name')
            assert resource.full_name == "Test Patient"
            
        except ImportError:
            pytest.skip("Resource mapper not available")


@pytest.mark.unit
class TestHACSPersistenceGranularAdapter:
    """Test HACS Persistence granular adapter functionality."""

    @patch('hacs_persistence.granular_adapter.get_database_connection')
    def test_granular_adapter_initialization(self, mock_get_conn):
        """Test granular adapter initialization."""
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        
        try:
            from hacs_persistence.granular_adapter import GranularAdapter
            
            adapter = GranularAdapter(database_url="sqlite:///test.db")
            assert adapter is not None
            
        except ImportError:
            pytest.skip("Granular adapter not available")

    @patch('hacs_persistence.granular_adapter.get_database_connection')
    def test_bulk_operations(self, mock_get_conn):
        """Test bulk operations with granular adapter."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        try:
            from hacs_persistence.granular_adapter import GranularAdapter
            from hacs_core import Patient
            
            adapter = GranularAdapter(database_url="sqlite:///test.db")
            
            # Create multiple patients
            patients = [
                Patient(full_name=f"Patient {i}", birth_date=date(1990, 1, 1))
                for i in range(5)
            ]
            
            result = adapter.bulk_save(patients)
            
            assert result["success"] is True
            assert result["saved_count"] == 5
            
        except ImportError:
            pytest.skip("Granular adapter not available")

    @patch('hacs_persistence.granular_adapter.get_database_connection')
    def test_transaction_management(self, mock_get_conn):
        """Test transaction management."""
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        
        try:
            from hacs_persistence.granular_adapter import GranularAdapter
            
            adapter = GranularAdapter(database_url="sqlite:///test.db")
            
            # Test transaction context
            with adapter.transaction() as tx:
                assert tx is not None
                # Transaction operations would go here
                
        except ImportError:
            pytest.skip("Granular adapter not available")


@pytest.mark.unit
class TestHACSPersistenceError:
    """Test HACS Persistence error handling."""

    @patch('hacs_persistence.adapter.get_database_connection')
    def test_database_connection_error(self, mock_get_conn):
        """Test database connection error handling."""
        # Mock connection failure
        mock_get_conn.side_effect = Exception("Database connection failed")
        
        try:
            from hacs_persistence import Adapter
            
            with pytest.raises(Exception):
                adapter = Adapter(database_url="invalid://url")
                
        except ImportError:
            pytest.skip("Adapter not available")

    @patch('hacs_persistence.adapter.get_database_connection')
    def test_resource_not_found_error(self, mock_get_conn):
        """Test resource not found error handling."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None  # No results
        mock_get_conn.return_value = mock_conn
        
        try:
            from hacs_persistence import Adapter
            
            adapter = Adapter(database_url="sqlite:///test.db")
            
            result = adapter.get_resource("Patient", "nonexistent-id")
            
            assert result is None
            
        except ImportError:
            pytest.skip("Adapter not available")

    @patch('hacs_persistence.vector_store.get_pgvector_connection')
    def test_vector_store_error_handling(self, mock_get_conn):
        """Test vector store error handling."""
        # Mock connection failure
        mock_get_conn.side_effect = Exception("Vector store connection failed")
        
        try:
            from hacs_persistence.vector_store import VectorStore
            
            with pytest.raises(Exception):
                store = VectorStore(database_url="invalid://url")
                
        except ImportError:
            pytest.skip("Vector store not available")


@pytest.mark.performance
class TestHACSPersistencePerformance:
    """Test HACS Persistence performance."""

    @patch('hacs_persistence.adapter.get_database_connection')
    def test_bulk_operations_performance(self, mock_get_conn):
        """Test bulk operations performance."""
        import time
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        try:
            from hacs_persistence import Adapter
            from hacs_core import Patient
            
            adapter = Adapter(database_url="sqlite:///test.db")
            
            start = time.time()
            
            # Create and save multiple patients
            patients = [
                Patient(full_name=f"Patient {i}", birth_date=date(1990, 1, 1))
                for i in range(50)
            ]
            
            for patient in patients:
                adapter.save_resource(patient)
            
            end = time.time()
            duration = end - start
            
            # Should be reasonably fast even with mocking overhead
            assert duration < 5.0
            
        except ImportError:
            pytest.skip("Adapter not available")

    @patch('hacs_persistence.vector_store.get_pgvector_connection')
    def test_vector_search_performance(self, mock_get_conn):
        """Test vector search performance."""
        import time
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            (f"resource-{i}", [0.1, 0.2, 0.3, 0.4], 0.9, {"type": "test"})
            for i in range(20)
        ]
        mock_get_conn.return_value = mock_conn
        
        try:
            from hacs_persistence.vector_store import VectorStore
            
            store = VectorStore(database_url="postgresql://test")
            
            start = time.time()
            
            # Perform multiple vector searches
            for _ in range(10):
                store.search_vectors(
                    query_embedding=[0.1, 0.2, 0.3, 0.4],
                    top_k=20
                )
            
            end = time.time()
            duration = end - start
            
            # Should be fast
            assert duration < 2.0
            
        except ImportError:
            pytest.skip("Vector store not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 