"""M11 tests: update check (no network)."""

from __future__ import annotations

import pytest

from aniworld_cli import update


@pytest.fixture(autouse=True)
def _isolate_state(tmp_path, monkeypatch):
    monkeypatch.setenv("ANIWORLD_STATE_DIR", str(tmp_path))
    monkeypatch.setattr(update.sys, "prefix", "/usr")


def test_parse_version():
    assert update.parse_version("v0.2.4") == (0, 2, 4)
    assert update.parse_version("0.10.0") == (0, 10, 0)
    assert update.parse_version("0.0.0.dev0") is None
    assert update.parse_version("") is None


def test_notice_only_for_newer_release(monkeypatch):
    monkeypatch.setattr(update, "_fetch_latest", lambda: "v0.10.0")
    notice = update.update_notice("0.9.1")
    assert "0.10.0" in notice and "0.9.1" in notice and "pip install -U" in notice
    assert update.update_notice("0.10.0") is None
    assert update.update_notice("0.0.0.dev0") is None


def test_github_is_asked_once_a_day(monkeypatch):
    calls = []
    monkeypatch.setattr(update, "_fetch_latest", lambda: calls.append(1) or "v1.0.0")
    assert update.latest_version(now=1000.0) == "v1.0.0"
    assert update.latest_version(now=1000.0 + 3600) == "v1.0.0"
    assert len(calls) == 1
    update.latest_version(now=1000.0 + update.CHECK_EVERY + 1)
    assert len(calls) == 2


def test_network_errors_are_silent_and_cached(monkeypatch):
    def boom():
        raise update.requests.ConnectionError("offline")

    monkeypatch.setattr(update, "_fetch_latest", boom)
    assert update.update_notice("0.2.3") is None
    monkeypatch.setattr(update, "_fetch_latest", lambda: pytest.fail("asked again"))
    assert update.update_notice("0.2.3") is None  # failure cached for the day


def test_upgrade_command_matches_install(monkeypatch):
    monkeypatch.setattr(update, "_fetch_latest", lambda: "v9.0.0")
    monkeypatch.setattr(update.sys, "prefix", "/home/u/.local/share/pipx/venvs/aniworld-cli")
    assert "pipx upgrade aniworld-cli" in update.update_notice("0.2.3")
    monkeypatch.setattr(update.sys, "prefix", "/nix/store/abc-python3")
    assert update.update_notice("0.2.3") is None
