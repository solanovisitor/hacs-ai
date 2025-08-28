#!/usr/bin/env python3
"""
Comprehensive Supabase Connection Validation Script

This script validates HACS persistence with Supabase using psycopg3 async best practices.
It follows the patterns established in the HACS documentation and ensures robust
DATABASE_URL environment variable loading across all packages.

Usage:
    uv run scripts/validate_supabase_connection.py
"""

import os
import asyncio
import logging
from urllib.parse import urlparse
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Environment setup - use dotenv as user prefers
try:
    from dotenv import dotenv_values, load_dotenv
    
    # Load .env files in order of preference
    for env_file in ['.env', '.env.local']:
        if os.path.exists(env_file):
            load_dotenv(env_file, override=False)
            vals = dotenv_values(env_file)
            # Update environment with non-None values
            os.environ.update({k: v for k, v in vals.items() if v is not None})
            logger.info(f"Loaded environment from {env_file}")
            break
except ImportError:
    logger.warning("dotenv not available, using direct environment variables")


class SupabaseConnectionValidator:
    """Validates HACS connection to Supabase using psycopg3 async best practices."""
    
    def __init__(self):
        self.database_url = self._get_database_url()
        self._validate_url()
        
    def _get_database_url(self) -> str:
        """Get DATABASE_URL with proper precedence following HACS patterns."""
        # Check multiple environment variables as per HACS settings
        url = (
            os.getenv("DATABASE_URL") or 
            os.getenv("HACS_DATABASE_URL") or 
            os.getenv("POSTGRES_URL") or
            os.getenv("HACS_POSTGRES_URL")
        )
        
        if not url:
            raise ValueError(
                "DATABASE_URL not found. Please set one of: "
                "DATABASE_URL, HACS_DATABASE_URL, POSTGRES_URL, or HACS_POSTGRES_URL"
            )
        
        # Ensure HACS_DATABASE_URL is set for hacs-persistence
        os.environ["HACS_DATABASE_URL"] = url
        
        return url
    
    def _validate_url(self) -> None:
        """Validate DATABASE_URL format and Supabase requirements."""
        try:
            parsed = urlparse(self.database_url)
            
            # Basic validation
            if not parsed.scheme.startswith('postgresql'):
                raise ValueError(f"Invalid scheme: {parsed.scheme}. Expected postgresql://")
            
            if not parsed.hostname:
                raise ValueError("Missing hostname in DATABASE_URL")
            
            if not parsed.username:
                raise ValueError("Missing username in DATABASE_URL")
                
            if not parsed.password:
                raise ValueError("Missing password in DATABASE_URL")
            
            # Supabase-specific validation
            is_supabase = 'supabase.co' in parsed.hostname
            if is_supabase:
                if 'sslmode=require' not in self.database_url:
                    logger.warning("Supabase connection should include sslmode=require")
                
                logger.info("✓ Supabase URL detected and validated")
            else:
                logger.info(f"✓ PostgreSQL URL validated (host: {parsed.hostname})")
                
        except Exception as e:
            raise ValueError(f"Invalid DATABASE_URL format: {e}")
    
    def get_masked_url(self) -> str:
        """Return DATABASE_URL with password masked for safe logging."""
        parsed = urlparse(self.database_url)
        if parsed.password:
            masked_password = parsed.password[:4] + "****"
            return self.database_url.replace(parsed.password, masked_password)
        return self.database_url

    async def test_direct_psycopg3_connection(self) -> Dict[str, Any]:
        """Test direct psycopg3 async connection using recommended patterns."""
        logger.info("Testing direct psycopg3 async connection...")
        
        try:
            import psycopg
            
            # Use async connection as per psycopg3 best practices
            async with await psycopg.AsyncConnection.connect(
                self.database_url,
                autocommit=True
            ) as conn:
                async with conn.cursor() as cur:
                    # Test basic connection
                    await cur.execute("SELECT version(), current_database(), inet_server_addr()")
                    version, db_name, addr = await cur.fetchone()
                    
                    # Test HACS schema presence
                    await cur.execute("""
                        SELECT table_schema, count(*) as table_count
                        FROM information_schema.tables 
                        WHERE table_schema IN ('hacs_core', 'hacs_clinical', 'hacs_registry')
                        GROUP BY table_schema
                        ORDER BY table_schema
                    """)
                    schemas = await cur.fetchall()
                    
                    return {
                        "success": True,
                        "postgres_version": version,
                        "database": db_name,
                        "server_address": addr,
                        "hacs_schemas": dict(schemas) if schemas else {},
                        "connection_method": "psycopg3_async"
                    }
                    
        except ImportError:
            raise RuntimeError("psycopg3 not available. Install with: uv pip install psycopg[binary]")
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "connection_method": "psycopg3_async"
            }

    async def test_hacs_adapter_connection(self) -> Dict[str, Any]:
        """Test HACS adapter connection using create_postgres_adapter."""
        logger.info("Testing HACS adapter connection...")
        
        try:
            from hacs_persistence.adapter import create_postgres_adapter
            from hacs_models import Patient, Actor
            
            # Create adapter using HACS factory pattern
            adapter = await create_postgres_adapter()
            
            # Test save/read cycle with proper Actor
            author = Actor(
                name="connection-validator", 
                role="system", 
                permissions=["*:write", "*:read"]
            )
            
            test_patient = Patient(
                full_name="Connection Test Patient",
                birth_date="1990-01-01",
                gender="other"  # Valid HACS gender value
            )
            
            # Save patient
            saved_patient = await adapter.save(test_patient, author)
            
            # Read back to verify persistence
            read_patient = await adapter.read(Patient, saved_patient.id, author)
            
            return {
                "success": True,
                "patient_id": saved_patient.id,
                "patient_name": read_patient.full_name,
                "adapter_type": type(adapter).__name__,
                "operation": "save_and_read"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "adapter_type": "create_postgres_adapter"
            }

    async def test_hacs_tools_integration(self) -> Dict[str, Any]:
        """Test HACS tools with injected config/state using current_actor pattern."""
        logger.info("Testing HACS tools integration...")
        
        try:
            from hacs_tools.domains.modeling import pin_resource
            from hacs_tools.domains.database import save_resource
            from hacs_core.config import configure_hacs
            from hacs_models import Actor
            
            # Configure actor context for tools (new pattern)
            tools_actor = Actor(
                name="tools-validator",
                role="physician", 
                permissions=["*:write", "*:read"]
            )
            configure_hacs(current_actor=tools_actor)
            
            # Test pin_resource (modeling domain)
            pin_result = pin_resource("Patient", {
                "full_name": "Tools Integration Patient",
                "birth_date": "1985-07-15",
                "gender": "male"
            })
            
            if not pin_result.success:
                return {
                    "success": False,
                    "error": f"pin_resource failed: {pin_result.message}",
                    "operation": "pin_resource"
                }
            
            # Test save_resource with typed tables (database domain)
            save_result = await save_resource(
                resource=pin_result.data["resource"],
                as_typed=True
            )
            
            if not save_result.success:
                return {
                    "success": False,
                    "error": f"save_resource failed: {save_result.message}",
                    "operation": "save_resource"
                }
            
            return {
                "success": True,
                "resource_id": save_result.data.get("resource_id"),
                "pin_success": pin_result.success,
                "save_success": save_result.success,
                "actor_name": tools_actor.name,
                "operation": "pin_and_save"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "operation": "hacs_tools_integration"
            }

    async def verify_data_persistence(self) -> Dict[str, Any]:
        """Verify that data was actually persisted to the database."""
        logger.info("Verifying data persistence...")
        
        try:
            import psycopg
            
            async with await psycopg.AsyncConnection.connect(self.database_url) as conn:
                async with conn.cursor() as cur:
                    # Count patients in typed table
                    await cur.execute("SELECT count(*) FROM hacs_core.patients")
                    typed_count = (await cur.fetchone())[0]
                    
                    # Count patients in generic table (if exists)
                    # Check if generic table exists first, then query
                    await cur.execute("SELECT to_regclass('public.hacs_resources') IS NOT NULL")
                    has_generic_table = (await cur.fetchone())[0]
                    
                    if has_generic_table:
                        await cur.execute("""
                            SELECT count(*) 
                            FROM public.hacs_resources 
                            WHERE resource_type = 'Patient'
                        """)
                        generic_count = (await cur.fetchone())[0]
                    else:
                        generic_count = 0
                    
                    # Get recent patients for verification
                    await cur.execute("""
                        SELECT id, full_name, created_at
                        FROM hacs_core.patients 
                        ORDER BY created_at DESC 
                        LIMIT 5
                    """)
                    recent_patients = await cur.fetchall()
                    
                    return {
                        "success": True,
                        "typed_table_count": typed_count,
                        "generic_table_count": generic_count,
                        "recent_patients": [
                            {"id": pid[:12] + "...", "name": name, "created": str(created)[:19]}
                            for pid, name, created in recent_patients
                        ],
                        "total_test_records": typed_count + generic_count
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "operation": "persistence_verification"
            }

    async def run_comprehensive_validation(self) -> None:
        """Run all validation tests and provide a comprehensive report."""
        print("=" * 60)
        print("🏥 HACS Supabase Connection Validation")
        print("=" * 60)
        print()
        
        # Display connection info
        print("📋 Connection Details:")
        print(f"   Database URL: {self.get_masked_url()}")
        parsed = urlparse(self.database_url)
        print(f"   Host: {parsed.hostname}")
        print(f"   Database: {(parsed.path or '/').lstrip('/')}")
        print(f"   SSL Mode: {'✓' if 'sslmode=require' in self.database_url else '✗'}")
        print()
        
        tests = [
            ("Direct psycopg3 Connection", self.test_direct_psycopg3_connection),
            ("HACS Adapter Connection", self.test_hacs_adapter_connection),
            ("HACS Tools Integration", self.test_hacs_tools_integration),
            ("Data Persistence Verification", self.verify_data_persistence),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"🧪 {test_name}...")
            try:
                result = await test_func()
                results.append((test_name, result))
                
                if result["success"]:
                    print(f"   ✅ {test_name} passed")
                    # Show relevant details
                    if "postgres_version" in result:
                        print(f"      PostgreSQL: {result['postgres_version'].split()[0]}")
                    if "hacs_schemas" in result:
                        schemas = result["hacs_schemas"]
                        if schemas:
                            print(f"      HACS schemas: {', '.join(f'{k}({v})' for k, v in schemas.items())}")
                    if "patient_id" in result:
                        print(f"      Created patient: {result['patient_id']}")
                    if "resource_id" in result:
                        print(f"      Saved resource: {result['resource_id']}")
                    if "total_test_records" in result:
                        print(f"      Total records: {result['total_test_records']}")
                else:
                    print(f"   ❌ {test_name} failed")
                    print(f"      Error: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"   ❌ {test_name} failed with exception")
                print(f"      Error: {str(e)}")
                results.append((test_name, {"success": False, "error": str(e)}))
            
            print()
        
        # Summary
        passed = sum(1 for _, result in results if result["success"])
        total = len(results)
        
        print("📊 Validation Summary:")
        print(f"   Tests passed: {passed}/{total}")
        print(f"   Success rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 All tests passed! HACS is properly configured for Supabase.")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Check the errors above.")
            
        print("\n💡 Recommendations:")
        print("   - Ensure DATABASE_URL includes sslmode=require for Supabase")
        print("   - Run migrations if HACS schemas are missing")
        print("   - Check network connectivity to Supabase if connections fail")
        print("   - Verify API keys and environment variables are properly loaded")


async def main():
    """Main validation function."""
    try:
        validator = SupabaseConnectionValidator()
        await validator.run_comprehensive_validation()
    except Exception as e:
        logger.error(f"Validation setup failed: {e}")
        print(f"\n❌ Validation setup failed: {e}")
        print("\n💡 Common fixes:")
        print("   - Ensure .env file exists with DATABASE_URL")
        print("   - Check DATABASE_URL format: postgresql://user:pass@host:port/db")
        print("   - Install required packages: uv pip install psycopg[binary]")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
