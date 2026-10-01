# nowPlayingDesktopsAppleMusic

[![CI](https://github.com/hippi345/nowPlayingDesktopsAppleMusic/actions/workflows/ci.yml/badge.svg)](https://github.com/hippi345/nowPlayingDesktopsAppleMusic/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**A glass-style album-art tile on your desktop wallpaper** for whatever you are playing in **Apple Music**, using [MusicKit](https://developer.apple.com/documentation/musickit) the way Apple documents it (developer token + music user token).

Same product idea as [nowPlayingDesktops](https://github.com/hippi345/nowPlayingDesktops): wallpaper only, restore your original wallpaper on pause or exit. No play/pause/skip controls on the wallpaper. **Apple Music only** (no Spotify or other services).

**This slice:** Windows, macOS, and Linux desktop wallpaper. iOS/Android are out of scope here.

## What works in this slice

| Area | Status |
|------|--------|
| Wallpaper compose + apply (glass tile, title, artist) | Implemented (ported from sister repo) |
| Windows wallpaper (multi-monitor, restore snapshot) | Implemented |
| macOS wallpaper (`osascript` / optional PyObjC) | Implemented |
| Linux wallpaper (GNOME/KDE/`feh`/etc.) | Implemented |
| MusicKit HTTP client (`GET /v1/me/recent/played/tracks`) | Implemented (not exercised in CI) |
| `run` loop, pause/idle restore, autostart hooks | Implemented |
| `musickit-sign-token` JWT signer from `.p8` + config | Implemented (run locally with your key) |

## Stubbed until Joel configures tokens

Nothing in this repo ships a real Apple Developer **Team ID**, **Key ID**, **`.p8` private key**, or signed **developer token**.

Until Joel adds credentials on his machine:

1. **`MUSICKIT_DEVELOPER_TOKEN`** — unset. The app runs, logs/warns, and `now-playing-apple-music status` explains that the developer token is missing. Generate locally with `musickit-sign-token` (see below).
2. **`MUSICKIT_USER_TOKEN`** — unset. Even with a developer token, the Apple Music API user endpoints need a **music user token** from MusicKit user authorization (documented Apple flow; not implemented as an interactive login UI in this slice). The app reports that the user token is missing instead of crashing or faking playback.
3. **Live playback sync** — with both tokens set, this slice polls **recently played** tracks via the documented REST API. Tighter “true now playing” alignment with the desktop Music app may need follow-up (native MusicKit player state or queue APIs) once tokens exist.

No live MusicKit calls are made in CI.

## Install from source

```bash
git clone https://github.com/hippi345/nowPlayingDesktopsAppleMusic.git
cd nowPlayingDesktopsAppleMusic
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"       # add windows, linux, or macos extras on that OS
```

## Configuration

Copy [`.env.example`](.env.example) to your per-user config directory:

- **Linux:** `~/.config/now-playing-apple-music/.env`
- **macOS:** `~/Library/Application Support/now-playing-apple-music/.env`
- **Windows:** `%APPDATA%\now-playing-apple-music\.env`

Or pass `--env-file PATH` on the CLI.

| Variable | Purpose |
|----------|---------|
| `MUSICKIT_DEVELOPER_TOKEN` | Signed JWT (Bearer token) for the Apple Music API |
| `MUSICKIT_USER_TOKEN` | Music user token from MusicKit authorization |
| `MUSICKIT_STOREFRONT` | Storefront code (default `us`) |

## Sign a developer token (local only)

1. Copy [`config/examples/musickit-signing.example.json`](config/examples/musickit-signing.example.json) to a **gitignored** path (e.g. `config/musickit-signing.local.json`).
2. Point `private_key_path` at your **local** `AuthKey_*.p8` (also gitignored).
3. Run:

```bash
musickit-sign-token --config config/musickit-signing.local.json
```

Paste the printed JWT into `MUSICKIT_DEVELOPER_TOKEN` in your `.env`. **Do not commit** keys, tokens, or realistic-looking placeholders (GitHub secret scanning is enabled).

## Run

```bash
now-playing-apple-music status    # config check only (no API call)
now-playing-apple-music run       # poll MusicKit and update wallpaper
now-playing-apple-music restore   # restore saved original wallpaper
```

Common flags: `-v` / `--verbose`, `--once`, `--poll-interval SECONDS`, `--no-online-art` (skip downloading MusicKit artwork URLs).

### Platform notes

- **Windows:** `pip install -e ".[windows]"` for WinRT helpers used by some diagnostics; core wallpaper uses Win32 APIs.
- **macOS:** `pip install -e ".[macos]"` for better per-display wallpaper control.
- **Linux:** `pip install -e ".[linux]"` if you use D-Bus-related helpers; wallpaper backends match the sister project (GNOME `gsettings`, KDE tools, `feh`, etc.).

## Login autostart

```bash
now-playing-apple-music autostart enable
now-playing-apple-music autostart status
now-playing-apple-music autostart disable
```

Autostart enable requires `MUSICKIT_DEVELOPER_TOKEN` in your resolved `.env` file.

## License

MIT — see [LICENSE](LICENSE).
