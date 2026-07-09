from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from models.schemas import Message, Preset, SearchResult, Session, User, UserConfig, to_plain_dict
from storage.base import StorageBackend


class SQLiteBackend(StorageBackend):
    """SQLite 后端；接口保持 async，内部用标准库 sqlite3 完成轻量持久化。"""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    async def init(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(SCHEMA_SQL)
            conn.commit()

    async def close(self) -> None:
        return None

    async def create_user(self, user: User) -> User:
        with self._connect() as conn:
            self._insert_or_replace(conn, "users", to_plain_dict(user))
            conn.commit()
        return user

    async def get_user(self, user_id: str) -> User | None:
        row = self._fetchone("SELECT * FROM users WHERE id = ?", (user_id,))
        return User(**dict(row)) if row else None

    async def get_user_by_username(self, username: str) -> User | None:
        row = self._fetchone("SELECT * FROM users WHERE username = ?", (username,))
        return User(**dict(row)) if row else None

    async def list_users(self) -> list[User]:
        return [User(**dict(row)) for row in self._fetchall("SELECT * FROM users ORDER BY created_at")]

    async def update_user(self, user: User) -> User:
        return await self.create_user(user)

    async def delete_user(self, user_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()

    async def upsert_preset(self, preset: Preset) -> Preset:
        with self._connect() as conn:
            self._insert_or_replace(conn, "presets", to_plain_dict(preset))
            conn.commit()
        return preset

    async def get_preset(self, preset_id: str) -> Preset | None:
        row = self._fetchone("SELECT * FROM presets WHERE id = ?", (preset_id,))
        return Preset(**dict(row)) if row else None

    async def list_presets(self, user_id: str | None = None, include_builtin: bool = True) -> list[Preset]:
        clauses = []
        params: list[Any] = []
        if include_builtin:
            clauses.append("is_builtin = 1")
        if user_id is not None:
            clauses.append("user_id = ?")
            params.append(user_id)
        if not clauses:
            clauses.append("user_id IS NULL AND is_builtin = 0")
        sql = f"SELECT * FROM presets WHERE {' OR '.join(clauses)} ORDER BY is_builtin DESC, name"
        return [Preset(**dict(row)) for row in self._fetchall(sql, tuple(params))]

    async def delete_preset(self, preset_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM presets WHERE id = ? AND is_builtin = 0", (preset_id,))
            conn.commit()

    async def upsert_session(self, session: Session) -> Session:
        with self._connect() as conn:
            self._insert_or_replace(conn, "sessions", to_plain_dict(session))
            conn.commit()
        return session

    async def get_session(self, session_id: str) -> Session | None:
        row = self._fetchone("SELECT * FROM sessions WHERE id = ?", (session_id,))
        return Session(**dict(row)) if row else None

    async def list_sessions(self, user_id: str) -> list[Session]:
        rows = self._fetchall(
            "SELECT * FROM sessions WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,),
        )
        return [Session(**dict(row)) for row in rows]

    async def delete_session(self, session_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            conn.commit()

    async def add_message(self, message: Message) -> Message:
        with self._connect() as conn:
            self._insert_or_replace(conn, "messages", to_plain_dict(message))
            conn.commit()
        return message

    async def list_messages(self, session_id: str) -> list[Message]:
        rows = self._fetchall(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at, id",
            (session_id,),
        )
        return [Message(**dict(row)) for row in rows]

    async def search_messages(self, user_id: str, keyword: str) -> list[SearchResult]:
        like = f"%{keyword}%"
        rows = self._fetchall(
            """
            SELECT s.id AS session_id, s.title AS session_title, m.id AS message_id,
                   m.role, m.content, m.created_at
            FROM messages m
            JOIN sessions s ON s.id = m.session_id
            WHERE s.user_id = ? AND m.content LIKE ?
            ORDER BY m.created_at DESC
            """,
            (user_id, like),
        )
        results = [SearchResult(**dict(row)) for row in rows]
        if results or keyword.isascii():
            return results

        # 部分 Windows SQLite 构建在 LIKE 查询中文时会受到编码/排序影响；
        # 这里补一层 Python 过滤，保证跨环境行为稳定。
        sessions = {session.id: session for session in await self.list_sessions(user_id)}
        fallback = []
        for session_id, session in sessions.items():
            for message in await self.list_messages(session_id):
                if keyword in message.content:
                    fallback.append(
                        SearchResult(
                            session_id=session.id,
                            session_title=session.title,
                            message_id=message.id,
                            role=message.role,
                            content=message.content,
                            created_at=message.created_at,
                        )
                    )
        return sorted(fallback, key=lambda item: item.created_at, reverse=True)

    async def set_user_config(self, config: UserConfig) -> UserConfig:
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT id FROM user_configs WHERE user_id = ? AND key = ?",
                (config.user_id, config.key),
            ).fetchone()
            payload = to_plain_dict(config)
            if existing:
                payload["id"] = existing["id"]
            self._insert_or_replace(conn, "user_configs", payload)
            conn.commit()
        return config

    async def get_user_config(self, user_id: str, key: str) -> UserConfig | None:
        row = self._fetchone(
            "SELECT * FROM user_configs WHERE user_id = ? AND key = ?",
            (user_id, key),
        )
        return UserConfig(**dict(row)) if row else None

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _fetchone(self, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
        with self._connect() as conn:
            return conn.execute(sql, params).fetchone()

    def _fetchall(self, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        with self._connect() as conn:
            return list(conn.execute(sql, params).fetchall())

    @staticmethod
    def _insert_or_replace(conn: sqlite3.Connection, table: str, payload: dict[str, Any]) -> None:
        columns = list(payload)
        placeholders = ", ".join("?" for _ in columns)
        names = ", ".join(columns)
        updates = ", ".join(f"{column} = excluded.{column}" for column in columns if column != "id")
        sql = (
            f"INSERT INTO {table} ({names}) VALUES ({placeholders}) "
            f"ON CONFLICT(id) DO UPDATE SET {updates}"
        )
        conn.execute(sql, tuple(payload[column] for column in columns))


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    default_model TEXT NOT NULL,
    default_preset_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS presets (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    system_prompt TEXT NOT NULL,
    is_builtin INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    model_name TEXT NOT NULL,
    preset_id TEXT,
    total_prompt_tokens INTEGER NOT NULL DEFAULT 0,
    total_completion_tokens INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (preset_id) REFERENCES presets(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_configs (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(user_id, key),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
"""
