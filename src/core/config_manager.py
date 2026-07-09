from __future__ import annotations

import logging
import logging.config
import os
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency fallback
    load_dotenv = None


ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")


class ConfigManager:
    """加载基础配置、环境覆盖配置和 .env 文件。"""

    def __init__(self, project_root: str | Path | None = None, env: str | None = None) -> None:
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.env = env or os.getenv("APP_ENV", "dev")
        self.config = self.load()

    def load(self) -> dict[str, Any]:
        self._load_env_files()
        base = self._read_yaml(self.project_root / "config.yaml")
        override = self._read_yaml(self.project_root / f"config.{self.env}.yaml")
        merged = deep_merge(base, override)
        merged = expand_env_values(merged)
        merged.setdefault("app", {})["environment"] = self.env
        return merged

    def setup_logging(self) -> None:
        log_config_path = self.project_root / self.get("logging.config_path", "config/logging.yaml")
        if not log_config_path.exists():
            logging.basicConfig(level=logging.INFO)
            return

        logs_dir = self.project_root / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        config = self._read_yaml(log_config_path)
        for handler in config.get("handlers", {}).values():
            filename = handler.get("filename")
            if filename:
                handler["filename"] = str(self.project_root / filename)
        logging.config.dictConfig(config)

    def get(self, dotted_key: str, default: Any = None) -> Any:
        value: Any = self.config
        for part in dotted_key.split("."):
            if not isinstance(value, dict) or part not in value:
                return default
            value = value[part]
        return value

    def set(self, dotted_key: str, new_value: Any) -> None:
        target = self.config
        parts = dotted_key.split(".")
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = new_value

    def available_models(self) -> list[str]:
        return [item["name"] for item in self.get("llm.models", []) if "name" in item]

    def _load_env_files(self) -> None:
        if load_dotenv is None:
            return
        load_dotenv(self.project_root / ".env", override=False)
        load_dotenv(self.project_root / f".env.{self.env}", override=True)

    @staticmethod
    def _read_yaml(path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
        if not isinstance(data, dict):
            raise ValueError(f"YAML root must be a mapping: {path}")
        return data


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def expand_env_values(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: expand_env_values(item) for key, item in value.items()}
    if isinstance(value, list):
        return [expand_env_values(item) for item in value]
    if isinstance(value, str):
        return ENV_PATTERN.sub(lambda match: os.getenv(match.group(1), ""), value)
    return value
