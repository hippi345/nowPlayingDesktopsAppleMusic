"""Login autostart registration per OS."""

from __future__ import annotations

import os
import plistlib
import sys
from pathlib import Path

from now_playing_apple_music import env_loader
from now_playing_apple_music.config import online_art_enabled, user_config_dir


class AutostartSetupError(RuntimeError):
    """Raised when autostart cannot be configured safely."""


def _windows_run_key_name() -> str:
    return "now-playing-apple-music"


def _quote_windows_argument(value: str) -> str:
    if value == "":
        return '""'
    if any(ch in value for ch in (" ", "\t", '"')):
        return '"' + value.replace('"', r"\"") + '"'
    return value


def _quote_desktop_exec_argument(value: str) -> str:
    if any(ch in value for ch in (" ", "\t", '"', "\\")):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return value


def _runner_invocation() -> list[str]:
    import shutil

    script = shutil.which("now-playing-apple-music")
    if script:
        return [script]
    return [sys.executable, "-m", "now_playing_apple_music"]


def build_run_argv(
    *,
    env_file: Path | None,
    no_online_art: bool = False,
) -> list[str]:
    argv = [*_runner_invocation(), "run"]
    if env_file is not None:
        argv.extend(["--env-file", str(env_file)])
    if no_online_art:
        argv.append("--no-online-art")
    return argv


def _windows_run_command(
    *,
    env_file: Path | None,
    no_online_art: bool = False,
) -> str:
    argv = build_run_argv(env_file=env_file, no_online_art=no_online_art)
    inner = " ".join(_quote_windows_argument(part) for part in argv)
    workdir = _working_directory()
    return f'cmd /c "cd /d {_quote_windows_argument(str(workdir))} && {inner}"'


def _working_directory() -> Path:
    return user_config_dir()


def autostart_enabled() -> bool:
    if sys.platform == "win32":
        return _windows_autostart_enabled()
    if sys.platform == "darwin":
        return _macos_autostart_enabled()
    if sys.platform == "linux":
        return _linux_autostart_enabled()
    return False


def enable_autostart(
    *,
    env_file: Path | None = None,
    no_online_art: bool = False,
) -> None:
    if env_file is not None and not env_file.expanduser().is_file():
        raise AutostartSetupError(env_loader.missing_env_file_message())

    env_loader.load_environment(explicit=env_file)
    disable_online_art = no_online_art or not online_art_enabled()
    resolved_env = env_loader.find_env_file(explicit=env_file)
    if resolved_env is None or not env_loader.musickit_tokens_configured(explicit=env_file):
        raise AutostartSetupError(env_loader.missing_env_file_message())

    if sys.platform == "win32":
        _windows_enable_autostart(env_file=resolved_env, no_online_art=disable_online_art)
    elif sys.platform == "darwin":
        _macos_enable_autostart(env_file=resolved_env, no_online_art=disable_online_art)
    elif sys.platform == "linux":
        _linux_enable_autostart(env_file=resolved_env, no_online_art=disable_online_art)
    else:
        raise OSError(f"Autostart not supported on {sys.platform}")


def disable_autostart() -> None:
    if sys.platform == "win32":
        _windows_disable_autostart()
    elif sys.platform == "darwin":
        _macos_disable_autostart()
    elif sys.platform == "linux":
        _linux_disable_autostart()
    else:
        raise OSError(f"Autostart not supported on {sys.platform}")


def _windows_autostart_enabled() -> bool:
    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
        ) as key:
            winreg.QueryValueEx(key, _windows_run_key_name())
            return True
    except OSError:
        return False


def _windows_enable_autostart(
    *,
    env_file: Path | None,
    no_online_art: bool = False,
) -> None:
    import winreg

    command = _windows_run_command(env_file=env_file, no_online_art=no_online_art)
    with winreg.CreateKeyEx(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
    ) as key:
        winreg.SetValueEx(key, _windows_run_key_name(), 0, winreg.REG_SZ, command)


def read_windows_autostart_command() -> str | None:
    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
        ) as key:
            value, _ = winreg.QueryValueEx(key, _windows_run_key_name())
    except OSError:
        return None
    return str(value) if value else None


def _windows_disable_autostart() -> None:
    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            winreg.DeleteValue(key, _windows_run_key_name())
    except OSError:
        pass


def _linux_config_dir() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME", "").strip()
    if xdg:
        return Path(xdg)
    return Path.home() / ".config"


def _linux_desktop_path() -> Path:
    return _linux_config_dir() / "autostart" / "now-playing-apple-music.desktop"


def _linux_autostart_enabled() -> bool:
    return _linux_desktop_path().is_file()


def _linux_enable_autostart(
    *,
    env_file: Path | None,
    no_online_art: bool = False,
) -> None:
    argv = build_run_argv(env_file=env_file, no_online_art=no_online_art)
    exec_line = " ".join(_quote_desktop_exec_argument(part) for part in argv)
    workdir = _working_directory()
    path = _linux_desktop_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    content = (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=Now Playing Apple Music\n"
        f"Exec={exec_line}\n"
        f"Path={workdir}\n"
        "Terminal=false\n"
        "X-GNOME-Autostart-enabled=true\n"
    )
    path.write_text(content, encoding="utf-8")


def _linux_disable_autostart() -> None:
    path = _linux_desktop_path()
    if path.is_file():
        path.unlink()


def _macos_plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / "com.nowplayingapplemusic.agent.plist"


def _macos_autostart_enabled() -> bool:
    return _macos_plist_path().is_file()


def _macos_enable_autostart(
    *,
    env_file: Path | None,
    no_online_art: bool = False,
) -> None:
    argv = build_run_argv(env_file=env_file, no_online_art=no_online_art)
    plist_path = _macos_plist_path()
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "Label": "com.nowplayingapplemusic.agent",
        "ProgramArguments": argv,
        "WorkingDirectory": str(_working_directory()),
        "RunAtLoad": True,
        "KeepAlive": False,
    }
    with plist_path.open("wb") as handle:
        plistlib.dump(payload, handle)


def _macos_disable_autostart() -> None:
    path = _macos_plist_path()
    if path.is_file():
        path.unlink()
