"""M16 tests: the opt-in Anime4K flag (offline, no mpv, no network)."""

from __future__ import annotations

import os

import pytest

from aniworld_cli import cli, player, shaders
from aniworld_cli.__main__ import build_parser
from aniworld_cli.models import Stream


def _stream() -> Stream:
    return Stream(url="https://cdn/x.m3u8", headers={"Referer": "https://ref"})


def _args(*extra: str):
    return build_parser().parse_args(["--no-menu", *extra, "frieren"])


@pytest.fixture
def captured(monkeypatch):
    """Record the argv handed to mpv instead of starting it."""
    seen: dict[str, object] = {}

    def fake_play(stream, player_path, title=None, extra=None):
        seen["extra"] = list(extra or [])
        return 0

    monkeypatch.setattr(player, "play", fake_play)
    return seen


# --- the preset table -----------------------------------------------------


def test_every_preset_resolves_to_shipped_files():
    for preset in shaders.PRESETS:
        assert shaders.missing_files(preset) == [], preset


def test_presets_only_name_glsl_files_that_exist():
    shipped = {path.name for path in shaders.shader_dir().glob("*.glsl")}
    for preset, names in shaders.PRESETS.items():
        assert set(names) <= shipped, preset
        # A file may legitimately appear twice (Mode A upscales in two passes),
        # so only the presence is asserted, never uniqueness.


def test_off_is_the_empty_chain():
    assert shaders.files("off") == []
    assert shaders.glsl_value("off") == ""


def test_glsl_value_is_absolute_and_path_separated():
    parts = shaders.glsl_value("fast").split(os.pathsep)
    assert len(parts) == len(shaders.PRESETS["fast"])
    assert all(os.path.isabs(part) for part in parts)
    assert all(part.endswith(".glsl") and os.path.isfile(part) for part in parts)


# --- the flag -------------------------------------------------------------


def test_flag_accepts_every_preset():
    for preset in shaders.PRESETS:
        assert _args("--anime4k", preset).anime4k == preset


def test_flag_rejects_an_unknown_preset():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["--anime4k", "ultra", "frieren"])


# --- wiring into the mpv argv --------------------------------------------


def test_without_the_flag_nothing_is_added(captured):
    assert cli.play_stream(_stream(), "mpv", None, _args()) == 0
    assert captured["extra"] == []


def test_off_adds_nothing_either(captured):
    assert cli.play_stream(_stream(), "mpv", None, _args("--anime4k", "off")) == 0
    assert captured["extra"] == []


def test_preset_becomes_one_glsl_shaders_argument(captured):
    assert cli.play_stream(_stream(), "mpv", None, _args("--anime4k", "fast")) == 0
    assert captured["extra"] == [f"--glsl-shaders={shaders.glsl_value('fast')}"]


def test_user_arguments_come_after_the_shaders(captured):
    """mpv's last-wins rule must leave the final say with --mpv-args."""
    args = _args("--anime4k", "restore", "--mpv-args=--contrast=5")
    assert cli.play_stream(_stream(), "mpv", None, args) == 0
    assert captured["extra"] == [
        f"--glsl-shaders={shaders.glsl_value('restore')}",
        "--contrast=5",
    ]


def test_missing_shader_files_warn_but_still_play(monkeypatch, captured, capsys, tmp_path):
    """A bundle without the package data must not play shaders silently."""
    monkeypatch.setattr(shaders, "shader_dir", lambda: tmp_path)
    assert cli.play_stream(_stream(), "mpv", None, _args("--anime4k", "fast")) == 0
    assert captured["extra"] == []
    assert "playing without them" in capsys.readouterr().out
