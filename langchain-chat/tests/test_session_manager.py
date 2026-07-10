from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import uuid4

from core.session_manager import SessionManager
from models.schemas import TokenUsage, User
from storage.sqlite_backend import SQLiteBackend


def local_tmp(name: str) -> Path:
    path = Path("testdata") / f"{name}-{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_session_manager_save_search_export():
    async def scenario():
        temp_dir = local_tmp("session-manager")
        storage = SQLiteBackend(temp_dir / "app.db")
        await storage.init()
        user = await storage.create_user(User(username="carol"))
        manager = SessionManager(storage, temp_dir / "users")
        session = await manager.create_session(user.id, "mock-local")
        await manager.add_user_message(session, "第一条消息")
        session = await manager.get_session(session.id)
        await manager.add_ai_message(session, "回复内容", TokenUsage(prompt_tokens=2, completion_tokens=3))
        assert len(await manager.search(user.id, "第一条")) == 1
        path = await manager.export_markdown(user.username, session.id)
        assert path.exists()
        assert "回复内容" in path.read_text(encoding="utf-8")

    asyncio.run(scenario())
