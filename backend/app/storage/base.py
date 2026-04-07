from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO


class FileStorage(ABC):
    @abstractmethod
    def save_bytes(self, filename: str, content: bytes) -> Path:
        raise NotImplementedError

    @abstractmethod
    def save_stream(self, filename: str, stream: BinaryIO) -> tuple[Path, int]:
        raise NotImplementedError

    @abstractmethod
    def read_text(self, path: Path) -> str:
        raise NotImplementedError
