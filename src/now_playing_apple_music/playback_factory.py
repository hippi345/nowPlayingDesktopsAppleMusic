"""Construct the Apple Music playback provider."""

from __future__ import annotations

from now_playing_apple_music.sources.musickit_provider import (
    MusickitPlaybackProvider,
    build_musickit_provider,
)


def build_playback_provider() -> MusickitPlaybackProvider:
    return build_musickit_provider()
