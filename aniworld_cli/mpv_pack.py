"""The bundled mpv environment: where it comes from, where it is materialised.

The point of a private config dir is portability: ``mpv.conf`` addresses
everything relative to itself (``~~/shaders/...``), so one bundle behaves the
same on Arch, Ubuntu, NixOS, macOS and Windows without a single OS-specific
path in the code.

Two locations matter:

* the **source** tree, shipped as package data next to this module (a wheel, a
  Nix store path or a PyInstaller bundle may all be read-only);
* the **materialised** copy under the per-user data dir, which mpv needs to be
  writable (it drops ``watch_later``, caches shaders, and the app writes
  ``user-overlay.conf`` there on first run).
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

#: Bump when the shipped pack changes, so existing installs refresh their copy.
PACK_VERSION = "6"

USER_OVERLAY = "user-overlay.conf"

#: Files written once and then owned by the user: later pack versions must not
#: overwrite them, or every update would silently undo local settings.
SEED_ONLY = ("script-opts/modernz.conf",)


class ConfigError(ValueError):
    """``--mpv-config`` names something that cannot be a config directory.

    Raised instead of letting mpv start with an empty ``--config-dir``: a typo
    such as ``--mpv-config bunlded`` would otherwise give a directory with no
    mpv.conf, no ModernZ and no aniworld.lua -- playback works, every control
    silently does not.
    """


#: Custom directories we have already explained, so one run says it once.
_explained: set[str] = set()


def _copy_tree(source_dir: Path, dest_dir: Path, pack_root: Path) -> None:
    """Merge one directory of the pack into ``dest_dir``.

    Directories are merged, files are replaced -- except the :data:`SEED_ONLY`
    ones, which are only written when absent.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    for item in source_dir.iterdir():
        target = dest_dir / item.name
        if item.is_dir():
            _copy_tree(item, target, pack_root)
            continue
        rel = item.relative_to(pack_root).as_posix()
        if rel in SEED_ONLY and target.exists():
            continue
        shutil.copy2(item, target)


def app_data_dir() -> Path:
    """Per-user data directory for this app, on every OS."""
    if sys.platform.startswith("win"):
        base = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Local")
    elif sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
    return Path(base) / "aniworld-cli"


def pack_source() -> Path:
    """The shipped, possibly read-only pack (``aniworld_cli/mpv``)."""
    return Path(__file__).resolve().parent / "mpv"


def materialize(target: Path | None = None) -> Path | None:
    """Copy the pack to a writable location and return it.

    Idempotent: re-copies only when :data:`PACK_VERSION` changed, and never
    touches ``user-overlay.conf``. Returns ``None`` when the pack is missing
    (e.g. a source checkout or a wheel built without package data), so callers
    can fall back to the user's own mpv configuration.
    """
    source = pack_source()
    if not source.is_dir():
        return None
    dest = target or (app_data_dir() / "mpv")
    stamp = dest / ".pack-version"
    try:
        if stamp.is_file() and stamp.read_text(encoding="utf-8").strip() == PACK_VERSION:
            return dest
    except OSError:
        pass

    dest.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        if item.name.startswith("."):
            continue
        if item.is_dir():
            _copy_tree(item, dest / item.name, source)
        else:
            shutil.copy2(item, dest / item.name)

    overlay = dest / USER_OVERLAY
    if not overlay.exists():
        overlay.write_text(
            "# Your own mpv options. This file survives updates.\n", encoding="utf-8"
        )
    try:
        stamp.write_text(PACK_VERSION + "\n", encoding="utf-8")
    except OSError:
        pass
    return dest


def bundled_windows_portable_config(mpv_path: str) -> Path | None:
    """``portable_config`` next to a bundled mpv.exe, if the release ships one.

    mpv in portable mode reads it automatically, so pointing ``--config-dir``
    at it keeps the packaged Windows experience intact.
    """
    if not sys.platform.startswith("win"):
        return None
    candidate = Path(mpv_path).resolve().parent / "portable_config"
    return candidate if (candidate / "mpv.conf").is_file() else None


def shader_dir(config_dir: Path | None) -> Path | None:
    """The directory whose shaders a preset should reference.

    Normally that is ``<config-dir>/shaders``. The exception is Windows portable
    mode: a user who dropped in their own ``portable_config`` owns that file, so
    honouring it must not cost them the Anime4K chain. The shaders are then taken
    from the shipped pack instead -- mpv happily loads shaders by absolute path
    from anywhere, they do not have to live inside ``--config-dir``.
    """
    if config_dir is not None:
        own = config_dir / "shaders"
        if own.is_dir():
            return own
    bundle = pack_source() / "shaders"
    return bundle if bundle.is_dir() else None


def resolve(mode: str, mpv_path: str) -> Path | None:
    """Map ``--mpv-config`` to a config directory.

    ``user`` means "do not interfere": no ``--config-dir`` at all, mpv keeps
    whatever the user configured globally. A path has to be an existing
    directory; see :class:`ConfigError`.
    """
    if mode == "user":
        return None
    if mode == "bundled":
        portable = bundled_windows_portable_config(mpv_path)
        return portable if portable is not None else materialize()
    path = Path(mode).expanduser()
    if path.exists() and not path.is_dir():
        raise ConfigError("--mpv-config %s: not a directory" % mode)
    if not path.is_dir():
        raise ConfigError(
            "--mpv-config %s: no such directory (use 'bundled' for the shipped "
            "config or 'user' for your own mpv setup)" % mode
        )
    return path.resolve()


def warn_custom_dir(config_dir: Path | None) -> None:
    """Say once per run what a custom ``--mpv-config`` directory does not give.

    Neither note is fatal, they exist because both fallbacks are otherwise
    invisible: presets keep working from the shipped pack while the user's own
    directory has no shaders, and a directory with nothing in it (a typo for
    ``bundled``) looks like broken settings instead of a wrong path.
    """
    if config_dir is None:
        return
    key = str(config_dir)
    if key in _explained:
        return
    _explained.add(key)

    if not (config_dir / "shaders").is_dir():
        bundle = pack_source() / "shaders"
        if bundle.is_dir():
            print(
                "aniworld-cli: %s has no shaders/ directory; Anime4K presets use "
                "the bundled shaders in %s" % (config_dir, bundle),
                file=sys.stderr,
            )
    if not any(
        (config_dir / name).exists() for name in ("mpv.conf", "input.conf", "scripts")
    ):
        print(
            "aniworld-cli: %s has no mpv.conf, input.conf or scripts/ -- did you "
            "mean --mpv-config bundled?" % config_dir,
            file=sys.stderr,
        )
