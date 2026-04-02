from dataclasses import dataclass


@dataclass(frozen=True)
class OptimizerConfig:
    disable_all: bool = False
    remove_docstrings: bool = False
    remove_type_annotations: bool = False
    remove_assertions: bool = False
    remove_comments: bool = False
    remove_tests: bool = False
    remove_typestubs: bool = False
    remove_pycache: bool = False
    remove_c_source: bool = False
    remove_cython_source: bool = False
    minify_whitespace: bool = False
    compile_pyc: bool = False
