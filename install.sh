#!/usr/bin/env bash
# install.sh - Installation script for aniworld-cli
# Installs dependencies and creates symlink to /usr/local/bin

set -e

# Colors
BLUE='\033[1;34m'
GREEN='\033[1;32m'
RED='\033[1;31m'
YELLOW='\033[1;33m'
RESET='\033[0m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/usr/local/bin"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/aniworld-cli"

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BLUE}║${RESET}  aniworld-cli Installer                              ${BLUE}║${RESET}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${RESET}"
echo ""

# Check if running as root for system-wide installation
if [ "$EUID" -ne 0 ] && [ -w "$INSTALL_DIR" ] 2>/dev/null; then
    echo -e "${YELLOW}Note: Not running as root. System-wide installation may fail.${RESET}"
    echo -e "${YELLOW}Consider running with: sudo ./install.sh${RESET}"
    echo ""
fi

# Detect OS
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        OS_LIKE=$ID_LIKE
    elif command -v lsb_release &>/dev/null; then
        OS=$(lsb_release -si | tr '[:upper:]' '[:lower:]')
    elif [ -f /etc/lsb-release ]; then
        . /etc/lsb-release
        OS=$(echo $DISTRIB_ID | tr '[:upper:]' '[:lower:]')
    elif [ "$(uname)" = "Darwin" ]; then
        OS="macos"
    else
        OS="unknown"
    fi
    echo "$OS"
}

# Check dependencies
check_dependencies() {
    local missing=()
    local deps=("curl" "grep" "sed" "fzf" "jq")

    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &>/dev/null; then
            missing+=("$dep")
        fi
    done

    # Check for video player
    if ! command -v mpv &>/dev/null && ! command -v vlc &>/dev/null; then
        missing+=("mpv")
    fi

    # Check for yt-dlp (recommended but optional)
    if ! command -v yt-dlp &>/dev/null; then
        missing+=("yt-dlp")
    fi

    echo "${missing[@]}"
}

# Install dependencies based on OS
install_dependencies() {
    local os="$1"
    local os_like="$2"
    shift 2
    local deps=("$@")

    if [ ${#deps[@]} -eq 0 ]; then
        echo -e "${GREEN}✓${RESET} All dependencies are already installed!"
        return 0
    fi

    echo -e "${YELLOW}Missing dependencies:${RESET} ${deps[*]}"
    echo ""

    # Try exact OS match first, then fall back to OS_LIKE
    local install_method=""

    case "$os" in
        ubuntu|debian|linuxmint|pop|kali|raspbian)
            install_method="apt"
            ;;
        arch|manjaro|endeavouros|artix|garuda)
            install_method="pacman"
            ;;
        fedora|rhel|centos|rocky|almalinux)
            install_method="dnf"
            ;;
        opensuse*|sles)
            install_method="zypper"
            ;;
        alpine)
            install_method="apk"
            ;;
        void)
            install_method="xbps"
            ;;
        gentoo|funtoo)
            install_method="emerge"
            ;;
        solus)
            install_method="eopkg"
            ;;
        nixos)
            install_method="nix-env"
            ;;
        macos)
            install_method="brew"
            ;;
        *)
            # Try OS_LIKE as fallback
            if [[ "$os_like" =~ debian|ubuntu ]]; then
                install_method="apt"
            elif [[ "$os_like" =~ arch ]]; then
                install_method="pacman"
            elif [[ "$os_like" =~ fedora|rhel ]]; then
                install_method="dnf"
            elif [[ "$os_like" =~ suse ]]; then
                install_method="zypper"
            fi
            ;;
    esac

    case "$install_method" in
        apt)
            echo -e "${BLUE}Installing dependencies with apt...${RESET}"
            sudo apt update && sudo apt install -y "${deps[@]}"
            ;;
        pacman)
            echo -e "${BLUE}Installing dependencies with pacman...${RESET}"
            sudo pacman -Sy --noconfirm --needed "${deps[@]}"
            ;;
        dnf)
            echo -e "${BLUE}Installing dependencies with dnf...${RESET}"
            sudo dnf install -y "${deps[@]}"
            ;;
        zypper)
            echo -e "${BLUE}Installing dependencies with zypper...${RESET}"
            sudo zypper install -y "${deps[@]}"
            ;;
        apk)
            echo -e "${BLUE}Installing dependencies with apk...${RESET}"
            sudo apk add "${deps[@]}"
            ;;
        xbps)
            echo -e "${BLUE}Installing dependencies with xbps-install...${RESET}"
            sudo xbps-install -Sy "${deps[@]}"
            ;;
        emerge)
            echo -e "${BLUE}Installing dependencies with emerge...${RESET}"
            sudo emerge --ask=n "${deps[@]}"
            ;;
        eopkg)
            echo -e "${BLUE}Installing dependencies with eopkg...${RESET}"
            sudo eopkg install -y "${deps[@]}"
            ;;
        nix-env)
            echo -e "${BLUE}Installing dependencies with nix-env...${RESET}"
            nix-env -iA nixpkgs.{$(IFS=, ; echo "${deps[*]}")}
            ;;
        brew)
            if ! command -v brew &>/dev/null; then
                echo -e "${RED}✗ Homebrew not found. Please install from: https://brew.sh${RESET}"
                return 1
            fi
            echo -e "${BLUE}Installing dependencies with brew...${RESET}"
            # macOS needs gnu-sed instead of sed
            local mac_deps=()
            for dep in "${deps[@]}"; do
                if [ "$dep" = "sed" ]; then
                    mac_deps+=("gnu-sed")
                else
                    mac_deps+=("$dep")
                fi
            done
            brew install "${mac_deps[@]}"
            ;;
        *)
            echo -e "${YELLOW}Unknown OS: $os${RESET}"
            echo -e "${YELLOW}Please install the following packages manually:${RESET}"
            echo "  ${deps[*]}"
            echo ""
            echo -e "${YELLOW}Common package managers:${RESET}"
            echo "  apt:        sudo apt install ${deps[*]}"
            echo "  pacman:     sudo pacman -S ${deps[*]}"
            echo "  dnf:        sudo dnf install ${deps[*]}"
            echo "  zypper:     sudo zypper install ${deps[*]}"
            echo ""
            read -p "Continue anyway? [y/N]: " response
            if [[ ! "$response" =~ ^[Yy]$ ]]; then
                echo -e "${RED}Installation cancelled.${RESET}"
                exit 1
            fi
            ;;
    esac
}

# Main installation
main() {
    echo -e "${BLUE}→${RESET} Detecting OS..."
    OS=$(detect_os)
    echo -e "  Detected: ${GREEN}${OS}${RESET}"

    # Get OS_LIKE for better fallback detection
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS_LIKE=${ID_LIKE:-""}
    else
        OS_LIKE=""
    fi
    echo ""

    echo -e "${BLUE}→${RESET} Checking dependencies..."
    MISSING=$(check_dependencies)
    echo ""

    if [ -n "$MISSING" ]; then
        install_dependencies "$OS" "$OS_LIKE" $MISSING
        echo ""
    else
        echo -e "${GREEN}✓${RESET} All dependencies are installed!"
        echo ""
    fi

    echo -e "${BLUE}→${RESET} Creating data directory..."
    mkdir -p "$DATA_DIR"
    echo -e "  ${GREEN}✓${RESET} Created: $DATA_DIR"
    echo ""

    # Migrate old data if exists
    if [ -d "$SCRIPT_DIR/data" ] && [ "$(ls -A "$SCRIPT_DIR/data" 2>/dev/null)" ]; then
        echo -e "${BLUE}→${RESET} Migrating old data..."
        cp -r "$SCRIPT_DIR/data/"* "$DATA_DIR/" 2>/dev/null || true
        echo -e "  ${GREEN}✓${RESET} Data migrated to $DATA_DIR"
        echo ""
    fi

    echo -e "${BLUE}→${RESET} Installing aniworld-cli..."

    # Make executable
    chmod +x "$SCRIPT_DIR/aniworld-cli"

    # Create symlink
    if [ -L "$INSTALL_DIR/aniworld-cli" ]; then
        echo -e "  ${YELLOW}!${RESET} Symlink already exists, removing old version..."
        sudo rm "$INSTALL_DIR/aniworld-cli"
    fi

    sudo ln -s "$SCRIPT_DIR/aniworld-cli" "$INSTALL_DIR/aniworld-cli"
    echo -e "  ${GREEN}✓${RESET} Created symlink: $INSTALL_DIR/aniworld-cli -> $SCRIPT_DIR/aniworld-cli"
    echo ""

    # Success message
    echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${GREEN}║${RESET}  Installation complete!                              ${GREEN}║${RESET}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${RESET}"
    echo ""
    echo -e "${BLUE}Usage:${RESET}"
    echo -e "  ${GREEN}aniworld-cli${RESET}                  - Interactive mode (recommended)"
    echo -e "  ${GREEN}aniworld-cli \"Anime Name\"${RESET}    - Search and watch anime"
    echo -e "  ${GREEN}aniworld-cli --continue${RESET}       - Continue last anime"
    echo -e "  ${GREEN}aniworld-cli --help${RESET}           - Show help"
    echo ""
    echo -e "${BLUE}Data location:${RESET} $DATA_DIR"
    echo -e "${BLUE}Script location:${RESET} $SCRIPT_DIR"
    echo ""
    echo -e "${YELLOW}Tip:${RESET} Just run '${GREEN}aniworld-cli${RESET}' to start!"
    echo ""
}

main "$@"
