#!/usr/bin/env bash
# uninstall.sh - Uninstallation script for aniworld-cli

set -e

# Colors
BLUE='\033[1;34m'
GREEN='\033[1;32m'
RED='\033[1;31m'
YELLOW='\033[1;33m'
RESET='\033[0m'

INSTALL_DIR="/usr/local/bin"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/aniworld-cli"

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BLUE}║${RESET}  aniworld-cli Uninstaller                            ${BLUE}║${RESET}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${RESET}"
echo ""

# Remove symlink
if [ -L "$INSTALL_DIR/aniworld-cli" ]; then
    echo -e "${BLUE}→${RESET} Removing symlink from $INSTALL_DIR..."
    sudo rm "$INSTALL_DIR/aniworld-cli"
    echo -e "  ${GREEN}✓${RESET} Symlink removed"
    echo ""
else
    echo -e "${YELLOW}!${RESET} Symlink not found at $INSTALL_DIR/aniworld-cli"
    echo ""
fi

# Ask about data directory
if [ -d "$DATA_DIR" ]; then
    echo -e "${YELLOW}Data directory found:${RESET} $DATA_DIR"
    echo -e "This contains your watch history and configuration."
    echo ""
    read -p "Remove data directory? [y/N]: " response

    if [[ "$response" =~ ^[Yy]$ ]]; then
        rm -rf "$DATA_DIR"
        echo -e "${GREEN}✓${RESET} Data directory removed"
    else
        echo -e "${BLUE}→${RESET} Data directory kept at: $DATA_DIR"
    fi
    echo ""
fi

echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${RESET}"
echo -e "${GREEN}║${RESET}  Uninstallation complete!                           ${GREEN}║${RESET}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${RESET}"
echo ""
echo -e "${BLUE}Thank you for using aniworld-cli!${RESET}"
echo ""
