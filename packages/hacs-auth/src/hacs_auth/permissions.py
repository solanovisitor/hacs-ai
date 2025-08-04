"""
Permission management system for HACS authentication.

This module provides comprehensive permission management with healthcare-specific
roles, resources, and actions. Designed for flexibility and security in
healthcare AI agent systems.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field

from .actor import ActorRole


class ResourceType(str, Enum):
    """Healthcare resource types for permission management."""
    
    # Core FHIR resources
    PATIENT = "patient"
    OBSERVATION = "observation"
    ENCOUNTER = "encounter"  
    CONDITION = "condition"
    MEDICATION = "medication"
    MEDICATION_REQUEST = "medication_request"
    PROCEDURE = "procedure"
    GOAL = "goal"
    
    # AI-specific resources
    MEMORY = "memory"
    AGENT_MESSAGE = "agent_message"
    WORKFLOW = "workflow"
    
    # System resources
    REGISTRY = "registry"
    AUDIT = "audit"
    SYSTEM = "system"
    CONFIG = "config"
    
    # Special resources
    OWN_DATA = "own_data"  # Patient's own data
    ALL = "*"  # All resources


class ActionType(str, Enum):
    """Action types for permission management."""
    
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    AUDIT = "audit"
    EXECUTE = "execute"
    APPROVE = "approve"
    DENY = "deny"
    ALL = "*"  # All actions


class Permission(BaseModel):
    """
    Represents a single permission with action and resource.
    
    Permissions follow the format: action:resource
    Examples: "read:patient", "write:observation", "admin:*"
    """
    
    action: ActionType = Field(..., description="Action type (read/write/delete/admin/etc)")
    resource: ResourceType = Field(..., description="Resource type or '*' for all")
    conditions: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional conditions for permission (e.g., ownership, context)"
    )
    
    def __str__(self) -> str:
        """String representation in action:resource format."""
        return f"{self.action}:{self.resource}"
    
    def matches(self, required_permission: str) -> bool:
        """
        Check if this permission matches a required permission string.
        
        Args:
            required_permission: Permission string to check (e.g., "read:patient")
            
        Returns:
            True if this permission covers the required permission
        """
        if ":" not in required_permission:
            return False
            
        req_action, req_resource = required_permission.split(":", 1)
        
        # Check action match
        action_match = (
            self.action == ActionType.ALL or
            self.action == req_action or
            (self.action == ActionType.ADMIN and req_action in ["read", "write", "delete"])
        )
        
        if not action_match:
            return False
            
        # Check resource match
        resource_match = (
            self.resource == ResourceType.ALL or
            self.resource == req_resource
        )
        
        return resource_match


class PermissionSchema(BaseModel):
    """
    Schema for managing sets of permissions with validation.
    """
    
    permissions: List[Permission] = Field(
        default_factory=list,
        description="List of permissions"
    )
    
    def add_permission(self, action: str, resource: str, conditions: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a permission to the schema.
        
        Args:
            action: Action type
            resource: Resource type
            conditions: Optional conditions
        """
        permission = Permission(
            action=ActionType(action),
            resource=ResourceType(resource),
            conditions=conditions
        )
        
        # Avoid duplicates
        if permission not in self.permissions:
            self.permissions.append(permission)
    
    def remove_permission(self, action: str, resource: str) -> bool:
        """
        Remove a permission from the schema.
        
        Args:
            action: Action type
            resource: Resource type
            
        Returns:
            True if permission was removed
        """
        for perm in self.permissions:
            if perm.action == action and perm.resource == resource:
                self.permissions.remove(perm)
                return True
        return False
    
    def has_permission(self, required_permission: str) -> bool:
        """
        Check if schema contains required permission.
        
        Args:
            required_permission: Permission string to check
            
        Returns:
            True if permission is granted
        """
        return any(perm.matches(required_permission) for perm in self.permissions)
    
    def to_string_list(self) -> List[str]:
        """Convert permissions to list of strings."""
        return [str(perm) for perm in self.permissions]
    
    @classmethod
    def from_string_list(cls, permission_strings: List[str]) -> "PermissionSchema":
        """
        Create schema from list of permission strings.
        
        Args:
            permission_strings: List of "action:resource" strings
            
        Returns:
            PermissionSchema instance
        """
        schema = cls()
        
        for perm_str in permission_strings:
            if ":" not in perm_str:
                continue
                
            action, resource = perm_str.split(":", 1)
            try:
                schema.add_permission(action, resource)
            except ValueError:
                # Skip invalid permissions
                continue
                
        return schema


class PermissionManager:
    """
    Manages permissions for healthcare systems with role-based templates
    and dynamic permission management.
    """
    
    def __init__(self):
        """Initialize permission manager with role templates."""
        self._role_templates = self._create_role_templates()
    
    def _create_role_templates(self) -> Dict[ActorRole, PermissionSchema]:
        """Create permission templates for each healthcare role."""
        templates = {}
        
        # Physician permissions
        physician_permissions = [
            "read:patient", "write:patient", "delete:patient",
            "read:observation", "write:observation", "delete:observation",
            "read:encounter", "write:encounter", "delete:encounter",
            "read:condition", "write:condition", "delete:condition",
            "read:medication", "write:medication",
            "read:medication_request", "write:medication_request",
            "read:procedure", "write:procedure", "delete:procedure",
            "read:goal", "write:goal", "delete:goal",
            "read:memory", "write:memory",
        ]
        templates[ActorRole.PHYSICIAN] = PermissionSchema.from_string_list(physician_permissions)
        
        # Nurse permissions  
        nurse_permissions = [
            "read:patient", "write:patient",
            "read:observation", "write:observation",
            "read:encounter", "write:encounter",
            "read:condition",
            "read:medication", "write:medication",
            "read:medication_request",
            "read:procedure",
            "read:goal", "write:goal",
        ]
        templates[ActorRole.NURSE] = PermissionSchema.from_string_list(nurse_permissions)
        
        # Pharmacist permissions
        pharmacist_permissions = [
            "read:patient",
            "read:observation", 
            "read:condition",
            "read:medication", "write:medication",
            "read:medication_request", "write:medication_request",
        ]
        templates[ActorRole.PHARMACIST] = PermissionSchema.from_string_list(pharmacist_permissions)
        
        # Therapist permissions
        therapist_permissions = [
            "read:patient", "write:patient",
            "read:observation", "write:observation",
            "read:encounter", "write:encounter", 
            "read:condition",
            "read:procedure", "write:procedure",
            "read:goal", "write:goal",
        ]
        templates[ActorRole.THERAPIST] = PermissionSchema.from_string_list(therapist_permissions)
        
        # Technician permissions
        technician_permissions = [
            "read:patient",
            "read:observation", "write:observation",
            "read:procedure", "write:procedure",
        ]
        templates[ActorRole.TECHNICIAN] = PermissionSchema.from_string_list(technician_permissions)
        
        # Administrator permissions
        admin_permissions = [
            "admin:*", "audit:*", "read:*", "write:*", "delete:*"
        ]
        templates[ActorRole.ADMINISTRATOR] = PermissionSchema.from_string_list(admin_permissions)
        templates[ActorRole.ADMIN] = PermissionSchema.from_string_list(admin_permissions)
        
        # Patient permissions - own data only
        patient_permissions = [
            "read:own_data", "write:own_data"
        ]
        templates[ActorRole.PATIENT] = PermissionSchema.from_string_list(patient_permissions)
        
        # Caregiver permissions
        caregiver_permissions = [
            "read:patient", "read:observation", "read:encounter", "read:condition"
        ]
        templates[ActorRole.CAREGIVER] = PermissionSchema.from_string_list(caregiver_permissions)
        
        # AI Agent permissions
        agent_permissions = [
            "read:patient", "write:patient",
            "read:observation", "write:observation",
            "read:encounter", "write:encounter",
            "read:condition", "write:condition",
            "read:memory", "write:memory", "delete:memory",
            "read:agent_message", "write:agent_message",
            "read:workflow", "execute:workflow",
        ]
        templates[ActorRole.AGENT] = PermissionSchema.from_string_list(agent_permissions)
        
        # System permissions
        system_permissions = [
            "admin:*", "audit:*", "read:*", "write:*", "delete:*", "execute:*"
        ]
        templates[ActorRole.SYSTEM] = PermissionSchema.from_string_list(system_permissions)
        
        # Researcher permissions - read only with audit
        researcher_permissions = [
            "read:patient", "read:observation", "read:encounter", "read:condition",
            "audit:research"
        ]
        templates[ActorRole.RESEARCHER] = PermissionSchema.from_string_list(researcher_permissions)
        
        # Auditor permissions - read and audit everything
        auditor_permissions = [
            "read:*", "audit:*"
        ]
        templates[ActorRole.AUDITOR] = PermissionSchema.from_string_list(auditor_permissions)
        
        return templates
    
    def get_role_permissions(self, role: ActorRole) -> PermissionSchema:
        """
        Get default permissions for a role.
        
        Args:
            role: Actor role
            
        Returns:
            PermissionSchema with role's default permissions
        """
        return self._role_templates.get(role, PermissionSchema())
    
    def create_custom_permissions(self, permissions: List[str]) -> PermissionSchema:
        """
        Create custom permission schema from string list.
        
        Args:
            permissions: List of permission strings
            
        Returns:
            PermissionSchema instance
        """
        return PermissionSchema.from_string_list(permissions)
    
    def merge_permissions(self, *schemas: PermissionSchema) -> PermissionSchema:
        """
        Merge multiple permission schemas.
        
        Args:
            *schemas: Permission schemas to merge
            
        Returns:
            Merged permission schema
        """
        merged = PermissionSchema()
        
        for schema in schemas:
            for perm in schema.permissions:
                if perm not in merged.permissions:
                    merged.permissions.append(perm)
        
        return merged
    
    def validate_permission_string(self, permission: str) -> bool:
        """
        Validate permission string format.
        
        Args:
            permission: Permission string to validate
            
        Returns:
            True if permission is valid
        """
        if ":" not in permission:
            return False
            
        action, resource = permission.split(":", 1)
        
        try:
            ActionType(action)
            ResourceType(resource)
            return True
        except ValueError:
            return False
    
    def get_effective_permissions(
        self,
        role: ActorRole,
        additional_permissions: Optional[List[str]] = None,
        conditions: Optional[Dict[str, Any]] = None
    ) -> PermissionSchema:
        """
        Get effective permissions for a role with additional permissions.
        
        Args:
            role: Base actor role
            additional_permissions: Additional permissions to grant
            conditions: Conditions that might affect permissions
            
        Returns:
            Effective permission schema
        """
        # Start with role permissions
        base_permissions = self.get_role_permissions(role)
        
        # Add additional permissions if provided
        if additional_permissions:
            additional_schema = self.create_custom_permissions(additional_permissions)
            return self.merge_permissions(base_permissions, additional_schema)
        
        return base_permissions
    
    def check_permission_hierarchy(self, granter_role: ActorRole, permission: str) -> bool:
        """
        Check if a role can grant a specific permission (permission hierarchy).
        
        Args:
            granter_role: Role of the actor granting permission
            permission: Permission being granted
            
        Returns:
            True if role can grant this permission
        """
        granter_permissions = self.get_role_permissions(granter_role)
        
        # Admin roles can grant any permission
        if granter_permissions.has_permission("admin:*"):
            return True
        
        # Can only grant permissions that the granter has
        return granter_permissions.has_permission(permission)
    
    def get_resource_permissions(self, resource: ResourceType) -> Set[str]:
        """
        Get all possible permissions for a resource type.
        
        Args:
            resource: Resource type
            
        Returns:
            Set of possible permission strings for the resource
        """
        actions = [action.value for action in ActionType if action != ActionType.ALL]
        return {f"{action}:{resource.value}" for action in actions}
    
    def audit_permission_changes(
        self,
        actor_id: str,
        old_permissions: List[str],
        new_permissions: List[str],
        changed_by: str
    ) -> Dict[str, Any]:
        """
        Create audit record for permission changes.
        
        Args:
            actor_id: ID of actor whose permissions changed
            old_permissions: Previous permissions
            new_permissions: New permissions
            changed_by: ID of actor who made the change
            
        Returns:
            Audit record
        """
        old_set = set(old_permissions)
        new_set = set(new_permissions)
        
        added = new_set - old_set
        removed = old_set - new_set
        
        return {
            "event": "permission_change",
            "actor_id": actor_id,
            "changed_by": changed_by,
            "timestamp": None,  # Set by audit system
            "changes": {
                "added": list(added),
                "removed": list(removed),
                "old_permissions": old_permissions,
                "new_permissions": new_permissions
            }
        }