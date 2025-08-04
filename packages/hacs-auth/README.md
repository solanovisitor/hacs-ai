# HACS Authentication

Authentication and authorization components for HACS (Healthcare Agent Communication Standard) providing JWT token management, role-based access control, and comprehensive audit logging.

## Features

- **JWT Token Management**: Healthcare-specific claims with organization context
- **Role-Based Access Control**: 13+ healthcare roles with smart permissions
- **Session Management**: Secure session handling with activity tracking  
- **Audit Logging**: HIPAA-compliant access tracking and compliance reports
- **Healthcare Security**: Security levels, PHI tracking, consent management
- **AI Agent Integration**: Simplified APIs for intelligent healthcare agents

## Installation

```bash
pip install hacs-auth
```

## Quick Start

```python
from hacs_auth import AuthManager, Actor, ActorRole, require_auth

# JWT Authentication
auth_manager = AuthManager()
token = auth_manager.create_access_token(
    user_id="physician-123",
    role="physician", 
    permissions=["read:patient", "write:observation"],
    organization="Mayo Clinic"
)

# Actor Management
actor = Actor(
    name="Dr. Sarah Johnson",
    role=ActorRole.PHYSICIAN,
    organization="Mayo Clinic"
)

# Function Protection
@require_auth(permission="read:patient")
def get_patient_data(patient_id: str, **kwargs):
    token_data = kwargs["token_data"]
    return f"Patient data for {patient_id}"
```

## License

MIT License - see LICENSE file for details.