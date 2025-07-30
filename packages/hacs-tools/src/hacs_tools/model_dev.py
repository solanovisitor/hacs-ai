"""
HACS Resource Development Utilities

Advanced tools for healthcare resource composition, stacking, and development workflows.
These utilities enable sophisticated resource manipulation and creation patterns.

DEPRECATED: This module has been reorganized into domain-specific modules.
Please use the following imports instead:

    from hacs_tools.domains.development_tools import (
        create_resource_stack,
        create_clinical_template,
        optimize_resource_for_llm
    )

All "Model" terminology has been updated to "Resource" to reflect healthcare domain focus.
"""

# Import the new tools from development_tools domain for backwards compatibility
from .domains.development_tools import (
    create_resource_stack,
    create_clinical_template, 
    optimize_resource_for_llm,
)

# Backwards compatibility aliases
create_model_stack = create_resource_stack
create_clinical_template = create_clinical_template
optimize_model_for_llm = optimize_resource_for_llm

__all__ = [
    # New resource-based tools
    "create_resource_stack",
    "create_clinical_template", 
    "optimize_resource_for_llm",
    
    # Backwards compatibility aliases
    "create_model_stack",
    "optimize_model_for_llm",
]