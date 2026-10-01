"""Diagnostic lines for MusicKit configuration."""

from __future__ import annotations

from pathlib import Path

from now_playing_apple_music.musickit.config import MusickitConfig
from now_playing_apple_music.playback_factory import build_playback_provider


def playback_diag_lines(*, art_cache_dir: Path) -> list[str]:
    config = MusickitConfig.from_environment()
    provider = build_playback_provider()
    lines = [
        "Playback source: Apple Music (MusicKit API)",
        f"Storefront: {config.storefront}",
        f"Art cache: {art_cache_dir}",
    ]
    reason = provider.availability_reason()
    if reason:
        lines.append(f"Configuration: {reason}")
    else:
        lines.append("Configuration: MusicKit tokens present (API not probed)")
    return lines
