from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator

from models.schemas import ChatChunk, Message, MessageRole, TokenUsage


class ChatEngine:
    """对话引擎。

    没有 API Key 或使用 mock-local 时走本地模拟流式输出，便于教学和测试。
    配置真实 OpenAI 兼容服务后，会尝试使用 langchain_openai.ChatOpenAI。
    """

    def __init__(self, config: dict) -> None:
        self.config = config
        self.default_model = config.get("llm", {}).get("default_model", "mock-local")
        self.timeout = int(config.get("llm", {}).get("timeout_seconds", 30))
        self.max_retries = int(config.get("llm", {}).get("max_retries", 3))

    async def stream_reply(
        self,
        user_input: str,
        history: list[Message] | None = None,
        model_name: str | None = None,
        system_prompt: str | None = None,
    ) -> AsyncIterator[ChatChunk]:
        model = model_name or self.default_model
        if model == "mock-local" or not os.getenv("API_KEY"):
            async for chunk in self._mock_stream(user_input, history or [], system_prompt):
                yield chunk
            return

        try:
            async for chunk in self._langchain_stream(user_input, history or [], model, system_prompt):
                yield chunk
        except Exception as exc:
            fallback = f"模型调用失败，已回退到本地响应。错误：{exc}"
            for part in split_for_stream(fallback):
                yield ChatChunk(content=part)
            yield ChatChunk(content="", is_final=True, usage=estimate_usage(user_input, fallback))

    async def _mock_stream(
        self,
        user_input: str,
        history: list[Message],
        system_prompt: str | None,
    ) -> AsyncIterator[ChatChunk]:
        prefix = "已收到"
        if system_prompt:
            prefix = "已按预设收到"
        response = f"{prefix}：{user_input}\n\n这是 mock-local 的流式回复，用于无 API Key 时验证多轮会话、保存和导出流程。"
        if history:
            response += f"\n\n当前会话已有 {len(history)} 条历史消息。"
        for part in split_for_stream(response):
            await asyncio.sleep(0)
            yield ChatChunk(content=part)
        yield ChatChunk(content="", is_final=True, usage=estimate_usage(user_input, response))

    async def _langchain_stream(
        self,
        user_input: str,
        history: list[Message],
        model_name: str,
        system_prompt: str | None,
    ) -> AsyncIterator[ChatChunk]:
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI

        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        for message in history:
            if message.role == MessageRole.HUMAN:
                messages.append(HumanMessage(content=message.content))
            elif message.role == MessageRole.AI:
                messages.append(AIMessage(content=message.content))
            elif message.role == MessageRole.SYSTEM:
                messages.append(SystemMessage(content=message.content))
        messages.append(HumanMessage(content=user_input))

        llm = ChatOpenAI(
            model=model_name,
            base_url=os.getenv("API_BASE_URL") or None,
            api_key=os.getenv("API_KEY"),
            timeout=self.timeout,
            max_retries=self.max_retries,
            streaming=True,
        )
        collected = []
        async for chunk in llm.astream(messages):
            content = getattr(chunk, "content", "")
            if content:
                collected.append(content)
                yield ChatChunk(content=str(content))
        response = "".join(collected)
        yield ChatChunk(content="", is_final=True, usage=estimate_usage(user_input, response))


def split_for_stream(text: str, size: int = 8) -> list[str]:
    return [text[index : index + size] for index in range(0, len(text), size)]


def estimate_usage(prompt: str, completion: str) -> TokenUsage:
    return TokenUsage(
        prompt_tokens=max(1, len(prompt) // 4),
        completion_tokens=max(1, len(completion) // 4),
    )
