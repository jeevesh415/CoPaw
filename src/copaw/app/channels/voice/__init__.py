# -*- coding: utf-8 -*-
"""Voice channel: Twilio ConversationRelay + Cloudflare Tunnel."""

try:
    from .channel import VoiceChannel

    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    VoiceChannel = None  # type: ignore[assignment,misc]

__all__ = ["VoiceChannel", "VOICE_AVAILABLE"]
