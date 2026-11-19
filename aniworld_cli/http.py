"""Shared HTTP session: realistic UA, timeouts, retry/backoff, polite delay."""

from __future__ import annotations

import time
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter

try:  # urllib3 is a requests dependency; import path differs across versions
    from urllib3.util.retry import Retry
except ImportError:  # pragma: no cover
    from requests.packages.urllib3.util.retry import Retry  # type: ignore

from . import config

# The site answers a blocked IP with an anti-bot page, not with content:
# Cloudflare sends a JS challenge, DDoS-Guard a bare nginx 403. Both are 403 or
# 503, and both carry the protection's name in a header or in the body.
_BLOCK_STATUSES = (403, 503)
_CLOUDFLARE_MARKERS = (
    "just a moment",
    "cf-chl",
    "challenge-platform",
    "cf-browser-verification",
)
_DDOS_GUARD_MARKERS = ("ddos-guard", "ddos guard")


class Blocked(Exception):
    """The site answered with a bot-protection page instead of what was asked for.

    An IP-level block parses exactly like an empty page, so ``search`` used to
    convert it into an empty result list and the CLI printed "No results found
    for 'frieren'!" -- a wrong diagnosis that sends people hunting for a typo
    instead of switching the VPN exit. ``protection`` names what answered.
    """

    def __init__(self, url: str, status: int, protection: str) -> None:
        self.url = url
        self.status = status
        self.protection = protection
        super().__init__(f"{protection} blocked {url} (HTTP {status})")

    @property
    def is_cloudflare(self) -> bool:
        return self.protection == "Cloudflare"


_session: requests.Session | None = None
_last_request_at = 0.0


def get_session() -> requests.Session:
    """Return the process-wide session, creating it on first use."""
    global _session
    if _session is None:
        s = requests.Session()
        s.headers.update(
            {
                "User-Agent": config.USER_AGENT,
                "Accept-Language": "de-DE,de;q=0.9,en;q=0.6",
            }
        )
        retry = Retry(
            total=config.MAX_RETRIES,
            backoff_factor=config.BACKOFF_FACTOR,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET", "POST"]),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        s.mount("https://", adapter)
        s.mount("http://", adapter)
        _session = s
    return _session


def _throttle() -> None:
    """Keep a small minimum gap between requests."""
    global _last_request_at
    elapsed = time.monotonic() - _last_request_at
    wait = config.REQUEST_DELAY - elapsed
    if wait > 0:
        time.sleep(wait)
    _last_request_at = time.monotonic()


def blocked_by(resp: requests.Response) -> str | None:
    """Name the bot protection behind ``resp``, or ``None`` when it is content."""
    if resp.status_code not in _BLOCK_STATUSES:
        return None
    server = resp.headers.get("Server", "").lower()
    body = resp.text[:4000].lower()
    if "cloudflare" in server and any(marker in body for marker in _CLOUDFLARE_MARKERS):
        return "Cloudflare"
    if "ddos-guard" in server or any(marker in body for marker in _DDOS_GUARD_MARKERS):
        return "DDoS-Guard"
    if resp.status_code == 403 and "html" in resp.headers.get("Content-Type", "").lower():
        return server or "an unidentified filter"
    return None


def _check_block(resp: requests.Response, url: str) -> None:
    """Raise :class:`Blocked` for the site's own pages.

    Only the site is checked: hoster CDNs answer 403 to media on purpose (the
    player probes a segment to test liveness and falls through to the next
    hoster), so treating those as a block would break hoster fallback.
    """
    if urlparse(url).netloc != urlparse(config.BASE_URL).netloc:
        return
    protection = blocked_by(resp)
    if protection is not None:
        raise Blocked(url, resp.status_code, protection)


def get(url: str, **kwargs: object) -> requests.Response:
    """GET with throttle, shared session, and block detection."""
    _throttle()
    kwargs.setdefault("timeout", config.TIMEOUT)
    resp = get_session().get(url, **kwargs)  # type: ignore[arg-type]
    _check_block(resp, url)
    return resp


def post(url: str, **kwargs: object) -> requests.Response:
    """POST with throttle, shared session, and block detection."""
    _throttle()
    kwargs.setdefault("timeout", config.TIMEOUT)
    resp = get_session().post(url, **kwargs)  # type: ignore[arg-type]
    _check_block(resp, url)
    return resp
