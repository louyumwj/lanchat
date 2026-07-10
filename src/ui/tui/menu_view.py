from __future__ import annotations

from models.schemas import Preset, Session, User
from ui.tui.widgets import console, prompt_text


class MenuView:
    async def main_menu(self, current_user: User | None) -> str:
        console.rule("LangChain Chat")
        user_label = current_user.username if current_user else "未选择"
        console.print(f"当前用户：{user_label}")
        console.print("1. 用户管理")
        console.print("2. 会话管理")
        console.print("3. 预设管理")
        console.print("4. 开始对话")
        console.print("5. 设置")
        console.print("0. 退出")
        return await prompt_text("请选择")

    async def user_menu(self) -> str:
        console.rule("用户管理")
        console.print("1. 创建用户")
        console.print("2. 切换用户")
        console.print("3. 删除用户")
        console.print("4. 查看用户")
        console.print("0. 返回")
        return await prompt_text("请选择")

    async def session_menu(self) -> str:
        console.rule("会话管理")
        console.print("1. 查看会话")
        console.print("2. 新建会话")
        console.print("3. 重命名会话")
        console.print("4. 删除会话")
        console.print("5. 搜索消息")
        console.print("6. 导出会话")
        console.print("0. 返回")
        return await prompt_text("请选择")

    async def preset_menu(self) -> str:
        console.rule("预设管理")
        console.print("1. 查看预设")
        console.print("2. 新增个人预设")
        console.print("3. 编辑个人预设")
        console.print("4. 删除个人预设")
        console.print("0. 返回")
        return await prompt_text("请选择")

    def show_users(self, users: list[User]) -> None:
        console.table(
            "用户列表",
            ["用户名", "默认模型", "创建时间"],
            [[user.username, user.default_model, user.created_at.isoformat()] for user in users],
        )

    def show_sessions(self, sessions: list[Session]) -> None:
        console.table(
            "会话列表",
            ["ID", "标题", "模型", "更新时间"],
            [
                [session.id[:8], session.title, session.model_name, session.updated_at.isoformat()]
                for session in sessions
            ],
        )

    def show_presets(self, presets: list[Preset]) -> None:
        console.table(
            "预设列表",
            ["ID", "名称", "类型", "说明"],
            [
                [
                    preset.id[:8],
                    preset.name,
                    "系统" if preset.is_builtin else "个人",
                    preset.description,
                ]
                for preset in presets
            ],
        )
