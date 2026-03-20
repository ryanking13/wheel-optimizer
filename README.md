# wheel-optimizer

Pluggable post-processing optimizers for Python wheels. Reduce wheel size by stripping docstrings, type hints, and other unnecessary data from `.py` files before distribution.

## Installation

```
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

## Documentation

Full documentation is available at [wheel-optimizer.readthedocs.io](https://wheel-optimizer.readthedocs.io/).

## License

MIT
