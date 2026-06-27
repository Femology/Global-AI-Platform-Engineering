"""Infrastructure adapter for Python source code parsing.

This module provides an offline, deterministic syntax analyzer using the
native ``ast`` module. It maps raw Python source code into the pure domain
entities defined in ``repolens.domain.models``.
"""

import ast
from typing import Optional

from repolens.domain.models import (
    ClassInfo,
    FunctionInfo,
    ModuleMetrics,
    Parameter,
    Visibility,
)


def _get_visibility(name: str) -> Visibility:
    """Infer visibility based on standard Python naming conventions."""
    if name.startswith("__") and name.endswith("__"):
        return Visibility.DUNDER
    if name.startswith("__"):
        return Visibility.PRIVATE
    if name.startswith("_"):
        return Visibility.PROTECTED
    return Visibility.PUBLIC


def _safe_unparse(node: Optional[ast.AST]) -> Optional[str]:
    """Safely convert an AST node back to source text.
    
    Returns None if the node is None or if unparsing fails.
    """
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return "<unparse_error>"


class PyFileVisitor(ast.NodeVisitor):
    """AST NodeVisitor that traverses a Python file to extract domain metrics.
    
    This visitor focuses on architectural features: classes, module-level
    functions, and imports. It intentionally ignores deeply nested closures
    or local variables, as they are not part of a module's public API or
    overall architecture.
    """

    def __init__(self) -> None:
        self.classes: list[ClassInfo] = []
        self.functions: list[FunctionInfo] = []
        self.imports: set[str] = set()
    
    def _extract_parameters(self, args_node: ast.arguments) -> tuple[Parameter, ...]:
        """Extract parameter definitions from a function's arguments node."""
        params: list[Parameter] = []
        
        # Positional and pos-only arguments
        all_pos = getattr(args_node, 'posonlyargs', []) + args_node.args
        defaults_offset = len(all_pos) - len(args_node.defaults)
        
        for i, arg in enumerate(all_pos):
            default_node = args_node.defaults[i - defaults_offset] if i >= defaults_offset else None
            params.append(
                Parameter(
                    name=arg.arg,
                    annotation=_safe_unparse(arg.annotation),
                    default=_safe_unparse(default_node),
                )
            )
            
        # Variadic positional (*args)
        if args_node.vararg:
            params.append(
                Parameter(
                    name=args_node.vararg.arg,
                    annotation=_safe_unparse(args_node.vararg.annotation),
                    is_variadic=True,
                )
            )
            
        # Keyword-only arguments
        for i, arg in enumerate(args_node.kwonlyargs):
            default_node = args_node.kw_defaults[i] if i < len(args_node.kw_defaults) else None
            params.append(
                Parameter(
                    name=arg.arg,
                    annotation=_safe_unparse(arg.annotation),
                    default=_safe_unparse(default_node),
                )
            )
            
        # Variadic keyword (**kwargs)
        if args_node.kwarg:
            params.append(
                Parameter(
                    name=args_node.kwarg.arg,
                    annotation=_safe_unparse(args_node.kwarg.annotation),
                    is_keyword_variadic=True,
                )
            )
            
        return tuple(params)

    def _parse_function(
        self, 
        node: ast.FunctionDef | ast.AsyncFunctionDef, 
        is_method: bool = False,
        parent_name: str = ""
    ) -> FunctionInfo:
        """Map a function/method AST node to a FunctionInfo domain entity."""
        qualname = f"{parent_name}.{node.name}" if parent_name else node.name
        
        return FunctionInfo(
            name=node.name,
            qualified_name=qualname,
            parameters=self._extract_parameters(node.args),
            return_annotation=_safe_unparse(node.returns),
            docstring=ast.get_docstring(node),
            decorators=tuple(
                _safe_unparse(dec) or "<decorator>" for dec in node.decorator_list
            ),
            line_start=node.lineno,
            line_end=getattr(node, "end_lineno", node.lineno),
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_method=is_method,
            visibility=_get_visibility(node.name)
        )

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit a synchronous module-level function."""
        self.functions.append(self._parse_function(node, is_method=False))
        # We do not call generic_visit(node) here to avoid processing 
        # nested/closure functions, which are not architectural components.

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit an asynchronous module-level function."""
        self.functions.append(self._parse_function(node, is_method=False))
        # Exclude closures for async too.

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit a class definition and explicitly process its methods."""
        methods: list[FunctionInfo] = []
        
        # Manually extract methods to avoid bleeding them into module-level functions
        for body_node in node.body:
            if isinstance(body_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(
                    self._parse_function(
                        body_node, 
                        is_method=True, 
                        parent_name=node.name
                    )
                )

        class_info = ClassInfo(
            name=node.name,
            qualified_name=node.name,  # Nested classes not fully supported yet for simplicity
            base_classes=tuple(
                _safe_unparse(base) or "<base>" for base in node.bases
            ),
            methods=tuple(methods),
            docstring=ast.get_docstring(node),
            decorators=tuple(
                _safe_unparse(dec) or "<decorator>" for dec in node.decorator_list
            ),
            line_start=node.lineno,
            line_end=getattr(node, "end_lineno", node.lineno),
            visibility=_get_visibility(node.name)
        )
        self.classes.append(class_info)
        # Skip generic_visit to avoid parsing inner classes/functions globally

    def visit_Import(self, node: ast.Import) -> None:
        """Record base import dependencies (e.g. `import os`)."""
        for alias in node.names:
            self.imports.add(alias.name.split(".")[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Record from-import dependencies (e.g. `from os import path`)."""
        if node.module:
            self.imports.add(node.module.split(".")[0])
        self.generic_visit(node)


class PythonRepositoryParser:
    """Parser that maps physical Python files into the ModuleMetrics domain."""

    def _infer_module_path(self, file_path: str) -> str:
        """Convert a file path to a plausible Python module path."""
        # e.g., 'src/repolens/domain/models.py' -> 'src.repolens.domain.models'
        path_no_ext = file_path.rsplit(".py", 1)[0]
        return path_no_ext.replace("/", ".").replace("\\", ".")

    def parse_file(self, file_path: str, content: str) -> ModuleMetrics:
        """Parse raw Python source into a ModuleMetrics domain entity.
        
        Gracefully intercepts syntax errors to ensure that a single malformed
        file does not crash an entire repository scan.
        
        Args:
            file_path: The location of the file in the repository.
            content: The raw string source code of the Python file.
            
        Returns:
            A populated ModuleMetrics object, or a flagged/empty object if
            the source code could not be parsed.
        """
        loc = len(content.splitlines())
        module_path = self._infer_module_path(file_path)

        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            # Return an empty metric entity with a flagged docstring so the 
            # domain reflects that a file exists but is unreadable.
            return ModuleMetrics(
                module_path=module_path,
                file_path=file_path,
                docstring=f"[Error] SyntaxError during parse: {e}",
                loc=loc
            )
        except Exception as e:
            # Catching generic exceptions just in case ast.parse chokes internally
            return ModuleMetrics(
                module_path=module_path,
                file_path=file_path,
                docstring=f"[Error] Unexpected failure during parse: {e}",
                loc=loc
            )

        visitor = PyFileVisitor()
        visitor.visit(tree)
        
        module_docstring = ast.get_docstring(tree)

        return ModuleMetrics(
            module_path=module_path,
            file_path=file_path,
            functions=tuple(visitor.functions),
            classes=tuple(visitor.classes),
            imports=tuple(sorted(visitor.imports)),
            docstring=module_docstring,
            loc=loc
        )
