"""Use case for scanning a local directory and mapping its architecture.

This module orchestrates the physical traversal of a repository, filtering out
irrelevant or ignored directories, reading source files, and passing them to
an injected parser to aggregate a pure RepositoryBlueprint.
"""

import os
from pathlib import Path
from typing import Protocol, Optional

from repolens.domain.models import ModuleMetrics, RepositoryBlueprint


class ParserProtocol(Protocol):
    """Abstract interface for a source code parser.
    
    The Use Case layer relies on this interface rather than a concrete
    implementation to uphold Clean Architecture boundaries.
    """
    def parse_file(self, file_path: str, content: str) -> ModuleMetrics:
        ...


class RepositoryScanner:
    """Orchestrates the scanning of a local repository directory."""

    DEFAULT_IGNORES = {
        ".git",
        "__pycache__",
        "venv",
        ".venv",
        "env",
        "node_modules",
        ".pytest_cache",
        ".mypy_cache",
        ".tox",
        "build",
        "dist",
    }

    def __init__(
        self, 
        parser: ParserProtocol, 
        ignore_dirs: Optional[set[str]] = None
    ) -> None:
        """Initialize the scanner with a parser and directory filters.
        
        Args:
            parser: An implementation of ParserProtocol (e.g., PythonRepositoryParser).
            ignore_dirs: Set of directory names to skip. Defaults to common cache/env dirs.
        """
        self.parser = parser
        self.ignore_dirs = ignore_dirs if ignore_dirs is not None else self.DEFAULT_IGNORES

    def scan_directory(self, root_path: str, repo_name: Optional[str] = None) -> RepositoryBlueprint:
        """Walk a directory, parse Python files, and build a Blueprint.
        
        Args:
            root_path: The absolute or relative path to the repository root.
            repo_name: Optional explicit name. Defaults to the root directory's name.
            
        Returns:
            A pure RepositoryBlueprint aggregate entity containing all module metrics.
        """
        root = Path(root_path).resolve()
        modules: list[ModuleMetrics] = []

        # os.walk allows us to mutate dirnames in-place to prune the search tree efficiently
        for dirpath, dirnames, filenames in os.walk(root):
            # Prune ignored directories and hidden directories
            dirnames[:] = [
                d for d in dirnames 
                if d not in self.ignore_dirs and not d.startswith(".")
            ]

            for filename in filenames:
                if not filename.endswith(".py"):
                    continue
                
                file_path = Path(dirpath) / filename
                
                # Determine repository-relative path for the domain model
                try:
                    rel_path = file_path.relative_to(root).as_posix()
                except ValueError:
                    rel_path = file_path.as_posix()

                # Read source cautiously
                try:
                    content = file_path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    # Log or record skipped binary/malformed file (simplified for Phase 3)
                    continue

                # Parse and aggregate
                metrics = self.parser.parse_file(rel_path, content)
                modules.append(metrics)

        name = repo_name if repo_name else root.name

        return RepositoryBlueprint(
            name=name,
            root_path=root.as_posix(),
            modules=tuple(modules),
            description=None
        )
