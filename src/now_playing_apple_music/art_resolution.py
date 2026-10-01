"""Resolve album art from MusicKit artwork URLs or placeholders."""

from __future__ import annotations

import hashlib
import io
import logging
from dataclasses import dataclass
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

from now_playing_apple_music.playback_types import TrackPlayback

logger = logging.getLogger(__name__)

ART_DOWNLOAD_TIMEOUT_SECONDS = 10.0


@dataclass(frozen=True)
class ResolvedArt:
    image: Image.Image
    source: str
    detail: str = ""


def _placeholder_image(title: str, artist: str, size: int = 800) -> Image.Image:
    seed = hashlib.sha256(f"{title}|{artist}".encode()).digest()
    r, g, b = seed[0], seed[1], seed[2]
    img = Image.new("RGBA", (size, size), (r, g, b, 255))
    draw = ImageDraw.Draw(img)
    text = f"{title}\n{artist}" if artist else title
    try:
        font = ImageFont.load_default()
    except OSError:
        font = None
    draw.multiline_text((24, size // 2 - 24), text, fill=(255, 255, 255, 230), font=font, spacing=8)
    return img


def _download_art_url(
    url: str,
    *,
    session: requests.Session | None,
    timeout_seconds: float = ART_DOWNLOAD_TIMEOUT_SECONDS,
) -> bytes | None:
    if not url:
        return None
    http = session or requests.Session()
    try:
        response = http.get(url, timeout=timeout_seconds)
        response.raise_for_status()
        return response.content
    except requests.RequestException:
        logger.warning("Failed to download artwork from %s", url, exc_info=True)
        return None


def resolve_track_art(
    track: TrackPlayback,
    *,
    download_dir: Path,
    session: requests.Session | None = None,
) -> ResolvedArt:
    """Resolve cover bytes using embedded bytes, MusicKit URL, then placeholder."""
    if track.art_bytes:
        return ResolvedArt(
            image=Image.open(io.BytesIO(track.art_bytes)).convert("RGBA"),
            source="embedded",
        )
    if track.art_url:
        raw = _download_art_url(track.art_url, session=session)
        if raw:
            return ResolvedArt(
                image=Image.open(io.BytesIO(raw)).convert("RGBA"),
                source="musickit_url",
                detail=track.art_url,
            )
    return ResolvedArt(
        image=_placeholder_image(track.title, track.artist),
        source="placeholder",
    )


def describe_track_art(track: TrackPlayback, *, cache_dir: Path) -> str:
    if track.art_bytes:
        return "embedded bytes"
    if track.art_url:
        return f"musickit_url {track.art_url}"
    return "placeholder"
