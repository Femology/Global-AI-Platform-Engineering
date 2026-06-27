"""Infrastructure layer.

Concrete implementations of the interfaces required by the use-case layer:
AST-based source parsing, LLM client adapters, and file-system access.
Depends on ``domain`` (and optionally ``usecase`` ports), never the reverse.
"""
