# mpv with Anime4K preinstalled, for people who do not (yet) have a custom mpv
# setup. Unlike the CLI's --anime4k, nothing is downloaded or written at runtime:
# the shader chain and the Ctrl+1..Ctrl+6 bindings are baked into the wrapper.
#
# Because mpv has no way to *append* a key binding file, the generated
# input.conf replaces mpv's config directory input.conf (mpv's built-in keys
# stay). If you already maintain one, skip this package and use the CLI's
# --anime4k instead.
{
  lib,
  pkgs,
  mode ? "a",
  hq ? false,
  osc ? true,
}:
let
  shaders = pkgs.callPackage ./anime4k-shaders.nix { };
  modes = import ./anime4k-modes.nix { inherit lib; };

  shaderPath = relative: "${shaders}/share/anime4k/shaders/${relative}";
  chain = m: lib.concatMapStringsSep ":" shaderPath (modes.chain { mode = m; inherit hq; });

  labels = {
    a = "A (1080p)";
    b = "B (720p)";
    c = "C (480p)";
    "a+a" = "A+A";
    "b+b" = "B+B";
    "c+a" = "C+A";
  };
  hotkeys = {
    "CTRL+1" = "a";
    "CTRL+2" = "b";
    "CTRL+3" = "c";
    "CTRL+4" = "a+a";
    "CTRL+5" = "b+b";
    "CTRL+6" = "c+a";
  };

  inputConf = pkgs.writeText "mpv-anime4k-input.conf" (
    lib.concatStrings (
      lib.mapAttrsToList (
        key: m: ''
          ${key} no-osd change-list glsl-shaders set "${chain m}"; show-text "Anime4K: ${labels.${m}}"
        ''
      ) hotkeys
    )
    + ''
      CTRL+0 no-osd change-list glsl-shaders clr ""; show-text "Anime4K: off"
    ''
  );
in
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
      "--input-conf=${inputConf}"
      "--add-flags"
      "--glsl-shaders=${chain mode}"
    ]
    ++ lib.optionals osc [
      "--add-flags"
      "--osc=no"
    ];
}
