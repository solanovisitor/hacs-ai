#!/usr/bin/env python3
"""
HACS Tools CLI - Command line interface for HACS healthcare AI tools.

Provides commands for:
- extract: Extract HACS resources from clinical text using ExtractionRunner
- registry: Inspect HACS resource registry and extractable fields
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

def create_parser() -> argparse.ArgumentParser:
    """Create the main CLI parser."""
    parser = argparse.ArgumentParser(
        description="HACS Tools CLI - Healthcare AI agent tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  hacs-tools extract --transcript example.txt --model gpt-4o-mini
  hacs-tools registry --list-extractables
  hacs-tools extract --transcript example.txt --timeout 120 --concurrency 2
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Extract command
    extract_parser = subparsers.add_parser(
        "extract", 
        help="Extract HACS resources from clinical text"
    )
    extract_parser.add_argument(
        "--transcript", 
        required=True, 
        help="Path to clinical transcript file"
    )
    extract_parser.add_argument(
        "--model", 
        default="gpt-4o-mini", 
        help="LLM model to use (default: gpt-4o-mini)"
    )
    extract_parser.add_argument(
        "--max-chars", 
        type=int, 
        default=4000, 
        help="Maximum characters to process (default: 4000)"
    )
    extract_parser.add_argument(
        "--timeout", 
        type=int, 
        default=300, 
        help="Total timeout in seconds (default: 300)"
    )
    extract_parser.add_argument(
        "--window-timeout", 
        type=int, 
        default=30, 
        help="Per-window timeout in seconds (default: 30)"
    )
    extract_parser.add_argument(
        "--concurrency", 
        type=int, 
        default=3, 
        help="Concurrent windows (default: 3)"
    )
    extract_parser.add_argument(
        "--max-fields", 
        type=int, 
        default=4, 
        help="Max extractable fields per resource (default: 4)"
    )
    extract_parser.add_argument(
        "--out-dir", 
        default=".", 
        help="Output directory (default: current directory)"
    )
    extract_parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug output"
    )
    
    # Registry command
    registry_parser = subparsers.add_parser(
        "registry", 
        help="Inspect HACS resource registry"
    )
    registry_parser.add_argument(
        "--list-extractables", 
        action="store_true", 
        help="List extractable fields for all resources"
    )
    registry_parser.add_argument(
        "--resource", 
        help="Show details for specific resource type"
    )
    registry_parser.add_argument(
        "--compact", 
        action="store_true", 
        help="Show compact output"
    )
    
    return parser


async def cmd_extract(args: argparse.Namespace) -> int:
    """Execute the extract command."""
    try:
        from langchain_openai import ChatOpenAI
        from hacs_utils.extraction import ExtractionRunner, ExtractionConfig
    except ImportError as e:
        print(f"Error: Missing dependencies for extraction: {e}")
        print("Install with: pip install langchain-openai hacs-utils")
        return 1
    
    # Read transcript
    transcript_path = Path(args.transcript)
    if not transcript_path.exists():
        print(f"Error: Transcript file not found: {transcript_path}")
        return 1
    
    try:
        source_text = transcript_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading transcript: {e}")
        return 1
    
    if len(source_text) > args.max_chars:
        source_text = source_text[:args.max_chars]
        print(f"Truncated transcript to {args.max_chars} characters")
    
    # Create LLM provider
    try:
        llm_provider = ChatOpenAI(
            model=args.model,
            timeout=args.window_timeout,
            temperature=0.1,
        )
    except Exception as e:
        print(f"Error creating LLM provider: {e}")
        print("Make sure OPENAI_API_KEY environment variable is set")
        return 1
    
    # Setup output directory
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Extracting from transcript ({len(source_text)} chars) using {args.model}")
    
    # Configure ExtractionRunner
    config = ExtractionConfig(
        concurrency_limit=args.concurrency,
        window_timeout_sec=args.window_timeout,
        total_timeout_sec=args.timeout,
        max_retries=2,
        enable_zero_yield_fallback=True,
        max_extractable_fields=args.max_fields,
        debug_dir=str(out_dir / "debug") if args.debug else None,
        enable_metrics=True,
    )
    
    runner = ExtractionRunner(config)
    
    try:
        # Run extraction
        results = await runner.extract_document(
            llm_provider,
            source_text=source_text,
            debug_prefix="cli_extraction",
        )
        
        # Get metrics
        metrics = runner.get_metrics()
        
        # Save results
        results_path = out_dir / "extraction_results.json"
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    k: [
                        {
                            "record": item.get("record").model_dump(mode="json") if hasattr(item.get("record"), "model_dump") else str(item.get("record")),
                            "citation": item.get("citation"),
                            "char_interval": item.get("char_interval"),
                        }
                        for item in v
                    ] 
                    for k, v in results.items()
                },
                f,
                indent=2,
                ensure_ascii=False,
                default=str,
            )
        
        # Save metrics
        if metrics:
            metrics_path = out_dir / "extraction_metrics.json"
            with open(metrics_path, "w", encoding="utf-8") as f:
                json.dump(metrics.to_dict(), f, indent=2)
        
        # Print summary
        total_records = sum(len(v) for v in results.values())
        print("\n✓ Extraction completed successfully!")
        print(f"  Total records: {total_records}")
        print(f"  Resource types: {list(results.keys())}")
        print(f"  Output: {results_path}")
        
        if metrics:
            print(f"  Duration: {metrics.total_duration_sec:.2f}s")
            print(f"  Citations found: {metrics.total_citations_found}")
            if metrics.timeout_failures > 0:
                print(f"  ⚠ Timeout failures: {metrics.timeout_failures}")
            if metrics.validation_failures > 0:
                print(f"  ⚠ Validation failures: {metrics.validation_failures}")
        
        return 0
        
    except Exception as e:
        print(f"Error during extraction: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


def cmd_registry(args: argparse.Namespace) -> int:
    """Execute the registry command."""
    try:
        from hacs_registry.resource_registry import HACSResourceRegistry
    except ImportError as e:
        print(f"Error: Missing dependencies for registry: {e}")
        print("Install with: pip install hacs-registry")
        return 1
    
    try:
        registry = HACSResourceRegistry()
        
        if args.list_extractables:
            print("HACS Resource Extractable Fields:")
            print("=" * 40)
            
            extractables_index = registry.get_extractables_index()
            
            for resource_name, info in sorted(extractables_index.items()):
                extractable_fields = info.get("extractable_fields", [])
                required_fields = info.get("required_extractables", [])
                
                if args.compact:
                    print(f"{resource_name}: {len(extractable_fields)} fields")
                else:
                    print(f"\n{resource_name}:")
                    print(f"  Extractable fields ({len(extractable_fields)}): {', '.join(extractable_fields)}")
                    if required_fields:
                        print(f"  Required fields ({len(required_fields)}): {', '.join(required_fields)}")
                    print(f"  Has coercion: {info.get('has_coerce_extractable', False)}")
        
        elif args.resource:
            resource_name = args.resource
            extractables_index = registry.get_extractables_index()
            
            if resource_name not in extractables_index:
                print(f"Error: Resource '{resource_name}' not found")
                print(f"Available resources: {', '.join(sorted(extractables_index.keys()))}")
                return 1
            
            info = extractables_index[resource_name]
            print(f"Resource: {resource_name}")
            print(f"Extractable fields: {info.get('extractable_fields', [])}")
            print(f"Required extractables: {info.get('required_extractables', [])}")
            print(f"Has canonical defaults: {info.get('canonical_defaults', {}) != {}}")
            print(f"Has coercion: {info.get('has_coerce_extractable', False)}")
            
            # Try to get model class and show hints
            try:
                for model_class in registry.iter_model_classes():
                    if getattr(model_class, "__name__", "") == resource_name:
                        hints = getattr(model_class, "llm_hints", lambda: [])()
                        if hints:
                            print("LLM hints:")
                            for hint in hints:
                                print(f"  - {hint}")
                        break
            except Exception:
                pass
        
        else:
            # Show general registry info
            extractables_index = registry.get_extractables_index()
            print("HACS Resource Registry")
            print(f"Total resources: {len(extractables_index)}")
            print(f"Resources with extractables: {sum(1 for info in extractables_index.values() if info.get('extractable_fields'))}")
            print(f"Resources with coercion: {sum(1 for info in extractables_index.values() if info.get('has_coerce_extractable'))}")
            print("\nUse --list-extractables to see all extractable fields")
            print("Use --resource <name> to see details for a specific resource")
        
        return 0
        
    except Exception as e:
        print(f"Error accessing registry: {e}")
        return 1


def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == "extract":
        return asyncio.run(cmd_extract(args))
    elif args.command == "registry":
        return cmd_registry(args)
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
