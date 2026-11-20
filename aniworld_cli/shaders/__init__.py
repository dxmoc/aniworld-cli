"""Anime4K shader presets, shipped with the package.

Opt-in only: without ``--anime4k`` nothing here is used, no ``--config-dir`` is
passed to mpv, and the user's own ``~/.config/mpv`` keeps doing what it does.

The ``.glsl`` files next to this file are unmodified [bloc97/Anime4K] (MIT) --
see ``THIRD-PARTY.md``. They are read straight from the installed package, so a
wheel and a PyInstaller bundle need them as package data.
"""

from __future__ import annotations

import os
from pathlib import Path

#: clang-format off
PRESETS: dict[str, list[str]] = {
    "off": [],
    # Artifact removal only: cheapest, and what these streams need most
    # (720p at ~1.2 Mbit).
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
    # Upscale only: no restoration. Named by what it does, because it is not
    # bloc97's Mode B (that one is Restore_CNN_Soft + upscale).
    "upscale": [
        "Anime4K_Clamp_Highlights.glsl",
        "Anime4K_Upscale_CNN_x2_M.glsl",
        "Anime4K_AutoDownscalePre_x2.glsl",
        "Anime4K_AutoDownscalePre_x4.glsl",
        "Anime4K_Upscale_CNN_x2_S.glsl",
    ],
    # Denoise + deblur, no upscale at all: also not bloc97's Mode C
    # (Upscale_Denoise + upscale), so it is named by its effect instead of a
    # mode letter.
    "denoise": [
        "Anime4K_Clamp_Highlights.glsl",
        "Anime4K_Denoise_Bilateral_Mean.glsl",
        "Anime4K_Deblur_DoG.glsl",
    ],
}
#: clang-format on

#: One line per preset, shown in ``--help`` next to the flag.
HINTS: dict[str, str] = {
    "off": "no shaders (default)",
    "restore": "repair blocky lines only - cheapest",
    "gentle": "softer repair for very blocky sources",
    "fast": "Mode A on the small CNNs - about a third of the GPU cost of 'a'",
    "a": "Mode A - restore + 2x upscale, heaviest; drops frames on an iGPU",
    "upscale": "upscale only, no repair - cheapest way to sharpen",
    "denoise": "denoise + deblur, no upscale",
}


def shader_dir() -> Path:
    """Directory holding the shipped ``.glsl`` files."""
    return Path(__file__).parent


def files(preset: str) -> list[str]:
    """The shader file names of ``preset`` (empty for ``off``)."""
    return list(PRESETS[preset])


def glsl_value(preset: str) -> str:
    """What mpv's ``--glsl-shaders`` wants: absolute paths, PATH-separated.

    mpv splits the value on ``:`` on POSIX and on ``;`` on Windows, which is
    exactly :data:`os.pathsep`, so a Windows drive letter stays intact.
    """
    base = shader_dir()
    return os.pathsep.join(str(base / name) for name in files(preset))


def missing_files(preset: str) -> list[str]:
    """Shipped presets should always resolve; a frozen build without the data
    can lose them, and that is worth a clear error instead of a silent fallback.
    """
    base = shader_dir()
    return [name for name in files(preset) if not (base / name).is_file()]
