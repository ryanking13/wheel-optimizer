from pathlib import Path

import pytest

from wheel_optimizer.optimizers.remove_type_annotations import (
    RemoveTypeAnnotationsOptimizer,
    _remove_type_annotations,
)


def test_removes_return_annotation():
    source = "def foo() -> int:\n    return 1\n"
    result = _remove_type_annotations(source)
    assert "-> int" not in result
    assert "return 1" in result


def test_removes_arg_annotation():
    source = "def foo(x: int, y: str):\n    pass\n"
    result = _remove_type_annotations(source)
    assert ": int" not in result
    assert ": str" not in result
    assert "def foo(x, y):" in result


def test_removes_posonly_annotations():
    source = "def foo(x: int, /, y: str):\n    pass\n"
    result = _remove_type_annotations(source)
    assert ": int" not in result
    assert ": str" not in result


def test_removes_kwonly_annotations():
    source = "def foo(*, x: int, y: str):\n    pass\n"
    result = _remove_type_annotations(source)
    assert ": int" not in result
    assert ": str" not in result


def test_removes_vararg_annotation():
    source = "def foo(*args: int):\n    pass\n"
    result = _remove_type_annotations(source)
    assert ": int" not in result


def test_removes_kwarg_annotation():
    source = "def foo(**kwargs: str):\n    pass\n"
    result = _remove_type_annotations(source)
    assert ": str" not in result


def test_removes_async_function_annotations():
    source = "async def foo(x: int) -> str:\n    return 'hi'\n"
    result = _remove_type_annotations(source)
    assert ": int" not in result
    assert "-> str" not in result
    assert "return" in result


def test_ann_assign_with_value():
    source = "x: int = 5\n"
    result = _remove_type_annotations(source)
    assert ": int" not in result
    assert "x = 5" in result


def test_ann_assign_without_value():
    source = "x: int\ny = 1\n"
    result = _remove_type_annotations(source)
    assert ": int" not in result
    assert "y = 1" in result


def test_preserves_dataclass_fields():
    source = (
        "from dataclasses import dataclass\n"
        "@dataclass\n"
        "class Foo:\n"
        "    x: int\n"
        "    y: str = 'hi'\n"
    )
    result = _remove_type_annotations(source)
    assert "x: int" in result
    assert "y: str" in result


def test_preserves_dataclass_with_call():
    source = (
        "from dataclasses import dataclass\n"
        "@dataclass(frozen=True)\n"
        "class Foo:\n"
        "    x: int = 0\n"
    )
    result = _remove_type_annotations(source)
    assert "x: int" in result


def test_preserves_named_tuple_fields():
    source = (
        "from typing import NamedTuple\n"
        "class Point(NamedTuple):\n"
        "    x: int\n"
        "    y: int\n"
    )
    result = _remove_type_annotations(source)
    assert "x: int" in result
    assert "y: int" in result


def test_preserves_typed_dict_fields():
    source = (
        "from typing import TypedDict\n"
        "class Config(TypedDict):\n"
        "    name: str\n"
        "    value: int\n"
    )
    result = _remove_type_annotations(source)
    assert "name: str" in result
    assert "value: int" in result


def test_preserves_protocol_fields():
    source = "from typing import Protocol\nclass Readable(Protocol):\n    name: str\n"
    result = _remove_type_annotations(source)
    assert "name: str" in result


def test_strips_method_annotations_inside_dataclass():
    source = (
        "from dataclasses import dataclass\n"
        "@dataclass\n"
        "class Foo:\n"
        "    x: int\n"
        "    def bar(self) -> str:\n"
        "        return 'hi'\n"
    )
    result = _remove_type_annotations(source)
    assert "x: int" in result
    assert "-> str" not in result


def test_no_annotations_returns_original():
    source = "x = 1\ny = 2\n"
    result = _remove_type_annotations(source)
    assert result == source


def test_syntax_error_raises():
    with pytest.raises(SyntaxError):
        _remove_type_annotations("def foo(:\n")


def test_result_is_valid_python():
    source = (
        "def foo(x: int, y: str = 'a') -> bool:\n    z: float = 1.0\n    return True\n"
    )
    result = _remove_type_annotations(source)
    compile(result, "<test>", "exec")


def test_idempotent():
    source = "def foo(x: int) -> str:\n    y: int = 1\n    return str(y)\n"
    result1 = _remove_type_annotations(source)
    result2 = _remove_type_annotations(result1)
    assert result1 == result2


def test_should_process_py_files():
    opt = RemoveTypeAnnotationsOptimizer()
    assert opt.should_process(Path("module.py")) is True
    assert opt.should_process(Path("pkg/sub/mod.py")) is True


def test_should_not_process_non_py():
    opt = RemoveTypeAnnotationsOptimizer()
    assert opt.should_process(Path("data.json")) is False
    assert opt.should_process(Path("lib.so")) is False


def test_process_file_in_place(tmp_path: Path):
    source = "def foo(x: int) -> str:\n    return str(x)\n"
    py_file = tmp_path / "mod.py"
    py_file.write_text(source)

    opt = RemoveTypeAnnotationsOptimizer()
    opt.process_file(py_file)

    result = py_file.read_text()
    assert ": int" not in result
    assert "-> str" not in result
    assert "return str(x)" in result


def test_process_file_syntax_error_no_crash(tmp_path: Path):
    bad = "def foo(:\n"
    py_file = tmp_path / "bad.py"
    py_file.write_text(bad)

    opt = RemoveTypeAnnotationsOptimizer()
    opt.process_file(py_file)

    assert py_file.read_text() == bad


def test_empty_file():
    result = _remove_type_annotations("")
    assert result == ""


def test_complex_annotations():
    source = "def foo(x: list[dict[str, int]], y: int | None = None) -> tuple[str, ...]:\n    pass\n"
    result = _remove_type_annotations(source)
    assert "list[dict" not in result
    assert "int | None" not in result
    assert "tuple[str" not in result
    compile(result, "<test>", "exec")


def test_class_attribute_annotation_stripped():
    source = "class Foo:\n    x: int = 5\n"
    result = _remove_type_annotations(source)
    assert ": int" not in result
    assert "x = 5" in result


def test_preserves_qualified_annotation_dependent_base():
    source = "import typing\nclass Config(typing.TypedDict):\n    name: str\n"
    result = _remove_type_annotations(source)
    assert "name: str" in result


def test_nested_class_not_confused():
    source = "class Outer:\n    x: int = 1\n    class Inner:\n        y: str = 'hi'\n"
    result = _remove_type_annotations(source)
    assert ": int" not in result
    assert ": str" not in result
