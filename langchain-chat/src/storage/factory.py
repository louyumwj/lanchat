from __future__ import annotations

from pathlib import Path
from typing import Any

from storage.base import StorageBackend
from storage.file_backend import FileBackend
from storage.mysql_backend import MySQLBackend
from storage.sqlite_backend import SQLiteBackend


class StorageFactory:
    @staticmethod
    def create(config: dict[str, Any], project_root: str | Path | None = None) -> StorageBackend:
        root = Path(project_root or Path.cwd())
        storage = config.get("storage", {})
        storage_type = storage.get("type", "sqlite")

        if storage_type == "sqlite":
            path = root / storage.get("sqlite", {}).get("path", "data/sqlite/app.db")
            return SQLiteBackend(path)
        if storage_type == "file":
            path = root / storage.get("file", {}).get("root", "data/file")
            return FileBackend(path)
        if storage_type == "mysql":
            return MySQLBackend(storage.get("mysql", {}))
        raise ValueError(f"不支持的存储后端：{storage_type}")
