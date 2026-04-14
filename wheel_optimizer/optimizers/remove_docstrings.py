from __future__ import annotations

import ast
from pathlib import Path

from wheel_optimizer.base import ORDER_NORMAL, WheelOptimizer


class RemoveDocstringsOptimizer(WheelOptimizer):
    name = "remove_docstrings"
    description = "Replace docstrings with empty strings in .py files"
    default_enabled = False
    order = ORDER_NORMAL

    def should_process(self, file_path: Path) -> bool:
        return file_path.suffix == ".py"

    def process_file(self, full_path: Path) -> None:
        source = full_path.read_text(encoding="utf-8")
        try:
            result = _remove_docstrings(source)
        except SyntaxError:
            return

        if result != source:
            full_path.write_text(result, encoding="utf-8")


def _remove_docstrings(source: str) -> str:
    tree = ast.parse(source)
    transformer = _DocstringRemover()
    new_tree = transformer.visit(tree)
    if not transformer.changed:
        return source
    ast.fix_missing_locations(new_tree)
    return ast.unparse(new_tree) + "\n"


class _DocstringRemover(ast.NodeTransformer):
    def __init__(self) -> None:
        self.changed = False

    def _strip_docstring(self, node: ast.AST) -> ast.AST:
        if not hasattr(node, "body") or not node.body:
            return node

        first = node.body[0]
        if not isinstance(first, ast.Expr):
            return node
        if not isinstance(first.value, ast.Constant):
            return node
        if not isinstance(first.value.value, str):
            return node

        if not first.value.value:
            return node  # Already empty, skip for idempotency

        self.changed = True
        first.value.value = ""
        return node

    def visit_Module(self, node: ast.Module) -> ast.Module:
        self._strip_docstring(node)
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        self._strip_docstring(node)
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(
        self, node: ast.AsyncFunctionDef
    ) -> ast.AsyncFunctionDef:
        self._strip_docstring(node)
        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        self._strip_docstring(node)
        self.generic_visit(node)
        return node
