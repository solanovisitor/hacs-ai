# HACS Models

**Pure Healthcare Data Models for AI Agent Systems**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Type Checked](https://img.shields.io/badge/type--checked-mypy-blue.svg)](http://mypy-lang.org/)
[![Code Quality](https://img.shields.io/badge/code--quality-ruff-blue.svg)](https://github.com/astral-sh/ruff)
[![FHIR Compliant](https://img.shields.io/badge/FHIR-R4%2FR5-green.svg)](https://hl7.org/fhir/)

## Overview

`hacs-models` provides pure, type-safe Pydantic data models for healthcare applications. These models are designed for AI agent communication and are fully compliant with FHIR R4/R5 standards.

## Design Principles

- **Pure Data Models**: No business logic, just data structures
- **Type Safety**: Full type annotations with mypy strict mode
- **FHIR Compliance**: Adherent to healthcare data standards
- **Zero Dependencies**: Minimal dependency footprint (only Pydantic)
- **Immutable Design**: Designed for functional programming patterns
- **AI-Optimized**: Structured for AI agent communication

## Features

### Core Healthcare Models
- `Patient` - Patient demographics and identifiers
- `Observation` - Clinical observations and measurements  
- `Encounter` - Healthcare encounters and visits
- `Condition` - Medical conditions and diagnoses
- `Medication` - Medication information
- `MedicationRequest` - Medication prescriptions
- `Procedure` - Medical procedures
- `Goal` - Care goals and objectives

### Specialized Models
- `MemoryBlock` - AI agent memory structures
- `AgentMessage` - Inter-agent communication
- `ResourceBundle` - FHIR resource collections
- `WorkflowDefinition` - Clinical workflow definitions

### Base Classes
- `BaseResource` - Foundation for all healthcare resources
- `DomainResource` - Base for domain-specific resources
- `BackboneElement` - Reusable data structures

## Installation

```bash
# Install from PyPI (when published)
pip install hacs-models

# Install in development mode
uv add -e packages/hacs-models
```

## Quick Start

```python
from hacs_models import Patient, Observation
from datetime import date

# Create a patient
patient = Patient(
    id="patient-001",
    full_name="Jane Doe",
    birth_date=date(1990, 1, 15),
    gender="female"
)

# Create an observation
observation = Observation(
    id="obs-001",
    subject_reference=f"Patient/{patient.id}",
    code="85354-9",  # Blood pressure
    value_quantity={"value": 120, "unit": "mmHg"}
)

# Models are immutable and type-safe
print(f"Patient: {patient.full_name}")
print(f"Blood Pressure: {observation.value_quantity}")
```

## Architecture

```
hacs-models/
├── base_resource.py     # BaseResource, DomainResource
├── patient.py          # Patient model
├── observation.py      # Observation model  
├── encounter.py        # Encounter model
├── condition.py        # Condition model
├── medication.py       # Medication models
├── procedure.py        # Procedure model
├── goal.py            # Goal model
├── memory.py          # AI memory models
├── workflow.py        # Workflow models
└── types.py           # Common types and enums
```

## Development

```bash
# Run tests
uv run pytest

# Type checking  
uv run mypy src/hacs_models

# Code formatting
uv run ruff format src/hacs_models

# Linting
uv run ruff check src/hacs_models
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new models
4. Ensure 100% type coverage
5. Submit a pull request

## License

MIT License - see LICENSE file for details.