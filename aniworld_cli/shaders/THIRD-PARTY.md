# Third-party shaders in this directory

The `Anime4K_*.glsl` files are unmodified third-party work, vendored so that
`--anime4k` needs no download step. They are not part of aniworld-cli:

| Origin | License |
|---|---|
| [bloc97/Anime4K](https://github.com/bloc97/Anime4K) | MIT |

Nothing here is patched. Replacing a file with a newer upstream one is safe as
long as the name stays the same, because `PRESETS` in `__init__.py` refers to
files by name only.
