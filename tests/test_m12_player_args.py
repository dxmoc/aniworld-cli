"""M12 tests: mpv argv construction and --mpv-args splitting (offline)."""

from __future__ import annotations

import sys

import pytest

from aniworld_cli import player
from aniworld_cli.models import Stream
from aniworld_cli.player import split_args


def _stream() -> Stream:
    return Stream(url="https://cdn/x.m3u8", headers={"Referer": "https://ref"})


def test_command_is_unchanged_without_new_options():
    """The no-flag path must stay byte-identical: CI and users depend on it."""
    assert player.build_command("mpv", Stream(url="https://cdn/x.m3u8")) == [
        "mpv",
        "--no-terminal",
        "https://cdn/x.m3u8",
    ]


def test_config_dir_and_ipc_come_before_the_url():
    cmd = player.build_command(
        "mpv", _stream(), config_dir="/tmp/cfg", ipc_path="/tmp/s.sock"
    )
    assert cmd[0] == "mpv" and cmd[-1] == "https://cdn/x.m3u8"
    assert "--config-dir=/tmp/cfg" in cmd
    assert "--input-ipc-server=/tmp/s.sock" in cmd
    assert cmd.index("--config-dir=/tmp/cfg") < cmd.index("https://cdn/x.m3u8")


def test_extra_args_are_appended_before_the_url():
    cmd = player.build_command("mpv", _stream(), extra=["--mute=yes"])
    assert cmd[-2:] == ["--mute=yes", "https://cdn/x.m3u8"]


def test_headers_and_title_still_work_alongside_new_options():
    cmd = player.build_command(
        "mpv", _stream(), title="Frieren - S01E01", config_dir="/tmp/cfg"
    )
    assert "--user-agent=" not in " ".join(cmd)
    assert "--http-header-fields=Referer: https://ref" in cmd
    assert "--force-media-title=Frieren - S01E01" in cmd


@pytest.mark.parametrize("posix", [True, False], ids=["linux", "windows"])
def test_split_args_unquotes_attached_values_on_every_platform(monkeypatch, posix):
    """``--script-opts="a=b,c=d"``: on Windows the quotes sit *inside* the token.

    ``shlex(posix=False)`` hands back the token with its quotes attached to the
    option name, so checking only the first and last character left them in and
    mpv parsed ``"a`` as the value. Both branches are exercised on any OS.
    """
    monkeypatch.setattr(player, "_POSIX", posix)

    assert player.split_args('--script-opts="a=b,c=d"') == ["--script-opts=a=b,c=d"]
    assert player.split_args("--geometry=1280x720 --mute=yes") == [
        "--geometry=1280x720",
        "--mute=yes",
    ]
    assert player.split_args("--mute=yes") == ["--mute=yes"]


def test_split_args_handles_quotes_and_backslashes():
    assert split_args(None) == []
    assert split_args("") == []
    assert split_args("--mute=yes") == ["--mute=yes"]
    assert split_args('--geometry=1280x720 --mute=yes') == [
        "--geometry=1280x720",
        "--mute=yes",
    ]
    assert split_args('--script-opts="a=b,c=d"') == ["--script-opts=a=b,c=d"]
    if not sys.platform.startswith("win"):
        assert split_args("--screenshot-dir=/tmp/a b".replace(" b", "\\ b")) == [
            "--screenshot-dir=/tmp/a b"
        ]


def test_mpv_args_accepts_a_value_that_starts_with_a_dash():
    """The documented form is --mpv-args "--mute=yes"; argparse chokes on it."""
    from aniworld_cli.__main__ import _join_mpv_args, build_parser

    both = build_parser().parse_args(
        _join_mpv_args(["--mpv-args", "--geometry=1400x850", "frieren"])
    )
    assert both.mpv_args == "--geometry=1400x850"
    assert both.query == "frieren"

    # The --opt=value spelling must keep working unchanged.
    glued = build_parser().parse_args(["--mpv-args=--mute=yes"])
    assert glued.mpv_args == "--mute=yes"

    # Nothing else in argv is touched.
    assert _join_mpv_args(["--lang", "ger-dub", "frieren"]) == [
        "--lang",
        "ger-dub",
        "frieren",
    ]
