from pathlib import Path

from wheel_optimizer.base import ORDER_EARLY
from wheel_optimizer.optimizers.remove_c_source import RemoveCSourceOptimizer


class TestShouldProcess:
    def test_c_extensions(self):
        opt = RemoveCSourceOptimizer()
        assert opt.should_process(Path("module.c")) is True
        assert opt.should_process(Path("module.cc")) is True
        assert opt.should_process(Path("module.cpp")) is True
        assert opt.should_process(Path("module.cxx")) is True

    def test_header_extensions(self):
        opt = RemoveCSourceOptimizer()
        assert opt.should_process(Path("module.h")) is True
        assert opt.should_process(Path("module.hh")) is True
        assert opt.should_process(Path("module.hpp")) is True
        assert opt.should_process(Path("module.hxx")) is True

    def test_case_insensitive(self):
        opt = RemoveCSourceOptimizer()
        assert opt.should_process(Path("module.C")) is True
        assert opt.should_process(Path("module.H")) is True
        assert opt.should_process(Path("module.CPP")) is True

    def test_nested_paths(self):
        opt = RemoveCSourceOptimizer()
        assert opt.should_process(Path("pkg/src/module.c")) is True
        assert opt.should_process(Path("pkg/wcs/src/docstrings.c")) is True

    def test_ignores_python_files(self):
        opt = RemoveCSourceOptimizer()
        assert opt.should_process(Path("module.py")) is False
        assert opt.should_process(Path("module.pyx")) is False

    def test_ignores_other_files(self):
        opt = RemoveCSourceOptimizer()
        assert opt.should_process(Path("data.json")) is False
        assert opt.should_process(Path("lib.so")) is False
        assert opt.should_process(Path("README.md")) is False

    def test_does_not_match_include_dir(self):
        opt = RemoveCSourceOptimizer()
        assert opt.should_process(Path("include/config.json")) is False

    def test_matches_header_in_include_dir(self):
        opt = RemoveCSourceOptimizer()
        assert opt.should_process(Path("include/arrow/api.h")) is True

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

    def test_skips_nonexistent(self, tmp_path: Path):
        opt = RemoveCSourceOptimizer()
        opt.process_file(tmp_path / "gone.c")

    def test_skips_directories(self, tmp_path: Path):
        d = tmp_path / "src"
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
        # Non-C files in include/ are preserved
        assert (inc / "config.json").exists()
        assert (pkg / "__init__.py").exists()
        assert (pkg / "core.py").exists()
