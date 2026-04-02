from __future__ import annotations

import io
import tokenize
from pathlib import Path

from wheel_optimizer.base import ORDER_NORMAL, WheelOptimizer


class MinifyWhitespaceOptimizer(WheelOptimizer):
    name = "minify_whitespace"
    description = "Reduce indentation to 1 space per level and remove blank lines"
    default_enabled = False
    order = ORDER_NORMAL

    def should_process(self, file_path: Path) -> bool:
        return file_path.suffix == ".py"

    def process_file(self, full_path: Path) -> None:
        source = full_path.read_bytes()
        try:
            result = _minify_whitespace(source)
        except (SyntaxError, tokenize.TokenError):
            return

        if result != source:
            full_path.write_bytes(result)


def _minify_whitespace(source: bytes) -> bytes:
    if not source.strip():
        return source

    indent_unit = _detect_indent_unit(source)
    if indent_unit <= 1:
        return _remove_blank_lines(source)

    lines = source.split(b"\n")
    result_lines: list[bytes] = []

    for line in lines:
        if line.strip() == b"":
            continue

        stripped = line.lstrip(b" ")
        n_spaces = len(line) - len(stripped)
        level = n_spaces // indent_unit if indent_unit > 0 else 0
        new_indent = b" " * level
        result_lines.append(new_indent + stripped)

    result = b"\n".join(result_lines)
    if source.endswith(b"\n"):
        result += b"\n"

    return result


def _detect_indent_unit(source: bytes) -> int:
    try:
        tokens = list(tokenize.tokenize(io.BytesIO(source).readline))
    except tokenize.TokenError:
        return 4

    for tok in tokens:
        if tok.type == tokenize.INDENT:
            indent_str = tok.string
            n_spaces = len(indent_str)
            if n_spaces > 0:
                return n_spaces

    return 4


def _remove_blank_lines(source: bytes) -> bytes:
    lines = source.split(b"\n")
    result: list[bytes] = [line for line in lines if line.strip() != b""]
    out = b"\n".join(result)
    if source.endswith(b"\n"):
        out += b"\n"
    return out
