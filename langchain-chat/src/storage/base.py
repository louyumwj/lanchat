from __future__ import annotations

from abc import ABC, abstractmethod

from models.schemas import Message, Preset, SearchResult, Session, User, UserConfig


class StorageBackend(ABC):
    """所有存储后端必须遵守的统一接口。"""

    @abstractmethod
    async def init(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def create_user(self, user: User) -> User:
        raise NotImplementedError

    @abstractmethod
    async def get_user(self, user_id: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def get_user_by_username(self, username: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def list_users(self) -> list[User]:
        raise NotImplementedError

    @abstractmethod
    async def update_user(self, user: User) -> User:
        raise NotImplementedError

    @abstractmethod
    async def delete_user(self, user_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def upsert_preset(self, preset: Preset) -> Preset:
        raise NotImplementedError

    @abstractmethod
    async def get_preset(self, preset_id: str) -> Preset | None:
        raise NotImplementedError

    @abstractmethod
    async def list_presets(self, user_id: str | None = None, include_builtin: bool = True) -> list[Preset]:
        raise NotImplementedError

    @abstractmethod
    async def delete_preset(self, preset_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def upsert_session(self, session: Session) -> Session:
        raise NotImplementedError

    @abstractmethod
    async def get_session(self, session_id: str) -> Session | None:
        raise NotImplementedError

    @abstractmethod
    async def list_sessions(self, user_id: str) -> list[Session]:
        raise NotImplementedError

    @abstractmethod
    async def delete_session(self, session_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def add_message(self, message: Message) -> Message:
        raise NotImplementedError

    @abstractmethod
    async def list_messages(self, session_id: str) -> list[Message]:
        raise NotImplementedError

    @abstractmethod
    async def search_messages(self, user_id: str, keyword: str) -> list[SearchResult]:
        raise NotImplementedError

    @abstractmethod
    async def set_user_config(self, config: UserConfig) -> UserConfig:
        raise NotImplementedError

    @abstractmethod
    async def get_user_config(self, user_id: str, key: str) -> UserConfig | None:
        raise NotImplementedError
