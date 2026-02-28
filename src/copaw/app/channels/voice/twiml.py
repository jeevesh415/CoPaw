# -*- coding: utf-8 -*-
"""TwiML generation helpers for the Voice channel."""
from __future__ import annotations

from xml.sax.saxutils import escape, quoteattr


def build_conversation_relay_twiml(
    ws_url: str,
    *,
    welcome_greeting: str = "Hi! This is CoPaw. How can I help you?",
    tts_provider: str = "google",
    tts_voice: str = "en-US-Journey-D",
    stt_provider: str = "deepgram",
    language: str = "en-US",
    interruptible: bool = True,
) -> str:
    """Build TwiML ``<Response>`` that connects to ConversationRelay.

    Returns an XML string suitable as an HTTP response to Twilio's
    incoming call webhook.
    """
    attrs = (
        f"url={quoteattr(ws_url)}"
        f" welcomeGreeting={quoteattr(welcome_greeting)}"
        f" ttsProvider={quoteattr(tts_provider)}"
        f" voice={quoteattr(tts_voice)}"
        f" transcriptionProvider={quoteattr(stt_provider)}"
        f" language={quoteattr(language)}"
        f' interruptible="{str(interruptible).lower()}"'
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        "<Connect>"
        f"<ConversationRelay {attrs}/>"
        "</Connect>"
        "</Response>"
    )


def build_busy_twiml(message: str = "CoPaw is on another call. Please try again later.") -> str:
    """Build TwiML that speaks a message and hangs up."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        f"<Say>{escape(message)}</Say>"
        "</Response>"
    )


def build_error_twiml(message: str = "An error occurred. Please try again later.") -> str:
    """Build TwiML that speaks an error message and hangs up."""
    return build_busy_twiml(message)
