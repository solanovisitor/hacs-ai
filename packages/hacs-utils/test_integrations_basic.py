#!/usr/bin/env python3
"""
Basic Integration Test Script for HACS Utils

This script tests that all integrations can be imported and basic functionality works
without requiring external API keys or services.
"""

import sys
import traceback
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))


def test_basic_imports():
    """Test basic package imports."""
    print("Testing basic imports...")

    try:
        import hacs_utils
        print("✓ hacs_utils imported successfully")
        print(f"  Version: {hacs_utils.__version__}")

        # Test utility functions
        available = hacs_utils.list_available_integrations()
        print(f"  Available integrations: {available}")

        # Test backward compatibility
        assert hasattr(hacs_utils, 'CrewAIAdapter')
        print("✓ Backward compatibility exports available")

        return True
    except Exception as e:
        print(f"✗ Basic imports failed: {e}")
        traceback.print_exc()
        return False


def test_crewai_integration():
    """Test CrewAI integration."""
    print("\nTesting CrewAI integration...")

    try:
        from hacs_utils import CrewAIAdapter, CrewAIAgentRole, CrewAITaskType

        # Test adapter creation
        adapter = CrewAIAdapter()
        print("✓ CrewAI adapter created")

        # Test enums
        assert hasattr(CrewAIAgentRole, 'CLINICAL_ASSESSOR')
        assert hasattr(CrewAITaskType, 'PATIENT_ASSESSMENT')
        print("✓ CrewAI enums available")

        return True
    except Exception as e:
        print(f"✗ CrewAI integration failed: {e}")
        traceback.print_exc()
        return False


def test_openai_integration():
    """Test OpenAI integration."""
    print("\nTesting OpenAI integration...")

    try:
        from hacs_utils.integrations import openai
        if openai is None:
            print("ℹ OpenAI integration not available (dependencies not installed)")
            return True

        # Test that classes exist
        from hacs_utils.integrations.openai import OpenAIEmbedding, OpenAIClient
        print("✓ OpenAI classes imported")

        # Test factory functions
        from hacs_utils.integrations.openai import create_openai_client, create_openai_embedding
        print("✓ OpenAI factory functions available")

        return True
    except ImportError:
        print("ℹ OpenAI integration not available (dependencies not installed)")
        return True
    except Exception as e:
        print(f"✗ OpenAI integration failed: {e}")
        traceback.print_exc()
        return False


def test_pinecone_integration():
    """Test Pinecone integration."""
    print("\nTesting Pinecone integration...")

    try:
        from hacs_utils.integrations import pinecone
        if pinecone is None:
            print("ℹ Pinecone integration not available (dependencies not installed)")
            return True

        # Test that classes exist
        from hacs_utils.integrations.pinecone import PineconeVectorStore
        print("✓ Pinecone classes imported")

        # Test factory functions
        from hacs_utils.integrations.pinecone import create_pinecone_store
        print("✓ Pinecone factory functions available")

        return True
    except ImportError:
        print("ℹ Pinecone integration not available (dependencies not installed)")
        return True
    except Exception as e:
        print(f"✗ Pinecone integration failed: {e}")
        traceback.print_exc()
        return False


def test_qdrant_integration():
    """Test Qdrant integration."""
    print("\nTesting Qdrant integration...")

    try:
        from hacs_utils.integrations import qdrant
        if qdrant is None:
            print("ℹ Qdrant integration not available (dependencies not installed)")
            return True

        # Test that classes exist
        from hacs_utils.integrations.qdrant import QdrantVectorStore
        print("✓ Qdrant classes imported")

        # Test factory functions
        from hacs_utils.integrations.qdrant import create_qdrant_store
        print("✓ Qdrant factory functions available")

        return True
    except ImportError:
        print("ℹ Qdrant integration not available (dependencies not installed)")
        return True
    except Exception as e:
        print(f"✗ Qdrant integration failed: {e}")
        traceback.print_exc()
        return False


def test_integration_info():
    """Test integration information functions."""
    print("\nTesting integration information...")

    try:
        import hacs_utils

        info = hacs_utils.get_integration_info()
        assert isinstance(info, dict)
        assert 'openai' in info
        assert 'pinecone' in info
        assert 'qdrant' in info
        assert 'crewai' in info

        print("✓ Integration info function works")

        # Print integration status
        for name, details in info.items():
            status = "✓" if details['available'] else "○"
            print(f"  {status} {name}: {details['description']}")

        return True
    except Exception as e:
        print(f"✗ Integration info failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("HACS Utils Integration Test Suite")
    print("=" * 40)

    tests = [
        test_basic_imports,
        test_crewai_integration,
        test_openai_integration,
        test_pinecone_integration,
        test_qdrant_integration,
        test_integration_info,
    ]

    results = []
    for test in tests:
        results.append(test())

    print("\n" + "=" * 40)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())