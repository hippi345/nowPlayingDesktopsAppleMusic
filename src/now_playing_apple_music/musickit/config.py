"""Load MusicKit credentials from the environment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import StrEnum


class MusickitTokenStatus(StrEnum):
    OK = "ok"
    DEVELOPER_TOKEN_MISSING = "developer_token_missing"
    USER_TOKEN_MISSING = "user_token_missing"


@dataclass(frozen=True)
class MusickitConfig:
    developer_token: str | None
    user_token: str | None
    storefront: str

    @classmethod
    def from_environment(cls) -> MusickitConfig:
        dev = (os.environ.get("MUSICKIT_DEVELOPER_TOKEN") or "").strip() or None
        user = (os.environ.get("MUSICKIT_USER_TOKEN") or "").strip() or None
        storefront = (os.environ.get("MUSICKIT_STOREFRONT") or "us").strip().lower() or "us"
        return cls(developer_token=dev, user_token=user, storefront=storefront)

    def token_status(self) -> MusickitTokenStatus:
        if not self.developer_token:
            return MusickitTokenStatus.DEVELOPER_TOKEN_MISSING
        if not self.user_token:
            return MusickitTokenStatus.USER_TOKEN_MISSING
        return MusickitTokenStatus.OK

    def availability_message(self) -> str | None:
        status = self.token_status()
        if status == MusickitTokenStatus.DEVELOPER_TOKEN_MISSING:
            return (
                "MusicKit developer token is not configured. Set MUSICKIT_DEVELOPER_TOKEN "
                "(sign a JWT with musickit-sign-token; see README)."
            )
        if status == MusickitTokenStatus.USER_TOKEN_MISSING:
            return (
                "MusicKit user token is not configured. Set MUSICKIT_USER_TOKEN after "
                "authorizing Apple Music (MusicKit user token; see README)."
            )
        return None
