#!/usr/bin/env bash
# scraper.sh - Web Scraping Functions

# Suche nach Anime
search_anime() {
    local query="$1"

    show_loading "Suche nach '${query}'"

    # AJAX-Request an die Search-API
    local json
    json=$(curl -s -X POST \
                -A "$USER_AGENT" \
                -H "Content-Type: application/x-www-form-urlencoded" \
                -d "keyword=${query}" \
                "${BASE_URL}/ajax/search")

    clear_loading

    # Parse JSON und extrahiere nur Anime-Links
    # Format: Titel|Slug
    if command -v jq &>/dev/null; then
        # Mit jq (bevorzugt)
        echo "$json" | \
            jq -r '.[] | select(.link | startswith("/anime/stream/")) | .title + "|" + (.link | sub("/anime/stream/"; ""))' | \
            sed 's/<em>//g; s/<\/em>//g'
    else
        # Fallback ohne jq
        echo "$json" | \
            tr ',' '\n' | \
            grep '/anime/stream/' | \
            grep -oP '"link":"\/anime\/stream\/\K[^"]+' | \
            while read -r slug; do
                title=$(echo "$json" | grep -oP "\"link\":\"/anime/stream/${slug}\"[^}]*\"title\":\"\K[^\"]+")
                echo "${title}|${slug}"
            done | \
            sed 's/<em>//g; s/<\/em>//g'
    fi
}

# Hole Staffeln für einen Anime
get_seasons() {
    local slug="$1"

    show_loading "Lade Staffeln"

    local html
    html=$(curl -s -A "$USER_AGENT" "${BASE_URL}/anime/stream/${slug}")

    clear_loading

    # Parse Staffeln (Windows-kompatibel mit sed)
    echo "$html" | \
        sed -n 's/.*staffel-\([0-9][0-9]*\).*/\1/p' | \
        sort -nu
}

# Hole Episoden für eine Staffel
get_episodes() {
    local slug="$1"
    local season="$2"

    show_loading "Lade Episoden"

    local html
    html=$(curl -s -A "$USER_AGENT" "${BASE_URL}/anime/stream/${slug}")

    clear_loading

    # Parse Episoden für die Staffel (Windows-kompatibel mit sed)
    echo "$html" | \
        sed -n "s/.*staffel-${season}\/episode-\([0-9][0-9]*\).*/\1/p" | \
        sort -nu
}

# Hole Hoster-Links für eine Episode
get_hoster_links() {
    local slug="$1"
    local season="$2"
    local episode="$3"

    show_loading "Lade Hoster"

    local url="${BASE_URL}/anime/stream/${slug}/staffel-${season}/episode-${episode}"
    local html
    html=$(curl -s -A "$USER_AGENT" "$url")

    clear_loading

    # Debug: Speichere HTML für Fehleranalyse (optional)
    if [ -n "${DEBUG:-}" ]; then
        echo "$html" > "${DATA_DIR}/debug_episode.html"
        show_info "Debug: HTML gespeichert in ${DATA_DIR}/debug_episode.html"
    fi

    # Parse Redirect-IDs und Hoster-Namen
    # Format: redirect_id|hoster_name
    # Windows-kompatible Version ohne grep -oP (funktioniert mit Git Bash)

    # Extrahiere alle redirect IDs und Hoster-Namen
    echo "$html" | \
        tr '\n' ' ' | \
        sed 's/<li/\n<li/g' | \
        grep 'data-link-target="/redirect/' | \
        while read -r line; do
            # Extrahiere redirect_id mit sed (POSIX-kompatibel)
            redirect_id=$(echo "$line" | sed -n 's/.*data-link-target="\/redirect\/\([0-9]*\)".*/\1/p')

            # Extrahiere Hoster-Name aus verschiedenen Patterns
            # Pattern 1: <i class="icon HOSTER">
            hoster=$(echo "$line" | sed -n 's/.*<i class="icon \([^"]*\)".*/\1/p' | head -1)

            # Pattern 2: <h4>HOSTER</h4>
            if [ -z "$hoster" ]; then
                hoster=$(echo "$line" | sed -n 's/.*<h4>\([^<]*\)<\/h4>.*/\1/p' | head -1)
            fi

            # Pattern 3: data-lang-key Attribute
            if [ -z "$hoster" ]; then
                hoster=$(echo "$line" | sed -n 's/.*data-lang-key="\([^"]*\)".*/\1/p' | head -1)
            fi

            # Debug output
            if [ -n "${DEBUG:-}" ]; then
                echo "DEBUG: redirect_id=$redirect_id hoster=$hoster" >&2
            fi

            # Nur ausgeben wenn redirect_id vorhanden
            if [ -n "$redirect_id" ]; then
                # Wenn kein Hoster-Name gefunden, generischen Namen verwenden
                if [ -z "$hoster" ]; then
                    hoster="Hoster_${redirect_id}"
                fi
                echo "${redirect_id}|${hoster}"
            fi
        done
}

# Extrahiere Video-URL aus Hoster
extract_video_url() {
    local redirect_id="$1"

    show_loading "Extrahiere Video-URL"

    # Folge dem Redirect
    local redirect_url="${BASE_URL}/redirect/${redirect_id}"
    local embed_url
    embed_url=$(curl -sL -A "$USER_AGENT" \
                     -w '%{url_effective}' \
                     -o /dev/null \
                     "$redirect_url")

    if [ -z "$embed_url" ]; then
        clear_loading
        show_error "Konnte Redirect nicht folgen"
        return 1
    fi

    # Versuche Video-URL zu extrahieren basierend auf Hoster
    local video_url=""

    if [[ "$embed_url" == *"streamtape"* ]]; then
        video_url=$(extract_streamtape_url "$embed_url")
    elif [[ "$embed_url" == *"vidmoly"* ]]; then
        video_url=$(extract_vidmoly_url "$embed_url")
    elif [[ "$embed_url" == *"doodstream"* ]] || [[ "$embed_url" == *"dood"* ]]; then
        video_url=$(extract_doodstream_url "$embed_url")
    elif [[ "$embed_url" == *"voe.sx"* ]]; then
        video_url=$(extract_voe_url "$embed_url")
    elif [[ "$embed_url" == *"filemoon"* ]]; then
        video_url="$embed_url"  # Filemoon direkt probieren
    else
        # Fallback: Versuche Embed-URL direkt
        video_url="$embed_url"
    fi

    clear_loading
    echo "$video_url"
}

# Extrahiere VOE Video-URL
extract_voe_url() {
    local embed_url="$1"

    # VOE.sx redirects to another domain, follow JavaScript redirect
    local html
    html=$(curl -s -A "$USER_AGENT" "$embed_url")

    # Parse redirect URL from JavaScript (Windows-kompatibel)
    local redirect_url
    redirect_url=$(echo "$html" | sed -n "s/.*window\.location\.href = '\([^']*\)'.*/\1/p" | head -1)

    if [ -n "$redirect_url" ]; then
        html=$(curl -s -A "$USER_AGENT" "$redirect_url")
    fi

    # Suche nach m3u8 oder mp4 URL (Windows-kompatibel mit sed/grep Fallback)
    local video_url
    video_url=$(echo "$html" | grep -o 'https\?://[^"'\'']*\.\(m3u8\|mp4\)[^"'\'']*' | grep -v "test-videos" | head -1)

    if [ -n "$video_url" ]; then
        echo "$video_url"
    else
        # Fallback: Embed-URL für mpv (yt-dlp könnte es schaffen)
        echo "$embed_url"
    fi
}

# Extrahiere Vidmoly Video-URL
extract_vidmoly_url() {
    local embed_url="$1"

    local html
    html=$(curl -s -A "$USER_AGENT" "$embed_url")

    # Vidmoly verwendet oft "sources" in JavaScript (Windows-kompatibel)
    local video_url
    video_url=$(echo "$html" | sed -n 's/.*\(sources\|file\):\s*["\x27]\(https\?:\/\/[^"'\'']*\.\(m3u8\|mp4\)[^"'\'']*\).*/\2/p' | head -1)

    # Fallback: Generisches Pattern
    if [ -z "$video_url" ]; then
        video_url=$(echo "$html" | grep -o 'https\?://[^"'\'']*\.\(m3u8\|mp4\)[^"'\'']*' | head -1)
    fi

    if [ -n "$video_url" ]; then
        echo "$video_url"
    else
        echo "$embed_url"
    fi
}

# Extrahiere Streamtape Video-URL
extract_streamtape_url() {
    local embed_url="$1"

    local html
    html=$(curl -s -A "$USER_AGENT" "$embed_url")

    # Streamtape verschleiert die URL, suche nach typischen Patterns (Windows-kompatibel)
    local video_url
    video_url=$(echo "$html" | sed -n "s/.*document\.getElementById('videolink')\.innerHTML = '\/\/\([^']*\)'.*/\1/p" | head -1)

    if [ -n "$video_url" ]; then
        echo "https://${video_url}"
    else
        # Fallback: Embed-URL
        echo "$embed_url"
    fi
}

# Extrahiere Doodstream Video-URL
extract_doodstream_url() {
    local embed_url="$1"

    local html
    html=$(curl -s -A "$USER_AGENT" "$embed_url")

    # Doodstream verwendet ein spezielles Pattern
    local video_url
    video_url=$(echo "$html" | grep -oP '\$\.get\(["\x27]/pass_md5/[^"'\'']+["\x27]' | grep -oP '/pass_md5/\K[^"'\'']+')

    if [ -n "$video_url" ]; then
        # Hole finale URL
        local base_url
        base_url=$(echo "$embed_url" | grep -oP 'https?://[^/]+')
        video_url=$(curl -s -A "$USER_AGENT" "${base_url}/pass_md5/${video_url}")
        echo "$video_url"
    else
        # Fallback: Embed-URL
        echo "$embed_url"
    fi
}

# Hole Anime-Titel
get_anime_title() {
    local slug="$1"

    local html
    html=$(curl -s -A "$USER_AGENT" "${BASE_URL}/anime/stream/${slug}")

    # Titel ist in <h1 itemprop="name"><span>TITEL</span></h1> Format
    # Wichtig: Nur das erste <span> innerhalb von <h1>, nicht greedy matchen
    echo "$html" | \
        grep 'itemprop="name"' | \
        sed -n 's/.*<h1[^>]*>.*<span>\([^<]*\)<\/span>.*/\1/p' | \
        head -1
}

# Hole Gesamt-Episodenanzahl über alle Staffeln
get_total_episode_count() {
    local slug="$1"

    local seasons
    seasons=$(get_seasons "$slug")

    local total=0
    while read -r season; do
        local episodes
        episodes=$(get_episodes "$slug" "$season")
        local count
        count=$(echo "$episodes" | wc -l)
        total=$((total + count))
    done <<< "$seasons"

    echo "$total"
}

# Hole Video-URL für Episode (zentralisiert mit Loading-Nachrichten)
get_video_for_episode() {
    local slug="$1"
    local season="$2"
    local episode="$3"

    show_loading "Lade Episode ${episode}"

    # Hole Hoster
    local hoster_id
    hoster_id=$(select_hoster_interactive "$slug" "$season" "$episode")

    if [ -z "$hoster_id" ]; then
        clear_loading
        return 1
    fi

    # Extrahiere Video-URL
    local video_url
    video_url=$(extract_video_url "$hoster_id")

    clear_loading

    if [ -z "$video_url" ]; then
        return 1
    fi

    echo "$video_url"
}
