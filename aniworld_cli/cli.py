"""Interactive flow (fzf menus in the style of ani-cli).

Drives the whole pipeline: search -> series -> season/episode -> resolve a stream
by language+hoster priority -> mpv. After playback it offers the ani-cli style
next / replay / previous / select / quit loop. ``--no-menu`` and ``--episode``
allow a fully non-interactive run; ``--debug`` resolves and prints the final URL
without launching mpv.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from typing import cast

from iterfzf import BUNDLED_EXECUTABLE, iterfzf

from . import i18n, player
from .models import Episode, Series, Stream

# Wheels ship fzf inside iterfzf; source builds (e.g. Nix) rely on fzf from PATH.
_FZF = BUNDLED_EXECUTABLE if BUNDLED_EXECUTABLE and BUNDLED_EXECUTABLE.exists() else "fzf"

# A menu entry: the text shown in fzf and the value returned when it is picked.
Choice = tuple[str, object]

# A navigation position: the chosen season, its episode list, and the index
# of the current episode within that list.
Nav = tuple[int, list[Episode], int]


def _styled(text: str, style: str, stream) -> str:
    """ani-cli style line (clear line, colour); plain text when not on a terminal."""
    return f"\33[2K\r\033[{style}m{text}\033[0m" if stream.isatty() else text


def info(message: str) -> None:
    """Status line, same look as ani-cli's ``info``."""
    print(_styled(message, "1;34", sys.stdout), flush=True)


def error(message: str) -> None:
    """Error line, same look as ani-cli's ``die`` (without exiting)."""
    print(_styled(message, "1;31", sys.stderr), file=sys.stderr, flush=True)


def _select(message: str, choices: list[Choice]) -> object | None:
    """fzf menu like ani-cli; a lone choice is taken directly, Esc/Ctrl-C give None."""
    if not choices:
        return None
    if len(choices) == 1:
        return choices[0][1]
    # The hidden index column maps the picked line back to its value, even for
    # duplicate labels; fzf neither shows nor searches it.
    lines = [f"{i}\t{' '.join(label.split())}" for i, (label, _) in enumerate(choices)]
    try:
        picked = iterfzf(
            lines,
            prompt=f"{message} ",
            sort=True,
            cycle=True,
            executable=_FZF,
            __extra__=["--reverse", "--delimiter=\t", "--with-nth=2.."],
        )
    except KeyboardInterrupt:
        return None
    if picked is None:
        return None
    return choices[int(picked.split("\t", 1)[0])][1]


def check_player(player_path: str | None) -> str | None:
    """Locate mpv and, if missing, print an install hint."""
    mpv = player.find_mpv(player_path)
    if not mpv:
        error(i18n.t("mpv_missing"))
        error(player.install_hint())
    return mpv


def _season_label(season: int) -> str:
    return i18n.t("movies_label") if season == 0 else i18n.t("season_label", season)


def parse_episode_arg(value: str) -> tuple[int, int] | None:
    """Parse ``--episode S-E`` into ``(season, number)``. ``0-N`` == film N."""
    parts = value.split("-")
    if len(parts) != 2:
        return None
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None


def _episode_label(episode: Episode) -> str:
    """Menu text for an episode: just its number (plus title), like ani-cli."""
    return f"{episode.number} {episode.title}" if episode.title else str(episode.number)


def _playing_label(episode: Episode) -> str:
    """"episode 2" for the playing lines, as in ani-cli; movies keep "Film N"."""
    return i18n.t("episode_label", episode.number) if episode.season else episode.label


def _resolve_query(args: argparse.Namespace) -> str | None:
    query = args.query
    if not query and not args.no_menu:
        # Same prompt as ani-cli: bold cyan, asked again until something is typed.
        prompt = _styled(f"{i18n.t('search_prompt')} ", "1;36", sys.stdout)
        try:
            while not (query or "").strip():
                query = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print()
            return None
    return query.strip() if query else None


def _pick_series(results: list[Series], args: argparse.Namespace) -> Series | None:
    if args.no_menu:
        return results[0]
    return _select(  # type: ignore[return-value]
        i18n.t("choose_series"),
        [(f"{i} {s.display}", s) for i, s in enumerate(results, 1)],
    )


def choose_episode_nav(series: Series) -> Nav | None:
    """Interactive season -> episode selection, returning a Nav position."""
    from . import series as series_mod

    info(i18n.t("loading_series"))
    seasons = series_mod.list_seasons(series)
    if not seasons:
        error(i18n.t("no_episodes"))
        return None

    season = cast(
        "int | None",
        _select(i18n.t("choose_season"), [(_season_label(s), s) for s in seasons]),
    )
    if season is None:
        return None

    episodes = series_mod.list_episodes(series, season)
    if not episodes:
        error(i18n.t("no_episodes"))
        return None

    chosen = cast(
        "int | None",
        _select(
            i18n.t("choose_episode"),
            [(_episode_label(e), i) for i, e in enumerate(episodes)],
        ),
    )
    if chosen is None:
        return None
    return season, episodes, chosen


def _initial_nav(series: Series, args: argparse.Namespace) -> Nav | None:
    """Decide the first episode: from --episode, from --no-menu defaults, or menu."""
    from . import series as series_mod

    if args.episode:
        parsed = parse_episode_arg(args.episode)
        if not parsed:
            error(i18n.t("episode_arg_invalid", args.episode))
            return None
        season, number = parsed
        seasons = series_mod.list_seasons(series)
        if season not in seasons:
            error(i18n.t("season_not_found", season))
            return None
        episodes = series_mod.list_episodes(series, season)
        for idx, ep in enumerate(episodes):
            if ep.number == number:
                return season, episodes, idx
        error(i18n.t("episode_not_found", number))
        return None

    from . import state

    progress = state.get_progress(series.slug)
    if args.no_menu:
        # -w --no-menu continues the most recent series instead of restarting it.
        if args.watchlist and progress:
            resumed = _nav_after_progress(series, progress)
            if resumed is not None:
                return resumed
        seasons = series_mod.list_seasons(series)
        if not seasons:
            error(i18n.t("no_episodes"))
            return None
        # Prefer the first real season over the films section when available.
        season = next((s for s in seasons if s != 0), seasons[0])
        episodes = series_mod.list_episodes(series, season)
        if not episodes:
            error(i18n.t("no_episodes"))
            return None
        return season, episodes, 0

    # Interactive: offer to continue after the episode watched last.
    resumed = _nav_after_progress(series, progress) if progress else None
    if resumed is not None:
        _season, episodes, index = resumed
        choice = _select(
            i18n.t("resume_prompt"),
            [
                (i18n.t("resume_continue", episodes[index].label), "resume"),
                (i18n.t("resume_choose_other"), "other"),
            ],
        )
        if choice is None:
            return None  # aborted (Esc / Ctrl-C)
        if choice == "resume":
            return resumed

    return choose_episode_nav(series)


def _nav_after_progress(series: Series, progress: dict) -> Nav | None:
    """Position of the episode after the stored one, like ani-cli's history.

    At the end of a season this is the next season's first episode; after the
    very last episode it stays on that episode. None if it no longer exists.
    """
    from . import series as series_mod

    season = progress.get("season")
    number = progress.get("number")
    if season is None or number is None:
        return None
    info(i18n.t("loading_series"))
    episodes = series_mod.list_episodes(series, season)
    index = next((i for i, ep in enumerate(episodes) if ep.number == number), None)
    if index is None:
        return None
    if index + 1 < len(episodes):
        return season, episodes, index + 1
    if season != 0:  # films (season 0) do not continue into season 1
        later = [s for s in series_mod.list_seasons(series) if s > season]
        if later:
            next_episodes = series_mod.list_episodes(series, later[0])
            if next_episodes:
                return later[0], next_episodes, 0
    return season, episodes, index


def run(args: argparse.Namespace) -> int:
    """Top-level entry. Returns a process exit code."""
    # mpv is required for actual playback (not for --debug).
    if not args.debug and not check_player(args.player):
        return 1
    # fzf draws every menu; only source installs (e.g. Nix) can lack it.
    if not args.no_menu and not (_FZF != "fzf" or shutil.which("fzf")):
        error(i18n.t("fzf_missing"))
        return 1

    # Without menus nothing can be aborted, so a missing series/episode is an error.
    failed = 1 if args.no_menu else 0
    series = _pick_from_watchlist(args) if args.watchlist else _search_and_pick(args)
    if series is None:
        return failed

    nav = _initial_nav(series, args)
    if nav is None:
        return failed
    return _playback_loop(series, nav, args)


def _search_and_pick(args: argparse.Namespace) -> Series | None:
    """Resolve a query, search the site, and let the user pick a series."""
    query = _resolve_query(args)
    if not query:
        error(i18n.t("no_query") if args.no_menu else i18n.t("aborted"))
        return None

    info(i18n.t("searching"))
    from . import search as search_mod

    results = search_mod.search(query)
    if not results:
        error(i18n.t("no_results", query))
        return None

    series = _pick_series(results, args)
    if series is None:
        error(i18n.t("aborted"))
    return series


def _pick_from_watchlist(args: argparse.Namespace) -> Series | None:
    """Pick a series from the watched-history store, skipping search entirely."""
    from . import state

    entries = state.list_entries()
    if not entries:
        error(i18n.t("watchlist_empty"))
        return None

    series_list = [
        Series(title=e.get("title", e["slug"]), slug=e["slug"], url=e.get("url", ""))
        for e in entries
    ]
    if args.no_menu:
        return series_list[0]
    choices: list[Choice] = [
        (f"{i} " + i18n.t("watchlist_entry", s.title, e.get("label", "?")), s)
        for i, (e, s) in enumerate(zip(entries, series_list), 1)
    ]
    return _select(i18n.t("choose_from_watchlist"), choices)  # type: ignore[return-value]


def _lang_label(token: str) -> str:
    """Readable label for a language token, falling back to the raw token."""
    label = i18n.t(f"lang_{token}")
    return token if label == f"lang_{token}" else label


def _choose_language(hosters, args: argparse.Namespace, remembered: str | None) -> str | None:
    """Decide the language for this episode.

    Returns a concrete language token, or ``None`` to mean "use priority
    automatically". The menu is only shown interactively when more than one
    language is available; ``--lang`` and ``--no-menu`` skip it. A previously
    chosen language is reused as long as it is still on offer.
    """
    from . import resolve as resolve_mod

    if args.no_menu or args.lang:
        return None
    langs = resolve_mod.available_languages(hosters)
    if not langs:
        return None
    if remembered and remembered in langs:
        return remembered
    if len(langs) == 1:
        return langs[0]
    picked = _select(i18n.t("choose_language"), [(_lang_label(lang), lang) for lang in langs])
    # fzf's screen switch overwrote the cursor _playback_loop saved. Wipe the two
    # status lines above ("Playing ...", "Loading hosters...") and save it again.
    if sys.stdout.isatty():
        print("\033[2A\033[J\0337", end="", flush=True)
    return picked  # type: ignore[return-value]


def _playback_loop(series: Series, nav: Nav, args: argparse.Namespace) -> int:
    """Play the current episode, then offer the ani-cli style menu until the user exits."""
    season, episodes, index = nav
    preferred_lang: str | None = None
    while True:
        episode = episodes[index]
        # Like ani-cli: status lines of a successful run are wiped after playback.
        tty = sys.stdout.isatty()
        if tty:
            print("\0337", end="", flush=True)
        info(i18n.t("now_playing", _playing_label(episode)))
        rc, preferred_lang = resolve_and_play(episode, args, preferred_lang, series)
        if tty and rc == 0 and not args.debug:
            print("\0338\033[J", end="", flush=True)

        # Remember this as the resume point, but only if it actually played.
        if rc == 0 and not args.debug:
            from . import state

            state.record(series, episode)

        # --debug resolves one episode and stops.
        if args.debug:
            return rc

        # Auto/binge mode: advance without prompting until the season ends.
        if args.auto:
            if index + 1 < len(episodes):
                index += 1
                info(i18n.t("auto_next"))
                continue
            info(i18n.t("auto_season_end"))
            return rc

        # --no-menu plays exactly one episode.
        if args.no_menu:
            return rc

        action = post_playback_menu(
            series, episode, has_next=index + 1 < len(episodes), has_previous=index > 0
        )
        if action in (None, "quit"):
            info(i18n.t("goodbye"))
            return 0
        if action == "next":
            index += 1
        elif action == "previous":
            index -= 1
        elif action == "other":
            new_nav = choose_episode_nav(series)
            if new_nav is None:
                info(i18n.t("goodbye"))
                return 0
            season, episodes, index = new_nav


def resolve_and_play(
    episode: Episode,
    args: argparse.Namespace,
    preferred_lang: str | None = None,
    series: Series | None = None,
) -> tuple[int, str | None]:
    """Load hosters, let the user pick a language, resolve and play/debug-print.

    Returns ``(exit_code, chosen_language)``; the chosen language is carried back
    so the playback loop can reuse it for the next episode. ``series`` is used
    only to build a friendly mpv window title.
    """
    from . import episode as episode_mod
    from . import resolve as resolve_mod

    info(i18n.t("loading_hosters"))
    hosters = episode_mod.list_hosters(episode)
    if not hosters:
        error(i18n.t("no_hosters"))
        return 1, preferred_lang

    language = _choose_language(hosters, args, preferred_lang)
    # Remember a concrete pick; keep the old one when resolution is automatic.
    next_lang = language or preferred_lang

    stream, _hoster = resolve_mod.resolve_stream(hosters, language=language, report=info)
    if stream is None:
        error(i18n.t("all_hosters_failed"))
        return 1, next_lang

    if args.debug:
        print(i18n.t("debug_stream_url", stream.url))
        print(i18n.t("debug_headers", stream.headers))
        return 0, next_lang

    title = f"{series.title} – {episode.label}" if series else episode.label
    return play_stream(stream, args.player, title), next_lang


def post_playback_menu(
    series: Series, episode: Episode, has_next: bool = True, has_previous: bool = True
) -> str | None:
    """Shown after mpv exits, laid out like ani-cli's next/replay/previous menu.

    "next"/"previous" are left out at the ends of the season, so picking them
    can never fall back to replaying the current episode.
    """
    choices: list[Choice] = []
    if has_next:
        choices.append((i18n.t("next_episode"), "next"))
    choices.append((i18n.t("replay_episode"), "replay"))
    if has_previous:
        choices.append((i18n.t("previous_episode"), "previous"))
    choices += [(i18n.t("other_episode"), "other"), (i18n.t("quit"), "quit")]
    return _select(i18n.t("what_next", _playing_label(episode), series.title), choices)  # type: ignore[return-value]


def play_stream(stream: Stream, player_path: str | None, title: str | None = None) -> int:
    """Launch mpv, surfacing an error if it cannot start."""
    info(i18n.t("starting_player"))
    try:
        rc = player.play(stream, player_path, title)
    except player.PlayerNotFound as exc:
        error(i18n.t("mpv_missing"))
        error(str(exc))
        return 1
    # mpv no longer prints to the terminal, so say when it failed (0 = quit or end).
    if rc != 0:
        error(i18n.t("player_failed", rc))
    return rc
