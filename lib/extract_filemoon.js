#!/usr/bin/env node
// Filemoon Video-URL Extractor
// Dekodiert obfuszierten JavaScript-Code und extrahiert die Video-URL

const https = require('https');
const http = require('http');

function fetch(url, referer) {
    return new Promise((resolve, reject) => {
        const urlObj = new URL(url);
        const client = urlObj.protocol === 'https:' ? https : http;

        const options = {
            headers: {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                'Referer': referer || 'https://aniworld.to/'
            }
        };

        client.get(url, options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => resolve(data));
        }).on('error', reject);
    });
}

async function extractFilemoonURL(embed_url) {
    try {
        // 1. Lade Haupt-Filemoon-Seite
        const html = await fetch(embed_url, 'https://aniworld.to/');

        // 2. Extrahiere iframe-URL
        const iframeMatch = html.match(/<iframe[^>]*src="([^"]+)"/);
        if (!iframeMatch) {
            console.error('Keine iframe-URL gefunden');
            return null;
        }

        let iframeURL = iframeMatch[1];
        if (iframeURL.startsWith('//')) {
            iframeURL = 'https:' + iframeURL;
        }

        // 3. Lade iframe-Seite
        const iframeHTML = await fetch(iframeURL, 'https://filemoon.to/');

        // 4. Extrahiere und dekodiere eval-Code
        const evalMatch = iframeHTML.match(/eval\(function\(p,a,c,k,e,d\){[\s\S]+?}\('([\s\S]+?)',(\d+),(\d+),'([\s\S]+?)'\.split\('\|'\)\)\)/);

        if (!evalMatch) {
            console.error('Kein eval-Code gefunden');
            // Debug: Zeige ob überhaupt eval im Code ist
            if (iframeHTML.includes('eval(function')) {
                console.error('eval gefunden, aber Regex-Match fehlgeschlagen');
                console.error('iframe HTML Länge:', iframeHTML.length);
            } else {
                console.error('Kein eval im iframe HTML');
            }
            return null;
        }

        const [, packed, radix, count, dictionary] = evalMatch;
        const words = dictionary.split('|');

        // Dekodiere
        let unpacked = packed;
        for (let i = parseInt(count) - 1; i >= 0; i--) {
            if (words[i]) {
                const regex = new RegExp('\\b' + i.toString(parseInt(radix)) + '\\b', 'g');
                unpacked = unpacked.replace(regex, words[i]);
            }
        }

        // 5. Extrahiere Video-URL
        const m3u8Match = unpacked.match(/file:"([^"]+\.m3u8[^"]*)"/);
        if (m3u8Match) {
            return m3u8Match[1];
        }

        // Alternative: Suche nach sources Array
        const sourcesMatch = unpacked.match(/sources:\[{file:"([^"]+)"/);
        if (sourcesMatch) {
            return sourcesMatch[1];
        }

        console.error('Keine Video-URL im dekodierten Code gefunden');
        return null;

    } catch (error) {
        console.error('Fehler:', error.message);
        return null;
    }
}

// Main
const embed_url = process.argv[2];
if (!embed_url) {
    console.error('Usage: extract_filemoon.js <embed_url>');
    process.exit(1);
}

extractFilemoonURL(embed_url).then(url => {
    if (url) {
        console.log(url);
        process.exit(0);
    } else {
        process.exit(1);
    }
});
