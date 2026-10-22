#!/usr/bin/env bash
# Install or update aniworld-cli on Linux:
#   curl -fsSL https://raw.githubusercontent.com/dxmoc/aniworld-cli/main/install.sh | bash
#
# Installs mpv (and Python, if missing) with the system package manager, then
# aniworld-cli from the latest release wheel into its own venv. Run it again to
# update. Uninstall: rm -rf ~/.local/share/aniworld-cli ~/.local/bin/aniworld-cli
set -euo pipefail

REPO="dxmoc/aniworld-cli"
APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/aniworld-cli"
BIN_DIR="$HOME/.local/bin"

say() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
die() { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }

python_ok() {
    command -v python3 >/dev/null 2>&1 &&
        python3 -c 'import sys; sys.exit(sys.version_info < (3, 9))' 2>/dev/null
}

# Package names per manager: python3, the venv module (Debian splits it out), mpv.
packages() {
    local want=()
    python_ok || want+=("$1")
    python_ok && python3 -c 'import ensurepip' 2>/dev/null || { [ -n "$2" ] && want+=("$2"); }
    command -v mpv >/dev/null 2>&1 || want+=(mpv)
    echo "${want[@]}"
}

install_system_packages() {
    local sudo="" pkgs
    [ "$(id -u)" -eq 0 ] || sudo="sudo"
    if command -v apt-get >/dev/null 2>&1; then
        pkgs=$(packages python3 python3-venv)
        [ -z "$pkgs" ] && return
        say "Installing $pkgs (apt)"
        $sudo apt-get update -qq && $sudo apt-get install -y $pkgs
    elif command -v dnf >/dev/null 2>&1; then
        pkgs=$(packages python3 "")
        [ -z "$pkgs" ] && return
        say "Installing $pkgs (dnf)"
        $sudo dnf install -y $pkgs
    elif command -v pacman >/dev/null 2>&1; then
        pkgs=$(packages python "")
        [ -z "$pkgs" ] && return
        say "Installing $pkgs (pacman)"
        $sudo pacman -S --needed --noconfirm $pkgs
    elif command -v zypper >/dev/null 2>&1; then
        pkgs=$(packages python3 "")
        [ -z "$pkgs" ] && return
        say "Installing $pkgs (zypper)"
        $sudo zypper --non-interactive install $pkgs
    else
        pkgs=$(packages python3 "")
        [ -z "$pkgs" ] && return
        die "No supported package manager found. Install these yourself, then run this script again: $pkgs"
    fi
}

main() {
    [ "$(uname -s)" = "Linux" ] || die "This installer is for Linux. See the README for other systems."
    command -v curl >/dev/null 2>&1 || die "curl is required."

    install_system_packages
    python_ok || die "Python 3.9 or newer is required."
    command -v mpv >/dev/null 2>&1 || die "mpv is still missing after the install step."

    # /releases/latest redirects to /releases/tag/<tag>; no API call, no rate limit.
    local tag version wheel
    tag=$(curl -fsSLI -o /dev/null -w '%{url_effective}' "https://github.com/$REPO/releases/latest")
    tag=${tag##*/}
    case "$tag" in v[0-9]*) ;; *) die "Could not find the latest release." ;; esac
    version=${tag#v}
    wheel="https://github.com/$REPO/releases/download/$tag/aniworld_cli-$version-py3-none-any.whl"

    say "Installing aniworld-cli $version into $APP_DIR"
    [ -x "$APP_DIR/venv/bin/python" ] || python3 -m venv "$APP_DIR/venv"
    "$APP_DIR/venv/bin/python" -m pip install --quiet --disable-pip-version-check --upgrade "$wheel"

    mkdir -p "$BIN_DIR"
    ln -sf "$APP_DIR/venv/bin/aniworld-cli" "$BIN_DIR/aniworld-cli"
    say "Done: $("$BIN_DIR/aniworld-cli" --version)"

    case ":$PATH:" in
        *":$BIN_DIR:"*) say "Start it with: aniworld-cli" ;;
        *) say "Add $BIN_DIR to your PATH (e.g. in ~/.profile), then start it with: aniworld-cli" ;;
    esac
}

# Everything runs from main, so a half-downloaded script does nothing.
main "$@"
