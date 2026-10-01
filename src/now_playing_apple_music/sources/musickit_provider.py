"""Playback provider backed by the Apple Music API (MusicKit tokens)."""

from __future__ import annotations

import logging

from now_playing_apple_music.musickit.client import MusickitClient
from now_playing_apple_music.musickit.config import MusickitConfig, MusickitTokenStatus
from now_playing_apple_music.playback_types import TrackPlayback

logger = logging.getLogger(__name__)


class MusickitPlaybackProvider:
    """Fetches the most recent Apple Music track when tokens are configured."""

    source_name = "musickit"

    def __init__(self, client: MusickitClient) -> None:
        self._client = client
        self._config = client.config
        self._logged_unconfigured: set[MusickitTokenStatus] = set()

    def availability_reason(self) -> str | None:
        return self._config.availability_message()

    def _log_unconfigured_once(self) -> None:
        status = self._config.token_status()
        if status == MusickitTokenStatus.OK:
            return
        if status in self._logged_unconfigured:
            return
        message = self._config.availability_message()
        if message:
            logger.warning("%s", message)
        self._logged_unconfigured.add(status)

    def fetch_current(self) -> TrackPlayback | None:
        if self._config.token_status() != MusickitTokenStatus.OK:
            self._log_unconfigured_once()
            return None
        try:
            recent = self._client.get_recent_played_tracks(limit=1)
        except Exception:
            logger.exception("MusicKit API request failed")
            return None
        if not recent:
            return None
        return recent[0].track

    def peek_current(self) -> TrackPlayback | None:
        return self.fetch_current()


def build_musickit_provider() -> MusickitPlaybackProvider:
    config = MusickitConfig.from_environment()
    return MusickitPlaybackProvider(MusickitClient(config))
