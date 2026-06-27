"""CLI Entrypoint and Composition Root for RepoLens.

This module provides the command-line interface, parses user arguments,
wires together all layers of the Clean Architecture, and triggers the
application workflow.
"""

import argparse
import os
import sys
from pathlib import Path

from repolens.infrastructure.parsers import PythonRepositoryParser
from repolens.infrastructure.clients import OpenAIClient
from repolens.usecase.scanner import RepositoryScanner
from repolens.usecase.enricher import AIEnrichmentService


def run() -> None:
    """Main CLI execution loop."""
    parser = argparse.ArgumentParser(
        prog="repolens",
        description="AI-powered repository understanding & documentation agent."
    )
    
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Path to the local repository directory to scan (default: current directory)."
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Directory where markdown reports will be saved (default: target path)."
    )

    args = parser.parse_args()

    # 1. Resolve paths
    target_path = Path(args.path).resolve()
    if not target_path.exists() or not target_path.is_dir():
        print(f"Error: Target path '{target_path}' is not a valid directory.")
        sys.exit(1)
        
    output_path = Path(args.output).resolve() if args.output else target_path
    output_path.mkdir(parents=True, exist_ok=True)

    # 2. Check API Key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable is missing.")
        print("Please export it before running RepoLens.")
        sys.exit(1)

    print(f"ðŸš€ Initializing RepoLens scan on: {target_path}")

    # ---------------------------------------------------------
    # 3. Composition Root (Dependency Injection)
    # ---------------------------------------------------------
    
    # Infrastructure: AST parser
    repo_parser = PythonRepositoryParser()
    
    # Infrastructure: LLM Client
    llm_client = OpenAIClient(api_key=api_key)
    
    # Use Case: Scanner
    scanner = RepositoryScanner(parser=repo_parser)
    
    # Use Case: Enricher
    enricher = AIEnrichmentService(llm_client=llm_client)

    # ---------------------------------------------------------
    # 4. Execute Workflow
    # ---------------------------------------------------------
    print("ðŸ” Parsing Python files and mapping architecture...")
    blueprint = scanner.scan_directory(root_path=str(target_path))
    
    print(f"âœ… Found {blueprint.module_count} modules with "
          f"{blueprint.total_classes} classes and {blueprint.total_functions} functions.")
    print("ðŸ§  Generating high-level repository summary via OpenAI...")
    
    summary_md = enricher.generate_repository_summary(blueprint)
    
    print("ðŸ—ºï¸ Generating developer onboarding guide...")
    onboarding_md = enricher.generate_onboarding_guide(blueprint)

    # 5. Output Results
    summary_file = output_path / "REPOLENS_SUMMARY.md"
    onboarding_file = output_path / "REPOLENS_ONBOARDING.md"

    summary_file.write_text(summary_md, encoding="utf-8")
    onboarding_file.write_text(onboarding_md, encoding="utf-8")

    print(f"ðŸŽ‰ Success! Documentation generated successfully:")
    print(f"   ðŸ“„ {summary_file}")
    print(f"   ðŸ“„ {onboarding_file}")


if __name__ == "__main__":
    run()
