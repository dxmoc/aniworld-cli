# Third-party files in this directory

The mpv configuration in this directory is bundled so that playback looks the
same on every OS without touching the user's own `~/.config/mpv`. These files
are third-party work, not part of aniworld-cli:

| File | Origin | License |
|---|---|---|
| `scripts/modernz.lua` | [Samillion/ModernZ](https://github.com/Samillion/ModernZ) v0.3.3 | LGPL-2.1 (`plugins/` upstream: GNU Lesser General Public License v2.1) |
| `fonts/modernz-icons.ttf` | Samillion/ModernZ | LGPL-2.1, see the ModernZ repository |
| `shaders/Anime4K_*.glsl` | [bloc97/Anime4K](https://github.com/bloc97/Anime4K) | MIT |

Anime4K is a set of mpv user shaders; the presets in `aniworld_cli/shaders.py`
only reference the files above.

The Windows release additionally ships mpv itself under `mpv/`, with a
`SOURCE.txt` written by the release workflow.

All of these are unmodified upstream files. Local changes belong in
`user-overlay.conf` (mpv options) — this directory is replaced on update.
