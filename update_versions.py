#!/usr/bin/env python3
"""
Update all HACS package versions to 0.3.1 for republishing to PyPI.
"""

import re
from pathlib import Path

def update_version_in_file(file_path: Path, new_version: str):
    """Update version in a pyproject.toml file."""
    content = file_path.read_text()
    
    # Update version = "0.3.0" to version = "0.3.1"
    updated_content = re.sub(
        r'version = "[0-9]+\.[0-9]+\.[0-9]+"',
        f'version = "{new_version}"',
        content
    )
    
    # Also update dependency versions for HACS packages
    for pkg in ["hacs-models", "hacs-auth", "hacs-infrastructure", "hacs-core", 
                "hacs-persistence", "hacs-tools", "hacs-registry", "hacs-utils", "hacs-cli"]:
        updated_content = re.sub(
            f'"{pkg}>=[0-9]+\\.[0-9]+\\.[0-9]+"',
            f'"{pkg}>={new_version}"',
            updated_content
        )
    
    if content != updated_content:
        file_path.write_text(updated_content)
        print(f"✅ Updated {file_path.name}")
        return True
    else:
        print(f"🔄 No changes needed for {file_path.name}")
        return False

def main():
    """Update all HACS package versions to 0.3.1."""
    new_version = "0.3.1"
    packages_dir = Path("packages")
    
    if not packages_dir.exists():
        print(f"❌ Packages directory not found: {packages_dir}")
        return
    
    updated_count = 0
    
    # Find all pyproject.toml files in package directories
    for package_dir in packages_dir.iterdir():
        if package_dir.is_dir() and package_dir.name.startswith("hacs-"):
            pyproject_file = package_dir / "pyproject.toml"
            if pyproject_file.exists():
                print(f"📦 Updating {package_dir.name}...")
                if update_version_in_file(pyproject_file, new_version):
                    updated_count += 1
            else:
                print(f"⚠️  No pyproject.toml found in {package_dir.name}")
    
    print(f"\n🎉 Updated {updated_count} packages to version {new_version}")
    print("Ready for rebuilding and republishing to PyPI!")

if __name__ == "__main__":
    main()