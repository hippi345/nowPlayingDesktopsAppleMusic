from unittest.mock import MagicMock

from now_playing_apple_music.musickit.client import MusickitClient
from now_playing_apple_music.musickit.config import MusickitConfig


def test_client_parses_recent_track():
    session = MagicMock()
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {
        "data": [
            {
                "id": "123",
                "attributes": {
                    "name": "Song",
                    "artistName": "Artist",
                    "albumName": "Album",
                    "artwork": {
                        "url": "https://example.com/{w}x{h}bb.{f}",
                        "width": 100,
                        "height": 100,
                    },
                },
            }
        ]
    }
    session.get.return_value = response
    config = MusickitConfig(
        developer_token="dev",
        user_token="user",
        storefront="us",
    )
    client = MusickitClient(config, session=session)
    tracks = client.get_recent_played_tracks(limit=1)
    assert len(tracks) == 1
    assert tracks[0].track.title == "Song"
    assert tracks[0].track.is_playing is True
    session.get.assert_called_once()
    args, kwargs = session.get.call_args
    assert "recent/played/tracks" in args[0]
    assert kwargs["headers"]["Authorization"] == "Bearer dev"
    assert kwargs["headers"]["Music-User-Token"] == "user"


def test_client_skips_request_without_tokens():
    session = MagicMock()
    config = MusickitConfig(developer_token=None, user_token=None, storefront="us")
    client = MusickitClient(config, session=session)
    assert client.get_recent_played_tracks() == []
    session.get.assert_not_called()
