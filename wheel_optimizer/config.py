from dataclasses import dataclass


@dataclass(frozen=True)
class OptimizerConfig:
    disable_all: bool = False
    remove_docstrings: bool = False
