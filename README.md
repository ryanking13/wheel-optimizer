# wheel-optimizer

Pluggable post-processing optimizers for Python wheels. Reduce wheel size by stripping docstrings, type hints, and other unnecessary data from `.py` files before distribution.

## Installation

```
pip install wheel-optimizer
```

## Usage

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

## Available optimizers

| Name | Description | Default | Order |
|------|-------------|---------|-------|
| `remove_tests` | Remove test files confirmed to contain test framework usage | off | early |
| `remove_typestubs` | Remove `.pyi` type stub files and `py.typed` markers | off | early |
| `remove_pycache` | Remove `__pycache__/` contents | off | early |
| `remove_docstrings` | Strip docstrings from `.py` files | off | normal |
| `remove_type_annotations` | Strip type annotations (preserves dataclass/NamedTuple/TypedDict/Protocol fields) | off | normal |
| `remove_assertions` | Strip `assert` statements | off | normal |
| `remove_comments` | Strip `#` comments | off | normal |
| `compile_pyc` | Compile `.py` → `.pyc` and remove originals | off | late |

## Writing a custom optimizer

```python
from pathlib import Path

from wheel_optimizer import WheelOptimizer


class MyOptimizer(WheelOptimizer):
    name = "my_optimizer"
    description = "My custom optimization"
    default_enabled = False

    def should_process(self, file_path: Path) -> bool:
        return file_path.suffix == ".py"

    def process_file(self, full_path: Path) -> None:
        ...
```

## License

MIT
