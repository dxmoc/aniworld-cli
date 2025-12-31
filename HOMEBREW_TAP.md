# Homebrew Tap Setup

Diese Anleitung erklärt, wie du ein Homebrew Tap für aniworld-cli erstellst und verwaltest.

## Was ist ein Homebrew Tap?

Ein "Tap" ist ein Git-Repository, das Homebrew Formulas enthält. Es ermöglicht Nutzern, deine Software mit `brew install` zu installieren.

---

## Tap-Struktur

Ein Tap-Repository sollte diese Struktur haben:

```
homebrew-aniworld-cli/    (oder nur: aniworld-cli)
├── Formula/
│   └── aniworld-cli.rb   # Homebrew Formula
└── README.md
```

**Wichtig:** Homebrew erwartet spezielle Repository-Namen:
- Format: `homebrew-<name>`
- Beispiel: `homebrew-aniworld-cli`
- Alternativ: Nutze das Hauptrepository mit `Formula/` Verzeichnis

---

## Option 1: Separates Tap-Repository (Empfohlen)

### 1. Neues Repository erstellen

Auf GitHub:
1. Gehe zu https://github.com/new
2. **Repository Name:** `homebrew-aniworld-cli`
3. **Description:** "Homebrew tap for aniworld-cli"
4. **Public** (muss öffentlich sein)
5. Create repository

### 2. Repository aufsetzen

```bash
# Clone das neue Repository
git clone https://github.com/dxmoc/homebrew-aniworld-cli.git
cd homebrew-aniworld-cli

# Erstelle Formula-Verzeichnis
mkdir Formula

# Kopiere die Formula
cp /path/to/aniworld-cli/Formula/aniworld-cli.rb Formula/

# README erstellen
cat > README.md << 'EOF'
# Homebrew Tap for aniworld-cli

## Installation

```bash
brew tap dxmoc/aniworld-cli
brew install aniworld-cli
```

## More Information

Visit [aniworld-cli on GitHub](https://github.com/dxmoc/aniworld-cli)
EOF

# Committen und pushen
git add .
git commit -m "Initial commit: aniworld-cli formula"
git push origin main
```

### 3. Nutzer-Installation

Nutzer können jetzt installieren:

```bash
# Tap hinzufügen
brew tap dxmoc/aniworld-cli

# aniworld-cli installieren
brew install aniworld-cli
```

---

## Option 2: Formula im Hauptrepository

Alternativ kannst du die Formula im Hauptrepository behalten:

```bash
cd aniworld-cli

# Formula/ Verzeichnis ist bereits vorhanden
# Nutzer installieren mit:
brew tap dxmoc/aniworld-cli https://github.com/dxmoc/aniworld-cli.git
brew install aniworld-cli
```

**Vorteil:** Alles in einem Repository
**Nachteil:** Nutzer laden das gesamte Repository beim tap

---

## Formula aktualisieren

### Neue Version veröffentlichen

1. **Erstelle GitHub Release:**
   ```bash
   cd aniworld-cli
   git tag -a v1.1.0 -m "Release v1.1.0"
   git push origin v1.1.0
   ```

2. **Berechne SHA256:**
   ```bash
   curl -L -o aniworld-cli-1.1.0.tar.gz \
     https://github.com/dxmoc/aniworld-cli/archive/refs/tags/v1.1.0.tar.gz
   sha256sum aniworld-cli-1.1.0.tar.gz
   ```

3. **Aktualisiere Formula:**

   In `Formula/aniworld-cli.rb`:
   ```ruby
   class AniworldCli < Formula
     desc "CLI tool to browse and watch anime from aniworld.to"
     homepage "https://github.com/dxmoc/aniworld-cli"
     url "https://github.com/dxmoc/aniworld-cli/archive/refs/tags/v1.1.0.tar.gz"
     version "1.1.0"
     sha256 "HIER_DEN_BERECHNETEN_HASH"
     license "GPL-3.0"
     ...
   end
   ```

4. **Teste lokal:**
   ```bash
   # Audit (prüft auf Fehler)
   brew audit --strict Formula/aniworld-cli.rb

   # Installation testen
   brew install --build-from-source Formula/aniworld-cli.rb

   # Funktionalität testen
   aniworld-cli --version

   # Aufräumen
   brew uninstall aniworld-cli
   ```

5. **Committe und pushe:**
   ```bash
   git add Formula/aniworld-cli.rb
   git commit -m "Bump aniworld-cli to v1.1.0"
   git push origin main
   ```

6. **Nutzer aktualisieren:**
   ```bash
   brew update
   brew upgrade aniworld-cli
   ```

---

## Formula Best Practices

### Pfade anpassen

aniworld-cli verwendet `lib/` Dateien. In der Formula müssen wir Pfade anpassen:

```ruby
def install
  bin.install "aniworld-cli"

  # Installiere lib Dateien nach libexec
  libexec.install Dir["lib/*"]

  # Passe LIB_DIR im Script an
  inreplace bin/"aniworld-cli",
    'LIB_DIR="${SCRIPT_DIR}/lib"',
    "LIB_DIR=\"#{libexec}\""

  doc.install "README.md"
end
```

Dies sorgt dafür, dass das Script die lib-Dateien findet, auch wenn sie unter `libexec` installiert sind.

### Dependencies

```ruby
depends_on "bash"
depends_on "curl"
depends_on "fzf"
depends_on "grep"
depends_on "node"
depends_on "sed"
```

**Wichtig:**
- Nur echte Dependencies, keine optionalen
- Optionale in `caveats` erwähnen

### Caveats

Zeige wichtige Hinweise nach Installation:

```ruby
def caveats
  <<~EOS
    aniworld-cli requires a video player for playback.
    Install mpv (recommended):
      brew install mpv

    Optional dependencies for enhanced functionality:
      brew install yt-dlp ffmpeg aria2
  EOS
end
```

### Tests

Füge einen einfachen Test hinzu:

```ruby
test do
  assert_match "aniworld-cli", shell_output("#{bin}/aniworld-cli --help", 0)
end
```

---

## homebrew-core (Fortgeschritten)

Für maximale Reichweite kannst du einen PR an homebrew-core senden.

### Voraussetzungen

- Mindestens 75 GitHub Stars
- Stabile, etablierte Software
- Keine kommerzielle/proprietäre Software

### Prozess

1. **Fork homebrew-core:**
   ```bash
   # Fork auf GitHub: https://github.com/Homebrew/homebrew-core

   # Clone deinen Fork
   git clone https://github.com/DEIN_USERNAME/homebrew-core.git
   cd homebrew-core
   ```

2. **Erstelle Branch:**
   ```bash
   git checkout -b aniworld-cli
   ```

3. **Erstelle Formula:**
   ```bash
   # Homebrew stellt ein Tool bereit
   brew create https://github.com/dxmoc/aniworld-cli/archive/refs/tags/v1.0.0.tar.gz
   ```

   Dies erstellt automatisch `Formula/aniworld-cli.rb` mit Template.

4. **Passe Formula an:**
   - Füge Dependencies hinzu
   - Implementiere `install` Methode
   - Füge `test` hinzu
   - Füge `caveats` hinzu (wenn nötig)

5. **Teste gründlich:**
   ```bash
   # Audit
   brew audit --strict --online aniworld-cli

   # Installieren und testen
   brew install --build-from-source aniworld-cli
   brew test aniworld-cli
   brew linkage aniworld-cli

   # Aufräumen
   brew uninstall aniworld-cli
   ```

6. **Erstelle Pull Request:**
   ```bash
   git add Formula/aniworld-cli.rb
   git commit -m "aniworld-cli 1.0.0 (new formula)"
   git push origin aniworld-cli
   ```

   Auf GitHub:
   - Erstelle PR zu `Homebrew/homebrew-core:master`
   - Folge der PR-Vorlage
   - Warte auf Review

**Hinweis:** homebrew-core hat strenge Richtlinien. Dein PR wird geprüft und möglicherweise abgelehnt. Ein eigenes Tap ist für Beginn besser.

---

## GitHub Actions für Auto-Update

Automatisiere Formula-Updates bei Releases:

Erstelle `.github/workflows/homebrew-update.yml`:

```yaml
name: Update Homebrew Formula

on:
  release:
    types: [published]

jobs:
  update-formula:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          repository: dxmoc/homebrew-aniworld-cli
          token: ${{ secrets.TAP_GITHUB_TOKEN }}

      - name: Update Formula
        run: |
          VERSION="${{ github.event.release.tag_name }}"
          VERSION="${VERSION#v}"

          # Download tarball
          curl -L -o archive.tar.gz \
            "https://github.com/dxmoc/aniworld-cli/archive/refs/tags/${{ github.event.release.tag_name }}.tar.gz"

          # Calculate SHA256
          SHA256=$(sha256sum archive.tar.gz | cut -d' ' -f1)

          # Update Formula
          sed -i "s|version \".*\"|version \"$VERSION\"|" Formula/aniworld-cli.rb
          sed -i "s|url \".*\"|url \"https://github.com/dxmoc/aniworld-cli/archive/refs/tags/v$VERSION.tar.gz\"|" Formula/aniworld-cli.rb
          sed -i "s|sha256 \".*\"|sha256 \"$SHA256\"|" Formula/aniworld-cli.rb

      - name: Commit and Push
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add Formula/aniworld-cli.rb
          git commit -m "aniworld-cli: update to ${{ github.event.release.tag_name }}"
          git push
```

**Wichtig:** Erstelle ein Personal Access Token mit `repo` Scope und füge es als Secret `TAP_GITHUB_TOKEN` hinzu.

---

## Troubleshooting

### "Error: Invalid formula"

```bash
# Prüfe Syntax
brew audit Formula/aniworld-cli.rb

# Häufige Fehler:
# - Ruby-Syntax-Fehler
# - Falsche Einrückung
# - Fehlende end-Statements
```

### "SHA256 mismatch"

```bash
# Hash neu berechnen
curl -L -o test.tar.gz https://github.com/dxmoc/aniworld-cli/archive/refs/tags/v1.0.0.tar.gz
shasum -a 256 test.tar.gz
```

### "Command not found nach Installation"

Prüfe `bin.install` in Formula:
```ruby
bin.install "aniworld-cli"  # Dateiname muss stimmen
```

### "lib-Dateien nicht gefunden"

Prüfe `inreplace` in Formula:
```ruby
inreplace bin/"aniworld-cli",
  'LIB_DIR="${SCRIPT_DIR}/lib"',
  "LIB_DIR=\"#{libexec}\""
```

---

## Homebrew Guidelines

### Naming

- Class Name: `CamelCase` (z.B. `AniworldCli`)
- Dateiname: `lowercase-with-dashes.rb` (z.B. `aniworld-cli.rb`)
- Keine Versionsnummern im Namen

### Formula-Struktur

```ruby
class AniworldCli < Formula
  desc "Short description (max 80 chars)"
  homepage "https://..."
  url "https://..."
  version "1.0.0"
  sha256 "..."
  license "GPL-3.0"  # oder "MIT", "Apache-2.0", etc.

  depends_on "dependency1"
  depends_on "dependency2"

  def install
    # Installation code
  end

  def caveats
    # Post-install message
  end

  test do
    # Test code
  end
end
```

### Testen vor Release

```bash
# 1. Audit (prüft Style, Errors)
brew audit --strict Formula/aniworld-cli.rb

# 2. Style check
brew style Formula/aniworld-cli.rb

# 3. Installation von Source
brew install --build-from-source Formula/aniworld-cli.rb

# 4. Test ausführen
brew test aniworld-cli

# 5. Linkage prüfen (optional)
brew linkage --test aniworld-cli

# 6. Deinstallation testen
brew uninstall aniworld-cli
```

---

## Nutzung für User

Nach Setup:

```bash
# Tap hinzufügen (nur einmal)
brew tap dxmoc/aniworld-cli

# Installieren
brew install aniworld-cli

# Testen
aniworld-cli --version

# Aktualisieren
brew update
brew upgrade aniworld-cli

# Deinstallieren
brew uninstall aniworld-cli
brew untap dxmoc/aniworld-cli
```

---

## Weiterführende Links

- [Homebrew Formula Cookbook](https://docs.brew.sh/Formula-Cookbook)
- [Homebrew Tap Documentation](https://docs.brew.sh/Taps)
- [Acceptable Formulas](https://docs.brew.sh/Acceptable-Formulae)
- [How to Create a Tap](https://docs.brew.sh/How-to-Create-and-Maintain-a-Tap)

---

## Support

Bei Fragen:
- [Homebrew Discussions](https://github.com/Homebrew/brew/discussions)
- [Homebrew Discourse](https://discourse.brew.sh/)
