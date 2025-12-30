#!/usr/bin/env bash
# history.sh - Watch History Management

# Speichere Episode in History
save_history() {
    local slug="$1"
    local season="$2"
    local episode="$3"
    local timestamp
    timestamp=$(date -Iseconds)

    mkdir -p "$DATA_DIR"
    echo "${slug}|${season}|${episode}|${timestamp}" >> "$HISTORY_FILE"
}

# Prüfe ob Anime in History ist
has_history() {
    local slug="$1"

    [ -f "$HISTORY_FILE" ] && grep -q "^${slug}|" "$HISTORY_FILE"
}

# Hole letzte Episode für Anime
get_last_episode() {
    local slug="$1"

    if [ ! -f "$HISTORY_FILE" ]; then
        echo ""
        return 1
    fi

    grep "^${slug}|" "$HISTORY_FILE" | tail -1 | cut -d'|' -f2,3
}

# Frage ob Fortsetzen gewünscht ist
prompt_continue_history() {
    local slug="$1"
    local last_episode
    last_episode=$(get_last_episode "$slug")

    if [ -n "$last_episode" ]; then
        local season episode
        season=$(echo "$last_episode" | cut -d'|' -f1)
        episode=$(echo "$last_episode" | cut -d'|' -f2)

        prompt_yes_no "Fortsetzen bei Staffel ${season}, Episode ${episode}" "y"
    else
        return 1
    fi
}

# Hole nächste Episode
get_next_episode() {
    local season="$1"
    local episode="$2"
    local max_episode="$3"

    local next_ep=$((episode + 1))

    if [ "$next_ep" -le "$max_episode" ]; then
        echo "${season}|${next_ep}"
        return 0
    else
        # Nächste Staffel, Episode 1
        echo "$((season + 1))|1"
        return 0
    fi
}
