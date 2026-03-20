from __future__ import annotations

from pathlib import Path

from wheel_optimizer.base import ORDER_EARLY, WheelOptimizer


class RemoveTypestubsOptimizer(WheelOptimizer):
    name = "remove_typestubs"
    description = "Remove .pyi type stub files and py.typed markers"
    default_enabled = False
    order = ORDER_EARLY

    def should_process(self, file_path: Path) -> bool:
        return file_path.suffix == ".pyi" or file_path.name == "py.typed"

    def process_file(self, full_path: Path) -> None:
        if full_path.is_file():
            full_path.unlink()
