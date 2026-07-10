from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from models.schemas import Message, Preset, SearchResult, Session, User, UserConfig, to_plain_dict
from storage.base import StorageBackend

T = TypeVar("T", bound=BaseModel)


class FileBackend(StorageBackend):
    """JSON 文件后端，适合教学演示和轻量本地使用。"""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.files = {
            "users": self.root / "users.json",
            "presets": self.root / "presets.json",
            "sessions": self.root / "sessions.json",
            "messages": self.root / "messages.json",
            "user_configs": self.root / "user_configs.json",
        }

    async def init(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        for path in self.files.values():
            if not path.exists():
                self._write_list(path, [])

    async def close(self) -> None:
        return None

    async def create_user(self, user: User) -> User:
        items = self._load_models("users", User)
        if any(item.username == user.username and item.id != user.id for item in items):
            raise ValueError(f"用户名已存在：{user.username}")
        self._upsert("users", user)
        return user

    async def get_user(self, user_id: str) -> User | None:
        return self._find("users", User, user_id)

    async def get_user_by_username(self, username: str) -> User | None:
        return next((item for item in self._load_models("users", User) if item.username == username), None)

    async def list_users(self) -> list[User]:
        return sorted(self._load_models("users", User), key=lambda item: item.created_at)

    async def update_user(self, user: User) -> User:
        self._upsert("users", user)
        return user

    async def delete_user(self, user_id: str) -> None:
        self._delete("users", user_id)
        sessions = [item for item in self._load_models("sessions", Session) if item.user_id == user_id]
        for session in sessions:
            await self.delete_session(session.id)
        self._write_models(
            "presets",
            [item for item in self._load_models("presets", Preset) if item.user_id != user_id],
        )
        self._write_models(
            "user_configs",
            [item for item in self._load_models("user_configs", UserConfig) if item.user_id != user_id],
        )

    async def upsert_preset(self, preset: Preset) -> Preset:
        self._upsert("presets", preset)
        return preset

    async def get_preset(self, preset_id: str) -> Preset | None:
        return self._find("presets", Preset, preset_id)

    async def list_presets(self, user_id: str | None = None, include_builtin: bool = True) -> list[Preset]:
        presets = self._load_models("presets", Preset)
        result = []
        for preset in presets:
            if include_builtin and preset.is_builtin:
                result.append(preset)
            elif user_id is not None and preset.user_id == user_id:
                result.append(preset)
            elif user_id is None and not include_builtin and not preset.is_builtin:
                result.append(preset)
        return sorted(result, key=lambda item: (not item.is_builtin, item.name))

    async def delete_preset(self, preset_id: str) -> None:
        presets = self._load_models("presets", Preset)
        self._write_models(
            "presets",
            [item for item in presets if item.id != preset_id or item.is_builtin],
        )

    async def upsert_session(self, session: Session) -> Session:
        self._upsert("sessions", session)
        return session

    async def get_session(self, session_id: str) -> Session | None:
        return self._find("sessions", Session, session_id)

    async def list_sessions(self, user_id: str) -> list[Session]:
        sessions = [item for item in self._load_models("sessions", Session) if item.user_id == user_id]
        return sorted(sessions, key=lambda item: item.updated_at, reverse=True)

    async def delete_session(self, session_id: str) -> None:
        self._delete("sessions", session_id)
        self._write_models(
            "messages",
            [item for item in self._load_models("messages", Message) if item.session_id != session_id],
        )

    async def add_message(self, message: Message) -> Message:
        self._upsert("messages", message)
        return message

    async def list_messages(self, session_id: str) -> list[Message]:
        messages = [item for item in self._load_models("messages", Message) if item.session_id == session_id]
        return sorted(messages, key=lambda item: (item.created_at, item.id))

    async def search_messages(self, user_id: str, keyword: str) -> list[SearchResult]:
        sessions = {item.id: item for item in await self.list_sessions(user_id)}
        results = []
        for message in self._load_models("messages", Message):
            session = sessions.get(message.session_id)
            if session and keyword.lower() in message.content.lower():
                results.append(
                    SearchResult(
                        session_id=session.id,
                        session_title=session.title,
                        message_id=message.id,
                        role=message.role,
                        content=message.content,
                        created_at=message.created_at,
                    )
                )
        return sorted(results, key=lambda item: item.created_at, reverse=True)

    async def set_user_config(self, config: UserConfig) -> UserConfig:
        configs = self._load_models("user_configs", UserConfig)
        configs = [
            item for item in configs if not (item.user_id == config.user_id and item.key == config.key)
        ]
        configs.append(config)
        self._write_models("user_configs", configs)
        return config

    async def get_user_config(self, user_id: str, key: str) -> UserConfig | None:
        return next(
            (
                item
                for item in self._load_models("user_configs", UserConfig)
                if item.user_id == user_id and item.key == key
            ),
            None,
        )

    def _find(self, name: str, model: type[T], item_id: str) -> T | None:
        return next((item for item in self._load_models(name, model) if item.id == item_id), None)

    def _upsert(self, name: str, model: BaseModel) -> None:
        items = [item for item in self._read_list(self.files[name]) if item.get("id") != getattr(model, "id")]
        items.append(to_plain_dict(model))
        self._write_list(self.files[name], items)

    def _delete(self, name: str, item_id: str) -> None:
        self._write_list(
            self.files[name],
            [item for item in self._read_list(self.files[name]) if item.get("id") != item_id],
        )

    def _load_models(self, name: str, model: type[T]) -> list[T]:
        return [model(**item) for item in self._read_list(self.files[name])]

    def _write_models(self, name: str, models: list[BaseModel]) -> None:
        self._write_list(self.files[name], [to_plain_dict(model) for model in models])

    @staticmethod
    def _read_list(path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, list):
            raise ValueError(f"JSON file must contain a list: {path}")
        return data

    @staticmethod
    def _write_list(path: Path, items: list[dict[str, Any]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            json.dump(items, file, ensure_ascii=False, indent=2)
