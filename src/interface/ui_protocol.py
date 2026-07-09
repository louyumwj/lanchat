from __future__ import annotations

from abc import ABC, abstractmethod


class AbstractUI(ABC):
    @abstractmethod
    async def run(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def show_main_menu(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def start_chat(self) -> None:
        raise NotImplementedError


class FutureWebUIProtocol(ABC):
    @abstractmethod
    async def compare_models(self, prompt: str, model_names: list[str]) -> dict[str, str]:
        raise NotImplementedError

    @abstractmethod
    async def accept_multimodal_input(self, files: list[str]) -> str:
        raise NotImplementedError

    @abstractmethod
    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        raise NotImplementedError
