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

_INCLUDE_DIR_NAMES = frozenset(
    {
        "include",
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
        return _is_c_source(file_path)

    def process_file(self, full_path: Path) -> None:
        if full_path.is_file():
            full_path.unlink()


def _is_c_source(file_path: Path) -> bool:
    if file_path.suffix.lower() in _C_SOURCE_EXTENSIONS:
        return True

    for part in file_path.parts[:-1]:
        if part.lower() in _INCLUDE_DIR_NAMES:
            return True

    return False
