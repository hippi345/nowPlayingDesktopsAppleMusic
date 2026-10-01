"""Parse artwork URLs from Apple Music API JSON."""

from __future__ import annotations


def artwork_url_from_attributes(attributes: dict) -> str:
    """Return a fetchable HTTPS URL from MusicKit ``artwork`` attributes."""
    artwork = attributes.get("artwork") or {}
    template = artwork.get("url")
    if not template:
        return ""
    width = artwork.get("width") or 1200
    height = artwork.get("height") or 1200
    return template.replace("{w}", str(width)).replace("{h}", str(height)).replace("{f}", "jpg")
