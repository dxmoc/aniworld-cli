"""M10 tests: fzf menu wrapper and the post-playback loop (no fzf, no network)."""

from __future__ import annotations

import argparse

import pytest

from aniworld_cli import cli
from aniworld_cli.models import Episode, Series


def test_select_maps_duplicate_labels_by_index(monkeypatch):
    seen = {}

    def fake_fzf(lines, **kwargs):
        seen["lines"] = lines
        seen["kwargs"] = kwargs
        return lines[1]

    monkeypatch.setattr(cli, "iterfzf", fake_fzf)
    assert cli._select("Select anime:", [("Same", "a"), ("Same", "b")]) == "b"
    assert seen["lines"] == ["0\tSame", "1\tSame"]
    assert seen["kwargs"]["prompt"] == "Select anime: "
    assert "--reverse" in seen["kwargs"]["__extra__"]


def test_select_flattens_whitespace_fzf_cannot_take(monkeypatch):
    monkeypatch.setattr(cli, "iterfzf", lambda lines, **_kw: lines[0])
    assert cli._select("x", [("a\tb\nc", 1), ("d", 2)]) == 1


def test_select_single_choice_skips_fzf(monkeypatch):
    monkeypatch.setattr(cli, "iterfzf", lambda *_a, **_kw: pytest.fail("fzf was opened"))
    assert cli._select("x", [("only", 42)]) == 42
    assert cli._select("x", []) is None


@pytest.mark.parametrize("result", [None, KeyboardInterrupt])
def test_select_abort_returns_none(monkeypatch, result):
    def fake_fzf(*_a, **_kw):
        if result is KeyboardInterrupt:
            raise KeyboardInterrupt
        return result

    monkeypatch.setattr(cli, "iterfzf", fake_fzf)
    assert cli._select("x", [("a", 1), ("b", 2)]) is None


def _episodes(n: int) -> list[Episode]:
    return [Episode("s", f"/e{i}", 1, i) for i in range(1, n + 1)]


def test_post_playback_menu_hides_next_and_previous_at_season_ends(monkeypatch):
    offered = []
    monkeypatch.setattr(cli, "_select", lambda _m, choices: offered.append([v for _, v in choices]))
    series, ep = Series("T", "t", "/t"), _episodes(1)[0]
    cli.post_playback_menu(series, ep, has_next=False, has_previous=False)
    cli.post_playback_menu(series, ep)
    assert offered[0] == ["replay", "other", "quit"]
    assert offered[1] == ["next", "replay", "previous", "other", "quit"]


def test_playback_loop_follows_menu_actions(monkeypatch):
    played = []
    actions = iter(["next", "previous", "replay", "quit"])
    monkeypatch.setattr(
        cli, "resolve_and_play", lambda ep, *_a: (played.append(ep.number), (0, None))[1]
    )
    monkeypatch.setattr(cli, "post_playback_menu", lambda *_a, **_kw: next(actions))
    monkeypatch.setattr("aniworld_cli.state.record", lambda *_a: None)
    args = argparse.Namespace(debug=False, auto=False, no_menu=False)
    nav = (1, _episodes(3), 0)
    assert cli._playback_loop(Series("T", "t", "/t"), nav, args) == 0
    assert played == [1, 2, 1, 1]


def test_failed_playback_is_not_recorded(monkeypatch):
    recorded = []
    monkeypatch.setattr(cli, "resolve_and_play", lambda *_a: (1, None))
    monkeypatch.setattr("aniworld_cli.state.record", lambda *a: recorded.append(a))
    args = argparse.Namespace(debug=False, auto=False, no_menu=True)
    assert cli._playback_loop(Series("T", "t", "/t"), (1, _episodes(1), 0), args) == 1
    assert recorded == []


def test_no_menu_errors_exit_nonzero(monkeypatch):
    monkeypatch.setattr(cli, "_search_and_pick", lambda _a: None)
    args = argparse.Namespace(debug=True, no_menu=True, watchlist=False, player=None)
    assert cli.run(args) == 1
    args.no_menu = False  # an interactive abort is not an error
    assert cli.run(args) == 0


def test_playing_lines_say_episode_not_season_code():
    assert cli._playing_label(Episode("s", "/e", 2, 3)) == "episode 3"
    assert cli._playing_label(Episode("s", "/f", 0, 1)) == "Film 1"
