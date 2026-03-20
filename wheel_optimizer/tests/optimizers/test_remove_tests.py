from pathlib import Path

from wheel_optimizer.optimizers.remove_tests import (
    RemoveTestsOptimizer,
    _is_test_path,
)


def test_detects_test_directory():
    assert _is_test_path(Path("tests/test_foo.py")) is True
    assert _is_test_path(Path("test/something.py")) is True
    assert _is_test_path(Path("testing/util.py")) is True
    assert _is_test_path(Path("test_suite/run.py")) is True


def test_detects_nested_test_directory():
    assert _is_test_path(Path("pkg/tests/conftest.py")) is True
    assert _is_test_path(Path("pkg/sub/test/file.py")) is True


def test_detects_test_file_prefix():
    assert _is_test_path(Path("test_module.py")) is True
    assert _is_test_path(Path("tests_module.py")) is True


def test_detects_test_file_suffix():
    assert _is_test_path(Path("module_test.py")) is True
    assert _is_test_path(Path("module_tests.py")) is True


def test_detects_conftest():
    assert _is_test_path(Path("conftest.py")) is True
    assert _is_test_path(Path("pkg/conftest.py")) is True


def test_ignores_non_test_files():
    assert _is_test_path(Path("module.py")) is False
    assert _is_test_path(Path("pkg/utils.py")) is False
    assert _is_test_path(Path("data.json")) is False


def test_ignores_test_like_names_without_convention():
    assert _is_test_path(Path("contest.py")) is False
    assert _is_test_path(Path("latest.py")) is False
    assert _is_test_path(Path("attest.py")) is False


def test_case_insensitive_dirs():
    assert _is_test_path(Path("Tests/foo.py")) is True
    assert _is_test_path(Path("TESTS/foo.py")) is True


def test_should_process_matches_is_test_path():
    opt = RemoveTestsOptimizer()
    assert opt.should_process(Path("tests/test_foo.py")) is True
    assert opt.should_process(Path("module.py")) is False


def test_process_file_deletes_file(tmp_path: Path):
    test_file = tmp_path / "test_foo.py"
    test_file.write_text("assert True\n")

    opt = RemoveTestsOptimizer()
    opt.process_file(test_file)

    assert not test_file.exists()


def test_process_file_deletes_directory(tmp_path: Path):
    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    (test_dir / "__init__.py").write_text("")
    (test_dir / "test_foo.py").write_text("assert True\n")

    opt = RemoveTestsOptimizer()
    opt.process_file(test_dir)

    assert not test_dir.exists()


def test_order_is_early():
    from wheel_optimizer.base import ORDER_EARLY

    opt = RemoveTestsOptimizer()
    assert opt.order == ORDER_EARLY


def test_non_py_test_files_not_matched():
    assert _is_test_path(Path("test_data.json")) is False
    assert _is_test_path(Path("test_image.png")) is False


def test_test_prefix_only_for_py():
    assert _is_test_path(Path("test_module.py")) is True
    assert _is_test_path(Path("test_module.txt")) is False


def test_files_inside_test_dir_all_matched():
    assert _is_test_path(Path("tests/helpers.py")) is True
    assert _is_test_path(Path("tests/fixtures/data.json")) is True
    assert _is_test_path(Path("tests/__init__.py")) is True
