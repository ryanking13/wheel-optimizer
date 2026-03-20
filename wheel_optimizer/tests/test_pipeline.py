from pathlib import Path

from wheel_optimizer.config import OptimizerConfig
from wheel_optimizer.pipeline import OptimizerPipeline, _resolve_optimizers


def test_resolve_all_disabled():
    config = OptimizerConfig(disable_all=True, remove_docstrings=True)
    assert _resolve_optimizers(config) == []


def test_resolve_none_enabled():
    config = OptimizerConfig()
    assert _resolve_optimizers(config) == []


def test_resolve_docstrings_enabled():
    config = OptimizerConfig(remove_docstrings=True)
    optimizers = _resolve_optimizers(config)
    assert len(optimizers) == 1
    assert optimizers[0].name == "remove_docstrings"


def test_run_skips_dist_info(tmp_path: Path):
    dist_info = tmp_path / "pkg-1.0.dist-info"
    dist_info.mkdir()
    metadata = dist_info / "METADATA"
    metadata.write_text("Name: pkg\nVersion: 1.0\n")

    py_file = tmp_path / "pkg" / "module.py"
    py_file.parent.mkdir()
    source = 'def foo():\n    """Remove me."""\n    return 1\n'
    py_file.write_text(source)

    config = OptimizerConfig(remove_docstrings=True)
    pipeline = OptimizerPipeline(config)
    pipeline.run(tmp_path)

    assert metadata.read_text() == "Name: pkg\nVersion: 1.0\n"
    result = py_file.read_text()
    assert '"""Remove me."""' not in result
    assert "return 1" in result


def test_run_noop_when_no_optimizers(tmp_path: Path):
    py_file = tmp_path / "module.py"
    source = 'def foo():\n    """Keep me."""\n    return 1\n'
    py_file.write_text(source)

    config = OptimizerConfig()
    pipeline = OptimizerPipeline(config)
    pipeline.run(tmp_path)

    assert py_file.read_text() == source
