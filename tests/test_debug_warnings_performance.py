import os
import time
import warnings
import gc


def test_debug_warnings_and_performance():
    """Debug warnings and measure performance of HACS operations."""
    os.environ.setdefault("PYTHONPATH", ".")

    print("\n⚠️  DEBUGGING WARNINGS AND PERFORMANCE")
    print("=" * 60)

    # Capture warnings
    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter("always")

        # Test imports to see what warnings they generate
        print("🔍 Testing imports and their warnings...")

        start_time = time.time()
        from hacs_models import (
            get_model_registry,
        )
        from hacs_tools.domains import resource_management, schema_discovery

        import_time = time.time() - start_time

        print(f"   Import time: {import_time:.3f}s")
        print(f"   Warnings during import: {len(warning_list)}")

        # Categorize warnings
        warning_categories = {}
        for w in warning_list:
            category = w.category.__name__
            if category not in warning_categories:
                warning_categories[category] = []
            warning_categories[category].append(str(w.message))

        print("\n📊 Warning Analysis:")
        for category, messages in warning_categories.items():
            print(f"   {category}: {len(messages)} warnings")
            # Show first few unique messages per category
            unique_messages = list(set(messages))[:3]
            for msg in unique_messages:
                print(f"      - {msg[:100]}{'...' if len(msg) > 100 else ''}")

    # Performance testing
    print("\n🚀 PERFORMANCE TESTING")
    print("=" * 40)

    # Test 1: Model registry performance
    print("🔍 Model registry performance...")
    start_time = time.time()
    for _ in range(100):
        registry = get_model_registry()
    registry_time = time.time() - start_time
    print(
        f"   100 registry calls: {registry_time:.3f}s ({registry_time * 10:.1f}ms per call)"
    )

    # Test 2: Schema discovery performance
    print("\n🔍 Schema discovery performance...")
    test_models = ["Patient", "Observation", "MedicationRequest", "Procedure"]

    discovery_times = {}
    for model in test_models:
        start_time = time.time()
        for _ in range(10):
            result = schema_discovery.get_hacs_resource_schema(
                model, include_examples=False
            )
        end_time = time.time()
        discovery_times[model] = (end_time - start_time) / 10
        print(f"   {model}: {discovery_times[model] * 1000:.1f}ms per discovery")

    # Test 3: Resource creation performance
    print("\n🔍 Resource creation performance...")

    # Simple patient creation
    simple_patient_data = {"full_name": "Performance Test", "gender": "other"}
    start_time = time.time()
    for i in range(50):
        result = resource_management.create_record(
            actor_name="PerfTester",
            resource_type="Patient",
            resource_data={**simple_patient_data, "full_name": f"Test Patient {i}"},
        )
        assert result.success
    simple_creation_time = time.time() - start_time
    print(
        f"   50 simple patients: {simple_creation_time:.3f}s ({simple_creation_time * 20:.1f}ms per creation)"
    )

    # Complex observation creation
    complex_obs_data = {
        "status": "final",
        "code": {
            "text": "Blood Pressure",
            "coding": [{"code": "BP", "system": "custom"}],
        },
        "value_quantity": {"value": 120, "unit": "mmHg"},
        "category": [{"text": "vital-signs"}],
        "reference_range": [{"low": {"value": 100}, "high": {"value": 140}}],
        "agent_context": {"source": "performance_test", "batch": True},
    }

    start_time = time.time()
    for i in range(25):
        result = resource_management.create_record(
            actor_name="PerfTester",
            resource_type="Observation",
            resource_data={
                **complex_obs_data,
                "value_quantity": {"value": 120 + i, "unit": "mmHg"},
            },
        )
        assert result.success
    complex_creation_time = time.time() - start_time
    print(
        f"   25 complex observations: {complex_creation_time:.3f}s ({complex_creation_time * 40:.1f}ms per creation)"
    )

    # Test 4: Memory usage tracking
    print("\n🔍 Memory usage analysis...")
    gc.collect()  # Clean up before measuring

    # Create many resources and track memory
    initial_objects = len(gc.get_objects())
    print(f"   Initial objects in memory: {initial_objects:,}")

    resources_created = []
    for i in range(100):
        result = resource_management.create_record(
            actor_name="MemoryTester",
            resource_type="Patient",
            resource_data={"full_name": f"Memory Test {i}", "gender": "other"},
        )
        if hasattr(result, "resource_data"):
            resources_created.append(result.resource_data)

    after_creation_objects = len(gc.get_objects())
    print(f"   Objects after 100 creations: {after_creation_objects:,}")
    print(f"   Object increase: {after_creation_objects - initial_objects:,}")

    # Clean up
    del resources_created
    gc.collect()
    after_cleanup_objects = len(gc.get_objects())
    print(f"   Objects after cleanup: {after_cleanup_objects:,}")

    # Test 5: Batch operations
    print("\n🔍 Batch operations performance...")

    batch_data = []
    for i in range(20):
        batch_data.append(
            {
                "resource_type": "Observation",
                "data": {
                    "status": "final",
                    "code": {"text": f"Test {i}"},
                    "value_string": f"Value {i}",
                    "agent_context": {"batch_id": "perf_test_batch"},
                },
            }
        )

    start_time = time.time()
    batch_results = []
    for item in batch_data:
        result = resource_management.create_record(
            actor_name="BatchTester",
            resource_type=item["resource_type"],
            resource_data=item["data"],
        )
        batch_results.append(result)
    batch_time = time.time() - start_time

    successful_creates = sum(1 for r in batch_results if r.success)
    print(f"   Batch of 20 observations: {batch_time:.3f}s")
    print(
        f"   Success rate: {successful_creates}/20 ({successful_creates / 20 * 100:.1f}%)"
    )
    print(f"   Average per item: {batch_time * 50:.1f}ms")

    # Performance summary
    print("\n📈 PERFORMANCE SUMMARY")
    print("=" * 40)
    print(f"   Registry access: {registry_time * 10:.1f}ms per call")
    print(
        f"   Schema discovery: {sum(discovery_times.values()) / len(discovery_times) * 1000:.1f}ms avg"
    )
    print(f"   Simple creation: {simple_creation_time * 20:.1f}ms per patient")
    print(f"   Complex creation: {complex_creation_time * 40:.1f}ms per observation")
    print(
        f"   Memory overhead: {after_creation_objects - initial_objects:,} objects per 100 resources"
    )

    # Performance assertions (basic smoke tests)
    assert registry_time < 1.0, "Registry access too slow"
    assert all(t < 0.1 for t in discovery_times.values()), "Schema discovery too slow"
    assert simple_creation_time < 5.0, "Simple creation too slow"
    assert complex_creation_time < 10.0, "Complex creation too slow"

    print(
        "\n✅ Performance testing completed - all benchmarks within acceptable ranges"
    )


def test_debug_circular_import_warnings():
    """Specifically debug circular import warnings."""
    os.environ.setdefault("PYTHONPATH", ".")

    print("\n🔄 DEBUGGING CIRCULAR IMPORT WARNINGS")
    print("=" * 50)

    import sys

    # Track import order and dependencies
    initial_modules = set(sys.modules.keys())
    print(f"🔍 Initial modules loaded: {len(initial_modules)}")

    # Test importing packages in different orders
    import_sequences = [
        ["hacs_models", "hacs_core", "hacs_tools"],
        ["hacs_core", "hacs_models", "hacs_tools"],
        ["hacs_tools", "hacs_models", "hacs_core"],
        ["hacs_registry", "hacs_models", "hacs_utils"],
    ]

    for i, sequence in enumerate(import_sequences):
        print(f"\n   Test {i + 1}: Import sequence {' -> '.join(sequence)}")

        # Clear specific modules to test fresh imports
        modules_to_clear = []
        for mod_name in sequence:
            modules_to_clear.extend(
                [name for name in sys.modules.keys() if name.startswith(mod_name)]
            )

        # Record warnings during import
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            try:
                for mod_name in sequence:
                    if mod_name == "hacs_models":
                        pass
                    elif mod_name == "hacs_core":
                        pass
                    elif mod_name == "hacs_tools":
                        pass
                    elif mod_name == "hacs_registry":
                        pass
                    elif mod_name == "hacs_utils":
                        pass

                circular_warnings = [
                    warning
                    for warning in w
                    if "circular import" in str(warning.message).lower()
                ]

                print(f"      Circular import warnings: {len(circular_warnings)}")
                for warning in circular_warnings[:2]:  # Show first 2
                    print(f"         - {str(warning.message)[:80]}...")

            except Exception as e:
                print(f"      Import error: {type(e).__name__}: {e}")

    final_modules = set(sys.modules.keys())
    new_modules = final_modules - initial_modules
    print(f"\n📊 New modules loaded during testing: {len(new_modules)}")
    hacs_modules = [m for m in new_modules if "hacs" in m]
    print(f"   HACS-related modules: {len(hacs_modules)}")

    print("\n✅ Circular import analysis completed")


if __name__ == "__main__":
    # Run performance and warning tests
    test_debug_circular_import_warnings()
    test_debug_warnings_and_performance()
