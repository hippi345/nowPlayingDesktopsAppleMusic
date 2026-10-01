"""Create a MusicKit developer token JWT per Apple's documentation."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

import jwt


@dataclass(frozen=True)
class SigningConfig:
    team_id: str
    key_id: str
    private_key_path: Path
    token_ttl_seconds: int = 15_552_000  # 180 days (Apple allows up to ~6 months)

    @classmethod
    def from_json_file(cls, path: Path) -> SigningConfig:
        data = json.loads(path.read_text(encoding="utf-8"))
        team_id = str(data.get("team_id", "")).strip()
        key_id = str(data.get("key_id", "")).strip()
        key_path_raw = str(data.get("private_key_path", "")).strip()
        ttl = int(data.get("token_ttl_seconds", cls.token_ttl_seconds))
        if not team_id or not key_id or not key_path_raw:
            raise ValueError("team_id, key_id, and private_key_path are required in config JSON")
        key_path = Path(key_path_raw).expanduser()
        if not key_path.is_file():
            raise FileNotFoundError(f"Private key not found: {key_path}")
        return cls(team_id=team_id, key_id=key_id, private_key_path=key_path, token_ttl_seconds=ttl)


def sign_developer_token(config: SigningConfig) -> str:
    private_key = config.private_key_path.read_text(encoding="utf-8")
    now = int(time.time())
    headers = {"alg": "ES256", "kid": config.key_id}
    payload = {
        "iss": config.team_id,
        "iat": now,
        "exp": now + config.token_ttl_seconds,
    }
    return jwt.encode(payload, private_key, algorithm="ES256", headers=headers)


def main(argv: list[str] | None = None) -> int:
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Sign an Apple Music API MusicKit developer token (JWT) from a .p8 key.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to signing config JSON (team_id, key_id, private_key_path).",
    )
    args = parser.parse_args(argv)
    try:
        config = SigningConfig.from_json_file(args.config.expanduser().resolve())
        token = sign_developer_token(config)
    except (OSError, ValueError, jwt.PyJWTError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print(token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
