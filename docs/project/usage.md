# Usage

## Installation

```bash
pip install wheel-optimizer
```

## Quick start

```python
from pathlib import Path

from wheel_optimizer import OptimizerConfig, OptimizerPipeline

config = OptimizerConfig(
    remove_docstrings=True,
    remove_type_annotations=True,
    remove_assertions=True,
    remove_comments=True,
)
pipeline = OptimizerPipeline(config)
pipeline.run(Path("unpacked-wheel-directory/"))
```

The pipeline operates on an **unpacked wheel directory** — you unzip the `.whl` first,
run the pipeline, then repack it. The pipeline never touches `.dist-info/` contents,
so wheel metadata stays intact.

## Configuration

All optimizers are **off by default**. Enable them explicitly via `OptimizerConfig`:

```python
config = OptimizerConfig(
    remove_docstrings=True,
    remove_type_annotations=True,
    remove_assertions=True,
    remove_comments=True,
    remove_tests=True,
    remove_typestubs=True,
    remove_pycache=True,
    compile_pyc=True,
)
```

To disable all optimizers regardless of individual settings:

```python
config = OptimizerConfig(disable_all=True, remove_docstrings=True)
# Nothing runs — disable_all takes precedence
```

## Execution order

Optimizers run in a fixed order based on their `order` attribute:

1. **Early** (100) — File/directory deletion (`remove_tests`, `remove_typestubs`, `remove_pycache`)
2. **Normal** (500) — Source transforms (`remove_docstrings`, `remove_type_annotations`, `remove_assertions`, `remove_comments`)
3. **Late** (900) — Compilation (`compile_pyc`)

This ensures files are deleted before being unnecessarily transformed,
and source transforms happen before compilation to `.pyc`.
