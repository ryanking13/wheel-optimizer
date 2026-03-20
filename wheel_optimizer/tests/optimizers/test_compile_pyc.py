from pathlib import Path

from wheel_optimizer.base import ORDER_LATE
from wheel_optimizer.optimizers.compile_pyc import CompilePycOptimizer


def test_compiles_py_to_pyc(tmp_path: Path):
    py_file = tmp_path / "module.py"
    py_file.write_text("x = 1\n")

    opt = CompilePycOptimizer()
    opt.process_file(py_file)

    pyc_file = tmp_path / "module.pyc"
    assert pyc_file.exists()
    assert not py_file.exists()


def test_pyc_is_valid_bytecode(tmp_path: Path):
    py_file = tmp_path / "module.py"
    py_file.write_text("x = 1\n")

    opt = CompilePycOptimizer()
    opt.process_file(py_file)

    pyc_file = tmp_path / "module.pyc"
    data = pyc_file.read_bytes()
    assert len(data) > 16


def test_syntax_error_keeps_original(tmp_path: Path):
    py_file = tmp_path / "bad.py"
    py_file.write_text("def foo(:\n")

    opt = CompilePycOptimizer()
    opt.process_file(py_file)

    assert py_file.exists()
    pyc_file = tmp_path / "bad.pyc"
    assert not pyc_file.exists()


def test_should_process_py_files():
    opt = CompilePycOptimizer()
    assert opt.should_process(Path("module.py")) is True
    assert opt.should_process(Path("pkg/sub.py")) is True


def test_should_not_process_non_py():
    opt = CompilePycOptimizer()
    assert opt.should_process(Path("data.json")) is False
    assert opt.should_process(Path("lib.so")) is False
    assert opt.should_process(Path("module.pyc")) is False


def test_order_is_late():
    opt = CompilePycOptimizer()
    assert opt.order == ORDER_LATE


def test_complex_module(tmp_path: Path):
    source = "class Foo:\n    def bar(self):\n        return [i for i in range(10)]\n"
    py_file = tmp_path / "complex.py"
    py_file.write_text(source)

    opt = CompilePycOptimizer()
    opt.process_file(py_file)

    assert (tmp_path / "complex.pyc").exists()
    assert not py_file.exists()


def test_empty_file(tmp_path: Path):
    py_file = tmp_path / "empty.py"
    py_file.write_text("")

    opt = CompilePycOptimizer()
    opt.process_file(py_file)

    assert (tmp_path / "empty.pyc").exists()
    assert not py_file.exists()


def test_init_file(tmp_path: Path):
    py_file = tmp_path / "__init__.py"
    py_file.write_text("")

    opt = CompilePycOptimizer()
    opt.process_file(py_file)

    assert (tmp_path / "__init__.pyc").exists()
    assert not py_file.exists()
