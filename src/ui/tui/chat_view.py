from __future__ import annotations

from core.chat_engine import ChatEngine
from core.session_manager import SessionManager
from models.schemas import Session, TokenUsage
from storage.base import StorageBackend
from ui.tui.widgets import console, prompt_text


class ChatView:
    def __init__(
        self,
        chat_engine: ChatEngine,
        session_manager: SessionManager,
        storage: StorageBackend,
    ) -> None:
        self.chat_engine = chat_engine
        self.session_manager = session_manager
        self.storage = storage

    async def chat_loop(self, session: Session) -> None:
        console.rule(f"对话：{session.title}")
        console.print("输入 /exit 返回，/model 切换模型，/export 导出当前会话。")
        while True:
            user_input = await prompt_text("你")
            if not user_input.strip():
                continue
            if user_input == "/exit":
                return
            if user_input == "/model":
                model = await prompt_text("模型名称")
                session = await self.session_manager.switch_model(session.id, model)
                console.print(f"已切换到：{model}")
                continue
            if user_input == "/export":
                console.print("请从会话管理菜单导出，会自动放入 data/users/{username}/exports。")
                continue

            await self.session_manager.add_user_message(session, user_input)
            history = await self.session_manager.list_messages(session.id)
            preset = await self.storage.get_preset(session.preset_id) if session.preset_id else None
            console.print("助手：")
            parts = []
            usage = None
            async for chunk in self.chat_engine.stream_reply(
                user_input=user_input,
                history=history[:-1],
                model_name=session.model_name,
                system_prompt=preset.system_prompt if preset else None,
            ):
                if chunk.content:
                    parts.append(chunk.content)
                    print(chunk.content, end="", flush=True)
                if chunk.is_final:
                    usage = chunk.usage
            print()
            message = "".join(parts)
            session = await self.session_manager.get_session(session.id)
            await self.session_manager.add_ai_message(session, message, usage or TokenUsage())
            session = await self.session_manager.get_session(session.id)
            console.print(
                f"Token：prompt={session.total_prompt_tokens}, completion={session.total_completion_tokens}"
            )
