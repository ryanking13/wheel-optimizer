from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wheel_optimizer.base import WheelOptimizer
    from wheel_optimizer.config import OptimizerConfig

logger = logging.getLogger(__name__)


def _get_all_optimizers() -> list[WheelOptimizer]:
    from wheel_optimizer.optimizers.compile_pyc import CompilePycOptimizer
    from wheel_optimizer.optimizers.minify_whitespace import MinifyWhitespaceOptimizer
    from wheel_optimizer.optimizers.remove_assertions import RemoveAssertionsOptimizer
    from wheel_optimizer.optimizers.remove_c_source import RemoveCSourceOptimizer
    from wheel_optimizer.optimizers.remove_comments import RemoveCommentsOptimizer
    from wheel_optimizer.optimizers.remove_cython_source import (
        RemoveCythonSourceOptimizer,
    )
    from wheel_optimizer.optimizers.remove_docstrings import RemoveDocstringsOptimizer
    from wheel_optimizer.optimizers.remove_pycache import RemovePycacheOptimizer
    from wheel_optimizer.optimizers.remove_tests import RemoveTestsOptimizer
    from wheel_optimizer.optimizers.remove_type_annotations import (
        RemoveTypeAnnotationsOptimizer,
    )
    from wheel_optimizer.optimizers.remove_typestubs import RemoveTypestubsOptimizer

    return [
        RemoveTestsOptimizer(),
        RemoveTypestubsOptimizer(),
        RemovePycacheOptimizer(),
        RemoveCSourceOptimizer(),
        RemoveCythonSourceOptimizer(),
        RemoveDocstringsOptimizer(),
        RemoveTypeAnnotationsOptimizer(),
        RemoveAssertionsOptimizer(),
        RemoveCommentsOptimizer(),
        MinifyWhitespaceOptimizer(),
        CompilePycOptimizer(),
    ]


class OptimizerPipeline:
    def __init__(self, config: OptimizerConfig) -> None:
        self.optimizers = _resolve_optimizers(config)

    def run(self, wheel_dir: Path) -> None:
        if not self.optimizers:
            return

        names = ", ".join(o.name for o in self.optimizers)
        logger.info("Running optimizers: %s", names)

        for optimizer in self.optimizers:
            _run_single(optimizer, wheel_dir)


def _resolve_optimizers(config: OptimizerConfig) -> list[WheelOptimizer]:
    if config.disable_all:
        return []

    enabled: list[WheelOptimizer] = []
    for opt in _get_all_optimizers():
        is_enabled = getattr(config, opt.name, opt.default_enabled)
        if is_enabled:
            enabled.append(opt)

    enabled.sort(key=lambda o: o.order)
    return enabled


def _run_single(optimizer: WheelOptimizer, wheel_dir: Path) -> None:
    processed = 0
    for file_path in sorted(wheel_dir.rglob("*")):
        if not file_path.is_file():
            continue

        relative = file_path.relative_to(wheel_dir)

        if relative.parts and relative.parts[0].endswith(".dist-info"):
            continue

        if optimizer.should_process(relative):
            optimizer.process_file(file_path)
            processed += 1

    logger.info(
        "Optimizer %s: processed %d file(s)",
        optimizer.name,
        processed,
    )
