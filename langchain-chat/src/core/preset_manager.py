from __future__ import annotations

from pathlib import Path

import yaml

from models.schemas import Preset, utc_now
from storage.base import StorageBackend


class PresetManager:
    def __init__(self, storage: StorageBackend, presets_path: str | Path = "config/presets.yaml") -> None:
        self.storage = storage
        self.presets_path = Path(presets_path)

    async def load_builtin_presets(self) -> list[Preset]:
        if not self.presets_path.exists():
            return []
        with self.presets_path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
        created = []
        existing_names = {preset.name for preset in await self.storage.list_presets(include_builtin=True)}
        for item in data.get("presets", []):
            if item["name"] in existing_names:
                continue
            preset = Preset(
                name=item["name"],
                description=item.get("description", ""),
                system_prompt=item["system_prompt"],
                is_builtin=True,
            )
            await self.storage.upsert_preset(preset)
            created.append(preset)
        return created

    async def list_presets(self, user_id: str) -> list[Preset]:
        return await self.storage.list_presets(user_id=user_id, include_builtin=True)

    async def create_preset(
        self,
        user_id: str,
        name: str,
        system_prompt: str,
        description: str = "",
    ) -> Preset:
        preset = Preset(
            user_id=user_id,
            name=name,
            description=description,
            system_prompt=system_prompt,
            is_builtin=False,
        )
        return await self.storage.upsert_preset(preset)

    async def update_preset(
        self,
        preset_id: str,
        name: str | None = None,
        system_prompt: str | None = None,
        description: str | None = None,
    ) -> Preset:
        preset = await self.storage.get_preset(preset_id)
        if preset is None:
            raise ValueError("预设不存在")
        if preset.is_builtin:
            raise ValueError("系统内置预设不能编辑")
        if name is not None:
            preset.name = name
        if system_prompt is not None:
            preset.system_prompt = system_prompt
        if description is not None:
            preset.description = description
        preset.updated_at = utc_now()
        return await self.storage.upsert_preset(preset)

    async def delete_preset(self, preset_id: str) -> None:
        await self.storage.delete_preset(preset_id)
