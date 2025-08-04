#!/usr/bin/env python3
"""
Final validation script to ensure HACS is ready for open-source publication.
This script validates all critical components and dependencies.
"""

import sys
import importlib
from pathlib import Path

def test_imports():
    """Test all critical imports work correctly."""
    try:
        print("Testing core imports...")
        
        # Test authentication system
        from hacs_auth import Actor, ActorRole, PermissionLevel
        print("✅ Authentication system (hacs-auth)")
        
        # Test models system
        from hacs_models import Patient, Observation, Encounter
        print("✅ Healthcare models (hacs-models)")
        
        # Test core system
        from hacs_core import protocols, memory, compatibility
        print("✅ Core system (hacs-core)")
        
        # Test infrastructure
        from hacs_infrastructure import Container, get_container
        print("✅ Infrastructure system (hacs-infrastructure)")
        
        # Test tools system
        from hacs_tools.domains.resource_management import create_hacs_record
        from hacs_tools.domains.clinical_workflows import execute_clinical_workflow
        print("✅ Tools system (hacs-tools)")
        
        # Test persistence system
        from hacs_persistence import PostgreSQLAdapter
        print("✅ Persistence system (hacs-persistence)")
        
        # Test registry system
        from hacs_registry import HACSToolRegistry
        print("✅ Registry system (hacs-registry)")
        
        # Test utilities
        from hacs_utils.mcp.tools import execute_tool
        print("✅ Utilities system (hacs-utils)")
        
        print("✅ All critical imports working")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_package_metadata():
    """Test that all packages have correct metadata for PyPI."""
    packages = [
        "hacs-auth", "hacs-models", "hacs-core", "hacs-infrastructure",
        "hacs-tools", "hacs-persistence", "hacs-registry", "hacs-utils", "hacs-cli"
    ]
    
    print("Testing package metadata...")
    for pkg in packages:
        pyproject_path = Path(f"packages/{pkg}/pyproject.toml")
        if pyproject_path.exists():
            content = pyproject_path.read_text()
            if "solanovisitor@gmail.com" in content and "github.com/solanovisitor/hacs-ai" in content:
                print(f"✅ {pkg} metadata ready for PyPI")
            else:
                print(f"❌ {pkg} metadata needs update")
                return False
        else:
            print(f"❌ {pkg} pyproject.toml not found")
            return False
    
    return True

def test_example_agent():
    """Test that the example agent is properly configured."""
    example_path = Path("examples/hacs_developer_agent")
    required_files = [
        "pyproject.toml", "agent.py", "langgraph.json", 
        "configuration.py", "tools.py", "state.py"
    ]
    
    print("Testing example agent...")
    for file in required_files:
        if (example_path / file).exists():
            print(f"✅ Example agent file: {file}")
        else:
            print(f"❌ Example agent missing: {file}")
            return False
    
    return True

def test_clean_project():
    """Test that business-specific code has been removed."""
    print("Testing project cleanup...")
    
    # Check that VOA Health directory is gone
    if Path("voa_health").exists():
        print("❌ VOA Health directory still exists")
        return False
    else:
        print("✅ VOA Health directory removed")
    
    # Check that documentation cleanup occurred
    unwanted_docs = [
        "HACS_TOOLS_IMPLEMENTATION_REVIEW.md",
        "examples/hacs_deep_agent",
        "examples/langchain_integration"
    ]
    
    for item in unwanted_docs:
        if Path(item).exists():
            print(f"❌ Unwanted item still exists: {item}")
            return False
        else:
            print(f"✅ Removed: {item}")
    
    return True

def main():
    """Run all validation tests."""
    print("🔍 HACS Publication Readiness Validation")
    print("=" * 50)
    
    tests = [
        ("Core Imports", test_imports),
        ("Package Metadata", test_package_metadata), 
        ("Example Agent", test_example_agent),
        ("Project Cleanup", test_clean_project)
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        if not test_func():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🚀 HACS IS READY FOR OPEN-SOURCE PUBLICATION!")
        print("📦 All packages ready for PyPI")
        print("🔗 Repository ready for GitHub as 'hacs-ai'")
        return 0
    else:
        print("❌ HACS needs fixes before publication")
        return 1

if __name__ == "__main__":
    sys.exit(main())