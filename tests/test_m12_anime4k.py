"""M12 tests: Anime4K shader chains, cache handling and mpv flags (no network)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from aniworld_cli import anime4k, player
from aniworld_cli.models import Stream


def test_parse_mode():
    assert anime4k.parse_mode(None) is None
    assert anime4k.parse_mode("off") is None
    assert anime4k.parse_mode(" A ") == "a"
    assert anime4k.parse_mode("a+a") == "a+a"
    with pytest.raises(anime4k.Anime4KError):
        anime4k.parse_mode("d")


def test_chain_mode_a_fast():
    assert anime4k.chain("a") == [
        "Restore/Anime4K_Clamp_Highlights.glsl",
        "Restore/Anime4K_Restore_CNN_M.glsl",
        "Upscale/Anime4K_Upscale_CNN_x2_M.glsl",
        "Upscale/Anime4K_AutoDownscalePre_x2.glsl",
        "Upscale/Anime4K_AutoDownscalePre_x4.glsl",
        "Upscale/Anime4K_Upscale_CNN_x2_S.glsl",
    ]


def test_chain_hq_uses_bigger_variants():
    assert anime4k.chain("a", hq=True)[1] == "Restore/Anime4K_Restore_CNN_VL.glsl"
    assert anime4k.chain("a", hq=True)[-1] == "Upscale/Anime4K_Upscale_CNN_x2_M.glsl"
    # Non-CNN shaders are unchanged by the quality tier.
    assert anime4k.chain("a")[0] == anime4k.chain("a", hq=True)[0]


def test_every_mode_ends_with_an_upscaler():
    for mode in anime4k.MODE_NAMES:
        assert anime4k.chain(mode)[-1].startswith("Upscale/Anime4K_Upscale_CNN_x2_")
        assert anime4k.chain(mode)[0] == "Restore/Anime4K_Clamp_Highlights.glsl"


def test_required_shaders_covers_every_mode():
    required = anime4k.required_shaders()
    assert len(required) == len(set(required))
    for mode in anime4k.MODE_NAMES:
        for hq in (False, True):
            for relative in anime4k.chain(mode, hq):
                assert relative in required


def test_shader_url_is_pinned():
    assert anime4k.shader_url(
        "Upscale+Denoise/Anime4K_Upscale_Denoise_CNN_x2_M.glsl"
    ) == (
        "https://raw.githubusercontent.com/bloc97/Anime4K/v4.0.1/glsl/"
        "Upscale+Denoise/Anime4K_Upscale_Denoise_CNN_x2_M.glsl"
    )


def _fake_fetch(seen: list[str]):
    def fetch(url: str, destination: Path) -> None:
        seen.append(url)
        Path(destination).parent.mkdir(parents=True, exist_ok=True)
        Path(destination).write_text("// shader", encoding="utf-8")

    return fetch


def test_ensure_shaders_downloads_only_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("ANIWORLD_ANIME4K_DIR", str(tmp_path))
    seen: list[str] = []

    assert anime4k.ensure_shaders(fetch=_fake_fetch(seen)) == anime4k.shader_dir()
    assert len(seen) == len(anime4k.required_shaders())

    # Second run sees a warm cache and downloads nothing.
    anime4k.ensure_shaders(fetch=_fake_fetch(seen))
    assert len(seen) == len(anime4k.required_shaders())


def test_ensure_shaders_surfaces_download_errors(tmp_path, monkeypatch):
    monkeypatch.setenv("ANIWORLD_ANIME4K_DIR", str(tmp_path))

    def offline(url: str, destination: Path) -> None:
        raise OSError("offline")

    with pytest.raises(anime4k.Anime4KError):
        anime4k.ensure_shaders(fetch=offline)


def test_mpv_args_append_each_shader(tmp_path):
    shaders = anime4k.chain("c")
    args = anime4k.mpv_args(shaders, tmp_path)
    assert len(args) == len(shaders)
    assert all(arg.startswith("--glsl-shaders-append=") for arg in args)
    assert args[0].endswith("Restore/Anime4K_Clamp_Highlights.glsl")


def test_write_input_conf_binds_every_mode(tmp_path, monkeypatch):
    monkeypatch.setenv("ANIWORLD_ANIME4K_DIR", str(tmp_path))
    text = anime4k.write_input_conf(tmp_path / "shaders").read_text(encoding="utf-8")
    for key in ("CTRL+1", "CTRL+2", "CTRL+3", "CTRL+4", "CTRL+5", "CTRL+6", "CTRL+0"):
        assert key in text
    assert (tmp_path / "shaders" / "Restore/Anime4K_Restore_CNN_M.glsl").as_posix() in text


def test_prepare_adds_input_conf_only_without_custom_controls(tmp_path, monkeypatch):
    monkeypatch.setenv("ANIWORLD_ANIME4K_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    seen: list[str] = []
    monkeypatch.setattr(anime4k, "_download", _fake_fetch(seen))

    args = anime4k.prepare("b")
    assert args[-1].startswith("--input-conf=")
    assert any(arg.startswith("--glsl-shaders-append=") for arg in args)

    mpv_dir = tmp_path / "xdg" / "mpv"
    mpv_dir.mkdir(parents=True)
    (mpv_dir / "input.conf").write_text("f cycle fullscreen\n", encoding="utf-8")
    assert not any(arg.startswith("--input-conf=") for arg in anime4k.prepare("b"))


@pytest.mark.skipif(
    sys.platform.startswith("win"), reason="POSIX permissions required"
)
def test_prepare_survives_a_read_only_shader_dir(tmp_path, monkeypatch):
    """A Nix store (or any read-only cache) still plays, just without the hotkeys."""
    cache = tmp_path / "cache"
    monkeypatch.setenv("ANIWORLD_ANIME4K_DIR", str(cache))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    anime4k.ensure_shaders(fetch=_fake_fetch([]))
    cache.chmod(0o555)
    try:
        args = anime4k.prepare("a")
    finally:
        cache.chmod(0o755)
    assert any(arg.startswith("--glsl-shaders-append=") for arg in args)
    assert not any(arg.startswith("--input-conf=") for arg in args)


def test_prepare_skips_when_mpv_conf_already_uses_anime4k(tmp_path, monkeypatch):
    monkeypatch.setenv("ANIWORLD_ANIME4K_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    mpv_dir = tmp_path / "xdg" / "mpv"
    mpv_dir.mkdir(parents=True)
    (mpv_dir / "mpv.conf").write_text(
        'glsl-shaders="~~/shaders/Anime4K_Restore_CNN_M.glsl"\n', encoding="utf-8"
    )
    warnings: list[str] = []
    assert anime4k.prepare("a", warn=warnings.append) == []
    assert warnings


def test_build_command_appends_extra_args_before_the_url():
    stream = Stream(url="https://cdn.example/master.m3u8", headers={"User-Agent": "UA"})
    cmd = player.build_command("mpv", stream, "Show – S01E01", ["--glsl-shaders-append=/a.glsl"])
    assert cmd[0] == "mpv"
    assert "--no-terminal" in cmd
    assert cmd[-1] == stream.url
    assert cmd.index("--glsl-shaders-append=/a.glsl") < cmd.index("--user-agent=UA")
    assert "--force-media-title=Show – S01E01" in cmd
