from pathlib import Path

from wheel_optimizer.optimizers.remove_comments import (
    RemoveCommentsOptimizer,
    _remove_comments,
)


def test_removes_inline_comment():
    source = b"x = 1  # set x\n"
    result = _remove_comments(source)
    assert b"# set x" not in result
    assert b"x = 1" in result


def test_removes_line_comment():
    source = b"# this is a comment\nx = 1\n"
    result = _remove_comments(source)
    assert b"# this is a comment" not in result
    assert b"x = 1" in result


def test_removes_multiple_comments():
    source = b"# first\nx = 1  # inline\n# second\ny = 2\n"
    result = _remove_comments(source)
    assert b"#" not in result
    assert b"x = 1" in result
    assert b"y = 2" in result


def test_preserves_strings_with_hash():
    source = b'x = "has # inside"\n'
    result = _remove_comments(source)
    assert b"has # inside" in result


def test_preserves_docstrings():
    source = b'def foo():\n    """A docstring."""\n    return 1\n'
    result = _remove_comments(source)
    assert b'"""A docstring."""' in result


def test_no_comments_returns_original():
    source = b"x = 1\ny = 2\n"
    result = _remove_comments(source)
    assert result == source


def test_preserves_shebang():
    source = b"#!/usr/bin/env python\nx = 1\n"
    result = _remove_comments(source)
    # Shebang is a COMMENT token, so it gets removed
    assert b"x = 1" in result


def test_result_is_valid_python():
    source = b"# module comment\ndef foo(x):  # func\n    # body\n    return x  # ret\n"
    result = _remove_comments(source)
    compile(result, "<test>", "exec")


def test_idempotent():
    source = b"x = 1  # comment\n"
    result1 = _remove_comments(source)
    result2 = _remove_comments(result1)
    assert result1 == result2


def test_should_process_py_files():
    opt = RemoveCommentsOptimizer()
    assert opt.should_process(Path("module.py")) is True
    assert opt.should_process(Path("pkg/sub/mod.py")) is True


def test_should_not_process_non_py():
    opt = RemoveCommentsOptimizer()
    assert opt.should_process(Path("data.json")) is False
    assert opt.should_process(Path("lib.so")) is False


def test_process_file_in_place(tmp_path: Path):
    source = b"x = 1  # comment\n"
    py_file = tmp_path / "mod.py"
    py_file.write_bytes(source)

    opt = RemoveCommentsOptimizer()
    opt.process_file(py_file)

    result = py_file.read_bytes()
    assert b"#" not in result
    assert b"x = 1" in result


def test_process_file_bad_token_no_crash(tmp_path: Path):
    bad = b"\xff\xfe"
    py_file = tmp_path / "bad.py"
    py_file.write_bytes(bad)

    opt = RemoveCommentsOptimizer()
    opt.process_file(py_file)

    assert py_file.read_bytes() == bad


def test_empty_file():
    result = _remove_comments(b"")
    assert result == b""


def test_only_comments():
    source = b"# just a comment\n# another\n"
    result = _remove_comments(source)
    assert b"#" not in result


def test_comment_after_function_def():
    source = b"def foo():  # my func\n    pass\n"
    result = _remove_comments(source)
    assert b"# my func" not in result
    assert b"def foo():" in result
    assert b"pass" in result
