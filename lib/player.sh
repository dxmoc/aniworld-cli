#!/usr/bin/env bash
# player.sh - Video Player Integration

# Prüfe verfügbare Player (Windows-kompatibel)
get_available_player() {
    if command -v mpv &>/dev/null || command -v mpv.exe &>/dev/null; then
        echo "mpv"
    elif command -v vlc &>/dev/null || command -v vlc.exe &>/dev/null; then
        echo "vlc"
    else
        echo ""
    fi
}

# Spiele Video ab
play_video() {
    local video_url="$1"
    local player
    player=$(get_available_player)

    if [ -z "$player" ]; then
        show_error "Kein Video-Player gefunden (mpv oder vlc benötigt)"
        return 1
    fi

    # Kein "Starte player..." output - direkt abspielen

    # Windows-kompatibel: Finde den korrekten Befehl
    local player_cmd=""
    if [ "$player" = "mpv" ]; then
        if command -v mpv &>/dev/null; then
            player_cmd="mpv"
        elif command -v mpv.exe &>/dev/null; then
            player_cmd="mpv.exe"
        fi
    elif [ "$player" = "vlc" ]; then
        if command -v vlc &>/dev/null; then
            player_cmd="vlc"
        elif command -v vlc.exe &>/dev/null; then
            player_cmd="vlc.exe"
        fi
    fi

    case "$player" in
        mpv)
            # Prüfe ob yt-dlp verfügbar ist
            local ytdl_path=""
            if command -v yt-dlp &>/dev/null; then
                ytdl_path="yt-dlp"
            elif command -v yt-dlp.exe &>/dev/null; then
                ytdl_path="yt-dlp.exe"
            elif command -v youtube-dl &>/dev/null; then
                ytdl_path="youtube-dl"
            fi

            if [ -n "$ytdl_path" ]; then
                "$player_cmd" "$video_url" \
                    --referrer="https://aniworld.to" \
                    --user-agent="$USER_AGENT" \
                    --script-opts=ytdl_hook-ytdl_path="$ytdl_path" \
                    --ytdl-format=bestvideo+bestaudio/best \
                    --force-media-title="$CURRENT_TITLE" \
                    >/dev/null 2>&1
            else
                "$player_cmd" "$video_url" \
                    --referrer="https://aniworld.to" \
                    --user-agent="$USER_AGENT" \
                    --force-media-title="$CURRENT_TITLE" \
                    >/dev/null 2>&1
            fi
            ;;
        vlc)
            "$player_cmd" "$video_url" \
                --http-referrer="https://aniworld.to" \
                --http-user-agent="$USER_AGENT" \
                --no-loop \
                --play-and-exit \
                >/dev/null 2>&1
            ;;
    esac
}

# Konfiguriere Player-Präferenz
get_player_preference() {
    if [ -f "$CONFIG_FILE" ]; then
        grep "^player=" "$CONFIG_FILE" | cut -d'=' -f2
    fi
}

# Setze Player-Präferenz
set_player_preference() {
    local player="$1"
    mkdir -p "$DATA_DIR"

    if [ -f "$CONFIG_FILE" ]; then
        sed -i "/^player=/d" "$CONFIG_FILE"
    fi

    echo "player=${player}" >> "$CONFIG_FILE"
}
