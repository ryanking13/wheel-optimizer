from __future__ import annotations

import py_compile
from pathlib import Path

from wheel_optimizer.base import ORDER_LATE, WheelOptimizer


class CompilePycOptimizer(WheelOptimizer):
    name = "compile_pyc"
    description = "Compile .py files to .pyc and remove originals"
    default_enabled = False
    order = ORDER_LATE

    def should_process(self, file_path: Path) -> bool:
        return file_path.suffix == ".py"

    def process_file(self, full_path: Path) -> None:
        pyc_path = full_path.with_suffix(".pyc")
        try:
            py_compile.compile(
                str(full_path),
                cfile=str(pyc_path),
                doraise=True,
            )
        except py_compile.PyCompileError:
            return

        full_path.unlink()
