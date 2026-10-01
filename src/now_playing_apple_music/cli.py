"""Command-line entry points."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

if sys.platform == "win32":
    from now_playing_apple_music.platforms.windows_dpi import (
        set_process_dpi_aware as _win32_dpi_bootstrap,
    )

    _win32_dpi_bootstrap()

from now_playing_apple_music.config import (
    DEFAULT_POLL_INTERVAL_SECONDS,
    default_cache_dir,
    state_file_path,
    user_config_dir,
)
from now_playing_apple_music.env_loader import load_environment
from now_playing_apple_music.logging_setup import configure_application_logging
from now_playing_apple_music.platforms import UnsupportedPlatformError, get_platform
from now_playing_apple_music.playback_diag import playback_diag_lines
from now_playing_apple_music.playback_factory import build_playback_provider
from now_playing_apple_music.runner import NowPlayingRunner, RunnerDeps


def _configure_logging(verbose: bool, *, command: str) -> None:
    configure_application_logging(
        verbose=verbose,
        enable_file_log=command == "run",
    )


def _peek_command_and_verbose(argv: list[str]) -> tuple[str, bool]:
    verbose = _argv_requests_verbose(argv)
    command = "run"
    for token in argv:
        if token in {"run", "restore", "autostart", "diag", "status"}:
            command = token
            break
    return command, verbose


def _shared_verbose_parser() -> argparse.ArgumentParser:
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    shared.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help="Load MusicKit settings from this .env file (see README).",
    )
    shared.add_argument(
        "--no-online-art",
        action="store_true",
        help="Do not fetch album art over the network (MusicKit artwork URLs).",
    )
    return shared


def build_parser() -> argparse.ArgumentParser:
    shared = _shared_verbose_parser()
    parser = argparse.ArgumentParser(
        prog="now-playing-apple-music",
        description="Set your desktop wallpaper to the Apple Music track you are playing.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(
        "run",
        help="Poll Apple Music (MusicKit) and update the wallpaper.",
        parents=[shared],
    )
    run_parser.add_argument(
        "--poll-interval",
        type=float,
        default=DEFAULT_POLL_INTERVAL_SECONDS,
        help=f"Seconds between polls (default {DEFAULT_POLL_INTERVAL_SECONDS}).",
    )
    run_parser.add_argument(
        "--once",
        action="store_true",
        help="Perform a single poll/apply cycle and exit.",
    )
    run_parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="Override the composed-art cache directory.",
    )

    restore_parser = subparsers.add_parser(
        "restore",
        help="Restore the wallpaper saved at startup.",
        parents=[shared],
    )
    restore_parser.add_argument(
        "--state-file",
        type=Path,
        default=None,
        help="Override the session state file path.",
    )

    autostart_parser = subparsers.add_parser(
        "autostart",
        help="Enable or disable login autostart for the wallpaper runner.",
        parents=[shared],
    )
    autostart_parser.add_argument(
        "action",
        choices=("enable", "disable", "status"),
        help="Register, remove, or query autostart.",
    )

    subparsers.add_parser(
        "status",
        help="Show MusicKit configuration status (no network calls).",
        parents=[shared],
    )

    subparsers.add_parser(
        "diag",
        help="Print display/wallpaper diagnostics.",
        parents=[shared],
    )
    return parser


def _print_musickit_status() -> int:
    provider = build_playback_provider()
    reason = provider.availability_reason()
    if reason:
        print(reason)
        return 0
    print("MusicKit developer and user tokens are configured.")
    print("Live Apple Music API calls are not made by this command; use `run` once tokens are set.")
    return 0


def _run(args: argparse.Namespace) -> int:
    from now_playing_apple_music.single_instance import ensure_single_run_instance

    run_lock = ensure_single_run_instance()
    if run_lock is None:
        return 0
    try:
        return _run_with_lock(args)
    finally:
        run_lock.release()


def _run_with_lock(args: argparse.Namespace) -> int:
    try:
        platform = get_platform()
    except UnsupportedPlatformError as exc:
        print(exc, file=sys.stderr)
        return 1

    provider = build_playback_provider()
    reason = provider.availability_reason()
    if reason:
        print(reason, file=sys.stderr)

    cache_dir = args.cache_dir or default_cache_dir()
    runner = NowPlayingRunner(
        RunnerDeps(
            platform=platform,
            playback_provider=provider,
            cache_dir=cache_dir,
            state_path=state_file_path(),
            poll_interval_seconds=args.poll_interval,
        )
    )

    try:
        if args.once:
            runner.startup()
            runner.apply_playback_once()
            return 0
        runner.run_forever()
    except KeyboardInterrupt:
        runner.restore_original_wallpaper()
        return 0
    return 0


def _apply_cli_online_art_override(args: argparse.Namespace) -> None:
    if getattr(args, "no_online_art", False):
        import os

        os.environ["NOW_PLAYING_ONLINE_ART"] = "0"


def _autostart(args: argparse.Namespace) -> int:
    from now_playing_apple_music.platforms.autostart import (
        AutostartSetupError,
        autostart_enabled,
        disable_autostart,
        enable_autostart,
    )

    if args.action == "status":
        print("enabled" if autostart_enabled() else "disabled")
        return 0
    if args.action == "enable":
        try:
            enable_autostart(
                env_file=args.env_file,
                no_online_art=getattr(args, "no_online_art", False),
            )
        except AutostartSetupError as exc:
            print(exc, file=sys.stderr)
            return 1
        print("Autostart enabled")
        return 0
    disable_autostart()
    print("Autostart disabled")
    return 0


def _diag(args: argparse.Namespace) -> int:
    from now_playing_apple_music.config import default_cache_dir

    cache_dir = default_cache_dir()
    diag_lines = playback_diag_lines(art_cache_dir=cache_dir / "downloads")
    if sys.platform == "win32":
        from now_playing_apple_music.platforms.windows_diag import (
            collect_windows_diag_report,
            format_windows_diag_report,
        )
        from now_playing_apple_music.platforms.windows_dpi import bootstrap_process_dpi_awareness

        bootstrap_process_dpi_awareness()
        report = collect_windows_diag_report()
        print("\n".join([*diag_lines, "", format_windows_diag_report(report)]))
        return 0
    print("\n".join(diag_lines))
    return 0


def _restore(args: argparse.Namespace) -> int:
    try:
        platform = get_platform()
    except UnsupportedPlatformError as exc:
        print(exc, file=sys.stderr)
        return 1

    runner = NowPlayingRunner(
        RunnerDeps(
            platform=platform,
            playback_provider=build_playback_provider(),
            cache_dir=default_cache_dir(),
            state_path=args.state_file or state_file_path(),
            poll_interval_seconds=DEFAULT_POLL_INTERVAL_SECONDS,
        )
    )
    if runner.restore_original_wallpaper():
        return 0
    print("nothing to restore")
    return 0


def _argv_requests_verbose(argv: list[str]) -> bool:
    return any(token in {"-v", "--verbose"} for token in argv)


def _resolve_env_file_path(explicit: Path | None) -> Path | None:
    if explicit is None:
        return None
    return explicit.expanduser().resolve()


def _ensure_runtime_working_directory() -> None:
    target = user_config_dir()
    target.mkdir(parents=True, exist_ok=True)
    try:
        import os

        os.chdir(target)
    except OSError:
        logging.getLogger(__name__).warning(
            "Could not chdir to %s; relative asset paths may fail",
            target,
        )


def main(argv: list[str] | None = None) -> int:
    if sys.platform == "win32":
        from now_playing_apple_music.platforms.windows_dpi import set_process_dpi_aware

        set_process_dpi_aware()
    argv = list(argv) if argv is not None else sys.argv[1:]
    command, verbose_from_argv = _peek_command_and_verbose(argv)
    parser = build_parser()
    args = parser.parse_args(argv)
    verbose = bool(getattr(args, "verbose", False)) or verbose_from_argv
    _configure_logging(verbose, command=command)
    env_file = _resolve_env_file_path(getattr(args, "env_file", None))
    load_environment(explicit=env_file, verbose=verbose)
    _apply_cli_online_art_override(args)
    if args.command in {"run", "restore"}:
        _ensure_runtime_working_directory()
    if args.command == "run":
        return _run(args)
    if args.command == "restore":
        return _restore(args)
    if args.command == "autostart":
        return _autostart(args)
    if args.command == "status":
        return _print_musickit_status()
    if args.command == "diag":
        return _diag(args)
    parser.error(f"Unknown command {args.command!r}")
    return 2


def _legacy_argv() -> list[str]:
    argv = sys.argv[1:]
    if argv and argv[0] not in {"run", "restore", "autostart", "diag", "status"}:
        return ["run", *argv]
    return argv


def main_macos() -> None:
    raise SystemExit(main(_legacy_argv()))


def main_windows() -> None:
    if sys.platform == "win32":
        from now_playing_apple_music.platforms.windows_dpi import set_process_dpi_aware

        set_process_dpi_aware()
    raise SystemExit(main(_legacy_argv()))


if __name__ == "__main__":
    raise SystemExit(main())
