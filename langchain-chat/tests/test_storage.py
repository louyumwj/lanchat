from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import uuid4

from models.schemas import Message, MessageRole, Session, User
from storage.sqlite_backend import SQLiteBackend


def local_tmp(name: str) -> Path:
    path = Path("testdata") / f"{name}-{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_sqlite_backend_crud():
    async def scenario():
        storage = SQLiteBackend(local_tmp("storage") / "app.db")
        await storage.init()
        user = await storage.create_user(User(username="alice"))
        session = await storage.upsert_session(Session(user_id=user.id, title="hello"))
        await storage.add_message(
            Message(session_id=session.id, role=MessageRole.HUMAN, content="find me")
        )
        assert (await storage.get_user_by_username("alice")).id == user.id
        assert len(await storage.list_sessions(user.id)) == 1
        assert len(await storage.search_messages(user.id, "find")) == 1

    asyncio.run(scenario())
