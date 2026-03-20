from abc import ABC, abstractmethod
from pathlib import Path

ORDER_EARLY: int = 100
ORDER_NORMAL: int = 500
ORDER_LATE: int = 900


class WheelOptimizer(ABC):
    name: str
    description: str
    default_enabled: bool = False
    order: int = ORDER_NORMAL

    @abstractmethod
    def should_process(self, file_path: Path) -> bool:
        raise NotImplementedError

    @abstractmethod
    def process_file(self, full_path: Path) -> None:
        raise NotImplementedError
