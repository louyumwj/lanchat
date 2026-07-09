from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.config_manager import ConfigManager
from core.preset_manager import PresetManager
from storage.factory import StorageFactory


async def main() -> None:
    config_manager = ConfigManager(ROOT)
    storage = StorageFactory.create(config_manager.config, ROOT)
    await storage.init()
    await PresetManager(storage, ROOT / "config" / "presets.yaml").load_builtin_presets()
    await storage.close()
    print(f"数据库初始化完成，当前环境：{config_manager.env}")


if __name__ == "__main__":
    asyncio.run(main())
