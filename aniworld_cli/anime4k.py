"""Anime4K upscaling, without touching the user's mpv configuration.

Anime4K ships as a set of GLSL shaders. The usual installation copies them next
to a hand-written ``mpv.conf``/``input.conf``; instead this module

* downloads the shaders once into aniworld-cli's own directory,
* appends the chosen chain to mpv's shader list via ``--glsl-shaders-append``,
  so an existing custom mpv setup keeps working, and
* when mpv has no ``input.conf`` yet (no custom controls), points it at a
  generated one with Ctrl+1..Ctrl+6 for the six modes and Ctrl+0 to clear them,
  so the shaders can be switched while an episode plays.

Everything here is best-effort: a failed download raises :class:`Anime4KError`
and the caller plays the episode without upscaling.
"""

from __future__ import annotations

import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from . import i18n, state

# Pinned so a later upstream change cannot silently alter the shader chain.
ANIME4K_VERSION = "v4.0.1"
SHADER_URL = (
    "https://raw.githubusercontent.com/bloc97/Anime4K/{version}/glsl/{folder}/{name}.glsl"
)

# Roles in a chain -> (folder in the Anime4K repo, file name). ``{v}`` is the CNN
# variant: S < M < L < VL < UL in cost and quality.
_ROLES: dict[str, tuple[str, str]] = {
    "clamp": ("Restore", "Anime4K_Clamp_Highlights"),
    "restore": ("Restore", "Anime4K_Restore_CNN_{v}"),
    "restore_soft": ("Restore", "Anime4K_Restore_CNN_Soft_{v}"),
    "upscale": ("Upscale", "Anime4K_Upscale_CNN_x2_{v}"),
    "upscale_denoise": ("Upscale+Denoise", "Anime4K_Upscale_Denoise_CNN_x2_{v}"),
    "adp2": ("Upscale", "Anime4K_AutoDownscalePre_x2"),
    "adp4": ("Upscale", "Anime4K_AutoDownscalePre_x4"),
}

# The six official v4 modes, with the "fast" CNN variants of the low-end GPU
# template. A None variant marks a shader that has no CNN size.
MODES: dict[str, tuple[tuple[str, str | None], ...]] = {
    # 1080p anime
    "a": (
        ("clamp", None),
        ("restore", "M"),
        ("upscale", "M"),
        ("adp2", None),
        ("adp4", None),
        ("upscale", "S"),
    ),
    # 720p anime
    "b": (
        ("clamp", None),
        ("restore_soft", "M"),
        ("upscale", "M"),
        ("adp2", None),
        ("adp4", None),
        ("upscale", "S"),
    ),
    # 480p anime
    "c": (
        ("clamp", None),
        ("upscale_denoise", "M"),
        ("adp2", None),
        ("adp4", None),
        ("upscale", "S"),
    ),
    # Secondary modes, for a sharper (and more artifact-prone) image.
    "a+a": (
        ("clamp", None),
        ("restore", "M"),
        ("upscale", "M"),
        ("restore", "S"),
        ("adp2", None),
        ("adp4", None),
        ("upscale", "S"),
    ),
    "b+b": (
        ("clamp", None),
        ("restore_soft", "M"),
        ("upscale", "M"),
        ("adp2", None),
        ("adp4", None),
        ("restore_soft", "S"),
        ("upscale", "S"),
    ),
    "c+a": (
        ("clamp", None),
        ("upscale_denoise", "M"),
        ("adp2", None),
        ("adp4", None),
        ("restore", "S"),
        ("upscale", "S"),
    ),
}

MODE_NAMES = tuple(MODES)
DEFAULT_MODE = "a"

# Higher-end GPU variant of the same chain: every CNN step moves up two sizes.
_HQ_VARIANT = {"S": "M", "M": "VL", "L": "UL"}

_OFF_VALUES = {"", "off", "none", "no", "0", "false"}

# Ctrl+1..Ctrl+0 bind the modes in this order, see write_input_conf().
_HOTKEYS = ("CTRL+1", "CTRL+2", "CTRL+3", "CTRL+4", "CTRL+5", "CTRL+6")


class Anime4KError(Exception):
    """Raised for an unknown mode or a failed shader download."""


def parse_mode(value: str | None) -> str | None:
    """Turn a ``--anime4k`` value into a mode name, or None for "off"."""
    if value is None:
        return None
    text = value.strip().lower()
    if text in _OFF_VALUES:
        return None
    if text not in MODES:
        raise Anime4KError(i18n.t("anime4k_bad_mode", value, ", ".join(MODE_NAMES)))
    return text


def cache_dir() -> Path:
    """Where shaders and the generated input.conf live.

    ``ANIWORLD_ANIME4K_DIR`` overrides it (useful for NixOS, which prefers not to
    write into the home directory).
    """
    override = os.environ.get("ANIWORLD_ANIME4K_DIR")
    if override:
        return Path(override)
    return state.config_dir() / "anime4k"


def shader_dir() -> Path:
    return cache_dir() / "shaders"


def chain(mode: str, hq: bool = False) -> list[str]:
    """Relative paths of the shaders for ``mode``, in processing order."""
    if mode not in MODES:
        raise Anime4KError(i18n.t("anime4k_bad_mode", mode, ", ".join(MODE_NAMES)))
    paths = []
    for role, variant in MODES[mode]:
        folder, name = _ROLES[role]
        if variant is not None:
            if hq:
                variant = _HQ_VARIANT.get(variant, variant)
            name = name.format(v=variant)
        paths.append(f"{folder}/{name}.glsl")
    return paths


def required_shaders() -> list[str]:
    """Every shader any mode needs, for both quality tiers, deduplicated."""
    seen: dict[str, None] = {}
    for mode in MODES:
        for hq in (False, True):
            for path in chain(mode, hq):
                seen.setdefault(path, None)
    return list(seen)


def shader_url(relative: str) -> str:
    folder, name = relative.rsplit("/", 1)
    return SHADER_URL.format(
        version=ANIME4K_VERSION, folder=folder, name=name[: -len(".glsl")]
    )


def ensure_shaders(fetch=None, report=None) -> Path:
    """Download missing shaders into :func:`shader_dir` and return that path.

    ``fetch`` (url, destination) is injectable so tests stay offline.
    """
    target = shader_dir()
    missing = [rel for rel in required_shaders() if not (target / rel).is_file()]
    if not missing:
        return target
    target.mkdir(parents=True, exist_ok=True)
    if report is not None:
        report(i18n.t("anime4k_downloading"))
    download = fetch or _download
    try:
        for relative in missing:
            destination = target / relative
            if not destination.parent.is_dir():
                destination.parent.mkdir(parents=True, exist_ok=True)
            download(shader_url(relative), destination)
    except (OSError, urllib.error.URLError, Anime4KError) as exc:
        raise Anime4KError(i18n.t("anime4k_download_failed", exc)) from exc
    return target


def _download(url: str, destination: Path) -> None:
    """Fetch one shader, then move it into place so a partial file never sticks."""
    request = urllib.request.Request(url, headers={"User-Agent": "aniworld-cli"})
    tmp = destination.with_suffix(destination.suffix + ".part")
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - https URL
        data = response.read()
    if not data:
        raise Anime4KError(f"empty response for {url}")
    tmp.write_bytes(data)
    tmp.replace(destination)


def mpv_args(shaders: list[str], base: Path | None = None) -> list[str]:
    """``--glsl-shaders-append`` per shader; appending keeps the user's own chain."""
    base = base or shader_dir()
    # Forward slashes: mpv accepts them everywhere, and input.conf treats
    # backslashes as escapes.
    return [
        f"--glsl-shaders-append={(base / relative).as_posix()}" for relative in shaders
    ]


def user_mpv_config_dir() -> Path:
    """mpv's per-user config directory, as mpv itself resolves it."""
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return Path(base) / "mpv"
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
        os.path.expanduser("~"), ".config"
    )
    return Path(base) / "mpv"


def has_custom_controls() -> bool:
    """True when the user has an mpv input.conf, i.e. their own key bindings."""
    return (user_mpv_config_dir() / "input.conf").is_file()


def user_has_anime4k() -> bool:
    """True when the user's mpv.conf already loads Anime4K shaders."""
    try:
        return "anime4k" in (user_mpv_config_dir() / "mpv.conf").read_text(
            encoding="utf-8", errors="replace"
        ).lower()
    except OSError:
        return False


def write_input_conf(shaders_dir: Path | None = None, hq: bool = False) -> Path:
    """Write the Anime4K key bindings and return the file path.

    Only meant for mpv installations without an ``input.conf``: the file is
    passed as ``--input-conf``, which keeps mpv's built-in keys (space, arrows,
    q, ...) but replaces a custom binding file.
    """
    base = shaders_dir or shader_dir()
    lines = [
        "# Generated by aniworld-cli for Anime4K. Edits are overwritten.",
        "# Ctrl+1..Ctrl+6 enable a mode, Ctrl+0 removes the shaders again.",
    ]
    titles = {
        "a": "A (1080p)",
        "b": "B (720p)",
        "c": "C (480p)",
        "a+a": "A+A (sharper 1080p)",
        "b+b": "B+B (sharper 720p)",
        "c+a": "C+A (sharper 480p)",
    }
    # mpv separates list values with ':' on Unix and ';' on Windows (where ':'
    # belongs to drive letters).
    separator = ";" if sys.platform.startswith("win") else ":"
    for hotkey, mode in zip(_HOTKEYS, MODE_NAMES):
        paths = separator.join((base / rel).as_posix() for rel in chain(mode, hq))
        lines.append(
            f'{hotkey} no-osd change-list glsl-shaders set "{paths}"; '
            f'show-text "Anime4K: Mode {titles[mode]}"'
        )
    lines.append('CTRL+0 no-osd change-list glsl-shaders clr ""; show-text "Anime4K: off"')
    target = cache_dir() / "input.conf"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def prepare(mode: str, hq: bool = False, report=None, warn=None) -> list[str]:
    """Resolve a mode into mpv arguments, downloading shaders on first use.

    Returns an empty list when the user already configures Anime4K themselves,
    so nothing is applied twice.
    """
    if mode not in MODES:
        raise Anime4KError(i18n.t("anime4k_bad_mode", mode, ", ".join(MODE_NAMES)))
    if user_has_anime4k():
        if warn is not None:
            warn(i18n.t("anime4k_already_configured"))
        return []
    shaders = chain(mode, hq)
    base = ensure_shaders(report=report)
    args = mpv_args(shaders, base)
    # Without an input.conf there are no custom controls to preserve, so hand
    # mpv the generated one and mode switching works right away.
    if not has_custom_controls():
        try:
            args.append(f"--input-conf={write_input_conf(base, hq).as_posix()}")
        except OSError:
            # Read-only cache (e.g. a Nix store path): play without the hotkeys.
            pass
    return args
