# Available optimizers

## Early-stage optimizers (order 100)

These run first and delete entire files or directories, avoiding unnecessary
processing by later optimizers.

### `remove_tests`

Removes Python test files that are confirmed to contain test framework usage.
Requires **both** a test naming convention (`test_*.py`, `*_test.py`, `conftest.py`,
or files inside `tests/`/`test/` directories) **and** test framework signals
(`import pytest`, `import unittest`, `def test_`, `class Test`) before deleting.

- Only removes `.py` files
- Keeps `__init__.py`, helper modules, fixture data, and non-Python files
- `conftest.py` only removed if it imports pytest

### `remove_typestubs`

Removes `.pyi` type stub files and `py.typed` PEP 561 markers.
Type stubs are only used by type checkers and IDEs, never at runtime.

### `remove_pycache`

Removes files inside `__pycache__/` directories that sometimes get
included in wheels by buggy build systems.

## Normal-stage optimizers (order 500)

These transform `.py` source files in place.

### `remove_docstrings`

Strips docstrings from module, class, function, and async function bodies
using AST parsing and token manipulation. Preserves all runtime behavior
since docstrings are only used for documentation.

### `remove_type_annotations`

Strips type annotations using an AST `NodeTransformer` and `ast.unparse()`.
Handles all annotation locations:

- Function parameters (positional-only, regular, keyword-only, `*args`, `**kwargs`)
- Return type annotations
- Annotated assignments (`x: int = 5` → `x = 5`; bare `x: int` → `pass`)

**Preserves annotations in:**
- `@dataclass` classes
- `NamedTuple` subclasses
- `TypedDict` subclasses
- `Protocol` subclasses

These classes depend on annotations for their runtime behavior.

### `remove_assertions`

Replaces `assert` statements with `pass` using an AST `NodeTransformer`.
This is similar to running Python with the `-O` flag but applied at the
source level.

### `remove_comments`

Strips `#` comments from `.py` files using the `tokenize` module.
Correctly preserves strings that contain `#` characters and docstrings.

### `minify_whitespace`

Reduces indentation from 4 spaces (or whatever the file uses) to 1 space
per level and removes blank lines. Uses `tokenize` to detect the indent
unit, then rewrites line-by-line. String contents are preserved. This is
analogous to whitespace minification in JavaScript bundlers.

## Late-stage optimizers (order 900)

These run last, after all source transforms are complete.

### `compile_pyc`

Compiles `.py` files to `.pyc` bytecode using `py_compile` and removes
the original `.py` files. The `.pyc` file is placed next to the original
(not in `__pycache__/`). Files with syntax errors are skipped.
