# -*- coding: utf-8 -*-
"""Tests for ConversationRelayHandler (WebSocket message parsing)."""
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from copaw.app.channels.voice.conversation_relay import ConversationRelayHandler
from copaw.app.channels.voice.session import CallSessionManager


def _make_handler(
    messages=None,
    process_response="Hello from CoPaw!",
):
    """Create a handler with a mock WebSocket and process."""
    ws = AsyncMock()
    if messages is not None:
        # Set up receive_text to return messages in order then raise
        side_effects = [json.dumps(m) for m in messages]
        side_effects.append(Exception("WS closed"))
        ws.receive_text = AsyncMock(side_effect=side_effects)

    session_mgr = CallSessionManager()

    # Mock process that yields a completed message event
    async def mock_process(request):
        event = MagicMock()
        event.object = "message"

        from agentscope_runtime.engine.schemas.agent_schemas import RunStatus

        event.status = RunStatus.Completed
        content_item = MagicMock()

        from agentscope_runtime.engine.schemas.agent_schemas import ContentType

        content_item.type = ContentType.TEXT
        content_item.text = process_response
        event.content = [content_item]
        yield event

    handler = ConversationRelayHandler(
        ws=ws,
        process=mock_process,
        session_mgr=session_mgr,
        channel_type="voice",
    )
    return handler, ws, session_mgr


class TestConversationRelayHandler:
    @pytest.mark.asyncio
    async def test_handle_setup(self):
        messages = [
            {"type": "setup", "callSid": "CA123", "from": "+15551234567", "to": "+15559876543"},
        ]
        handler, ws, session_mgr = _make_handler(messages)
        await handler.handle()

        assert handler.call_sid == "CA123"
        assert handler.caller_info["from"] == "+15551234567"
        assert session_mgr.get_session("CA123") is not None

    @pytest.mark.asyncio
    async def test_handle_prompt(self):
        messages = [
            {"type": "setup", "callSid": "CA123", "from": "+1555", "to": "+1999"},
            {"type": "prompt", "voicePrompt": "What's the weather?"},
        ]
        handler, ws, session_mgr = _make_handler(messages)
        await handler.handle()

        # Verify that text was sent back to Twilio
        calls = ws.send_text.call_args_list
        text_sends = [
            c for c in calls if c.args and "token" in str(c.args[0])
        ]
        assert len(text_sends) > 0

    @pytest.mark.asyncio
    async def test_handle_interrupt(self):
        messages = [
            {"type": "setup", "callSid": "CA123", "from": "+1555", "to": "+1999"},
            {"type": "interrupt", "utteranceUntilInterrupt": "Hello, I was say"},
        ]
        handler, ws, session_mgr = _make_handler(messages)
        await handler.handle()
        # Interrupt handling is logged but doesn't crash
        assert handler.call_sid == "CA123"

    @pytest.mark.asyncio
    async def test_handle_dtmf(self):
        messages = [
            {"type": "setup", "callSid": "CA123", "from": "+1555", "to": "+1999"},
            {"type": "dtmf", "digit": "5"},
        ]
        handler, ws, session_mgr = _make_handler(messages)
        await handler.handle()
        # DTMF handling is logged but doesn't crash
        assert handler.call_sid == "CA123"

    @pytest.mark.asyncio
    async def test_send_text(self):
        handler, ws, session_mgr = _make_handler(messages=[])
        handler._closed = False

        await handler.send_text("Hello!")

        ws.send_text.assert_called()
        sent = json.loads(ws.send_text.call_args.args[0])
        assert sent == {"type": "text", "token": "Hello!", "last": True}

    @pytest.mark.asyncio
    async def test_close(self):
        handler, ws, session_mgr = _make_handler(messages=[])
        handler._closed = False

        await handler.close()

        assert handler._closed is True
        # Should have sent end message
        end_call = None
        for call in ws.send_text.call_args_list:
            data = json.loads(call.args[0])
            if data.get("type") == "end":
                end_call = data
        assert end_call is not None

    @pytest.mark.asyncio
    async def test_session_ended_on_disconnect(self):
        messages = [
            {"type": "setup", "callSid": "CA123", "from": "+1555", "to": "+1999"},
        ]
        handler, ws, session_mgr = _make_handler(messages)
        await handler.handle()

        # After WS closes, session should be ended
        session = session_mgr.get_session("CA123")
        assert session is not None
        assert session.status == "ended"

    @pytest.mark.asyncio
    async def test_empty_prompt_ignored(self):
        messages = [
            {"type": "setup", "callSid": "CA123", "from": "+1555", "to": "+1999"},
            {"type": "prompt", "voicePrompt": "   "},
        ]
        handler, ws, session_mgr = _make_handler(messages)
        await handler.handle()

        # Only setup message processed; no text sent for empty prompt
        text_sends = [
            c for c in ws.send_text.call_args_list
            if c.args and "token" in str(c.args[0])
        ]
        assert len(text_sends) == 0
