from now_playing_apple_music.musickit.artwork import artwork_url_from_attributes


def test_artwork_template_substitution():
    url = artwork_url_from_attributes(
        {
            "artwork": {
                "url": "https://example.com/{w}x{h}bb.{f}",
                "width": 300,
                "height": 300,
            }
        }
    )
    assert url == "https://example.com/300x300bb.jpg"
