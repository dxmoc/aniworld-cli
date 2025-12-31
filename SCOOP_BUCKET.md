# Scoop Bucket Setup

Diese Anleitung erklärt, wie du das aniworld-cli Scoop Bucket einrichtest und verwaltest.

## Was ist ein Scoop Bucket?

Ein Scoop Bucket ist ein Git-Repository, das Manifest-Dateien (JSON) für Scoop-Pakete enthält. Nutzer können dein Bucket hinzufügen und dann deine Software installieren.

---

## Bucket-Struktur

Das Repository sollte diese Struktur haben:

```
aniworld-cli/
├── bucket/
│   └── aniworld-cli.json    # Scoop Manifest
├── README.md
└── SCOOP_BUCKET.md (diese Datei)
```

Das `bucket/` Verzeichnis ist bereits in diesem Repository vorhanden.

---

## Manifest-Datei

Die Manifest-Datei `bucket/aniworld-cli.json` definiert:

- **version**: Aktuelle Version
- **url**: Download-URL (GitHub Archive)
- **hash**: SHA256 Checksum
- **bin**: Ausführbare Datei
- **depends**: Abhängigkeiten
- **suggest**: Empfohlene Pakete

### Hash berechnen

Bei jedem Update musst du den Hash neu berechnen:

```powershell
# Download das Archive
curl -L -o aniworld-cli.zip https://github.com/dxmoc/aniworld-cli/archive/refs/heads/main.zip

# Berechne SHA256
(Get-FileHash aniworld-cli.zip -Algorithm SHA256).Hash.ToLower()
```

Oder in Git Bash:
```bash
curl -L -o aniworld-cli.zip https://github.com/dxmoc/aniworld-cli/archive/refs/heads/main.zip
sha256sum aniworld-cli.zip
```

Aktualisiere den `hash` in `bucket/aniworld-cli.json`:
```json
"hash": "HIER_DEN_BERECHNETEN_HASH"
```

---

## Bucket veröffentlichen

### Option 1: Eigenes Bucket (Empfohlen für Beginn)

Du kannst dein eigenes Bucket hosten:

```bash
# Nutzer fügen dein Bucket hinzu
scoop bucket add aniworld https://github.com/dxmoc/aniworld-cli.git

# Dann installieren sie dein Paket
scoop install aniworld/aniworld-cli
```

**Vorteile:**
- Volle Kontrolle
- Keine Review-Prozesse
- Schnelle Updates

**Nachteile:**
- Weniger Sichtbarkeit
- Nutzer müssen das Bucket manuell hinzufügen

### Option 2: Pull Request an extras Bucket

Das offizielle "extras" Bucket hat mehr Nutzer:

1. **Fork das extras Bucket:**
   ```bash
   # Gehe zu: https://github.com/ScoopInstaller/Extras
   # Klicke "Fork"
   ```

2. **Clone deinen Fork:**
   ```bash
   git clone https://github.com/DEIN_USERNAME/Extras.git
   cd Extras
   ```

3. **Kopiere dein Manifest:**
   ```bash
   cp /path/to/aniworld-cli/bucket/aniworld-cli.json bucket/
   ```

4. **Teste lokal:**
   ```bash
   # Füge deinen Fork als Bucket hinzu
   scoop bucket add extras-test https://github.com/DEIN_USERNAME/Extras.git

   # Installiere zum Testen
   scoop install extras-test/aniworld-cli

   # Teste
   aniworld-cli --version
   ```

5. **Erstelle Pull Request:**
   ```bash
   git add bucket/aniworld-cli.json
   git commit -m "Add aniworld-cli v1.0.0"
   git push origin master
   ```

   Dann auf GitHub:
   - Gehe zu deinem Fork
   - Klicke "Pull Request"
   - Base: `ScoopInstaller/Extras:master`
   - Head: `DEIN_USERNAME/Extras:master`
   - Beschreibe dein Paket
   - Submit PR

**Vorteile:**
- Mehr Sichtbarkeit
- Nutzer haben "extras" oft schon installiert
- Teil des offiziellen Ökosystems

**Nachteile:**
- Review-Prozess dauert Zeit
- Muss Guidelines folgen
- Weniger Kontrolle über Updates

---

## Updates veröffentlichen

### Eigenes Bucket

Bei jedem Release:

1. **Erstelle GitHub Release:**
   ```bash
   git tag -a v1.1.0 -m "Release v1.1.0"
   git push origin v1.1.0
   ```

2. **Berechne neuen Hash:**
   ```bash
   curl -L -o aniworld-cli.zip \
     https://github.com/dxmoc/aniworld-cli/archive/refs/heads/main.zip
   sha256sum aniworld-cli.zip
   ```

3. **Aktualisiere Manifest:**
   ```json
   {
     "version": "1.1.0",
     "hash": "NEUER_HASH",
     ...
   }
   ```

4. **Committe und pushe:**
   ```bash
   git add bucket/aniworld-cli.json
   git commit -m "Update aniworld-cli to v1.1.0"
   git push origin main
   ```

5. **Nutzer aktualisieren:**
   ```bash
   scoop update
   scoop update aniworld-cli
   ```

### extras Bucket

Erstelle einen Pull Request mit dem aktualisierten Manifest für jede neue Version.

---

## Auto-Update (Fortgeschritten)

Scoop unterstützt Auto-Update im Manifest:

```json
{
  "checkver": {
    "url": "https://github.com/dxmoc/aniworld-cli/releases/latest",
    "regex": "tag/v([\\d.]+)"
  },
  "autoupdate": {
    "url": "https://github.com/dxmoc/aniworld-cli/archive/refs/tags/v$version.tar.gz"
  }
}
```

Mit dieser Konfiguration kann Scoop automatisch neue Versionen erkennen.

Testen:
```bash
# Prüfe auf neue Version
scoop checkver aniworld-cli

# Update mit automatischer Hash-Berechnung
scoop update aniworld-cli
```

---

## Scoop Guidelines (für extras PR)

Falls du einen PR an extras sendest, beachte:

### Naming

- Package name sollte lowercase sein: `aniworld-cli`
- Keine Versionsnummern im Namen
- Binaries ohne `.exe` Extension im `bin` Feld

### Manifest-Qualität

1. **Alle Felder ausgefüllt:**
   - `description`, `homepage`, `license`
   - `url`, `hash`, `version`

2. **Dependencies korrekt:**
   - Nur Scoop-Pakete als `depends`
   - Optionale als `suggest`

3. **Korrekte Extraktion:**
   - `extract_dir` wenn nötig
   - `bin` zeigt auf richtige Datei

4. **Funktionierende URLs:**
   - URLs müssen erreichbar sein
   - Hash muss übereinstimmen

### Testing vor PR

```bash
# Manifest validieren
scoop checkver aniworld-cli --app ./bucket/aniworld-cli.json

# Installation testen
scoop install ./bucket/aniworld-cli.json

# Funktionalität testen
aniworld-cli --version
aniworld-cli --help

# Deinstallation testen
scoop uninstall aniworld-cli
```

---

## GitHub Actions (Optional)

Automatisiere Updates mit GitHub Actions:

Erstelle `.github/workflows/scoop-update.yml`:

```yaml
name: Update Scoop Manifest

on:
  release:
    types: [published]

jobs:
  update-manifest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Update manifest version
        run: |
          VERSION="${{ github.event.release.tag_name }}"
          VERSION="${VERSION#v}"

          # Download archive
          curl -L -o archive.zip \
            "https://github.com/${{ github.repository }}/archive/refs/tags/${{ github.event.release.tag_name }}.zip"

          # Calculate hash
          HASH=$(sha256sum archive.zip | cut -d' ' -f1)

          # Update manifest
          jq --arg ver "$VERSION" \
             --arg hash "$HASH" \
             '.version = $ver | .hash = $hash' \
             bucket/aniworld-cli.json > tmp.json
          mv tmp.json bucket/aniworld-cli.json

      - name: Commit changes
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add bucket/aniworld-cli.json
          git commit -m "Update to v${{ github.event.release.tag_name }}"
          git push
```

Dies aktualisiert automatisch das Manifest bei jedem GitHub Release.

---

## Nutzung für User

Nach dem Setup können Nutzer installieren:

```bash
# Bucket hinzufügen (nur einmal)
scoop bucket add aniworld https://github.com/dxmoc/aniworld-cli.git

# aniworld-cli installieren
scoop install aniworld/aniworld-cli

# Oder wenn im extras Bucket:
scoop bucket add extras
scoop install aniworld-cli
```

---

## Troubleshooting

### "Could not find manifest"

- Prüfe ob `bucket/aniworld-cli.json` existiert
- Prüfe Schreibweise: `scoop install aniworld/aniworld-cli`

### "Hash check failed"

- Hash stimmt nicht mit Download überein
- Berechne Hash neu und aktualisiere Manifest

### "App isn't available"

- URL ist nicht erreichbar
- GitHub Release existiert nicht
- Prüfe `url` im Manifest

### "Dependencies not found"

- Dependencies müssen in Scoop verfügbar sein
- Prüfe: `scoop search DEPENDENCY`

---

## Weiterführende Links

- [Scoop Documentation](https://scoop.sh/)
- [Manifest Reference](https://github.com/ScoopInstaller/Scoop/wiki/App-Manifests)
- [Contributing Guide](https://github.com/ScoopInstaller/Scoop/blob/master/.github/CONTRIBUTING.md)
- [Extras Bucket](https://github.com/ScoopInstaller/Extras)

---

## Support

Bei Fragen:
- [Scoop GitHub Discussions](https://github.com/ScoopInstaller/Scoop/discussions)
- [Scoop Discord](https://discord.gg/s9yRQHt)
