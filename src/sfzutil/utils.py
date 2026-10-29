from abc import abstractmethod, ABC
from collections import defaultdict
from io import TextIOWrapper
from typing import Any


class SFZFile:
    def __init__(self, file: TextIOWrapper):
        self._file = file
        self._cfg = defaultdict(None)

    def config(self, **kwargs):
        for k, v in kwargs:
            self._cfg[k] = v

    def write(self, val: str):
        self._file.write(val)


class Writable(ABC):
    @abstractmethod
    def get_writer(self) -> Writer: ...


class Writer(ABC):
    @abstractmethod
    def write(self, file: SFZFile, cfg: dict[str, Any] | None = None): ...
