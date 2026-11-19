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

## Local changes

Two of these files are no longer stock upstream. Both changes are small, are
listed here, and have to be re-applied when the files are replaced by a newer
upstream build:

| File | Change |
|---|---|
| `scripts/modernz.lua` | the single `custom_button` became `custom_button1`..`custom_button3`, so more than one script-defined button can be shown (`script-opts/modernz.conf` uses all three), plus the per-button `_label_off` / `_toggle_property` pair that swaps a button's icon while a property is true, and per-button left/right-click commands. |
| `fonts/modernz-icons.ttf` | three icons added for buttons upstream has no glyph for, plus one ASCII placeholder — see below. |

The font additions are `fluent_anime4k` (a four-point "enhance" sparkle, U+F091),
`fluent_shortcuts` (a keyboard, U+F092) and `fluent_anime4k_off` (the same
sparkle with a diagonal slash, U+F093 — the "shaders are off" state), each with
the `_filled` ligature upstream's naming scheme implies (all three point at the
same outline, since none of the drawings has a filled twin). They are drawn on
the font's own grid: 1024 units per em, 24 units per icon, 2 units of stroke, one
em of advance — the same measurements the bundled icons use.

The slash sits on the diagonal through the sparkle's own centre, not the centre
of the 24-unit box: the star is not centred in its square, and a box-centred line
crosses it off centre. The slash and the star are the same colour, so they merge
where they overlap — that is deliberate, and it is why the smallest of the three
sparkles is missing from the `_off` drawing (the diagonal runs through the corner
it occupies).

The placeholder is `U+0034` (`4`), a blank, zero-advance glyph like the ones
upstream ships for the other letters and digits. This font is a ligature font:
it types `fluent_anime4k` and swaps the whole run for one glyph, and it only
carries the ASCII characters its own names need. `4` was not one of them, so
without the placeholder that name could not be typed at all.

Consequence worth knowing: text rendered in this font shows only what the
ligatures and the fallback font provide. Uppercase letters are absent, so the
renderer falls back to a normal font for them; lowercase letters and the digits
`0 1 3 4 5` are blank and zero-width by design. That is why the button labels in
`script-opts/modernz.conf` are ligature names: a label that is neither a
ligature nor uppercase renders as an empty button, with no error anywhere.

## Rebuilding the font

The patched font is a build artefact of `tools/pack_icons.py` in the repository
(not shipped in the wheel). It draws the three glyphs, adds the
`_filled` ligatures, keeps the `U+0034` placeholder, and skips any icon that is
already there — keyed on the GSUB ligature text, because this font's `post` table
is version 3.0 and carries no glyph names to check. Running it on the shipped
font is a no-op and does not rewrite the file. It needs `fontTools`, which is not
a runtime dependency:

```bash
pip install fonttools
python3 tools/pack_icons.py     # after replacing the ttf with a newer upstream build
```

`tests/test_m13_mpv_pack.py::test_button_labels_are_real_icons` re-reads the
GSUB table and fails on a label that is neither a ligature nor uppercase text.
It `importorskip`s `fontTools`; CI installs it for the test run, and a local
check needs `pip install fonttools` too, or it is skipped rather than run.

Everything else (mpv options, per-user tweaks) belongs in `user-overlay.conf` —
the rest of this directory is replaced on update.
