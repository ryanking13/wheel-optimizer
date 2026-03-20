from __future__ import annotations

from pathlib import Path

from wheel_optimizer.base import ORDER_EARLY, WheelOptimizer

_CYTHON_EXTENSIONS = frozenset(
    {
        ".pyx",
        ".pxd",
        ".pxi",
    }
)


class RemoveCythonSourceOptimizer(WheelOptimizer):
    name = "remove_cython_source"
    description = "Remove Cython source files shipped alongside compiled extensions"
    default_enabled = False
    order = ORDER_EARLY

    def should_process(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in _CYTHON_EXTENSIONS

    def process_file(self, full_path: Path) -> None:
        if full_path.is_file():
            full_path.unlink()
