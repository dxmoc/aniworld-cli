<h1 align="center">aniworld-cli</h1>

<p align="center">
  Stream anime from <a href="https://aniworld.to">aniworld.to</a> in your terminal, with the look and feel of
  <a href="https://github.com/pystardust/ani-cli">ani-cli</a>.
</p>

<p align="center">
  <a href="https://github.com/dxmoc/aniworld-cli/actions/workflows/tests.yml"><img src="https://github.com/dxmoc/aniworld-cli/actions/workflows/tests.yml/badge.svg" alt="tests"></a>
  <a href="https://github.com/dxmoc/aniworld-cli/releases/latest"><img src="https://img.shields.io/github/v/release/dxmoc/aniworld-cli" alt="release"></a>
  <img src="https://img.shields.io/badge/python-3.9%2B-blue" alt="Python 3.9+">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-GPL--3.0--or--later-green" alt="GPL-3.0-or-later"></a>
</p>

<details>
<summary><b>Demo</b> (click to expand)</summary>
<br>
<p align="center"><img src="docs/demo.gif" alt="aniworld-cli demo" width="800"></p>
</details>

## Features

- **fzf menus like ani-cli**: type to filter, arrows to move, Enter to pick.
  fzf ships with the `iterfzf` dependency, there is nothing extra to install.
- **Series, season (including movies), episode**, then a language menu when an
  episode offers more than one (German dub, German subtitles, English
  subtitles). Your language choice carries over to the next episodes.
  Episodes and movies are listed with their titles, so you can filter by name.
- **After playback**: `next`, `replay`, `previous`, `select`, `quit`, just like ani-cli.
- **Resume**: picking a series again offers to continue with the episode after
  the one you watched last, into the next season when one ends.
- **Watchlist** (`-w`): jump back into a series you watched without searching.
- **Binge mode** (`--auto`): plays the next episode automatically until the season ends.
- **Hoster fallback**: tries VOE, then Vidmoly. Every stream is checked before
  mpv starts, so a hoster that hands out dead (403) segments is skipped instead
  of stalling the player.
- **mpv only**: streaming, no downloads. mpv shows `Series – S01E03 – Episode title` as the title.
- **Bundled mpv + Anime4K**: an isolated mpv config with upscaling shaders ships
  inside the package, so a 720p stream looks sharp without touching your own
  `~/.config/mpv`. Switch language, quality or shader *while watching*
  (`Alt+s`, `Alt+u`, or the A4K button in the on-screen controls).
- **Update hint**: once a day it checks GitHub for a newer release and prints
  the upgrade command (pipx or pip). Offline or rate-limited, it stays quiet.

## Install

### Quick install

**Linux** (installs mpv with your package manager, asks for `sudo`):

```bash
curl -fsSL https://raw.githubusercontent.com/dxmoc/aniworld-cli/main/install.sh | bash
```

**Windows** (PowerShell, no Python needed, mpv is included):

```powershell
irm https://raw.githubusercontent.com/dxmoc/aniworld-cli/main/install.ps1 | iex
```

Run the same command again to update. The Linux script supports apt, dnf,
pacman and zypper and installs into `~/.local/share/aniworld-cli`. The Windows
script unpacks `aniworld-cli-windows.zip` from the latest release (aniworld-cli
with Python and mpv) to `%LOCALAPPDATA%\aniworld-cli` and adds it to your `PATH`.
Windows may warn about an unknown publisher because the exe is not signed.

To uninstall, delete `~/.local/share/aniworld-cli` and `~/.local/bin/aniworld-cli`
on Linux, or `%LOCALAPPDATA%\aniworld-cli` and its `PATH` entry on Windows.

### Manual install

You need **Python 3.9+** and **[mpv](https://mpv.io/)** on your `PATH`.

#### 1. aniworld-cli

With [pipx](https://pipx.pypa.io/) (recommended, keeps it in its own environment):

```bash
pipx install git+https://github.com/dxmoc/aniworld-cli
```

With pip (or install a wheel from the [releases page](https://github.com/dxmoc/aniworld-cli/releases/latest)):

```bash
pip install git+https://github.com/dxmoc/aniworld-cli
```

With Nix (flakes enabled; mpv and fzf come along):

```bash
nix run github:dxmoc/aniworld-cli
```

To update later, install again over the old version (`pipx upgrade` does not
re-fetch installs from git; aniworld-cli is not on PyPI):

```bash
pipx install --force git+https://github.com/dxmoc/aniworld-cli
```

#### 2. mpv

| System | Command |
|---|---|
| Arch / Manjaro | `sudo pacman -S mpv` |
| Debian / Ubuntu / WSL | `sudo apt install mpv` |
| Fedora | `sudo dnf install mpv` |
| Windows (Scoop) | `scoop bucket add extras` then `scoop install mpv` |
| Windows (winget) | `winget install --id shinchiro.mpv` |

After installing on Windows, open a **new** terminal so the updated `PATH`
applies. The winget package does not add mpv to `PATH` by itself: add its folder
(e.g. `C:\Program Files\MPV Player`) or pass `--player "C:\Program Files\MPV Player\mpv.exe"`.
Check with `mpv --version`.

Tested in CI on Linux (Python 3.9 to 3.14) and Windows (3.9 and 3.14, mpv from
Scoop). macOS should work but is untested. In WSL, mpv needs a GUI backend
(WSLg on Windows 11) to open a window.

## Usage

```bash
aniworld-cli                       # asks for a search term
aniworld-cli "frieren"             # search, then pick series, season, episode
aniworld-cli -w                    # pick from series you watched before
aniworld-cli "frieren" --auto      # binge the season
aniworld-cli "frieren" --lang eng-sub
aniworld-cli "frieren" --no-menu --episode 1-3   # straight to S01E03
aniworld-cli -w --no-menu          # continue the most recent series
```

### Keys in the menus

| Key | Action |
|---|---|
| typing | filter the list (fuzzy, like fzf) |
| Up / Down, Ctrl-K / Ctrl-J | move (wraps around) |
| Enter | pick |
| Esc, Ctrl-C | abort (in the menu after playback: quit) |

Menus with a single entry, such as a series with one season, are skipped.

### Options

| Option | Meaning |
|---|---|
| `query` | search term (asked for if missing) |
| `-w`, `--watchlist` | pick from series you watched before instead of searching |
| `--episode S-E` | pick season and episode directly, e.g. `1-3` (`0-1` = first movie) |
| `--no-menu` | no interactive menus, use arguments and defaults only |
| `--auto` | play the next episode automatically until the season ends |
| `--lang LIST` | language priority, e.g. `ger-dub,ger-sub,eng-sub` |
| `--hoster LIST` | hoster priority, comma-separated, e.g. `Vidmoly,VOE` |
| `--player PATH` | path to mpv (default: the bundled mpv on Windows, otherwise from `PATH`) |
| `--mpv-config MODE` | `bundled` (default): shipped config + Anime4K; `user`: leave your own mpv config and shaders alone; or a directory to use instead |
| `--anime4k PRESET` | `auto` (default, from the source height), `off`, `restore`, `gentle`, `a`, `fast`, `b`, `c` |
| `--mpv-args ARGS` | extra mpv arguments, e.g. `--mpv-args "--geometry=1280x720 --mute=yes"` |
| `--no-control` | do not attach to mpv: no in-player menus, no switching, no resume from the menu |
| `--debug` | print the stream URL and headers instead of starting mpv; shows full tracebacks |
| `--version` | print the version |

Language tokens: `ger-dub` (German dub), `ger-sub` (German subtitles),
`eng-sub` (English subtitles). Default order: `ger-dub,ger-sub,eng-sub`.

### Anime4K and the bundled mpv config

By default aniworld-cli starts mpv with `--config-dir` pointing at its **own**
config, so your `~/.config/mpv` is never read or modified. Nothing has to be
installed: mpv loads the shipped `mpv.conf`, the control script and the
Anime4K shaders from a private directory.

The streams are ~720p at ~1.2 Mbit/s, which looks blocky on a large display, so
an upscaling preset is chosen automatically: `a` (Mode A, ~16 % of an RTX 2080
at 24 fps) below 1080p, `restore` at 1080p and above. Pick another one with
`--anime4k`.

On first run the pack is copied out of the package into your data directory,
because a wheel, a Nix store path or a PyInstaller bundle can be read-only:

| OS | Location |
|---|---|
| Linux / BSD | `$XDG_DATA_HOME/aniworld-cli/mpv` (default `~/.local/share/aniworld-cli/mpv`) |
| macOS | `~/Library/Application Support/aniworld-cli/mpv` |
| Windows | `%LOCALAPPDATA%\aniworld-cli\mpv` |

Two files there are yours: `user-overlay.conf` is included from `mpv.conf` and
`script-opts/modernz.conf` configures the on-screen controls. Both are written
once and never overwritten by an update — delete one to get the defaults back.
Updates replace everything else, and the copy is refreshed automatically when
the shipped pack changes.

`--mpv-config user` skips all of this: mpv then uses your own configuration and
Anime4K is disabled, because replacing your shader chain would be rude.
`--mpv-config /some/dir` uses that directory instead. The directory has to
exist — a typo is rejected instead of starting mpv with an empty config dir that
has no on-screen controls — and if it has no `shaders/` of its own the presets
keep working from the bundled chain, which is said once on stderr.

The on-screen controls are Lua plus `script-opts`, with no per-platform code,
but they have only been driven by hand on Linux: CI's Windows run plays five
seconds headless, which exercises the pack and the IPC socket but draws nothing.

### Keys inside the player

| Key | Action |
|---|---|
| `Alt+s` | menu with language and quality (then `1`–`6`) |
| `Alt+l` | language only |
| `Alt+q` | quality only |
| `Alt+u` | Anime4K preset only (`1`–`7`, `Esc` closes) |
| `Alt+k` | all key bindings |
| `Esc` | close the menu |

The shader menu explains what each preset does and marks the one that suits
your stream's resolution. The same menu is on the **A4K** button in the
on-screen controls: left click turns the presets on and off, right click opens
the menu. Beside it, the **K** button lists every key binding and the **Lang**
button opens the language menu. Switching a shader applies instantly; switching
language or quality reloads the stream — the three languages are separate
encodes with burned-in subtitles, so there is no audio track to switch to. The
new stream resumes at the position you were at. A quality you picked yourself is
kept across a language switch; if that encode has no such height (1080p exists
only on some English encodes) the switch uses Auto instead and says so in the
player.

Adding `--no-control` starts mpv on its own, without the IPC socket, the menus
or the shader switching (useful with `--mpv-config user`).


### Environment variables

| Variable | Effect |
|---|---|
| `ANIWORLD_LANG` | language priority, like `--lang` |
| `ANIWORLD_HOSTER` | hoster priority, like `--hoster` |
| `ANIWORLD_STATE_DIR` | where resume and watchlist data is stored |
| `ANIWORLD_BASE_URL` | override the site URL |
| `ANIWORLD_UA` | custom User-Agent |

Resume and watchlist data lives in `state.json` under `%APPDATA%\aniworld-cli`
on Windows and `~/.config/aniworld-cli` (or `$XDG_CONFIG_HOME`) elsewhere.

## Troubleshooting

| Message or symptom | Fix |
|---|---|
| `mpv not found!` | Install mpv (see above) or pass `--player <path>`. |
| `fzf not found!` | Only happens when installed from source without the bundled fzf. Install fzf or use the release wheel. |
| `No hoster returned a playable stream!` | The hosters are down for this episode. Try again later or pick another language with `--lang`. |
| Cloudflare message | The site is blocking automated access. An external [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) service can help (not included). |
| Garbled characters on Windows | UTF-8 is forced automatically; on old consoles `chcp 65001` helps. |
| No mpv window in WSL | WSL needs a GUI backend (WSLg on Windows 11). `--debug` still resolves the URL. |

## Hoster status

aniworld.to changes hosters and their embed pages regularly. Last checked **2026-10-21**:

| Hoster | Status |
|---|---|
| VOE | working |
| Vidmoly | working |
| Doodstream | removed, embed is behind a Cloudflare Turnstile CAPTCHA |
| Filemoon | removed, needs a headless browser |
| Vidoza, SpeedFiles, Streamtape | removed, no longer offered by the site |

VOE and Vidmoly covered every episode in a live survey, so the removed hosters
cost no real coverage. A new hoster is one module in `aniworld_cli/extractors/`,
see the extractor contract in that package's `__init__.py`.

## Development

```bash
git clone https://github.com/dxmoc/aniworld-cli.git
cd aniworld-cli
python -m venv .venv && source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install -e . pytest
python -m pytest -q
```

The tests run offline against saved pages in `tests/fixtures/`. For a live check
without starting mpv: `aniworld-cli "naruto" --no-menu --episode 1-1 --debug`
should print a `master.m3u8` URL.

Code path: `search.py` -> `series.py` / `episode.py` -> `resolve.py` ->
`extractors/<hoster>.py` -> `playback.py` -> `player.py`. The bundled player
environment is materialised by `mpv_pack.py`, driven over mpv's IPC socket by
`mpvctl.py`, and the shader chains are in `shaders.py`; what the controls draw
is `mpv/scripts/aniworld.lua`. Menus live in `cli.py`, all on-screen text in
`i18n.py`.

## Credits and license

aniworld-cli is a derivative work of [ani-cli](https://github.com/pystardust/ani-cli)
by pystardust and contributors (GPL-3.0). Changes from the original: rewritten in
Python, ported to aniworld.to, season/episode/language menus, resume and
watchlist, binge mode, liveness-checked hoster fallback.

Licensed under the **GNU GPL v3.0 or later**, see [LICENSE](LICENSE).
Copyright © 2026 dxmoc.

This is a client-side access tool and hosts no content. You are responsible for
using it lawfully.
