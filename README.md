# aniworld-cli

Ein Bash-basiertes CLI-Tool zum Streamen von Animes von AniWorld.to mit deutschen Synchronisationen und Untertiteln.

Inspiriert von [ani-cli](https://github.com/pystardust/ani-cli), aber speziell für deutsche Anime-Inhalte optimiert.

## Features

- 🎯 **Interaktiver Modus**: Starte `aniworld-cli` ohne Argument für interaktive Suche
- 🔍 **Anime-Suche**: Suche nach Anime-Titeln auf AniWorld.to (AJAX API)
- 📺 **Vollbild-fzf**: Nutzt das komplette Terminal-Fenster für bessere Übersicht
- 📜 **Watch History**: Speichere deinen Fortschritt und setze dort fort, wo du aufgehört hast
- 🎬 **Continue-Menü**: Elegantes fzf-Menü statt Y/n-Abfrage
- 🎮 **Post-Episode-Menü**: Wähle nach jeder Episode: next, replay, previous, select, quit
- 🌐 **Automatische Hoster-Auswahl**: Intelligente Auswahl (Streamtape → Vidmoly → Doodstream → VOE)
- 🎥 **mpv/vlc Integration**: Nahtlose Video-Player-Integration mit yt-dlp Support
- 🚀 **Binge-Watch-Modus**: Fließend durch Episoden navigieren
- 🎨 **Clean UI**: Keine Console-Spam, nur fzf-Menüs und minimale Loading-Nachrichten

## Dependencies

Folgende Tools müssen installiert sein:

- `curl` - Für HTTP-Requests
- `grep` - Text-Verarbeitung
- `sed` - Text-Verarbeitung
- `fzf` - Interaktive Auswahl
- `mpv` oder `vlc` - Video-Player
- `yt-dlp` oder `youtube-dl` - **Empfohlen** für Video-URL-Extraktion
- `jq` - **Optional** für besseres JSON-Parsing

### Installation der Dependencies

**Ubuntu/Debian:**
```bash
sudo apt install curl grep sed fzf mpv yt-dlp jq
```

**Arch Linux:**
```bash
sudo pacman -S curl grep sed fzf mpv yt-dlp jq
```

**Fedora:**
```bash
sudo dnf install curl grep sed fzf mpv yt-dlp jq
```

**macOS:**
```bash
brew install curl grep gnu-sed fzf mpv yt-dlp jq
```

## Installation

### Schnelle Installation

```bash
# Repository clonen
git clone https://github.com/USERNAME/aniworld-cli.git
cd aniworld-cli

# Install-Script ausführen
chmod +x install.sh
sudo ./install.sh
```

Das Install-Script wird:
- ✓ Automatisch dein Betriebssystem erkennen (Ubuntu, Arch, Fedora, macOS)
- ✓ Fehlende Dependencies installieren
- ✓ aniworld-cli system-weit verfügbar machen
- ✓ Data-Verzeichnis einrichten

### Manuelle Installation

Falls du das Install-Script nicht verwenden möchtest:

1. Dependencies installieren:
```bash
# Ubuntu/Debian
sudo apt install curl grep sed fzf mpv yt-dlp jq

# Arch Linux
sudo pacman -S curl grep sed fzf mpv yt-dlp jq

# Fedora
sudo dnf install curl grep sed fzf mpv yt-dlp jq
```

2. Symlink erstellen:
```bash
sudo ln -s "$(pwd)/aniworld-cli" /usr/local/bin/aniworld-cli
```

## Verwendung

### Interaktiver Modus (Empfohlen)

Starte aniworld-cli ohne Argument für den interaktiven Modus:
```bash
aniworld-cli
```

Du wirst dann gefragt:
```
INFO: Checking dependencies...
Search anime: [hier tippen]
```

Nach der Suche öffnet sich ein fzf-Vollbild-Menü mit allen Ergebnissen. Du kannst:
- 🔼🔽 Mit Pfeiltasten navigieren
- ⌨️  Tippen um Ergebnisse zu filtern
- ⏎  Enter drücken um auszuwählen

### Schnelle Suche

Suche direkt mit einem Argument:
```bash
aniworld-cli "One Piece"
```

### Fortsetzen

Setze den zuletzt geschauten Anime fort:
```bash
aniworld-cli --continue
# oder
aniworld-cli -c
```

### Post-Episode-Menü

Nach jeder Episode erscheint automatisch ein fzf-Menü:
```
> next      - Nächste Episode
  replay    - Episode wiederholen
  previous  - Vorherige Episode
  select    - Andere Episode wählen
  quit      - Beenden
```

### Hilfe anzeigen

```bash
aniworld-cli --help
```

### Version anzeigen

```bash
aniworld-cli --version
```

## Deinstallation

Um aniworld-cli zu deinstallieren:

```bash
cd aniworld-cli
sudo ./uninstall.sh
```

Das Uninstall-Script wird:
- ✓ Symlink aus /usr/local/bin entfernen
- ✓ Optional: Watch-History und Config löschen (du wirst gefragt)

## Workflow

1. **Start**: `aniworld-cli` (ohne Argument für interaktiven Modus)
2. **Suche**: Gib einen Anime-Titel ein (z.B. "One Piece")
3. **Auswahl**: Wähle aus den Suchergebnissen mit fzf-Vollbild
4. **History-Check**: Falls vorhanden, fzf-Menü zum Fortsetzen oder Neustart
5. **Staffel wählen**: Wähle die gewünschte Staffel (fzf-Vollbild)
6. **Episode wählen**: Wähle die gewünschte Episode (fzf-Vollbild)
7. **Hoster-Auswahl**: Automatische Auswahl des besten Hosters (Streamtape > Vidmoly > Doodstream > VOE)
8. **Streaming**: Video wird in mpv/vlc abgespielt (keine Console-Ausgabe)
9. **Post-Episode-Menü**: Wähle zwischen next, replay, previous, select oder quit
10. **Loop**: Zurück zu Schritt 8 für nahtloses Binge-Watching

## Datei-Struktur

```
aniworld-cli/
├── aniworld-cli           # Haupt-Executable
├── lib/
│   ├── scraper.sh        # Web-Scraping-Funktionen (AJAX API, Hoster-Extraktion)
│   ├── player.sh         # Video-Player-Integration (mpv/vlc)
│   ├── history.sh        # Watch-History-Management
│   └── ui.sh             # UI/UX-Funktionen (fzf-Vollbild-Menüs)
├── install.sh            # Installations-Script
├── uninstall.sh          # Deinstallations-Script
├── LICENSE               # MIT License
└── README.md             # Diese Datei

~/.local/share/aniworld-cli/  # Data-Verzeichnis (XDG-konform)
├── history.txt               # Watch-History (auto-generiert)
└── config                    # Konfiguration (auto-generiert)
```

## Konfiguration

Die Konfigurationsdatei wird automatisch unter `~/.local/share/aniworld-cli/config` erstellt.

### Player-Präferenz

Standardmäßig wird `mpv` bevorzugt, falls verfügbar. Du kannst die Präferenz manuell ändern:

```bash
echo "player=vlc" > ~/.local/share/aniworld-cli/config
```

## Watch History

Die Watch History wird in `~/.local/share/aniworld-cli/history.txt` gespeichert.

Format: `slug|season|episode|timestamp`

Beispiel:
```
one-piece|1|42|2025-12-30T12:34:56+01:00
naruto|2|15|2025-12-30T14:20:00+01:00
```

## Troubleshooting

### "Keine Ergebnisse gefunden"

- Überprüfe deine Internetverbindung
- Versuche einen anderen Suchbegriff
- AniWorld.to könnte offline sein

### "Konnte Video-URL nicht extrahieren"

- Der gewählte Hoster ist möglicherweise offline
- Versuche einen anderen Hoster manuell auszuwählen
- Manche Hoster benötigen spezielle Parsing-Logik

### Player startet nicht

- Stelle sicher, dass `mpv` oder `vlc` installiert ist
- Überprüfe mit: `which mpv` oder `which vlc`

### Cloudflare-Blockierung

Falls AniWorld.to Cloudflare-Schutz hat:
- Das Skript setzt bereits User-Agent-Header
- Versuche es nach einigen Minuten erneut
- Zu viele Requests können zu temporären Blockierungen führen

## Rechtlicher Hinweis

Dieses Tool greift auf Inhalte von AniWorld.to zu. Die Legalität des Streamens von Inhalten auf dieser Plattform liegt in einer Grauzone. Nutze dieses Tool auf eigene Verantwortung.

**Empfehlung**: Unterstütze offizielle Streaming-Dienste wie Crunchyroll, Wakanim oder Netflix für legalen Anime-Konsum.

## Bekannte Einschränkungen

- Keine Download-Funktion (nur Streaming)
- Hoster-Verfügbarkeit kann variieren
- Manche Hoster haben Anti-Scraping-Maßnahmen
- Qualitätsauswahl ist vom Hoster abhängig

## Contributing

Beiträge sind willkommen! So kannst du helfen:

1. **Fork** das Repository
2. Erstelle einen **Feature Branch** (`git checkout -b feature/AmazingFeature`)
3. **Committe** deine Änderungen (`git commit -m 'Add AmazingFeature'`)
4. **Push** zum Branch (`git push origin feature/AmazingFeature`)
5. Öffne einen **Pull Request**

### Bug Reports

Wenn du einen Bug findest, öffne bitte ein Issue mit:
- Beschreibung des Problems
- Schritte zur Reproduktion
- Erwartetes vs. tatsächliches Verhalten
- System-Info (OS, Dependencies-Versionen)

### Feature Requests

Feature-Ideen sind willkommen! Öffne ein Issue mit:
- Beschreibung des Features
- Use Case / Warum ist es nützlich?
- Optionale Implementierungs-Ideen

## Lizenz

MIT License - siehe [LICENSE](LICENSE) Datei für Details

Das bedeutet: Du kannst das Tool frei verwenden, modifizieren und verteilen.

## Credits

- Inspiriert von [ani-cli](https://github.com/pystardust/ani-cli)
- Verwendet [fzf](https://github.com/junegunn/fzf) für interaktive Auswahl
- Player: [mpv](https://mpv.io/) / [VLC](https://www.videolan.org/)
