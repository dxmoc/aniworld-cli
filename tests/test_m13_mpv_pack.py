"""M13 tests: the bundled mpv pack (materialisation, overlay, modes)."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest

from aniworld_cli import mpv_pack, shaders


def test_every_button_target_actually_exists():
    """Every script-binding the shipped configs use must exist in the script.

    A missing binding is silent: the button fires, mpv answers "can't find
    script", and nothing happens. A Lua error is worse -- mpv terminates the
    script, after which every button stops working until the player restarts.
    """
    pack_root = mpv_pack.pack_source()
    lua = (pack_root / "scripts" / "aniworld.lua").read_text(encoding="utf-8")
    bound = set(re.findall(r'mp\.add_key_binding\(\s*nil\s*,\s*"([\w-]+)"', lua))
    assert "toggle-shaders" in bound and "menu-shaders" in bound

    used = set()
    for name in ("script-opts/modernz.conf", "input.conf"):
        text = (pack_root / name).read_text(encoding="utf-8")
        used |= set(re.findall(r"script-binding\s+aniworld/([\w-]+)", text))
    assert used, "no aniworld bindings referenced at all?"
    missing = used - bound
    assert not missing, f"config references bindings the script does not define: {missing}"


def test_materialize_copies_the_pack_and_creates_the_overlay(tmp_path: Path):
    dest = mpv_pack.materialize(tmp_path / "mpv")
    assert dest is not None
    assert (dest / "mpv.conf").is_file()
    assert (dest / "input.conf").is_file()
    assert (dest / "scripts" / "aniworld.lua").is_file()
    assert (dest / "shaders").is_dir()
    assert (dest / mpv_pack.USER_OVERLAY).is_file()


def test_materialize_is_idempotent_and_keeps_user_edits(tmp_path: Path):
    dest = mpv_pack.materialize(tmp_path / "mpv")
    assert dest is not None
    overlay = dest / mpv_pack.USER_OVERLAY
    overlay.write_text("volume=40\n", encoding="utf-8")
    again = mpv_pack.materialize(tmp_path / "mpv")
    assert again == dest
    assert overlay.read_text(encoding="utf-8") == "volume=40\n"


def test_materialize_refreshes_when_the_pack_version_changes(tmp_path: Path, monkeypatch):
    dest = mpv_pack.materialize(tmp_path / "mpv")
    assert dest is not None
    (dest / "mpv.conf").write_text("stale\n", encoding="utf-8")
    monkeypatch.setattr(mpv_pack, "PACK_VERSION", "999")
    mpv_pack.materialize(tmp_path / "mpv")
    assert "stale" not in (dest / "mpv.conf").read_text(encoding="utf-8")


def test_button_labels_are_real_icons():
    """A button label is drawn in the icon font, where a typo is invisible.

    Lowercase letters in ``modernz-icons.ttf`` are blank, zero-width placeholders
    that exist only to be *typed*: the font swaps a whole ligature name such as
    ``fluent_shortcuts`` for one glyph. Anything else renders as nothing at all,
    so the labels have to be checked against the font rather than eyeballed.
    """
    pytest.importorskip("fontTools.ttLib")
    from fontTools.ttLib import TTFont

    font = TTFont(mpv_pack.pack_source() / "fonts" / "modernz-icons.ttf")
    cmap = font.getBestCmap()
    cp_of = {name: cp for cp, name in cmap.items()}
    ligatures = {
        "".join(chr(cp_of[g]) for g in [first] + list(ligature.Component))
        for lookup in font["GSUB"].table.LookupList.Lookup
        for subtable in lookup.SubTable
        for first, ligature_set in (subtable.ligatures or {}).items()
        for ligature in ligature_set
    }
    # The pack's own icons have to survive a font refresh.
    assert {"fluent_anime4k", "fluent_anime4k_off", "fluent_shortcuts"} <= ligatures

    conf = (mpv_pack.pack_source() / "script-opts" / "modernz.conf").read_text(encoding="utf-8")
    labels = re.findall(r"^custom_button\d+_label(?:_off)?\s*=\s*(\S+)\s*$", conf, flags=re.M)
    assert labels, "no custom button labels found -- did the option names change?"
    for label in labels:
        assert label in ligatures or label.upper() == label, (
            f"button label {label!r} is neither a ligature in modernz-icons.ttf nor "
            f"uppercase text: the icon font renders lowercase letters as blank, so "
            f"this button would show an empty box"
        )


def test_modernz_conf_edit_is_never_clobbered(tmp_path: Path, monkeypatch):
    """Users edit modernz.conf; a pack update must not undo that."""
    dest = mpv_pack.materialize(tmp_path / "mpv")
    assert dest is not None
    conf = dest / "script-opts" / "modernz.conf"
    assert conf.is_file()
    text = conf.read_text(encoding="utf-8")
    assert "custom_button1=yes" in text        # sparkle: Anime4K menu
    assert "custom_button2=yes" in text        # keyboard: key bindings
    assert "custom_button3=yes" in text        # subtitles: language menu
    # Switching audio tracks cannot work here (one track, languages are separate
    # encodes), so the track button is off and Lang does the job instead.
    assert "audio_tracks_button=no" in text
    # ModernZ's own download button cannot work against these streams (no
    # Referer/UA on the yt-dlp call, "master.mp4" for every file, killed when
    # playback stops); it must stay disabled by default.
    assert "download_button=no" in text

    conf.write_text("custom_button1=no\n", encoding="utf-8")
    monkeypatch.setattr(mpv_pack, "PACK_VERSION", "999")
    mpv_pack.materialize(tmp_path / "mpv")
    assert conf.read_text(encoding="utf-8") == "custom_button1=no\n"
    # ...while ordinary pack files are still refreshed.
    assert "custom_button" not in (dest / "mpv.conf").read_text(encoding="utf-8")


def test_untouched_modernz_conf_gets_new_defaults(tmp_path: Path, monkeypatch):
    """A user who never edited the file must still receive pack updates.

    Seeding a file once used to freeze it at its first version, so a new default
    -- a new button, a renamed option -- could never reach an existing install.
    The shipped content is hashed instead, and only an edit blocks the refresh.
    """
    pack = tmp_path / "pack"
    shutil.copytree(mpv_pack.pack_source(), pack)
    monkeypatch.setattr(mpv_pack, "pack_source", lambda: pack)
    dest = mpv_pack.materialize(tmp_path / "mpv")
    conf = dest / "script-opts" / "modernz.conf"

    def ship(text: str) -> None:
        (pack / "script-opts" / "modernz.conf").write_text(text, encoding="utf-8")
        monkeypatch.setattr(mpv_pack, "PACK_VERSION", mpv_pack.PACK_VERSION + text)

    ship("custom_button1=yes  # v2\n")
    mpv_pack.materialize(tmp_path / "mpv")
    assert conf.read_text(encoding="utf-8") == "custom_button1=yes  # v2\n"

    # Now the user edits it: from here on the file is theirs alone.
    conf.write_text("custom_button1=no\n", encoding="utf-8")
    ship("custom_button1=yes  # v3\n")
    mpv_pack.materialize(tmp_path / "mpv")
    assert conf.read_text(encoding="utf-8") == "custom_button1=no\n"


def test_materialize_returns_none_without_a_source(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(mpv_pack, "pack_source", lambda: tmp_path / "missing")
    assert mpv_pack.materialize(tmp_path / "mpv") is None


def test_user_mode_disables_the_bundled_config():
    assert mpv_pack.resolve("user", "mpv") is None


def test_path_mode_is_used_verbatim(tmp_path: Path):
    assert mpv_pack.resolve(str(tmp_path), "mpv") == tmp_path.resolve()


def test_bundled_mode_points_at_a_usable_dir(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(mpv_pack, "app_data_dir", lambda: tmp_path)
    resolved = mpv_pack.resolve("bundled", "mpv")
    assert resolved is not None
    assert (resolved / "mpv.conf").is_file()


@pytest.mark.skipif(
    not __import__("sys").platform.startswith("win"),
    reason="portable_config is a Windows-only mpv feature",
)
def test_windows_portable_config_wins(tmp_path: Path):  # pragma: no cover
    (tmp_path / "mpv").mkdir()
    (tmp_path / "mpv" / "portable_config").mkdir()
    (tmp_path / "mpv" / "portable_config" / "mpv.conf").write_text("", encoding="utf-8")
    assert mpv_pack.resolve("bundled", str(tmp_path / "mpv" / "mpv.exe")) == (
        tmp_path / "mpv" / "portable_config"
    )


def test_portable_config_wins_on_any_platform_when_forced(tmp_path: Path, monkeypatch):
    """Same check as above, but runnable off Windows -- it was silently dead there."""
    monkeypatch.setattr(mpv_pack.sys, "platform", "win32")
    (tmp_path / "mpv" / "portable_config").mkdir(parents=True)
    (tmp_path / "mpv" / "portable_config" / "mpv.conf").write_text("", encoding="utf-8")
    assert mpv_pack.resolve("bundled", str(tmp_path / "mpv" / "mpv.exe")) == (
        tmp_path / "mpv" / "portable_config"
    )


def test_play_stream_finds_the_portable_config_next_to_mpv(tmp_path: Path, monkeypatch):
    """Regression: the raw ``--player`` name cannot locate ``portable_config``.

    ``Path("mpv").parent`` is the current directory, so the packed Windows
    config next to ``mpv.exe`` was never found and mpv ran with the app's own
    directory instead. It looks harmless until the harness relies on that file
    (its ``end=`` made mpv exit) and mpv stays open forever.
    """
    from aniworld_cli import cli, player
    from aniworld_cli.models import Stream

    mpv_dir = tmp_path / "mpv"
    (mpv_dir / "portable_config").mkdir(parents=True)
    (mpv_dir / "portable_config" / "mpv.conf").write_text("", encoding="utf-8")

    monkeypatch.setattr(mpv_pack.sys, "platform", "win32")
    monkeypatch.setattr(mpv_pack, "_explained", set())
    seen: dict = {}
    monkeypatch.setattr(player, "play", lambda *a, **k: seen.update(k) or 0)

    args = type("A", (), {"mpv_args": None, "mpv_config": "bundled"})()
    rc = cli.play_stream(
        Stream(url="https://cdn/x.m3u8", headers={}),
        "mpv",
        "t",
        args,
        str(mpv_dir / "mpv.exe"),
    )

    assert rc == 0
    assert seen["config_dir"] == mpv_dir / "portable_config"


def test_shader_dir_prefers_the_config_dir(tmp_path: Path):
    (tmp_path / "shaders").mkdir()
    assert mpv_pack.shader_dir(tmp_path) == tmp_path / "shaders"


def test_shader_dir_falls_back_to_the_pack(tmp_path: Path):
    """Windows portable_config has no shaders; the bundled chain must still load."""
    (tmp_path / "mpv.conf").write_text("", encoding="utf-8")
    resolved = mpv_pack.shader_dir(tmp_path)
    assert resolved is not None
    assert (resolved / "Anime4K_Clamp_Highlights.glsl").is_file()


def test_shader_dir_is_none_without_a_pack(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(mpv_pack, "pack_source", lambda: tmp_path / "missing")
    assert mpv_pack.shader_dir(tmp_path) is None


# -- --mpv-config validation -------------------------------------------


def test_missing_config_dir_is_an_error_not_a_silent_empty_dir(tmp_path: Path):
    """A typo must not start mpv with an empty --config-dir (no ModernZ, no Lua)."""
    with pytest.raises(mpv_pack.ConfigError, match="no such directory"):
        mpv_pack.resolve(str(tmp_path / "bunlded"), "mpv")


def test_a_file_instead_of_a_directory_is_an_error(tmp_path: Path):
    (tmp_path / "mpv.conf").write_text("", encoding="utf-8")
    with pytest.raises(mpv_pack.ConfigError, match="not a directory"):
        mpv_pack.resolve(str(tmp_path / "mpv.conf"), "mpv")


def test_custom_dir_without_shaders_warns_once_and_uses_the_bundle(
    tmp_path: Path, capsys, monkeypatch
):
    monkeypatch.setattr(mpv_pack, "_explained", set())
    (tmp_path / "mpv.conf").write_text("", encoding="utf-8")

    mpv_pack.warn_custom_dir(tmp_path)
    mpv_pack.warn_custom_dir(tmp_path)          # same run: said already

    err = capsys.readouterr().err
    assert err.count("has no shaders/") == 1
    assert "no mpv.conf" not in err             # it has one: only the shader note
    assert (mpv_pack.shader_dir(tmp_path) or Path()) == mpv_pack.pack_source() / "shaders"


def test_empty_custom_dir_asks_whether_bundled_was_meant(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.setattr(mpv_pack, "_explained", set())
    mpv_pack.warn_custom_dir(tmp_path)
    assert "did you mean --mpv-config bundled?" in capsys.readouterr().err


def test_complete_custom_dir_is_not_warned_about(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.setattr(mpv_pack, "_explained", set())
    (tmp_path / "mpv.conf").write_text("", encoding="utf-8")
    (tmp_path / "shaders").mkdir()
    mpv_pack.warn_custom_dir(tmp_path)
    assert capsys.readouterr().err == ""


def test_user_mode_has_nothing_to_warn_about(capsys, monkeypatch):
    monkeypatch.setattr(mpv_pack, "_explained", set())
    mpv_pack.warn_custom_dir(None)
    assert capsys.readouterr().err == ""


def test_cli_refuses_to_start_mpv_with_a_bogus_config_dir(
    tmp_path: Path, monkeypatch, capsys
):
    """Exit 2 with a readable message, before any player is spawned."""
    from aniworld_cli import cli, player
    from aniworld_cli.models import Stream

    monkeypatch.setattr(player, "play", lambda *a, **kw: pytest.fail("mpv was started"))
    monkeypatch.setattr(mpv_pack, "_explained", set())
    args = type("A", (), {"mpv_args": None, "mpv_config": str(tmp_path / "nope")})()
    rc = cli.play_stream(Stream(url="https://cdn/x.m3u8", headers={}), "mpv", "t", args)
    assert rc == 2
    assert "no such directory" in capsys.readouterr().err


def test_every_preset_has_a_menu_hint():
    """The shader menu explains each mode; a missing hint is a silent gap."""
    assert set(shaders.HINTS) == set(shaders.PRESETS)
    for token, label in shaders.LABELS:
        hint = shaders.HINTS[token]
        assert hint, token
        # Drawn at fs19 inside an 860 px panel: keep it on one line.
        assert len(hint) <= 56, (token, len(hint))
