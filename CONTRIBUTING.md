# Contributing to aniworld-cli

Thank you for considering contributing to aniworld-cli! This document provides guidelines for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Features](#suggesting-features)
  - [Pull Requests](#pull-requests)
- [Development Setup](#development-setup)
- [Code Guidelines](#code-guidelines)
- [Testing](#testing)
- [Package Manager Maintenance](#package-manager-maintenance)

## Code of Conduct

This project follows a simple code of conduct:

- Be respectful and considerate
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Keep discussions professional and on-topic

## How Can I Contribute?

### Reporting Bugs

Before submitting a bug report:

1. **Check existing issues** - Your bug may have already been reported
2. **Test with latest version** - Ensure you're using the latest release
3. **Verify dependencies** - Make sure all required tools are installed

When submitting a bug report, include:

- **Operating System** and version (Linux distro, macOS, Windows)
- **Installation method** (AUR, Scoop, Homebrew, manual)
- **aniworld-cli version** (`aniworld-cli --version`)
- **Complete error message** and stack trace
- **Steps to reproduce** the issue
- **Expected vs actual behavior**

### Suggesting Features

Feature suggestions are welcome! Please:

1. **Check existing issues** to avoid duplicates
2. **Describe the use case** - Why is this feature needed?
3. **Provide examples** - How would it work?
4. **Consider alternatives** - Are there other solutions?

### Pull Requests

We actively welcome pull requests! To submit a PR:

#### Before You Start

1. **Open an issue first** for major changes to discuss the approach
2. **Fork the repository** and create a branch from `main`
3. **Follow code guidelines** (see below)

#### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Tested on at least one platform (Linux/macOS/Windows)
- [ ] Updated documentation if needed
- [ ] Added comments for complex logic
- [ ] No hardcoded values or credentials
- [ ] Works with all supported video providers

#### PR Description Should Include

- **What does this PR do?** - Brief summary
- **Why is this needed?** - Problem it solves
- **How was it tested?** - Test steps
- **Screenshots/demos** - For UI changes (if applicable)

## Development Setup

### Prerequisites

Install required dependencies:

**Arch Linux:**
```bash
sudo pacman -S bash curl sed grep fzf mpv yt-dlp nodejs jq
```

**Ubuntu/Debian:**
```bash
sudo apt install bash curl sed grep fzf mpv yt-dlp nodejs jq
```

**macOS:**
```bash
brew install bash curl gnu-sed grep fzf mpv yt-dlp node jq
```

**Windows (Git Bash):**
```bash
scoop install fzf mpv yt-dlp nodejs aria2 jq
```

### Clone and Run

```bash
git clone https://github.com/dxmoc/aniworld-cli.git
cd aniworld-cli
chmod +x aniworld-cli
./aniworld-cli
```

### Project Structure

```
aniworld-cli/
├── aniworld-cli          # Main script
├── lib/                  # Library modules
│   ├── ui.sh            # UI/menu functions
│   ├── player.sh        # Video player integration
│   ├── providers.sh     # Video provider extractors
│   ├── download.sh      # Download functionality
│   └── filemoon.js      # Filemoon extractor
├── PKGBUILD             # Arch Linux package
├── PKGBUILD-git         # Arch Linux git package
├── bucket/              # Scoop manifest
└── Formula/             # Homebrew formula
```

## Code Guidelines

### Shell Script Style

- **Indentation:** 4 spaces (no tabs)
- **Line length:** Max 100 characters where practical
- **Variables:** Use `${VAR}` syntax, uppercase for globals
- **Functions:** Lowercase with underscores (`function_name`)
- **Error handling:** Check exit codes with `|| exit 1`
- **Quotes:** Always quote variables: `"${variable}"`

### Example

```bash
function search_anime() {
    local query="$1"

    if [[ -z "${query}" ]]; then
        echo "Error: Search query required"
        return 1
    fi

    local results
    results=$(curl -s "${API_URL}?q=${query}") || {
        echo "Error: Failed to fetch results"
        return 1
    }

    echo "${results}"
}
```

### Comments

- Use comments for complex logic only
- Avoid stating the obvious
- Explain **why**, not **what**

### Security

- **Never hardcode credentials** or API keys
- **Validate user input** before using in commands
- **Use absolute paths** for system commands
- **Avoid `eval`** unless absolutely necessary
- **Quote all variables** to prevent injection

## Testing

### Manual Testing

Test your changes across:

1. **Different providers** - Vidoza, Streamtape, VOE, Filemoon
2. **Different features** - Search, browse, watch, download
3. **Edge cases** - Empty results, network errors, invalid input
4. **Multiple platforms** - If possible, test on Linux/macOS/Windows

### Debug Mode

Enable debug output:

```bash
bash -x ./aniworld-cli
```

### Common Issues to Check

- Path handling (especially on Windows)
- Special characters in anime names
- Network timeouts and errors
- Player compatibility
- Download interruptions

## Package Manager Maintenance

### Updating AUR Packages

When releasing a new version:

1. Create GitHub release with tag `v1.x.x`
2. Calculate SHA256: `sha256sum aniworld-cli-1.x.x.tar.gz`
3. Update `PKGBUILD`:
   - Increment `pkgver`
   - Reset `pkgrel=1`
   - Update `sha256sums`
4. Generate `.SRCINFO`: `makepkg --printsrcinfo > .SRCINFO`
5. Test build: `makepkg -si`
6. Push to AUR: `git push origin master`

### Updating Scoop Manifest

1. Download new archive
2. Calculate hash: `sha256sum aniworld-cli.zip`
3. Update `bucket/aniworld-cli.json`:
   - Update `version`
   - Update `hash`
4. Test: `scoop install ./bucket/aniworld-cli.json`
5. Commit and push

### Updating Homebrew Formula

1. Update `Formula/aniworld-cli.rb`:
   - Update `url` with new tag
   - Update `version`
   - Update `sha256`
2. Test: `brew install --build-from-source ./Formula/aniworld-cli.rb`
3. Commit and push

See detailed guides in:
- [AUR_UPLOAD.md](AUR_UPLOAD.md)
- [SCOOP_BUCKET.md](SCOOP_BUCKET.md)
- [HOMEBREW_TAP.md](HOMEBREW_TAP.md)

## Questions?

- **Bug reports:** [GitHub Issues](https://github.com/dxmoc/aniworld-cli/issues)
- **General questions:** Open a discussion or issue
- **Security concerns:** Open a private security advisory

## License

By contributing, you agree that your contributions will be licensed under the GPL-3.0 License.
