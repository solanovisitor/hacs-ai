#!/usr/bin/env python3
"""Quick test to verify ResourceBundle entry creation"""

import sys
import os

# Add HACS paths
sys.path.extend([
    "/Users/solanotodeschini/Code/hacs-ai/packages/hacs-models/src",
    "/Users/solanotodeschini/Code/hacs-ai/packages/hacs-core/src",
])

from hacs_models import ResourceBundle, Patient

def test_bundle_creation():
    """Test that ResourceBundle properly stores entries with resources"""
    # Create a bundle
    bundle = ResourceBundle(
        title="Test Bundle",
        bundle_type="document"
    )
    
    # Create a patient
    patient = Patient(
        full_name="Test Patient",
        birth_date="1990-01-01",
        gender="male"
    )
    
    # Add patient to bundle
    bundle.add_entry(
        resource=patient,
        title="Patient - test_patient",
        tags=["patient", "test"],
        priority=1
    )
    
    print("Bundle created:")
    print(f"- Title: {bundle.title}")
    print(f"- Number of entries: {len(bundle.entries)}")
    
    if bundle.entries:
        entry = bundle.entries[0]
        print(f"- Entry title: {entry.title}")
        print(f"- Entry tags: {entry.tags}")
        print(f"- Entry priority: {entry.priority}")
        print(f"- Entry has resource: {entry.resource is not None}")
        if entry.resource:
            print(f"- Resource type: {getattr(entry.resource, 'resource_type', 'Unknown')}")
            print(f"- Resource name: {getattr(entry.resource, 'full_name', 'N/A')}")
    
    return bundle

if __name__ == "__main__":
    bundle = test_bundle_creation()
    print("\nBundle JSON representation:")
    print(bundle.model_dump_json(indent=2))
