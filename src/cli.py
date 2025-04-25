"""
CLI interface for the Data Dictionary Agency application.
"""
import argparse
import asyncio
import logging
import os
import sys
from typing import Any, Dict, List, Optional

from src.core.config import settings
from src.core.logging import configure_logging
from src.format_detection.service import FormatDetectionService
from src.repository.github_client import GitHubClient


logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser.
    
    Returns:
        argparse.ArgumentParser: Argument parser.
    """
    parser = argparse.ArgumentParser(
        description="Data Dictionary Agency - Automated data dictionary generation for GitHub repositories",
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Repository command
    repo_parser = subparsers.add_parser("repository", help="Repository operations")
    repo_subparsers = repo_parser.add_subparsers(dest="repo_command", help="Repository command")
    
    # Repository analyze command
    analyze_parser = repo_subparsers.add_parser("analyze", help="Analyze a repository")
    analyze_parser.add_argument("url", help="GitHub repository URL")
    analyze_parser.add_argument("--branch", help="Branch to analyze")
    analyze_parser.add_argument("--include", nargs="+", help="Paths to include")
    analyze_parser.add_argument("--exclude", nargs="+", help="Paths to exclude")
    analyze_parser.add_argument("--formats", nargs="+", help="Formats to detect")
    analyze_parser.add_argument("--output", "-o", help="Output directory for results")
    
    # Repository list command
    list_parser = repo_subparsers.add_parser("list", help="List analyzed repositories")
    list_parser.add_argument("--limit", type=int, default=10, help="Maximum number of repositories to list")
    
    # Format command
    format_parser = subparsers.add_parser("format", help="Format operations")
    format_subparsers = format_parser.add_subparsers(dest="format_command", help="Format command")
    
    # Format list command
    format_list_parser = format_subparsers.add_parser("list", help="List supported formats")
    
    # Format detect command
    format_detect_parser = format_subparsers.add_parser("detect", help="Detect format of a file")
    format_detect_parser.add_argument("file", help="File to detect format of")
    format_detect_parser.add_argument("--confidence", type=float, default=0.7, help="Confidence threshold")
    
    # Format parse command
    format_parse_parser = format_subparsers.add_parser("parse", help="Parse a file")
    format_parse_parser.add_argument("file", help="File to parse")
    format_parse_parser.add_argument("--format", help="Format ID")
    format_parse_parser.add_argument("--output", "-o", help="Output file for parsed result")
    
    # Schema command
    schema_parser = subparsers.add_parser("schema", help="Schema operations")
    schema_subparsers = schema_parser.add_subparsers(dest="schema_command", help="Schema command")
    
    # Schema list command
    schema_list_parser = schema_subparsers.add_parser("list", help="List schemas")
    schema_list_parser.add_argument("--repository", help="Filter by repository ID")
    schema_list_parser.add_argument("--format", help="Filter by format ID")
    schema_list_parser.add_argument("--limit", type=int, default=10, help="Maximum number of schemas to list")
    
    # Schema export command
    schema_export_parser = schema_subparsers.add_parser("export", help="Export a schema")
    schema_export_parser.add_argument("schema_id", help="Schema ID")
    schema_export_parser.add_argument("--format", default="json", help="Export format")
    schema_export_parser.add_argument("--output", "-o", help="Output file for exported schema")
    
    # Version command
    subparsers.add_parser("version", help="Show version information")
    
    return parser


async def handle_format_list() -> None:
    """Handle the format list command."""
    service = FormatDetectionService()
    formats = await service.list_formats()
    
    print(f"Supported formats ({len(formats)}):")
    for fmt in formats:
        capabilities = ", ".join(
            name for name, enabled in fmt.capabilities.items() if enabled
        )
        extensions = ", ".join(fmt.extensions)
        print(f"  {fmt.id} - {fmt.name} ({extensions}) - Capabilities: {capabilities}")


async def handle_format_detect(args: argparse.Namespace) -> None:
    """Handle the format detect command."""
    service = FormatDetectionService()
    
    try:
        with open(args.file, "rb") as f:
            content = f.read()
        
        result = await service.detect_format(
            filename=os.path.basename(args.file),
            content=content,
            confidence_threshold=args.confidence,
        )
        
        print(f"File: {args.file}")
        print(f"Size: {result.file_size} bytes")
        print(f"Detected format: {result.format_id or 'Unknown'}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"MIME type: {result.mime_type or 'Unknown'}")
        
        if result.sample_data:
            print(f"Sample data: {result.sample_data[:100]}...")
        
    except Exception as e:
        logger.error("Failed to detect format: %s", e)
        print(f"Error: {e}")
        sys.exit(1)


async def handle_format_parse(args: argparse.Namespace) -> None:
    """Handle the format parse command."""
    service = FormatDetectionService()
    
    try:
        with open(args.file, "rb") as f:
            content = f.read()
        
        result = await service.parse_file(
            filename=os.path.basename(args.file),
            content=content,
            format_id=args.format,
        )
        
        print(f"File: {args.file}")
        print(f"Format: {result['format']}")
        print(f"Schema: {result['schema']}")
        
        if args.output:
            import json
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)
            print(f"Parsed result saved to {args.output}")
        
    except Exception as e:
        logger.error("Failed to parse file: %s", e)
        print(f"Error: {e}")
        sys.exit(1)


async def handle_repository_analyze(args: argparse.Namespace) -> None:
    """Handle the repository analyze command."""
    try:
        github_client = GitHubClient()
        print(f"Analyzing repository: {args.url}")
        
        # This is a stub implementation
        # In a real application, this would use the repository service
        # to create a repository analysis job
        
        print("Repository analysis job created (stub implementation)")
        print("Branch:", args.branch or "default")
        if args.include:
            print("Include paths:", args.include)
        if args.exclude:
            print("Exclude paths:", args.exclude)
        if args.formats:
            print("Formats to detect:", args.formats)
        
    except Exception as e:
        logger.error("Failed to analyze repository: %s", e)
        print(f"Error: {e}")
        sys.exit(1)


def handle_version() -> None:
    """Handle the version command."""
    print(f"Data Dictionary Agency version {settings.VERSION}")
    print(f"Environment: {settings.APP_ENV}")
    print(f"Python version: {sys.version}")


async def run_cli() -> None:
    """Run the CLI application."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == "format":
        if args.format_command == "list":
            await handle_format_list()
        elif args.format_command == "detect":
            await handle_format_detect(args)
        elif args.format_command == "parse":
            await handle_format_parse(args)
        else:
            parser.print_help()
    
    elif args.command == "repository":
        if args.repo_command == "analyze":
            await handle_repository_analyze(args)
        elif args.repo_command == "list":
            print("Repository list command - not implemented yet")
        else:
            parser.print_help()
    
    elif args.command == "schema":
        if args.schema_command == "list":
            print("Schema list command - not implemented yet")
        elif args.schema_command == "export":
            print("Schema export command - not implemented yet")
        else:
            parser.print_help()
    
    elif args.command == "version":
        handle_version()


def main() -> None:
    """CLI entry point."""
    # Configure logging
    configure_logging()
    
    # Run the CLI application
    asyncio.run(run_cli())


if __name__ == "__main__":
    main()
