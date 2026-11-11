"""M3 parser tests — offline against saved series/season/episode fixtures."""

from __future__ import annotations

from pathlib import Path

from aniworld_cli import config, series
from aniworld_cli.episode import parse_hosters, parse_language_map
from aniworld_cli.models import Series
from aniworld_cli.series import parse_episodes, parse_seasons

FIX = Path(__file__).parent / "fixtures"


def _read(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


def test_parse_seasons_includes_films_as_zero():
    seasons = parse_seasons(_read("series_naruto.html"), "naruto")
    assert seasons == [0, 1, 2, 3, 4]  # 0 == Filme, then staffel 1..4


def test_parse_episodes_staffel_one():
    eps = parse_episodes(_read("series_naruto.html"), "naruto", 1)
    assert eps, "expected episodes for season 1"
    assert eps[0].number == 1
    assert eps[0].season == 1
    assert eps[0].url.endswith("/anime/stream/naruto/staffel-1/episode-1")
    # strictly increasing, no dupes
    nums = [e.number for e in eps]
    assert nums == sorted(set(nums))
    assert eps[0].label == "S01E01 – Wer ist Naruto?"


def test_parse_episodes_films():
    eps = parse_episodes(_read("films_naruto.html"), "naruto", 0)
    assert eps, "expected film entries"
    assert all(e.season == 0 for e in eps)
    assert eps[0].url.endswith("/anime/stream/naruto/filme/film-1")
    assert eps[0].label.startswith("Film 1")
    # No German title: the original one is used; the site double-escapes entities.
    assert eps[0].title == "Hidden Leaf Village Grand Sports Festival! [OVA]"
    assert eps[1].title == "Geheimmission im Land des ewigen Schnees"
    assert eps[5].title == "Naruto's ultimate heroes [OVA]"


def test_parse_episodes_without_title_table_and_with_escape_codes():
    nav = '<div id="stream"><a href="/anime/stream/x/staffel-1/episode-1">1</a></div>'
    assert parse_episodes(nav, "x", 1)[0].title == ""
    cell = (
        '<table><tr><td class="seasonEpisodeTitle"><a href="/anime/stream/x/staffel-1/episode-1">'
        "<strong> </strong><span>A\x1b[2J\n  B</span></a></td></tr></table>"
    )
    assert parse_episodes(nav + cell, "x", 1)[0].title == "A[2J B"


def test_series_page_is_fetched_once_and_serves_its_first_season(monkeypatch):
    fetched = []

    class _Resp:
        ok = True
        text = _read("series_naruto.html")

    monkeypatch.setattr(series, "_pages", {})
    monkeypatch.setattr(series.http, "get", lambda url: fetched.append(url) or _Resp())
    naruto = Series("Naruto", "naruto", config.BASE_URL + "/anime/stream/naruto")

    assert series.list_seasons(naruto) == [0, 1, 2, 3, 4]
    assert len(series.list_episodes(naruto, 1)) == 52
    assert series.list_seasons(naruto) == [0, 1, 2, 3, 4]
    assert fetched == [naruto.url]
    # Any other season still needs its own page (the fake serves season 1 again).
    assert series.list_episodes(naruto, 2) == []
    assert fetched == [naruto.url, naruto.url + "/staffel-2"]


def test_failed_page_is_not_cached(monkeypatch):
    class _Resp:
        ok = False
        text = ""

    monkeypatch.setattr(series, "_pages", {})
    monkeypatch.setattr(series.http, "get", lambda _url: _Resp())
    assert series.list_seasons(Series("Naruto", "naruto", "https://x/naruto")) == []
    assert series._pages == {}


def test_language_map_derived_not_hardcoded():
    lang_map = parse_language_map(_read("episode_naruto_s1e1.html"))
    # We do not assume which integer means what; we assert the *derived* mapping
    # covers all three canonical tokens for this episode.
    assert set(lang_map.values()) >= {
        config.LANG_GER_DUB,
        config.LANG_GER_SUB,
        config.LANG_ENG_SUB,
    }


def test_parse_hosters():
    markup = _read("episode_naruto_s1e1.html")
    hosters = parse_hosters(markup)
    assert hosters, "expected hoster entries"
    names = {h.name for h in hosters}
    # VOE is present per the brief's priority list.
    assert "VOE" in names
    for h in hosters:
        assert h.redirect_url.startswith(config.BASE_URL + "/redirect/")
        assert h.lang in {
            config.LANG_GER_DUB,
            config.LANG_GER_SUB,
            config.LANG_ENG_SUB,
        } or h.lang.startswith("lang-")
