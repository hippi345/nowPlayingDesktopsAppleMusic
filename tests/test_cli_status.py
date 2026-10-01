from now_playing_apple_music.cli import main


def test_status_without_tokens(capsys, monkeypatch):
    monkeypatch.delenv("MUSICKIT_DEVELOPER_TOKEN", raising=False)
    monkeypatch.delenv("MUSICKIT_USER_TOKEN", raising=False)
    code = main(["status"])
    out = capsys.readouterr().out
    assert code == 0
    assert "developer token" in out.lower()
