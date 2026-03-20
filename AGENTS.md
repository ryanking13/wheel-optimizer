# AGENTS.md

## What this project is

A standalone, generic wheel optimization library extracted from [pyodide-build](https://github.com/pyodide/pyodide-build). It provides a pluggable pipeline that transforms files inside unpacked wheel directories to reduce size (strip docstrings, type hints, tests, etc.) before distribution.

The origin issue is [pyodide-build#309](https://github.com/pyodide/pyodide-build/issues/309) and the proof-of-concept is [pyodide-build#310](https://github.com/pyodide/pyodide-build/pull/310). This repo extracts the generic parts; pyodide-build will depend on this package and provide its own config loading and integration glue.

## The boundary: what belongs here vs. pyodide-build

This package is a **library**, not an application. It knows nothing about pyodide, `meta.yaml`, `[tool.pyodide.optimizer]`, or how wheels get built. The contract:

- **This repo**: `WheelOptimizer` ABC, `OptimizerConfig`, `OptimizerPipeline`, and all optimizer implementations (docstring removal, type stripping, etc.)
- **pyodide-build**: Config loading from `pyproject.toml`/`meta.yaml`, merging global+per-package configs, calling `OptimizerPipeline.run()` inside its `modify_wheel()` flow.

When adding features, ask: "Would a non-pyodide project also want this?" If yes, it goes here. If it's about pyodide's config format or build pipeline, it stays in pyodide-build.

## Development

Use `uv` for all Python operations:

```
uv pip install -e . --group test    # install with test deps
uv run pytest                       # run tests
uv run mypy wheel_optimizer/        # type check (tests excluded)
uv run ruff check wheel_optimizer/  # lint
uv run ruff format wheel_optimizer/ # format
```

## Conventions (follow pyodide-build)

Tooling choices mirror [pyodide/pyodide-build](https://github.com/pyodide/pyodide-build) intentionally. When in doubt about style or config, check what pyodide-build does and match it.

- **Build**: hatchling + hatch-vcs. Version comes from git tags.
- **Lint/format**: ruff only (no black, no flake8, no isort separately).
- **Type check**: mypy. Strict on source, excluded on tests.
- **Test**: pytest + pytest-cov. Tests live inside the package at `wheel_optimizer/tests/` and are excluded from sdist.
- **CI actions**: Always pin to full commit SHA, never floating tags.
- **Dev deps**: PEP 735 dependency groups (`[dependency-groups]`), not `[project.optional-dependencies]`.

## Type annotations

All functions and methods must have complete type annotations. `mypy` runs in strict mode on source code (`wheel_optimizer/tests/` is excluded). No `as any`, `type: ignore` without an error code, or untyped public APIs.

- Every function signature: annotate all parameters and return type.
- Use `from __future__ import annotations` when forward references or `TYPE_CHECKING` imports are needed.
- Prefer precise types over broad ones (`ast.expr` over `ast.AST` when you know the node type).

## Testing

Tests follow TDD: write tests **before** the implementation, not after. Each optimizer must have extensive test coverage in `wheel_optimizer/tests/optimizers/test_<name>.py`.

An optimizer's test file should cover at minimum:

- **Core behavior**: Does it transform what it claims to? Test each category of transformation individually.
- **Preservation**: Does it leave unrelated code intact? Verify strings, comments, and logic that look similar to targets but shouldn't be touched.
- **Edge cases**: Empty files, syntax errors, files with only the target construct, deeply nested constructs, unicode content.
- **`should_process` filtering**: Correct file extensions accepted, others rejected.
- **`process_file` in-place mutation**: Write to a temp file, run the optimizer, read back and assert.
- **Round-trip validity**: The output must be valid Python (`compile(result, "<test>", "exec")`).
- **No-op idempotency**: Running the optimizer on already-optimized output should produce identical output.

Pipeline and config tests live in `wheel_optimizer/tests/test_pipeline.py` and `wheel_optimizer/tests/test_config.py`.

## Zero runtime dependencies

This package has **no runtime dependencies**. Keep it that way. The config model uses stdlib `dataclasses`, not pydantic. Optimizer implementations should use only stdlib modules (`ast`, `tokenize`, `pathlib`, etc.). If an optimizer genuinely needs an external dep, it should be an optional extra with a lazy import.

## How to add a new optimizer

1. Create `wheel_optimizer/optimizers/<name>.py` with a class that subclasses `WheelOptimizer`.
2. Set `name` to match the config field name (e.g., `name = "remove_types"`).
3. Add a corresponding `bool` field to `OptimizerConfig` in `config.py` (default `False`).
4. Register the instance in `_get_all_optimizers()` in `pipeline.py`.
5. Add tests in `wheel_optimizer/tests/optimizers/test_<name>.py`.
6. The pipeline handles everything else: resolving enabled optimizers from config, ordering by `.order`, walking files, skipping `.dist-info`.

The optimizer interface is two methods:
- `should_process(file_path: Path) -> bool` — receives the path **relative** to wheel root.
- `process_file(full_path: Path) -> None` — receives the **absolute** path; modify the file in-place.

Use `ORDER_EARLY` (100) for optimizers that delete entire files, `ORDER_NORMAL` (500) for source transforms, `ORDER_LATE` (900) for compilation steps like `.py` → `.pyc`.

## Architecture notes

- `pipeline.py` uses a lazy `_get_all_optimizers()` function with local imports to avoid circular imports and keep module load time minimal.
- `_resolve_optimizers` uses `getattr(config, opt.name, opt.default_enabled)` to match optimizer names to config fields. This means the optimizer's `name` attribute **must** exactly match the `OptimizerConfig` field name.
- The pipeline never touches `.dist-info/` contents — wheel metadata must stay intact.
