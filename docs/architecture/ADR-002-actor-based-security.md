# ADR-002: Actor-Based Security Architecture

## Status
**Accepted** - Implemented in hacs-auth package

## Context
Healthcare AI systems require robust security that aligns with healthcare compliance standards (HIPAA, GDPR) while supporting both human users and AI agents. Traditional user-based authentication doesn't adequately address the needs of AI agents that may operate with different permission sets and audit requirements.

## Decision
We will implement an **Actor-Based Security Architecture** where both human users and AI agents are represented as "Actors" with role-based permissions,audit trails, and healthcare-specific security features.

## Architecture Overview

### Core Components

#### Actor Model
```python
class Actor(BaseResource):
    """Represents any entity (human or AI) that can perform actions in the system."""
    name: str
    role: ActorRole  # PHYSICIAN, NURSE, AGENT, PATIENT, etc.
    permissions: List[str]  # Auto-generated based on role
    organization: str
    session_id: Optional[str]
    audit_context: Dict[str, Any]
```

#### Role-Based Permissions
```python
class ActorRole(str, Enum):
    PHYSICIAN = "physician"     # Full clinical access
    NURSE = "nurse"            # Clinical care access
    AGENT = "agent"            # AI agent with specific permissions
    PATIENT = "patient"        # Own data access only
    ADMIN = "admin"            # System administration
    AUDITOR = "auditor"        # Read-only audit access
```

#### Permission Schema
```python
# Granular permissions following "action:resource" pattern
PHYSICIAN_PERMISSIONS = [
    "read:patient", "write:patient", "delete:patient",
    "read:observation", "write:observation",
    "read:encounter", "write:encounter",
    "execute:clinical_workflow"
]

AGENT_PERMISSIONS = [
    "read:patient", "write:observation",
    "execute:workflow", "read:memory", "write:memory"
]
```

## Key Design Decisions

### 1. Unified Actor Model
**Decision**: Use a single Actor model for both humans and AI agents rather than separate User/Agent models.

**Rationale**:
- Simplifies permission management
- Enables consistent audit trails
- Supports hybrid human-AI workflows
- Reduces code duplication

### 2. Role-Based Permission Generation
**Decision**: Auto-generate permissions based on roles with override capability.

**Rationale**:
- Reduces configuration errors
- Ensures compliance with healthcare standards
- Provides sensible defaults
- Allows customization when needed

### 3. Session-Based Context
**Decision**: Implementsession management with healthcare-specific features.

**Rationale**:
- Supports audit requirements
- Enables activity tracking
- Provides security controls (timeouts, IP tracking)
- Supports multi-factor authentication

### 4.Audit Trails
**Decision**: Log all actor activities with structured audit events.

**Rationale**:
- HIPAA compliance requirement
- Enables security monitoring
- Supports forensic analysis
- Provides operational insights

## Implementation Details

### Authentication Flow
```mermaid
sequenceDiagram
    participant Client
    participant AuthManager
    participant Actor
    participant SessionManager
    participant AuditLogger

    Client->>AuthManager: authenticate(credentials)
    AuthManager->>Actor: create/retrieve actor
    AuthManager->>SessionManager: create_session(actor)
    SessionManager->>AuditLogger: log_session_start
    AuthManager->>Client: return JWT token
```

### Permission Checking
```python
def require_permission(permission: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            actor = get_current_actor()
            if not actor.has_permission(permission):
                raise PermissionError(f"Actor {actor.name} lacks {permission}")
            return func(*args, **kwargs)
        return wrapper
    return decorator

@require_permission("read:patient")
def get_patient_data(patient_id: str) -> Patient:
    pass
```

### Healthcare-Specific Features

#### 1. Break-Glass Access
```python
class EmergencyAccess:
    def grant_emergency_access(self, actor: Actor, justification: str):
        # Grant temporary elevated permissions for emergency situations
        # Log extensively for audit compliance
        pass
```

#### 2. Data Access Logging
```python
def log_data_access(actor: Actor, resource_type: str, resource_id: str, action: str):
    audit_event = AuditEvent(
        actor_id=actor.id,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        timestamp=now(),
        ip_address=get_client_ip(),
        session_id=actor.session_id
    )
    audit_logger.log(audit_event)
```

#### 3. Patient Consent Management
```python
class ConsentManager:
    def check_patient_consent(self, patient_id: str, actor: Actor, purpose: str) -> bool:
        # Verify patient has consented to data access for this purpose
        pass
```

## Security Features

### 1. Multi-Factor Authentication
- Support for TOTP, SMS, hardware tokens
- Risk-based authentication triggers
- Device fingerprinting

### 2. Session Security
- Configurable session timeouts
- IP address change detection
- Concurrent session limits
- Session hijacking protection

### 3. Permission Hierarchy
- Role inheritance (Senior Physician > Physician > Resident)
- Delegation capabilities
- Temporary permission elevation
- Permission expiration

### 4. Audit and Compliance
-audit logs
- HIPAA audit trail requirements
- Automated compliance reporting
- Real-time security monitoring

## Healthcare Compliance

### HIPAA Compliance
- ✅ Access controls and user authentication
- ✅ Audit logs for all PHI access
- ✅ Automatic logoff after inactivity
- ✅ Unique user identification
- ✅ Emergency access procedures

### GDPR Compliance
- ✅ Data subject access rights
- ✅ Right to erasure implementation
- ✅ Consent management
- ✅ Data processing audit trails

## Performance Considerations

### 1. Permission Caching
- Cache role-based permissions
- Invalidate cache on permission changes
- Use Redis for distributed caching

### 2. Session Optimization
- Efficient session storage
- Background session cleanup
- Connection pooling for session data

### 3. Audit Log Performance
- Asynchronous audit logging
- Batch audit event processing
- Efficient log storage and retrieval

## Migration Strategy

### Phase 1: Core Implementation
- ✅ Basic Actor model
- ✅ Role-based permissions
- ✅ Session management
- ✅ Basic audit logging

### Phase 2: Healthcare Features
- ✅ Break-glass access
- ✅ Patient consent management
- ✅ Advanced audit features
- ✅ Compliance reporting

### Phase 3: Advanced Security
- Multi-factor authentication
- Advanced threat detection
- Automated compliance monitoring
- Integration with SIEM systems

## Consequences

### Positive
- **Compliance**: Meets healthcare regulatory requirements
- **Flexibility**: Supports both human and AI actors
- **Security**:security controls
- **Auditability**: Complete audit trails for compliance
- **Scalability**: Designed for enterprise healthcare systems

### Negative
- **Complexity**: More complex than simple user authentication
- **Performance**: Additional security checks impact performance
- **Storage**: Audit logs require significant storage
- **Maintenance**: Security features require ongoing maintenance

## Related Decisions
- [ADR-001: SOLID Principles Compliance](ADR-001-SOLID-principles-compliance.md)
- [ADR-003: Protocol-First Design](ADR-003-protocol-first-design.md)

## References
- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [Healthcare Security Best Practices](https://www.healthit.gov/topic/privacy-security-and-hipaa)

---
**Date**: 2025-08-04  
**Author**: HACS Security Team  
**Reviewers**: Security Review Board, Healthcare Compliance Team