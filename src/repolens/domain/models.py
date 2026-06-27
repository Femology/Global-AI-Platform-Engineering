"""Pure domain models for RepoLens.

These dataclasses are the canonical, framework-agnostic representation of a
parsed codebase. They describe *what* RepoLens knows about a repository, never
*how* that knowledge was obtained.

Purity contract
---------------
This module is the innermost layer of the architecture and is held to a strict
purity standard:

* It depends only on the Python standard library's typing/utility primitives.
* It MUST NOT import ``ast`` (or any parser).
* It MUST NOT import AI/LLM client libraries, HTTP clients, or file-IO helpers.
* It contains no side effects: no logging, no network, no disk access.

Frozen, slotted dataclasses are used to make the entities immutable and cheap,
which keeps the domain easy to reason about and safe to share across threads.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Visibility(str, Enum):
    """Conventional access level of a code symbol.

    Python has no enforced visibility, so this is inferred by naming convention
    elsewhere in the system (e.g. a leading underscore implies ``PRIVATE``).
    The domain merely records the conclusion.
    """

    PUBLIC = "public"
    PROTECTED = "protected"  # single leading underscore: ``_name``
    PRIVATE = "private"      # double leading underscore: ``__name``
    DUNDER = "dunder"        # dunder methods: ``__name__``


@dataclass(frozen=True, slots=True)
class Parameter:
    """A single parameter of a callable.

    Attributes
    ----------
    name:
        The parameter's identifier (e.g. ``"path"``).
    annotation:
        The type annotation as written in source, if any (e.g. ``"str"``).
        ``None`` when the parameter is unannotated.
    default:
        The default value rendered as source text (e.g. ``"None"``), or
        ``None`` when the parameter is required.
    is_variadic:
        ``True`` for ``*args``-style parameters.
    is_keyword_variadic:
        ``True`` for ``**kwargs``-style parameters.
    """

    name: str
    annotation: Optional[str] = None
    default: Optional[str] = None
    is_variadic: bool = False
    is_keyword_variadic: bool = False

    @property
    def is_required(self) -> bool:
        """Whether the parameter must be supplied by a caller."""
        return self.default is None and not (
            self.is_variadic or self.is_keyword_variadic
        )


@dataclass(frozen=True, slots=True)
class FunctionInfo:
    """Description of a function or method.

    Attributes
    ----------
    name:
        The function's identifier.
    qualified_name:
        Dotted path within its module (e.g. ``"ClassName.method"`` for a
        method, or just ``"function"`` for a module-level function).
    parameters:
        Ordered parameters, including ``self``/``cls`` when present.
    return_annotation:
        The return type annotation as source text, if any.
    docstring:
        The function's docstring, stripped, or ``None`` if absent.
    decorators:
        Decorator names applied to the function, in source order.
    line_start:
        1-based line number where the definition begins.
    line_end:
        1-based line number where the definition ends.
    is_async:
        ``True`` for ``async def`` functions.
    is_method:
        ``True`` when the function is defined inside a class body.
    visibility:
        Inferred access level (see :class:`Visibility`).
    """

    name: str
    qualified_name: str
    parameters: tuple[Parameter, ...] = ()
    return_annotation: Optional[str] = None
    docstring: Optional[str] = None
    decorators: tuple[str, ...] = ()
    line_start: int = 0
    line_end: int = 0
    is_async: bool = False
    is_method: bool = False
    visibility: Visibility = Visibility.PUBLIC

    @property
    def line_count(self) -> int:
        """Number of source lines spanned by the definition (inclusive)."""
        if self.line_end < self.line_start:
            return 0
        return self.line_end - self.line_start + 1

    @property
    def has_docstring(self) -> bool:
        """Whether the function is documented."""
        return bool(self.docstring and self.docstring.strip())

    @property
    def arity(self) -> int:
        """Total number of declared parameters."""
        return len(self.parameters)


@dataclass(frozen=True, slots=True)
class ClassInfo:
    """Description of a class definition.

    Attributes
    ----------
    name:
        The class identifier.
    qualified_name:
        Dotted path within its module (supports nested classes).
    base_classes:
        Names of direct base classes as written in source.
    methods:
        Methods declared directly on the class.
    docstring:
        The class docstring, stripped, or ``None`` if absent.
    decorators:
        Decorator names applied to the class, in source order.
    line_start:
        1-based line number where the definition begins.
    line_end:
        1-based line number where the definition ends.
    visibility:
        Inferred access level (see :class:`Visibility`).
    """

    name: str
    qualified_name: str
    base_classes: tuple[str, ...] = ()
    methods: tuple[FunctionInfo, ...] = ()
    docstring: Optional[str] = None
    decorators: tuple[str, ...] = ()
    line_start: int = 0
    line_end: int = 0
    visibility: Visibility = Visibility.PUBLIC

    @property
    def method_count(self) -> int:
        """Number of methods declared directly on the class."""
        return len(self.methods)

    @property
    def public_methods(self) -> tuple[FunctionInfo, ...]:
        """Methods that form part of the class's public API."""
        return tuple(
            m for m in self.methods if m.visibility is Visibility.PUBLIC
        )

    @property
    def has_docstring(self) -> bool:
        """Whether the class is documented."""
        return bool(self.docstring and self.docstring.strip())

    @property
    def is_subclass(self) -> bool:
        """Whether the class declares at least one explicit base class."""
        return len(self.base_classes) > 0


@dataclass(frozen=True, slots=True)
class ModuleMetrics:
    """Quantitative summary and structure of a single source module.

    A module corresponds to one analysed source file.

    Attributes
    ----------
    module_path:
        Dotted import path of the module (e.g. ``"repolens.domain.models"``).
    file_path:
        Repository-relative path of the source file (POSIX style).
    functions:
        Module-level (non-method) functions.
    classes:
        Classes declared in the module.
    imports:
        Distinct import targets referenced by the module, in source order.
    docstring:
        The module-level docstring, stripped, or ``None`` if absent.
    loc:
        Total physical lines of code in the file.
    """

    module_path: str
    file_path: str
    functions: tuple[FunctionInfo, ...] = ()
    classes: tuple[ClassInfo, ...] = ()
    imports: tuple[str, ...] = ()
    docstring: Optional[str] = None
    loc: int = 0

    @property
    def function_count(self) -> int:
        """Number of module-level functions."""
        return len(self.functions)

    @property
    def class_count(self) -> int:
        """Number of classes in the module."""
        return len(self.classes)

    @property
    def import_count(self) -> int:
        """Number of distinct imports referenced by the module."""
        return len(self.imports)

    @property
    def has_docstring(self) -> bool:
        """Whether the module is documented."""
        return bool(self.docstring and self.docstring.strip())

    @property
    def public_api(self) -> tuple[str, ...]:
        """Names of public top-level symbols exposed by the module."""
        names: list[str] = [
            f.name for f in self.functions if f.visibility is Visibility.PUBLIC
        ]
        names.extend(
            c.name for c in self.classes if c.visibility is Visibility.PUBLIC
        )
        return tuple(names)


@dataclass(frozen=True, slots=True)
class RepositoryBlueprint:
    """The complete structural model of an analysed repository.

    This is the top-level aggregate that downstream use cases (documentation
    generation, diagramming, onboarding guides) consume.

    Attributes
    ----------
    name:
        Human-readable repository name.
    root_path:
        Absolute or repository-relative root that was analysed.
    modules:
        Every successfully analysed module.
    description:
        Optional high-level description (e.g. from a top-level README or an
        enrichment step). The domain only stores it; it never produces it.
    """

    name: str
    root_path: str
    modules: tuple[ModuleMetrics, ...] = ()
    description: Optional[str] = None

    @property
    def module_count(self) -> int:
        """Number of analysed modules."""
        return len(self.modules)

    @property
    def total_classes(self) -> int:
        """Total class definitions across the repository."""
        return sum(m.class_count for m in self.modules)

    @property
    def total_functions(self) -> int:
        """Total module-level function definitions across the repository."""
        return sum(m.function_count for m in self.modules)

    @property
    def total_loc(self) -> int:
        """Aggregate physical lines of code across all modules."""
        return sum(m.loc for m in self.modules)

    @property
    def documented_module_ratio(self) -> float:
        """Fraction of modules that carry a module-level docstring.

        Returns ``0.0`` for an empty repository to avoid division by zero.
        """
        if not self.modules:
            return 0.0
        documented = sum(1 for m in self.modules if m.has_docstring)
        return documented / len(self.modules)
