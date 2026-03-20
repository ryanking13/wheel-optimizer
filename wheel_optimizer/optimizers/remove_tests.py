from __future__ import annotations

from pathlib import Path

from wheel_optimizer.base import ORDER_EARLY, WheelOptimizer

_TEST_DIR_NAMES = frozenset(
    {
        "test",
        "tests",
    }
)

_TEST_FILE_PREFIXES = ("test_", "tests_")
_TEST_FILE_SUFFIXES = ("_test.py", "_tests.py")
_TEST_FILE_EXACT = frozenset(
    {
        "conftest.py",
    }
)

_TEST_FRAMEWORK_SIGNALS = (
    b"import pytest",
    b"from pytest",
    b"import unittest",
    b"from unittest",
)

_TEST_DEFINITION_SIGNALS = (
    b"def test_",
    b"class Test",
)


class RemoveTestsOptimizer(WheelOptimizer):
    name = "remove_tests"
    description = "Remove test files confirmed to contain test framework usage"
    default_enabled = False
    order = ORDER_EARLY

    def should_process(self, file_path: Path) -> bool:
        return _has_test_naming(file_path)

    def process_file(self, full_path: Path) -> None:
        if not full_path.is_file():
            return

        if full_path.suffix == ".py":
            if not _has_test_signals(full_path):
                return
            full_path.unlink()
        elif _in_test_directory(full_path):
            full_path.unlink()


def _in_test_directory(file_path: Path) -> bool:
    for part in file_path.parts[:-1]:
        if part.lower() in _TEST_DIR_NAMES:
            return True
    return False


def _has_test_naming(file_path: Path) -> bool:
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


def _has_test_signals(full_path: Path) -> bool:
    try:
        content = full_path.read_bytes()
    except OSError:
        return False

    for signal in _TEST_FRAMEWORK_SIGNALS:
        if signal in content:
            return True

    for signal in _TEST_DEFINITION_SIGNALS:
        if signal in content:
            return True

    return False
