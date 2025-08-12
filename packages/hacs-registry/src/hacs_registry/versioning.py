"""
Tool Versioning System for HACS

This module provides comprehensive versioning support for HACS tools including:
- Semantic versioning validation
- Version comparison and compatibility checking
- Deprecation warnings and migration paths
- Version-aware tool selection
- Backward compatibility management
"""

import re
import warnings
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum


class VersionStatus(str, Enum):
    """Version status indicators."""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    OBSOLETE = "obsolete"
    BETA = "beta"
    ALPHA = "alpha"


@dataclass
class VersionInfo:
    """Comprehensive version information."""
    version: str
    status: VersionStatus = VersionStatus.ACTIVE
    release_date: Optional[datetime] = None
    deprecation_date: Optional[datetime] = None
    end_of_life_date: Optional[datetime] = None
    migration_notes: str = ""
    breaking_changes: List[str] = field(default_factory=list)
    compatibility_notes: str = ""


class SemanticVersion:
    """Semantic versioning implementation following semver.org."""
    
    def __init__(self, version_string: str):
        self.original = version_string
        self.major, self.minor, self.patch, self.prerelease, self.build = self._parse(version_string)
    
    def _parse(self, version_string: str) -> Tuple[int, int, int, Optional[str], Optional[str]]:
        """Parse semantic version string."""
        # Remove 'v' prefix if present
        version_string = version_string.lstrip('v')
        
        # Pattern for semantic versioning
        pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$'
        
        match = re.match(pattern, version_string)
        if not match:
            raise ValueError(f"Invalid semantic version: {version_string}")
        
        major, minor, patch, prerelease, build = match.groups()
        
        return (
            int(major),
            int(minor), 
            int(patch),
            prerelease,
            build
        )
    
    def __str__(self) -> str:
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build:
            version += f"+{self.build}"
        return version
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, SemanticVersion):
            other = SemanticVersion(str(other))
        return (self.major, self.minor, self.patch, self.prerelease) == \
               (other.major, other.minor, other.patch, other.prerelease)
    
    def __lt__(self, other) -> bool:
        if not isinstance(other, SemanticVersion):
            other = SemanticVersion(str(other))
        
        # Compare major.minor.patch first
        if (self.major, self.minor, self.patch) != (other.major, other.minor, other.patch):
            return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
        
        # Handle prerelease comparison
        if self.prerelease is None and other.prerelease is None:
            return False
        if self.prerelease is None:
            return False  # Normal version > prerelease
        if other.prerelease is None:
            return True   # Prerelease < normal version
        
        return self.prerelease < other.prerelease
    
    def __le__(self, other) -> bool:
        return self == other or self < other
    
    def __gt__(self, other) -> bool:
        return not self <= other
    
    def __ge__(self, other) -> bool:
        return not self < other
    
    def is_compatible_with(self, other: 'SemanticVersion') -> bool:
        """Check if this version is backward compatible with another version."""
        # Same major version = compatible (following semver)
        return self.major == other.major and self >= other
    
    def is_breaking_change_from(self, other: 'SemanticVersion') -> bool:
        """Check if this version introduces breaking changes from another version."""
        return self.major > other.major


class ToolVersionManager:
    """Manages tool versions and compatibility."""
    
    def __init__(self):
        self._tool_versions: Dict[str, List[VersionInfo]] = {}
        self._active_versions: Dict[str, str] = {}  # tool_name -> active_version
    
    def register_version(self, tool_name: str, version_info: VersionInfo):
        """Register a version for a tool."""
        if tool_name not in self._tool_versions:
            self._tool_versions[tool_name] = []
        
        # Validate version format
        try:
            semantic_version = SemanticVersion(version_info.version)
        except ValueError as e:
            raise ValueError(f"Invalid version for tool {tool_name}: {e}")
        
        # Check for duplicate versions
        existing_versions = [v.version for v in self._tool_versions[tool_name]]
        if version_info.version in existing_versions:
            raise ValueError(f"Version {version_info.version} already exists for tool {tool_name}")
        
        # Add the version
        self._tool_versions[tool_name].append(version_info)
        
        # Sort versions
        self._tool_versions[tool_name].sort(
            key=lambda v: SemanticVersion(v.version), 
            reverse=True
        )
        
        # Update active version if this is the latest active version
        if version_info.status == VersionStatus.ACTIVE:
            current_active = self._active_versions.get(tool_name)
            if not current_active or SemanticVersion(version_info.version) > SemanticVersion(current_active):
                self._active_versions[tool_name] = version_info.version
    
    def get_active_version(self, tool_name: str) -> Optional[str]:
        """Get the active version for a tool."""
        return self._active_versions.get(tool_name)
    
    def get_version_info(self, tool_name: str, version: str) -> Optional[VersionInfo]:
        """Get version information for a specific tool version."""
        if tool_name not in self._tool_versions:
            return None
        
        for version_info in self._tool_versions[tool_name]:
            if version_info.version == version:
                return version_info
        
        return None
    
    def get_all_versions(self, tool_name: str) -> List[VersionInfo]:
        """Get all versions for a tool, sorted by version (newest first)."""
        return self._tool_versions.get(tool_name, []).copy()
    
    def find_compatible_version(self, tool_name: str, requested_version: str) -> Optional[str]:
        """Find a compatible version for a tool."""
        if tool_name not in self._tool_versions:
            return None
        
        try:
            requested_semver = SemanticVersion(requested_version)
        except ValueError:
            return None
        
        # Find the highest compatible version
        compatible_versions = []
        for version_info in self._tool_versions[tool_name]:
            if version_info.status in [VersionStatus.ACTIVE, VersionStatus.DEPRECATED]:
                try:
                    version_semver = SemanticVersion(version_info.version)
                    if version_semver.is_compatible_with(requested_semver):
                        compatible_versions.append(version_info)
                except ValueError:
                    continue
        
        if compatible_versions:
            # Return the highest compatible version
            compatible_versions.sort(key=lambda v: SemanticVersion(v.version), reverse=True)
            return compatible_versions[0].version
        
        return None
    
    def check_deprecation(self, tool_name: str, version: str) -> Optional[str]:
        """Check if a tool version is deprecated and return warning message."""
        version_info = self.get_version_info(tool_name, version)
        if not version_info:
            return None
        
        if version_info.status == VersionStatus.DEPRECATED:
            message = f"Tool {tool_name} version {version} is deprecated."
            
            if version_info.end_of_life_date:
                message += f" End of life: {version_info.end_of_life_date.strftime('%Y-%m-%d')}"
            
            active_version = self.get_active_version(tool_name)
            if active_version:
                message += f" Please migrate to version {active_version}."
            
            if version_info.migration_notes:
                message += f" Migration notes: {version_info.migration_notes}"
            
            return message
        
        return None
    
    def get_migration_path(self, tool_name: str, from_version: str, to_version: str) -> Dict[str, Any]:
        """Get migration information between two versions."""
        from_info = self.get_version_info(tool_name, from_version)
        to_info = self.get_version_info(tool_name, to_version)
        
        if not from_info or not to_info:
            return {"error": "Version not found"}
        
        try:
            from_semver = SemanticVersion(from_version)
            to_semver = SemanticVersion(to_version)
        except ValueError as e:
            return {"error": f"Invalid version format: {e}"}
        
        migration_info = {
            "from_version": from_version,
            "to_version": to_version,
            "is_breaking_change": to_semver.is_breaking_change_from(from_semver),
            "is_compatible": to_semver.is_compatible_with(from_semver),
            "breaking_changes": to_info.breaking_changes,
            "migration_notes": to_info.migration_notes,
            "compatibility_notes": to_info.compatibility_notes
        }
        
        return migration_info
    
    def cleanup_obsolete_versions(self, tool_name: str) -> List[str]:
        """Remove obsolete versions and return list of removed versions."""
        if tool_name not in self._tool_versions:
            return []
        
        removed_versions = []
        current_time = datetime.now()
        
        # Filter out obsolete versions that have passed their end of life date
        remaining_versions = []
        for version_info in self._tool_versions[tool_name]:
            if (version_info.status == VersionStatus.OBSOLETE and 
                version_info.end_of_life_date and 
                current_time > version_info.end_of_life_date):
                removed_versions.append(version_info.version)
            else:
                remaining_versions.append(version_info)
        
        self._tool_versions[tool_name] = remaining_versions
        
        return removed_versions
    
    def get_version_statistics(self) -> Dict[str, Any]:
        """Get statistics about tool versions."""
        stats = {
            "total_tools": len(self._tool_versions),
            "total_versions": sum(len(versions) for versions in self._tool_versions.values()),
            "status_breakdown": {status.value: 0 for status in VersionStatus},
            "tools_with_multiple_versions": 0,
            "deprecated_tools": []
        }
        
        for tool_name, versions in self._tool_versions.items():
            if len(versions) > 1:
                stats["tools_with_multiple_versions"] += 1
            
            for version_info in versions:
                stats["status_breakdown"][version_info.status.value] += 1
                
                if version_info.status == VersionStatus.DEPRECATED:
                    stats["deprecated_tools"].append({
                        "tool": tool_name,
                        "version": version_info.version,
                        "end_of_life": version_info.end_of_life_date
                    })
        
        return stats


# Global version manager instance
version_manager = ToolVersionManager()


def check_tool_version(tool_name: str, version: str) -> None:
    """Check tool version and issue deprecation warnings if needed."""
    warning_message = version_manager.check_deprecation(tool_name, version)
    if warning_message:
        warnings.warn(warning_message, DeprecationWarning, stacklevel=3)


def register_tool_version(tool_name: str, version: str, status: VersionStatus = VersionStatus.ACTIVE,
                         migration_notes: str = "", breaking_changes: List[str] = None,
                         deprecation_date: Optional[datetime] = None,
                         end_of_life_date: Optional[datetime] = None) -> None:
    """
    Register a tool version with the version manager.
    
    Args:
        tool_name: Name of the tool
        version: Semantic version string
        status: Version status
        migration_notes: Notes for migrating to/from this version
        breaking_changes: List of breaking changes in this version
        deprecation_date: When this version was/will be deprecated
        end_of_life_date: When this version reaches end of life
    """
    version_info = VersionInfo(
        version=version,
        status=status,
        release_date=datetime.now(),
        deprecation_date=deprecation_date,
        end_of_life_date=end_of_life_date,
        migration_notes=migration_notes,
        breaking_changes=breaking_changes or [],
        compatibility_notes=""
    )
    
    version_manager.register_version(tool_name, version_info)


def get_tool_version_info(tool_name: str) -> Dict[str, Any]:
    """Get comprehensive version information for a tool."""
    active_version = version_manager.get_active_version(tool_name)
    all_versions = version_manager.get_all_versions(tool_name)
    
    return {
        "tool_name": tool_name,
        "active_version": active_version,
        "all_versions": [
            {
                "version": v.version,
                "status": v.status.value,
                "release_date": v.release_date.isoformat() if v.release_date else None,
                "deprecation_date": v.deprecation_date.isoformat() if v.deprecation_date else None,
                "end_of_life_date": v.end_of_life_date.isoformat() if v.end_of_life_date else None,
                "migration_notes": v.migration_notes,
                "breaking_changes": v.breaking_changes
            }
            for v in all_versions
        ]
    }