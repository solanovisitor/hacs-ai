## Creating a private Registry

This guide shows how an organization can create a private registry of custom resources using decorators and a migration step. We will:

- Register a composed, organization-specific resource (PatientSnapshot)
- Discover and import plugin modules
- Persist the catalog (resources and tools) to the database

### Prerequisites

- Environment: Python 3.11+ with `uv`
- Set `OPENAI_API_KEY` and database credentials in `.env`
- Packages installed (editable): `hacs-models`, `hacs-registry`, `hacs-persistence`, `hacs-utils`, `hacs-core`, `hacs-tools`

### 1) Define and register an organization-specific resource

Create a module for your private package, e.g. `org_acme/resources.py`:

```python
from pydantic import BaseModel, Field
from typing import Optional

from hacs_models import BaseResource, Patient, Observation
from hacs_registry import register_resource, ResourceCategory, ResourceStatus


@register_resource(
    name="PatientSnapshot",
    version="1.0.0",
    description="Organization-specific snapshot composed from Patient and key Observations",
    category=ResourceCategory.CLINICAL,
    status=ResourceStatus.PUBLISHED,
    tags=["org:acme", "snapshot"],
)
class PatientSnapshot(BaseResource):
    """A compact view combining demographics and vitals."""

    resource_type: str = Field(default="PatientSnapshot")

    # Derived fields from Patient
    patient_id: str
    full_name: str
    gender: Optional[str] = None
    birth_date: Optional[str] = None

    # Composed fields from recent Observations
    latest_systolic_bp: Optional[float] = None
    latest_diastolic_bp: Optional[float] = None
    latest_heart_rate: Optional[float] = None
    latest_weight_kg: Optional[float] = None

    # Organization-specific extensions
    risk_band: Optional[str] = Field(default=None, description="Internal risk band A/B/C/D")

    @classmethod
    def from_resources(
        cls,
        patient: Patient,
        observations: list[Observation],
        *,
        risk_band: Optional[str] = None,
    ) -> "PatientSnapshot":
        # pick vitals
        def get_obs(code: str) -> Optional[Observation]:
            for obs in observations:
                if getattr(obs, "code", "") == code:
                    return obs
            return None

        sbp = get_obs("systolic-bp")
        dbp = get_obs("diastolic-bp")
        hr = get_obs("heart-rate")
        wt = get_obs("weight")

        return cls(
            patient_id=patient.id,
            full_name=getattr(patient, "full_name", None) or f"{patient.name.given} {patient.name.family}",
            gender=getattr(patient, "gender", None),
            birth_date=getattr(patient, "birth_date", None),
            latest_systolic_bp=getattr(sbp, "value", None),
            latest_diastolic_bp=getattr(dbp, "value", None),
            latest_heart_rate=getattr(hr, "value", None),
            latest_weight_kg=getattr(wt, "value", None),
            risk_band=risk_band,
        )
```

Notes:
- The `@register_resource` decorator enqueues registration for a migration step; it does not write to DB immediately.
- The classmethod `from_resources` shows composing variables from existing resources and extending with custom fields.

### 2) Discover and import your private module

Export your module path through `HACS_PLUGIN_PACKAGES` to auto-import it during migration:

```bash
uv run --env-file .env -- bash -lc 'export HACS_PLUGIN_PACKAGES="org_acme.resources"; python - <<PY
import asyncio, os
from hacs_registry import register_catalog

async def main():
    report = await register_catalog(persist=False)
    print("registered_resources:", report.get("resources"))
    print("discovered_tools:", report.get("tools"))

asyncio.run(main())
PY'
```

Expected output (counts will vary):

```text
registered_resources: 1
discovered_tools: 75
```

### 3) Persist your private catalog to the database

To persist to PostgreSQL, configure the registry persistence integration using `hacs-persistence`:

```python
import asyncio
from dotenv import load_dotenv
load_dotenv()

from hacs_persistence.adapter import create_postgres_adapter
from hacs_registry import get_registry_integration, register_catalog

async def main():
    adapter = await create_postgres_adapter()
    integ = get_registry_integration()
    integ.configure_persistence(adapter)

    report = await register_catalog(persist=True)
    print("persisted:", report.get("persisted"))

asyncio.run(main())
```

Example output:

```text
persisted: True
```

### 4) Use your private resource in code

After migration, the resource is available via the registry:

```python
from hacs_registry import get_global_registry

reg = get_global_registry()
snapshots = reg.find_resources(name_pattern="PatientSnapshot")
print(len(snapshots) > 0)
```

### Next steps

- Use `PatientSnapshot.from_resources(patient, observations, risk_band="B")` in your pipelines.
- Register additional private resources with `@register_resource` and persist them with `register_catalog`.
- Combine with “Persist Resources” to save instances and “Use & Register Tools” to expose operations over snapshots.


