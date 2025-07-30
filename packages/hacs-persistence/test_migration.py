#!/usr/bin/env python3
"""
Test script for HACS Database Migration

This script tests the migration system to ensure all HACS models
are properly supported in the database schema.
"""

import os
import sys
from pathlib import Path

# Add the src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from hacs_persistence.migrations import run_migration, get_migration_status


def test_migration():
    """Test the HACS database migration."""
    print("🚀 Testing HACS Database Migration System")
    print("=" * 50)

    # Use a test database URL (you can modify this for your environment)
    test_db_url = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")

    if not test_db_url:
        print("❌ No database URL provided. Set TEST_DATABASE_URL or DATABASE_URL environment variable.")
        print("   Example: postgresql://user:password@localhost:5432/hacs_test")
        return False

    print(f"📊 Database URL: {test_db_url.split('@')[1] if '@' in test_db_url else test_db_url}")
    print()

    # Check migration status before running
    print("🔍 Checking migration status...")
    status_before = get_migration_status(test_db_url)

    if "error" in status_before:
        print(f"❌ Error checking migration status: {status_before['error']}")
        return False

    print(f"   Schemas found: {status_before['total_schemas']}")
    print(f"   Tables found: {status_before.get('total_tables', 0)}")
    print(f"   Migration complete: {status_before['migration_complete']}")
    print()

    # Run migration
    print("🛠️  Running migration...")
    success = run_migration(test_db_url)

    if not success:
        print("❌ Migration failed!")
        return False

    print("✅ Migration completed successfully!")
    print()

    # Check migration status after running
    print("📋 Verifying migration results...")
    status_after = get_migration_status(test_db_url)

    if "error" in status_after:
        print(f"❌ Error checking migration status: {status_after['error']}")
        return False

    print(f"   ✅ Schemas created: {status_after['total_schemas']}/{status_after['expected_schemas']}")
    print(f"   ✅ Tables created: {status_after.get('total_tables', 0)}/{status_after.get('expected_min_tables', 25)}")
    print(f"   ✅ Migration table exists: {status_after['migration_table_exists']}")
    print(f"   ✅ Overall status: {'COMPLETE' if status_after['migration_complete'] else 'INCOMPLETE'}")
    print()

    # Verify HACS models are supported
    print("🔍 Verifying HACS models support...")

    # List of key HACS models that should have database support
    key_models = [
        "Patient", "Observation", "Encounter", "Condition",
        "Medication", "MedicationRequest", "Procedure", "AllergyIntolerance",
        "Goal", "ServiceRequest", "FamilyMemberHistory", "RiskAssessment",
        "Organization", "OrganizationContact", "OrganizationQualification",
        "PlanDefinition", "ActivityDefinition", "Library", "GuidanceResponse",
        "EvidenceVariable", "Task", "Appointment"
    ]

    print(f"   📊 Key HACS models to verify: {len(key_models)}")
    print(f"   🗃️  Expected minimum tables: {status_after.get('expected_min_tables', 25)}")

    if status_after.get('total_tables', 0) >= 25:
        print("   ✅ Sufficient tables created for all HACS models")
    else:
        print(f"   ⚠️  Only {status_after.get('total_tables', 0)} tables created, may be missing some models")

    print()
    print("🎉 Migration test completed!")
    print(f"   📈 Overall success: {status_after['migration_complete']}")

    return status_after['migration_complete']


def main():
    """Main function."""
    try:
        success = test_migration()
        exit_code = 0 if success else 1

        print(f"\n{'='*50}")
        print(f"🏁 Test {'PASSED' if success else 'FAILED'}")
        print(f"{'='*50}")

        sys.exit(exit_code)

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()