from __future__ import annotations

from pathlib import Path

from wheel_optimizer.base import ORDER_EARLY, WheelOptimizer

_C_SOURCE_EXTENSIONS = frozenset(
    {
        ".c",
        ".cc",
        ".cpp",
        ".cxx",
        ".h",
        ".hh",
        ".hpp",
        ".hxx",
    }
)


class RemoveCSourceOptimizer(WheelOptimizer):
    name = "remove_c_source"
    description = (
        "Remove C/C++ source and header files shipped alongside compiled extensions"
    )
    default_enabled = False
    order = ORDER_EARLY

    def should_process(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in _C_SOURCE_EXTENSIONS

    def process_file(self, full_path: Path) -> None:
        if full_path.is_file():
            full_path.unlink()
