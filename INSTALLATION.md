# Installation Guide

Ausführliche Installationsanleitung für aniworld-cli auf verschiedenen Plattformen.

## Inhaltsverzeichnis

- [Package Manager Installation](#package-manager-installation)
  - [Arch Linux (AUR)](#arch-linux-aur)
  - [Windows (Scoop)](#windows-scoop)
  - [macOS/Linux (Homebrew)](#macoslinux-homebrew)
- [Manuelle Installation](#manuelle-installation)
  - [Linux](#linux)
  - [macOS](#macos)
  - [Windows](#windows)
- [Dependencies](#dependencies)
- [Troubleshooting](#troubleshooting)

---

## Package Manager Installation

Die einfachste Methode, aniworld-cli zu installieren, ist über einen Package Manager. Dies kümmert sich automatisch um Dependencies und Updates.

### Arch Linux (AUR)

aniworld-cli ist im Arch User Repository (AUR) verfügbar.

#### Mit einem AUR Helper (empfohlen)

**yay:**
```bash
yay -S aniworld-cli
```

**paru:**
```bash
paru -S aniworld-cli
```

**Development Version (Git):**
```bash
yay -S aniworld-cli-git
```

Die Git-Version installiert direkt vom main branch und ist immer auf dem neuesten Stand.

#### Manuelle AUR Installation

Wenn du keinen AUR Helper verwendest:

```bash
# Clone das AUR Repository
git clone https://aur.archlinux.org/aniworld-cli.git
cd aniworld-cli

# Baue das Paket
makepkg -si
```

#### Was wird installiert?

- Binary: `/usr/bin/aniworld-cli`
- Libraries: `/usr/share/aniworld-cli/lib/`
- Dokumentation: `/usr/share/doc/aniworld-cli/`

#### Updates

Mit yay:
```bash
yay -Syu
```

Für Git-Versionen:
```bash
yay -Syu --devel
```

---

### Windows (Scoop)

Scoop ist ein Kommandozeilen-Package Manager für Windows.

#### Voraussetzungen

1. **Scoop installieren** (falls noch nicht installiert):

   Öffne PowerShell und führe aus:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression
   ```

2. **Git Bash installieren:**
   ```powershell
   scoop install git
   ```

#### Installation

```bash
# Füge das aniworld-cli bucket hinzu
scoop bucket add aniworld https://github.com/dxmoc/aniworld-cli.git

# Installiere aniworld-cli und Dependencies
scoop install aniworld/aniworld-cli
scoop install fzf mpv yt-dlp nodejs aria2 jq
```

#### Konfiguration für Git Bash

1. Öffne Windows Terminal
2. Gehe zu Einstellungen → Profile → Neues Profil
3. Konfiguriere:
   - **Name:** Git Bash
   - **Befehlszeile:** `C:\Program Files\Git\bin\bash.exe -i -l`
   - **Startverzeichnis:** `%USERPROFILE%`
4. Speichern und Git Bash als Standard setzen (optional)

#### Updates

```bash
scoop update aniworld-cli
```

Alle Scoop-Pakete aktualisieren:
```bash
scoop update *
```

---

### macOS/Linux (Homebrew)

Homebrew ist ein Package Manager für macOS und Linux.

#### Voraussetzungen

**macOS:** Homebrew ist normalerweise vorinstalliert. Falls nicht:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**Linux:** Siehe [Homebrew Linux Installation](https://docs.brew.sh/Homebrew-on-Linux)

#### Installation

```bash
# Füge das aniworld-cli tap hinzu
brew tap dxmoc/aniworld-cli https://github.com/dxmoc/aniworld-cli.git

# Installiere aniworld-cli
brew install aniworld-cli

# Installiere empfohlene Dependencies
brew install mpv yt-dlp ffmpeg aria2
```

#### Was wird installiert?

- Binary: `$(brew --prefix)/bin/aniworld-cli`
- Libraries: `$(brew --prefix)/libexec/aniworld-cli/`

#### Updates

```bash
brew update
brew upgrade aniworld-cli
```

---

## Manuelle Installation

Falls du keinen Package Manager verwenden möchtest oder kannst.

### Linux

#### 1. Dependencies installieren

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install curl grep sed fzf mpv yt-dlp nodejs jq git
```

**Arch Linux:**
```bash
sudo pacman -S curl grep sed fzf mpv yt-dlp nodejs jq git
```

**Fedora:**
```bash
sudo dnf install curl grep sed fzf mpv yt-dlp nodejs jq git
```

#### 2. Repository klonen

```bash
git clone https://github.com/dxmoc/aniworld-cli.git
cd aniworld-cli
```

#### 3. Installation

**Option A: Install-Script (empfohlen)**
```bash
chmod +x install.sh
sudo ./install.sh
```

**Option B: Manueller Symlink**
```bash
sudo ln -s "$(pwd)/aniworld-cli" /usr/local/bin/aniworld-cli
chmod +x aniworld-cli
```

#### 4. Testen

```bash
aniworld-cli --version
```

---

### macOS

#### 1. Dependencies installieren

```bash
brew install curl grep gnu-sed fzf mpv yt-dlp node jq git
```

**Wichtig:** macOS verwendet BSD sed, du brauchst GNU sed:
```bash
export PATH="/usr/local/opt/gnu-sed/libexec/gnubin:$PATH"
```

Füge das zu deiner `~/.zshrc` oder `~/.bashrc` hinzu für permanente Verwendung.

#### 2. Repository klonen

```bash
git clone https://github.com/dxmoc/aniworld-cli.git
cd aniworld-cli
```

#### 3. Installation

```bash
chmod +x install.sh
sudo ./install.sh
```

Oder manuell:
```bash
sudo cp aniworld-cli "$(brew --prefix)/bin/"
chmod +x "$(brew --prefix)/bin/aniworld-cli"
```

---

### Windows

#### 1. Scoop installieren (falls nicht vorhanden)

Siehe [Windows (Scoop)](#windows-scoop) oben.

#### 2. Dependencies installieren

```bash
scoop bucket add extras
scoop install fzf mpv yt-dlp nodejs aria2 jq git
```

#### 3. Repository klonen

Im **Git Bash Terminal**:
```bash
cd ~
git clone https://github.com/dxmoc/aniworld-cli.git
cd aniworld-cli
```

#### 4. Zum PATH hinzufügen

```bash
echo 'export PATH="$HOME/aniworld-cli:$PATH"' >> ~/.bashrc
source ~/.bashrc
chmod +x aniworld-cli
```

#### 5. Testen

```bash
aniworld-cli --version
```

---

## Dependencies

### Erforderliche Dependencies

| Tool | Zweck | Installation |
|------|-------|--------------|
| `bash` | Shell | Normalerweise vorinstalliert |
| `curl` | HTTP Requests | `apt install curl` / `brew install curl` |
| `grep` | Text-Verarbeitung | Normalerweise vorinstalliert |
| `sed` | Text-Verarbeitung | `apt install sed` / `brew install gnu-sed` |
| `fzf` | Interaktive Auswahl | `apt install fzf` / `brew install fzf` |
| `nodejs` | Filemoon-Extractor | `apt install nodejs` / `brew install node` |

### Empfohlene Dependencies

| Tool | Zweck | Installation |
|------|-------|--------------|
| `mpv` | Video-Player (primär) | `apt install mpv` / `brew install mpv` |
| `yt-dlp` | Video-Extraktion | `apt install yt-dlp` / `brew install yt-dlp` |
| `jq` | JSON-Parsing | `apt install jq` / `brew install jq` |

### Optionale Dependencies

| Tool | Zweck | Installation |
|------|-------|--------------|
| `vlc` | Alternative zu mpv | `apt install vlc` / `brew install vlc` |
| `aria2` | Download-Support | `apt install aria2` / `brew install aria2` |
| `ffmpeg` | Video-Processing | `apt install ffmpeg` / `brew install ffmpeg` |

---

## Troubleshooting

### "Command not found: aniworld-cli"

**Linux/macOS:**
```bash
# Prüfe ob Symlink existiert
ls -la /usr/local/bin/aniworld-cli

# Falls nicht, erstelle ihn
sudo ln -s "$(pwd)/aniworld-cli" /usr/local/bin/aniworld-cli
```

**Windows:**
```bash
# Prüfe PATH
echo $PATH | grep aniworld-cli

# Füge zum PATH hinzu (falls nicht vorhanden)
echo 'export PATH="$HOME/aniworld-cli:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### "fzf: command not found"

Installiere fzf:
```bash
# Ubuntu/Debian
sudo apt install fzf

# Arch Linux
sudo pacman -S fzf

# macOS
brew install fzf

# Windows (Git Bash)
scoop install fzf
```

### "mpv: command not found"

Installiere mpv:
```bash
# Ubuntu/Debian
sudo apt install mpv

# Arch Linux
sudo pacman -S mpv

# macOS
brew install mpv

# Windows (Git Bash)
scoop install mpv
```

### Node.js ist erforderlich für Filemoon

Installiere Node.js:
```bash
# Ubuntu/Debian
sudo apt install nodejs

# Arch Linux
sudo pacman -S nodejs

# macOS
brew install node

# Windows (Git Bash)
scoop install nodejs
```

### Permission denied (macOS/Linux)

```bash
chmod +x aniworld-cli
```

### Encoding-Fehler bei deutschen Umlauten (Windows)

Füge zu `~/.bashrc` hinzu:
```bash
export LANG=de_DE.UTF-8
export LC_ALL=de_DE.UTF-8
```

Dann:
```bash
source ~/.bashrc
```

---

## Deinstallation

### Arch Linux (AUR)

```bash
yay -R aniworld-cli
# oder
sudo pacman -R aniworld-cli
```

### Windows (Scoop)

```bash
scoop uninstall aniworld-cli
scoop bucket rm aniworld
```

### macOS/Linux (Homebrew)

```bash
brew uninstall aniworld-cli
brew untap dxmoc/aniworld-cli
```

### Manuelle Installation

```bash
cd aniworld-cli
sudo ./uninstall.sh
```

Oder manuell:
```bash
sudo rm /usr/local/bin/aniworld-cli
rm -rf ~/.local/share/aniworld-cli
```

---

## Weiterführende Informationen

- [README.md](README.md) - Hauptdokumentation
- [GitHub Repository](https://github.com/dxmoc/aniworld-cli)
- [Issue Tracker](https://github.com/dxmoc/aniworld-cli/issues)

## Support

Falls du Probleme hast:

1. Prüfe [Troubleshooting](#troubleshooting)
2. Suche in den [GitHub Issues](https://github.com/dxmoc/aniworld-cli/issues)
3. Öffne ein neues Issue mit detaillierter Beschreibung

Erforderliche Informationen für Bug Reports:
- Betriebssystem und Version
- Installationsmethode
- Fehlermeldung (komplett)
- Output von `aniworld-cli --debug`
