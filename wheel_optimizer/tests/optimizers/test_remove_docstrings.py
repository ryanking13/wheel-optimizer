from pathlib import Path

import pytest

from wheel_optimizer.optimizers.remove_docstrings import (
    RemoveDocstringsOptimizer,
    _remove_docstrings,
)

SAMPLE_MODULE = '''\
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
    assert '"""Module docstring."""' not in result


def test_remove_function_docstring():
    result = _remove_docstrings(SAMPLE_MODULE)
    assert '"""Say hello."""' not in result


def test_remove_class_docstring():
    result = _remove_docstrings(SAMPLE_MODULE)
    assert '"""A greeter class."""' not in result


def test_remove_method_docstring():
    result = _remove_docstrings(SAMPLE_MODULE)
    assert '"""Instance method docstring."""' not in result


def test_remove_async_docstring():
    result = _remove_docstrings(SAMPLE_MODULE)
    assert '"""Async docstring."""' not in result


def test_preserves_code():
    result = _remove_docstrings(SAMPLE_MODULE)
    assert "def greet(name):" in result
    assert "class Greeter:" in result


def test_preserves_non_docstrings():
    source = 'x = """not a docstring"""\n'
    result = _remove_docstrings(source)
    assert '"""not a docstring"""' in result


def test_syntax_error_raises():
    with pytest.raises(SyntaxError):
        _remove_docstrings("def foo(:\n")


def test_no_docstrings_returns_original():
    source = "x = 1\ny = 2\n"
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
    py_file = tmp_path / "mod.py"
    py_file.write_text('def foo():\n    """Remove."""\n    return 1\n')

    opt = RemoveDocstringsOptimizer()
    opt.process_file(py_file)

    result = py_file.read_text()
    assert '"""Remove."""' not in result
    assert "return 1" in result


def test_process_file_syntax_error_no_crash(tmp_path: Path):
    py_file = tmp_path / "bad.py"
    py_file.write_text("def foo(:\n")

    opt = RemoveDocstringsOptimizer()
    opt.process_file(py_file)

    assert py_file.read_text() == "def foo(:\n"


def test_result_is_valid_python():
    result = _remove_docstrings(SAMPLE_MODULE)
    compile(result, "<test>", "exec")


def test_sole_docstring_class_gets_pass():
    source = 'class Foo:\n    """Only a docstring."""\n'
    result = _remove_docstrings(source)
    assert "pass" in result
    compile(result, "<test>", "exec")


def test_sole_docstring_function_gets_pass():
    source = 'def foo():\n    """Only a docstring."""\n'
    result = _remove_docstrings(source)
    assert "pass" in result
    compile(result, "<test>", "exec")


def test_idempotent():
    result1 = _remove_docstrings(SAMPLE_MODULE)
    result2 = _remove_docstrings(result1)
    assert result1 == result2


def test_empty_file():
    assert _remove_docstrings("") == ""
