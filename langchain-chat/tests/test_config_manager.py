from __future__ import annotations

from core.config_manager import ConfigManager


def test_config_manager_loads_environment_override():
    manager = ConfigManager(env="test")
    assert manager.get("app.environment") == "test"
    assert "data/test" in manager.get("storage.sqlite.path")
