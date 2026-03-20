# Writing a custom optimizer

## Basics

Create a class that subclasses `WheelOptimizer` and implement two methods:

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

### `should_process(file_path)`

Receives the path **relative** to the wheel root. Return `True` if this
optimizer should process the file.

### `process_file(full_path)`

Receives the **absolute** path. Modify the file in-place or delete it.

## Execution order

Set the `order` attribute to control when your optimizer runs:

```python
from wheel_optimizer import ORDER_EARLY, ORDER_NORMAL, ORDER_LATE

class MyOptimizer(WheelOptimizer):
    order = ORDER_EARLY  # 100 — runs before source transforms
```

| Constant | Value | Use for |
|----------|-------|---------|
| `ORDER_EARLY` | 100 | Deleting entire files or directories |
| `ORDER_NORMAL` | 500 | Source code transforms |
| `ORDER_LATE` | 900 | Compilation steps (`.py` → `.pyc`) |

## Registration

To make your optimizer available via `OptimizerConfig`:

1. Add a `bool` field to `OptimizerConfig` in `config.py` with the **same name**
   as your optimizer's `name` attribute:

   ```python
   @dataclass(frozen=True)
   class OptimizerConfig:
       my_optimizer: bool = False
   ```

2. Register the instance in `_get_all_optimizers()` in `pipeline.py`:

   ```python
   def _get_all_optimizers():
       from mypackage import MyOptimizer
       return [
           ...,
           MyOptimizer(),
       ]
   ```

The pipeline matches optimizer names to config fields via
`getattr(config, optimizer.name)`.
