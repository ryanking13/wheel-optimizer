from pathlib import Path

import pytest

from wheel_optimizer.optimizers.remove_docstrings import (
    RemoveDocstringsOptimizer,
    _remove_docstrings,
)

SAMPLE_MODULE = b'''\
"""Module docstring."""


def greet(name):
    """Say hello."""
    return f"Hello, {name}"


class Greeter:
    """A greeter class."""

    def hello(self):
        """Instance method docstring."""
        return "hi"


async def async_greet():
    """Async docstring."""
    return "async hi"
'''


def test_remove_module_docstring():
    result = _remove_docstrings(SAMPLE_MODULE)
    assert b'"""Module docstring."""' not in result


def test_remove_function_docstring():
    result = _remove_docstrings(SAMPLE_MODULE)
    assert b'"""Say hello."""' not in result


def test_remove_class_docstring():
    result = _remove_docstrings(SAMPLE_MODULE)
    assert b'"""A greeter class."""' not in result


def test_remove_method_docstring():
    result = _remove_docstrings(SAMPLE_MODULE)
    assert b'"""Instance method docstring."""' not in result


def test_remove_async_docstring():
    result = _remove_docstrings(SAMPLE_MODULE)
    assert b'"""Async docstring."""' not in result


def test_preserves_code():
    result = _remove_docstrings(SAMPLE_MODULE)
    assert b"def greet(name):" in result
    assert b'return f"Hello, {name}"' in result
    assert b"class Greeter:" in result
    assert b'return "hi"' in result
    assert b'return "async hi"' in result


def test_preserves_non_docstrings():
    source = b'x = """not a docstring"""\n'
    result = _remove_docstrings(source)
    assert b'"""not a docstring"""' in result


def test_syntax_error_raises():
    source = b"def foo(:\n"
    with pytest.raises(SyntaxError):
        _remove_docstrings(source)


def test_no_docstrings_returns_original():
    source = b"x = 1\ny = 2\n"
    result = _remove_docstrings(source)
    assert result == source


def test_should_process_py_files():
    opt = RemoveDocstringsOptimizer()
    assert opt.should_process(Path("module.py")) is True
    assert opt.should_process(Path("pkg/sub/mod.py")) is True


def test_should_not_process_non_py():
    opt = RemoveDocstringsOptimizer()
    assert opt.should_process(Path("data.json")) is False
    assert opt.should_process(Path("lib.so")) is False
    assert opt.should_process(Path("README.md")) is False


def test_process_file_in_place(tmp_path: Path):
    source = b'def foo():\n    """Remove."""\n    return 1\n'
    py_file = tmp_path / "mod.py"
    py_file.write_bytes(source)

    opt = RemoveDocstringsOptimizer()
    opt.process_file(py_file)

    result = py_file.read_bytes()
    assert b'"""Remove."""' not in result
    assert b"return 1" in result


def test_process_file_syntax_error_no_crash(tmp_path: Path):
    bad_source = b"def foo(:\n"
    py_file = tmp_path / "bad.py"
    py_file.write_bytes(bad_source)

    opt = RemoveDocstringsOptimizer()
    opt.process_file(py_file)

    assert py_file.read_bytes() == bad_source


def test_result_is_valid_python():
    result = _remove_docstrings(SAMPLE_MODULE)
    compile(result, "<test>", "exec")
