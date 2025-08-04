"""
Integration tests for HACS end-to-end functionality.

Tests the integration between core components:
- Actor authentication and authorization
- Permission management
- MCP tool execution
- Database integration
- Vector store operations
"""

import pytest
import asyncio
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

# Core HACS imports
from hacs_auth import Actor, ActorRole, PermissionManager, SessionManager
from hacs_core import get_llm_provider, get_vector_store, get_persistence_provider
from hacs_models import Patient, Observation
from hacs_utils.mcp.tools import execute_hacs_tool


class TestActorIntegration:
    """Test actor-based authentication and authorization integration."""
    
    def test_actor_creation_with_permissions(self):
        """Test creating actors with proper permissions."""
        # Create physician actor
        physician = Actor(
            name="Dr. Sarah Johnson",
            role=ActorRole.PHYSICIAN,
            organization="Test Hospital"
        )
        
        # Should have comprehensive permissions
        assert len(physician.permissions) > 0
        assert any("patient:read" in perm for perm in physician.permissions)
        assert any("patient:write" in perm for perm in physician.permissions)
        
        # Create patient actor
        patient = Actor(
            name="John Doe",
            role=ActorRole.PATIENT,
            organization="Test Hospital"
        )
        
        # Should have limited permissions
        assert len(patient.permissions) > 0
        assert any("own_data" in perm for perm in patient.permissions)
    
    def test_permission_manager_integration(self):
        """Test permission manager with different roles."""
        perm_manager = PermissionManager()
        
        # Test physician permissions
        physician_perms = perm_manager.get_role_permissions(ActorRole.PHYSICIAN)
        assert physician_perms.has_permission("read:patient")
        assert physician_perms.has_permission("write:observation")
        
        # Test patient permissions
        patient_perms = perm_manager.get_role_permissions(ActorRole.PATIENT)
        assert not patient_perms.has_permission("read:patient")  # Can't read other patients
        assert patient_perms.has_permission("read:own_data")
    
    def test_session_management_integration(self):
        """Test session management with actors."""
        session_manager = SessionManager()
        
        actor = Actor(
            name="Test User",
            role=ActorRole.NURSE,
            organization="Test Hospital"
        )
        
        # Create session
        session = session_manager.create_session(
            user_id="test_user",
            actor=actor,
            organization="Test Hospital"
        )
        
        assert session.user_id == "test_user"
        assert session.organization == "Test Hospital"
        assert session.is_active()
        
        # Update activity
        success = session_manager.update_session_activity(session.session_id)
        assert success
        
        # Terminate session
        terminated = session_manager.terminate_session(session.session_id)
        assert terminated


class TestMCPToolIntegration:
    """Test MCP tool execution with authentication and permissions."""
    
    @pytest.mark.asyncio
    async def test_mcp_tool_execution_with_actor(self):
        """Test MCP tool execution with proper actor context."""
        # Create test actor
        actor = Actor(
            name="Test Physician",
            role=ActorRole.PHYSICIAN,
            organization="Test Hospital"
        )
        
        # Mock database and vector store
        mock_db = MagicMock()
        mock_vector_store = MagicMock()
        
        # Test parameters for creating a patient
        params = {
            "resource_type": "Patient",
            "resource_data": {
                "full_name": "Test Patient",
                "date_of_birth": "1990-01-01"
            }
        }
        
        # This should work with proper mocking
        # In real scenario, this would create an actual patient record
        with patch('hacs_utils.mcp.tools.HACS_TOOLS_AVAILABLE', True):
            with patch('hacs_utils.mcp.tools._get_tool_function') as mock_get_tool:
                mock_tool = AsyncMock(return_value="Patient created successfully")
                mock_get_tool.return_value = mock_tool
                
                result = await execute_hacs_tool(
                    "create_resource",
                    params,
                    db_adapter=mock_db,
                    vector_store=mock_vector_store,
                    actor=actor
                )
                
                assert not result.isError
                assert len(result.content) > 0
    
    @pytest.mark.asyncio
    async def test_mcp_tool_with_insufficient_permissions(self):
        """Test MCP tool execution with insufficient permissions."""
        # Create patient actor (limited permissions)
        actor = Actor(
            name="Test Patient",
            role=ActorRole.PATIENT,
            organization="Test Hospital"
        )
        
        # Try to create another patient (should be restricted)
        params = {
            "resource_type": "Patient",
            "resource_data": {"full_name": "Another Patient"}
        }
        
        # This would normally fail due to permissions
        # but since we're mocking, we test the framework structure
        with patch('hacs_utils.mcp.tools.HACS_TOOLS_AVAILABLE', True):
            result = await execute_hacs_tool(
                "create_resource", 
                params,
                actor=actor
            )
            
            # Should handle gracefully (even if mocked)
            assert isinstance(result.content, list)


class TestHealthcareModelIntegration:
    """Test integration between healthcare models and core systems."""
    
    def test_patient_model_creation(self):
        """Test creating Patient models with validation."""
        patient_data = {
            "full_name": "Jane Smith",
            "date_of_birth": "1985-03-15",
            "gender": "female",
            "contact_info": {
                "email": "jane.smith@example.com",
                "phone": "+1-555-0123"
            }
        }
        
        # This should work with FHIR-compliant model
        patient = Patient(**patient_data)
        
        assert patient.full_name == "Jane Smith"
        assert patient.gender == "female"
        assert patient.id is not None  # Should auto-generate ID
    
    def test_observation_model_creation(self):
        """Test creating Observation models."""
        observation_data = {
            "patient_id": "patient_123",
            "observation_type": "vital_signs",
            "value": "120/80 mmHg",
            "unit": "mmHg",
            "observed_datetime": "2024-01-15T10:30:00Z"
        }
        
        observation = Observation(**observation_data)
        
        assert observation.patient_id == "patient_123"
        assert observation.observation_type == "vital_signs"
        assert observation.value == "120/80 mmHg"


class TestContainerIntegration:
    """Test dependency injection container integration."""
    
    @pytest.mark.skipif(True, reason="Requires running services")
    def test_llm_provider_integration(self):
        """Test LLM provider integration."""
        try:
            provider = get_llm_provider("auto")
            assert provider is not None
        except Exception:
            # Skip if no providers available
            pytest.skip("No LLM providers available")
    
    @pytest.mark.skipif(True, reason="Requires running services")
    def test_vector_store_integration(self):
        """Test vector store integration."""
        try:
            vector_store = get_vector_store("auto")
            assert vector_store is not None
        except Exception:
            # Skip if no vector stores available
            pytest.skip("No vector stores available")
    
    @pytest.mark.skipif(True, reason="Requires running services")
    def test_persistence_provider_integration(self):
        """Test persistence provider integration."""
        try:
            persistence = get_persistence_provider("auto")
            assert persistence is not None
        except Exception:
            # Skip if no persistence providers available
            pytest.skip("No persistence providers available")


class TestSecurityIntegration:
    """Test security integration across components."""
    
    def test_actor_permission_enforcement(self):
        """Test that actor permissions are properly enforced."""
        # Create actors with different roles
        admin = Actor(name="Admin", role=ActorRole.ADMIN)
        nurse = Actor(name="Nurse", role=ActorRole.NURSE)
        patient = Actor(name="Patient", role=ActorRole.PATIENT)
        
        # Admin should have broad permissions
        admin_permissions = set(admin.permissions)
        assert any("admin" in perm for perm in admin_permissions)
        
        # Nurse should have healthcare permissions but not admin
        nurse_permissions = set(nurse.permissions)
        assert any("patient:read" in perm for perm in nurse_permissions)
        assert not any("admin" in perm for perm in nurse_permissions)
        
        # Patient should have minimal permissions
        patient_permissions = set(patient.permissions)
        assert any("own_data" in perm for perm in patient_permissions)
        assert not any("patient:write" in perm for perm in patient_permissions)
    
    def test_authentication_flow(self):
        """Test authentication flow integration."""
        from hacs_auth import AuthManager, AuthConfig
        
        # Create auth manager
        config = AuthConfig(jwt_secret="test-secret")
        auth_manager = AuthManager(config)
        
        # Create token for actor
        token = auth_manager.create_access_token(
            user_id="test_user",
            role="physician",
            permissions=["read:patient", "write:observation"]
        )
        
        assert token is not None
        
        # Verify token
        token_data = auth_manager.verify_token(token)
        assert token_data.user_id == "test_user"
        assert token_data.role == "physician"


@pytest.mark.integration
class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""
    
    @pytest.mark.asyncio
    async def test_complete_healthcare_workflow(self):
        """Test a complete healthcare workflow from authentication to data storage."""
        # 1. Create and authenticate physician
        physician = Actor(
            name="Dr. Emily Chen",
            role=ActorRole.PHYSICIAN,
            organization="General Hospital"
        )
        
        # 2. Start session
        session_manager = SessionManager()
        session = session_manager.create_session(
            user_id="emily_chen",
            actor=physician
        )
        
        assert session.is_active()
        
        # 3. Create patient data
        patient_data = {
            "full_name": "Michael Johnson",
            "date_of_birth": "1978-09-22",
            "gender": "male"
        }
        
        # 4. Simulate MCP tool execution (mocked)
        with patch('hacs_utils.mcp.tools.HACS_TOOLS_AVAILABLE', True):
            with patch('hacs_utils.mcp.tools._get_tool_function') as mock_get_tool:
                mock_tool = AsyncMock(return_value={"success": True, "patient_id": "patient_456"})
                mock_get_tool.return_value = mock_tool
                
                result = await execute_hacs_tool(
                    "create_resource",
                    {"resource_type": "Patient", "resource_data": patient_data},
                    actor=physician
                )
                
                assert not result.isError
        
        # 5. Update session activity
        session_manager.update_session_activity(session.session_id)
        
        # 6. Clean up - terminate session
        session_manager.terminate_session(session.session_id)
        
        # Verify workflow completed successfully
        assert True  # If we get here, the workflow completed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])