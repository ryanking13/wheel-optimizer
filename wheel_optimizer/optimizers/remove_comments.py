from __future__ import annotations

import io
import tokenize
from pathlib import Path

from wheel_optimizer.base import ORDER_NORMAL, WheelOptimizer


class RemoveCommentsOptimizer(WheelOptimizer):
    name = "remove_comments"
    description = "Strip comments from .py files"
    default_enabled = False
    order = ORDER_NORMAL

    def should_process(self, file_path: Path) -> bool:
        return file_path.suffix == ".py"

    def process_file(self, full_path: Path) -> None:
        source = full_path.read_bytes()
        try:
            result = _remove_comments(source)
        except (tokenize.TokenError, SyntaxError):
            return

        if result != source:
            full_path.write_bytes(result)


def _remove_comments(source: bytes) -> bytes:
    tokens = list(tokenize.tokenize(io.BytesIO(source).readline))

    changed = False
    for i, tok in enumerate(tokens):
        if tok.type == tokenize.COMMENT:
            tokens[i] = tok._replace(string="")
            changed = True

    if not changed:
        return source

    result: bytes = tokenize.untokenize(tokens)  # type: ignore[assignment]
    return _collapse_blank_lines(result)


def _collapse_blank_lines(source: bytes) -> bytes:
    lines = source.split(b"\n")
    result: list[bytes] = []
    prev_blank = False
    for line in lines:
        is_blank = line.strip() == b""
        if is_blank and prev_blank:
            continue
        result.append(line)
        prev_blank = is_blank
    return b"\n".join(result)
