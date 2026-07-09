from __future__ import annotations

import asyncio
from pathlib import Path

from core.chat_engine import ChatEngine
from core.config_manager import ConfigManager
from core.preset_manager import PresetManager
from core.session_manager import SessionManager
from core.user_manager import UserManager
from storage.factory import StorageFactory
from ui.tui.app import TUIApp


async def create_app(project_root: Path | None = None) -> TUIApp:
    root = project_root or Path(__file__).resolve().parents[1]
    config_manager = ConfigManager(root)
    config_manager.setup_logging()
    storage = StorageFactory.create(config_manager.config, root)
    user_manager = UserManager(storage, config_manager.get("llm.default_model", "mock-local"))
    preset_manager = PresetManager(storage, root / "config" / "presets.yaml")
    session_manager = SessionManager(storage, root / config_manager.get("exports.root", "data/users"))
    chat_engine = ChatEngine(config_manager.config)
    return TUIApp(
        config_manager=config_manager,
        storage=storage,
        user_manager=user_manager,
        preset_manager=preset_manager,
        session_manager=session_manager,
        chat_engine=chat_engine,
    )


async def main() -> None:
    app = await create_app()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
