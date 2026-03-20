from __future__ import annotations

from pathlib import Path

from wheel_optimizer.base import ORDER_EARLY, WheelOptimizer


class RemovePycacheOptimizer(WheelOptimizer):
    name = "remove_pycache"
    description = "Remove __pycache__ directories and stale .pyc files"
    default_enabled = False
    order = ORDER_EARLY

    def should_process(self, file_path: Path) -> bool:
        return _is_pycache_artifact(file_path)

    def process_file(self, full_path: Path) -> None:
        if full_path.is_file():
            full_path.unlink()


def _is_pycache_artifact(file_path: Path) -> bool:
    for part in file_path.parts:
        if part == "__pycache__":
            return True
    return False
