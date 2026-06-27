"""RepoLens — AI-powered repository understanding & documentation agent.

RepoLens ingests an entire codebase and produces architecture overviews,
dependency graphs, API documentation, and onboarding guides.

The package follows a Clean Architecture layout:

- ``domain``         : Pure, dependency-free business entities and rules.
- ``usecase``        : Application-specific orchestration (use cases).
- ``infrastructure`` : Concrete adapters (AST parsing, LLM clients, file IO).
- ``cli``            : Command-line entry points.
"""

__version__ = "0.1.0"
