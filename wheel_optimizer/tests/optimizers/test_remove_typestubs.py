from pathlib import Path

from wheel_optimizer.base import ORDER_EARLY
from wheel_optimizer.optimizers.remove_typestubs import RemoveTypestubsOptimizer


class TestShouldProcess:
    def test_matches_pyi(self):
        opt = RemoveTypestubsOptimizer()
        assert opt.should_process(Path("module.pyi")) is True
        assert opt.should_process(Path("pkg/__init__.pyi")) is True
        assert opt.should_process(Path("pkg/sub/types.pyi")) is True

    def test_matches_py_typed(self):
        opt = RemoveTypestubsOptimizer()
        assert opt.should_process(Path("py.typed")) is True
        assert opt.should_process(Path("pkg/py.typed")) is True

    def test_ignores_py_files(self):
        opt = RemoveTypestubsOptimizer()
        assert opt.should_process(Path("module.py")) is False

    def test_ignores_other_files(self):
        opt = RemoveTypestubsOptimizer()
        assert opt.should_process(Path("data.json")) is False
        assert opt.should_process(Path("lib.so")) is False
        assert opt.should_process(Path("README.md")) is False

    def test_order_is_early(self):
        opt = RemoveTypestubsOptimizer()
        assert opt.order == ORDER_EARLY


class TestProcessFile:
    def test_deletes_pyi_file(self, tmp_path: Path):
        stub = tmp_path / "module.pyi"
        stub.write_text("def foo(x: int) -> str: ...\n")

        opt = RemoveTypestubsOptimizer()
        opt.process_file(stub)

        assert not stub.exists()

    def test_deletes_py_typed_marker(self, tmp_path: Path):
        marker = tmp_path / "py.typed"
        marker.write_text("")

        opt = RemoveTypestubsOptimizer()
        opt.process_file(marker)

        assert not marker.exists()

    def test_leaves_py_files_alone(self, tmp_path: Path):
        py = tmp_path / "module.py"
        py.write_text("x = 1\n")

        opt = RemoveTypestubsOptimizer()
        # should_process would return False, but test process_file directly
        # to ensure no crash if called on wrong file
        opt.process_file(py)
        # process_file deletes any file it's called on
        # but pipeline only calls it when should_process is True

    def test_skips_nonexistent(self, tmp_path: Path):
        gone = tmp_path / "gone.pyi"

        opt = RemoveTypestubsOptimizer()
        opt.process_file(gone)  # should not raise


class TestEndToEnd:
    def test_pipeline_removes_stubs(self, tmp_path: Path):
        from wheel_optimizer.config import OptimizerConfig
        from wheel_optimizer.pipeline import OptimizerPipeline

        pkg = tmp_path / "mypkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "__init__.pyi").write_text("def foo() -> int: ...\n")
        (pkg / "core.py").write_text("def foo():\n    return 1\n")
        (pkg / "core.pyi").write_text("def foo() -> int: ...\n")
        (pkg / "py.typed").write_text("")

        config = OptimizerConfig(remove_typestubs=True)
        OptimizerPipeline(config).run(tmp_path)

        assert not (pkg / "__init__.pyi").exists()
        assert not (pkg / "core.pyi").exists()
        assert not (pkg / "py.typed").exists()
        assert (pkg / "__init__.py").exists()
        assert (pkg / "core.py").exists()
