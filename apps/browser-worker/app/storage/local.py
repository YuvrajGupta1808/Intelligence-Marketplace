from __future__ import annotations

from pathlib import Path


class LocalArtifactStorage:
    def __init__(self, root: Path, public_base_url: str) -> None:
        self.root = root
        self.public_base_url = public_base_url.rstrip("/")
        self.root.mkdir(parents=True, exist_ok=True)

    def build_path(self, task_id: str, suffix: str) -> Path:
        return self.root / f"{task_id}{suffix}"

    def public_url(self, path: Path) -> str:
        return f"{self.public_base_url}/{path.name}"

    def save_text(self, task_id: str, suffix: str, content: str) -> str:
        path = self.build_path(task_id, suffix)
        path.write_text(content)
        return self.public_url(path)

    def save_bytes(self, task_id: str, suffix: str, content: bytes) -> str:
        path = self.build_path(task_id, suffix)
        path.write_bytes(content)
        return self.public_url(path)

