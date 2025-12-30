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

    # Parse Staffeln
    echo "$html" | \
        grep -oP 'staffel-\K[0-9]+' | \
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

    # Parse Episoden für die Staffel
    echo "$html" | \
        grep -oP "staffel-${season}/episode-\K[0-9]+" | \
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

    # Parse Redirect-IDs und Hoster-Namen
    # Format: redirect_id|hoster_name
    # Extrahiere aus: <i class="icon HOSTER_NAME" ...> oder <h4>HOSTER_NAME</h4>
    echo "$html" | \
        tr '\n' ' ' | \
        grep -oP '<li[^>]*data-link-target="/redirect/[0-9]+"[^>]*>.*?</li>' | \
        while read -r li_block; do
            redirect_id=$(echo "$li_block" | grep -oP 'data-link-target="/redirect/\K[0-9]+')
            # Versuche Hoster-Name aus <i class="icon HOSTER">
            hoster=$(echo "$li_block" | grep -oP '<i class="icon \K[^"]+' | head -1)
            # Falls nicht gefunden, versuche aus <h4>
            if [ -z "$hoster" ]; then
                hoster=$(echo "$li_block" | grep -oP '<h4>\K[^<]+' | head -1)
            fi
            [ -n "$redirect_id" ] && echo "${redirect_id}|${hoster}"
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

    # Parse redirect URL from JavaScript
    local redirect_url
    redirect_url=$(echo "$html" | grep -oP "window\.location\.href = '\K[^']+" | head -1)

    if [ -n "$redirect_url" ]; then
        html=$(curl -s -A "$USER_AGENT" "$redirect_url")
    fi

    # Suche nach m3u8 oder mp4 URL
    local video_url
    video_url=$(echo "$html" | grep -oP 'https?://[^"'\'']*\.(m3u8|mp4)(\?[^"'\'']*)?' | grep -v "test-videos" | head -1)

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

    # Vidmoly verwendet oft "sources" in JavaScript
    local video_url
    video_url=$(echo "$html" | grep -oP '(sources:|file:)\s*["\x27]\K(https?://[^"'\'']+\.(m3u8|mp4)[^"'\'']*)' | head -1)

    # Fallback: Generisches Pattern
    if [ -z "$video_url" ]; then
        video_url=$(echo "$html" | grep -oP 'https?://[^"'\'']*\.(m3u8|mp4)(\?[^"'\'']*)?' | head -1)
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

    # Streamtape verschleiert die URL, suche nach typischen Patterns
    local video_url
    video_url=$(echo "$html" | grep -oP "document\.getElementById\('videolink'\)\.innerHTML = '//[^']+" | grep -oP "//\K[^']+")

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

    # Titel ist in <h1><span>TITEL</span></h1> Format
    echo "$html" | \
        grep -oP '<h1[^>]*>.*?<span>\K[^<]+' | \
        head -1
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
