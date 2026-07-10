from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import uuid4

from core.user_manager import UserManager
from storage.sqlite_backend import SQLiteBackend


def local_tmp(name: str) -> Path:
    path = Path("testdata") / f"{name}-{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_user_manager_create_switch_delete():
    async def scenario():
        storage = SQLiteBackend(local_tmp("user-manager") / "app.db")
        await storage.init()
        manager = UserManager(storage)
        await manager.create_user("bob")
        await manager.switch_user("bob")
        assert manager.current_user.username == "bob"
        await manager.delete_user("bob")
        assert await storage.get_user_by_username("bob") is None

    asyncio.run(scenario())
