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
