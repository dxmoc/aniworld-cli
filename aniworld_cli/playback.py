"""In-player controls: keep mpv alive and re-resolve streams on demand.

The CLI owns the network, mpv owns the picture, and mpv's JSON IPC socket joins
them. A Lua script inside mpv (``scripts/aniworld.lua``) turns a keypress into a
``script-message``; that surfaces here as a ``client-message`` event, this module
re-resolves and asks mpv to ``loadfile`` the new stream at the current
timestamp.

Why reload instead of a track switch: aniworld's ger-dub / ger-sub / eng-sub are
separate encodes with burned-in subtitles, and the master playlist carries no
``EXT-X-MEDIA`` audio or subtitle renditions. There is nothing to switch.
"""

from __future__ import annotations

import json
import os
from queue import Empty, Queue
from typing import Any

from . import http, i18n, mpv_pack, mpvctl, player, resolve, shaders
from .models import Episode, Hoster, Series, Stream


def _label_lang(token: str) -> str:
    label = i18n.t(f"lang_{token}")
    return token if label == f"lang_{token}" else label


class Session:
    """One episode, played in an mpv instance we can talk to."""

    def __init__(
        self,
        series: Series | None,
        episode: Episode,
        hosters: list[Hoster],
        stream: Stream,
        hoster: Hoster | None,
        language: str | None,
        args: Any,
        mpv_path: str,
    ) -> None:
        self.series = series
        self.episode = episode
        self.hosters = hosters
        self.stream = stream
        self.hoster = hoster
        self.language = language
        self.args = args
        self.mpv_path = mpv_path

        self.config_dir = mpv_pack.resolve(getattr(args, "mpv_config", "bundled"), mpv_path)
        mpv_pack.warn_custom_dir(self.config_dir)
        # ``--mpv-config user`` means mpv's own config stays exactly as it is,
        # and that includes its shader chain: passing --glsl-shaders there would
        # replace whatever the user configured, so presets are inactive then.
        self.shader_dir = (
            mpv_pack.shader_dir(self.config_dir) if self.config_dir else None
        )
        # The stream the hoster resolved -- normally a master playlist. A quality
        # pick replaces ``self.stream`` with one of its variants, so the master
        # has to be remembered: otherwise the variant list would be re-read from
        # a media playlist (no rows left in the menu) and a language switch could
        # not go back to "auto".
        self.master: Stream | None = stream
        self.variants: list[tuple[int, str]] = []
        self.preset = self._initial_preset()
        # A height token ("720") or "auto". Kept across a language switch: the
        # same height is re-applied when the new encode lists it.
        self.quality = "auto"
        self.busy = False
        self.mpv: mpvctl.Mpv | None = None
        self._queue: Queue[list[str]] = Queue()

    # -- setup ----------------------------------------------------------
    def _initial_preset(self) -> str:
        if not self.shader_dir:
            return "off"
        wanted = getattr(self.args, "anime4k", None) or "auto"
        if wanted != "auto":
            return wanted if wanted in shaders.PRESETS else shaders.DEFAULT
        return shaders.auto_preset(self._source_height())

    def _source_height(self) -> int | None:
        """Highest variant of the resolved stream, if the playlist lists any."""
        self.variants = self._fetch_variants(self.master)
        return max((h for h, _ in self.variants), default=None)

    def _fetch_variants(self, stream: Stream | None) -> list[tuple[int, str]]:
        if stream is None:
            return []
        try:
            return resolve.list_variants(stream, http.get_session())
        except Exception:  # noqa: BLE001 - best effort, never block playback
            return []

    def _state(self) -> dict[str, Any]:
        langs = [
            {"token": tok, "label": _label_lang(tok), "action": "language"}
            for tok in resolve.available_languages(self.hosters)
        ]
        qualities = [{"token": "auto", "label": "Auto (best)", "action": "quality"}]
        for height, _url in sorted(self.variants, reverse=True):
            qualities.append(
                {"token": str(height), "label": "%dp" % height, "action": "quality"}
            )
        return {
            "episode": "%s - %s" % (
                self.series.title if self.series else "",
                self.episode.label,
            ),
            "hoster": self.hoster.name if self.hoster else "",
            "lang": self.language or "",
            "quality": self.quality,
            "shader": self.preset,
            "busy": self.busy,
            "langs": langs,
            "qualities": qualities if len(qualities) > 1 else qualities[:1],
            # No preset can apply without a shader directory (``--mpv-config
            # user``), so do not offer a menu that would silently do nothing.
            "shaders": [
                {"token": token, "label": label, "action": "shader"}
                for token, label in (shaders.LABELS if self.shader_dir else ())
            ],
        }

    # -- mpv ------------------------------------------------------------
    def _command(self) -> list[str]:
        extra = player.split_args(getattr(self.args, "mpv_args", None))
        if self.preset != "off" and self.shader_dir:
            extra = extra + [
                "--glsl-shaders=" + shaders.glsl_value(self.preset, self.shader_dir)
            ]
        return player.build_command(
            self.mpv_path,
            self.stream,
            title=self._title(),
            extra=extra,
            config_dir=str(self.config_dir) if self.config_dir else None,
            ipc_path=self.ipc_path,
        )

    def _title(self) -> str:
        if self.series:
            return "%s - %s" % (self.series.title, self.episode.label)
        return self.episode.label

    def _env(self) -> dict[str, str]:
        env = dict(os.environ)
        env["ANIWORLD_MPV_STATE"] = json.dumps(self._state())
        if self.config_dir:
            env["ANIWORLD_MPV_PACK"] = str(self.config_dir)
        return env

    def _push_state(self) -> None:
        if self.mpv is None:
            return
        self.mpv.script_message("aniworld", "state", json.dumps(self._state()))

    # -- actions --------------------------------------------------------
    def _switch(self, kind: str, token: str) -> None:
        """Re-resolve a language, hoster or quality and reload at the same time."""
        assert self.mpv is not None
        try:
            position = self.mpv.get("time-pos")
        except mpvctl.MpvError:
            position = None

        self.busy = True
        self._push_state()

        if kind == "shader":
            self.preset = token
            self._apply_shaders()
            self.busy = False
            self._push_state()
            self.mpv.script_message(
                "aniworld", "osd", i18n.t("shader_changed", dict(shaders.LABELS)[token])
            )
            return

        # Whatever height was picked stays wanted across a language or hoster
        # switch; only a quality pick itself changes it.
        wanted = token if kind == "quality" else self.quality
        target: Stream | None = self.master
        if kind == "language":
            target, hoster = resolve.resolve_stream(
                self.hosters, language=token, report=lambda _m: None
            )
            if target and hoster:
                self.hoster = hoster
                self.language = token
        elif kind == "hoster":
            candidates = [h for h in self.hosters if h.name.lower() == token.lower()]
            target, hoster = resolve.resolve_stream(candidates, report=lambda _m: None)
            if target and hoster:
                self.hoster = hoster
        elif kind == "quality" and token == "auto":
            # Re-resolve so "auto" starts from a fresh master URL, not from the
            # variant that happens to be playing.
            target, hoster = resolve.resolve_stream(
                [h for h in self.hosters if self.hoster and h.name == self.hoster.name],
                language=self.language,
                report=lambda _m: None,
            )

        if target is None:
            self.busy = False
            self._push_state()
            self.mpv.script_message("aniworld", "osd", i18n.t("switch_failed"))
            return

        self.master = target
        self.stream, applied = self._quality_stream(target, wanted)
        self.quality = applied
        self._apply_stream_headers(self.stream)
        self.mpv.loadfile(self.stream.url, start=position)
        self.busy = False
        self._push_state()
        if applied != wanted:
            self.mpv.script_message(
                "aniworld", "osd", i18n.t("switched_no_quality", kind, token, wanted + "p")
            )
        else:
            self.mpv.script_message("aniworld", "osd", i18n.t("switched", kind, token))

    def _quality_stream(self, base: Stream, wanted: str) -> tuple[Stream, str]:
        """The stream to load for ``wanted``, and the token actually applied.

        ``auto`` keeps the master playlist and lets mpv choose the best variant.
        It is also the fallback when the new encode does not list the height the
        previous one had: ger-dub, ger-sub and eng-sub are separate encodes with
        different ladders (1080p exists only on some eng-sub ones), so carrying
        the number over blindly would either fail or silently drop quality.
        """
        self.variants = self._fetch_variants(base)
        if wanted != "auto":
            url = next((u for h, u in self.variants if h == int(wanted)), None)
            if url is not None:
                return Stream(url=url, headers=dict(base.headers)), wanted
        return base, "auto"

    def _apply_stream_headers(self, stream: Stream) -> None:
        """Point mpv's HTTP options at a new stream.

        mpv is already running, so the headers cannot come from argv any more.
        User-Agent is set through its own property, exactly as on the command
        line: ffmpeg always emits one, and folding it into the header list would
        send a duplicate that some CDNs reject with HTTP 400.
        """
        if self.mpv is None:
            return
        headers = dict(stream.headers)
        user_agent = next(
            (headers.pop(k) for k in list(headers) if k.lower() == "user-agent"), None
        )
        if user_agent:
            self.mpv.set("user-agent", user_agent)
        self.mpv.set(
            "http-header-fields",
            ",".join("%s: %s" % (k, v) for k, v in headers.items()),
        )

    def _apply_shaders(self) -> None:
        if self.mpv is None:
            return
        if not self.shader_dir:
            return
        value = shaders.glsl_value(self.preset, self.shader_dir)
        self.mpv.set("glsl-shaders", value)

    # -- run ------------------------------------------------------------
    def run(self) -> int:
        """Start mpv and service in-player requests until it exits."""
        self.ipc_path = mpvctl.default_socket_path()
        self.mpv = mpvctl.Mpv(self.ipc_path)
        self.mpv.on_client_message = self._queue.put
        cmd = self._command()
        proc = player.spawn(cmd, env=self._env())
        try:
            self.mpv.connect()
            self._push_state()
        except mpvctl.MpvError:
            # No IPC: let the episode play, but without in-player controls.
            proc.wait()
            return proc.returncode

        while proc.poll() is None:
            try:
                args = self._queue.get(timeout=0.2)
            except Empty:
                continue
            self._handle(args)
        self.mpv.close()
        return proc.returncode or 0

    def _handle(self, args: list[str]) -> None:
        """A ``script-message aniworld-cmd <action> <value>`` from the Lua script.

        mpv delivers the message name as the first argument, so the payload
        starts at index 1.
        """
        if len(args) < 3:
            return
        _name, action, value = args[0], args[1], args[2]
        if action in ("language", "hoster", "quality", "shader"):
            self._switch(action, value)


def launch(
    series: Series | None,
    episode: Episode,
    hosters: list[Hoster],
    stream: Stream,
    hoster: Hoster | None,
    language: str | None,
    args: Any,
    mpv_path: str,
) -> int:
    """Run one episode with in-player controls. Returns mpv's exit code."""
    session = Session(
        series=series,
        episode=episode,
        hosters=hosters,
        stream=stream,
        hoster=hoster,
        language=language,
        args=args,
        mpv_path=mpv_path,
    )
    return session.run()
