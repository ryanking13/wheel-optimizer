from pathlib import Path

from wheel_optimizer.optimizers.remove_tests import (
    RemoveTestsOptimizer,
    _has_test_naming,
    _has_test_signals,
)


class TestNamingDetection:
    def test_test_directory(self):
        assert _has_test_naming(Path("tests/test_foo.py")) is True
        assert _has_test_naming(Path("test/something.py")) is True
        assert _has_test_naming(Path("testing/util.py")) is True
        assert _has_test_naming(Path("test_suite/run.py")) is True

    def test_nested_test_directory(self):
        assert _has_test_naming(Path("pkg/tests/conftest.py")) is True
        assert _has_test_naming(Path("pkg/sub/test/file.py")) is True

    def test_test_file_prefix(self):
        assert _has_test_naming(Path("test_module.py")) is True
        assert _has_test_naming(Path("tests_module.py")) is True

    def test_test_file_suffix(self):
        assert _has_test_naming(Path("module_test.py")) is True
        assert _has_test_naming(Path("module_tests.py")) is True

    def test_conftest(self):
        assert _has_test_naming(Path("conftest.py")) is True
        assert _has_test_naming(Path("pkg/conftest.py")) is True

    def test_ignores_non_test_files(self):
        assert _has_test_naming(Path("module.py")) is False
        assert _has_test_naming(Path("pkg/utils.py")) is False
        assert _has_test_naming(Path("data.json")) is False

    def test_ignores_test_like_names_without_convention(self):
        assert _has_test_naming(Path("contest.py")) is False
        assert _has_test_naming(Path("latest.py")) is False
        assert _has_test_naming(Path("attest.py")) is False

    def test_case_insensitive_dirs(self):
        assert _has_test_naming(Path("Tests/foo.py")) is True
        assert _has_test_naming(Path("TESTS/foo.py")) is True

    def test_non_py_test_prefix_not_matched(self):
        assert _has_test_naming(Path("test_data.json")) is False
        assert _has_test_naming(Path("test_image.png")) is False
        assert _has_test_naming(Path("test_module.txt")) is False

    def test_files_inside_test_dir_matched(self):
        assert _has_test_naming(Path("tests/helpers.py")) is True
        assert _has_test_naming(Path("tests/fixtures/data.json")) is True
        assert _has_test_naming(Path("tests/__init__.py")) is True


class TestSignalDetection:
    def test_detects_pytest_import(self, tmp_path: Path):
        f = tmp_path / "t.py"
        f.write_text("import pytest\n\ndef test_foo():\n    assert True\n")
        assert _has_test_signals(f) is True

    def test_detects_from_pytest(self, tmp_path: Path):
        f = tmp_path / "t.py"
        f.write_text("from pytest import fixture\n")
        assert _has_test_signals(f) is True

    def test_detects_unittest_import(self, tmp_path: Path):
        f = tmp_path / "t.py"
        f.write_text("import unittest\n\nclass TestFoo(unittest.TestCase):\n    pass\n")
        assert _has_test_signals(f) is True

    def test_detects_from_unittest(self, tmp_path: Path):
        f = tmp_path / "t.py"
        f.write_text("from unittest import TestCase\n")
        assert _has_test_signals(f) is True

    def test_detects_test_function_def(self, tmp_path: Path):
        f = tmp_path / "t.py"
        f.write_text("def test_something():\n    assert 1 == 1\n")
        assert _has_test_signals(f) is True

    def test_detects_test_class(self, tmp_path: Path):
        f = tmp_path / "t.py"
        f.write_text("class TestMyFeature:\n    def test_it(self):\n        pass\n")
        assert _has_test_signals(f) is True

    def test_no_signals_in_regular_code(self, tmp_path: Path):
        f = tmp_path / "t.py"
        f.write_text("def helper():\n    return 42\n")
        assert _has_test_signals(f) is False

    def test_no_signals_in_empty_file(self, tmp_path: Path):
        f = tmp_path / "t.py"
        f.write_text("")
        assert _has_test_signals(f) is False

    def test_no_signals_in_init_file(self, tmp_path: Path):
        f = tmp_path / "__init__.py"
        f.write_text("")
        assert _has_test_signals(f) is False

    def test_nonexistent_file_returns_false(self, tmp_path: Path):
        f = tmp_path / "gone.py"
        assert _has_test_signals(f) is False


class TestProcessFile:
    def test_removes_confirmed_test_file(self, tmp_path: Path):
        f = tmp_path / "test_foo.py"
        f.write_text("import pytest\n\ndef test_bar():\n    assert True\n")

        opt = RemoveTestsOptimizer()
        opt.process_file(f)

        assert not f.exists()

    def test_keeps_test_named_file_without_signals(self, tmp_path: Path):
        f = tmp_path / "test_utils.py"
        f.write_text("def helper():\n    return 42\n")

        opt = RemoveTestsOptimizer()
        opt.process_file(f)

        assert f.exists()

    def test_keeps_empty_init_in_test_dir(self, tmp_path: Path):
        test_dir = tmp_path / "tests"
        test_dir.mkdir()
        init = test_dir / "__init__.py"
        init.write_text("")

        opt = RemoveTestsOptimizer()
        opt.process_file(init)

        assert init.exists()

    def test_keeps_non_py_files(self, tmp_path: Path):
        f = tmp_path / "test_data.json"
        f.write_text('{"key": "value"}')

        opt = RemoveTestsOptimizer()
        opt.process_file(f)

        assert f.exists()

    def test_keeps_conftest_without_pytest(self, tmp_path: Path):
        f = tmp_path / "conftest.py"
        f.write_text("DATA = [1, 2, 3]\n")

        opt = RemoveTestsOptimizer()
        opt.process_file(f)

        assert f.exists()

    def test_removes_conftest_with_pytest(self, tmp_path: Path):
        f = tmp_path / "conftest.py"
        f.write_text("import pytest\n\n@pytest.fixture\ndef db():\n    return {}\n")

        opt = RemoveTestsOptimizer()
        opt.process_file(f)

        assert not f.exists()

    def test_removes_unittest_file(self, tmp_path: Path):
        f = tmp_path / "test_stuff.py"
        f.write_text(
            "import unittest\n\n"
            "class TestStuff(unittest.TestCase):\n"
            "    def test_it(self):\n"
            "        self.assertTrue(True)\n"
        )

        opt = RemoveTestsOptimizer()
        opt.process_file(f)

        assert not f.exists()

    def test_skips_directories(self, tmp_path: Path):
        d = tmp_path / "tests"
        d.mkdir()

        opt = RemoveTestsOptimizer()
        opt.process_file(d)

        assert d.exists()

    def test_keeps_helper_in_test_dir(self, tmp_path: Path):
        test_dir = tmp_path / "tests"
        test_dir.mkdir()
        helper = test_dir / "helpers.py"
        helper.write_text("def make_fixture():\n    return {}\n")

        opt = RemoveTestsOptimizer()
        opt.process_file(helper)

        assert helper.exists()


class TestShouldProcess:
    def test_matches_test_naming(self):
        opt = RemoveTestsOptimizer()
        assert opt.should_process(Path("tests/test_foo.py")) is True
        assert opt.should_process(Path("module.py")) is False

    def test_order_is_early(self):
        from wheel_optimizer.base import ORDER_EARLY

        opt = RemoveTestsOptimizer()
        assert opt.order == ORDER_EARLY


class TestEndToEnd:
    def test_pipeline_only_removes_confirmed_tests(self, tmp_path: Path):
        from wheel_optimizer.config import OptimizerConfig
        from wheel_optimizer.pipeline import OptimizerPipeline

        test_dir = tmp_path / "tests"
        test_dir.mkdir()
        (test_dir / "__init__.py").write_text("")
        (test_dir / "test_foo.py").write_text(
            "import pytest\n\ndef test_x():\n    assert True\n"
        )
        (test_dir / "helpers.py").write_text("DATA = 1\n")
        (test_dir / "fixture.json").write_text("{}")

        pkg_dir = tmp_path / "mypkg"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "core.py").write_text("x = 1\n")

        config = OptimizerConfig(remove_tests=True)
        OptimizerPipeline(config).run(tmp_path)

        assert not (test_dir / "test_foo.py").exists()
        assert (test_dir / "__init__.py").exists()
        assert (test_dir / "helpers.py").exists()
        assert (test_dir / "fixture.json").exists()
        assert (pkg_dir / "core.py").exists()
