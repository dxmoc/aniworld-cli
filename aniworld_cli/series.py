"""Series -> seasons/episodes.

Verified against the live site. The series/season pages carry a navigation block
``<div id="stream" class="hosterSiteDirectNav">`` with:

* a season ``<ul>`` of links ``/anime/stream/<slug>/staffel-<n>`` plus an optional
  ``/anime/stream/<slug>/filme`` entry (films), and
* an episode ``<ul>`` listing only the *currently active* season's episodes.

Below it, ``<table class="seasonEpisodesList">`` repeats those episode links in
``<td class="seasonEpisodeTitle">`` cells: ``<strong>`` holds the German title
(empty when there is none), ``<span>`` the original one.

So to enumerate a season we fetch that season's own page and read its episode
list. Films use ``/filme/film-<n>``; we model the films section as season 0.
"""

from __future__ import annotations

import html
import re

from bs4 import BeautifulSoup

from . import config, http
from .models import Episode, Series

FILMS_SEASON = 0


def _soup(markup: str) -> BeautifulSoup:
    return BeautifulSoup(markup, "html.parser")


def _nav(soup: BeautifulSoup):
    return soup.select_one("div#stream")


def season_path(slug: str, season: int) -> str:
    if season == FILMS_SEASON:
        return f"/anime/stream/{slug}/filme"
    return f"/anime/stream/{slug}/staffel-{season}"


def parse_seasons(markup: str, slug: str) -> list[int]:
    """Season numbers from the nav block; 0 == films. Sorted, deduped."""
    soup = _soup(markup)
    nav = _nav(soup)
    found: set[int] = set()
    scope = nav.find_all("a", href=True) if nav else []
    staffel = re.compile(rf"^/anime/stream/{re.escape(slug)}/staffel-(\d+)/?$")
    filme = re.compile(rf"^/anime/stream/{re.escape(slug)}/filme/?$")
    for a in scope:
        href = a["href"]
        m = staffel.match(href)
        if m:
            found.add(int(m.group(1)))
        elif filme.match(href):
            found.add(FILMS_SEASON)
    return sorted(found)


def _title(link) -> str:
    """The site's main (German) episode title, else the original one."""
    for node in link.find_all(["strong", "span"]):
        text = html.unescape(" ".join(node.get_text().split()))
        if text:
            # Site text ends up on the terminal: keep escape sequences out.
            return "".join(ch for ch in text if ch.isprintable())
    return ""


def parse_episodes(markup: str, slug: str, season: int) -> list[Episode]:
    """Episodes for ``season`` from that season page's nav block. Deduped."""
    soup = _soup(markup)
    nav = _nav(soup)
    titles = {a["href"]: _title(a) for a in soup.select("td.seasonEpisodeTitle a[href]")}
    if season == FILMS_SEASON:
        pat = re.compile(rf"^/anime/stream/{re.escape(slug)}/filme/film-(\d+)/?$")
    else:
        pat = re.compile(
            rf"^/anime/stream/{re.escape(slug)}/staffel-{season}/episode-(\d+)/?$"
        )
    seen: set[int] = set()
    episodes: list[Episode] = []
    scope = nav.find_all("a", href=True) if nav else []
    for a in scope:
        m = pat.match(a["href"])
        if not m:
            continue
        number = int(m.group(1))
        if number in seen:
            continue
        seen.add(number)
        episodes.append(
            Episode(
                series_slug=slug,
                url=config.BASE_URL + a["href"],
                season=season,
                number=number,
                title=titles.get(a["href"], ""),
            )
        )
    episodes.sort(key=lambda e: e.number)
    return episodes


# shortcut: pages are kept for the whole run, so an episode released while the
# program is open only shows up after a restart; add an expiry if that matters.
_pages: dict[str, str] = {}


def _page(url: str) -> str:
    """Fetch a series/season page once per run; the menus revisit the same pages."""
    if url not in _pages:
        resp = http.get(url)
        if not resp.ok:
            return resp.text
        _pages[url] = resp.text
    return _pages[url]


def list_seasons(series: Series) -> list[int]:
    """Season numbers from the series page (0 == films)."""
    return parse_seasons(_page(series.url), series.slug)


def list_episodes(series: Series, season: int) -> list[Episode]:
    """Return a season's episodes, fetching its page unless already known."""
    # The series page doubles as its first season's page: no second request then.
    root = _pages.get(series.url)
    episodes = parse_episodes(root, series.slug, season) if root else []
    if not episodes:
        url = config.BASE_URL + season_path(series.slug, season)
        episodes = parse_episodes(_page(url), series.slug, season)
    return episodes
