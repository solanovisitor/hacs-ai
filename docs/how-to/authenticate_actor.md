# Configure Actor Context for HACS Tools

This guide shows how to create and configure an Actor with role-based permissions for HACS tools.

```python
from hacs_models import Actor
from hacs_core.config import get_current_actor, configure_hacs

# Create physician with read/write permissions
physician = Actor(
    name="Dr. Chen",
    role="physician",
    permissions=["patient:read", "patient:write"]
)

# Configure HACS with this actor
configure_hacs(current_actor=physician)

# Verify the current actor
current = get_current_actor()
print("Actor configured:")
print(f"  Name: {current.name}")
print(f"  Role: {current.role}")
print(f"  Permissions: {current.permissions}")
```

**Output:**
```
Actor configured:
  Name: Dr. Chen
  Role: physician
  Permissions: ['patient:read', 'patient:write']
```

## Check permissions and access

```python
# Check specific permissions
print("Permission checks:")
print(f"  Has patient:read: {'patient:read' in current.permissions}")
print(f"  Has patient:write: {'patient:write' in current.permissions}")
print(f"  Has admin permissions: {'admin:*' in current.permissions}")

# Show how tools access the current actor
from hacs_core.config import get_settings
settings = get_settings()
print(f"\nTools access:")
print(f"  Current actor in settings: {settings.current_actor.name if settings.current_actor else 'None'}")
print(f"  Tools use config.current_actor for permissions")
```

**Output:**
```
Permission checks:
  Has patient:read: True
  Has patient:write: True
  Has admin permissions: False

Tools access:
  Current actor in settings: Dr. Chen
  Tools use config.current_actor for permissions
```

## Admin actor with wildcard permissions

```python
# Create admin actor with wildcard permissions
admin = Actor(
    name="System Admin",
    role="admin",
    permissions=["admin:*"]  # Wildcard grants all permissions
)

configure_hacs(current_actor=admin)
admin_current = get_current_actor()

print("Admin actor:")
print(f"  Name: {admin_current.name}")
print(f"  Role: {admin_current.role}")
print(f"  Has wildcard: {'admin:*' in admin_current.permissions}")

# Test permission enforcement
physician_perms = ["patient:read", "patient:write"]
print(f"\nPermission test:")
print(f"  Physician can delete: {'patient:delete' in physician_perms}")
print(f"  Admin can delete: {'admin:*' in admin_current.permissions}")
```

**Output:**
```
Admin actor:
  Name: System Admin
  Role: admin
  Has wildcard: True

Permission test:
  Physician can delete: False
  Admin can delete: True
```

## Using actors with HACS tools

```python
from hacs_utils.integrations.common.tool_loader import set_injected_params

# Set up tool injection with configured actor
settings = get_settings()
set_injected_params({'config': settings})

print("Tool integration:")
print(f"  Actor in config: {settings.current_actor.name}")
print(f"  Actor role: {settings.current_actor.role}")
print(f"  Tools will use this actor for permissions")

# Example: Tools automatically use the configured actor
from hacs_tools.domains.modeling import pin_resource

result = pin_resource("Patient", {
    "full_name": "Test Patient",
    "birth_date": "1990-01-01",
    "gender": "female"
})

print(f"\nTool execution:")
print(f"  Result: {result.success}")
print(f"  Used actor: {settings.current_actor.name} (automatically)")
```

**Output:**
```
Tool integration:
  Actor in config: Dr. Chen
  Actor role: physician
  Tools will use this actor for permissions

Tool execution:
  Result: True
  Used actor: Dr. Chen (automatically)
```

## Tips

- Use specific permissions like `patient:read` and `patient:write` for precise access control
- Use `admin:*` sparingly; prefer fine-grained permissions for security
- Configure actors once and let tools access them automatically via `config.current_actor`
- All HACS tools support automatic actor injection for consistent permission enforcement

## Next steps

- Connect to a database and persist resources: see [Connect to a database](connect_postgres.md)
- Use HACS tools with configured actors: see [HACS Tools Reference](../hacs-tools.md)
- Visualize resources and outputs: see [Visualize Resources](visualize_resources.md)
