"""HTTP client for documented Apple Music API endpoints."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import requests

from now_playing_apple_music.musickit.artwork import artwork_url_from_attributes
from now_playing_apple_music.musickit.config import MusickitConfig, MusickitTokenStatus
from now_playing_apple_music.playback_types import TrackPlayback, stable_track_id

logger = logging.getLogger(__name__)

MUSICKIT_API_BASE = "https://api.music.apple.com"


@dataclass(frozen=True)
class RecentTrackSnapshot:
    track: TrackPlayback
    raw: dict[str, Any]


class MusickitClient:
    """Calls Apple Music API with developer + music-user tokens."""

    def __init__(
        self,
        config: MusickitConfig,
        *,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config
        self._session = session or requests.Session()

    def token_status(self) -> MusickitTokenStatus:
        return self.config.token_status()

    def _auth_headers(self) -> dict[str, str] | None:
        if self.config.token_status() != MusickitTokenStatus.OK:
            return None
        return {
            "Authorization": f"Bearer {self.config.developer_token}",
            "Music-User-Token": self.config.user_token or "",
        }

    def get_recent_played_tracks(self, *, limit: int = 1) -> list[RecentTrackSnapshot]:
        """``GET /v1/me/recent/played/tracks`` (requires both tokens)."""
        headers = self._auth_headers()
        if headers is None:
            return []
        url = f"{MUSICKIT_API_BASE}/v1/me/recent/played/tracks"
        response = self._session.get(url, headers=headers, params={"limit": limit}, timeout=15)
        response.raise_for_status()
        payload = response.json()
        snapshots: list[RecentTrackSnapshot] = []
        for item in payload.get("data") or []:
            track = self._track_from_resource(item)
            if track is not None:
                snapshots.append(RecentTrackSnapshot(track=track, raw=item))
        return snapshots

    def _track_from_resource(self, resource: dict[str, Any]) -> TrackPlayback | None:
        attributes = resource.get("attributes") or {}
        title = (attributes.get("name") or "").strip()
        artist = (attributes.get("artistName") or "").strip()
        album = (attributes.get("albumName") or "").strip()
        if not title:
            return None
        track_id = resource.get("id") or stable_track_id(title=title, artist=artist, album=album)
        art_url = artwork_url_from_attributes(attributes)
        return TrackPlayback(
            track_id=str(track_id),
            art_url=art_url,
            title=title,
            artist=artist,
            album=album,
            is_playing=True,
        )
