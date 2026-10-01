"""Load MusicKit settings from ``.env`` files without a shell environment."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import dotenv_values, load_dotenv

from now_playing_apple_music.config import user_config_dir

logger = logging.getLogger(__name__)

MUSICKIT_ENV_KEYS = (
    "MUSICKIT_DEVELOPER_TOKEN",
    "MUSICKIT_USER_TOKEN",
    "MUSICKIT_STOREFRONT",
)


def env_file_candidates(*, explicit: Path | None = None) -> list[Path]:
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(explicit.expanduser())
    env_from_var = os.environ.get("NOW_PLAYING_ENV_FILE", "").strip()
    if env_from_var:
        candidates.append(Path(env_from_var).expanduser())
    candidates.append(user_config_dir() / ".env")
    candidates.append(Path.cwd() / ".env")
    return candidates


def find_env_file(*, explicit: Path | None = None) -> Path | None:
    for path in env_file_candidates(explicit=explicit):
        if path.is_file():
            return path.resolve()
    return None


def load_environment(*, explicit: Path | None = None, verbose: bool = False) -> Path | None:
    path = find_env_file(explicit=explicit)
    if path is None:
        return None
    load_dotenv(path, override=False)
    if verbose:
        logger.debug("Loaded environment from %s", path)
    return path


def merged_env_values(*, explicit: Path | None = None) -> dict[str, str | None]:
    merged: dict[str, str | None] = {key: os.environ.get(key) for key in MUSICKIT_ENV_KEYS}
    path = find_env_file(explicit=explicit)
    if path is not None:
        for key, value in dotenv_values(path).items():
            if value is not None and not merged.get(key):
                merged[key] = value
    return merged


def musickit_tokens_configured(*, explicit: Path | None = None) -> bool:
    values = merged_env_values(explicit=explicit)
    return bool((values.get("MUSICKIT_DEVELOPER_TOKEN") or "").strip())


def default_env_file_hint() -> str:
    return str(user_config_dir() / ".env")


def missing_env_file_message() -> str:
    return (
        "Cannot enable autostart: MusicKit settings were not found. "
        f"Create {default_env_file_hint()} with MUSICKIT_DEVELOPER_TOKEN "
        "(see .env.example and README), or pass --env-file PATH."
    )
