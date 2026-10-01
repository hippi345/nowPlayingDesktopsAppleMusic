"""Playback provider protocol."""

from __future__ import annotations

from typing import Protocol

from now_playing_apple_music.playback_types import TrackPlayback


class PlaybackProvider(Protocol):
    source_name: str

    def fetch_current(self) -> TrackPlayback | None:
        """Return the current track snapshot, or ``None`` when idle/unavailable."""

    def availability_reason(self) -> str | None:
        """Human-readable reason when this source cannot run, or ``None`` if OK."""

    def peek_current(self) -> TrackPlayback | None:
        """Best-effort snapshot for diagnostics (no side effects)."""
