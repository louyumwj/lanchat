from __future__ import annotations

import asyncio

from core.chat_engine import ChatEngine


def test_chat_engine_mock_stream():
    async def scenario():
        engine = ChatEngine({"llm": {"default_model": "mock-local"}})
        chunks = []
        final_seen = False
        async for chunk in engine.stream_reply("你好"):
            chunks.append(chunk.content)
            final_seen = final_seen or chunk.is_final
        assert final_seen
        assert "你好" in "".join(chunks)

    asyncio.run(scenario())
