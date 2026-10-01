"""Allow ``python -m now_playing_apple_music``."""

import sys

if sys.platform == "win32":
    from now_playing_apple_music.platforms.windows_dpi import set_process_dpi_aware

    set_process_dpi_aware()

from now_playing_apple_music.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
