# Clinical Consultation Template

## Basic Structure

```json
{
    "resourceType": "Consultation",
    "id": "unique-id",
    "status": "active",
    "subject": {
        "reference": "Patient/[id]"
    },
    "performer": {
        "reference": "Practitioner/[id]"
    },
    "date": "ISO8601 DateTime",
    "type": {
        "coding": [{
            "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
            "code": "CON",
            "display": "Consultation"
        }]
    },
    "reason": {
        "text": "Reason for consultation"
    },
    "findings": {
        "text": "Clinical findings"
    },
    "diagnosis": [{
        "condition": {
            "reference": "Condition/[id]"
        },
        "use": {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/diagnosis-role",
                "code": "DD",
                "display": "Differential Diagnosis"
            }]
        }
    }],
    "plan": {
        "text": "Treatment plan"
    }
}
```

## Usage Guidelines

1. Always include required fields
2. Use standard terminologies
3. Maintain referential integrity
4. Document all findings
5. Include proper metadata