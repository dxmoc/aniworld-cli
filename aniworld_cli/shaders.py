"""Anime4K shader presets.

Only the shipped files are referenced, so a preset can never point at a file
that is not in the bundle. Paths are absolute and built at runtime: the shader
directory lives in a per-user writable copy of the mpv pack, not next to the
installed package (a Nix store, a wheel or a PyInstaller bundle may be
read-only).
"""

from __future__ import annotations

from pathlib import Path

#: clang-format off
PRESETS: dict[str, list[str]] = {
    "off": [],
    # Artifact removal only: best default for these streams (720p at ~1.2 Mbit).
    "restore": ["Anime4K_Clamp_Highlights.glsl", "Anime4K_Restore_CNN_M.glsl"],
    # Softer variant for very blocky sources where the sharp restore goes waxy.
    "gentle": ["Anime4K_Clamp_Highlights.glsl", "Anime4K_Restore_CNN_Soft_M.glsl"],
    # bloc97's Mode A (HQ): restore + 2x upscale, downscale-safe on hi-dpi output.
    "a": [
        "Anime4K_Clamp_Highlights.glsl",
        "Anime4K_Restore_CNN_VL.glsl",
        "Anime4K_Upscale_CNN_x2_VL.glsl",
        "Anime4K_AutoDownscalePre_x2.glsl",
        "Anime4K_AutoDownscalePre_x4.glsl",
        "Anime4K_Upscale_CNN_x2_M.glsl",
    ],
    # Mode A on the small CNNs: roughly a third of the GPU cost.
    "fast": [
        "Anime4K_Clamp_Highlights.glsl",
        "Anime4K_Restore_CNN_S.glsl",
        "Anime4K_Upscale_CNN_x2_S.glsl",
        "Anime4K_AutoDownscalePre_x2.glsl",
        "Anime4K_AutoDownscalePre_x4.glsl",
        "Anime4K_Upscale_CNN_x2_S.glsl",
    ],
    # Mode B: upscale only, no restoration.
    "b": [
        "Anime4K_Clamp_Highlights.glsl",
        "Anime4K_Upscale_CNN_x2_M.glsl",
        "Anime4K_AutoDownscalePre_x2.glsl",
        "Anime4K_AutoDownscalePre_x4.glsl",
        "Anime4K_Upscale_CNN_x2_S.glsl",
    ],
    # Mode C: denoise + deblur, no CNN upscale.
    "c": [
        "Anime4K_Clamp_Highlights.glsl",
        "Anime4K_Denoise_Bilateral_Mean.glsl",
        "Anime4K_Deblur_DoG.glsl",
    ],
}
#: clang-format on

#: Menu order and human labels for the in-player menu.
LABELS: list[tuple[str, str]] = [
    ("off", "Off"),
    ("restore", "Restore only"),
    ("gentle", "Gentle (soft restore)"),
    ("a", "Mode A - HQ"),
    ("fast", "Mode A - fast"),
    ("b", "Mode B - upscale only"),
    ("c", "Mode C - denoise + deblur"),
]

DEFAULT = "restore"


def shader_paths(preset: str, shader_dir: Path) -> list[str]:
    """Absolute paths for ``preset``; an unknown name falls back to the default."""
    files = PRESETS.get(preset)
    if files is None:
        files = PRESETS[DEFAULT]
    return [str(shader_dir / name) for name in files]


def auto_preset(source_height: int | None) -> str:
    """Pick a preset from the source resolution.

    A 720p stream on a 1080p display is exactly the case Mode A was written for;
    a real 1080p stream gains nothing from a 2x chain, so only restoration runs.
    """
    if not source_height:
        return DEFAULT
    if source_height >= 1080:
        return "restore"
    return "a"


def glsl_value(preset: str, shader_dir: Path) -> str:
    """The value for mpv's ``--glsl-shaders`` (colon-separated, as mpv wants)."""
    return ":".join(shader_paths(preset, shader_dir))
