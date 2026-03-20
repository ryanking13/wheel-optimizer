from __future__ import annotations

import shutil
from pathlib import Path

from wheel_optimizer.base import ORDER_EARLY, WheelOptimizer

_TEST_DIR_NAMES = frozenset(
    {
        "test",
        "tests",
        "testing",
        "test_suite",
    }
)

_TEST_FILE_PREFIXES = ("test_", "tests_")
_TEST_FILE_SUFFIXES = ("_test.py", "_tests.py")
_TEST_FILE_EXACT = frozenset(
    {
        "conftest.py",
    }
)


class RemoveTestsOptimizer(WheelOptimizer):
    name = "remove_tests"
    description = "Remove test directories and files"
    default_enabled = False
    order = ORDER_EARLY

    def should_process(self, file_path: Path) -> bool:
        return _is_test_path(file_path)

    def process_file(self, full_path: Path) -> None:
        if full_path.is_dir():
            shutil.rmtree(full_path)
        elif full_path.is_file():
            full_path.unlink()


def _is_test_path(file_path: Path) -> bool:
    for part in file_path.parts:
        if part.lower() in _TEST_DIR_NAMES:
            return True

    name = file_path.name.lower()

    if name in _TEST_FILE_EXACT:
        return True

    if name.endswith(".py"):
        for prefix in _TEST_FILE_PREFIXES:
            if name.startswith(prefix):
                return True
        for suffix in _TEST_FILE_SUFFIXES:
            if name.endswith(suffix):
                return True

    return False
