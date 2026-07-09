from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return uuid4().hex


class MessageRole(StrEnum):
    HUMAN = "human"
    AI = "ai"
    SYSTEM = "system"


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class User(BaseModel):
    id: str = Field(default_factory=new_id)
    username: str
    default_model: str = "mock-local"
    default_preset_id: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("username")
    @classmethod
    def username_must_not_be_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("username must not be blank")
        return cleaned


class Preset(BaseModel):
    id: str = Field(default_factory=new_id)
    user_id: str | None = None
    name: str
    description: str = ""
    system_prompt: str
    is_builtin: bool = False
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Session(BaseModel):
    id: str = Field(default_factory=new_id)
    user_id: str
    title: str = "新会话"
    model_name: str = "mock-local"
    preset_id: str | None = None
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Message(BaseModel):
    id: str = Field(default_factory=new_id)
    session_id: str
    role: MessageRole
    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    created_at: datetime = Field(default_factory=utc_now)


class UserConfig(BaseModel):
    id: str = Field(default_factory=new_id)
    user_id: str
    key: str
    value: str
    updated_at: datetime = Field(default_factory=utc_now)


class SearchResult(BaseModel):
    session_id: str
    session_title: str
    message_id: str
    role: MessageRole
    content: str
    created_at: datetime


class ChatChunk(BaseModel):
    content: str
    is_final: bool = False
    usage: TokenUsage = Field(default_factory=TokenUsage)
    metadata: dict[str, Any] = Field(default_factory=dict)


def to_plain_dict(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json")
