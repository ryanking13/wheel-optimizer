from pathlib import Path

from wheel_optimizer.base import ORDER_EARLY
from wheel_optimizer.optimizers.remove_cython_source import RemoveCythonSourceOptimizer


class TestShouldProcess:
    def test_matches_pyx(self):
        opt = RemoveCythonSourceOptimizer()
        assert opt.should_process(Path("module.pyx")) is True

    def test_matches_pxd(self):
        opt = RemoveCythonSourceOptimizer()
        assert opt.should_process(Path("module.pxd")) is True

    def test_matches_pxi(self):
        opt = RemoveCythonSourceOptimizer()
        assert opt.should_process(Path("module.pxi")) is True

    def test_case_insensitive(self):
        opt = RemoveCythonSourceOptimizer()
        assert opt.should_process(Path("module.PYX")) is True

    def test_nested_paths(self):
        opt = RemoveCythonSourceOptimizer()
        assert opt.should_process(Path("pkg/sub/module.pyx")) is True

    def test_ignores_py(self):
        opt = RemoveCythonSourceOptimizer()
        assert opt.should_process(Path("module.py")) is False

    def test_ignores_pyi(self):
        opt = RemoveCythonSourceOptimizer()
        assert opt.should_process(Path("module.pyi")) is False

    def test_ignores_other(self):
        opt = RemoveCythonSourceOptimizer()
        assert opt.should_process(Path("module.c")) is False
        assert opt.should_process(Path("module.so")) is False

    def test_order_is_early(self):
        opt = RemoveCythonSourceOptimizer()
        assert opt.order == ORDER_EARLY


class TestProcessFile:
    def test_deletes_pyx(self, tmp_path: Path):
        f = tmp_path / "module.pyx"
        f.write_text("def foo(): return 1\n")

        opt = RemoveCythonSourceOptimizer()
        opt.process_file(f)

        assert not f.exists()

    def test_deletes_pxd(self, tmp_path: Path):
        f = tmp_path / "module.pxd"
        f.write_text("cdef int x\n")

        opt = RemoveCythonSourceOptimizer()
        opt.process_file(f)

        assert not f.exists()

    def test_skips_nonexistent(self, tmp_path: Path):
        opt = RemoveCythonSourceOptimizer()
        opt.process_file(tmp_path / "gone.pyx")

    def test_skips_directories(self, tmp_path: Path):
        d = tmp_path / "cython"
        d.mkdir()

        opt = RemoveCythonSourceOptimizer()
        opt.process_file(d)

        assert d.exists()


class TestEndToEnd:
    def test_pipeline_removes_cython_source(self, tmp_path: Path):
        from wheel_optimizer.config import OptimizerConfig
        from wheel_optimizer.pipeline import OptimizerPipeline

        pkg = tmp_path / "mypkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "_fast.pyx").write_text("def fast(): return 1\n")
        (pkg / "_fast.pxd").write_text("cdef int x\n")
        (pkg / "_fast.cpython-312-wasm32.so").write_bytes(b"\x00" * 16)

        config = OptimizerConfig(remove_cython_source=True)
        OptimizerPipeline(config).run(tmp_path)

        assert not (pkg / "_fast.pyx").exists()
        assert not (pkg / "_fast.pxd").exists()
        assert (pkg / "_fast.cpython-312-wasm32.so").exists()
        assert (pkg / "__init__.py").exists()
