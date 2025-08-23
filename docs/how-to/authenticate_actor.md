# Authenticate an Actor with permissions

This guide shows how to create and validate an access token with role-based permissions.

```python
# Prereq (demo secret): export HACS_JWT_SECRET="this_is_a_demo_secret_key_with_length_over_32_chars________"
from hacs_auth.auth_manager import AuthManager
from hacs_auth.decorators import require_permission

am = AuthManager()
# Physician with read/write to patient
token = am.create_access_token(
    user_id="dr_chen",
    role="physician",
    permissions=["patient:read", "patient:write"],
    organization="General Hospital",
)
print("token_prefix:", token[:24])

@require_permission("patient:read")
def get_patient(patient_id: str, **kwargs):
    return {"id": patient_id, "status": "ok"}

print(get_patient("patient-123", token=token))
```

```
token_prefix: eyJhbGciOiJIUzI1NiIsInR5
{'id': 'patient-123', 'status': 'ok'}
```

## Verify token and inspect claims

```python
from hacs_auth.auth_manager import AuthError

# Decode and verify token
claims = am.verify_token(token)

print("User:", claims.user_id)
print("Role:", claims.role)
print("Permissions:", claims.permissions)
print("Org:", claims.organization)
print("Issued:", claims.issued_at)
print("Expires:", claims.expires_at)
print("TTL (s):", am.get_token_ttl(claims))
print("Expired?", am.is_token_expired(claims))
```

```
User: dr_chen
Role: physician
Permissions: ['patient:read', 'patient:write']
Org: General Hospital
Issued: 2025-08-19 19:07:46.184696+00:00
Expires: 2025-08-19 19:22:46.184696+00:00
TTL (s): 899
Expired? False
```

## Permission checks (exact, wildcard, admin)

```python
# Exact permission
print("Has patient:read?", am.has_permission(claims, "patient:read"))

# Wildcard permission example (admin:* overrides everything)
admin_token = am.create_access_token(
    user_id="sec_admin",
    role="admin",
    permissions=["admin:*"],
    organization="General Hospital",
)
admin_claims = am.verify_token(admin_token)

print("Admin has patient:write?", am.has_permission(admin_claims, "patient:write"))

# Enforce required permission (raises AuthError if missing)
try:
    am.require_permission(claims, "patient:delete")
    print("Delete allowed (unexpected)")
except AuthError as e:
    print("Delete denied:", e.message)
```

```
Has patient:read? True
Admin has patient:write? True
Delete denied: Permission denied: patient:delete required
```

## Security level validation

```python
# Token created above has default security_level="medium"
print("Meets 'low'?", am.validate_security_level(claims, "low"))
print("Meets 'high'?", am.validate_security_level(claims, "high"))
```

```
Meets 'low'? True
Meets 'high'? False
```

## Refresh token flow

```python
# Issue and verify a refresh token
refresh = am.create_refresh_token(user_id=claims.user_id)
print("refresh_prefix:", refresh[:24])

user_from_refresh = am.verify_refresh_token(refresh)
print("user_from_refresh:", user_from_refresh)

# Mint a new access token using refresh identity
new_token = am.create_access_token(
    user_id=user_from_refresh,
    role=claims.role,
    permissions=claims.permissions,
    organization=claims.organization,
)
print("new_token_prefix:", new_token[:24])
```

```
refresh_prefix: eyJhbGciOiJIUzI1NiIsInR5
user_from_refresh: dr_chen
new_token_prefix: eyJhbGciOiJIUzI1NiIsInR5
```

## Decorators for write operations

```python
@require_permission("patient:write")
def update_patient(patient_id: str, payload: dict, **kwargs):
    return {"id": patient_id, "updated": True, "payload_keys": sorted(payload.keys())}

print(update_patient("patient-123", {"allergies": ["penicillin"]}, token=token))
```

```
{'id': 'patient-123', 'updated': True, 'payload_keys': ['allergies']}
```

## Tips

- Use strong secrets; set `HACS_JWT_SECRET` to a 32+ char value. In production, HTTPS and MFA are enforced via `AuthConfig`.
- Default access token expiry is 15 min; adjust via `HACS_TOKEN_EXPIRE_MINUTES` (min 5, max 60).
- Use `admin:*` sparingly; prefer fine-grained permissions like `patient:read` and `patient:write`.

## Next steps

- Connect to a database and persist resources: see [Connect to a database](connect_postgres.md)
- Validate models and structure: see [Validate HACS Models](validate_hacs_models.md)
- Visualize resources and outputs: see [Visualize Resources](visualize_resources.md)
