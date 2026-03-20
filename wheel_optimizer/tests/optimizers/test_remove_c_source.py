from pathlib import Path

from wheel_optimizer.base import ORDER_EARLY
from wheel_optimizer.optimizers.remove_c_source import (
    RemoveCSourceOptimizer,
    _is_c_source,
)


class TestDetection:
    def test_c_extensions(self):
        assert _is_c_source(Path("module.c")) is True
        assert _is_c_source(Path("module.cc")) is True
        assert _is_c_source(Path("module.cpp")) is True
        assert _is_c_source(Path("module.cxx")) is True

    def test_header_extensions(self):
        assert _is_c_source(Path("module.h")) is True
        assert _is_c_source(Path("module.hh")) is True
        assert _is_c_source(Path("module.hpp")) is True
        assert _is_c_source(Path("module.hxx")) is True

    def test_case_insensitive(self):
        assert _is_c_source(Path("module.C")) is True
        assert _is_c_source(Path("module.H")) is True
        assert _is_c_source(Path("module.CPP")) is True

    def test_nested_paths(self):
        assert _is_c_source(Path("pkg/src/module.c")) is True
        assert _is_c_source(Path("pkg/wcs/src/docstrings.c")) is True

    def test_include_directory(self):
        assert _is_c_source(Path("include/arrow/api.h")) is True
        assert _is_c_source(Path("pkg/include/types.h")) is True
        assert _is_c_source(Path("include/config.json")) is True

    def test_ignores_python_files(self):
        assert _is_c_source(Path("module.py")) is False
        assert _is_c_source(Path("module.pyx")) is False

    def test_ignores_other_files(self):
        assert _is_c_source(Path("data.json")) is False
        assert _is_c_source(Path("lib.so")) is False
        assert _is_c_source(Path("README.md")) is False

    def test_ignores_include_in_filename(self):
        assert _is_c_source(Path("include_utils.py")) is False


class TestShouldProcess:
    def test_matches(self):
        opt = RemoveCSourceOptimizer()
        assert opt.should_process(Path("module.c")) is True
        assert opt.should_process(Path("module.py")) is False

    def test_order_is_early(self):
        opt = RemoveCSourceOptimizer()
        assert opt.order == ORDER_EARLY


class TestProcessFile:
    def test_deletes_c_file(self, tmp_path: Path):
        c_file = tmp_path / "module.c"
        c_file.write_text("int main() { return 0; }\n")

        opt = RemoveCSourceOptimizer()
        opt.process_file(c_file)

        assert not c_file.exists()

    def test_deletes_header(self, tmp_path: Path):
        h_file = tmp_path / "module.h"
        h_file.write_text("#pragma once\n")

        opt = RemoveCSourceOptimizer()
        opt.process_file(h_file)

        assert not h_file.exists()

    def test_deletes_file_in_include_dir(self, tmp_path: Path):
        inc = tmp_path / "include"
        inc.mkdir()
        header = inc / "api.h"
        header.write_text("#pragma once\n")

        opt = RemoveCSourceOptimizer()
        opt.process_file(header)

        assert not header.exists()

    def test_skips_nonexistent(self, tmp_path: Path):
        opt = RemoveCSourceOptimizer()
        opt.process_file(tmp_path / "gone.c")

    def test_skips_directories(self, tmp_path: Path):
        d = tmp_path / "include"
        d.mkdir()

        opt = RemoveCSourceOptimizer()
        opt.process_file(d)

        assert d.exists()


class TestEndToEnd:
    def test_pipeline_removes_c_source(self, tmp_path: Path):
        from wheel_optimizer.config import OptimizerConfig
        from wheel_optimizer.pipeline import OptimizerPipeline

        pkg = tmp_path / "mypkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "core.py").write_text("x = 1\n")
        (pkg / "_core.c").write_text("int main() {}\n")
        (pkg / "_core.h").write_text("#pragma once\n")

        inc = pkg / "include"
        inc.mkdir()
        (inc / "types.h").write_text("#pragma once\n")
        (inc / "config.json").write_text("{}")

        config = OptimizerConfig(remove_c_source=True)
        OptimizerPipeline(config).run(tmp_path)

        assert not (pkg / "_core.c").exists()
        assert not (pkg / "_core.h").exists()
        assert not (inc / "types.h").exists()
        assert not (inc / "config.json").exists()
        assert (pkg / "__init__.py").exists()
        assert (pkg / "core.py").exists()
