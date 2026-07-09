from __future__ import annotations

from pathlib import Path

from models.schemas import Message, MessageRole, SearchResult, Session, TokenUsage, utc_now
from storage.base import StorageBackend


class SessionManager:
    def __init__(self, storage: StorageBackend, export_root: str | Path = "data/users") -> None:
        self.storage = storage
        self.export_root = Path(export_root)

    async def create_session(
        self,
        user_id: str,
        model_name: str,
        preset_id: str | None = None,
        title: str = "新会话",
    ) -> Session:
        session = Session(
            user_id=user_id,
            title=title,
            model_name=model_name,
            preset_id=preset_id,
        )
        return await self.storage.upsert_session(session)

    async def get_session(self, session_id: str) -> Session:
        session = await self.storage.get_session(session_id)
        if session is None:
            raise ValueError("会话不存在")
        return session

    async def list_sessions(self, user_id: str) -> list[Session]:
        return await self.storage.list_sessions(user_id)

    async def rename_session(self, session_id: str, title: str) -> Session:
        session = await self.get_session(session_id)
        session.title = title.strip() or session.title
        session.updated_at = utc_now()
        return await self.storage.upsert_session(session)

    async def delete_session(self, session_id: str) -> None:
        await self.storage.delete_session(session_id)

    async def add_user_message(self, session: Session, content: str) -> Message:
        message = Message(session_id=session.id, role=MessageRole.HUMAN, content=content)
        await self.storage.add_message(message)
        if session.title == "新会话":
            session.title = content.strip()[:30] or "新会话"
        session.updated_at = utc_now()
        await self.storage.upsert_session(session)
        return message

    async def add_ai_message(self, session: Session, content: str, usage: TokenUsage) -> Message:
        message = Message(
            session_id=session.id,
            role=MessageRole.AI,
            content=content,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
        )
        await self.storage.add_message(message)
        session.total_prompt_tokens += usage.prompt_tokens
        session.total_completion_tokens += usage.completion_tokens
        session.updated_at = utc_now()
        await self.storage.upsert_session(session)
        return message

    async def list_messages(self, session_id: str) -> list[Message]:
        return await self.storage.list_messages(session_id)

    async def search(self, user_id: str, keyword: str) -> list[SearchResult]:
        return await self.storage.search_messages(user_id, keyword)

    async def switch_model(self, session_id: str, model_name: str) -> Session:
        session = await self.get_session(session_id)
        session.model_name = model_name
        session.updated_at = utc_now()
        return await self.storage.upsert_session(session)

    async def export_markdown(self, username: str, session_id: str) -> Path:
        session = await self.get_session(session_id)
        messages = await self.list_messages(session_id)
        safe_user = safe_filename(username)
        safe_title = safe_filename(session.title)
        export_dir = self.export_root / safe_user / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        path = export_dir / f"{safe_title}-{utc_now().date().isoformat()}.md"
        lines = [
            f"# {session.title}",
            "",
            f"- 模型：{session.model_name}",
            f"- Prompt Tokens：{session.total_prompt_tokens}",
            f"- Completion Tokens：{session.total_completion_tokens}",
            "",
        ]
        for message in messages:
            title = {"human": "用户", "ai": "助手", "system": "系统"}[message.role.value]
            lines.extend([f"## {title}", "", message.content, ""])
        path.write_text("\n".join(lines), encoding="utf-8")
        return path


def safe_filename(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in "-_." else "_" for char in value.strip())
    return cleaned or "untitled"
