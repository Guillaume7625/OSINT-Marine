from __future__ import annotations

import uuid
from pathlib import Path

from app.storage.base import FileStorage


class LocalFileStorage(FileStorage):
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def save_bytes(self, filename: str, content: bytes) -> Path:
        safe_name = filename.replace("/", "_").replace("\\", "_")
        target = self.root / f"{uuid.uuid4()}_{safe_name}"
        target.write_bytes(content)
        return target

    def read_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")
