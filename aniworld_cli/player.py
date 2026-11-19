"""mpv detection and launch via subprocess (no shell, cross-platform)."""

from __future__ import annotations

import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from . import i18n
from .models import Stream


class PlayerNotFound(Exception):
    """Raised when no usable mpv binary can be located."""


def find_mpv(explicit: str | None = None) -> str | None:
    """Return a path to mpv, or None. ``explicit`` (from --player) wins."""
    if explicit:
        # Accept an absolute/relative path or a name resolvable on PATH.
        return shutil.which(explicit) or (explicit if _looks_executable(explicit) else None)
    return _bundled_mpv() or shutil.which("mpv")


def _bundled_mpv() -> str | None:
    """mpv shipped in the Windows release zip, in a folder next to aniworld-cli.exe."""
    if not getattr(sys, "frozen", False):
        return None
    exe = Path(sys.executable).parent / "mpv" / "mpv.exe"
    return str(exe) if exe.is_file() else None


def _looks_executable(path: str) -> bool:
    import os

    return os.path.isfile(path) and os.access(path, os.X_OK)


def install_hint() -> str:
    """OS-appropriate install hint for mpv."""
    if sys.platform.startswith("win"):
        return i18n.t("mpv_hint_windows")
    return i18n.t("mpv_hint_linux")


#: ``shlex`` in POSIX mode would eat the backslashes of a Windows path, so the
#: splitter differs per platform. Kept as a constant rather than read inline so a
#: test can exercise both branches on any OS.
_POSIX = not sys.platform.startswith("win")


def _unquote(token: str) -> str:
    """Strip one layer of quotes from one token.

    ``posix=False`` keeps the quotes, and not only around whole tokens: for
    ``--script-opts="a=b,c=d"`` the quote is *inside* the token, so checking the
    first and last character alone misses it and mpv receives ``"a`` as the
    option value.
    """
    if len(token) >= 2 and token[0] == token[-1] and token[0] in "\"'":
        return token[1:-1]
    name, sep, value = token.partition("=")
    if sep and len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return f"{name}={value[1:-1]}"
    return token


def split_args(value: str | None) -> list[str]:
    """Split ``--mpv-args`` into argv tokens, on every OS.

    ``posix=True`` would eat backslashes in Windows paths, ``posix=False`` keeps
    the quotes around quoted tokens; so: split per platform, then unquote --
    including the ``name="value"`` form, where the quotes do not start the token.
    """
    if not value:
        return []
    return [_unquote(token) for token in shlex.split(value, posix=_POSIX)]


def build_command(
    mpv_path: str,
    stream: Stream,
    title: str | None = None,
    extra: Sequence[str] | None = None,
    config_dir: str | Path | None = None,
    ipc_path: str | None = None,
) -> list[str]:
    """Build the mpv argv from the resolved stream and its required headers.

    User-Agent is passed via mpv's dedicated ``--user-agent`` flag rather than
    folded into ``--http-header-fields``: ffmpeg always emits a User-Agent of its
    own, so adding a second one through the header-fields list produces a
    duplicate header that some CDNs reject with HTTP 400. Remaining headers
    (e.g. Referer) go into ``--http-header-fields``.

    ``title`` (e.g. "Naruto – S03E12") is passed via ``--force-media-title`` so
    mpv shows the episode name instead of the opaque, tokenised CDN URL.

    ``--no-terminal`` keeps mpv's log (track list, harmless ffmpeg TLS noise on
    quit) out of the terminal, as with ani-cli; mpv is controlled in its window.

    Everything below ``--no-terminal`` is optional and additive: with no extra
    arguments the command is byte-for-byte what it always was.
    """
    cmd = [mpv_path, "--no-terminal"]
    headers = dict(stream.headers)
    user_agent = next(
        (headers.pop(k) for k in list(headers) if k.lower() == "user-agent"), None
    )
    if user_agent:
        cmd.append(f"--user-agent={user_agent}")
    if headers:
        fields = ",".join(f"{k}: {v}" for k, v in headers.items())
        cmd.append(f"--http-header-fields={fields}")
    if title:
        cmd.append(f"--force-media-title={title}")
    if config_dir:
        cmd.append(f"--config-dir={config_dir}")
    if ipc_path:
        cmd.append(f"--input-ipc-server={ipc_path}")
    cmd.extend(extra or ())
    cmd.append(stream.url)
    return cmd


def play(
    stream: Stream,
    mpv_path: str | None = None,
    title: str | None = None,
    extra: Sequence[str] | None = None,
    config_dir: str | Path | None = None,
) -> int:
    """Launch mpv for ``stream`` and wait. Returns mpv's exit code.

    Raises PlayerNotFound if mpv is unavailable. This is the no-IPC path; when
    in-player controls are enabled, :mod:`aniworld_cli.playback` drives mpv
    through its JSON IPC socket instead.
    """
    resolved = find_mpv(mpv_path)
    if not resolved:
        raise PlayerNotFound(install_hint())
    cmd = build_command(
        resolved, stream, title, extra=extra, config_dir=config_dir
    )
    proc = subprocess.run(cmd)  # noqa: S603 - argv list, no shell
    return proc.returncode


def spawn(cmd: Sequence[str], env: dict[str, str] | None = None) -> subprocess.Popen:
    """Start mpv without waiting, for the IPC path."""
    return subprocess.Popen(list(cmd), env=env)  # noqa: S603 - argv list, no shell
