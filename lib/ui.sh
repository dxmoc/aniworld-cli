#!/usr/bin/env bash
# ui.sh - User Interface Functions

# ANSI Color Codes
BLUE='\033[1;34m'
GREEN='\033[1;32m'
RED='\033[1;31m'
YELLOW='\033[1;33m'
CYAN='\033[1;36m'
RESET='\033[0m'

# Zeige Loading-Nachricht (silent mode - keine Ausgabe)
show_loading() {
    # Alles läuft im Hintergrund, keine Anzeige
    true
}

# Lösche Loading-Nachricht (silent mode)
clear_loading() {
    # Alles läuft im Hintergrund, keine Anzeige
    true
}

# fzf-Wrapper für Auswahl (Vollbild wie ani-cli)
select_with_fzf() {
    local prompt="$1"
    local input
    input=$(cat)

    # Vollbild-Modus wie ani-cli (kein --height)
    if command -v tty >/dev/null 2>&1 && tty -s 2>/dev/null; then
        echo "$input" | fzf --prompt="${prompt}: " --reverse --cycle --ansi 0</dev/tty 2>/dev/null || \
        echo "$input" | fzf --prompt="${prompt}: " --reverse --cycle --ansi
    else
        echo "$input" | fzf --prompt="${prompt}: " --reverse --cycle --ansi
    fi
}

# Zeige Fehler
show_error() {
    echo -e "${RED}ERROR: $1${RESET}" >&2
}

# Zeige Info
show_info() {
    echo -e "${GREEN}INFO: $1${RESET}" >&2
}

# Zeige Warnung
show_warning() {
    echo -e "${YELLOW}WARNING: $1${RESET}" >&2
}

# Episode-Menü nach Playback (fzf-basiert wie ani-cli)
show_episode_menu_fzf() {
    local current_title="$1"
    local current_season="$2"
    local current_episode="$3"

    # Optionen für fzf
    local options="next
replay
previous
select
quit"

    # fzf mit ani-cli Style
    echo "$options" | select_with_fzf "Playing: ${current_title} S${current_season}E${current_episode}"
}

# Ja/Nein-Prompt
prompt_yes_no() {
    local question="$1"
    local default="${2:-n}"

    local prompt_text
    if [ "$default" = "y" ]; then
        prompt_text="${CYAN}${question} [Y/n]:${RESET} "
    else
        prompt_text="${CYAN}${question} [y/N]:${RESET} "
    fi

    read -p "$(echo -e "$prompt_text")" response
    response="${response:-$default}"

    [[ "$response" =~ ^[Yy] ]]
}
