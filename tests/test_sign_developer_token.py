import json
from pathlib import Path

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from now_playing_apple_music.musickit.sign_developer_token import (
    SigningConfig,
    sign_developer_token,
)


def test_sign_developer_token_round_trip(tmp_path: Path):
    key = ec.generate_private_key(ec.SECP256R1())
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    key_path = tmp_path / "test.p8"
    key_path.write_bytes(pem)
    config_path = tmp_path / "signing.json"
    config_path.write_text(
        json.dumps(
            {
                "team_id": "TEAM123",
                "key_id": "KEY123",
                "private_key_path": str(key_path),
                "token_ttl_seconds": 3600,
            }
        ),
        encoding="utf-8",
    )
    config = SigningConfig.from_json_file(config_path)
    token = sign_developer_token(config)
    public_key = key.public_key()
    decoded = jwt.decode(
        token,
        public_key,
        algorithms=["ES256"],
        options={"verify_exp": False},
    )
    assert decoded["iss"] == "TEAM123"
