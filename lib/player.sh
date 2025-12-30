#!/usr/bin/env bash
# player.sh - Video Player Integration

# Prüfe verfügbare Player
get_available_player() {
    if command -v mpv &>/dev/null; then
        echo "mpv"
    elif command -v vlc &>/dev/null; then
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

    case "$player" in
        mpv)
            # Prüfe ob yt-dlp verfügbar ist
            local ytdl_path=""
            if command -v yt-dlp &>/dev/null; then
                ytdl_path="yt-dlp"
            elif command -v youtube-dl &>/dev/null; then
                ytdl_path="youtube-dl"
            fi

            if [ -n "$ytdl_path" ]; then
                mpv "$video_url" \
                    --referrer="https://aniworld.to" \
                    --user-agent="$USER_AGENT" \
                    --script-opts=ytdl_hook-ytdl_path="$ytdl_path" \
                    --ytdl-format=bestvideo+bestaudio/best \
                    --force-media-title="$CURRENT_TITLE" \
                    >/dev/null 2>&1
            else
                mpv "$video_url" \
                    --referrer="https://aniworld.to" \
                    --user-agent="$USER_AGENT" \
                    --force-media-title="$CURRENT_TITLE" \
                    >/dev/null 2>&1
            fi
            ;;
        vlc)
            vlc "$video_url" \
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
