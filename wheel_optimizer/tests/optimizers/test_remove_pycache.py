from pathlib import Path

from wheel_optimizer.base import ORDER_EARLY
from wheel_optimizer.optimizers.remove_pycache import (
    RemovePycacheOptimizer,
    _is_pycache_artifact,
)


class TestDetection:
    def test_detects_pycache_files(self):
        assert _is_pycache_artifact(Path("__pycache__/module.cpython-312.pyc")) is True
        assert _is_pycache_artifact(Path("pkg/__pycache__/mod.cpython-312.pyc")) is True

    def test_detects_nested_pycache(self):
        assert (
            _is_pycache_artifact(Path("pkg/sub/__pycache__/deep.cpython-312.pyc"))
            is True
        )

    def test_ignores_regular_files(self):
        assert _is_pycache_artifact(Path("module.py")) is False
        assert _is_pycache_artifact(Path("pkg/core.py")) is False

    def test_ignores_regular_pyc_outside_pycache(self):
        assert _is_pycache_artifact(Path("module.pyc")) is False

    def test_ignores_pycache_in_filename(self):
        assert _is_pycache_artifact(Path("not__pycache__file.py")) is False


class TestShouldProcess:
    def test_matches_pycache(self):
        opt = RemovePycacheOptimizer()
        assert opt.should_process(Path("__pycache__/mod.cpython-312.pyc")) is True
        assert opt.should_process(Path("module.py")) is False

    def test_order_is_early(self):
        opt = RemovePycacheOptimizer()
        assert opt.order == ORDER_EARLY


class TestProcessFile:
    def test_deletes_pyc_in_pycache(self, tmp_path: Path):
        cache_dir = tmp_path / "__pycache__"
        cache_dir.mkdir()
        pyc = cache_dir / "module.cpython-312.pyc"
        pyc.write_bytes(b"\x00" * 16)

        opt = RemovePycacheOptimizer()
        opt.process_file(pyc)

        assert not pyc.exists()

    def test_skips_nonexistent(self, tmp_path: Path):
        gone = tmp_path / "__pycache__" / "gone.pyc"

        opt = RemovePycacheOptimizer()
        opt.process_file(gone)  # should not raise

    def test_skips_directories(self, tmp_path: Path):
        cache_dir = tmp_path / "__pycache__"
        cache_dir.mkdir()

        opt = RemovePycacheOptimizer()
        opt.process_file(cache_dir)

        assert cache_dir.exists()


class TestEndToEnd:
    def test_pipeline_removes_pycache_contents(self, tmp_path: Path):
        from wheel_optimizer.config import OptimizerConfig
        from wheel_optimizer.pipeline import OptimizerPipeline

        pkg = tmp_path / "mypkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "core.py").write_text("x = 1\n")

        cache = pkg / "__pycache__"
        cache.mkdir()
        (cache / "__init__.cpython-312.pyc").write_bytes(b"\x00" * 16)
        (cache / "core.cpython-312.pyc").write_bytes(b"\x00" * 16)

        config = OptimizerConfig(remove_pycache=True)
        OptimizerPipeline(config).run(tmp_path)

        assert not (cache / "__init__.cpython-312.pyc").exists()
        assert not (cache / "core.cpython-312.pyc").exists()
        assert (pkg / "__init__.py").exists()
        assert (pkg / "core.py").exists()
