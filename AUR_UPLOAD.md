# AUR Upload Anleitung

Diese Anleitung erklärt, wie du die aniworld-cli PKGBUILDs zum Arch User Repository (AUR) hochlädst.

## Voraussetzungen

1. **AUR-Account erstellen:**
   - Gehe zu https://aur.archlinux.org/register
   - Registriere dich mit einer E-Mail-Adresse
   - Bestätige deine E-Mail

2. **SSH-Key hinzufügen:**
   ```bash
   # Generiere SSH-Key (falls nicht vorhanden)
   ssh-keygen -t ed25519 -C "your.email@example.com"

   # Zeige Public Key an
   cat ~/.ssh/id_ed25519.pub
   ```

   - Gehe zu https://aur.archlinux.org/account/
   - Füge den Public Key unter "SSH Public Key" hinzu

3. **Git konfigurieren:**
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

---

## Upload von aniworld-cli

### 1. Repository vorbereiten

```bash
# Clone das leere AUR Repository
git clone ssh://aur@aur.archlinux.org/aniworld-cli.git aur-aniworld-cli
cd aur-aniworld-cli
```

### 2. PKGBUILD kopieren und anpassen

```bash
# Kopiere PKGBUILD
cp ../aniworld-cli/PKGBUILD .

# WICHTIG: Passe die Maintainer-Zeile an
sed -i "s/Your Name <your.email@example.com>/Dein Name <deine.email@example.com>/" PKGBUILD
```

### 3. Release erstellen auf GitHub

Bevor du zu AUR hochlädst, erstelle ein Release auf GitHub:

```bash
cd ../aniworld-cli

# Tag erstellen
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

Dann auf GitHub:
- Gehe zu https://github.com/dxmoc/aniworld-cli/releases
- Klicke "Create a new release"
- Wähle Tag: v1.0.0
- Titel: "Release v1.0.0"
- Beschreibung: Feature-Liste
- Publish release

### 4. SHA256-Checksum berechnen

```bash
# Download das Release-Archiv
curl -L -o aniworld-cli-1.0.0.tar.gz \
  https://github.com/dxmoc/aniworld-cli/archive/refs/tags/v1.0.0.tar.gz

# Berechne Checksum
sha256sum aniworld-cli-1.0.0.tar.gz
```

Aktualisiere im PKGBUILD:
```bash
sha256sums=('HIER_DIE_BERECHNETE_CHECKSUM')
```

### 5. .SRCINFO generieren

```bash
cd aur-aniworld-cli

# Generiere .SRCINFO aus PKGBUILD
makepkg --printsrcinfo > .SRCINFO
```

### 6. Testen

Teste das PKGBUILD lokal:

```bash
# Baue das Paket
makepkg -si

# Teste ob es funktioniert
aniworld-cli --version

# Bereinige
sudo pacman -R aniworld-cli
rm -rf pkg src *.tar.gz
```

### 7. Hochladen zu AUR

```bash
# Füge Dateien hinzu
git add PKGBUILD .SRCINFO

# Commit
git commit -m "Initial commit: aniworld-cli 1.0.0"

# Push zu AUR
git push origin master
```

### 8. Verifizieren

- Gehe zu https://aur.archlinux.org/packages/aniworld-cli
- Prüfe ob das Paket erscheint
- Teste die Installation: `yay -S aniworld-cli`

---

## Upload von aniworld-cli-git

Der Prozess ist ähnlich, aber für die Git-Version:

```bash
# Clone AUR Repository
git clone ssh://aur@aur.archlinux.org/aniworld-cli-git.git aur-aniworld-cli-git
cd aur-aniworld-cli-git

# Kopiere PKGBUILD-git und benenne um
cp ../aniworld-cli/PKGBUILD-git PKGBUILD

# Passe Maintainer an
sed -i "s/Your Name <your.email@example.com>/Dein Name <deine.email@example.com>/" PKGBUILD

# .SRCINFO generieren
makepkg --printsrcinfo > .SRCINFO

# Testen (baut von GitHub main branch)
makepkg -si

# Test
aniworld-cli --version

# Aufräumen
sudo pacman -R aniworld-cli-git
rm -rf pkg src

# Hochladen
git add PKGBUILD .SRCINFO
git commit -m "Initial commit: aniworld-cli-git"
git push origin master
```

---

## Updates veröffentlichen

### Neue Version von aniworld-cli

```bash
cd aur-aniworld-cli

# 1. GitHub Release erstellen (siehe oben)
# 2. pkgver und pkgrel in PKGBUILD aktualisieren

# Beispiel:
pkgver=1.1.0
pkgrel=1

# 3. Neue Checksum berechnen
curl -L -o aniworld-cli-1.1.0.tar.gz \
  https://github.com/dxmoc/aniworld-cli/archive/refs/tags/v1.1.0.tar.gz
sha256sum aniworld-cli-1.1.0.tar.gz

# 4. Checksum in PKGBUILD aktualisieren
# 5. .SRCINFO neu generieren
makepkg --printsrcinfo > .SRCINFO

# 6. Testen
makepkg -si

# 7. Hochladen
git add PKGBUILD .SRCINFO
git commit -m "Update to v1.1.0"
git push origin master
```

### aniworld-cli-git aktualisieren

Für die Git-Version musst du nur `pkgrel` erhöhen, wenn du Änderungen am PKGBUILD selbst machst:

```bash
cd aur-aniworld-cli-git

# pkgrel erhöhen
pkgrel=2

# .SRCINFO neu generieren
makepkg --printsrcinfo > .SRCINFO

# Hochladen
git add PKGBUILD .SRCINFO
git commit -m "Update PKGBUILD dependencies"
git push origin master
```

---

## Wichtige Hinweise

### PKGBUILD Best Practices

1. **Immer .SRCINFO aktualisieren** nach PKGBUILD-Änderungen
2. **Teste lokal** bevor du hochlädst
3. **Versionsnummern** müssen mit GitHub-Releases übereinstimmen
4. **Checksums** sind kritisch - falsche Checksums = fehlgeschlagene Builds

### AUR Etikette

1. **Orphan-Pakete:** Falls ein Paket mit gleichem Namen existiert:
   - Prüfe ob es verwaist (orphaned) ist
   - Kontaktiere den Maintainer bevor du ein ähnliches Paket erstellst

2. **Naming Conventions:**
   - `-git` Suffix für VCS-Pakete (direkt von Git)
   - `-bin` Suffix für pre-compiled binaries
   - Kein Suffix für stable releases

3. **Maintenance:**
   - Antworte auf Kommentare von Nutzern
   - Halte das Paket aktuell
   - Markiere "Out-of-date" flags als behoben nach Updates

### Automatisierung (optional)

Du kannst GitHub Actions verwenden, um automatisch AUR zu aktualisieren:

1. Erstelle `.github/workflows/aur-publish.yml`
2. Bei jedem Release-Tag automatisch:
   - Checksum berechnen
   - PKGBUILD aktualisieren
   - Zu AUR pushen

Beispiel-Workflow: https://github.com/marketplace/actions/aur-publish

---

## Troubleshooting

### "Permission denied (publickey)"

SSH-Key nicht richtig konfiguriert:
```bash
# Prüfe SSH-Verbindung
ssh -T aur@aur.archlinux.org

# Sollte ausgeben: "Hi username! You've successfully authenticated..."
```

Falls nicht:
- Prüfe ob SSH-Key in AUR-Account hinzugefügt wurde
- Prüfe SSH-Agent: `ssh-add -l`

### "ERROR: One or more PGP signatures could not be verified!"

Wenn du PGP-signed sources verwendest, musst du:
```bash
validpgpkeys=('FINGERPRINT_DES_KEYS')
```
im PKGBUILD hinzufügen.

Für aniworld-cli nicht nötig, da wir `sha256sums=('SKIP')` für Git-Version verwenden.

### "ERROR: Integrity checks failed"

Checksums stimmen nicht überein:
```bash
# Lade Source erneut herunter
curl -L -O https://github.com/dxmoc/aniworld-cli/archive/refs/tags/v1.0.0.tar.gz

# Berechne Checksum neu
sha256sum v1.0.0.tar.gz

# Aktualisiere im PKGBUILD
```

---

## Weiterführende Links

- [AUR Submission Guidelines](https://wiki.archlinux.org/title/AUR_submission_guidelines)
- [PKGBUILD Reference](https://wiki.archlinux.org/title/PKGBUILD)
- [Arch Packaging Standards](https://wiki.archlinux.org/title/Arch_package_guidelines)
- [AUR Account Management](https://aur.archlinux.org/account/)

## Support

Bei Fragen:
- AUR Mailing List: https://lists.archlinux.org/mailman3/lists/aur-general.lists.archlinux.org/
- Arch Forums: https://bbs.archlinux.org/
- IRC: #archlinux-aur on Libera.Chat
