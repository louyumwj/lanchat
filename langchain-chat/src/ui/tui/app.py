from __future__ import annotations

from core.chat_engine import ChatEngine
from core.config_manager import ConfigManager
from core.preset_manager import PresetManager
from core.session_manager import SessionManager
from core.user_manager import UserManager
from interface.ui_protocol import AbstractUI
from storage.base import StorageBackend
from ui.tui.chat_view import ChatView
from ui.tui.menu_view import MenuView
from ui.tui.widgets import console, prompt_text


class TUIApp(AbstractUI):
    def __init__(
        self,
        config_manager: ConfigManager,
        storage: StorageBackend,
        user_manager: UserManager,
        preset_manager: PresetManager,
        session_manager: SessionManager,
        chat_engine: ChatEngine,
    ) -> None:
        self.config_manager = config_manager
        self.storage = storage
        self.user_manager = user_manager
        self.preset_manager = preset_manager
        self.session_manager = session_manager
        self.chat_view = ChatView(chat_engine, session_manager, storage)
        self.menu = MenuView()

    async def run(self) -> None:
        await self.storage.init()
        await self.preset_manager.load_builtin_presets()
        if not await self.user_manager.list_users():
            await self.user_manager.ensure_user()
        elif self.user_manager.current_user is None:
            self.user_manager.current_user = (await self.user_manager.list_users())[0]

        while True:
            choice = self.menu.main_menu(self.user_manager.current_user)
            if choice == "1":
                await self.show_user_menu()
            elif choice == "2":
                await self.show_session_menu()
            elif choice == "3":
                await self.show_preset_menu()
            elif choice == "4":
                await self.start_chat()
            elif choice == "5":
                await self.show_settings()
            elif choice == "0":
                await self.storage.close()
                return
            else:
                console.print("请输入有效选项。")

    async def show_main_menu(self) -> None:
        self.menu.main_menu(self.user_manager.current_user)

    async def show_user_menu(self) -> None:
        while True:
            choice = self.menu.user_menu()
            if choice == "1":
                await self.user_manager.create_user(prompt_text("用户名"))
            elif choice == "2":
                await self.user_manager.switch_user(prompt_text("用户名"))
            elif choice == "3":
                username = prompt_text("要删除的用户名")
                confirm = prompt_text("输入 YES 确认删除")
                if confirm == "YES":
                    await self.user_manager.delete_user(username)
            elif choice == "4":
                self.menu.show_users(await self.user_manager.list_users())
            elif choice == "0":
                return

    async def show_session_menu(self) -> None:
        user = await self.require_user()
        while True:
            choice = self.menu.session_menu()
            if choice == "1":
                self.menu.show_sessions(await self.session_manager.list_sessions(user.id))
            elif choice == "2":
                session = await self.create_session_for_user(user.id)
                console.print(f"已新建会话：{session.title}")
            elif choice == "3":
                session = await self.pick_session(user.id)
                if session:
                    await self.session_manager.rename_session(session.id, prompt_text("新标题"))
            elif choice == "4":
                session = await self.pick_session(user.id)
                if session and prompt_text("输入 YES 确认删除") == "YES":
                    await self.session_manager.delete_session(session.id)
            elif choice == "5":
                keyword = prompt_text("关键词")
                results = await self.session_manager.search(user.id, keyword)
                console.table(
                    "搜索结果",
                    ["会话", "角色", "内容"],
                    [[item.session_title, item.role.value, item.content[:60]] for item in results],
                )
            elif choice == "6":
                session = await self.pick_session(user.id)
                if session:
                    path = await self.session_manager.export_markdown(user.username, session.id)
                    console.print(f"已导出：{path}")
            elif choice == "0":
                return

    async def show_preset_menu(self) -> None:
        user = await self.require_user()
        while True:
            choice = self.menu.preset_menu()
            if choice == "1":
                self.menu.show_presets(await self.preset_manager.list_presets(user.id))
            elif choice == "2":
                await self.preset_manager.create_preset(
                    user.id,
                    prompt_text("名称"),
                    prompt_text("System Prompt"),
                    prompt_text("说明"),
                )
            elif choice == "3":
                preset_id = prompt_text("预设 ID 前 8 位或完整 ID")
                preset = await self.resolve_preset(user.id, preset_id)
                if preset:
                    await self.preset_manager.update_preset(
                        preset.id,
                        name=prompt_text("新名称"),
                        system_prompt=prompt_text("新 System Prompt"),
                        description=prompt_text("新说明"),
                    )
            elif choice == "4":
                preset = await self.resolve_preset(user.id, prompt_text("预设 ID 前 8 位或完整 ID"))
                if preset:
                    await self.preset_manager.delete_preset(preset.id)
            elif choice == "0":
                return

    async def start_chat(self) -> None:
        user = await self.require_user()
        session = await self.create_session_for_user(user.id)
        await self.chat_view.chat_loop(session)

    async def show_settings(self) -> None:
        user = await self.require_user()
        models = self.config_manager.available_models()
        console.print(f"可用模型：{', '.join(models)}")
        model = prompt_text("新的默认模型")
        if model:
            await self.user_manager.update_default_model(user, model)

    async def create_session_for_user(self, user_id: str):
        user = await self.require_user()
        presets = await self.preset_manager.list_presets(user.id)
        self.menu.show_presets(presets)
        preset_choice = prompt_text("预设 ID 前 8 位，或直接回车不使用")
        preset = await self.resolve_preset(user.id, preset_choice) if preset_choice else None
        return await self.session_manager.create_session(
            user_id=user_id,
            model_name=user.default_model,
            preset_id=preset.id if preset else None,
        )

    async def pick_session(self, user_id: str):
        sessions = await self.session_manager.list_sessions(user_id)
        self.menu.show_sessions(sessions)
        prefix = prompt_text("会话 ID 前 8 位或完整 ID")
        return next((item for item in sessions if item.id.startswith(prefix)), None)

    async def resolve_preset(self, user_id: str, prefix: str):
        presets = await self.preset_manager.list_presets(user_id)
        return next((item for item in presets if item.id.startswith(prefix)), None)

    async def require_user(self):
        if self.user_manager.current_user is not None:
            return self.user_manager.current_user
        return await self.user_manager.ensure_user()
