"""M15: a bot-protection page must not read as "nothing found".

Measured on 2026-11-19: from one VPN exit the site answers `POST /ajax/search`
with HTTP 403 and a bare nginx body from DDoS-Guard, from the next exit with the
expected JSON. That body is not JSON, so `search()` returned an empty list and
the CLI printed *No results found for 'frieren'!* -- a wrong diagnosis that sends
people hunting for a typo instead of switching the exit node.

Offline: every response here is a stub, no network.
"""

from __future__ import annotations

import pytest

from aniworld_cli import __main__ as entry
from aniworld_cli import config, http, search

DDOS_GUARD_PAGE = (
    "<html><head><title>403 Forbidden</title></head>"
    "<body><center><h1>403 Forbidden</h1></center><hr><center>nginx</center></body>"
    "</html>"
)
CLOUDFLARE_PAGE = "<html><body>Just a moment...</body></html>"


class FakeResponse:
    """The three attributes the block check reads, plus ``json()``."""

    def __init__(
        self,
        status: int = 200,
        body: str = "",
        ctype: str = "text/html",
        server: str = "nginx",
    ) -> None:
        self.status_code = status
        self.text = body
        self.headers = {"Content-Type": ctype, "Server": server}

    def json(self):
        import json

        return json.loads(self.text)


class StubSession:
    """Stands in for ``http._session`` so no request leaves the process."""

    def __init__(self, response: FakeResponse) -> None:
        self.response = response

    def get(self, url: str, **kwargs: object) -> FakeResponse:
        return self.response

    def post(self, url: str, **kwargs: object) -> FakeResponse:
        return self.response


@pytest.fixture(autouse=True)
def _no_throttle(monkeypatch):
    monkeypatch.setattr(http, "_throttle", lambda: None)


def _serve(monkeypatch, response: FakeResponse) -> None:
    monkeypatch.setattr(http, "_session", StubSession(response))


def _site_url(path: str = "/ajax/search") -> str:
    return config.BASE_URL + path


# --- naming the protection -------------------------------------------------


def test_ddos_guard_403_is_named():
    resp = FakeResponse(403, DDOS_GUARD_PAGE, server="ddos-guard")
    assert http.blocked_by(resp) == "DDoS-Guard"


def test_cloudflare_challenge_is_named():
    resp = FakeResponse(503, CLOUDFLARE_PAGE, server="cloudflare")
    assert http.blocked_by(resp) == "Cloudflare"


def test_generic_html_403_reports_the_server():
    assert http.blocked_by(FakeResponse(403, "<html>no</html>")) == "nginx"


def test_html_403_without_a_server_header_is_still_a_block():
    assert http.blocked_by(FakeResponse(403, "<html>no</html>", server="")) == (
        "an unidentified filter"
    )


def test_json_403_is_left_to_the_caller():
    # An API-level refusal is not a block; the caller decides what to do with it.
    resp = FakeResponse(403, '{"error": "nope"}', ctype="application/json")
    assert http.blocked_by(resp) is None


def test_404_is_missing_content_not_a_block():
    resp = FakeResponse(404, DDOS_GUARD_PAGE, server="ddos-guard")
    assert http.blocked_by(resp) is None


# --- where it is raised ---------------------------------------------------


def test_site_page_raises_blocked(monkeypatch):
    _serve(monkeypatch, FakeResponse(403, DDOS_GUARD_PAGE, server="ddos-guard"))
    with pytest.raises(http.Blocked) as excinfo:
        http.post(_site_url())
    assert excinfo.value.status == 403
    assert excinfo.value.protection == "DDoS-Guard"
    assert not excinfo.value.is_cloudflare


def test_hoster_cdn_keeps_its_own_403(monkeypatch):
    # resolve.py probes a segment on purpose and falls through to the next
    # hoster on 403, so a media response must stay a response.
    _serve(monkeypatch, FakeResponse(403, "", server="ddos-guard"))
    assert http.get("https://cdn.example/stream/master.m3u8").status_code == 403


def test_search_raises_instead_of_returning_nothing(monkeypatch):
    _serve(monkeypatch, FakeResponse(403, DDOS_GUARD_PAGE, server="ddos-guard"))
    with pytest.raises(http.Blocked):
        search.search("frieren")


def test_soft_block_with_http_200_is_not_an_empty_result(monkeypatch):
    # A challenge or maintenance page can arrive with 200 and an HTML body.
    _serve(monkeypatch, FakeResponse(200, CLOUDFLARE_PAGE, server="cloudflare"))
    with pytest.raises(http.Blocked) as excinfo:
        search.search("frieren")
    assert excinfo.value.protection == "an HTML page"


def test_empty_query_still_returns_nothing_without_a_request(monkeypatch):
    _serve(monkeypatch, FakeResponse(403, DDOS_GUARD_PAGE, server="ddos-guard"))
    assert search.search("   ") == []


# --- what the user sees ---------------------------------------------------


def test_cli_explains_the_block_instead_of_no_results(monkeypatch, capsys):
    def blocked(args):
        raise http.Blocked(_site_url(), 403, "DDoS-Guard")

    monkeypatch.setattr("aniworld_cli.cli.run", blocked)
    code = entry.main(["--no-menu", "frieren"])
    err = capsys.readouterr().err

    assert code == 1
    assert "No results found" not in err
    assert "HTTP 403" in err
    assert "DDoS-Guard" in err
    assert "VPN" in err


def test_cli_adds_the_flaresolverr_hint_for_cloudflare(monkeypatch, capsys):
    def blocked(args):
        raise http.Blocked(_site_url(), 503, "Cloudflare")

    monkeypatch.setattr("aniworld_cli.cli.run", blocked)
    assert entry.main(["--no-menu", "frieren"]) == 1
    err = capsys.readouterr().err
    assert "flaresolverr" in err
