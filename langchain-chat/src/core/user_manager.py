from __future__ import annotations

import logging

from models.schemas import User, utc_now
from storage.base import StorageBackend

logger = logging.getLogger(__name__)


class UserManager:
    def __init__(self, storage: StorageBackend, default_model: str = "mock-local") -> None:
        self.storage = storage
        self.default_model = default_model
        self.current_user: User | None = None

    async def create_user(self, username: str) -> User:
        if await self.storage.get_user_by_username(username):
            raise ValueError(f"用户名已存在：{username}")
        user = User(username=username, default_model=self.default_model)
        await self.storage.create_user(user)
        self.current_user = user
        logger.info("created user %s", user.username)
        return user

    async def list_users(self) -> list[User]:
        return await self.storage.list_users()

    async def switch_user(self, username: str) -> User:
        user = await self.storage.get_user_by_username(username)
        if user is None:
            raise ValueError(f"用户不存在：{username}")
        self.current_user = user
        logger.info("switched user %s", user.username)
        return user

    async def delete_user(self, username: str) -> None:
        user = await self.storage.get_user_by_username(username)
        if user is None:
            raise ValueError(f"用户不存在：{username}")
        await self.storage.delete_user(user.id)
        if self.current_user and self.current_user.id == user.id:
            self.current_user = None
        logger.info("deleted user %s", username)

    async def update_default_model(self, user: User, model_name: str) -> User:
        user.default_model = model_name
        user.updated_at = utc_now()
        await self.storage.update_user(user)
        self.current_user = user
        return user

    async def ensure_user(self, username: str = "default") -> User:
        user = await self.storage.get_user_by_username(username)
        if user is not None:
            self.current_user = user
            return user
        return await self.create_user(username)
