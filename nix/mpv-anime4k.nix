# mpv with Anime4K preinstalled, for people who do not (yet) have a custom mpv
# setup. Nothing is downloaded or written at runtime.
#
# The keys and the profile menu come from the shipped Lua script, which changes
# the shader chain at runtime, so no input.conf is generated or replaced and an
# existing one keeps working.
{
  lib,
  pkgs,
  mode ? "a",
  hq ? false,
  osc ? true,
}:
let
  shaders = pkgs.callPackage ./anime4k-shaders.nix { };
  script = ../mpv/aniworld-anime4k.lua;

  modes = [
    "a"
    "b"
    "c"
    "a+a"
    "b+b"
    "c+a"
  ];

  scriptOpts = lib.concatStringsSep "," [
    "aniworld-anime4k-shaders_dir=${shaders}/share/anime4k/shaders"
    "aniworld-anime4k-mode=${mode}"
    "aniworld-anime4k-hq=${if hq then "yes" else "no"}"
  ];
in
assert lib.assertMsg (builtins.elem mode modes)
  "Unknown Anime4K mode '${mode}'. Choose one of: ${lib.concatStringsSep ", " modes}.";
pkgs.mpv.override {
  # ModernZ replaces the stock OSC, which is why osc=no is passed below.
  scripts = lib.optionals osc [ pkgs.mpvScripts.modernz ];

  extraMakeWrapperArgs =
    [
      "--add-flags"
      "--vo=gpu-next"
      "--add-flags"
      "--hwdec=auto-safe"
      "--add-flags"
      "--script=${script}"
      "--add-flags"
      "--script-opts=${scriptOpts}"
    ]
    ++ lib.optionals osc [
      "--add-flags"
      "--osc=no"
    ];
}
