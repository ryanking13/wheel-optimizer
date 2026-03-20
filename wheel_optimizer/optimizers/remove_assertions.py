from __future__ import annotations

import ast
from pathlib import Path

from wheel_optimizer.base import ORDER_NORMAL, WheelOptimizer


class RemoveAssertionsOptimizer(WheelOptimizer):
    name = "remove_assertions"
    description = "Strip assert statements from .py files"
    default_enabled = False
    order = ORDER_NORMAL

    def should_process(self, file_path: Path) -> bool:
        return file_path.suffix == ".py"

    def process_file(self, full_path: Path) -> None:
        source = full_path.read_text(encoding="utf-8")
        try:
            result = _remove_assertions(source)
        except SyntaxError:
            return

        if result != source:
            full_path.write_text(result, encoding="utf-8")


def _remove_assertions(source: str) -> str:
    tree = ast.parse(source)
    transformer = _AssertionRemover()
    new_tree = transformer.visit(tree)
    if not transformer.changed:
        return source
    ast.fix_missing_locations(new_tree)
    return ast.unparse(new_tree) + "\n"


class _AssertionRemover(ast.NodeTransformer):
    def __init__(self) -> None:
        self.changed = False

    def visit_Assert(self, node: ast.Assert) -> ast.Pass:
        self.changed = True
        return ast.copy_location(ast.Pass(), node)
