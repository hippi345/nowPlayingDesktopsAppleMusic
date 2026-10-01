from PIL import Image

from now_playing_apple_music.composer import compose_wallpaper


def test_compose_wallpaper_dimensions():
    cover = Image.new("RGBA", (400, 400), (80, 120, 200, 255))
    composed = compose_wallpaper(cover, title="Track", artist="Artist", width=1280, height=720)
    assert composed.size == (1280, 720)
