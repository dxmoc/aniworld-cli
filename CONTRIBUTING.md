# Contributing to aniworld-cli

Thank you for contributing to aniworld-cli!

## Reporting Bugs

Open an issue and include:
- OS and installation method
- Complete error message
- Steps to reproduce

## Suggesting Features

Open an issue describing:
- What you want to achieve
- Why it would be useful

## Pull Requests

1. Fork and create a branch from `main`
2. Make your changes
3. Test on at least one platform
4. Submit a PR with a clear description

### Code Style

- 4 spaces indentation
- Quote all variables: `"${var}"`
- Functions: lowercase_with_underscores
- Add comments only for complex logic

### Example

```bash
function search_anime() {
    local query="$1"

    if [[ -z "${query}" ]]; then
        echo "Error: Search query required"
        return 1
    fi

    curl -s "${API_URL}?q=${query}"
}
```

## Development Setup

```bash
git clone https://github.com/dxmoc/aniworld-cli.git
cd aniworld-cli
chmod +x aniworld-cli
./aniworld-cli
```

## Testing

Test your changes with:
- Different video providers
- Search, browse, watch, download features
- Edge cases (empty results, network errors)

Debug mode:
```bash
bash -x ./aniworld-cli
```

## Questions?

Open an issue on [GitHub](https://github.com/dxmoc/aniworld-cli/issues).

## License

Contributions are licensed under GPL-3.0.
