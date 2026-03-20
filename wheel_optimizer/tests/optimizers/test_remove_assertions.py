from pathlib import Path

import pytest

from wheel_optimizer.optimizers.remove_assertions import (
    RemoveAssertionsOptimizer,
    _remove_assertions,
)


def test_removes_simple_assert():
    source = "x = 1\nassert x == 1\n"
    result = _remove_assertions(source)
    assert "assert" not in result


def test_removes_assert_with_message():
    source = 'assert x > 0, "must be positive"\n'
    result = _remove_assertions(source)
    assert "assert" not in result


def test_preserves_other_code():
    source = "x = 1\nassert x\ny = 2\n"
    result = _remove_assertions(source)
    assert "x = 1" in result
    assert "y = 2" in result


def test_removes_multiple_asserts():
    source = "assert a\nassert b\nassert c\n"
    result = _remove_assertions(source)
    assert "assert" not in result


def test_assert_in_function():
    source = "def foo():\n    assert True\n    return 1\n"
    result = _remove_assertions(source)
    assert "assert" not in result
    assert "return 1" in result


def test_assert_in_class():
    source = "class Foo:\n    def bar(self):\n        assert self\n"
    result = _remove_assertions(source)
    assert "assert" not in result


def test_no_asserts_returns_original():
    source = "x = 1\ny = 2\n"
    result = _remove_assertions(source)
    assert result == source


def test_syntax_error_raises():
    with pytest.raises(SyntaxError):
        _remove_assertions("def foo(:\n")


def test_result_is_valid_python():
    source = "def foo(x):\n    assert x > 0\n    assert isinstance(x, int), 'bad'\n    return x\n"
    result = _remove_assertions(source)
    compile(result, "<test>", "exec")


def test_idempotent():
    source = "assert True\nx = 1\n"
    result1 = _remove_assertions(source)
    result2 = _remove_assertions(result1)
    assert result1 == result2


def test_should_process_py_files():
    opt = RemoveAssertionsOptimizer()
    assert opt.should_process(Path("module.py")) is True
    assert opt.should_process(Path("pkg/sub/mod.py")) is True


def test_should_not_process_non_py():
    opt = RemoveAssertionsOptimizer()
    assert opt.should_process(Path("data.json")) is False
    assert opt.should_process(Path("lib.so")) is False


def test_process_file_in_place(tmp_path: Path):
    source = "assert True\nx = 1\n"
    py_file = tmp_path / "mod.py"
    py_file.write_text(source)

    opt = RemoveAssertionsOptimizer()
    opt.process_file(py_file)

    result = py_file.read_text()
    assert "assert" not in result
    assert "x = 1" in result


def test_process_file_syntax_error_no_crash(tmp_path: Path):
    bad = "def foo(:\n"
    py_file = tmp_path / "bad.py"
    py_file.write_text(bad)

    opt = RemoveAssertionsOptimizer()
    opt.process_file(py_file)

    assert py_file.read_text() == bad


def test_empty_file():
    result = _remove_assertions("")
    assert result == ""


def test_only_assert():
    source = "assert True\n"
    result = _remove_assertions(source)
    assert "assert" not in result
    compile(result, "<test>", "exec")
