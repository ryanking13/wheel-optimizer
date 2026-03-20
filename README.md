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

config = OptimizerConfig(remove_docstrings=True)
pipeline = OptimizerPipeline(config)
pipeline.run(Path("unpacked-wheel-directory/"))
```

## Available optimizers

| Name | Description | Default |
|------|-------------|---------|
| `remove_docstrings` | Strip docstrings from `.py` files | off |

## Writing a custom optimizer

```python
from pathlib import Path

from wheel_optimizer import WheelOptimizer


class RemoveCommentsOptimizer(WheelOptimizer):
    name = "remove_comments"
    description = "Strip comments from .py files"
    default_enabled = False

    def should_process(self, file_path: Path) -> bool:
        return file_path.suffix == ".py"

    def process_file(self, full_path: Path) -> None:
        ...
```

## License

MIT
