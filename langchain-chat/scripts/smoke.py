from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.chat_engine import ChatEngine
from core.config_manager import ConfigManager
from core.preset_manager import PresetManager
from core.session_manager import SessionManager
from core.user_manager import UserManager
from models.schemas import TokenUsage
from storage.factory import StorageFactory


async def smoke_once(env: str) -> None:
    os.environ["APP_ENV"] = env
    config_manager = ConfigManager(ROOT, env=env)
    storage = StorageFactory.create(config_manager.config, ROOT)
    await storage.init()
    await PresetManager(storage, ROOT / "config" / "presets.yaml").load_builtin_presets()
    user_manager = UserManager(storage, config_manager.get("llm.default_model", "mock-local"))
    username = f"smoke_{env}"
    user = await storage.get_user_by_username(username)
    if user is None:
        user = await user_manager.create_user(username)
    session_manager = SessionManager(storage, ROOT / config_manager.get("exports.root", "data/users"))
    session = await session_manager.create_session(user.id, user.default_model, title=f"{env} 冒烟会话")
    await session_manager.add_user_message(session, "你好，执行一次冒烟测试")
    reply_parts = []
    usage = None
    async for chunk in ChatEngine(config_manager.config).stream_reply("你好，执行一次冒烟测试"):
        reply_parts.append(chunk.content)
        if chunk.is_final:
            usage = chunk.usage
    session = await session_manager.get_session(session.id)
    await session_manager.add_ai_message(session, "".join(reply_parts), usage or TokenUsage())
    await session_manager.export_markdown(username, session.id)
    await storage.close()
    print(f"{env}: ok")


async def main() -> None:
    envs = sys.argv[1:] or ["dev", "test", "prod"]
    for env in envs:
        await smoke_once(env)


if __name__ == "__main__":
    asyncio.run(main())
