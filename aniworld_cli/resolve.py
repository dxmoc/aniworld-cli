"""Pick and resolve a playable stream from a list of hosters.

Ordering follows the configured language priority first, then hoster priority,
so we exhaust the best available language's hosters before falling through to the
next language. Extraction failures fall through to the next candidate.

A resolved URL is additionally *liveness-checked* before it is accepted: some
hosters (VOE in particular) hand out a master playlist that loads fine while its
media segments answer 403 from a rotating CDN node. Without the check we would
commit to that dead stream and never fall back, leaving the player stuck on a
wall of 403s. So we fetch one real segment; if it fails, we try the next hoster.
"""

from __future__ import annotations

import re
import time
from typing import Callable, Optional
from urllib.parse import urljoin

import requests

from . import config, http, i18n
from .extractors import dispatch
from .models import Hoster, Stream

# Status codes that mean "the CDN served us bytes" (206 = partial/Range reply).
_OK_STATUS = (200, 206)


def available_languages(hosters: list[Hoster]) -> list[str]:
    """Distinct languages offered for an episode, ordered by config priority.

    Languages not in the configured priority are kept and appended at the end,
    so the user can still pick them from the menu.
    """
    pri = config.language_priority()
    uniq: list[str] = []
    for h in hosters:
        if h.lang not in uniq:
            uniq.append(h.lang)
    return sorted(uniq, key=lambda lang: pri.index(lang) if lang in pri else len(pri))


def order_hosters(hosters: list[Hoster], language: str | None = None) -> list[Hoster]:
    """Order hosters for resolution.

    If ``language`` is given, restrict to that exact language and order by hoster
    priority. Otherwise order by (language priority, hoster priority) and drop
    languages not in the configured priority.
    """
    host_pri = [h.lower() for h in config.hoster_priority()]

    def host_rank(h: Hoster) -> int:
        name = h.name.lower()
        return host_pri.index(name) if name in host_pri else len(host_pri)

    if language is not None:
        candidates = [h for h in hosters if h.lang == language]
        return sorted(candidates, key=host_rank)

    lang_pri = config.language_priority()

    def lang_rank(h: Hoster) -> int:
        return lang_pri.index(h.lang) if h.lang in lang_pri else len(lang_pri)

    candidates = [h for h in hosters if h.lang in lang_pri]
    return sorted(candidates, key=lambda h: (lang_rank(h), host_rank(h)))


def list_variants(
    stream: Stream, session: requests.Session, retries: int = 2
) -> list[tuple[int, str]]:
    """Quality variants of an HLS master playlist as ``(height, url)``.

    aniworld's hosts serve 720p plus a 480p fallback for most shows, 1080p only
    for some english-subtitle encodes. A progressive URL has no variants.

    Used for the in-player quality menu and to pick an Anime4K preset that suits
    the source: the playlist is the only place the real resolution is stated
    before playback starts.

    The hosts rate-limit back-to-back requests for one token, so a fresh master
    can answer 403 to a request made a few hundred milliseconds after the
    liveness check fetched the very same URL. One short retry covers it.
    """
    if ".m3u8" not in stream.url.lower():
        return []

    master = None
    for attempt in range(retries + 1):
        try:
            master = session.get(stream.url, headers=stream.headers, timeout=config.TIMEOUT)
        except requests.RequestException:
            master = None
        if master is not None and master.status_code in _OK_STATUS:
            break
        if attempt < retries:
            time.sleep(0.4)
    if master is None or master.status_code not in _OK_STATUS:
        return []

    variants: list[tuple[int, str]] = []
    lines = master.text.splitlines()
    for index, line in enumerate(lines):
        if not line.strip().startswith("#EXT-X-STREAM-INF"):
            continue
        match = re.search(r"RESOLUTION=\d+x(\d+)", line)
        if not match:
            continue
        height = int(match.group(1))
        for entry in lines[index + 1 :]:
            entry = entry.strip()
            if not entry or entry.startswith("#"):
                continue
            variants.append((height, urljoin(stream.url, entry)))
            break
    return variants


def _first_entry(playlist_text: str, base_url: str) -> str | None:
    """First non-comment URL in an m3u8, resolved against ``base_url``."""
    for line in playlist_text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            return urljoin(base_url, line)
    return None


def stream_is_live(stream: Stream, session: requests.Session) -> bool:
    """Best-effort check that ``stream`` actually delivers bytes, not just a 200.

    For HLS we drill master -> variant playlist -> first segment and confirm the
    segment answers 200/206 (this is where VOE's 403 shows up). For a progressive
    URL we probe the URL itself. ``stream=True`` keeps us from downloading the
    body. Any network error is treated as "not live" so the caller falls through.
    """
    try:
        url = stream.url
        headers = stream.headers
        if ".m3u8" in url.lower():
            master = session.get(url, headers=headers, timeout=config.TIMEOUT)
            if master.status_code not in _OK_STATUS:
                return False
            target = _first_entry(master.text, url)
            if target is None:
                return True  # nothing to drill into; the master itself was OK
            if ".m3u8" in target.lower():
                variant = session.get(target, headers=headers, timeout=config.TIMEOUT)
                if variant.status_code not in _OK_STATUS:
                    return False
                segment = _first_entry(variant.text, target)
                if segment is None:
                    return True
                target = segment
        else:
            target = url
        resp = session.get(target, headers=headers, timeout=config.TIMEOUT, stream=True)
        ok = resp.status_code in _OK_STATUS
        resp.close()
        return ok
    except requests.RequestException:
        return False


def resolve_stream(
    hosters: list[Hoster],
    language: str | None = None,
    report: Optional[Callable[[str], None]] = None,
    verify: bool = True,
) -> tuple[Stream | None, Hoster | None]:
    """Try ordered hosters until one extractor yields a *playable* Stream.

    If ``language`` is given, only hosters of that language are tried. ``report``
    receives status lines (defaults to no-op). When ``verify`` is set
    (default), a resolved stream is liveness-checked and skipped if its segments
    do not load. Returns the resolved ``(Stream, Hoster)`` or ``(None, None)``.
    """
    say = report or (lambda _msg: None)
    session = http.get_session()
    for hoster in order_hosters(hosters, language):
        extract = dispatch(hoster.name)
        if extract is None:
            continue
        say(i18n.t("resolving_hoster", hoster.name))
        stream = extract(hoster.redirect_url, session)
        if stream is None:
            say(i18n.t("extract_failed", hoster.name))
            continue
        if verify and not stream_is_live(stream, session):
            say(i18n.t("stream_dead", hoster.name))
            continue
        say(i18n.t("resolved_stream", hoster.name))
        return stream, hoster
    return None, None
