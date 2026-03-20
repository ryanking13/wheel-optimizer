from __future__ import annotations

import ast
from pathlib import Path

from wheel_optimizer.base import ORDER_NORMAL, WheelOptimizer

_ANNOTATION_DEPENDENT_BASES = frozenset(
    {
        "NamedTuple",
        "TypedDict",
        "Protocol",
    }
)

_DATACLASS_NAMES = frozenset(
    {
        "dataclass",
        "dataclasses.dataclass",
    }
)


class RemoveTypeAnnotationsOptimizer(WheelOptimizer):
    name = "remove_type_annotations"
    description = "Strip type annotations from .py files"
    default_enabled = False
    order = ORDER_NORMAL

    def should_process(self, file_path: Path) -> bool:
        return file_path.suffix == ".py"

    def process_file(self, full_path: Path) -> None:
        source = full_path.read_text(encoding="utf-8")
        try:
            result = _remove_type_annotations(source)
        except SyntaxError:
            return

        if result != source:
            full_path.write_text(result, encoding="utf-8")


def _remove_type_annotations(source: str) -> str:
    tree = ast.parse(source)
    transformer = _TypeAnnotationRemover()
    new_tree = transformer.visit(tree)
    if not transformer.changed:
        return source
    ast.fix_missing_locations(new_tree)
    return ast.unparse(new_tree) + "\n"


class _TypeAnnotationRemover(ast.NodeTransformer):
    def __init__(self) -> None:
        self.changed = False
        self._class_stack: list[ast.ClassDef] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        self._class_stack.append(node)
        self.generic_visit(node)
        self._class_stack.pop()
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        if node.returns is not None:
            node.returns = None
            self.changed = True
        self._strip_arguments(node.args)
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(
        self, node: ast.AsyncFunctionDef
    ) -> ast.AsyncFunctionDef:
        if node.returns is not None:
            node.returns = None
            self.changed = True
        self._strip_arguments(node.args)
        self.generic_visit(node)
        return node

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AST | None:
        if self._in_annotation_dependent_class():
            return node

        self.changed = True
        if node.value is not None:
            new_node = ast.Assign(
                targets=[node.target],
                value=node.value,
            )
            return ast.copy_location(new_node, node)
        return ast.copy_location(ast.Pass(), node)

    def _strip_arguments(self, args: ast.arguments) -> None:
        for arg_list in (args.posonlyargs, args.args, args.kwonlyargs):
            for arg in arg_list:
                if arg.annotation is not None:
                    arg.annotation = None
                    self.changed = True
        if args.vararg and args.vararg.annotation is not None:
            args.vararg.annotation = None
            self.changed = True
        if args.kwarg and args.kwarg.annotation is not None:
            args.kwarg.annotation = None
            self.changed = True

    def _in_annotation_dependent_class(self) -> bool:
        if not self._class_stack:
            return False
        cls = self._class_stack[-1]
        return _is_dataclass(cls) or _has_annotation_dependent_base(cls)


def _is_dataclass(cls: ast.ClassDef) -> bool:
    for decorator in cls.decorator_list:
        name = _decorator_name(decorator)
        if name in _DATACLASS_NAMES:
            return True
    return False


def _has_annotation_dependent_base(cls: ast.ClassDef) -> bool:
    for base in cls.bases:
        if isinstance(base, ast.Name) and base.id in _ANNOTATION_DEPENDENT_BASES:
            return True
        if isinstance(base, ast.Attribute) and base.attr in _ANNOTATION_DEPENDENT_BASES:
            return True
    return False


def _decorator_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Call):
        return _decorator_name(node.func)
    if isinstance(node, ast.Attribute):
        value_name = _decorator_name(node.value)
        if value_name:
            return f"{value_name}.{node.attr}"
        return node.attr
    return ""
