"""Tell the user when a newer release is out on GitHub.

Asks the GitHub API at most once a day and caches the answer next to the watch
state, so every other start costs nothing. Any failure (offline, rate limit,
odd response) is silent: an update hint is never worth breaking a start for.
"""

from __future__ import annotations

import json
import sys
import time

import requests

from . import __version__, i18n
from .state import _state_dir

LATEST_URL = "https://api.github.com/repos/dxmoc/aniworld-cli/releases/latest"
CHECK_EVERY = 24 * 60 * 60  # seconds
TIMEOUT = 2.0


def parse_version(text: str) -> tuple[int, ...] | None:
    """``"v0.2.4"`` -> ``(0, 2, 4)``; None for anything that is not plain digits."""
    parts = text.strip().lstrip("v").split(".")
    if not all(p.isdigit() for p in parts):
        return None
    return tuple(int(p) for p in parts)


def _fetch_latest() -> str | None:
    resp = requests.get(
        LATEST_URL, timeout=TIMEOUT, headers={"Accept": "application/vnd.github+json"}
    )
    if resp.status_code != 200:
        return None
    tag = resp.json().get("tag_name")
    return tag if isinstance(tag, str) else None


def latest_version(now: float | None = None) -> str | None:
    """Newest release tag, from the daily cache or from GitHub."""
    now = time.time() if now is None else now
    cache = _state_dir() / "update-check.json"
    try:
        cached = json.loads(cache.read_text(encoding="utf-8"))
        if now - float(cached["checked"]) < CHECK_EVERY:
            return cached.get("latest")
    except (OSError, ValueError, KeyError, TypeError):
        pass
    try:
        latest = _fetch_latest()
    except (requests.RequestException, ValueError):
        latest = None
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps({"checked": now, "latest": latest}), encoding="utf-8")
    except OSError:
        pass
    return latest


def _upgrade_command() -> str:
    if "pipx" in sys.prefix.replace("\\", "/"):
        return "pipx upgrade aniworld-cli"
    return "pip install -U git+https://github.com/dxmoc/aniworld-cli"


def update_notice(current: str = __version__) -> str | None:
    """Hint to show at startup, or None when up to date or not applicable."""
    mine = parse_version(current)
    # Dev checkouts have no real version; Nix installs update through Nix.
    if mine is None or sys.prefix.startswith("/nix/store"):
        return None
    latest = latest_version()
    theirs = parse_version(latest) if latest else None
    if theirs is None or theirs <= mine:
        return None
    return i18n.t("update_available", latest.lstrip("v"), current, _upgrade_command())
