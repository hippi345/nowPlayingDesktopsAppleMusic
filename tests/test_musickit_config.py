from now_playing_apple_music.musickit.config import MusickitConfig, MusickitTokenStatus


def test_missing_developer_token(monkeypatch):
    monkeypatch.delenv("MUSICKIT_DEVELOPER_TOKEN", raising=False)
    monkeypatch.delenv("MUSICKIT_USER_TOKEN", raising=False)
    config = MusickitConfig.from_environment()
    assert config.token_status() == MusickitTokenStatus.DEVELOPER_TOKEN_MISSING
    assert "developer token" in (config.availability_message() or "").lower()


def test_missing_user_token(monkeypatch):
    monkeypatch.setenv("MUSICKIT_DEVELOPER_TOKEN", "dev.jwt.example")
    monkeypatch.delenv("MUSICKIT_USER_TOKEN", raising=False)
    config = MusickitConfig.from_environment()
    assert config.token_status() == MusickitTokenStatus.USER_TOKEN_MISSING


def test_ok_when_both_set(monkeypatch):
    monkeypatch.setenv("MUSICKIT_DEVELOPER_TOKEN", "dev.jwt.example")
    monkeypatch.setenv("MUSICKIT_USER_TOKEN", "user.token.example")
    config = MusickitConfig.from_environment()
    assert config.token_status() == MusickitTokenStatus.OK
    assert config.availability_message() is None
