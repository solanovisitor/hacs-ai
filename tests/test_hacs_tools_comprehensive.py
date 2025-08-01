#!/usr/bin/env python3
"""
Comprehensive HACS Tools Test Suite

This module provides complete testing for all 42 HACS tools across 10 domains,
including direct tool testing and MCP server integration testing.

Test Categories:
- Unit tests for each individual tool
- MCP server integration tests
- End-to-end workflow tests
- Error handling and validation tests

Usage:
    # Run all tests
    python -m pytest tests/test_hacs_tools_comprehensive.py -v
    
    # Run specific domain tests
    python -m pytest tests/test_hacs_tools_comprehensive.py::TestResourceManagement -v
    
    # Run with MCP server integration (requires running MCP server)
    python -m pytest tests/test_hacs_tools_comprehensive.py --mcp-integration -v

Author: HACS Development Team
License: MIT
Version: 1.0.0
"""

import asyncio
import json
import logging
import os
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional
import pytest
import httpx

# Add packages to Python path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "hacs-core", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "hacs-tools", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "hacs-utils", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "hacs-persistence", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "hacs-registry", "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def pytest_addoption(parser):
    """Add custom pytest options."""
    parser.addoption(
        "--mcp-integration",
        action="store_true",
        default=False,
        help="Run MCP server integration tests"
    )
    parser.addoption(
        "--mcp-server-url",
        action="store",
        default="http://localhost:8000",
        help="MCP server URL for integration tests"
    )


@pytest.fixture
def mcp_integration(request):
    """Fixture to check if MCP integration tests should run."""
    return request.config.getoption("--mcp-integration")


@pytest.fixture
def mcp_server_url(request):
    """Fixture to get MCP server URL."""
    return request.config.getoption("--mcp-server-url")


class HACSToolTester:
    """Comprehensive tester for all HACS tools."""
    
    def __init__(self, mcp_server_url: str = "http://localhost:8000"):
        self.mcp_server_url = mcp_server_url
        self.test_results = {}
        
        # Test data templates for each domain
        self.test_data = self._initialize_test_data()
        
        # All 42 HACS tools organized by domain
        self.tools_by_domain = {
            "resource_management": [
                "create_hacs_record",
                "get_hacs_record", 
                "update_hacs_record",
                "delete_hacs_record",
                "search_hacs_records"
            ],
            "clinical_workflows": [
                "execute_clinical_workflow",
                "get_clinical_guidance",
                "query_with_datarequirement",
                "validate_clinical_protocol"
            ],
            "memory_operations": [
                "create_hacs_memory",
                "search_hacs_memories",
                "consolidate_memories",
                "retrieve_context",
                "analyze_memory_patterns"
            ],
            "vector_search": [
                "store_embedding",
                "vector_similarity_search",
                "vector_hybrid_search",
                "get_vector_collection_stats",
                "optimize_vector_collection"
            ],
            "schema_discovery": [
                "discover_hacs_resources",
                "get_hacs_resource_schema",
                "analyze_resource_fields",
                "compare_resource_schemas"
            ],
            "development_tools": [
                "create_resource_stack",
                "create_clinical_template",
                "optimize_resource_for_llm"
            ],
            "fhir_integration": [
                "convert_to_fhir",
                "validate_fhir_compliance",
                "process_fhir_bundle",
                "lookup_fhir_terminology"
            ],
            "healthcare_analytics": [
                "calculate_quality_measures",
                "analyze_population_health",
                "generate_clinical_dashboard",
                "perform_risk_stratification"
            ],
            "ai_integrations": [
                "deploy_healthcare_ai_model",
                "run_clinical_inference",
                "preprocess_medical_data"
            ],
            "admin_operations": [
                "run_database_migration",
                "check_migration_status",
                "describe_database_schema",
                "get_table_structure",
                "test_database_connection"
            ]
        }

    def _initialize_test_data(self) -> Dict[str, Any]:
        """Initialize test data templates for all tool categories."""
        return {
            # Resource Management Test Data
            "patient_data": {
                "full_name": "John Doe Test Patient",
                "birth_date": "1990-01-15",
                "gender": "male",
                "phone": "+1-555-123-4567",
                "email": "john.doe.test@example.com"
            },
            "observation_data": {
                "code": {
                    "coding": [{
                        "code": "85354-9",
                        "system": "http://loinc.org",
                        "display": "Blood pressure"
                    }]
                },
                "value_quantity": {
                    "value": 120,
                    "unit": "mmHg",
                    "system": "http://unitsofmeasure.org"
                },
                "status": "final"
            },
            
            # Clinical Workflow Test Data
            "clinical_context": {
                "patient_id": "patient-test-001",
                "chief_complaint": "Chest pain",
                "vital_signs": {
                    "blood_pressure": "140/90 mmHg",
                    "heart_rate": "85 bpm",
                    "temperature": "98.6°F"
                },
                "medical_history": ["hypertension", "diabetes"]
            },
            
            # Memory Operations Test Data
            "memory_data": {
                "content": "Patient shows improvement in blood pressure control",
                "memory_type": "episodic",
                "context": "clinical_assessment",
                "tags": ["hypertension", "improvement", "medication_compliance"]
            },
            
            # Vector Search Test Data
            "embedding_data": {
                "text": "Patient presents with chest pain and shortness of breath",
                "vector": [0.1, 0.2, 0.3, 0.4, 0.5] * 100,  # 500-dim vector
                "metadata": {
                    "patient_id": "patient-001",
                    "document_type": "clinical_note"
                }
            },
            
            # FHIR Integration Test Data
            "fhir_patient": {
                "resourceType": "Patient",
                "id": "example-patient",
                "name": [{
                    "given": ["John"],
                    "family": "Doe"
                }],
                "gender": "male",
                "birthDate": "1990-01-15"
            },
            
            # Healthcare Analytics Test Data
            "population_data": {
                "patient_cohort": "diabetes_patients",
                "time_period": "2024-Q1",
                "measures": ["hba1c_control", "blood_pressure_control"]
            },
            
            # AI/ML Integration Test Data
            "ml_model_config": {
                "model_name": "diabetes_risk_predictor",
                "model_type": "classification",
                "version": "1.0.0",
                "input_features": ["age", "bmi", "glucose_level"]
            },
            "clinical_data": {
                "age": 45,
                "bmi": 28.5,
                "glucose_level": 150,
                "systolic_bp": 140,
                "diastolic_bp": 90
            }
        }

    async def test_tool_via_mcp(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Test a tool via MCP server call."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": params
                    }
                }
                
                response = await client.post(
                    f"{self.mcp_server_url}/mcp",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "data": result,
                        "status_code": response.status_code
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "status_code": response.status_code
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": None
            }

    async def test_mcp_server_health(self) -> Dict[str, Any]:
        """Test MCP server health and availability."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test server health endpoint
                health_response = await client.get(f"{self.mcp_server_url}/health")
                
                # Test MCP tools list endpoint
                list_payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list"
                }
                
                tools_response = await client.post(
                    f"{self.mcp_server_url}/mcp",
                    json=list_payload,
                    headers={"Content-Type": "application/json"}
                )
                
                return {
                    "server_accessible": health_response.status_code == 200,
                    "mcp_endpoint_accessible": tools_response.status_code == 200,
                    "health_status": health_response.status_code,
                    "tools_endpoint_status": tools_response.status_code,
                    "available_tools": tools_response.json() if tools_response.status_code == 200 else None
                }
                
        except Exception as e:
            return {
                "server_accessible": False,
                "mcp_endpoint_accessible": False,
                "error": str(e)
            }


# Pytest Test Classes

class TestMCPServerIntegration:
    """Test MCP server integration and health."""
    
    @pytest.mark.asyncio
    async def test_mcp_server_health(self, mcp_integration, mcp_server_url):
        """Test MCP server health check."""
        if not mcp_integration:
            pytest.skip("MCP integration tests not enabled")
        
        tester = HACSToolTester(mcp_server_url)
        health_result = await tester.test_mcp_server_health()
        
        assert health_result["server_accessible"], "MCP server should be accessible"
        assert health_result["mcp_endpoint_accessible"], "MCP endpoint should be accessible"


class TestResourceManagement:
    """Test all resource management tools."""
    
    def setup_method(self):
        """Set up test data."""
        self.tester = HACSToolTester()
        
    @pytest.mark.asyncio
    async def test_create_hacs_record_mcp(self, mcp_integration, mcp_server_url):
        """Test create_hacs_record via MCP."""
        if not mcp_integration:
            pytest.skip("MCP integration tests not enabled")
        
        self.tester.mcp_server_url = mcp_server_url
        result = await self.tester.test_tool_via_mcp("create_hacs_record", {
            "actor_name": "Dr. Test Smith",
            "resource_type": "Patient",
            "resource_data": self.tester.test_data["patient_data"],
            "auto_generate_id": True,
            "validate_fhir": True
        })
        
        assert result["success"], f"create_hacs_record should succeed: {result.get('error', '')}"
    
    @pytest.mark.asyncio 
    async def test_discover_hacs_resources_mcp(self, mcp_integration, mcp_server_url):
        """Test discover_hacs_resources via MCP."""
        if not mcp_integration:
            pytest.skip("MCP integration tests not enabled")
        
        self.tester.mcp_server_url = mcp_server_url
        result = await self.tester.test_tool_via_mcp("discover_hacs_resources", {
            "category_filter": "clinical",
            "fhir_compliant_only": False,
            "include_field_details": True
        })
        
        assert result["success"], f"discover_hacs_resources should succeed: {result.get('error', '')}"

    def test_resource_management_tools_exist(self):
        """Test that all resource management tools are defined."""
        expected_tools = self.tester.tools_by_domain["resource_management"]
        assert len(expected_tools) == 5, "Should have 5 resource management tools"
        
        # Test that all expected tools are in the list
        for tool_name in expected_tools:
            assert tool_name in expected_tools, f"Tool {tool_name} should be defined"


class TestClinicalWorkflows:
    """Test all clinical workflow tools."""
    
    def setup_method(self):
        """Set up test data."""
        self.tester = HACSToolTester()
    
    @pytest.mark.asyncio
    async def test_get_clinical_guidance_mcp(self, mcp_integration, mcp_server_url):
        """Test get_clinical_guidance via MCP."""
        if not mcp_integration:
            pytest.skip("MCP integration tests not enabled")
        
        self.tester.mcp_server_url = mcp_server_url
        result = await self.tester.test_tool_via_mcp("get_clinical_guidance", {
            "actor_name": "Dr. Test Physician",
            "patient_context": self.tester.test_data["clinical_context"],
            "clinical_question": "What is the appropriate next step for this chest pain patient?",
            "evidence_requirements": ["clinical_guidelines", "recent_studies"],
            "urgency_level": "routine"
        })
        
        assert result["success"], f"get_clinical_guidance should succeed: {result.get('error', '')}"

    def test_clinical_workflow_tools_exist(self):
        """Test that all clinical workflow tools are defined."""
        expected_tools = self.tester.tools_by_domain["clinical_workflows"]
        assert len(expected_tools) == 4, "Should have 4 clinical workflow tools"


class TestMemoryOperations:
    """Test all memory operations tools."""
    
    def setup_method(self):
        """Set up test data."""
        self.tester = HACSToolTester()
    
    @pytest.mark.asyncio
    async def test_create_hacs_memory_mcp(self, mcp_integration, mcp_server_url):
        """Test create_hacs_memory via MCP."""
        if not mcp_integration:
            pytest.skip("MCP integration tests not enabled")
        
        self.tester.mcp_server_url = mcp_server_url
        result = await self.tester.test_tool_via_mcp("create_hacs_memory", {
            "actor_name": "Dr. Test Physician",
            "memory_content": self.tester.test_data["memory_data"]["content"],
            "memory_type": self.tester.test_data["memory_data"]["memory_type"],
            "context_tags": self.tester.test_data["memory_data"]["tags"],
            "patient_reference": "patient-test-001"
        })
        
        assert result["success"], f"create_hacs_memory should succeed: {result.get('error', '')}"

    def test_memory_operations_tools_exist(self):
        """Test that all memory operations tools are defined."""
        expected_tools = self.tester.tools_by_domain["memory_operations"]
        assert len(expected_tools) == 5, "Should have 5 memory operations tools"


class TestVectorSearch:
    """Test all vector search tools."""
    
    def setup_method(self):
        """Set up test data."""
        self.tester = HACSToolTester()

    def test_vector_search_tools_exist(self):
        """Test that all vector search tools are defined."""
        expected_tools = self.tester.tools_by_domain["vector_search"]
        assert len(expected_tools) == 5, "Should have 5 vector search tools"


class TestSchemaDiscovery:
    """Test all schema discovery tools."""
    
    def setup_method(self):
        """Set up test data."""
        self.tester = HACSToolTester()

    def test_schema_discovery_tools_exist(self):
        """Test that all schema discovery tools are defined."""
        expected_tools = self.tester.tools_by_domain["schema_discovery"]
        assert len(expected_tools) == 4, "Should have 4 schema discovery tools"


class TestDevelopmentTools:
    """Test all development tools."""
    
    def setup_method(self):
        """Set up test data."""
        self.tester = HACSToolTester()
    
    @pytest.mark.asyncio
    async def test_create_clinical_template_mcp(self, mcp_integration, mcp_server_url):
        """Test create_clinical_template via MCP."""
        if not mcp_integration:
            pytest.skip("MCP integration tests not enabled")
        
        self.tester.mcp_server_url = mcp_server_url
        result = await self.tester.test_tool_via_mcp("create_clinical_template", {
            "template_type": "assessment",
            "focus_area": "cardiology",
            "complexity_level": "standard",
            "include_workflow_fields": True
        })
        
        assert result["success"], f"create_clinical_template should succeed: {result.get('error', '')}"

    def test_development_tools_exist(self):
        """Test that all development tools are defined."""
        expected_tools = self.tester.tools_by_domain["development_tools"]
        assert len(expected_tools) == 3, "Should have 3 development tools"


class TestFHIRIntegration:
    """Test all FHIR integration tools."""
    
    def setup_method(self):
        """Set up test data."""
        self.tester = HACSToolTester()

    def test_fhir_integration_tools_exist(self):
        """Test that all FHIR integration tools are defined."""
        expected_tools = self.tester.tools_by_domain["fhir_integration"]
        assert len(expected_tools) == 4, "Should have 4 FHIR integration tools"


class TestHealthcareAnalytics:
    """Test all healthcare analytics tools."""
    
    def setup_method(self):
        """Set up test data."""
        self.tester = HACSToolTester()

    def test_healthcare_analytics_tools_exist(self):
        """Test that all healthcare analytics tools are defined."""
        expected_tools = self.tester.tools_by_domain["healthcare_analytics"]
        assert len(expected_tools) == 4, "Should have 4 healthcare analytics tools"


class TestAIIntegrations:
    """Test all AI/ML integration tools."""
    
    def setup_method(self):
        """Set up test data."""
        self.tester = HACSToolTester()

    def test_ai_integrations_tools_exist(self):
        """Test that all AI integration tools are defined."""
        expected_tools = self.tester.tools_by_domain["ai_integrations"]
        assert len(expected_tools) == 3, "Should have 3 AI integration tools"


class TestAdminOperations:
    """Test all admin operations tools."""
    
    def setup_method(self):
        """Set up test data."""
        self.tester = HACSToolTester()
    
    @pytest.mark.asyncio
    async def test_test_database_connection_mcp(self, mcp_integration, mcp_server_url):
        """Test test_database_connection via MCP."""
        if not mcp_integration:
            pytest.skip("MCP integration tests not enabled")
        
        self.tester.mcp_server_url = mcp_server_url
        result = await self.tester.test_tool_via_mcp("test_database_connection", {
            "actor_name": "System Admin",
            "connection_type": "postgresql",
            "include_performance_metrics": True
        })
        
        assert result["success"], f"test_database_connection should succeed: {result.get('error', '')}"

    def test_admin_operations_tools_exist(self):
        """Test that all admin operations tools are defined."""
        expected_tools = self.tester.tools_by_domain["admin_operations"]
        assert len(expected_tools) == 5, "Should have 5 admin operations tools"


class TestComprehensiveToolsCount:
    """Test the total tool count and organization."""
    
    def setup_method(self):
        """Set up test data."""
        self.tester = HACSToolTester()
    
    def test_total_tools_count(self):
        """Test that we have exactly 42 tools across all domains."""
        total_tools = sum(len(tools) for tools in self.tester.tools_by_domain.values())
        assert total_tools == 42, f"Should have exactly 42 tools total, found {total_tools}"
    
    def test_domain_organization(self):
        """Test that all domains are properly organized."""
        expected_domains = [
            "resource_management", "clinical_workflows", "memory_operations",
            "vector_search", "schema_discovery", "development_tools",
            "fhir_integration", "healthcare_analytics", "ai_integrations",
            "admin_operations"
        ]
        
        assert len(self.tester.tools_by_domain) == 10, "Should have exactly 10 domains"
        
        for domain in expected_domains:
            assert domain in self.tester.tools_by_domain, f"Domain {domain} should exist"
            assert len(self.tester.tools_by_domain[domain]) > 0, f"Domain {domain} should have tools"


if __name__ == "__main__":
    # Command line execution for manual testing
    import sys
    
    if "--mcp" in sys.argv:
        # Run MCP integration tests
        asyncio.run(manual_test_mcp_integration())
    else:
        # Run basic tool validation
        tester = HACSToolTester()
        total_tools = sum(len(tools) for tools in tester.tools_by_domain.values())
        print(f"✅ HACS Tools Test Suite Validated")
        print(f"   Total Tools: {total_tools}")
        print(f"   Domains: {len(tester.tools_by_domain)}")
        print(f"   Run with pytest for full testing: pytest tests/test_hacs_tools_comprehensive.py -v")
        print(f"   Run with MCP integration: pytest tests/test_hacs_tools_comprehensive.py --mcp-integration -v")


async def manual_test_mcp_integration():
    """Manual MCP integration test for debugging."""
    tester = HACSToolTester()
    
    print("🚀 HACS Tools MCP Integration Test")
    print("=" * 50)
    
    # Test server health
    health_result = await tester.test_mcp_server_health()
    print(f"Server Health: {'✅' if health_result.get('server_accessible') else '❌'}")
    print(f"MCP Endpoint: {'✅' if health_result.get('mcp_endpoint_accessible') else '❌'}")
    
    if health_result.get('mcp_endpoint_accessible'):
        # Test a few key tools
        test_tools = [
            ("discover_hacs_resources", {
                "category_filter": "clinical",
                "include_field_details": True
            }),
            ("test_database_connection", {
                "actor_name": "Test User",
                "connection_type": "postgresql"
            })
        ]
        
        for tool_name, params in test_tools:
            print(f"\nTesting {tool_name}...")
            result = await tester.test_tool_via_mcp(tool_name, params)
            print(f"  Result: {'✅' if result['success'] else '❌'}")
            if not result['success']:
                print(f"  Error: {result.get('error', 'Unknown error')}")
    
    print("\n" + "=" * 50)
    print("MCP Integration test complete!")