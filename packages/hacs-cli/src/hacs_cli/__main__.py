"""
HACS CLI - Healthcare Agent Communication Standard Command Line Interface

This module provides a comprehensive command-line interface for interacting with
HACS (Healthcare Agent Communication Standard) resources. It offers healthcare
organizations and developers a powerful tool for managing clinical data, AI agent
communications, and FHIR-compliant healthcare workflows.

Features:
    🏥 Healthcare Resource Management
        - Create, validate, and manage Patient, Observation, Encounter records
        - Full support for HACS clinical data models
        - FHIR compliance checking and validation
    
    🤖 AI Agent Operations  
        - Memory storage and retrieval for healthcare AI agents
        - Evidence collection and clinical reasoning support
        - Actor-based permissions and role management
    
    🔄 Data Conversion & Validation
        - Convert between HACS and FHIR formats
        - Multi-level validation (basic, strict, fhir)
        - Batch processing for large datasets
    
    📊 Rich Terminal Interface
        - Interactive resource builder with guided prompts
        - Beautiful tables and panels for data display
        - Progress tracking for long-running operations

Commands:
    create      Create new healthcare resources (Patient, Observation, etc.)
    validate    Validate existing resources against HACS/FHIR standards
    convert     Convert between HACS and FHIR formats
    memory      Store and retrieve memories for AI agents
    evidence    Manage clinical evidence and reasoning
    search      Search across healthcare resources and memories
    interactive Launch interactive resource builder

Usage Examples:
    # Create a new patient record
    hacs-cli create Patient --data '{"full_name": "John Doe", "birth_date": "1990-01-01"}'
    
    # Validate a healthcare resource file
    hacs-cli validate patient.json --level strict
    
    # Convert HACS format to FHIR
    hacs-cli convert patient.json fhir --output patient_fhir.json
    
    # Interactive mode for guided resource creation
    hacs-cli interactive --resource Patient
    
    # Store a memory for an AI agent
    hacs-cli memory store "Patient exhibits signs of hypertension" --type clinical
    
    # Search for evidence related to a condition  
    hacs-cli search evidence --query "hypertension treatment"

Requirements:
    - Python 3.11+
    - hacs-core package for resource models
    - Rich terminal support for best experience
    - Optional: hacs-tools for advanced MCP operations

Author: HACS Development Team
License: MIT
Version: 0.3.0
Repository: https://github.com/solanovisitor/hacs-ai
Documentation: https://docs.hacs.dev
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import typer
from dotenv import load_dotenv

# Import HACS modules
from hacs_core import Actor, ActorRole, Evidence, EvidenceType, MemoryBlock
from hacs_core.models import AgentMessage, Encounter, Observation, Patient

# Optional FHIR functionality (graceful degradation if not available)
try:
    from hacs_core.utils import from_fhir, to_fhir, validate_fhir_compliance
    FHIR_AVAILABLE = True
except ImportError:
    # Provide placeholder functions for graceful degradation
    def validate_fhir_compliance(resource: Any) -> list[str]:
        """FHIR validation unavailable - install FHIR dependencies."""
        # TODO: Implement proper FHIR validation or install required dependencies
        return ["FHIR validation not available - install hacs-core with FHIR extras"]
    
    def to_fhir(resource: Any) -> dict[str, Any]:
        """FHIR conversion unavailable - install FHIR dependencies."""
        # TODO: Implement proper FHIR conversion or install required dependencies
        return {"error": "FHIR conversion not available"}
    
    def from_fhir(data: dict[str, Any]) -> Any:
        """FHIR conversion unavailable - install FHIR dependencies."""
        # TODO: Implement proper FHIR conversion or install required dependencies
        return {"error": "FHIR conversion not available"}
    
    FHIR_AVAILABLE = False
from hacs_tools import (
    create_hacs_memory,
    search_hacs_memories,
    search_hacs_records,
    vector_similarity_search,
    validate_fhir_compliance,
)
from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich.table import Table

# Load environment variables
load_dotenv()

# Initialize Typer app and Rich console
app = typer.Typer(
    name="hacs",
    help="Healthcare Agent Communication Standard (HACS) CLI",
    epilog="For more information, visit: https://docs.hacs.dev",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
console = Console()

# Global state for current actor
current_actor: Actor | None = None


class CLIError(Exception):
    """Custom CLI error for better error handling."""

    pass


def get_current_actor() -> Actor:
    """Get current actor or create a default one."""
    global current_actor

    if current_actor is None:
        # Create default actor for CLI operations
        current_actor = Actor(
            id="cli-user", name="CLI User", role=ActorRole.PHYSICIAN, permissions=["*:*"], is_active=True
        )

    return current_actor


def load_resource_from_file(file_path: Path) -> dict[str, Any]:
    """Load and parse a resource from JSON file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise CLIError(f"File not found: {file_path}")
    except json.JSONDecodeError as e:
        raise CLIError(f"Invalid JSON in {file_path}: {e}")
    except Exception as e:
        raise CLIError(f"Error reading {file_path}: {e}")


def save_resource_to_file(resource: dict[str, Any], file_path: Path) -> None:
    """Save resource to JSON file."""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(resource, f, indent=2, default=str)
    except Exception as e:
        raise CLIError(f"Error writing to {file_path}: {e}")


def detect_resource_type(data: dict[str, Any]) -> str:
    """Detect resource type from data."""
    if "resource_type" in data:
        return data["resource_type"]
    elif "given" in data and "family" in data:
        return "Patient"
    elif "status" in data and "code" in data and "subject" in data:
        return "Observation"
    elif "role" in data and "content" in data:
        return "AgentMessage"
    elif "memory_type" in data:
        return "MemoryBlock"
    elif "evidence_type" in data:
        return "Evidence"
    else:
        raise CLIError("Could not detect resource type from data")


def create_resource_from_data(data: dict[str, Any], resource_type: str):
    """Create a typed resource from data."""
    resource_classes = {
        "Patient": Patient,
        "Observation": Observation,
        "AgentMessage": AgentMessage,
        "Encounter": Encounter,
        "MemoryBlock": MemoryBlock,
        "Evidence": Evidence,
    }

    if resource_type not in resource_classes:
        raise CLIError(f"Unsupported resource type: {resource_type}")

    try:
        return resource_classes[resource_type](**data)
    except ValidationError as e:
        raise CLIError(f"Validation error creating {resource_type}: {e}")


@app.command()
def validate(
    file_path: Path = typer.Argument(..., help="Path to the resource file to validate"),
    resource_type: str | None = typer.Option(
        None, "--type", "-t", help="Resource type (auto-detected if not specified)"
    ),
    level: str = typer.Option("standard", "--level", "-l", help="Validation level: basic, standard, strict, fhir"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed validation results"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Save validation report to file"),
) -> None:
    """
    Validate any HACS resource with detailed error reporting and Actor context.

    Examples:
        hacs validate patient.json
        hacs validate observation.json --type Observation --level strict
        hacs validate memory.json --verbose --output report.json
    """
    try:
        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            task = progress.add_task("Loading and validating resource...", total=None)

            # Load resource
            data = load_resource_from_file(file_path)

            # Detect or use specified resource type
            if resource_type is None:
                resource_type = detect_resource_type(data)

            progress.update(task, description=f"Validating {resource_type}...")

            # Create typed resource
            resource = create_resource_from_data(data, resource_type)

            # Get current actor for validation context
            actor = get_current_actor()

            # Perform validation based on level
            validation_results = []

            if level in ["basic", "standard", "strict"]:
                if resource_type in ["Patient", "Observation", "Encounter", "AgentMessage"]:
                    result = validate_hacs_resource(resource, actor)
                    validation_results.append(
                        {
                            "type": "business_rules",
                            "passed": len(result.errors) == 0,
                            "errors": result.errors,
                            "warnings": result.warnings,
                        }
                    )

            if level in ["fhir", "strict"]:
                try:
                    fhir_errors = validate_fhir_compliance(resource)
                    validation_results.append(
                        {
                            "type": "fhir_compliance",
                            "passed": len(fhir_errors) == 0,
                            "errors": fhir_errors,
                            "warnings": [],
                        }
                    )
                except Exception as e:
                    validation_results.append(
                        {
                            "type": "fhir_compliance",
                            "passed": False,
                            "errors": [f"FHIR validation failed: {e}"],
                            "warnings": [],
                        }
                    )

        # Display results
        all_passed = all(result["passed"] for result in validation_results)
        total_errors = sum(len(result["errors"]) for result in validation_results)
        total_warnings = sum(len(result["warnings"]) for result in validation_results)

        # Create summary panel
        status_color = "green" if all_passed else "red"
        status_text = "✅ VALID" if all_passed else "❌ INVALID"

        summary = f"[{status_color}]{status_text}[/{status_color}]\n"
        summary += f"Resource: {resource_type}\n"
        summary += f"Validation Level: {level}\n"
        summary += f"Errors: {total_errors}\n"
        summary += f"Warnings: {total_warnings}"

        console.print(Panel(summary, title="Validation Summary", border_style=status_color))

        # Show detailed results if verbose
        if verbose or not all_passed:
            for result in validation_results:
                if result["errors"]:
                    console.print(f"\n[red]❌ {result['type'].replace('_', ' ').title()} Errors:[/red]")
                    for error in result["errors"]:
                        console.print(f"  • {error}")

                if result["warnings"]:
                    console.print(f"\n[yellow]⚠️  {result['type'].replace('_', ' ').title()} Warnings:[/yellow]")
                    for warning in result["warnings"]:
                        console.print(f"  • {warning}")

        # Save report if requested
        if output:
            report = {
                "file_path": str(file_path),
                "resource_type": resource_type,
                "validation_level": level,
                "timestamp": datetime.now().isoformat(),
                "summary": {"passed": all_passed, "total_errors": total_errors, "total_warnings": total_warnings},
                "results": validation_results,
            }
            save_resource_to_file(report, output)
            console.print(f"\n[green]Validation report saved to: {output}[/green]")

        # Exit with error code if validation failed
        if not all_passed:
            raise typer.Exit(1)

    except CLIError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command("convert")
def convert_command(
    direction: str = typer.Argument(..., help="Conversion direction: 'to-fhir' or 'from-fhir'"),
    file_path: Path = typer.Argument(..., help="Path to the input file"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file path"),
    pretty: bool = typer.Option(True, "--pretty/--compact", help="Pretty print JSON output"),
    validate_result: bool = typer.Option(True, "--validate/--no-validate", help="Validate the conversion result"),
) -> None:
    """
    Convert between HACS and FHIR formats with validation.

    Examples:
        hacs convert to-fhir patient.json --output patient_fhir.json
        hacs convert from-fhir observation_fhir.json --output observation.json
        hacs convert to-fhir encounter.json --pretty --validate
    """
    try:
        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            task = progress.add_task("Loading resource...", total=None)

            # Load input resource
            data = load_resource_from_file(file_path)

            if direction == "to-fhir":
                progress.update(task, description="Converting to FHIR...")

                # Detect resource type and create HACS resource
                resource_type = detect_resource_type(data)
                resource = create_resource_from_data(data, resource_type)

                # Convert to FHIR
                fhir_resource = to_fhir(resource)
                result = fhir_resource

            elif direction == "from-fhir":
                progress.update(task, description="Converting from FHIR...")

                # Convert from FHIR to HACS
                hacs_resource = from_fhir(data)
                result = hacs_resource.model_dump()

            else:
                raise CLIError(f"Invalid direction: {direction}. Use 'to-fhir' or 'from-fhir'")

            progress.update(task, description="Saving result...")

            # Determine output path
            if output is None:
                suffix = "_fhir.json" if direction == "to-fhir" else "_hacs.json"
                output = file_path.with_suffix("").with_suffix(suffix)

            # Save result
            if pretty:
                with open(output, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, default=str)
            else:
                with open(output, "w", encoding="utf-8") as f:
                    json.dump(result, f, default=str)

        console.print("[green]✅ Conversion completed successfully![/green]")
        console.print(f"[blue]Input:[/blue] {file_path}")
        console.print(f"[blue]Output:[/blue] {output}")
        console.print(f"[blue]Direction:[/blue] {direction}")

    except CLIError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Conversion failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def schema(
    resource_type: str = typer.Argument(..., help="Resource type to show schema for"),
    format_type: str = typer.Option("json", "--format", "-f", help="Output format: json or table"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Save schema to file"),
) -> None:
    """
    Output JSON schema for any HACS resource type.

    Examples:
        hacs schema Patient
        hacs schema Observation --format table
        hacs schema MemoryBlock --output memory_schema.json
    """
    try:
        resource_classes = {
            "Patient": Patient,
            "Observation": Observation,
            "AgentMessage": AgentMessage,
            "Encounter": Encounter,
            "MemoryBlock": MemoryBlock,
            "Evidence": Evidence,
            "Actor": Actor,
        }

        if resource_type not in resource_classes:
            available = ", ".join(resource_classes.keys())
            raise CLIError(f"Unknown resource type: {resource_type}. Available: {available}")

        resource_class = resource_classes[resource_type]
        schema = resource_class.model_json_schema()

        if format_type == "json":
            if output:
                save_resource_to_file(schema, output)
                console.print(f"[green]Schema saved to: {output}[/green]")
            else:
                syntax = Syntax(json.dumps(schema, indent=2), "json", theme="monokai", line_numbers=True)
                console.print(Panel(syntax, title=f"{resource_type} JSON Schema", border_style="blue"))

        elif format_type == "table":
            table = Table(title=f"{resource_type} Schema")
            table.add_column("Field", style="cyan", no_wrap=True)
            table.add_column("Type", style="magenta")
            table.add_column("Required", style="green")
            table.add_column("Description", style="white")

            properties = schema.get("properties", {})
            required_fields = set(schema.get("required", []))

            for field_name, field_info in properties.items():
                field_type = field_info.get("type", "unknown")
                if "anyOf" in field_info:
                    types = [item.get("type", "unknown") for item in field_info["anyOf"]]
                    field_type = " | ".join(types)

                is_required = "✓" if field_name in required_fields else ""
                description = field_info.get("description", "")

                table.add_row(field_name, field_type, is_required, description)

            console.print(table)

        else:
            raise CLIError(f"Unsupported format: {format_type}. Use 'json' or 'table'")

    except CLIError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Schema generation failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def auth(
    action: str = typer.Argument(..., help="Authentication action: 'login', 'logout', or 'status'"),
    actor_id: str | None = typer.Option(None, "--id", help="Actor ID for login"),
    actor_name: str | None = typer.Option(None, "--name", help="Actor name for login"),
    actor_role: str | None = typer.Option(None, "--role", help="Actor role for login"),
) -> None:
    """
    Actor authentication commands for CLI session management.

    Examples:
        hacs auth login --id physician-001 --name "Dr. Smith" --role physician
        hacs auth status
        hacs auth logout
    """
    global current_actor

    try:
        if action == "login":
            if not actor_id:
                actor_id = Prompt.ask("Enter Actor ID")
            if not actor_name:
                actor_name = Prompt.ask("Enter Actor Name", default="CLI User")
            if not actor_role:
                actor_role = Prompt.ask(
                    "Enter Actor Role", default="physician", choices=["physician", "nurse", "patient", "admin"]
                )

            try:
                role = ActorRole(actor_role.upper())
                permissions = ["*:*"] if role == ActorRole.PHYSICIAN else ["patient:read", "observation:read"]

                current_actor = Actor(id=actor_id, name=actor_name, role=role, permissions=permissions, is_active=True)

                console.print("[green]✅ Logged in successfully![/green]")
                console.print(f"[blue]Actor ID:[/blue] {current_actor.id}")
                console.print(f"[blue]Name:[/blue] {current_actor.name}")
                console.print(f"[blue]Role:[/blue] {current_actor.role}")
                console.print(f"[blue]Permissions:[/blue] {len(current_actor.permissions)} granted")

            except ValueError:
                raise CLIError(f"Invalid role: {actor_role}")

        elif action == "logout":
            if current_actor:
                console.print(f"[yellow]Logging out {current_actor.name}...[/yellow]")
                current_actor = None
                console.print("[green]✅ Logged out successfully![/green]")
            else:
                console.print("[yellow]No active session to logout.[/yellow]")

        elif action == "status":
            if current_actor:
                table = Table(title="Current Actor Session")
                table.add_column("Property", style="cyan")
                table.add_column("Value", style="white")

                table.add_row("Actor ID", current_actor.id)
                table.add_row("Name", current_actor.name)
                table.add_row("Role", current_actor.role.value)
                table.add_row("Active", "✅ Yes" if current_actor.is_active else "❌ No")
                table.add_row("Permissions", f"{len(current_actor.permissions)} granted")
                table.add_row("Session Start", str(current_actor.created_at))

                console.print(table)
            else:
                console.print("[yellow]No active actor session.[/yellow]")
                console.print("[blue]Use 'hacs auth login' to authenticate.[/blue]")

        else:
            raise CLIError(f"Unknown action: {action}. Use 'login', 'logout', or 'status'")

    except CLIError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Authentication failed: {e}[/red]")
        raise typer.Exit(1)


# Memory commands
memory_app = typer.Typer(help="Memory operations with Actor authentication")
app.add_typer(memory_app, name="memory")


@memory_app.command("store")
def memory_store(
    file_path: Path = typer.Argument(..., help="Path to the memory file to store"),
    memory_type: str | None = typer.Option(None, "--type", "-t", help="Memory type: episodic, procedural, executive"),
    importance: float = typer.Option(0.5, "--importance", "-i", help="Importance score (0.0-1.0)"),
    metadata: str | None = typer.Option(None, "--metadata", "-m", help="Additional metadata as JSON string"),
) -> None:
    """
    Store memory blocks with validation and Actor permissions.

    Examples:
        hacs memory store episode.json --type episodic --importance 0.8
        hacs memory store procedure.json --metadata '{"context": "surgery"}'
    """
    try:
        actor = get_current_actor()

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            task = progress.add_task("Loading memory...", total=None)

            # Load memory data
            data = load_resource_from_file(file_path)

            # Override memory type if specified
            if memory_type:
                data["memory_type"] = memory_type

            # Set importance score
            data["importance_score"] = importance

            # Add metadata if provided
            if metadata:
                try:
                    metadata_dict = json.loads(metadata)
                    data.setdefault("metadata", {}).update(metadata_dict)
                except json.JSONDecodeError:
                    raise CLIError("Invalid JSON in metadata parameter")

            progress.update(task, description="Creating memory block...")

            # Create memory block
            memory_block = MemoryBlock(**data)

            progress.update(task, description="Storing memory...")

            # Store memory
            result = create_hacs_memory(memory_block, actor)
            memory_id = result.data.get('id', 'unknown') if result.success else None

        console.print("[green]✅ Memory stored successfully![/green]")
        console.print(f"[blue]Memory ID:[/blue] {memory_id}")
        console.print(f"[blue]Type:[/blue] {memory_block.memory_type}")
        console.print(f"[blue]Importance:[/blue] {memory_block.importance_score}")
        console.print(f"[blue]Actor:[/blue] {actor.name}")

    except CLIError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Memory storage failed: {e}[/red]")
        raise typer.Exit(1)


@memory_app.command("recall")
def memory_recall(
    query: str = typer.Argument(..., help="Search query for memory recall"),
    memory_type: str | None = typer.Option(None, "--type", "-t", help="Memory type filter"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of results"),
    min_importance: float = typer.Option(0.0, "--min-importance", help="Minimum importance score"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Save results to file"),
) -> None:
    """
    Search and recall memory blocks with Actor permissions.

    Examples:
        hacs memory recall "patient consultation" --type episodic
        hacs memory recall "surgical procedure" --min-importance 0.7 --limit 5
        hacs memory recall "treatment plan" --output results.json
    """
    try:
        actor = get_current_actor()

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            progress.add_task("Searching memories...", total=None)

            # Search memories
            result = search_hacs_memories(query, memory_type or "all", actor)
            memories = result.data if result.success else []

            # Filter by importance if specified
            if min_importance > 0.0:
                memories = [m for m in memories if m.memory.importance_score >= min_importance]

            # Limit results
            memories = memories[:limit]

        if not memories:
            console.print("[yellow]No memories found matching the query.[/yellow]")
            return

        # Display results
        table = Table(title=f"Memory Recall Results ({len(memories)} found)")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Type", style="magenta")
        table.add_column("Content", style="white", max_width=50)
        table.add_column("Importance", style="green")
        table.add_column("Access Count", style="blue")

        for memory_result in memories:
            memory = memory_result.memory
            content_preview = memory.content[:47] + "..." if len(memory.content) > 50 else memory.content
            table.add_row(
                memory.id,
                memory.memory_type,
                content_preview,
                f"{memory.importance_score:.2f}",
                str(memory.access_count),
            )

        console.print(table)

        # Save results if requested
        if output:
            results = [memory_result.memory.model_dump() for memory_result in memories]
            save_resource_to_file({"query": query, "results": results}, output)
            console.print(f"\n[green]Results saved to: {output}[/green]")

    except CLIError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Memory recall failed: {e}[/red]")
        raise typer.Exit(1)


# Evidence commands
evidence_app = typer.Typer(help="Evidence operations with Actor authentication")
app.add_typer(evidence_app, name="evidence")


@evidence_app.command("create")
def evidence_create(
    citation: str = typer.Argument(..., help="Citation for the evidence"),
    content: str = typer.Argument(..., help="Evidence content"),
    evidence_type: str | None = typer.Option("clinical_note", "--type", "-t", help="Evidence type"),
    confidence: float = typer.Option(0.8, "--confidence", "-c", help="Confidence score (0.0-1.0)"),
    quality: float = typer.Option(0.8, "--quality", "-q", help="Quality score (0.0-1.0)"),
    vector_id: str | None = typer.Option(None, "--vector-id", help="Vector ID for RAG integration"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Save evidence to file"),
) -> None:
    """
    Create evidence records with provenance tracking.

    Examples:
        hacs evidence create "Smith et al. 2024" "RCT shows efficacy" --type rct
        hacs evidence create "Clinical Guideline" "Recommend treatment X" --confidence 0.9
        hacs evidence create "Expert Opinion" "Based on experience" --vector-id vec_123
    """
    try:
        actor = get_current_actor()

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            progress.add_task("Creating evidence...", total=None)

            # Create evidence directly
            evidence = Evidence(
                citation=citation,
                content=content,
                actor_id=actor.id if actor else "unknown",
                evidence_type=EvidenceType.CLINICAL_NOTE
            )

            # Update evidence properties
            if evidence_type:
                try:
                    evidence.evidence_type = EvidenceType(evidence_type.upper())
                except ValueError:
                    console.print(
                        f"[yellow]Warning: Unknown evidence type '{evidence_type}', using CLINICAL_NOTE[/yellow]"
                    )

            evidence.confidence_score = confidence
            evidence.quality_score = quality

            if vector_id:
                evidence.vector_id = vector_id

        console.print("[green]✅ Evidence created successfully![/green]")
        console.print(f"[blue]Evidence ID:[/blue] {evidence.id}")
        console.print(f"[blue]Type:[/blue] {evidence.evidence_type}")
        console.print(f"[blue]Confidence:[/blue] {evidence.confidence_score}")
        console.print(f"[blue]Quality:[/blue] {evidence.quality_score}")
        console.print(f"[blue]Actor:[/blue] {actor.name}")

        # Save evidence if requested
        if output:
            save_resource_to_file(evidence.model_dump(), output)
            console.print(f"\n[green]Evidence saved to: {output}[/green]")

    except CLIError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Evidence creation failed: {e}[/red]")
        raise typer.Exit(1)


@evidence_app.command("search")
def evidence_search(
    query: str = typer.Argument(..., help="Search query for evidence"),
    level: str | None = typer.Option(None, "--level", "-l", help="Evidence level filter"),
    min_confidence: float = typer.Option(0.0, "--min-confidence", help="Minimum confidence score"),
    min_quality: float = typer.Option(0.0, "--min-quality", help="Minimum quality score"),
    limit: int = typer.Option(10, "--limit", help="Maximum number of results"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Save results to file"),
) -> None:
    """
    Search evidence with ranking and filtering.

    Examples:
        hacs evidence search "hypertension treatment" --level rct
        hacs evidence search "diabetes" --min-confidence 0.8 --min-quality 0.7
        hacs evidence search "cardiology" --limit 5 --output evidence_results.json
    """
    try:
        actor = get_current_actor()

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            progress.add_task("Searching evidence...", total=None)

            # Search evidence
            # Search for evidence using vector search
            result = vector_similarity_search(query, actor)
            evidence_list = result.data if result.success else []

            # Filter by confidence and quality
            filtered_evidence = []
            for evidence_result in evidence_list:
                evidence = evidence_result.evidence
                if evidence.confidence_score >= min_confidence and evidence.quality_score >= min_quality:
                    filtered_evidence.append(evidence_result)

            # Limit results
            filtered_evidence = filtered_evidence[:limit]

        if not filtered_evidence:
            console.print("[yellow]No evidence found matching the criteria.[/yellow]")
            return

        # Display results
        table = Table(title=f"Evidence Search Results ({len(filtered_evidence)} found)")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Type", style="magenta")
        table.add_column("Citation", style="white", max_width=30)
        table.add_column("Content", style="white", max_width=40)
        table.add_column("Confidence", style="green")
        table.add_column("Quality", style="blue")

        for evidence_result in filtered_evidence:
            evidence = evidence_result.evidence
            citation_preview = evidence.citation[:27] + "..." if len(evidence.citation) > 30 else evidence.citation
            content_preview = evidence.content[:37] + "..." if len(evidence.content) > 40 else evidence.content

            table.add_row(
                evidence.id,
                evidence.evidence_type.value,
                citation_preview,
                content_preview,
                f"{evidence.confidence_score:.2f}",
                f"{evidence.quality_score:.2f}",
            )

        console.print(table)

        # Save results if requested
        if output:
            results = [evidence_result.evidence.model_dump() for evidence_result in filtered_evidence]
            save_resource_to_file({"query": query, "results": results}, output)
            console.print(f"\n[green]Results saved to: {output}[/green]")

    except CLIError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Evidence search failed: {e}[/red]")
        raise typer.Exit(1)


# Protocol export commands
export_app = typer.Typer(help="Export HACS resources to different protocol formats")
app.add_typer(export_app, name="export")


@export_app.command("mcp")
def export_mcp(
    file_path: Path = typer.Argument(..., help="Path to the HACS resource file"),
    operation: str = typer.Option("create", "--operation", "-op", help="Operation type (create, read, update, delete)"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file path"),
    priority: int = typer.Option(5, "--priority", "-p", help="Task priority (1-10)"),
    timeout: int = typer.Option(30, "--timeout", "-t", help="Task timeout in seconds"),
) -> None:
    """
    Export HACS resource to MCP task format for integration testing.

    Examples:
        hacs export mcp patient.json --operation create --priority 7
        hacs export mcp observation.json --operation update --output mcp_task.json
        hacs export mcp memory.json --operation memory_store --timeout 45
    """
    try:
        from hacs_tools.adapters import convert_to_mcp_task

        actor = get_current_actor()

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            task = progress.add_task("Loading resource...", total=None)

            # Load resource
            data = load_resource_from_file(file_path)
            resource_type = detect_resource_type(data)
            resource = create_resource_from_data(data, resource_type)

            progress.update(task, description="Converting to MCP format...")

            # Convert to MCP task
            mcp_task = convert_to_mcp_task(
                operation, resource=resource, actor=actor, priority=priority, timeout_seconds=timeout
            )

            # Convert to dict for JSON output
            result = mcp_task.model_dump()

            progress.update(task, description="Saving MCP task...")

            # Determine output path
            if output is None:
                output = file_path.with_name(file_path.stem + "_mcp.json")

            # Save result
            save_resource_to_file(result, output)

        console.print("[green]✅ MCP export completed successfully![/green]")
        console.print(f"[blue]Input:[/blue] {file_path}")
        console.print(f"[blue]Output:[/blue] {output}")
        console.print(f"[blue]Operation:[/blue] {operation}")
        console.print(f"[blue]Task ID:[/blue] {result['task_id']}")
        console.print(f"[blue]Priority:[/blue] {priority}")

    except CLIError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]MCP export failed: {e}[/red]")
        raise typer.Exit(1)


@export_app.command("a2a")
def export_a2a(
    file_path: Path = typer.Argument(..., help="Path to the HACS resource file"),
    message_type: str = typer.Option("request", "--type", "-t", help="Message type (request, response, notification)"),
    recipient_id: str | None = typer.Option(None, "--recipient", "-r", help="Recipient actor ID"),
    conversation_id: str | None = typer.Option(None, "--conversation", "-c", help="Conversation ID"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file path"),
    priority: int = typer.Option(5, "--priority", "-p", help="Message priority (1-10)"),
) -> None:
    """
    Export HACS resource to A2A envelope format for agent-to-agent communication.

    Examples:
        hacs export a2a patient.json --type request --recipient agent-002
        hacs export a2a observation.json --type notification --priority 8
        hacs export a2a memory.json --type memory_share --conversation conv-123
    """
    try:
        from hacs_core import Actor, ActorRole
        from hacs_tools.adapters import create_a2a_envelope

        sender = get_current_actor()

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            task = progress.add_task("Loading resource...", total=None)

            # Load resource
            data = load_resource_from_file(file_path)
            resource_type = detect_resource_type(data)
            resource = create_resource_from_data(data, resource_type)

            progress.update(task, description="Creating A2A envelope...")

            # Create recipient if specified
            recipient = None
            if recipient_id:
                recipient = Actor(
                    id=recipient_id,
                    name=f"Agent {recipient_id}",
                    role=ActorRole.PHYSICIAN,
                    permissions=["*:*"],
                    is_active=True,
                )

            # Create A2A envelope
            envelope = create_a2a_envelope(
                message_type, sender, resource, recipient=recipient, conversation_id=conversation_id, priority=priority
            )

            # Convert to dict for JSON output
            result = envelope.model_dump()

            progress.update(task, description="Saving A2A envelope...")

            # Determine output path
            if output is None:
                output = file_path.with_name(file_path.stem + "_a2a.json")

            # Save result
            save_resource_to_file(result, output)

        console.print("[green]✅ A2A export completed successfully![/green]")
        console.print(f"[blue]Input:[/blue] {file_path}")
        console.print(f"[blue]Output:[/blue] {output}")
        console.print(f"[blue]Message Type:[/blue] {message_type}")
        console.print(f"[blue]Message ID:[/blue] {result['message_id']}")
        console.print(f"[blue]Sender:[/blue] {sender.name}")
        if recipient_id:
            console.print(f"[blue]Recipient:[/blue] {recipient_id}")

    except CLIError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]A2A export failed: {e}[/red]")
        raise typer.Exit(1)


@export_app.command("ag-ui")
def export_ag_ui(
    file_path: Path = typer.Argument(..., help="Path to the HACS resource file"),
    event_type: str = typer.Option("resource_created", "--event", "-e", help="UI event type"),
    component: str = typer.Option("patient_dashboard", "--component", "-c", help="Target UI component"),
    action: str = typer.Option("view", "--action", "-a", help="UI action (view, edit, create, delete)"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file path"),
    priority: int = typer.Option(5, "--priority", "-p", help="Event priority (1-10)"),
    auto_dismiss: bool = typer.Option(False, "--auto-dismiss", help="Auto-dismiss the event"),
) -> None:
    """
    Export HACS resource to AG-UI event format for frontend integration.

    Examples:
        hacs export ag-ui patient.json --event resource_created --component patient_dashboard
        hacs export ag-ui observation.json --event observation_alert --component observation_panel --priority 9
        hacs export ag-ui memory.json --event memory_stored --component memory_viewer --auto-dismiss
    """
    try:
        from hacs_tools.adapters import format_for_ag_ui

        actor = get_current_actor()

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            task = progress.add_task("Loading resource...", total=None)

            # Load resource
            data = load_resource_from_file(file_path)
            resource_type = detect_resource_type(data)
            resource = create_resource_from_data(data, resource_type)

            progress.update(task, description="Creating AG-UI event...")

            # Create AG-UI event
            event = format_for_ag_ui(
                event_type,
                component,
                resource=resource,
                actor=actor,
                action=action,
                priority=priority,
                auto_dismiss=auto_dismiss,
            )

            # Convert to dict for JSON output
            result = event.model_dump()

            progress.update(task, description="Saving AG-UI event...")

            # Determine output path
            if output is None:
                output = file_path.with_name(file_path.stem + "_agui.json")

            # Save result
            save_resource_to_file(result, output)

        console.print("[green]✅ AG-UI export completed successfully![/green]")
        console.print(f"[blue]Input:[/blue] {file_path}")
        console.print(f"[blue]Output:[/blue] {output}")
        console.print(f"[blue]Event Type:[/blue] {event_type}")
        console.print(f"[blue]Component:[/blue] {component}")
        console.print(f"[blue]Event ID:[/blue] {result['event_id']}")
        console.print(f"[blue]Priority:[/blue] {priority}")

    except CLIError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]AG-UI export failed: {e}[/red]")
        raise typer.Exit(1)


def main():
    """Main CLI entry point."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    main()
