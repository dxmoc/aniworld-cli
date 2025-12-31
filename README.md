# aniworld-cli

Ein Bash-basiertes CLI-Tool zum Streamen von Animes von AniWorld.to mit deutschen Synchronisationen und Untertiteln.

Inspiriert von [ani-cli](https://github.com/pystardust/ani-cli), aber speziell für deutsche Anime-Inhalte optimiert.

## Features

- 🎯 **Interaktiver Modus**: Starte `aniworld-cli` ohne Argument für interaktive Suche
- 🔍 **Anime-Suche**: Suche nach Anime-Titeln auf AniWorld.to (AJAX API)
- 📺 **Vollbild-fzf**: Nutzt das komplette Terminal-Fenster für bessere Übersicht
- 📜 **Watch History**: Speichere deinen Fortschritt und setze dort fort, wo du aufgehört hast
- 🎬 **Continue-Menü**: Elegantes fzf-Menü statt Y/n-Abfrage
- 🎮 **Post-Episode-Menü**: Wähle nach jeder Episode: next, replay, previous, select, hoster, quit
- 🌐 **Intelligente Hoster-Auswahl**: Automatische Auswahl (Streamtape → Vidmoly → Doodstream → VOE)
- 🔄 **Manuelle Hoster-Wechsel**: Wechsle zwischen Streaming-Anbietern während der Wiedergabe
- 🎥 **mpv/vlc Integration**: Nahtlose Video-Player-Integration mit yt-dlp Support
- 🚀 **Binge-Watch-Modus**: Fließend durch Episoden navigieren
- 🎨 **Clean UI**: Keine Console-Spam, nur fzf-Menüs und minimale Loading-Nachrichten
- 💻 **Cross-Platform**: Linux, macOS und Windows (via Git Bash)

## Dependencies

Folgende Tools müssen installiert sein:

- `curl` - Für HTTP-Requests
- `grep` - Text-Verarbeitung
- `sed` - Text-Verarbeitung
- `fzf` - Interaktive Auswahl
- `mpv` oder `vlc` - Video-Player
- `yt-dlp` oder `youtube-dl` - **Empfohlen** für Video-URL-Extraktion
- `node` (Node.js) - **Erforderlich** für Filemoon-Hoster-Unterstützung
- `jq` - **Optional** für besseres JSON-Parsing

**Wichtig:** Node.js wird für den Filemoon-Hoster benötigt, da dieser seine Video-URLs mit obfusziertem JavaScript verschleiert. Ohne Node.js funktioniert Filemoon nicht.

### Installation der Dependencies

**Ubuntu/Debian:**
```bash
sudo apt install curl grep sed fzf mpv yt-dlp nodejs jq
```

**Arch Linux:**
```bash
sudo pacman -S curl grep sed fzf mpv yt-dlp nodejs jq
```

**Fedora:**
```bash
sudo dnf install curl grep sed fzf mpv yt-dlp nodejs jq
```

**macOS:**
```bash
brew install curl grep gnu-sed fzf mpv yt-dlp node jq
```

**Windows:**
```bash
# In Git Bash (siehe Windows Installation Sektion)
scoop install fzf mpv yt-dlp nodejs aria2 jq
```

## Installation

### Linux/macOS - Schnelle Installation

```bash
# Repository clonen
git clone https://github.com/dxmoc/aniworld-cli.git
cd aniworld-cli

# Install-Script ausführen
chmod +x install.sh
sudo ./install.sh
```

Das Install-Script wird:
- ✓ Automatisch dein Betriebssystem erkennen (Ubuntu, Arch, Fedora, Alpine, Void, Gentoo, Solus, NixOS, macOS)
- ✓ Fehlende Dependencies installieren
- ✓ aniworld-cli system-weit verfügbar machen
- ✓ Data-Verzeichnis einrichten

**Windows-Nutzer:** Siehe [Windows Installation](#windows-installation) weiter unten.

### Manuelle Installation

Falls du das Install-Script nicht verwenden möchtest:

1. Dependencies installieren:
```bash
# Ubuntu/Debian
sudo apt install curl grep sed fzf mpv yt-dlp nodejs jq

# Arch Linux
sudo pacman -S curl grep sed fzf mpv yt-dlp nodejs jq

# Fedora
sudo dnf install curl grep sed fzf mpv yt-dlp nodejs jq
```

2. Symlink erstellen:
```bash
sudo ln -s "$(pwd)/aniworld-cli" /usr/local/bin/aniworld-cli
```

### Windows Installation

aniworld-cli funktioniert auf Windows über **Git Bash** in Windows Terminal. PowerShell/CMD werden nicht unterstützt.

#### Voraussetzungen

**1. Scoop Package Manager installieren**

Öffne PowerShell und folge der Anleitung auf [scoop.sh](https://scoop.sh/):
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression
```

**2. Windows Terminal installieren** (falls nicht vorhanden)

Windows 11: Bereits vorinstalliert
Windows 10:
```powershell
scoop bucket add extras
scoop install extras/windows-terminal
```

**3. Git Bash installieren und konfigurieren**

```powershell
scoop install git
```

Git Bash als Windows Terminal Profil einrichten:
- Öffne Windows Terminal
- Klicke auf das Dropdown-Menü (▼) → Einstellungen
- Profile → Neues Profil hinzufügen → Neues leeres Profil
- **Befehlszeile:** `C:\Program Files\Git\bin\bash.exe -i -l`
- **Startverzeichnis:** `%USERPROFILE%`
- **Name:** Git Bash
- Speichern und Windows Terminal neu starten

#### Installation

Öffne das **Git Bash Profil** in Windows Terminal:

**1. Dependencies installieren:**
```bash
scoop bucket add extras
scoop install fzf mpv yt-dlp nodejs aria2 jq
```

**2. aniworld-cli installieren:**
```bash
# Repository clonen
cd ~
git clone https://github.com/dxmoc/aniworld-cli.git
cd aniworld-cli

# Zum PATH hinzufügen (in ~/.bashrc)
echo "export PATH=\"\$HOME/aniworld-cli:\$PATH\"" >> ~/.bashrc
source ~/.bashrc

# Executable machen
chmod +x aniworld-cli
```

**3. Testen:**
```bash
aniworld-cli --version
```

#### Windows-spezifische Hinweise

- ✅ Verwende **nur Git Bash** (keine PowerShell/CMD)
- ✅ Windows Terminal wird empfohlen (bessere Unicode-Unterstützung)
- ✅ mpv öffnet Videos in einem separaten Fenster
- ⚠️ Falls fzf nicht reagiert: Stelle sicher, dass du Git Bash verwendest (nicht mintty)

#### Troubleshooting

**Problem: "fzf: command not found"**
```bash
scoop install fzf
```

**Problem: "mpv: command not found"**
```bash
scoop install mpv
```

**Problem: Videos starten nicht**
- Stelle sicher, dass yt-dlp installiert ist: `scoop install yt-dlp`
- Prüfe mpv Installation: `mpv --version`
- Für Filemoon-Hoster: Node.js installieren: `scoop install nodejs`

**Problem: Encoding-Fehler bei deutschen Umlauten**
```bash
# In ~/.bashrc hinzufügen:
export LANG=de_DE.UTF-8
export LC_ALL=de_DE.UTF-8
```

**Problem: "Keine Hoster gefunden"**

Wenn du diesen Fehler siehst, wurde die Hoster-Extraktion verbessert für Windows-Kompatibilität:

1. **Mit Debug-Modus starten:**
   ```bash
   aniworld-cli --debug "Anime Name"
   ```

2. **HTML-Datei prüfen:**
   Die Debug-Datei wird gespeichert unter:
   ```
   ~/.local/share/aniworld-cli/debug_episode.html
   ```

3. **GitHub Issue öffnen:**
   Falls das Problem weiterhin besteht, öffne ein Issue auf GitHub mit:
   - Deinem Betriebssystem (Windows/macOS/Linux)
   - Der debug_episode.html Datei
   - Der genauen Fehlermeldung

**Windows-spezifisch:** Das Tool wurde für Windows Git Bash optimiert. Alle `grep -oP` Befehle wurden durch POSIX-kompatible `sed` Alternativen ersetzt.

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
  hoster    - Hoster/Qualität wechseln
  quit      - Beenden
```

Das Menü zeigt auch den aktuellen Hoster an:
```
Cowboy Bebop | S1E5/26 | Hoster: Streamtape
```

### Debug-Modus

Bei Problemen (z.B. "Keine Hoster gefunden") starte mit Debug-Modus:
```bash
aniworld-cli --debug "Anime Name"
# oder
aniworld-cli -d "Anime Name"
```

Der Debug-Modus:
- Zeigt detaillierte Shell-Ausgaben
- Speichert HTML-Dateien in `~/.local/share/aniworld-cli/debug_episode.html`
- Gibt Hoster-Extraktions-Details aus

### Hoster-Auswahl

aniworld-cli wählt automatisch den besten verfügbaren Hoster basierend auf folgender Priorität:
1. **Streamtape** - Meistens die beste Qualität und Zuverlässigkeit
2. **Vidmoly** - Gute Alternative mit hoher Verfügbarkeit
3. **Doodstream** - Fallback-Option
4. **VOE** - Letzte Alternative
5. **Filemoon** - Funktioniert nur mit Node.js (dekodiert obfuszierten JavaScript-Code)

#### Manueller Hoster-Wechsel

Du kannst jederzeit während der Wiedergabe den Hoster wechseln:

1. Wähle **"hoster"** im Post-Episode-Menü
2. Dir werden alle verfügbaren Hoster für die aktuelle Episode angezeigt
3. Wähle einen Hoster aus der Liste
4. Das Video wird mit dem neuen Hoster geladen und abgespielt
5. Das Menü bleibt sichtbar und zeigt den neuen Hoster an

**Anwendungsfälle:**
- Ein Hoster lädt zu langsam → Wechsle zu einem anderen
- Video-Qualität ist schlecht → Probiere einen anderen Hoster
- Hoster ist offline → Wähle eine funktionierende Alternative

Der aktuelle Hoster wird immer im Menü-Prompt angezeigt:
```
One Piece | S1E42/61 | Hoster: Streamtape
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
3. **Auswahl**: Wähle aus den Suchergebnissen mit fzf-Vollbild (zeigt Episodenanzahl)
4. **History-Check**: Falls vorhanden, fzf-Menü zum Fortsetzen oder Neustart
5. **Staffel wählen**: Wähle die gewünschte Staffel (fzf-Vollbild)
6. **Episode wählen**: Wähle die gewünschte Episode (fzf-Vollbild)
7. **Hoster-Auswahl**: Automatische Auswahl des besten Hosters (Streamtape > Vidmoly > Doodstream > VOE)
8. **Streaming**: Video wird in mpv/vlc abgespielt (im Hintergrund, Menü bleibt sichtbar)
9. **Post-Episode-Menü**: Wähle zwischen next, replay, previous, select, hoster oder quit
   - **hoster**: Wechsle zu einem anderen Streaming-Anbieter für bessere Qualität/Geschwindigkeit
10. **Loop**: Zurück zu Schritt 8 für nahtloses Binge-Watching

## Datei-Struktur

```
aniworld-cli/
├── aniworld-cli           # Haupt-Executable
├── lib/
│   ├── scraper.sh        # Web-Scraping-Funktionen (AJAX API, Hoster-Extraktion)
│   ├── player.sh         # Video-Player-Integration (mpv/vlc)
│   ├── history.sh        # Watch-History-Management
│   ├── ui.sh             # UI/UX-Funktionen (fzf-Vollbild-Menüs)
│   └── extract_filemoon.js  # Filemoon Video-URL Dekoder (Node.js)
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
- **Filemoon-Hoster**: Stelle sicher, dass Node.js installiert ist (`node --version`)
  - Ubuntu/Debian: `sudo apt install nodejs`
  - Arch: `sudo pacman -S nodejs`
  - macOS: `brew install node`
  - Windows: `scoop install nodejs`

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
- Video-Qualität ist vom Hoster abhängig (nutze die Hoster-Auswahl um bessere Qualität zu finden)

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
