from pathlib import Path

from wheel_optimizer.optimizers.minify_whitespace import (
    MinifyWhitespaceOptimizer,
    _minify_whitespace,
)


class TestIndentReduction:
    def test_4_space_to_1(self):
        source = b"def foo():\n    return 1\n"
        result = _minify_whitespace(source)
        assert result == b"def foo():\n return 1\n"

    def test_nested_indent(self):
        source = b"def foo():\n    if True:\n        return 1\n"
        result = _minify_whitespace(source)
        assert result == b"def foo():\n if True:\n  return 1\n"

    def test_deeply_nested(self):
        source = b"class A:\n    def b(self):\n        if True:\n            for x in y:\n                pass\n"
        result = _minify_whitespace(source)
        assert (
            result == b"class A:\n def b(self):\n  if True:\n   for x in y:\n    pass\n"
        )

    def test_already_1_space(self):
        source = b"def foo():\n return 1\n"
        result = _minify_whitespace(source)
        assert b"return 1" in result


class TestBlankLineRemoval:
    def test_removes_blank_lines(self):
        source = b"x = 1\n\ny = 2\n\nz = 3\n"
        result = _minify_whitespace(source)
        assert b"\n\n" not in result
        assert b"x = 1" in result
        assert b"z = 3" in result

    def test_removes_blank_lines_in_function(self):
        source = b"def foo():\n    x = 1\n\n    y = 2\n"
        result = _minify_whitespace(source)
        assert b"\n\n" not in result

    def test_multiple_consecutive_blanks(self):
        source = b"x = 1\n\n\n\ny = 2\n"
        result = _minify_whitespace(source)
        assert b"\n\n" not in result


class TestPreservation:
    def test_result_is_valid_python(self):
        source = b"class Foo:\n    def bar(self):\n        if True:\n            return 1\n        return 2\n"
        result = _minify_whitespace(source)
        compile(result, "<test>", "exec")

    def test_preserves_strings_with_spaces(self):
        source = b'x = "  hello  "\n'
        result = _minify_whitespace(source)
        assert b'"  hello  "' in result

    def test_preserves_empty_file(self):
        assert _minify_whitespace(b"") == b""
        assert _minify_whitespace(b"\n") == b"\n"

    def test_no_trailing_newline_preserved(self):
        source = b"x = 1"
        result = _minify_whitespace(source)
        assert not result.endswith(b"\n")

    def test_trailing_newline_preserved(self):
        source = b"x = 1\n"
        result = _minify_whitespace(source)
        assert result.endswith(b"\n")


class TestIdempotent:
    def test_idempotent(self):
        source = b"def foo():\n    if True:\n        return 1\n"
        result1 = _minify_whitespace(source)
        result2 = _minify_whitespace(result1)
        assert result1 == result2


class TestShouldProcess:
    def test_py_files(self):
        opt = MinifyWhitespaceOptimizer()
        assert opt.should_process(Path("module.py")) is True

    def test_non_py(self):
        opt = MinifyWhitespaceOptimizer()
        assert opt.should_process(Path("data.json")) is False


class TestProcessFile:
    def test_in_place(self, tmp_path: Path):
        source = b"def foo():\n    return 1\n"
        f = tmp_path / "mod.py"
        f.write_bytes(source)

        opt = MinifyWhitespaceOptimizer()
        opt.process_file(f)

        result = f.read_bytes()
        assert result == b"def foo():\n return 1\n"

    def test_syntax_error_no_crash(self, tmp_path: Path):
        bad = b"def foo(:\n"
        f = tmp_path / "bad.py"
        f.write_bytes(bad)

        opt = MinifyWhitespaceOptimizer()
        opt.process_file(f)

        assert f.read_bytes() == bad


class TestEndToEnd:
    def test_pipeline(self, tmp_path: Path):
        from wheel_optimizer.config import OptimizerConfig
        from wheel_optimizer.pipeline import OptimizerPipeline

        pkg = tmp_path / "mypkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "core.py").write_bytes(b"def foo():\n    x = 1\n\n    return x\n")

        config = OptimizerConfig(minify_whitespace=True)
        OptimizerPipeline(config).run(tmp_path)

        result = (pkg / "core.py").read_bytes()
        assert b"\n\n" not in result
        assert b"    " not in result
        compile(result, "<test>", "exec")


class TestRealWorldPatterns:
    def test_class_with_methods(self):
        source = (
            b"class Calculator:\n"
            b"    def __init__(self):\n"
            b"        self.value = 0\n"
            b"\n"
            b"    def add(self, n):\n"
            b"        self.value += n\n"
            b"        return self\n"
        )
        result = _minify_whitespace(source)
        compile(result, "<test>", "exec")
        assert b"    " not in result

    def test_try_except(self):
        source = (
            b"def safe():\n"
            b"    try:\n"
            b"        return 1\n"
            b"    except Exception:\n"
            b"        return 0\n"
        )
        result = _minify_whitespace(source)
        compile(result, "<test>", "exec")

    def test_multiline_string_not_corrupted(self):
        source = b'x = """\n    indented\n    text\n"""\n'
        result = _minify_whitespace(source)
        assert b"indented" in result
