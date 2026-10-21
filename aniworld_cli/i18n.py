"""All user-facing strings, in English.

Keep every on-screen string here so wording stays in one place. Use ``t`` for
lookups; values may contain ``{}`` placeholders for ``str.format``. Menu prompts
follow ani-cli's wording where it has an equivalent.
"""

from __future__ import annotations

STRINGS: dict[str, str] = {
    # Generic
    "goodbye": "See you, Space Cowboy...",
    "aborted": "Aborted.",
    "unexpected_error": "Unexpected error. Run with --debug for details.",
    # Search
    "search_prompt": "Search anime:",
    "searching": "Searching...",
    "no_results": "No results found for '{}'!",
    "choose_series": "Select anime:",
    # Seasons / episodes
    "loading_series": "Loading series...",
    "choose_season": "Select season:",
    "choose_episode": "Select episode:",
    "season_label": "Season {}",
    "movies_label": "Movies",
    "no_episodes": "No episodes found!",
    # Language selection
    "choose_language": "Select language:",
    "lang_ger-dub": "German dub",
    "lang_ger-sub": "Japanese with German subtitles",
    "lang_eng-sub": "Japanese with English subtitles",
    # Hoster / extraction
    "loading_hosters": "Loading hosters...",
    "no_hosters": "No matching hosters found!",
    "resolving_hoster": "Resolving {}...",
    "extract_failed": "Could not resolve {}, trying the next hoster...",
    "stream_dead": "Stream from {} is not playable (e.g. 403), trying the next hoster...",
    "all_hosters_failed": "No hoster returned a playable stream!",
    "resolved_stream": "{} links fetched",
    # Player
    "mpv_missing": "mpv not found!",
    "mpv_hint_linux": "Install it with 'sudo pacman -S mpv', 'sudo apt install mpv' or 'sudo dnf install mpv'.",
    "mpv_hint_windows": "Install it with 'scoop install mpv' or 'winget install mpv'.",
    "starting_player": "Starting mpv...",
    "fzf_missing": (
        "fzf not found! Install it ('sudo apt install fzf', 'scoop install fzf') "
        "or install aniworld-cli from the wheel, which ships fzf."
    ),
    # Post-playback menu
    "what_next": "Playing {} of {}...",
    "next_episode": "next",
    "replay_episode": "replay",
    "previous_episode": "previous",
    "other_episode": "select",
    "quit": "quit",
    "now_playing": "Playing {}...",
    "episode_label": "episode {}",
    # Resume / watchlist / auto mode
    "resume_prompt": "Resume?",
    "resume_continue": "Continue with {}",
    "resume_choose_other": "Select another episode",
    "choose_from_watchlist": "Select anime:",
    "watchlist_entry": "{} - last watched {}",
    "watchlist_empty": "Your watchlist is empty. Watch something first and it will show up here.",
    "auto_next": "Auto mode: next episode...",
    "auto_season_end": "End of season reached, auto mode stopped.",
    # Argument handling
    "episode_arg_invalid": "Invalid --episode value '{}'. Expected season-episode, e.g. 1-3 (or 0-1 for movies).",
    "episode_not_found": "Episode {} not found!",
    "season_not_found": "Season {} not found!",
    "no_query": "No search term given!",
    # Network / anti-bot
    "network_error": "Network error. Is the site reachable?",
    "cloudflare_block": (
        "The site is behind a Cloudflare challenge. "
        "An external 'flaresolverr' service can help (not included)."
    ),
    # Debug
    "debug_stream_url": "Stream URL: {}",
    "debug_headers": "Headers: {}",
}


def t(key: str, *args: object) -> str:
    """Look up a string and optionally ``format`` it."""
    text = STRINGS.get(key, key)
    if args:
        return text.format(*args)
    return text
