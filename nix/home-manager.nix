# Home Manager module for NixOS (and any other Home Manager setup).
#
#   programs.aniworld-cli = {
#     enable = true;
#     anime4k.enable = true;   # bundles an Anime4K-enabled mpv
#     anime4k.mode = "a";      # 1080p; "b" for 720p, "c" for 480p, ...
#   };
#
# With anime4k.enable nothing is fetched or written while an episode plays: the
# shaders are pinned in the Nix store and handed to mpv by its wrapper.
{ self }:
{
  config,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.programs.aniworld-cli;
  packages = self.packages.${pkgs.system};

  anime4kCli = pkgs.callPackage ./aniworld-cli-anime4k.nix {
    aniworld-cli = packages.aniworld-cli;
    mpvAnime4k = pkgs.callPackage ./mpv-anime4k.nix {
      inherit (cfg.anime4k) hq;
      mode = cfg.anime4k.mode;
    };
  };
in
{
  options.programs.aniworld-cli = {
    enable = lib.mkEnableOption "aniworld-cli, a streaming-only CLI for aniworld.to";

    package = lib.mkOption {
      type = lib.types.package;
      default = if cfg.anime4k.enable then anime4kCli else packages.aniworld-cli;
      defaultText = lib.literalExpression "aniworld-cli, or its Anime4K bundle when anime4k.enable is set";
      description = "The aniworld-cli package to install.";
    };

    anime4k = {
      enable = lib.mkEnableOption ''
        Anime4K v4 upscaling, bundled with an mpv wrapper (shaders from the Nix
        store, Ctrl+1..Ctrl+6 to switch modes). Replaces mpv's input.conf, so do
        not combine it with your own mpv key bindings
      '';

      mode = lib.mkOption {
        type = lib.types.enum [
          "a"
          "b"
          "c"
          "a+a"
          "b+b"
          "c+a"
        ];
        default = "a";
        description = ''
          Starting Anime4K mode: "a" for 1080p, "b" for 720p, "c" for 480p, and
          the "a+a"/"b+b"/"c+a" variants for a sharper, more artifact-prone image.
        '';
      };

      hq = lib.mkOption {
        type = lib.types.bool;
        default = false;
        description = ''
          Use the larger (VL/M) CNN variants instead of the fast M/S ones. Slower;
          it needs a reasonably strong GPU to keep 24 fps.
        '';
      };
    };
  };

  config = lib.mkIf cfg.enable {
    home.packages = [ cfg.package ];
  };
}
