"""
HACS CLI - Healthcare Agent Communication Standard Command Line Interface

Entry point for the HACS CLI application with Typer and Rich for enhanced UX.
"""

from .__main__ import app, main

__version__ = "0.1.0"

# Explicit re-exports
__all__ = ["app", "main"]
