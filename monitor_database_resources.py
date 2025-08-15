#!/usr/bin/env python3
"""
Database Resource Monitor for HF Ingestion
Tracks resource states, relationships, and data quality during ingestion.
"""

import os
import sys
import time
import json
import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import hashlib

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add packages to path
packages = ["hacs-models", "hacs-core", "hacs-persistence", "hacs-registry"]
for pkg in packages:
    pkg_path = os.path.join(os.getcwd(), "packages", pkg, "src")
    if os.path.exists(pkg_path) and pkg_path not in sys.path:
        sys.path.insert(0, pkg_path)

@dataclass
class ResourceSnapshot:
    """Snapshot of a resource at a point in time."""
    timestamp: float
    resource_id: str
    resource_type: str
    resource_data: Dict[str, Any]
    data_hash: str
    metadata: Dict[str, Any]
    
    @classmethod
    def from_resource(cls, resource, metadata: Dict[str, Any] = None):
        """Create snapshot from a HACS resource."""
        if metadata is None:
            metadata = {}
        
        # Serialize resource data
        if hasattr(resource, 'model_dump'):
            data = resource.model_dump()
        elif hasattr(resource, '__dict__'):
            data = {k: v for k, v in resource.__dict__.items() if not k.startswith('_')}
        else:
            data = {"raw": str(resource)}
        
        # Create hash for change detection
        data_str = json.dumps(data, sort_keys=True, default=str)
        data_hash = hashlib.md5(data_str.encode()).hexdigest()
        
        return cls(
            timestamp=time.time(),
            resource_id=getattr(resource, 'id', 'unknown'),
            resource_type=getattr(resource, 'resource_type', type(resource).__name__),
            resource_data=data,
            data_hash=data_hash,
            metadata=metadata
        )


class DatabaseResourceMonitor:
    """Monitor database resources during HF ingestion workflow."""
    
    def __init__(self, monitor_id: Optional[str] = None):
        self.monitor_id = monitor_id or f"monitor_{int(time.time())}"
        self.snapshots: List[ResourceSnapshot] = []
        self.resource_registry: Dict[str, List[ResourceSnapshot]] = {}
        self.logger = logging.getLogger(f"DBMonitor.{self.monitor_id}")
        self.start_time = time.time()
        
        # Database connection
        self.database_url = os.getenv("DATABASE_URL", "postgresql://hacs:hacs_dev@localhost:5432/hacs")
        self.adapter = None
        self._setup_database()
        
        self.logger.info(f"Database Resource Monitor initialized: {self.monitor_id}")
    
    def _setup_database(self):
        """Setup database adapter for monitoring."""
        try:
            from hacs_persistence.adapter import PostgreSQLAdapter
            self.adapter = PostgreSQLAdapter(self.database_url)
            self.logger.info("Database adapter configured")
        except Exception as e:
            self.logger.warning(f"Database adapter setup failed, using mock: {e}")
            self.adapter = None
    
    def capture_resource_snapshot(self, resource, stage: str = "unknown", metadata: Dict[str, Any] = None):
        """Capture a snapshot of a resource."""
        if metadata is None:
            metadata = {}
        
        metadata.update({
            "stage": stage,
            "monitor_id": self.monitor_id,
            "capture_time": datetime.now().isoformat()
        })
        
        try:
            snapshot = ResourceSnapshot.from_resource(resource, metadata)
            self.snapshots.append(snapshot)
            
            # Update resource registry
            if snapshot.resource_id not in self.resource_registry:
                self.resource_registry[snapshot.resource_id] = []
            self.resource_registry[snapshot.resource_id].append(snapshot)
            
            self.logger.info(f"Captured snapshot: {snapshot.resource_type} {snapshot.resource_id} at {stage}")
            return snapshot
            
        except Exception as e:
            self.logger.error(f"Failed to capture snapshot: {e}")
            return None
    
    def get_resource_evolution(self, resource_id: str) -> List[ResourceSnapshot]:
        """Get the evolution of a resource over time."""
        return self.resource_registry.get(resource_id, [])
    
    def detect_resource_changes(self, resource_id: str) -> List[Dict[str, Any]]:
        """Detect changes in a resource over time."""
        snapshots = self.get_resource_evolution(resource_id)
        if len(snapshots) < 2:
            return []
        
        changes = []
        for i in range(1, len(snapshots)):
            prev = snapshots[i-1]
            curr = snapshots[i]
            
            if prev.data_hash != curr.data_hash:
                changes.append({
                    "timestamp": curr.timestamp,
                    "stage_from": prev.metadata.get("stage"),
                    "stage_to": curr.metadata.get("stage"),
                    "hash_changed": True,
                    "time_delta": curr.timestamp - prev.timestamp
                })
        
        return changes
    
    async def monitor_database_state(self) -> Dict[str, Any]:
        """Monitor the current database state."""
        state = {
            "timestamp": time.time(),
            "connection_status": "unknown",
            "table_counts": {},
            "recent_records": {},
            "data_integrity": {}
        }
        
        if not self.adapter:
            state["connection_status"] = "no_adapter"
            self.logger.warning("No database adapter available for monitoring")
            return state
        
        try:
            # Test connection with a simple operation
            from hacs_core import Actor
            test_actor = Actor(id="monitor", name="DB Monitor", role="system")
            
            # Try to create a test record
            from hacs_models import Patient
            test_patient = Patient(
                full_name="DB Monitor Test",
                gender="other",
                agent_context={"monitor_test": True, "monitor_id": self.monitor_id}
            )
            
            conn_start = time.time()
            result = await self.adapter.save(test_patient, test_actor)
            conn_duration = time.time() - conn_start
            
            state["connection_status"] = "connected"
            state["connection_duration"] = conn_duration
            state["test_record_id"] = result.id if result else None
            
            self.logger.info(f"Database connection verified in {conn_duration:.3f}s")
            
        except Exception as e:
            state["connection_status"] = "error"
            state["connection_error"] = str(e)
            self.logger.error(f"Database connection failed: {e}")
        
        return state
    
    def analyze_resource_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in captured resources."""
        analysis = {
            "total_snapshots": len(self.snapshots),
            "unique_resources": len(self.resource_registry),
            "resource_type_distribution": {},
            "stage_distribution": {},
            "resource_evolution_stats": {},
            "data_quality_metrics": {}
        }
        
        # Resource type distribution
        for snapshot in self.snapshots:
            rt = snapshot.resource_type
            analysis["resource_type_distribution"][rt] = analysis["resource_type_distribution"].get(rt, 0) + 1
        
        # Stage distribution
        for snapshot in self.snapshots:
            stage = snapshot.metadata.get("stage", "unknown")
            analysis["stage_distribution"][stage] = analysis["stage_distribution"].get(stage, 0) + 1
        
        # Resource evolution analysis
        evolution_lengths = [len(snapshots) for snapshots in self.resource_registry.values()]
        if evolution_lengths:
            analysis["resource_evolution_stats"] = {
                "avg_snapshots_per_resource": sum(evolution_lengths) / len(evolution_lengths),
                "max_snapshots_per_resource": max(evolution_lengths),
                "min_snapshots_per_resource": min(evolution_lengths),
                "resources_with_changes": sum(1 for length in evolution_lengths if length > 1)
            }
        
        # Data quality metrics
        quality_issues = []
        for resource_id, snapshots in self.resource_registry.items():
            # Check for duplicate hashes (no actual changes)
            hashes = [s.data_hash for s in snapshots]
            if len(set(hashes)) < len(hashes):
                quality_issues.append(f"Resource {resource_id}: Duplicate snapshots detected")
            
            # Check for rapid changes (potential data instability)
            if len(snapshots) > 1:
                time_deltas = [snapshots[i].timestamp - snapshots[i-1].timestamp for i in range(1, len(snapshots))]
                if any(delta < 0.1 for delta in time_deltas):  # Changes within 100ms
                    quality_issues.append(f"Resource {resource_id}: Rapid changes detected")
        
        analysis["data_quality_metrics"] = {
            "quality_issues_count": len(quality_issues),
            "quality_issues": quality_issues[:10]  # Limit to first 10
        }
        
        return analysis
    
    def generate_resource_report(self, resource_id: str) -> Dict[str, Any]:
        """Generate a detailed report for a specific resource."""
        snapshots = self.get_resource_evolution(resource_id)
        if not snapshots:
            return {"error": f"No snapshots found for resource {resource_id}"}
        
        first_snapshot = snapshots[0]
        last_snapshot = snapshots[-1]
        
        report = {
            "resource_id": resource_id,
            "resource_type": first_snapshot.resource_type,
            "total_snapshots": len(snapshots),
            "first_captured": datetime.fromtimestamp(first_snapshot.timestamp).isoformat(),
            "last_captured": datetime.fromtimestamp(last_snapshot.timestamp).isoformat(),
            "stages_traversed": list(set(s.metadata.get("stage", "unknown") for s in snapshots)),
            "changes_detected": len(self.detect_resource_changes(resource_id)),
            "data_evolution": []
        }
        
        # Track key field changes
        if len(snapshots) > 1:
            for i in range(1, len(snapshots)):
                prev_data = snapshots[i-1].resource_data
                curr_data = snapshots[i].resource_data
                
                changed_fields = []
                for key in set(prev_data.keys()) | set(curr_data.keys()):
                    if prev_data.get(key) != curr_data.get(key):
                        changed_fields.append(key)
                
                if changed_fields:
                    report["data_evolution"].append({
                        "snapshot_index": i,
                        "timestamp": snapshots[i].timestamp,
                        "stage": snapshots[i].metadata.get("stage"),
                        "changed_fields": changed_fields
                    })
        
        return report
    
    def export_monitoring_data(self, filename: Optional[str] = None) -> str:
        """Export all monitoring data to JSON file."""
        if filename is None:
            filename = f"db_monitor_{self.monitor_id}_{int(time.time())}.json"
        
        export_data = {
            "monitor_id": self.monitor_id,
            "start_time": self.start_time,
            "export_time": time.time(),
            "total_duration": time.time() - self.start_time,
            "snapshots": [
                {
                    "timestamp": s.timestamp,
                    "resource_id": s.resource_id,
                    "resource_type": s.resource_type,
                    "data_hash": s.data_hash,
                    "metadata": s.metadata,
                    "resource_data": s.resource_data
                }
                for s in self.snapshots
            ],
            "analysis": self.analyze_resource_patterns()
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        self.logger.info(f"Monitoring data exported to {filename}")
        return filename


async def monitor_hf_ingestion_workflow():
    """Monitor the HF ingestion workflow with detailed resource tracking."""
    print("🔍 Database Resource Monitor for HF Ingestion")
    print("="*60)
    
    monitor = DatabaseResourceMonitor()
    
    try:
        # Initial database state
        print("\n📊 Initial Database State")
        initial_state = await monitor.monitor_database_state()
        print(f"Connection Status: {initial_state['connection_status']}")
        if initial_state.get('connection_duration'):
            print(f"Connection Time: {initial_state['connection_duration']:.3f}s")
        
        # Simulate monitoring during ingestion workflow
        print("\n🔄 Simulating Workflow Monitoring")
        
        # Stage 1: Template Creation
        print("Stage 1: Template Creation")
        try:
            from hacs_models import StackTemplate, LayerSpec
            
            template = StackTemplate(
                name="monitor_test_template",
                version="1.0.0",
                description="Test template for monitoring",
                variables={"patient_name": {"type": "string"}, "condition": {"type": "string"}},
                layers=[
                    LayerSpec(
                        resource_type="Patient",
                        layer_name="patient",
                        bindings={"full_name": "patient_name"},
                        constant_fields={"gender": "unknown"}
                    ),
                    LayerSpec(
                        resource_type="Observation",
                        layer_name="observation",
                        bindings={"value_string": "condition"},
                        constant_fields={"status": "final", "code.text": "Clinical Note"}
                    )
                ]
            )
            
            monitor.capture_resource_snapshot(template, "template_creation")
            print(f"  ✅ Template captured: {template.name}")
            
        except Exception as e:
            print(f"  ❌ Template creation failed: {e}")
        
        # Stage 2: Resource Instantiation
        print("\nStage 2: Resource Instantiation")
        try:
            from hacs_models import instantiate_stack_template, Patient, Observation
            
            variables = {"patient_name": "Monitor Test Patient", "condition": "Monitoring workflow"}
            stack = instantiate_stack_template(template, variables)
            
            for layer_name, resource in stack.items():
                monitor.capture_resource_snapshot(resource, "instantiation", {"layer_name": layer_name})
                print(f"  ✅ Resource captured: {resource.resource_type} ({layer_name})")
        
        except Exception as e:
            print(f"  ❌ Resource instantiation failed: {e}")
        
        # Stage 3: Persistence Simulation
        print("\nStage 3: Persistence Simulation")
        for layer_name, resource in stack.items():
            # Simulate persistence changes
            if hasattr(resource, 'agent_context'):
                if resource.agent_context is None:
                    resource.agent_context = {}
                resource.agent_context['persisted'] = True
                resource.agent_context['persist_time'] = time.time()
            
            monitor.capture_resource_snapshot(resource, "pre_persistence", {"layer_name": layer_name})
            
            # Simulate post-persistence state
            if hasattr(resource, 'updated_at'):
                resource.updated_at = datetime.now()
            
            monitor.capture_resource_snapshot(resource, "post_persistence", {"layer_name": layer_name})
            print(f"  ✅ Persistence simulated: {resource.resource_type}")
        
        # Stage 4: Data Quality Validation
        print("\nStage 4: Data Quality Validation")
        for layer_name, resource in stack.items():
            # Simulate validation changes
            if hasattr(resource, 'agent_context'):
                if resource.agent_context is None:
                    resource.agent_context = {}
                resource.agent_context['validated'] = True
                resource.agent_context['validation_score'] = 0.95
            
            monitor.capture_resource_snapshot(resource, "validation", {"layer_name": layer_name})
            print(f"  ✅ Validation captured: {resource.resource_type}")
        
        # Final database state
        print("\n📊 Final Database State")
        final_state = await monitor.monitor_database_state()
        print(f"Connection Status: {final_state['connection_status']}")
        
        # Analysis and reporting
        print("\n📈 Monitoring Analysis")
        analysis = monitor.analyze_resource_patterns()
        
        print(f"Total Snapshots: {analysis['total_snapshots']}")
        print(f"Unique Resources: {analysis['unique_resources']}")
        
        print(f"\nResource Type Distribution:")
        for rt, count in analysis['resource_type_distribution'].items():
            print(f"  {rt}: {count}")
        
        print(f"\nStage Distribution:")
        for stage, count in analysis['stage_distribution'].items():
            print(f"  {stage}: {count}")
        
        if analysis['resource_evolution_stats']:
            stats = analysis['resource_evolution_stats']
            print(f"\nResource Evolution:")
            print(f"  Avg snapshots per resource: {stats['avg_snapshots_per_resource']:.1f}")
            print(f"  Resources with changes: {stats['resources_with_changes']}")
        
        if analysis['data_quality_metrics']['quality_issues']:
            print(f"\nData Quality Issues:")
            for issue in analysis['data_quality_metrics']['quality_issues']:
                print(f"  ⚠️  {issue}")
        
        # Generate detailed reports for each resource
        print(f"\n📋 Resource Reports")
        for resource_id in monitor.resource_registry.keys():
            report = monitor.generate_resource_report(resource_id)
            print(f"\nResource {resource_id[:8]}...:")
            print(f"  Type: {report['resource_type']}")
            print(f"  Snapshots: {report['total_snapshots']}")
            print(f"  Stages: {', '.join(report['stages_traversed'])}")
            print(f"  Changes: {report['changes_detected']}")
        
        # Export data
        export_file = monitor.export_monitoring_data()
        print(f"\n💾 Monitoring data exported to: {export_file}")
        
        # Sleep for log analysis
        sleep_time = float(os.getenv("MONITOR_SLEEP", "2.0"))
        print(f"\n⏱️  Sleeping for {sleep_time}s to allow log analysis...")
        time.sleep(sleep_time)
        print("⏰ Sleep completed")
        
    except Exception as e:
        print(f"❌ Monitoring failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")


if __name__ == "__main__":
    asyncio.run(monitor_hf_ingestion_workflow())
