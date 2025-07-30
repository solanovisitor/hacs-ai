#!/usr/bin/env python3
"""
HACS PyPI Publishing Script - Fresh Repository

This script publishes the comprehensive HACS healthcare packages to PyPI.
"""

import argparse
import glob
import subprocess
import sys
from pathlib import Path
import os

# Load environment variables from .env file
def load_env():
    """Load environment variables from .env file."""
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Load environment variables
load_env()

# Package order for publishing (dependencies first)
PACKAGE_ORDER = [
    "hacs-core",
    "hacs-registry",
    "hacs-persistence",
    "hacs-tools",
    "hacs-utils",
    "hacs-cli",
]

PACKAGE_PATHS = {
    "hacs-core": "packages/hacs-core",
    "hacs-tools": "packages/hacs-tools",
    "hacs-utils": "packages/hacs-utils",
    "hacs-persistence": "packages/hacs-persistence",
    "hacs-registry": "packages/hacs-registry",
    "hacs-cli": "packages/hacs-cli",
}

# Legacy packages to delete from PyPI
LEGACY_PACKAGES = [
    "hacs-models",
    "hacs-fhir",
]


def run_command(cmd, cwd=None):
    """Run a command and return True if successful."""
    try:
        result = subprocess.run(
            cmd, check=True, capture_output=True, text=True, cwd=cwd
        )
        print(f"✅ {' '.join(cmd[:3])}...")  # Truncate long commands
        if result.stdout.strip():
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {' '.join(cmd[:3])}... (failed)")
        if e.stdout:
            print(f"   Stdout: {e.stdout.strip()}")
        if e.stderr:
            print(f"   Error: {e.stderr.strip()}")
        return False


def validate_package(package_name):
    """Validate a package configuration."""
    print(f"\n📦 Validating {package_name}...")
    
    package_path = Path(PACKAGE_PATHS[package_name])
    if not package_path.exists():
        print(f"❌ Package path does not exist: {package_path}")
        return False

    # Check if pyproject.toml exists
    pyproject_path = package_path / "pyproject.toml"
    if not pyproject_path.exists():
        print(f"❌ pyproject.toml not found in {package_path}")
        return False

    print(f"✅ {package_name} validation passed")
    return True


def build_package(package_name):
    """Build a package using uv."""
    print(f"\n🔨 Building {package_name}...")
    
    # Clean previous builds for this package in workspace dist
    dist_path = Path("dist")
    if dist_path.exists():
        # Remove any existing builds for this package
        for file in dist_path.glob(f"{package_name.replace('-', '_')}-*"):
            file.unlink()
    
    # Build the package (UV builds all packages to workspace dist)
    if run_command(["uv", "build", "--package", package_name]):
        print(f"✅ {package_name} built successfully")
        return True
    else:
        print(f"❌ Failed to build {package_name}")
        return False


def publish_package(package_name, repository="pypi"):
    """Publish a package to PyPI or TestPyPI."""
    print(f"\n📤 Publishing {package_name} to {repository}...")
    
    repository_url = {
        "testpypi": "https://test.pypi.org/legacy/",
        "pypi": "https://upload.pypi.org/legacy/"
    }
    
    # Set up authentication
    if repository == "testpypi":
        token = os.getenv("TEST_PYPI_API_TOKEN")
        if not token:
            print("❌ TEST_PYPI_API_TOKEN environment variable not set")
            print("   Get your TestPyPI token from: https://test.pypi.org/manage/account/token/")
            return False
        username = "__token__"
        password = token
    else:  # pypi
        token = os.getenv("PYPI_API_TOKEN")
        if not token:
            print("❌ PYPI_API_TOKEN environment variable not set")
            print("   Get your PyPI token from: https://pypi.org/manage/account/token/")
            return False
        username = "__token__"
        password = token
    
    # Find the built files for this package
    dist_path = Path("dist")
    package_files = list(dist_path.glob(f"{package_name.replace('-', '_')}-*"))
    
    if not package_files:
        print(f"❌ No built files found for {package_name} in dist/")
        return False
    
    # Upload the specific package files
    cmd = [
        "uv", "run", "twine", "upload",
        "--repository-url", repository_url[repository],
        "--username", username,
        "--password", password,
    ] + [str(f) for f in package_files]
    
    if run_command(cmd):
        print(f"✅ {package_name} published to {repository}")
        return True
    else:
        print(f"❌ Failed to publish {package_name}")
        return False


def check_packages():
    """Validate all packages."""
    print("🔍 Validating all packages...")
    all_valid = True
    
    for package_name in PACKAGE_ORDER:
        if not validate_package(package_name):
            all_valid = False
    
    if all_valid:
        print("\n✅ All packages validated successfully!")
    else:
        print("\n❌ Some packages failed validation")
        sys.exit(1)


def test_publish():
    """Build and publish packages to TestPyPI."""
    print("🧪 Testing publishing to TestPyPI...")
    
    # Check if TEST_PYPI_API_TOKEN is available
    if not os.getenv("TEST_PYPI_API_TOKEN"):
        print("⚠️  TEST_PYPI_API_TOKEN not found in environment")
        print("\nOptions:")
        print("1. Get TestPyPI token from: https://test.pypi.org/manage/account/token/")
        print("2. Run dry-run build test: uv run python publish.py --check")
        print("3. Skip to production: uv run python publish.py --production")
        
        if os.getenv("PYPI_API_TOKEN"):
            print("\n✅ Production PYPI_API_TOKEN found - you can proceed with --production")
        
        return
    
    # First validate all packages
    check_packages()
    
    # Build and publish each package
    for package_name in PACKAGE_ORDER:
        if not build_package(package_name):
            sys.exit(1)
        if not publish_package(package_name, "testpypi"):
            sys.exit(1)
    
    print("\n🎉 All packages successfully published to TestPyPI!")
    print("📝 Test your packages with:")
    print("   pip install --index-url https://test.pypi.org/simple/ hacs-core")


def production_publish():
    """Build and publish packages to production PyPI."""
    print("🚀 Publishing to production PyPI...")
    
    # Show existing packages warning
    existing_packages = ["hacs-tools"]  # Based on user's PyPI account
    new_packages = ["hacs-core", "hacs-registry", "hacs-persistence", "hacs-utils", "hacs-cli"]
    
    print("\n📋 Publishing Plan:")
    print("   📦 Updating existing packages:")
    for pkg in existing_packages:
        if pkg in PACKAGE_ORDER:
            print(f"      - {pkg} (version update)")
    
    print("   ✨ Publishing new packages:")
    for pkg in new_packages:
        if pkg in PACKAGE_ORDER:
            print(f"      - {pkg} (first release)")
    
    # Confirmation prompt
    response = input("\n⚠️  Are you sure you want to publish to production PyPI? (yes/no): ")
    if response.lower() != "yes":
        print("❌ Aborted")
        sys.exit(1)
    
    # First validate all packages
    check_packages()
    
    # Build and publish each package
    for package_name in PACKAGE_ORDER:
        if not build_package(package_name):
            sys.exit(1)
        if not publish_package(package_name, "pypi"):
            sys.exit(1)
    
    print("\n🎉 All packages successfully published to PyPI!")
    print("📝 Install your packages with:")
    print("   pip install hacs-core")
    print("\n💡 Legacy package cleanup:")
    print("   Consider deprecating 'hacs-models' in favor of 'hacs-core'")


def main():
    parser = argparse.ArgumentParser(description="Publish HACS packages to PyPI")
    parser.add_argument("--check", action="store_true", help="Only validate packages")
    parser.add_argument("--delete-legacy", action="store_true", help="Show legacy deletion instructions")
    parser.add_argument("--test", action="store_true", help="Build and publish to TestPyPI")
    parser.add_argument("--production", action="store_true", help="Build and publish to production PyPI")
    
    args = parser.parse_args()
    
    if args.delete_legacy:
        print("🗑️ Legacy packages to delete from PyPI:")
        for pkg in LEGACY_PACKAGES:
            print(f"  - {pkg}")
        print("\nTo delete these packages:")
        print("1. Go to https://pypi.org/manage/projects/")
        print("2. Navigate to each legacy project")
        print("3. Delete the project to free up the name")
        return
    
    if args.check:
        check_packages()
        return
    
    if args.test:
        test_publish()
        return
    
    if args.production:
        production_publish()
        return
    
    # Default: show package information
    print("📦 Current HACS packages ready for publishing:")
    for pkg in PACKAGE_ORDER:
        print(f"  - {pkg}")
    print("\nAvailable commands:")
    print("  --check         Validate packages")
    print("  --test          Publish to TestPyPI")
    print("  --production    Publish to PyPI")
    print("  --delete-legacy Show legacy deletion instructions")


if __name__ == "__main__":
    main()
