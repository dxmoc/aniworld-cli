#!/usr/bin/env bash
# scraper.sh - Web Scraping Functions

# Session Cache für HTML-Seiten (reduziert HTTP-Requests)
declare -A HTML_CACHE

# Hole HTML mit Cache
get_anime_html() {
    local slug="$1"

    # Prüfe Cache
    if [ -n "${HTML_CACHE[$slug]:-}" ]; then
        echo "${HTML_CACHE[$slug]}"
        return 0
    fi

    # Lade HTML
    local html
    html=$(curl -s --compressed -A "$USER_AGENT" "${BASE_URL}/anime/stream/${slug}")

    # Speichere im Cache
    HTML_CACHE[$slug]="$html"

    echo "$html"
}

# Suche nach Anime
search_anime() {
    local query="$1"

    show_loading "Suche nach '${query}'"

    # AJAX-Request an die Search-API (mit Compression und Timeout)
    local json
    json=$(curl -s --compressed --max-time 10 -X POST \
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

# Hole Staffeln für einen Anime (gecached)
get_seasons() {
    local slug="$1"

    show_loading "Lade Staffeln"

    local html
    html=$(get_anime_html "$slug")

    clear_loading

    # Parse Staffeln (Windows-kompatibel mit sed, optimiert)
    echo "$html" | \
        sed -n 's/.*staffel-\([0-9][0-9]*\).*/\1/p' | \
        sort -nu
}

# Hole Episoden für eine Staffel (gecached)
get_episodes() {
    local slug="$1"
    local season="$2"

    show_loading "Lade Episoden"

    local html
    html=$(get_anime_html "$slug")

    clear_loading

    # Parse Episoden für die Staffel (Windows-kompatibel mit sed, optimiert)
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
    html=$(curl -s --compressed -A "$USER_AGENT" "$url")

    clear_loading

    # Debug: Speichere HTML für Fehleranalyse (optional)
    if [ -n "${DEBUG:-}" ]; then
        echo "$html" > "${DATA_DIR}/debug_episode.html"
        show_info "Debug: HTML gespeichert in ${DATA_DIR}/debug_episode.html"
    fi

    # Parse Redirect-IDs, Hoster-Namen und Metadaten
    # Format: redirect_id|hoster_name|language|quality
    # Windows-kompatible Version ohne grep -oP (funktioniert mit Git Bash)

    # Extrahiere alle redirect IDs, Hoster-Namen und Metadaten
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

            # Extrahiere Sprache (data-lang-key) und mappe zu lesbaren Namen
            local lang_key=$(echo "$line" | sed -n 's/.*data-lang-key="\([^"]*\)".*/\1/p' | head -1)

            # Mappe language keys zu lesbaren Namen (basierend auf aniworld.to Konvention)
            case "$lang_key" in
                1) language="GerDub" ;;
                2) language="GerSub" ;;
                3) language="EngSub" ;;
                *) language="" ;;
            esac

            # Extrahiere Qualität aus verschiedenen Quellen
            # 1. Suche nach expliziten Qualitäts-Angaben (720p, 1080p, etc.)
            quality=$(echo "$line" | grep -oE '[0-9]{3,4}p' | head -1)

            # 2. Wenn nicht gefunden, suche nach Qualitäts-Keywords
            if [ -z "$quality" ]; then
                if echo "$line" | grep -qi "1080"; then
                    quality="1080p"
                elif echo "$line" | grep -qi "720"; then
                    quality="720p"
                elif echo "$line" | grep -qi "480"; then
                    quality="480p"
                elif echo "$line" | grep -qi "HD"; then
                    quality="HD"
                fi
            fi

            # Fallback: Suche nach GerDub, GerSub direkt im Text
            if [ -z "$language" ]; then
                language=$(echo "$line" | grep -oE '(GerDub|GerSub|EngSub|Ger|Eng)' | head -1)
            fi

            # Fallback: Wenn kein Hoster-Name gefunden, nutze language oder generischen Namen
            if [ -z "$hoster" ]; then
                if [ -n "$language" ]; then
                    hoster="$language"
                else
                    hoster="Hoster_${redirect_id}"
                fi
            fi

            # Debug output
            if [ -n "${DEBUG:-}" ]; then
                echo "DEBUG: redirect_id=$redirect_id hoster=$hoster language=$language quality=$quality" >&2
            fi

            # Nur ausgeben wenn redirect_id vorhanden
            if [ -n "$redirect_id" ]; then
                # Format: redirect_id|hoster|language|quality
                echo "${redirect_id}|${hoster}|${language:-N/A}|${quality:-N/A}"
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
    elif [[ "$embed_url" == *"voe.sx"* ]] || [[ "$embed_url" == *"voe"* ]]; then
        video_url=$(extract_voe_url "$embed_url")
    elif [[ "$embed_url" == *"filemoon"* ]]; then
        video_url=$(extract_filemoon_url "$embed_url")
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

# Extrahiere Filemoon Video-URL
extract_filemoon_url() {
    local embed_url="$1"

    # Filemoon verschleiert die Video-URL mit obfusziertem JavaScript
    # Verwende Node.js-Extractor, um die tatsächliche Video-URL zu dekodieren
    if command -v node &>/dev/null; then
        local video_url
        video_url=$(node "${LIB_DIR}/extract_filemoon.js" "$embed_url" 2>/dev/null)

        if [ -n "$video_url" ]; then
            echo "$video_url"
        else
            # Fallback: Embed-URL (mpv wird es versuchen)
            echo "$embed_url"
        fi
    else
        # Node.js nicht verfügbar - Fallback
        echo "$embed_url"
    fi
}

# Hole Anime-Titel (gecached)
get_anime_title() {
    local slug="$1"

    local html
    html=$(get_anime_html "$slug")

    # Titel ist in <h1 itemprop="name"><span>TITEL</span></h1> Format
    # Wichtig: Nur das erste <span> innerhalb von <h1>, nicht greedy matchen
    echo "$html" | \
        grep 'itemprop="name"' | \
        sed -n 's/.*<h1[^>]*>.*<span>\([^<]*\)<\/span>.*/\1/p' | \
        head -1
}

# Hole Gesamt-Episodenanzahl über alle Staffeln (mit Cache)
get_total_episode_count() {
    local slug="$1"

    # Prüfe Cache
    if [ -f "$EPISODE_COUNT_CACHE" ]; then
        local cached
        cached=$(grep "^${slug}|" "$EPISODE_COUNT_CACHE" 2>/dev/null | cut -d'|' -f2)
        if [ -n "$cached" ]; then
            echo "$cached"
            return 0
        fi
    fi

    # Hole HTML aus Cache
    local html
    html=$(get_anime_html "$slug")

    # Extrahiere alle Staffeln aus dem HTML
    local seasons
    seasons=$(echo "$html" | sed -n 's/.*staffel-\([0-9][0-9]*\).*/\1/p' | sort -nu)

    # Zähle Episoden pro Staffel
    local total=0
    while read -r season; do
        local count
        count=$(echo "$html" | sed -n "s/.*staffel-${season}\/episode-\([0-9][0-9]*\).*/\1/p" | sort -nu | tail -1)
        if [ -n "$count" ]; then
            total=$((total + count))
        fi
    done <<< "$seasons"

    # Speichere im Cache
    mkdir -p "$CACHE_DIR"
    echo "${slug}|${total}" >> "$EPISODE_COUNT_CACHE"

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
